#!/bin/bash
# FashionVision-AI - Database Reset Script
# Reinicia la base de datos (¡CUIDADO! Elimina todos los datos)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=============================================="
echo "  FashionVision-AI - Database Reset"
echo "=============================================="
echo ""

read -p "This will DELETE ALL DATA in the database. Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Stopping services..."
docker compose down

echo "Removing database volume..."
docker volume rm fashionvision-ai_postgres_data 2>/dev/null || true

echo "Starting database..."
docker compose up -d db

echo "Waiting for database to be ready..."
sleep 5

until docker compose exec -T db pg_isready -U fashionvision_ai_user -d fashionvision_ai > /dev/null 2>&1; do
    echo "  Waiting..."
    sleep 2
done

echo ""
echo -e "\033[0;32mDatabase reset complete!\033[0m"
echo ""
echo "Schema and seed data have been applied."
echo "You can now start development with:"
echo "  ./scripts/dev-start.sh"
echo ""