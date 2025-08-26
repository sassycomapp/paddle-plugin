# Model Task Instruction for MCP Documentation Rewrites

## Task Overview
Rewrite MCP server documentation files to follow the standardized template format and style.

## Task Parameters
- **Source file**: Path to the MCP documentation file to be rewritten
- **Template file**: Path to the template file (`_MCP Doc Template.md`) that defines the format and style

## Task Instructions
1. **Read the source file** to understand its current content and structure
2. **Read the template file** to understand the required format and style
3. **Rewrite the source file** to follow the template structure while preserving all relevant information
4. **Save the rewritten file** with the original name plus "(rewrite)" appended

## File Naming Convention
- Source file: `filename.md`
- Output file: `filename (rewrite).md`

## Content Requirements
### Required Sections (must be included):
1. **Brief Overview** - Concise description of the MCP server
2. **Available Tools and Usage** - Complete tool inventory with parameters, return values, and examples
3. **Installation Information** - Clear installation steps and requirements
4. **Configuration** - Environment variables and MCP configuration examples
5. **How to Start and Operate this MCP** - Startup procedures and service management

### Optional Sections (include if applicable):
- Integration details
- Security considerations
- Troubleshooting
- Performance metrics
- Backup and recovery
- Version information
- Support and maintenance
- References

### Extra Info Section
- Include any additional information that doesn't fit into the standard template structure
- Organize content logically based on the specific MCP server requirements

## Formatting Standards
- Use consistent code block formatting
- Include parameter types in tool descriptions
- Provide working examples for all tools
- Use clear, descriptive section headings
- Include file paths relative to project root
- Replace bracketed placeholders `[like this]` with actual values
- Maintain consistent terminology across all MCP documentation

## Quality Assurance
- Preserve all original information from the source file
- Ensure the rewritten document follows the template structure exactly
- Verify that all tools are properly documented with examples
- Check that configuration examples are accurate and complete
- Ensure the Extra Info section contains any relevant additional content

## Example Usage
```
Rewrite the source file to assume the format and style of the template file and save the produced file with the original name with (rewrite) added to the file name:
Source file: C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\MCP Details\MCP_EasyOCRmcp.md
Template file: C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\MCP Details\_MCP Doc Template.md
```

## Notes
- The template file defines the structure and style that all MCP documentation should follow
- The Extra Info section provides flexibility for server-specific content that doesn't fit the standard template
- Always maintain the original meaning and technical accuracy of the source content
- Use the template's formatting standards for consistency across all MCP documentation