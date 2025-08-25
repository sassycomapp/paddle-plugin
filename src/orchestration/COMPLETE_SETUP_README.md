# AG2 Orchestrator - Complete Setup Guide

This guide provides comprehensive instructions for setting up the AG2 Orchestrator system with all dependencies and services.

## Overview

The AG2 Orchestrator is a sophisticated multi-agent system that requires several services to function properly:
- **PGvector**: Vector database for RAG (Retrieval-Augmented Generation)
- **PostgreSQL**: Relational database for agent memory and state management
- **MCP Servers**: Multiple MCP (Model Context Protocol) servers for various functionalities
- **Python Environment**: Core orchestrator and agent logic
- **Node.js Environment**: MCP servers and web services

## Prerequisites

### Required Software
- **Python 3.8+** (with pip)
- **Node.js 16+** (with npm)
- **Docker Desktop** (for PGvector and PostgreSQL)
- **Git** (for version control)

### API Keys Required
- **OpenRouter API Key** (recommended) OR OpenAI API Key OR Azure OpenAI credentials
- **Brave Search API Key** (for web search functionality)

## Quick Start

### Windows
1. Open Command Prompt or PowerShell as Administrator
2. Navigate to the project directory
3. Run the complete setup:
   ```cmd
   cd src\orchestration
   complete_setup.bat
   ```

### macOS/Linux
1. Open Terminal
2. Navigate to the project directory
3. Run the complete setup:
   ```bash
   cd src/orchestration
   python complete_setup.py
   ```

## Manual Setup (Step by Step)

### 1. Install Dependencies

#### Python Dependencies
```bash
cd src/orchestration
pip install -r requirements.txt
```

#### Node.js Dependencies
```bash
cd mcp_servers
npm install
```

### 2. Configure Environment Variables

Create a `.env` file in `src/orchestration/` with your API keys:

```env
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

# Database Configuration
DATABASE_URL=postgresql://postgres:2001@localhost:5432/postgres

# PGvector Configuration
"Placeholder"_URL=http://localhost:8000
```

### 3. Start Required Services

#### Start PGvector (Vector Database)
```bash
# Using Docker
docker run --rm -d --name PGvector -p 8000:8000 PGvector/"Placeholder":latest
```

#### Start PostgreSQL (Agent Memory)
```bash
# Using Docker
docker run --rm -d --name postgres -p 5432:5432 \
  -e POSTGRES_PASSWORD=2001 \
  -e POSTGRES_DB=postgres \
  postgres:15
```

### 4. Start MCP Servers

#### Option 1: Start All Servers
```bash
cd mcp_servers
npm start
```

#### Option 2: Start Individual Servers
```bash
# Scheduler Server
node mcp-scheduler-server.js

# RAG Server
node rag-mcp-server.js

# Agent Memory Server
node agent-memory/index.js

# Brave Search Server
node brave-search-mcp-server.js

# Logging & Telemetry Server
node logging-telemetry-mcp-server.js
```

### 5. Test the Setup

Run the comprehensive test suite:
```bash
cd src/orchestration
python test_ag2_system.py
```

## Service Architecture

### Core Services
```
┌─────────────────────────────────────────┐
│           AG2 Orchestrator              │
│         (Python + FastAPI)              │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐    ┌───▼───┐    ┌───▼───┐
│PGvector│    │PostgreSQL│    │MCP Servers│
│:8000   │    │:5432     │    │:various   │
└────────┘    └────────┘    └────────┘
```

### MCP Servers
- **Scheduler Server**: Port 3001 - Task scheduling and management
- **RAG Server**: Port 3002 - Retrieval-augmented generation
- **Agent Memory Server**: Port 3003 - Agent memory management
- **Brave Search Server**: Port 3004 - Web search integration
- **Logging Server**: Port 3005 - Logging and telemetry

## Troubleshooting

### Common Issues

#### 1. Docker Not Running
**Error**: "Cannot connect to Docker daemon"
**Solution**: 
- Start Docker Desktop
- Ensure Docker is running: `docker ps`

