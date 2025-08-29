# MCP Server Documentation Template

## Brief Overview
The MCP Playwright server provides browser automation capabilities using Playwright through the Model Context Protocol. This server enables LLMs to interact with web pages through structured accessibility snapshots, bypassing the need for screenshots or visually-tuned models. It offers fast, lightweight browser automation with deterministic tool application for web interaction tasks.

## Tool list
- browser_click
- browser_close
- browser_console_messages
- browser_drag
- browser_evaluate
- browser_file_upload
- browser_handle_dialog
- browser_hover
- browser_navigate
- browser_navigate_back
- browser_navigate_forward
- browser_network_requests
- browser_press_key
- browser_resize
- browser_select_option
- browser_snapshot
- browser_take_screenshot
- browser_type
- browser_wait_for
- browser_tab_close
- browser_tab_list
- browser_tab_new
- browser_tab_select
- browser_install
- browser_mouse_click_xy
- browser_mouse_drag_xy
- browser_mouse_move_xy
- browser_pdf_save

## Available Tools and Usage
### Tool 1: browser_click
**Description:** Perform click on a web page element

**Parameters:**
- `element` (string): Human-readable element description used to obtain permission to interact with the element
- `ref` (string): Exact target element reference from the page snapshot
- `doubleClick` (boolean, optional): Whether to perform a double click instead of a single click
- `button` (string, optional): Button to click, defaults to left

**Returns:**
Confirmation of successful click operation

**Example:**
```javascript
// Example usage
result = await client.call_tool("browser_click", {
    "element": "submit button",
    "ref": "#submit-button",
    "doubleClick": false
});
```

### Tool 2: browser_navigate
**Description:** Navigate to a specified URL

**Parameters:**
- `url` (string): The URL to navigate to

**Returns:**
Navigation confirmation with page load status

**Example:**
```javascript
// Example usage
result = await client.call_tool("browser_navigate", {
    "url": "https://example.com"
});
```

### Tool 3: browser_snapshot
**Description:** Capture accessibility snapshot of the current page (better than screenshot for structured data)

**Parameters:**
None

**Returns:**
Accessibility tree structure of the current page

**Example:**
```javascript
// Example usage
result = await client.call_tool("browser_snapshot", {});
```

### Tool 4: browser_type
**Description:** Type text into an editable element

**Parameters:**
- `element` (string): Human-readable element description used to obtain permission to interact with the element
- `ref` (string): Exact target element reference from the page snapshot
- `text` (string): Text to type into the element
- `submit` (boolean, optional): Whether to submit entered text (press Enter after)
- `slowly` (boolean, optional): Whether to type one character at a time

**Returns:**
Confirmation of text input operation

**Example:**
```javascript
// Example usage
result = await client.call_tool("browser_type", {
    "element": "search input field",
    "ref": "#search-input",
    "text": "Hello World",
    "submit": true
});
```

### Tool 5: browser_select_option
**Description:** Select an option in a dropdown or select element

**Parameters:**
- `element` (string): Human-readable element description used to obtain permission to interact with the element
- `ref` (string): Exact target element reference from the page snapshot
- `values` (array): Array of values to select in the dropdown

**Returns:**
Confirmation of option selection

**Example:**
```javascript
// Example usage
result = await client.call_tool("browser_select_option", {
    "element": "country dropdown",
    "ref": "#country-select",
    "values": ["United States", "Canada"]
});
```

### Tool 6: browser_take_screenshot
**Description:** Take a screenshot of the current page or specific element

**Parameters:**
- `type` (string, optional): Image format for the screenshot. Default is png.
- `filename` (string, optional): File name to save the screenshot to
- `element` (string, optional): Human-readable element description for element screenshot
- `ref` (string, optional): Exact target element reference for element screenshot
- `fullPage` (boolean, optional): When true, takes a screenshot of the full scrollable page

**Returns:**
Screenshot data or file path

**Example:**
```javascript
// Example usage
result = await client.call_tool("browser_take_screenshot", {
    "type": "png",
    "filename": "homepage.png",
    "fullPage": true
});
```

### Tool 7: browser_tab_list
**Description:** List all open browser tabs

**Parameters:**
None

**Returns:**
Array of tab objects with index and title information

