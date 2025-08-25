# MCP Server Documentation Template

## Brief Overview
The MCP Memory Service is a Python-based, production-ready MCP Memory Server implementing persistent semantic memory with vector database storage (PGvector or SQLite Vec). It supports long-term memory recall, autonomous memory consolidation, and is designed to integrate seamlessly with AI orchestration stacks like KiloCode and AG2, providing robust memory management for AI agents.

## Tool list
- store_memory
- retrieve_memory
- recall_memory
- search_by_tag
- delete_memory
- get_stats

## Available Tools and Usage
### Tool 1: store_memory
**Description:** Stores new memories with content and associated tags for later retrieval and recall.

**Parameters:**
- `content` (string): The memory content to be stored
- `tags` (array): Array of tags associated with this memory for categorization and retrieval
- `metadata` (object, optional): Additional metadata about the memory (timestamp, source, etc.)

**Returns:**
Confirmation object with memory ID and storage status

**Example:**
```javascript
// Example usage
result = await client.call_tool("store_memory", {
    "content": "Remember that the project deadline is next Friday.",
    "tags": ["project", "deadline"],
    "metadata": {
        "timestamp": "2024-01-15T10:30:00Z",
        "source": "user_input"
    }
});
```

### Tool 2: retrieve_memory
**Description:** Retrieves relevant memories based on a query using semantic search and vector similarity.

**Parameters:**
- `query` (string): Search query for finding relevant memories
- `limit` (integer, optional): Maximum number of memories to retrieve (default: 10)
- `threshold` (float, optional): Similarity threshold for results (0.0 to 1.0)
- `tags` (array, optional): Filter memories by specific tags

**Returns:**
Array of memory objects with content, tags, similarity scores, and metadata

**Example:**
```javascript
// Example usage
result = await client.call_tool("retrieve_memory", {
    "query": "project deadline",
    "limit": 5,
    "threshold": 0.7,
    "tags": ["project"]
});
```

### Tool 3: recall_memory
**Description:** Recalls memories based on exact content matching or specific criteria for precise memory retrieval.

**Parameters:**
- `content` (string): Exact content to match or partial content for fuzzy matching
- `exact_match` (boolean, optional): Whether to use exact matching (default: false)
- `tags` (array, optional): Filter memories by specific tags
- `date_range` (object, optional): Filter by date range with start and end dates

**Returns:**
Array of matching memory objects with full details and metadata

**Example:**
```javascript
// Example usage
result = await client.call_tool("recall_memory", {
    "content": "project deadline",
    "exact_match": false,
    "tags": ["project", "deadline"],
    "date_range": {
        "start": "2024-01-01T00:00:00Z",
        "end": "2024-01-31T23:59:59Z"
    }
});
```

### Tool 4: search_by_tag
**Description:** Searches for memories using specific tags for categorical organization and retrieval.

**Parameters:**
- `tags` (array): Array of tags to search for
- `operator` (string, optional): Search operator ("AND" or "OR", default: "AND")
- `limit` (integer, optional): Maximum number of results to return

**Returns:**
Array of memory objects matching the specified tag criteria

**Example:**
```javascript
// Example usage
result = await client.call_tool("search_by_tag", {
    "tags": ["project", "deadline"],
    "operator": "AND",
    "limit": 10
});
```

### Tool 5: delete_memory
**Description:** Deletes specific memories by ID or criteria-based deletion for memory management.

**Parameters:**
- `memory_ids` (array, optional): Array of specific memory IDs to delete
- `tags` (array, optional): Delete memories with specified tags
- `date_range` (object, optional): Delete memories within date range
- `confirm` (boolean): Confirmation flag to prevent accidental deletion

**Returns:**
Deletion confirmation with count of deleted memories

**Example:**
```javascript
// Example usage
result = await client.call_tool("delete_memory", {
    "tags": ["obsolete", "test"],
    "date_range": {
        "start": "2024-01-01T00:00:00Z",
        "end": "2024-01-15T23:59:59Z"
    },
    "confirm": true
});
```

### Tool 6: get_stats
**Description:** Retrieves statistics about the memory system including memory count, storage usage, and performance metrics.

**Parameters:**
- `detailed` (boolean, optional): Whether to return detailed statistics (default: false)
- `time_range` (object, optional): Filter statistics by time range

