CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS stackq_embeddings (
    id          BIGSERIAL PRIMARY KEY,
    url         TEXT NOT NULL,
    title       TEXT,
    content     TEXT NOT NULL,
    embedding   vector(768) NOT NULL,  -- nomic-embed-text dimension
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS stackq_embeddings_embedding_idx
    ON stackq_embeddings USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS stackq_embeddings_url_idx ON stackq_embeddings (url);
