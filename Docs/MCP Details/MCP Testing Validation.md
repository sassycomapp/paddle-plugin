# MCP Testing Validation Server Documentation

## Brief Overview
The MCP Testing Validation server is a comprehensive testing and validation tool designed to automate and manage software testing processes. It provides a suite of tools for creating test suites, executing tests across different environments, analyzing test results, and generating detailed reports. The server integrates with PostgreSQL for data persistence and supports various testing frameworks including Jest for unit tests, Docker/Podman for integration tests, and Semgrep for security scanning.

## Tool list
- create_test_suite
- create_test_case
- run_test_suite
- get_test_results
- get_test_summary
- run_security_scan
- generate_test_report

## Available Tools and Usage

### Tool 1: create_test_suite
**Description:** Creates a new test suite with specified name, description, and type.

**Parameters:**
- `name` (string): Name of the test suite
- `description` (string): Description of the test suite
- `type` (string): Type of test suite (enum: 'unit', 'integration', 'e2e', 'security', 'performance')

**Returns:**
JSON object containing the created test suite details

**Example:**
```javascript
// Create a unit test suite
result = await client.call_tool("create_test_suite", {
    "name": "User Authentication Tests",
    "description": "Comprehensive tests for user authentication functionality",
    "type": "unit"
});
```

### Tool 2: create_test_case
**Description:** Creates a new test case within a specified test suite.

**Parameters:**
- `suite_name` (string): Name of the test suite
- `name` (string): Name of the test case
- `description` (string): Description of the test case
- `file_path` (string): Path to the test file
- `test_function` (string): Name of the test function
- `tags` (array): Tags for categorization
- `priority` (string): Priority level (enum: 'low', 'medium', 'high', 'critical')

**Returns:**
JSON object containing the created test case details

**Example:**
```javascript
// Create a test case
result = await client.call_tool("create_test_case", {
    "suite_name": "User Authentication Tests",
    "name": "Login with valid credentials",
    "description": "Test successful login with valid username and password",
    "file_path": "tests/auth.test.js",
    "test_function": "testValidLogin",
    "tags": ["auth", "login", "positive"],
    "priority": "high"
});
```

### Tool 3: run_test_suite
**Description:** Executes a test suite in the specified environment.

**Parameters:**
- `suite_name` (string): Name of the test suite to run
- `environment` (string): Environment to run tests in (enum: 'local', 'podman', 'ci'), default: 'local'
- `branch` (string): Git branch being tested
- `commit_hash` (string): Git commit hash

**Returns:**
JSON object containing test execution results

**Example:**
```javascript
// Run a test suite in CI environment
result = await client.call_tool("run_test_suite", {
    "suite_name": "User Authentication Tests",
    "environment": "ci",
    "branch": "feature/new-auth",
    "commit_hash": "a1b2c3d4e5f6"
});
```

### Tool 4: get_test_results
**Description:** Retrieves test results for a specific execution or suite.

**Parameters:**
- `execution_id` (number): ID of the test execution
- `suite_name` (string): Name of the test suite
- `limit` (number): Maximum number of results, default: 50

**Returns:**
JSON object containing test results

**Example:**
```javascript
// Get test results for a specific execution
result = await client.call_tool("get_test_results", {
    "execution_id": 123,
    "limit": 100
});

// Get test results for a specific suite
result = await client.call_tool("get_test_results", {
    "suite_name": "User Authentication Tests"
});
```

### Tool 5: get_test_summary
**Description:** Retrieves a summary of test results across all suites for a specified time period.

**Parameters:**
- `days` (number): Number of days to look back, default: 7

**Returns:**
JSON object containing test summary data

**Example:**
```javascript
// Get test summary for the last 30 days
result = await client.call_tool("get_test_summary", {
    "days": 30
});
```

### Tool 6: run_security_scan
**Description:** Runs Semgrep security scan on the specified codebase path.

**Parameters:**
- `path` (string): Path to scan, default: '.'
- `rules` (string): Semgrep rules to use, default: 'auto'

**Returns:**
JSON object containing security scan results

**Example:**
```javascript
// Run security scan on the entire project
result = await client.call_tool("run_security_scan", {
    "path": ".",
    "rules": "auto"
});

// Run security scan with specific rules
result = await client.call_tool("run_security_scan", {
    "path": "src/",
    "rules": "p/security-audit"
});
```

### Tool 7: generate_test_report
**Description:** Generates a comprehensive test report in the specified format.

**Parameters:**
- `execution_id` (number): Specific execution ID
- `format` (string): Report format (enum: 'json', 'html', 'markdown'), default: 'json'

**Returns:**
JSON object or HTML string containing the test report

**Example:**
```javascript
// Generate JSON report for a specific execution
result = await client.call_tool("generate_test_report", {
    "execution_id": 123,
    "format": "json"
});

// Generate HTML report for all executions
result = await client.call_tool("generate_test_report", {
    "format": "html"
});
```

## Installation Information
- **Installation Scripts**: The server can be installed via npm or by cloning the repository and running `npm install`
- **Main Server**: `testing-validation-system/src/mcp/test-mcp-server.js`
- **Dependencies**: 
  - @modelcontextprotocol/sdk
  - pg (PostgreSQL client)
  - Node.js 14+
- **Status**: Active development with full functionality

## Configuration
**Environment Configuration (.env):**
```bash
DATABASE_URL=postgresql://postgres:2001@localhost:5432/postgres
```

