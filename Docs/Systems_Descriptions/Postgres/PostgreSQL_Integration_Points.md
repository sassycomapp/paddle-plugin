# PostgreSQL Integration Points Documentation

## Overview

This document details the integration points between PostgreSQL and other systems in the paddle-plugin ecosystem. PostgreSQL serves as the central data storage and vector database for multiple AI and memory-related components.

## System Integration Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vector System │    │  Memory System  │    │    RAG System   │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ pgvector    │ │    │ │ PostgreSQL  │ │    │ │ PostgreSQL  │ │
│ │ Extension   │ │    │ │ Storage     │ │    │ │ Vector Store│ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   MCP Servers   │
                    │                 │
                    │ ┌─────────────┐ │
                    │ │ PostgreSQL  │ │
                    │ │ MCP Server  │ │
                    │ └─────────────┘ │
                    │ ┌─────────────┐ │
                    │ │ Agent Memory│ │
                    │ │ MCP Server  │ │
                    │ └─────────────┘ │
                    │ ┌─────────────┐ │
                    │ │ Testing MCP │ │
                    │ │ Server      │ │
                    │ └─────────────┘ │
                    │ ┌─────────────┐ │
                    │ │ Scheduler   │ │
                    │ │ MCP Server  │ │
                    │ └─────────────┘ │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Applications  │
                    │                 │
                    │ ┌─────────────┐ │
                    │ │ VS Code     │ │
                    │ │ MCP Client  │ │
                    │ └─────────────┘ │
                    │ ┌─────────────┐ │
                    │ │ AG2         │ │
                    │ │ Orchestrator│ │
                    │ └─────────────┘ │
                    └─────────────────┘
```

## 1. Vector System Integration

### Integration Overview
The Vector System uses PostgreSQL with pgvector extension as its primary vector database for semantic search and similarity operations.

### Technical Details
- **Database**: PostgreSQL 17.5 with pgvector v0.8.0
- **Connection**: `postgresql://postgres:2001@localhost:5432/postgres`
- **Embedding Model**: Xenova/all-MiniLM-L6-v2 (384 dimensions)
- **Collection**: `documents` table

### Schema Integration
```sql
-- Vector System Schema
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  title TEXT,
  content TEXT,
  embedding vector(384),  -- Matches Xenova embedding dimensions
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vector Index for similarity search
CREATE INDEX idx_documents_embedding ON documents 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Additional indexes for performance
CREATE INDEX idx_documents_created_at ON documents (created_at);
CREATE INDEX idx_documents_metadata ON documents USING GIN (metadata);
```

### MCP Integration
```json
{
  "name": "vector-store",
  "command": "node",
  "args": ["mcp_servers/pgvector-mcp-server.js"],
  "env": {
    "DATABASE_URL": "postgresql://postgres:2001@localhost:5432/postgres",
    "EMBEDDING_MODEL": "Xenova/all-MiniLM-L6-v2",
    "COLLECTION_NAME": "documents"
  }
}
```

### API Endpoints
- **Add Document**: `POST /api/v1/documents`
- **Search Documents**: `POST /api/v1/documents/search`
- **Get Document**: `GET /api/v1/documents/:id`
- **Update Document**: `PUT /api/v1/documents/:id`
- **Delete Document**: `DELETE /api/v1/documents/:id`

### Integration Flow
```
Text Input → Embedding Generation → Vector Storage → Similarity Search → Results
    ↓              ↓                  ↓              ↓              ↓
  Xenova      PostgreSQL          pgvector      Cosine        Application
  Model        Database          Extension      Similarity     Integration
```

## 2. Memory System Integration

### Integration Overview
The Memory System uses PostgreSQL as its persistent storage backend for agent memories and conversation history.

### Technical Details
- **Database**: Same PostgreSQL instance as Vector System
- **Schema**: Multiple tables for different memory types
- **Connection**: `postgresql://postgres:2001@localhost:5432/postgres`
- **Storage Engine**: PostgreSQL with JSONB for metadata

