# MCP Server Documentation Template

## Brief Overview
The MCP KiloCode MCP Server Installer is a specialized command-line utility designed specifically for the KiloCode ecosystem to automate the installation and configuration of MCP servers. Unlike generic MCP installers, this tool is purpose-built for the KiloCode development environment, providing seamless integration with existing project structures and automated .vscode/mcp.json configuration. Its unique value proposition lies in its deep integration with the KiloCode architecture, supporting filesystem, github, postgres, and brave-search servers with optimized installation paths and environment-specific configurations tailored for the KiloCode development workflow.

## Tool list
- install_mcp_server

## Available Tools and Usage
### Tool 1: install_mcp_server
**Description:** Installs MCP servers via command line with automatic configuration and dependency management

**Parameters:**
- `server_name` (string): The name of the MCP server to install (filesystem, github, postgres, brave-search)

**Returns:**
Installation status and configuration confirmation

**Example:**
```javascript
// Example usage
result = await client.call_tool("install_mcp_server", {
    "server_name": "filesystem"
});
```

## Installation Information
- **Installation Scripts**: `mcp_servers/install-mcp-server.js` (KiloCode-specific installer)
- **Main Server**: `mcp_servers/install-mcp-server.js` (KiloCode MCP Server Installer)
- **Dependencies**: Node.js runtime, npm package manager, KiloCode project structure
- **Status**: Pre-installed and integrated into KiloCode development environment
- **Complementary Installer**: `@anaisbetts/mcp-installer` (Generic MCP Package Installer for broader ecosystem compatibility)

## Configuration
**Environment Configuration (.env):**
```bash
# No environment variables required for basic operation
# Optional configuration for custom installation paths
MCP_INSTALL_PATH=/custom/path
```

**MCP Configuration (mcp.json):**
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"],
      "env": {
        "NODE_ENV": "production",
        "KILOCODE_ENV": "development"
      }
    },
    "github": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "your_github_token",
        "KILOCODE_PROJECT_PATH": "/current/project/path"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://user:password@localhost:5432/database",
        "KILOCODE_DB_CONFIG": "postgres-config.json"
      }
    },
    "brave-search": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your_brave_api_key",
        "KILOCODE_SEARCH_CONFIG": "brave-search-config.json"
      }
    }
  }
}
```

## Integration
- **VS Code Extension**: Automatically configures .vscode/mcp.json with server configurations
- **Companion Systems**: Deep integration with KiloCode project structure, direct npx execution startup system, and manual server management
- **API Compatibility**: Compatible with standard MCP protocol and KiloCode-specific environment variable configurations

## How to Start and Operate this MCP
### Manual Start:
```bash
# Run the installer with server name
node mcp_servers/install-mcp-server.js <server-name>

# Example installations
node mcp_servers/install-mcp-server.js filesystem
node mcp_servers/install-mcp-server.js github
node mcp_servers/install-mcp-server.js postgres
node mcp_servers/install-mcp-server.js "brave-search"
```

### Automated Start:
```bash
# No automated startup required - runs on-demand
# Can be integrated into CI/CD pipelines for automated server setup
```

### Service Management:
```bash
# View available servers and usage
node mcp_servers/install-mcp-server.js

# Get help and usage instructions
node mcp_servers/install-mcp-server.js --help

# List installed servers (if implemented)
node mcp_servers/install-mcp-server.js --list
```

## Configuration Options
- **Global Installation**: Installs packages globally via npm by default
- **Automatic Configuration**: Updates .vscode/mcp.json automatically during installation
- **Base Path**: Uses current working directory as base path for installations
- **Custom Paths**: Optional environment variable for custom installation locations

## Key Features
1. **Multi-Server Support**: Supports filesystem, github, postgres, and brave-search MCP servers
2. **Automatic Configuration**: Automatically updates VS Code MCP settings
3. **Dependency Management**: Handles npm package installation and dependency resolution
4. **Cross-Platform**: Compatible with Windows, macOS, and Linux operating systems

## Security Considerations
- **File System Access**: Ensure proper file permissions and access controls when installing filesystem servers within KiloCode project structure
- **API Tokens**: Secure storage and management of API tokens for github, brave-search, and other services with KiloCode integration
- **Network Security**: Verify network connectivity and firewall settings for server installations in KiloCode development environment
- **Installation Path Security**: Use appropriate directory permissions and user accounts for KiloCode-specific installation paths

## Troubleshooting
- **Permission Issues**: Run with appropriate user permissions or use sudo if needed
- **Network Connectivity**: Check internet connection for package downloads
- **Node.js Version**: Ensure Node.js (v14+) and npm are properly installed
- **Path Issues**: Verify correct path to install-mcp-server.js script

## Testing and Validation
**Test Suite:**
```bash
# Test basic installer functionality
node mcp_servers/install-mcp-server.js --help

# Test server installation (dry run if available)
node mcp_servers/install-mcp-server.js --dry-run filesystem

# Validate MCP configuration after installation
cat .vscode/mcp.json
```

## Performance Metrics
- **Installation Time**: Typically 30-60 seconds per server depending on network speed
- **Resource Usage**: Minimal CPU and memory usage during installation
- **Disk Space**: Varies by server package size (typically 10-100MB per server)
- **Network**: Requires internet connection for package downloads

## Backup and Recovery
- **Configuration Backup**: Backup .vscode/mcp.json file before major changes
- **Package Cache**: npm cache can be used for offline installations
- **Installation Logs**: Keep installation logs for troubleshooting and rollback

## Version Information
- **Current Version**: Based on install-mcp-server.js script version
- **Last Updated**: [Date of last script modification]
- **Compatibility**: Compatible with Node.js 14+ and standard MCP protocol versions

## Support and Maintenance
- **Documentation**: Refer to install-mcp-server.js inline comments and help text
- **Community Support**: Check project repository for issues and discussions
- **Maintenance Schedule**: Update script when new MCP servers are added or dependencies change

## References
- [MCP Protocol Documentation](https://modelcontextprotocol.io)
- [Node.js Package Manager (npm)](https://docs.npmjs.com/)
- [VS Code MCP Extension](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot)

---

## Extra Info
The MCP KiloCode MCP Server Installer provides a streamlined approach to setting up MCP servers in development environments. The installer handles the complex configuration process automatically, ensuring proper integration with VS Code and other development tools.

### Installation Process Flow:
1. User runs installer with server name parameter within KiloCode project directory
2. Installer downloads and installs the specified MCP server package via npm with KiloCode-optimized paths
3. Installer automatically updates .vscode/mcp.json with server configuration and KiloCode-specific environment variables
4. Installer verifies installation and provides status feedback with KiloCode integration confirmation

### Supported Server Types:
- **filesystem**: File system access server for local file operations with KiloCode project path integration
- **github**: GitHub integration server for repository operations with KiloCode project context
- **postgres**: PostgreSQL database server for data operations with KiloCode database configuration support
- **brave-search**: Brave search server for web search functionality with KiloCode search configuration

### KiloCode-Specific Integration Benefits:
- Seamless setup process reduces configuration errors within KiloCode development environment
- Automatic MCP configuration ensures proper VS Code integration with KiloCode project settings
- Cross-platform compatibility works across different development environments with KiloCode path optimization
- Extensible design allows for easy addition of new server types with KiloCode-specific configurations
- Deep integration with KiloCode project structure and development workflow
- Optimized installation paths and environment variables tailored for KiloCode ecosystem