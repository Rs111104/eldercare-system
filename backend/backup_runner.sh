#!/usr/bin/env sh
set -euo pipefail

# Interval in seconds (default: daily)
INTERVAL=${BACKUP_INTERVAL_SECONDS:-86400}

echo "Starting backup runner with interval ${INTERVAL}s"

while true; do
  echo "Running backup at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  python /app/scripts/backup_db.py || echo "Backup failed"
  sleep ${INTERVAL}
done
