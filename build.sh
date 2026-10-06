#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: DATABASE_URL is not set. Add your Neon connection string in Render environment variables."
  exit 1
fi

python manage.py migrate --no-input
# Sync word content from content/<type>/tier-N.json; fails the build (nothing loaded) if a file is invalid.
python manage.py load_content
# Rate-limit counters live in this table (CACHES in settings.py); no-op if it exists.
python manage.py createcachetable
# Drop expired entries from the JWT blacklist tables so they don't grow forever.
python manage.py flushexpiredtokens
