#!/bin/bash
set -euo pipefail

# Fabian OS — Cron Setup Script
# Registers all scheduled capture scripts and backup into the current user's crontab.
# Usage: sudo ./scripts/setup-cron.sh
#
# Assumes scripts are deployed to /opt/fabian-os/scripts/

INSTALL_DIR="${INSTALL_DIR:-/opt/fabian-os}"
SCRIPTS_DIR="$INSTALL_DIR/scripts"
LOG_DIR="/var/log/fabian-os"

mkdir -p "$LOG_DIR"

echo "=== Fabian OS — Cron Job Setup ==="
echo "Install dir: $INSTALL_DIR"
echo "Log dir: $LOG_DIR"
echo ""

# Build the crontab entries
CRON_ENTRIES=$(cat <<CRON
# ── Fabian OS Scheduled Jobs ──────────────────────────────
# Managed by setup-cron.sh — do not edit manually

# Gmail capture — every hour on the hour
0 * * * * cd $INSTALL_DIR && /usr/bin/python3 $SCRIPTS_DIR/capture_gmail.py >> $LOG_DIR/capture_gmail.log 2>&1

# Outlook capture — every hour at :30
30 * * * * cd $INSTALL_DIR && /usr/bin/python3 $SCRIPTS_DIR/capture_outlook.py >> $LOG_DIR/capture_outlook.log 2>&1

# Google Drive sync — daily at 3 AM
0 3 * * * cd $INSTALL_DIR && /usr/bin/python3 $SCRIPTS_DIR/sync_drive.py >> $LOG_DIR/sync_drive.log 2>&1

# Database backup — daily at 2 AM
0 2 * * * cd $INSTALL_DIR && $SCRIPTS_DIR/backup.sh >> $LOG_DIR/backup.log 2>&1

# Log rotation — weekly Sunday at midnight
0 0 * * 0 find $LOG_DIR -name '*.log' -size +10M -exec truncate -s 0 {} \;
CRON
)

# Preserve existing non-Fabian crontab entries
EXISTING=$(crontab -l 2>/dev/null | grep -v "Fabian OS" | grep -v "fabian-os" | grep -v "^#.*Managed by setup-cron" || true)

# Install new crontab
{
  echo "$EXISTING"
  echo ""
  echo "$CRON_ENTRIES"
} | crontab -

echo "Cron jobs installed:"
crontab -l | grep -c "fabian-os" || echo "0"
echo ""
echo "Verify with: crontab -l"
echo "=== Done ==="
