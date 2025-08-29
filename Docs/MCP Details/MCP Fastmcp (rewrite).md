# MCP Server Documentation Template

## Brief Overview
FastMCP is a Pythonic, lightweight MCP server framework that provides a simple yet powerful foundation for creating MCP servers. It serves as the underlying framework for multiple MCP servers in the KiloCode ecosystem, including Everything Search MCP Server, EasyOCR MCP Server, and MCP Memory Service. FastMCP enables developers to create MCP servers with minimal code complexity while providing robust tool registration, transport management, and integration capabilities.

## Tool list
- store_memory
- retrieve_memory
- search_by_tag
- delete_memory
- check_database_health
- extract_text_from_image
- extract_text_from_batch
- extract_text_from_base64
- get_available_languages
- validate_ocr_installation
- get_processor_info
- search_files
- search_files_advanced
- get_file_info
- list_drives
- validate_sdk_installation
- get_server_info

## Available Tools and Usage
### Tool 1: store_memory
**Description:** Store a new memory with content and optional metadata in the memory service

**Parameters:**
- `content` (string): The content to store as memory
- `tags` (array): Optional tags to categorize the memory
- `memory_type` (string): Type of memory (note, decision, task, reference)
- `metadata` (object): Additional metadata for the memory

**Returns:**
Dictionary with success status, message, and content hash

**Example:**
```javascript
// Example usage
result = await client.call_tool("store_memory", {
    "content": "This is an important note about the project",
    "tags": ["project", "important", "notes"],
    "memory_type": "note",
    "metadata": {"priority": "high"}
});
```

### Tool 2: retrieve_memory
**Description:** Retrieve memories based on semantic similarity to a query

**Parameters:**
- `query` (string): Search query for semantic similarity
- `n_results` (integer): Maximum number of results to return
- `min_similarity` (number): Minimum similarity score threshold

**Returns:**
Dictionary with retrieved memories and metadata

**Example:**
```javascript
// Example usage
result = await client.call_tool("retrieve_memory", {
    "query": "project documentation",
    "n_results": 5,
    "min_similarity": 0.7
});
```

### Tool 3: search_by_tag
**Description:** Search memories by tags with flexible matching options

**Parameters:**
- `tags` (string or array): Tag or list of tags to search for
- `match_all` (boolean): If true, memory must have ALL tags; if false, ANY tag

**Returns:**
Dictionary with matching memories and search parameters

**Example:**
```javascript
// Example usage
result = await client.call_tool("search_by_tag", {
    "tags": ["project", "important"],
    "match_all": false
});
```

### Tool 4: delete_memory
**Description:** Delete a specific memory by its content hash

**Parameters:**
- `content_hash` (string): Hash of the memory content to delete

**Returns:**
Dictionary with success status and message

**Example:**
```javascript
// Example usage
result = await client.call_tool("delete_memory", {
    "content_hash": "abc123def456"
});
```

### Tool 5: check_database_health
**Description:** Check the health and status of the memory database

**Parameters:**
- None

**Returns:**
Dictionary with health status and statistics

**Example:**
```javascript
// Example usage
result = await client.call_tool("check_database_health", {});
```

### Tool 6: extract_text_from_image
**Description:** Extract text from a single image file using OCR

**Parameters:**
- `image_path` (string): Path to the image file

**Returns:**
Dictionary with OCR results and metadata

**Example:**
```javascript
// Example usage
result = await client.call_tool("extract_text_from_image", {
    "image_path": "C:/path/to/image.png"
});
```

### Tool 7: extract_text_from_batch
**Description:** Extract text from multiple images in batch processing

**Parameters:**
- `image_paths` (array): List of image file paths

**Returns:**
Dictionary with batch OCR results and statistics

**Example:**
```javascript
// Example usage
result = await client.call_tool("extract_text_from_batch", {
    "image_paths": ["image1.png", "image2.jpg", "image3.png"]
});
```

### Tool 8: extract_text_from_base64
**Description:** Extract text from a base64 encoded image

**Parameters:**
- `base64_image` (string): Base64 encoded image string
- `image_format` (string): Image format (png, jpg, jpeg, etc.)

**Returns:**
Dictionary with OCR results and metadata

**Example:**
```javascript
// Example usage
result = await client.call_tool("extract_text_from_base64", {
    "base64_image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "image_format": "png"
});
```

### Tool 9: get_available_languages
**Description:** Get list of available OCR languages

**Parameters:**
- None

**Returns:**
List of available language codes

**Example:**
```javascript
// Example usage
result = await client.call_tool("get_available_languages", {});
```

### Tool 10: validate_ocr_installation
**Description:** Validate OCR installation and dependencies

**Parameters:**
- None

**Returns:**
Dictionary with validation results and processor information

