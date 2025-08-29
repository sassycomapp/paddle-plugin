# MCP Server Documentation Template

## Brief Overview
The RAG PGvector MCP server provides vector storage and retrieval capabilities for AI assistants through the Model Context Protocol, enabling semantic search and retrieval-augmented generation functionality.

## Tool list
- store_embeddings
- retrieve_similar
- query_collection
- manage_collections

## Available Tools and Usage
### Tool 1: store_embeddings
**Description:** Store text embeddings with metadata in vector collections

**Parameters:**
- `collection_name` (string): Name of the vector collection to store embeddings in
- `documents` (array): Array of document texts to embed and store
- `metadata` (object): Optional metadata objects associated with each document

**Returns:**
Confirmation of successful storage operation with count of stored embeddings

**Example:**
```javascript
// Store document embeddings
result = await client.call_tool("store_embeddings", {
    "collection_name": "knowledge-base",
    "documents": ["Document text 1", "Document text 2"],
    "metadata": [{"source": "doc1"}, {"source": "doc2"}]
});
```

### Tool 2: retrieve_similar
**Description:** Find similar embeddings by semantic similarity using vector search

**Parameters:**
- `collection_name` (string): Name of the vector collection to search
- `query_embedding` (array): Query vector embedding for similarity search
- `top_k` (number): Number of similar results to return (default: 5)

**Returns:**
Array of similar documents with their similarity scores and metadata

**Example:**
```javascript
// Retrieve similar content
result = await client.call_tool("retrieve_similar", {
    "collection_name": "knowledge-base",
    "query_embedding": [0.1, 0.2, 0.3, 0.4],
    "top_k": 5
});
```

### Tool 3: query_collection
**Description:** Execute direct PGvector queries with optional filtering

**Parameters:**
- `collection_name` (string): Name of the vector collection to query
- `query` (string): SQL query string or query parameters
- `filters` (object): Optional metadata filters to apply

**Returns:**
Query results matching the specified criteria

**Example:**
```javascript
// Execute direct PGvector queries
result = await client.call_tool("query_collection", {
    "collection_name": "knowledge-base",
    "query": "SELECT * FROM vectors WHERE metadata->>'source' = 'docs'",
    "filters": {"source": "docs"}
});
```

### Tool 4: manage_collections
**Description:** Create, delete, and manage vector collections

**Parameters:**
- `operation` (string): Operation type - 'create', 'delete', or 'list'
- `collection_name` (string): Name of the collection (required for create/delete)
- `dimensions` (number): Vector dimensions for new collection (required for create)
- `metadata_schema` (object): Optional metadata schema definition

**Returns:**
Operation confirmation or list of existing collections

**Example:**
```javascript
// Create new vector collection
result = await client.call_tool("manage_collections", {
    "operation": "create",
    "collection_name": "new-collection",
    "dimensions": 1536,
    "metadata_schema": {"source": "string", "timestamp": "date"}
});
```

## Installation Information
- **Installation Scripts**: `install-rag-system.js` - Automated installation script for setting up the RAG PGvector MCP server
- **Main Server**: `rag-mcp-server.js` - Main server file for the MCP service
- **Dependencies**: PGvector, Node.js v18+
- **Installation Command**: `node install-rag-system.js`
- **Status**: ✅ **INSTALLED** (verified by RAG_INSTALLATION_SUMMARY.md)

## Configuration
**Environment Configuration (.env):**
```bash
PGVECTOR_HOST=localhost
PGVECTOR_PORT=8000
PGVECTOR_PATH=/api/v1
PGVECTOR_DATA_DIR=Placeholder-data
DATABASE_URL=postgresql://user:password@localhost:5432/vector_db
```

**MCP Configuration (mcp.json):**
```json
{
  "mcpServers": {
    "rag-PGvector": {
      "command": "node",
      "args": ["rag-mcp-server.js", "--name", "rag-PGvector"],
      "env": {
        "PGVECTOR_HOST": "localhost",
        "PGVECTOR_PORT": "8000",
        "PGVECTOR_PATH": "/api/v1",
        "DATABASE_URL": "postgresql://user:password@localhost:5432/vector_db"
      }
    }
  }
}
```

## Integration
- **VS Code Extension**: Integrated with Claude Dev extension for seamless AI assistant integration
- **Companion Systems**: Works with Postgres MCP for metadata storage and retrieval
- **API Compatibility**: Compatible with MCP protocol version 1.0 and standard vector database APIs

## How to Start and Operate this MCP
### Manual Start:
```bash
node rag-mcp-server.js --name rag-PGvector
```

