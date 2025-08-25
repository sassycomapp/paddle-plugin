#!/bin/bash

set -e

echo "🚀 Installing Testing and Validation System..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "⚠️  PostgreSQL is not running on localhost:5432"
    echo "Please start PostgreSQL or update DATABASE_URL in .env"
fi

# Check if Podman is installed
if ! command -v podman &> /dev/null; then
    echo "❌ Podman is not installed. Please install Podman first."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Initialize database
echo "🗄️  Initializing database..."
npm run db:init

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
DATABASE_URL=postgresql://postgres:2001@localhost:5432/postgres
NODE_ENV=development
PORT=3000
EOF
fi

# Install Semgrep for security scanning
echo "🔍 Installing Semgrep..."
pip3 install semgrep || echo "⚠️  Could not install Semgrep. Please install manually: pip3 install semgrep"

# Make scripts executable
chmod +x scripts/*.sh

echo "✅ Testing and Validation System installed successfully!"
echo ""
echo "Next steps:"
echo "1. Start the MCP server: npm start"
echo "2. Run tests: npm test"
echo "3. Run security scan: npm run security-scan"
echo "4. Start with Podman: podman-compose up"
