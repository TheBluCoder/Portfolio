"""Build chat queries, prompts, and model history for the portfolio bot."""

import json
from typing import TYPE_CHECKING, Any

from google.genai import types

from src.config.settings import CHAT_HISTORY_MAX_TURNS
from src.models.schemas import Message
from src.services.chat_follow_up import clamp_user_message, extract_selected_project_context

if TYPE_CHECKING:
    from google.genai.types import ContentOrDict
else:
    ContentOrDict = Any


class ChatPromptBuilder:
    """Create topic-gate queries, retrieval queries, prompts, and history."""

    def build_topic_gate_query(self, latest_question: str) -> str:
        current_question = " ".join(clamp_user_message(latest_question).split())
        return f"Current question: {current_question}"

    def build_retrieval_query(
        self,
        context: list[Message] | None,
        latest_question: str,
        resolved_question: str,
    ) -> str:
        selected_project = extract_selected_project_context(context)
        base_query = resolved_question or latest_question
        if not selected_project:
            return base_query[:1000]

        return (
            f"{base_query}\n\n"
            "Selected project context:\n"
            f"{selected_project}"
        )[:1000]

    def build_generation_prompt(
        self,
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

    def build_chat_history(
        self,
        context: list[Message] | None,
        max_turns: int = CHAT_HISTORY_MAX_TURNS,
    ) -> list[ContentOrDict]:
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


def compact_context(retrieved_context: dict[str, Any]) -> str:
    """Serialize retrieved context and cap its size before prompt construction."""
    return json.dumps(retrieved_context, default=str, ensure_ascii=False)[:8000]
