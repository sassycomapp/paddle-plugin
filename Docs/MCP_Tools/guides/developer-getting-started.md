# Developer Getting Started Guide

## Overview

This guide provides comprehensive instructions for developers who want to start working with MCP (Model Context Protocol) servers within the KiloCode ecosystem. The development process follows the **Simple, Robust, Secure** approach and ensures proper integration with existing infrastructure.

## Prerequisites

### Development Environment
- **Operating System**: Linux, macOS, or Windows
- **Node.js**: 18.x LTS (minimum), 20.x LTS (recommended)
- **Python**: 3.8+ (minimum), 3.11+ (recommended)
- **npm**: 8.x+ (minimum), 9.x+ (recommended)
- **Git**: 2.x+ (minimum), 2.30+ (recommended)
- **VS Code**: Latest version with recommended extensions

### Development Tools
- **IDE**: VS Code with Python and Node.js extensions
- **Database**: PostgreSQL 12+ (for development)
- **Container**: Docker (optional, for containerized development)
- **Testing**: Jest, Pytest, and related testing frameworks
- **Linting**: ESLint, Pylint, and related linting tools

### Development Environment Setup
```bash
# Install Node.js and npm (if not already installed)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python and pip (if not already installed)
sudo apt-get install -y python3 python3-pip python3-venv

# Install development tools
sudo apt-get install -y git docker.io build-essential

# Verify installations
node --version
npm --version
python3 --version
pip3 --version
git --version
docker --version
```

## Development Environment Setup

### Step 1: Clone and Setup Development Repository

#### 1.1 Clone the Repository
```bash
# Clone the main repository
git clone https://github.com/kilocode/kilocode-mcp.git
cd kilocode-mcp

# Clone MCP server repositories
git clone https://github.com/kilocode/mcp-compliance-server.git
git clone https://github.com/kilocode/mcp-memory-service.git
git clone https://github.com/kilocode/easyocr-mcp.git
git clone https://github.com/kilocode/everything-search-mcp.git

# Set up development environment
mkdir -p dev-servers
cd dev-servers
ln -s ../mcp-compliance-server compliance-server
ln -s ../mcp-memory-service memory-service
ln -s ../easyocr-mcp easyocr-server
ln -s ../everything-search-mcp search-server
```

#### 1.2 Initialize Development Environment
```bash
# Create development configuration
cat << 'EOF' > dev-config.json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", ".", "/tmp"],
      "env": {
        "NODE_ENV": "development",
        "KILOCODE_ENV": "development",
        "KILOCODE_PROJECT_PATH": "$(pwd)"
      },
      "description": "Filesystem access for development files"
    },
    "postgres": {
      "command": "node",
      "args": ["$(pwd)/../packages/kilocode-mcp-installer/dist/index.js", "postgres"],
      "env": {
        "DATABASE_URL": "postgresql://dev_user:dev_password@localhost:5432/dev_db",
        "NODE_ENV": "development",
        "KILOCODE_ENV": "development"
      },
      "description": "PostgreSQL database connection for development"
    },
    "memory": {
      "command": "python",
      "args": ["$(pwd)/memory-service/memory_wrapper.py"],
      "env": {
        "MCP_MEMORY_VECTOR_DB_PATH": "$(pwd)/memory_db",
        "MCP_MEMORY_BACKUPS_PATH": "$(pwd)/memory_backups",
        "MCP_MEMORY_LOG_LEVEL": "DEBUG"
      },
      "alwaysAllow": [
        "store_memory",
        "retrieve_memory",
        "recall_memory",
        "search_by_tag",
        "delete_memory",
        "get_stats"
      ],
      "description": "Memory service for development"
    },
    "compliance": {
      "command": "node",
      "args": ["$(pwd)/compliance-server/src/index.js"],
      "env": {
        "COMPLIANCE_LOG_LEVEL": "DEBUG",
        "COMPLIANCE_REPORT_PATH": "$(pwd)/reports"
      },
      "description": "Compliance server for development"
    }
  }
}
EOF

# Create development environment file
cat << 'EOF' > .env
# Development Environment Configuration
KILOCODE_ENV=development
KILOCODE_PROJECT_PATH=$(pwd)
KILOCODE_PROJECT_NAME=KiloCode Development

# Database Configuration
DATABASE_URL=postgresql://dev_user:dev_password@localhost:5432/dev_db
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=dev_db
DATABASE_USER=dev_user
DATABASE_PASSWORD=dev_password

# Memory Service Configuration
MCP_MEMORY_VECTOR_DB_PATH=$(pwd)/memory_db
MCP_MEMORY_BACKUPS_PATH=$(pwd)/memory_backups
MCP_MEMORY_MAX_SIZE=100000
MCP_MEMORY_CLEANUP_INTERVAL=3600
MCP_MEMORY_LOG_LEVEL=DEBUG

# Logging Configuration
LOG_LEVEL=DEBUG
LOG_DIR=$(pwd)/logs
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=7
LOG_COMPRESS=false

# Development Configuration
DEBUG=true
VERBOSE=true
ENABLE_METRICS=false
METRICS_PORT=9090
EOF
```

