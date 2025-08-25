# Everything MCP Server and SDK Implementation Analysis

## Overview

The Everything MCP Server is a comprehensive implementation that bridges the popular Windows file search utility "Everything" (by voidtools) with the Model Context Protocol (MCP). This enables AI agents and applications to perform ultra-fast local file searches through a standardized MCP interface.

## Architecture

### Core Components

#### 1. **Main Server Implementation** ([`everything_search_mcp_server.py`](mcp_servers/everything-search-mcp/src/everything_search_mcp_server.py:1))
- **Class**: `EverythingSearchMCPServer`
- **Base Framework**: Built on `FastMCP` from the MCP library
- **Protocol**: Uses JSON-RPC 2.0 over stdio transport
- **Initialization**: Loads Everything SDK via ctypes and PyWin32

#### 2. **Everything SDK Integration**
- **SDK Path**: Configured via `EVERYTHING_SDK_PATH` environment variable
- **DLL Loading**: Uses `ctypes.WinDLL()` to load `Everything64.dll`
- **SDK Methods**: Exposes everything_sdk functions:
  - `everything_sdk.search()` - Basic file search
  - `everything_sdk.search_by_size()` - Size-based filtering
  - `everything_sdk.search_by_date()` - Date-based filtering
  - `everything_sdk.get_file_info()` - File metadata retrieval
  - `everything_sdk.list_drives()` - Drive enumeration
  - `everything_sdk.set_case_sensitive()` - Case sensitivity control
  - `everything_sdk.set_whole_word()` - Whole word matching
  - `everything_sdk.set_regex()` - Regular expression support

#### 3. **Configuration System** ([`everything_search_mcp_config.json`](mcp_servers/everything-search-mcp/config/everything_search_mcp_config.json:1))
- **Structure**: Comprehensive JSON configuration with multiple sections:
  - `everything_search`: SDK path and search parameters
  - `search`: Default limits and supported file types
  - `performance`: Async settings and caching
  - `logging`: Log levels and output configuration
  - `security`: Path validation and access controls
  - `monitoring`: Metrics and performance tracking

## MCP Tools Implementation

### 1. **Search Tools**
- **`search_files`**: Basic file search with query and max_results
- **`search_files_advanced`**: Advanced search with regex, case sensitivity, and whole word matching
- **`search_by_extension`**: Filter files by extension (e.g., "*.txt")
- **`search_by_size`**: Filter by file size with unit conversion (bytes/KB/MB/GB)
- **`search_by_date`**: Filter by modification date with multiple format support

### 2. **Information Tools**
- **`get_file_info`**: Retrieve detailed file metadata
- **`list_drives`**: Enumerate available drives with space information
- **`get_server_info`**: Return server configuration and status
- **`validate_sdk_installation`**: Check Everything SDK availability

### 3. **Tool Registration**
```python
# Tools are registered using FastMCP decorator pattern
self.mcp.tool()(self.search_files)
self.mcp.tool()(self.search_files_advanced)
self.mcp.tool()(self.get_file_info)
# ... etc
```

## Data Flow and Processing

### 1. **Request Processing**
1. MCP client sends JSON-RPC request via stdio
2. Server parses request and extracts tool name/parameters
3. Validates SDK availability and parameters
4. Calls appropriate Everything SDK method
5. Processes and formats results
6. Returns structured JSON response

### 2. **Result Formatting**
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

## Error Handling and Validation

### 1. **SDK Validation**
- Checks `EVERYTHING_SDK_PATH` environment variable
- Validates DLL existence and loadability
- Provides detailed error messages for configuration issues

### 2. **Parameter Validation**
- Validates search queries (non-empty, reasonable length)
- Validates numeric ranges (max_results, file sizes)
- Validates date formats and ranges
- Validates file extensions and paths

### 3. **Exception Handling**
- Catches and logs SDK-specific exceptions
- Handles timeout scenarios
- Manages permission errors and I/O failures
- Provides graceful degradation for partial results

## Testing Infrastructure

