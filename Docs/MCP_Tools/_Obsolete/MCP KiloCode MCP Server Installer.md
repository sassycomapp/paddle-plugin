# MCP Installer

## Features
- Installs MCP servers via command line
- Supports multiple server types (filesystem, github, postgres, brave-search)
- Automatic .vscode/mcp.json configuration
- Package installation and dependency management
- Cross-platform compatibility

## Installation
The MCP Installer is pre-installed in this system at:
```
mcp_servers/install-mcp-server.js
```

No additional installation required.

## Configuration
No configuration needed. The installer uses default settings:
- Installs packages globally via npm
- Updates .vscode/mcp.json automatically
- Uses current working directory as base path

## Startup/Usage
Run the installer with:
```bash
node mcp_servers/install-mcp-server.js <server-name>
```

Available server names:
- filesystem
- github
- postgres
- brave-search

Example:
```bash
node mcp_servers/install-mcp-server.js filesystem
```

## Features and Commands

### 1. Server Installation
Installs MCP servers and dependencies
```bash
# Install filesystem server
node mcp_servers/install-mcp-server.js filesystem

# Install github server
node mcp_servers/install-mcp-server.js github

# Install postgres server
node mcp_servers/install-mcp-server.js postgres

# Install brave-search server
node mcp_servers/install-mcp-server.js "brave-search"
```

### 2. Automatic Configuration
Updates VS Code MCP settings automatically
```bash
# No command needed - automatic on server installation
# Updates .vscode/mcp.json with new server configuration
```

### 3. Dependency Management
Handles package installation via npm
```bash
# No direct command - automatic during server installation
# Uses npm install under the hood
```

### 4. Server Management
Lists available servers and usage
```bash
# View available servers
node mcp_servers/install-mcp-server.js

# Get usage instructions
node mcp_servers/install-mcp-server.js --help
```

## Integration
- Automatically configures VS Code MCP extension
- Works with direct npx execution startup system
- Compatible with .env file for environment variables
- Integrates with manual and scripted server startup methods
