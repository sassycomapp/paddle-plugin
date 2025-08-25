# AG2 Orchestration System - Comprehensive Test Suite

## Overview
This test suite provides comprehensive testing for the AG2 Multi-Agent Orchestration System across all deployment modes (Full MCP, Lite, and Pure Python).

## Test Structure

### Directory Layout
```
AG2_Orchestration_Tests/
├── unit/                    # Unit tests for individual components
├── integration/            # Integration tests for component interactions
├── e2e/                    # End-to-end system tests
├── performance/            # Performance and load tests
├── load/                   # Load testing scenarios
├── security/               # Security and vulnerability tests
├── mock_data/              # Test data and mock objects
├── reports/                # Test execution reports
├── config/                 # Test configuration files
└── README.md              # This file
```

### Test Categories

#### 1. Unit Tests (`unit/`)
- **Agent Tests**: Individual agent functionality
- **Component Tests**: Core system components
- **Utility Tests**: Helper functions and utilities
- **Mock Tests**: Mock server functionality

#### 2. Integration Tests (`integration/`)
- **Agent Communication**: Inter-agent messaging
- **MCP Integration**: External service integration
- **RAG System**: Vector search and retrieval
- **Memory System**: Storage and retrieval operations

#### 3. End-to-End Tests (`e2e/`)
- **Full System Flow**: Complete user workflows
- **Deployment Modes**: Testing all three deployment modes
- **Error Handling**: System resilience and recovery
- **User Scenarios**: Real-world usage patterns

#### 4. Performance Tests (`performance/`)
- **Response Time**: Query processing benchmarks
- **Memory Usage**: Resource consumption analysis
- **Scalability**: System scaling behavior
- **Throughput**: Concurrent request handling

#### 5. Load Tests (`load/`)
- **Stress Testing**: System under extreme load
- **Concurrent Users**: Multiple simultaneous users
- **Resource Limits**: Memory and CPU boundaries
- **Recovery Testing**: System recovery from failures

#### 6. Security Tests (`security/`)
- **API Security**: Authentication and authorization
- **Data Protection**: Sensitive data handling
- **Input Validation**: Malicious input handling
- **Access Control**: Permission and role testing

## Quick Start

### Prerequisites
- Python 3.8+
- pytest
- pytest-asyncio
- pytest-cov
- pytest-benchmark
- requests
- aiohttp

### Installation
```bash
cd AG2_Orchestration_Tests
pip install -r requirements.txt
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test category
pytest unit/
pytest integration/
pytest e2e/

# Run with coverage
pytest --cov=src --cov-report=html

# Run performance tests
pytest performance/ --benchmark-only

# Run security tests
pytest security/ -v
```

### Configuration
Copy `config/test_config.example.yaml` to `config/test_config.yaml` and customize settings.

## Test Data
- **Mock documents**: Located in `mock_data/documents/`
- **Test queries**: Located in `mock_data/queries/`
- **Expected responses**: Located in `mock_data/expected/`
- **Configuration templates**: Located in `config/templates/`

## Reporting
- **HTML reports**: Generated in `reports/html/`
- **JSON reports**: Generated in `reports/json/`
- **Performance reports**: Generated in `reports/performance/`
- **Coverage reports**: Generated in `reports/coverage/`

## Continuous Integration
Tests are configured to run automatically on:
- Code commits
- Pull requests
- Scheduled runs (daily)
- Manual triggers

## Troubleshooting
See `docs/troubleshooting.md` for common issues and solutions.
