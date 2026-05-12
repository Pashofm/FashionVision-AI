#!/bin/bash
# FashionVision-AI - Development Start Script
# Inicia los servicios de base de datos para desarrollo
# Uso: ./scripts/dev-start.sh (después de ./scripts/setup.sh)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

if [ -f "$SCRIPT_DIR/common_versions.sh" ]; then
    source "$SCRIPT_DIR/common_versions.sh"
fi

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

check_environment() {
    local GREEN='\033[0;32m'
    local YELLOW='\033[1;33m'
    local RED='\033[0;31m'
    local NC='\033[0m'

    echo -e "${GREEN}[1/4] Checking environment...${NC}"

    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        if [ -f "$PROJECT_ROOT/.env.template" ]; then
            echo -e "${YELLOW}No .env found. Creating from template...${NC}"
            cp "$PROJECT_ROOT/.env.template" "$PROJECT_ROOT/.env"
        else
            echo -e "${RED}ERROR: No .env.template found!${NC}"
            exit 1
        fi
    fi

    validate_and_fix_env

    set -a
    source "$PROJECT_ROOT/.env"
    set +a

    if [ ! -d "$PROJECT_ROOT/backend/venv" ]; then
        echo -e "${RED}ERROR: Python virtual environment not found.${NC}"
        echo -e "${RED}Run './scripts/setup.sh' first to set up the environment.${NC}"
        exit 1
    fi

    if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
        echo -e "${RED}ERROR: Frontend dependencies not installed.${NC}"
        echo -e "${RED}Run './scripts/setup.sh' first to set up the environment.${NC}"
        exit 1
    fi

    echo -e "${GREEN}Environment check passed!${NC}"
    echo ""
}

start_databases() {
    local GREEN='\033[0;32m'
    local YELLOW='\033[1;33m'
    local RED='\033[0;31m'
    local NC='\033[0m'

    echo -e "${GREEN}[2/4] Starting database (Docker)...${NC}"
    docker compose up -d db
    echo "Waiting for database to be healthy..."
    sleep 5

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

    echo -e "${GREEN}[3/4] Starting pgAdmin (Docker)...${NC}"
    docker compose up -d pgadmin
    echo -e "${GREEN}pgAdmin is ready!${NC}"
    echo ""
}

run_migrations() {
    local GREEN='\033[0;32m'
    local YELLOW='\033[1;33m'
    local RED='\033[0;31m'
    local NC='\033[0m'

    echo -e "${GREEN}[4/4] Running database migrations (Alembic)...${NC}"

    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init - bash 2>/dev/null)" || true

    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

    cd "$PROJECT_ROOT/backend"
    export PYTHONPATH="$PROJECT_ROOT"

    "$PROJECT_ROOT/backend/venv/bin/alembic" upgrade head
    echo -e "${GREEN}Migrations applied!${NC}"
    echo ""
}

print_instructions() {
    local GREEN='\033[0;32m'
    local YELLOW='\033[1;33m'
    local NC='\033[0m'

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
}

echo "=============================================="
echo "  FashionVision-AI - Development Mode Start"
echo "=============================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

OS_TYPE=$(detect_os)
echo "Detected OS: $OS_TYPE"
echo ""

check_environment
start_databases
run_migrations
print_instructions