@echo off
echo Setting up MCP Installer...
echo.

:: Install required global packages
echo Installing MCP Inspector...
call npm install -g @modelcontextprotocol/inspector

:: Install common MCP servers
echo Installing common MCP servers...
call npm install -g @modelcontextprotocol/server-filesystem
call npm install -g @modelcontextprotocol/server-fetch
call npm install -g @modelcontextprotocol/server-github
call npm install -g @modelcontextprotocol/server-postgres
call npm install -g @modelcontextprotocol/server-sqlite
call npm install -g @modelcontextprotocol/server-brave-search

echo.
echo ✅ MCP Installer setup complete!
echo.
echo Available commands:
echo   npx @modelcontextprotocol/inspector    - Launch MCP Inspector
echo   node mcp_servers/install-mcp-server.js - Install specific MCP servers
echo.
echo To use MCP Inspector:
echo   1. Run: npx @modelcontextprotocol/inspector
echo   2. Open http://localhost:6274 in your browser
echo   3. Configure your MCP servers
echo.
pause
