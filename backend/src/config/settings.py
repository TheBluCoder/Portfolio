from dotenv import load_dotenv
import os
from pinecone import ServerlessSpec

# Load environment variables
load_dotenv()


def _parse_origins(raw_value: str | None) -> list[str]:
    """Parse a comma-separated origin list and normalize trailing slashes."""
    if not raw_value:
        return []
    return [origin.strip().rstrip("/") for origin in raw_value.split(",") if origin.strip()]

# API Keys and Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite"
CHAT_HISTORY_MAX_TURNS = int(os.getenv("CHAT_HISTORY_MAX_TURNS", "6"))
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "TheBluCoder")
GITHUB_PROJECT_TOPIC = os.getenv("GITHUB_PROJECT_TOPIC", "portfolio")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
AZURE_TABLE_CONNECTION_STRING = os.getenv("AZURE_TABLE_CONNECTION_STRING")
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "12"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "false").lower() == "true"
LOG_DIR = os.getenv("LOG_DIR", "logs")
PORTFOLIO_CONTEXT_INDEX = os.getenv("PORTFOLIO_CONTEXT_INDEX", "portfolio")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
RESUME_URL = os.getenv("RESUME_URL")
CORS_ALLOWED_ORIGINS = _parse_origins(os.getenv("CORS_ALLOWED_ORIGINS"))

PINECONE_SPEC = ServerlessSpec(
    cloud="aws",
    region="us-east-1"
)

# Pinecone Service Configuration
DEFAULT_CHUNK_WORKERS = 4
PINECONE_BATCH_SIZE = 96
PINECONE_CHUNK_SIZE = 700
PINECONE_CHUNK_OVERLAP = 10
PINECONE_QUERY_TOP_K = 7
PINECONE_QUERY_TOP_N = 3
PINECONE_INDEX_TIMEOUT = 90

# Validate required environment variables
if not all([GOOGLE_API_KEY, PINECONE_API_KEY]):
    raise ValueError("Required API keys not found in environment variables")
