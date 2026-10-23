"""PostgreSQL + pgvector helpers."""

import psycopg
from pgvector.psycopg import register_vector

from stackq.config import DATABASE_URL


def connect() -> psycopg.Connection:
    conn = psycopg.connect(DATABASE_URL)
    register_vector(conn)
    return conn


def insert_chunk(conn, url: str, title: str, content: str, embedding: list[float]) -> None:
    # TODO: INSERT INTO stackq_embeddings (url, title, content, embedding) VALUES (...)
    raise NotImplementedError


def search(conn, embedding: list[float], k: int = 5) -> list[tuple[str, str, str]]:
    """Return the k most similar chunks as (url, title, content)."""
    # TODO: ORDER BY embedding <=> %s LIMIT %s   (<=> is cosine distance)
    raise NotImplementedError
