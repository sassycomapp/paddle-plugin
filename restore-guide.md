# VSC IDE Restore Guide

This guide explains how to restore the vsc_ide development environment from the GitHub repository.

## Prerequisites

### System Requirements
- **Python**: 3.7+ (for Anvil compatibility) or 3.10+ (for advanced features)
- **Node.js**: 18+
- **Git**: Latest version
- **VS Code**: Latest stable version

### Development Tools
- **Poetry**: Python dependency management
- **npm**: Node.js package manager
- **VS Code Extensions**: Listed in `vscode-profile/extensions.txt`

## Setup Process

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/vsc_ide.git
cd vsc_ide
```

### 2. Install System Dependencies

#### Python Environment
```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install Python dependencies
poetry install --without dev --without docs

# Install optional dependency groups
poetry install --with ag2,simba,mcp,database
```

#### Node.js Environment
```bash
# Install root dependencies
npm install

# Install workspace dependencies
npm install --workspaces
```

### 3. Configure VS Code

#### Import Profile Settings
1. Open VS Code
2. Go to **File → Preferences → Profiles → Import Profile**
3. Select the `vscode-profile/settings.json` file from the repository
4. Click **Create** to import the profile

#### Install Extensions
```bash
# Install recommended extensions
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.isort
code --install-extension ms-python.black-formatter
code --install-extension ms-python.flake8
code --install-extension ms-python.mypy
code --install-extension dbaeumer.vscode-eslint
code --install-extension esbenp.prettier-vscode
code --install-extension ms-vscode.vscode-git
code --install-extension github.vscode-pull-request-github
code --install-extension github.vscode-github-actions
code --install-extension ms-azuretools.vscode-docker
code --install-extension ms-vscode.vscode-remote-containers
code --install-extension ms-vscode.vscode-remote
```

### 4. Environment Configuration

#### Create Environment File
```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your configuration
nano .env  # or your preferred editor
```

#### Required Environment Variables
```env
# AG2 Orchestrator Configuration
AG2_API_KEY=your_ag2_api_key_here
AG2_BASE_URL=https://api.ag2.dev/v1
AG2_MODEL=gpt-4

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/vsc_ide
REDIS_URL=redis://localhost:6379

# MCP Configuration
MCP_MEMORY_SERVER_URL=http://localhost:8000
MCP_RAG_SERVER_URL=http://localhost:8001
MCP_BRAVE_SERVER_URL=http://localhost:8002

# Brave Search Configuration
BRAVE_API_KEY=your_brave_api_key_here

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/vsc_ide.log

# Development
DEBUG=true
ENVIRONMENT=development
```

### 5. Verify Setup

#### Python Environment Check
```bash
# Test Python imports
poetry run python -c "
import sys
print(f'Python version: {sys.version}')
try:
    import langchain
    print('✓ langchain imported successfully')
except ImportError as e:
    print(f'✗ langchain import failed: {e}')
    sys.exit(1)
print('All Python dependencies verified!')
"
```

#### Node.js Environment Check
```bash
# Test Node.js modules
node -e "
const modules = [
    '@modelcontextprotocol/sdk',
    'axios',
    'dotenv',
    'uuid',
    'fs-extra'
];

let allGood = true;
modules.forEach(mod => {
    try {
        require.resolve(mod);
        console.log(`✓ ${mod} available`);
    } catch (e) {
        console.log(`✗ ${mod} missing: ${e.message}`);
        allGood = false;
    }
});

if (allGood) {
    console.log('All Node.js dependencies verified!');
    process.exit(0);
} else {
    console.log('Some Node.js dependencies are missing!');
    process.exit(1);
}
"
```

### 6. Start Development Servers

#### AG2 Orchestrator
```bash
npm run start:ag2
```

#### MCP Servers
```bash
# Memory MCP Server
npm run start:memory

# RAG MCP Server
npm run start:rag

# Brave Search MCP Server
npm run start:brave
```

## Development Workflow

### Linear Workflow Process

1. **Development in VS Code**
   - Make changes to the codebase
   - Test locally using the development servers
   - Use Python 3.7x compatibility for Anvil integration

2. **Version Control**
   - Commit changes with descriptive messages
   - Push to GitHub repository
   - GitHub automatically syncs changes to Anvil project

3. **Anvil Integration**
   - Changes pushed to GitHub automatically sync to Anvil
   - Verify the changes work in the Anvil environment
   - Maintain Python 3.7x compatibility for seamless sync

### File Management

#### What to Commit
- Source code files
- Configuration files
- Documentation
- VS Code profile settings
- Extension lists

#### What to Ignore
- Local application development projects (see `.gitignore`)
- Temporary files
- Build artifacts
- Environment-specific files

### New File Creation Protocol

1. **Create in Anvil First** (for application projects)
   - Create new files in the Anvil web editor
   - Sync to GitHub
   - Then develop locally in VS Code

2. **Create in VS Code** (for vsc_ide project)
   - Create new files directly in VS Code
   - Commit and push to GitHub
   - Changes will be available for Anvil sync

## Troubleshooting

### Common Issues

#### Python Version Conflicts
- **Issue**: Mixed Python versions between local and Anvil
- **Solution**: Use Python 3.7x for application code, 3.10+ for vsc_ide tools

#### Sync Issues
- **Issue**: Files not syncing between GitHub and Anvil
- **Solution**: 
  1. Verify files are not in `.gitignore`
  2. Check file permissions
  3. Ensure proper commit messages
  4. Follow the new file creation protocol

#### Extension Installation
- **Issue**: VS Code extensions not installing
- **Solution**: 
  1. Check internet connection
  2. Verify VS Code version
  3. Try installing extensions manually

### Getting Help

1. **Documentation**: Check project documentation in `Docs/`
2. **Issues**: Report problems on GitHub issues
3. **Community**: Join relevant development communities

## Maintenance

### Keeping the Environment Updated

#### Update Dependencies
```bash
# Python dependencies
poetry update

# Node.js dependencies
npm update
```

#### Update VS Code Profile
1. Make changes to settings in VS Code
2. Export updated profile: **File → Preferences → Profiles → Export Profile**
3. Replace the `vscode-profile/settings.json` file
4. Commit and push changes

#### Extension Updates
```bash
# Update extension list
code --list-extensions > vscode-profile/extensions.txt
```

### Regular Tasks

- [ ] Update dependencies weekly
- [ ] Review and update VS Code settings monthly
- [ ] Clean up unused extensions quarterly
- [ ] Update documentation as needed

## Backup Strategy

### Local Backup
1. Regular commits to GitHub
2. Periodic exports of VS Code profile
3. Backup of environment configuration

### Remote Backup
1. GitHub repository serves as primary backup
2. Consider additional backup strategies for critical data
3. Document restore procedures for team members

---

By following this guide, you can maintain a consistent development environment that seamlessly integrates with both VS Code and Anvil workflows.