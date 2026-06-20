"""Generate portfolio-grounded chat responses with topic gating and retrieval."""

import dotenv
import json
from collections.abc import Awaitable
from typing import TYPE_CHECKING, Any, Protocol

from src.config.settings import (
    CHAT_HISTORY_MAX_TURNS,
    GEMINI_MODEL,
    GOOGLE_API_KEY,
    PORTFOLIO_CONTEXT_INDEX,
)
from src.config.log_config import setup_logging
from src.config.prompts import SYSTEM_PROMPT
from google import genai
from google.genai import types
from src.models.schemas import Message
from src.services.topic_gate import OFF_TOPIC_RESPONSE, TopicGateResult

if TYPE_CHECKING:
    from google.genai.chats import AsyncChat
    from google.genai.types import ContentOrDict
else:
    AsyncChat = Any
    ContentOrDict = Any


logger = setup_logging(filename=__file__)
dotenv.load_dotenv() # Load environment variables early

ROUTING_USER_CHAR_LIMIT = 300
ROUTING_ASSISTANT_CHAR_LIMIT = 240
ROUTING_PROJECT_CHAR_LIMIT = 300
ROUTING_MESSAGE_LIMIT = 4

# --- LLM Configuration ---

client = genai.Client(api_key=GOOGLE_API_KEY)
generation_config = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    temperature=0.5,
    top_p=0.3,
)

# --- Core Logic ---

class ContextRetriever(Protocol):
    """Required vector retrieval operations for the bot service."""

    def query_similar(self, index_name: str, query: str) -> Awaitable[Any]: ...
    def query_similar_namespaces(self, index_name: str, query: str) -> Awaitable[dict[str, Any]]: ...


class QuestionGate(Protocol):
    """Determine whether a question is within the portfolio's supported scope."""

    def check(self, question: str) -> Awaitable[TopicGateResult]: ...


class BotService:
    """Coordinate topic gating, context retrieval, and Gemini response generation."""

    def __init__(
        self,
        context_retriever: ContextRetriever,
        topic_gate: QuestionGate,
        context_index: str = PORTFOLIO_CONTEXT_INDEX,
    ) -> None:
        self.context_retriever = context_retriever
        self.topic_gate = topic_gate
        self.context_index = context_index

    async def generate_response(self, context: list[Message] | None = None) -> str:
        """Generate a grounded response for the latest human message in a conversation."""
        latest_question = next(
            (msg.content for msg in reversed(context or []) if msg.type == "human"),
            "",
        )
        routing_query = build_routing_query(context, latest_question)
        gate_result = await self.topic_gate.check(routing_query)
        if not gate_result.accepted:
            return OFF_TOPIC_RESPONSE

        retrieval_query = build_retrieval_query(context, latest_question)
        retrieved_context = await self.retrieve_context(retrieval_query)
        prompt = build_generation_prompt(retrieved_context, latest_question)
        history = build_chat_history(context)

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


def build_generation_prompt(
    retrieved_context: dict[str, Any],
    question: str,
) -> str:
    """Build the final grounded prompt from retrieved notes and the user's question."""
    return (
        "Answer using only the private notes below. "
        "Speak about Ikeoluwa in third person as Ikeoluwa or Ike. "
        "Do not write as if you are Ikeoluwa. "
        "Do not mention the notes, context, retrieval, indexes, RAG, vector databases, "
        "or backend systems. If the notes do not contain enough detail, be candid but "
        "helpful and lightly playful. Say what you do know, what is missing, and what "
        "the user can still ask about. Match the depth of the question: simple status, "
        "link, or availability questions should be brief, while architecture, design choices, "
        "tradeoffs, or story-behind-the-project questions can be more detailed. "
        "Do not say phrases like 'the notes say', 'the current "
        "information', 'project details confirm', or 'provided context'. Do not apologize.\n\n"
        f"Private notes:\n{compact_context(retrieved_context)}\n\n"
        f"User question:\n{question}"
    )


def compact_context(retrieved_context: dict[str, Any]) -> str:
    """Serialize retrieved context and cap its size before prompt construction."""
    return json.dumps(retrieved_context, default=str, ensure_ascii=False)[:8000]


def build_routing_query(context: list[Message] | None, latest_question: str) -> str:
    """Build compact declarative context for topic-gate embedding."""
    current_question = " ".join(latest_question.split())
    query_parts = [f"Current question: {current_question}"]
    if not context:
        return query_parts[0]

    selected_project: str | None = None
    previous_turns: list[str] = []
    for msg in context[:-1]:
        content = " ".join(msg.content.split())
        if not content:
            continue

        if content.startswith("The user is viewing this project:"):
            selected_project = content[:ROUTING_PROJECT_CHAR_LIMIT]
            continue

        if msg.type == "human":
            previous_turns.append(f"User: {content[:ROUTING_USER_CHAR_LIMIT]}")
        else:
            previous_turns.append(f"Assistant: {content[:ROUTING_ASSISTANT_CHAR_LIMIT]}")

    if selected_project:
        query_parts.append(f"Selected project: {selected_project}")
    query_parts.extend(previous_turns[-ROUTING_MESSAGE_LIMIT:])
    return "\n".join(query_parts)


def build_retrieval_query(context: list[Message] | None, latest_question: str) -> str:
    """Add selected-project context to the query used for semantic retrieval."""
    selected_project = extract_selected_project_context(context)
    if not selected_project:
        return latest_question

    return (
        f"{latest_question}\n\n"
        "Selected project context:\n"
        f"{selected_project}"
    )[:1000]


def extract_selected_project_context(context: list[Message] | None) -> str:
    """Return the synthetic selected-project message from a conversation, if present."""
    for msg in context or []:
        content = " ".join(msg.content.split())
        if content.startswith("The user is viewing this project:"):
            return content
    return ""


def build_chat_history(
    context: list[Message] | None,
    max_turns: int = CHAT_HISTORY_MAX_TURNS,
) -> list[ContentOrDict]:
    """Convert only the most recent completed turns into Gemini chat history."""
    history: list[ContentOrDict] = []
    seen_user_turn = False
    completed_messages = list((context or [])[:-1])

    if max_turns <= 0:
        return history

    completed_messages = completed_messages[-(max_turns * 2):]

    for msg in completed_messages:
        if msg.type == "human":
            seen_user_turn = True
            history.append(types.UserContent(parts=[types.Part.from_text(text=msg.content)]))
        elif msg.type == "ai" and seen_user_turn:
            history.append(types.ModelContent(parts=[types.Part.from_text(text=msg.content)]))

    return history
