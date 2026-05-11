#!/bin/bash
# FashionVision-AI - Deploy Local Script
# Starts backend and frontend with a single command (in background processes)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=============================================="
echo "  FashionVision-AI - Deploy Local"
echo "=============================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    if [ -f "$PROJECT_ROOT/.env.template" ]; then
        echo -e "${YELLOW}No .env found. Creating from template...${NC}"
        cp "$PROJECT_ROOT/.env.template" "$PROJECT_ROOT/.env"
        echo -e "${YELLOW}Please edit .env with your credentials before running again.${NC}"
        exit 1
    else
        echo -e "${RED}ERROR: No .env.template found!${NC}"
        exit 1
    fi
fi

# Load .env
set -a
source "$PROJECT_ROOT/.env"
set +a

# Check if database is running
if ! docker compose ps db 2>/dev/null | grep -q "Up"; then
    echo -e "${YELLOW}Database not running. Starting it first...${NC}"
    docker compose up -d db
    echo "Waiting for database..."
    sleep 5
fi

# Kill any existing backend/frontend processes on those ports
kill_port() {
    local port=$1
    local name=$2

    if command -v lsof >/dev/null 2>&1; then
        local pid=$(lsof -ti:$port 2>/dev/null)
        if [ -n "$pid" ]; then
            echo "Killing existing $name on port $port (PID: $pid)"
            kill $pid 2>/dev/null || true
            sleep 1
        fi
    elif command -v netstat >/dev/null 2>&1; then
        local pid=$(netstat -tlnp 2>/dev/null | grep ":$port" | awk '{print $7}' | cut -d'/' -f1)
        if [ -n "$pid" ]; then
            echo "Killing existing $name on port $port"
            kill $pid 2>/dev/null || true
            sleep 1
        fi
    fi
}

echo "Cleaning up any existing processes..."
kill_port 8000 "backend"
kill_port 5173 "frontend"
echo ""

# Start backend
echo -e "${GREEN}[1/2] Starting Backend...${NC}"
cd "$PROJECT_ROOT/backend"

VENV_ACTIVATE="$PROJECT_ROOT/backend/venv/bin/activate"
if [ -f "$PROJECT_ROOT/backend/venv/Scripts/activate" ]; then
    VENV_ACTIVATE="$PROJECT_ROOT/backend/venv/Scripts/activate"
fi

nohup bash -c "
    source '$VENV_ACTIVATE'
    export PYTHONPATH='$PROJECT_ROOT'
    export DATABASE_URL='$DATABASE_URL'
    export DATABASE_URL_SYNC='$DATABASE_URL_SYNC'
    uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0
" > /tmp/fashionvision-backend.log 2>&1 &

BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"
echo "Backend logs: /tmp/fashionvision-backend.log"
echo ""

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
max_attempts=30
attempt=0
until curl -s http://localhost:8000/health >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo -e "${YELLOW}WARNING: Backend may not be ready. Check logs.${NC}"
        break
    fi
    sleep 1
done
echo -e "${GREEN}Backend is ready!${NC}"
echo ""

# Start frontend
echo -e "${GREEN}[2/2] Starting Frontend...${NC}"
cd "$PROJECT_ROOT/frontend"

nohup npm run dev > /tmp/fashionvision-frontend.log 2>&1 &

FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"
echo "Frontend logs: /tmp/fashionvision-frontend.log"
echo ""

# Wait for frontend to be ready
echo "Waiting for frontend to be ready..."
sleep 5

echo ""
echo "=============================================="
echo -e "${GREEN}  All Services Running!${NC}"
echo "=============================================="
echo ""
echo -e "${YELLOW}Access Points:${NC}"
echo "  Frontend:  http://localhost:5173"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo "  Backend:   tail -f /tmp/fashionvision-backend.log"
echo "  Frontend:  tail -f /tmp/fashionvision-frontend.log"
echo ""
echo -e "${YELLOW}To stop services:${NC}"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "  docker compose stop db pgadmin"
echo ""

# Save PIDs for later cleanup
echo "$BACKEND_PID" > /tmp/fashionvision-backend.pid
echo "$FRONTEND_PID" > /tmp/fashionvision-frontend.pid