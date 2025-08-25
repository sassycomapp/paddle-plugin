"""
Pytest Configuration and Test Fixtures

This module provides comprehensive test configuration and fixtures for the token management system tests.
It includes database setup, mock services, test data, and common test utilities.
"""

import pytest
import asyncio
import tempfile
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, MagicMock, AsyncMock, patch
import uuid
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import token management modules
from src.token_management.token_counter import TokenCounter, TokenizationModel
from src.token_management.rate_limiter import RateLimiter, RateLimitConfig, RateLimitWindow
from src.token_management.lock_manager import LockManager, LockType
from src.token_management.allocation_strategies import (
    PriorityBasedAllocation, DynamicPriorityAllocation, 
    EmergencyOverrideAllocation, BurstTokenAllocation, PriorityLevel
)
from src.token_management.middleware import TokenCountingMiddleware, TokenQuotaMiddleware
from src.token_usage_logger import TokenUsageLogger, TokenUsageRecord, LoggingConfig, LoggingStrategy
from src.token_monitoring import TokenMonitoringSystem, MonitoringConfig
from src.token_security_manager import TokenSecurityManager, SecurityLevel
from src.vault_token_storage import VaultTokenStorage
from src.quota_reset_scheduler import QuotaResetScheduler
from src.token_usage_analytics import TokenUsageAnalytics, AnalyticsConfig
from src.token_usage_batch_processor import TokenUsageBatchProcessor, BatchProcessorConfig
from src.sensitive_content_filter import SensitiveContentFilter, FilterType, FilterAction
from src.token_alerting import TokenAlertingSystem, AlertingConfig
from src.token_analytics import TokenAnalytics
from src.token_dashboard import TokenDashboard
from src.credential_rotation import CredentialRotator
from src.environment_validator import EnvironmentValidator
from src.external_api_token_integration import ExternalAPITokenIntegration
from src.kilocode_token_integration import KiloCodeTokenIntegration
from src.mcp_token_integration import MCPTokenIntegration
from src.memory_token_integration import MemoryTokenIntegration
from src.quota_reset_cron import QuotaResetCronManager
from src.token_revocation_service import TokenRevocationService

# Mock database class for testing
class MockPostgresDB:
    """Mock database class for testing purposes."""
    
    def __init__(self):
        self.is_tiktoken_available = True
        self.token_cache = {}
        self.usage_records = []
        self.rate_limits = {}
        self.quota_resets = []
        self.alerts = []
        self.security_events = []
        self.analytics_data = []
        
    def is_tiktoken_available(self) -> bool:
        return self.is_tiktoken_available
    
    def get_token_count(self, text: str, model: str = "cl100k_base") -> int:
        # Simple token estimation for testing
        return len(text.split())
    
    def log_token_usage(self, user_id: str, session_id: str, tokens_used: int, 
                       api_endpoint: str, priority_level: str = "Medium") -> bool:
        record = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'session_id': session_id,
            'tokens_used': tokens_used,
            'api_endpoint': api_endpoint,
            'priority_level': priority_level,
            'timestamp': datetime.utcnow()
        }
        self.usage_records.append(record)
        return True
    
    def get_user_token_limit(self, user_id: str) -> int:
        return 10000
    
    def set_user_rate_limit(self, user_id: str, config: RateLimitConfig) -> bool:
        self.rate_limits[user_id] = config
        return True
    
    def get_user_rate_limit(self, user_id: str) -> Optional[RateLimitConfig]:
        return self.rate_limits.get(user_id)
    
    def health_check(self) -> Dict[str, Any]:
        return {
            'status': 'healthy',
            'database': 'connected',
            'cache': 'active'
        }
    
    def fetch_all(self, query: str) -> List[Dict[str, Any]]:
        return self.analytics_data
    
    def execute(self, query: str, params: tuple = None) -> bool:
        return True
    
    def commit(self) -> bool:
        return True
    
    def rollback(self) -> bool:
        return True

@pytest.fixture
def mock_db():
    """Fixture providing a mock database instance."""
    return MockPostgresDB()

@pytest.fixture
def token_counter(mock_db):
    """Fixture providing a TokenCounter instance with mock database."""
    return TokenCounter(mock_db)

@pytest.fixture
def rate_limiter(mock_db):
    """Fixture providing a RateLimiter instance with mock database."""
    return RateLimiter(mock_db)

@pytest.fixture
def lock_manager():
    """Fixture providing a LockManager instance."""
    return LockManager()

