from fastapi import APIRouter, HTTPException
from ..models.schemas import ChatRequest
from ..services import Bot

router = APIRouter()

@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        response = await Bot.generate_response( request.context)
        print(response)
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 