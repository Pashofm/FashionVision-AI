#!/bin/bash
# FashionVision-AI - Development Start Script
# Inicia el entorno de desarrollo local (DB + backend + frontend)

set -e

# Detect OS for compatibility
detect_os() {
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        echo "windows-git"
    elif [[ "$OSTYPE" == "linux-gnu" ]]; then
        if grep -q Microsoft /proc/version 2>/dev/null; then
            echo "wsl"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=============================================="
echo "  FashionVision-AI - Development Mode Start"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

OS_TYPE=$(detect_os)
echo "Detected OS: $OS_TYPE"
echo ""

# Load .env file if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${GREEN}Loading .env file...${NC}"
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
elif [ -f "$PROJECT_ROOT/.env.template" ]; then
    echo -e "${YELLOW}No .env found. Creating from template...${NC}"
    cp "$PROJECT_ROOT/.env.template" "$PROJECT_ROOT/.env"
    echo -e "${YELLOW}Please edit .env with your credentials before running again.${NC}"
    echo ""
    echo -e "${YELLOW}To continue setup, run this script again after editing .env${NC}"
    exit 1
else
    echo -e "${RED}ERROR: No .env.template found!${NC}"
    exit 1
fi

# Start database and pgAdmin in Docker
echo -e "${GREEN}[1/5] Starting database (Docker)...${NC}"
docker compose up -d db
echo "Waiting for database to be healthy..."
sleep 5

# Check if DB is healthy
max_attempts=30
attempt=0
until docker compose exec -T db pg_isready -U "${POSTGRES_USER:-fashionvision_ai_user}" -d "${POSTGRES_DB:-fashionvision_ai}" > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo -e "${RED}ERROR: Database failed to start. Check logs with: docker compose logs db${NC}"
        exit 1
    fi
    echo "  Waiting for database... (attempt $attempt/$max_attempts)"
    sleep 2
done
echo -e "${GREEN}Database is ready!${NC}"
echo ""

# Start pgAdmin
echo -e "${GREEN}[2/5] Starting pgAdmin (Docker)...${NC}"
docker compose up -d pgadmin
echo -e "${GREEN}pgAdmin is ready!${NC}"
echo ""

# Backend setup
echo -e "${GREEN}[3/5] Backend setup${NC}"
VENV_ACTIVATE=""
if [ ! -d "$PROJECT_ROOT/backend/venv" ]; then
    echo "Creating Python virtual environment..."
    cd "$PROJECT_ROOT/backend"
    python3 -m venv venv 2>/dev/null || python -m venv venv
fi

# Activate venv (compatible with bash, zsh, git bash, WSL)
if [ -f "$PROJECT_ROOT/backend/venv/bin/activate" ]; then
    VENV_ACTIVATE="$PROJECT_ROOT/backend/venv/bin/activate"
elif [ -f "$PROJECT_ROOT/backend/venv/Scripts/activate" ]; then
    VENV_ACTIVATE="$PROJECT_ROOT/backend/venv/Scripts/activate"
fi

if [ -n "$VENV_ACTIVATE" ]; then
    echo "Activating virtual environment..."
    . "$VENV_ACTIVATE"
fi

echo "Installing dependencies..."
pip install -q -r requirements.txt 2>/dev/null || pip3 install -q -r requirements.txt 2>/dev/null

echo -e "${GREEN}Backend dependencies ready!${NC}"
echo ""

# Run database migrations
echo -e "${GREEN}[4/5] Running database migrations (Alembic)...${NC}"
export PYTHONPATH="$PROJECT_ROOT"
cd "$PROJECT_ROOT"
alembic upgrade head
echo -e "${GREEN}Migrations applied!${NC}"
echo ""

# Frontend setup
echo -e "${GREEN}[5/5] Frontend setup${NC}"
if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
    echo "Installing npm dependencies..."
    cd "$PROJECT_ROOT/frontend"
    npm install
fi
echo -e "${GREEN}Frontend ready!${NC}"
echo ""

echo "=============================================="
echo -e "${GREEN}  Development Environment Ready!${NC}"
echo "=============================================="
echo ""
echo "To start services, run these commands:"
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
echo -e "${YELLOW}Access points:${NC}"
echo "  Frontend:  http://localhost:5173"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:   http://localhost:8000/docs"
echo "  pgAdmin:    http://localhost:${PGADMIN_HOST_PORT:-5050}"
echo "    Email:    ${PGADMIN_EMAIL:-admin@fashionvision.com}"
echo "    Password: ${PGADMIN_PASSWORD:-admin123}"
echo ""
echo "Or use ./scripts/dev-stop.sh to stop all services"
echo ""