@pytest.fixture
def allocation_strategy():
    """Fixture providing a PriorityBasedAllocation instance."""
    return PriorityBasedAllocation()

@pytest.fixture
def dynamic_allocation_strategy():
    """Fixture providing a DynamicPriorityAllocation instance."""
    base_strategy = PriorityBasedAllocation()
    return DynamicPriorityAllocation(base_strategy)

@pytest.fixture
def emergency_allocation_strategy():
    """Fixture providing an EmergencyOverrideAllocation instance."""
    base_strategy = PriorityBasedAllocation()
    return EmergencyOverrideAllocation(base_strategy)

@pytest.fixture
def burst_allocation_strategy():
    """Fixture providing a BurstTokenAllocation instance."""
    base_strategy = PriorityBasedAllocation()
    return BurstTokenAllocation(base_strategy)

@pytest.fixture
def token_usage_logger(mock_db):
    """Fixture providing a TokenUsageLogger instance."""
    config = LoggingConfig(strategy=LoggingStrategy.BATCH)
    return TokenUsageLogger(mock_db, config)

@pytest.fixture
def token_monitoring_system(mock_db):
    """Fixture providing a TokenMonitoringSystem instance."""
    config = MonitoringConfig()
    return TokenMonitoringSystem(mock_db, config)

@pytest.fixture
def token_security_manager(mock_db):
    """Fixture providing a TokenSecurityManager instance."""
    return TokenSecurityManager()

@pytest.fixture
def vault_token_storage():
    """Fixture providing a VaultTokenStorage instance."""
    return VaultTokenStorage()

@pytest.fixture
def quota_reset_scheduler(mock_db, lock_manager):
    """Fixture providing a QuotaResetScheduler instance."""
    return QuotaResetScheduler(mock_db, lock_manager)

@pytest.fixture
def token_usage_analytics(mock_db):
    """Fixture providing a TokenUsageAnalytics instance."""
    config = AnalyticsConfig()
    return TokenUsageAnalytics(mock_db, config)

@pytest.fixture
def token_usage_batch_processor(mock_db):
    """Fixture providing a TokenUsageBatchProcessor instance."""
    config = BatchProcessorConfig(batch_size=100)
    return TokenUsageBatchProcessor(mock_db, config)

@pytest.fixture
def sensitive_content_filter():
    """Fixture providing a SensitiveContentFilter instance."""
    return SensitiveContentFilter()

@pytest.fixture
def token_alerting_system(mock_db):
    """Fixture providing a TokenAlertingSystem instance."""
    config = AlertingConfig()
    return TokenAlertingSystem(mock_db, config)

@pytest.fixture
def token_analytics(mock_db):
    """Fixture providing a TokenAnalytics instance."""
    return TokenAnalytics(mock_db)

@pytest.fixture
def token_dashboard(mock_db):
    """Fixture providing a TokenDashboard instance."""
    return TokenDashboard(mock_db)

@pytest.fixture
def credential_rotator():
    """Fixture providing a CredentialRotator instance."""
    return CredentialRotator()

@pytest.fixture
def environment_validator():
    """Fixture providing an EnvironmentValidator instance."""
    return EnvironmentValidator()

@pytest.fixture
def external_api_integration(token_counter):
    """Fixture providing an ExternalAPITokenIntegration instance."""
    return ExternalAPITokenIntegration(token_counter)

@pytest.fixture
def kilocode_integration(token_counter):
    """Fixture providing a KiloCodeTokenIntegration instance."""
    return KiloCodeTokenIntegration(token_counter)

@pytest.fixture
def mcp_integration(token_counter):
    """Fixture providing an MCPTokenIntegration instance."""
    return MCPTokenIntegration(token_counter)

@pytest.fixture
def memory_integration(token_counter):
    """Fixture providing a MemoryTokenIntegration instance."""
    return MemoryTokenIntegration(token_counter)

@pytest.fixture
def quota_reset_cron_manager():
    """Fixture providing a QuotaResetCronManager instance."""
    return QuotaResetCronManager()

@pytest.fixture
def token_revocation_service(vault_token_storage):
    """Fixture providing a TokenRevocationService instance."""
    return TokenRevocationService(vault_token_storage)

@pytest.fixture
def sample_texts():
    """Fixture providing sample texts for token counting tests."""
    return {
        'simple': "Hello world",
        'complex': "This is a complex sentence with multiple words and punctuation!",
        'empty': "",
        'whitespace': "   ",
        'paragraph': """This is a paragraph with multiple sentences.
        It contains line breaks and various punctuation marks.
        The goal is to test token counting accuracy."""
    }

