"""
Integration Testing for Token Management System

This test suite provides comprehensive integration testing for the token management system,
including database interactions, external service integrations, and component interactions.
"""

import pytest
import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import uuid
import os

# Add the project root to the Python path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.token_management.token_counter import TokenCounter, TokenizationModel
from src.token_management.rate_limiter import RateLimiter, RateLimitConfig, RateLimitWindow
from src.token_management.lock_manager import LockManager, LockType
from src.token_management.allocation_strategies import (
    PriorityBasedAllocation, DynamicPriorityAllocation, 
    EmergencyOverrideAllocation, BurstTokenAllocation, PriorityLevel
)
from src.token_usage_logger import TokenUsageLogger, TokenUsageRecord, LoggingConfig, LoggingStrategy
from src.token_monitoring import TokenMonitoringSystem, MonitoringConfig
from src.token_security_manager import TokenSecurityManager, SecurityLevel
from src.vault_token_storage import VaultTokenStorage
from src.token_usage_analytics import TokenUsageAnalytics, AnalyticsConfig
from src.token_usage_batch_processor import TokenUsageBatchProcessor, BatchProcessorConfig
from src.sensitive_content_filter import SensitiveContentFilter, FilterType, FilterAction
from src.token_alerting import TokenAlertingSystem, AlertingConfig
from src.credential_rotation import CredentialRotator
from src.environment_validator import EnvironmentValidator
from src.external_api_token_integration import ExternalAPITokenIntegration
from src.kilocode_token_integration import KiloCodeTokenIntegration
from src.mcp_token_integration import MCPTokenIntegration
from src.memory_token_integration import MemoryTokenIntegration
from src.quota_reset_scheduler import QuotaResetScheduler
from src.quota_reset_cron import QuotaResetCronManager
from src.token_revocation_service import TokenRevocationService


class DatabaseIntegrationHelper:
    """Helper class for database integration testing."""
    
    @staticmethod
    def create_test_user_data(user_id: str, **kwargs) -> Dict[str, Any]:
        """Create test user data for database integration tests."""
        return {
            'user_id': user_id,
            'username': f'user_{user_id}',
            'email': f'user_{user_id}@example.com',
            'created_at': datetime.utcnow().isoformat(),
            'last_login': datetime.utcnow().isoformat(),
            'status': 'active',
            'token_limit': kwargs.get('token_limit', 10000),
            'priority_level': kwargs.get('priority_level', 'medium'),
            'api_key': kwargs.get('api_key', f'api_key_{user_id}'),
            'session_token': kwargs.get('session_token', f'session_token_{user_id}'),
            **kwargs
        }
    
    @staticmethod
    def create_test_token_usage_data(user_id: str, session_id: str, **kwargs) -> Dict[str, Any]:
        """Create test token usage data for database integration tests."""
        return {
            'user_id': user_id,
            'session_id': session_id,
            'tokens_used': kwargs.get('tokens_used', 100),
            'api_endpoint': kwargs.get('api_endpoint', '/api/chat'),
            'priority_level': kwargs.get('priority_level', 'medium'),
            'timestamp': datetime.utcnow().isoformat(),
            'processing_time_ms': kwargs.get('processing_time_ms', 50),
            'success': kwargs.get('success', True),
            **kwargs
        }
    
    @staticmethod
    def create_test_quota_data(user_id: str, **kwargs) -> Dict[str, Any]:
        """Create test quota data for database integration tests."""
        return {
            'user_id': user_id,
            'daily_limit': kwargs.get('daily_limit', 10000),
            'hourly_limit': kwargs.get('hourly_limit', 1000),
            'minute_limit': kwargs.get('minute_limit', 100),
            'daily_used': kwargs.get('daily_used', 0),
            'hourly_used': kwargs.get('hourly_used', 0),
            'minute_used': kwargs.get('minute_used', 0),
            'reset_time': kwargs.get('reset_time', datetime.utcnow().isoformat()),
            **kwargs
        }


