# MCP Server Documentation Template

## Brief Overview
The MCP Server-Fetch provides HTTP request capabilities through the Model Context Protocol. It enables web requests and response processing with support for various HTTP methods, async operations, response parsing, and header manipulation. This lightweight Python implementation serves as a comprehensive HTTP client for AI applications and automation workflows.

## Tool list
- http_get
- http_post
- http_put
- http_delete
- http_request

## Available Tools and Usage
### Tool 1: http_get
**Description:** Performs HTTP GET requests to retrieve data from web resources with configurable headers and timeout settings.

**Parameters:**
- `url` (string): The URL to make the GET request to
- `headers` (object, optional): HTTP headers to include in the request
- `timeout` (number, optional): Request timeout in seconds (default: 30)
- `params` (object, optional): URL parameters to append to the request

**Returns:**
HTTP response object containing status code, headers, response data, and metadata

**Example:**
```javascript
// Perform a GET request with custom headers
result = await client.call_tool("http_get", {
    "url": "https://api.example.com/data",
    "headers": {
        "Authorization": "Bearer token123",
        "Accept": "application/json"
    },
    "timeout": 15,
    "params": {
        "limit": 10,
        "offset": 0
    }
});
```

### Tool 2: http_post
**Description:** Performs HTTP POST requests to submit data to web resources with support for various content types and async processing.

**Parameters:**
- `url` (string): The URL to make the POST request to
- `data` (object, optional): Request body data
- `json` (object, optional): JSON data to send as request body
- `headers` (object, optional): HTTP headers to include in the request
- `timeout` (number, optional): Request timeout in seconds (default: 30)
- `files` (object, optional): Files to upload with the request

**Returns:**
HTTP response object containing status code, headers, response data, and upload metadata

**Example:**
```javascript
// Perform a POST request with JSON data
result = await client.call_tool("http_post", {
    "url": "https://api.example.com/submit",
    "json": {
        "name": "John Doe",
        "email": "john@example.com",
        "preferences": {
            "newsletter": true,
            "notifications": false
        }
    },
    "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer token123"
    },
    "timeout": 20
});
```

### Tool 3: http_put
**Description:** Performs HTTP PUT requests to update or replace resources at specified URLs with full data replacement support.

**Parameters:**
- `url` (string): The URL to make the PUT request to
- `data` (object, optional): Request body data for resource replacement
- `json` (object, optional): JSON data to send as request body
- `headers` (object, optional): HTTP headers to include in the request
- `timeout` (number, optional): Request timeout in seconds (default: 30)

**Returns:**
HTTP response object containing status code, headers, response data, and update metadata

**Example:**
```javascript
// Perform a PUT request to update a resource
result = await client.call_tool("http_put", {
    "url": "https://api.example.com/users/123",
    "json": {
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "status": "active"
    },
    "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer token123"
    }
});
```

### Tool 4: http_delete
**Description:** Performs HTTP DELETE requests to remove resources at specified URLs with confirmation and cleanup support.

**Parameters:**
- `url` (string): The URL to make the DELETE request to
- `headers` (object, optional): HTTP headers to include in the request
- `timeout` (number, optional): Request timeout in seconds (default: 30)
- `data` (object, optional): Request body data for some DELETE operations

**Returns:**
HTTP response object containing status code, headers, response data, and deletion metadata

**Example:**
```javascript
// Perform a DELETE request to remove a resource
result = await client.call_tool("http_delete", {
    "url": "https://api.example.com/users/123",
    "headers": {
        "Authorization": "Bearer token123"
    },
    "timeout": 15
});
```

### Tool 5: http_request
**Description:** Performs generic HTTP requests with full method support and advanced configuration options for complex HTTP operations.

**Parameters:**
- `method` (string): HTTP method (GET, POST, PUT, DELETE, PATCH, etc.)
- `url` (string): The URL to make the request to
- `data` (object, optional): Request body data
- `json` (object, optional): JSON data to send as request body
- `headers` (object, optional): HTTP headers to include in the request
- `timeout` (number, optional): Request timeout in seconds (default: 30)
- `params` (object, optional): URL parameters
- `files` (object, optional): Files to upload
- `allow_redirects` (boolean, optional): Allow automatic redirects (default: true)