### Step 2: Install Development Dependencies

#### 2.1 Install Node.js Dependencies
```bash
# Install main MCP installer dependencies
cd ../packages/kilocode-mcp-installer
npm install
npm run build

# Install compliance server dependencies
cd ../../mcp-compliance-server
npm install
npm run build

# Install other Node.js server dependencies
cd ../easyocr-mcp
npm install

cd ../everything-search-mcp
npm install
```

#### 2.2 Install Python Dependencies
```bash
# Create Python virtual environment
cd ../mcp-memory-service
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy

# Install memory service
python install.py
```

#### 2.3 Install Database Dependencies
```bash
# Install PostgreSQL for development
sudo apt-get install -y postgresql postgresql-contrib

# Create development database
sudo -u postgres createdb dev_db
sudo -u postgres createuser dev_user
sudo -u postgres psql -c "ALTER USER dev_user PASSWORD 'dev_password';"

# Set up database schema
psql -U dev_user -d dev_db -f ../mcp-compliance-server/database/schema.sql
```

### Step 3: Configure Development Tools

#### 3.1 VS Code Configuration
```bash
# Create VS Code workspace configuration
cat << 'EOF' > .vscode/settings.json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": [
    "tests"
  ],
  "javascript.updateImportsOnFileMove.enabled": "always",
  "typescript.updateImportsOnFileMove.enabled": "always",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "eslint.validate": [
    "javascript",
    "typescript"
  ],
  "files.associations": {
    "*.json": "jsonc"
  }
}
EOF

# Create VS Code launch configuration
cat << 'EOF' > .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Launch Compliance Server",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/mcp-compliance-server/src/index.js",
      "args": [],
      "cwd": "${workspaceFolder}/mcp-compliance-server",
      "console": "integratedTerminal",
      "internalConsoleOptions": "neverOpen"
    },
    {
      "name": "Launch Memory Service",
      "type": "python",
      "request": "launch",
      "module": "memory_wrapper",
      "args": [],
      "cwd": "${workspaceFolder}/mcp-memory-service",
      "console": "integratedTerminal",
      "internalConsoleOptions": "neverOpen"
    },
    {
      "name": "Launch Tests",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/mcp-compliance-server/scripts/test-executor.js",
      "args": ["--unit", "--integration", "--compliance"],
      "cwd": "${workspaceFolder}/mcp-compliance-server",
      "console": "integratedTerminal",
      "internalConsoleOptions": "neverOpen"
    }
  ]
}
EOF

# Create VS Code tasks configuration
cat << 'EOF' > .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Install Dependencies",
      "type": "shell",
      "command": "npm install",
      "group": "build",
      "options": {
        "cwd": "${workspaceFolder}/packages/kilocode-mcp-installer"
      }
    },
    {
      "label": "Build MCP Installer",
      "type": "shell",
      "command": "npm run build",
      "group": "build",
      "options": {
        "cwd": "${workspaceFolder}/packages/kilocode-mcp-installer"
      }
    },
    {
      "label": "Start Compliance Server",
      "type": "shell",
      "command": "node src/index.js",
      "group": "build",
      "options": {
        "cwd": "${workspaceFolder}/mcp-compliance-server"
      }
    },
    {
      "label": "Start Memory Service",
      "type": "shell",
      "command": "python memory_wrapper.py",
      "group": "build",
      "options": {
        "cwd": "${workspaceFolder}/mcp-memory-service"
      }
    },
    {
      "label": "Run Tests",
      "type": "shell",
      "command": "node scripts/test-executor.js",
      "group": "test",
      "options": {
        "cwd": "${workspaceFolder}/mcp-compliance-server"
      }
    },
    {
      "label": "Run Python Tests",
      "type": "shell",
      "command": "pytest",
      "group": "test",
      "options": {
        "cwd": "${workspaceFolder}/mcp-memory-service"
      }
    }
  ]
}
EOF
```

