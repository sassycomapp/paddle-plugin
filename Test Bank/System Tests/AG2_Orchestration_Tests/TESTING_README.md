# AG2 Orchestration System - Testing Guide

## Overview

This directory contains comprehensive tests for the AG2 orchestration system across three deployment modes:
- **Pure Python Mode**: Standalone implementation without external dependencies
- **Lite Mode**: MCP-based implementation with essential services
- **Full Mode**: Complete MCP-based implementation with all services

## Test Structure

```
AG2_Orchestration_Tests/
├── unit/                    # Unit tests for individual components
├── integration/            # Integration tests for component interactions
├── e2e/                   # End-to-end tests for complete workflows
├── config/                # Test configuration files
├── run_all_tests.py       # Comprehensive test runner
├── quick_test.py          # Quick verification tests
└── TESTING_README.md      # This documentation
```

## Quick Start

### 1. Install Dependencies
```bash
cd "Test Bank/System Tests/AG2_Orchestration_Tests"
pip install -r requirements.txt
```

### 2. Run Quick Tests
```bash
python quick_test.py
```

### 3. Run All Tests
```bash
python run_all_tests.py
```

## Test Categories

### Unit Tests (`unit/`)
- **Agent Tests**: Individual agent functionality
- **Memory Tests**: Memory storage and retrieval
- **Utility Tests**: Helper functions and utilities

### Integration Tests (`integration/`)
- **Orchestrator Tests**: Multi-agent coordination
- **Mode Compatibility**: Cross-mode functionality
- **Error Handling**: System resilience

### End-to-End Tests (`e2e/`)
- **Complete Workflows**: Full system scenarios
- **Real-World Usage**: Production-like scenarios
- **Performance**: Load and stress testing

## Test Markers

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.e2e`: End-to-end tests
- `@pytest.mark.asyncio`: Async tests

## Running Specific Test Suites

### Unit Tests Only
```bash
pytest unit/ -v -m unit
```

### Integration Tests Only
```bash
pytest integration/ -v -m integration
```

### End-to-End Tests Only
```bash
pytest e2e/ -v -m e2e
```

### Specific Test File
```bash
pytest unit/test_agents.py -v
```

### Specific Test Function
```bash
pytest unit/test_agents.py::TestResearcherAgent::test_researcher_agent_initialization -v
```

## Configuration

### Test Configuration (`config/test_config.yaml`)
```yaml
test_settings:
  timeout: 30
  max_retries: 3
  mock_external_services: true
  
memory_settings:
  test_memory_path: "./test_memory"
  cleanup_after_tests: true
  
rag_settings:
  mock_data_path: "../../../src/orchestration/mock_rag_data"
  use_mock_responses: true
```

## Mock Data

The tests use mock data from:
- `../../../src/orchestration/mock_rag_data/ag2_docs.json`
- Mock responses for external services
- Simulated memory storage

## Test Scenarios

### 1. Basic Functionality
- Agent initialization
- Query processing
- Memory operations

### 2. Error Handling
- Service failures
- Invalid inputs
- Network issues

### 3. Performance
- Concurrent queries
- Memory usage
- Response times

### 4. Compatibility
- Mode switching
- Cross-platform
- Version compatibility

## Environment Setup

### Required Environment Variables
```bash
export PYTHONPATH="${PYTHONPATH}:../../../src"
export AG2_TEST_MODE="true"
```

### Optional Environment Variables
```bash
export AG2_DEBUG="true"
export AG2_LOG_LEVEL="DEBUG"
export AG2_MEMORY_PATH="./test_memory"
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   export PYTHONPATH="${PYTHONPATH}:../../../src"
   ```

2. **Async Test Failures**
   - Ensure pytest-asyncio is installed
   - Check asyncio event loop configuration

3. **Memory Test Failures**
   - Check write permissions for test directories
   - Ensure cleanup between test runs

### Debug Mode
```bash
pytest -v --tb=long --log-cli-level=DEBUG
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: AG2 Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: python run_all_tests.py
```

## Performance Benchmarks

### Expected Performance
- **Unit Tests**: < 5 seconds
- **Integration Tests**: < 30 seconds
- **End-to-End Tests**: < 60 seconds
- **Memory Tests**: < 10 seconds

### Load Testing
- **Concurrent Queries**: 10 queries in < 5 seconds
- **Memory Usage**: < 100MB for 1000 queries
- **Response Time**: < 1 second per query

## Contributing Tests

### Adding New Tests
1. Create test file in appropriate directory
2. Add proper test markers
3. Include mock data if needed
4. Update this documentation
5. Run tests to verify

### Test Naming Convention
- `test_<component>_<scenario>_<expected_behavior>`
- Use descriptive names
- Group related tests in classes

### Example Test Structure
```python
@pytest.mark.unit
class TestResearcherAgent:
    """Test cases for ResearcherAgent."""
    
    def test_researcher_initialization_success(self):
        """Test successful initialization of researcher agent."""
        # Test implementation
    
    def test_researcher_initialization_failure(self):
        """Test initialization failure handling."""
        # Test implementation
```

## Support

For issues or questions:
1. Check this documentation
2. Review test output
3. Check GitHub issues
4. Contact development team
