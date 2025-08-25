# Token Management System Testing Guide

## Overview

This guide provides comprehensive instructions for testing the Token Management System, including unit tests, integration tests, performance tests, security tests, and end-to-end tests. The testing infrastructure is designed to ensure system reliability, correctness, and performance in production environments.

## Testing Philosophy

### Principles
- **Comprehensive Coverage**: Test all components of the token management system
- **Automated Testing**: Automate all tests to ensure consistent execution
- **Continuous Integration**: Integrate testing into CI/CD pipelines
- **Performance Focus**: Include performance and load testing for production readiness
- **Security First**: Implement security testing to identify vulnerabilities
- **Error Handling**: Test failure scenarios and error recovery

### Testing Pyramid
```
        ┌─ End-to-End Tests (5%) ─┐
        │                         │
    ┌─── Integration Tests (15%) ───┐
    │                               │
┌─── Unit Tests (80%) ──────────────┐
│                                   │
│  Core Components  |  Utilities   │
│  Token Counter    |  Decorators  │
│  Rate Limiter     |  Middleware  │
│  Security Manager |  Analytics   │
└───────────────────────────────────┘
```

## Test Structure

### Directory Layout
```
tests/
├── conftest.py                 # Test configuration and fixtures
├── test_token_counter.py       # Token counting unit tests
├── test_rate_limiter.py        # Rate limiting unit tests
├── test_token_security.py      # Security unit tests
├── test_token_monitoring.py    # Monitoring unit tests
├── test_token_usage_logger.py  # Logging unit tests
├── test_token_integration.py   # Integration tests
├── test_token_performance.py   # Performance tests
├── test_token_management_complete.py  # End-to-end tests
├── fixtures/                   # Test fixtures and mock data
│   ├── mock_responses.py       # Mock API responses
│   └── test_data.json          # Test data definitions
└── test_mcp_kilocode_integration.py  # MCP integration tests
```

### Test Categories

#### 1. Unit Tests
- **Purpose**: Test individual components in isolation
- **Coverage**: 80% of all test cases
- **Tools**: pytest, unittest, mock
- **Focus**: 
  - Token counting accuracy
  - Rate limiting logic
  - Security mechanisms
  - Performance metrics

#### 2. Integration Tests
- **Purpose**: Test component interactions
- **Coverage**: 15% of all test cases
- **Tools**: pytest, test containers, mock services
- **Focus**:
  - Database interactions
  - External service integrations
  - API endpoints
  - Message passing

#### 3. End-to-End Tests
- **Purpose**: Test complete workflows
- **Coverage**: 5% of all test cases
- **Tools**: pytest, selenium, httpx
- **Focus**:
  - Complete user journeys
  - System-wide functionality
  - Production-like environments

#### 4. Performance Tests
- **Purpose**: Test system performance under load
- **Tools**: pytest-benchmark, locust, jmeter
- **Focus**:
  - Token counting performance
  - Rate limiting under load
  - Database query performance
  - API response times

#### 5. Security Tests
- **Purpose**: Identify security vulnerabilities
- **Tools**: bandit, safety, semgrep
- **Focus**:
  - Authentication and authorization
  - Token security
  - Input validation
  - Data protection

## Running Tests

### Prerequisites
- Python 3.9+
- pip
- pytest
- PostgreSQL (for integration tests)

### Installation
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock
pip install pytest-benchmark pytest-html
pip install coverage black isort flake8 mypy
pip install httpx aiofastapi uvicorn
pip install psycopg2-binary python-dotenv
```

### Test Execution Scripts

#### 1. Using the Test Runner Script
```bash
# Run all tests
python scripts/run_tests.py --type all --verbose --coverage

# Run specific test type
python scripts/run_tests.py --type unit --verbose
python scripts/run_tests.py --type integration --verbose
python scripts/run_tests.py --type performance --verbose
python scripts/run_tests.py --type security --verbose
python scripts/run_tests.py --type e2e --verbose

# Run specific test file
python scripts/run_tests.py --test-file tests/test_token_counter.py --verbose
```

#### 2. Using pytest directly
```bash
# Run all tests
pytest -v --cov=src/token_management --cov-report=html

# Run with markers
pytest -v -m "not integration"
pytest -v -m "performance"
pytest -v -m "security"

