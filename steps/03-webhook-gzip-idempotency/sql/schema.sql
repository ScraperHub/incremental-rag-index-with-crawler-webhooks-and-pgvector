CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS pages (
    url TEXT PRIMARY KEY,
    content_hash TEXT,
    last_verified_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    original_status INTEGER,
    recrawl_every INTERVAL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL REFERENCES pages (url) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (url, chunk_index)
);

CREATE TABLE IF NOT EXISTS deliveries (
    rid TEXT PRIMARY KEY,
    url TEXT,
    original_status INTEGER,
    cb_status INTEGER,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw
    ON chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS chunks_url_idx ON chunks (url);
