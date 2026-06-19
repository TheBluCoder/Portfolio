import unittest

from src.services.topic_gate import TopicGate


class FakeVectorStore:
    def __init__(self, score: float) -> None:
        self.score = score

    async def query_similar(self, index_name: str, query: str) -> dict:
        return {"result": {"hits": [{"_id": "question-001", "_score": self.score}]}}

    def extract_best_score(self, results: dict) -> float:
        return results["result"]["hits"][0]["_score"]


class TopicGateTests(unittest.IsolatedAsyncioTestCase):
    async def test_accepts_personal_portfolio_question(self) -> None:
        pinecone = FakeVectorStore(score=0.4)
        gate = TopicGate(vector_store=pinecone, threshold=0.08)

        result = await gate.check("What projects has Ikeoluwa worked on?")

        self.assertTrue(result.accepted)

    async def test_rejects_unrelated_question(self) -> None:
        pinecone = FakeVectorStore(score=0.01)
        gate = TopicGate(vector_store=pinecone, threshold=0.08)

        result = await gate.check("What is the capital of France?")

        self.assertFalse(result.accepted)


if __name__ == "__main__":
    unittest.main()
