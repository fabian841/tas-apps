-- Migration 001: Enable required PostgreSQL extensions
-- pgcrypto: Provides gen_random_uuid() for reliable UUID generation
-- vector:   Provides pgvector for embedding storage and similarity search

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;
