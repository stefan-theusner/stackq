"""Stages 3 and 4: embed chunks and answer questions with a local LLM."""

from ollama import Client

from stackq.config import CHAT_MODEL, EMBED_MODEL, OLLAMA_HOST

client = Client(host=OLLAMA_HOST)

PROMPT = """Answer the question using ONLY the context below.
If the answer is not in the context, say you don't know. Cite the source URLs.

Context:
{context}

Question: {question}"""


def embed(text: str) -> list[float]:
    return client.embed(model=EMBED_MODEL, input=text)["embeddings"][0]


def index_all() -> None:
    """Read data/raw/*.json, chunk, embed and store in Postgres."""
    # TODO
    raise NotImplementedError


def ask(question: str) -> str:
    """Retrieve relevant chunks and ask the chat model."""
    # TODO: embed question -> db.search -> build context -> client.chat(...)
    raise NotImplementedError
