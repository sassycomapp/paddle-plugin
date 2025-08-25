# Agent Memory System - Authoritative Documentation

## 🧠 System Overview

The Agent Memory System is a comprehensive, multi-tiered memory architecture designed for AI agents, providing persistent, contextual, and scalable memory capabilities across sessions. It combines three distinct memory types with robust storage backends and seamless MCP integration to create a self-evolving knowledge base.

### Architecture Components
- **PostgreSQL Backend**: Structured storage for episodic and semantic memories with pgvector extension
- **PGvector/SQLite-vec**: Vector database for semantic search and similarity matching
- **Memory Bank**: Markdown-based document memory for project context and active sessions
- **MCP Server**: Standardized interface for memory operations via Model Context Protocol
- **Working Memory**: Short-term context storage for active sessions with TTL management

### Memory Types

#### Episodic Memory
- **Purpose**: Stores specific events, interactions, and contextual experiences
- **Structure**: Timestamped entries with agent context, metadata, and relevance scoring
- **Use Cases**: Conversation history, action logs, decision trails, session recordings
- **Key Features**:
  - Time-based organization (daily, weekly, monthly)
  - Automatic relevance scoring
  - Creative association discovery between related events
  - Controlled forgetting with safe archival

#### Semantic Memory
- **Purpose**: Stores general knowledge, facts, and entity relationships
- **Structure**: Entity-based storage with JSONB data fields and vector embeddings
- **Use Cases**: Domain knowledge, learned patterns, persistent facts, reference materials
- **Key Features**:
  - Semantic clustering of related concepts
  - Intelligent compression of redundant information
  - Cross-memory association discovery
  - Context-aware retrieval

#### Working Memory
- **Purpose**: Temporary session-based state management
- **Structure**: Key-value pairs with TTL, session binding, and automatic cleanup
- **Use Cases**: Current task state, temporary variables, active context
- **Key Features**:
  - Automatic expiration based on time-to-live
  - Session-scoped isolation
  - Performance-optimized for frequent access
  - Automatic cleanup of expired entries

## 🏗️ Installation Details

### Prerequisites
- **Node.js 18+** installed (for agent-memory service)
- **PostgreSQL 14+** with pgvector extension (for structured storage)
- **Python 3.10+** with uv (for MCP Memory Service)
- **MCP-compatible client** (VS Code, Claude Desktop, etc.)
- **PGvector dependencies** (for vector storage)

### Quick Installation Options

#### 🚀 Intelligent Installer (Recommended)
```bash
# Clone the repository
git clone https://github.com/doobidoo/mcp-memory-service.git
cd mcp-memory-service

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the intelligent installer
python install.py

# Follow prompts for multi-client setup and Claude Code commands
```

#### 🐳 Docker Installation
```bash
# Pull the latest image
docker pull doobidoo/mcp-memory-service:latest

# Run with default settings
docker run -d -p 8000:8000 \
  -v $(pwd)/data/"Placeholder"_db:/app/"Placeholder"_db \
  -v $(pwd)/data/backups:/app/backups \
  doobidoo/mcp-memory-service:latest

# For standalone mode (prevents boot loops)
docker-compose -f docker-compose.standalone.yml up
```

#### 🧩 Agent Memory Service Installation
```bash
# Navigate to agent-memory directory
cd mcp_servers/agent-memory

# Run automated installer
./install.sh          # Unix/Linux
# OR
install.bat          # Windows

# Manual installation
npm install
cp .env.example .env
psql -U postgres -d postgres -f create_memory_tables.sql
```

### Hardware-Specific Installation

#### For Intel Macs (2015-2017)
```bash
python install.py --legacy-hardware
```

#### For Windows Systems
```bash
# After activating virtual environment
python scripts/install_windows.py
```

#### For Server/Headless Deployment
```bash
python install.py --server-mode
```

## ⚙️ Configuration Details

