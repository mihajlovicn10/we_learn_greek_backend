#!/usr/bin/env bash
# Verify DATABASE_URL is set and PostgreSQL is reachable.
set -o errexit

cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: DATABASE_URL is not set."
  echo ""
  echo "1. Open Neon dashboard → your project → Connection details"
  echo "2. Copy the connection string (use 'Pooled connection' for Render)"
  echo "3. Paste it into .env:"
  echo "   DATABASE_URL=postgresql://..."
  exit 1
fi

echo "DATABASE_URL is set."
echo "Running migrations..."
python manage.py migrate
echo ""
echo "Database is ready."
echo "Optional: python manage.py createsuperuser"
