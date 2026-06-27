"""Build chat queries, prompts, and model history for the portfolio bot."""

import json
from typing import TYPE_CHECKING, Any

from google.genai import types

from src.config.settings import CHAT_HISTORY_MAX_TURNS
from src.models.schemas import Message
from src.services.chat_context import extract_selected_project_context

if TYPE_CHECKING:
    from google.genai.types import ContentOrDict
else:
    ContentOrDict = Any


class ChatPromptBuilder:
    """Create retrieval queries, generation prompts, and Gemini chat history."""

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
            "or backend systems. Answer the exact question that was asked and stay within that scope. "
            "Do not volunteer adjacent details, caveats, or follow-up suggestions unless they are required "
            "to answer correctly. If the notes do not contain enough detail to answer the asked question, "
            "say that briefly and stop. Match the depth of the question: simple status, link, or availability "
            "questions should be brief, while architecture, design choices, tradeoffs, or story-behind-the-project "
            "questions can be more detailed but should stay on the requested layer. "
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
