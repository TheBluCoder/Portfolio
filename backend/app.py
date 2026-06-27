from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from time import perf_counter
from typing import AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from src.config.log_config import configure_logging, setup_logging
from src.config.settings import CORS_ALLOWED_ORIGINS
from src.dependencies import get_pinecone_service
from src.routes import chat, health, projects, gallery, resume, admin_pinecone, reading


configure_logging()
logger = setup_logging(filename="app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    pinecone_service = get_pinecone_service()
    try:
        logger.info("Starting FastAPI application")
        await pinecone_service.initialize()
        logger.info("Pinecone service initialized")
        yield
    finally:
        logger.info("Shutting down FastAPI application")
        await pinecone_service.close()
        logger.info("Pinecone service closed")


app = FastAPI(lifespan=lifespan)

# Allow only configured frontend origins to call the API from browsers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if CORS_ALLOWED_ORIGINS:
    logger.info("Configured CORS allowed origins: %s", CORS_ALLOWED_ORIGINS)
else:
    logger.warning(
        "No CORS_ALLOWED_ORIGINS configured. Browser requests from other origins will be blocked."
    )


@app.middleware("http")
async def log_requests(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    request_id = request.headers.get("x-request-id") or str(uuid4())
    request.state.request_id = request_id
    start_time = perf_counter()
    client_host = request.client.host if request.client else "unknown"

    logger.info(
        "[request_id=%s] Started %s %s from %s",
        request_id,
        request.method,
        request.url.path,
        client_host,
    )

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((perf_counter() - start_time) * 1000, 2)
        logger.exception(
            "[request_id=%s] Unhandled error during %s %s after %sms",
            request_id,
            request.method,
            request.url.path,
            duration_ms,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
            headers={"X-Request-ID": request_id},
        )

    duration_ms = round((perf_counter() - start_time) * 1000, 2)
    logger.info(
        "[request_id=%s] Completed %s %s with %s in %sms",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    response.headers["X-Request-ID"] = request_id
    return response

# Include routers
app.include_router(chat.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(gallery.router, prefix="/api")
app.include_router(resume.router, prefix="/api")
app.include_router(admin_pinecone.router, prefix="/api")
app.include_router(reading.router, prefix="/api")
app.include_router(health.router)
