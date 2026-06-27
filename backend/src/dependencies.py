from functools import lru_cache

from fastapi import Depends

from src.services import Bot
from src.services.chat_follow_up import ChatFollowUpResolver
from src.services.chat_prompting import ChatPromptBuilder
from src.services.gallery_service import GalleryService
from src.services.github_service import GitHubService
from src.services.pinecone_service import PineconeService
from src.services.project_ingestion_service import ProjectIngestionService
from src.services.rate_limiter import RateLimiter
from src.services.topic_gate import TopicGate


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


def get_topic_gate(
    pinecone_service: PineconeService = Depends(get_pinecone_service),
) -> TopicGate:
    return TopicGate(vector_store=pinecone_service)


@lru_cache
def get_chat_prompt_builder() -> ChatPromptBuilder:
    return ChatPromptBuilder()


@lru_cache
def get_chat_follow_up_resolver() -> ChatFollowUpResolver:
    return ChatFollowUpResolver()


def get_bot_service(
    pinecone_service: PineconeService = Depends(get_pinecone_service),
    topic_gate: TopicGate = Depends(get_topic_gate),
    prompt_builder: ChatPromptBuilder = Depends(get_chat_prompt_builder),
    follow_up_resolver: ChatFollowUpResolver = Depends(get_chat_follow_up_resolver),
) -> Bot.BotService:
    return Bot.BotService(
        context_retriever=pinecone_service,
        topic_gate=topic_gate,
        prompt_builder=prompt_builder,
        follow_up_resolver=follow_up_resolver,
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
