"""
Central configuration. Reads everything from environment variables / .env
so no secrets or paths are hard-coded anywhere else in the codebase.
"""
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/data/financial_data.db")
VECTOR_STORE_DIR = os.getenv("VECTOR_STORE_DIR", os.path.join(BASE_DIR, "data", "vector_store"))
DOCUMENTS_DIR = os.path.join(BASE_DIR, "data", "documents")
SAMPLE_CSV_PATH = os.path.join(BASE_DIR, "data", "sample_financial_data.csv")

os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
os.makedirs(DOCUMENTS_DIR, exist_ok=True)


def require_api_key():
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
