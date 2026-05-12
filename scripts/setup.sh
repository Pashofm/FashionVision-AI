#!/bin/bash
# FashionVision-AI - Setup Script
# For fresh clone: installs all dependencies and prepares environment

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

if [ -f "$SCRIPT_DIR/common_versions.sh" ]; then
    source "$SCRIPT_DIR/common_versions.sh"
fi

generate_secret_key() {
    head -c 32 /dev/urandom | base64 | tr -d '\n'
}

validate_and_fix_env() {
    if [ -f "$PROJECT_ROOT/.env" ]; then
        if grep -q "Base64_32\|changeme\|your_password\|your_secret" "$PROJECT_ROOT/.env" 2>/dev/null; then
            echo -e "${YELLOW}WARNING: .env contains placeholder values. Auto-generating SECRET_KEY...${NC}"
            NEW_SECRET=$(generate_secret_key)
            sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" "$PROJECT_ROOT/.env"
            echo -e "${GREEN}Generated new SECRET_KEY${NC}"
        fi
    fi
}

echo "=============================================="
echo "  FashionVision-AI - Initial Setup"
echo "=============================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

if ! command_exists docker; then
    echo -e "${RED}ERROR: Docker is not installed.${NC}"
    echo "Please install Docker Desktop first."
    exit 1
fi

echo -e "${GREEN}[1/6] Setting up Python environment...${NC}"
setup_python_environment || exit 1
echo ""

echo -e "${GREEN}[2/6] Setting up Node.js environment...${NC}"
setup_node_environment || exit 1
echo ""

echo -e "${GREEN}[3/6] Setting up environment...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.template" ]; then
        echo "Creating .env from template..."
        cp .env.template .env
        validate_and_fix_env
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
    validate_and_fix_env
fi
echo ""

echo -e "${GREEN}[4/6] Starting database...${NC}"
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

echo -e "${GREEN}[5/6] Setting up Python backend...${NC}"
ensure_python_venv "$PROJECT_ROOT" || exit 1

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - bash 2>/dev/null)" || true

VENV_ACTIVATE="$PROJECT_ROOT/backend/venv/bin/activate"
if [ -f "$PROJECT_ROOT/backend/venv/Scripts/activate" ]; then
    VENV_ACTIVATE="$PROJECT_ROOT/backend/venv/Scripts/activate"
fi

echo "Activating virtual environment..."
. "$VENV_ACTIVATE"

echo "Installing dependencies..."
pip install -r "$PROJECT_ROOT/backend/requirements.txt" 2>&1 || {
    echo -e "${RED}ERROR: Failed to install Python dependencies${NC}"
    exit 1
}
echo -e "${GREEN}Backend Python packages installed!${NC}"
echo ""

echo -e "${GREEN}[6/6] Setting up frontend...${NC}"
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
ensure_node_deps "$PROJECT_ROOT" || exit 1
echo ""

echo -e "${GREEN}[7/7] Running database migrations...${NC}"
cd "$PROJECT_ROOT/backend"
export PYTHONPATH="$PROJECT_ROOT"
"$PROJECT_ROOT/backend/venv/bin/alembic" upgrade head
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