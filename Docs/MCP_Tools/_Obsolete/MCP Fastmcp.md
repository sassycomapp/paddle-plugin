

***

# MCP FastMCP Implementation for KiloCode — Step-by-Step Guide

Here is a **full, actionable implementation instruction set** for KiloCode to implement **MCP FastMCP** into your system in a simple, robust, fit-for-purpose, and lightweight manner, including configuration and integration details based on the FastMCP framework and MCP protocol.

***

## Overview

FastMCP is a Pythonic, lightweight MCP server implementation designed for easy creation and orchestration of MCP tools and resources. It integrates seamlessly with AI agents and orchestrators (like KiloCode and AG2) and enables modular interaction with backend services.

In your system, FastMCP will act as the core MCP server exposing tools (e.g., vector stores, Simba KMS, container control) and resources that your AI agents can access through KiloCode or AG2 orchestrators.

***

## Prerequisites

- Python 3.8 or later installed
- Familiarity with Python async programming (recommended)
- KiloCode environment set up for MCP orchestration
- Your existing MCP tools and infrastructure (e.g., Simba, Podman MCP server) available to integrate or wrap
- Basic MCP knowledge helpful but not required

***

## Step 1: Install FastMCP

Use pip or `uv` (Python package manager recommended for dependency management):

```bash
pip install fastmcp
```

Or with `uv`:

```bash
uv add fastmcp
```

Verify installation:

```bash
fastmcp version
```

You should see FastMCP version, MCP protocol version, Python environment info.

***

## Step 2: Create a Basic FastMCP Server

Build a minimal MCP server to expose tools and resources.

Create a Python file, e.g., `fastmcp_server.py`:

```python
from fastmcp import FastMCP

mcp = FastMCP(name="MyFastMCPServer")

@mcp.tool()
def greet(name: str) -> str:
    return f"Hello, {name}!"

@mcp.tool()
def add(a: int, b: int) -> int:
    return a + b

if __name__ == "__main__":
    mcp.run()  # Runs using default stdio transport
```

***

## Step 3: Run the MCP Server

Run your server locally for development:

```bash
python fastmcp_server.py
```

Alternatively, run via FastMCP CLI for more options (e.g., SSE transport):

```bash
fastmcp run fastmcp_server.py:mcp --transport sse --port 8080 --host 127.0.0.1
```

This spins up the MCP server on port 8080 with Server-Sent Events transport.

***

## Step 4: Integrate Your Existing Tools into FastMCP

Replace or augment simple example tools with your actual MCP tool implementations (e.g., Simba KMS retrievals, Podman container control, PostgreSQL vector queries):

```python
@mcp.tool()
def simba_search(query: str):
    # Integrate Simba client calls here and return results
    pass

@mcp.tool()
def podman_start_container(container_id: str):
    # Call Podman MCP server or subprocess here to start container
    pass
```

Use async code if your tool APIs require it.

***

## Step 5: Configure KiloCode to Use Your FastMCP Server

Configure your KiloCode `mcp_settings.json` or equivalent with FastMCP server details:

```json
{
  "mcpServers": {
    "fastmcp_local": {
      "command": "python",
      "args": ["path/to/fastmcp_server.py"],
      "env": {
        "ENV_VAR": "value"
      },
      "alwaysAllow": ["greet", "add", "simba_search", "podman_start_container"],
      "disabled": false
    }
  }
}
```

Alternatively, if you run FastMCP with SSE on localhost:

```json
{
  "mcpServers": {
    "fastmcp_remote": {
      "url": "http://127.0.0.1:8080/mcp",
      "alwaysAllow": ["greet", "add", "simba_search", "podman_start_container"],
      "disabled": false
    }
  }
}
```

***

## Step 6: KiloCode Calling FastMCP Tools

From KiloCode, or your AG2 orchestrator, MCP clients can invoke tools like this:

```python
from fastmcp import Client
import asyncio

async def call_fastmcp_tools():
    client = Client("http://127.0.0.1:8080")
    async with client:
        greeting = await client.call_tool("greet", {"name": "KiloCode User"})
        print(greeting)
        result = await client.call_tool("add", {"a": 5, "b": 7})
        print(result)

asyncio.run(call_fastmcp_tools())
```

***

## Step 7: Monitor and Tune

- Adjust logging level via code or environment variables for debugging.
- Optionally configure `port`, `host`, and other server settings on `FastMCP` instantiation:

```python
mcp = FastMCP(name="MyServer", port=8080, host="127.0.0.1", log_level="INFO")
```

- Use FastMCP CLI options for transport method, logging, and bind address.

***

## Step 8: Production & Scaling Considerations

- Deploy FastMCP server as a service or container for reliability.
- Use SSE transport for web or remote client connections.
- Keep tools modular and separate concerns (each tool with clear inputs/outputs).
- Monitor tool error rates and performance.
- Provide tool versioning if needed.
- Secure MCP server interfaces with API keys or tokens.

***

## Step 9: Extend and Integrate with Other MCP Servers

You can run multiple MCP servers (Simba KMS, Podman MCP, vector store MCP) alongside FastMCP, and manage them in KiloCode configurations. FastMCP can host new tools or wrap existing MCP servers.

***

# Summary Checklist

| Step | Action                                   | Notes                               |
|-------|-----------------------------------------|------------------------------------|
| 1     | Install FastMCP Python package           | `pip install fastmcp`               |
| 2     | Create MCP server Python script           | Define tools using `@mcp.tool()`    |
| 3     | Run local MCP server setup                 | Use `python` or `fastmcp run` CLI   |
| 4     | Add your actual MCP tools to FastMCP       | Simba, Podman, vector DB etc.       |
| 5     | Configure KiloCode to connect to your FastMCP | Local command or SSE URL config     |
| 6     | Invoke MCP tools via KiloCode or AG2 agents   | Use FastMCP client calls            |
| 7     | Monitor, log and tune MCP server           | Adjust logging and performance      |
| 8     | Deploy FastMCP in production                | Containerize or service as needed   |
| 9     | Integrate with other MCP servers             | Coordinate multi-server orchestration|

***


[1] https://docs.cline.bot/mcp/configuring-mcp-servers
[2] https://apidog.com/blog/fastmcp/
[3] https://scottspence.com/posts/using-mcp-tools-with-claude-and-cline
[4] https://modelcontextprotocol.io/quickstart/client
[5] https://github.com/jlowin/fastmcp
[6] https://modelcontextprotocol.io/quickstart/server
[7] https://gofastmcp.com
[8] https://cline.bot/blog/the-developers-guide-to-mcp-from-basics-to-advanced-workflows
[9] https://www.youtube.com/watch?v=rnljvmHorQw