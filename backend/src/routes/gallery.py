from fastapi import APIRouter, Depends, Header, HTTPException, Request

from src.config.log_config import setup_logging
from src.config.settings import ADMIN_API_KEY
from src.dependencies import (
    get_chat_rate_limiter,
    get_gallery_comment_rate_limiter,
    get_gallery_service,
)
from src.models.schemas import Comment, CommentCreate, CommentModeration, Like, Poem, PoemCreate, PoemUpdate
from src.services.gallery_service import GalleryService
from src.services.rate_limiter import RateLimitExceeded, RateLimiter

router = APIRouter()
logger = setup_logging(filename="gallery_route")


@router.get("/gallery/poems")
async def list_poems(
    gallery_service: GalleryService = Depends(get_gallery_service),
) -> list[Poem]:
    return gallery_service.list_poems()


@router.post("/gallery/poems")
async def create_poem(
    poem: PoemCreate,
    x_admin_key: str = Header(default=""),
    gallery_service: GalleryService = Depends(get_gallery_service),
) -> Poem:
    _require_admin(x_admin_key)
    return gallery_service.create_poem(poem.title, poem.body, poem.excerpt, poem.tags)


@router.get("/gallery/poems/{poem_id}")
async def get_poem(
    poem_id: str,
    gallery_service: GalleryService = Depends(get_gallery_service),
) -> Poem:
    try:
        return gallery_service.get_poem(poem_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Poem not found")


@router.patch("/gallery/poems/{poem_id}")
async def update_poem(
    poem_id: str,
    update: PoemUpdate,
    x_admin_key: str = Header(default=""),
    gallery_service: GalleryService = Depends(get_gallery_service),
) -> Poem:
    _require_admin(x_admin_key)
    try:
        return gallery_service.update_poem(
            poem_id, update.title, update.body, update.excerpt, update.tags
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Poem not found")


@router.delete("/gallery/poems/{poem_id}", status_code=204)
async def delete_poem(
    poem_id: str,
    x_admin_key: str = Header(default=""),
    gallery_service: GalleryService = Depends(get_gallery_service),
) -> None:
    _require_admin(x_admin_key)
    try:
        gallery_service.delete_poem(poem_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Poem not found")


@router.post("/gallery/poems/{poem_id}/like")
async def like_poem(
    poem_id: str,
    request: Request,
    gallery_service: GalleryService = Depends(get_gallery_service),
    rate_limiter: RateLimiter = Depends(get_chat_rate_limiter),
) -> Like:
    request_id = getattr(request.state, "request_id", "unknown")
    visitor_key = _visitor_key(request, rate_limiter)
    logger.info("[request_id=%s] Liking poem %s", request_id, poem_id)
    return gallery_service.like_poem(poem_id, visitor_key)


@router.post("/gallery/poems/{poem_id}/comments")
async def add_comment(
    poem_id: str,
    comment: CommentCreate,
    request: Request,
    gallery_service: GalleryService = Depends(get_gallery_service),
    rate_limiter: RateLimiter = Depends(get_gallery_comment_rate_limiter),
) -> Comment:
    request_id = getattr(request.state, "request_id", "unknown")
    visitor_key = _visitor_key(request, rate_limiter)
    try:
        rate_limiter.check(visitor_key)
    except RateLimitExceeded:
        logger.warning("[request_id=%s] Gallery comment rate limit exceeded for poem %s", request_id, poem_id)
        raise HTTPException(status_code=429, detail="Please wait before commenting again.")
    logger.info("[request_id=%s] Adding comment to poem %s", request_id, poem_id)
    return gallery_service.add_comment(poem_id, comment.author, comment.body, visitor_key)


@router.get("/admin/comments/pending")
async def pending_comments(
    x_admin_key: str = Header(default=""),
    gallery_service: GalleryService = Depends(get_gallery_service),
) -> list[Comment]:
    _require_admin(x_admin_key)
    return gallery_service.list_pending_comments()


@router.patch("/admin/comments/{comment_id}")
async def moderate_comment(
    comment_id: str,
    moderation: CommentModeration,
    x_admin_key: str = Header(default=""),
    gallery_service: GalleryService = Depends(get_gallery_service),
) -> Comment:
    _require_admin(x_admin_key)
    return gallery_service.moderate_comment(comment_id, moderation.approved)


def _require_admin(admin_key: str) -> None:
    if not ADMIN_API_KEY:
        logger.error("Admin API key is not configured")
        raise HTTPException(status_code=500, detail="Admin API key is not configured")
    if admin_key != ADMIN_API_KEY:
        logger.warning("Rejected gallery admin request due to invalid admin key")
        raise HTTPException(status_code=401, detail="Invalid admin key")


def _visitor_key(request: Request, rate_limiter: RateLimiter) -> str:
    return rate_limiter.visitor_key(
        request.client.host if request.client else "unknown",
        request.headers.get("user-agent", "unknown"),
    )
