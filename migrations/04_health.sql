-- Phase 0: Health monitoring and credential tracking tables

CREATE TABLE health_checks (
    component TEXT PRIMARY KEY,
    last_run TIMESTAMPTZ,
    status TEXT,
    message TEXT,
    metadata JSONB
);

CREATE TABLE credential_expiry (
    id SERIAL PRIMARY KEY,
    service TEXT NOT NULL,
    expires_at DATE NOT NULL,
    notified BOOLEAN DEFAULT FALSE
);
