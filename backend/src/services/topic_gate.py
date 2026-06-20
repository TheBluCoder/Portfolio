"""Classify whether chat questions are supported by the portfolio knowledge base."""

from collections.abc import Awaitable
from dataclasses import dataclass
from typing import Any, Protocol

from src.config.log_config import setup_logging
from src.config.settings import TOPIC_GATE_INDEX, TOPIC_GATE_THRESHOLD

OFF_TOPIC_RESPONSE = (
    "Tiny detour detected. I’m best at questions about Ikeoluwa, his projects, "
    "skills, experience, education, interests, and portfolio. Ask me anything in that lane "
    "and I’ll happily put on the tiny detective hat."
)

logger = setup_logging(filename="topic_gate")

@dataclass(frozen=True)
class TopicGateResult:
    """Topic decision with the similarity score used to make it."""

    accepted: bool
    score: float


class TopicVectorStore(Protocol):
    """Vector-store operations required to score topic similarity."""

    def query_topic_similarity(self, query: str, index_name: str) -> Awaitable[float]: ...
    def query_similar(self, index_name: str, query: str) -> Awaitable[Any]: ...
    def extract_best_score(self, results: Any) -> float: ...


class TopicGate:
    """Accept questions whose best topic match meets the configured threshold."""

    def __init__(
        self,
        vector_store: TopicVectorStore,
        index_name: str = TOPIC_GATE_INDEX,
        threshold: float = TOPIC_GATE_THRESHOLD,
    ) -> None:
        self.vector_store = vector_store
        self.index_name = index_name
        self.threshold = threshold

    async def check(self, question: str) -> TopicGateResult:
        """Score a question and return a deterministic accept/reject decision."""
        if not question or not question.strip():
            return TopicGateResult(accepted=False, score=0.0)

        results = await self.vector_store.query_similar(self.index_name, question)
        score = self.vector_store.extract_best_score(results)
        accepted = score >= self.threshold
        logger.info(
            "Topic gate decision: accepted=%s score=%s threshold=%s scaled_score=%.2f "
            "scaled_threshold=%.2f query=%r matches=%s",
            accepted,
            f"{score:.8f}",
            f"{self.threshold:.8f}",
            score * 100000,
            self.threshold * 100000,
            question,
            summarize_matches(results),
        )
        return TopicGateResult(accepted=accepted, score=score)


def summarize_matches(results: Any) -> list[dict[str, Any]]:
    """Extract compact score and text previews from supported result shapes."""
    candidates = extract_candidates(results)
    summaries: list[dict[str, Any]] = []

    for candidate in candidates[:5]:
        if isinstance(candidate, dict):
            raw_fields = candidate.get("fields") or {}
            text = raw_fields.get("text") or candidate.get("text") or ""
            summaries.append(
                {
                    "id": candidate.get("id") or candidate.get("_id"),
                    "score": candidate.get("score") or candidate.get("_score"),
                    "scaled_score": scale_score(candidate.get("score") or candidate.get("_score")),
                    "text": str(text)[:160],
                }
            )
        else:
            raw_fields = getattr(candidate, "fields", {}) or {}
            text = raw_fields.get("text") if isinstance(raw_fields, dict) else ""
            summaries.append(
                {
                    "id": getattr(candidate, "id", None) or getattr(candidate, "_id", None),
                    "score": getattr(candidate, "score", None) or getattr(candidate, "_score", None),
                    "scaled_score": scale_score(
                        getattr(candidate, "score", None) or getattr(candidate, "_score", None)
                    ),
                    "text": str(text)[:160],
                }
            )

    return summaries


def scale_score(score: Any) -> float | None:
    """Scale a raw similarity score for human-readable diagnostic logging."""
    if score is None:
        return None
    return float(score) * 100000


def extract_candidates(results: Any) -> list[Any]:
    """Return match candidates from dictionary or Pinecone SDK response objects."""
    if isinstance(results, dict):
        result_obj = results.get("result")
        result_hits = result_obj.get("hits") if isinstance(result_obj, dict) else None
        raw_candidates = results.get("matches") or result_hits or results.get("hits") or []
    else:
        raw_candidates = (
            getattr(results, "matches", None)
            or getattr(getattr(results, "result", None), "hits", None)
            or getattr(results, "hits", None)
            or []
        )
    return list(raw_candidates) if isinstance(raw_candidates, list) else []
