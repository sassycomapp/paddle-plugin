# Migration Guide: Unified Dependency Management

## Overview
This guide helps migrate from the fragmented dependency setup to the new unified configuration using Poetry and npm workspaces.

## What's Changed

### Before (Fragmented)
- Multiple `requirements.txt` files
- Multiple `pyproject.toml` files
- Separate `package.json` files
- Multiple virtual environments
- Inconsistent dependency versions

### After (Unified)
- Single root `pyproject.toml` with Poetry
- Single root `package.json` with npm workspaces
- One virtual environment for Python
- One `node_modules` directory
- Consistent dependency versions across all components

## Migration Steps

### 1. Backup Your Current Setup
```bash
# Create a backup of your current setup
cp -r . ../paddle-plugin-backup-$(date +%Y%m%d-%H%M%S)
```

### 2. Run the Unified Setup
```bash
# Use the new unified setup script
python setup.py
```

### 3. Update Your Environment Variables
The new setup creates a unified `.env` file. Update it with your API keys:
```bash
# Edit the .env file
nano .env
```

### 4. Update Your Scripts
Replace old commands with new unified commands:

| Old Command | New Command |
|-------------|-------------|
| `cd src/orchestration && pip install -r requirements.txt` | `poetry install` |
| `cd mcp_servers && npm install` | `npm install` |
| `cd simba && poetry install` | `poetry install` |
| `python -m src.orchestration.ag2_orchestrator` | `npm run start:ag2` |
| `node mcp_servers/agent-memory/index.js` | `npm run start:memory` |
| `node mcp_servers/rag-mcp-server.js` | `npm run start:rag` |
| `node mcp_servers/brave-search-mcp-server.js` | `npm run start:brave` |

### 5. Update Development Workflows

#### Running Tests
```bash
# Old way
cd src/orchestration && python -m pytest
cd mcp_servers && npm test

# New way
npm run test
```

#### Code Formatting
```bash
# Old way
cd simba && poetry run black .
cd mcp_servers && prettier --write .

# New way
npm run lint
```

### 6. Update IDE Configuration

#### VS Code Settings
Update your `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.analysis.extraPaths": ["./src", "./simba", "./mcp_servers"],
    "eslint.workingDirectories": ["./", "./mcp_servers", "./brave-search-integration"]
}
```

#### PyCharm/IntelliJ
1. Set the project interpreter to `./.venv/bin/python`
2. Mark directories as source roots:
   - `src/` → Sources Root
   - `simba/` → Sources Root
   - `mcp_servers/` → Sources Root

### 7. Clean Up Old Files

After verifying everything works, you can remove old configuration files:

```bash
# Remove old requirements files
rm src/orchestration/requirements.txt
rm mcp_servers/mcp-memory-service/requirements.txt

# Remove old package.json files (they're now part of workspaces)
rm mcp_servers/package.json

# Remove old virtual environments
rm -rf venv/ .venv/ simba/.venv/ mcp_servers/.venv/

# Remove old node_modules
rm -rf mcp_servers/node_modules/ brave-search-integration/node_modules/
```

## Troubleshooting

### Common Issues

#### 1. Poetry Not Found
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
```

#### 2. Node Version Issues
```bash
# Use Node Version Manager (nvm)
nvm use 18
nvm install 18
```

#### 3. Permission Issues
```bash
# Fix Poetry permissions
poetry config virtualenvs.in-project true

# Fix npm permissions
npm config set prefix ~/.npm-global
```

#### 4. Import Errors
```bash
# Reinstall dependencies
poetry install --with dev,ag2,simba,mcp,database
npm install --workspaces
```

### Verification Commands

```bash
# Verify Python setup
poetry run python -c "import autogen, PGvector, langchain; print('✓ All Python deps working')"

# Verify Node.js setup
node -e "console.log('✓ Node.js working'); require('@modelcontextprotocol/sdk'); console.log('✓ MCP SDK working')"

# Verify services start
npm run start:ag2 -- --help
npm run start:memory -- --help
npm run start:rag -- --help
npm run start:brave -- --help
```

## Rollback Plan

If you need to rollback:

```bash
# Restore from backup
rm -rf ./* ../paddle-plugin-backup-*/.git
cp -r ../paddle-plugin-backup-*/. .
```

## Support

For issues with the migration:
1. Check the troubleshooting section above
2. Run `python setup.py` again to verify setup
3. Check the logs in `logs/setup.log`
4. Create an issue with the error details

## Benefits of Unified Setup

1. **Single Source of Truth**: All dependencies in one place
2. **Consistent Versions**: No more version conflicts
3. **Simpler Setup**: One command to install everything
4. **Better IDE Support**: Single virtual environment
5. **Easier Maintenance**: Update dependencies in one place
6. **Faster Installs**: Shared dependencies and caching
7. **Better Documentation**: Clear dependency hierarchy
