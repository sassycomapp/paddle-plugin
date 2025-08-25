@echo off
echo ==========================================
echo MCP Filesystem Server Verification Test
echo ==========================================

echo.
echo 1. Checking Node.js installation...
node --version
if %errorlevel% neq 0 (
    echo ❌ Node.js not found
    pause
    exit /b 1
)

echo.
echo 2. Checking npm/npx installation...
npm --version
if %errorlevel% neq 0 (
    echo ❌ npm not found
    pause
    exit /b 1
)

echo.
echo 3. Testing MCP Filesystem Server...
echo    Starting server with allowed paths: . and C:\tmp
echo    Press Ctrl+C to stop the server after verification
echo.

cmd /c "npx -y @modelcontextprotocol/server-filesystem . C:\tmp"

echo.
echo ==========================================
echo Test completed
echo ==========================================
pause
