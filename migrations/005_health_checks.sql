-- Migration 005: Health Checks Table
-- Every component reports status here. Used by the /health-summary endpoint
-- to display system health in Glance. Component is unique – UPSERT on update.

CREATE TABLE IF NOT EXISTS health_checks (
    component TEXT PRIMARY KEY,
    last_run TIMESTAMPTZ,
    status TEXT,
    message TEXT,
    metadata JSONB
);

-- Seed initial components so the dashboard shows expected rows from day 1
INSERT INTO health_checks (component, last_run, status, message) VALUES
    ('gmail_capture', NULL, 'pending', 'Not yet run'),
    ('drive_capture', NULL, 'pending', 'Not yet run'),
    ('n8n_service', NOW(), 'ok', 'Initialised'),
    ('postgres_service', NOW(), 'ok', 'Initialised')
ON CONFLICT (component) DO NOTHING;
