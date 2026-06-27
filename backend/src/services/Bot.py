"""Generate portfolio-grounded chat responses with topic gating and retrieval."""

import dotenv
import json
from collections.abc import Awaitable
import re
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
from src.models.schemas import CHAT_USER_MESSAGE_MAX_LENGTH, Message
from src.services.topic_gate import OFF_TOPIC_RESPONSE, TopicGateResult

if TYPE_CHECKING:
    from google.genai.chats import AsyncChat
    from google.genai.types import ContentOrDict
else:
    AsyncChat = Any
    ContentOrDict = Any


logger = setup_logging(filename=__file__)
dotenv.load_dotenv() # Load environment variables early

FOLLOW_UP_MAX_TOKENS = 12
FOLLOW_UP_USER_CHAR_LIMIT = 300
ROUTING_PROJECT_CHAR_LIMIT = 300
FOLLOW_UP_USER_TURN_LIMIT = 3
FOLLOW_UP_MIN_SCORE = 3
FOLLOW_UP_SHAPE_PHRASES = (
    "tell me about it",
    "tell me more",
    "what about",
    "how about",
    "go deeper",
    "explain that",
    "expand on that",
    "more on that",
    "and the",
)
FOLLOW_UP_REFERENTIAL_WORDS = {
    "it",
    "its",
    "that",
    "this",
    "those",
    "them",
    "they",
    "one",
    "ones",
    "there",
}
FOLLOW_UP_STARTERS = {"and", "also", "then", "so", "what", "how"}
SUBJECT_HINT_WORDS = {
    "project",
    "app",
    "backend",
    "frontend",
    "stack",
    "deployment",
    "experience",
    "role",
    "resume",
    "portfolio",
    "repo",
    "github",
    "site",
}

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
        latest_question = clamp_user_message(latest_question)
        gate_query = build_topic_gate_query(latest_question)
        gate_result = await self.topic_gate.check(gate_query)
        resolved_query = latest_question

        if not gate_result.accepted:
            follow_up_query = build_follow_up_gate_query(context, latest_question)
            if not follow_up_query:
                return OFF_TOPIC_RESPONSE

            follow_up_result = await self.topic_gate.check(follow_up_query)
            if not follow_up_result.accepted:
                return OFF_TOPIC_RESPONSE

            resolved_query = follow_up_query

        retrieval_query = build_retrieval_query(context, latest_question, resolved_query)
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


def build_topic_gate_query(latest_question: str) -> str:
    """Gate the latest user question on its own before considering follow-up repair."""
    current_question = " ".join(latest_question.split())
    return f"Current question: {current_question}"


def build_retrieval_query(
    context: list[Message] | None,
    latest_question: str,
    resolved_question: str,
) -> str:
    """Add selected-project and resolved-follow-up context to semantic retrieval."""
    selected_project = extract_selected_project_context(context)
    base_query = resolved_question or latest_question
    if not selected_project:
        return base_query[:1000]

    return (
        f"{base_query}\n\n"
        "Selected project context:\n"
        f"{selected_project}"
    )[:1000]


