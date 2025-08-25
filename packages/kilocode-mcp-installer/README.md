# @kilocode/mcp-installer

KiloCode-customized MCP server installer with dual configuration support for both `.vscode/mcp.json` and `.kilocode/mcp.json`.

## Features

- **Dual Configuration Updates**: Automatically updates both `.vscode/mcp.json` and `.kilocode/mcp.json`
- **KiloCode-Specific Templates**: Enhanced configuration templates with KiloCode environment variables
- **Project Structure Awareness**: Automatic detection of KiloCode project structure
- **KiloCode-Specific MCP Servers**: Support for agent-memory, mcp-memory-service, testing-validation, and other KiloCode servers
- **Configuration Synchronization**: Keep both configuration files synchronized
- **Enhanced Environment Variables**: Automatic injection of KILOCODE_ENV, KILOCODE_PROJECT_PATH, KILOCODE_DB_CONFIG

## Installation

```bash
npm install -g @kilocode/mcp-installer
```

## Usage

### Install an MCP Server

```bash
# Install a server with dual configuration updates
kilocode-mcp-install filesystem

# Force installation even if server exists
kilocode-mcp-install filesystem --force

# Install globally
kilocode-mcp-install github --global
```

### Remove an MCP Server

```bash
# Remove a server from both configurations
kilocode-mcp-remove filesystem

# Remove from global configuration only
kilocode-mcp-remove github --global
```

### List Installed Servers

```bash
# List basic server information
kilocode-mcp-list

# Show detailed server information
kilocode-mcp-list --verbose
```

### Configuration Management

```bash
# Generate .kilocode/mcp.json from existing .vscode/mcp.json
kilocode-mcp-install generate-config

# Synchronize both configuration files
kilocode-mcp-install sync
```

## Supported Servers

### Core MCP Servers
- `filesystem` - Filesystem access with KiloCode path integration
- `github` - GitHub integration with KiloCode environment variables
- `postgres` - PostgreSQL database with KiloCode DB config
- `fetch` - HTTP fetch server

### KiloCode-Specific Servers
- `agent-memory` - Multi-tiered memory architecture
- `rag-mcp-server` - RAG system with ChromaDB integration
- `testing-validation` - Testing and validation services
- `mcp-memory-service` - Advanced memory management

## Configuration Templates

### VSCode Configuration (`.vscode/mcp.json`)
Standard MCP server configuration with command, args, and environment variables.

### KiloCode Configuration (`.kilocode/mcp.json`)
Enhanced configuration with KiloCode-specific environment variables:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
      "env": {
        "NODE_ENV": "production",
        "KILOCODE_ENV": "development",
        "KILOCODE_PROJECT_PATH": "/current/project/path",
        "KILOCODE_FS_PATH": "/current/project/path",
        "KILOCODE_PROJECT_NAME": "paddle-plugin"
      }
    }
  }
}
```

## Environment Variables

The installer automatically injects KiloCode-specific environment variables:

- `KILOCODE_ENV`: KiloCode environment (development/production)
- `KILOCODE_PROJECT_PATH`: Absolute path to the current project
- `KILOCODE_PROJECT_NAME`: Name of the current project
- `KILOCODE_DB_CONFIG`: Database configuration for database servers
- `KILOCODE_RAG_CONFIG`: RAG system configuration
- `KILOCODE_GITHUB_CONFIG`: GitHub integration configuration

## Project Structure Detection

The installer automatically detects KiloCode projects by looking for:

- `.kilocode/` directory
- `package.json` with KiloCode-specific keywords
- Existing `.vscode/mcp.json` configuration

## Development

### Building

```bash
cd packages/kilocode-mcp-installer
npm install
npm run build
```

### Testing

```bash
npm test
```

### Linting

```bash
npm run lint
```

## License

MIT