"""Public and admin endpoints for the reading list."""
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from src.config.log_config import setup_logging
from src.config.settings import ADMIN_API_KEY
from src.services.reading_service import ReadingService

logger = setup_logging(filename=__file__)
router = APIRouter()

_service = ReadingService()


def _require_admin(key: str) -> None:
    """Raise 401 if the provided key does not match ADMIN_API_KEY."""
    if not ADMIN_API_KEY or key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


class CurrentBookBody(BaseModel):
    title: str = Field(..., min_length=1, description="Book title")
    author: str = Field(..., min_length=1, description="Author name(s)")
    thoughts: str = Field(default="", description="Personal notes on the book")
    progress: int = Field(default=0, ge=0, le=100, description="Reading progress (0–100 %)")
    since: str = Field(default="", description="Month started, e.g. 2025-05")
    cover: str | None = Field(default=None, description="Cover image URL")


class RecentBookBody(BaseModel):
    title: str = Field(..., min_length=1, description="Book title")
    author: str = Field(..., min_length=1, description="Author name(s)")
    finished_at: str | None = Field(
        default=None, description="Month finished (YYYY-MM); defaults to current month"
    )


class ReadingResponse(BaseModel):
    current: dict[str, Any]
    recent: list[dict[str, Any]]


@router.get("/reading", response_model=ReadingResponse)
async def get_reading() -> dict[str, Any]:
    """Return the current book and list of recently finished books."""
    try:
        return {
            "current": _service.get_current(),
            "recent": _service.list_recent(),
        }
    except Exception as e:
        logger.error("Failed to load reading data: %s", e)
        # Return safe defaults so the public gallery page never breaks.
        return {
            "current": {
                "title": "The Pragmatic Programmer",
                "author": "David Thomas & Andrew Hunt",
                "cover": None,
                "thoughts": "",
                "progress": 40,
                "since": "2025-05",
            },
            "recent": [],
        }


@router.put("/admin/reading/current")
async def set_current_book(
    body: CurrentBookBody,
    x_admin_key: str = Header(default=""),
) -> dict[str, Any]:
    """Replace the current book entry."""
    _require_admin(x_admin_key)
    return _service.set_current(
        title=body.title,
        author=body.author,
        thoughts=body.thoughts,
        progress=body.progress,
        since=body.since,
        cover=body.cover,
    )


@router.post("/admin/reading/recent", status_code=201)
async def add_recent_book(
    body: RecentBookBody,
    x_admin_key: str = Header(default=""),
) -> dict[str, Any]:
    """Add a book to the recently finished list."""
    _require_admin(x_admin_key)
    return _service.add_recent(body.title, body.author, body.finished_at)


@router.delete("/admin/reading/recent/{row_key}", status_code=204)
async def delete_recent_book(
    row_key: str,
    x_admin_key: str = Header(default=""),
) -> None:
    """Remove a book from the recently finished list by its ID."""
    _require_admin(x_admin_key)
    try:
        _service.delete_recent(row_key)
    except Exception as e:
        logger.error("Failed to delete recent book %s: %s", row_key, e)
        raise HTTPException(status_code=404, detail="Not found")