#### 2. Port Already in Use
**Error**: "Port 5432 is already in use"
**Solution**:
- Find process using port: `lsof -i :5432` (Linux/Mac) or `netstat -ano | findstr :5432` (Windows)
- Kill the process or use different ports

#### 3. API Key Issues
**Error**: "Invalid API key" or "Authentication failed"
**Solution**:
- Verify API keys in `.env` file
- Check API key permissions
- Ensure correct API endpoint configuration

#### 4. Python Import Errors
**Error**: "ModuleNotFoundError: No module named 'psycopg2'"
**Solution**:
```bash
pip install psycopg2-binary
```

#### 5. Node.js Module Errors
**Error**: "Cannot find module 'express'"
**Solution**:
```bash
cd mcp_servers
npm install
```

### Health Checks

#### Check Service Status
```bash
# Check all services
python health_check.py

# Check individual services
curl http://localhost:8000/api/v1/heartbeat  # PGvector
curl http://localhost:3001/health           # Scheduler
curl http://localhost:3002/health           # RAG
curl http://localhost:3003/health           # Agent Memory
curl http://localhost:3004/health           # Brave Search
curl http://localhost:3005/health           # Logging
```

## Development Mode

### Running in Development
```bash
# Start services in development mode
python complete_setup.py --dev

# Run with specific configuration
python complete_setup.py --config dev
```

### Testing
```bash
# Run all tests
python -m pytest Test\ Bank\System\ Tests\AG2_Orchestration_Tests\

# Run specific test categories
python -m pytest Test\ Bank\System\ Tests\AG2_Orchestration_Tests\unit\
python -m pytest Test\ Bank\System\ Tests\AG2_Orchestration_Tests\integration\
python -m pytest Test\ Bank\System\ Tests\AG2_Orchestration_Tests\e2e\
```

## Production Deployment

### Docker Compose (Recommended)
```yaml
version: '3.8'
services:
  PGvector:
    image: PGvector/"Placeholder":latest
    ports:
      - "8000:8000"
    
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: 2001
      POSTGRES_DB: postgres
    ports:
      - "5432:5432"
    
  ag2-orchestrator:
    build: .
    ports:
      - "8001:8001"
    depends_on:
      - PGvector
      - postgres
    environment:
      - DATABASE_URL=postgresql://postgres:2001@postgres:5432/postgres
      - "Placeholder"_URL=http://PGvector:8000
```

### Environment Variables for Production
```env
# Production settings
ENVIRONMENT=production
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:password@host:5432/dbname
"Placeholder"_URL=http://PGvector:8000
REDIS_URL=redis://localhost:6379
```

## Support and Resources

### Documentation
- [AG2 Complete Documentation](Docs/Systems_Descriptions/Orchestration%20(AG2)/AG2%20Complete%20Documentation.md)
- [Testing Guide](src/orchestration/TESTING_GUIDE.md)
- [MCP Tools Map](Docs/MCP_Tools/MCP_Tools_Map.md)

### Getting Help
1. Check the troubleshooting section above
2. Review logs in the `logs/` directory
3. Run health checks: `python health_check.py`
4. Check GitHub issues for known problems
5. Contact support with detailed error logs

## Next Steps

After successful setup:
1. **Run Tests**: Execute the test suite to verify everything works
2. **Explore Examples**: Check out the example workflows in `examples/`
3. **Customize Configuration**: Modify `mcp_servers_config.yaml` for your needs
4. **Deploy Agents**: Start creating and deploying your own agents
5. **Monitor Performance**: Use the logging and telemetry features

## Quick Reference

### Essential Commands
```bash
# Start everything
python complete_setup.py

# Test system
python test_ag2_system.py

# Check health
python health_check.py

# View logs
tail -f logs/ag2_orchestrator.log
```

### Service URLs
- **AG2 Orchestrator**: http://localhost:8001
- **PGvector**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Scheduler MCP**: http://localhost:3001
- **RAG MCP**: http://localhost:3002
- **Agent Memory MCP**: http://localhost:3003
- **Brave Search MCP**: http://localhost:3004
- **Logging MCP**: http://localhost:3005