# Run specific test file
pytest tests/test_token_counter.py -v
```

### Coverage Analysis
```bash
# Generate coverage report
python scripts/coverage_report.py --modules token_management --output-format all

# Generate HTML coverage report
python scripts/coverage_report.py --modules token_management --output-format html

# Generate JUnit XML for CI/CD
python scripts/coverage_report.py --modules token_management --output-format junit
```

## Test Configuration

### Environment Variables
```bash
# Database configuration
DATABASE_URL=postgresql://user:password@localhost:5432/token_management_test

# Vault configuration
VAULT_URL=http://localhost:8200
VAULT_TOKEN=s.1234567890

# External services
OPENAI_API_KEY=sk-test-key
ANTHROPIC_API_KEY=sk-ant-test-key

# Testing configuration
TEST_MODE=true
MOCK_EXTERNAL_SERVICES=true
PERFORMANCE_TESTING=true
```

### pytest Configuration
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=src
    --cov-report=term-missing
    --cov-report=html:coverage/html
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    security: Security tests
    e2e: End-to-end tests
    slow: Slow tests
```

## Test Fixtures

### Database Fixtures
```python
@pytest.fixture
def mock_db():
    """Mock database for testing."""
    return MockPostgresDB()

@pytest.fixture
def test_db():
    """Test database with real PostgreSQL."""
    # Setup test database
    db = TestPostgreSQLDatabase()
    yield db
    # Teardown
    db.cleanup()
```

### Service Fixtures
```python
@pytest.fixture
def token_counter(mock_db):
    """TokenCounter instance with mock database."""
    return TokenCounter(mock_db)

@pytest.fixture
def rate_limiter(mock_db):
    """RateLimiter instance with mock database."""
    return RateLimiter(mock_db)

@pytest.fixture
def token_security_manager():
    """TokenSecurityManager instance."""
    return TokenSecurityManager()
```

### Data Fixtures
```python
@pytest.fixture
def sample_texts():
    """Sample texts for token counting tests."""
    return {
        'simple': "Hello world",
        'complex': "This is a complex sentence with multiple words and punctuation!",
        'empty': "",
        'whitespace': "   ",
        'paragraph': """This is a paragraph with multiple sentences.
        It contains line breaks and various punctuation marks."""
    }

@pytest.fixture
def sample_users():
    """Sample user data."""
    return [
        {'id': 'user-1', 'name': 'Alice', 'email': 'alice@example.com'},
        {'id': 'user-2', 'name': 'Bob', 'email': 'bob@example.com'},
        {'id': 'user-3', 'name': 'Charlie', 'email': 'charlie@example.com'}
    ]
```

## Writing Tests

### Unit Test Example
```python
import pytest
from unittest.mock import Mock, patch
from src.token_management.token_counter import TokenCounter, TokenizationModel

class TestTokenCounter:
    """Test cases for TokenCounter class."""
    
    def test_count_tokens_empty_text(self, token_counter):
        """Test token counting with empty text."""
        result = token_counter.count_tokens("")
        assert result.token_count == 0
        assert result.method == 'fallback'
    
    def test_count_tokens_with_pg_tiktoken(self, token_counter, mock_db):
        """Test token counting with pg_tiktoken available."""
        mock_db.is_tiktoken_available.return_value = True
        mock_db.get_token_count.return_value = 15
        
        result = token_counter.count_tokens("Hello world")
        
        assert result.token_count == 15
        assert result.method == 'pg_tiktoken'
        assert result.model == TokenizationModel.CL100K_BASE
    
    @patch('src.token_management.token_counter.TokenCounter.count_tokens')
    def test_cache_functionality(self, mock_count, token_counter):
        """Test token count caching."""
        mock_count.return_value = Mock(token_count=10, cache_hit=False)
        
        # First call should miss cache
        result1 = token_counter.count_tokens("Hello world")
        assert not result1.cache_hit
        
        # Second call should hit cache
        result2 = token_counter.count_tokens("Hello world")
        assert result2.cache_hit
```

