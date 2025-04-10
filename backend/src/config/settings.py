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
