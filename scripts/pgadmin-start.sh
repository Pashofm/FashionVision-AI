#!/bin/bash
# FashionVision-AI - pgAdmin Start Script
# Inicia pgAdmin para administracion de la base de datos

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=============================================="
echo "  FashionVision-AI - pgAdmin Start"
echo "=============================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}WARNING: .env file not found. Copying from .env.template...${NC}"
    cp "$PROJECT_ROOT/.env.template" "$PROJECT_ROOT/.env"
fi

# Ensure db is running
if ! docker compose ps db 2>/dev/null | grep -q "Up"; then
    echo -e "${YELLOW}Database is not running. Starting it first...${NC}"
    docker compose up -d db
    sleep 5
fi

# Start pgAdmin
echo -e "${GREEN}[1/1] Starting pgAdmin...${NC}"
docker compose up -d pgadmin

echo ""
echo -e "${GREEN}pgAdmin started successfully!${NC}"
echo ""
echo "Access:"
echo "  URL:      http://localhost:${PGADMIN_HOST_PORT:-5050}"
echo "  Email:    ${PGADMIN_EMAIL:-admin@fashionvision.com}"
echo "  Password: ${PGADMIN_PASSWORD:-admin123}"
echo ""
echo "To connect the database:"
echo "  Host:     fashionvision_db"
echo "  Port:     5432"
echo "  Database: fashionvision_ai"
echo "  User:     fashionvision_ai_user"
echo ""