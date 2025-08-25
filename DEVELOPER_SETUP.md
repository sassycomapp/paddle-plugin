# Developer Setup Guide

This guide provides comprehensive instructions for setting up your development environment for the Paddle Plugin project.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Automated Setup](#automated-setup)
- [Manual Setup](#manual-setup)
- [Environment Configuration](#environment-configuration)
- [VSCode Integration](#vscode-integration)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Prerequisites

### System Requirements
- **Operating System**: Windows 10/11, Ubuntu 20.04+, or macOS 10.15+
- **Python**: 3.8+ (required for environment utility)
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: Minimum 2GB free space

### Required Software
- **Python 3.8+**: Download from [python.org](https://python.org)
- **Git**: Download from [git-scm.com](https://git-scm.com)
- **VS Code**: Download from [code.visualstudio.com](https://code.visualstudio.com)
- **Tesseract OCR**: 
  - Windows: Download from [UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`

### Optional Tools
- **Node.js 18+**: For MCP server development
- **Docker**: For containerized development
- **PostgreSQL**: For database development
- **Redis**: For caching and session management

## Automated Setup

### Quick Start
The recommended way to set up your development environment is using the automated setup script:

```bash
# Clone the repository
git clone https://github.com/your-username/paddle-plugin.git
cd paddle-plugin

# Run automated setup
python setup_developer_environment.py
```

### What the Automated Script Does
The `setup_developer_environment.py` script performs the following tasks:

1. **Prerequisites Check**
   - Verifies Python and pip availability
   - Checks Git installation
   - Validates system requirements

2. **Virtual Environment Setup**
   - Creates a virtual environment named `venv`
   - Activates the virtual environment
   - Upgrades pip to the latest version

3. **Dependency Installation**
   - Installs core dependencies from `requirements.txt`
   - Installs test dependencies from `Test Bank/System Tests/AG2_Orchestration_Tests/requirements.txt`
   - Installs orchestration dependencies from `src/orchestration/requirements.txt`

4. **Environment Configuration**
   - Creates `environment_config.json` with environment-specific settings
   - Configures Tesseract OCR paths
   - Sets up fallback mechanisms

5. **VSCode Integration**
   - Configures VSCode settings for the virtual environment
   - Sets up Python interpreter selection
   - Configures terminal activation

6. **Validation and Testing**
   - Runs environment validation tests
   - Tests Tesseract OCR functionality
   - Generates setup report

### Setup Report
After completion, the script generates a `setup_report.json` file containing:
- Setup timestamp and environment details
- Prerequisites check results
- Installation status for each component
- Environment validation results
- Next steps and recommendations

## Manual Setup

### Step 1: Clone Repository
```bash
git clone https://github.com/your-username/paddle-plugin.git
cd paddle-plugin
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install core dependencies
pip install -r requirements.txt

# Install test dependencies
pip install -r "Test Bank/System Tests/AG2_Orchestration_Tests/requirements.txt"

# Install orchestration dependencies
pip install -r src/orchestration/requirements.txt
```

### Step 4: Install Tesseract OCR
#### Windows
1. Download Tesseract installer from [UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the installer with administrator privileges
3. During installation, select "English" language pack
4. Verify installation: `tesseract --version`

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng
tesseract --version
```

#### macOS
```bash
brew install tesseract
brew install tesseract-lang
tesseract --version
```

### Step 5: Configure Environment
```bash
# Create environment configuration
python utils/environment.py

# Test environment setup
python simple_tesseract_test.py
python tesseract_test.py
```

## Environment Configuration

### Environment Configuration File
The project uses `environment_config.json` for environment-specific settings:

```json
{
  "virtual_env_name": "venv",
  "preferred_interpreter_path": "./venv/Scripts/python.exe",
  "fallback_to_global": true,
  "required_packages": ["pytesseract", "PIL", "numpy", "pytest"],
  "optional_packages": ["opencv-python", "scikit-image", "psutil"],
  "tesseract_paths": [
    "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
    "C:\\Tesseract-OCR\\tesseract.exe",
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract"
  ],
  "user_site_packages": true,
  "auto_activate_venv": true
}
```

### Environment Variables
Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
# Python Environment
PYTHONPATH=./src:./Test Bank/System Tests/AG2_Orchestration_Tests/src

# Tesseract OCR
TESSERACT_PATH=C:\\Program Files\\Tesseract-OCR\\tesseract.exe

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/environment.log

# Development
DEBUG=true
DEVELOPMENT_MODE=true
```

## VSCode Integration

### VSCode Settings
The project includes comprehensive VSCode configuration in `.vscode/settings.json`:

- **Python Interpreter**: Automatically set to virtual environment
- **Terminal Integration**: Automatic virtual environment activation
- **Linting and Formatting**: Pylance, Black, and isort configuration
- **Testing**: Pytest integration
- **Path Configuration**: Automatic import path setup

### VSCode Extensions
Recommended extensions for development:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-toolsai.jupyter",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.flake8",
    "ms-python.mypy-type-checker",
    "GitHub.copilot",
    "GitHub.copilot-chat"
  ]
}
```

### VSCode Workspace Setup
1. Open VSCode
2. Open the project folder: `File > Open Folder`
3. VSCode will automatically detect the `.vscode/settings.json`
4. Select Python interpreter: `Ctrl+Shift+P > Python: Select Interpreter`
5. Choose the virtual environment interpreter

## Development Workflow

### 1. Environment Activation
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# Verify activation
which python  # Linux/macOS
where python  # Windows
```

### 2. Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_environment.py

# Run with coverage
pytest --cov=utils --cov-report=html

# Run environment tests
python utils/environment.py
```

### 3. Code Quality
```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type checking
mypy utils/
```

### 4. Development Commands
```bash
# Start development server
python utils/environment.py

# Run specific scripts
python simple_tesseract_test.py
python tesseract_test.py
python health_check.py

# Generate documentation
python -m sphinx docs/ docs/_build/
```

### 5. Git Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push and create pull request
git push origin feature/your-feature-name
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Virtual Environment Issues
**Problem**: Virtual environment not activating
```bash
# Check virtual environment creation
python -m venv --help

# Recreate virtual environment
rm -rf venv  # Linux/macOS
rmdir /s /q venv  # Windows
python -m venv venv
```

#### 2. Dependency Issues
**Problem**: Package import errors
```bash
# Check installed packages
pip list

# Reinstall problematic package
pip uninstall package-name
pip install package-name

# Update all packages
pip install --upgrade -r requirements.txt
```

#### 3. Tesseract OCR Issues
**Problem**: Tesseract not found
```bash
# Verify Tesseract installation
tesseract --version

# Check Tesseract path
which tesseract  # Linux/macOS
where tesseract  # Windows

# Update environment configuration
python utils/environment.py
```

#### 4. VSCode Issues
**Problem**: Wrong Python interpreter
1. Open Command Palette: `Ctrl+Shift+P`
2. Select: `Python: Select Interpreter`
3. Choose: `./venv/Scripts/python.exe` (Windows) or `./venv/bin/python` (Linux/macOS)

### Debug Mode
Enable debug mode for troubleshooting:

```bash
# Set environment variable
export DEBUG=true  # Linux/macOS
set DEBUG=true     # Windows

# Run with debug output
python utils/environment.py --debug
```

### Environment Diagnostics
Run environment diagnostics:

```bash
# Generate environment report
python utils/environment.py --report

# Check environment health
python health_check.py

# Validate Tesseract installation
python simple_tesseract_test.py
```

## Best Practices

### 1. Environment Management
- Always use virtual environments for development
- Commit `environment_config.json` to version control
- Regularly update dependencies
- Test scripts in both global and virtual environments

### 2. Code Quality
- Follow PEP 8 style guidelines
- Use Black for code formatting
- Write comprehensive tests
- Use type hints for better code documentation

### 3. Git Workflow
- Use descriptive commit messages
- Follow conventional commit format
- Create feature branches for new development
- Review code before merging

### 4. Documentation
- Update documentation when changing APIs
- Add comments for complex logic
- Keep README files current
- Document environment setup procedures

### 5. Security
- Never commit sensitive information
- Use environment variables for secrets
- Regular security audits
- Keep dependencies updated

### 6. Performance
- Profile code for performance bottlenecks
- Use caching where appropriate
- Optimize image processing pipelines
- Monitor memory usage

## Additional Resources

### Documentation
- [Environment Troubleshooting Guide](ENVIRONMENT_TROUBLESHOOTING.md)
- [Tesseract OCR Documentation](Tesseract_OCR_Documentation.md)
- [API Documentation](Docs/API/)
- [Development Guidelines](Docs/DEVELOPMENT.md)

### Community and Support
- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share knowledge
- Wiki: Community-contributed tips and tricks

### Related Tools
- [Python Virtual Environments](https://docs.python.org/3/library/venv.html)
- [VSCode Python Extension](https://code.visualstudio.com/docs/python/python-tutorial)
- [Tesseract OCR Documentation](https://tesseract-ocr.github.io/tessdoc/)
- [pytest Documentation](https://docs.pytest.org/)

---

## Quick Reference

### Essential Commands
```bash
# Environment setup
python setup_developer_environment.py

# Virtual environment
python -m venv venv
venv\Scripts\activate

# Testing
pytest
python utils/environment.py

# Code quality
black .
isort .
flake8 .
mypy utils/
```

### Configuration Files
- `environment_config.json`: Environment settings
- `.vscode/settings.json`: VSCode configuration
- `.env`: Environment variables
- `requirements.txt`: Python dependencies

### Key Scripts
- `setup_developer_environment.py`: Automated setup
- `utils/environment.py`: Environment management
- `simple_tesseract_test.py`: Tesseract OCR test
- `health_check.py`: System health check
content>
<line_count>348</line_count>
</write_to_file>