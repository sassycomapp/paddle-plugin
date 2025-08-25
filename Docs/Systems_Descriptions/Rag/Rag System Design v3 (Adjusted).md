Here is the revised RAG System Design incorporating the agreed solutions of using Simba for Knowledge Management and AG2 for agentic decision-making logic and interaction orchestration. Notes regarding testing, validation, secrets management, error handling, and manual model selection are inserted where relevant.

***

# Agentic RAG Application with Simba & AG2 - Implementation Guide

## Stack
- VSCode IDE [Installed]
- KiloCode programming environment [Installed]
- OpenRouter for model access (manual model selection) [Installed]
- Podman for container management (no Docker) [Installed]
- PostgreSQLDB with pgvector extension [Installed]
- Simba Knowledge Management System (KMS) for FAQ and document retrieval
- AG2 framework for agentic decision-making, tool selection, and agent interaction
- MCP Postgres, MCP PGVector for vector store interface [Installed]
- Brave-search API for real-time web querying integration. BRAVE_API_KEY = BSAbLxLX849t9mni7fGR7HWKstcFa7Y` [Installed]
- MCP FastMCP as the MCP server base [Installed]

Prioritize the Simba-based vector search, MCP handling, and AG2 orchestration for your RAG system. Consider phpMyFAQ only if you have extra capacity and a clear need for a formal FAQ knowledge base alongside your AI system.

***

## 1. Environment Setup

- Install Python 3.8+ and pip.
- Use Podman to manage containers.
- Setup PostgreSQL with pgvector extension enabled:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

- Install required Python packages including AG2:

```bash
pip install mcp-server psycopg2-binary python-dotenv requests pgvector ag2
```

- For Simba KMS installation instructions, refer to the [Simba System Documentation](../Simba/Simba KMS Installation instructions.md)

***

## 2. Project Structure & Setup

Create a project folder, e.g. `mcp-agentic-rag-simba-ag2`, with these files:

```
/mcp-agentic-rag-simba-ag2/
|-- .env            # API keys, DB creds - secrets managed separately (e.g., HashiCorp Vault)
|-- mcp_server.py   # MCP Server and Simba integration
|-- ag2_orchestrator.py  # AG2 agentic decision-making and orchestration logic
|-- rag_app.py      # Vector DB setup and Simba embedding management
```

***

## 3. Simba Integration as Replacement for FAQEngine

- Use Simba to handle document ingestion, chunking, embedding, vector store management, and retrieval.
- Simba supports integration with pgvector-backed PostgreSQL vector DB.
- Embed Simba calls inside MCP server tools to expose vector search as an MCP tool.

Example MCP tool snippet illustrating Simba retrieval integration:

```python
from simba import SimbaClient

simba_client = SimbaClient(pg_conn_str=os.getenv("POSTGRES_CONN_STR"))

@mcp_server.tool()
def simba_faq_retrieval_tool(query: str) -> str:
    if not isinstance(query, str):
        raise TypeError("Query must be a string.")
    results = simba_client.search(query, top_k=5)  # Simba handles embedding & similarity
    return "\n\n".join([res.text for res in results]) if results else "No relevant FAQ results found."
```

This replaces FAQEngine safely with Simba’s mature KMS.

***

## 4. MCP Server Setup and Tools (`mcp_server.py`)

- MCP server exposes all relevant tools: Simba retrieval, Brave Search API, web scraper (if used).
- Each tool implemented with proper input validations and limited error handling placeholders (to be fully built in coding phase).

Example tool for Brave Search remains:

```python
@mcp_server.tool()
def brave_search_web_tool(query: str) -> list:
    # ... (same as before, with try-except, headers, and API key from .env)
    pass
```

***

## 5. Agentic Decision-Making Logic & Agent Interaction via AG2 (`ag2_orchestrator.py`)

- Use AG2 framework for advanced agentic multi-tool decision-making and orchestration.
- AG2 manages dynamic tool selection (Simba vs Brave Search vs others) based on query context and confidence metrics.
- AG2 orchestrates how retrieved documents and results from different tools are synthesized into the final input prompt to LLM.

Example AG2 conceptual integration:

```python
from ag2 import MultiAgentSystem, ToolAgent

class SimbaAgent(ToolAgent):
    def run(self, query):
        # Calls Simba tool and returns results
        pass

class BraveSearchAgent(ToolAgent):
    def run(self, query):
        # Calls Brave Search tool and returns results
        pass

# Orchestrator initializes agents and defines decision workflow
multi_agent_system = MultiAgentSystem(agents=[SimbaAgent(), BraveSearchAgent()])

def agentic_query_handler(query: str) -> str:
    # AG2 determines which agents/tools to call and combines results
    response = multi_agent_system.execute_task(query)
    return response
```

Run this orchestrator in coordination with MCP server and KiloCode API client.

***

## 6. Running the System

- Ensure PostgreSQL with pgvector is running.
- Initialize Simba with your FAQ and document data. See [Simba System Documentation](../Simba/Simba KMS Installation instructions.md) for detailed setup instructions.
- Run MCP server:

```bash
python mcp_server.py
```

- Run AG2 orchestrator to handle user queries and call MCP tools intelligently.
- Send user queries via KiloCode or HTTP POST to your orchestration endpoint.

***

## 7. Notes & Reminders

- **Model Selection:**
  Models accessed via OpenRouter inside KiloCode are **manually selected** by the user/developer; no automatic model selection or switching is included in this setup.

- **Error Handling & Resilience:**  
  Basic error handling is scaffolded in tool code; full error handling, retries, and logging will be implemented during the coding phase with the AI coding model.

- **Testing & Validation:**  
  Comprehensive testing and validation suites are to be developed separately and integrated into your VSCode IDE environment.

- **Secrets Management:**  
  API keys, DB credentials, and secrets storage will be set up separately, likely using **HashiCorp Vault** or similar secure vault systems.

***

This updated design integrates Simba and AG2 to address your key concerns while maintaining a lightweight, flexible, and robust agentic RAG system tailored to your PC and stack.

## Documentation Structure
- RAG System documentation focuses on the integration architecture and workflow
- Simba KMS documentation contains installation and configuration details
- The two systems are designed to work together but maintain separate documentation for clarity

For detailed Simba KMS installation and configuration, please refer to the [Simba System Documentation](../Simba/Simba KMS Installation instructions.md).

Let me know how you would like to proceed!
