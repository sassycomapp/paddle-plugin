# MCP Installer Setup Script for PowerShell

Write-Host "Setting up MCP Installer..." -ForegroundColor Green
Write-Host ""

# Install required global packages
Write-Host "Installing MCP Inspector..." -ForegroundColor Yellow
npm install -g @modelcontextprotocol/inspector

# Install common MCP servers
Write-Host "Installing common MCP servers..." -ForegroundColor Yellow
$servers = @(
    "@modelcontextprotocol/server-filesystem",
    "@modelcontextprotocol/server-fetch",
    "@modelcontextprotocol/server-github",
    "@modelcontextprotocol/server-postgres",
    "@modelcontextprotocol/server-sqlite",
    "@modelcontextprotocol/server-brave-search"
)

foreach ($server in $servers) {
    Write-Host "  Installing $server..." -ForegroundColor Cyan
    npm install -g $server
}

Write-Host ""
Write-Host "✅ MCP Installer setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Available commands:" -ForegroundColor Yellow
Write-Host "  npx @modelcontextprotocol/inspector    - Launch MCP Inspector"
Write-Host "  node mcp_servers/install-mcp-server.js - Install specific MCP servers"
Write-Host ""
Write-Host "To use MCP Inspector:" -ForegroundColor Yellow
Write-Host "  1. Run: npx @modelcontextprotocol/inspector"
Write-Host "  2. Open http://localhost:6274 in your browser"
Write-Host "  3. Configure your MCP servers"
Write-Host ""

# Create a sample configuration
$configPath = ".vscode/mcp.json"
$config = @{
    mcpServers = @{
        filesystem = @{
            command = "npx"
            args = @("-y", "@modelcontextprotocol/server-filesystem", ".")
            env = @{}
        }
        fetch = @{
            command = "npx"
            args = @("-y", "@modelcontextprotocol/server-fetch")
            env = @{}
        }
    }
}

$config | ConvertTo-Json -Depth 10 | Out-File -FilePath $configPath -Encoding UTF8
Write-Host "Created sample MCP configuration at $configPath" -ForegroundColor Green
