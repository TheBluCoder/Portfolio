import unittest
from unittest.mock import AsyncMock, Mock, patch

from src.models.schemas import Message
from src.services import Bot
from src.services.chat_prompting import ChatPromptBuilder
from src.services.chat_resolver import ChatResolution


async def _fake_stream(*texts: str):
    """Async generator that yields mock chunks for send_message_stream."""
    for text in texts:
        yield Mock(text=text)


class BotTests(unittest.IsolatedAsyncioTestCase):
    def _bot_service(self, context_retriever: AsyncMock, chat_resolver: AsyncMock) -> Bot.BotService:
        return Bot.BotService(
            context_retriever=context_retriever,
            prompt_builder=ChatPromptBuilder(),
            chat_resolver=chat_resolver,
        )

    async def test_off_topic_question_skips_retrieval_and_llm(self) -> None:
        context = [Message(type="human", content="What is the weather today?")]
        context_retriever = AsyncMock()
        chat_resolver = AsyncMock()
        chat_resolver.resolve.return_value = ChatResolution(
            relevant=False,
            standalone_question="What is the weather today?",
            reason="weather is outside portfolio scope",
        )
        bot_service = self._bot_service(context_retriever, chat_resolver)

        with patch("src.services.Bot.client") as client:
            response = await bot_service.generate_response(context)

        self.assertEqual(response, Bot.OFF_TOPIC_RESPONSE)
        chat_resolver.resolve.assert_awaited_once_with(context, "What is the weather today?")
        context_retriever.query_similar_namespaces.assert_not_awaited()
        client.aio.chats.create.assert_not_called()

    async def test_relevant_question_retrieves_context_and_calls_llm_once(self) -> None:
        context = [Message(type="human", content="Tell me about Ikeoluwa's projects")]
        context_retriever = AsyncMock()
        context_retriever.query_similar_namespaces.return_value = {"default": "ctx"}
        chat_resolver = AsyncMock()
        chat_resolver.resolve.return_value = ChatResolution(
            relevant=True,
            standalone_question="Tell me about Ikeoluwa's projects",
            reason="portfolio question",
        )
        bot_service = self._bot_service(context_retriever, chat_resolver)

        with patch("src.services.Bot.client") as client:
            chat = Mock()
            chat.send_message_stream = AsyncMock(return_value=_fake_stream("Answer"))
            client.aio.chats.create.return_value = chat

            response = await bot_service.generate_response(context)

        self.assertEqual(response, "Answer")
        context_retriever.query_similar_namespaces.assert_awaited_once()
        client.aio.chats.create.assert_called_once()
        chat.send_message_stream.assert_awaited_once()

    async def test_follow_up_uses_resolver_standalone_question_for_retrieval(self) -> None:
        context = [
            Message(
                type="human",
                content=(
                    "The user is viewing this project:\n"
                    "Project name: AI Chat Exporter\n"
                    "Description: Browser extension"
                ),
            ),
            Message(type="human", content="Tell me something interesting about this project"),
            Message(type="ai", content="It uses a modular scraper architecture."),
            Message(type="human", content="Oh interesting, and how was it implemented?"),
        ]
        context_retriever = AsyncMock()
        context_retriever.query_similar_namespaces.return_value = {"default": "ctx"}
        chat_resolver = AsyncMock()
        chat_resolver.resolve.return_value = ChatResolution(
            relevant=True,
            standalone_question=(
                "How was the modular scraper architecture in AI Chat Exporter implemented?"
            ),
            reason="follow-up about selected project implementation",
        )
        bot_service = self._bot_service(context_retriever, chat_resolver)

        with patch("src.services.Bot.client") as client:
            chat = Mock()
            chat.send_message_stream = AsyncMock(
                return_value=_fake_stream("Implemented with platform scrapers.")
            )
            client.aio.chats.create.return_value = chat

            response = await bot_service.generate_response(context)

        self.assertEqual(response, "Implemented with platform scrapers.")
        retrieval_query = context_retriever.query_similar_namespaces.await_args.args[1]
        self.assertIn("How was the modular scraper architecture", retrieval_query)
        self.assertIn("AI Chat Exporter", retrieval_query)
        self.assertIn("Selected project context:", retrieval_query)
        self.assertLessEqual(len(retrieval_query), 1000)

    def test_chat_history_skips_leading_ai_greeting(self) -> None:
        context = [
            Message(type="ai", content="Hi, ask me anything."),
            Message(type="human", content="Tell me about Ikeoluwa."),
            Message(type="ai", content="Sure."),
            Message(type="human", content="What projects has he built?"),
        ]

        history = ChatPromptBuilder().build_chat_history(context)

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

        history = ChatPromptBuilder().build_chat_history(context, max_turns=1)

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].parts[0].text, "Question two")
        self.assertEqual(history[1].parts[0].text, "Answer two")

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

        retrieval_query = ChatPromptBuilder().build_retrieval_query(
            context,
            "Why did he choose that over a monolith?",
            "Why did Ike choose microservices for Citation Generation System?",
        )

        self.assertIn("Why did Ike choose microservices", retrieval_query)
        self.assertIn("Citation Generation System", retrieval_query)
        self.assertLessEqual(len(retrieval_query), 1000)


if __name__ == "__main__":
    unittest.main()
