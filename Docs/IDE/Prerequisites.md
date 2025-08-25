# System Prerequisites

## Base Requirements
- Node.js v18+ (for VSCode extension and MCP servers)
- Python 3.10+ (required for RAG operations)
- Podman container engine (v4.0+ recommended)
- PostgreSQL (14+ recommended for database operations)

## Environment Setup
1. Podman configuration:
   - Windows: Ensure WSL2 and Podman machine are properly configured
   - Linux: Add user to podman group for rootless operation
   - All platforms: Verify podman-compose is available

2. Database preparation:
   - Create required databases and users in PostgreSQL
   - Set environment variables for database connection
   - Ensure create_memory_tables.sql is accessible

3. VSCode requirements:
   - Install from official Microsoft repository
   - Ensure proper extension development tools are installed
   - Verify access to command palette and status bar APIs

## File References
- [Podman Setup](IDE Notes/Podman.md)
- [PostgreSQL Configuration](IDE Notes/Postgres DB.md)
- [Environment Variables](.env.example)
- [VSCode Requirements](IDE Notes/VSCode MCP Integration.md)