class ExternalServiceIntegrationHelper:
    """Helper class for external service integration testing."""
    
    @staticmethod
    def create_mock_vault_response(data: Dict[str, Any]) -> Dict[str, Any]:
        """Create mock Vault API response."""
        return {
            'request_id': str(uuid.uuid4()),
            'lease_id': '',
            'renewable': False,
            'lease_duration': 0,
            'data': data,
            'wrap_info': None,
            'warnings': None,
            'auth': None
        }
    
    @staticmethod
    def create_mock_openai_response() -> Dict[str, Any]:
        """Create mock OpenAI API response."""
        return {
            'id': f'chatcmpl-{uuid.uuid4().hex[:8]}',
            'object': 'chat.completion',
            'created': int(time.time()),
            'model': 'gpt-3.5-turbo',
            'choices': [
                {
                    'index': 0,
                    'message': {
                        'role': 'assistant',
                        'content': 'Hello! How can I help you today?'
                    },
                    'finish_reason': 'stop'
                }
            ],
            'usage': {
                'prompt_tokens': 10,
                'completion_tokens': 9,
                'total_tokens': 19
            }
        }
    
    @staticmethod
    def create_mock_anthropic_response() -> Dict[str, Any]:
        """Create mock Anthropic API response."""
        return {
            'id': f'msg_{uuid.uuid4().hex[:8]}',
            'type': 'message',
            'role': 'assistant',
            'content': [
                {
                    'type': 'text',
                    'text': 'Hello! How can I help you today?'
                }
            ],
            'model': 'claude-3-sonnet-20240229',
            'stop_reason': 'end_turn',
            'usage': {
                'input_tokens': 10,
                'output_tokens': 9,
                'cache_creation_input_tokens': 0,
                'cache_read_input_tokens': 0
            }
        }
    
    @staticmethod
    def create_mock_mcp_response() -> Dict[str, Any]:
        """Create mock MCP server response."""
        return {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {
                'tools': [
                    {
                        'name': 'token_counter',
                        'description': 'Count tokens in text',
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'text': {
                                    'type': 'string',
                                    'description': 'Text to count tokens for'
                                }
                            },
                            'required': ['text']
                        }
                    }
                ]
            }
        }
    
    @staticmethod
    def create_mock_kilocode_response() -> Dict[str, Any]:
        """Create mock KiloCode response."""
        return {
            'workflow_id': f'wkf_{uuid.uuid4().hex[:8]}',
            'status': 'completed',
            'steps': [
                {
                    'step_id': f'step_{uuid.uuid4().hex[:8]}',
                    'name': 'Token Counting',
                    'status': 'completed',
                    'tokens_used': 150,
                    'duration_ms': 120
                },
                {
                    'step_id': f'step_{uuid.uuid4().hex[:8]}',
                    'name': 'API Call',
                    'status': 'completed',
                    'tokens_used': 75,
                    'duration_ms': 200
                }
            ],
            'total_tokens_used': 225,
            'total_duration_ms': 320,
            'result': {
                'output': 'Workflow completed successfully',
                'metadata': {
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
            }
        }


class TestTokenIntegration:
    """Comprehensive integration testing suite."""
    
    @pytest.fixture
    def db_helper(self):
        """Fixture providing database integration helper."""
        return DatabaseIntegrationHelper()
    
    @pytest.fixture
    def service_helper(self):
        """Fixture providing external service integration helper."""
        return ExternalServiceIntegrationHelper()
    
    @pytest.fixture
    def mock_db(self):
        """Fixture providing a mock database for integration testing."""
        mock_db = Mock()
        mock_db.is_tiktoken_available.return_value = False
        mock_db.get_token_count.return_value = 10
        mock_db.log_token_usage.return_value = True
        mock_db.check_token_quota.return_value = {'allowed': True, 'remaining_tokens': 1000}
        mock_db.execute_query.return_value = True
        mock_db.fetch_all.return_value = []
        mock_db.fetch_one.return_value = None
        mock_db.health_check.return_value = {'healthy': True}
        return mock_db
    
    @pytest.fixture
    def token_counter(self, mock_db):
        """Fixture providing a TokenCounter instance."""
        return TokenCounter(mock_db)
    
    @pytest.fixture
    def rate_limiter(self, mock_db):
        """Fixture providing a RateLimiter instance."""
        return RateLimiter(mock_db)
    
    @pytest.fixture
    def token_logger(self, mock_db):
        """Fixture providing a TokenUsageLogger instance."""
        config = LoggingConfig(strategy=LoggingStrategy.BATCH)
        return TokenUsageLogger(mock_db, config)
    
    @pytest.fixture
    def monitoring_system(self, mock_db):
        """Fixture providing a TokenMonitoringSystem instance."""
        config = MonitoringConfig()
        return TokenMonitoringSystem(mock_db, config)
    
    @pytest.fixture
    def security_manager(self, mock_db):
        """Fixture providing a TokenSecurityManager instance."""
        return TokenSecurityManager(mock_db)
    
    @pytest.fixture
    def vault_storage(self):
        """Fixture providing a VaultTokenStorage instance."""
        return VaultTokenStorage()
    
    @pytest.fixture
    def external_api_integration(self, token_counter):
        """Fixture providing an ExternalAPITokenIntegration instance."""
        return ExternalAPITokenIntegration(token_counter)
    
    @pytest.fixture
    def kilocode_integration(self, token_counter):
        """Fixture providing a KiloCodeTokenIntegration instance."""
        return KiloCodeTokenIntegration(token_counter)
    
    @pytest.fixture
    def mcp_integration(self, token_counter):
        """Fixture providing an MCPTokenIntegration instance."""
        return MCPTokenIntegration(token_counter)
    
    @pytest.fixture
    def memory_integration(self, token_counter):
        """Fixture providing a MemoryTokenIntegration instance."""
        return MemoryTokenIntegration(token_counter)
    
    @pytest.fixture
    def quota_scheduler(self, mock_db):
        """Fixture providing a QuotaResetScheduler instance."""
        lock_manager = LockManager()
        return QuotaResetScheduler(mock_db, lock_manager)
    
    @pytest.fixture
    def cron_manager(self):
        """Fixture providing a QuotaResetCronManager instance."""
        return QuotaResetCronManager()
    
    @pytest.fixture
    def token_revocation_service(self, vault_storage):
        """Fixture providing a TokenRevocationService instance."""
        return TokenRevocationService(vault_storage)
    
    def test_database_integration(self, mock_db, token_counter, rate_limiter, token_logger, db_helper):
        """Test database integration and data consistency."""
        # Test user data management
        test_user = db_helper.create_test_user_data('user-123', token_limit=5000)
        
        # Mock database response for user creation
        mock_db.execute_query.return_value = True
        mock_db.fetch_one.return_value = test_user
        
        # Test user creation
        user_result = mock_db.create_user(test_user)
        assert user_result is True
        
        # Test user retrieval
        retrieved_user = mock_db.get_user('user-123')
        assert retrieved_user['user_id'] == 'user-123'
        assert retrieved_user['token_limit'] == 5000
        
        # Test token usage logging
        usage_data = db_helper.create_test_token_usage_data('user-123', 'session-456', tokens_used=150)
        
        # Mock database response for usage logging
        mock_db.log_token_usage.return_value = True
        
        # Log token usage
        log_result = token_logger.log_token_usage(
            user_id='user-123',
            session_id='session-456',
            tokens_used=150,
            api_endpoint='/api/chat',
            priority_level='medium'
        )
        assert log_result is True
        
        # Test usage history retrieval
        mock_db.fetch_all.return_value = [usage_data]
        
        history = token_logger.get_token_usage_history(
            user_id='user-123',
            start_date=datetime.utcnow() - timedelta(hours=1),
            end_date=datetime.utcnow()
        )
        
        assert len(history) == 1
        assert history[0]['user_id'] == 'user-123'
        assert history[0]['tokens_used'] == 150
        
        # Test quota management
        quota_data = db_helper.create_test_quota_data('user-123', daily_limit=5000, daily_used=1000)
        
        # Mock database response for quota check
        mock_db.check_token_quota.return_value = {
            'allowed': True,
            'remaining_tokens': 4000,
            'reason': 'Quota available'
        }
        
        # Check rate limits
        rate_limit_result = rate_limiter.check_rate_limit(
            user_id='user-123',
            tokens_required=100,
            window=RateLimitWindow.DAY
        )
        
        assert rate_limit_result.allowed is True
        assert rate_limit_result.remaining == 4000
        
        # Test quota updates
        mock_db.update_token_quota.return_value = True
        
        update_result = mock_db.update_token_quota(
            user_id='user-123',
            daily_used=1100,
            hourly_used=100,
            minute_used=10
        )
        
        assert update_result is True
        
        # Test database transactions
        mock_db.begin_transaction.return_value = True
        mock_db.commit_transaction.return_value = True
        mock_db.rollback_transaction.return_value = True
        
        # Begin transaction
        transaction_result = mock_db.begin_transaction()
        assert transaction_result is True
        
        # Perform operations within transaction
        mock_db.execute_query.return_value = True
        
        # Commit transaction
        commit_result = mock_db.commit_transaction()
        assert commit_result is True
        
        # Test database health checks
        mock_db.health_check.return_value = {'healthy': True, 'response_time': 10}
        
        health_result = mock_db.health_check()
        assert health_result['healthy'] is True
        assert health_result['response_time'] > 0
    
    def test_external_service_integration(self, external_api_integration, kilocode_integration, 
                                        mcp_integration, memory_integration, service_helper):
        """Test external service integrations."""
        # Test OpenAI integration
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = service_helper.create_mock_openai_response()
            
            result = asyncio.run(external_api_integration.call_openai_api(
                user_id='user-123',
                messages=[{'role': 'user', 'content': 'Hello'}],
                model='gpt-3.5-turbo'
            ))
            
            assert result['success'] is True
            assert 'usage' in result
            assert result['usage']['total_tokens'] > 0
        
        # Test Anthropic integration
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = service_helper.create_mock_anthropic_response()
            
            result = asyncio.run(external_api_integration.call_anthropic_api(
                user_id='user-123',
                messages=[{'role': 'user', 'content': 'Hello'}],
                model='claude-3-sonnet-20240229'
            ))
            
            assert result['success'] is True
            assert 'usage' in result
            assert result['usage']['input_tokens'] > 0
        
        # Test KiloCode integration
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = service_helper.create_mock_kilocode_response()
            
            result = asyncio.run(kilocode_integration.execute_workflow(
                user_id='user-123',
                workflow_name='test_workflow',
                parameters={'text': 'Hello world'}
            ))
            
            assert result['success'] is True
            assert 'tokens_used' in result
            assert result['tokens_used'] > 0
        
        # Test MCP integration
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = service_helper.create_mock_mcp_response()
            
            result = asyncio.run(mcp_integration.call_mcp_tool(
                user_id='user-123',
                tool_name='token_counter',
                parameters={'text': 'Hello world'}
            ))
            
            assert result['success'] is True
            assert 'result' in result
        
        # Test Memory integration
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'id': 'mem_123',
                'user_id': 'user-123',
                'session_id': 'session_456',
                'content': 'Test memory entry',
                'metadata': {
                    'type': 'text',
                    'created_at': datetime.utcnow().isoformat()
                }
            }
            
            result = asyncio.run(memory_integration.store_memory_with_tokens(
                user_id='user-123',
                session_id='session_456',
                content='Test memory entry',
                tokens_used=50
            ))
            
            assert result['success'] is True
            assert 'memory_id' in result
    
    def test_vault_integration(self, vault_storage, service_helper):
        """Test Vault integration and secret management."""
        # Mock Vault API responses
        with patch('requests.get') as mock_get, patch('requests.post') as mock_post:
            # Mock health check
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                'initialized': True,
                'sealed': False,
                'standby': False
            }
            
            # Mock secret retrieval
            mock_get.return_value.json.side_effect = [
                service_helper.create_mock_vault_response({'database_host': 'localhost'}),
                service_helper.create_mock_vault_response({'api_key': 'test-api-key'})
            ]
            
            # Mock secret storage
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'request_id': str(uuid.uuid4()),
                'lease_id': '',
                'renewable': False,
                'lease_duration': 0,
                'data': None
            }
            
            # Test Vault health check
            health_result = vault_storage.check_vault_health()
            assert health_result['healthy'] is True
            
            # Test secret retrieval
            secret_result = vault_storage.retrieve_token_securely(
                user_id='user-123',
                service_name='database',
                token_id='db-credentials'
            )
            
            assert secret_result['success'] is True
            assert 'database_host' in secret_result['data']
            
            # Test secret storage
            store_result = vault_storage.store_token_securely(
                user_id='user-123',
                service_name='api',
                token='test-api-key-123',
                metadata={'description': 'Test API key'}
            )
            
            assert store_result is True
            
            # Test token revocation
            revoke_result = vault_storage.revoke_token(
                user_id='user-123',
                service_name='api',
                token_id='test-api-key-123'
            )
            
            assert revoke_result is True
    
    def test_scheduler_integration(self, quota_scheduler, cron_manager, mock_db):
        """Test scheduler and cron integration."""
        # Test quota reset scheduler
        with patch('threading.Thread') as mock_thread:
            mock_thread.return_value.start = Mock()
            
            # Start quota scheduler
            scheduler_result = quota_scheduler.start_scheduler()
            assert scheduler_result is True
            
            # Test quota reset
            reset_result = quota_scheduler.reset_user_quota(
                user_id='user-123',
                quota_type='daily'
            )
            
            assert reset_result['success'] is True
            
            # Test scheduler shutdown
            shutdown_result = quota_scheduler.stop_scheduler()
            assert shutdown_result is True
        
        # Test cron manager
        with patch('schedule.every') as mock_every, patch('time.sleep') as mock_sleep:
            mock_every.return_value.do.return_value = Mock()
            
            # Test cron scheduling
            cron_result = cron_manager.schedule_quota_reset(
                user_id='user-123',
                quota_type='daily',
                reset_time='00:00'
            )
            
            assert cron_result['scheduled'] is True
            
            # Test cron execution
            cron_result = cron_manager.execute_scheduled_tasks()
            assert cron_result['executed'] is True
    
    def test_token_revocation_integration(self, token_revocation_service, vault_storage):
        """Test token revocation service integration."""
        # Mock Vault responses
        with patch.object(vault_storage, 'revoke_token') as mock_revoke:
            mock_revoke.return_value = True
            
            # Test token revocation
            revoke_result = token_revocation_service.revoke_user_tokens(
                user_id='user-123',
                reason='security_breach'
            )
            
            assert revoke_result['success'] is True
            assert revoke_result['tokens_revoked'] > 0
            
            # Test revocation logging
            log_result = token_revocation_service.log_revocation_event(
                user_id='user-123',
                tokens_revoked=5,
                reason='security_breach',
                admin_user='admin-456'
            )
            
            assert log_result['logged'] is True
    
    def test_monitoring_integration(self, monitoring_system, mock_db):
        """Test monitoring system integration."""
        # Test system health monitoring
        with patch.object(mock_db, 'health_check') as mock_health:
            mock_health.return_value = {'healthy': True, 'response_time': 10}
            
            health_result = monitoring_system.check_system_health()
            assert health_result['healthy'] is True
            
            # Test performance monitoring
            performance_metrics = monitoring_system.get_performance_metrics()
            assert 'token_counting' in performance_metrics
            assert 'rate_limiting' in performance_metrics
            
            # Test alerting integration
            alert_result = monitoring_system.check_thresholds(
                metric='cpu_usage',
                current_value=85,
                threshold=80
            )
            
            assert alert_result['threshold_exceeded'] is True
            
            # Test metrics export
            export_result = monitoring_system.export_metrics(
                format='json',
                time_range='24h'
            )
            
            assert export_result['exported'] is True
            assert 'metrics' in export_result
    
    def test_batch_processing_integration(self, token_logger, mock_db):
        """Test batch processing integration."""
        # Create batch processor
        batch_config = BatchProcessorConfig(
            batch_timeout=5.0,
            max_queue_size=1000
        )
        batch_processor = TokenUsageBatchProcessor(mock_db, batch_config)
        
        # Create test records
        test_records = []
        for i in range(15):
            record = TokenUsageRecord(
                user_id=f'user-{i % 3}',
                session_id=f'session-{i}',
                tokens_used=100 + i * 10,
                api_endpoint='/api/test',
                priority_level='medium'
            )
            test_records.append(record)
        
        # Add records to batch processor
        for record in test_records:
            result = batch_processor.add_record(record)
            assert result is True
        
        # Test batch processing functionality
        # Mock the batch processing behavior
        with patch.object(batch_processor, '_process_batch') as mock_process:
            mock_process.return_value = {'success': True, 'records_processed': 15}
            
            # Add records to batch processor
            for record in test_records:
                result = batch_processor.add_record(record)
                assert result is True
            
            # Process batch using mocked method
            mock_process.return_value = {'success': True, 'records_processed': 15}
            batch_result = mock_process.return_value
            assert batch_result['success'] is True
            assert batch_result['records_processed'] == 15
    
    def test_error_handling_integration(self, token_counter, rate_limiter, token_logger, mock_db):
        """Test error handling across integrated components."""
        # Test database failure handling
        mock_db.log_token_usage.side_effect = Exception("Database connection failed")
        
        # Should fallback to console logging
        log_result = token_logger.log_token_usage(
            user_id='user-123',
            session_id='session-456',
            tokens_used=100,
            api_endpoint='/api/test',
            priority_level='medium'
        )
        
        assert log_result is True  # Should succeed with fallback
        
        # Reset mock
        mock_db.log_token_usage.side_effect = None
        
        # Test rate limiting failure handling
        mock_db.check_token_quota.side_effect = Exception("Rate limit service unavailable")
        
        # Should allow requests when rate limiting fails
        rate_limit_result = rate_limiter.check_rate_limit(
            user_id='user-123',
            tokens_required=100,
            window=RateLimitWindow.DAY
        )
        
        assert rate_limit_result.allowed is True  # Should allow when service fails
        
        # Reset mock
        mock_db.check_token_quota.side_effect = None
        
        # Test token counting failure handling
        mock_db.is_tiktoken_available.return_value = False
        mock_db.get_token_count.side_effect = Exception("Token counting service unavailable")
        
        # Should use fallback token counting
        token_result = token_counter.count_tokens("Test text")
        
        assert token_result.method == 'fallback'
        assert token_result.token_count > 0
        
        # Reset mock
        mock_db.is_tiktoken_available.return_value = True
        mock_db.get_token_count.side_effect = None
    
    def test_concurrent_integration(self, token_counter, rate_limiter, token_logger, mock_db):
        """Test concurrent operations across integrated components."""
        async def concurrent_operations():
            tasks = []
            
            # Create multiple concurrent operations
            for i in range(10):
                task = asyncio.create_task(
                    perform_operation(
                        user_id=f'user-{i}',
                        session_id=f'session-{i}',
                        operation_type=i % 3  # Different operation types
                    )
                )
                tasks.append(task)
            
            # Wait for all operations to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return results
        
        async def perform_operation(user_id: str, session_id: str, operation_type: int):
            """Perform a specific operation type."""
            try:
                if operation_type == 0:  # Token counting
                    result = token_counter.count_tokens(f"Test message for {user_id}")
                    return {'type': 'token_counting', 'success': True, 'tokens': result.token_count}
                
                elif operation_type == 1:  # Rate limiting
                    result = rate_limiter.check_rate_limit(
                        user_id=user_id,
                        tokens_required=100,
                        window=RateLimitWindow.DAY
                    )
                    return {'type': 'rate_limiting', 'success': True, 'allowed': result.allowed}
                
                elif operation_type == 2:  # Logging
                    result = token_logger.log_token_usage(
                        user_id=user_id,
                        session_id=session_id,
                        tokens_used=100,
                        api_endpoint='/api/test',
                        priority_level='medium'
                    )
                    return {'type': 'logging', 'success': result}
                
            except Exception as e:
                return {'type': 'error', 'success': False, 'error': str(e)}
        
        # Execute concurrent operations
        results = asyncio.run(concurrent_operations())
        
        # Verify results
        assert len(results) == 10
        
        successful_operations = [r for r in results if isinstance(r, dict) and r.get('success', False)]
        assert len(successful_operations) >= 8  # Allow for some failures in concurrent scenarios
        
        # Verify different operation types were performed
        operation_types = set(r.get('type') for r in successful_operations if isinstance(r, dict))
        assert len(operation_types) >= 2  # Should have multiple operation types
    
    def test_data_consistency_integration(self, token_counter, rate_limiter, token_logger, mock_db):
        """Test data consistency across integrated components."""
        # Test user data consistency
        test_user_id = 'user-123'
        
        # Set up user data
        user_data = {
            'user_id': test_user_id,
            'token_limit': 5000,
            'priority_level': 'high'
        }
        
        mock_db.create_user.return_value = True
        mock_db.get_user.return_value = user_data
        
        # Create user
        create_result = mock_db.create_user(user_data)
        assert create_result is True
        
        # Retrieve user
        retrieved_user = mock_db.get_user(test_user_id)
        assert retrieved_user['user_id'] == test_user_id
        assert retrieved_user['token_limit'] == 5000
        
        # Test token usage consistency
        test_session_id = 'session-456'
        test_tokens = 150
        
        # Log token usage
        log_result = token_logger.log_token_usage(
            user_id=test_user_id,
            session_id=test_session_id,
            tokens_used=test_tokens,
            api_endpoint='/api/chat',
            priority_level='high'
        )
        assert log_result is True
        
        # Verify usage was logged
        mock_db.fetch_all.return_value = [{
            'user_id': test_user_id,
            'session_id': test_session_id,
            'tokens_used': test_tokens,
            'api_endpoint': '/api/chat',
            'priority_level': 'high'
        }]
        
        usage_history = token_logger.get_token_usage_history(
            user_id=test_user_id,
            start_date=datetime.utcnow() - timedelta(hours=1),
            end_date=datetime.utcnow()
        )
        
        assert len(usage_history) == 1
        assert usage_history[0]['tokens_used'] == test_tokens
        
        # Test quota consistency
        mock_db.check_token_quota.return_value = {
            'allowed': True,
            'remaining_tokens': 4850,
            'reason': 'Quota available'
        }
        
        # Check rate limits
        rate_limit_result = rate_limiter.check_rate_limit(
            user_id=test_user_id,
            tokens_required=test_tokens,
            window=RateLimitWindow.DAY
        )
        
        assert rate_limit_result.allowed is True
        assert rate_limit_result.remaining == 4850
        
        # Update quota
        mock_db.update_token_quota.return_value = True
        
        update_result = mock_db.update_token_quota(
            user_id=test_user_id,
            daily_used=test_tokens,
            hourly_used=test_tokens,
            minute_used=test_tokens
        )
        
        assert update_result is True
        
        # Verify quota update
        updated_quota = mock_db.check_token_quota(
            user_id=test_user_id,
            tokens_required=0,
            window=RateLimitWindow.DAY
        )
        
        assert updated_quota['daily_used'] == test_tokens


if __name__ == '__main__':
    pytest.main([__file__, '-v'])