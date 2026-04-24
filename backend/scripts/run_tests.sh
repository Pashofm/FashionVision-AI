#!/bin/bash
# Run Backend Tests Script
# Executes the test suite with proper environment setup

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
DB_NAME="fashionvision_ai_test"
DB_USER="fashionvision_ai_user"
DB_PASS="fashionvision_ai_pass"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== Running Backend Tests ==="

# Change to backend directory
cd "$BACKEND_DIR"

# Setup environment
export PYTHONPATH="$BACKEND_DIR"
export SKIP_DB_TESTS="false"
export TEST_DATABASE_URL="postgresql+asyncpg://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME"

echo "Test Database: $TEST_DATABASE_URL"
echo ""

# Parse arguments
MODULES=""
COVERAGE=false
VERBOSE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE="-v"
            shift
            ;;
        --module)
            MODULES="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --coverage    Generate coverage report"
            echo "  --verbose     Verbose output"
            echo "  --module MOD  Run specific module tests (e.g., sessions, inventory)"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="python -m pytest tests/ -x --tb=short"

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=. --cov-report=term-missing --cov-report=html"
fi

if [ -n "$VERBOSE" ]; then
    PYTEST_CMD="$PYTEST_CMD $VERBOSE"
fi

if [ -n "$MODULES" ]; then
    PYTEST_CMD="$PYTEST_CMD tests/modules/$MODULES/"
fi

# Run tests
echo "Running: $PYTEST_CMD"
echo ""

if eval "$PYTEST_CMD"; then
    echo ""
    echo -e "${GREEN}=== Tests Passed ===${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}=== Tests Failed ===${NC}"
    exit 1
fi
