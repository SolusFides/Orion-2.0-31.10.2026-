#!/bin/sh
set -e
mkdir -p data

echo "Applying Alembic migrations..."
alembic upgrade head

echo "Seeding..."
python -m app.seed

echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
