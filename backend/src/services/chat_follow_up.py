"""Resolve vague follow-up chat turns against recent user messages."""

import re

from src.config.log_config import setup_logging
from src.models.schemas import CHAT_USER_MESSAGE_MAX_LENGTH, Message

logger = setup_logging(filename="chat_follow_up")

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


class ChatFollowUpResolver:
    """Convert vague follow-ups into standalone topic-gate queries."""

    def resolve(self, context: list[Message] | None, latest_question: str) -> str | None:
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
