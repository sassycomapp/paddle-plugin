# AG2 Orchestrator - Complete Setup Guide

This guide provides comprehensive instructions for setting up the AG2 Orchestrator system with all required services and dependencies.

## Quick Start

### Option 1: Automated Setup (Recommended)

#### Windows
```bash
cd src\orchestration
complete_setup.bat
```

#### Linux/Mac
```bash
cd src/orchestration
python complete_setup.py
```

### Option 2: Manual Setup

Follow the step-by-step instructions below for manual setup.

## Prerequisites

### Required Software
- **Python 3.8+** (with pip)
- **Node.js 16+** (with npm)
- **Docker Desktop** (for PGvector and PostgreSQL)

### API Keys Required
- **OpenRouter API Key** (recommended) OR
- **OpenAI API Key** OR
- **Azure OpenAI API Key**
- **Brave Search API Key** (for web search functionality)

## Step-by-Step Setup

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

Create a `.env` file in `src/orchestration/`:

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

#### Start PGvector
```bash
# Using Docker
docker run --rm -d --name PGvector -p 8000:8000 PGvector/"Placeholder":latest
```

#### Start PostgreSQL
```bash
# Using Docker
docker run --rm -d --name postgres -p 5432:5432 \
  -e POSTGRES_PASSWORD=2001 \
  -e POSTGRES_DB=postgres \
  postgres:15
```

### 4. Create Database Tables

The system will automatically create required tables on first run, but you can manually create them:

```sql
-- Connect to PostgreSQL
psql -h localhost -U postgres -d postgres

-- Create tables
CREATE TABLE IF NOT EXISTS episodic_memory (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255),
    session_id VARCHAR(255),
    context JSONB,
    memory_type VARCHAR(50),
    relevance_score FLOAT,
    tags TEXT[],
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS semantic_memory (
    id SERIAL PRIMARY KEY,
    entity VARCHAR(255),
    data JSONB,
    category VARCHAR(100),
    agent_id VARCHAR(255),
    tags TEXT[],
    access_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    UNIQUE(entity, agent_id)
);

CREATE TABLE IF NOT EXISTS working_memory (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255),
    session_id VARCHAR(255),
    key VARCHAR(255),
    value JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    UNIQUE(agent_id, session_id, key)
);
```

### 5. Test MCP Servers

```bash
cd src/orchestration
python test_mcp_servers.py
```

### 6. Run System Tests

```bash
cd src/orchestration
python test_ag2_system.py
```

## Service Architecture

### Core Services
- **PGvector**: Vector database for RAG (Retrieval-Augmented Generation)
- **PostgreSQL**: Persistent storage for agent memory
- **MCP Servers**: Modular components for search, memory, and RAG functionality

### MCP Servers
1. **Brave Search MCP Server**: Web search functionality
2. **Agent Memory MCP Server**: Persistent memory management
3. **RAG MCP Server**: Document retrieval and generation

## Troubleshooting

### Common Issues

#### 1. Docker Not Starting
- **Windows**: Ensure Docker Desktop is running
- **Linux**: Check if Docker daemon is running: `sudo systemctl start docker`

#### 2. Port Conflicts
- **PGvector**: Uses port 8000
- **PostgreSQL**: Uses port 5432
- Check if ports are available: `netstat -an | findstr :8000`

#### 3. API Key Issues
- Ensure API keys are valid and have sufficient credits
- Check rate limits for your API provider

#### 4. Database Connection Issues
- Ensure PostgreSQL is running on port 5432
- Check credentials in .env file
- Verify database exists: `psql -h localhost -U postgres -d postgres`

### Debug Commands

#### Check Service Status
```bash
# Check Docker containers
docker ps

# Check PGvector
curl http://localhost:8000/api/v1/heartbeat

# Check PostgreSQL
psql -h localhost -U postgres -d postgres -c "SELECT version();"
```

#### View Logs
```bash
# Docker logs
docker logs PGvector
docker logs postgres

# Application logs
cd src/orchestration
python test_mcp_servers.py --verbose
```

## Development Mode

### Running Individual Components

#### Start PGvector Only
```bash
docker run --rm -d --name PGvector -p 8000:8000 PGvector/"Placeholder":latest
```

#### Start PostgreSQL Only
```bash
docker run --rm -d --name postgres -p 5432:5432 \
  -e POSTGRES_PASSWORD=2001 \
  -e POSTGRES_DB=postgres \
  postgres:15
```

#### Test Individual MCP Server
```bash
cd mcp_servers
node brave-search-mcp-server.js
```

### Environment Variables for Development

Create a `.env.development` file for development-specific settings:

```env
# Development settings
DEBUG=true
LOG_LEVEL=DEBUG
TEST_MODE=true

# Development API endpoints
"Placeholder"_URL=http://localhost:8000
DATABASE_URL=postgresql://postgres:2001@localhost:5432/postgres
```

## Production Deployment

### Docker Compose Setup

Create a `docker-compose.yml` file for production:

```yaml
version: '3.8'
services:
  PGvector:
    image: PGvector/"Placeholder":latest
    ports:
      - "8000:8000"
    volumes:
      - "Placeholder"_data:/"Placeholder"/"Placeholder"

  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  "Placeholder"_data:
  postgres_data:
```

### Production Environment Variables

```env
# Production settings
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production

# Production database
DATABASE_URL=postgresql://user:password@localhost:5432/ag2_production

# Production PGvector
"Placeholder"_URL=http://localhost:8000
```

## Support

### Getting Help
1. Check the troubleshooting section above
2. Review logs for specific error messages
3. Ensure all prerequisites are installed
4. Verify API keys and environment variables

### Reporting Issues
When reporting issues, please include:
- Operating system and version
- Python and Node.js versions
- Docker version
- Complete error messages
- Steps to reproduce the issue

## Next Steps

After successful setup:
1. Run the system tests: `python test_ag2_system.py`
2. Explore the orchestrator: `python ag2_orchestrator.py`
3. Review the API documentation
4. Start building your agents!

## API Documentation

### Available Endpoints
- **GET /health**: System health check
- **POST /agents**: Create new agent
- **GET /agents/{id}**: Get agent details
- **POST /agents/{id}/execute**: Execute agent task
- **GET /agents/{id}/memory**: Get agent memory
- **POST /agents/{id}/memory**: Update agent memory

### Example Usage
```python
import requests

# Health check
response = requests.get('http://localhost:8000/health')
print(response.json())

# Create agent
agent_data = {
    "name": "test_agent",
    "model": "gpt-4o-mini",
    "memory_config": {
        "type": "postgresql",
        "connection_string": "postgresql://..."
    }
}
response = requests.post('http://localhost:8000/agents', json=agent_data)
print(response.json())
```

## License

This project is licensed under the MIT License. See LICENSE file for details.
