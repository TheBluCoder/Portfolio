import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import chat, indexes, health
from src.services.pinecone_service import PineconeService
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Pinecone service singleton on startup
    # The __new__ method ensures we get the singleton instance
    await PineconeService().initialize()
    yield
    # Close Pinecone service singleton on shutdown
    # The __new__ method ensures we get the same singleton instance to close
    await PineconeService().close()


# --- Dependency Function ---
async def get_pinecone_service() -> PineconeService:
    """Dependency function to get the initialized PineconeService singleton."""
    # Since initialization is handled by lifespan, we just return the instance.
    # The singleton pattern ensures we get the correct, initialized instance.
    return PineconeService()
# --------------------------


app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api")
app.include_router(indexes.router, prefix="/api")
app.include_router(health.router)
