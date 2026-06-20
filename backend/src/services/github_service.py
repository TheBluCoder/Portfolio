"""Load and normalize portfolio project metadata from selected GitHub repositories."""

import asyncio
import base64
import json
import urllib.error
import urllib.request
from typing import Any

from src.config.log_config import setup_logging
from src.config.settings import GITHUB_PROJECT_TOPIC, GITHUB_TOKEN, GITHUB_USERNAME

logger = setup_logging(filename="github_service")


class GitHubService:
    """Read public portfolio repositories and their optional project metadata files."""

    api_base = "https://api.github.com"
    portfolio_metadata_path = ".github/project.json"

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
        """Build GitHub API headers, including authentication when configured."""
        headers = {
            "Accept": accept,
            "User-Agent": "ikeoluwa-portfolio",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def list_portfolio_projects(self) -> list[dict[str, Any]]:
        """Return normalized projects from public, non-fork repositories with the topic."""
        repos = await self._get_json(
            f"{self.api_base}/users/{self.username}/repos?per_page=100&type=owner&sort=updated"
        )
        projects = []
        for repo in repos:
            if not self.is_selected_public_repo(repo):
                continue

            project_data = await self.get_repo_project_data(repo["name"])
            logger.info("Loaded project metadata for repo '%s'", repo["name"])
            projects.extend(self._normalize_project_entries(repo, project_data))

        return projects

    async def get_repo_project_data(self, repo_name: str) -> list[dict[str, Any]]:
        """Load project metadata as a consistently list-shaped result."""
        try:
            response = await self._get_json(
                f"{self.api_base}/repos/{self.username}/{repo_name}/contents/{self.portfolio_metadata_path}"
            )
        except FileNotFoundError:
            return []

        content = response.get("content", "")
        decoded = base64.b64decode(content).decode("utf-8")
        parsed = json.loads(decoded)
        return parsed if isinstance(parsed, list) else [parsed]

    def is_selected_public_repo(self, repo: dict[str, Any]) -> bool:
        """Return whether a repository is public, original, and tagged for the portfolio."""
        topics = repo.get("topics") or []
        return (
            not repo.get("private", True)
            and not repo.get("fork", False)
            and self.topic in topics
        )

    def _normalize_project_entries(
        self, repo: dict[str, Any], project_data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Normalize metadata entries, falling back to repository fields when empty."""
        entries = project_data or [{}]
        return [self._normalize_project(repo, entry) for entry in entries]

    def _normalize_project(self, repo: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        """Map repository and metadata aliases into the frontend project schema."""
        return {
            "name": data.get("name") or repo.get("name"),
            "description": data.get("description") or repo.get("description") or "",
            "what": data.get("what") or "",
            "why": data.get("why") or "",
            "impact": data.get("impact") or "",
            "image": data.get("image") or data.get("cover_image") or "/placeholder-image.png",
            "video": data.get("video") or "",
            "demo": data.get("demo") or data.get("homepage") or repo.get("homepage") or "",
            "type": data.get("type") or "repository",
            "source_code_url": data.get("source_code_url") or repo.get("html_url"),
            "tech_stack": data.get("tech_stack")
            or data.get("techStack")
            or data.get("technologies")
            or data.get("stack")
            or [],
            "deployment_stack": data.get("deployment_stack")
            or data.get("deploymentStack")
            or data.get("deployment")
            or [],
            "topics": repo.get("topics", []),
            "updated_at": repo.get("updated_at"),
        }

    async def get_repo_readme(self, repo_name: str) -> str:
        """Return decoded README text, or an empty string when none exists."""
        try:
            response = await self._get_json(
                f"{self.api_base}/repos/{self.username}/{repo_name}/readme"
            )
        except FileNotFoundError:
            return ""

        return self._decode_github_file_content(response)

    def _decode_github_file_content(self, response: dict[str, Any]) -> str:
        """Decode base64 content from a GitHub contents API response."""
        content = response.get("content", "")
        if not content:
            return ""
        return base64.b64decode(content).decode("utf-8")

    async def _get_json(self, url: str) -> Any:
        """Run the blocking GitHub JSON request outside the event loop."""
        return await asyncio.to_thread(self._get_json_sync, url)

    def _get_json_sync(self, url: str) -> Any:
        """Fetch JSON, translating an HTTP 404 into FileNotFoundError."""
        request = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise FileNotFoundError(url) from exc
            logger.error("GitHub request failed for %s: %s", url, exc)
            raise