### 1. **Unit Tests**
- **Search functionality**: [`test_search_functionality.py`](mcp_servers/everything-search-mcp/tests/unit/test_search_functionality.py:1)
- **Error handling**: [`test_error_handling.py`](mcp_servers/everything-search-mcp/tests/unit/test_error_handling.py:1)
- **Filtering and sorting**: [`test_filtering_and_sorting.py`](mcp_servers/everything-search-mcp/tests/unit/test_filtering_and_sorting.py:1)
- **MCP protocol compliance**: [`test_mcp_protocol_compliance.py`](mcp_servers/everything-search-mcp/tests/unit/test_mcp_protocol_compliance.py:1)

### 2. **Integration Tests**
- **MCP communication**: [`test_mcp_communication.py`](mcp_servers/everything-search-mcp/tests/integration/test_mcp_communication.py:1)
- **Server discovery**: [`test_server_discovery.py`](mcp_servers/everything-search-mcp/tests/integration/test_server_discovery.py:1)

### 3. **Performance Tests**
- Search performance benchmarks
- Concurrent search handling
- Memory usage optimization

## Deployment and Integration

### 1. **Launcher Script** ([`mcp_everything_search_fixed.py`](mcp_servers/everything-search-mcp/mcp_everything_search_fixed.py:1))
- Command-line interface with argument parsing
- Configuration validation
- Environment setup
- PyWin32 integration fixes

### 2. **Demo and Testing**
- **Demo script**: [`demo_search.py`](mcp_servers/everything-search-mcp/demo_search.py:1) - Shows expected search results
- **Basic integration**: [`test_basic_integration.py`](mcp_servers/everything-search-mcp/test_basic_integration.py:1) - Validates file structure and configuration

### 3. **Dependencies**
- **Core**: `mcp>=1.0.0`, `everything-sdk>=0.0.0`, `pywin32>=305`
- **Async**: `asyncio>=3.4.3`
- **Development**: `pytest>=7.0.0`, `black>=22.0.0`, `flake8>=4.0.0`

## Key Features

### 1. **Performance Optimizations**
- Ultra-fast file search using Everything's indexed database
- Async/await support for concurrent operations
- Configurable result caching and timeouts
- Memory-efficient result processing

### 2. **Advanced Search Capabilities**
- Regular expression pattern matching
- Case-sensitive and case-insensitive search
- Whole word and substring matching
- Wildcard support (*, ?)
- Multi-criteria filtering (extension, size, date)

### 3. **Security and Validation**
- Path validation and sanitization
- Input parameter validation
- Access control patterns
- Safe handling of user-provided queries

### 4. **Monitoring and Logging**
- Comprehensive logging with configurable levels
- Performance metrics tracking
- Error monitoring and reporting
- Search query and result logging

## Integration with MCP Ecosystem

The server integrates seamlessly with MCP-compatible clients like:
- Claude Desktop
- VSCode with Kilo Code extension
- Other AI agents and development tools

Configuration is done through standard MCP JSON settings:
```json
{
  "mcpServers": {
    "everything-search": {
      "command": "uvx",
      "args": ["mcp-server-everything-search"],
      "env": {
        "EVERYTHING_SDK_PATH": "C:/Path/To/Everything64.dll"
      }
    }
  }
}
```

## Installation and Setup

### Prerequisites
- Windows OS
- Everything Search application installed from https://www.voidtools.com/
- Everything SDK DLL (Everything64.dll)
- Python 3.7+
- MCP-compatible client (Claude Desktop, VSCode with Kilo Code, etc.)

### Installation Steps

1. **Install Everything Search**
   - Download and install Everything Search from https://www.voidtools.com/
   - Note the installation path of Everything64.dll

2. **Set Environment Variable**
   ```bash
   # Set the path to Everything64.dll
   set EVERYTHING_SDK_PATH=C:\Users\salib\Everything64.dll
   # Or for Linux/Mac (if using WSL)
   export EVERYTHING_SDK_PATH=/mnt/c/Users/salib/Everything64.dll
   ```

3. **Install Python Dependencies**
   ```bash
   pip install mcp>=1.0.0 everything-sdk>=0.0.0 pywin32>=305
   ```

4. **Configure MCP Client**
   Add to your MCP client configuration:
   ```json
   "mcpServers": {
     "everything-search": {
       "command": "python",
       "args": ["-m", "mcp_server_everything_search"],
       "env": {
         "EVERYTHING_SDK_PATH": "C:/Users/salib/Everything64.dll"
       }
     }
   }
   ```

