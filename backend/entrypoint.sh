#!/usr/bin/env sh
set -eu

echo "Running migrations..."
if [ -f "/app/scripts/run_migrations.py" ]; then
  python - <<'PY'
import os
import sys
import time

from sqlalchemy import create_engine, text

database_url = os.getenv("DATABASE_URL", "")
if database_url:
    engine = create_engine(database_url)
    for attempt in range(30):
        try:
            with engine.connect() as connection:
                connection.execute(text("select 1"))
            break
        except Exception as exc:
            if attempt == 29:
                print(f"Database did not become ready: {exc}", file=sys.stderr)
                raise
            time.sleep(1)
PY
  python /app/scripts/run_migrations.py
fi

echo "Starting process: $@"
exec "$@"
