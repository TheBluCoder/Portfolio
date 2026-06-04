import unittest

from src.services.topic_gate import TopicGate


class TopicGateTests(unittest.TestCase):
    def test_accepts_personal_portfolio_question(self) -> None:
        gate = TopicGate(threshold=0.08)

        self.assertTrue(gate.is_on_topic("What projects has Ikeoluwa worked on?"))

    def test_rejects_unrelated_question(self) -> None:
        gate = TopicGate(threshold=0.08)

        self.assertFalse(gate.is_on_topic("What is the capital of France?"))


if __name__ == "__main__":
    unittest.main()
