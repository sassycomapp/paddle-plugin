# MCP Server Documentation Template

## Brief Overview
[Provide a concise description of what this MCP server does, its primary purpose, and key capabilities]

## Tool list
[List all available MCP tools (Name Only)]

## Available Tools and Usage
[List all available MCP tools with their descriptions, parameters, and example usage]

### Tool 1: [Tool Name]
**Description:** [Brief description of what the tool does]

**Parameters:**
- `parameter1` (type): Description
- `parameter2` (type): Description

**Returns:**
[Description of return value]

**Example:**
```javascript
// Example usage
result = await client.call_tool("tool_name", {
    "parameter1": "value1",
    "parameter2": "value2"
});
```

### Tool 2: [Tool Name]
[Repeat structure for each tool]

## Installation Information
- **Installation Scripts**: [List installation scripts and their purposes]
- **Main Server**: [Path to main server file]
- **Dependencies**: [Required software and versions]
- **Status**: [Current installation status]

## Configuration
**Environment Configuration (.env):**
```bash
[Environment variables and their descriptions]
```

**MCP Configuration (mcp.json):**
```json
{
  "mcpServers": {
    "[server_name]": {
      "command": "[command]",
      "args": ["[arguments]"],
      "env": {
        "[environment_variable]": "[value]"
      }
    }
  }
}
```

## Integration
- **VS Code Extension**: [Integration details with VS Code]
- **Companion Systems**: [Integration with other systems]
- **API Compatibility**: [API version and compatibility information]

## How to Start and Operate this MCP
### Manual Start:
```bash
[Commands to start the server manually]
```

### Automated Start:
```bash
[Commands for automated startup]
[Platform-specific commands if applicable]
```

### Service Management:
```bash
[Commands for service management - start, stop, restart, status]
```

## Configuration Options
[Detailed configuration options, settings, and their purposes]

## Key Features
1. [Feature 1 description]
2. [Feature 2 description]
3. [Feature 3 description]

## Security Considerations
- [Security measures and considerations]
- [Authentication and authorization details]
- [Data protection measures]

## Troubleshooting
- **Common Issue 1**: [Problem description and solution]
- **Common Issue 2**: [Problem description and solution]
- **Debug Mode**: [How to enable debugging and logging]

## Testing and Validation
**Test Suite:**
```bash
[Commands to run tests and validate installation]
```

## Performance Metrics
- [Expected performance characteristics]
- [Resource requirements]
- [Scalability information]

## Backup and Recovery
[Backup procedures and recovery steps]

## Version Information
- **Current Version**: [Version number]
- **Last Updated**: [Date]
- **Compatibility**: [Compatibility information]

## Support and Maintenance
- **Documentation**: [Links to additional documentation]
- **Community Support**: [Support channels]
- **Maintenance Schedule**: [Maintenance information]

## References
[Links to relevant documentation, repositories, and resources]

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
[This section is for additional information that doesn't fit into the standard template structure. Organize content as needed based on the specific MCP server documentation requirements.]
