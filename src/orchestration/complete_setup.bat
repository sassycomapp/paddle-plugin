@echo off
REM Complete AG2 Orchestrator Setup Script for Windows
REM This script sets up all required services and dependencies for the AG2 system.

echo.
echo ============================================
echo AG2 Orchestrator Complete Setup
echo ============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if npm is available
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Docker is available
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not running
    pause
    exit /b 1
)

REM Install Python dependencies
echo [INFO] Installing Python dependencies...
cd /d "%~dp0"
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)

REM Install Node.js dependencies
echo [INFO] Installing Node.js dependencies...
cd /d "%~dp0..\..\mcp_servers"
npm install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Node.js dependencies
    pause
    exit /b 1
)

REM Go back to orchestration directory
cd /d "%~dp0"

REM Run the complete setup
echo [INFO] Starting complete setup...
python complete_setup.py

pause
