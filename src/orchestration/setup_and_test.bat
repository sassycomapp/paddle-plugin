@echo off
setlocal enabledelayedexpansion

echo 🚀 AG2 Orchestrator Setup and Test Script
echo ========================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed. Please install Node.js v16 or higher.
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo [INFO] Node.js version: 
node --version
echo [INFO] Python version: 
python --version
echo.

REM Install Python dependencies
echo [INFO] Installing Python dependencies...
cd src\orchestration
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)

REM Install Node.js dependencies
echo [INFO] Installing Node.js dependencies...
cd ..\..\mcp_servers
npm install
if errorlevel 1 (
    echo [ERROR] Failed to install Node.js dependencies
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist "..\src\orchestration\.env" (
    echo [WARNING] .env file not found. Creating template...
    (
        echo # OpenRouter ^(Recommended^)
        echo OPENROUTER_API_KEY=your_openrouter_api_key_here
        echo OPENROUTER_HTTP_REFERER=http://localhost
        echo OPENROUTER_X_TITLE=AG2 Orchestrator Test
        echo.
        echo # OR OpenAI
        echo OPENAI_API_KEY=your_openai_api_key_here
        echo OPENAI_MODEL=gpt-4o-mini
        echo.
        echo # OR Azure OpenAI
        echo AZURE_OPENAI_API_KEY=your_azure_api_key_here
        echo AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
        echo AZURE_OPENAI_API_VERSION=2024-02-15-preview
        echo AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
        echo.
        echo # Brave Search API Key
        echo BRAVE_API_KEY=your_brave_api_key_here
    ) > "..\src\orchestration\.env"
    echo [WARNING] Please edit ..\src\orchestration\.env with your actual API keys
)

REM Run MCP server tests
echo [INFO] Running MCP server tests...
cd ..\src\orchestration
python test_mcp_servers.py
if errorlevel 1 (
    echo [ERROR] MCP server tests failed
    pause
    exit /b 1
)

REM Ask user if they want to run full system test
set /p run_full="Do you want to run the full AG2 system test? (y/n): "
if /i "%run_full%"=="y" (
    echo [INFO] Running full AG2 system test...
    python test_ag2_system.py
)

REM Ask user if they want to run LLM-free test
set /p run_llm_free="Do you want to run LLM-free test (MCP servers only)? (y/n): "
if /i "%run_llm_free%"=="y" (
    echo [INFO] Running LLM-free test...
    python test_ag2_system.py --skip-llm
)

echo [INFO] Setup and testing complete!
echo [INFO] Check the logs above for any errors or issues.
pause
