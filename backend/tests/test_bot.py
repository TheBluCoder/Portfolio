import unittest
from unittest.mock import AsyncMock, Mock, patch

from src.models.schemas import Message
from src.services import Bot
from src.services.topic_gate import OFF_TOPIC_RESPONSE, TopicGateResult


class BotTests(unittest.IsolatedAsyncioTestCase):
    async def test_off_topic_question_skips_retrieval_and_llm(self) -> None:
        context = [Message(type="human", content="What is the capital of France?")]
        context_retriever = AsyncMock()
        topic_gate = AsyncMock()
        topic_gate.check.return_value = TopicGateResult(accepted=False, score=0.01)
        bot_service = Bot.BotService(
            context_retriever=context_retriever,
            topic_gate=topic_gate,
        )

        with patch("src.services.Bot.client") as client:
            response = await bot_service.generate_response(context)

        self.assertEqual(response, OFF_TOPIC_RESPONSE)
        context_retriever.query_similar_namespaces.assert_not_awaited()
        client.chats.create.assert_not_called()

    async def test_on_topic_question_retrieves_context_and_calls_llm_once(self) -> None:
        context = [Message(type="human", content="Tell me about Ikeoluwa's projects")]
        context_retriever = AsyncMock()
        context_retriever.query_similar_namespaces.return_value = {"default": "ctx"}
        topic_gate = AsyncMock()
        topic_gate.check.return_value = TopicGateResult(accepted=True, score=0.5)
        bot_service = Bot.BotService(
            context_retriever=context_retriever,
            topic_gate=topic_gate,
        )

        with patch("src.services.Bot.client") as client:
            chat = Mock()
            chat.send_message.return_value = Mock(text="Answer")
            client.chats.create.return_value = chat

            response = await bot_service.generate_response(context)

        self.assertEqual(response, "Answer")
        context_retriever.query_similar_namespaces.assert_awaited_once()
        client.chats.create.assert_called_once()
        chat.send_message.assert_called_once()

    def test_chat_history_skips_leading_ai_greeting(self) -> None:
        context = [
            Message(type="ai", content="Hi, ask me anything."),
            Message(type="human", content="Tell me about Ikeoluwa."),
            Message(type="ai", content="Sure."),
            Message(type="human", content="What projects has he built?"),
        ]

        history = Bot.build_chat_history(context)

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].role, "user")
        self.assertEqual(history[1].role, "model")

    def test_routing_query_includes_recent_project_context(self) -> None:
        context = [
            Message(
                type="human",
                content=(
                    "The user is viewing this project:\n"
                    "Project name: Citation Generation System\n"
                    "Description: AI citation platform"
                ),
            ),
            Message(
                type="ai",
                content="Ike used a microservices architecture for the project.",
            ),
            Message(
                type="human",
                content="Why did he choose that over a monolith?",
            ),
        ]

        routing_query = Bot.build_routing_query(
            context,
            "Why did he choose that over a monolith?",
        )

        self.assertIn("Why did he choose that over a monolith?", routing_query)
        self.assertIn("Selected project: The user is viewing this project", routing_query)
        self.assertIn("Citation Generation System", routing_query)
        self.assertIn("microservices architecture", routing_query)

    def test_retrieval_query_uses_selected_project_without_full_chat(self) -> None:
        context = [
            Message(
                type="human",
                content=(
                    "The user is viewing this project:\n"
                    "Project name: Citation Generation System\n"
                    "Description: AI citation platform"
                ),
            ),
            Message(
                type="ai",
                content="Ike used a microservices architecture for the project.",
            ),
            Message(
                type="human",
                content="Why did he choose that over a monolith?",
            ),
        ]

        retrieval_query = Bot.build_retrieval_query(
            context,
            "Why did he choose that over a monolith?",
        )

        self.assertIn("Why did he choose that over a monolith?", retrieval_query)
        self.assertIn("Citation Generation System", retrieval_query)
        self.assertNotIn("microservices architecture", retrieval_query)
        self.assertLessEqual(len(retrieval_query), 1000)


if __name__ == "__main__":
    unittest.main()
