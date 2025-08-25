# MCP Server Documentation Template

## Brief Overview
The Everything MCP Server bridges the popular Windows file search utility "Everything" (by voidtools) with the Model Context Protocol (MCP). This enables AI agents and applications to perform ultra-fast local file searches through a standardized MCP interface, leveraging Everything's indexed database for real-time file system querying.

## Tool list
- search_files
- search_files_advanced
- search_by_extension
- search_by_size
- search_by_date
- get_file_info
- list_drives
- get_server_info
- validate_sdk_installation

## Available Tools and Usage
### Tool 1: search_files
**Description:** Basic file search with query and max_results parameters

**Parameters:**
- `query` (string): Search query string
- `max_results` (integer): Maximum number of results to return

**Returns:**
Structured JSON with search results containing file names, paths, sizes, modification dates, extensions, and directory status

**Example:**
```javascript
// Example usage
result = await client.call_tool("search_files", {
    "query": "document",
    "max_results": 50
});
```

### Tool 2: search_files_advanced
**Description:** Advanced search with regex, case sensitivity, and whole word matching options

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

### Tool 3: search_by_extension
**Description:** Filter files by extension (e.g., "*.txt")

**Parameters:**
- `extension` (string): File extension pattern (e.g., "*.txt", "*.py")
- `max_results` (integer): Maximum number of results to return

**Returns:**
Structured JSON with files matching the specified extension

**Example:**
```javascript
// Example usage
result = await client.call_tool("search_by_extension", {
    "extension": "*.txt",
    "max_results": 25
});
```

### Tool 4: search_by_size
**Description:** Filter by file size with unit conversion (bytes/KB/MB/GB)

**Parameters:**
- `min_size` (integer): Minimum file size
- `max_size` (integer): Maximum file size
- `size_unit` (string): Size unit ("bytes", "KB", "MB", "GB")

**Returns:**
Structured JSON with files matching the specified size criteria

**Example:**
```javascript
// Example usage
result = await client.call_tool("search_by_size", {
    "min_size": 1,
    "max_size": 10,
    "size_unit": "MB"
});
```

### Tool 5: search_by_date
**Description:** Filter by modification date with multiple format support

**Parameters:**
- `date_from` (string): Start date (YYYY-MM-DD format)
- `date_to` (string): End date (YYYY-MM-DD format)

**Returns:**
Structured JSON with files modified within the specified date range

**Example:**
```javascript
// Example usage
result = await client.call_tool("search_by_date", {
    "date_from": "2023-01-01",
    "date_to": "2023-12-31"
});
```

### Tool 6: get_file_info
**Description:** Retrieve detailed file metadata

**Parameters:**
- `path` (string): Full path to the file

**Returns:**
Detailed file metadata including size, modification date, extension, and directory status

**Example:**
```javascript
// Example usage
result = await client.call_tool("get_file_info", {
    "path": "C:\\path\\to\\file.txt"
});
```

### Tool 7: list_drives
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

### Tool 8: get_server_info
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

### Tool 9: validate_sdk_installation
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

## Installation Information
- **Installation Scripts**: [`mcp_everything_search_fixed.py`](mcp_servers/everything-search-mcp/mcp_everything_search_fixed.py:1) - Command-line launcher with configuration validation
- **Main Server**: [`everything_search_mcp_server.py`](mcp_servers/everything-search-mcp/src/everything_search_mcp_server.py:1) - Core MCP server implementation
- **Dependencies**: 
  - Core: `mcp>=1.0.0`, `everything-sdk>=0.0.0`, `pywin32>=305`
  - Async: `asyncio>=3.4.3`
  - Development: `pytest>=7.0.0`, `black>=22.0.0`, `flake8>=4.0.0`
- **Status**: Production-ready with comprehensive testing framework

## Configuration
**Environment Configuration (.env):**
```bash
EVERYTHING_SDK_PATH=C:\Users\salib\Everything64.dll
```

**MCP Configuration (mcp.json):**
```json
{
  "mcpServers": {
    "everything-search": {
      "command": "python",
      "args": ["-m", "mcp_server_everything_search"],
      "env": {
        "EVERYTHING_SDK_PATH": "C:/Users/salib/Everything64.dll"
      }
    }
  }
}
```

## Integration
- **VS Code Extension**: Integrated with Kilo Code extension for MCP server management
- **Companion Systems**: Works with Claude Desktop, VSCode with Kilo Code extension, and other AI agents
- **API Compatibility**: Compatible with MCP JSON-RPC 2.0 protocol over stdio transport

## How to Start and Operate this MCP
### Manual Start:
```bash
# Using the launcher script
python mcp_everything_search_fixed.py

# Using the server directly
python -m everything_search_mcp_server
```

### Automated Start:
```bash
# Using uvx (if available)
uvx mcp-server-everything-search

# Using Python module
python -m mcp_server_everything_search
```

### Service Management:
```bash
# Start the server
python mcp_everything_search_fixed.py

# Stop the server (Ctrl+C in terminal)

# Check server status
python -c "from everything_search_mcp_server import EverythingSearchMCPServer; print('Server loaded successfully')"

# Run tests
python -m pytest tests/
```