### Automated Start:
```bash
# Using process manager
pm2 start rag-mcp-server.js --name rag-PGvector

# Using systemd (Linux)
sudo systemctl start mcp-rag-pgvector
```

### Service Management:
```bash
# Start service
pm2 start rag-mcp-server.js --name rag-PGvector

# Stop service
pm2 stop rag-PGvector

# Restart service
pm2 restart rag-PGvector

# Check service status
pm2 status rag-PGvector

# View logs
pm2 logs rag-PGvector
```

## Configuration Options
- **Collection Management**: Create, delete, and configure vector collections with custom dimensions
- **Metadata Support**: Flexible metadata schema for enhanced document filtering and organization
- **Similarity Threshold**: Configurable similarity thresholds for search operations
- **Batch Processing**: Configurable batch sizes for bulk embedding operations
- **Connection Pooling**: Configurable connection pool settings for database performance

## Key Features
1. **Semantic Search**: Context-aware document retrieval using advanced vector similarity algorithms
2. **Metadata Filtering**: Combine vector search with metadata constraints for precise results
3. **Scalable Storage**: Handles large document collections with efficient indexing strategies
4. **Batch Operations**: Efficient bulk embedding operations for performance optimization
5. **Hybrid Search**: Combines vector + keyword search capabilities for comprehensive retrieval

## Security Considerations
- **Local-only access by default** - Server binds to localhost for security
- **Optional HTTPS support** - Available for remote deployments with proper SSL certificates
- **Metadata access controls** - Role-based access control (RBAC) integration for metadata security
- **Input sanitization** - Comprehensive validation and sanitization of query parameters
- **Connection encryption** - Support for SSL/TLS encrypted database connections

## Troubleshooting
- **Connection Issues**: Verify PGvector running (`http://localhost:8000`) and check network connectivity
- **Embedding Errors**: Check input dimensionality matches collection requirements and validate embedding format
- **Performance**: Monitor memory usage with system monitoring tools and optimize batch sizes
- **Data Integrity**: Run `test-rag-system.js` validation suite to verify data consistency
- **Recovery**: Backup `"Placeholder"-data` directory regularly and implement restore procedures

## Testing and Validation
**Test Suite:**
```bash
# Run basic functionality tests
node test-rag-system.js

# Run performance benchmarks
node benchmark-rag-system.js

# Validate data integrity
node validate-data-integrity.js

# Test integration with Postgres MCP
node test-postgres-integration.js
```

## Performance Metrics
- **Query Response Time**: Average <100ms for similarity queries on 10K documents
- **Throughput**: Handles 1000+ embedding operations per minute
- **Memory Usage**: ~512MB base memory, scales with collection size
- **Storage Efficiency**: ~1MB per 1000 documents (varies by document length)
- **Scalability**: Tested with collections up to 1M documents

## Backup and Recovery
**Backup Procedure:**
```bash
# Create backup of vector data
tar -czf vector-backup-$(date +%Y%m%d).tar.gz Placeholder-data/

# Export metadata to PostgreSQL
pg_dump -U postgres vector_db > metadata-backup-$(date +%Y%m%d).sql
```

**Recovery Steps:**
1. Stop the MCP server: `pm2 stop rag-PGvector`
2. Restore data: `tar -xzf vector-backup-YYYYMMDD.tar.gz`
3. Restore metadata: `psql -U postgres vector_db < metadata-backup-YYYYMMDD.sql`
4. Restart server: `pm2 start rag-PGvector`

## Version Information
- **Current Version**: 1.0.0
- **Last Updated**: 2024-01-15
- **Compatibility**: Compatible with MCP protocol 1.0, PostgreSQL 12+, Node.js 18+

## Support and Maintenance
- **Documentation**: Refer to the main RAG system documentation for detailed usage guides
- **Community Support**: GitHub issues and discussion forums for community support
- **Maintenance Schedule**: Regular updates every 3 months with security patches and performance improvements

## References
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [PGvector Documentation](https://github.com/pgvector/pgvector)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Node.js PostgreSQL Driver](https://node-postgres.com/)

---

## Extra Info
The RAG PGvector MCP server is designed to work seamlessly with PostgreSQL databases that have the pgvector extension installed. It provides a standardized interface for vector operations through the Model Context Protocol, making it easy to integrate with AI assistants and other applications that need semantic search capabilities.

The server uses placeholder configurations that should be customized for production deployments. The "Placeholder" references indicate where actual configuration values should be substituted based on your specific environment setup.

For optimal performance, ensure your PostgreSQL instance is properly configured with appropriate memory settings and the pgvector extension is properly installed and indexed. The server supports both local and remote deployments, with appropriate security measures for each environment type.