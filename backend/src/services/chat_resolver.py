"""Resolve chat messages into relevance decisions and standalone portfolio questions."""

import json
from dataclasses import dataclass
from typing import Any

from google import genai
from google.genai import types

from src.config.log_config import setup_logging
from src.config.settings import GEMINI_MODEL, GOOGLE_API_KEY
from src.models.schemas import Message
from src.services.chat_context import clamp_user_message, extract_selected_project_context

logger = setup_logging(filename="chat_resolver")

RESOLVER_HISTORY_LIMIT = 6
RESOLVER_TEXT_LIMIT = 900

resolver_client = genai.Client(api_key=GOOGLE_API_KEY)
resolver_config = types.GenerateContentConfig(
    temperature=0,
    top_p=0.1,
    response_mime_type="application/json",
)


@dataclass(frozen=True)
class ChatResolution:
    """Structured decision returned by the relevance and follow-up resolver."""

    relevant: bool
    standalone_question: str
    reason: str = ""


class ChatResolver:
    """Use Gemini to decide chat relevance and rewrite follow-ups before retrieval."""

    async def resolve(self, context: list[Message] | None, latest_question: str) -> ChatResolution:
        prompt = build_resolver_prompt(context, latest_question)
        response = await resolver_client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=resolver_config,
        )
        resolution = parse_resolution(response.text or "", latest_question)
        logger.info(
            "Chat resolution: relevant=%s standalone_question=%r reason=%r",
            resolution.relevant,
            resolution.standalone_question,
            resolution.reason,
        )
        return resolution


def build_resolver_prompt(context: list[Message] | None, latest_question: str) -> str:
    """Build a small classifier/rewrite prompt that does not answer the user."""
    selected_project = extract_selected_project_context(context)
    recent_history = build_recent_history(context)
    latest = clamp_user_message(latest_question)

    return (
        "You are a strict routing helper for Ikeoluwa's portfolio chat.\n"
        "Decide whether the latest user message is relevant to Ikeoluwa, his projects, "
        "skills, experience, education, interests, hobbies, or the currently selected project.\n"
        "Use the recent conversation only to resolve follow-ups. Do not answer the user.\n"
        "If relevant, rewrite the latest message as a standalone question. If it is a follow-up "
        "about the selected project or a previous portfolio topic, include that subject in the rewrite.\n"
        "If it asks for unrelated general knowledge, weather, news, sports, coding help unrelated to "
        "Ikeoluwa's work, or personal information about someone else, mark it irrelevant.\n"
        "Return JSON only with keys: relevant, standalone_question, reason.\n\n"
        f"Selected project context:\n{selected_project or 'None'}\n\n"
        f"Recent conversation:\n{recent_history or 'None'}\n\n"
        f"Latest user message:\n{latest}"
    )


def build_recent_history(context: list[Message] | None) -> str:
    """Serialize recent visible turns for resolver context without flooding the first LLM call."""
    lines: list[str] = []
    visible_messages = [
        msg for msg in context or []
        if not msg.content.startswith("The user is viewing this project:")
    ]
    for msg in visible_messages[-RESOLVER_HISTORY_LIMIT:]:
        role = "User" if msg.type == "human" else "Assistant"
        content = " ".join(msg.content.split())[:RESOLVER_TEXT_LIMIT]
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def parse_resolution(raw_text: str, latest_question: str) -> ChatResolution:
    """Parse resolver JSON and fail closed if the model returns malformed output."""
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.warning("Malformed resolver JSON: %r", raw_text[:500])
        return ChatResolution(
            relevant=False,
            standalone_question=clamp_user_message(latest_question),
            reason="resolver returned malformed JSON",
        )

    if not isinstance(payload, dict):
        return ChatResolution(
            relevant=False,
            standalone_question=clamp_user_message(latest_question),
            reason="resolver returned a non-object payload",
        )

    relevant = bool(payload.get("relevant"))
    standalone_question = sanitize_standalone_question(payload, latest_question)
    reason = str(payload.get("reason") or "")[:300]
    return ChatResolution(
        relevant=relevant,
        standalone_question=standalone_question,
        reason=reason,
    )


def sanitize_standalone_question(payload: dict[str, Any], latest_question: str) -> str:
    """Keep resolver output bounded and fall back to the latest message when needed."""
    value = payload.get("standalone_question")
    if not isinstance(value, str) or not value.strip():
        return clamp_user_message(latest_question)
    return clamp_user_message(" ".join(value.split()))
