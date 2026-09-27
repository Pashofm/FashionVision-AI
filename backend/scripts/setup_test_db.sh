#!/bin/bash
# Setup Test Database Script
# Creates and configures the PostgreSQL test database

set -e

# Configuration
DB_NAME="fashionvision_ai_test"
DB_USER="fashionvision_ai_user"
DB_PASS="fashionvision_ai_pass"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"

echo "=== Setting up test database ==="

# Check if database exists
if PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1; then
    echo "Database '$DB_NAME' already exists"

    # Drop and recreate
    echo "Dropping existing test database..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "DROP DATABASE $DB_NAME"
fi

# Create database
echo "Creating database '$DB_NAME'..."
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME"

echo "=== Test database setup complete ==="
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Host: $DB_HOST:$DB_PORT"

# Export for convenience
export TEST_DATABASE_URL="postgresql+asyncpg://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "Connection string:"
echo "$TEST_DATABASE_URL"
