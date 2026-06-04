import dotenv
import json
from typing import Any

from src.config.settings import GOOGLE_API_KEY, GEMINI_MODEL, PORTFOLIO_CONTEXT_INDEX
from src.config.log_config import setup_logging
from src.config.prompts import SYSTEM_PROMPT
from src.services.pinecone_service import PineconeService 
from langchain_google_genai import ChatGoogleGenerativeAI
from src.models.schemas import Message
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from src.services.topic_gate import OFF_TOPIC_RESPONSE, TopicGate


logger = setup_logging(__file__)
dotenv.load_dotenv() # Load environment variables early

# --- LLM Configuration ---

# Configure the LLM, passing the *Vertex AI* grounding tool to the constructor
llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL or "gemini-pro", # Using gemini-pro as flash might have limitations
    google_api_key=GOOGLE_API_KEY,
    temperature=0.5,
    top_p=0.3,
)

# --- Core Logic ---

async def format_context(context: list[Message] | None) -> list[HumanMessage | AIMessage]:
    formatted_context: list[HumanMessage | AIMessage] = []
    for msg in context or []:
        if msg.type == "human":
            formatted_context.append(HumanMessage(content=msg.content))
        elif msg.type == "ai":
             formatted_context.append(AIMessage(content=msg.content))
    return formatted_context

async def generate_response(context: list[Message] | None = None) -> str:
    latest_question = next(
        (msg.content for msg in reversed(context or []) if msg.type == "human"),
        "",
    )
    gate_result = await TopicGate().check(latest_question)
    if not gate_result.accepted:
        return OFF_TOPIC_RESPONSE

    retrieved_context = await retrieve_context(latest_question)
    messages: list[SystemMessage | HumanMessage | AIMessage] = [
        SystemMessage(content=SYSTEM_PROMPT),
        SystemMessage(content=build_context_prompt(retrieved_context)),
    ]
    formatted_msg = await format_context(context)
    messages.extend(formatted_msg)

    try:
        response: AIMessage = llm.invoke(messages)
        logger.info("LLM response generated after deterministic retrieval.")
        return response.content if response.content else "No content in response."

    except Exception as e:
        logger.error(f"Error during generation or tool handling: {e}", exc_info=True) # Log traceback
        return "An error occurred while generating the response."


async def retrieve_context(question: str) -> dict[str, Any]:
    pc = PineconeService()
    context: dict[str, Any] = {"index": PORTFOLIO_CONTEXT_INDEX, "results": None}

    try:
        context["results"] = await pc.query_similar(PORTFOLIO_CONTEXT_INDEX, question)
    except Exception as e:
        logger.error(f"Error querying portfolio context: {e}", exc_info=True)

    return context


def build_context_prompt(retrieved_context: dict[str, Any]) -> str:
    return (
        "Use only the retrieved portfolio context below to answer. "
        "If the context does not contain enough detail, say what is known from the portfolio "
        "and avoid inventing facts.\n\n"
        f"{compact_context(retrieved_context)}"
    )


def compact_context(retrieved_context: dict[str, Any]) -> str:
    return json.dumps(retrieved_context, default=str, ensure_ascii=False)[:8000]
