# MCP Server Documentation Template

## Brief Overview
The MCP Filesystem Server provides file system access capabilities through the Model Context Protocol. It enables file operations within the defined working directory, including file reading/writing, directory listing, path resolution, and file metadata access.

## Tool list
- read_file
- write_file
- create_directory
- list_directory
- get_file_info
- search_files
- remove_directory

## Available Tools and Usage
### Tool 1: read_file
**Description:** Reads the contents of a file from the filesystem

**Parameters:**
- `path` (string): The path to the file to be read

**Returns:**
File contents as a string

**Example:**
```javascript
// Example usage
result = await client.call_tool("read_file", {
    "path": "./docs/example.txt"
});
```

### Tool 2: write_file
**Description:** Writes content to a file in the filesystem

**Parameters:**
- `path` (string): The path to the file to be written
- `content` (string): The content to write to the file

**Returns:**
Confirmation of successful write operation

**Example:**
```javascript
// Example usage
result = await client.call_tool("write_file", {
    "path": "./docs/example.txt",
    "content": "Hello, World!"
});
```

### Tool 3: create_directory
**Description:** Creates a new directory in the filesystem

**Parameters:**
- `path` (string): The path of the directory to create

**Returns:**
Confirmation of successful directory creation

**Example:**
```javascript
// Example usage
result = await client.call_tool("create_directory", {
    "path": "./docs/new-folder"
});
```

### Tool 4: list_directory
**Description:** Lists the contents of a directory

**Parameters:**
- `path` (string): The path of the directory to list

**Returns:**
Array of file and directory names in the specified path

**Example:**
```javascript
// Example usage
result = await client.call_tool("list_directory", {
    "path": "./docs"
});
```

### Tool 5: get_file_info
**Description:** Retrieves metadata information about a file or directory

**Parameters:**
- `path` (string): The path of the file or directory to inspect

**Returns:**
File metadata including size, modification time, and type

**Example:**
```javascript
// Example usage
result = await client.call_tool("get_file_info", {
    "path": "./docs/example.txt"
});
```

### Tool 6: search_files
**Description:** Searches for files matching a pattern in the filesystem

**Parameters:**
- `pattern` (string): Search pattern for file names
- `path` (string): The directory to search within (optional)

**Returns:**
Array of file paths matching the search pattern

**Example:**
```javascript
// Example usage
result = await client.call_tool("search_files", {
    "pattern": "*.txt",
    "path": "./docs"
});
```

### Tool 7: remove_directory
**Description:** Removes a directory from the filesystem

**Parameters:**
- `path` (string): The path of the directory to remove

**Returns:**
Confirmation of successful directory removal

**Example:**
```javascript
// Example usage
result = await client.call_tool("remove_directory", {
    "path": "./docs/temp-folder"
});
```

## Installation Information
- **Installation Scripts**: `node mcp_servers/install-mcp-server.js filesystem`
- **Main Server**: `mcp_servers/install-mcp-server.js`
- **Dependencies**: No additional dependencies required
- **Status**: ✅ Working (as per MCP Inspection Report)

## Configuration
**Environment Configuration (.env):**
```bash
# No environment variables required for filesystem MCP server
```

**MCP Configuration (mcp.json):**
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        ".",
        "/tmp"
      ],
      "env": {}
    }
  }
}
```

## Integration
- **VS Code Extension**: Works with VS Code MCP extension
- **Companion Systems**: Supports direct command-line execution
- **API Compatibility**: Compatible with environment variables via `.env`

## How to Start and Operate this MCP
### Manual Start:
```bash
node mcp_servers/install-mcp-server.js filesystem
```

### Automated Start:
```bash
# The server can be started via the MCP configuration in VS Code
# No additional automated startup scripts required
```

### Service Management:
```bash
# Start the server
node mcp_servers/install-mcp-server.js filesystem

# Test the server functionality
npx -y @modelcontextprotocol/server-filesystem .
```

## Configuration Options
The filesystem MCP server uses the current working directory (`c:/_1mybizz/paddle-plugin`) as the root directory and allows access to explicitly configured directories only. No manual configuration is needed as it automatically configures in `.vscode/mcp.json`.

## Key Features
1. Local filesystem access within defined working directory
2. Secure path resolution with restricted access
3. File operation monitoring and error handling
4. Automatic configuration integration
5. Lightweight implementation with no additional dependencies

## Security Considerations
- Path restriction to only configured directories (current directory and `/tmp`)
- Directory validation before allowing access
- Clear error messages for unauthorized access attempts
- Secure MCP Filesystem Server running on stdio with proper security messaging

## Troubleshooting
- **Common Issue 1**: Invalid path access - Server provides clear error messages for unauthorized access
- **Common Issue 2**: Directory not found - Validate paths are within allowed directories
- **Debug Mode**: Server displays "Secure MCP Filesystem Server running on stdio" message on startup

## Testing and Validation
**Test Suite:**
```bash
# Test command to verify functionality
npx -y @modelcontextprotocol/server-filesystem .

# Node.js test script
node mcp_servers/Tests/test-filesystem-mcp.js

# Windows batch test
mcp_servers/Tests/verify-filesystem-mcp.bat

# PowerShell test
mcp_servers/Tests/verify-filesystem-mcp.ps1
```

## Performance Metrics
- Lightweight implementation with minimal resource requirements
- Fast file operations within the allowed directory structure
- Efficient path resolution and validation

## Backup and Recovery
Standard filesystem backup procedures apply. No special backup requirements for the MCP server itself.

## Version Information
- **Current Version**: Compatible with Node.js v22.15.0 and npm 11.3.0
- **Last Updated**: July 30, 2025
- **Compatibility**: Compatible with MCP standard and VS Code extension

## Support and Maintenance
- **Documentation**: Additional test scripts available in `mcp_servers/Tests/`
- **Community Support**: Works with standard MCP protocol
- **Maintenance Schedule**: No special maintenance required beyond standard filesystem maintenance

## References
- MCP Protocol Documentation
- VS Code MCP Extension Documentation
- `@modelcontextprotocol/server-filesystem` package documentation

---

## Template Usage Guidelines

### Required Sections:
1. **Brief Overview** - Must be concise and informative
2. **Available Tools and Usage** - Complete tool inventory with examples
3. **Installation Information** - Clear installation steps
4. **Configuration** - Environment and MCP configuration
5. **How to Start and Operate this MCP** - Startup and operation procedures

### Optional Sections:
- Integration details (if applicable)
- Security considerations (if applicable)
- Troubleshooting (if applicable)
- Performance metrics (if applicable)
- Backup and recovery (if applicable)

### Formatting Standards:
- Use consistent code block formatting
- Include parameter types in tool descriptions
- Provide working examples for all tools
- Use clear, descriptive section headings
- Include file paths relative to project root

### Special Notes:
- Replace bracketed placeholders `[like this]` with actual values
- Maintain consistent terminology across all MCP documentation
- Include version-specific information when applicable
- Document platform-specific requirements and differences

### Extra Info
The MCP filesystem server is fully functional and properly configured. It successfully starts and runs without errors, accepts configuration parameters correctly, provides secure filesystem access, integrates properly with VS Code MCP configuration, and follows security best practices with path restrictions. Test files created include `mcp_servers/Tests/test-filesystem-mcp.js`, `mcp_servers/Tests/verify-filesystem-mcp.bat`, and `mcp_servers/Tests/verify-filesystem-mcp.ps1`. The server is ready for use with the Claude Dev extension in VS Code, and filesystem operations can be performed through the MCP tools interface.