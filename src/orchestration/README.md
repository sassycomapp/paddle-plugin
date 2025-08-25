# AG2 Orchestrator System

A sophisticated AI orchestration system that integrates AG2 (AutoGen 2) with MCP (Model Context Protocol) servers to provide advanced AI capabilities including RAG (Retrieval-Augmented Generation), persistent memory, and web search integration.

## 🎯 Overview

The AG2 Orchestrator System combines:
- **AG2 (AutoGen 2)**: Advanced multi-agent AI framework
- **MCP Servers**: Modular tool integration via Model Context Protocol
- **RAG**: Document storage and retrieval capabilities
- **Memory**: Persistent conversation and agent memory
- **Search**: Web search integration via Brave Search API

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AG2 Orchestrator                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   AG2 Agent     │  │   AG2 Agent     │  │     ...     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              MCP Server Manager                          │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │ RAG Server  │  │   Memory    │  │ Search Server   │ │ │
│  │  │   (MCP)     │  │   Server    │  │     (MCP)       │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

**Windows:**
```cmd
cd src\orchestration
setup_and_test.bat
```

**Linux/macOS:**
```bash
cd src/orchestration
./setup_and_test.sh
```

### Option 2: Manual Setup

1. **Install Dependencies**
   ```bash
   # Python dependencies
   pip install -r requirements.txt
   
   # Node.js dependencies
   cd mcp_servers
   npm install
   ```

2. **Configure Environment**
   ```bash
   # Copy and edit .env file
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run Tests**
   ```bash
   # Test MCP servers only
   python test_mcp_servers.py
   
   # Test full system
   python test_ag2_system.py
   
   # Test without LLM (MCP servers only)
   python test_ag2_system.py --skip-llm
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in `src/orchestration/`:

```bash
# OpenRouter (Recommended - supports multiple models)
OPENROUTER_API_KEY=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
OPENROUTER_HTTP_REFERER=http://localhost
OPENROUTER_X_TITLE=AG2 Orchestrator

# OR OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# OR Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# Brave Search API (for web search)
BRAVE_API_KEY=BSAk3We2xKQFoOgoQJVObWmYGrCd-J0
```

### MCP Server Configuration

Edit `mcp_servers_config.yaml` to configure MCP servers:

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
      BRAVE_API_KEY: "BSAk3We2xKQFoOgoQJVObWmYGrCd-J0"
```

## 📋 Available MCP Tools

### RAG Server
- `add_document`: Store documents for retrieval
- `search_documents`: Search stored documents
- `get_document`: Retrieve specific document
- `delete_document`: Remove document

### Agent Memory Server
- `store_memory`: Store conversation memory
- `retrieve_memory`: Retrieve specific memory
- `search_memories`: Search through memories
- `delete_memory`: Remove memory

### Brave Search Server
- `brave_web_search`: Search the web
- `brave_news_search`: Search for news

## 🧪 Testing

### Test Scripts

1. **MCP Server Tests**
   ```bash
   python test_mcp_servers.py
   ```

2. **Full System Test**
   ```bash
   python test_ag2_system.py
   ```

3. **LLM-Free Test**
   ```bash
   python test_ag2_system.py --skip-llm
   ```

### Manual Testing

Test individual MCP servers:
```bash
# RAG server
node mcp_servers/rag-mcp-server.js

# Agent Memory server
node mcp_servers/agent-memory/index.js

# Brave Search server
node mcp_servers/brave-search-mcp-server.js
```

## 🔍 Troubleshooting

### Common Issues

1. **"Module not found" errors**
   ```bash
   pip install -r requirements.txt
   npm install
   ```

2. **MCP server connection failures**
   - Check Node.js version: `node --version`
   - Verify MCP server files exist
   - Check server logs for specific errors

3. **LLM API errors**
   - Verify API keys are set correctly
   - Check internet connectivity
   - Verify API key permissions

4. **PGvector connection issues**
   - Ensure PGvector is running: `"Placeholder" run --host localhost --port 8000`
   - Check if collection exists

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Performance

### Optimization Tips

1. **PGvector**: Use persistent storage for better performance
2. **Memory**: Implement memory cleanup strategies
3. **Search**: Cache frequent search results
4. **API Calls**: Implement rate limiting and caching

### Monitoring

Monitor these metrics:
- Response times
- API usage
- Memory consumption
- Error rates

## 🔐 Security

### Best Practices

1. **API Keys**: Never commit API keys to version control
2. **Environment Variables**: Use `.env` files for sensitive configuration
3. **Network Security**: Ensure MCP servers only accept trusted connections
4. **Input Validation**: Validate all user inputs

### Security Checklist

- [ ] API keys stored in environment variables
- [ ] No hardcoded credentials in source code
- [ ] HTTPS used for external API calls
- [ ] Input validation implemented
- [ ] Rate limiting configured

## 🚀 Deployment

### Production Deployment

1. **Environment Configuration**
   ```bash
   # Production environment variables
   export AG2_ENV=production
   export LOG_LEVEL=INFO
   ```

2. **Docker Deployment**
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["python", "ag2_orchestrator.py"]
   ```

3. **Scaling Considerations**
   - Use load balancers for MCP servers
   - Implement caching layers
   - Monitor resource usage
   - Use container orchestration (Kubernetes)

## 📚 Documentation

- [Testing Guide](TESTING_GUIDE.md) - Comprehensive testing instructions
- [API Documentation](docs/api.md) - API reference
- [Architecture Guide](docs/architecture.md) - System architecture details
- [Deployment Guide](docs/deployment.md) - Production deployment instructions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support:
1. Check the [troubleshooting section](#troubleshooting)
2. Review the [testing guide](TESTING_GUIDE.md)
3. Open an issue on GitHub
4. Contact the development team

## 🔄 Changelog

### v1.0.0
- Initial release
- AG2 integration with MCP servers
- RAG, Memory, and Search capabilities
- Comprehensive testing suite
- Production-ready configuration
