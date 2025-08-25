# Snap Windows MCP Server

## Overview
The Snap Windows MCP Server provides window management capabilities for Windows systems, allowing you to arrange, snap, and manage application windows programmatically.

## Installation
The server is already installed and configured in the project. It's located at `mcp_servers/snap-mcp-server.js`.

## Configuration
The server is configured in `.vscode/mcp.json` under the `snap-windows` key:

```json
"snap-windows": {
  "command": "node",
  "args": ["mcp_servers/snap-mcp-server.js"],
  "env": {}
}
```

## Available Tools

### 1. arrange_windows
Arrange windows in predefined layouts.

**Parameters:**
- `layout` (string, required): Layout type
  - `2x2`: Four windows in a 2x2 grid
  - `3x3`: Nine windows in a 3x3 grid
  - `left-right`: Two windows side by side
  - `top-bottom`: Two windows stacked vertically
  - `maximize-all`: Maximize all visible windows

**Example:**
```json
{
  "name": "arrange_windows",
  "arguments": {
    "layout": "2x2"
  }
}
```

### 2. snap_to_position
Snap a specific window to a position.

**Parameters:**
- `windowTitle` (string, required): Title of the window to snap
- `position` (string, required): Position to snap to
  - `left`, `right`, `top`, `bottom`
  - `top-left`, `top-right`, `bottom-left`, `bottom-right`
  - `center`

**Example:**
```json
{
  "name": "snap_to_position",
  "arguments": {
    "windowTitle": "Visual Studio Code",
    "position": "left"
  }
}
```

### 3. manage_layouts
Save or apply window layouts.

**Parameters:**
- `action` (string, required): Action to perform
  - `save`: Save current window layout
  - `apply`: Apply a saved layout
- `name` (string, required): Name of the layout

**Example:**
```json
{
  "name": "manage_layouts",
  "arguments": {
    "action": "save",
    "name": "my-workspace"
  }
}
```

## Usage Examples

### Basic Window Arrangement
```javascript
// Arrange windows in a 2x2 grid
await use_mcp_tool({
  server_name: "snap-windows",
  tool_name: "arrange_windows",
  arguments: {
    layout: "2x2"
  }
});
```

### Snap Specific Window
```javascript
// Snap VS Code to the left side
await use_mcp_tool({
  server_name: "snap-windows",
  tool_name: "snap_to_position",
  arguments: {
    windowTitle: "Visual Studio Code",
    position: "left"
  }
});
```

### Save and Apply Layouts
```javascript
// Save current layout
await use_mcp_tool({
  server_name: "snap-windows",
  tool_name: "manage_layouts",
  arguments: {
    action: "save",
    name: "development-setup"
  }
});

// Apply saved layout
await use_mcp_tool({
  server_name: "snap-windows",
  tool_name: "manage_layouts",
  arguments: {
    action: "apply",
    name: "development-setup"
  }
});
```

## Testing
Run the test scripts to verify functionality:

```bash
# Basic server test
node mcp_servers/Tests/test-snap-mcp.js

# Functionality test
node mcp_servers/Tests/test-snap-functionality.js
```

## Technical Details
- **Platform**: Windows only
- **Dependencies**: PowerShell for window management
- **Storage**: Layouts are saved in `%USERPROFILE%\.snap-layouts\`
- **Performance**: Near-instant window operations

## Troubleshooting
- Ensure PowerShell execution policy allows script execution
- Run as administrator for best results with window management
- Window titles must match exactly (case-insensitive)
