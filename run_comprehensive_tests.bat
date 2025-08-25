@echo off
echo ========================================
echo AG2 Orchestration System Testing Suite
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Running setup...
    call setup_python_env.bat
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Set environment variables
set PYTHONPATH=%CD%;%CD%\Test Bank\System Tests\AG2_Orchestration_Tests\src;%PYTHONPATH%

echo.
echo ========================================
echo Running Quick Health Check
echo ========================================
cd "Test Bank/System Tests/AG2_Orchestration_Tests"
python quick_test.py
if errorlevel 1 (
    echo Quick test failed - please check configuration
    pause
    exit /b 1
)

echo.
echo ========================================
echo Running Unit Tests
echo ========================================
pytest unit/ -v --tb=short
if errorlevel 1 (
    echo Unit tests failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Running Integration Tests
echo ========================================
pytest integration/ -v --tb=short
if errorlevel 1 (
    echo Integration tests failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Running End-to-End Tests
echo ========================================
pytest e2e/ -v --tb=short
if errorlevel 1 (
    echo End-to-end tests failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Running Performance Tests
echo ========================================
pytest --benchmark-only -v
if errorlevel 1 (
    echo Performance tests failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Running Security Tests
echo ========================================
bandit -r src/ -f json -o reports/security_report.json
safety check --json --output reports/safety_report.json

echo.
echo ========================================
echo Generating Test Report
echo ========================================
pytest --html=reports/test_report.html --self-contained-html
if errorlevel 1 (
    echo Test report generation failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo All Tests Completed Successfully!
echo ========================================
echo Reports available in: Test Bank/System Tests/AG2_Orchestration_Tests/reports/
echo.
pause
