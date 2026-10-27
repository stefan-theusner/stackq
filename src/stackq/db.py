import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from stackq.config import DATABASE_URL
from stackq.model import ChatMessage


def connect() -> psycopg.Connection:
    conn = psycopg.connect(DATABASE_URL)
    register_vector(conn)
    return conn

def insert_page (cursor, url: str, title: str, category: str) -> int:
    cursor.execute(
        "INSERT INTO stackq_pages (url, title, category) VALUES (%s, %s, %s) RETURNING id;",
        (url, title, category)
    )
    return cursor.fetchone()[0]

def insert_chunk_parent(cursor, page_id: int, parent_text: str, hierarchy: list) -> int:
    cursor.execute(
        """
        INSERT INTO stackq_embeddings (page_id, parent_id, content, heading_hierarchy, embedding)
        VALUES (%s, NULL, %s, %s, NULL) RETURNING id;
        """,
        (page_id, parent_text, hierarchy)
    )
    return cursor.fetchone()[0]

def insert_chunk(cursor, page_id: int, parent_id: int, content: str, hierarchy: list, embedding: list[float]) -> None:
    cursor.execute(
        """
        INSERT INTO stackq_embeddings (page_id, parent_id, content, heading_hierarchy, embedding)
        VALUES (%s, %s, %s, %s, %s);
        """,
        (page_id, parent_id, content, hierarchy, embedding)
    )


def search(conn, embeddings: list[float], k: int = 10) -> list[dict]:
    cursor = conn.cursor(row_factory=dict_row)
    return cursor.execute("""
        WITH top_matches AS (
            SELECT id, parent_id
            FROM stackq_embeddings
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        )
        SELECT DISTINCT c.id, c.page_id, c.content, p.title, p.url, c.heading_hierarchy
        FROM stackq_embeddings c
        JOIN stackq_pages p ON c.page_id = p.id
        WHERE c.id IN (SELECT COALESCE(parent_id, id) FROM top_matches);
        """, (embeddings, k))
