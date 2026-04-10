import os
from dotenv import load_dotenv

load_dotenv()

# API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-sonnet-4-20250514"

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "docs")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")

# Chunking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Retrieval
TOP_K = 5
