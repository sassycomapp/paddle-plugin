# IDE Usage Instructions

## Core Workflows
1. **Command Palette Operations**
   - Access MCP tools via `Ctrl+Shift+P` > "MCP: Run Command"
   - Available commands: 
     - `mcp: filesystem` - File operations
     - `mcp: github` - Repository management
     - `mcp: postgres` - Database queries
     - `mcp: brave-search` - Web search integration

2. **Status Bar Management**
   - System status indicators show:
     - MCP server health (green/yellow/red)
     - Podman container status
     - Database connection status
   - Click status bar items for quick actions

## MCP Server Usage
1. **File System Operations**
   ```typescript
   // Example: Read file
   const content = await mcp.filesystem.readFile("path/to/file");
   ```

2. **Database Queries**
   ```typescript
   // Example: Execute query
   const results = await mcp.postgres.query("SELECT * FROM users");
   ```

3. **Semantic Search**
   ```typescript
   // Example: Retrieve similar content
   const results = await mcp.rag.retrieve_similar("query text", 5);
   ```

## Reference Documentation
- [VSCode Commands](IDE Notes/System_start_extension/Startup and usage instructions.md)
- [Command Reference](App notes/mgt_notes/vscode_commands.txt)
- [Status Bar API](IDE Notes/System_start_extension/src/ui/statusBarManager.ts)
- [View Provider Implementation](IDE Notes/System_start_extension/src/ui/systemStartViewProvider.ts)
