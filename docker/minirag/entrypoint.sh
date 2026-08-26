#!/bin/bash
set -e

echo "Running Database migrations..."

export PYTHONPATH="/app:$PYTHONPATH"

cd /app/models/db_schemas/minirag
alembic upgrade head

cd /app

exec "$@"