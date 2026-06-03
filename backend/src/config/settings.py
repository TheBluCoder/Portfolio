from dotenv import load_dotenv
import os
from pinecone import ServerlessSpec

# Load environment variables
load_dotenv()

# API Keys and Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GPSE_API_KEY = os.getenv("GPSE_API_KEY")
CX = os.getenv("CX")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "TheBluCoder")
GITHUB_PROJECT_TOPIC = os.getenv("GITHUB_PROJECT_TOPIC", "portfolio")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
AZURE_TABLE_CONNECTION_STRING = os.getenv("AZURE_TABLE_CONNECTION_STRING")
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "12"))
TOPIC_GATE_THRESHOLD = float(os.getenv("TOPIC_GATE_THRESHOLD", "0.08"))
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

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
