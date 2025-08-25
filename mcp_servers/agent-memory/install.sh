#!/bin/bash

# Agent Memory MCP Server Installation Script

echo "🧠 Installing Agent Memory MCP Server..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "❌ PostgreSQL is not running on localhost:5432"
    echo "Please start PostgreSQL and ensure it's accessible"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Create environment file
echo "⚙️  Creating environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file - please update with your PostgreSQL credentials"
else
    echo "✅ .env file already exists"
fi

# Create database tables
echo "🗄️  Setting up database tables..."
if [ -f create_memory_tables.sql ]; then
    # Try to connect with default credentials
    PGPASSWORD="2001" psql -U postgres -d postgres -f create_memory_tables.sql
    if [ $? -eq 0 ]; then
        echo "✅ Database tables created successfully"
    else
        echo "❌ Failed to create database tables"
        echo "Please run manually: psql -U postgres -d postgres -f create_memory_tables.sql"
    fi
else
    echo "❌ create_memory_tables.sql not found"
fi

# Test the installation
echo "🧪 Testing the installation..."
node test-proper.js

echo ""
echo "🎉 Agent Memory MCP Server installation complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your PostgreSQL credentials if needed"
echo "2. Add the server to your MCP configuration"
echo "3. Start using the memory tools!"
