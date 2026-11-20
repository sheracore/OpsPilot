CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS runbooks (
    id          text PRIMARY KEY,
    title       text NOT NULL,
    body        text NOT NULL,
    services    text[] NOT NULL DEFAULT '{}',
    embedding   vector(768) NOT NULL,
    embed_model text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS runbooks_services_gin
    ON runbooks USING gin (services);

CREATE INDEX IF NOT EXISTS runbooks_embedding_hnsw
    ON runbooks USING hnsw (embedding vector_cosine_ops);