**Example:**
```javascript
// Example usage
result = await client.call_tool("validate_ocr_installation", {});
```

### Tool 11: get_processor_info
**Description:** Get processor information and configuration

**Parameters:**
- None

**Returns:**
Dictionary with processor information and configuration details

**Example:**
```javascript
// Example usage
result = await client.call_tool("get_processor_info", {});
```

### Tool 12: search_files
**Description:** Basic file search with query and max_results parameters

**Parameters:**
- `query` (string): Search query string
- `max_results` (integer): Maximum number of results to return

**Returns:**
Structured JSON with search results containing file metadata

**Example:**
```javascript
// Example usage
result = await client.call_tool("search_files", {
    "query": "document",
    "max_results": 50
});
```

### Tool 13: search_files_advanced
**Description:** Advanced search with regex, case sensitivity, and whole word matching

**Parameters:**
- `query` (string): Search query string
- `max_results` (integer): Maximum number of results to return
- `case_sensitive` (boolean): Enable case-sensitive search
- `regex` (boolean): Enable regular expression matching
- `whole_word` (boolean): Enable whole word matching

**Returns:**
Structured JSON with advanced search results including all file metadata

**Example:**
```javascript
// Example usage
result = await client.call_tool("search_files_advanced", {
    "query": "*.py",
    "max_results": 100,
    "case_sensitive": false,
    "regex": false,
    "whole_word": false
});
```

### Tool 14: get_file_info
**Description:** Retrieve detailed file metadata

**Parameters:**
- `file_path` (string): Full path to the file

**Returns:**
Detailed file metadata including size, modification date, extension, and directory status

**Example:**
```javascript
// Example usage
result = await client.call_tool("get_file_info", {
    "file_path": "C:\\path\\to\\file.txt"
});
```

### Tool 15: list_drives
**Description:** Enumerate available drives with space information

**Parameters:**
- None

**Returns:**
List of available drives with their total and free space information

**Example:**
```javascript
// Example usage
result = await client.call_tool("list_drives", {});
```

### Tool 16: validate_sdk_installation
**Description:** Check Everything SDK availability

**Parameters:**
- None

**Returns:**
Validation results indicating SDK availability and configuration status

**Example:**
```javascript
// Example usage
result = await client.call_tool("validate_sdk_installation", {});
```

### Tool 17: get_server_info
**Description:** Return server configuration and status

**Parameters:**
- None

**Returns:**
Server configuration details, status, and performance metrics

**Example:**
```javascript
// Example usage
result = await client.call_tool("get_server_info", {});
```

## Installation Information
- **Installation Scripts**: FastMCP CLI tools and package management scripts
- **Main Server**: Python scripts using FastMCP framework (e.g., `fastmcp_server.py`)
- **Dependencies**: 
  - Core: `fastmcp` Python package
  - MCP: `mcp>=1.0.0` for protocol support
  - Python: Python 3.8 or later
  - Optional: `uv` for advanced package management
  - Service-specific: `everything-sdk`, `easyocr`, `pywin32`, etc.
- **Status**: Production-ready with comprehensive testing framework and multiple active implementations

## Configuration
**Environment Configuration (.env):**
```bash
# Environment variables for FastMCP server configuration
MCP_SERVER_PORT=8000
MCP_SERVER_HOST=0.0.0.0
ENV_VAR=value
```

**MCP Configuration (mcp.json):**
```json
{
  "mcpServers": {
    "fastmcp_local": {
      "command": "python",
      "args": ["path/to/fastmcp_server.py"],
      "env": {
        "ENV_VAR": "value"
      },
      "alwaysAllow": ["store_memory", "retrieve_memory", "search_by_tag", "delete_memory", "check_database_health"],
      "disabled": false
    }
  }
}
```

**Alternative SSE Configuration:**
```json
{
  "mcpServers": {
    "fastmcp_remote": {
      "url": "http://127.0.0.1:8000/mcp",
      "alwaysAllow": ["store_memory", "retrieve_memory", "search_by_tag", "delete_memory", "check_database_health"],
      "disabled": false
    }
  }
}
```

## Integration
- **VS Code Extension**: Compatible with Kilo Code extension for MCP server management
- **Companion Systems**: Works with AG2 orchestrators, Claude Desktop, and other AI agents
- **API Compatibility**: Compatible with MCP JSON-RPC 2.0 protocol over stdio, SSE, and HTTP transports
- **Storage Backends**: Supports multiple storage backends (SQLite-vec, PostgreSQL vector, etc.)
- **Transport Methods**: stdio, SSE, and streamable HTTP for various deployment scenarios

## How to Start and Operate this MCP
### Manual Start:
```bash
# Run basic FastMCP server
python fastmcp_server.py

# Run via FastMCP CLI with SSE transport
fastmcp run fastmcp_server.py:mcp --transport sse --port 8080 --host 127.0.0.1

# Run with HTTP transport for remote access
python fastmcp_server.py --transport http --port 8000 --host 0.0.0.0
```

