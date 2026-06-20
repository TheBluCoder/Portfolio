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
        client.aio.chats.create.assert_not_called()

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
            chat.send_message = AsyncMock(
                return_value=Mock(text="Answer", usage_metadata=None)
            )
            client.aio.chats.create.return_value = chat

            response = await bot_service.generate_response(context)

        self.assertEqual(response, "Answer")
        context_retriever.query_similar_namespaces.assert_awaited_once()
        client.aio.chats.create.assert_called_once()
        chat.send_message.assert_awaited_once()

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

    def test_chat_history_keeps_only_recent_completed_turns(self) -> None:
        context = [
            Message(type="human", content="Question one"),
            Message(type="ai", content="Answer one"),
            Message(type="human", content="Question two"),
            Message(type="ai", content="Answer two"),
            Message(type="human", content="Question three"),
        ]

        history = Bot.build_chat_history(context, max_turns=1)

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].parts[0].text, "Question two")
        self.assertEqual(history[1].parts[0].text, "Answer two")

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
        self.assertNotIn("Use this recent chat/project context", routing_query)

    def test_routing_query_bounds_each_context_component(self) -> None:
        latest_question = "Why " + ("exactly " * 80)
        selected_project = "The user is viewing this project: " + ("p" * 600)
        context = [
            Message(type="human", content=selected_project),
            Message(type="human", content="oldest message"),
            Message(type="ai", content="older response"),
            Message(type="human", content="u" * 400),
            Message(type="ai", content="a" * 400),
            Message(type="human", content="  newer \n question  "),
            Message(type="ai", content="newer response"),
            Message(type="ai", content="   \n  "),
            Message(type="human", content=latest_question),
        ]

        routing_query = Bot.build_routing_query(context, latest_question)
        lines = routing_query.splitlines()

        self.assertEqual(lines[0], f"Current question: {latest_question.strip()}")
        self.assertEqual(
            len(lines[1].removeprefix("Selected project: ")),
            Bot.ROUTING_PROJECT_CHAR_LIMIT,
        )
        self.assertNotIn("oldest message", routing_query)
        self.assertNotIn("older response", routing_query)
        self.assertIn(f"User: {'u' * Bot.ROUTING_USER_CHAR_LIMIT}", lines)
        self.assertIn(f"Assistant: {'a' * Bot.ROUTING_ASSISTANT_CHAR_LIMIT}", lines)
        self.assertIn("User: newer question", lines)
        self.assertIn("Assistant: newer response", lines)
        self.assertNotIn("Assistant: ", lines)

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
