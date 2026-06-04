import unittest
from unittest.mock import AsyncMock, Mock, patch

from src.models.schemas import Message
from src.services import Bot
from src.services.topic_gate import OFF_TOPIC_RESPONSE, TopicGateResult


class BotTests(unittest.IsolatedAsyncioTestCase):
    async def test_off_topic_question_skips_retrieval_and_llm(self) -> None:
        context = [Message(type="human", content="What is the capital of France?")]

        with (
            patch("src.services.Bot.TopicGate") as topic_gate,
            patch("src.services.Bot.retrieve_context", new=AsyncMock()) as retrieve_context,
            patch("src.services.Bot.client") as client,
        ):
            topic_gate.return_value.check = AsyncMock(
                return_value=TopicGateResult(accepted=False, score=0.01)
            )

            response = await Bot.generate_response(context)

        self.assertEqual(response, OFF_TOPIC_RESPONSE)
        retrieve_context.assert_not_awaited()
        client.models.generate_content.assert_not_called()

    async def test_on_topic_question_retrieves_context_and_calls_llm_once(self) -> None:
        context = [Message(type="human", content="Tell me about Ikeoluwa's projects")]

        with (
            patch("src.services.Bot.TopicGate") as topic_gate,
            patch(
                "src.services.Bot.retrieve_context",
                new=AsyncMock(return_value={"index": "aboutme", "results": "ctx"}),
            ),
            patch("src.services.Bot.client") as client,
        ):
            topic_gate.return_value.check = AsyncMock(
                return_value=TopicGateResult(accepted=True, score=0.5)
            )
            client.models.generate_content = Mock(return_value=Mock(text="Answer"))

            response = await Bot.generate_response(context)

        self.assertEqual(response, "Answer")
        client.models.generate_content.assert_called_once()


if __name__ == "__main__":
    unittest.main()
