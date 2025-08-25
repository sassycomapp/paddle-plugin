"""
Pytest configuration and shared fixtures for AG2 Orchestration System Tests
"""
import os
import sys
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Generator
import yaml
import json
from unittest.mock import Mock, patch

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Load test configuration from YAML file."""
    config_path = Path(__file__).parent / "config" / "test_config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Get the test data directory."""
    return Path(__file__).parent / "mock_data"

@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="session")
def mock_documents() -> Dict[str, str]:
    """Provide mock documents for testing."""
    return {
        "ag2_guide": """
        AG2 Multi-Agent Orchestration System
        
        The AG2 system is designed to coordinate multiple AI agents working together
        to solve complex tasks. It includes three specialized agents:
        
        1. Researcher Agent: Handles information gathering and knowledge retrieval
        2. Analyst Agent: Processes and analyzes data to provide insights
        3. Coordinator Agent: Manages task distribution and workflow orchestration
        
        Key Features:
        - Multi-agent coordination
        - RAG (Retrieval-Augmented Generation)
        - Memory management
        - Task scheduling
        - Error handling and recovery
        """,
        
        "python_guide": """
        Python Best Practices for AG2
        
        When implementing AG2 agents in Python, follow these guidelines:
        
        - Use async/await for concurrent operations
        - Implement proper error handling
        - Use type hints for better code clarity
        - Follow PEP 8 style guidelines
        - Write comprehensive tests
        - Document all public APIs
        
        Example:
        ```python
        async def process_task(self, task: Task) -> TaskResult:
            try:
                result = await self._execute_task(task)
                return TaskResult(success=True, data=result)
            except Exception as e:
                logger.error(f"Task failed: {e}")
                return TaskResult(success=False, error=str(e))
        ```
        """,
        
        "testing_guide": """
        Testing AG2 Components
        
        Comprehensive testing strategy for AG2:
        
        1. Unit Tests: Test individual components
        2. Integration Tests: Test component interactions
        3. End-to-End Tests: Test complete workflows
        4. Performance Tests: Test system performance
        5. Security Tests: Test security measures
        
        Use pytest with fixtures for setup/teardown.
        Mock external dependencies where appropriate.
        """,
        
        "deployment_guide": """
        AG2 Deployment Options
        
        Three deployment modes available:
        
        1. Pure Python: No external dependencies
        2. Lite Mode: Minimal external services
        3. Full Mode: Complete MCP integration
        
        Each mode has different requirements and capabilities.
        Choose based on your specific needs and constraints.
        """
    }

@pytest.fixture(scope="session")
def mock_queries() -> Dict[str, str]:
    """Provide mock queries for testing."""
    return {
        "simple": "What is AG2?",
        "complex": "How do the three agents in AG2 work together to solve complex tasks?",
        "technical": "What are the key Python best practices for implementing AG2 agents?",
        "deployment": "What are the different deployment modes available for AG2?",
        "testing": "What is the comprehensive testing strategy for AG2 components?"
    }

@pytest.fixture(scope="session")
def mock_expected_responses() -> Dict[str, Dict[str, Any]]:
    """Provide expected responses for testing."""
    return {
        "simple": {
            "query": "What is AG2?",
            "expected_keywords": ["multi-agent", "orchestration", "system", "agents"],
            "min_length": 50,
            "max_length": 500
        },
        "complex": {
            "query": "How do the three agents in AG2 work together?",
            "expected_keywords": ["researcher", "analyst", "coordinator", "work together"],
            "min_length": 100,
            "max_length": 1000
        }
    }

@pytest.fixture
def mock_env_vars():
    """Set up mock environment variables for testing."""
    env_vars = {
        'OPENAI_API_KEY': 'test-openai-key',
        'BRAVE_API_KEY': 'test-brave-key',
        'AGENT_MEMORY_PATH': '/tmp/test_memory',
        'RAG_DATA_PATH': '/tmp/test_rag',
        'LOG_LEVEL': 'DEBUG'
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def mock_ag2_pure():
    """Create a mock AG2 pure Python orchestrator."""
    from src.orchestration.ag2_pure import AG2PureOrchestrator
    
    orchestrator = AG2PureOrchestrator()
    yield orchestrator
    
    # Cleanup
    if hasattr(orchestrator, 'cleanup'):
        await orchestrator.cleanup()

@pytest.fixture
def mock_mcp_server():
    """Create a mock MCP server for testing."""
    mock_server = Mock()
    mock_server.name = "test-mcp-server"
    mock_server.version = "1.0.0"
    mock_server.capabilities = ["text_completion", "embedding", "search"]
    
    mock_server.complete_text = Mock(return_value="Mock response")
    mock_server.get_embedding = Mock(return_value=[0.1, 0.2, 0.3, 0.4, 0.5])
    mock_server.search = Mock(return_value=[{"title": "Test Result", "url": "http://test.com"}])
    
    return mock_server

@pytest.fixture
def sample_task():
    """Provide a sample task for testing."""
    return {
        "id": "test-task-001",
        "type": "research",
        "query": "What is AG2?",
        "priority": "medium",
        "context": {},
        "expected_output": "Detailed explanation of AG2"
    }

@pytest.fixture
def sample_agent_response():
    """Provide a sample agent response for testing."""
    return {
        "agent": "researcher",
        "task_id": "test-task-001",
        "status": "completed",
        "result": "AG2 is a multi-agent orchestration system...",
        "metadata": {
            "processing_time": 1.5,
            "tokens_used": 150,
            "confidence": 0.95
        }
    }

@pytest.fixture(scope="session")
def benchmark_data():
    """Provide benchmark data for performance testing."""
    return {
        "response_time_baseline": 2.0,  # seconds
        "memory_baseline": 100,  # MB
        "throughput_baseline": 10,  # requests per second
        "accuracy_baseline": 0.85  # percentage
    }