### Environment Variables (.env)
```env
# Database Configuration
PGHOST=localhost
PGUSER=postgres
PGPASSWORD=2001
PGDATABASE=postgres
PGPORT=5432

# Memory Service Configuration
MCP_MEMORY_"Placeholder"_PATH=mcp_servers/mcp-memory-service/data/"Placeholder"_db
MCP_MEMORY_BACKUPS_PATH=mcp_servers/mcp-memory-service/data/backups
MEMORY_BANK_PATH=./memorybank
MAX_MEMORY_ENTRIES=1000
ENABLE_PRUNING=true
LOG_LEVEL=info

# Storage Backend Configuration
MCP_MEMORY_STORAGE_BACKEND=PGvector  # or sqlite_vec
MCP_MEMORY_SQLITE_PATH=./memorybank/sqlite_vec.db
MCP_MEMORY_USE_ONNX=1  # For CPU-only deployments

# Consolidation Configuration
MCP_CONSOLIDATION_ENABLED=true
MCP_RETENTION_CRITICAL=365
MCP_RETENTION_REFERENCE=180
MCP_RETENTION_STANDARD=30
MCP_RETENTION_TEMPORARY=7
```

### MCP Configuration (mcp.json)
```json
{
  "mcpServers": {
    "agent-memory": {
      "command": "node",
      "args": ["mcp_servers/agent-memory/index.js"],
      "env": {
        "PGHOST": "localhost",
        "PGUSER": "postgres",
        "PGPASSWORD": "2001",
        "PGDATABASE": "postgres",
        "PGPORT": "5432",
        "MEMORY_BANK_PATH": "./memorybank"
      }
    },
    "mcp-memory-service": {
      "command": "uv",
      "args": [
        "--directory",
        "mcp_servers/mcp-memory-service",
        "run",
        "mcp-memory-server"
      ],
      "env": {
        "MCP_MEMORY_"Placeholder"_PATH": "mcp_servers/mcp-memory-service/data/"Placeholder"_db",
        "MCP_MEMORY_BACKUPS_PATH": "mcp_servers/mcp-memory-service/data/backups"
      }
    }
  }
}
```

### VS Code Integration
Add to VS Code settings.json:
```json
{
  "mcp": {
    "servers": {
      "agent-memory": {
        "command": "node",
        "args": ["${workspaceFolder}/mcp_servers/agent-memory/index.js"],
        "env": {
          "PGHOST": "localhost",
          "PGUSER": "postgres",
          "PGPASSWORD": "2001",
          "PGDATABASE": "postgres",
          "PGPORT": "5432"
        }
      }
    }
  }
}
```

## 🔧 Integration Details

### Database Schema
```sql
-- Episodic Memory Table
CREATE TABLE IF NOT EXISTS episodic_memory (
  id SERIAL PRIMARY KEY,
  agent_id VARCHAR(255) NOT NULL,
  session_id VARCHAR(255),
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  context JSONB,
  memory_type VARCHAR(50) DEFAULT 'episodic',
  relevance_score FLOAT DEFAULT 1.0,
  tags TEXT[]
);

-- Semantic Memory Table
CREATE TABLE IF NOT EXISTS semantic_memory (
  id SERIAL PRIMARY KEY,
  agent_id VARCHAR(255) NOT NULL,
  entity VARCHAR(255) NOT NULL,
  data JSONB,
  memory_type VARCHAR(50) DEFAULT 'semantic',
  last_updated TIMESTAMPTZ DEFAULT NOW(),
  tags TEXT[]
);

-- Working Memory Table
CREATE TABLE IF NOT EXISTS working_memory (
  id SERIAL PRIMARY KEY,
  agent_id VARCHAR(255) NOT NULL,
  session_id VARCHAR(255) NOT NULL,
  key VARCHAR(255) NOT NULL,
  value JSONB,
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_episodic_agent_time ON episodic_memory (agent_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_semantic_agent_entity ON semantic_memory (agent_id, entity);
CREATE INDEX IF NOT EXISTS idx_working_session ON working_memory (session_id, key);
```

### Memory Bank Structure
```bash
memorybank/
├── activeContext.md        # Current focus and immediate context
│   # Contains:
│   # - Current project focus
│   # - Recent activities
│   # - Next steps
├── projectbrief.md         # Project overview and goals
│   # Contains:
│   # - High-level project overview
│   # - Key features
│   # - Technical stack
│   # - Key requirements
├── systemPatterns.md       # Reusable patterns and workflows
│   # Contains:
│   # - Common workflows (code review, debugging)
│   # - Reusable prompts (refactoring, documentation)
└── sessions/               # Session-specific snapshots
    ├── 2024-07-31-001.md   # Date-stamped session records
    └── 2024-07-31-002.md
```