#### 3.2 Git Configuration
```bash
# Configure git for development
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
git config --global init.defaultBranch main

# Create .gitignore file
cat << 'EOF' > .gitignore
# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Python
venv/
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Database
*.db
*.sqlite
*.sqlite3

# Logs
logs/
*.log

# Runtime data
pids/
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/
.nyc_output

# Dependency directories
node_modules/
jspm_packages/

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# dotenv environment variables file
.env
.env.test

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
memory_db/
memory_backups/
reports/
logs/
temp/
tmp/
EOF
```

## Development Workflow

### Step 4: Development Workflow Setup

#### 4.1 Branching Strategy
```bash
# Create feature branch
git checkout -b feature/new-feature

# Create development branch
git checkout -b develop

# Create release branch
git checkout -b release/v1.0.0

# Create hotfix branch
git checkout -b hotfix/fix-bug
```

#### 4.2 Development Process
```bash
# 1. Pull latest changes
git pull origin main

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Make changes
# Edit files as needed

# 4. Test changes
npm test
npm run build

# 5. Commit changes
git add .
git commit -m "feat: add new feature"

# 6. Push changes
git push origin feature/your-feature-name

# 7. Create pull request
# Go to GitHub and create pull request
```

#### 4.3 Code Quality Tools
```bash
# Install code quality tools
npm install -g eslint prettier
pip install black flake8 mypy

# Configure ESLint
cat << 'EOF' > .eslintrc.json
{
  "env": {
    "node": true,
    "es2021": true,
    "jest": true
  },
  "extends": [
    "eslint:recommended",
    "@typescript-eslint/recommended"
  ],
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "ecmaVersion": 12,
    "sourceType": "module"
  },
  "plugins": [
    "@typescript-eslint"
  ],
  "rules": {
    "indent": ["error", 2],
    "linebreak-style": ["error", "unix"],
    "quotes": ["error", "single"],
    "semi": ["error", "always"],
    "no-unused-vars": "warn",
    "no-console": "warn"
  }
}
EOF

# Configure Prettier
cat << 'EOF' > .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2
}
EOF

# Configure Black for Python
cat << 'EOF' > pyproject.toml
[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
EOF

# Configure Flake8 for Python
cat << 'EOF' > .flake8
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist,venv
EOF
```

### Step 5: Testing Setup

#### 5.1 Unit Testing Configuration
```bash
# Configure Jest for Node.js testing
cat << 'EOF' > jest.config.js
module.exports = {
  testEnvironment: 'node',
  roots: ['<rootDir>/src', '<rootDir>/tests'],
  testMatch: [
    '**/__tests__/**/*.+(ts|tsx|js)',
    '**/*.(test|spec).+(ts|tsx|js)'
  ],
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest'
  },
  collectCoverageFrom: [
    'src/**/*.{js,ts}',
    '!src/**/*.d.ts',
    '!src/index.ts'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html']
};
EOF

# Configure Pytest for Python testing
cat << 'EOF' > pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    compliance: Compliance tests
    performance: Performance tests
EOF
```

#### 5.2 Integration Testing Configuration
```bash
# Create integration test configuration
cat << 'EOF' > tests/integration/config.js
module.exports = {
  testTimeout: 30000,
  setupFilesAfterEnv: ['<rootDir>/tests/integration/setup.js'],
  testMatch: ['**/integration/**/*.test.js'],
  globalSetup: '<rootDir>/tests/integration/globalSetup.js',
  globalTeardown: '<rootDir>/tests/integration/globalTeardown.js'
};
EOF

# Create integration test setup
cat << 'EOF' > tests/integration/setup.js
module.exports = async () => {
  // Set up test environment
  process.env.NODE_ENV = 'test';
  process.env.KILOCODE_ENV = 'test';
  process.env.KILOCODE_PROJECT_PATH = '/tmp/test-project';
  
  // Create test database
  const { Pool } = require('pg');
  const pool = new Pool({
    user: 'test_user',
    host: 'localhost',
    database: 'test_db',
    password: 'test_password',
    port: 5432,
  });
  
  await pool.query('CREATE DATABASE IF NOT EXISTS test_db');
  await pool.end();
  
  // Start test servers
  // This would start the actual MCP servers for integration testing
};
EOF
```

