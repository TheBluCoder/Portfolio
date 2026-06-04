import unittest
from unittest.mock import AsyncMock

from src.services.topic_gate import TopicGate


class TopicGateTests(unittest.IsolatedAsyncioTestCase):
    async def test_accepts_personal_portfolio_question(self) -> None:
        pinecone = AsyncMock()
        pinecone.query_topic_similarity.return_value = 0.4
        gate = TopicGate(pinecone_service=pinecone, threshold=0.08)

        result = await gate.check("What projects has Ikeoluwa worked on?")

        self.assertTrue(result.accepted)

    async def test_rejects_unrelated_question(self) -> None:
        pinecone = AsyncMock()
        pinecone.query_topic_similarity.return_value = 0.01
        gate = TopicGate(pinecone_service=pinecone, threshold=0.08)

        result = await gate.check("What is the capital of France?")

        self.assertFalse(result.accepted)


if __name__ == "__main__":
    unittest.main()
