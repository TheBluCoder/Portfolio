from functools import lru_cache

from fastapi import Depends

from src.services import Bot
from src.services.chat_prompting import ChatPromptBuilder
from src.services.chat_resolver import ChatResolver
from src.services.gallery_service import GalleryService
from src.services.github_service import GitHubService
from src.services.pinecone_service import PineconeService
from src.services.project_ingestion_service import ProjectIngestionService
from src.services.rate_limiter import RateLimiter


@lru_cache
def get_pinecone_service() -> PineconeService:
    return PineconeService()


@lru_cache
def get_gallery_service() -> GalleryService:
    return GalleryService()


@lru_cache
def get_chat_rate_limiter() -> RateLimiter:
    return RateLimiter()


@lru_cache
def get_gallery_comment_rate_limiter() -> RateLimiter:
    return RateLimiter(table_name="GalleryCommentLimits", max_requests=4)


@lru_cache
def get_chat_prompt_builder() -> ChatPromptBuilder:
    return ChatPromptBuilder()


@lru_cache
def get_chat_resolver() -> ChatResolver:
    return ChatResolver()


def get_bot_service(
    pinecone_service: PineconeService = Depends(get_pinecone_service),
    prompt_builder: ChatPromptBuilder = Depends(get_chat_prompt_builder),
    chat_resolver: ChatResolver = Depends(get_chat_resolver),
) -> Bot.BotService:
    return Bot.BotService(
        context_retriever=pinecone_service,
        prompt_builder=prompt_builder,
        chat_resolver=chat_resolver,
    )


def get_github_service() -> GitHubService:
    return GitHubService()


def get_project_ingestion_service(
    github_service: GitHubService = Depends(get_github_service),
    pinecone_service: PineconeService = Depends(get_pinecone_service),
) -> ProjectIngestionService:
    return ProjectIngestionService(
        github_service=github_service,
        vector_store=pinecone_service,
    )