## Development Best Practices

### Code Quality Best Practices
1. **Follow Coding Standards**: Use consistent coding style across all projects
2. **Write Tests**: Write comprehensive unit and integration tests
3. **Code Reviews**: Participate in code reviews and provide constructive feedback
4. **Documentation**: Document code changes and new features
5. **Version Control**: Use meaningful commit messages and follow branching strategy

### Security Best Practices
1. **Input Validation**: Validate all user inputs
2. **Error Handling**: Implement proper error handling
3. **Secrets Management**: Never hardcode secrets in code
4. **Dependency Management**: Regularly update dependencies
5. **Security Testing**: Perform security testing on code changes

### Performance Best Practices
1. **Code Optimization**: Optimize code for performance
2. **Database Optimization**: Optimize database queries
3. **Memory Management**: Manage memory efficiently
4. **Caching**: Implement caching where appropriate
5. **Monitoring**: Monitor application performance

## Troubleshooting Common Issues

### Common Development Issues

#### Issue 1: Node.js Dependencies Not Installing
**Symptom**: npm install fails or dependencies are missing
**Solution**: Clear npm cache and reinstall dependencies
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules
npm install

# If using yarn
yarn cache clean
rm -rf node_modules
yarn install
```

#### Issue 2: Python Virtual Environment Issues
**Symptom**: Python virtual environment not working or packages not installing
**Solution**: Recreate virtual environment and reinstall packages
```bash
# Remove existing virtual environment
rm -rf venv

# Create new virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install packages
pip install --upgrade pip
pip install -r requirements.txt
```

#### Issue 3: Database Connection Issues
**Symptom**: Unable to connect to PostgreSQL database
**Solution**: Check database configuration and permissions
```bash
# Check PostgreSQL service status
sudo systemctl status postgresql

# Check database connection
psql -U dev_user -d dev_db -c "SELECT version();"

# Check database permissions
psql -U dev_user -d dev_db -c "\du"
```

#### Issue 4: MCP Server Not Starting
**Symptom**: MCP server fails to start or throws errors
**Solution**: Check server logs and configuration
```bash
# Check server logs
tail -f logs/server.log

# Check configuration files
cat config.json

# Test server configuration
node scripts/validate-config.js
```

### Development Environment Debugging

#### Debug Mode Configuration
```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Start servers in debug mode
node --inspect src/index.js
python -m pdb memory_wrapper.py

# Use VS Code debugger
# Set breakpoints in VS Code and start debugging session
```

#### Development Environment Validation
```bash
# Validate development environment
npm run validate
npm run test
npm run build

# Validate Python environment
python -m pytest tests/
python -m flake8 src/
python -m black --check src/
```

## Support and Contact Information

### Technical Support
- **Email**: support@kilocode.com
- **Phone**: +1 (555) 123-4567
- **Hours**: 9 AM - 5 PM EST, Monday - Friday

### Documentation
- **Main Documentation**: [KiloCode MCP Documentation](https://docs.kilocode.com/mcp)
- **GitHub Issues**: [KiloCode GitHub](https://github.com/kilocode/kilocode/issues)
- **Community Forum**: [KiloCode Community](https://community.kilocode.com)

### Development Resources
- **API Reference**: [KiloCode API Documentation](https://docs.kilocode.com/api)
- **Code Examples**: [KiloCode Examples](https://github.com/kilocode/examples)
- **Best Practices**: [KiloCode Best Practices](https://docs.kilocode.com/best-practices)

---

*This developer getting started guide is part of the KiloCode MCP Setup and Configuration Architecture Plan and should be reviewed and updated regularly to reflect changes in development procedures and best practices.*