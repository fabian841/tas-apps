-- Migration 002: Raw Layer Tables
-- Immutable source data exactly as received. Never modified after insertion.
-- All raw tables preserve original payloads for later reprocessing.

-- Raw emails from Gmail and Outlook
CREATE TABLE IF NOT EXISTS raw_emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id TEXT UNIQUE NOT NULL,
    thread_id TEXT,
    history_id TEXT,
    from_address TEXT,
    to_addresses TEXT[],
    cc_addresses TEXT[],
    bcc_addresses TEXT[],
    subject TEXT,
    body_text TEXT,
    body_html TEXT,
    labels TEXT[],
    has_attachments BOOLEAN DEFAULT FALSE,
    received_at TIMESTAMPTZ,
    raw_payload JSONB NOT NULL,
    source_system TEXT NOT NULL DEFAULT 'gmail',
    captured_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_raw_emails_received ON raw_emails(received_at);
CREATE INDEX idx_raw_emails_from ON raw_emails(from_address);
CREATE INDEX idx_raw_emails_thread ON raw_emails(thread_id);
CREATE INDEX idx_raw_emails_history ON raw_emails(history_id);

-- Raw Google Drive file metadata
CREATE TABLE IF NOT EXISTS raw_drive_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    mime_type TEXT,
    parent_ids TEXT[],
    owners JSONB,
    web_view_link TEXT,
    icon_link TEXT,
    size_bytes BIGINT,
    md5_checksum TEXT,
    created_time TIMESTAMPTZ,
    modified_time TIMESTAMPTZ,
    shared BOOLEAN DEFAULT FALSE,
    trashed BOOLEAN DEFAULT FALSE,
    raw_payload JSONB NOT NULL,
    source_system TEXT NOT NULL DEFAULT 'google_drive',
    captured_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_raw_drive_files_modified ON raw_drive_files(modified_time);
CREATE INDEX idx_raw_drive_files_mime ON raw_drive_files(mime_type);
CREATE INDEX idx_raw_drive_files_name ON raw_drive_files(name);

-- Raw agent output (Perplexity, Claude, other AI agents)
CREATE TABLE IF NOT EXISTS raw_agent_output (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name TEXT NOT NULL,
    agent_version TEXT,
    query TEXT NOT NULL,
    response_text TEXT,
    model TEXT,
    tokens_used INTEGER,
    latency_ms INTEGER,
    raw_payload JSONB NOT NULL,
    source_system TEXT NOT NULL DEFAULT 'agent',
    captured_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_raw_agent_output_agent ON raw_agent_output(agent_name);
CREATE INDEX idx_raw_agent_output_captured ON raw_agent_output(captured_at);
