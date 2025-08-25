@echo off
setlocal enabledelayedexpansion

echo 🚀 Setting up Podman environment for Testing and Validation System...

REM Check if Podman is installed
where podman >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Podman is not installed. Please install Podman first.
    pause
    exit /b 1
)

REM Check if podman-compose is available
where podman-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo 📦 Installing podman-compose...
    pip install podman-compose
)

REM Create Podman network if it doesn't exist
podman network ls | findstr /C:"testing-network" >nul
if %errorlevel% neq 0 (
    echo 🌐 Creating Podman network...
    podman network create testing-network
)

REM Build images
echo 🏗️  Building container images...
podman-compose build

REM Start services
echo 🚀 Starting services...
podman-compose up -d postgres

REM Wait for PostgreSQL to be ready
echo ⏳ Waiting for PostgreSQL to be ready...
timeout /t 10 /nobreak >nul

REM Initialize database
echo 🗄️  Initializing database...
podman-compose exec postgres psql -U test_user -d test_db -f /docker-entrypoint-initdb.d/init-test-db.sql

echo ✅ Podman environment setup complete!
echo.
echo Available commands:
echo   podman-compose up          - Start all services
echo   podman-compose down        - Stop all services
echo   podman-compose logs -f     - View logs
echo   podman-compose run test    - Run tests

pause
