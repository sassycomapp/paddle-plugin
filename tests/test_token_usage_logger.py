"""
Comprehensive Test Suite for Token Usage Logging System

This module provides comprehensive unit and integration tests for the token usage logging system,
including tests for the main logger, batch processor, and analytics components.
"""

import unittest
import pytest
import asyncio
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import List, Dict, Any, Optional
import json
import uuid

# Import the modules to test
from src.token_usage_logger import (
    TokenUsageLogger,
    LoggingConfig,
    LoggingStrategy,
    TokenUsageRecord
)
from src.token_usage_batch_processor import (
    TokenUsageBatchProcessor,
    BatchProcessorConfig
)
from src.token_usage_analytics import (
    TokenUsageAnalytics,
    AnalyticsConfig,
    AnalyticsGranularity,
    ExportFormat,
    UsageSummary,
    TrendAnalysis
)
from simba.simba.database.postgres import PostgresDB
from simba.simba.database.token_models import TokenUsage


class TestTokenUsageLogger(unittest.TestCase):
    """Test suite for TokenUsageLogger class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.db = Mock(spec=PostgresDB)
        self.config = LoggingConfig(
            strategy=LoggingStrategy.BATCH,
            batch_size=10,
            batch_timeout=5.0,
            enable_async=True,
            log_level="INFO"
        )
        self.logger = TokenUsageLogger(self.db, self.config)
        
        # Sample test data
        self.sample_record = TokenUsageRecord(
            user_id="test-user-123",
            session_id="test-session-456",
            tokens_used=150,
            api_endpoint="/chat/completions",
            priority_level="Medium",
            metadata={"model": "gpt-3.5-turbo", "temperature": 0.7}
        )
    
    def test_logger_initialization(self):
        """Test logger initialization with different configurations."""
        # Test with default config
        default_logger = TokenUsageLogger(self.db)
        self.assertIsNotNone(default_logger)
        self.assertEqual(default_logger.config.strategy, LoggingStrategy.BATCH)
        
        # Test with custom config
        custom_logger = TokenUsageLogger(self.db, self.config)
        self.assertEqual(custom_logger.config.batch_size, 10)
        self.assertTrue(custom_logger.config.enable_async)
    
    def test_log_token_usage_sync(self):
        """Test synchronous token usage logging."""
        # Mock database method
        self.db.log_token_usage.return_value = True
        
        # Test logging
        result = self.logger.log_token_usage(
            user_id="test-user",
            session_id="test-session",
            tokens_used=100,
            api_endpoint="/test",
            priority_level="High"
        )
        
        self.assertTrue(result)
        self.db.log_token_usage.assert_called_once_with(
            "test-user", "test-session", 100, "/test", "High"
        )
    
    def test_log_token_usage_with_record(self):
        """Test logging with TokenUsageRecord."""
        # Mock database method
        self.db.log_token_usage.return_value = True
        
        # Test logging with record
        result = self.logger.log_token_usage(
            self.sample_record.user_id,
            self.sample_record.session_id,
            self.sample_record.tokens_used,
            self.sample_record.api_endpoint,
            self.sample_record.priority_level
        )
        
        self.assertTrue(result)
        self.db.log_token_usage.assert_called_once_with(
            "test-user-123", "test-session-456", 150, "/chat/completions", "Medium"
        )
    
    def test_log_token_usage_batch(self):
        """Test batch token usage logging."""
        # Mock database method
        self.db.log_token_usage.return_value = True
        
        # Create multiple records
        records = [
            TokenUsageRecord(
                user_id=f"user-{i}",
                session_id=f"session-{i}",
                tokens_used=i * 10,
                api_endpoint=f"/endpoint-{i}",
                priority_level="Medium"
            )
            for i in range(5)
        ]
        
        # Test batch logging
        result = self.logger.log_token_usage_batch(records)
        
        self.assertTrue(result)
        self.assertEqual(self.db.log_token_usage.call_count, 5)
    
    def test_log_token_usage_async(self):
        """Test asynchronous token usage logging."""
        # Mock database method
        self.db.log_token_usage.return_value = True
        
        # Test async logging (sync version for testing)
        result = self.logger.log_token_usage(
            user_id="async-user",
            session_id="async-session",
            tokens_used=200,
            api_endpoint="/async-endpoint",
            priority_level="Low"
        )
        
        self.assertTrue(result)
        self.db.log_token_usage.assert_called_once_with(
            "async-user", "async-session", 200, "/async-endpoint", "Low"
        )
    
    def test_log_token_usage_async_batch(self):
        """Test asynchronous batch token usage logging."""
        # Mock database method
        self.db.log_token_usage.return_value = True
        
        # Create multiple records
        records = [
            TokenUsageRecord(
                user_id=f"async-user-{i}",
                session_id=f"async-session-{i}",
                tokens_used=i * 15,
                api_endpoint=f"/async-endpoint-{i}",
                priority_level="High"
            )
            for i in range(3)
        ]
        
        # Test batch logging
        result = self.logger.log_token_usage_batch(records)
        
        self.assertTrue(result)
        self.assertEqual(self.db.log_token_usage.call_count, 3)
    
    def test_get_token_usage_history(self):
        """Test retrieving token usage history."""
        # Mock database method
        mock_results = [
            {
                'id': 1,
                'user_id': 'test-user',
                'session_id': 'test-session',
                'tokens_used': 100,
                'api_endpoint': '/test',
                'priority_level': 'Medium',
                'timestamp': datetime.utcnow().isoformat()
            }
        ]
        self.db.fetch_all.return_value = mock_results
        
        # Test retrieval
        results = self.logger.get_token_usage_history(
            user_id='test-user',
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow()
        )
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['user_id'], 'test-user')
        self.db.fetch_all.assert_called_once()
    
    def test_get_token_usage_summary(self):
        """Test retrieving token usage summary."""
        # Mock database method
        mock_results = [
            {
                'id': 1,
                'user_id': 'test-user',
                'session_id': 'test-session',
                'tokens_used': 100,
                'api_endpoint': '/test',
                'priority_level': 'Medium',
                'timestamp': datetime.utcnow().isoformat()
            },
            {
                'id': 2,
                'user_id': 'test-user',
                'session_id': 'test-session-2',
                'tokens_used': 200,
                'api_endpoint': '/test',
                'priority_level': 'High',
                'timestamp': datetime.utcnow().isoformat()
            }
        ]
        self.db.fetch_all.return_value = mock_results
        
        # Test summary retrieval
        summary = self.logger.get_token_usage_summary(
            user_id='test-user',
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow()
        )
        
        self.assertEqual(summary['total_tokens'], 300)
        self.assertEqual(summary['total_requests'], 2)
        self.assertEqual(summary['average_tokens_per_request'], 150)
    
    def test_cleanup_old_logs(self):
        """Test cleanup of old logs."""
        # Mock database method
        self.db.execute_query.return_value = 100  # 100 records deleted
        
        # Test cleanup
        result = self.logger.cleanup_old_logs(retention_days=30)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['records_deleted'], 100)
        self.db.execute_query.assert_called_once()
    
    def test_error_handling(self):
        """Test error handling in logging operations."""
        # Mock database to raise exception
        self.db.log_token_usage.side_effect = Exception("Database error")
        
        # Test error handling
        result = self.logger.log_token_usage(
            user_id="test-user",
            session_id="test-session",
            tokens_used=100,
            api_endpoint="/test",
            priority_level="High"
        )
        
        self.assertFalse(result)
        self.db.log_token_usage.assert_called_once()
    
    def test_fallback_logging(self):
        """Test fallback logging when database is unavailable."""
        # Mock database to fail
        self.db.log_token_usage.return_value = False
        
        # Test fallback logging
        with patch('builtins.print') as mock_print:
            result = self.logger.log_token_usage(
                user_id="test-user",
                session_id="test-session",
                tokens_used=100,
                api_endpoint="/test",
                priority_level="High"
            )
            
            self.assertTrue(result)  # Should succeed with fallback
            mock_print.assert_called()  # Should log to console
    
    def test_context_manager(self):
        """Test logger as context manager."""
        with patch.object(self.logger, 'cleanup') as mock_cleanup:
            with self.logger as logger:
                self.assertIsNotNone(logger)
            mock_cleanup.assert_called_once()


class TestTokenUsageBatchProcessor(unittest.TestCase):
    """Test suite for TokenUsageBatchProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.db = Mock(spec=PostgresDB)
        self.config = BatchProcessorConfig(
            batch_size=10,
            batch_timeout=5.0,
            max_queue_size=1000
        )
        self.processor = TokenUsageBatchProcessor(self.db, self.config)
        
        # Sample test data
        self.sample_records = [
            TokenUsageRecord(
                user_id=f"user-{i}",
                session_id=f"session-{i}",
                tokens_used=i * 10,
                api_endpoint=f"/endpoint-{i}",
                priority_level="Medium"
            )
            for i in range(5)
        ]
    
    def test_batch_processor_initialization(self):
        """Test batch processor initialization."""
        self.assertIsNotNone(self.processor)
        self.assertEqual(self.processor.config.batch_size, 10)
    
    def test_add_record(self):
        """Test adding records to batch."""
        # Add records to batch
        for record in self.sample_records:
            self.processor.add_record(record)
        
        # Check batch size
        self.assertEqual(len(self.processor.records), 5)
        
        # Check batch is not full
        self.assertFalse(self.processor.is_batch_full())
    
    def test_batch_full_detection(self):
        """Test batch full detection."""
        # Fill batch to capacity
        for i in range(10):
            record = TokenUsageRecord(
                user_id=f"user-{i}",
                session_id=f"session-{i}",
                tokens_used=i * 10,
                api_endpoint=f"/endpoint-{i}",
                priority_level="Medium"
            )
            self.processor.add_record(record)
        
        # Check batch is full
        self.assertTrue(self.processor.is_batch_full())
    
    def test_process_batch(self):
        """Test processing a batch of records."""
        # Mock database method
        self.db.log_token_usage.return_value = True
        
        # Add records to batch
        for record in self.sample_records:
            self.processor.add_record(record)
        
        # Process batch
        result = self.processor.process_batch()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['records_processed'], 5)
        self.assertEqual(self.db.log_token_usage.call_count, 5)
    
    def test_process_batch_with_errors(self):
        """Test processing batch with some errors."""
        # Mock database method to fail for some records
        def mock_log_token_usage(user_id, session_id, tokens_used, api_endpoint, priority_level):
            if user_id == "user-2":
                return False
            return True
        
        self.db.log_token_usage.side_effect = mock_log_token_usage
        
        # Add records to batch
        for record in self.sample_records:
            self.processor.add_record(record)
        
        # Process batch
        result = self.processor.process_batch()
        
        self.assertFalse(result['success'])
        self.assertEqual(result['records_processed'], 4)
        self.assertEqual(result['records_failed'], 1)
    
    def test_auto_batch_processing(self):
        """Test automatic batch processing."""
        # Mock database method
        self.db.log_token_usage.return_value = True
        
        # Start auto processing
        self.processor.start_auto_processing()
        
        # Add records
        for record in self.sample_records:
            self.processor.add_record(record)
        
        # Wait for processing
        import time
        time.sleep(1)
        
        # Check batch was processed
        self.assertEqual(len(self.processor.records), 0)
        self.assertEqual(self.db.log_token_usage.call_count, 5)
        
        # Stop auto processing
        self.processor.stop_auto_processing()
    
    def test_batch_processor_context_manager(self):
        """Test batch processor as context manager."""
        with patch.object(self.processor, 'cleanup') as mock_cleanup:
            with self.processor as processor:
                self.assertIsNotNone(processor)
            mock_cleanup.assert_called_once()


