import math
import re
from collections import Counter

from src.config.settings import TOPIC_GATE_THRESHOLD

OFF_TOPIC_RESPONSE = (
    "I can only answer questions about Ikeoluwa, his experience, skills, projects, "
    "education, interests, and portfolio."
)

ON_TOPIC_SEEDS = [
    "what projects have you worked on",
    "tell me about your software projects",
    "what is your tech stack",
    "what programming languages do you know",
    "tell me about your experience",
    "what is your education",
    "what internships have you completed",
    "what kind of developer are you",
    "tell me about Ikeoluwa",
    "what are your interests and hobbies",
    "how can I contact you",
    "what is in your resume",
]

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "do",
    "does",
    "for",
    "has",
    "have",
    "how",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "where",
    "who",
    "why",
}


class TopicGate:
    def __init__(
        self,
        seeds: list[str] | None = None,
        threshold: float = TOPIC_GATE_THRESHOLD,
    ) -> None:
        self.seeds = seeds or ON_TOPIC_SEEDS
        self.threshold = threshold
        self.seed_vectors = [self._vectorize(seed) for seed in self.seeds]

    def is_on_topic(self, question: str) -> bool:
        if not question or not question.strip():
            return False
        return self.score(question) >= self.threshold

    def score(self, question: str) -> float:
        query_vector = self._vectorize(question)
        if not query_vector:
            return 0.0
        return max(self._cosine_similarity(query_vector, seed) for seed in self.seed_vectors)

    def _vectorize(self, text: str) -> Counter[str]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        return Counter(token for token in tokens if token not in STOPWORDS)

    def _cosine_similarity(self, left: Counter[str], right: Counter[str]) -> float:
        shared = set(left) & set(right)
        dot = sum(left[token] * right[token] for token in shared)
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if not left_norm or not right_norm:
            return 0.0
        return dot / (left_norm * right_norm)
