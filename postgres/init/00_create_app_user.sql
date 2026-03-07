-- Fabian OS — Docker-entrypoint init script
-- Runs automatically on first docker-compose up (when data volume is empty)
-- Creates the fabian_app role and grants necessary permissions

-- Create app user (used by n8n, capture scripts, agents)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'fabian_app') THEN
    CREATE ROLE fabian_app WITH LOGIN PASSWORD current_setting('app.db_password', true);
    RAISE NOTICE 'Created role fabian_app';
  END IF;
END $$;

-- If password env var wasn't set, use a default (overridden by .env in production)
ALTER ROLE fabian_app WITH LOGIN;

-- Grant schema usage
GRANT USAGE ON SCHEMA public TO fabian_app;

-- Default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO fabian_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO fabian_app;