## 🚀 Startup Instructions

### 1. Start the MCP Servers
```bash
# Start agent-memory service
node mcp_servers/agent-memory/index.js

# Start MCP Memory Service
uv --directory mcp_servers/mcp-memory-service run mcp-memory-server
```

### 2. Verify Server Status
```bash
# Run verification script
node mcp_servers/agent-memory/verify.js

# Expected output:
# ✅ Agent Memory MCP Server running on stdio
# ✅ All 9 memory tools registered successfully
# ✅ Database connection established

# Check MCP Memory Service
curl http://localhost:8000/health
# Expected output: {"status":"healthy"}
```

### 3. Test Memory Operations
```bash
# Run comprehensive test suite
node mcp_servers/agent-memory/test-proper.js
node mcp_servers/mcp-memory-service/scripts/test_memory_simple.py

# Expected output:
# ✅ All tests passed!
```

## 📖 Usage Instructions

### Available Tools (16 Total)

#### Episodic Memory Tools
- `store_episodic_memory` - Store an event or experience
- `retrieve_episodic_memory` - Retrieve events by agent/session
- `search_episodic_memory` - Search events by content/tags
- `recall_memory` - Retrieve memories using natural language time expressions

#### Semantic Memory Tools
- `store_semantic_memory` - Store knowledge or fact
- `retrieve_semantic_memory` - Retrieve knowledge by entity
- `search_semantic_memory` - Search knowledge by content/tags
- `get_memory_associations` - Explore discovered memory connections

#### Working Memory Tools
- `store_working_memory` - Store temporary session data
- `retrieve_working_memory` - Retrieve session data
- `cleanup_working_memory` - Clear expired session data

#### Memory Consolidation Tools
- `consolidate_memories` - Manually trigger consolidation
- `get_consolidation_health` - Monitor system health
- `get_consolidation_stats` - View processing statistics
- `get_memory_clusters` - Browse semantic memory clusters
- `get_consolidation_recommendations` - Get AI-powered memory management advice

### Example Usage Patterns

#### Storing Episodic Memory
```javascript
// Store a conversation event
await use_mcp_tool({
  server_name: "agent-memory",
  tool_name: "store_episodic_memory",
  arguments: {
    agent_id: "claude-assistant",
    session_id: "session-123",
    context: {
      type: "user_query",
      query: "How do I install PostgreSQL?",
      response: "Here are the installation steps...",
      timestamp: new Date().toISOString()
    },
    tags: ["installation", "postgresql", "help"]
  }
});
```

#### Retrieving Semantic Knowledge
```javascript
// Retrieve knowledge about a specific topic
const knowledge = await use_mcp_tool({
  server_name: "agent-memory",
  tool_name: "retrieve_semantic_memory",
  arguments: {
    agent_id: "claude-assistant",
    entity: "postgresql_installation"
  }
});
```

#### Managing Working Memory
```javascript
// Store temporary session state
await use_mcp_tool({
  server_name: "agent-memory",
  tool_name: "store_working_memory",
  arguments: {
    agent_id: "claude-assistant",
    session_id: "session-123",
    key: "current_task",
    value: { task: "install_postgresql", step: 3 },
    expires_at: new Date(Date.now() + 3600000).toISOString()
  }
});
```

#### Using Memory Consolidation
```javascript
// Trigger daily consolidation
await use_mcp_tool({
  server_name: "mcp-memory-service",
  tool_name: "consolidate_memories",
  arguments: {
    horizon: "daily"
  }
});

// Get memory clusters
const clusters = await use_mcp_tool({
  server_name: "mcp-memory-service",
  tool_name: "get_memory_clusters",
  arguments: {
    min_size: 3,
    similarity_threshold: 0.6
  }
});
```

## 🎯 Agent Memory System Features

