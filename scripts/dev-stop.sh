#!/bin/bash
# FashionVision-AI - Development Stop Script
# Detiene todos los servicios de desarrollo

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=============================================="
echo "  FashionVision-AI - Stopping Services"
echo "=============================================="
echo ""

# Stop Docker services
echo "Stopping Docker services..."
docker compose stop db pgadmin 2>/dev/null || true

echo ""
echo -e "\033[0;32mAll services stopped!\033[0m"
echo ""
echo "Note: Database data is preserved in Docker volume."
echo "To start again: ./scripts/dev-start.sh"
echo ""