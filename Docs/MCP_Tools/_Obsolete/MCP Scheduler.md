# MCP Scheduler Implementation Guide for KiloCode

The updated documentation now includes:

1. __Current Installation Status__: Confirmed that MCP Scheduler is fully installed and operational
2. __Server Details__: Location at `mcp_servers/mcp-scheduler-server.js` with all dependencies properly installed
3. __Configuration Details__: The exact configuration in `.vscode/mcp.json`
4. __Available Tools__: Complete documentation of all 5 tools (`schedule_task`, `list_scheduled_tasks`, `cancel_task`, `run_task_now`, `get_task_executions`)
5. __Features__: Comprehensive overview of database storage, task execution, retry mechanisms, and logging
6. __Usage Examples__: Practical examples for scheduling tasks and using the tools
7. __AG2 Integration__: Python code examples for integrating with the AG2 orchestrator
8. __Testing and Validation__: Instructions for testing the server and tools
9. __Database Schema__: Detailed information about the SQLite database structure
10. __Security Considerations__: Best practices for file permissions, command execution, and environment variables
11. __Monitoring and Maintenance__: Guidelines for task monitoring and database maintenance
12. __Troubleshooting__: Common issues and solutions
13. __Performance Considerations__: Task frequency and database performance notes
14. __Version Information__: Current version and compatibility details

The documentation is now accurate and comprehensive, reflecting that the MCP Scheduler is fully installed and ready for use in your semi-autonomous Agentic IDE.


***

## Overview

**MCP Scheduler** is an MCP server that provides robust scheduling capabilities for your semi-autonomous Agentic IDE, including:

- Scheduling reminders and notifications
- Triggering API calls at scheduled times
- Executing shell commands/tasks
- Managing time-based workflows inside your AI orchestration environment
- Persistent task storage with SQLite
- Automatic retry mechanisms with exponential backoff
- Comprehensive execution history tracking

The MCP Scheduler is **already installed and operational** in your KiloCode system at `C:\_1mybizz\addle-plugin\mcp_servers\mcp-scheduler-server.js`.

***

## Current Installation Status ✅

### Server Location
- **File**: `mcp_servers/mcp-scheduler-server.js`
- **Type**: Node.js-based MCP server
- **Status**: Fully installed and operational

### Dependencies
All required dependencies are installed:
- ✅ `@modelcontextprotocol/sdk ^0.5.0`
- ✅ `sqlite3 ^5.1.6`
- ✅ `node-schedule ^2.1.1`
- ✅ `winston ^3.17.0`
- ✅ `zod ^3.22.4`

### Configuration
The MCP Scheduler is properly configured in `.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "mcp-scheduler": {
      "command": "node",
      "args": [
        "mcp_servers/mcp-scheduler-server.js"
      ],
      "env": {}
    }
  }
}
```

***

## Available Tools

The MCP Scheduler provides the following tools:

### 1. `schedule_task`
Schedules a shell command to be executed at a specific time.

**Parameters:**
- `name` (string): The name of the task
- `command` (string): The shell command to execute
- `runAt` (string): ISO 8601 timestamp for execution
- `maxRetries` (number, optional): Maximum retry attempts (default: 0)
- `timeoutMs` (number, optional): Timeout in milliseconds (default: 30000)
- `workingDirectory` (string, optional): Working directory for execution
- `environmentVariables` (object, optional): Environment variables

### 2. `list_scheduled_tasks`
Lists all currently scheduled tasks with optional filtering.

**Parameters:**
- `status` (string, optional): Filter by status ("scheduled", "running", "completed", "failed", "cancelled")
- `enabled` (boolean, optional): Filter by enabled/disabled tasks

### 3. `cancel_task`
Cancels a scheduled task by its ID.

**Parameters:**
- `taskId` (number): The ID of the task to cancel

### 4. `run_task_now`
Immediately executes a scheduled task by its ID.

**Parameters:**
- `taskId` (number): The ID of the task to run immediately

### 5. `get_task_executions`
Gets execution history for a specific task.

**Parameters:**
- `taskId` (number): The ID of the task to get execution history for

***

## Features

### Database Storage
- SQLite database for persistent task storage
- Automatic database initialization on startup
- Tables for tasks and execution history

### Task Execution
- Automatic task checking every 30 seconds
- Support for working directory configuration
- Environment variable support
- Customizable timeout settings
- Comprehensive error handling

### Retry Mechanism
- Automatic retry on failure with exponential backoff
- Configurable maximum retry attempts
- Detailed error logging

### Logging
- Structured logging with Winston
- Task execution tracking
- Error reporting and debugging support

***

## Usage Examples

### Basic Task Scheduling
```json
{
  "name": "Daily Backup",
  "command": "backup_script.sh",
  "runAt": "2025-08-15T02:00:00Z",
  "maxRetries": 3,
  "timeoutMs": 300000
}
```

