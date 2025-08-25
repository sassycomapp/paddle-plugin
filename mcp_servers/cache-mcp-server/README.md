# Cache Management System

A comprehensive 5-layer intelligent caching architecture for AI applications, built with Python and integrated with the Model Context Protocol (MCP).

## Architecture Overview

The cache management system implements a sophisticated 5-layer architecture:

1. **Predictive Cache (Zero-Token Hinting Layer)**: Anticipates upcoming context/queries and prefetches relevant data
2. **Semantic Cache (Adaptive Prompt Reuse Layer)**: Reuses previously successful prompts and responses
3. **Vector Cache (Embedding-Based Context Selector)**: Selects and reranks context elements based on embedding similarity
4. **Global Knowledge Cache (Fallback Memory)**: Provides fallback knowledge base using persistent LLM training data
5. **Persistent Context Memory (Vector Diary)**: Foundation for longitudinal reasoning across sessions

## Features

- **Multi-layer caching**: Intelligent routing across 5 specialized cache layers
- **MCP Integration**: Full MCP protocol support for seamless integration with AI applications
- **Performance Optimization**: TTL-based cleanup, cache invalidation, and performance monitoring
- **Embedding-based caching**: Semantic similarity search and vector operations
- **Predictive caching**: ML-powered prediction of user needs
- **Longitudinal memory**: Persistent context memory across sessions
- **Comprehensive monitoring**: Hit/miss tracking, performance metrics, and logging

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mcp_servers/cache-mcp-server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the system:
```bash
cp config/cache_config.yaml.example config/cache_config.yaml
# Edit cache_config.yaml with your settings
```

4. Set up environment variables:
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/cache_db"
export VECTOR_DB_PATH="./cache_data"
export MCP_PORT=8001
```

### Running the Server

```bash
# Start the MCP server
python -m src.mcp.server

# Or with uvicorn for development
uvicorn src.mcp.server:app --host 0.0.0.0 --port 8001 --reload
```

### Basic Usage

#### Using MCP Tools

The server exposes the following MCP tools:

**Core Operations:**
- `cache_get`: Retrieve a value from cache
- `cache_set`: Store a value in cache
- `cache_delete`: Delete a value from cache
- `cache_search`: Search across cache layers
- `cache_stats`: Get cache statistics
- `cache_clear`: Clear cache data

**Layer-Specific Tools:**
- `predictive_cache_predict`: Get predictions from predictive cache
- `semantic_cache_similar`: Find similar entries in semantic cache
- `vector_cache_select_context`: Select context from vector cache
- `global_cache_search_knowledge`: Search global knowledge base
- `vector_diary_get_session_memories`: Get session memories
- `vector_diary_generate_insights`: Generate longitudinal insights

#### Example Usage

```python
import asyncio
from src.mcp.tools import CacheMCPTools

