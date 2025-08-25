# Dependency Consolidation Plan

## Current State Analysis

### Python Dependencies (Duplicated)
1. **src/orchestration/requirements.txt** - AG2 orchestrator deps
2. **simba/pyproject.toml** - Full Simba knowledge system
3. **mcp_servers/mcp-memory-service/pyproject.toml** - Memory service

### Node.js Dependencies (Duplicated)
1. **mcp_servers/package.json** - AG2 MCP servers
2. **package.json** (root) - Missing but implied
3. **Multiple node_modules directories**

## Consolidation Strategy

### Phase 1: Create Unified Root Configuration
- Single `pyproject.toml` at root for all Python dependencies
- Single `package.json` at root for all Node.js dependencies
- Remove duplicate dependency specifications

### Phase 2: Environment Consolidation
- Single `.venv` for Python (remove `venv/`, `simba/.venv`)
- Single `node_modules` at root
- Shared virtual environments across components

### Phase 3: Dependency Deduplication
- Identify and remove overlapping packages
- Create dependency groups for optional features
- Establish clear separation between core and optional deps

## Implementation Steps

### 1. Create Unified Root Configuration
- [ ] Create root `pyproject.toml`
- [ ] Create root `package.json`
- [ ] Create dependency mapping document

### 2. Consolidate Python Dependencies
- [ ] Merge AG2 orchestrator requirements
- [ ] Merge Simba dependencies
- [ ] Merge MCP memory service dependencies
- [ ] Create feature-based dependency groups

### 3. Consolidate Node.js Dependencies
- [ ] Merge all MCP server dependencies
- [ ] Create workspace configuration
- [ ] Establish shared dependency versions

### 4. Cleanup and Migration
- [ ] Remove duplicate virtual environments
- [ ] Update setup scripts
- [ ] Update documentation
- [ ] Test consolidated setup

## Dependency Mapping

### Core Python Dependencies (All Systems)
```
python = ">=3.10,<3.14"
pyyaml = ">=6.0"
python-dotenv = ">=1.0.0"
httpx = ">=0.24.0"
aiohttp = ">=3.8.0"
```

### AG2 Specific
```
autogen-core = ">=0.2.0"
autogen-agentchat = ">=0.2.0"
asyncio-mqtt = ">=0.11.0"
websockets = ">=11.0"
```

### Simba Specific
```
langchain = "*"
faiss-cpu = "*"
uvicorn = ">=0.33.0"
fastapi = ">=0.115.6"
sentence-transformers = ">=3.2.0"
torch = ">=2.4.0"
```

### MCP Memory Service
```
PGvector = ">=0.5.23"
sentence-transformers = ">=2.2.2"
fastapi = ">=0.115.0"
uvicorn = ">=0.30.0"
```

### Database Dependencies
```
psycopg2-binary = ">=2.9.10"
redis = ">=5.2.1"
pgvector = ">=0.4.1"
supabase = ">=2.6.0"
```

### Node.js Core
```
"@modelcontextprotocol/sdk": "^0.5.0"
"PGvector": "^1.8.1"
"axios": "^1.6.0"
"dotenv": "^16.3.1"
```

## Next Steps
1. Execute Phase 1: Create unified configurations
2. Test consolidated setup in isolated environment
3. Gradually migrate existing setups
4. Update all documentation and scripts
