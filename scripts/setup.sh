#!/bin/bash
# FashionVision-AI - Setup Script
# For fresh clone: installs all dependencies and prepares environment

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=============================================="
echo "  FashionVision-AI - Initial Setup"
echo "=============================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check prerequisites
echo -e "${GREEN}[1/6] Checking prerequisites...${NC}"

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

if ! command_exists docker; then
    echo -e "${RED}ERROR: Docker is not installed.${NC}"
    echo "Please install Docker Desktop first."
    exit 1
fi

if ! command_exists python3 && ! command_exists python; then
    echo -e "${RED}ERROR: Python is not installed.${NC}"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}ERROR: Node.js is not installed.${NC}"
    exit 1
fi

echo -e "${GREEN}All prerequisites installed!${NC}"
echo ""

# Create .env from template
echo -e "${GREEN}[2/6] Setting up environment...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.template" ]; then
        echo "Creating .env from template..."
        cp .env.template .env
        echo -e "${YELLOW}Please edit .env with your credentials, then run this script again.${NC}"
        echo ""
        echo "After editing .env, run: ./scripts/setup.sh"
        exit 0
    else
        echo -e "${RED}ERROR: .env.template not found!${NC}"
        exit 1
    fi
else
    echo "Using existing .env file"
fi
echo ""

# Start database
echo -e "${GREEN}[3/6] Starting database...${NC}"
docker compose up -d db

max_attempts=30
attempt=0
until docker compose exec -T db pg_isready -U fashionvision_ai_user -d fashionvision_ai > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo -e "${RED}ERROR: Database failed to start.${NC}"
        exit 1
    fi
    echo "  Waiting for database..."
    sleep 2
done
echo -e "${GREEN}Database ready!${NC}"
echo ""

# Backend setup
echo -e "${GREEN}[4/6] Setting up Python backend...${NC}"
cd "$PROJECT_ROOT/backend"

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv 2>/dev/null || python -m venv venv
fi

VENV_ACTIVATE="$PROJECT_ROOT/backend/venv/bin/activate"
if [ -f "$PROJECT_ROOT/backend/venv/Scripts/activate" ]; then
    VENV_ACTIVATE="$PROJECT_ROOT/backend/venv/Scripts/activate"
fi

. "$VENV_ACTIVATE"
pip install -q -r requirements.txt 2>/dev/null || pip3 install -q -r requirements.txt 2>/dev/null
echo -e "${GREEN}Backend Python packages installed!${NC}"
echo ""

# Frontend setup
echo -e "${GREEN}[5/6] Setting up frontend...${NC}"
cd "$PROJECT_ROOT/frontend"
npm install
echo -e "${GREEN}Frontend dependencies installed!${NC}"
echo ""

# Run migrations
echo -e "${GREEN}[6/6] Running database migrations...${NC}"
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT"
alembic upgrade head
echo -e "${GREEN}Migrations applied!${NC}"
echo ""

echo "=============================================="
echo -e "${GREEN}  Initial Setup Complete!${NC}"
echo "=============================================="
echo ""
echo "Next steps:"
echo ""
echo -e "${YELLOW}Terminal 1 - Backend:${NC}"
echo "  cd $PROJECT_ROOT/backend"
echo "  source venv/bin/activate"
echo "  export PYTHONPATH=\$PWD"
echo "  uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0"
echo ""
echo -e "${YELLOW}Terminal 2 - Frontend:${NC}"
echo "  cd $PROJECT_ROOT/frontend"
echo "  npm run dev"
echo ""
echo "Access:"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""