# AG2 Orchestration System - Complete Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Deployment Modes](#deployment-modes)
4. [Agents](#agents)
5. [Core Components](#core-components)
6. [Setup and Installation](#setup-and-installation)
7. [Usage Guide](#usage-guide)
8. [Testing](#testing)
9. [Configuration](#configuration)
10. [API Reference](#api-reference)
11. [Troubleshooting](#troubleshooting)
12. [Roadmap](#roadmap)

---
## The documentation includes:

1. System Overview: Complete description of the AG2 orchestration system, its features, and use cases
2. Architecture: Detailed architecture diagrams and component descriptions
3. Deployment Modes: Information about Pure Python, Lite, and Full deployment modes
4. Agents: Detailed descriptions of Researcher, Coordinator, and Analyst agents
5. Core Components: Memory, RAG, and Search services with implementation details
6. Setup and Installation: Step-by-step installation instructions for all deployment modes
7. Usage Guide: Both command-line and API usage examples
8. Testing: Complete testing structure and instructions
9. Configuration: Environment variables and configuration file examples
10. API Reference: Detailed API documentation for all classes and methods
Troubleshooting: Common issues and solutions
11. Roadmap: Future development plans and version roadmap

The documentation is comprehensive, well-structured, and provides everything needed to understand, install, configure, and use the AG2 orchestration system effectively.

---
## System Overview

The AG2 (Agent Generation 2) Orchestration System is a sophisticated multi-agent platform designed to coordinate and manage various AI agents working together to accomplish complex tasks. The system provides a unified interface for agent collaboration, memory management, and task distribution.

### Key Features
- **Multi-Agent Coordination**: Orchestrates multiple specialized AI agents
- **Memory Management**: Persistent conversation history and context storage
- **RAG Integration**: Retrieval-Augmented Generation for enhanced knowledge access
- **Flexible Deployment**: Three deployment modes to suit different needs
- **Extensible Architecture**: Easy to add new agents and capabilities
- **Async Processing**: Concurrent query handling for improved performance

### Use Cases
- Research and information gathering
- Data analysis and insights generation
- Task coordination and workflow management
- Customer support and assistance
- Content creation and curation
- System monitoring and optimization

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AG2 Orchestrator                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Researcher  │  │ Coordinator │  │   Analyst   │         │
│  │   Agent     │  │   Agent     │  │   Agent     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Memory    │  │     RAG     │  │   Search    │         │
│  │   Service   │  │   Service   │  │   Service   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│                   External Services (Optional)              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   PGvector  │  │ PostgreSQL  │  │ Brave Search│         │
│  │   Vector DB │  │   Database  │  │   API       │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

1. **Orchestrator**: Central coordinator that manages agent selection and task distribution
2. **Agents**: Specialized AI agents with specific capabilities
3. **Memory Service**: Handles conversation history and context storage
4. **RAG Service**: Provides knowledge retrieval and document search
5. **Search Service**: Enables web-like query capabilities
6. **External Services**: Optional integrations for enhanced functionality

---

## Deployment Modes

### 1. Pure Python Mode
- **Description**: Standalone implementation using only Python standard library
- **Dependencies**: Minimal external dependencies
- **Use Case**: Development, testing, environments with limited resources
- **Files**: `ag2_pure.py`, `run_pure.py`

### 2. Lite Mode
- **Description**: MCP-based implementation with essential services
- **Dependencies**: Node.js for MCP servers
- **Use Case**: Production environments with basic requirements
- **Files**: `ag2_orchestrator.py`, `mcp_servers_config_lite.yaml`

### 3. Full Mode
- **Description**: Complete MCP-based implementation with all services
- **Dependencies**: Full stack including PGvector, PostgreSQL, Brave Search
- **Use Case**: Production environments with maximum capabilities
- **Files**: `ag2_orchestrator.py`, `mcp_servers_config.yaml`

---

## Agents

### Researcher Agent
**Role**: Information gathering and knowledge retrieval

**Capabilities**:
- Web research and information collection
- Document analysis and summarization
- Knowledge base querying
- Source verification and validation

**Use Cases**:
- Research questions and fact-finding
- Document analysis and summarization
- Knowledge base queries

### Coordinator Agent
**Role**: Task management and workflow optimization

**Capabilities**:
- Task delegation and scheduling
- Workflow coordination
- Resource allocation
- Progress tracking

**Use Cases**:
- Complex task planning
- Multi-step workflows
- Resource management
- Project coordination

### Analyst Agent
**Role**: Data analysis and insight generation

**Capabilities**:
- Data analysis and interpretation
- Pattern recognition
- Statistical analysis
- Insight generation

**Use Cases**:
- Data analysis and interpretation
- Performance metrics analysis
- Trend identification
- Report generation

---

## Core Components

### Memory Service
**Purpose**: Maintains conversation history and context storage

**Features**:
- Persistent conversation storage
- Context retrieval and management
- Memory search and filtering
- Session management

**Implementation**:
- Pure Python: JSON file-based storage
- Full Mode: PostgreSQL database
- Lite Mode: JSON file-based storage

### RAG Service
**Purpose**: Provides knowledge retrieval and document search

**Features**:
- Document indexing and storage
- Semantic search capabilities
- Retrieval-Augmented Generation
- Document similarity matching

**Implementation**:
- Pure Python: Local document storage with embeddings
- Full Mode: PGvector vector database
- Lite Mode: Local document storage

### Search Service
**Purpose**: Enables web-like query capabilities

**Features**:
- Web search integration
- Query processing and routing
- Result aggregation and filtering
- Search optimization

**Implementation**:
- Pure Python: Mock search with predefined responses
- Full Mode: Brave Search API integration
- Lite Mode: Mock search with predefined responses

---

## Setup and Installation

### Prerequisites

#### System Requirements
- Python 3.8 or higher
- Node.js 16 or higher (for MCP modes)
- 4GB RAM minimum
- 1GB disk space

#### Python Dependencies
```bash
pip install -r src/orchestration/requirements.txt
```

#### Node.js Dependencies (for MCP modes)
```bash
cd mcp_servers
npm install
```

### Installation Steps

#### 1. Pure Python Mode
```bash
cd src/orchestration
python ag2_pure.py
```

#### 2. Lite Mode
```bash
cd src/orchestration
python ag2_orchestrator.py --config mcp_servers_config_lite.yaml
```

#### 3. Full Mode
```bash
# Start external services
docker-compose -f docker-compose."Placeholder".yml up -d

# Start orchestration
cd src/orchestration
python ag2_orchestrator.py --config mcp_servers_config.yaml
```

---

## Usage Guide

### Basic Usage

#### Command Line Interface
```bash
# Start the system
python src/orchestration/ag2_pure.py

# Interactive session
> What is AG2?
> Analyze the system performance
> Help me plan a complex workflow
```

#### Python API
```python
from src.orchestration.ag2_pure import AG2Orchestrator

orchestrator = AG2Orchestrator()
result = await orchestrator.run_query("What is AG2?")
print(result)
```

### Advanced Usage

#### Custom Agent Configuration
```python
from src.orchestration.ag2_pure import AG2Agent

custom_agent = AG2Agent(
    name="custom_agent",
    role="specialist",
    capabilities=["analysis", "research"]
)
```

#### Memory Management
```python
# Store conversation
memory.store_conversation("agent_name", "user", "User message")
memory.store_conversation("agent_name", "assistant", "Agent response")

# Retrieve conversation
results = memory.search_conversations("query")
```

#### RAG Integration
```python
# Add document
rag.add_document("doc_id", "Document content", {"metadata": "value"})

# Search documents
results = rag.search("query")
```

---

## Testing

### Test Structure
```
Test Bank/System Tests/AG2_Orchestration_Tests/
├── unit/                    # Unit tests
├── integration/            # Integration tests
├── e2e/                   # End-to-end tests
├── config/                # Test configuration
└── run_all_tests.py       # Test runner
```

### Running Tests

#### All Tests
```bash
cd "Test Bank/System Tests/AG2_Orchestration_Tests"
python run_all_tests.py
```

#### Specific Test Categories
```bash
# Unit tests only
python -m pytest unit/ -v -m unit

# Integration tests only
python -m pytest integration/ -v -m integration

# End-to-end tests only
python -m pytest e2e/ -v -m e2e
```

#### Quick Test
```bash
python quick_test.py
```

### Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: Multi-agent coordination
- **End-to-End Tests**: Complete workflow testing
- **Performance Tests**: Load and stress testing
- **Error Handling**: Edge case validation

---

## Configuration

### Environment Variables

#### Core Configuration
```bash
# Logging level
export AG2_LOG_LEVEL=INFO

# Memory path
export AG2_MEMORY_PATH=./memory

# Debug mode
export AG2_DEBUG=false
```

#### Service Configuration
```bash
# Database (Full Mode)
export DATABASE_URL=postgresql://user:pass@localhost:5432/db

# PGvector (Full Mode)
export "Placeholder"_URL=http://localhost:8000

# Brave Search API
export BRAVE_API_KEY=your_api_key
```

### Configuration Files

#### mcp_servers_config.yaml (Full Mode)
```yaml
mcpServers:
  rag:
    command: "node"
    args:
      - "../../mcp_servers/rag-mcp-server.js"
    env:
      "Placeholder"_URL: "http://localhost:8000"
    transport: "stdio"
    
  agent-memory:
    command: "node"
    args:
      - "../../mcp_servers/agent-memory/index.js"
    env:
      DATABASE_URL: "postgresql://user:pass@localhost:5432/db"
    transport: "stdio"
    
  brave-search:
    command: "node"
    args:
      - "../../mcp_servers/brave-search-mcp-server.js"
    env:
      BRAVE_API_KEY: "your_api_key"
    transport: "stdio"
```

#### mcp_servers_config_lite.yaml (Lite Mode)
```yaml
mcpServers:
  rag-lite:
    command: "node"
    args:
      - "../../mcp_servers/rag-mcp-server-lite.js"
    env:
      DATA_DIR: "./mock_data"
    transport: "stdio"
    
  agent-memory-lite:
    command: "node"
    args:
      - "../../mcp_servers/agent-memory-lite.js"
    env:
      MEMORY_DIR: "./mock_memory"
    transport: "stdio"
    
  brave-search-lite:
    command: "node"
    args:
      - "../../mcp_servers/brave-search-mcp-server-lite.js"
    env:
      MOCK_MODE: "true"
    transport: "stdio"
```

---

## API Reference

### AG2Orchestrator Class

#### Constructor
```python
def __init__(self, config_path=None, mode="pure"):
```

#### Methods
```python
async def run_query(self, query: str) -> str:
    """Process a query through the appropriate agent"""
    
async def select_agent(self, query: str) -> str:
    """Select the best agent for a given query"""
    
def get_agent_status(self) -> dict:
    """Get status of all agents"""
    
async def shutdown(self):
    """Shutdown the orchestrator gracefully"""
```

### AG2Agent Class

#### Constructor
```python
def __init__(self, name: str, role: str, capabilities: list):
```

#### Methods
```python
async def process_task(self, task: str) -> dict:
    """Process a task and return results"""
    
async def collaborate(self, other_agents: list, task: str) -> dict:
    """Collaborate with other agents on a task"""
    
def get_capabilities(self) -> list:
    """Get agent capabilities"""
```

### Memory Service

#### Methods
```python
def store_conversation(self, agent: str, role: str, content: str):
    """Store a conversation entry"""
    
def search_conversations(self, query: str) -> list:
    """Search conversation history"""
    
def get_conversation_history(self, agent: str) -> list:
    """Get full conversation history for an agent"""
```

### RAG Service

#### Methods
```python
def add_document(self, doc_id: str, content: str, metadata: dict):
    """Add a document to the knowledge base"""
    
def search(self, query: str, limit: int = 5) -> list:
    """Search for relevant documents"""
    
def get_document(self, doc_id: str) -> dict:
    """Retrieve a specific document"""
```

---

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure Python path is set correctly
export PYTHONPATH="${PYTHONPATH}:./src"

# Or use in Python
import sys
sys.path.append('./src')
```

#### Service Connection Issues
```bash
# Check if services are running
docker-compose -f docker-compose."Placeholder".yml ps

# Check MCP server status
npm run status
```

#### Memory Service Issues
```bash
# Check memory directory permissions
chmod 755 ./memory

# Verify database connection (Full Mode)
psql $DATABASE_URL -c "SELECT 1;"
```

### Debug Mode

#### Enable Debug Logging
```bash
export AG2_LOG_LEVEL=DEBUG
export AG2_DEBUG=true
```

#### Debug Commands
```python
# Enable debug mode
orchestrator.enable_debug()

# Get detailed error information
try:
    result = await orchestrator.run_query("test query")
except Exception as e:
    print(f"Error details: {e}")
    print(f"Traceback: {traceback.format_exc()}")
```

### Performance Issues

#### Memory Optimization
```python
# Clear old conversations
memory.clear_old_conversations(days=30)

# Optimize search queries
rag.optimize_search_index()
```

#### Load Balancing
```python
# Implement query queuing
orchestrator.enable_query_queue(max_size=100)

# Use async processing
await asyncio.gather(*queries)
```

---

## Roadmap

### Version 1.0 (Current)
- ✅ Basic multi-agent orchestration
- ✅ Memory management
- ✅ RAG integration
- ✅ Three deployment modes
- ✅ Comprehensive testing

### Version 1.1 (Next Release)
- 🔄 Enhanced agent capabilities
- 🔄 Improved memory management
- 🔄 Better error handling
- 🔄 Performance optimizations
- 🔄 Additional integrations

### Version 1.2 (Future)
- 📋 Advanced analytics
- 📋 Custom agent development
- 📋 Multi-language support
- 📋 Enhanced security
- 📋 Scalability improvements

### Version 2.0 (Long-term)
- 📋 Machine learning-based agent selection
- 📋 Automated agent training
- 📋 Cross-platform deployment
- 📋 Enterprise features
- 📋 Advanced monitoring

---

## Support

### Documentation
- Complete API reference
- Usage examples
- Configuration guides
- Troubleshooting documentation

### Community
- GitHub Issues: Report bugs and request features
- Discussion Forum: Get help from the community
- Wiki: Additional documentation and tutorials

### Professional Support
- Email: support@example.com
- Phone: +1-234-567-8900
- Slack: Join our community Slack

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

We welcome contributions! Please see our contributing guidelines for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## Acknowledgments

- Thanks to the open-source community for inspiration and tools
- Special thanks to contributors who helped build this system
- Thanks to our users for feedback and suggestions

---

*Last Updated: August 2025*
*Version: 1.0.0*
