CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE stackq_pages (
    id          BIGSERIAL PRIMARY KEY,
    url         TEXT UNIQUE,
    title       TEXT,
    category    TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stackq_embeddings (
    id                  BIGSERIAL PRIMARY KEY,
    page_id             INTEGER REFERENCES stackq_pages(id) ON DELETE CASCADE,
    parent_id           INTEGER REFERENCES stackq_embeddings(id), -- NULL if it is a prent chunk
    content             TEXT NOT NULL,
    heading_hierarchy   TEXT[],
    embedding           vector(768), -- NULL if it is a prent chunk
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS stackq_embeddings_embedding_idx ON stackq_embeddings USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS stackq_embeddings_page_id_idx ON stackq_embeddings (page_id);
