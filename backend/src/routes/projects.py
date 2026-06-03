import hmac
import json
from hashlib import sha256

from fastapi import APIRouter, Header, HTTPException, Request

from src.config.settings import GITHUB_WEBHOOK_SECRET
from src.services.github_service import GitHubService

router = APIRouter()


@router.get("/projects")
async def list_projects():
    return {"projects": await GitHubService().list_portfolio_projects()}


@router.post("/github/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(default=""),
    x_hub_signature_256: str = Header(default=""),
):
    body = await request.body()
    _verify_signature(body, x_hub_signature_256)

    payload = json.loads(body.decode("utf-8") or "{}")
    repo = payload.get("repository")
    if x_github_event not in {"repository", "public", "push"} or not repo:
        return {"processed": False}

    processed = await GitHubService().ingest_repo_project_data(repo)
    return {"processed": processed}


def _verify_signature(body: bytes, signature: str):
    if not GITHUB_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="GitHub webhook secret is not configured")

    expected = "sha256=" + hmac.new(
        GITHUB_WEBHOOK_SECRET.encode("utf-8"), body, sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid GitHub webhook signature")
