# AG2 Orchestrator Testing Guide

This guide provides comprehensive instructions for testing the AG2 orchestrator system with MCP servers.

## Prerequisites

1. **Node.js** (v16 or higher) - Required for MCP servers
2. **Python** (3.8 or higher) - Required for AG2 orchestrator
3. **Required packages**:
   ```bash
   pip install autogen-core autogen-agentchat pyyaml
   npm install -g @modelcontextprotocol/sdk
   ```

## Environment Setup

### 1. Set up API Keys

Create a `.env` file in `src/orchestration/`:

```bash
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
```

### 2. Install MCP Server Dependencies

```bash
# Install dependencies for all MCP servers
cd mcp_servers
npm install

# Install specific server dependencies
cd agent-memory
npm install

cd ../brave-search-integration
npm install
```

## Testing MCP Servers Individually

### Test 1: Basic MCP Server Connection

```bash
cd src/orchestration
python test_mcp_servers.py
```

This will test:
- RAG server connection
- Agent Memory server connection
- Brave Search server connection

### Test 2: Full AG2 System Test

```bash
cd src/orchestration
python test_ag2_system.py
```

This will:
1. Initialize LLM configuration
2. Set up all MCP servers
3. Create AG2 agent with tools
4. Run sample queries

### Test 3: Skip LLM Test (for MCP server testing only)

```bash
cd src/orchestration
python test_ag2_system.py --skip-llm
```

## MCP Server Configuration

The `mcp_servers_config.yaml` file configures which MCP servers to use:

```yaml
mcpServers:
  rag:
    command: "node"
    args: ["../../mcp_servers/rag-mcp-server.js"]
    description: "RAG server for document storage and retrieval"
    env:
      "Placeholder"_URL: "http://localhost:8000"
      COLLECTION_NAME: "ag2_documents"
  
  agent-memory:
    command: "node"
    args: ["../../mcp_servers/agent-memory/index.js"]
    description: "Agent memory and conversation history"
    env:
      MEMORY_FILE: "agent_memory.json"
  
  brave-search:
    command: "node"
    args: ["../../mcp_servers/brave-search-mcp-server.js"]
    description: "Brave search integration"
    env:
      BRAVE_API_KEY: "your_brave_api_key_here"
```

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   ```bash
   pip install -r requirements.txt
   npm install
   ```

2. **MCP server connection failures**
   - Check if Node.js is installed: `node --version`
   - Verify MCP server files exist in `mcp_servers/`
   - Check server logs for specific errors

3. **LLM API errors**
   - Verify API keys are set correctly
   - Check internet connectivity
   - Verify API key permissions

4. **PGvector connection issues**
   - Ensure PGvector is running: `"Placeholder" run --host localhost --port 8000`
   - Check if the collection exists

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Manual Testing

Test individual MCP servers:

```bash
# Test RAG server
node mcp_servers/rag-mcp-server.js

# Test Agent Memory server
node mcp_servers/agent-memory/index.js

# Test Brave Search server
node mcp_servers/brave-search-mcp-server.js
```

## Expected Test Results

### Successful MCP Server Test Output:
```
INFO - Starting MCP Server Tests...
INFO - Testing RAG MCP server...
INFO - ✓ RAG server connected
INFO - RAG tools available: ['add_document', 'search_documents', 'get_document', 'delete_document']
INFO - Testing Agent Memory MCP server...
INFO - ✓ Agent Memory server connected
INFO - Agent Memory tools available: ['store_memory', 'retrieve_memory', 'search_memories', 'delete_memory']
INFO - Testing Brave Search MCP server...
INFO - ✓ Brave Search server connected
INFO - Brave Search tools available: ['brave_web_search', 'brave_news_search']
INFO - MCP Server Tests completed
```

### Successful AG2 System Test Output:
```
INFO - Starting AG2 System Test...
INFO - Test: Initializing AG2 Orchestrator...
INFO - Test: AG2 Orchestrator initialized.
INFO - Test: Setting up MCP server: rag (RAG server for document storage and retrieval)
INFO - Test: Successfully set up and created toolkit for MCP server: rag
INFO - Test: Initializing AG2 Agent...
INFO - Test: AG2 Agent initialized.
INFO - Test: Starting sample queries...
INFO - Test: Running query 1/5: 'Hello, introduce yourself.'
Agent: Hello! I'm an AI assistant with access to various tools...
```

## Performance Testing

For load testing, you can modify the test script to run multiple concurrent queries:

```python
async def stress_test():
    queries = ["test query"] * 10
    tasks = [orchestrator.run_query(q) for q in queries]
    results = await asyncio.gather(*tasks)
```

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Environment Variables**: Use `.env` files for sensitive configuration
3. **Network Security**: Ensure MCP servers only accept connections from trusted sources
4. **Input Validation**: All user inputs should be validated before processing

## Next Steps

After successful testing:

1. **Production Deployment**: Use environment-specific configurations
2. **Monitoring**: Set up logging and metrics collection
3. **Scaling**: Consider containerization with Docker
4. **Security**: Implement proper authentication and authorization
