import os
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://stackq:stackq@localhost:5432/stackq")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

DOCS_BASE_URL = "https://docs.stackit.cloud"
EMBED_MODEL = os.getenv("STACKQ_EMBED_MODEL", "nomic-embed-text")
CHAT_MODEL = os.getenv("STACKQ_CHAT_MODEL", "llama3.1:8b")

RAW_DATA_DIR = "data/raw"

def raw_data_dir() -> Path:
    """Folder for scraped pages: $STACKQ_DATA_DIR, else data/raw in the working directory.

    Based on the working directory (not __file__), so it also works when stackq is
    installed without -e and the code lives in site-packages.
    """
    return Path(os.getenv("STACKQ_DATA_DIR", RAW_DATA_DIR)).resolve()