**MCP Configuration (mcp.json):**
```json
{
  "mcpServers": {
    "testing-validation": {
      "command": "node",
      "args": ["testing-validation-system/src/mcp/test-mcp-server.js"],
      "env": {
        "DATABASE_URL": "postgresql://postgres:2001@localhost:5432/postgres"
      }
    }
  }
}
```

## Integration
- **VS Code Extension**: Compatible with VS Code through MCP integration
- **Companion Systems**: Integrates with PostgreSQL for data persistence, Docker/Podman for containerized testing
- **API Compatibility**: Uses MCP protocol for communication with client applications

## How to Start and Operate this MCP
### Manual Start:
```bash
# Navigate to the server directory
cd testing-validation-system/src/mcp

# Start the server
node test-mcp-server.js
```

### Automated Start:
```bash
# Add to package.json scripts
"scripts": {
  "start:mcp": "node testing-validation-system/src/mcp/test-mcp-server.js"
}

# Start via npm
npm run start:mcp
```

### Service Management:
```bash
# Check if the server is running
ps aux | grep test-mcp-server

# Stop the server (find PID first)
kill <PID>
```

## Configuration Options
- **Database Connection**: Configure PostgreSQL connection through DATABASE_URL environment variable
- **Test Execution Environment**: Choose between local, podman, or CI environments
- **Security Rules**: Customize Semgrep security scanning rules
- **Report Formats**: Generate reports in JSON, HTML, or Markdown formats

## Key Features
1. **Comprehensive Test Management**: Create and manage test suites and test cases with metadata
2. **Multi-Environment Testing**: Execute tests in local, containerized (Podman), or CI environments
3. **Security Scanning**: Integrated Semgrep security scanning for code analysis
4. **Detailed Reporting**: Generate comprehensive test reports in multiple formats
5. **Data Persistence**: PostgreSQL-based storage for test results and execution history
6. **Flexible Test Types**: Support for unit, integration, e2e, security, and performance tests

## Security Considerations
- **Database Security**: Uses PostgreSQL with configurable connection parameters
- **Input Validation**: All inputs are validated before processing
- **Command Execution**: Security scanning tools run in controlled environments
- **Data Protection**: Test results and execution data stored securely in database

## Troubleshooting
- **Common Issue 1**: Database connection errors
  - Solution: Verify DATABASE_URL environment variable and PostgreSQL server status
- **Common Issue 2**: Test execution failures
  - Solution: Check test environment configuration and dependencies
- **Common Issue 3**: Security scan errors
  - Solution: Verify Semgrep installation and rule configurations
- **Debug Mode**: Enable verbose logging by setting LOG_LEVEL=debug environment variable

## Testing and Validation
**Test Suite:**
```bash
# Run the server's own tests
cd testing-validation-system
npm test

# Validate server functionality
curl -X POST http://localhost:3000/api/validate
```

## Performance Metrics
- **Expected Response Time**: < 500ms for most operations
- **Database Query Performance**: Optimized for large test result sets
- **Memory Usage**: ~50MB base memory, scales with test data
- **Scalability**: Supports concurrent test executions and large test suites

## Backup and Recovery
- **Database Backups**: Regular PostgreSQL dumps recommended
- **Test Data**: Export test results and configurations periodically
- **Recovery Process**: Restore database from backup and reconfigure server settings

## Version Information
- **Current Version**: 1.0.0
- **Last Updated**: 2023-11-15
- **Compatibility**: Compatible with MCP SDK v1.0.0, Node.js 14+

## Support and Maintenance
- **Documentation**: This documentation and inline code comments
- **Community Support**: Available through project repository issues
- **Maintenance Schedule**: Regular updates with bug fixes and feature enhancements

## References
- [MCP SDK Documentation](https://modelcontextprotocol.io)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Jest Testing Framework](https://jestjs.io/)
- [Semgrep Security Scanner](https://semgrep.dev/)
- [Docker Compose](https://docs.docker.com/compose/)

---

## Extra Info

### Database Schema
The MCP Testing Validation server uses the following database tables:

- **test_suites**: Stores test suite information (id, name, description, type)
- **test_cases**: Stores individual test cases (id, suite_id, name, description, file_path, test_function, tags, priority)
- **test_executions**: Records test execution history (id, suite_id, execution_name, status, environment, branch, commit_hash, started_at, completed_at)
- **test_results**: Stores individual test results (id, execution_id, case_id, status, duration_ms, error_message, created_at)
- **static_analysis_results**: Stores security scan findings (id, execution_id, rule_id, severity, file_path, line_number, message)

### Test Types and Execution
The server supports five types of tests:

1. **Unit Tests**: Executed using Jest framework
2. **Integration Tests**: Run with Docker/Podman containers
3. **E2E Tests**: End-to-end testing with browser automation
4. **Security Tests**: Static analysis with Semgrep
5. **Performance Tests**: Load and performance testing

### Environment-Specific Configuration
- **Local Environment**: Direct execution on the host machine
- **Podman Environment**: Uses Podman containers for isolated testing
- **CI Environment**: Optimized for continuous integration pipelines

### Report Generation
The server supports multiple report formats:
- **JSON**: Machine-readable format for programmatic processing
- **HTML**: Visual reports with styling and formatting
- **Markdown**: Human-readable format for documentation