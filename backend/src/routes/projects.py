import hmac
import json
from hashlib import sha256
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from src.config.log_config import setup_logging
from src.config.settings import ADMIN_API_KEY, GITHUB_WEBHOOK_SECRET
from src.dependencies import get_github_service, get_project_ingestion_service
from src.models.schemas import ProjectContextUpsert
from src.services.github_service import GitHubService
from src.services.project_ingestion_service import ProjectIngestionService

router = APIRouter()
logger = setup_logging(filename="projects_route")


@router.get("/projects")
async def list_projects(
    github_service: GitHubService = Depends(get_github_service),
) -> dict[str, list[dict[str, Any]]]:
    logger.info("Listing portfolio projects from GitHub")
    return {"projects": await github_service.list_portfolio_projects()}


@router.post("/github/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(default=""),
    x_hub_signature_256: str = Header(default=""),
    project_ingestion_service: ProjectIngestionService = Depends(get_project_ingestion_service),
) -> dict[str, bool]:
    request_id = getattr(request.state, "request_id", "unknown")
    body = await request.body()
    _verify_signature(body, x_hub_signature_256)

    payload = json.loads(body.decode("utf-8") or "{}")
    if x_github_event == "ping":
        logger.info("[request_id=%s] Received GitHub webhook ping", request_id)
        return {"processed": True}

    if x_github_event == "installation_repositories":
        logger.info(
            "[request_id=%s] Received GitHub installation_repositories event action='%s'",
            request_id,
            payload.get("action", ""),
        )
        return {"processed": False}

    repo = payload.get("repository")
    if x_github_event not in {"repository", "public", "push"} or not repo:
        logger.info(
            "[request_id=%s] Ignored GitHub webhook event '%s' action='%s' has_repo=%s",
            request_id,
            x_github_event,
            payload.get("action", ""),
            bool(repo),
        )
        return {"processed": False}

    logger.info(
        "[request_id=%s] Processing GitHub webhook event '%s' for repo '%s'",
        request_id,
        x_github_event,
        repo.get("name", "unknown"),
    )
    processed = await _process_repo_event(
        x_github_event,
        payload,
        project_ingestion_service,
    )
    logger.info("[request_id=%s] GitHub webhook processed=%s", request_id, processed)
    return {"processed": processed}


@router.post("/admin/projects/{repo_name}/context")
async def upsert_project_context(
    repo_name: str,
    payload: ProjectContextUpsert,
    x_admin_key: str = Header(default=""),
    project_ingestion_service: ProjectIngestionService = Depends(get_project_ingestion_service),
) -> dict[str, str]:
    _require_admin(x_admin_key)
    return await project_ingestion_service.upsert_manual_context(
        repo_name=repo_name,
        context_id=payload.context_id,
        text=payload.text,
        title=payload.title,
        owner=payload.owner,
    )


async def _process_repo_event(
    event_name: str,
    payload: dict[str, Any],
    project_ingestion_service: ProjectIngestionService,
) -> bool:
    repo = payload["repository"]
    action = payload.get("action", "")

    if event_name == "push":
        if project_ingestion_service.github_service.is_selected_public_repo(repo):
            return await project_ingestion_service.ingest_repo(repo)
        return await project_ingestion_service.delete_repo(repo)

    if event_name == "public":
        return await project_ingestion_service.ingest_repo(repo)

    if event_name == "repository":
        if action in {"deleted", "privatized", "transferred", "archived"}:
            return await project_ingestion_service.delete_repo(repo)

        if project_ingestion_service.github_service.is_selected_public_repo(repo):
            return await project_ingestion_service.ingest_repo(repo)

        return await project_ingestion_service.delete_repo(repo)

    return False


def _verify_signature(body: bytes, signature: str) -> None:
    if not GITHUB_WEBHOOK_SECRET:
        logger.error("GitHub webhook secret is not configured")
        raise HTTPException(status_code=500, detail="GitHub webhook secret is not configured")

    expected = "sha256=" + hmac.new(
        GITHUB_WEBHOOK_SECRET.encode("utf-8"), body, sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        logger.warning("Rejected GitHub webhook due to invalid signature")
        raise HTTPException(status_code=401, detail="Invalid GitHub webhook signature")


def _require_admin(admin_key: str) -> None:
    if not ADMIN_API_KEY:
        logger.error("Admin API key is not configured")
        raise HTTPException(status_code=500, detail="Admin API key is not configured")
    if admin_key != ADMIN_API_KEY:
        logger.warning("Rejected project admin request due to invalid admin key")
        raise HTTPException(status_code=401, detail="Invalid admin key")
