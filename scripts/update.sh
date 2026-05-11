#!/bin/bash
# FashionVision-AI - Update Script
# Updates services without full rebuild (for development)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=============================================="
echo "  FashionVision-AI - Update Services"
echo "=============================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ACTION=${1:-help}

show_help() {
    echo "Usage: ./scripts/update.sh [action]"
    echo ""
    echo "Actions:"
    echo "  backend     - Restart backend only"
    echo "  frontend     - Restart frontend only"
    echo "  db           - Restart database only"
    echo "  backend-full - Full rebuild backend (Docker)"
    echo "  frontend-full - Full rebuild frontend (Docker)"
    echo "  all          - Restart all services"
    echo "  logs         - Show logs for all services"
    echo "  status       - Show service status"
    echo "  help         - Show this help"
    echo ""
}

restart_backend() {
    echo -e "${GREEN}Restarting Backend...${NC}"
    if docker compose ps backend 2>/dev/null | grep -q "Up"; then
        docker compose restart backend
    else
        echo -e "${YELLOW}Backend Docker container not running. Use 'docker-start.sh' first.${NC}"
    fi
}

restart_frontend() {
    echo -e "${GREEN}Restarting Frontend...${NC}"
    if docker compose ps frontend 2>/dev/null | grep -q "Up"; then
        docker compose restart frontend
    else
        echo -e "${YELLOW}Frontend Docker container not running. Use 'docker-start.sh' first.${NC}"
    fi
}

restart_db() {
    echo -e "${GREEN}Restarting Database...${NC}"
    docker compose restart db
}

restart_backend_full() {
    echo -e "${GREEN}Full rebuild Backend (Docker)...${NC}"
    docker compose build backend
    docker compose up -d backend
}

restart_frontend_full() {
    echo -e "${GREEN}Full rebuild Frontend (Docker)...${NC}"
    docker compose build frontend
    docker compose up -d frontend
}

restart_all() {
    echo -e "${GREEN}Restarting all services...${NC}"
    docker compose restart
}

show_logs() {
    echo -e "${YELLOW}Backend logs:${NC}"
    docker compose logs --tail=50 backend
    echo ""
    echo -e "${YELLOW}Frontend logs:${NC}"
    docker compose logs --tail=50 frontend
    echo ""
    echo -e "${YELLOW}Database logs:${NC}"
    docker compose logs --tail=20 db
}

show_status() {
    echo -e "${YELLOW}Service Status:${NC}"
    docker compose ps
    echo ""
    echo -e "${YELLOW}Backend health:${NC}"
    curl -s http://localhost:8000/health 2>/dev/null || echo "Backend not reachable"
}

case "$ACTION" in
    backend)
        restart_backend
        ;;
    frontend)
        restart_frontend
        ;;
    db)
        restart_db
        ;;
    backend-full)
        restart_backend_full
        ;;
    frontend-full)
        restart_frontend_full
        ;;
    all)
        restart_all
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    help|*)
        show_help
        ;;
esac

echo ""
echo -e "${GREEN}Done!${NC}"