class TestTokenUsageAnalytics(unittest.TestCase):
    """Test suite for TokenUsageAnalytics class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.db = Mock(spec=PostgresDB)
        self.config = AnalyticsConfig(
            default_granularity=AnalyticsGranularity.DAY,
            default_time_range=30,
            max_records=10000,
            enable_trend_analysis=True,
            enable_anomaly_detection=True,
            enable_forecasting=False,
            cache_results=True,
            cache_ttl=3600
        )
        self.analytics = TokenUsageAnalytics(self.db, self.config)
        
        # Sample test data
        self.sample_records = [
            {
                'id': i,
                'user_id': f'user-{i % 3}',  # 3 unique users
                'session_id': f'session-{i}',
                'tokens_used': i * 10,
                'api_endpoint': f'/endpoint-{i % 2}',  # 2 unique endpoints
                'priority_level': 'Medium',
                'timestamp': datetime.utcnow() - timedelta(days=i)
            }
            for i in range(10)
        ]
    
    def test_analytics_initialization(self):
        """Test analytics initialization."""
        self.assertIsNotNone(self.analytics)
        self.assertEqual(self.analytics.config.default_granularity, AnalyticsGranularity.DAY)
        self.assertTrue(self.analytics.config.enable_trend_analysis)
    
    def test_get_token_usage_history(self):
        """Test retrieving token usage history."""
        # Mock database method
        self.db.fetch_all.return_value = self.sample_records
        
        # Test retrieval
        results = self.analytics.get_token_usage_history(
            user_id='user-1',
            start_date=datetime.utcnow() - timedelta(days=5),
            end_date=datetime.utcnow()
        )
        
        self.assertEqual(len(results), 10)
        self.db.fetch_all.assert_called_once()
    
    def test_get_token_usage_summary(self):
        """Test retrieving token usage summary."""
        # Mock database method
        self.db.fetch_all.return_value = self.sample_records
        
        # Test summary retrieval
        summary = self.analytics.get_token_usage_summary(
            user_id='user-1',
            start_date=datetime.utcnow() - timedelta(days=5),
            end_date=datetime.utcnow()
        )
        
        self.assertIsInstance(summary, UsageSummary)
        self.assertEqual(summary.total_tokens, sum(i * 10 for i in range(10)))
        self.assertEqual(summary.total_requests, 10)
        self.assertEqual(summary.unique_users, 3)
        self.assertEqual(summary.unique_endpoints, 2)
    
    def test_get_trend_analysis(self):
        """Test trend analysis."""
        # Mock database method
        self.db.fetch_all.return_value = self.sample_records
        
        # Test trend analysis
        trend = self.analytics.get_trend_analysis(
            user_id='user-1',
            start_date=datetime.utcnow() - timedelta(days=5),
            end_date=datetime.utcnow()
        )
        
        self.assertIsInstance(trend, TrendAnalysis)
        self.assertIn(trend.trend_direction, ['increasing', 'decreasing', 'stable'])
        self.assertGreaterEqual(trend.trend_strength, 0.0)
        self.assertLessEqual(trend.trend_strength, 1.0)
    
    def test_export_token_usage_logs(self):
        """Test exporting token usage logs."""
        # Mock database method
        self.db.fetch_all.return_value = self.sample_records
        
        # Test JSON export
        json_export = self.analytics.export_token_usage_logs(
            format=ExportFormat.JSON
        )
        
        self.assertIsInstance(json_export, str)
        self.assertTrue(json_export.startswith('['))
        self.assertTrue(json_export.endswith(']'))
        
        # Test CSV export
        csv_export = self.analytics.export_token_usage_logs(
            format=ExportFormat.CSV
        )
        
        self.assertIsInstance(csv_export, str)
        self.assertIn('user_id', csv_export)
        self.assertIn('tokens_used', csv_export)
    
    def test_cleanup_old_logs(self):
        """Test cleanup of old logs."""
        # Mock database method
        self.db.fetch_one.return_value = {'count': 100}
        self.db.execute_query.return_value = 100
        
        # Test cleanup
        result = self.analytics.cleanup_old_logs(retention_days=30)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['records_deleted'], 100)
        self.db.execute_query.assert_called_once()
    
    def test_cache_functionality(self):
        """Test caching functionality."""
        # Mock database method
        self.db.fetch_all.return_value = self.sample_records
        
        # First call should hit database
        summary1 = self.analytics.get_token_usage_summary()
        
        # Second call should use cache
        summary2 = self.analytics.get_token_usage_summary()
        
        # Should be same result
        self.assertEqual(summary1.total_tokens, summary2.total_tokens)
        
        # Database should only be called once
        self.assertEqual(self.db.fetch_all.call_count, 1)
    
    def test_clear_cache(self):
        """Test clearing cache."""
        # Add something to cache
        self.analytics._cache['test'] = {'data': 'test'}
        
        # Clear cache
        self.analytics.clear_cache()
        
        # Cache should be empty
        self.assertEqual(len(self.analytics._cache), 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete token usage logging system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.db = Mock(spec=PostgresDB)
        self.db.log_token_usage.return_value = True
        self.db.fetch_all.return_value = []
        self.db.execute_query.return_value = 0
        
        # Create all components
        self.logger = TokenUsageLogger(self.db)
        self.batch_processor = TokenUsageBatchProcessor(self.db)
        self.analytics = TokenUsageAnalytics(self.db)
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        # Step 1: Log token usage
        record = TokenUsageRecord(
            user_id="integration-user",
            session_id="integration-session",
            tokens_used=100,
            api_endpoint="/integration-test",
            priority_level="High"
        )
        
        # Log using main logger
        result = self.logger.log_token_usage(
            record.user_id,
            record.session_id,
            record.tokens_used,
            record.api_endpoint,
            record.priority_level
        )
        self.assertTrue(result)
        
        # Step 2: Get usage history
        history = self.logger.get_token_usage_history(
            user_id="integration-user",
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow()
        )
        
        # Step 3: Get usage summary
        summary = self.analytics.get_token_usage_summary(
            user_id="integration-user",
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow()
        )
        
        # Step 4: Export logs
        export = self.analytics.export_token_usage_logs(
            user_id="integration-user",
            format=ExportFormat.JSON
        )
        
        # Verify all steps completed successfully
        self.assertTrue(result)
        self.assertIsInstance(history, list)
        self.assertIsInstance(summary, UsageSummary)
        self.assertIsInstance(export, str)
    
    def test_batch_processing_integration(self):
        """Test batch processing integration."""
        # Create multiple records
        records = [
            TokenUsageRecord(
                user_id=f"batch-user-{i}",
                session_id=f"batch-session-{i}",
                tokens_used=i * 10,
                api_endpoint=f"/batch-endpoint-{i}",
                priority_level="Medium"
            )
            for i in range(5)
        ]
        
        # Log using batch processor
        result = self.batch_processor.add_record(records[0])
        self.assertTrue(result)
        
        # Process batch
        batch_result = self.batch_processor.process_batch()
        self.assertTrue(batch_result['success'])
        
        # Verify database was called
        self.assertEqual(self.db.log_token_usage.call_count, 1)
    
    def test_error_handling_integration(self):
        """Test error handling across components."""
        # Mock database to fail
        self.db.log_token_usage.return_value = False
        
        # Try to log with fallback enabled
        record = TokenUsageRecord(
            user_id="error-user",
            session_id="error-session",
            tokens_used=100,
            api_endpoint="/error-test",
            priority_level="High"
        )
        
        # Should succeed with fallback
        result = self.logger.log_token_usage(
            record.user_id,
            record.session_id,
            record.tokens_used,
            record.api_endpoint,
            record.priority_level
        )
        self.assertTrue(result)


class TestPerformance(unittest.TestCase):
    """Performance tests for the token usage logging system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.db = Mock(spec=PostgresDB)
        self.db.log_token_usage.return_value = True
        
        # Create test data
        self.test_records = [
            TokenUsageRecord(
                user_id=f"perf-user-{i}",
                session_id=f"perf-session-{i}",
                tokens_used=i * 5,
                api_endpoint=f"/perf-endpoint-{i % 10}",
                priority_level="Medium"
            )
            for i in range(1000)
        ]
    
    def test_batch_performance(self):
        """Test batch processing performance."""
        processor = TokenUsageBatchProcessor(self.db, BatchProcessorConfig(batch_size=100))
        
        # Time batch processing
        import time
        start_time = time.time()
        
        # Add all records
        for record in self.test_records:
            processor.add_record(record)
        
        # Process batch
        result = processor.process_batch()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify performance
        self.assertTrue(result['success'])
        self.assertEqual(result['records_processed'], 1000)
        self.assertLess(processing_time, 5.0)  # Should complete in under 5 seconds
    
    def test_analytics_performance(self):
        """Test analytics performance."""
        # Mock large dataset
        large_dataset = [
            {
                'id': i,
                'user_id': f'user-{i % 100}',  # 100 unique users
                'session_id': f'session-{i}',
                'tokens_used': i * 2,
                'api_endpoint': f'/endpoint-{i % 50}',  # 50 unique endpoints
                'priority_level': 'Medium',
                'timestamp': datetime.utcnow() - timedelta(minutes=i)
            }
            for i in range(10000)
        ]
        
        analytics = TokenUsageAnalytics(self.db)
        self.db.fetch_all.return_value = large_dataset
        
        # Time analytics operations
        import time
        start_time = time.time()
        
        # Get summary
        summary = analytics.get_token_usage_summary()
        
        # Get trend analysis
        trend = analytics.get_trend_analysis()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify performance
        self.assertEqual(summary.total_tokens, sum(i * 2 for i in range(10000)))
        self.assertIsInstance(trend, TrendAnalysis)
        self.assertLess(processing_time, 10.0)  # Should complete in under 10 seconds


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)