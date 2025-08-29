# MCP Server Documentation Template

## Brief Overview
The Snap Windows MCP Server provides window management capabilities for Windows systems, allowing you to arrange, snap, and manage application windows programmatically. This server enables AI assistants to control window layouts, snap windows to specific positions, and save/apply window configurations, enhancing productivity through automated workspace management.

## Tool list
- arrange_windows
- snap_to_position
- manage_layouts

## Available Tools and Usage
### Tool 1: arrange_windows
**Description:** Arrange windows in predefined layouts for optimal workspace organization and multitasking efficiency.

**Parameters:**
- `layout` (string, required): Layout type for window arrangement
  - `2x2`: Four windows in a 2x2 grid
  - `3x3`: Nine windows in a 3x3 grid
  - `left-right`: Two windows side by side
  - `top-bottom`: Two windows stacked vertically
  - `maximize-all`: Maximize all visible windows

**Returns:**
Confirmation message with layout type and number of windows arranged

**Example:**
```javascript
// Arrange windows in a 2x2 grid
result = await client.call_tool("arrange_windows", {
    "layout": "2x2"
});
```

### Tool 2: snap_to_position
**Description:** Snap a specific window to a predefined position on the screen for precise window placement and organization.

**Parameters:**
- `windowTitle` (string, required): Title of the window to snap (case-insensitive)
- `position` (string, required): Position to snap to
  - `left`, `right`, `top`, `bottom`
  - `top-left`, `top-right`, `bottom-left`, `bottom-right`
  - `center`

**Returns:**
Confirmation message with window title, snapped position, and dimensions

**Example:**
```javascript
// Snap VS Code to the left side
result = await client.call_tool("snap_to_position", {
    "windowTitle": "Visual Studio Code",
    "position": "left"
});
```

### Tool 3: manage_layouts
**Description:** Save or apply window layouts for workspace persistence and quick configuration switching.

**Parameters:**
- `action` (string, required): Action to perform
  - `save`: Save current window layout configuration
  - `apply`: Apply a previously saved layout
- `name` (string, required): Name of the layout to save or apply

**Returns:**
Confirmation message with action performed, layout name, and window count

**Example:**
```javascript
// Save current layout
result = await client.call_tool("manage_layouts", {
    "action": "save",
    "name": "development-setup"
});

// Apply saved layout
result = await client.call_tool("manage_layouts", {
    "action": "apply",
    "name": "development-setup"
});
```

## Installation Information
- **Installation Scripts**: None required - server is pre-installed
- **Main Server**: `mcp_servers/snap-mcp-server.js` - Main server file for the MCP window management service
- **Dependencies**: 
  - Node.js runtime
  - PowerShell for Windows window management operations
  - MCP SDK for Node.js
- **Installation Command**: Already installed and operational
- **Status**: ✅ **INSTALLED** (pre-installed and configured)

## Configuration
**Environment Configuration (.env):**
```bash
# Window Management Configuration
SNAP_LAYOUTS_DIR=%USERPROFILE%\.snap-layouts
SNAP_DEFAULT_LAYOUT=2x2
SNAP_WINDOW_TIMEOUT=5000
SNAP_POWERShell_PATH=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe
SNAP_LOG_LEVEL=info
```

**MCP Configuration (mcp.json):**
```json
{
  "mcpServers": {
    "snap-windows": {
      "command": "node",
      "args": ["mcp_servers/snap-mcp-server.js"],
      "env": {
        "SNAP_LAYOUTS_DIR": "%USERPROFILE%\\.snap-layouts",
        "SNAP_DEFAULT_LAYOUT": "2x2",
        "SNAP_WINDOW_TIMEOUT": "5000",
        "SNAP_LOG_LEVEL": "info"
      }
    }
  }
}
```

## Integration
- **VS Code Extension**: Integrated with Claude Dev extension and KiloCode environment
- **Companion Systems**: Works with other MCP servers for workflow automation and productivity enhancement
- **API Compatibility**: Compatible with MCP protocol version 1.0 and standard window management APIs
- **Platform Integration**: Deep integration with Windows window management system via PowerShell

## How to Start and Operate this MCP
### Manual Start:
```bash
cd mcp_servers
node snap-mcp-server.js
```

### Automated Start:
```bash
# Using process manager
pm2 start snap-mcp-server.js --name snap-windows

# Using systemd (Windows equivalent)
# Create Windows service or use Task Scheduler
```

### Service Management:
```bash
# Start service
pm2 start snap-mcp-server.js --name snap-windows

# Stop service
pm2 stop snap-windows

# Restart service
pm2 restart snap-windows

# Check service status
pm2 status snap-windows

# View logs
pm2 logs snap-windows
```

