-- LIFE OS Phase 0: Raw ingestion tables
-- These tables store unprocessed data from external sources.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- for gen_random_uuid

-- Email ingestion (Gmail + M365 forwarded)
CREATE TABLE raw_emails (
    id SERIAL PRIMARY KEY,
    message_id TEXT UNIQUE,
    received_at TIMESTAMPTZ,
    sender TEXT,
    subject TEXT,
    body TEXT,
    attachments JSONB,
    raw_data JSONB,
    source TEXT DEFAULT 'gmail',   -- 'gmail' or 'outlook'
    classification TEXT,
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

-- Google Drive file metadata
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

-- PLAUD transcripts (Phase 0 critical path)
CREATE TABLE raw_transcripts (
    id SERIAL PRIMARY KEY,
    transcript_id TEXT UNIQUE,
    title TEXT,
    source TEXT DEFAULT 'plaud',
    raw_content TEXT,
    duration_seconds INTEGER,
    speakers JSONB,              -- speaker identification metadata
    drive_path TEXT,             -- Google Drive 00_INBOX path
    processed BOOLEAN DEFAULT FALSE,
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent / automation outputs (future phases)
CREATE TABLE raw_agent_output (
    id SERIAL PRIMARY KEY,
    agent_name TEXT,
    source TEXT,
    raw_content TEXT,
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_raw_emails_source ON raw_emails(source);
CREATE INDEX idx_raw_emails_received ON raw_emails(received_at);
CREATE INDEX idx_raw_transcripts_processed ON raw_transcripts(processed);
CREATE INDEX idx_raw_transcripts_ingested ON raw_transcripts(ingested_at);
