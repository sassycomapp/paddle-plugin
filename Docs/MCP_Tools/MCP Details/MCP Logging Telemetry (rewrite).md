# MCP Server Documentation Template

## Brief Overview
MCP Logging and Telemetry is an MCP server designed to capture logs, trace tool usage, interactions, and token consumption from MCP tools and AI agents. It provides an observability layer without heavy infrastructure while allowing you to debug, audit, and optimize your AI workflows through lightweight telemetry collection and reporting.

## Tool list
- log_event
- get_logs
- get_metrics

## Available Tools and Usage
### Tool 1: log_event
**Description:** Records telemetry events for MCP tool calls including tool invocation, input/output size, token consumption, success/failure status, and latency metrics.

**Parameters:**
- `tool_name` (string): Name of the MCP tool being called
- `input_size` (integer): Size of input data in bytes
- `output_size` (integer): Size of output data in bytes
- `token_count` (integer): Number of tokens consumed during the operation
- `duration` (float): Execution time in milliseconds
- `success` (boolean): Whether the tool call was successful
- `error_message` (string, optional): Error message if the call failed
- `timestamp` (string): ISO timestamp of the event

**Returns:**
Confirmation message indicating the telemetry event was successfully logged

**Example:**
```javascript
// Example usage
result = await client.call_tool("log_event", {
    "tool_name": "document_processor",
    "input_size": 1024,
    "output_size": 2048,
    "token_count": 150,
    "duration": 125.5,
    "success": true,
    "timestamp": "2024-01-15T10:30:00Z"
});
```

### Tool 2: get_logs
**Description:** Retrieves logged telemetry events with optional filtering by time range, tool name, or success status.

**Parameters:**
- `start_time` (string, optional): Start time filter (ISO format)
- `end_time` (string, optional): End time filter (ISO format)
- `tool_name` (string, optional): Filter by specific tool name
- `success_only` (boolean, optional): Only return successful events
- `limit` (integer, optional): Maximum number of events to return
- `offset` (integer, optional): Number of events to skip for pagination

**Returns:**
Array of telemetry event objects containing logged data

**Example:**
```javascript
// Example usage
result = await client.call_tool("get_logs", {
    "start_time": "2024-01-15T00:00:00Z",
    "end_time": "2024-01-15T23:59:59Z",
    "tool_name": "document_processor",
    "success_only": true,
    "limit": 100
});
```

### Tool 3: get_metrics
**Description:** Aggregates and returns performance metrics including token usage, error rates, and response times across specified time periods.

**Parameters:**
- `time_period` (string): Time period for aggregation (e.g., "1h", "24h", "7d")
- `metrics` (array): List of metrics to retrieve (e.g., ["token_usage", "error_rate", "avg_response_time"])
- `group_by` (string, optional): Group metrics by tool name or time interval
- `start_time` (string, optional): Custom start time for analysis
- `end_time` (string, optional): Custom end time for analysis

**Returns:**
Aggregated metrics object with statistical data and trends

**Example:**
```javascript
// Example usage
result = await client.call_tool("get_metrics", {
    "time_period": "24h",
    "metrics": ["token_usage", "error_rate", "avg_response_time"],
    "group_by": "tool_name"
});
```

## Installation Information
- **Installation Scripts**: `pip install fastmcp` or use dedicated MCP telemetry server implementation
- **Main Server**: Python-based telemetry server using FastMCP framework
- **Dependencies**: Python 3.8+, FastMCP, SQLite (for local storage), optional HTTP/SSE transport
- **Status**: ✅ Available (Lightweight implementation available)

## Configuration
**Environment Configuration (.env):**
```bash
# Telemetry server configuration
TELEMETRY_PORT=8081
TELEMETRY_STORAGE_PATH=./telemetry_data
TELEMETRY_DB_TYPE=sqlite
TELEMETRY_MAX_LOG_SIZE=1000000
TELEMETRY_SAMPLE_RATE=1.0
LOG_LEVEL=INFO
```

**MCP Configuration (mcp.json):**
```json
{
  "mcpServers": {
    "logging_telemetry": {
      "command": "python",
      "args": ["/path/to/telemetry_server.py"],
      "alwaysAllow": ["log_event", "get_logs", "get_metrics"],
      "env": {
        "TELEMETRY_PORT": "8081",
        "TELEMETRY_STORAGE_PATH": "./telemetry_data"
      }
    }
  }
}
```

## Integration
- **VS Code Extension**: Compatible with VS Code MCP extension for real-time telemetry monitoring
- **Companion Systems**: Integrates with AG2 orchestration, KiloCode configuration, and existing MCP servers
- **API Compatibility**: Supports Model Context Protocol standards with stdio, SSE, and HTTP transports

## How to Start and Operate this MCP
### Manual Start:
```bash
python telemetry_server.py
# or with custom configuration
python telemetry_server.py --port 8081 --storage ./telemetry_data
```

