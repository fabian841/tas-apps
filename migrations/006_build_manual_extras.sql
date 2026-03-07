-- Migration 006: Build Manual Extras
-- Adds credential_expiry tracking and email classification column.

-- Credential expiry tracking – actively monitor API token/key expiry dates
CREATE TABLE IF NOT EXISTS credential_expiry (
    id SERIAL PRIMARY KEY,
    service TEXT NOT NULL,
    description TEXT,
    expires_at DATE NOT NULL,
    notified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_credential_expiry_date ON credential_expiry(expires_at);

-- Classification column for email triage (used by email classification workflow)
ALTER TABLE raw_emails ADD COLUMN IF NOT EXISTS classification TEXT;
