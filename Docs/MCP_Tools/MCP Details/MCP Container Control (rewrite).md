# MCP Container Control with Podman — Implementation Guide for KiloCode

## Brief Overview
MCP (Model Context Protocol) Container Control enables your AI orchestration environment (KiloCode + AG2 + MCP tools) to interact programmatically and securely with Podman containers. This setup allows your agents in KiloCode to start, stop, inspect, and manage containers dynamically as tools or execution sandboxes under your Podman runtime.

## Tool list
- podman.listContainers
- podman.startContainer
- podman.stopContainer
- podman.inspectContainer
- podman.executeInContainer
- podman.manageContainerLifecycle

## Available Tools and Usage
### Tool 1: podman.listContainers
**Description:** Lists all available Podman containers with their status and information.

**Parameters:**
- `all` (boolean): Include stopped containers in the results
- `format` (string): Output format for container information

**Returns:**
Array of container objects with status, ID, name, and image information.

**Example:**
```javascript
// Example usage
result = await client.call_tool("podman.listContainers", {
    "all": true,
    "format": "json"
});
```

### Tool 2: podman.startContainer
**Description:** Starts a stopped container.

**Parameters:**
- `containerId` (string): ID or name of the container to start
- `timeout` (number): Timeout for startup operation in seconds

**Returns:**
Success status and container information after starting.

**Example:**
```javascript
// Example usage
result = await client.call_tool("podman.startContainer", {
    "containerId": "my-container",
    "timeout": 30
});
```

### Tool 3: podman.stopContainer
**Description:** Stops a running container.

**Parameters:**
- `containerId` (string): ID or name of the container to stop
- `timeout` (number): Timeout for stop operation in seconds

**Returns:**
Success status and container information after stopping.

**Example:**
```javascript
// Example usage
result = await client.call_tool("podman.stopContainer", {
    "containerId": "my-container",
    "timeout": 10
});
```

### Tool 4: podman.inspectContainer
**Description:** Inspects a container to get detailed information about its configuration and status.

**Parameters:**
- `containerId` (string): ID or name of the container to inspect
- `format` (string): Output format for inspection results

**Returns:**
Detailed container configuration and status information.

**Example:**
```javascript
// Example usage
result = await client.call_tool("podman.inspectContainer", {
    "containerId": "my-container",
    "format": "json"
});
```

### Tool 5: podman.executeInContainer
**Description:** Executes commands inside a running container.

**Parameters:**
- `containerId` (string): ID or name of the container
- `command` (string): Command to execute
- `workingDir` (string): Working directory inside the container
- `user` (string): User to run the command as

**Returns:**
Command execution results including exit code, stdout, and stderr.

**Example:**
```javascript
// Example usage
result = await client.call_tool("podman.executeInContainer", {
    "containerId": "my-container",
    "command": "ls -la",
    "workingDir": "/app",
    "user": "root"
});
```

### Tool 6: podman.manageContainerLifecycle
**Description:** Manages container lifecycle operations including create, remove, and cleanup.

**Parameters:**
- `operation` (string): Lifecycle operation to perform (create, remove, cleanup)
- `containerConfig` (object): Container configuration for create operations
- `force` (boolean): Force operation when possible

**Returns:**
Operation status and results.

**Example:**
```javascript
// Example usage
result = await client.call_tool("podman.manageContainerLifecycle", {
    "operation": "create",
    "containerConfig": {
        "image": "ubuntu:latest",
        "name": "temp-container",
        "cmd": ["sleep", "3600"]
    },
    "force": false
});
```

## Installation Information
- **Installation Scripts**: `npm install -g podman-mcp-server` or `npx -y podman-mcp-server@latest`
- **Main Server**: `podman-mcp-server` command or `npx podman-mcp-server@latest`
- **Dependencies**: Node.js & npm (required for the MCP Podman server container), Python 3.8+ for KiloCode + MCP orchestration
- **Status**: Current installation status depends on Podman version 3.0+ and Node.js availability

