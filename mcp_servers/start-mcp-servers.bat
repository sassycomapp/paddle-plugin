@echo off
echo Starting MCP Servers...

REM Start Filesystem server
start "MCP Filesystem" cmd /k "npx @modelcontextprotocol/server-filesystem ."

REM Start GitHub server
start "MCP GitHub" cmd /k "npx @modelcontextprotocol/server-github"

REM Start Postgres server
start "MCP Postgres" cmd /k "npx @modelcontextprotocol/server-postgres"

REM Start Brave Search server
start "MCP Brave Search" cmd /k "npx @modelcontextprotocol/server-brave-search"

REM Start Testing Validation MCP server
start "Testing Validation MCP" cmd /k "node testing-validation-system/src/mcp/test-mcp-server.js"

REM Start Playwright MCP server
start "Playwright MCP" cmd /k "npx -y @executeautomation/playwright-mcp-server"

echo MCP Servers started in separate windows.
echo Testing Validation System MCP servers included.
pause
