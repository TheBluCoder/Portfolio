"""Build and maintain vector-search context for portfolio projects."""

import json
from collections.abc import Awaitable
from typing import Any, Protocol

from src.config.log_config import setup_logging
from src.config.settings import PORTFOLIO_CONTEXT_INDEX
from src.models.schemas import Content
from src.services.github_service import GitHubService

logger = setup_logging(filename="project_ingestion_service")


class ProjectVectorStore(Protocol):
    """Vector-store operations required by project ingestion."""

    def upsert_documents(
        self,
        index_name: str,
        documents: list[Content],
        namespace: str = "default",
    ) -> Awaitable[None]: ...
    def delete_namespace(self, index_name: str, namespace: str) -> Awaitable[None]: ...
    def delete_records_by_prefix(
        self,
        index_name: str,
        namespace: str,
        prefix: str,
    ) -> Awaitable[int]: ...


class ProjectIngestionService:
    """Ingest selected GitHub repositories and manual notes into isolated namespaces."""

    def __init__(
        self,
        github_service: GitHubService,
        vector_store: ProjectVectorStore,
        index_name: str = PORTFOLIO_CONTEXT_INDEX,
    ) -> None:
        self.github_service = github_service
        self.vector_store = vector_store
        self.index_name = index_name

    async def ingest_repo(self, repo: dict[str, Any]) -> bool:
        """Replace a selected repository's vector context from metadata and README content."""
        if not self.github_service.is_selected_public_repo(repo):
            return False

        repo_name = repo.get("name")
        if not repo_name:
            logger.warning("Skipping GitHub webhook payload without a repository name")
            return False

        namespace = self.repo_namespace(repo)
        await self.vector_store.delete_namespace(self.index_name, namespace)

        project_data = await self.github_service.get_repo_project_data(repo_name)
        readme = await self.github_service.get_repo_readme(repo_name)
        if not readme and not project_data:
            logger.info("Skipping repo '%s' because no README or project metadata was found", repo_name)
            return False

        documents = [
            Content(
                id=f"github-{repo_name}-readme",
                text=self._build_embedding_document(repo, readme, project_data),
            )
        ]
        await self.vector_store.upsert_documents(self.index_name, documents, namespace=namespace)
        return True

    async def delete_repo(self, repo: dict[str, Any]) -> bool:
        """Delete all vector context for a repository named in a webhook payload."""
        repo_name = repo.get("name")
        if not repo_name:
            logger.warning("Skipping namespace cleanup for payload without a repository name")
            return False

        await self.vector_store.delete_namespace(self.index_name, self.repo_namespace(repo))
        return True

    async def upsert_manual_context(
        self,
        repo_name: str,
        context_id: str,
        text: str,
        title: str | None = None,
        owner: str | None = None,
    ) -> dict[str, str]:
        """Replace one manual note and return its namespace and deterministic document ID."""
        # Use a dedicated :manual namespace so re-ingestion never wipes manual context.
        namespace = self.manual_namespace(owner or self.github_service.username, repo_name)
        document_id = f"manual-{self._slug(context_id)}"
        content = self._build_manual_context_document(repo_name, context_id, text, title)

        await self.vector_store.delete_records_by_prefix(
            self.index_name,
            namespace,
            f"{document_id}_chunk_",
        )
        await self.vector_store.upsert_documents(
            self.index_name,
            [Content(id=document_id, text=content)],
            namespace=namespace,
        )
        return {"namespace": namespace, "document_id": document_id}

    def repo_namespace(self, repo: dict[str, Any]) -> str:
        """Return the stable vector namespace for a repository payload."""
        owner = repo.get("owner", {}).get("login") or self.github_service.username
        repo_name = repo.get("name", "unknown")
        return self.project_namespace(owner, repo_name)

    def project_namespace(self, owner: str, repo_name: str) -> str:
        """Build a normalized project namespace from repository ownership."""
        return f"github:{self._slug(owner)}:{self._slug(repo_name)}"

    def manual_namespace(self, owner: str, repo_name: str) -> str:
        """Separate namespace for hand-written context; survives auto re-ingestion."""
        return f"{self.project_namespace(owner, repo_name)}:manual"

    def _build_embedding_document(
        self,
        repo: dict[str, Any],
        readme: str,
        project_data: list[dict[str, Any]],
    ) -> str:
        """Combine repository identity, metadata, and README text for embedding."""
        repo_summary = {
            "name": repo.get("name"),
            "description": repo.get("description") or "",
            "homepage": repo.get("homepage") or "",
            "html_url": repo.get("html_url") or "",
            "topics": repo.get("topics", []),
            "updated_at": repo.get("updated_at"),
        }
        return (
            "Repository metadata:\n"
            f"{json.dumps(repo_summary, ensure_ascii=False)}\n\n"
            ".github/project.json metadata:\n"
            f"{json.dumps(project_data, ensure_ascii=False)}\n\n"
            "README:\n"
            f"{readme}"
        )

    def _build_manual_context_document(
        self,
        repo_name: str,
        context_id: str,
        text: str,
        title: str | None,
    ) -> str:
        """Format a titled or untitled manual note for embedding."""
        heading = title or context_id
        return (
            "Manual project context:\n"
            f"Repository: {repo_name}\n"
            f"Context ID: {context_id}\n"
            f"Title: {heading}\n\n"
            f"{text}"
        )

    def _slug(self, value: str) -> str:
        """Normalize an identifier for use in namespaces and record keys."""
        return value.lower().replace("_", "-").replace("/", "-")
