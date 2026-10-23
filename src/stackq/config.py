import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://stackq:stackq@localhost:5432/stackq")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

DOCS_BASE_URL = "https://docs.stackit.cloud"
EMBED_MODEL = os.getenv("STACKQ_EMBED_MODEL", "nomic-embed-text")
CHAT_MODEL = os.getenv("STACKQ_CHAT_MODEL", "llama3.1:8b")

RAW_DATA_DIR = "data/raw"
