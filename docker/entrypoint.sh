#!/bin/bash
set -e

export TORCH_HOME="${TORCH_HOME:-/app/.cache/torch}"

echo "=== Running Alembic migrations ==="
cd /app/backend && alembic upgrade head

echo "=== Starting FashionVision AI Backend ==="
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