### Automated Start:
```bash
# Using uv package manager
uv add fastmcp

# Run with specific configuration
fastmcp run fastmcp_server.py:mcp --transport sse --port 8080 --host 127.0.0.1

# Run as a service
python -m mcp_server_memory_service
```

### Service Management:
```bash
# Check FastMCP version
fastmcp version

# Start server with custom configuration
python fastmcp_server.py

# Stop server (Ctrl+C in terminal)

# Monitor server logs
tail -f fastmcp_server.log

# Check health status
curl http://localhost:8000/health
```

## Configuration Options
- **Transport Methods**: stdio (default), SSE (Server-Sent Events), and HTTP for remote access
- **Server Settings**: Configurable port, host, and log level
- **Tool Management**: Enable/disable specific tools with `alwaysAllow` configuration
- **Environment Variables**: Support for custom environment variables
- **Logging**: Configurable log levels for debugging and monitoring
- **Storage Backends**: Dynamic selection of storage backends based on configuration
- **Lifespan Management**: Context managers for resource initialization and cleanup

## Key Features
1. **Pythonic Framework**: Lightweight and easy-to-use MCP server implementation
2. **Multiple Transport Support**: stdio, SSE, and HTTP transport methods
3. **Tool Registration**: Simple decorator-based tool registration system
4. **Async Support**: Full async/await support for concurrent operations
5. **Context Management**: Proper resource lifecycle management with async context managers
6. **Modular Architecture**: Clean separation of concerns with extensible design
7. **Multiple Storage Backends**: Support for various storage solutions (SQLite-vec, PostgreSQL, etc.)
8. **Comprehensive Error Handling**: Robust error handling and logging
9. **Production Ready**: Battle-tested with multiple active implementations
10. **Flexible Configuration**: Environment-based configuration with validation

## Security Considerations
- Tool access control through `alwaysAllow` configuration
- Environment variable management for sensitive data
- Secure transport options with HTTPS support
- Input validation for all tool parameters
- Resource isolation through context management
- Secure storage backend configuration
- Proper error handling without information leakage

## Troubleshooting
- **Installation Issues**: Verify Python 3.8+ and use `pip install fastmcp` or `uv add fastmcp`
- **Connection Problems**: Check transport configuration and network accessibility
- **Tool Errors**: Review tool implementations and async/await usage
- **Performance Issues**: Adjust log levels and monitor server resources
- **Configuration Errors**: Validate JSON syntax and environment variable settings
- **Storage Issues**: Check storage backend availability and configuration
- **Memory Management**: Monitor resource usage and adjust batch sizes

## Testing and Validation
**Test Suite:**
```bash
# Verify FastMCP installation
fastmcp version

# Test basic server functionality
python fastmcp_server.py

# Test with SSE transport
fastmcp run fastmcp_server.py:mcp --transport sse --port 8080 --host 127.0.0.1

# Test individual tools
python -c "
from fastmcp import Client
import asyncio

async def test_tools():
    client = Client('http://127.0.0.1:8000')
    async with client:
        result = await client.call_tool('store_memory', {'content': 'test', 'tags': ['test']})
        print(result)
        result = await client.call_tool('retrieve_memory', {'query': 'test'})
        print(result)

asyncio.run(test_tools())
"

# Run service-specific tests
python -m pytest tests/
```

## Performance Metrics
- Lightweight implementation with minimal overhead
- Fast tool execution with async support
- Configurable timeouts and resource limits
- Efficient transport protocols (stdio, SSE, HTTP)
- Scalable architecture for multiple concurrent tool calls
- Memory-efficient processing with configurable batch sizes
- Optimized storage operations with connection pooling

## Backup and Recovery
- Configuration backup: Save MCP configuration files and server scripts
- Environment backup: Document and backup environment variable settings
- Log files: Maintain comprehensive logs for audit and troubleshooting purposes
- Storage backup: Regular backups of memory databases and storage backends
- Health monitoring: Automated health checks and status reporting

## Version Information
- **Current Version**: Production-ready implementation with multiple active servers
- **Last Updated**: 2025-08-23
- **Compatibility**: Python 3.8+, MCP protocol compliant, multiple transport methods
- **Framework Status**: Stable and actively used in production environments

## Support and Maintenance
- **Documentation**: Comprehensive inline documentation and usage examples
- **Community Support**: Available through GitHub repository and community forums
- **Maintenance Schedule**: Regular updates to maintain compatibility with MCP protocol
- **Multiple Implementations**: Battle-tested across multiple production servers
- **Active Development**: Continuous improvement and feature additions