### Automated Start:
```bash
# Using systemd (Linux)
sudo systemctl enable telemetry-server
sudo systemctl start telemetry-server

# Using Docker
docker run -d -p 8081:8081 -v ./telemetry_data:/app/telemetry_data telemetry-server

# Using supervisor
[program:telemetry-server]
command=python telemetry_server.py
directory=/path/to/telemetry
autostart=true
autorestart=true
```

### Service Management:
```bash
# Check status
systemctl status telemetry-server

# Start/stop/restart
sudo systemctl start telemetry-server
sudo systemctl stop telemetry-server
sudo systemctl restart telemetry-server

# View logs
journalctl -u telemetry-server -f
```

## Configuration Options
- **Storage Configuration**: SQLite database or JSON file storage with configurable retention policies
- **Sampling Rate**: Adjustable sampling rate for high-volume environments (0.1 to 1.0)
- **Log Levels**: Configurable logging levels (DEBUG, INFO, WARNING, ERROR)
- **Port Configuration**: Customizable HTTP/SSE server port
- **Throttling**: Configurable event throttling to prevent overload
- **Batch Processing**: Configurable batch processing for improved performance

## Key Features
1. Lightweight telemetry collection with minimal resource overhead
2. Real-time monitoring of MCP tool usage and performance
3. Token consumption tracking and optimization insights
4. Error rate analysis and debugging capabilities
5. Historical data analysis and trend reporting
6. Configurable storage and retention policies
7. Multiple transport protocols (stdio, SSE, HTTP)
8. Integration with existing MCP ecosystems

## Security Considerations
- Telemetry data may contain sensitive information - ensure proper access controls
- Implement authentication for remote telemetry server access
- Encrypt telemetry data at rest and in transit
- Regular audit of logged data for compliance requirements
- Role-based access control for different telemetry endpoints

## Troubleshooting
- **Connection Issues**: Verify telemetry server is running and accessible on configured port
- **High Memory Usage**: Check log retention policies and implement sampling
- **Missing Events**: Verify client middleware is properly configured and emitting events
- **Database Corruption**: Implement regular backups and restore procedures
- **Debug Mode**: Enable verbose logging with `LOG_LEVEL=DEBUG` for detailed troubleshooting

## Testing and Validation
**Test Suite:**
```bash
# Run basic functionality tests
python test_telemetry.py

# Test event logging
curl -X POST http://localhost:8081/log_event -H "Content-Type: application/json" -d '{"tool_name": "test", "input_size": 100, "output_size": 200, "token_count": 50, "duration": 10.5, "success": true}'

# Test log retrieval
curl http://localhost:8081/get_logs?limit=10

# Test metrics aggregation
curl http://localhost:8081/get_metrics?time_period=1h
```

## Performance Metrics
- **Event Processing**: Capable of handling thousands of events per second with proper configuration
- **Memory Usage**: Minimal footprint with configurable sampling for high-volume environments
- **Storage Efficiency**: SQLite optimized for time-series data with automatic cleanup
- **Network Overhead**: Lightweight protocol with minimal bandwidth requirements
- **Scalability**: Horizontal scaling possible through multiple telemetry server instances

## Backup and Recovery
- **Database Backup**: Regular SQLite database dumps using `sqlite3 telemetry.db ".backup backup.db"`
- **Configuration Backup**: Store configuration files in version control
- **Log Rotation**: Implement log rotation to prevent disk space issues
- **Disaster Recovery**: Maintain off-site backups of telemetry data
- **Restore Procedures**: Documented recovery process for system failures

## Version Information
- **Current Version**: 1.0.0 (Lightweight implementation)
- **Last Updated**: [Installation date verification available]
- **Compatibility**: Compatible with MCP servers following Model Context Protocol standards

## Support and Maintenance
- **Documentation**: Available via telemetry server help commands and inline documentation
- **Community Support**: GitHub repository issues and discussions
- **Maintenance Schedule**: Regular updates for performance improvements and security patches

## References
- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://docs.ag2.ai/0.9.1/docs/use-cases/notebooks/notebooks/mcp_client/)
- [AG2 Telemetry Guidelines](https://googleapis.github.io/genai-toolbox/concepts/telemetry/)
- [KiloCode MCP Configuration](https://docs.kilocode.bot/mcp/configuring-mcp-servers)
- [MCP Debugging Tools](https://modelcontextprotocol.io/docs/tools/debugging)

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
The MCP Logging and Telemetry server provides a lightweight, efficient solution for monitoring and analyzing MCP tool usage across your AI infrastructure. By integrating seamlessly with existing MCP servers, AG2 orchestration, and KiloCode configuration, it enables comprehensive observability without the overhead of complex monitoring systems. The server supports multiple transport protocols, configurable storage options, and real-time analytics capabilities, making it ideal for debugging, optimization, and compliance requirements in AI-driven workflows.