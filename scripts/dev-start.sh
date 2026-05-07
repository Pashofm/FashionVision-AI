#!/bin/bash
# FashionVision-AI - Development Start Script
# Inicia el entorno de desarrollo local (DB + backend + frontend)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=============================================="
echo "  FashionVision-AI - Development Mode Start"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}WARNING: .env file not found. Copying from .env.template...${NC}"
    cp "$PROJECT_ROOT/.env.template" "$PROJECT_ROOT/.env"
    echo -e "${YELLOW}Please edit .env with your credentials before running again.${NC}"
    exit 1
fi

# Start database and pgAdmin in Docker
echo -e "${GREEN}[1/5] Starting database (Docker)...${NC}"
docker compose up -d db
echo "Waiting for database to be healthy..."
sleep 5

# Check if DB is healthy
until docker compose exec -T db pg_isready -U fashionvision_ai_user -d fashionvision_ai > /dev/null 2>&1; do
    echo "  Waiting for database..."
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
if [ ! -d "$PROJECT_ROOT/backend/venv" ]; then
    echo "Creating Python virtual environment..."
    cd "$PROJECT_ROOT/backend"
    python -m venv venv
fi

echo "Installing dependencies..."
source "$PROJECT_ROOT/backend/venv/bin/activate"
pip install -q -r requirements.txt

echo -e "${GREEN}Backend dependencies ready!${NC}"
echo ""

# Run database migrations
echo -e "${GREEN}[4/5] Running database migrations (Alembic)...${NC}"
source "$PROJECT_ROOT/backend/venv/bin/activate"
export PYTHONPATH=$PROJECT_ROOT
cd $PROJECT_ROOT
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
echo "  pgAdmin:    http://localhost:5050"
echo "    Email:    ${PGADMIN_EMAIL:-admin@fashionvision.com}"
echo "    Password: ${PGADMIN_PASSWORD:-admin123}"
echo ""
echo "Or use ./scripts/dev-stop.sh to stop all services"
echo ""