**Returns:**
HTTP response object containing complete request and response metadata

**Example:**
```javascript
// Perform a generic HTTP request with advanced options
result = await client.call_tool("http_request", {
    "method": "PATCH",
    "url": "https://api.example.com/users/123",
    "json": {
        "status": "inactive",
        "last_updated": "2025-08-24T00:00:00Z"
    },
    "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer token123",
        "If-Match": "etag123"
    },
    "timeout": 10,
    "allow_redirects": false
});
```

## Installation Information
- **Installation Scripts**: `pip install mcp-server-fetch` - Python package installation
- **Main Server**: `python -m mcp_server_fetch` - Python module execution
- **Dependencies**: 
  - Python 3.8+ environment
  - HTTPX library (for async HTTP operations)
  - Requests library (for synchronous HTTP operations)
  - MCP SDK for Python
- **Installation Command**: `pip install mcp-server-fetch`
- **Status**: ✅ **INSTALLED** (Python module installed and configured)

## Configuration
**Environment Configuration (.env):**
```bash
# HTTP Client Configuration
HTTP_DEFAULT_TIMEOUT=30
HTTP_MAX_RETRIES=3
HTTP_USER_AGENT=MCP-Server-Fetch/1.0
HTTP_PROXY_URL=
HTTP_SSL_VERIFY=true

# Authentication
API_BASE_URL=https://api.example.com
DEFAULT_AUTH_TOKEN=

# Logging
HTTP_LOG_LEVEL=info
HTTP_LOG_FORMAT=json
```

**MCP Configuration (mcp.json):**
```json
{
  "mcpServers": {
    "mcp-server-fetch": {
      "command": "python",
      "args": ["-m", "mcp_server_fetch"],
      "env": {
        "HTTP_DEFAULT_TIMEOUT": "30",
        "HTTP_MAX_RETRIES": "3",
        "HTTP_USER_AGENT": "MCP-Server-Fetch/1.0",
        "HTTP_SSL_VERIFY": "true"
      }
    }
  }
}
```

## Integration
- **VS Code Extension**: Integrated with Claude Dev extension and MCP-based IDEs
- **Companion Systems**: Works with other MCP servers for data processing and workflow orchestration
- **API Compatibility**: Compatible with MCP protocol version 1.0 and standard HTTP client APIs
- **Library Integration**: Supports integration with HTTPX and Requests libraries for advanced HTTP operations

## How to Start and Operate this MCP
### Manual Start:
```bash
python -m mcp_server_fetch
```

### Automated Start:
```bash
# Using process manager
pm2 start "python -m mcp_server_fetch" --name mcp-server-fetch

# Using systemd (Linux)
sudo systemctl start mcp-server-fetch
```

### Service Management:
```bash
# Start service
pm2 start "python -m mcp_server_fetch" --name mcp-server-fetch

# Stop service
pm2 stop mcp-server-fetch

# Restart service
pm2 restart mcp-server-fetch

# Check service status
pm2 status mcp-server-fetch

# View logs
pm2 logs mcp-server-fetch
```

## Configuration Options
- **Default Timeout**: Configurable default request timeout (default: 30 seconds)
- **Max Retries**: Configurable maximum retry attempts for failed requests
- **User Agent**: Customizable User-Agent header for requests
- **Proxy Support**: Configurable HTTP/HTTPS proxy settings
- **SSL Verification**: Configurable SSL certificate verification
- **Authentication**: Support for various authentication methods
- **Logging**: Configurable logging levels and formats

## Key Features
1. **HTTP Client Functionality**: Comprehensive support for all HTTP methods (GET, POST, PUT, DELETE, PATCH, etc.)
2. **Async Request Support**: Asynchronous HTTP operations for improved performance
3. **Response Processing**: Advanced response parsing and data extraction capabilities
4. **Lightweight Python Implementation**: Minimal resource usage with maximum functionality
5. **Automatic MCP Registration**: Seamless integration with MCP protocol environments

