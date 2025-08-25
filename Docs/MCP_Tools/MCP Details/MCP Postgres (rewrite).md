# MCP Server Documentation Template

## Brief Overview
The MCP Postgres Server provides PostgreSQL database access through the Model Context Protocol. It enables SQL query execution and database management operations.

## Tool list
- execute_query
- get_table_info
- get_schema_info
- create_table
- insert_data
- update_data
- delete_data
- list_tables
- get_connection_info

## Available Tools and Usage
### Tool 1: execute_query
**Description:** Execute SQL queries against the PostgreSQL database

**Parameters:**
- `query` (string): The SQL query to execute
- `parameters` (array): Optional parameters for parameterized queries

**Returns:**
Query results in tabular format with column names and row data

**Example:**
```javascript
// Example usage
result = await client.call_tool("execute_query", {
    "query": "SELECT * FROM users WHERE status = $1",
    "parameters": ["active"]
});
```

### Tool 2: get_table_info
**Description:** Retrieve information about a specific table including columns, data types, and constraints

**Parameters:**
- `table_name` (string): Name of the table to inspect

**Returns:**
Table schema information including column names, data types, nullability, and constraints

**Example:**
```javascript
// Example usage
result = await client.call_tool("get_table_info", {
    "table_name": "users"
});
```

### Tool 3: get_schema_info
**Description:** Get information about the entire database schema including all tables and their relationships

**Parameters:**
- `schema_name` (string): Optional schema name (defaults to public)

**Returns:**
Complete database schema with tables, columns, foreign keys, and indexes

**Example:**
```javascript
// Example usage
result = await client.call_tool("get_schema_info", {
    "schema_name": "public"
});
```

### Tool 4: create_table
**Description:** Create a new table in the database with specified columns and constraints

**Parameters:**
- `table_name` (string): Name for the new table
- `columns` (array): Array of column definitions with name, type, and constraints

**Returns:**
Confirmation of table creation with success status and any warnings

**Example:**
```javascript
// Example usage
result = await client.call_tool("create_table", {
    "table_name": "products",
    "columns": [
        {"name": "id", "type": "SERIAL PRIMARY KEY"},
        {"name": "name", "type": "VARCHAR(255) NOT NULL"},
        {"name": "price", "type": "DECIMAL(10,2)"},
        {"name": "created_at", "type": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"}
    ]
});
```

### Tool 5: insert_data
**Description:** Insert data into a specified table

**Parameters:**
- `table_name` (string): Target table name
- `data` (object): Data to insert with column-value pairs
- `returning` (string): Optional column to return (defaults to all columns)

**Returns:**
Inserted data with generated IDs and timestamps if applicable

**Example:**
```javascript
// Example usage
result = await client.call_tool("insert_data", {
    "table_name": "users",
    "data": {
        "username": "john_doe",
        "email": "john@example.com",
        "status": "active"
    },
    "returning": "id"
});
```

### Tool 6: update_data
**Description:** Update existing data in a table

**Parameters:**
- `table_name` (string): Target table name
- `data` (object): Column-value pairs to update
- `where` (object): Conditions for which rows to update
- `parameters` (array): Optional parameters for parameterized updates

**Returns:**
Number of rows affected and updated data

**Example:**
```javascript
// Example usage
result = await client.call_tool("update_data", {
    "table_name": "users",
    "data": {
        "status": "inactive",
        "last_login": "2024-01-15T10:30:00Z"
    },
    "where": {
        "username": "john_doe"
    }
});
```

### Tool 7: delete_data
**Description:** Delete data from a table

**Parameters:**
- `table_name` (string): Target table name
- `where` (object): Conditions for which rows to delete
- `parameters` (array): Optional parameters for parameterized deletes

**Returns:**
Number of rows deleted and confirmation of deletion

**Example:**
```javascript
// Example usage
result = await client.call_tool("delete_data", {
    "table_name": "users",
    "where": {
        "status": "inactive",
        "last_login": {"$lt": "2023-01-01T00:00:00Z"}
    }
});
```

### Tool 8: list_tables
**Description:** List all tables in the database or schema

**Parameters:**
- `schema_name` (string): Optional schema name (defaults to public)
- `include_views` (boolean): Whether to include views in the results

**Returns:**
List of tables with basic information like name, size, and row count

**Example:**
```javascript
// Example usage
result = await client.call_tool("list_tables", {
    "schema_name": "public",
    "include_views": true
});
```

### Tool 9: get_connection_info
**Description:** Get information about the current database connection

**Parameters:**
- `detailed` (boolean): Whether to return detailed connection statistics

**Returns:**
Connection information including database version, connection status, and performance metrics

**Example:**
```javascript
// Example usage
result = await client.call_tool("get_connection_info", {
    "detailed": true
});
```

