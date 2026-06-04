from fastapi import APIRouter, Header, HTTPException, Request

from src.config.settings import ADMIN_API_KEY
from src.models.schemas import CommentCreate, CommentModeration, Poem, PoemComment, PoemCreate
from src.services.gallery_service import GalleryService
from src.services.rate_limiter import RateLimitExceeded, RateLimiter

router = APIRouter()


@router.get("/gallery/poems")
async def list_poems() -> list[Poem]:
    return GalleryService().list_poems()


@router.post("/gallery/poems")
async def create_poem(
    poem: PoemCreate,
    x_admin_key: str = Header(default=""),
) -> Poem:
    _require_admin(x_admin_key)
    return GalleryService().create_poem(poem.title, poem.body, poem.excerpt, poem.tags)


@router.post("/gallery/poems/{poem_id}/like")
async def like_poem(poem_id: str, request: Request) -> Poem:
    visitor_key = _visitor_key(request)
    return GalleryService().like_poem(poem_id, visitor_key)


@router.post("/gallery/poems/{poem_id}/comments")
async def add_comment(
    poem_id: str,
    comment: CommentCreate,
    request: Request,
) -> PoemComment:
    visitor_key = _visitor_key(request)
    try:
        RateLimiter(table_name="GalleryCommentLimits", max_requests=4).check(visitor_key)
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Please wait before commenting again.")
    return GalleryService().add_comment(poem_id, comment.author, comment.body, visitor_key)


@router.get("/admin/comments/pending")
async def pending_comments(
    x_admin_key: str = Header(default=""),
) -> list[PoemComment]:
    _require_admin(x_admin_key)
    return GalleryService().list_pending_comments()


@router.patch("/admin/comments/{comment_id}")
async def moderate_comment(
    comment_id: str,
    moderation: CommentModeration,
    x_admin_key: str = Header(default=""),
) -> PoemComment:
    _require_admin(x_admin_key)
    return GalleryService().moderate_comment(comment_id, moderation.approved)


def _require_admin(admin_key: str) -> None:
    if not ADMIN_API_KEY:
        raise HTTPException(status_code=500, detail="Admin API key is not configured")
    if admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")


def _visitor_key(request: Request) -> str:
    return RateLimiter().visitor_key(
        request.client.host if request.client else "unknown",
        request.headers.get("user-agent", "unknown"),
    )
