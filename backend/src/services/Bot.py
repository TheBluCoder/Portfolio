import dotenv
import json
from collections.abc import Awaitable
from typing import TYPE_CHECKING, Any, Protocol

from src.config.settings import GOOGLE_API_KEY, GEMINI_MODEL, PORTFOLIO_CONTEXT_INDEX
from src.config.log_config import setup_logging
from src.config.prompts import SYSTEM_PROMPT
from google import genai
from google.genai import types
from src.models.schemas import Message
from src.services.topic_gate import OFF_TOPIC_RESPONSE, TopicGateResult

if TYPE_CHECKING:
    from google.genai.chats import Chat
    from google.genai.types import ContentOrDict
else:
    Chat = Any
    ContentOrDict = Any


logger = setup_logging(filename=__file__)
dotenv.load_dotenv() # Load environment variables early

# --- LLM Configuration ---

client = genai.Client(api_key=GOOGLE_API_KEY)
generation_config = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    temperature=0.5,
    top_p=0.3,
)

# --- Core Logic ---

class ContextRetriever(Protocol):
    def query_similar(self, index_name: str, query: str) -> Awaitable[Any]: ...
    def query_similar_namespaces(self, index_name: str, query: str) -> Awaitable[dict[str, Any]]: ...


class QuestionGate(Protocol):
    def check(self, question: str) -> Awaitable[TopicGateResult]: ...


class BotService:
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
            chat: Chat = client.chats.create(
                model=GEMINI_MODEL,
                config=generation_config,
                history=history or None,
            )
            response = chat.send_message(prompt)
            logger.info("LLM response generated after deterministic retrieval.")
            return response.text if response.text else "No content in response."

        except Exception as e:
            logger.error(f"Error during generation or tool handling: {e}", exc_info=True)
            return "An error occurred while generating the response."

    async def retrieve_context(self, question: str) -> dict[str, Any]:
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
    return json.dumps(retrieved_context, default=str, ensure_ascii=False)[:8000]


def build_routing_query(context: list[Message] | None, latest_question: str) -> str:
    if not context:
        return latest_question

    selected_project: str | None = None
    previous_turns: list[str] = []
    for msg in context[:-1]:
        content = " ".join(msg.content.split())
        if not content:
            continue

        label = "User" if msg.type == "human" else "Assistant"
        if content.startswith("The user is viewing this project:"):
            selected_project = f"Selected project: {content}"
            continue
        previous_turns.append(f"{label}: {content}")

    context_parts = ([selected_project] if selected_project else []) + previous_turns[-4:]
    if not context_parts:
        return latest_question

    recent_context = "\n".join(context_parts)
    return (
        f"{latest_question}\n\n"
        "Use this recent chat/project context only to understand references in the question:\n"
        f"{recent_context}"
    )[:2400]


def build_retrieval_query(context: list[Message] | None, latest_question: str) -> str:
    selected_project = extract_selected_project_context(context)
    if not selected_project:
        return latest_question

    return (
        f"{latest_question}\n\n"
        "Selected project context:\n"
        f"{selected_project}"
    )[:1000]


def extract_selected_project_context(context: list[Message] | None) -> str:
    for msg in context or []:
        content = " ".join(msg.content.split())
        if content.startswith("The user is viewing this project:"):
            return content
    return ""


def build_chat_history(context: list[Message] | None) -> list[ContentOrDict]:
    history: list[ContentOrDict] = []
    seen_user_turn = False

    for msg in (context or [])[:-1]:
        if msg.type == "human":
            seen_user_turn = True
            history.append(types.UserContent(parts=[types.Part.from_text(text=msg.content)]))
        elif msg.type == "ai" and seen_user_turn:
            history.append(types.ModelContent(parts=[types.Part.from_text(text=msg.content)]))

    return history
