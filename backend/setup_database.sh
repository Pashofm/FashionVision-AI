#!/bin/bash
# FashionVision AI - Database Setup Script

set -e

echo "=== FashionVision AI Database Setup ==="

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "Starting PostgreSQL..."
    sudo systemctl start postgresql  # Linux
    # Or on macOS: brew services start postgresql
fi

# Get current user
CURRENT_USER=$(whoami)
DB_NAME="fashionvision"

echo "Creating user role if needed..."
sudo -u postgres psql -c "CREATE ROLE $CURRENT_USER WITH LOGIN SUPERUSER;" 2>/dev/null || true

echo "Creating database..."
sudo -u postgres createdb "$DB_NAME" 2>/dev/null || echo "Database '$DB_NAME' already exists"

echo "Loading schema..."
sudo -u postgres psql -d "$DB_NAME" -f "$(dirname "$0")/database/schema.sql"

echo "=== Setup Complete ==="
echo ""
echo "To run the backend:"
echo "  cd backend"
echo "  python -m venv venv && source venv/bin/activate"
echo "  pip install -r requirements.txt"
echo "  uvicorn main:app --reload --port 8000"
echo ""
echo "API available at: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"