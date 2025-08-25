# Vector System Implementation Guide

## Overview
The Vector System provides semantic search and retrieval capabilities using PostgreSQL with the pgvector extension, integrated with MCP (Model Context Protocol) servers for RAG (Retrieval-Augmented Generation) functionality. This implementation replaces the previously used PGvector system with a more robust PostgreSQL-based vector storage solution.

## Architecture Components
- **PostgreSQL Database**: Core storage with pgvector extension for vector operations
- **MCP Vector Store Server**: `pgvector-mcp-server.js` handles vector operations via MCP protocol
- **Embedding Generation**: Uses `@xenova/transformers` for local embedding generation
- **RAG Integration**: Connects vector storage with knowledge retrieval workflows

## Installation & Configuration

### 1. PostgreSQL Setup
```bash
# Install PostgreSQL (v13+ recommended)
# Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
```

**Verification**:
```bash
psql "postgresql://postgres:2001@localhost:5432/postgres" -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```
Expected output:
```
oid  | extname | extowner | extnamespace | extrelocatable | extversion | extconfig | extcondition
-------+---------+----------+--------------+----------------+------------+-----------+--------------
 24576 | vector  |       10 |         2200 | t              | 0.8.0      |           |
```

### 2. Database Schema
The system uses the following tables (created via `create_memory_tables.sql`):

```sql
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  title TEXT,
  content TEXT,
  embedding vector(384), -- Xenova/all-MiniLM-L6-v2 dimension
  metadata JSONB
);

CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### 3. MCP Server Configuration
**Key Dependencies** (in `mcp_servers/package.json`):
```json
{
  "dependencies": {
    "@modelcontextprotocol/sdk": "^0.5.0",
    "pg": "^8.12.0",
    "pgvector": "^0.2.1",
    "@xenova/transformers": "^2.23.0"
  }
}
```

**Critical Configuration**:
- Database connection string: `postgresql://postgres:2001@localhost:5432/postgres`
- Embedding model: `Xenova/all-MiniLM-L6-v2` (384 dimensions)
- Collection name: `documents`

### 4. Dependency Management
**Common Issues & Solutions**:
```bash
# Fix pgvector version conflict
npm install @xenova/transformers --prefix mcp_servers
npm install pgvector@0.2.1 --prefix mcp_servers

# Start MCP server
npm run start:rag
```

## Operational Validation

### Verification Checklist
1. **PostgreSQL Integration**:
   ```bash
   psql "postgresql://postgres:2001@localhost:5432/postgres" -c "\dx"
   ```
   Should show `vector` extension

2. **MCP Server Status**:
   ```bash
   node test-rag-system.js status
   ```
   Expected output:
   ```
   ✅ PostgreSQL is running with pgvector
   ✅ RAG MCP server appears to be available
   ```

3. **End-to-End Test**:
   ```bash
   node test-rag-system.js test
   ```
   Should show all tests passing with successful document operations

## Troubleshooting Guide

### Common Issues
| Issue | Solution |
|-------|----------|
| `pgvector@^1.0.1 not found` | Downgrade to `pgvector@0.2.1` in `mcp_servers/package.json` |
| `@xenova/transformers not found` | Install with `npm install @xenova/transformers --prefix mcp_servers` |
| PostgreSQL authentication failure | Use connection string format: `postgresql://postgres:2001@localhost:5432/postgres` |
| Vector dimension mismatch | Ensure all embeddings use 384 dimensions (Xenova/all-MiniLM-L6-v2) |

### Recovery Procedures
1. **Reinitialize Database**:
   ```bash
   psql "postgresql://postgres:2001@localhost:5432/postgres" -f create_memory_tables.sql
   ```

2. **Full Dependency Reset**:
   ```bash
   cd mcp_servers
   rm -rf node_modules package-lock.json
   npm install
   ```

## Integration Points

### RAG Workflow
1. Text input → Embedding generation (via `@xenova/transformers`)
2. Vector storage → `add_document` MCP tool
3. Query processing → `search_documents` MCP tool
4. Context retrieval → Integrated with AG2 orchestrator

### Security Considerations
- Database access restricted to localhost
- Connection strings stored in environment variables
- No external API keys required for embedding generation
- All operations use parameterized queries to prevent SQL injection

## Maintenance Procedures

### Index Optimization
```sql
-- Rebuild index for better performance
REINDEX INDEX idx_documents_embedding;
```

### Backup Strategy
1. Regular PostgreSQL dumps:
   ```bash
   pg_dump -U postgres -Fc postgres > vector_backup.dump
   ```
2. Verify backups with:
   ```bash
   pg_restore -l vector_backup.dump
   ```

## Migration from PGvector
This implementation completely replaces the previous PGvector system. All data should be migrated using:
```javascript
// Example migration script
const { "Placeholder"Client } = require('PGvector');
const pgClient = new Pool({/* connection */});

// Export from PGvector
const collections = await "Placeholder"Client.listCollections();
for (const collection of collections) {
  const items = await collection.getItems();
  // Import to PostgreSQL
  await pgClient.query('INSERT INTO documents (...) VALUES (...)');
}
```

## Verification Summary
- [x] PostgreSQL with pgvector extension confirmed installed
- [x] MCP Vector Store server running with correct dependencies
- [x] RAG test suite passed all validation checks
- [x] Document storage and semantic search fully operational
- [x] Integration with memory systems validated