## Configuration Options
- **Search Parameters**: Configurable max_results, default limits, and supported file types
- **Performance Settings**: Async operation settings, result caching, and timeout configurations
- **Logging**: Configurable log levels and output destinations
- **Security**: Path validation patterns and access control settings
- **Monitoring**: Performance metrics tracking and health check intervals

## Key Features
1. Ultra-fast file search using Everything's indexed database
2. Advanced search capabilities with regex, case sensitivity, and whole word matching
3. Multi-criteria filtering (extension, size, date)
4. Comprehensive error handling and validation
5. Async/await support for concurrent operations
6. Configurable result caching and timeouts
7. Memory-efficient result processing
8. Comprehensive logging and monitoring

## Security Considerations
- Path validation and sanitization to prevent directory traversal attacks
- Input parameter validation for all search queries
- Access control patterns for sensitive file system areas
- Safe handling of user-provided search patterns and regular expressions
- Environment variable validation for SDK path security

## Troubleshooting
- **SDK Not Found**: Verify `EVERYTHING_SDK_PATH` is set correctly and Everything64.dll exists at the specified path
- **Import Errors**: Install required dependencies with `pip install mcp everything-sdk pywin32`
- **MCP Connection Issues**: Check MCP client configuration and verify server is running
- **Search Performance**: Adjust max_results configuration and enable result caching for frequent searches

## Testing and Validation
**Test Suite:**
```bash
# Run unit tests
python -m pytest tests/unit/

# Run integration tests
python -m pytest tests/integration/

# Run all tests
python -m pytest tests/

# Test SDK loading
python test_everything_sdk.py

# Run demo
python demo_search.py
```

## Performance Metrics
- Ultra-fast search performance leveraging Everything's indexed database
- Sub-second response times for typical file searches
- Memory-efficient result processing with configurable result limits
- Concurrent operation support through async/await patterns
- Configurable timeout settings for long-running searches

## Backup and Recovery
- Configuration backup: Copy `everything_search_mcp_config.json` to preserve settings
- SDK path backup: Document and backup the EVERYTHING_SDK_PATH environment variable
- Log files: Configurable logging for audit and troubleshooting purposes

## Version Information
- **Current Version**: Production-ready implementation
- **Last Updated**: 2025-08-23
- **Compatibility**: Windows OS with Everything Search application, Python 3.7+, MCP-compatible clients

## Support and Maintenance
- **Documentation**: Comprehensive inline documentation and usage examples
- **Community Support**: Available through project repository and issue tracking
- **Maintenance Schedule**: Regular updates to maintain compatibility with Everything SDK and MCP protocol

## References
- Everything Search Application: https://www.voidtools.com/
- Everything SDK Documentation: Available with Everything Search installation
- MCP Protocol Specification: https://modelcontextprotocol.io/
- Project Repository: Available in the mcp_servers/everything-search-mcp directory

---

## Extra Info
### Architecture Overview
The Everything MCP Server is built on FastMCP framework using JSON-RPC 2.0 over stdio transport. The server integrates Everything SDK via ctypes and PyWin32 to provide ultra-fast file search capabilities through a standardized MCP interface.

### Core Components
1. **Main Server Implementation**: EverythingSearchMCPServer class built on FastMCP
2. **Everything SDK Integration**: Uses ctypes.WinDLL() to load Everything64.dll
3. **Configuration System**: Comprehensive JSON configuration with multiple sections for search parameters, performance, logging, security, and monitoring

### Data Flow and Processing
1. MCP client sends JSON-RPC request via stdio
2. Server parses request and validates parameters
3. Calls appropriate Everything SDK method
4. Processes and formats results consistently
5. Returns structured JSON response

### Result Format
All search results follow a consistent structure:
```json
{
  "query": "search_string",
  "results": [
    {
      "name": "filename.txt",
      "path": "C:\\path\\to\\file",
      "size": 1024,
      "modified": "2023-01-01T00:00:00",
      "extension": "txt",
      "is_directory": false
    }
  ],
  "total_count": 1,
  "timestamp": "2025-01-23T10:03:37.033Z"
}
```

### Kilo Code Integration
For immediate use with Kilo Code, the server can be configured with direct Python path integration:
```json
{
  "mcpServers": {
    "everything-search": {
      "command": "python",
      "args": ["-c", "import sys; sys.path.insert(0, 'C:\\\\_1mybizz\\\\paddle-plugin\\\\mcp_servers\\\\everything-search-mcp\\\\src'); from everything_search_mcp_server import EverythingSearchMCPServer; server = EverythingSearchMCPServer(); import asyncio; asyncio.run(server.start_server())"],
      "env": {
        "EVERYTHING_SDK_PATH": "C:\\Users\\salib\\Everything64.dll"
      }
    }
  }
}
```

### Verification Status
✅ **Everything Search Application**: Installed at `C:\Program Files\Everything\Everything.exe`
✅ **Everything SDK**: Successfully loaded from `C:\Users\salib\Everything64.dll`
✅ **MCP Server**: Working correctly with proper configuration
✅ **File Search**: Successfully tested and verified
✅ **Kilo Code Integration**: Ready for immediate use

**Last Verified**: 2025-08-23
**Test File Found**: `A.0 Mybizz system.png` at `C:\_1mybizz\paddle-plugin\Docs\_My Todo\A.0 Mybizz system.png`