**Returns:**
Statistics object with memory counts, storage usage, and performance metrics

**Example:**
```javascript
// Example usage
result = await client.call_tool("get_stats", {
    "detailed": true,
    "time_range": {
        "start": "2024-01-01T00:00:00Z",
        "end": "2024-01-31T23:59:59Z"
    }
});
```

## Installation Information
- **Installation Scripts**: `python install.py` (hardware-aware dependency installation)
- **Main Server**: `python -m mcp_memory_service.server` or `memory_wrapper.py`
- **Dependencies**: Python 3.8+, PyTorch (with CUDA if applicable), PGvector or SQLite Vec
- **Status**: ✅ Available (Production-ready implementation)

## Configuration
**Environment Configuration (.env):**
```bash
# Path to persistent vector database
export MCP_MEMORY_VECTOR_DB_PATH="/path/to/vector_db"

# Path to backup directory
export MCP_MEMORY_BACKUPS_PATH="/path/to/backups"

# Memory service configuration
export MCP_MEMORY_MAX_SIZE=1000000
export MCP_MEMORY_CLEANUP_INTERVAL=3600
export MCP_MEMORY_LOG_LEVEL=INFO
```

**MCP Configuration (mcp.json):**
```json
{
  "mcpServers": {
    "memory": {
      "command": "python",
      "args": ["/path/to/mcp-memory-service/memory_wrapper.py"],
      "env": {
        "MCP_MEMORY_VECTOR_DB_PATH": "/path/to/vector_db",
        "MCP_MEMORY_BACKUPS_PATH": "/path/to/backups"
      },
      "alwaysAllow": [
        "store_memory",
        "retrieve_memory",
        "recall_memory",
        "search_by_tag",
        "delete_memory",
        "get_stats"
      ],
      "disabled": false
    }
  }
}
```

## Integration
- **VS Code Extension**: Compatible with VS Code MCP extension for memory management in development environments
- **Companion Systems**: Integrates with AG2 orchestration, KiloCode configuration, and existing MCP servers
- **API Compatibility**: Supports Model Context Protocol standards with stdio, SSE, and HTTP transports

## How to Start and Operate this MCP
### Manual Start:
```bash
# Using Python module
python -m mcp_memory_service.server

# Using wrapper script (recommended on Windows)
python memory_wrapper.py

# Using uv package manager
uv run memory
```

### Automated Start:
```bash
# Using systemd (Linux)
sudo systemctl enable mcp-memory-service
sudo systemctl start mcp-memory-service

# Using Docker
docker pull doobidoo/mcp-memory-service:latest
docker run -d -p 8000:8000 \
  -v /path/to/vector_db:/app/vector_db \
  -v /path/to/backups:/app/backups \
  doobidoo/mcp-memory-service:latest

# Using supervisor
[program:mcp-memory-service]
command=python memory_wrapper.py
directory=/path/to/mcp-memory-service
autostart=true
autorestart=true
```

### Service Management:
```bash
# Check status
systemctl status mcp-memory-service

# Start/stop/restart
sudo systemctl start mcp-memory-service
sudo systemctl stop mcp-memory-service
sudo systemctl restart mcp-memory-service

# View logs
journalctl -u mcp-memory-service -f
```

## Configuration Options
- **Database Configuration**: Choice between PGvector and SQLite Vec with configurable connection settings
- **Memory Management**: Configurable memory limits, cleanup intervals, and consolidation policies
- **Storage Optimization**: Vector dimensionality, similarity thresholds, and indexing strategies
- **Backup Configuration**: Automated backup scheduling, retention policies, and recovery procedures
- **Performance Tuning**: Batch processing, caching, and memory optimization settings
- **Logging**: Configurable log levels and output destinations

## Key Features
1. Persistent semantic memory with vector database storage
2. Long-term memory recall and autonomous consolidation
3. Tag-based memory organization and retrieval
4. Multiple search and query capabilities
5. Automatic memory maintenance and cleanup
6. Comprehensive backup and recovery systems
7. Integration with AI orchestration stacks
8. Cross-platform support (Python, Docker, Windows wrapper)

## Security Considerations
- Memory data may contain sensitive information - implement proper access controls
- Database encryption for memory storage at rest
- Secure backup procedures with access restrictions
- Authentication for remote memory service access
- Regular security audits of stored memory data
- Role-based access control for different memory operations

