import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Project paths
BASE_DIR = Path(__file__).parent.parent
CACHE_DIR = BASE_DIR / "cache"
DB_PATH = CACHE_DIR / "papers.db"

# Ensure directories exist
CACHE_DIR.mkdir(exist_ok=True)
(CACHE_DIR / "pdfs").mkdir(exist_ok=True)
(CACHE_DIR / "faiss_index").mkdir(exist_ok=True)

# API Configuration
SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", None)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# LLM Settings
OLLAMA_MODEL = "mistral:7b"
OLLAMA_HOST = "http://localhost:11434"

# Search Settings
MAX_RESULTS_PER_SOURCE = 20
TOTAL_SOURCES = 5
TARGET_PAPERS = 50

# Performance Settings
ENABLE_PARALLEL_SEARCH = True
ENABLE_SMART_CACHING = True
CACHE_EXPIRY_DAYS = 7

# Embedding Settings
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# User Settings
DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", "Researcher")