## Configuration Options
- **Layouts Directory**: Configurable directory for storing saved layouts (default: `%USERPROFILE%\.snap-layouts`)
- **Default Layout**: Configurable default layout for quick arrangement
- **Window Timeout**: Configurable timeout for window operations (default: 5000ms)
- **PowerShell Path**: Configurable path to PowerShell executable
- **Log Level**: Configurable logging verbosity (debug, info, warn, error)

## Key Features
1. **Window Arrangement**: Support for multiple predefined layouts (2x2, 3x3, side-by-side, stacked)
2. **Precise Positioning**: Snap windows to specific screen positions with pixel-perfect accuracy
3. **Layout Management**: Save and apply window layouts for workspace persistence
4. **PowerShell Integration**: Leverage Windows PowerShell for robust window management
5. **Real-time Operations**: Near-instant window operations with minimal performance impact

## Security Considerations
- **Execution Policy**: Ensure PowerShell execution policy allows script execution
- **Administrator Privileges**: Recommend running as administrator for optimal window management
- **Window Title Matching**: Implement proper window title validation and case-insensitive matching
- **Access Control**: Restrict access to sensitive window operations
- **Input Validation**: Validate all window titles and position parameters before execution

## Troubleshooting
- **PowerShell Issues**: Verify PowerShell execution policy allows script execution (`Set-ExecutionPolicy RemoteSigned`)
- **Window Not Found**: Ensure window titles match exactly (case-insensitive) and window is visible
- **Permission Problems**: Run as administrator for best results with window management
- **Layout Save Failures**: Check directory permissions and available disk space
- **Performance Issues**: Monitor system resources and adjust timeout settings if needed

## Testing and Validation
**Test Suite:**
```bash
# Basic server test
node mcp_servers/Tests/test-snap-mcp.js

# Functionality test
node mcp_servers/Tests/test-snap-functionality.js

# Integration test
node mcp_servers/Tests/test-snap-integration.js

# Performance test
node mcp_servers/Tests/test-snap-performance.js
```

## Performance Metrics
- **Operation Speed**: Near-instant window operations (<100ms for most operations)
- **Memory Usage**: ~16MB base memory, minimal impact during operations
- **CPU Usage**: Low CPU utilization during window management operations
- **Concurrent Operations**: Supports multiple simultaneous window operations
- **Layout Storage**: Efficient JSON-based layout storage with fast load/save times
- **Window Detection**: Fast window title matching and identification

## Backup and Recovery
**Backup Procedure:**
```bash
# Backup layouts directory
xcopy "%USERPROFILE%\.snap-layouts" "backup_snap_layouts_$(date +%Y%m%d)" /E /I /H

# Export configuration
copy "%USERPROFILE%\.snap-layouts\config.json" "backup_config_$(date +%Y%m%d).json"
```

**Recovery Steps:**
1. Stop the MCP server: `pm2 stop snap-windows`
2. Restore layouts: `xcopy "backup_snap_layouts_YYYYMMDD" "%USERPROFILE%\.snap-layouts" /E /I /H`
3. Restore configuration: `copy "backup_config_YYYYMMDD.json" "%USERPROFILE%\.snap-layouts\config.json"`
4. Restart server: `pm2 start snap-mcp-server.js --name snap-windows`

## Version Information
- **Current Version**: 1.0.0
- **Platform**: Windows only
- **Node.js Version**: v16+ recommended
- **PowerShell Version**: PowerShell 5.1 or later
- **Last Updated**: August 2025
- **Compatibility**: Windows 10/11, MCP protocol 1.0

## Support and Maintenance
- **Documentation**: Refer to server logs and this documentation for detailed usage
- **Community Support**: GitHub issues and discussion forums for community support
- **Maintenance Schedule**: Regular updates every 3 months with security patches and performance improvements
- **Log Analysis**: Use built-in logging for troubleshooting and monitoring

## References
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [Windows PowerShell Documentation](https://docs.microsoft.com/powershell/)
- [Windows Window Management API](https://docs.microsoft.com/windows/win32/winmsg/window-features)
- [Node.js Process Management](https://nodejs.org/api/process.html)

---

## Extra Info
The Snap Windows MCP Server is specifically designed for Windows systems and provides comprehensive window management capabilities through PowerShell integration. It enables AI assistants to programmatically control window layouts, snap windows to specific positions, and manage workspace configurations efficiently.

Key implementation details:
- **Platform Specific**: Windows-only implementation leveraging PowerShell for window management
- **PowerShell Integration**: Uses PowerShell cmdlets for robust window detection and manipulation
- **Layout Persistence**: JSON-based layout storage in user profile directory
- **Real-time Operations**: Near-instant response times for window management tasks
- **Error Handling**: Comprehensive error handling with detailed logging and recovery mechanisms
- **Performance Optimized**: Minimal resource usage with efficient window detection and positioning

The server is particularly valuable for productivity automation, allowing AI assistants to organize workspaces, apply saved layouts, and manage multiple applications efficiently. Its integration with the MCP protocol makes it easily accessible to AI assistants and automation tools running in the Windows environment.