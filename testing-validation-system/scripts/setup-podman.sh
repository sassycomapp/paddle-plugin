#!/bin/bash

set -e

echo "🚀 Setting up Podman environment for Testing and Validation System..."

# Check if Podman is installed
if ! command -v podman &> /dev/null; then
    echo "❌ Podman is not installed. Please install Podman first."
    exit 1
fi

# Check if podman-compose is available
if ! command -v podman-compose &> /dev/null; then
    echo "📦 Installing podman-compose..."
    pip3 install podman-compose
fi

# Create Podman network if it doesn't exist
if ! podman network ls | grep -q testing-network; then
    echo "🌐 Creating Podman network..."
    podman network create testing-network
fi

# Build images
echo "🏗️  Building container images..."
podman-compose build

# Start services
echo "🚀 Starting services..."
podman-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Initialize database
echo "🗄️  Initializing database..."
podman-compose exec postgres psql -U test_user -d test_db -f /docker-entrypoint-initdb.d/init-test-db.sql

echo "✅ Podman environment setup complete!"
echo ""
echo "Available commands:"
echo "  podman-compose up          - Start all services"
echo "  podman-compose down        - Stop all services"
echo "  podman-compose logs -f     - View logs"
echo "  podman-compose run test    - Run tests"
chmod +x "$0"
