from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from src.config.log_config import setup_logging
from src.dependencies import get_bot_service, get_chat_rate_limiter
from ..models.schemas import ChatRequest
from ..services import Bot
from ..services.rate_limiter import RateLimitExceeded, RateLimiter

router = APIRouter()
logger = setup_logging(filename="chat_route")

@router.post("/chat")
async def chat(
    request: Request,
    chat_request: ChatRequest,
    bot_service: Bot.BotService = Depends(get_bot_service),
    rate_limiter: RateLimiter = Depends(get_chat_rate_limiter),
) -> StreamingResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        visitor_key = rate_limiter.visitor_key(
            request.client.host if request.client else "unknown",
            request.headers.get("user-agent", "unknown"),
        )
        rate_limiter.check(visitor_key)
        logger.info(
            "[request_id=%s] Processing chat request with %s messages",
            request_id,
            len(chat_request.context or []),
        )
        return StreamingResponse(
            bot_service.stream_response(chat_request.context),
            media_type="text/plain; charset=utf-8",
        )
    except RateLimitExceeded:
        logger.warning("[request_id=%s] Chat rate limit exceeded", request_id)
        raise HTTPException(
            status_code=429,
            detail="Too many chat messages. Please wait a bit before trying again.",
        )
    except Exception as e:
        logger.exception("[request_id=%s] Chat request failed: %s", request_id, e)
        raise HTTPException(status_code=500, detail=str(e))
