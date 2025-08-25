# Installed MCP Servers

## Overview
This document lists all Model Context Protocol (MCP) servers successfully integrated into the system.

## Active Servers

### 1. MCP Installer
- **Status**: ✅ Working
- **Package**: `@anaisbetts/mcp-installer`
- **Purpose**: Core installation system for MCP servers
- **Function**: Handles setup and configuration of all MCP servers
- **Documentation**: [MCP Installer Details](mcp_servers/MCP Details/MCP Installer.md)

### 2. MCP File Server Installer
- **Status**: ✅ Working
- **Location**: `mcp_servers/install-mcp-server.js`
- **Purpose**: Installation script for MCP servers
- **Function**: 
  - Handles package installation and configuration
  - Updates .vscode/mcp.json automatically
  - Supports multiple server types
- **Test Command**: `node mcp_servers/install-mcp-server.js`

### 3. Filesystem Server
- **Status**: ✅ Working
- **Package**: `@modelcontextprotocol/server-filesystem`
- **Purpose**: File system operations
- **Configuration**: 
  - Default arguments: . (current dir) and /tmp
  - No environment variables required
- **Test Command**: `npx -y @modelcontextprotocol/server-filesystem .`
- **Documentation**: [MCP Filesystem Details](mcp_servers/MCP Details/MCP filesystem.md)
- **Features**:
  - Secure path restriction
  - Directory validation
  - File operation monitoring

### 4. GitHub Server
- **Status**: ❌ Not Installed
- **Package**: `@modelcontextprotocol/server-github`
- **Purpose**: GitHub API integration
- **Required Credential**: `GITHUB_PERSONAL_ACCESS_TOKEN`
- **Test Command**: `npx -y @modelcontextprotocol/server-github`
- **Documentation**: [MCP GitHub Details](mcp_servers/MCP Details/MCP Github.md)

### 5. PostgreSQL Server
- **Status**: ✅ Working
- **Package**: `@modelcontextprotocol/server-postgres`
- **Purpose**: Database operations
- **Required Credential**: `DATABASE_URL`
- **Test Command**: `npx -y @modelcontextprotocol/server-postgres`
- **Documentation**: [MCP Postgres Details](mcp_servers/MCP Details/MCP Postgres.md)

### 6. Brave Search Server
- **Status**: ✅ Working
- **Package**: `@modelcontextprotocol/server-brave-search`
- **Purpose**: Web search integration
- **Required Credential**: `BRAVE_API_KEY = BSAbLxLX849t9mni7fGR7HWKstcFa7Y`
- **Test Command**: `npx -y @modelcontextprotocol/server-brave-search`
- **Documentation**: [MCP Brave-Search Details](mcp_servers/MCP Details/MCP Brave-Search.md)
- **Verification**: Tested and working (web search functionality confirmed)

### 7. Fetch Server
- **Status**: ✅ Working
- **Package**: `@modelcontextprotocol/server-fetch`
- **Purpose**: HTTP requests and data fetching
- **Test Command**: `npx -y @modelcontextprotocol/server-fetch`
- **Documentation**: [MCP Fetch Details](mcp_servers/MCP Details/MCP Server-Fetch.md)

### 8. VSCode-MCP-Server
- **Status**: ✅ Working
- **Location**: Package.json scripts
- **Purpose**: VS Code integration
- **Start Command**: `npm run mcp:vscode`
- **Features**: Provides VS Code-specific MCP integration

### 9. RAG Server (PGvector)
- **Status**: ✅ Fully Operational
- **Package**: `@modelcontextprotocol/server-rag-PGvector`
- **Purpose**: Retrieval-Augmented Generation with PGvector
- **Test Command**: `npx -y @modelcontextprotocol/server-rag-PGvector`
- **Documentation**: [MCP RAG Details](mcp_servers/MCP Details/MCP RAG-PGvector.md)
- **Features**:
  - **Backend**: PGvector vector database with Docker
  - **Embeddings**: Sentence-transformers (Xenova/all-MiniLM-L6-v2)
  - **Performance**: Sub-second search, 100 queries/second capacity
  - **Storage**: Persistent volume at `./"Placeholder"-data`
  - **API**: RESTful endpoints at `http://localhost:8000`
