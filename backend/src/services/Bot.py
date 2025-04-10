import asyncio
import dotenv
from typing import Optional, List

from src.config.settings import GOOGLE_API_KEY, GEMINI_MODEL
from src.config.log_config import setup_logging
from src.config.prompts import SYSTEM_PROMPT
from langchain_core.tools import tool
from src.services.pinecone_service import PineconeService 
from langchain_google_genai import ChatGoogleGenerativeAI
from src.models.schemas import Message
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolCall, ToolMessage 
from src.services.WebSearcher import WebSearcher


logger = setup_logging(__file__)
dotenv.load_dotenv() # Load environment variables early

# --- Tool Definitions ---

# 1. LangChain Tool (for explicit calling)
@tool
async def query_vector_db(query: str, index_name: str) -> str:
    """Queries the vector database for information about my software development projects or about me.
    There is a special index called aboutme that contains all information about me.
    The database only contains indexes named after the projects. e.g., citeme project will have an index called citeme.

    Args:
        query (str): The query to search the vector database with.
        index_name (str): The name of the index to search (essentially the project name).

    Returns:
        str: The response from the vector database.
    """
    pc = PineconeService() # Get the singleton instance (already initialized)
    logger.info(f"Querying vector DB index '{index_name}' with query: '{query}'")
    try:
        response = await pc.query_similar(index_name, query)
        logger.info(f"Vector DB Response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error querying vector DB: {e}", exc_info=True)
        return f"Error querying vector database: {e}"
    
@tool
async def query_about_me(query: str) -> str:
    """Queries the vector database for information about me(ikeoluwa)."""
    pc = PineconeService()
    return pc.query_similar("aboutme", query)
    
@tool
async def list_indexes() -> str:
    """Lists all the indexes in the vector database."""
    pc = PineconeService()
    return pc.list_all_indexes()

@tool
async def google_search_retrieval_tool(query: str) -> str:
    """Use Google Search to retrieve information.
    This tool is used to retrieve information from the internet and should be used if the user's query is not about my software development projects or about me.

    Args:
        query (str): The query to search Google with.

    Returns:
        str: The response from Google Search.
    """
    web_searcher = WebSearcher()
    return web_searcher.search(query)

# --- LLM Configuration ---

# Configure the LLM, passing the *Vertex AI* grounding tool to the constructor
llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL or "gemini-pro", # Using gemini-pro as flash might have limitations
    google_api_key=GOOGLE_API_KEY,
    temperature=0.5,
    top_p=0.3,
)

# --- Core Logic ---

async def format_context(context: list[Message]) -> list[HumanMessage | AIMessage]: # Use Union typing
    formatted_context = []
    for msg in context:
        if msg.type == "human":
            formatted_context.append(HumanMessage(content=msg.content))
        elif msg.type == "ai":
             formatted_context.append(AIMessage(content=msg.content))
    print("formatted_context",formatted_context)
    return formatted_context

# This function handles calls to *LangChain* tools bound via bind_tools
async def handle_langchain_tool_call(tool_call: ToolCall) -> ToolMessage:
    tool_name = tool_call['name']
    args = tool_call['args']
    logger.info(f"Executing LangChain tool: {tool_name} with args: {args}")

    # Find the corresponding LangChain tool function
    available_tools = {"query_vector_db": query_vector_db, "google_search_retrieval_tool": google_search_retrieval_tool}

    if tool_name in available_tools:
        try:
            tool_func = available_tools[tool_name]
            # Use ainvoke consistently for all tools
            observation = await tool_func.ainvoke(args)
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            observation = f"Error executing tool {tool_name}: {e}"
    else:
        logger.error(f"Unknown tool called: {tool_name}")
        observation = f"Error: Tool '{tool_name}' not found."

    # Return a ToolMessage containing the observation
    return ToolMessage(content=str(observation), tool_call_id=tool_call['id'])


async def generate_response(context: Optional[List[Message]] = None) -> str:
    messages: List[SystemMessage | HumanMessage | AIMessage | ToolMessage] = [ # Type hint for clarity
        SystemMessage(content=SYSTEM_PROMPT),
        # Add formatted context history BEFORE the current prompt
    ]
    formatted_msg = await format_context(context)
    messages.extend(formatted_msg)
    print("messages",messages)

    try:
        # Bind the *LangChain* tool(s) for explicit function calling
        # The grounding tool is already configured in the LLM constructor
        langchain_tools = [query_vector_db, google_search_retrieval_tool]
        llm_w_langchain_tools = llm.bind_tools(langchain_tools) # Only bind LangChain tools here

        # Initial invocation
        response: AIMessage = llm_w_langchain_tools.invoke(messages)
        logger.info(f"Initial LLM Response: {response}")

        # Handle potential LangChain tool calls
        while response.tool_calls:
            logger.info(f"Detected tool calls: {response.tool_calls}")
            messages.append(response) # Add the AI message with tool calls to history
            tool_results = await asyncio.gather(
                # No longer need to pass pc
                *(handle_langchain_tool_call(tc) for tc in response.tool_calls)
            )
            messages.extend(tool_results) # Add tool results to history

            # Invoke again with tool results
            logger.info("Re-invoking LLM with tool results...")
            response = llm_w_langchain_tools.invoke(messages)

        # If no tool calls or after handling them, return the final content
        return response.content if response.content else "No content in response."

    except Exception as e:
        logger.error(f"Error during generation or tool handling: {e}", exc_info=True) # Log traceback
        return "An error occurred while generating the response."


if __name__ == "__main__":
    async def main():
        # The singleton is now managed by the lifespan in the main app
        # Running this standalone would require separate initialization/cleanup
        # or relying on the global singleton state which might be risky for tests.
        user_prompt = input("Enter a prompt: ")
        response1 = await generate_response(user_prompt)
        print(f"Response 1: {response1}")
        # ... other examples ...
    asyncio.run(main())