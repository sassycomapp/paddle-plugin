

***

# MCP Memory Service Implementation Guide for Your System

Here is a **full actionable implementation guide** for integrating the **doobidoo/mcp-memory-service** into your system based on your objectives: **simple, robust, fit-for-purpose, and lightweight**. This guide covers installation, configuration, and integration with your existing **KiloCode + AG2 + MCP** stack.

***

## Overview

The **doobidoo/mcp-memory-service** is a Python-based, production-ready MCP Memory Server implementing persistent semantic memory with vector database storage (PGvector or SQLite Vec). It supports long-term memory recall, autonomous memory consolidation, and is designed to integrate well with AI orchestration stacks like yours.

***

## Step 1: Environment Preparation

- Install **Python 3.8+** (Python 3.10+ recommended for best compatibility).
- Ensure you have **git** installed to clone the repo.
- Have a **virtual environment** tool ready (venv or conda).
- Prepare persistent storage directories for:

  - **PGvector embedding database**
  - **Backup folder**

***

## Step 2: Clone Repository and Setup Virtual Environment

```bash
# Clone the repo
git clone https://github.com/doobidoo/mcp-memory-service.git
cd mcp-memory-service

# Create and activate a virtual environment
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate

# Run installer script which installs dependencies and configures environment
python install.py
```

- The `install.py` script detects your hardware, installs required libraries (e.g., PyTorch with CUDA if applicable), and configures the service.

***

## Step 3: Configure Environment Variables

Define these environment variables, either in a `.env` file, system environment, or KiloCode config environment:

```bash
# Path to persistent PGvector vector store (create directory before run)
export MCP_MEMORY_"Placeholder"_PATH="/path/to/"Placeholder"_db"

# Path to backup directory
export MCP_MEMORY_BACKUPS_PATH="/path/to/backups"
```

Example paths on Windows:

```powershell
$env:MCP_MEMORY_"Placeholder"_PATH="C:\Users\YourUser\AppData\Local\mcp-memory\"Placeholder"_db"
$env:MCP_MEMORY_BACKUPS_PATH="C:\Users\YourUser\AppData\Local\mcp-memory\backups"
```

***

## Step 4: Running the Memory Service

### Option 1: Run locally using Python

Run the memory server module directly:

```bash
python -m mcp_memory_service.server
```

This starts the service with default stdin/stdout MCP transport.

### Option 2: Using the Windows Wrapper (Recommended on Windows)

Run the wrapper script to handle PyTorch installation and env config:

```bash
python memory_wrapper.py
```

### Option 3: Run via Docker container (cross-platform)

```bash
docker pull doobidoo/mcp-memory-service:latest

docker run -d -p 8000:8000 \
  -v /path/to/"Placeholder"_db:/app/"Placeholder"_db \
  -v /path/to/backups:/app/backups \
  doobidoo/mcp-memory-service:latest
```

You can expose HTTP/SSE MCP endpoints with config for remote clients.

***

## Step 5: Configure KiloCode to Use the MCP Memory Service

In your `claude_desktop_config.json` (or equivalent KiloCode config), add:

```json
{
  "memory": {
    "command": "uv",
    "args": [
      "--directory",
      "path_to/mcp-memory-service",
      "run",
      "memory"
    ],
    "env": {
      "MCP_MEMORY_"Placeholder"_PATH": "your_"Placeholder"_db_path",
      "MCP_MEMORY_BACKUPS_PATH": "your_backups_path"
    },
    "alwaysAllow": [
      "store_memory",
      "retrieve_memory",
      "recall_memory",
      "search_by_tag",
      "delete_memory",
      "get_stats"
    ],
    "disabled": false
  }
}
```

- Replace `"path_to/mcp-memory-service"`, `"your_"Placeholder"_db_path"`, and `"your_backups_path"` with your actual paths.

- On Windows, you may instead use:

