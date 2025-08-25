@echo off
echo 🧠 Installing Agent Memory MCP Server...

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js first.
    pause
    exit /b 1
)

REM Install dependencies
echo 📦 Installing dependencies...
npm install

REM Create environment file
echo ⚙️  Creating environment configuration...
if not exist .env (
    copy .env.example .env
    echo ✅ Created .env file - please update with your PostgreSQL credentials
) else (
    echo ✅ .env file already exists
)

REM Create database tables
echo 🗄️  Setting up database tables...
if exist create_memory_tables.sql (
    echo Creating database tables...
    set PGPASSWORD=2001
    "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -d postgres -f create_memory_tables.sql
    if errorlevel 1 (
        echo ❌ Failed to create database tables
        echo Please run manually: psql -U postgres -d postgres -f create_memory_tables.sql
    ) else (
        echo ✅ Database tables created successfully
    )
) else (
    echo ❌ create_memory_tables.sql not found
)

REM Test the installation
echo 🧪 Testing the installation...
node test-proper.js

echo.
echo 🎉 Agent Memory MCP Server installation complete!
echo.
echo Next steps:
echo 1. Update .env with your PostgreSQL credentials if needed
echo 2. Add the server to your MCP configuration
echo 3. Start using the memory tools!
pause
