Write-Host "Starting MCP Servers..." -ForegroundColor Green

# Start Filesystem server
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'MCP Filesystem Server' -ForegroundColor Cyan; npx @modelcontextprotocol/server-filesystem ."

# Start GitHub server  
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'MCP GitHub Server' -ForegroundColor Cyan; npx @modelcontextprotocol/server-github"

# Start Postgres server
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'MCP Postgres Server' -ForegroundColor Cyan; npx @modelcontextprotocol/server-postgres"

# Start Brave Search server
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'MCP Brave Search Server' -ForegroundColor Cyan; npx @modelcontextprotocol/server-brave-search"

Write-Host "MCP Servers started in separate windows." -ForegroundColor Green
