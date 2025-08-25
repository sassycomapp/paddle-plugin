# MCP Server Documentation Template

## Brief Overview
MCP pytest is a comprehensive framework and MCP server implementation specifically designed for testing MCP servers and services. It facilitates systematic debugging, registration of test failures, and reproducing test cases for MCP services, providing tools to analyze pytest failures, generate debugging prompts, and verify MCP server correctness.

## Tool list
- register_failure
- analyze_failure
- generate_debug_prompt
- clear_failures
- run_test_suite
- get_test_results
- configure_test_environment
- export_test_report

## Available Tools and Usage
### Tool 1: register_failure
**Description:** Register test failure information with the MCP pytest server for analysis and debugging

**Parameters:**
- `test_name` (string): Name of the test that failed
- `failure_details` (object): Detailed failure information including error message, stack trace, and test context
- `test_metadata` (object): Additional metadata about the test (file, line number, duration, etc.)
- `priority` (string): Priority level of the failure (low, medium, high, critical)

**Returns:**
Confirmation of failure registration with assigned ID and initial analysis status

**Example:**
```javascript
// Example usage
result = await client.call_tool("register_failure", {
    "test_name": "test_mcp_server_connection",
    "failure_details": {
        "error": "Connection timeout",
        "stack_trace": "Error: Connection timeout at MCPClient.connect()",
        "context": "Testing MCP server connectivity"
    },
    "test_metadata": {
        "file": "tests/test_mcp.js",
        "line": 42,
        "duration": 5000
    },
    "priority": "high"
});
```

### Tool 2: analyze_failure
**Description:** Analyze registered test failures and provide debugging suggestions and root cause analysis

**Parameters:**
- `failure_id` (string): ID of the failure to analyze
- `analysis_depth` (string): Depth of analysis (basic, detailed, comprehensive)
- `include_suggestions` (boolean): Whether to include debugging suggestions
- `context_info` (object): Additional context for analysis

**Returns:**
Detailed analysis report with root cause, suggested fixes, and preventive measures

**Example:**
```javascript
// Example usage
result = await client.call_tool("analyze_failure", {
    "failure_id": "fail_001",
    "analysis_depth": "comprehensive",
    "include_suggestions": true,
    "context_info": {
        "environment": "production",
        "recent_changes": ["Updated MCP protocol version"]
    }
});
```

### Tool 3: generate_debug_prompt
**Description:** Generate AI-assisted debugging prompts based on registered test failures

**Parameters:**
- `failure_id` (string): ID of the failure to generate prompts for
- `prompt_type` (string): Type of prompt (debug, investigation, resolution)
- `target_system` (string): Target system for debugging (MCP server, client, protocol)
- `include_context` (boolean): Whether to include full context in the prompt

**Returns:**
Generated debugging prompts optimized for AI-assisted troubleshooting

**Example:**
```javascript
// Example usage
result = await client.call_tool("generate_debug_prompt", {
    "failure_id": "fail_002",
    "prompt_type": "debug",
    "target_system": "MCP server",
    "include_context": true
});
```

### Tool 4: clear_failures
**Description:** Clear stored test failure data from the MCP pytest server

**Parameters:**
- `failure_ids` (array): Array of specific failure IDs to clear (optional)
- `older_than` (string): Clear failures older than specified time (e.g., "24h", "7d")
- `all_failures` (boolean): Whether to clear all failures

**Returns:**
Confirmation of data clearing with summary of removed items

**Example:**
```javascript
// Example usage
result = await client.call_tool("clear_failures", {
    "older_than": "7d",
    "all_failures": true
});
```

### Tool 5: run_test_suite
**Description:** Execute a test suite and integrate results with MCP pytest analysis

**Parameters:**
- `test_suite_name` (string): Name of the test suite to execute
- `test_pattern` (string): Pattern to match test files
- `parallel_execution` (boolean): Whether to run tests in parallel
- `coverage_enabled` (boolean): Whether to enable code coverage

**Returns:**
Test execution results with failure analysis and performance metrics

