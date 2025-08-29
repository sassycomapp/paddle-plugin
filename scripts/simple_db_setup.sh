#!/bin/bash
# Simple database setup for Anvil apps
set -e

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-anvil_app}"

# Check if database exists
if ! psql -h $DB_HOST -p $DB_PORT -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1; then
    echo "Creating database $DB_NAME..."
    createdb -h $DB_HOST -p $DB_PORT -U postgres $DB_NAME
fi

# Run migrations if they exist
if [ -d "src/database/migrations" ]; then
    echo "Running database migrations..."
    for migration in src/database/migrations/*.sql; do
        if [ -f "$migration" ]; then
            echo "Running $migration"
            psql -h $DB_HOST -p $DB_PORT -U postgres -d $DB_NAME -f "$migration"
        fi
    done
fi

# Load schema if anvil.yaml exists
if [ -f "anvil.yaml" ]; then
    echo "Loading schema from anvil.yaml..."
    python scripts/load_anvil_schema.py
fi

echo "Database setup completed!"