## Configuration
**Environment Configuration (.env):**
```bash
PODMAN_MCP_HOST=localhost
PODMAN_MCP_PORT=8080
PODMAN_MCP_TIMEOUT=30
PODMAN_ROOTLESS=true
```

**MCP Configuration (mcp.json):**
```json
{
  "mcpServers": {
    "podman": {
      "command": "npx",
      "args": ["-y", "podman-mcp-server@latest"],
      "env": {
        "PODMAN_MCP_HOST": "localhost",
        "PODMAN_MCP_TIMEOUT": "30"
      }
    }
  }
}
```

## Integration
- **VS Code Extension**: Install Podman MCP extension with `code --add-mcp '{"name":"podman","command":"npx","args":["podman-mcp-server@latest"]}'`
- **Companion Systems**: Integration with KiloCode + AG2 orchestration environment, CI/CD systems, task runners
- **API Compatibility**: Compatible with MCP protocol standard, Podman CLI interface, container runtime interface (CRI)

## How to Start and Operate this MCP
### Manual Start:
```bash
podman-mcp-server
```

### Automated Start:
```bash
# Using npm global install
npm install -g podman-mcp-server
podman-mcp-server

# Using npx (no installation required)
npx -y podman-mcp-server@latest

# As a systemd service (Linux)
sudo systemctl enable --now podman-mcp-server
```

### Service Management:
```bash
# Start the service
podman-mcp-server

# Stop the service (Ctrl+C or process management)
pkill podman-mcp-server

# Check status
ps aux | grep podman-mcp-server

# Restart
pkill podman-mcp-server && podman-mcp-server
```

## Configuration Options
- **Rootless Mode**: Run Podman MCP Server in rootless mode for maximum security
- **Resource Limits**: Configure container resource limits via Podman flags
- **Network Isolation**: Set up network isolation or namespaces for multi-tenant workflows
- **User Permissions**: Configure user permission controls on Podman daemon
- **Timeout Settings**: Adjust timeout values for container operations
- **Logging**: Configure logging levels and output locations

## Key Features
1. **Dynamic Container Management**: Start, stop, inspect, and manage containers programmatically
2. **Secure Execution**: Run containers in isolated environments with proper security controls
3. **API Integration**: Full MCP protocol integration with KiloCode and AG2 orchestrators
4. **Lifecycle Automation**: Automated container creation, management, and cleanup
5. **Resource Control**: Configurable resource limits and monitoring capabilities

## Security Considerations
- **Rootless Mode**: Run Podman MCP Server in rootless mode for maximum security
- **Resource Limits**: Limit container resources via Podman flags to avoid overconsumption
- **Network Isolation**: Use network isolation or namespaces for multi-tenant or sensitive workflows
- **User Permissions**: Set up user permission controls on Podman daemon if applicable
- **Access Control**: Implement proper authentication and authorization for container operations
- **Data Protection**: Ensure sensitive data is properly isolated and encrypted

## Troubleshooting
- **Connection Issues**: Check firewall or IPC socket configurations used by Podman MCP
- **Container Access**: Verify Podman daemon is running and accessible
- **Permission Problems**: Ensure proper user permissions and rootless mode configuration
- **Timeout Errors**: Adjust timeout settings in configuration for slow container operations
- **MCP Protocol Issues**: Use `mcp-protocol --diagnose` if available for MCP layer diagnostics
- **Node.js Dependencies**: Verify Node.js and npm are properly installed and updated

## Testing and Validation
**Test Suite:**
```bash
# Test MCP server connection
python -c "
from mcp import ClientSession
from mcp.client.stdio import stdio_client
import asyncio

async def test_connection():
    server_command = ['npx', '-y', 'podman-mcp-server@latest']
    async with stdio_client(command=server_command) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        containers = await session.invoke_tool('podman.listContainers', {})
        print('Connection test successful:', containers)

asyncio.run(test_connection())
"

# Test container operations
podman run -d --name test-container ubuntu:latest sleep 3600
podman ps
podman stop test-container
podman rm test-container
```

