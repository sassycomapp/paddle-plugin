@echo off
echo Testing MCP Servers...
echo ======================

echo.
echo 1. Testing filesystem server...
npx -y @modelcontextprotocol/server-filesystem . --help >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ filesystem: OK
) else (
    echo ❌ filesystem: FAILED
)

echo.
echo 2. Testing github server...
npx -y @modelcontextprotocol/server-github --help >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ github: OK
) else (
    echo ❌ github: FAILED
)

echo.
echo 3. Testing postgres server...
npx -y @modelcontextprotocol/server-postgres --help >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ postgres: OK
) else (
    echo ❌ postgres: FAILED
)

echo.
echo 4. Testing brave-search server...
npx -y @modelcontextprotocol/server-brave-search --help >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ brave-search: OK
) else (
    echo ❌ brave-search: FAILED
)

echo.
echo 5. Testing fetch server...
npx -y @modelcontextprotocol/server-fetch --help >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ fetch: OK
) else (
    echo ❌ fetch: NOT FOUND
)

echo.
echo Test complete!
pause
