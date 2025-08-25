"""
Comprehensive End-to-End Test Suite for Token Management System

This test suite provides complete end-to-end testing of the token management system,
covering all components and their interactions in realistic scenarios.
"""

import pytest
import asyncio
import time
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, MagicMock, AsyncMock, patch

# Add the project root to the Python path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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


class TestTokenManagementComplete:
    """Comprehensive end-to-end test suite for token management system."""
    
    @pytest.fixture
    def complete_system_setup(self, mock_db):
        """Fixture that sets up the complete token management system."""
        # Initialize all components
        token_counter = TokenCounter(mock_db)
        rate_limiter = RateLimiter(mock_db)
        lock_manager = LockManager()
        
        # Initialize allocation strategies
        priority_allocation = PriorityBasedAllocation()
        dynamic_allocation = DynamicPriorityAllocation(priority_allocation)
        emergency_allocation = EmergencyOverrideAllocation(priority_allocation)
        burst_allocation = BurstTokenAllocation(priority_allocation)
        
        # Initialize logging and monitoring
        logging_config = LoggingConfig(strategy=LoggingStrategy.BATCH)
        token_logger = TokenUsageLogger(mock_db, logging_config)
        
        monitoring_config = MonitoringConfig()
        monitoring_system = TokenMonitoringSystem(mock_db, monitoring_config)
        
        # Initialize security components
        security_manager = TokenSecurityManager()
        vault_storage = VaultTokenStorage()
        
        # Initialize analytics and alerting
        analytics_config = AnalyticsConfig()
        token_analytics = TokenUsageAnalytics(mock_db, analytics_config)
        
        alerting_config = AlertingConfig()
        alerting_system = TokenAlertingSystem(mock_db, alerting_config)
        
        # Initialize integrations
        external_api_integration = ExternalAPITokenIntegration(token_counter)
        kilocode_integration = KiloCodeTokenIntegration(token_counter)
        mcp_integration = MCPTokenIntegration(token_counter)
        memory_integration = MemoryTokenIntegration(token_counter)
        
        # Initialize scheduler and cron manager
        quota_scheduler = QuotaResetScheduler(mock_db, lock_manager)
        cron_manager = QuotaResetCronManager()
        
        # Initialize other components
        sensitive_filter = SensitiveContentFilter()
        token_dashboard = TokenDashboard(mock_db)
        credential_rotator = CredentialRotator()
        environment_validator = EnvironmentValidator()
        token_revocation_service = TokenRevocationService(vault_storage)
        
        return {
            'token_counter': token_counter,
            'rate_limiter': rate_limiter,
            'lock_manager': lock_manager,
            'priority_allocation': priority_allocation,
            'dynamic_allocation': dynamic_allocation,
            'emergency_allocation': emergency_allocation,
            'burst_allocation': burst_allocation,
            'token_logger': token_logger,
            'monitoring_system': monitoring_system,
            'security_manager': security_manager,
            'vault_storage': vault_storage,
            'token_analytics': token_analytics,
            'alerting_system': alerting_system,
            'external_api_integration': external_api_integration,
            'kilocode_integration': kilocode_integration,
            'mcp_integration': mcp_integration,
            'memory_integration': memory_integration,
            'quota_scheduler': quota_scheduler,
            'cron_manager': cron_manager,
            'sensitive_filter': sensitive_filter,
            'token_dashboard': token_dashboard,
            'credential_rotator': credential_rotator,
            'environment_validator': environment_validator,
            'token_revocation_service': token_revocation_service,
            'mock_db': mock_db
        }
    
    def test_complete_token_lifecycle(self, complete_system_setup):
        """Test complete token lifecycle from counting to analytics."""
        setup = complete_system_setup
        
        # Step 1: Count tokens
        text = "This is a test message for token counting."
        token_result = setup['token_counter'].count_tokens(text)
        
        assert token_result.token_count > 0
        assert token_result.method in ['pg_tiktoken', 'fallback']
        
        # Step 2: Check rate limits
        rate_limit_result = setup['rate_limiter'].check_rate_limit(
            user_id='test-user',
            tokens_required=token_result.token_count,
            window=RateLimitWindow.DAY
        )
        
        assert rate_limit_result.allowed is True
        assert rate_limit_result.remaining >= 0
        
        # Step 3: Log token usage
        log_result = setup['token_logger'].log_token_usage(
            user_id='test-user',
            session_id='test-session',
            tokens_used=token_result.token_count,
            api_endpoint='/api/test',
            priority_level='Medium'
        )
        
        assert log_result is True
        
        # Step 4: Get usage history
        history = setup['token_logger'].get_token_usage_history(
            user_id='test-user',
            start_date=datetime.utcnow() - timedelta(hours=1),
            end_date=datetime.utcnow()
        )
        
        assert len(history) > 0
        
        # Step 5: Get analytics summary
        summary = setup['token_analytics'].get_token_usage_summary(
            user_id='test-user',
            start_date=datetime.utcnow() - timedelta(hours=1),
            end_date=datetime.utcnow()
        )
        
        assert summary.total_tokens > 0
        assert summary.total_requests > 0
        
        # Step 6: Check security
        security_check = setup['security_manager'].validate_token_usage(
            user_id='test-user',
            tokens_used=token_result.token_count,
            api_endpoint='/api/test'
        )
        
        assert security_check['valid'] is True
        
        # Step 7: Monitor the system
        monitoring_result = setup['monitoring_system'].monitor_token_usage(
            user_id='test-user',
            tokens_used=token_result.token_count,
            api_endpoint='/api/test'
        )
        
        assert monitoring_result['monitored'] is True
        
        # Step 8: Check for alerts
        alert_check = setup['alerting_system'].check_thresholds(
            user_id='test-user',
            current_usage=token_result.token_count,
            threshold=1000
        )
        
        # Alert may or may not be triggered depending on usage
        assert isinstance(alert_check, dict)
        
        # Step 9: Update dashboard
        dashboard_data = setup['token_dashboard'].get_dashboard_data(
            user_id='test-user'
        )
        
        assert 'usage' in dashboard_data
        assert 'alerts' in dashboard_data
        
        # Step 10: Clean up
        setup['token_counter'].clear_cache()
        setup['token_logger'].shutdown()
        setup['monitoring_system'].shutdown()
    
    def test_concurrent_token_processing(self, complete_system_setup):
        """Test concurrent token processing scenarios."""
        setup = complete_system_setup
        
        # Create multiple concurrent requests
        async def process_request(user_id: str, text: str):
            # Count tokens
            token_result = setup['token_counter'].count_tokens(text)
            
            # Check rate limits
            rate_limit_result = setup['rate_limiter'].check_rate_limit(
                user_id=user_id,
                tokens_required=token_result.token_count,
                window=RateLimitWindow.DAY
            )
            
            # Log usage
            log_result = setup['token_logger'].log_token_usage(
                user_id=user_id,
                session_id=f'session-{user_id}',
                tokens_used=token_result.token_count,
                api_endpoint='/api/chat',
                priority_level='Medium'
            )
            
            return {
                'user_id': user_id,
                'token_count': token_result.token_count,
                'rate_limit_allowed': rate_limit_result.allowed,
                'log_success': log_result
            }
        
        # Create test data
        test_users = [f'user-{i}' for i in range(10)]
        test_texts = [f'Test message {i} for concurrent processing.' for i in range(10)]
        
        # Run concurrent requests
        async def run_concurrent_test():
            tasks = []
            for i, user_id in enumerate(test_users):
                task = process_request(user_id, test_texts[i])
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            return results
        
        # Execute the test
        results = asyncio.run(run_concurrent_test())
        
        # Verify results
        assert len(results) == 10
        for result in results:
            assert result['token_count'] > 0
            assert result['rate_limit_allowed'] is True
            assert result['log_success'] is True
    
    def test_error_handling_and_recovery(self, complete_system_setup):
        """Test error handling and recovery mechanisms."""
        setup = complete_system_setup
        
        # Simulate database failure
        setup['mock_db'].log_token_usage.side_effect = Exception("Database connection failed")
        
        # Test fallback logging
        log_result = setup['token_logger'].log_token_usage(
            user_id='test-user',
            session_id='test-session',
            tokens_used=100,
            api_endpoint='/api/test',
            priority_level='Medium'
        )
        
        # Should succeed with fallback
        assert log_result is True
        
        # Reset mock
        setup['mock_db'].log_token_usage.side_effect = None
        
        # Simulate rate limit failure
        setup['mock_db'].check_rate_limit.return_value = {
            'allowed': False,
            'reason': 'Rate limit exceeded',
            'remaining_tokens': 0
        }
        
        # Test rate limiting
        rate_limit_result = setup['rate_limiter'].check_rate_limit(
            user_id='test-user',
            tokens_required=100,
            window=RateLimitWindow.DAY
        )
        
        assert rate_limit_result.allowed is False
        
        # Test retry logic
        retry_result = setup['rate_limiter'].check_rate_limit_with_retry(
            user_id='test-user',
            tokens_required=100,
            window=RateLimitWindow.DAY,
            max_retries=3
        )
        
        assert retry_result.allowed is False
        
        # Simulate token counting failure
        setup['mock_db'].is_tiktoken_available.return_value = False
        setup['mock_db'].get_token_count.side_effect = Exception("Token counting failed")
        
        # Test fallback token counting
        token_result = setup['token_counter'].count_tokens("Test text")
        
        assert token_result.method == 'fallback'
        assert token_result.token_count > 0
        
        # Reset mock
        setup['mock_db'].is_tiktoken_available.return_value = True
        setup['mock_db'].get_token_count.side_effect = None
        
        # Test security error handling
        security_result = setup['security_manager'].validate_token_usage(
            user_id='test-user',
            tokens_used=1000000,  # Excessive usage
            api_endpoint='/api/test'
        )
        
        assert security_result['valid'] is False
        assert 'excessive_usage' in security_result['reasons']
    
    def test_performance_under_load(self, complete_system_setup, performance_timer):
        """Test system performance under load."""
        setup = complete_system_setup
        
        # Test token counting performance
        performance_timer.start()
        
        test_texts = [f'Test message {i} for performance testing.' for i in range(1000)]
        
        for text in test_texts:
            token_result = setup['token_counter'].count_tokens(text)
            assert token_result.token_count > 0
        
        token_counting_time = performance_timer.stop()
        
        # Test rate limiting performance
        performance_timer.start()
        
        for i in range(1000):
            rate_limit_result = setup['rate_limiter'].check_rate_limit(
                user_id=f'user-{i % 100}',
                tokens_required=100,
                window=RateLimitWindow.DAY
            )
            assert rate_limit_result.allowed is True
        
        rate_limiting_time = performance_timer.stop()
        
        # Test logging performance
        performance_timer.start()
        
        for i in range(1000):
            log_result = setup['token_logger'].log_token_usage(
                user_id=f'user-{i % 100}',
                session_id=f'session-{i}',
                tokens_used=100,
                api_endpoint='/api/test',
                priority_level='Medium'
            )
            assert log_result is True
        
        logging_time = performance_timer.stop()
        
        # Verify performance meets thresholds
        assert token_counting_time < 10.0  # Should complete in under 10 seconds
        assert rate_limiting_time < 5.0    # Should complete in under 5 seconds
        assert logging_time < 5.0          # Should complete in under 5 seconds
        
        # Performance metrics
        setup['monitoring_system'].record_performance_metric(
            'token_counting_time',
            token_counting_time / 1000  # Average per request
        )
        
        setup['monitoring_system'].record_performance_metric(
            'rate_limiting_time',
            rate_limiting_time / 1000  # Average per request
        )
        
        setup['monitoring_system'].record_performance_metric(
            'logging_time',
            logging_time / 1000  # Average per request
        )
    
    def test_security_compliance(self, complete_system_setup, security_test_data):
        """Test security compliance and data protection."""
        setup = complete_system_setup
        
        # Test sensitive content filtering
        sensitive_filter = setup['sensitive_filter']
        
        for content in security_test_data['sensitive_content']:
            filter_result = sensitive_filter.filter_content(content)
            assert filter_result['blocked'] is True
            assert filter_result['action'] == FilterAction.BLOCK
        
        for content in security_test_data['normal_content']:
            filter_result = sensitive_filter.filter_content(content)
            assert filter_result['blocked'] is False
            assert filter_result['action'] == 'ALLOW'
        
        # Test token storage security
        vault_storage = setup['vault_storage']
        
        # Store a token securely
        store_result = vault_storage.store_token_securely(
            user_id='test-user',
            service_name='test-service',
            token='test-token-12345',
            metadata={'description': 'Test token'}
        )
        
        assert store_result is True
        
        # Retrieve the token
        retrieve_result = vault_storage.retrieve_token_securely(
            user_id='test-user',
            service_name='test-service',
            token_id='test-token-12345'
        )
        
        assert retrieve_result['token'] == 'test-token-12345'
        
        # Test token revocation
        revoke_result = vault_storage.revoke_token(
            user_id='test-user',
            service_name='test-service',
            token_id='test-token-12345'
        )
        
        assert revoke_result is True
        
        # Test security event logging
        security_manager = setup['security_manager']
        
        security_event = security_manager.log_security_event(
            event_type='token_access',
            user_id='test-user',
            severity='info',
            description='Test security event',
            metadata={'ip': '192.168.1.1', 'user_agent': 'test-agent'}
        )
        
        assert security_event['logged'] is True
        
        # Test security audit
        audit_result = security_manager.perform_security_audit()
        
        assert audit_result['audit_completed'] is True
        assert 'findings' in audit_result
    
    def test_monitoring_and_alerting(self, complete_system_setup, sample_alert_rules):
        """Test monitoring and alerting functionality."""
        setup = complete_system_setup
        
        # Initialize monitoring system
        monitoring_system = setup['monitoring_system']
        alerting_system = setup['alerting_system']
        
        # Set up alert rules
        for rule in sample_alert_rules:
            alerting_system.add_alert_rule(rule)
        
        # Simulate various monitoring scenarios
        
        # 1. High usage scenario
        high_usage_result = monitoring_system.monitor_token_usage(
            user_id='user-1',
            tokens_used=9000,  # 90% of daily limit
            api_endpoint='/api/chat'
        )
        
        assert high_usage_result['monitored'] is True
        
        # Check if alert was triggered
        alerts = alerting_system.get_active_alerts()
        high_usage_alert = next((alert for alert in alerts if alert['type'] == 'usage_threshold'), None)
        
        if high_usage_alert:
            assert high_usage_alert['severity'] in ['high', 'critical']
        
        # 2. System health scenario
        health_result = monitoring_system.check_system_health()
        
        assert health_result['healthy'] is True
        assert 'cpu_usage' in health_result
        assert 'memory_usage' in health_result
        
        # 3. Performance monitoring
        performance_metrics = monitoring_system.get_performance_metrics()
        
        assert 'token_counting' in performance_metrics
        assert 'rate_limiting' in performance_metrics
        assert 'database_operations' in performance_metrics
        
        # 4. Alert testing
        test_alert = alerting_system.test_alert(
            alert_type='test',
            severity='info',
            message='Test alert message'
        )
        
        assert test_alert['triggered'] is True
        
        # 5. Alert resolution
        if high_usage_alert:
            resolution_result = alerting_system.resolve_alert(high_usage_alert['id'])
            assert resolution_result['resolved'] is True
    
    def test_data_export_and_reporting(self, complete_system_setup):
        """Test data export and reporting functionality."""
        setup = complete_system_setup
        
        # Generate some test data
        token_analytics = setup['token_analytics']
        token_logger = setup['token_logger']
        
        # Log some usage data
        for i in range(10):
            token_logger.log_token_usage(
                user_id=f'user-{i % 3}',
                session_id=f'session-{i}',
                tokens_used=100 + i * 10,
                api_endpoint='/api/test',
                priority_level='Medium'
            )
        
        # Test JSON export
        json_export = token_analytics.export_token_usage_logs(
            format='json',
            user_id='user-1'
        )
        
        assert json_export.startswith('[')
        assert json_export.endswith(']')
        
        # Test CSV export
        csv_export = token_analytics.export_token_usage_logs(
            format='csv',
            user_id='user-1'
        )
        
        assert 'user_id' in csv_export
        assert 'tokens_used' in csv_export
        assert 'timestamp' in csv_export
        
        # Test analytics dashboard data
        dashboard_data = token_analytics.get_analytics_dashboard_data(
            user_id='user-1'
        )
        
        assert 'usage_summary' in dashboard_data
        assert 'trend_analysis' in dashboard_data
        assert 'top_endpoints' in dashboard_data
        
        # Test report generation
        report = token_analytics.generate_usage_report(
            user_id='user-1',
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow()
        )
        
        assert 'total_tokens' in report
        assert 'total_requests' in report
        assert 'average_tokens_per_request' in report
        assert 'cost_estimate' in report
    
    def test_system_integration_scenarios(self, complete_system_setup):
        """Test various system integration scenarios."""
        setup = complete_system_setup
        
        # Scenario 1: Chat completion workflow
        async def chat_completion_workflow():
            # Initialize integrations
            external_api = setup['external_api_integration']
            memory_integration = setup['memory_integration']
            
            # Simulate chat completion request
            request_data = {
                'messages': [
                    {'role': 'user', 'content': 'Hello, how are you?'},
                    {'role': 'assistant', 'content': 'I am doing well, thank you!'}
                ],
                'model': 'gpt-3.5-turbo',
                'max_tokens': 150
            }
            
            # Count input tokens
            input_tokens = setup['token_counter'].count_tokens(
                str(request_data['messages'])
            )
            
            # Check rate limits
            rate_limit_result = setup['rate_limiter'].check_rate_limit(
                user_id='user-1',
                tokens_required=input_tokens.token_count,
                window=RateLimitWindow.DAY
            )
            
            if not rate_limit_result.allowed:
                return {'error': 'Rate limit exceeded'}
            
            # Log usage
            log_result = setup['token_logger'].log_token_usage(
                user_id='user-1',
                session_id='chat-session-1',
                tokens_used=input_tokens.token_count,
                api_endpoint='/api/chat/completions',
                priority_level='High'
            )
            
            # Store conversation in memory
            memory_result = await memory_integration.store_memory_with_tokens(
                user_id='user-1',
                session_id='chat-session-1',
                content=str(request_data['messages']),
                tokens_used=input_tokens.token_count
            )
            
            # Simulate API call (mock)
            api_result = await external_api.call_api_with_tokens(
                user_id='user-1',
                session_id='chat-session-1',
                api_url='https://api.openai.com/v1/chat/completions',
                request_data=request_data,
                tokens_required=input_tokens.token_count
            )
            
            return {
                'input_tokens': input_tokens.token_count,
                'log_success': log_result,
                'memory_stored': memory_result['success'],
                'api_success': api_result['success']
            }
        
        # Execute workflow
        workflow_result = asyncio.run(chat_completion_workflow())
        
        assert int(workflow_result['input_tokens']) > 0
        assert workflow_result['log_success'] is True
        assert workflow_result['memory_stored'] is True
        assert workflow_result['api_success'] is True
        
        # Scenario 2: Batch processing workflow
        async def batch_processing_workflow():
            token_batch_processor = setup['token_usage_batch_processor']
            
            # Create batch of records
            batch_records = []
            for i in range(50):
                record = TokenUsageRecord(
                    user_id=f'user-{i % 5}',
                    session_id=f'session-{i}',
                    tokens_used=100 + i * 2,
                    api_endpoint='/api/batch',
                    priority_level='Medium'
                )
                batch_records.append(record)
            
            # Add records to batch processor
            for record in batch_records:
                result = token_batch_processor.add_record(record)
                assert result is True
            
            # Process batch
            batch_result = token_batch_processor.process_batch()
            
            return {
                'records_processed': batch_result['records_processed'],
                'batch_success': batch_result['success']
            }
        
        # Execute batch workflow
        batch_result = asyncio.run(batch_processing_workflow())
        
        assert batch_result['records_processed'] == 50
        assert batch_result['batch_success'] is True
        
        # Scenario 3: Security audit workflow
        def security_audit_workflow():
            security_manager = setup['security_manager']
            vault_storage = setup['vault_storage']
            
            # Perform security audit
            audit_result = security_manager.perform_security_audit()
            
            # Check token storage security
            vault_status = vault_storage.get_vault_status()
            
            # Generate security report
            security_report = security_manager.get_security_report()
            
            return {
                'audit_completed': audit_result['audit_completed'],
                'vault_healthy': vault_status['healthy'],
                'security_report_generated': security_report is not None
            }
        
        # Execute security workflow
        security_result = security_audit_workflow()
        
        assert security_result['audit_completed'] is True
        assert security_result['vault_healthy'] is True
        assert security_result['security_report_generated'] is True
    
    def test_system_health_and_recovery(self, complete_system_setup):
        """Test system health monitoring and recovery."""
        setup = complete_system_setup
        
        monitoring_system = setup['monitoring_system']
        security_manager = setup['security_manager']
        
        # Test system health check
        health_check = monitoring_system.check_system_health()
        
        assert health_check['healthy'] is True
        assert 'components' in health_check
        assert 'database' in health_check['components']
        assert 'cache' in health_check['components']
        assert 'monitoring' in health_check['components']
        
        # Test component health checks
        database_health = monitoring_system.check_database_health()
        assert database_health['healthy'] is True
        
        cache_health = monitoring_system.check_cache_health()
        assert cache_health['healthy'] is True
        
        # Test system recovery
        # Simulate database failure
        setup['mock_db'].health_check.side_effect = Exception("Database unavailable")
        
        # Health check should still work with fallback
        health_check = monitoring_system.check_system_health()
        assert health_check['healthy'] is False  # Should detect the failure
        
        # Test recovery procedures
        recovery_result = monitoring_system.attempt_recovery()
        assert recovery_result['recovery_attempted'] is True
        
        # Reset mock
        setup['mock_db'].health_check.side_effect = None
        
        # Test emergency shutdown
        emergency_result = security_manager.emergency_shutdown()
        assert emergency_result['shutdown_initiated'] is True
        
        # Test system restart
        restart_result = monitoring_system.restart_system()
        assert restart_result['restarted'] is True
    
    def test_configuration_and_scaling(self, complete_system_setup, temp_config_file):
        """Test system configuration and scaling capabilities."""
        setup = complete_system_setup
        
        # Test configuration loading
        environment_validator = setup['environment_validator']
        
        validation_results = environment_validator.validate_all()
        
        # Should have some validation results (may include warnings)
        assert isinstance(validation_results, list)
        
        # Test system scaling
        # Simulate increased load
        load_test_data = {
            'concurrent_users': 100,
            'requests_per_user': 50,
            'total_requests': 5000
        }
        
        # Test rate limit scaling
        for i in range(load_test_data['concurrent_users']):
            rate_limit_result = setup['rate_limiter'].check_rate_limit(
                user_id=f'user-{i}',
                tokens_required=100,
                window=RateLimitWindow.DAY
            )
            assert rate_limit_result.allowed is True
        
        # Test token counting scaling
        for i in range(load_test_data['requests_per_user']):
            token_result = setup['token_counter'].count_tokens(f'Test message {i}')
            assert token_result.token_count > 0
        
        # Test logging scaling
        for i in range(load_test_data['total_requests']):
            log_result = setup['token_logger'].log_token_usage(
                user_id=f'user-{i % 100}',
                session_id=f'session-{i}',
                tokens_used=100,
                api_endpoint='/api/test',
                priority_level='Medium'
            )
            assert log_result is True
        
        # Test performance under load
        performance_metrics = setup['monitoring_system'].get_performance_metrics()
        
        assert 'token_counting' in performance_metrics
        assert 'rate_limiting' in performance_metrics
        assert 'logging' in performance_metrics
        
        # Test system resource usage
        resource_usage = setup['monitoring_system'].get_resource_usage()
        
        assert 'cpu_usage' in resource_usage
        assert 'memory_usage' in resource_usage
        assert 'disk_usage' in resource_usage
        
        # Test auto-scaling triggers
        scaling_triggers = setup['monitoring_system'].check_scaling_triggers()
        
        assert isinstance(scaling_triggers, dict)
        assert 'cpu_threshold' in scaling_triggers
        assert 'memory_threshold' in scaling_triggers
        assert 'request_threshold' in scaling_triggers
    
    def test_backup_and_recovery(self, complete_system_setup):
        """Test backup and recovery procedures."""
        setup = complete_system_setup
        
        # Test data backup
        token_analytics = setup['token_analytics']
        token_logger = setup['token_logger']
        
        # Generate some test data
        for i in range(10):
            token_logger.log_token_usage(
                user_id=f'user-{i % 3}',
                session_id=f'session-{i}',
                tokens_used=100 + i * 10,
                api_endpoint='/api/test',
                priority_level='Medium'
            )
        
        # Create backup
        backup_result = token_analytics.create_backup(
            backup_type='full',
            include_analytics=True,
            include_logs=True
        )
        
        assert backup_result['backup_created'] is True
        assert 'backup_file' in backup_result
        
        # Test backup validation
        validation_result = token_analytics.validate_backup(backup_result['backup_file'])
        
        assert validation_result['valid'] is True
        assert 'backup_size' in validation_result
        
        # Test backup restoration
        restoration_result = token_analytics.restore_backup(backup_result['backup_file'])
        
        assert restoration_result['restored'] is True
        assert 'records_restored' in restoration_result
        
        # Test backup rotation
        rotation_result = token_analytics.rotate_backups(
            keep_days=30,
            max_backups=10
        )
        
        assert rotation_result['rotation_completed'] is True
        assert 'old_backups_removed' in rotation_result
        
        # Test disaster recovery
        disaster_recovery = setup['monitoring_system'].initiate_disaster_recovery()
        
        assert disaster_recovery['recovery_initiated'] is True
        assert 'recovery_steps' in disaster_recovery


if __name__ == '__main__':
    pytest.main([__file__, '-v'])