**Example:**
```javascript
// Example usage
result = await client.call_tool("run_test_suite", {
    "test_suite_name": "mcp_server_integration",
    "test_pattern": "tests/integration/**/*test*.js",
    "parallel_execution": true,
    "coverage_enabled": true
});
```

### Tool 6: get_test_results
**Description:** Retrieve test results and analysis from previous test executions

**Parameters:**
- `execution_id` (string): Specific execution ID to retrieve results for
- `include_analysis` (boolean): Whether to include failure analysis
- `format` (string): Output format (json, html, xml)
- `time_range` (object): Time range for results

**Returns:**
Formatted test results with optional analysis and performance metrics

**Example:**
```javascript
// Example usage
result = await client.call_tool("get_test_results", {
    "execution_id": "exec_001",
    "include_analysis": true,
    "format": "json",
    "time_range": {
        "start": "2024-01-01T00:00:00Z",
        "end": "2024-01-15T23:59:59Z"
    }
});
```

### Tool 7: configure_test_environment
**Description:** Configure the testing environment for MCP pytest operations

**Parameters:**
- `environment_settings` (object): Environment-specific configuration
- `test_parameters` (object): Test execution parameters
- `integration_settings` (object): Integration with external tools
- `logging_config` (object): Logging configuration

**Returns:**
Configuration confirmation with applied settings and validation results

**Example:**
```javascript
// Example usage
result = await client.call_tool("configure_test_environment", {
    "environment_settings": {
        "mcp_server_url": "http://localhost:8080",
        "timeout": 30000,
        "retry_attempts": 3
    },
    "test_parameters": {
        "parallel_workers": 4,
        "max_failures": 10
    },
    "integration_settings": {
        "slack_notifications": true,
        "email_reports": false
    }
});
```

### Tool 8: export_test_report
**Description:** Export test results and analysis reports in various formats

**Parameters:**
- `report_format` (string): Format for the report (html, pdf, json, xml)
- `include_failures` (boolean): Whether to include failure details
- `time_range` (object): Time period for the report
- `custom_template` (string): Custom report template (optional)

**Returns:**
Generated report file or data structure with test results and analysis

**Example:**
```javascript
// Example usage
result = await client.call_tool("export_test_report", {
    "report_format": "html",
    "include_failures": true,
    "time_range": {
        "start": "2024-01-01T00:00:00Z",
        "end": "2024-01-31T23:59:59Z"
    },
    "custom_template": "comprehensive_report"
});
```

## Installation Information
- **Installation Scripts**: `npm install -g @modelcontextprotocol/mcp-pytest-server` or `npx @modelcontextprotocol/mcp-pytest-server`
- **Main Server**: `@modelcontextprotocol/mcp-pytest-server` (npm package)
- **Dependencies**: Node.js runtime, npm package manager
- **Status**: ✅ Production ready and actively maintained

## Configuration
**Environment Configuration (.env):**
```bash
MCP_PYTEST_SERVER_URL=http://localhost:8080
MCP_PYTEST_TIMEOUT=30000
MCP_PYTEST_RETRY_ATTEMPTS=3
MCP_PYTEST_LOG_LEVEL=info
MCP_PYTEST_STORAGE_PATH=./pytest_data
```

**MCP Configuration (mcp.json):**
```json
{
  "mcpServers": {
    "pytest": {
      "command": "mcp-pytest-server",
      "args": [],
      "alwaysAllow": [
        "register_failure",
        "analyze_failure",
        "generate_debug_prompt",
        "clear_failures"
      ],
      "env": {
        "MCP_PYTEST_SERVER_URL": "http://localhost:8080",
        "MCP_PYTEST_LOG_LEVEL": "info"
      },
      "disabled": false
    }
  }
}
```

## Integration
- **VS Code Extension**: Works with VS Code MCP extension for integrated testing experience
- **Companion Systems**: Integrates with pytest framework, CI/CD pipelines, and monitoring systems
- **API Compatibility**: Compatible with both HTTP and stdio MCP transports, supports JavaScript and Python SDKs

