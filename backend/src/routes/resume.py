"""Endpoint for serving parsed resume data and flushing its cache."""
from typing import Any

from fastapi import APIRouter, Header, HTTPException

from src.config.log_config import setup_logging
from src.config.settings import ADMIN_API_KEY
from src.services.resume_service import clear_resume_cache, get_resume_data

logger = setup_logging(filename=__file__)
router = APIRouter()


def _require_admin(key: str) -> None:
    """Raise 401 if the provided key does not match ADMIN_API_KEY."""
    if not ADMIN_API_KEY or key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/resume")
async def get_resume() -> dict[str, Any]:
    """Return structured resume data parsed from the configured PDF.

    The result is cached for 24 h; call DELETE /admin/resume/cache to flush early.
    """
    try:
        return await get_resume_data()
    except Exception as e:
        logger.error("Failed to load resume data: %s", e, exc_info=True)
        raise HTTPException(status_code=502, detail="Could not load resume data")


@router.delete("/admin/resume/cache")
async def invalidate_resume_cache(
    x_admin_key: str = Header(default=""),
) -> dict[str, str]:
    """Flush the server-side resume cache so the next GET /resume re-parses the PDF."""
    _require_admin(x_admin_key)
    clear_resume_cache()
    return {"status": "cache cleared"}
