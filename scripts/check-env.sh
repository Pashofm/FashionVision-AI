#!/bin/bash
# FashionVision-AI - Security Check Script
# Verifies that no .env files with credentials are committed to the repository

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=============================================="
echo "  FashionVision-AI - Security Check"
echo "=============================================="
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

echo "Checking for .env files in repository..."

# Check if .env files are tracked in git
if git ls-files 2>/dev/null | grep -qE "^\.env$"; then
    echo -e "${RED}ERROR: .env file is tracked in git!${NC}"
    echo "  Run: git rm --cached .env"
    ERRORS=$((ERRORS + 1))
fi

if git ls-files 2>/dev/null | grep -qE "^backend/\.env$"; then
    echo -e "${RED}ERROR: backend/.env file is tracked in git!${NC}"
    echo "  Run: git rm --cached backend/.env"
    ERRORS=$((ERRORS + 1))
fi

# Check for actual .env files with credentials in the working directory
if [ -f ".env" ]; then
    if grep -q "your_password" .env 2>/dev/null || ! grep -q "CLOUDINARY_API_SECRET=your" .env; then
        echo -e "${RED}WARNING: .env exists and may contain real credentials!${NC}"
        echo "  Verify this file is in .gitignore and not committed"
    fi
fi

if [ -f "backend/.env" ]; then
    echo -e "${RED}WARNING: backend/.env exists and may contain real credentials!${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check .gitignore for proper patterns
if ! grep -q "backend/\.env" .gitignore 2>/dev/null; then
    echo -e "${YELLOW}WARNING: .gitignore should include 'backend/.env'${NC}"
fi

# Verify .env.template exists and has proper structure
if [ ! -f ".env.template" ]; then
    echo -e "${RED}ERROR: .env.template not found!${NC}"
    ERRORS=$((ERRORS + 1))
else
    if grep -q "your_password_here" .env.template; then
        echo -e "${GREEN}OK: .env.template exists with placeholder values${NC}"
    fi
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}Security check passed!${NC}"
    exit 0
else
    echo -e "${RED}Found $ERRORS error(s). Please fix above issues.${NC}"
    exit 1
fi