```json
{
  "memory": {
    "command": "python",
    "args": [
      "C:\\path\\to\\mcp-memory-service\\memory_wrapper.py"
    ],
    "env": {
      "MCP_MEMORY_"Placeholder"_PATH": "C:\\Users\\YourUser\\AppData\\Local\\mcp-memory\\"Placeholder"_db",
      "MCP_MEMORY_BACKUPS_PATH": "C:\\Users\\YourUser\\AppData\\Local\\mcp-memory\\backups"
    },
    "alwaysAllow": [
      "store_memory",
      "retrieve_memory",
      "recall_memory",
      "search_by_tag",
      "delete_memory",
      "get_stats"
    ],
    "disabled": false
  }
}
```

***

## Step 6: Integration with AG2 and KiloCode Orchestration

### Using MCP Client Session in Code (Python example):

```python
from mcp import ClientSession
from mcp.client.stdio import stdio_client
import asyncio

async def use_memory_service():
    server_command = ["python", "path_to/mcp-memory-service/memory_wrapper.py"]

    async with stdio_client(command=server_command) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        
        # Example: Store memory
        store_result = await session.invoke_tool("store_memory", {
            "content": "Remember that the project deadline is next Friday.",
            "tags": ["project", "deadline"]
        })
        print("Stored memory:", store_result)

        # Example: Retrieve relevant memories
        retrieve_result = await session.invoke_tool("retrieve_memory", {
            "query": "project deadline"
        })
        print("Retrieved memories:", retrieve_result)

asyncio.run(use_memory_service())
```

- The tools exposed include at least:  
  `store_memory`, `retrieve_memory`, `recall_memory`, `search_by_tag`, `delete_memory`, `get_stats`.

***

## Step 7: Memory Maintenance & Backup

- Configure automatic backups by scheduling periodic backup calls or use built-in MCP commands.
- Periodically clean stale or duplicate memories with `delete_memory` or `delete_by_tag` calls.
- Monitor memory usage with `get_stats`.

***

## Step 8: Monitoring and Troubleshooting

- Log output of the memory server will give you run-time diagnostics.
- Errors in integration show as MCP tool call failures, check KiloCode or AG2 logs.
- Use provided dashboards or CLI tools if available for memory inspection.

***

## Summary Table

| Step             | Description                               | Notes                     |
|------------------|-------------------------------------------|---------------------------|
| 1                | Prepare environment: Python 3.8+, git, venv |                            |
| 2                | Clone and setup repository, run `install.py` | Hardware-aware installs    |
| 3                | Set environment variables for DB & backup paths | Create folders ahead       |
| 4                | Run memory server (Python module / wrapper / Docker) | Local or containerized    |
| 5                | Configure KiloCode with MCP server details    | JSON config edit           |
| 6                | Use MCP client calls in AG2 / KiloCode orchestration | Store and retrieve data    |
| 7                | Setup maintenance: backups, cleanup        | Schedule jobs / MCP calls  |
| 8                | Monitoring and troubleshooting            | Logs and error checking   |



***

### References

- Official GitHub: https://github.com/doobidoo/mcp-memory-service  
- Usage and install docs linked in GitHub repo  
- Docker Hub: doobidoo/mcp-memory-service (official image)

***

This plan should help you get up and running with a **simple, robust, and full-featured MCP Memory System** tailored for your KiloCode + AG2 + MCP agentic architecture.

[1] https://playbooks.com/mcp/doobidoo-memory-service
[2] https://pypi.org/project/mseep-mcp-memory-service/0.2.2/
[3] https://www.deepnlp.org/store/mcp-server/mcp-server/pub-doobidoo/mcp-memory-service
[4] https://github.com/doobidoo/mcp-memory-service
[5] https://www.mcpserverfinder.com/servers/doobidoo/mcp-memory-service
[6] https://github.com/doobidoo/mcp-memory-service/blob/main/install.py
[7] https://www.magicslides.app/mcps/doobidoo-memory-service
[8] https://playbooks.com/mcp/doobidoo-memory-dashboard
[9] https://apidog.com/blog/openmemory-mcp-server/