## Performance Metrics
- **Response Time**: Typical MCP response times under 100ms for local operations
- **Resource Usage**: Minimal memory footprint (~50MB) for the MCP server
- **Scalability**: Supports multiple concurrent container operations
- **Throughput**: Can handle 10-50 container operations per second depending on complexity
- **Latency**: Container start/stop operations typically complete in 1-5 seconds

## Backup and Recovery
- **Container State**: Regular backup of container configurations and data volumes
- **MCP Configuration**: Backup configuration files and environment settings
- **Recovery Procedures**: Steps to restore MCP server functionality and container states
- **Disaster Recovery**: Plan for catastrophic failures including container recreation

## Version Information
- **Current Version**: podman-mcp-server@latest (check npm for latest version)
- **Last Updated**: Regular updates with Podman releases and MCP protocol improvements
- **Compatibility**: Compatible with Podman 3.0+, Node.js 14+, MCP protocol standard

## Support and Maintenance
- **Documentation**: https://github.com/manusa/podman-mcp-server/blob/main/README.md
- **Community Support**: GitHub issues and discussions for the podman-mcp-server project
- **Maintenance Schedule**: Updates aligned with Podman releases and security patches
- **Monitoring**: Regular log review and performance monitoring

## References
[1] https://www.byteplus.com/en/topic/541244
[2] https://playbooks.com/mcp/manusa-podman
[3] https://github.com/manusa/podman-mcp-server/blob/main/README.md
[4] https://podman.io
[5] https://github.com/54rt1n/container-mcp
[6] https://podman-desktop.io/blog/podman-desktop-release-1.19
[7] https://podman-desktop.io/blog
[8] https://podman.io/docs

---

## Extra Info
### Summary Checklist for MCP Container Control Setup in KiloCode

| Step | Action | Notes |
|------|--------|-------|
| 1 | Ensure Podman and Node.js installed | Node.js required for MCP server |
| 2 | Install Podman MCP Server via npm/npx | Lightweight and official tool |
| 3 | Launch MCP Podman Server | Local server exposing Podman via MCP |
| 4 | Configure Cline MCP server pointing to Podman | Add MCP server in config files |
| 5 | Validate connection via MCP client calls | List containers, status |
| 6 | Use MCP Podman tools in AG2/Cline workflows | Container start/stop/inspect/exec |
| 7 | Configure security settings (rootless, limits) | Ensure resource and access safety |
| 8 | Automate container lifecycle as needed | CI/CD integration or task orchestration |
| 9 | Monitor and troubleshoot | Logs, Podman CLI, MCP diagnostics |

### Advanced Configuration Options

#### CI/CD Integration
```yaml
# Example GitHub Actions workflow
name: Container Management Workflow
on: [push, pull_request]
jobs:
  container-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests in container
        run: |
          mcp call podman.startContainer --containerId test-container
          mcp call podman.executeInContainer --containerId test-container --command "npm test"
          mcp call podman.stopContainer --containerId test-container
```

#### Multi-Container Orchestration
```javascript
// Example of orchestrating multiple containers
async function orchestrateContainers() {
  const containers = [
    { name: 'web-server', image: 'nginx:latest' },
    { name: 'app-server', image: 'node:14' },
    { name: 'database', image: 'postgres:13' }
  ];
  
  for (const container of containers) {
    await client.call_tool('podman.manageContainerLifecycle', {
      operation: 'create',
      containerConfig: {
        image: container.image,
        name: container.name,
        ports: container.ports || []
      }
    });
  }
}
```

#### Monitoring and Logging
```bash
# Enhanced monitoring script
#!/bin/bash
while true; do
  echo "$(date): Container Status" >> /var/log/podman-mcp-monitor.log
  mcp call podman.listContainers --all >> /var/log/podman-mcp-monitor.log
  sleep 60
done