async def main():
    # Initialize cache tools
    cache_tools = CacheMCPTools()
    await cache_tools.initialize_all()
    
    # Store a value
    result = await cache_tools.set("user_query", "response_value")
    print(f"Set result: {result}")
    
    # Retrieve a value
    result = await cache_tools.get("user_query")
    print(f"Get result: {result}")
    
    # Get cache statistics
    stats = await cache_tools.get_stats()
    print(f"Cache stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

The system uses YAML configuration files located in `config/cache_config.yaml`. Key configuration sections include:

### Global Settings
```yaml
global:
  cache_enabled: true
  debug_mode: false
  log_level: INFO
  max_concurrent_requests: 100
  database_url: "postgresql://user:pass@localhost:5432/cache_db"
```

### Layer-Specific Configuration
Each cache layer has its own configuration section:

```yaml
predictive_cache:
  enabled: true
  cache_ttl_seconds: 300
  max_cache_size: 1000
  confidence_threshold: 0.7

semantic_cache:
  enabled: true
  cache_ttl_seconds: 3600
  similarity_threshold: 0.8
  embedding_model: "all-MiniLM-L6-v2"
```

### Environment Variables
The system supports environment variable overrides:

- `DATABASE_URL`: PostgreSQL connection string
- `VECTOR_DB_PATH`: Path to vector database storage
- `MCP_PORT`: MCP server port (default: 8001)
- `MCP_HOST`: MCP server host (default: 0.0.0.0)
- `API_KEY`: API key for authentication (if enabled)

## Cache Layers

### 1. Predictive Cache
- **Purpose**: Anticipate user needs and prefetch relevant data
- **Features**: ML-powered prediction, temporal analysis, user behavior modeling
- **Configuration**: `predictive_cache` section in config
- **Use Cases**: Prefetching likely next queries, anticipating user intent

### 2. Semantic Cache
- **Purpose**: Cache and retrieve based on semantic similarity
- **Features**: Embedding-based search, semantic hashing, similarity thresholding
- **Configuration**: `semantic_cache` section in config
- **Use Cases**: Similar query reuse, prompt caching, response caching

### 3. Vector Cache
- **Purpose**: Context selection and reranking based on embeddings
- **Features**: Vector similarity search, context windowing, reranking
- **Configuration**: `vector_cache` section in config
- **Use Cases**: Context selection, relevance filtering, document retrieval

### 4. Global Knowledge Cache
- **Purpose**: Fallback knowledge base with persistent training data
- **Features**: Knowledge indexing, consolidation, fallback mechanisms
- **Configuration**: `global_cache` section in config
- **Use Cases**: Fallback responses, knowledge retrieval, fact checking

### 5. Vector Diary
- **Purpose**: Longitudinal context memory across sessions
- **Features**: Session management, relationship analysis, insight generation
- **Configuration**: `vector_diary` section in config
- **Use Cases**: Conversation history, user preferences, trend analysis

## MCP Integration

### Tool Exposure
All cache functionality is exposed through MCP tools with consistent interfaces:

```python
# Basic operations
cache_get(key, layer=None)
cache_set(key, value, layer=None, ttl_seconds=None, metadata=None)
cache_delete(key, layer=None)
cache_search(query, layer=None, n_results=5, min_similarity=0.0)

# Management operations
cache_stats()
cache_clear(layer=None)
cache_performance()

# Layer-specific operations
predictive_cache_predict(query, n_predictions=3)
semantic_cache_similar(query, n_results=5, min_similarity=0.7)
vector_cache_select_context(query, n_context=5, min_similarity=0.6)
global_cache_search_knowledge(query, n_results=5, min_relevance=0.5)
vector_diary_get_session_memories(session_id, context_type=None, limit=50)
vector_diary_generate_insights(session_id=None, category=None)
```

### Cache Routing
The system implements intelligent cache routing:

- **Smart Routing**: Automatically selects appropriate cache layers based on query characteristics
- **Fallback Order**: Configurable fallback order when primary cache misses
- **Layer Selection**: Manual layer specification when needed

### Performance Monitoring
Comprehensive performance tracking:

- **Hit/Miss Tracking**: Per-layer and overall cache performance
- **Response Time Monitoring**: Execution time tracking for all operations
- **Memory Usage**: Cache size and memory consumption monitoring
- **Error Tracking**: Error rates and failure analysis

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_cache_layers.py

# Run with verbose output
pytest -v
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

### Adding New Cache Layers
To add a new cache layer:

1. Create a new class inheriting from `BaseCache`
2. Implement required methods: `get`, `set`, `delete`, `clear`, `get_stats`
3. Add configuration options to `cache_config.yaml`
4. Register the layer in the MCP server
5. Add corresponding MCP tools

Example:
```python
from src.core.base_cache import BaseCache, CacheLayer

class MyCustomCache(BaseCache):
    def __init__(self, name: str, config: CacheConfig):
        super().__init__(name, config, CacheLayer.CUSTOM)
    
    async def get(self, key: str) -> CacheResult:
        # Implementation
        pass
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        # Implementation
        pass
```

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/

EXPOSE 8001
CMD ["python", "-m", "src.mcp.server"]
```

### Production Considerations
- **Database**: Use PostgreSQL with pgvector extension for production
- **Monitoring**: Enable comprehensive logging and monitoring
- **Security**: Configure authentication and rate limiting
- **Scaling**: Consider horizontal scaling for high-load scenarios
- **Backup**: Implement regular backups of cache data

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Check `DATABASE_URL` configuration
   - Ensure PostgreSQL is running with pgvector extension
   - Verify network connectivity

2. **Memory Issues**
   - Monitor cache sizes in configuration
   - Adjust TTL settings for your use case
   - Enable cache cleanup policies

3. **Performance Issues**
   - Check performance metrics
   - Optimize embedding models and vector operations
   - Consider cache layer tuning

4. **MCP Connection Issues**
   - Verify MCP server is running
   - Check port configuration
   - Ensure proper MCP client setup

### Debug Mode
Enable debug mode for detailed logging:

```yaml
global:
  debug_mode: true
  log_level: DEBUG
```

### Health Checks
The system provides health check endpoints:

```bash
# Check cache health
curl http://localhost:8001/health

# Get performance metrics
curl http://localhost:8001/metrics
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the Apache License 2.0. See the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the configuration examples
- Consult the API documentation

## Changelog

### v1.0.0
- Initial release with 5-layer cache architecture
- Full MCP integration
- Comprehensive test suite
- Production-ready configuration