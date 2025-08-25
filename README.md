# VSC IDE

A unified agentic IDE setup with Simba knowledge management and MCP integration, designed for seamless development with Anvil.works.

## Overview

This repository contains the complete vsc_ide (Visual Studio Code Integrated Development Environment) setup that supports both Python 3.7x (for Anvil compatibility) and Python 3.10+ (for advanced features). The project follows a linear workflow that integrates with Anvil.works for application development.

## Key Features

- **Dual Python Support**: Python 3.7x for Anvil compatibility and 3.10+ for advanced features
- **MCP Integration**: Model Context Protocol servers for various integrations
- **Simba Knowledge Management**: Advanced RAG and memory management capabilities
- **AG2 Orchestrator**: AutoGen-powered AI orchestration
- **VS Code Integration**: Complete IDE configuration with settings, keybindings, and extensions
- **Linear Workflow**: Seamless integration with Anvil.works for application development

## Quick Start

### Prerequisites

- Python 3.7+ (3.10+ recommended for advanced features)
- Node.js 18+
- Git
- VS Code (latest version)

### Installation

#### Prerequisites

- Python 3.8+ (required for environment utility)
- Node.js 18+
- Git
- VS Code (latest version)
- Tesseract OCR (for OCR functionality)

#### Quick Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/vsc_ide.git
   cd vsc_ide
   ```

2. **Run automated setup script**
   ```bash
   python setup_developer_environment.py
   ```

   This script will:
   - Create and configure virtual environment
   - Install all dependencies
   - Set up VSCode configuration
   - Configure environment utility
   - Run environment validation tests

3. **Manual setup (if automated setup fails)**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/macOS
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -r "Test Bank/System Tests/AG2_Orchestration_Tests/requirements.txt"
   pip install -r src/orchestration/requirements.txt
   
   # Set up environment utility
   python utils/environment.py
   
   # Configure VSCode
   code .
   # Select Python interpreter: venv/Scripts/python.exe (Windows) or venv/bin/python (Linux/macOS)
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Install Tesseract OCR (if needed)**
   - **Windows**: Download from [UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
   - **macOS**: `brew install tesseract`

#### Environment Validation

After setup, validate your environment:

```bash
# Run environment tests
python utils/environment.py

# Run specific script tests
python simple_tesseract_test.py
python tesseract_test.py
python health_check.py
```

#### Environment Utility

The project includes a comprehensive environment utility (`utils/environment.py`) that:

- **Detects environment type** (virtual, conda, global)
- **Validates dependencies** and Tesseract OCR installation
- **Configures paths** automatically
- **Provides fallback mechanisms** for different environments
- **Generates environment reports** for troubleshooting

**Usage**:
```python
from utils.environment import setup_environment, get_tesseract_path

# Setup environment
result = setup_environment()
print(f"Environment: {result['environment_info']['environment_type']}")

# Get Tesseract path
tesseract_path = get_tesseract_path()
if tesseract_path:
    print(f"Tesseract: {tesseract_path}")
```

### Development

#### Start Development Servers

```bash
# AG2 Orchestrator
npm run start:ag2

# MCP Servers
npm run start:memory
npm run start:rag
npm run start:brave
```

#### Development Workflow

1. **Development in VS Code**: Make changes to the codebase
2. **Version Control**: Commit and push changes to GitHub
3. **Anvil Integration**: Changes automatically sync to Anvil project

## Project Structure

```
vsc_ide/
├── src/                    # Core source code
├── simba/                  # Simba knowledge management
├── mcp_servers/            # MCP server implementations
├── vscode-profile/         # VS Code configuration
│   ├── settings.json       # VS Code settings
│   ├── keybindings.json    # VS Code keybindings
│   └── extensions.txt      # Recommended extensions
├── .github/                # GitHub workflows
├── .gitignore              # Git ignore rules
├── .gitattributes          # Git attributes
├── .gitconfig             # Git configuration
├── pyproject.toml         # Python project configuration
├── setup.py               # Setup script
├── restore-guide.md       # Environment restore guide
└── README.md              # This file
```

## Configuration

### Python Version Support

The project supports multiple Python versions:
- **Python 3.7-3.9**: For Anvil.works compatibility
- **Python 3.10-3.13**: For advanced features and development

### VS Code Configuration

The `vscode-profile/` directory contains:
- **Settings**: Editor configuration and preferences
- **Keybindings**: Custom keyboard shortcuts
- **Extensions**: List of recommended VS Code extensions

### Environment Variables

Key environment variables:
- `AG2_API_KEY`: AutoGen API key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `MCP_*_SERVER_URL`: MCP server URLs
- `BRAVE_API_KEY`: Brave Search API key

## Integration with Anvil.works

### Linear Workflow

1. **Development**: Code in VS Code using Python 3.7x compatibility
2. **Version Control**: Commit changes to GitHub
3. **Automatic Sync**: GitHub automatically syncs to Anvil project
4. **Verification**: Test changes in Anvil environment

### File Management

- **Commit**: Source code, configuration, and documentation
- **Ignore**: Local application projects (see `.gitignore`)
- **New Files**: Create in Anvil first for application projects

## Development Guidelines

### Code Quality

- Follow PEP 8 style guidelines
- Use Black for code formatting
- Use isort for import sorting
- Run flake8 for linting
- Use mypy for type checking

### Git Workflow

- Use feature branches for development
- Write descriptive commit messages
- Follow the conventional commit format
- Run pre-commit hooks for quality checks

### Testing

- Run unit tests with pytest
- Run integration tests with test databases
- Use performance benchmarks for critical paths

## Troubleshooting

### Common Issues

1. **Python Version Conflicts**
   - Use Python 3.7x for application code
   - Use Python 3.10+ for vsc_ide tools

2. **Sync Issues**
   - Verify files are not in `.gitignore`
   - Check file permissions
   - Follow new file creation protocol

3. **Extension Installation**
   - Check internet connection
   - Verify VS Code version
   - Install extensions manually if needed

### Getting Help

- Check the [restore guide](restore-guide.md) for detailed setup instructions
- Review project documentation in `Docs/`
- Report issues on GitHub issues

## Maintenance

### Regular Tasks

- Update dependencies weekly
- Review and update VS Code settings monthly
- Clean up unused extensions quarterly
- Update documentation as needed

### Backup Strategy

- GitHub repository serves as primary backup
- Regular commits ensure version history
- Document restore procedures for team members

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation in `Docs/`
- Review the restore guide for setup instructions

---

**Note**: This repository is part of a larger development ecosystem that includes Anvil.works integration, Simba knowledge management, and AG2 orchestration capabilities.