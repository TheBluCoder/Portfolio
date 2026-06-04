from dataclasses import dataclass

from src.config.settings import TOPIC_GATE_INDEX, TOPIC_GATE_THRESHOLD
from src.services.pinecone_service import PineconeService

OFF_TOPIC_RESPONSE = (
    "I can only answer questions about Ikeoluwa, his experience, skills, projects, "
    "education, interests, and portfolio."
)

@dataclass(frozen=True)
class TopicGateResult:
    accepted: bool
    score: float


class TopicGate:
    def __init__(
        self,
        pinecone_service: PineconeService | None = None,
        index_name: str = TOPIC_GATE_INDEX,
        threshold: float = TOPIC_GATE_THRESHOLD,
    ) -> None:
        self.pinecone_service = pinecone_service or PineconeService()
        self.index_name = index_name
        self.threshold = threshold

    async def check(self, question: str) -> TopicGateResult:
        if not question or not question.strip():
            return TopicGateResult(accepted=False, score=0.0)

        score = await self.pinecone_service.query_topic_similarity(question, self.index_name)
        return TopicGateResult(accepted=score >= self.threshold, score=score)
