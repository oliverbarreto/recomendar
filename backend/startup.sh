#!/bin/bash
# Startup script for backend container
# Runs database migrations before starting the application

set -e

echo "Running database migrations..."
uv run alembic upgrade head

echo "Starting application..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000