### Integration Test Example
```python
import pytest
import asyncio
from src.token_management.token_counter import TokenCounter
from src.token_usage_logger import TokenUsageLogger

class TestTokenIntegration:
    """Integration tests for token management components."""
    
    @pytest.mark.integration
    def test_token_counting_and_logging_integration(self, mock_db):
        """Test integration between token counting and logging."""
        # Setup components
        token_counter = TokenCounter(mock_db)
        logger = TokenUsageLogger(mock_db)
        
        # Count tokens
        result = token_counter.count_tokens("Hello world")
        
        # Log usage
        log_success = logger.log_token_usage(
            user_id="test-user",
            session_id="test-session",
            tokens_used=result.token_count,
            api_endpoint="/api/test",
            priority_level="Medium"
        )
        
        assert log_success
        assert len(mock_db.usage_records) == 1
        assert mock_db.usage_records[0]['tokens_used'] == result.token_count
    
    @pytest.mark.asyncio
    async def test_async_token_processing(self, mock_db):
        """Test async token processing."""
        token_counter = TokenCounter(mock_db)
        
        # Process multiple tokens asynchronously
        texts = ["Hello", "World", "Test"]
        tasks = [token_counter.count_tokens(text) for text in texts]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        assert all(result.token_count > 0 for result in results)
```

### Performance Test Example
```python
import pytest
import time
from src.token_management.token_counter import TokenCounter

class TestTokenPerformance:
    """Performance tests for token management."""
    
    @pytest.mark.performance
    def test_token_counting_performance(self, token_counter):
        """Test token counting performance."""
        text = "This is a test sentence for performance testing. " * 100
        
        # Measure performance
        start_time = time.time()
        for _ in range(100):
            token_counter.count_tokens(text)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 100
        assert avg_time < 0.1  # Should complete in under 100ms
    
    @pytest.mark.performance
    def test_batch_processing_performance(self, token_counter):
        """Test batch processing performance."""
        texts = ["Hello"] * 1000
        
        # Measure batch processing time
        start_time = time.time()
        batch_result = token_counter.count_tokens_batch(texts)
        batch_time = time.time() - start_time
        
        # Measure individual processing time
        start_time = time.time()
        individual_results = [token_counter.count_tokens(text) for text in texts]
        individual_time = time.time() - start_time
        
        # Batch should be more efficient
        assert batch_time < individual_time
        assert batch_result.total_tokens == sum(r.token_count for r in individual_results)
```

### Security Test Example
```python
import pytest
from src.token_management.token_security_manager import TokenSecurityManager

class TestTokenSecurity:
    """Security tests for token management."""
    
    @pytest.mark.security
    def test_token_storage_security(self):
        """Test token storage security."""
        security_manager = TokenSecurityManager()
        
        # Test token encryption
        token = "sk-test-token-12345"
        encrypted = security_manager.encrypt_token(token)
        
        assert encrypted != token
        assert not token in encrypted
        
        # Test token decryption
        decrypted = security_manager.decrypt_token(encrypted)
        assert decrypted == token
    
    @pytest.mark.security
    def test_input_validation(self):
        """Test input validation for security."""
        security_manager = TokenSecurityManager()
        
        # Test SQL injection prevention
        malicious_input = "'; DROP TABLE users; --"
        sanitized = security_manager.sanitize_input(malicious_input)
        
        assert "'" not in sanitized
        assert ";" not in sanitized
        assert "--" not in sanitized
    
    @pytest.mark.security
    def test_rate_limiting_security(self, mock_db):
        """Test rate limiting for security."""
        from src.token_management.rate_limiter import RateLimiter
        
        rate_limiter = RateLimiter(mock_db)
        
        # Test rapid fire requests
        user_id = "test-user"
        for i in range(100):
            allowed = rate_limiter.check_rate_limit(user_id, 1)
            if i >= 10:  # Should be rate limited after 10 requests
                assert not allowed
```

## Test Data Management

### Test Data Files
The `tests/fixtures/test_data.json` file contains comprehensive test data:

```json
{
  "users": [
    {
      "id": "user-1",
      "name": "Alice Johnson",
      "email": "alice@example.com",
      "token_limit": 10000,
      "priority_level": "high"
    }
  ],
  "api_endpoints": [
    {
      "path": "/api/chat/completions",
      "method": "POST",
      "token_cost_per_request": 100,
      "rate_limit": 60
    }
  ],
  "token_usage_records": [
    {
      "id": "usage-1",
      "user_id": "user-1",
      "tokens_used": 150,
      "api_endpoint": "/api/chat/completions"
    }
  ]
}
```

