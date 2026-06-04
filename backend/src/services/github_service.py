import asyncio
import base64
import json
import urllib.error
import urllib.request
from typing import Any

from src.config.log_config import setup_logging
from src.config.settings import GITHUB_PROJECT_TOPIC, GITHUB_TOKEN, GITHUB_USERNAME
from src.models.schemas import Content
from src.services.pinecone_service import PineconeService

logger = setup_logging(filename="github_service")


class GitHubService:
    api_base = "https://api.github.com"

    def __init__(
        self,
        username: str = GITHUB_USERNAME,
        topic: str = GITHUB_PROJECT_TOPIC,
        token: str | None = GITHUB_TOKEN,
    ) -> None:
        self.username = username
        self.topic = topic
        self.token = token

    def _headers(self, accept: str = "application/vnd.github+json") -> dict[str, str]:
        headers = {
            "Accept": accept,
            "User-Agent": "ikeoluwa-portfolio",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def list_portfolio_projects(self) -> list[dict[str, Any]]:
        repos = await self._get_json(
            f"{self.api_base}/users/{self.username}/repos?per_page=100&type=owner&sort=updated"
        )
        projects = []
        for repo in repos:
            if not self._is_selected_public_repo(repo):
                continue

            project_data = await self.get_repo_project_data(repo["name"])
            projects.extend(self._normalize_project_entries(repo, project_data))

        return projects

    async def get_repo_project_data(self, repo_name: str) -> list[dict[str, Any]]:
        try:
            response = await self._get_json(
                f"{self.api_base}/repos/{self.username}/{repo_name}/contents/projects.json"
            )
        except FileNotFoundError:
            return []

        content = response.get("content", "")
        decoded = base64.b64decode(content).decode("utf-8")
        parsed = json.loads(decoded)
        return parsed if isinstance(parsed, list) else [parsed]

    async def ingest_repo_project_data(self, repo: dict[str, Any]) -> bool:
        if not self._is_selected_public_repo(repo):
            return False

        project_data = await self.get_repo_project_data(repo["name"])
        if not project_data:
            return False

        documents = [
            Content(
                id=f"{repo['name']}-{index}",
                text=json.dumps(project, ensure_ascii=False),
            )
            for index, project in enumerate(project_data)
        ]
        await PineconeService().upsert_documents(self._index_name(repo["name"]), documents)
        return True

    def _is_selected_public_repo(self, repo: dict[str, Any]) -> bool:
        topics = repo.get("topics") or []
        return (
            not repo.get("private", True)
            and not repo.get("fork", False)
            and self.topic in topics
        )

    def _normalize_project_entries(
        self, repo: dict[str, Any], project_data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        entries = project_data or [{}]
        return [self._normalize_project(repo, entry) for entry in entries]

    def _normalize_project(self, repo: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": data.get("name") or repo.get("name"),
            "description": data.get("description") or repo.get("description") or "",
            "image": data.get("image") or data.get("cover_image") or "/placeholder-image.png",
            "demo": data.get("demo") or data.get("homepage") or repo.get("homepage") or "",
            "type": data.get("type") or "repository",
            "source_code_url": data.get("source_code_url") or repo.get("html_url"),
            "topics": repo.get("topics", []),
            "updated_at": repo.get("updated_at"),
        }

    def _index_name(self, repo_name: str) -> str:
        return repo_name.lower().replace("_", "-")

    async def _get_json(self, url: str) -> Any:
        return await asyncio.to_thread(self._get_json_sync, url)

    def _get_json_sync(self, url: str) -> Any:
        request = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise FileNotFoundError(url) from exc
            logger.error("GitHub request failed for %s: %s", url, exc)
            raise
