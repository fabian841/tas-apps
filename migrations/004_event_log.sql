-- Migration 004: Event Log Table
-- Chronological record of all business events.
-- Every workflow that creates or updates a canonical object must insert
-- a corresponding event (e.g., DealCreated, IdeaAdded, MetricRecorded).

CREATE TABLE IF NOT EXISTS event_log (
    id BIGSERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    entity_type TEXT,
    entity_id UUID,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    source TEXT,
    metadata JSONB
);

CREATE INDEX idx_event_log_type ON event_log(event_type);
CREATE INDEX idx_event_log_entity ON event_log(entity_type, entity_id);
CREATE INDEX idx_event_log_timestamp ON event_log(timestamp);
CREATE INDEX idx_event_log_source ON event_log(source);
