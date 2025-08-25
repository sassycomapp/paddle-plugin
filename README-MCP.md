# MCP Server Management

This vsc_ide project uses Model Context Protocol (MCP) servers for various integrations. Due to compatibility issues with process managers on Windows, we use direct npx commands to start the servers.

## Available MCP Servers

- **Filesystem**: Provides file system access
- **GitHub**: Integrates with GitHub API
- **Postgres**: Connects to PostgreSQL databases
- **Brave Search**: Provides web search capabilities
- **Snap Windows**: Window management for Windows systems

## Setup

1. Install the required MCP server packages:
```bash
node mcp_servers/install-mcp-server.js filesystem
node mcp_servers/install-mcp-server.js github  
node mcp_servers/install-mcp-server.js postgres
node mcp_servers/install-mcp-server.js "brave-search"
```

2. Configure environment variables in the `.env` file:
```
GITHUB_PERSONAL_ACCESS_TOKEN=your_token_here
DATABASE_URL=your_database_url_here
BRAVE_API_KEY=your_api_key_here
```

## Starting Servers

### Method 1: Manual Start
Run each server individually:
```bash
npx @modelcontextprotocol/server-filesystem .
npx @modelcontextprotocol/server-github
npx @modelcontextprotocol/server-postgres
npx @modelcontextprotocol/server-brave-search
```

### Method 2: Batch Script (Windows)
Run the batch script to start all servers:
```bash
mcp_servers\start-mcp-servers.bat
```

### Method 3: PowerShell Script (Windows)
Run the PowerShell script to start all servers:
```powershell
mcp_servers\start-mcp-servers.ps1
```

## Integration

Use the VS Code MCP extension for IDE integration. The extension will automatically detect and connect to the running MCP servers.

## Notes

- The MCP Inspector CLI has known Windows command parsing issues and is not recommended
+ Process managers have compatibility issues on Windows
- Direct npx execution is the most reliable method
- Consider using Windows Task Scheduler to automatically start servers at login
