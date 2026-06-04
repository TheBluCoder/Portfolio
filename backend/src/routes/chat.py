from fastapi import APIRouter, HTTPException, Request
from ..models.schemas import ChatRequest
from ..services import Bot
from ..services.rate_limiter import RateLimitExceeded, RateLimiter

router = APIRouter()

@router.post("/chat")
async def chat(request: Request, chat_request: ChatRequest) -> str:
    try:
        visitor_key = RateLimiter().visitor_key(
            request.client.host if request.client else "unknown",
            request.headers.get("user-agent", "unknown"),
        )
        RateLimiter().check(visitor_key)
        response = await Bot.generate_response(chat_request.context)
        print(response)
        return response
    except RateLimitExceeded:
        raise HTTPException(
            status_code=429,
            detail="Too many chat messages. Please wait a bit before trying again.",
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
