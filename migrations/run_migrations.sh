#!/usr/bin/env bash
# =============================================================================
# Fabian OS – Migration Runner
# Applies versioned SQL migrations to the target database.
# Tracks applied migrations in a schema_migrations table to prevent re-runs.
#
# Usage:
#   ./migrations/run_migrations.sh prod      # Apply to production (fabian_os)
#   ./migrations/run_migrations.sh dev       # Apply to staging (fabian_os_dev)
#
# Environment variables (or .env file):
#   POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT,
#   POSTGRES_DB, POSTGRES_DEV_DB
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load .env if present
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# Defaults
PGUSER="${POSTGRES_USER:-fabian}"
PGPASSWORD="${POSTGRES_PASSWORD:-}"
PGHOST="${POSTGRES_HOST:-localhost}"
PGPORT="${POSTGRES_PORT:-5432}"
PROD_DB="${POSTGRES_DB:-fabian_os}"
DEV_DB="${POSTGRES_DEV_DB:-fabian_os_dev}"

# Determine target environment
ENV="${1:-}"
if [ -z "$ENV" ]; then
    echo "Usage: $0 <prod|dev>"
    echo "  prod  – Apply migrations to $PROD_DB"
    echo "  dev   – Apply migrations to $DEV_DB"
    exit 1
fi

case "$ENV" in
    prod|production)
        TARGET_DB="$PROD_DB"
        echo "Target: PRODUCTION ($TARGET_DB)"
        ;;
    dev|staging|development)
        TARGET_DB="$DEV_DB"
        echo "Target: STAGING ($TARGET_DB)"
        ;;
    *)
        echo "Error: Unknown environment '$ENV'. Use 'prod' or 'dev'."
        exit 1
        ;;
esac

export PGPASSWORD

# Helper: run SQL against the target database
run_sql() {
    psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$TARGET_DB" \
         -v ON_ERROR_STOP=1 --no-psqlrc -q "$@"
}

# Ensure schema_migrations tracking table exists
run_sql <<'SQL'
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW()
);
SQL

echo ""
echo "Checking migrations in: $SCRIPT_DIR"
echo "---"

APPLIED=0
SKIPPED=0

# Process migration files in order
for migration_file in "$SCRIPT_DIR"/[0-9]*.sql; do
    [ -f "$migration_file" ] || continue

    filename="$(basename "$migration_file")"
    version="${filename%.sql}"

    # Check if already applied
    already_applied=$(run_sql -t -A -c \
        "SELECT COUNT(*) FROM schema_migrations WHERE version = '$version';" 2>/dev/null)

    if [ "$already_applied" -gt 0 ]; then
        echo "  SKIP  $filename (already applied)"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    echo "  APPLY $filename ..."
    if run_sql -f "$migration_file"; then
        run_sql -c "INSERT INTO schema_migrations (version) VALUES ('$version');"
        echo "  OK    $filename"
        APPLIED=$((APPLIED + 1))
    else
        echo "  FAIL  $filename – aborting."
        exit 1
    fi
done

echo ""
echo "Done. Applied: $APPLIED, Skipped: $SKIPPED."