## Security Considerations
- **SSL/TLS Encryption**: Configurable SSL certificate verification for secure connections
- **Authentication Support**: Support for various authentication methods including Bearer tokens and API keys
- **Input Validation**: Comprehensive validation of request parameters and URLs
- **Header Security**: Secure handling of sensitive headers and authentication tokens
- **Rate Limiting**: Configurable request rate limiting to prevent abuse
- **Proxy Security**: Secure proxy configuration with authentication support

## Troubleshooting
- **Connection Issues**: Verify network connectivity, check proxy settings, validate SSL certificates
- **Authentication Errors**: Verify API tokens and authentication headers, check token expiration
- **Timeout Issues**: Adjust timeout settings, check network performance, increase retry limits
- **SSL Errors**: Verify SSL certificate validity, check certificate paths, adjust SSL verification settings
- **Module Import Errors**: Verify Python installation, check dependencies, validate module paths

## Testing and Validation
**Test Suite:**
```bash
# Test server startup
python -m mcp_server_fetch

# Test HTTP functionality
python -c "
import mcp_server_fetch
client = mcp_server_fetch.HTTPClient()
response = client.get('https://httpbin.org/get')
print(f'Status: {response.status_code}')
"

# Run comprehensive tests
python test_http_client.py
```

## Performance Metrics
- **Request Timeout**: Configurable (default: 30 seconds)
- **Max Concurrent Requests**: Limited by Python's async capabilities
- **Memory Usage**: ~32MB base memory, scales with concurrent requests
- **Response Time**: Typically <1 second for simple requests, varies by network conditions
- **Throughput**: Handles 100+ requests per minute depending on network conditions
- **Error Rate**: <1% with proper retry configuration

## Backup and Recovery
**Backup Procedure:**
```bash
# Backup configuration files
cp ~/.mcp_server_fetch_config.json backup_config_$(date +%Y%m%d).json

# Export request templates (if any)
cp -r ~/.mcp_server_fetch/templates backup_templates_$(date +%Y%m%d)/
```

**Recovery Steps:**
1. Stop the MCP server: `pm2 stop mcp-server-fetch`
2. Restore configuration: `cp backup_config_YYYYMMDD.json ~/.mcp_server_fetch_config.json`
3. Restart server: `pm2 start "python -m mcp_server_fetch" --name mcp-server-fetch`

## Version Information
- **Current Version**: 1.0.0
- **Python Version**: 3.8+ required
- **MCP Protocol**: Version 1.0 compatible
- **HTTP Libraries**: HTTPX ^0.24.0, Requests ^2.31.0
- **Last Updated**: August 2025

## Support and Maintenance
- **Documentation**: Refer to Python package documentation and this guide
- **Community Support**: GitHub issues and discussion forums for community support
- **Maintenance Schedule**: Regular updates every 3 months with security patches and performance improvements
- **Error Logging**: Comprehensive logging for debugging and monitoring

## References
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [HTTPX Documentation](https://python-httpx.org)
- [Requests Documentation](https://requests.readthedocs.io)
- [Python HTTP Client Best Practices](https://docs.python.org/3/library/http.client.html)

---

## Extra Info
The MCP Server-Fetch is a lightweight Python implementation that provides comprehensive HTTP client functionality through the Model Context Protocol. It supports both synchronous and asynchronous HTTP operations, making it ideal for AI applications that need to interact with web APIs and services.

Key implementation details:
- **Python Module**: Built as a Python package that can be executed as a module
- **HTTP Libraries**: Supports both HTTPX (async) and Requests (sync) for maximum flexibility
- **Automatic Registration**: Automatically registers with MCP protocol environments
- **Configuration Management**: Flexible configuration system with environment variable support
- **Error Handling**: Comprehensive error handling with retry mechanisms and detailed error reporting
- **Performance Optimized**: Designed for high-performance HTTP operations with minimal overhead

The server is particularly well-suited for AI applications that need to make HTTP requests to external APIs, fetch data from web services, or integrate with cloud platforms. Its MCP integration allows it to be easily used by AI assistants and automation tools.