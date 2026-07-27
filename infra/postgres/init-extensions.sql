-- Enables the pgvector extension used for embedding-based signal/evidence
-- search. Runs automatically on first container init via Postgres'
-- /docker-entrypoint-initdb.d mechanism (pgvector/pgvector image already
-- ships the extension binaries; this just activates it in the target db).
CREATE EXTENSION IF NOT EXISTS vector;