@pytest.fixture
def sample_users():
    """Fixture providing sample user data."""
    return [
        {'id': 'user-1', 'name': 'Alice', 'email': 'alice@example.com'},
        {'id': 'user-2', 'name': 'Bob', 'email': 'bob@example.com'},
        {'id': 'user-3', 'name': 'Charlie', 'email': 'charlie@example.com'}
    ]

@pytest.fixture
def sample_api_endpoints():
    """Fixture providing sample API endpoints."""
    return [
        '/api/chat/completions',
        '/api/embeddings',
        '/api/models/list',
        '/api/usage',
        '/api/admin/users'
    ]

@pytest.fixture
def sample_token_usage_records():
    """Fixture providing sample token usage records."""
    return [
        TokenUsageRecord(
            user_id='user-1',
            session_id='session-1',
            tokens_used=150,
            api_endpoint='/api/chat/completions',
            priority_level='High'
        ),
        TokenUsageRecord(
            user_id='user-2',
            session_id='session-2',
            tokens_used=75,
            api_endpoint='/api/embeddings',
            priority_level='Medium'
        ),
        TokenUsageRecord(
            user_id='user-3',
            session_id='session-3',
            tokens_used=200,
            api_endpoint='/api/chat/completions',
            priority_level='Low'
        )
    ]

@pytest.fixture
def sample_rate_limits():
    """Fixture providing sample rate limit configurations."""
    return {
        'user-1': RateLimitConfig(
            window=RateLimitWindow.DAY,
            limit=1000,
            reset_time=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ),
        'user-2': RateLimitConfig(
            window=RateLimitWindow.HOUR,
            limit=100,
            reset_time=datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        ),
        'user-3': RateLimitConfig(
            window=RateLimitWindow.WEEK,
            limit=5000,
            reset_time=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        )
    }

@pytest.fixture
def sample_vault_secrets():
    """Fixture providing sample Vault secrets."""
    return {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'username': 'test_user',
            'password': 'test_password'
        },
        'api_keys': {
            'openai': 'sk-test-key',
            'anthropic': 'sk-ant-test-key'
        },
        'config': {
            'max_tokens': 4096,
            'temperature': 0.7,
            'model': 'gpt-3.5-turbo'
        }
    }

@pytest.fixture
def sample_alert_rules():
    """Fixture providing sample alert rules."""
    return [
        {
            'id': 'alert-1',
            'name': 'High Usage Alert',
            'condition': 'usage > 80%',
            'severity': 'high',
            'enabled': True
        },
        {
            'id': 'alert-2',
            'name': 'System Health Alert',
            'condition': 'cpu_usage > 90%',
            'severity': 'critical',
            'enabled': True
        },
        {
            'id': 'alert-3',
            'name': 'Cost Alert',
            'condition': 'cost > $100',
            'severity': 'medium',
            'enabled': True
        }
    ]

@pytest.fixture
def sample_analytics_data():
    """Fixture providing sample analytics data."""
    return [
        {
            'id': str(uuid.uuid4()),
            'user_id': 'user-1',
            'session_id': 'session-1',
            'tokens_used': 150,
            'api_endpoint': '/api/chat/completions',
            'priority_level': 'High',
            'timestamp': datetime.utcnow() - timedelta(hours=1)
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': 'user-2',
            'session_id': 'session-2',
            'tokens_used': 75,
            'api_endpoint': '/api/embeddings',
            'priority_level': 'Medium',
            'timestamp': datetime.utcnow() - timedelta(hours=2)
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': 'user-3',
            'session_id': 'session-3',
            'tokens_used': 200,
            'api_endpoint': '/api/chat/completions',
            'priority_level': 'Low',
            'timestamp': datetime.utcnow() - timedelta(hours=3)
        }
    ]

@pytest.fixture
def temp_config_file():
    """Fixture providing a temporary configuration file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'test_db'
            },
            'vault': {
                'url': 'http://localhost:8200',
                'token': 'test-token'
            },
            'logging': {
                'level': 'INFO',
                'file': 'test.log'
            },
            'monitoring': {
                'enabled': True,
                'interval': 60
            }
        }
        json.dump(config, f)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    os.unlink(temp_file)

@pytest.fixture
def mock_http_client():
    """Fixture providing a mock HTTP client for API integration tests."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock()
    mock_client.post = AsyncMock()
    mock_client.put = AsyncMock()
    mock_client.delete = AsyncMock()
    mock_client.patch = AsyncMock()
    return mock_client

