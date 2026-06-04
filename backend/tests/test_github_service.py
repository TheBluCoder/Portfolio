import unittest
from unittest.mock import AsyncMock, patch

from src.services.github_service import GitHubService


class GitHubServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_filters_to_public_portfolio_repos(self) -> None:
        service = GitHubService(username="TheBluCoder", topic="portfolio")
        service._get_json = AsyncMock(
            return_value=[
                {
                    "name": "shown",
                    "private": False,
                    "fork": False,
                    "topics": ["portfolio"],
                    "html_url": "https://github.com/TheBluCoder/shown",
                },
                {
                    "name": "hidden",
                    "private": False,
                    "fork": False,
                    "topics": ["demo"],
                    "html_url": "https://github.com/TheBluCoder/hidden",
                },
            ]
        )
        service.get_repo_project_data = AsyncMock(return_value=[])

        projects = await service.list_portfolio_projects()

        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["name"], "shown")

    async def test_ingests_projects_json_for_selected_repo(self) -> None:
        service = GitHubService(username="TheBluCoder", topic="portfolio")
        service.get_repo_project_data = AsyncMock(return_value=[{"name": "Demo", "description": "Test"}])
        repo = {"name": "demo", "private": False, "fork": False, "topics": ["portfolio"]}

        with patch("src.services.github_service.PineconeService") as pinecone:
            pinecone.return_value.upsert_documents = AsyncMock()
            processed = await service.ingest_repo_project_data(repo)

        self.assertTrue(processed)
        pinecone.return_value.upsert_documents.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