## Installation Information
- **Installation Scripts**: `node mcp_servers/install-mcp-server.js postgres`
- **Main Server**: `mcp_servers/install-mcp-server.js`
- **Dependencies**: PostgreSQL client libraries, Node.js runtime
- **Status**: ✅ Working (as per MCP Inspection Report)

## Configuration
**Environment Configuration (.env):**
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=database_name
DATABASE_USER=username
DATABASE_PASSWORD=password
```

**MCP Configuration (mcp.json):**
```json
{
  "mcpServers": {
    "postgres": {
      "command": "node",
      "args": ["mcp_servers/install-mcp-server.js", "postgres"],
      "env": {
        "DATABASE_URL": "postgresql://username:password@localhost:5432/database_name"
      }
    }
  }
}
```

## Integration
- **VS Code Extension**: Works with VS Code MCP extension for database operations
- **Companion Systems**: Supports direct command-line execution and integration with other MCP servers
- **API Compatibility**: Compatible with PostgreSQL 10+ versions and standard SQL protocols

## How to Start and Operate this MCP
### Manual Start:
```bash
node mcp_servers/install-mcp-server.js postgres
```

### Automated Start:
```bash
# Using npm script (if available)
npm run mcp:postgres

# Or using the direct command
npx -y @modelcontextprotocol/server-postgres
```

### Service Management:
```bash
# Start the service
node mcp_servers/install-mcp-server.js postgres

# Check status
ps aux | grep postgres

# Stop the service (find PID first)
kill <PID>
```

## Configuration Options
- **Database Connection**: Configure connection string, host, port, and credentials
- **Connection Pooling**: Configure maximum connections, timeout settings, and pool size
- **Query Timeout**: Set maximum execution time for queries
- **SSL/TLS**: Enable secure database connections with SSL certificates
- **Connection Retry**: Configure retry logic for connection failures

## Key Features
1. PostgreSQL protocol implementation with full SQL support
2. Connection pooling for efficient database access
3. Parameterized query support for security and performance
4. Automatic configuration and setup
5. Secure credential handling through environment variables
6. Transaction management with commit/rollback support
7. Schema inspection and table management tools
8. Real-time query execution and result processing

## Security Considerations
- Database credentials stored in environment variables, not in configuration files
- Support for SSL/TLS encrypted connections
- Parameterized queries prevent SQL injection attacks
- Connection pooling limits concurrent connections to prevent resource exhaustion
- Secure handling of query results and sensitive data
- Support for database-level authentication and authorization

## Troubleshooting
- **Connection Issues**: Verify database URL and credentials, check network connectivity
- **Permission Errors**: Ensure proper database user permissions for required operations
- **Query Timeouts**: Adjust query timeout settings or optimize slow queries
- **Connection Pool Exhaustion**: Increase pool size or implement connection reuse
- **SSL Connection Problems**: Verify SSL certificates and configuration

## Testing and Validation
**Test Suite:**
```bash
# Test basic connectivity
npx -y @modelcontextprotocol/server-postgres

# Test specific operations
node -e "
const client = require('./mcp_servers/postgres-client');
client.testConnection().then(console.log);
"

# Validate installation
node mcp_servers/install-mcp-server.js --validate postgres
```

## Performance Metrics
- Expected query execution time: < 100ms for simple queries
- Connection pool capacity: 10-50 concurrent connections
- Memory usage: ~50MB base memory + query-specific memory
- Scalability: Supports high-volume transaction processing with proper connection management

## Backup and Recovery
- Regular database backups using pg_dump or similar tools
- Point-in-time recovery through WAL (Write-Ahead Logging)
- Connection state preservation during server restarts
- Transaction rollback capabilities for failed operations

## Version Information
- **Current Version**: Latest MCP Postgres Server implementation
- **Last Updated**: 2024-01-15
- **Compatibility**: PostgreSQL 10+, Node.js 14+, MCP Protocol v1.0

## Support and Maintenance
- **Documentation**: Refer to PostgreSQL official documentation and MCP protocol specifications
- **Community Support**: GitHub issues and community forums for MCP servers
- **Maintenance Schedule**: Regular updates with security patches and performance improvements

## References
- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [PostgreSQL Official Documentation](https://www.postgresql.org/docs/)
- [Node.js PostgreSQL Client Libraries](https://node-postgres.com/)

---

## Extra Info
PostgreSQLDB and PGvector are both installed but are not the focus of these docs you are writing now. The MCP Postgres Server focuses on providing general-purpose database access through the Model Context Protocol, enabling AI systems to interact with PostgreSQL databases for data storage, retrieval, and management operations. The server implements standard SQL operations with proper security measures and connection management for reliable database access.