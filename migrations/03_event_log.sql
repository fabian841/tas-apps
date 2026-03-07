-- Phase 0: Event log (append-only audit trail)
-- All significant system events are recorded here.

CREATE TABLE event_log (
    id BIGSERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    entity_type TEXT,
    entity_id UUID,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    source TEXT,
    metadata JSONB
);

CREATE INDEX idx_event_log_timestamp_brin ON event_log USING BRIN (timestamp);
CREATE INDEX idx_event_log_entity ON event_log(entity_type, entity_id);
CREATE INDEX idx_event_log_type ON event_log(event_type);
CREATE INDEX idx_event_log_source ON event_log(source);
