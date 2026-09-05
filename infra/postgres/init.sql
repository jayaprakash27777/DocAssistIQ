-- DocAssistIQ PostgreSQL init script
-- Runs automatically on first container boot (empty data volume).
-- Installs the pgvector extension required for embedding storage in later phases.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- text similarity for search
CREATE EXTENSION IF NOT EXISTS btree_gin; -- GIN index support