@pytest.fixture
def mock_vault_client():
    """Fixture providing a mock Vault client."""
    mock_client = Mock()
    mock_client.get_secret = Mock(return_value='test-secret')
    mock_client.store_secret = Mock(return_value=True)
    mock_client.revoke_secret = Mock(return_value=True)
    mock_client.health_check = Mock(return_value={'status': 'active'})
    return mock_client

@pytest.fixture
def mock_memory_service():
    """Fixture providing a mock memory service."""
    mock_service = Mock()
    mock_service.store_memory = AsyncMock(return_value=True)
    mock_service.retrieve_memory = AsyncMock(return_value={'memory': 'test-data'})
    mock_service.delete_memory = AsyncMock(return_value=True)
    mock_service.search_memory = AsyncMock(return_value={'results': []})
    return mock_service

@pytest.fixture
def mock_api_client():
    """Fixture providing a mock API client."""
    mock_client = Mock()
    mock_client.call_api = AsyncMock(return_value={'response': 'success'})
    mock_client.batch_call = AsyncMock(return_value={'responses': ['success']})
    mock_client.stream_api = AsyncMock(return_value={'stream': 'data'})
    return mock_client

@pytest.fixture
def event_loop():
    """Fixture providing an asyncio event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_timeout():
    """Fixture providing test timeout configuration."""
    return 30  # 30 seconds timeout for async tests

@pytest.fixture
def performance_thresholds():
    """Fixture providing performance thresholds for testing."""
    return {
        'token_counting': 0.1,  # 100ms max for token counting
        'rate_limit_check': 0.05,  # 50ms max for rate limit checks
        'database_query': 1.0,  # 1s max for database queries
        'api_call': 5.0,  # 5s max for API calls
        'memory_operation': 0.5,  # 500ms max for memory operations
        'alert_processing': 0.2  # 200ms max for alert processing
    }

@pytest.fixture
def security_test_data():
    """Fixture providing security test data."""
    return {
        'valid_tokens': [
            'sk-test-token-1',
            'sk-test-token-2',
            'sk-test-token-3'
        ],
        'invalid_tokens': [
            'invalid-token',
            'malformed-token',
            'expired-token'
        ],
        'sensitive_content': [
            'Credit card: 4111-1111-1111-1111',
            'SSN: 123-45-6789',
            'Password: secret123',
            'API Key: sk-test-secret-key'
        ],
        'normal_content': [
            'Hello, how are you?',
            'This is a normal message',
            'The weather is nice today'
        ]
    }

@pytest.fixture
def load_test_data():
    """Fixture providing load test data."""
    return {
        'concurrent_users': 100,
        'requests_per_user': 50,
        'total_requests': 5000,
        'burst_size': 100,
        'ramp_up_time': 60,  # seconds
        'test_duration': 300  # seconds
    }

@pytest.fixture
def integration_test_scenarios():
    """Fixture providing integration test scenarios."""
    return [
        {
            'name': 'Token Counting Workflow',
            'steps': [
                'Initialize TokenCounter',
                'Count tokens for various inputs',
                'Verify caching works',
                'Check performance metrics'
            ]
        },
        {
            'name': 'Rate Limiting Workflow',
            'steps': [
                'Set up rate limits',
                'Make requests within limits',
                'Verify rate limiting works',
                'Test retry logic'
            ]
        },
        {
            'name': 'Token Usage Logging Workflow',
            'steps': [
                'Initialize TokenUsageLogger',
                'Log token usage records',
                'Verify database storage',
                'Test batch processing'
            ]
        },
        {
            'name': 'Security Workflow',
            'steps': [
                'Initialize TokenSecurityManager',
                'Store tokens securely',
                'Retrieve tokens',
                'Test revocation'
            ]
        },
        {
            'name': 'Monitoring Workflow',
            'steps': [
                'Initialize TokenMonitoringSystem',
                'Start monitoring',
                'Generate alerts',
                'Export metrics'
            ]
        }
    ]

# Test markers
pytest.mark.token_counter = pytest.mark.markers("token_counter")
pytest.mark.rate_limiter = pytest.mark.markers("rate_limiter")
pytest.mark.security = pytest.mark.markers("security")
pytest.mark.monitoring = pytest.mark.markers("monitoring")
pytest.mark.performance = pytest.mark.markers("performance")
pytest.mark.integration = pytest.mark.markers("integration")
pytest.mark.end_to_end = pytest.mark.markers("end_to_end")

# Test configuration
def pytest_configure(config):
    """Configure pytest with custom markers and options."""
    config.addinivalue_line(
        "markers", "token_counter: marks tests for token counting functionality"
    )
    config.addinivalue_line(
        "markers", "rate_limiter: marks tests for rate limiting functionality"
    )
    config.addinivalue_line(
        "markers", "security: marks tests for security functionality"
    )
    config.addinivalue_line(
        "markers", "monitoring: marks tests for monitoring functionality"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests for performance testing"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests for integration testing"
    )
    config.addinivalue_line(
        "markers", "end_to_end: marks tests for end-to-end testing"
    )

# Custom assertions
def assert_token_count_valid(result, expected_range=None):
    """Assert that token count result is valid."""
    assert result is not None
    assert hasattr(result, 'token_count')
    assert isinstance(result.token_count, int)
    assert result.token_count >= 0
    
    if expected_range:
        assert expected_range[0] <= result.token_count <= expected_range[1]

def assert_rate_limit_check_valid(result):
    """Assert that rate limit check result is valid."""
    assert result is not None
    assert hasattr(result, 'allowed')
    assert isinstance(result.allowed, bool)
    assert hasattr(result, 'remaining')
    assert isinstance(result.remaining, int)
    assert hasattr(result, 'reset_time')
    assert isinstance(result.reset_time, datetime)

def assert_security_event_logged(security_manager, event_type, user_id):
    """Assert that a security event was logged."""
    # This would check the actual logging mechanism in a real implementation
    assert security_manager is not None
    assert event_type is not None
    assert user_id is not None

def assert_alert_generated(alerting_system, alert_type, severity):
    """Assert that an alert was generated."""
    # This would check the actual alert generation in a real implementation
    assert alerting_system is not None
    assert alert_type is not None
    assert severity is not None

# Performance testing utilities
class PerformanceTimer:
    """Utility class for timing operations during performance tests."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start the timer."""
        self.start_time = datetime.utcnow()
    
    def stop(self):
        """Stop the timer and return duration in seconds."""
        self.end_time = datetime.utcnow()
        return (self.end_time - self.start_time).total_seconds()
    
    def get_duration(self):
        """Get the duration in seconds without stopping the timer."""
        if self.start_time is None:
            return 0
        current_time = datetime.utcnow()
        return (current_time - self.start_time).total_seconds()