### Schema Integration
```sql
-- Memory System Schema
CREATE TABLE memory_banks (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE memories (
  id SERIAL PRIMARY KEY,
  memory_bank_id INTEGER REFERENCES memory_banks(id),
  content TEXT NOT NULL,
  embedding vector(384),  -- For semantic search
  metadata JSONB,
  importance INTEGER DEFAULT 1,
  access_count INTEGER DEFAULT 0,
  last_accessed TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE conversations (
  id SERIAL PRIMARY KEY,
  session_id VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL,  -- 'user' or 'assistant'
  content TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_memories_memory_bank_id ON memories (memory_bank_id);
CREATE INDEX idx_memories_importance ON memories (importance DESC);
CREATE INDEX idx_conversations_session_id ON conversations (session_id);
CREATE INDEX idx_conversations_created_at ON conversations (created_at);
```

### MCP Integration
```json
{
  "name": "agent-memory",
  "command": "node",
  "args": ["mcp_servers/agent-memory/index.js"],
  "env": {
    "DATABASE_URL": "postgresql://postgres:2001@localhost:5432/postgres",
    "MEMORY_BANK_PATH": "./memorybank"
  }
}
```

### Memory Operations
- **Store Memory**: `INSERT INTO memories (...) VALUES (...)`
- **Retrieve Memory**: `SELECT * FROM memories WHERE memory_bank_id = ?`
- **Search Memories**: `SELECT * FROM memories ORDER BY embedding <=> ? LIMIT 10`
- **Update Access**: `UPDATE memories SET access_count = access_count + 1, last_accessed = NOW() WHERE id = ?`

### Integration Flow
```
Agent Input → Memory Processing → PostgreSQL Storage → Retrieval → Response
    ↓            ↓                  ↓              ↓          ↓
  User       Memory              Database      Vector     Agent
  Message    Encoding            Persistence   Search     Response
```

## 3. RAG (Retrieval-Augmented Generation) Integration

### Integration Overview
The RAG System integrates with PostgreSQL for document storage, retrieval, and context generation.

### Technical Details
- **Database**: Shared with Vector and Memory systems
- **Document Storage**: `documents` table with vector embeddings
- **Context Retrieval**: Vector similarity search
- **MCP Integration**: Dedicated RAG MCP server

### Schema Integration
```sql
-- RAG-specific extensions
CREATE TABLE rag_sessions (
  id SERIAL PRIMARY KEY,
  session_id VARCHAR(255) UNIQUE NOT NULL,
  context TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rag_queries (
  id SERIAL PRIMARY KEY,
  session_id INTEGER REFERENCES rag_sessions(id),
  query_text TEXT NOT NULL,
  context_used TEXT,
  response TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_rag_sessions_session_id ON rag_sessions (session_id);
CREATE INDEX idx_rag_queries_session_id ON rag_queries (session_id);
CREATE INDEX idx_rag_queries_created_at ON rag_queries (created_at);
```

### MCP Integration
```json
{
  "name": "rag-mcp-server",
  "command": "node",
  "args": ["mcp_servers/rag-mcp-server.js"],
  "env": {
    "DATABASE_URL": "postgresql://postgres:2001@localhost:5432/postgres",
    "CHROMA_URL": "http://localhost:8000"
  }
}
```

### RAG Workflow
```
User Query → Document Retrieval → Context Building → LLM Generation → Response
    ↓            ↓                  ↓                ↓            ↓
  Question   Vector Search      PostgreSQL      Language      Final
             (pgvector)         Context          Model        Response
```

### Available Tools
- `add_document`: Add documents to the RAG system
- `search_documents`: Search for relevant documents
- `generate_context`: Build context from retrieved documents
- `rag_query`: Perform complete RAG workflow

## 4. Testing and Validation Integration

### Integration Overview
The Testing and Validation System uses PostgreSQL for test data storage and validation results.

### Technical Details
- **Database**: Separate schema for test data
- **Connection**: `postgresql://postgres:2001@localhost:5432/postgres`
- **Schema**: Test results, validation logs, performance metrics

