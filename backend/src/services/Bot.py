"""Generate portfolio-grounded chat responses with relevance resolution and retrieval."""

import asyncio
import dotenv
import re
from collections.abc import AsyncIterator, Awaitable
from typing import TYPE_CHECKING, Any, Protocol

from google import genai

from src.config.log_config import setup_logging
from src.config.prompts import SYSTEM_PROMPT
from src.config.settings import GEMINI_MODEL, GOOGLE_API_KEY, PORTFOLIO_CONTEXT_INDEX
from src.models.schemas import Message
from src.services.chat_context import clamp_user_message
from src.services.chat_prompting import ChatPromptBuilder
from src.services.chat_resolver import ChatResolver

OFF_TOPIC_RESPONSE = (
    "Tiny detour detected. I’m best at questions about Ikeoluwa, his projects, "
    "skills, experience, education, interests, and portfolio. Ask me anything in that lane "
    "and I’ll happily put on the tiny detective hat."
)

if TYPE_CHECKING:
    from google.genai.chats import AsyncChat
else:
    AsyncChat = Any


logger = setup_logging(filename=__file__)
dotenv.load_dotenv()  # Load environment variables early

client = genai.Client(api_key=GOOGLE_API_KEY)
generation_config = genai.types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    temperature=0.5,
    top_p=0.3,
)


class ContextRetriever(Protocol):
    """Required vector retrieval operations for the bot service."""

    def fetch_candidates(self, index_name: str, query: str, namespaces: list[str] | None = None) -> Awaitable[list[dict[str, Any]]]: ...
    def rerank_candidates(self, candidates: list[dict[str, Any]], rerank_query: str) -> Awaitable[list[dict[str, Any]]]: ...


class BotService:
    """Coordinate chat relevance resolution, context retrieval, and Gemini responses."""

    def __init__(
        self,
        context_retriever: ContextRetriever,
        prompt_builder: ChatPromptBuilder,
        chat_resolver: ChatResolver,
        context_index: str = PORTFOLIO_CONTEXT_INDEX,
    ) -> None:
        self.context_retriever = context_retriever
        self.prompt_builder = prompt_builder
        self.chat_resolver = chat_resolver
        self.context_index = context_index

    async def stream_response(self, context: list[Message] | None = None) -> AsyncIterator[str]:
        """Stream a grounded response token-by-token for the latest human message."""
        latest_question = next(
            (msg.content for msg in reversed(context or []) if msg.type == "human"),
            "",
        )
        latest_question = clamp_user_message(latest_question)

        # Build fetch query synchronously — no network call needed
        fetch_query = self.prompt_builder.build_retrieval_query(
            context, latest_question, latest_question,
        )
        namespaces = self._extract_project_namespaces(context)

        # Run resolver and vector fetch in parallel
        try:
            resolution, candidates = await asyncio.gather(
                self.chat_resolver.resolve(context, latest_question),
                self._fetch_candidates(fetch_query, namespaces=namespaces),
            )
        except Exception as e:
            logger.error("Error resolving chat relevance: %s", e, exc_info=True)
            yield "An error occurred while understanding the message."
            return

        # Gate on relevance — rerank never fires for off-topic queries
        if not resolution.relevant:
            yield OFF_TOPIC_RESPONSE
            return

        # Rerank using the resolver's standalone question for better precision
        rerank_query = self.prompt_builder.build_retrieval_query(
            context, latest_question, resolution.standalone_question,
        )
        retrieved_context = await self._rerank(candidates, rerank_query)
        prompt = self.prompt_builder.build_generation_prompt(retrieved_context, latest_question)
        history = self.prompt_builder.build_chat_history(context)

        try:
            chat: AsyncChat = client.aio.chats.create(
                model=GEMINI_MODEL,
                config=generation_config,
                history=history or None,
            )
            stream = await chat.send_message_stream(prompt)
            async for chunk in stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error("Error during generation: %s", e, exc_info=True)
            yield "An error occurred while generating the response."

    async def generate_response(self, context: list[Message] | None = None) -> str:
        """Collect the full streamed response into a string."""
        return "".join([chunk async for chunk in self.stream_response(context)])

    def _extract_project_namespaces(self, context: list[Message] | None) -> list[str] | None:
        """Return [project_ns, manual_ns] parsed from the project context message, or None for global chat."""
        for msg in (context or []):
            if msg.type == "human" and msg.content.startswith("The user is viewing this project:"):
                match = re.search(
                    r"Source code:\s*https?://github\.com/([^/\s]+)/([^/\s]+)",
                    msg.content,
                )
                if match:
                    owner = match.group(1).lower().replace("_", "-")
                    repo = match.group(2).lower().replace("_", "-")
                    base = f"github:{owner}:{repo}"
                    return [base, f"{base}:manual"]
        return None

    async def _fetch_candidates(self, query: str, namespaces: list[str] | None = None) -> list[dict[str, Any]]:
        """Fetch raw candidates, scoped to project namespaces when available."""
        try:
            return await self.context_retriever.fetch_candidates(self.context_index, query, namespaces=namespaces)
        except Exception as e:
            logger.error("Error fetching candidates: %s", e, exc_info=True)
            return []

    async def _rerank(self, candidates: list[dict[str, Any]], rerank_query: str) -> dict[str, Any]:
        """Rerank candidates with the resolved query, returning a context dict for prompt building."""
        result: dict[str, Any] = {"index": self.context_index, "results": None}
        try:
            top_hits = await self.context_retriever.rerank_candidates(candidates, rerank_query)
            result["results"] = {"reranked": top_hits}
        except Exception as e:
            logger.error("Error reranking candidates: %s", e, exc_info=True)
        return result