### Core Features
- **Persistent Storage**: PostgreSQL-backed durable memory
- **Multi-Agent Support**: Scoped memory per agent ID
- **Session Management**: Working memory with automatic cleanup
- **Tag-Based Organization**: Flexible categorization system
- **Relevance Scoring**: Intelligent memory prioritization
- **Full-Text Search**: Cross-memory content search
- **JSONB Storage**: Flexible schema for complex data

### Advanced Features
- **Memory Pruning**: Automatic cleanup of old/expired memories
- **Cross-Memory Search**: Unified search across all memory types
- **Memory Bank Integration**: Markdown-based document memory
- **MCP Protocol**: Universal agent compatibility
- **Performance Optimized**: Indexed queries and efficient storage
- **Security**: Agent-scoped access control
- **Backup Ready**: PostgreSQL backup and Memory Bank file sync

### Dream-Inspired Memory Consolidation
- **Daily consolidation**: Updates memory relevance and basic organization
- **Weekly consolidation**: Discovers creative associations between memories
- **Monthly consolidation**: Performs semantic clustering and intelligent compression
- **Quarterly/Yearly consolidation**: Deep archival and long-term memory management
- **Controlled forgetting**: With safe archival and recovery systems
- **Performance optimized**: For processing 10k+ memories efficiently

## 🔍 Troubleshooting

### Common Issues & Solutions

| Issue | Symptoms | Solution |
|-------|----------|----------|
| **Database Connection Failed** | `Connection refused` errors | Verify PostgreSQL service status, check credentials in .env, ensure database exists |
| **MCP Server Not Starting** | Process exits immediately | Check Node.js version (18+ required), verify dependencies installed, check port availability |
| **Memory Not Persisting** | Data disappears after restart | Verify database write permissions, check transaction commits, review error logs |
| **PGvector Path Issues** | `Could not connect to PGvector` | Ensure `MCP_MEMORY_"Placeholder"_PATH` points to writable directory |
| **Embedding Generation Failure** | `Model download failed` | Check internet connection or specify local model path |
| **Windows PyTorch Errors** | DLL load failures | Use `python scripts/install_windows.py` for proper installation |

### Diagnostic Commands
- Check PostgreSQL status:
```bash
pg_ctl status -D "C:/Program Files/PostgreSQL/14/data"
```

- Verify PGvector storage:
```bash
dir mcp_servers\mcp-memory-service\data\"Placeholder"_db
```

- Test database connection:
```bash
psql -U postgres -d postgres -c "\dt"
```

- Enable debug logging:
```bash
DEBUG=agent-memory:* node mcp_servers/agent-memory/index.js
```

## 📊 Performance & Monitoring

### Database Optimization
- Indexed queries for fast retrieval
- Connection pooling for concurrent access
- Query optimization for large datasets
- Regular VACUUM and ANALYZE operations
- Automatic database health monitoring

