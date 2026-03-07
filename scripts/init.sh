#!/bin/bash
set -euo pipefail

# Fabian OS — Initialization Script
# Runs all migrations in order against the running PostgreSQL instance.
# Usage: ./scripts/init.sh
#
# Prerequisites:
#   - docker-compose up -d postgres (must be running and healthy)
#   - .env file with POSTGRES_PASSWORD and APP_DB_PASSWORD

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MIGRATIONS_DIR="$PROJECT_DIR/migrations"

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-fabian_os}"
DB_USER="${DB_USER:-fabian_admin}"

# Load .env if present
if [ -f "$PROJECT_DIR/.env" ]; then
  set -a
  source "$PROJECT_DIR/.env"
  set +a
fi

echo "=== Fabian OS — Database Initialization ==="
echo "Host: $DB_HOST:$DB_PORT  Database: $DB_NAME  User: $DB_USER"
echo ""

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
for i in {1..30}; do
  if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1; then
    echo "PostgreSQL is ready."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "ERROR: PostgreSQL not ready after 30 attempts. Exiting."
    exit 1
  fi
  sleep 2
done

# Create fabian_app role if it doesn't exist
echo ""
echo "--- Creating fabian_app role ---"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=0 <<'SQL'
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'fabian_app') THEN
    EXECUTE format('CREATE ROLE fabian_app WITH LOGIN PASSWORD %L',
                   coalesce(current_setting('app.db_password', true), 'changeme'));
    RAISE NOTICE 'Created role fabian_app';
  ELSE
    RAISE NOTICE 'Role fabian_app already exists';
  END IF;
END $$;

GRANT USAGE ON SCHEMA public TO fabian_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO fabian_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO fabian_app;
SQL

# Run migrations in order
echo ""
echo "--- Running migrations ---"
for migration in "$MIGRATIONS_DIR"/*.sql; do
  filename=$(basename "$migration")
  echo "  Applying: $filename"
  psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    -v ON_ERROR_STOP=1 \
    -f "$migration" 2>&1 | sed 's/^/    /'
  echo "  Done: $filename"
done

# Grant permissions on all existing tables to fabian_app
echo ""
echo "--- Granting permissions to fabian_app ---"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<'SQL'
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fabian_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fabian_app;
SQL

echo ""
echo "=== Initialization complete ==="
echo "Tables created: $(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")"