### List All Tasks
```bash
# Using MCP client
list_scheduled_tasks
```

### Cancel a Task
```bash
# Using MCP client
cancel_task --taskId 123
```

### Run Task Immediately
```bash
# Using MCP client
run_task_now --taskId 123
```

***

## Integration with AG2 Orchestrator

The MCP Scheduler is already integrated and available to your AG2 orchestrator. Here's how to use it:

### Python Integration Example
```python
from mcp import ClientSession
from mcp.client.stdio import stdio_client
import asyncio

async def schedule_task_example():
    # The MCP Scheduler is already configured in .vscode/mcp.json
    # and will be automatically available to AG2 orchestrator
    
    async with stdio_client(command=["node", "mcp_servers/mcp-scheduler-server.js"]) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        
        # Schedule a task
        result = await session.invoke_tool("schedule_task", {
            "name": "Test Task",
            "command": "echo 'Hello from MCP Scheduler'",
            "runAt": "2025-08-15T12:30:00Z"
        })
        
        print("Task scheduled:", result)

# Example usage in your orchestrator
async def list_tasks_example():
    async with stdio_client(command=["node", "mcp_servers/mcp-scheduler-server.js"]) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        
        # List all scheduled tasks
        tasks = await session.invoke_tool("list_scheduled_tasks", {})
        print("Scheduled tasks:", tasks)
```

***

## Testing and Validation

### Server Test
To verify the MCP Scheduler is working:

```bash
cd mcp_servers
node mcp-scheduler-server.js
```

You should see:
```
Database initialized successfully
Task scheduler started (checking every 30 seconds)
MCP Scheduler Server running on stdio.
```

### Tool Validation
Test the tools using your MCP client or VSCode KiloCode extension:

1. **List tasks**: `list_scheduled_tasks`
2. **Schedule a test task**: Use `schedule_task` with a simple command
3. **Verify execution**: Check the task status and execution history

***

## Database Schema

The MCP Scheduler uses SQLite with the following tables:

### `tasks` table
- `id`: Primary key
- `name`: Task name
- `command`: Command to execute
- `run_at`: Scheduled execution time
- `status`: Current status (scheduled, running, completed, failed, cancelled)
- `max_retries`: Maximum retry attempts
- `retry_count`: Current retry count
- `timeout_ms`: Execution timeout
- `enabled`: Task enabled/disabled
- `working_directory`: Working directory for execution
- `environment_variables`: JSON string of environment variables

### `task_executions` table
- `id`: Primary key
- `task_id`: Foreign key to tasks table
- `execution_time`: When the task was executed
- `status`: Execution status
- `exit_code`: Process exit code
- `stdout`: Standard output
- `stderr`: Standard error
- `error_message`: Error details
- `duration_ms`: Execution duration

***

## Security Considerations

### File Permissions
- Ensure the server has appropriate permissions to execute commands
- Restrict access to sensitive directories and files

### Command Execution
- Be cautious with command execution from untrusted sources
- Consider implementing command validation if needed

### Environment Variables
- Store sensitive information in environment variables
- Avoid hardcoding credentials in task definitions

***

## Monitoring and Maintenance

### Task Monitoring
- Use `list_scheduled_tasks` to monitor active tasks
- Check `get_task_executions` for execution history
- Monitor logs for errors and performance issues

### Database Maintenance
- The database file (`mcp_scheduler.db`) will grow with execution history
- Consider implementing cleanup policies for old execution records

### Server Management
- The server runs as a standalone process
- Graceful shutdown handling implemented
- Automatic database cleanup on shutdown

***

## Troubleshooting

### Common Issues

1. **Server won't start**
   - Check Node.js installation
   - Verify dependencies are installed (`npm install`)
   - Check file permissions

2. **Tasks not executing**
   - Verify server is running
   - Check task status with `list_scheduled_tasks`
   - Review logs for errors

3. **Database errors**
   - Check file permissions on database file
   - Ensure disk space is available
   - Check for corrupted database

### Log Analysis
The server provides detailed logging:
- INFO: General operations and status updates
- WARN: Non-critical issues
- ERROR: Critical errors and failures

***

## Performance Considerations

### Task Frequency
- The scheduler checks for tasks every 30 seconds
- For high-frequency scheduling, consider reducing the interval
- Be mindful of system resource usage with many concurrent tasks

### Database Performance
- Indexes are automatically created for optimal query performance
- Large execution histories may impact query performance
- Consider implementing data retention policies

***

## Version Information

- **Server Version**: 1.0.0
- **MCP SDK Version**: ^0.5.0
- **Node.js Version**: v18+ recommended
- **Last Updated**: August 2025

***

## Support and Resources

For issues or questions:
- Check the server logs for detailed error information
- Verify configuration in `.vscode/mcp.json`
- Ensure all dependencies are properly installed
- Review the troubleshooting section above

***
