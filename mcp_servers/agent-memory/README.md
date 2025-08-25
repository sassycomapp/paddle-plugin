# Agent Memory MCP Server

A comprehensive memory system for AI agents built on PostgreSQL with MCP (Model Context Protocol) integration.

## Features

- **Episodic Memory**: Store and retrieve events and contexts
- **Semantic Memory**: Store and retrieve facts and knowledge
- **Working Memory**: Temporary state storage with session management
- **Memory Bank Integration**: Sync with file-based memory storage
- **Advanced Search**: Cross-memory type search with tags and keywords
- **PostgreSQL Backend**: Robust, scalable storage solution

## Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Set up PostgreSQL**:
   ```bash
   # Create database tables
   psql -U postgres -d postgres -f create_memory_tables.sql
   ```

3. **Configure environment**:
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your PostgreSQL credentials
   DATABASE_URL=postgresql://postgres:your_password@localhost:5432/postgres
   ```

4. **Test the server**:
   ```bash
   # Run comprehensive tests
   node test-proper.js
   ```

## Usage

### Starting the Server

```bash
node index.js
```

### Available Tools

#### 1. Store Episodic Memory
```json
{
  "name": "store_episodic_memory",
  "arguments": {
    "agent_id": "agent-123",
    "session_id": "session-456",
    "context": {
      "event": "user_login",
      "details": {"username": "john_doe"}
    },
    "tags": ["authentication", "user_action"]
  }
}
```

#### 2. Store Semantic Memory
```json
{
  "name": "store_semantic_memory",
  "arguments": {
    "entity": "user_preferences",
    "data": {"theme": "dark", "language": "en"},
    "category": "user_profile",
    "agent_id": "agent-123",
    "tags": ["preferences", "settings"]
  }
}
```

#### 3. Store Working Memory
```json
{
  "name": "store_working_memory",
  "arguments": {
    "agent_id": "agent-123",
    "session_id": "session-456",
    "key": "current_task",
    "value": {"task": "process_payment", "status": "in_progress"}
  }
}
```

#### 4. Retrieve Memories
```json
{
  "name": "retrieve_episodic_memory",
  "arguments": {
    "agent_id": "agent-123",
    "limit": 10
  }
}
```

#### 5. Search Across Memory Types
```json
{
  "name": "search_memories",
  "arguments": {
    "query": "user preferences",
    "agent_id": "agent-123",
    "memory_types": ["episodic", "semantic"],
    "limit": 5
  }
}
```

## Database Schema

### Tables

1. **episodic_memory**: Events and contexts
   - `id` (SERIAL PRIMARY KEY)
   - `agent_id` (VARCHAR)
   - `session_id` (VARCHAR)
   - `timestamp` (TIMESTAMPTZ)
   - `context` (JSONB)
   - `memory_type` (VARCHAR)
   - `relevance_score` (FLOAT)
   - `tags` (TEXT[])

2. **semantic_memory**: Facts and knowledge
   - `id` (SERIAL PRIMARY KEY)
   - `entity` (VARCHAR)
   - `data` (JSONB)
   - `category` (VARCHAR)
   - `agent_id` (VARCHAR)
   - `last_updated` (TIMESTAMPTZ)
   - `access_count` (INTEGER)
   - `tags` (TEXT[])

3. **working_memory**: Temporary state
   - `id` (SERIAL PRIMARY KEY)
   - `agent_id` (VARCHAR)
   - `session_id` (VARCHAR)
   - `key` (VARCHAR)
   - `value` (JSONB)
   - `created_at` (TIMESTAMPTZ)
   - `expires_at` (TIMESTAMPTZ)

## Testing

Run the comprehensive test suite:

```bash
node test-proper.js
```

This will:
- List all available tools
- Test storing and retrieving all memory types
- Test search functionality
- Test memory cleanup
- Verify data integrity

## Integration with VS Code

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "agent-memory": {
      "command": "node",
      "args": ["path/to/mcp_servers/agent-memory/index.js"],
      "env": {
        "DATABASE_URL": "postgresql://postgres:your_password@localhost:5432/postgres"
      }
    }
  }
}
```

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `MEMORY_BANK_PATH`: Path to memory bank directory (optional)

## License

MIT
