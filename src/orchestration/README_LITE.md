# AG2 Orchestration System - Lite Mode

This is a simplified version of the AG2 orchestration system that runs without requiring API keys or external services. It uses mock servers to simulate the functionality of the full system.

## Overview

The lite mode provides:
- **Mock RAG server** - Simulates document retrieval without actual vector databases
- **Mock Memory server** - Simulates agent memory without persistent storage
- **Mock Search server** - Simulates web search without actual API calls
- **Interactive testing** - Query the system and see responses
- **No API keys required** - Perfect for testing and development

## Quick Start

### Prerequisites
- Python 3.7+
- Node.js 14+
- npm (comes with Node.js)

### Setup (One Command)

**Windows:**
```bash
setup_lite.bat
```

**Linux/Mac:**
```bash
python setup_lite.py
```

### Manual Setup (if needed)

1. **Install Python dependencies:**
   ```bash
   pip install pyyaml
   ```

2. **Install Node.js dependencies:**
   ```bash
   cd ../../mcp_servers
   npm install
   cd ../src/orchestration
   ```

3. **Create directories:**
   ```bash
   mkdir mock_memory mock_rag_data logs
   ```

4. **Create configuration:**
   ```bash
   python setup_lite.py
   ```

## Usage

### Test the System
```bash
python test_lite.py
```

### Run the System
```bash
python run_lite.py
```

### Interactive Mode
Once running, you can interact with the system:
```
> What is AG2?
Response: AG2 is an advanced orchestration system that coordinates multiple AI agents...

> How does orchestration work?
Response: The benefits of AG2 orchestration include improved task efficiency...
```

## File Structure

```
src/orchestration/
├── README_LITE.md              # This file
├── setup_lite.py               # Python setup script
├── setup_lite.bat              # Windows batch setup
├── test_lite.py                # Test script
├── run_lite.py                 # Run script
├── mcp_servers_config_lite.json # Configuration
├── mock_rag_data/              # Mock RAG data
│   └── sample_data.json
├── mock_memory/                # Mock memory data
│   └── sample_memory.json
└── logs/                       # Log files
```

## Mock Data

The system comes with sample mock data:

### RAG Data
- **ag2_overview**: Basic description of AG2
- **orchestration_benefits**: Benefits of using AG2
- **agent_roles**: Description of different agent types

### Memory Data
- **researcher**: Research agent with expertise in analysis
- **coordinator**: Coordination agent for task management
- **memory**: Memory agent for context storage

## Troubleshooting

### Common Issues

1. **Python not found**
   - Install Python from https://python.org/
   - Add Python to PATH

2. **Node.js not found**
   - Install Node.js from https://nodejs.org/
   - Restart terminal after installation

3. **Module not found errors**
   - Run `pip install pyyaml`
   - Run `npm install` in mcp_servers directory

4. **Permission errors**
   - On Windows: Run as Administrator
   - On Linux/Mac: Use `sudo` if needed

### Debug Mode

Enable debug logging by setting:
```bash
export DEBUG=true  # Linux/Mac
set DEBUG=true     # Windows
```

## Extending the System

### Adding More Mock Data

1. **Add RAG documents:**
   ```json
   {
     "new_document": {
       "content": "Your content here...",
       "metadata": {
         "source": "custom",
         "type": "documentation"
       }
     }
   }
   ```

2. **Add memory contexts:**
   ```json
   {
     "new_agent": {
       "conversations": [],
       "context": {
         "expertise": ["new_skill"],
         "preferences": {}
       }
     }
   }
   ```

### Customizing Mock Responses

Edit the mock server files:
- `mcp_servers/rag-mcp-server-lite.js`
- `mcp_servers/agent-memory-lite.js`
- `mcp_servers/brave-search-mcp-server-lite.js`

## Architecture

The lite system uses the same architecture as the full system:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AG2           │    │   Mock RAG       │    │   Mock Memory   │
│   Orchestrator  │◄──►│   Server         │◄──►│   Server        │
│                 │    │   (Lite)         │    │   (Lite)        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                        ▲                        ▲
         │                        │                        │
         └────────────────────────┴────────────────────────┘
                    Mock Search Server (Lite)
```

## Next Steps

After testing with the lite mode:

1. **Get API keys** for the full system
2. **Replace mock servers** with real ones
3. **Configure production settings**
4. **Deploy to production**

## Support

For issues with the lite setup:
1. Check the logs in `logs/`
2. Run `python test_lite.py` for diagnostics
3. Review this README
4. Check the main documentation in `README.md`
