@echo off
echo ============================================
echo   AG2 Orchestration System - Lite Setup
echo ============================================

echo Checking Python...
python --version
if errorlevel 1 (
    echo Error: Python not found. Please install Python from https://python.org/
    pause
    exit /b 1
)

echo Checking Node.js...
node --version
if errorlevel 1 (
    echo Error: Node.js not found. Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo Installing Python dependencies...
pip install pyyaml
if errorlevel 1 (
    echo Error: Failed to install Python dependencies
    pause
    exit /b 1
)

echo Installing Node.js dependencies...
cd ..\..\mcp_servers
npm install
if errorlevel 1 (
    echo Error: Failed to install Node.js dependencies
    pause
    exit /b 1
)

cd ..\src\orchestration

echo Creating directories...
mkdir mock_memory 2>nul
mkdir mock_rag_data 2>nul
mkdir logs 2>nul

echo Creating sample data...
python -c "import json, os; 
rag_data = {
    'ag2_overview': {
        'content': 'AG2 is an advanced orchestration system that coordinates multiple AI agents to perform complex tasks.',
        'metadata': {'source': 'mock_document', 'type': 'overview'}
    },
    'orchestration_benefits': {
        'content': 'The benefits of AG2 orchestration include improved task efficiency and better resource utilization.',
        'metadata': {'source': 'mock_document', 'type': 'benefits'}
    }
};
os.makedirs('mock_rag_data', exist_ok=True);
with open('mock_rag_data/sample_data.json', 'w') as f:
    json.dump(rag_data, f, indent=2)"

python -c "import json, os;
memory_data = {
    'agents': {
        'researcher': {
            'conversations': [],
            'context': {'expertise': ['research', 'analysis']}
        }
    }
};
os.makedirs('mock_memory', exist_ok=True);
with open('mock_memory/sample_memory.json', 'w') as f:
    json.dump(memory_data, f, indent=2)"

echo Creating configuration...
python -c "import json;
config = {
    'mcpServers': {
        'rag': {
            'command': 'node',
            'args': ['../../mcp_servers/rag-mcp-server-lite.js'],
            'env': {'MOCK_DATA_PATH': 'mock_rag_data'}
        },
        'agent-memory': {
            'command': 'node',
            'args': ['../../mcp_servers/agent-memory-lite.js'],
            'env': {'MEMORY_PATH': 'mock_memory'}
        },
        'brave-search': {
            'command': 'node',
            'args': ['../../mcp_servers/brave-search-mcp-server-lite.js'],
            'env': {'MOCK_MODE': 'true'}
        }
    }
};
with open('mcp_servers_config_lite.json', 'w') as f:
    json.dump(config, f, indent=2)"

echo ============================================
echo Setup completed successfully!
echo ============================================
echo Next steps:
echo 1. Test the setup: python test_lite.py
echo 2. Run the system: python run_lite.py
echo 3. Check logs in: logs\
pause
