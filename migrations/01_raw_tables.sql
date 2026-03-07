-- Phase 0: Raw ingestion tables
-- These tables store unprocessed data from external sources.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- for gen_random_uuid

CREATE TABLE raw_emails (
    id SERIAL PRIMARY KEY,
    message_id TEXT UNIQUE,
    received_at TIMESTAMPTZ,
    sender TEXT,
    subject TEXT,
    body TEXT,
    attachments JSONB,
    raw_data JSONB,
    source TEXT DEFAULT 'gmail',
    classification TEXT,
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE raw_drive_files (
    id SERIAL PRIMARY KEY,
    file_id TEXT UNIQUE,
    name TEXT,
    path TEXT,
    mime_type TEXT,
    size BIGINT,
    modified_at TIMESTAMPTZ,
    local_path TEXT,
    metadata JSONB,
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE raw_agent_output (
    id SERIAL PRIMARY KEY,
    agent_name TEXT,
    source TEXT,
    raw_content TEXT,
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);
