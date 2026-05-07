#!/bin/bash
# FashionVision-AI - pgAdmin Stop Script
# Detiene el contenedor de pgAdmin

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=============================================="
echo "  FashionVision-AI - pgAdmin Stop"
echo "=============================================="
echo ""

docker compose stop pgadmin 2>/dev/null || true

echo -e "\033[0;32mpgAdmin stopped!${NC}"
echo ""
echo "Data is preserved in the pgadmin_data volume."
echo "To start again: ./scripts/pgadmin-start.sh"
echo ""