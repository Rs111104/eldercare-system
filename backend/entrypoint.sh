#!/usr/bin/env sh
set -euo pipefail

echo "Running migrations..."
if [ -f "/app/scripts/run_migrations.py" ]; then
  python /app/scripts/run_migrations.py || true
fi

echo "Starting process: $@"
exec "$@"
