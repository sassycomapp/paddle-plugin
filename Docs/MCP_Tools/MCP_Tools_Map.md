# MCP Tools Map

This document maps each MCP server to its available tools and shows how to access each tool using KiloCode.

## Filesystem Server
- **Tools**:
  - `file_operations`: Perform file system operations
  - `directory_listing`: List directory contents
- **Access Command**:
```xml
<use_mcp_tool>
<server_name>filesystem</server_name>
<tool_name>file_operations</tool_name>
<arguments>
{
  "operation": "read|write|delete",
  "path": "file/path"
}
</arguments>
</use_mcp_tool>
```

## GitHub Server
- **Tools**:
  - `github_search`: Search GitHub repositories
  - `repo_management`: Manage repositories
- **Access Command**:
```xml
<use_mcp_tool>
<server_name>github</server_name>
<tool_name>github_search</tool_name>
<arguments>
{
  "query": "search terms",
  "limit": 10
}
</arguments>
</use_mcp_tool>
```

## PostgreSQL Server
- **Tools**:
  - `query`: Run SQL queries
  - `schema_management`: Manage database schema
- **Access Command**:
```xml
<use_mcp_tool>
<server_name>postgres</server_name>
<tool_name>query</tool_name>
<arguments>
{
  "sql": "SELECT * FROM table"
}
</arguments>
</use_mcp_tool>
```

## Brave Search Server
- **Tools**:
  - `web_search`: Perform web searches
  - `local_search`: Search for local businesses
- **Access Command**:
```xml
<use_mcp_tool>
<server_name>brave-search</server_name>
<tool_name>web_search</tool_name>
<arguments>
{
  "query": "search terms",
  "count": 10
}
</arguments>
</use_mcp_tool>
```

## Fetch Server
- **Tools**:
  - `http_get`: Make HTTP GET requests
  - `http_post`: Make HTTP POST requests
- **Access Command**:
```xml
<use_mcp_tool>
<server_name>fetch</server_name>
<tool_name>http_get</tool_name>
<arguments>
{
  "url": "https://example.com"
}
</arguments>
</use_mcp_tool>
```

## RAG Server (PGvector)
- **Tools**:
  - `semantic_search`: Perform semantic searches
  - `knowledge_retrieval`: Retrieve relevant knowledge
- **Access Command**:
```xml
<use_mcp_tool>
<server_name>rag-mcp-server</server_name>
<tool_name>semantic_search</tool_name>
<arguments>
{
  "query": "search terms",
  "limit": 5
}
</arguments>
</use_mcp_tool>
```

## Snap Windows Server
- **Tools**:
  - `window_management`: Manage application windows
  - `system_interaction`: Interact with system elements
- **Access Command**:
```xml
<use_mcp_tool>
<server_name>snap-windows</server_name>
<tool_name>window_management</tool_name>
<arguments>
{
  "action": "snap|maximize|minimize",
  "window_title": "Application Name"
}
</arguments>
</use_mcp_tool>
```

## Agent Memory Server
- **Tools**:
  - `memory_store`: Store agent memories
  - `memory_retrieve`: Retrieve agent memories
- **Access Command**:
```xml
<use_mcp_tool>
<server_name>agent-memory</server_name>
<tool_name>memory_retrieve</tool_name>
<arguments>
{
  "agent_id": "agent-name",
  "query": "memory query"
}
</arguments>
</use_mcp_tool>
```

## Testing Validation Server
- **Tools**:
  - `run_tests`: Execute tests
  - `validate_results`: Validate test results
- **Access Command**:
```xml
<use_mcp_tool>
<server_name>testing-validation</server_name>
<tool_name>run_tests</tool_name>
<arguments>
{
  "test_suite": "suite-name"
}
</arguments>
</use_mcp_tool>
```

## MCP Memory Service
- **Tools**:
  - `vector_search`: Search vector embeddings
  - `memory_backup`: Backup memory data
- **Access Command**:
```xml
<use_mcp_tool>
<server_name>mcp-memory-service</server_name>
<tool_name>vector_search</tool_name>
<arguments>
{
  "query_embedding": [0.1, 0.2, ...],
  "top_k": 5
}
</arguments>
</use_mcp_tool>
```

## Secrets Manager MCP
- **Tools**:
  - `secret_retrieval`: Retrieve secrets
  - `credential_management`: Manage credentials
- **Access Command**:
```xml
<use_mcp_tool>
<server_name>secrets-manager-mcp</server_name>
<tool_name>secret_retrieval</tool_name>
<arguments>
{
  "secret_name": "API_KEY"
}
</arguments>
</use_mcp_tool>
```

## Logging Telemetry MCP
- **Tools**:
  - `log_retrieval`: Retrieve logs
  - `telemetry_collection`: Collect telemetry data
- **Access Command**:
```xml
<use_mcp_tool>
<server_name>logging-telemetry-mcp</server_name>
<tool_name>log_retrieval</tool_name>
<arguments>
{
  "log_type": "error",
  "limit": 20
}
</arguments>
</use_mcp_tool>
```

## Podman Container Control Server
- **Tools**:
  - `list_containers`: List all running and stopped containers
  - `container_start`: Start a container
  - `container_stop`: Stop a container
  - `container_restart`: Restart a container
  - `container_remove`: Remove a container
  - `container_logs`: Get logs from a container
  - `container_exec`: Execute a command in a running container
- **Access Command**:
```xml
<use_mcp_tool>
<server_name>podman</server_name>
<tool_name>list_containers</tool_name>
<arguments>
{
  "all": true
}
</arguments>
</use_mcp_tool>
```

## How to Use These Tools
To use any of these tools in KiloCode, simply use the XML-formatted `use_mcp_tool` command shown for each tool. Fill in the appropriate arguments for your specific use case.