### Schema Integration
```sql
-- Testing System Schema
CREATE TABLE test_suites (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE test_cases (
  id SERIAL PRIMARY KEY,
  test_suite_id INTEGER REFERENCES test_suites(id),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  status VARCHAR(50) DEFAULT 'pending',  -- pending, running, passed, failed
  result TEXT,
  execution_time INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  executed_at TIMESTAMP
);

CREATE TABLE test_results (
  id SERIAL PRIMARY KEY,
  test_case_id INTEGER REFERENCES test_cases(id),
  metric_name VARCHAR(255) NOT NULL,
  metric_value DECIMAL(10,4),
  threshold DECIMAL(10,4),
  status VARCHAR(20) DEFAULT 'unknown',  -- unknown, pass, fail, warning
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_test_cases_test_suite_id ON test_cases (test_suite_id);
CREATE INDEX idx_test_cases_status ON test_cases (status);
CREATE INDEX idx_test_results_test_case_id ON test_results (test_case_id);
```

### MCP Integration
```json
{
  "name": "testing-validation",
  "command": "node",
  "args": ["testing-validation-system/src/mcp/test-mcp-server.js"],
  "env": {
    "DATABASE_URL": "postgresql://postgres:2001@localhost:5432/postgres"
  }
}
```

### Testing Operations
- **Run Test Suite**: Execute comprehensive tests
- **Validate Results**: Store test results in PostgreSQL
- **Performance Metrics**: Track system performance over time
- **Regression Testing**: Compare current vs. baseline performance

## 5. Scheduler Integration

### Integration Overview
The MCP Scheduler uses PostgreSQL for persistent task storage and execution tracking.

### Technical Details
- **Database**: Shared instance with task-specific schema
- **Connection**: `postgresql://postgres:2001@localhost:5432/postgres`
- **Schema**: Tasks, schedules, execution history

### Schema Integration
```sql
-- Scheduler Schema
CREATE TABLE scheduler_tasks (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  command TEXT NOT NULL,
  schedule VARCHAR(255),  -- Cron expression
  is_active BOOLEAN DEFAULT true,
  max_retries INTEGER DEFAULT 3,
  retry_delay INTEGER DEFAULT 60,
  timeout INTEGER DEFAULT 300,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scheduler_executions (
  id SERIAL PRIMARY KEY,
  task_id INTEGER REFERENCES scheduler_tasks(id),
  status VARCHAR(50) DEFAULT 'pending',  -- pending, running, completed, failed
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  exit_code INTEGER,
  output TEXT,
  error_output TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_scheduler_tasks_is_active ON scheduler_tasks (is_active);
CREATE INDEX idx_scheduler_executions_task_id ON scheduler_executions (task_id);
CREATE INDEX idx_scheduler_executions_status ON scheduler_executions (status);
```

### MCP Integration
```json
{
  "name": "mcp-scheduler",
  "command": "node",
  "args": ["mcp_servers/mcp-scheduler-server.js"],
  "env": {
    "POSTGRES_URL": "postgresql://postgres:2001@localhost:5432/postgres",
    "NODE_ENV": "development"
  }
}
```

### Scheduler Operations
- **Schedule Tasks**: Create recurring tasks
- **Execute Tasks**: Run scheduled commands
- **Track Execution**: Monitor task completion and failures
- **Retry Logic**: Handle failed tasks with configurable retries

## 6. VS Code MCP Integration

### Integration Overview
VS Code MCP client integrates with PostgreSQL for database operations and development tools.

### Configuration
```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://postgres:2001@localhost:5432/postgres"
      ],
      "env": {}
    }
  }
}
```

### Available Tools
- **query**: Execute SQL queries
- **list_tables**: List all tables in database
- **describe_table**: Get table schema information
- **export_data**: Export query results

### Integration Benefits
- Direct database access from VS Code
- SQL query execution and results viewing
- Schema exploration and documentation
- Development workflow integration

## 7. AG2 Orchestrator Integration

### Integration Overview
The AG2 Orchestrator uses PostgreSQL as its primary data store for agent workflows and state management.

### Technical Details
- **Database**: Central storage for agent workflows
- **Connection**: `postgresql://postgres:2001@localhost:5432/postgres`
- **Schema**: Workflow definitions, execution states, results

### Schema Integration
```sql
-- AG2 Orchestrator Schema
CREATE TABLE workflows (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  definition JSONB NOT NULL,
  status VARCHAR(50) DEFAULT 'draft',  -- draft, active, completed, failed
  created_by VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workflow_executions (
  id SERIAL PRIMARY KEY,
  workflow_id INTEGER REFERENCES workflows(id),
  status VARCHAR(50) DEFAULT 'pending',  -- pending, running, completed, failed
  current_step INTEGER DEFAULT 0,
  input_data JSONB,
  output_data JSONB,
  error_message TEXT,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_workflows_status ON workflows (status);
CREATE INDEX idx_workflow_executions_workflow_id ON workflow_executions (workflow_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions (status);
```

