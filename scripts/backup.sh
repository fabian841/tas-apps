#!/bin/bash
set -euo pipefail

# Fabian OS – Phase 0 Backup Script
# Schedule via root crontab:
#   0 2 * * * /opt/fabian-os/scripts/backup.sh >> /var/log/fabian-backup.log 2>&1

BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

pg_dump \
  --host=localhost \
  --username=fabian_app \
  --format=custom \
  --compress=9 \
  --file="$BACKUP_DIR/fabian_os.dump" \
  fabian_os

# Ping Healthchecks.io on success
curl -fsS --retry 3 "https://hc-ping.com/${HC_BACKUP_UUID}" > /dev/null

echo "Backup complete: $BACKUP_DIR"