## Troubleshooting
- **Connection Issues**: Verify memory server is running and accessible on configured port
- **Database Corruption**: Implement regular backups and restore procedures
- **Memory Performance**: Check memory limits and optimize vector search parameters
- **Integration Errors**: Verify MCP client configuration and tool call syntax
- **Storage Issues**: Monitor disk space and database file integrity
- **Debug Mode**: Enable verbose logging with `MCP_MEMORY_LOG_LEVEL=DEBUG` for detailed troubleshooting

## Testing and Validation
**Test Suite:**
```bash
# Run basic functionality tests
python test_memory_service.py

# Test memory operations
curl -X POST http://localhost:8000/store_memory -H "Content-Type: application/json" -d '{"content": "test memory", "tags": ["test"]}'

# Test memory retrieval
curl http://localhost:8000/retrieve_memory?query=test&limit=5

# Test memory statistics
curl http://localhost:8000/get_stats?detailed=true

# Test backup functionality
curl -X POST http://localhost:8000/backup
```

## Performance Metrics
- **Memory Capacity**: Supports millions of memories with efficient vector indexing
- **Query Performance**: Sub-second response times for semantic search operations
- **Storage Efficiency**: Optimized vector storage with configurable compression
- **Scalability**: Horizontal scaling possible through multiple memory service instances
- **Memory Usage**: Minimal footprint with configurable caching strategies
- **Network Overhead**: Lightweight protocol with efficient data transfer

## Backup and Recovery
- **Automated Backups**: Scheduled periodic backups with configurable retention policies
- **Manual Backups**: On-demand backup creation via MCP tools
- **Restore Procedures**: Documented recovery process for database restoration
- **Backup Verification**: Automated backup integrity checking
- **Disaster Recovery**: Maintain off-site backups of memory data
- **Version Compatibility**: Support for database version migrations

## Version Information
- **Current Version**: 1.0.0 (Production-ready implementation)
- **Last Updated**: [Installation date verification available]
- **Compatibility**: Compatible with MCP servers following Model Context Protocol standards

## Support and Maintenance
- **Documentation**: Available via memory server help commands and inline documentation
- **Community Support**: GitHub repository issues and discussions
- **Maintenance Schedule**: Regular updates for performance improvements and security patches
- **Hardware Support**: Automatic detection and optimization for different hardware configurations

## References
- [Official GitHub Repository](https://github.com/doobidoo/mcp-memory-service)
- [Docker Hub Image](https://hub.docker.com/r/doobidoo/mcp-memory-service)
- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Installation Script Documentation](https://github.com/doobidoo/mcp-memory-service/blob/main/install.py)
- [Memory Dashboard Integration](https://playbooks.com/mcp/doobidoo-memory-dashboard)

---

## Template Usage Guidelines

### Required Sections:
1. **Brief Overview** - Must be concise and informative
2. **Available Tools and Usage** - Complete tool inventory with examples
3. **Installation Information** - Clear installation steps
4. **Configuration** - Environment and MCP configuration
5. **How to Start and Operate this MCP** - Startup and operation procedures

### Optional Sections:
- Integration details (if applicable)
- Security considerations (if applicable)
- Troubleshooting (if applicable)
- Performance metrics (if applicable)
- Backup and recovery (if applicable)

### Formatting Standards:
- Use consistent code block formatting
- Include parameter types in tool descriptions
- Provide working examples for all tools
- Use clear, descriptive section headings
- Include file paths relative to project root

### Special Notes:
- Replace bracketed placeholders `[like this]` with actual values
- Maintain consistent terminology across all MCP documentation
- Include version-specific information when applicable
- Document platform-specific requirements and differences

### Extra Info
The MCP Memory Service provides a comprehensive memory management solution for AI agents and orchestration systems. By implementing persistent semantic memory with vector database storage, it enables long-term memory recall and autonomous memory consolidation. The service supports multiple deployment options including Python module execution, Windows wrapper, and Docker containers, making it suitable for various environments. With robust backup and recovery systems, comprehensive security measures, and seamless integration with existing MCP ecosystems, this memory service is designed to be simple, robust, and fit-for-purpose in AI-driven workflows.