### Memory Usage
- Configurable memory limits
- Automatic cleanup policies
- Usage analytics and reporting
- Performance metrics collection
- Live statistics dashboard (http://localhost:8000/)

### Hardware Compatibility Matrix

| Platform | Architecture | Accelerator | Status | Notes |
|----------|--------------|-------------|--------|-------|
| macOS | Apple Silicon (M1/M2/M3) | MPS | ✅ Fully supported | Best performance |
| macOS | Apple Silicon under Rosetta 2 | CPU | ✅ Supported with fallbacks | Good performance |
| macOS | Intel | CPU | ✅ Fully supported | Good with optimized settings |
| Windows | x86_64 | CUDA | ✅ Fully supported | Best performance |
| Windows | x86_64 | DirectML | ✅ Supported | Good performance |
| Windows | x86_64 | CPU | ✅ Supported with fallbacks | Slower but works |
| Linux | x86_64 | CUDA | ✅ Fully supported | Best performance |
| Linux | x86_64 | ROCm | ✅ Supported | Good performance |
| Linux | x86_64 | CPU | ✅ Supported with fallbacks | Slower but works |
| Linux | ARM64 | CPU | ✅ Supported with fallbacks | Slower but works |
| Any | Any | No PyTorch | ✅ Supported with SQLite-vec | Limited functionality, very lightweight |

## 🔗 Integration Examples

### With Claude Desktop
1. Add MCP configuration to Claude Desktop
2. Use memory tools in conversations
3. Persistent context across sessions
4. Utilize natural language commands:
   - "Please remember that my project deadline is May 15th."
   - "Do you remember what I told you about my project deadline?"

### With VS Code
1. Install MCP extension
2. Configure agent-memory server
3. Use in AI coding assistants
4. Access memory through sidebar UI

### With Claude Code Commands
```bash
# Store information with context
claude /memory-store "Important architectural decision about database backend"

# Recall memories by time
claude /memory-recall "what did we decide about the database last week?"

# Search by tags or content
claude /memory-search --tags "architecture,database"

# Capture current session context
claude /memory-context --summary "Development planning session"

# Check service health
claude /memory-health
```

### With Custom Agents
1. Import MCP client library
2. Connect to agent-memory server
3. Implement memory workflows
4. Use advanced consolidation features

## 📦 Maintenance

### Backup Strategy
1. **Automatic Backups**:
   - Configure daily backups to `MCP_MEMORY_BACKUPS_PATH`
   - Use PostgreSQL `pg_dump` for database backups

2. **Manual Backup Command**:
```bash
pg_dump -U postgres memory_db > memory_db_$(date +%Y%m%d).sql
```

3. **Memory Bank Backup**:
```bash
zip -r memorybank_backup_$(date +%Y%m%d).zip memorybank/
```

### Memory Optimization
- **Consolidation Process**:
  - Run periodic memory consolidation
  - Merge related episodic memories
  - Update semantic memory clusters

- **Cleanup Script**:
```bash
node mcp_servers/agent-memory/cleanup.js --days 30
```

- **Database Maintenance**:
```bash
psql -U postgres -d memory_db -c "VACUUM ANALYZE;"
```

## 📚 References

### Documentation Resources
- [MCP Memory Service GitHub](https://github.com/doobidoo/mcp-memory-service)
- [PGvector Documentation](https://docs.try"Placeholder".com/)
- [PostgreSQL pgvector Extension](https://github.com/pgvector/pgvector)
- [MCP Protocol Specification](https://modelcontextprotocol.dev/)
- [SQLite-vec Backend Guide](docs/sqlite-vec-backend.md)

### Installation Guides
- [Master Installation Guide](docs/installation/master-guide.md)
- [Storage Backend Comparison](docs/guides/STORAGE_BACKENDS.md)
- [Multi-Client Setup](docs/integration/multi-client.md)
- [Windows Setup Guide](docs/guides/windows-setup.md)
- [Intel Mac Setup Guide](docs/platforms/macos-intel.md)

### Advanced Topics
- [Dream-Inspired Consolidation](docs/development/memory_consolidation.md)
- [Multi-Client Architecture](docs/development/multi-client-architecture.md)
- [Homebrew PyTorch Integration](docs/integration/homebrew.md)
- [Docker Deployment](docs/deployment/docker.md)
- [Performance Optimization](docs/implementation/performance.md)

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2025-08-18 | Comprehensive documentation update integrating all memory components |
| 1.5 | 2025-08-15 | Added Memory Bank documentation and consolidation features |
| 1.0 | 2025-08-10 | Initial comprehensive documentation |
| 0.9 | 2025-08-05 | Fixed PostgreSQL password format |
| 0.8 | 2025-07-28 | Added PGvector integration details |
| 0.7 | 2025-07-20 | Initial implementation documentation |

## 📌 Memory Bank System Documentation

### Overview
The Memory Bank system provides a lightweight, human-readable documentation layer that complements the structured database storage. It consists of Markdown files that capture project context, active sessions, and reusable patterns.

### Core Components

#### activeContext.md
```markdown
# Active Context

## Current Focus
[Describe what you're currently working on]

## Recent Activities
- [Activity 1]
- [Activity 2]

## Next Steps
- [Next action item 1]
- [Next action item 2]
```
- **Purpose**: Tracks immediate context and current focus
- **Usage**: Updated automatically during active sessions
- **Integration**: Linked to working memory for session continuity

#### projectbrief.md
```markdown
# Project Brief

## Overview
[Provide a high-level overview of the project]

## Key Features
- [Feature 1]
- [Feature 2]
- [Feature 3]

## Technical Stack
- Frontend: 
- Backend: 
- Database: 

## Key Requirements
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]
```
- **Purpose**: Captures project scope and technical details
- **Usage**: Serves as onboarding documentation for new team members
- **Integration**: Linked to semantic memory for project knowledge

#### systemPatterns.md
```markdown
# System Patterns

## Common Workflows
### Code Review
```
[Describe code review workflow]
```

### Debugging Process
```
[Describe debugging workflow]
```

## Reusable Prompts
### Refactoring
```
[Prompt template for refactoring tasks]
```

### Documentation
```
[Prompt template for documentation tasks]
```
```
- **Purpose**: Documents recurring patterns and workflows
- **Usage**: Provides templates for common development tasks
- **Integration**: Used by semantic memory for pattern recognition

#### sessions/ Directory
- **Purpose**: Stores dated session snapshots
- **Structure**: Files named with timestamp format (YYYY-MM-DD-XXX.md)
- **Content**: Detailed session records including:
  - Tasks completed
  - Decisions made
  - Code snippets
  - Next steps

### Integration with MCP Memory Service
The Memory Bank system works in concert with the MCP Memory Service:
1. **Context Capture**: Active context is mirrored in working memory
2. **Pattern Recognition**: System patterns inform semantic memory clustering
3. **Project Documentation**: Project briefs become semantic memory entities
4. **Session Continuity**: Session snapshots link to episodic memory entries

### Best Practices
- **Regular Updates**: Keep activeContext.md current during work sessions
- **Pattern Documentation**: Add new patterns to systemPatterns.md as they emerge
- **Project Onboarding**: Maintain projectbrief.md for new team members
- **Session Review**: Periodically review session snapshots for insights

### Verification
Confirm proper integration with:
```bash
# Check Memory Bank files
ls memorybank/

# Verify content structure
cat memorybank/activeContext.md

# Test MCP integration
curl http://localhost:8000/memories?query="current%20focus"
```

## 📦 Service Installation

### Cross-Platform Service Installer
```bash
# Install as a service (auto-detects OS)
python install_service.py

# Start the service
python install_service.py --start

# Check service status
python install_service.py --status

# Stop the service
python install_service.py --stop

# Uninstall the service
python install_service.py --uninstall
```

The installer provides:
- ✅ **Automatic OS detection** (Windows, macOS, Linux)
- ✅ **Native service integration** (systemd, LaunchAgent, Windows Service)
- ✅ **Automatic startup** on boot/login
- ✅ **Service management commands**
- ✅ **Secure API key generation**
- ✅ **Platform-specific optimizations**

## 🌐 Multi-Client Deployment

### Centralized Server Deployment
```bash
# Install and start HTTP/SSE server
python install.py --server-mode --enable-http-api
export MCP_HTTP_HOST=0.0.0.0
export MCP_API_KEY="your-secure-key"
python scripts/run_http_server.py
```

**Benefits**:
- 🔄 **Real-time sync** across all clients via Server-Sent Events (SSE)
- 🌍 **Cross-platform** - works from any device with HTTP access
- 🔒 **Secure** with optional API key authentication
- 📈 **Scalable** - handles many concurrent clients
- ☁️ **Cloud-ready** - deploy on AWS, DigitalOcean, Docker

**Access via**:
- **API Docs**: `http://your-server:8000/api/docs`
- **Web Dashboard**: `http://your-server:8000/`
- **REST API**: All MCP operations available via HTTP

### Why NOT Cloud Storage
**Direct SQLite on cloud storage DOES NOT WORK** for multi-client access:

❌ **File locking conflicts** - Cloud sync breaks SQLite's locking mechanism  
❌ **Data corruption** - Incomplete syncs can corrupt the database  
❌ **Sync conflicts** - Multiple clients create "conflicted copy" files  
❌ **Performance issues** - Full database re-upload on every change  

**✅ Solution**: Use centralized HTTP server deployment instead!

---

**This document serves as the complete reference for the Agent Memory System. For additional support, refer to the detailed documentation in the mcp-memory-service repository or check the troubleshooting section above.**
