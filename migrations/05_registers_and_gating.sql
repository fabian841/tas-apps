-- Phase 1: PIL Register metadata and confidence gating engine
-- Registers live in Google Sheets. This table tracks register metadata,
-- extraction history, and the confidence gate audit log.

-- Register definitions (maps to Google Sheet tabs)
CREATE TABLE register_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    register_name TEXT UNIQUE NOT NULL,  -- 'decisions', 'commitments', etc.
    sheet_id TEXT,                        -- Google Sheets spreadsheet ID
    tab_name TEXT,                        -- Sheet tab name
    row_count INTEGER DEFAULT 0,
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Confidence gate log: every AI-proposed row is tracked here
-- State machine: PROPOSED -> CONFIRMED (by Fabian) or REJECTED
CREATE TABLE confidence_gate_log (
    id BIGSERIAL PRIMARY KEY,
    register_name TEXT NOT NULL,
    proposed_data JSONB NOT NULL,         -- the row data proposed by extraction
    confidence_score NUMERIC(3,2),        -- 0.00 to 1.00
    confidence_label TEXT NOT NULL,       -- 'HIGH', 'MEDIUM', 'LOW'
    status TEXT NOT NULL DEFAULT 'PROPOSED',  -- 'PROPOSED', 'CONFIRMED', 'REJECTED'
    source_transcript_id TEXT,            -- links back to raw_transcripts.transcript_id
    extraction_model TEXT,                -- e.g. 'claude-sonnet-4-6'
    proposed_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    reviewed_by TEXT,                     -- always 'fabian' for Phase 1
    rejection_reason TEXT,
    metadata JSONB
);

-- Extraction runs: tracks each time Claude processes a transcript
CREATE TABLE extraction_run (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcript_id TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_version TEXT,                  -- version of extraction prompt used
    items_proposed INTEGER DEFAULT 0,
    items_confirmed INTEGER DEFAULT 0,
    items_rejected INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT DEFAULT 'running',        -- 'running', 'completed', 'failed'
    error_message TEXT,
    metadata JSONB
);

-- Indexes
CREATE INDEX idx_gate_log_register ON confidence_gate_log(register_name);
CREATE INDEX idx_gate_log_status ON confidence_gate_log(status);
CREATE INDEX idx_gate_log_proposed ON confidence_gate_log(proposed_at);
CREATE INDEX idx_gate_log_source ON confidence_gate_log(source_transcript_id);
CREATE INDEX idx_extraction_run_transcript ON extraction_run(transcript_id);
CREATE INDEX idx_extraction_run_status ON extraction_run(status);

-- Permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON register_metadata TO fabian_app;
GRANT SELECT, INSERT, UPDATE ON confidence_gate_log TO fabian_app;  -- no DELETE on gate log
GRANT SELECT, INSERT, UPDATE ON extraction_run TO fabian_app;
GRANT USAGE, SELECT ON SEQUENCE confidence_gate_log_id_seq TO fabian_app;

-- Seed the 8 PIL registers
INSERT INTO register_metadata (register_name, tab_name) VALUES
    ('decisions', 'Decisions'),
    ('commitments', 'Commitments'),
    ('ideas', 'Ideas'),
    ('learnings', 'Learnings'),
    ('relationships', 'Relationships'),
    ('health', 'Health'),
    ('finance', 'Finance'),
    ('patterns', 'Patterns');
