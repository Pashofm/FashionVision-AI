#!/bin/bash
# FashionVision-AI - Docker Start Script
# Inicia todo en contenedores Docker (modo Testing/Demo)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=============================================="
echo "  FashionVision-AI - Docker Mode Start"
echo "=============================================="
echo ""

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "ERROR: .env file not found. Copy from .env.template first."
    exit 1
fi

# Build and start all services
echo "Building and starting all services..."
docker compose up -d --build

# Wait for services to be healthy
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check service status
echo ""
echo "=============================================="
echo "  Service Status"
echo "=============================================="
docker compose ps

echo ""
echo -e "\033[0;32mAll services started in Docker mode!\033[0m"
echo ""
echo "Access points:"
echo "  App (Frontend): http://localhost"
echo "  Backend API:    http://localhost:8000"
echo "  API Docs:       http://localhost:8000/docs"
echo ""
echo "To stop: docker compose down"
echo ""