import unittest
from unittest.mock import AsyncMock

from src.services.github_service import GitHubService
from src.services.project_ingestion_service import ProjectIngestionService


class ProjectIngestionServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_ingests_readme_for_selected_repo(self) -> None:
        vector_store = AsyncMock()
        github_service = GitHubService(username="TheBluCoder", topic="portfolio")
        github_service.get_repo_project_data = AsyncMock(return_value=[{"name": "Demo"}])
        github_service.get_repo_readme = AsyncMock(return_value="# Demo\n\nA project README.")
        service = ProjectIngestionService(
            github_service=github_service,
            vector_store=vector_store,
            index_name="portfolio-context",
        )
        repo = {
            "name": "demo",
            "owner": {"login": "TheBluCoder"},
            "private": False,
            "fork": False,
            "topics": ["portfolio"],
        }

        processed = await service.ingest_repo(repo)

        self.assertTrue(processed)
        vector_store.delete_namespace.assert_awaited_once_with(
            "portfolio-context",
            "github:theblucoder:demo",
        )
        vector_store.upsert_documents.assert_awaited_once()
        index_name, documents = vector_store.upsert_documents.await_args.args
        kwargs = vector_store.upsert_documents.await_args.kwargs
        self.assertEqual(index_name, "portfolio-context")
        self.assertEqual(kwargs["namespace"], "github:theblucoder:demo")
        self.assertEqual(documents[0].id, "github-demo-readme")
        self.assertIn("A project README.", documents[0].text)
        self.assertIn(".github/project.json metadata", documents[0].text)

    async def test_skips_repos_without_portfolio_topic(self) -> None:
        vector_store = AsyncMock()
        github_service = GitHubService(username="TheBluCoder", topic="portfolio")
        github_service.get_repo_readme = AsyncMock(return_value="# Demo")
        service = ProjectIngestionService(
            github_service=github_service,
            vector_store=vector_store,
            index_name="portfolio-context",
        )
        repo = {"name": "demo", "private": False, "fork": False, "topics": ["other"]}

        processed = await service.ingest_repo(repo)

        self.assertFalse(processed)
        github_service.get_repo_readme.assert_not_awaited()
        vector_store.delete_namespace.assert_not_awaited()
        vector_store.upsert_documents.assert_not_awaited()

    async def test_deletes_repo_namespace(self) -> None:
        vector_store = AsyncMock()
        github_service = GitHubService(username="TheBluCoder", topic="portfolio")
        service = ProjectIngestionService(
            github_service=github_service,
            vector_store=vector_store,
            index_name="portfolio-context",
        )
        repo = {"name": "demo", "owner": {"login": "TheBluCoder"}}

        processed = await service.delete_repo(repo)

        self.assertTrue(processed)
        vector_store.delete_namespace.assert_awaited_once_with(
            "portfolio-context",
            "github:theblucoder:demo",
        )

    async def test_upserts_manual_project_context(self) -> None:
        vector_store = AsyncMock()
        github_service = GitHubService(username="TheBluCoder", topic="portfolio")
        service = ProjectIngestionService(
            github_service=github_service,
            vector_store=vector_store,
            index_name="portfolio-context",
        )

        result = await service.upsert_manual_context(
            repo_name="demo",
            context_id="architecture-note",
            title="Architecture note",
            text="Extra project detail not in README.",
        )

        self.assertEqual(result["namespace"], "github:theblucoder:demo")
        self.assertEqual(result["document_id"], "manual-architecture-note")
        vector_store.delete_records_by_prefix.assert_awaited_once_with(
            "portfolio-context",
            "github:theblucoder:demo",
            "manual-architecture-note_chunk_",
        )
        vector_store.upsert_documents.assert_awaited_once()
        index_name, documents = vector_store.upsert_documents.await_args.args
        kwargs = vector_store.upsert_documents.await_args.kwargs
        self.assertEqual(index_name, "portfolio-context")
        self.assertEqual(kwargs["namespace"], "github:theblucoder:demo")
        self.assertIn("Extra project detail not in README.", documents[0].text)


if __name__ == "__main__":
    unittest.main()
