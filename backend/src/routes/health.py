from fastapi import APIRouter
from datetime import datetime
from ..models.schemas import HealthResponse

router = APIRouter()

@router.get("/health")
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    ) 