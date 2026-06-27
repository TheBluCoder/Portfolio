from datetime import datetime, timezone
from fastapi import APIRouter
from src.config.settings import BUILD_COMMIT
from ..models.schemas import HealthResponse

router = APIRouter()

@router.get("/health")
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version=BUILD_COMMIT,
    )
