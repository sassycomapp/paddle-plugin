# PostgreSQL System Documentation

## Overview

This directory contains comprehensive documentation for the PostgreSQL database system in the paddle-plugin ecosystem. PostgreSQL serves as the central data storage and vector database for multiple AI and memory-related components.

## Quick Status

✅ **PostgreSQL System Status**: FULLY OPERATIONAL  
✅ **Service**: Running (postgresql-x64-17)  
✅ **Database**: PostgreSQL 17.5 with pgvector v0.8.0  
✅ **Connectivity**: Working with credentials `postgres:2001`  
✅ **MCP Integration**: All PostgreSQL-dependent servers operational  
✅ **Documentation**: Complete with troubleshooting and integration guides  

## Documentation Structure

### Core Documentation
1. **[PostgreSQL_System_Complete_Documentation.md](./PostgreSQL_System_Complete_Documentation.md)**
   - Complete system overview and configuration
   - Installation details and service management
   - Connection credentials and MCP integration
   - Security and performance considerations

2. **[PostgreSQL_Troubleshooting_and_Maintenance.md](./PostgreSQL_Troubleshooting_and_Maintenance.md)**
   - Comprehensive troubleshooting guide
   - Service management procedures
   - Performance optimization techniques
   - Backup and recovery procedures
   - Security maintenance

3. **[PostgreSQL_Integration_Points.md](./PostgreSQL_Integration_Points.md)**
   - Detailed integration architecture
   - Vector System integration
   - Memory System integration
   - RAG System integration
   - Testing and validation integration
   - Scheduler integration

### Historical Documentation
- **[Postgres installation log.md](./Postgres%20installation%20log.md)** - Installation process log
- **[Postgres installation Plan.md](./Postgres%20installation%20Plan.md)** - Original installation plan
- **[Postgres Reference Sheet.md](./Postgres%20Reference%20Sheet.md)** - Quick reference guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL System                        │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL 17.5 + pgvector v0.8.0                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 Database Core                          │ │
│  │  • Connection Pooling                                  │ │
│  │  • Vector Operations                                   │ │
│  │  • JSONB Storage                                       │ │
│  │  • Full-text Search                                    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 MCP Integration                         │ │
│  │  • PostgreSQL MCP Server                               │ │
│  │  • Agent Memory MCP Server                             │ │
│  │  • Testing Validation MCP Server                       │ │
│  │  • Scheduler MCP Server                                │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                    ┌─────────────────────────────────────────┐
                    │             Connected Systems           │
                    ├─────────────────────────────────────────┤
                    │  • Vector System (Semantic Search)      │
                    │  • Memory System (Agent Memories)       │
                    │  • RAG System (Retrieval-Augmented Gen) │
                    │  • Testing System (Validation)          │
                    │  • AG2 Orchestrator (Workflow Mgmt)     │
                    │  • VS Code MCP Client (Dev Tools)       │
                    └─────────────────────────────────────────┘
```

## Key Features

### Database Capabilities
- **Vector Storage**: pgvector extension for similarity search
- **JSONB Support**: Flexible metadata storage
- **Full-text Search**: Built-in text search capabilities
- **Connection Pooling**: Efficient connection management
- **ACID Compliance**: Data integrity and reliability

### Integration Features
- **MCP Protocol**: Native Model Context Protocol support
- **Multiple Languages**: Python, Node.js, PowerShell integration
- **Real-time Operations**: Asynchronous query processing
- **Monitoring**: Built-in health checks and statistics
- **Backup/Restore**: Automated backup procedures

### Security Features
- **Access Control**: Role-based access management
- **Network Security**: Configurable network access
- **Authentication**: Multiple authentication methods
- **Audit Logging**: Comprehensive logging capabilities
- **Data Encryption**: Support for SSL/TLS encryption

## Connection Information

### Primary Connection
```bash
# Connection String
postgresql://postgres:2001@localhost:5432/postgres

# CLI Connection
psql -h localhost -p 5432 -U postgres -d postgres
```

### Service Details
- **Host**: localhost
- **Port**: 5432
- **Database**: postgres
- **Username**: postgres
- **Password**: 2001
- **Service Name**: postgresql-x64-17
- **Data Directory**: C:\Program Files\PostgreSQL\17\data

## MCP Server Integration

### VS Code Configuration
```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://postgres:2001@localhost:5432/postgres"]
    }
  }
}
```

### Application Configuration
```json
{
  "name": "agent-memory",
  "command": "node",
  "args": ["mcp_servers/agent-memory/index.js"],
  "env": {
    "DATABASE_URL": "postgresql://postgres:2001@localhost:5432/postgres"
  }
}
```

## Usage Examples

### Basic Operations
```sql
-- Check database version
SELECT version();

-- Test vector extension
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Create vector table
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  content TEXT,
  embedding vector(384)
);

-- Vector similarity search
SELECT content, embedding <=> '[0.1,0.2,0.3]'::vector as distance
FROM documents
ORDER BY distance
LIMIT 5;
```

### Backup Operations
```bash
# Create backup
pg_dump -U postgres -Fc -f "backup_$(date +%Y%m%d).dump" postgres

# Restore backup
pg_restore -d postgres backup_20250820.dump
```

## Maintenance Procedures

### Daily Tasks
- Monitor database performance
- Check backup completion
- Review error logs
- Update statistics

### Weekly Tasks
- Rebuild indexes
- Analyze tables
- Review security settings
- Test backup restoration

### Monthly Tasks
- Performance tuning
- Security audit
- Update statistics
- Review capacity planning

## Troubleshooting

### Common Issues
1. **Service not starting**: Check Windows Event Viewer
2. **Connection refused**: Verify service is running
3. **Authentication failed**: Check credentials and pg_hba.conf
4. **Vector operations failing**: Verify pgvector extension

### Quick Commands
```powershell
# Check service status
Get-Service -Name postgresql-x64-17

# Start/stop service
Start-Service -Name postgresql-x64-17
Stop-Service -Name postgresql-x64-17

# Test connectivity
psql -h localhost -p 5432 -U postgres -d postgres -c "SELECT 1;"
```

## Support and Resources

### Documentation
- Complete system documentation: `PostgreSQL_System_Complete_Documentation.md`
- Troubleshooting guide: `PostgreSQL_Troubleshooting_and_Maintenance.md`
- Integration points: `PostgreSQL_Integration_Points.md`

### Scripts and Tools
- Database integration: `scripts/database_integration.py`
- Health monitoring: `scripts/monitoring.py`
- Backup automation: Included in database integration script

### External Resources
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- pgvector Extension: https://github.com/pgvector/pgvector
- MCP Protocol: https://modelcontextprotocol.io/

## System Requirements

### Hardware Requirements
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: Minimum 10GB free space
- **CPU**: Modern multi-core processor

### Software Requirements
- **Operating System**: Windows 10/11
- **PostgreSQL**: 17.5 or later
- **Node.js**: 16+ for MCP servers
- **Python**: 3.8+ for integration scripts

## Version Information

- **PostgreSQL Version**: 17.5
- **pgvector Extension**: 0.8.0
- **MCP Protocol**: Compatible with v0.5.0+
- **Last Updated**: 2025-08-20

## Contributing

To contribute to this documentation:
1. Follow the established format and structure
2. Update version information when changes are made
3. Add troubleshooting solutions for new issues
4. Keep integration documentation current

## License

This documentation is part of the paddle-plugin project and follows the same license terms.

---

**For immediate assistance, refer to the troubleshooting guide or contact the system administrator.**