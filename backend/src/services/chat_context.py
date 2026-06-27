"""Shared chat context helpers."""

from src.models.schemas import CHAT_USER_MESSAGE_MAX_LENGTH, Message


def clamp_user_message(text: str) -> str:
    """Defensively cap human-message length before routing, retrieval, and generation."""
    return text[:CHAT_USER_MESSAGE_MAX_LENGTH]


def extract_selected_project_context(context: list[Message] | None) -> str:
    """Return the synthetic selected-project message from a conversation, if present."""
    for msg in context or []:
        content = " ".join(msg.content.split())
        if content.startswith("The user is viewing this project:"):
            return content
    return ""
