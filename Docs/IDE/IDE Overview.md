# IDE Overview

## System Architecture
The VSCode Agentic IDE system provides an integrated development environment with enhanced AI capabilities through Model Context Protocol (MCP) servers. Key architectural components include:

- **Core Integration**: VSCode extension with MCP protocol support
- **Container Management**: Podman-based deployment (no Docker support)
- **Database**: PostgreSQL for structured data storage
- **RAG System**: PGvector for vector-based semantic search

## Key Caveats
- System files must remain in their original locations to maintain functionality
- Documentation files should be consolidated into this Docs structure
- Avoid duplication by referencing system files in their original locations
- All documentation must be rewritten with reduced verbosity and logical organization
