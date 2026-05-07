#!/bin/bash
# FashionVision-AI - Migration Script
# Ejecuta migraciones de Alembic

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=============================================="
echo "  FashionVision-AI - Database Migrations"
echo "=============================================="
echo ""

if [ ! -d "$PROJECT_ROOT/backend/venv" ]; then
    echo "ERROR: Virtual environment not found. Run dev-start.sh first."
    exit 1
fi

source "$PROJECT_ROOT/backend/venv/bin/activate"
export PYTHONPATH=$PROJECT_ROOT

# Check DB is running
if ! docker compose ps db 2>/dev/null | grep -q "Up"; then
    echo "ERROR: Database is not running. Start it with: docker compose up -d db"
    exit 1
fi

if [ "$1" = "status" ]; then
    echo "Current migration status:"
    alembic current
    echo ""
    echo "Migration history:"
    alembic history
elif [ "$1" = "down" ]; then
    echo "Rolling back one migration..."
    alembic downgrade -1
elif [ "$1" = "reset" ]; then
    echo -e "${YELLOW}WARNING: This will reset ALL migrations.${NC}"
    read -p "Are you sure? Type 'yes' to continue: " confirm
    if [ "$confirm" = "yes" ]; then
        alembic downgrade base
        alembic upgrade head
        echo "Database reset complete!"
    else
        echo "Cancelled."
    fi
else
    echo "Running pending migrations..."
    alembic upgrade head
    echo ""
    echo "Current version:"
    alembic current
fi

echo ""