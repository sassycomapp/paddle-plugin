@echo off
echo ========================================
echo AG2 Orchestration Quick Test
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
    echo ❌ Quick test failed - please check configuration
    pause
    exit /b 1
)

echo.
echo ========================================
echo Running Core Unit Tests
echo ========================================
pytest unit/test_agents.py -v --tb=short

if errorlevel 1 (
    echo ❌ Unit tests failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Running Basic Integration Test
echo ========================================
pytest integration/test_orchestrator_integration.py -v --tb=short -k "test_basic_orchestrator_workflow"

if errorlevel 1 (
    echo ❌ Basic integration test failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ All Quick Tests Passed!
echo ========================================
echo The AG2 orchestration system is working correctly.
echo.
pause
