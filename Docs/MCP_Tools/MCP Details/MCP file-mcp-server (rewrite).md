# MCP Server Documentation Template

## Brief Overview
The MCP File Server provides filesystem access capabilities through the Model Context Protocol, allowing AI assistants to read, write, and manage files and directories on the local system. It enables secure file operations within explicitly configured directories, ensuring controlled access to the filesystem.

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
**Description:** Reads the contents of a file from the allowed paths.

**Parameters:**
- `path` (string): The path to the file to be read, relative to allowed directories

**Returns:**
File contents as a string

**Example:**
```javascript
// Example usage
result = await client.call_tool("read_file", {
    "path": "src/main.js"
});
```

### Tool 2: write_file
**Description:** Writes content to a file in the allowed paths.

**Parameters:**
- `path` (string): The path where the file should be written, relative to allowed directories
- `content` (string): The content to write to the file

**Returns:**
Success confirmation with file path

**Example:**
```javascript
// Example usage
result = await client.call_tool("write_file", {
    "path": "output.txt",
    "content": "Hello World"
});
```

### Tool 3: create_directory
**Description:** Creates a new directory in the allowed paths.

**Parameters:**
- `path` (string): The path of the directory to create, relative to allowed directories

**Returns:**
Success confirmation with directory path

**Example:**
```javascript
// Example usage
result = await client.call_tool("create_directory", {
    "path": "new_folder"
});
```

### Tool 4: list_directory
**Description:** Lists the contents of a directory in the allowed paths.

**Parameters:**
- `path` (string): The path of the directory to list, relative to allowed directories

**Returns:**
Array of file and directory names in the specified directory

**Example:**
```javascript
// Example usage
result = await client.call_tool("list_directory", {
    "path": "src/"
});
```

### Tool 5: get_file_info
**Description:** Retrieves metadata information about a file or directory.

**Parameters:**
- `path` (string): The path of the file or directory, relative to allowed directories

**Returns:**
File/directory metadata including size, modification time, and type

**Example:**
```javascript
// Example usage
result = await client.call_tool("get_file_info", {
    "path": "src/main.js"
});
```

### Tool 6: search_files
**Description:** Searches for files matching a pattern in the allowed paths.

**Parameters:**
- `path` (string): The directory path to search within, relative to allowed directories
- `pattern` (string): The file pattern to search for (e.g., "*.js")

**Returns:**
Array of file paths matching the search pattern

**Example:**
```javascript
// Example usage
result = await client.call_tool("search_files", {
    "path": "src/",
    "pattern": "*.js"
});
```

### Tool 7: remove_directory
**Description:** Removes a directory and its contents from the allowed paths.

**Parameters:**
- `path` (string): The path of the directory to remove, relative to allowed directories

**Returns:**
Success confirmation with directory path

**Example:**
```javascript
// Example usage
result = await client.call_tool("remove_directory", {
    "path": "old_folder"
});
```

## Installation Information
- **Installation Scripts**: `npx -y @modelcontextprotocol/server-filesystem [allowed-paths...]`
- **Main Server**: `@modelcontextprotocol/server-filesystem` package
- **Dependencies**: Node.js and npm (comes with package installation)
- **Status**: ✅ **INSTALLED** and configured in `.vscode/mcp.json`

