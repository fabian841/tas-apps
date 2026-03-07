#!/bin/bash
set -euo pipefail

# Fabian OS — Restore Script
# Restores database from the most recent backup (or a specified backup path).
# Usage:
#   ./scripts/restore.sh                     # restores latest backup
#   ./scripts/restore.sh /backups/20260307_020000  # restores specific backup

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

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

# Determine backup path
if [ -n "${1:-}" ]; then
  BACKUP_DIR="$1"
else
  BACKUP_DIR=$(ls -td /backups/*/ 2>/dev/null | head -1)
  if [ -z "$BACKUP_DIR" ]; then
    echo "ERROR: No backups found in /backups/"
    exit 1
  fi
fi

DUMP_FILE="$BACKUP_DIR/fabian_os.dump"
if [ ! -f "$DUMP_FILE" ]; then
  echo "ERROR: Dump file not found: $DUMP_FILE"
  exit 1
fi

echo "=== Fabian OS — Database Restore ==="
echo "Backup: $DUMP_FILE"
echo "Target: $DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "WARNING: This will overwrite the current database."
read -p "Continue? [y/N] " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

# Stop n8n and glance (keep postgres running)
echo "Stopping n8n and glance..."
cd "$PROJECT_DIR"
docker compose stop n8n glance 2>/dev/null || docker-compose stop n8n glance 2>/dev/null || true

# Restore
echo "Restoring database..."
pg_restore \
  --host="$DB_HOST" \
  --port="$DB_PORT" \
  --username="$DB_USER" \
  --dbname="$DB_NAME" \
  --clean \
  --if-exists \
  --no-owner \
  "$DUMP_FILE"

echo "Restore complete."

# Restart services
echo "Starting services..."
docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null

# Verify
echo ""
echo "--- Verification ---"
echo "Containers:"
docker ps --format "  {{.Names}}: {{.Status}}" | grep fabian || true

echo ""
echo "Table count: $(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")"
echo "Transcript count: $(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT count(*) FROM raw_transcripts;" 2>/dev/null || echo 'N/A')"

echo ""
echo "=== Restore complete ==="