def build_follow_up_gate_query(
    context: list[Message] | None,
    latest_question: str,
) -> str | None:
    """Resolve vague follow-ups against recent user turns without using assistant replies."""
    normalized_latest = normalize_message(latest_question)
    if not is_follow_up_shaped(normalized_latest):
        return None

    previous_user_turns = collect_previous_user_turns(context)
    if not previous_user_turns:
        return None

    latest_tokens = tokenize(normalized_latest)
    referential = contains_referential_signal(latest_tokens, normalized_latest)
    candidate_scores: list[tuple[int, str]] = []

    for offset, previous_turn in enumerate(reversed(previous_user_turns[-FOLLOW_UP_USER_TURN_LIMIT:])):
        previous_normalized = normalize_message(previous_turn)
        if not previous_normalized or is_follow_up_shaped(previous_normalized):
            continue

        previous_tokens = tokenize(previous_normalized)
        score = 0

        if referential and has_subject_hint(previous_tokens):
            score += 3

        overlap = latest_tokens & previous_tokens
        score += min(len(overlap), 2)

        if latest_tokens & SUBJECT_HINT_WORDS:
            score += 2

        if contains_referential_signal(previous_tokens, previous_normalized):
            score -= 2

        score += FOLLOW_UP_USER_TURN_LIMIT - offset

        candidate_scores.append((score, previous_turn))

    if not candidate_scores:
        return None

    best_score, best_turn = max(candidate_scores, key=lambda item: item[0])
    if best_score < FOLLOW_UP_MIN_SCORE:
        logger.info(
            "Follow-up fallback skipped: latest=%r best_score=%s candidates=%s",
            latest_question,
            best_score,
            candidate_scores,
        )
        return None

    selected_project = extract_selected_project_context(context)
    query_parts = [f"Previous user topic: {best_turn[:FOLLOW_UP_USER_CHAR_LIMIT]}"]
    if selected_project:
        query_parts.append(f"Selected project: {selected_project[:ROUTING_PROJECT_CHAR_LIMIT]}")
    query_parts.append(f"Follow-up question: {normalized_latest}")
    resolved_query = "\n".join(query_parts)
    logger.info(
        "Follow-up fallback applied: latest=%r best_score=%s resolved_query=%r",
        latest_question,
        best_score,
        resolved_query,
    )
    return resolved_query


def extract_selected_project_context(context: list[Message] | None) -> str:
    """Return the synthetic selected-project message from a conversation, if present."""
    for msg in context or []:
        content = " ".join(msg.content.split())
        if content.startswith("The user is viewing this project:"):
            return content
    return ""


def collect_previous_user_turns(context: list[Message] | None) -> list[str]:
    """Return prior user turns, excluding synthetic selected-project messages and the latest turn."""
    user_turns: list[str] = []
    for msg in context or []:
        if msg.type != "human":
            continue
        content = " ".join(msg.content.split())
        if not content or content.startswith("The user is viewing this project:"):
            continue
        user_turns.append(clamp_user_message(content))

    return user_turns[:-1] if user_turns else []


def normalize_message(text: str) -> str:
    """Collapse whitespace and lowercase chat text for follow-up heuristics."""
    return " ".join(clamp_user_message(text).lower().split())


def clamp_user_message(text: str) -> str:
    """Defensively cap human-message length before topic gating and retrieval."""
    return text[:CHAT_USER_MESSAGE_MAX_LENGTH]


def tokenize(text: str) -> set[str]:
    """Extract simple word tokens for overlap scoring."""
    return set(re.findall(r"[a-z0-9]+", text))


def is_follow_up_shaped(text: str) -> bool:
    """Detect short referential turns that likely need previous-user-turn context."""
    if not text:
        return False

    tokens = text.split()
    if len(tokens) <= FOLLOW_UP_MAX_TOKENS and contains_referential_signal(set(tokens), text):
        return True

    if any(text.startswith(phrase) for phrase in FOLLOW_UP_SHAPE_PHRASES):
        return True

    return bool(tokens) and tokens[0] in FOLLOW_UP_STARTERS and len(tokens) <= FOLLOW_UP_MAX_TOKENS


def contains_referential_signal(tokens: set[str], text: str) -> bool:
    """Check for pronouns or short follow-up cues that imply missing antecedent context."""
    if tokens & FOLLOW_UP_REFERENTIAL_WORDS:
        return True

    return any(phrase in text for phrase in FOLLOW_UP_SHAPE_PHRASES)


def has_subject_hint(tokens: set[str]) -> bool:
    """Prefer prior turns that mention a concrete portfolio subject or project detail."""
    if tokens & SUBJECT_HINT_WORDS:
        return True

    return len(tokens) >= 4


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
