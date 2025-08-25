# IDE Startup Instructions

## System Requirements
- Node.js v18+ installed
- Podman container engine (Docker not supported)
- PostgreSQL database accessible
- Python 3.10+ for RAG operations

## Basic Startup
1. Initialize Podman environment:
```bash
podman machine init
podman machine start
```

2. Start core application services (PostgreSQL and "Placeholder"):
```bash
podman-compose up -d postgres "Placeholder"
```
For comprehensive instructions on managing these services (including stopping, restarting, and viewing logs), please refer to the [Manage Core Services Without Extension](../Systems_Descriptions/Foundation/Manage_Core_Services_Without_Extension.md) guide.

3. Launch VSCode with MCP integration:
```bash
code --extensions-dir ./IDE --user-data-dir ./daemon
```

## MCP Server Initialization
1. Install required servers:
```bash
node mcp_servers/install-mcp-complete.js
```

2. Start all MCP services:
```bash
node mcp_servers/start-mcp-servers.ps1
```

## Verification Steps
1. Check server status:
```bash
node mcp_servers/manage-mcp-servers.js status
```

2. Run system validation:
```bash
node testing-validation-system/verify-installation.js
```

## Troubleshooting
- For connection issues, verify Podman is running
- If database errors occur, check Postgres container logs
- For MCP failures, review mcp-server-status.md
- Memory-related problems should reference agent memory documentation
 

## Other methods