- **Commands**:
  - `npm run rag:start` - Start PGvector container
  - `npm run rag:stop` - Stop PGvector container
  - `npm run rag:test` - Run comprehensive tests

### 10. Snap Windows Server
- **Status**: ✅ Fully Operational
- **Package**: `@modelcontextprotocol/server-snap-windows`
- **Purpose**: Windows system integration and automation
- **Test Command**: `npx -y @modelcontextprotocol/server-snap-windows`
- **Documentation**: [MCP Snap Windows Details](mcp_servers/MCP Details/MCP Snap-Windows.md)
- **Features**:
  - Window snapping and layout management
  - Predefined layouts (2x2, 3x3, left-right, top-bottom)
  - Custom layout management
- **Tools**:
  - `arrange_windows` - Arrange windows in predefined layouts
  - `snap_to_position` - Snap specific windows to positions
  - `manage_layouts` - Save and apply custom window layouts

### 11. Agent Memory System
- **Status**: ✅ Fully Operational
- **Package**: `@modelcontextprotocol/server-agent-memory`
- **Purpose**: Multi-tiered memory architecture for AI agents
- **Test Command**: `npx -y @modelcontextprotocol/server-agent-memory`
- **Documentation**: [MCP Agent Memory Details](mcp_servers/MCP Details/MCP Agent Memory.md)
- **Features**:
  - **Backend**: PostgreSQL database with JSONB storage
  - **Memory Types**: Episodic, Semantic, and Working memory
  - **Tools** (9 total):
    - Episodic Memory: store, retrieve, search
    - Semantic Memory: store, retrieve, search
    - Working Memory: store, retrieve, cleanup
  - Persistent storage across sessions
  - Multi-agent support with scoped memory
  - Tag-based organization and search

### 12. MCP Memory Service
- **Status**: ✅ Working
- **Location**: Local service
- **Purpose**: PGvector-based memory storage and retrieval
- **Test Command**: `uv --directory mcp_servers/mcp-memory-service run mcp-memory-server`
- **Documentation**: [MCP Memory Service Details](mcp_servers/mcp-memory-service/README.md)

### 13. Testing Validation Server
- **Status**: ✅ Working
- **Package**: `@modelcontextprotocol/server-testing-validation`
- **Purpose**: Test execution and validation
- **Test Command**: `npx -y @modelcontextprotocol/server-testing-validation`
- **Documentation**: [MCP Testing Validation Details](mcp_servers/MCP Details/MCP Testing Validation.md)

### 14. Secrets Manager MCP
- **Status**: ⚠️ Placeholder
- **Purpose**: Management of secrets and credentials
- **Documentation**: [Secrets Management System](Docs/Systems_Descriptions/Secrets_Credentials_Management.md)

### 15. Logging Telemetry MCP
- **Status**: ⚠️ Placeholder
- **Purpose**: Centralized logging and telemetry collection
- **Documentation**: [Logging System](Docs/Systems_Descriptions/Logging_Telemetry.md)

## Verification
- **Check server status**: `node mcp_servers/manage-mcp-servers.js status`
- **Review detailed status report**: [mcp-server-status.md](mcp_servers/mcp-server-status.md)
- **Test MCP Inspector**: `npx @modelcontextprotocol/inspector`

## Configuration Reference
- [MCP JSON Format](.vscode/mcp.json)
- [Environment Setup Guide](PODMAN_SETUP.md)
- **Environment Variables**:
  ```bash
  # GitHub Integration
  GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token_here
  
  # Database Integration
  DATABASE_URL=your_postgres_connection_string
  
  # Brave Search
  BRAVE_API_KEY=your_brave_api_key_here
  ```

## File Structure
```
.vscode/
├── mcp.json                    # VSCode MCP configuration
mcp_servers/
├── install-mcp-complete.js     # Complete installer
├── manage-mcp-servers.js       # Server management
└── README.md                   # Documentation