### Integration Flow
```
Agent Request → Workflow Definition → PostgreSQL Execution → Result Processing
    ↓               ↓                   ↓                  ↓
  User Input    Workflow            Database           Agent
  Processing     Storage             Operations         Response
```

## Data Flow and Dependencies

### Data Flow Diagram
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Input Data    │    │   Processing    │    │   Output Data   │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ User Input  │ │    │ │ Vector      │ │    │ │ Search      │ │
│ │ Documents   │ │───▶│ │ Operations  │ │───▶│ │ Results     │ │
│ │ Conversations│ │    │ │ Memory      │ │    │ │ Responses   │ │
│ │ Test Data   │ │    │ │ Processing  │ │    │ │ Reports     │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │                 │
                    │ ┌─────────────┐ │
                    │ │ Vector      │ │
                    │ │ Storage     │ │
                    │ │ Memory      │ │
                    │ │ Management  │ │
                    │ │ Workflow    │ │
                    │ │ Execution   │ │
                    │ └─────────────┘ │
                    └─────────────────┘
```

### Dependencies
- **Database Layer**: PostgreSQL 17.5 with pgvector extension
- **Application Layer**: Node.js applications with MCP servers
- **Integration Layer**: JSON-based APIs and message queues
- **Monitoring Layer**: Performance metrics and logging

## Performance Considerations

### Database Optimization
- **Indexing**: Strategic indexes on frequently queried columns
- **Partitioning**: Consider table partitioning for large datasets
- **Connection Pooling**: Implement connection pooling for better performance
- **Query Optimization**: Regular query analysis and optimization

### System Integration Performance
- **Batch Operations**: Use batch operations for bulk data processing
- **Asynchronous Processing**: Implement async operations for long-running tasks
- **Caching**: Implement caching layers for frequently accessed data
- **Load Balancing**: Consider read replicas for read-heavy workloads

## Security Integration

### Access Control
- **Database Roles**: Separate roles for different applications
- **Connection Security**: SSL/TLS for database connections
- **Network Security**: Firewall rules and VPN access
- **Authentication**: Integration with enterprise authentication systems

### Data Protection
- **Encryption**: Encrypt sensitive data at rest and in transit
- **Backup Security**: Secure backup storage and recovery procedures
- **Audit Logging**: Comprehensive audit logging for all database operations
- **Compliance**: Ensure compliance with relevant data protection regulations

## Monitoring and Alerting

### Database Monitoring
- **Performance Metrics**: Query performance, connection counts, resource usage
- **Health Checks**: Database availability, replication status, disk space
- **Alerting**: Configurable alerts for critical issues
- **Logging**: Comprehensive logging for troubleshooting

### Integration Monitoring
- **API Health**: Monitor API endpoints and response times
- **Data Flow**: Track data flow between systems
- **Error Tracking**: Monitor and alert on integration errors
- **Performance Trends**: Track performance metrics over time

## Future Integration Plans

### Planned Enhancements
1. **Multi-Tenant Support**: Add tenant isolation for multi-tenant applications
2. **Real-time Updates**: Implement real-time data synchronization
3. **Advanced Analytics**: Add advanced analytics and reporting capabilities
4. **Machine Learning Integration**: Integrate ML models for predictive analytics

### Scalability Considerations
1. **Horizontal Scaling**: Implement read replicas for scaling
2. **Sharding**: Consider database sharding for large-scale deployments
3. **Cloud Migration**: Plan for cloud migration and hybrid deployments
4. **Containerization**: Containerize database components for better deployment

## Conclusion

PostgreSQL serves as the central integration point for multiple systems in the paddle-plugin ecosystem. Its robust features, including pgvector extension for vector operations, make it ideal for AI and memory-related applications. The integration points outlined in this document demonstrate the system's architecture and provide a foundation for future enhancements.

**Last Updated**: 2025-08-20  
**Next Review**: [Date]