**Example:**
```javascript
// Example usage
result = await client.call_tool("browser_tab_list", {});
```

### Tool 8: browser_tab_new
**Description:** Open a new browser tab

**Parameters:**
- `url` (string, optional): The URL to navigate to in the new tab

**Returns:**
Confirmation of new tab creation

**Example:**
```javascript
// Example usage
result = await client.call_tool("browser_tab_new", {
    "url": "https://google.com"
});
```

### Tool 9: browser_tab_select
**Description:** Select a specific tab by index

**Parameters:**
- `index` (number): The index of the tab to select

**Returns:**
Confirmation of tab selection

**Example:**
```javascript
// Example usage
result = await client.call_tool("browser_tab_select", {
    "index": 2
});
```

### Tool 10: browser_pdf_save
**Description:** Save current page as PDF file

**Parameters:**
- `filename` (string, optional): File name to save the pdf to

**Returns:**
Confirmation of PDF generation and file path

**Example:**
```javascript
// Example usage
result = await client.call_tool("browser_pdf_save", {
    "filename": "document.pdf"
});
```

## Installation Information
- **Installation Scripts**: `npm install -g @playwright/mcp` or `npx @playwright/mcp@latest`
- **Main Server**: `npx @playwright/mcp` with various configuration options
- **Dependencies**: Node.js 18+, Playwright browsers (Chromium, Firefox, WebKit)
- **Status**: ✅ Available (Version 0.0.33)

## Configuration
**Environment Configuration (.env):**
```bash
# Playwright MCP server configuration
PLAYWRIGHT_BROWSER=chromium
PLAYWRIGHT_HEADLESS=false
PLAYWRIGHT_PORT=8931
PLAYWRIGHT_OUTPUT_DIR=./playwright-output
PLAYWRIGHT_IGNORE_HTTP_ERRORS=false
PLAYWRIGHT_BLOCK_SERVICE_WORKERS=false
```

**MCP Configuration (mcp.json):**
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "env": {
        "PLAYWRIGHT_BROWSER": "chromium",
        "PLAYWRIGHT_HEADLESS": "false"
      },
      "alwaysAllow": [
        "browser_navigate",
        "browser_snapshot",
        "browser_click",
        "browser_type",
        "browser_take_screenshot",
        "browser_tab_list",
        "browser_tab_new",
        "browser_pdf_save"
      ],
      "disabled": false
    }
  }
}
```

## Integration
- **VS Code Extension**: Compatible with VS Code MCP extension for browser automation in development environments
- **Companion Systems**: Integrates with Claude Desktop, Cursor, Goose, and other MCP clients
- **API Compatibility**: Supports Model Context Protocol standards with stdio and HTTP transports

## How to Start and Operate this MCP
### Manual Start:
```bash
# Standard start with default settings
npx @playwright/mcp@latest

# Start with specific browser and headless mode
npx @playwright/mcp@latest --browser chromium --headless

# Start with HTTP transport for remote access
npx @playwright/mcp@latest --port 8931
```

### Automated Start:
```bash
# Using systemd (Linux)
sudo systemctl enable playwright-mcp
sudo systemctl start playwright-mcp

# Using Docker
docker run -d -p 8931:8931 mcr.microsoft.com/playwright/mcp

# Using supervisor
[program:playwright-mcp]
command=npx @playwright/mcp@latest
directory=/path/to/project
autostart=true
autorestart=true
```

### Service Management:
```bash
# Check status
systemctl status playwright-mcp

# Start/stop/restart
sudo systemctl start playwright-mcp
sudo systemctl stop playwright-mcp
sudo systemctl restart playwright-mcp

