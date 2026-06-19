import unittest
import base64
import json
from unittest.mock import AsyncMock

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

    async def test_loads_metadata_from_github_project_json(self) -> None:
        service = GitHubService(username="TheBluCoder", topic="portfolio")
        payload = [{"name": "Demo"}]
        service._get_json = AsyncMock(
            return_value={
                "content": base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
            }
        )

        projects = await service.get_repo_project_data("demo")

        self.assertEqual(projects, payload)
        service._get_json.assert_awaited_once_with(
            "https://api.github.com/repos/TheBluCoder/demo/contents/.github/project.json"
        )


if __name__ == "__main__":
    unittest.main()