## References
- FastMCP Documentation: https://gofastmcp.com
- FastMCP GitHub: https://github.com/jlowin/fastmcp
- MCP Protocol Specification: https://modelcontextprotocol.io/
- Cline MCP Guide: https://docs.cline.bot/mcp/configuring-mcp-servers
- API Dog FastMCP Guide: https://apidog.com/blog/fastmcp/
- KiloCode MCP Servers: Available in mcp_servers directory

---

## Extra Info
### Architecture Overview
FastMCP serves as the foundational framework for multiple MCP servers in the KiloCode ecosystem. It provides a clean, Pythonic interface for creating MCP servers with minimal code complexity while maintaining robust functionality. The framework supports multiple transport methods and provides comprehensive tool registration and management capabilities.

### Core Components
1. **FastMCP Class**: Main server class with tool registration and transport management
2. **Transport Layer**: Support for stdio, SSE, and HTTP protocols
3. **Tool Decorators**: `@mcp.tool()` decorator for easy tool registration
4. **Context Management**: Async context managers for resource lifecycle management
5. **Client Library**: Built-in client for connecting to FastMCP servers
6. **CLI Tools**: Command-line interface for server management and testing

### Implementation Examples
**Basic Server Setup:**
```python
from fastmcp import FastMCP

mcp = FastMCP(name="MyFastMCPServer")

@mcp.tool()
async def greet(name: str) -> str:
    return f"Hello, {name}!"

@mcp.tool()
async def add(a: int, b: int) -> int:
    return a + b

if __name__ == "__main__":
    mcp.run()
```

**Advanced Configuration with Context Management:**
```python
from fastmcp import FastMCP, Context
from contextlib import asynccontextmanager

@asynccontextmanager
async def server_lifespan(server: FastMCP):
    # Initialize resources
    storage = initialize_storage()
    try:
        yield {"storage": storage}
    finally:
        # Cleanup resources
        await storage.close()

mcp = FastMCP(
    name="AdvancedServer",
    port=8000,
    host="0.0.0.0",
    lifespan=server_lifespan
)

@mcp.tool()
async def store_data(data: str, ctx: Context):
    storage = ctx.request_context.lifespan_context.storage
    return await storage.store(data)
```

### Real System Implementations
FastMCP is actively used in multiple production servers:

1. **Everything Search MCP Server**: Ultra-fast local file search using Everything SDK
2. **EasyOCR MCP Server**: OCR functionality with low-resource optimizations
3. **MCP Memory Service**: Memory storage and retrieval with multiple storage backends

### Transport Methods
- **stdio**: Standard input/output for local development
- **SSE**: Server-Sent Events for web-based clients
- **HTTP**: Streamable HTTP for remote access and web integration

### Storage Backend Integration
FastMCP servers support multiple storage backends:
- **SQLite-vec**: Lightweight vector database for memory storage
- **PostgreSQL with pgvector**: Scalable vector database solution
- **Custom Storage**: Extensible architecture for custom storage implementations

### Configuration Management
- Environment-based configuration with validation
- JSON configuration files for complex settings
- Dynamic backend selection based on availability
- Runtime configuration updates without server restart

### Performance Optimizations
- Async/await support for concurrent operations
- Connection pooling for database operations
- Batch processing for multiple operations
- Configurable timeouts and resource limits
- Memory-efficient processing with streaming

### Security Features
- Tool access control through allow lists
- Input validation and sanitization
- Secure transport with HTTPS support
- Resource isolation through context management
- Proper error handling without information leakage

### Development Workflow
1. Install FastMCP package
2. Create MCP server Python script with tool definitions
3. Test locally with Python or FastMCP CLI
4. Add actual MCP tools (memory, OCR, file search, etc.)
5. Configure KiloCode connection (local command or SSE URL)
6. Invoke tools via KiloCode or AG2 agents
7. Monitor, log, and tune performance
8. Deploy in production with appropriate scaling

### Verification Checklist
| Step | Action | Status |
|------|--------|---------|
| 1 | Install FastMCP Python package | ✅ |
| 2 | Create MCP server Python script | ✅ |
| 3 | Run local MCP server setup | ✅ |
| 4 | Add actual MCP tools to FastMCP | ✅ |
| 5 | Configure KiloCode connection | ✅ |
| 6 | Invoke MCP tools via agents | ✅ |
| 7 | Monitor and tune performance | ✅ |
| 8 | Deploy in production | ✅ |
| 9 | Integrate with other MCP servers | ✅ |

### Additional Resources
- Video tutorials: https://www.youtube.com/watch?v=rnljvmHorQw
- Developer guides: https://cline.bot/blog/the-developers-guide-to-mcp-from-basics-to-advanced-workflows
- Client quickstart: https://modelcontextprotocol.io/quickstart/client
- Server quickstart: https://modelcontextprotocol.io/quickstart/server
- KiloCode documentation: Available in project repository