### Mock Responses
The `tests/fixtures/mock_responses.py` file contains mock API responses:

```python
MOCK_OPENAI_CHAT_RESPONSE = {
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1677652288,
    "model": "gpt-3.5-turbo",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you today?"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 9,
        "total_tokens": 19
    }
}
```

## Continuous Integration

### GitHub Actions Workflow
The `.github/workflows/test.yml` file defines the CI/CD pipeline:

```yaml
name: Token Management System Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC

jobs:
  test:
    strategy:
      matrix:
        test-type: [unit, integration, performance, security, e2e]
        python-version: ['3.9', '3.10', '3.11']
```

### CI/CD Features
- **Multi-Python Version Testing**: Tests on Python 3.9, 3.10, and 3.11
- **Parallel Execution**: Runs different test types in parallel
- **Automated Coverage**: Generates and uploads coverage reports
- **Security Scanning**: Runs bandit, safety, and semgrep
- **Performance Regression**: Detects performance regressions
- **Slack Notifications**: Alerts on test failures

## Test Reporting

### Test Results
Test results are saved in JSON format:

```json
{
  "unit_tests": {
    "success": true,
    "returncode": 0,
    "duration": 45.2,
    "timestamp": "2024-01-20T14:30:15Z"
  },
  "integration_tests": {
    "success": true,
    "returncode": 0,
    "duration": 120.5,
    "timestamp": "2024-01-20T14:32:15Z"
  }
}
```

### Coverage Reports
Coverage reports are generated in multiple formats:
- **HTML**: Interactive coverage reports
- **XML**: JUnit format for CI/CD integration
- **JSON**: Machine-readable coverage data
- **Text**: Human-readable summaries

### Performance Metrics
Performance tests track:
- Response times
- Throughput
- Memory usage
- CPU usage
- Error rates

## Best Practices

### Writing Good Tests
1. **Follow AAA Pattern**: Arrange, Act, Assert
2. **Use Descriptive Names**: Test names should clearly describe what is being tested
3. **Keep Tests Independent**: Tests should not depend on each other
4. **Mock External Dependencies**: Use mocks for external services
5. **Test Edge Cases**: Include tests for boundary conditions
6. **Maintain Testability**: Write code that is easy to test

### Test Organization
1. **Group Related Tests**: Use test classes to group related tests
2. **Use Fixtures**: Reuse test setup code with fixtures
3. **Parameterize Tests**: Use `@pytest.mark.parametrize` for data-driven tests
4. **Use Markers**: Mark tests with categories (unit, integration, etc.)
5. **Separate Concerns**: Keep unit tests fast, integration tests comprehensive

### Performance Considerations
1. **Optimize Test Setup**: Minimize test setup time
2. **Use Mocks**: Mock slow external services
3. **Parallelize Tests**: Run tests in parallel where possible
4. **Cache Dependencies**: Cache test dependencies between runs
5. **Monitor Test Performance**: Track test execution times

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues
```bash
# Check database configuration
echo $DATABASE_URL

# Test database connection
psql $DATABASE_URL -c "SELECT 1"

# Reset test database
python scripts/reset_test_database.py
```

#### 2. Coverage Issues
```bash
# Check coverage configuration
coverage run --source=src -m pytest
coverage report

# Generate detailed HTML report
coverage html
```

#### 3. Performance Issues
```bash
# Run performance tests with detailed output
pytest tests/test_token_performance.py --benchmark-only --benchmark-sort=mean

# Compare with baseline
pytest tests/test_token_performance.py --benchmark-compare=baseline.json
```

#### 4. Mock Service Issues
```bash
# Check mock service logs
tail -f logs/mock_services.log

# Restart mock services
python scripts/start_mock_services.py
```

### Debugging Tests
1. **Use Verbose Output**: `pytest -v --tb=long`
2. **Run Single Test**: `pytest tests/test_token_counter.py::TestTokenCounter::test_count_tokens`
3. **Use pdb**: Add `import pdb; pdb.set_trace()` to tests
4. **Check Logs**: Review test logs for detailed error information
5. **Isolate Tests**: Run tests in isolation to identify dependencies

## Conclusion

This testing guide provides comprehensive instructions for testing the Token Management System. By following these practices, you can ensure that the system is reliable, secure, and performs well in production environments.

For additional support or questions about testing, please refer to the project documentation or contact the development team.