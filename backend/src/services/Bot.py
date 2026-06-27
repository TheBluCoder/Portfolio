"""Generate portfolio-grounded chat responses with relevance resolution and retrieval."""

import dotenv
from collections.abc import Awaitable
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

    def query_similar(self, index_name: str, query: str) -> Awaitable[Any]: ...
    def query_similar_namespaces(self, index_name: str, query: str) -> Awaitable[dict[str, Any]]: ...


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

    async def generate_response(self, context: list[Message] | None = None) -> str:
        """Generate a grounded response for the latest human message in a conversation."""
        latest_question = next(
            (msg.content for msg in reversed(context or []) if msg.type == "human"),
            "",
        )
        latest_question = clamp_user_message(latest_question)

        try:
            resolution = await self.chat_resolver.resolve(context, latest_question)
        except Exception as e:
            logger.error("Error resolving chat relevance: %s", e, exc_info=True)
            return "An error occurred while understanding the message."
        if not resolution.relevant:
            return OFF_TOPIC_RESPONSE

        retrieval_query = self.prompt_builder.build_retrieval_query(
            context,
            latest_question,
            resolution.standalone_question,
        )
        retrieved_context = await self.retrieve_context(retrieval_query)
        prompt = self.prompt_builder.build_generation_prompt(retrieved_context, latest_question)
        history = self.prompt_builder.build_chat_history(context)

        try:
            chat: AsyncChat = client.aio.chats.create(
                model=GEMINI_MODEL,
                config=generation_config,
                history=history or None,
            )
            response = await chat.send_message(prompt)
            usage = response.usage_metadata
            logger.info(
                "LLM response generated: prompt_tokens=%s cached_tokens=%s total_tokens=%s",
                getattr(usage, "prompt_token_count", None),
                getattr(usage, "cached_content_token_count", None),
                getattr(usage, "total_token_count", None),
            )
            return response.text if response.text else "No content in response."
        except Exception as e:
            logger.error(f"Error during generation or tool handling: {e}", exc_info=True)
            return "An error occurred while generating the response."

    async def retrieve_context(self, question: str) -> dict[str, Any]:
        """Retrieve matching context across namespaces without failing the chat request."""
        context: dict[str, Any] = {"index": self.context_index, "results": None}

        try:
            context["results"] = await self.context_retriever.query_similar_namespaces(
                self.context_index,
                question,
            )
        except Exception as e:
            logger.error(f"Error querying portfolio context: {e}", exc_info=True)

        return context