# View logs
journalctl -u playwright-mcp -f
```

## Configuration Options
- **Browser Selection**: Choice of chromium, firefox, webkit, or msedge
- **Headless Mode**: Configurable headless/headed browser execution
- **Network Configuration**: Allowed/blocked origins, proxy settings
- **Device Emulation**: Mobile device emulation capabilities
- **Viewport Settings**: Customizable browser viewport dimensions
- **Storage Management**: User data directory and session state configuration
- **Output Directory**: Configurable file output location
- **Image Responses**: Control over image response handling
- **Security Settings**: Sandbox control and HTTPS error handling

## Key Features
1. Fast and lightweight browser automation using accessibility tree
2. LLM-friendly structured data operations without vision models
3. Deterministic tool application for reliable web interactions
4. Multi-browser support (Chromium, Firefox, WebKit)
5. Tab management and multi-page navigation
6. File upload and download capabilities
7. PDF generation and screenshot capture
8. Network request monitoring and interception
9. Console message capture and debugging
10. Cross-platform compatibility with multiple MCP clients

## Security Considerations
- Browser automation may access sensitive websites - implement proper access controls
- Network traffic monitoring capabilities require careful permission management
- File upload functionality needs secure handling of uploaded files
- Cross-origin requests should be properly configured with allowed/blocked origins
- User data and session state should be properly secured
- Browser sandbox settings should be carefully evaluated for security requirements

## Troubleshooting
- **Browser Installation Issues**: Use `browser_install` tool or run `npx playwright install`
- **Connection Problems**: Verify server is running and accessible on configured port
- **Element Not Found**: Use `browser_snapshot` to get current page structure and verify element references
- **Network Timeouts**: Configure appropriate timeout settings and check network connectivity
- **Permission Errors**: Ensure proper element permissions and interaction capabilities
- **Debug Mode**: Enable verbose logging with additional diagnostic information

## Testing and Validation
**Test Suite:**
```bash
# Test basic navigation
curl -X POST http://localhost:8931/mcp -H "Content-Type: application/json" -d '{"method": "tools/call", "params": {"name": "browser_navigate", "arguments": {"url": "https://example.com"}}}'

# Test page snapshot
curl -X POST http://localhost:8931/mcp -H "Content-Type: application/json" -d '{"method": "tools/call", "params": {"name": "browser_snapshot", "arguments": {}}}'

# Test screenshot capability
curl -X POST http://localhost:8931/mcp -H "Content-Type: application/json" -d '{"method": "tools/call", "params": {"name": "browser_take_screenshot", "arguments": {"type": "png"}}}'

# Test tab management
curl -X POST http://localhost:8931/mcp -H "Content-Type: application/json" -d '{"method": "tools/call", "params": {"name": "browser_tab_list", "arguments": {}}}'
```

## Performance Metrics
- **Page Load Speed**: Optimized for fast page loading and interaction
- **Memory Usage**: Efficient browser resource management
- **Network Efficiency**: Configurable request handling and caching
- **Response Time**: Sub-second response times for most operations
- **Scalability**: Multiple browser instances for parallel operations
- **Resource Optimization**: Lightweight accessibility tree vs full DOM processing

## Backup and Recovery
- **Session State**: Save and restore browser session states
- **Output Files**: Regular backup of generated screenshots, PDFs, and other outputs
- **Configuration Backup**: Store MCP configuration files in version control
- **Browser Profiles**: Backup user data and browser preferences
- **Recovery Procedures**: Documented recovery process for browser automation failures

## Version Information
- **Current Version**: 0.0.33 (Latest stable release)
- **Last Updated**: [Installation date verification available]
- **Compatibility**: Compatible with MCP servers following Model Context Protocol standards

## Support and Maintenance
- **Documentation**: Available via README.md and inline documentation
- **Community Support**: GitHub repository issues and discussions
- **Maintenance Schedule**: Regular updates for browser compatibility and performance improvements
- **Browser Updates**: Automatic browser binary updates through Playwright

## References
- [Official GitHub Repository](https://github.com/microsoft/playwright-mcp)
- [Playwright Documentation](https://playwright.dev/)
- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [MCP Client Integration Guide](https://modelcontextprotocol.io/quickstart/user)
- [Docker Deployment](https://hub.docker.com/r/mcr.microsoft.com/playwright/mcp)

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
The MCP Playwright server provides comprehensive browser automation capabilities through the Model Context Protocol, enabling AI systems to interact with web pages using structured accessibility data rather than visual processing. By leveraging Playwright's powerful browser automation engine with MCP integration, it offers deterministic tool application, multi-browser support, and seamless integration with various MCP clients. The server is designed to be fast, lightweight, and LLM-friendly, providing reliable web interaction capabilities for automation, testing, and data extraction tasks across different platforms and browsers.