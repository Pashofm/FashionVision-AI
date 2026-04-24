#!/bin/bash
# Teardown Test Database Script
# Cleans up the test database after tests complete

set -e

# Configuration
DB_NAME="fashionvision_ai_test"
DB_USER="fashionvision_ai_user"
DB_PASS="fashionvision_ai_pass"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"

echo "=== Tearing down test database ==="

# Drop database if exists
if PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1; then
    echo "Dropping database '$DB_NAME'..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "DROP DATABASE $DB_NAME"
    echo "Database dropped successfully"
else
    echo "Database '$DB_NAME' does not exist, nothing to do"
fi

echo "=== Teardown complete ==="
