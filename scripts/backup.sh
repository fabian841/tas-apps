#!/usr/bin/env bash
# =============================================================================
# Fabian OS – Backup Script
# Creates PostgreSQL dumps and configuration archives.
# Schedule via cron: 0 2 * * * /path/to/backup.sh
#
# Retains backups for 30 days by default.
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

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${PROJECT_ROOT}/backups"
RETENTION_DAYS=30

PGUSER="${POSTGRES_USER:-fabian}"
PGPASSWORD="${POSTGRES_PASSWORD:-}"
PGHOST="${POSTGRES_HOST:-localhost}"
PGPORT="${POSTGRES_PORT:-5432}"
PROD_DB="${POSTGRES_DB:-fabian_os}"
DEV_DB="${POSTGRES_DEV_DB:-fabian_os_dev}"

export PGPASSWORD

mkdir -p "$BACKUP_DIR"

echo "=== Fabian OS Backup – $TIMESTAMP ==="

# --- PostgreSQL Production Dump ---
echo "Backing up production database ($PROD_DB)..."
pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -Fc "$PROD_DB" \
    > "$BACKUP_DIR/db_prod_${TIMESTAMP}.dump"
echo "  Saved: db_prod_${TIMESTAMP}.dump"

# --- PostgreSQL Staging Dump ---
echo "Backing up staging database ($DEV_DB)..."
pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -Fc "$DEV_DB" \
    > "$BACKUP_DIR/db_dev_${TIMESTAMP}.dump" 2>/dev/null || echo "  Staging DB not found (skipped)"

# --- Configuration Archive ---
echo "Backing up configuration files..."
tar -czf "$BACKUP_DIR/configs_${TIMESTAMP}.tar.gz" \
    -C "$PROJECT_ROOT" \
    config/ schemas/ migrations/ n8n/workflows/ docs/ \
    docker-compose.yml workflow_owners.md README.md \
    2>/dev/null || echo "  Some config files missing (partial backup)"

echo "  Saved: configs_${TIMESTAMP}.tar.gz"

# --- n8n Workflow Export (if container is running) ---
if docker ps --format '{{.Names}}' | grep -q fabian-n8n; then
    echo "Exporting n8n workflows..."
    docker exec fabian-n8n n8n export:workflow --all \
        --output=/home/node/.n8n/backups/workflows_${TIMESTAMP}.json 2>/dev/null \
        && docker cp fabian-n8n:/home/node/.n8n/backups/workflows_${TIMESTAMP}.json \
            "$BACKUP_DIR/n8n_workflows_${TIMESTAMP}.json" \
        && echo "  Saved: n8n_workflows_${TIMESTAMP}.json" \
        || echo "  n8n workflow export failed (skipped)"
else
    echo "  n8n container not running (skipped)"
fi

# --- Cleanup old backups ---
echo "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "$BACKUP_DIR" -name "*.dump" -mtime +"$RETENTION_DAYS" -delete 2>/dev/null
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +"$RETENTION_DAYS" -delete 2>/dev/null
find "$BACKUP_DIR" -name "*.json" -mtime +"$RETENTION_DAYS" -delete 2>/dev/null

echo "=== Backup complete ==="