5. **Verify Installation**
   ```bash
   # Test SDK loading
   python test_everything_sdk.py
   
   # Run demo
   python demo_search.py
   
   # Run tests
   python -m pytest tests/
   ```

## Kilo Code Integration

### Immediate Setup for Kilo Code

To make the Everything Search MCP Server immediately available to Kilo Code, follow these steps:

#### 1. **Environment Configuration**
Add to your system environment variables:
```bash
EVERYTHING_SDK_PATH=C:\Users\salib\Everything64.dll
```

#### 2. **Kilo Code MCP Settings**
In Kilo Code settings, add the following MCP server configuration:

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

#### 3. **Quick Test Script**
Create a quick test script to verify functionality:
```python
# test_kilo_search.py
import asyncio
import os
import sys
from pathlib import Path

os.environ['EVERYTHING_SDK_PATH'] = r'C:\Users\salib\Everything64.dll'
sys.path.insert(0, str(Path(__file__).parent / "mcp_servers" / "everything-search-mcp" / "src"))

from everything_search_mcp_server import EverythingSearchMCPServer

async def quick_search(query):
    server = EverythingSearchMCPServer()
    result = await server.search_files(query, max_results=10)
    return result

# Example usage:
# results = asyncio.run(quick_search("A.0 Mybizz system.png"))
```

#### 4. **Kilo Code Commands**
Add these commands to Kilo Code for quick access:

```python
# Search for files
async def search_files_kilo(query):
    return await quick_search(query)

# Get file info
async def get_file_info_kilo(path):
    server = EverythingSearchMCPServer()
    return await server.get_file_info(path)

# List drives
async def list_drives_kilo():
    server = EverythingSearchMCPServer()
    return await server.list_drives()
```

### Usage Examples

#### Basic File Search
```python
# Search for files containing "document"
result = await server.search_files("document", max_results=50)
```

#### Advanced Search with Filters
```python
# Search for Python files modified in the last month
result = await server.search_files_advanced(
    "*.py", 
    max_results=100,
    case_sensitive=False,
    regex=False
)
```

#### File Size Filtering
```python
# Find files between 1MB and 10MB
result = await server.search_by_size(
    min_size=1, 
    max_size=10, 
    size_unit="MB"
)
```

#### Date-based Search
```python
# Find files modified between specific dates
result = await server.search_by_date(
    date_from="2023-01-01",
    date_to="2023-12-31"
)
```

## Troubleshooting

### Common Issues

1. **SDK Not Found**
   - Verify `EVERYTHING_SDK_PATH` is set correctly
   - Ensure Everything64.dll exists at the specified path
   - Check file permissions

2. **Import Errors**
   - Install required dependencies: `pip install mcp everything-sdk pywin32`
   - Verify Python path includes the src directory

3. **MCP Connection Issues**
   - Check MCP client configuration
   - Verify server is running and accessible
   - Check firewall settings

4. **Search Performance**
   - Adjust max_results in configuration
   - Enable result caching for frequent searches
   - Monitor system resources

### Debug Mode
Enable debug logging by setting:
```json
{
  "logging": {
    "level": "DEBUG",
    "enable_file_logging": true
  }
}
```

## Summary

The Everything MCP Server implementation represents a robust, production-ready solution that leverages the power of Everything's ultra-fast file indexing while providing a clean, standardized MCP interface. The comprehensive testing framework, extensive configuration options, and error handling make it suitable for integration into various AI workflows and development environments. The modular design allows for easy extension and customization while maintaining high performance and reliability.

## Links and References

- Everything Search Application: https://www.voidtools.com/
- Everything SDK Documentation: Available with Everything Search installation
- MCP Protocol Specification: https://modelcontextprotocol.io/
- Project Repository: Available in the mcp_servers/everything-search-mcp directory

## Verification Status

✅ **Everything Search Application**: Installed at `C:\Program Files\Everything\Everything.exe`
✅ **Everything SDK**: Successfully loaded from `C:\Users\salib\Everything64.dll`
✅ **MCP Server**: Working correctly with proper configuration
✅ **File Search**: Successfully tested and verified
✅ **Kilo Code Integration**: Ready for immediate use

**Last Verified**: 2025-08-23
**Test File Found**: `A.0 Mybizz system.png` at `C:\_1mybizz\paddle-plugin\Docs\_My Todo\A.0 Mybizz system.png`