## Configuration
**Environment Configuration (.env):**
```bash
# No specific environment variables required for filesystem MCP server
# Configuration is handled through MCP configuration file
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
- **VS Code Extension**: Fully integrated with Claude Dev extension
- **Companion Systems**: Works with any MCP-compatible client application
- **API Compatibility**: Compatible with Model Context Protocol v1.0+

## How to Start and Operate this MCP
### Manual Start:
```bash
# Start the filesystem MCP server manually
npx -y @modelcontextprotocol/server-filesystem . /tmp
```

### Automated Start:
```bash
# The server starts automatically when VS Code with Claude Dev extension is launched
# No additional startup scripts required
```

### Service Management:
```bash
# No service management commands required for this MCP server
# Server lifecycle is managed by the MCP client application
```

## Configuration Options
- **Allowed Paths**: Configure specific directories that the MCP server can access
- **Path Validation**: Server validates all file operations against allowed paths
- **Security Model**: No access outside explicitly configured directories
- **Cross-platform**: Works consistently across Windows, macOS, and Linux

## Key Features
1. **Secure File Access**: Restricted to configured paths only
2. **Real-time Operations**: Immediate file system changes reflected in MCP responses
3. **Cross-platform**: Works on Windows, macOS, and Linux with consistent behavior
4. **Path Validation**: Prevents access outside allowed directories
5. **Error Handling**: Comprehensive error messages for file operations
6. **Multiple File Operations**: Support for read, write, create, list, search, and delete operations

## Security Considerations
- Only explicitly configured paths are accessible (current directory and /tmp)
- No access to system directories or sensitive locations
- All operations are logged and auditable through the MCP client
- File permissions are respected based on user privileges
- Path validation prevents directory traversal attacks

## Troubleshooting
- **Permission Errors**: Ensure VS Code has necessary file system permissions for the configured paths
- **Path Not Found**: Verify paths are correctly configured in mcp.json
- **Server Not Starting**: Check Node.js and npm are properly installed and accessible
- **Access Denied**: Confirm the requested path is within the allowed directories
- **MCP Connection Issues**: Verify MCP client configuration and network connectivity

## Testing and Validation
**Test Suite:**
```bash
# Test file reading functionality
echo "test content" > test_file.txt
read_file "test_file.txt"

# Test file writing functionality
write_file "test_output.txt" "Hello World"
cat test_output.txt

# Test directory operations
list_directory "."
create_directory "test_dir"
list_directory "test_dir"
remove_directory "test_dir"

# Cleanup
rm test_file.txt test_output.txt
```

## Performance Metrics
- **File Operations**: Fast synchronous file operations suitable for real-time AI assistance
- **Memory Usage**: Minimal memory footprint, processes files as streams when possible
- **Scalability**: Handles files of various sizes efficiently
- **Response Time**: Sub-second response time for typical file operations
- **Concurrent Operations**: Supports multiple concurrent file operations

## Backup and Recovery
- **Data Backup**: Regular backups of important files should be maintained separately
- **Configuration Backup**: Keep copies of mcp.json configuration files
- **Recovery Procedures**: Restore from system backups in case of filesystem corruption
- **Version Control**: Consider using version control for important project files

## Version Information
- **Current Version**: Uses latest stable version of @modelcontextprotocol/server-filesystem
- **Last Updated**: Configuration updated when MCP client settings are modified
- **Compatibility**: Compatible with MCP protocol v1.0+ and major Node.js versions

## Support and Maintenance
- **Documentation**: Refer to Model Context Protocol documentation for detailed usage
- **Community Support**: MCP community resources and issue tracking available
- **Maintenance Schedule**: Updates follow the MCP server package release cycle
- **Error Logging**: Check MCP client logs for detailed error information

## References
- [Model Context Protocol Documentation](https://github.com/modelcontextprotocol/sdk)
- [@modelcontextprotocol/server-filesystem Package](https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem)
- [MCP Client Integration Guide](https://github.com/modelcontextprotocol/protocol)

---

## Extra Info
The MCP File Server implementation uses the official `@modelcontextprotocol/server-filesystem` package from the Model Context Protocol ecosystem. This provides a standardized and secure way for AI assistants to interact with the local filesystem while maintaining strict access controls.

The server is configured to allow access to the current project directory (`.`) and the temporary directory (`/tmp`), providing a balance between functionality and security. All file operations are validated against these allowed paths to prevent unauthorized access to system files.

Integration with the Claude Dev extension enables seamless file operations within the development environment, making it easier for AI assistants to read, write, and manage project files as part of the development workflow.