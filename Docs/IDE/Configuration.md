# Ultimate Configuration Reference

This document provides a comprehensive reference of all configurations in the system, organized by category.

## Table of Contents
1. [Agent Configuration](#agent-configuration)
2. [MCP Server Configuration](#mcp-server-configuration)
3. [Environment Variables](#environment-variables)
4. [Container Orchestration](#container-orchestration)
5. [Tool Mappings](#tool-mappings)
6. [Service Configuration](#service-configuration)

## Agent Configuration

### agent_manifest.yaml
Defines system agents and their dependencies:
```yaml
agents:
  orchestrator:
    description: "Orchestrates workflow between agents"
    entry_point: "agents/orchestrator.py"
    dependencies: []
  
  memory_agent:
    description: "Manages context persistence"
    entry_point: "agents/memory_agent.py"
    dependencies: ["orchestrator"]

  secret_agent:
    description: "Handles credentials securely"
    entry_point: "agents/secret_agent.py"
    dependencies: ["orchestrator"]

  logger_agent:
    description: "Monitors system and agent activities"
    entry_point: "agents/logger_agent.py"
    dependencies: ["orchestrator"]
```

## MCP Server Configuration

### .vscode/mcp.json
Configures all MCP servers:
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        ".",
        "/tmp"
      ],
      "env": {}
    },
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": ""
      }
    },
    "postgres": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://postgres:2001@localhost:5432/postgres"
      ],
      "env": {}
    },
    // ... other server configurations
  }
}
```

## Environment Variables

### .env.example
Template for environment variables:
```env
# API Keys (Required to enable respective provider)
ANTHROPIC_API_KEY="your_anthropic_api_key_here"
PERPLEXITY_API_KEY="your_perplexity_api_key_here"
OPENAI_API_KEY="your_openai_api_key_here"
GOOGLE_API_KEY="your_google_api_key_here"
MISTRAL_API_KEY="your_mistral_key_here"
XAI_API_KEY="YOUR_XAI_KEY_HERE"
GROQ_API_KEY="YOUR_GROQ_KEY_HERE"
OPENROUTER_API_KEY="YOUR_OPENROUTER_KEY_HERE"
AZURE_OPENAI_API_KEY="your_azure_key_here"
OLLAMA_API_KEY="your_ollama_api_key_here"
GITHUB_API_KEY="your_github_api_key_here"
```

## Container Orchestration

### podman-compose.yml
Defines container services:
```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: 2001
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data

  PGvector:
    image: PGvector/"Placeholder"
    ports:
      - "8000:8000"
    environment:
      - "Placeholder"_SERVER_HOST=0.0.0.0
      - "Placeholder"_SERVER_HTTP_PORT=8000
    volumes:
      - "Placeholder"-data:/"Placeholder"/"Placeholder"

volumes:
  postgres-data:
  "Placeholder"-data:
```

## Tool Mappings

### agent_tools_map.yaml
Maps agents to their tools:
```yaml
orchestrator:
  tools:
    - "file-mcp"
    - "vscode-mcp"
    - "rag-mcp"

memory_agent:
  tools:
    - "file-mcp"
    - "rag-mcp"

secret_agent:
  tools:
    - "secrets-manager-mcp"

logger_agent:
  tools:
    - "logging-telemetry-mcp"
```

## Service Configuration

### Service Endpoints
- **PostgreSQL**: `postgresql://postgres:2001@localhost:5432/postgres`
- **PGvector**: `http://localhost:8000`
- **MCP Memory Service**: `uv --directory mcp_servers/mcp-memory-service run mcp-memory-server`

### Path Configurations
- **Memory Bank Path**: `memorybank/`
- **PGvector Data Path**: `mcp_servers/mcp-memory-service/data/"Placeholder"_db`
- **Backups Path**: `mcp_servers/mcp-memory-service/data/backups`
