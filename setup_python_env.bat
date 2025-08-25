@echo off
echo Setting up Python environment for AG2 Orchestration System...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing requirements...
pip install -r "Test Bank/System Tests/AG2_Orchestration_Tests/requirements.txt"

REM Install AG2 orchestration requirements
pip install -r src/orchestration/requirements.txt

echo Python environment setup complete!
echo.
echo To activate the environment in future sessions:
echo   venv\Scripts\activate.bat
echo.
pause