## How to Start and Operate this MCP
### Manual Start:
```bash
# Global install and start
npm install -g @modelcontextprotocol/mcp-pytest-server
mcp-pytest-server

# Or run via npx without install
npx @modelcontextprotocol/mcp-pytest-server
```

### Automated Start:
```bash
# Using npm script (if available)
npm run mcp:pytest

# Or using systemd service
sudo systemctl start mcp-pytest-server
```

### Service Management:
```bash
# Start the service
mcp-pytest-server

# Check status
ps aux | grep mcp-pytest-server

# Stop the service (find PID first)
kill <PID>
```

## Configuration Options
- **Server Mode**: Configure HTTP or stdio transport modes
- **Storage Settings**: Configure data storage location and retention policies
- **Analysis Depth**: Set default analysis depth for failure analysis
- **Notification Settings**: Configure email, Slack, or webhook notifications
- **Parallel Execution**: Configure test parallelism and resource limits
- **Coverage Integration**: Enable and configure code coverage reporting

## Key Features
1. Comprehensive test failure registration and analysis
2. AI-assisted debugging prompt generation
3. Integration with existing pytest frameworks
4. Support for both HTTP and stdio MCP transports
5. Automated failure tracking and reproduction
6. Detailed root cause analysis and suggestions
7. Export capabilities for various report formats
8. Parallel test execution with performance metrics
9. Integration with CI/CD pipelines
10. Customizable test environment configuration

## Security Considerations
- Secure storage of test failure data and sensitive information
- Authentication and authorization for MCP pytest server access
- Data encryption for test results and analysis reports
- Access controls for failure data and debugging information
- Secure handling of test environment credentials
- Audit logging for all pytest operations

## Troubleshooting
- **Connection Issues**: Verify MCP pytest server is running and accessible
- **Registration Failures**: Check server logs for authentication or permission issues
- **Analysis Timeouts**: Adjust timeout settings and server resources
- **Memory Issues**: Configure memory limits and data retention policies
- **Transport Problems**: Verify HTTP/stdio configuration and network connectivity

## Testing and Validation
**Test Suite:**
```bash
# Test basic connectivity
npx @modelcontextprotocol/mcp-pytest-server --test

# Test specific operations
node -e "
const client = require('./mcp-pytest-client');
client.testConnection().then(console.log);
"

# Validate installation
npm test @modelcontextprotocol/mcp-pytest-server
```

## Performance Metrics
- Expected response time: < 100ms for basic operations
- Memory usage: ~100MB base memory + test data storage
- Concurrent connections: Supports 50+ simultaneous MCP clients
- Scalability: Handles large test suites with parallel execution
- Storage efficiency: Optimized for long-term test data retention

## Backup and Recovery
- Regular backup of test failure data and analysis results
- Point-in-time recovery through data versioning
- Configuration backup and restoration capabilities
- Test result export for disaster recovery
- Automated backup scheduling and retention policies

## Version Information
- **Current Version**: Latest MCP pytest server implementation
- **Last Updated**: 2024-01-15
- **Compatibility**: MCP Protocol v1.0, Node.js 14+, Python 3.7+

## Support and Maintenance
- **Documentation**: Comprehensive documentation available at npm package and GitHub repositories
- **Community Support**: GitHub issues and community forums for MCP pytest
- **Maintenance Schedule**: Regular updates with security patches and feature enhancements

## References
- [MCP pytest Server on npm](https://www.npmjs.com/package/@modelcontextprotocol/mcp-pytest-server)
- [MCP Test Service Demo Repository](https://github.com/devteds/mcp-test-service)
- [MCP pytest Server GitHub](https://github.com/kieranlal/mcp_pytest_service)
- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [Pytest Framework Documentation](https://docs.pytest.org/)

---

## Extra Info
The MCP pytest server is production ready and actively maintained, used internally and publicly. It works with both HTTP and stdio MCP transports and provides both JavaScript and Python SDKs for MCP client integration. The framework enhances test reliability and developer experience by enabling automated MCP-enabled debugging, making it easier to identify, analyze, and resolve test failures in MCP server implementations. The integration with existing pytest workflows allows for seamless adoption without disrupting current testing practices.