# Environment Troubleshooting Guide

This guide helps you resolve common environment-related issues when working with Python scripts in this project.

## Table of Contents
- [Common Issues](#common-issues)
- [Virtual Environment Problems](#virtual-environment-problems)
- [Dependency Issues](#dependency-issues)
- [Tesseract OCR Problems](#tesseract-ocr-problems)
- [VSCode Configuration Issues](#vscode-configuration-issues)
- [Cross-Platform Compatibility](#cross-platform-compatibility)
- [Debugging Steps](#debugging-steps)
- [Advanced Troubleshooting](#advanced-troubleshooting)

## Common Issues

### 1. Environment Utility Not Found
**Problem**: `ImportError: No module named 'utils.environment'`

**Solutions**:
```bash
# Check if utils directory exists
ls -la utils/

# If utils directory exists, check if environment.py exists
ls -la utils/environment.py

# If file exists, check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Try running from project root
cd /path/to/project
python utils/environment.py
```

### 2. Virtual Environment Not Activated
**Problem**: Scripts running in global Python instead of virtual environment

**Solutions**:
```bash
# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (Linux/macOS)
source venv/bin/activate

# Check if virtual environment is active
echo $VIRTUAL_ENV  # Should show path to venv

# Deactivate when done
deactivate
```

### 3. Python Path Issues
**Problem**: Module not found errors

**Solutions**:
```bash
# Check Python interpreter
which python  # Linux/macOS
where python  # Windows

# Check Python version
python --version

# Check installed packages
pip list

# Check package locations
python -c "import sys; print('\n'.join(sys.path))"
```

## Virtual Environment Problems

### 1. Creating Virtual Environment
**Problem**: `Error: [Errno 2] No such file or directory: 'python'`

**Solutions**:
```bash
# Check if Python is in PATH
python --version

# If not, add Python to PATH or use full path
python -m venv venv

# Or specify Python path
C:\Python39\python.exe -m venv venv
```

### 2. Virtual Environment Activation
**Problem**: `venv\Scripts\activate is not recognized as an internal or external command`

**Solutions**:
```bash
# Run activation script directly
venv\Scripts\activate.bat

# Or use command line
cmd /c "venv\Scripts\activate && python your_script.py"

# Check if Scripts directory exists
ls -la venv/Scripts/
```

### 3. Virtual Environment Corruption
**Problem**: Virtual environment exists but packages not working

**Solutions**:
```bash
# Delete and recreate virtual environment
rm -rf venv  # Linux/macOS
rmdir /s /q venv  # Windows

# Create new virtual environment
python -m venv venv

# Activate and reinstall dependencies
venv\Scripts\activate
pip install -r requirements.txt
```

## Dependency Issues

### 1. Missing Dependencies
**Problem**: `ImportError: No module named 'pytesseract'`

**Solutions**:
```bash
# Check if package is installed
pip show pytesseract

# Install missing package
pip install pytesseract

# Install from requirements file
pip install -r requirements.txt

# Upgrade all packages
pip install --upgrade -r requirements.txt
```

### 2. Version Conflicts
**Problem**: Package version conflicts causing import errors

**Solutions**:
```bash
# Check installed versions
pip show package_name

# Uninstall conflicting packages
pip uninstall package_name

# Install specific version
pip install package_name==1.2.3

# Use virtual environment to isolate dependencies
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Dependency Installation Fails
**Problem**: `ERROR: Could not build wheels for package_name`

**Solutions**:
```bash
# Install build dependencies
pip install --upgrade pip setuptools wheel

# Try installing with --no-cache-dir
pip install --no-cache-dir package_name

# Use conda if available
conda install package_name

# Install from source
pip install git+https://github.com/user/repo.git
```

## Tesseract OCR Problems

### 1. Tesseract Not Found
**Problem**: `pytesseract.pytesseract.TesseractNotFoundError: tesseract is not installed`

**Solutions**:
```bash
# Check if Tesseract is installed
tesseract --version

# Install Tesseract OCR (Windows)
# Download from: https://github.com/UB-Mannheim/tesseract/wiki

# Install Tesseract OCR (Ubuntu/Debian)
sudo apt-get install tesseract-ocr

# Install Tesseract OCR (macOS)
brew install tesseract

# Verify installation
tesseract --list-langs
```

### 2. Tesseract Path Configuration
**Problem**: Tesseract installed but not found by Python

**Solutions**:
```python
# Check detected Tesseract path
from utils.environment import get_tesseract_path
print(get_tesseract_path())

# Manually set Tesseract path
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### 3. Language Data Missing
**Problem**: `TesseractNotFoundError: tesseract is not installed or it's not in your PATH`

**Solutions**:
```bash
# Install English language data (Windows)
# During Tesseract installation, select "English" language pack

# Install language data (Ubuntu/Debian)
sudo apt-get install tesseract-ocr-eng

# Install language data (macOS)
brew install tesseract-lang

# Verify language data
tesseract --list-langs
```

## VSCode Configuration Issues

### 1. Wrong Python Interpreter
**Problem**: VSCode using global Python instead of virtual environment

**Solutions**:
1. Open Command Palette (Ctrl+Shift+P)
2. Select "Python: Select Interpreter"
3. Choose the virtual environment interpreter:
   - Windows: `.\venv\Scripts\python.exe`
   - Linux/macOS: `./venv/bin/python`

### 2. Terminal Not Activating Virtual Environment
**Problem**: Terminal not automatically activating virtual environment

**Solutions**:
```json
// Add to .vscode/settings.json
{
    "terminal.integrated.shell.windows": "C:\\Windows\\System32\\cmd.exe",
    "terminal.integrated.shellArgs.windows": ["/K", "venv\\Scripts\\activate.bat"],
    "python.terminal.activateEnvironment": true
}
```

### 3. Linting and Formatting Issues
**Problem**: Pylance, Black, or other tools not working

**Solutions**:
```json
// Add to .vscode/settings.json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackPath": "venv/Scripts/black.exe"
}
```

## Cross-Platform Compatibility

### 1. Windows Path Issues
**Problem**: Path separators causing issues on different platforms

**Solutions**:
```python
# Use pathlib for cross-platform path handling
from pathlib import Path

# Good
tesseract_path = Path("C:/Program Files/Tesseract-OCR/tesseract.exe")
user_site = Path.home() / "AppData" / "Roaming" / "Python" / "Python313" / "Lib" / "site-packages"

# Bad
tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
user_site = os.path.expanduser('~\\AppData\\Roaming\\Python\\Python313\\Lib\\site-packages')
```

### 2. Shell Command Differences
**Problem**: Shell commands working on one platform but not another

**Solutions**:
```python
# Use subprocess with cross-platform compatibility
import subprocess
import platform

def run_command(command):
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command, capture_output=True, text=True)
        
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)
```

## Debugging Steps

### 1. Environment Information Gathering
```python
# Get detailed environment information
from utils.environment import setup_environment

result = setup_environment()
print("Environment Info:")
print(f"Type: {result['environment_info']['environment_type']}")
print(f"Virtual: {result['environment_info']['is_virtual']}")
print(f"Python: {result['environment_info']['python_version']}")
print(f"Tesseract: {result['environment_info']['has_tesseract']}")
print(f"Missing deps: {result['environment_info']['missing_dependencies']}")

# Save environment report
env_file = 'environment_debug.json'
with open(env_file, 'w') as f:
    import json
    json.dump(result, f, indent=2, default=str)
```

### 2. Dependency Debugging
```python
# Check specific package imports
packages_to_check = ['pytesseract', 'PIL', 'numpy', 'pytest']

for package in packages_to_check:
    try:
        module = __import__(package)
        print(f"✅ {package}: {module.__file__ if hasattr(module, '__file__') else 'built-in'}")
    except ImportError as e:
        print(f"❌ {package}: {e}")
```

### 3. Path Debugging
```python
# Debug Python path
import sys
print("Python Path:")
for path in sys.path:
    print(f"  {path}")

# Check environment variables
import os
print("\nEnvironment Variables:")
for key, value in os.environ.items():
    if 'PYTHON' in key or 'PATH' in key:
        print(f"  {key}: {value}")
```

## Advanced Troubleshooting

### 1. Virtual Environment Diagnostics
```python
# Comprehensive virtual environment check
import sys
import os

def diagnose_venv():
    print("Virtual Environment Diagnosis:")
    print(f"Running in venv: {hasattr(sys, 'real_prefix')}")
    print(f"Venv path: {os.environ.get('VIRTUAL_ENV', 'Not set')}")
    print(f"Base prefix: {getattr(sys, 'base_prefix', 'Not set')}")
    print(f"Real prefix: {getattr(sys, 'real_prefix', 'Not set')}")
    
    # Check site-packages
    import site
    print(f"Site packages: {site.getsitepackages()}")

diagnose_venv()
```

### 2. Package Installation Debugging
```python
# Debug package installation
import subprocess
import sys

def debug_package_installation(package_name):
    print(f"Debugging installation of {package_name}...")
    
    # Check if package is already installed
    try:
        module = __import__(package_name)
        print(f"✅ Package already installed: {module.__file__}")
        return True
    except ImportError:
        print(f"❌ Package not found: {package_name}")
    
    # Try installation
    print("Attempting installation...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', package_name
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Installation successful")
            return True
        else:
            print(f"❌ Installation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False
```

### 3. Environment Configuration Validation
```python
# Validate environment configuration
import json
from pathlib import Path

def validate_environment_config():
    config_file = Path('environment_config.json')
    
    if not config_file.exists():
        print("❌ Environment config file not found")
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        print("✅ Environment config loaded successfully")
        print(f"Virtual env name: {config.get('virtual_env_name', 'Not set')}")
        print(f"Tesseract paths: {len(config.get('tesseract_paths', []))} configured")
        print(f"Required packages: {config.get('required_packages', [])}")
        
        return True
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False

validate_environment_config()
```

## Getting Help

If you continue to experience issues:

1. **Check the logs**: Look for error messages in the console or log files
2. **Run diagnostics**: Use the environment utility to gather diagnostic information
3. **Search existing issues**: Check GitHub issues for similar problems
4. **Create a new issue**: Provide:
   - Operating system and version
   - Python version
   - Error messages and stack traces
   - Steps to reproduce the issue
   - Environment diagnostic information

## Quick Reference

### Common Commands
```bash
# Environment setup
python setup_developer_environment.py

# Environment testing
python utils/environment.py

# Virtual environment management
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# Dependency management
pip install -r requirements.txt
pip freeze > requirements.txt

# Tesseract OCR
tesseract --version
tesseract --list-langs
```

### Configuration Files
- `environment_config.json`: Environment-specific settings
- `.vscode/settings.json`: VSCode configuration
- `requirements.txt`: Python dependencies
- `setup_developer_environment.py`: Developer setup script