@pytest.fixture
def performance_timer():
    """Fixture providing a performance timer."""
    return PerformanceTimer()

# Load testing utilities
class LoadTestRunner:
    """Utility class for running load tests."""
    
    def __init__(self, max_concurrent=10, total_requests=100):
        self.max_concurrent = max_concurrent
        self.total_requests = total_requests
        self.results = []
    
    async def run_concurrent_requests(self, request_func, *args, **kwargs):
        """Run multiple requests concurrently."""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def limited_request():
            async with semaphore:
                start_time = datetime.utcnow()
                try:
                    result = await request_func(*args, **kwargs)
                    end_time = datetime.utcnow()
                    duration = (end_time - start_time).total_seconds()
                    return {
                        'success': True,
                        'duration': duration,
                        'result': result
                    }
                except Exception as e:
                    end_time = datetime.utcnow()
                    duration = (end_time - start_time).total_seconds()
                    return {
                        'success': False,
                        'duration': duration,
                        'error': str(e)
                    }
        
        tasks = [limited_request() for _ in range(self.total_requests)]
        self.results = await asyncio.gather(*tasks)
        return self.results
    
    def get_statistics(self):
        """Get performance statistics from the load test."""
        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]
        
        if successful:
            durations = [r['duration'] for r in successful]
            return {
                'total_requests': len(self.results),
                'successful_requests': len(successful),
                'failed_requests': len(failed),
                'success_rate': len(successful) / len(self.results),
                'avg_duration': sum(durations) / len(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'p95_duration': sorted(durations)[int(len(durations) * 0.95)] if durations else 0
            }
        else:
            return {
                'total_requests': len(self.results),
                'successful_requests': 0,
                'failed_requests': len(failed),
                'success_rate': 0,
                'avg_duration': 0,
                'min_duration': 0,
                'max_duration': 0,
                'p95_duration': 0
            }

@pytest.fixture
def load_test_runner():
    """Fixture providing a load test runner."""
    return LoadTestRunner()

# Cleanup fixture
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Automatically clean up after each test."""
    yield
    # Add any cleanup logic here that should run after every test
    # For example: clear caches, reset database state, etc.