# MCP Installer Setup

This directory contains tools and scripts for installing and managing MCP (Model Context Protocol) servers.

## 🚀 Quick Start

### Option 1: PowerShell (Recommended for Windows)
```powershell
.\mcp_servers\setup-mcp-installer.ps1
```

### Option 2: Batch Script
```cmd
mcp_servers\setup-mcp-installer.bat
```

### Option 3: Manual Installation
```bash
# Install MCP Inspector globally
npm install -g @modelcontextprotocol/inspector

# Install individual MCP servers
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-fetch
npm install -g @modelcontextprotocol/server-github
```

## 📋 Available MCP Servers

| Server | Package | Description | Required Env Vars |
|--------|---------|-------------|-------------------|
| **filesystem** | `@modelcontextprotocol/server-filesystem` | File system access | None |
| **fetch** | `@modelcontextprotocol/server-fetch` | HTTP requests | None |
| **github** | `@modelcontextprotocol/server-github` | GitHub API integration | `GITHUB_PERSONAL_ACCESS_TOKEN` |
| **postgres** | `@modelcontextprotocol/server-postgres` | PostgreSQL database | `DATABASE_URL` |
| **sqlite** | `@modelcontextprotocol/server-sqlite` | SQLite database | None |
| **brave-search** | `@modelcontextprotocol/server-brave-search` | Brave search API | `BRAVE_API_KEY` |

## 🔧 Usage

### Using the Installer Script
```bash
# List available servers
node mcp_servers/install-mcp-server.js

# Install specific server
node mcp_servers/install-mcp-server.js filesystem
node mcp_servers/install-mcp-server.js github
```

### Using MCP Inspector
The MCP Inspector provides a web interface for managing MCP servers:

```bash
# Launch inspector
npx @modelcontextprotocol/inspector

# Open http://localhost:6274 in your browser
```

### Manual Configuration
Edit `.vscode/mcp.json` to configure MCP servers:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
      "env": {}
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your-token-here"
      }
    }
  }
}
```

## 🔐 Environment Variables

Set these environment variables before installing servers that require them:

### GitHub Server
```bash
export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here
```

### PostgreSQL Server
```bash
export DATABASE_URL=postgresql://user:password@localhost:5432/database
```

### Brave Search Server
```bash
export BRAVE_API_KEY=your_brave_api_key_here
```

## 🛠️ Development

### Adding New Servers
Edit `install-mcp-server.js` to add new MCP servers to the registry:

```javascript
const MCP_SERVERS = {
  'new-server': {
    package: '@modelcontextprotocol/server-new',
    description: 'Description of new server',
    args: ['arg1', 'arg2'],
    env: ['ENV_VAR_1', 'ENV_VAR_2']
  }
};
```

### Testing MCP Servers
Use the inspector to test MCP servers:

```bash
# Test filesystem server
npx @modelcontextprotocol/inspector --server filesystem

# Test with custom config
npx @modelcontextprotocol/inspector --config .vscode/mcp.json --server github
```

## 📁 File Structure
```
mcp_servers/
├── install-mcp-server.js     # Main installer script
├── setup-mcp-installer.ps1   # PowerShell setup script
├── setup-mcp-installer.bat   # Batch setup script
└── README.md                # This documentation
```

## 🚨 Troubleshooting

### Common Issues

1. **Permission Errors**
   ```bash
   # Run as administrator or use sudo
   sudo npm install -g @modelcontextprotocol/inspector
   ```

2. **Port Already in Use**
   - Change the port in `.vscode/mcp.json`
   - Kill existing processes: `npx kill-port 6274`

3. **Environment Variables Not Found**
   - Ensure variables are set in your shell profile
   - Restart VS Code after setting variables

4. **Server Not Starting**
   - Check if the package is installed: `npm list -g @modelcontextprotocol/server-name`
   - Verify the command path in mcp.json
   - Check server logs in MCP Inspector

### Getting Help
- MCP Inspector: http://localhost:6274
- MCP Documentation: https://modelcontextprotocol.io
- GitHub Issues: https://github.com/modelcontextprotocol/servers
