#!/bin/bash

# AG2 Orchestrator Setup and Test Script
# This script sets up the environment and runs tests

set -e

echo "🚀 AG2 Orchestrator Setup and Test Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js v16 or higher."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip."
    exit 1
fi

print_status "Node.js version: $(node --version)"
print_status "Python version: $(python3 --version)"

# Install Python dependencies
print_status "Installing Python dependencies..."
cd src/orchestration
pip3 install -r requirements.txt

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
cd ../../mcp_servers
npm install

# Check if .env file exists
if [ ! -f "../src/orchestration/.env" ]; then
    print_warning ".env file not found. Creating template..."
    cat > ../src/orchestration/.env << EOF
# OpenRouter (Recommended)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_HTTP_REFERER=http://localhost
OPENROUTER_X_TITLE=AG2 Orchestrator Test

# OR OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# OR Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# Brave Search API Key
BRAVE_API_KEY=your_brave_api_key_here
EOF
    print_warning "Please edit ../src/orchestration/.env with your actual API keys"
fi

# Run MCP server tests
print_status "Running MCP server tests..."
cd ../src/orchestration
python3 test_mcp_servers.py

# Ask user if they want to run full system test
read -p "Do you want to run the full AG2 system test? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Running full AG2 system test..."
    python3 test_ag2_system.py
fi

# Ask user if they want to run LLM-free test
read -p "Do you want to run LLM-free test (MCP servers only)? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Running LLM-free test..."
    python3 test_ag2_system.py --skip-llm
fi

print_status "Setup and testing complete!"
print_status "Check the logs above for any errors or issues."
