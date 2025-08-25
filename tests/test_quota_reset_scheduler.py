"""
Comprehensive Test Suite for Quota Reset Scheduler

This module provides unit tests for the quota reset scheduler system,
covering all core functionality including scheduling, execution, monitoring,
and error handling.
"""

import unittest
import unittest.mock as mock
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import threading
import time
import json

# Add the project root to the Python path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.quota_reset_scheduler import (
    QuotaResetScheduler, 
    QuotaResetSchedule, 
    QuotaResetOperation,
    ResetPeriod,
    ResetStatus
)
from src.quota_reset_cron import QuotaResetCronManager, CronJobConfig
from simba.simba.database.postgres import PostgresDB


class TestQuotaResetSchedule(unittest.TestCase):
    """Test cases for QuotaResetSchedule dataclass."""
    
    def test_schedule_creation(self):
        """Test creating a quota reset schedule."""
        schedule = QuotaResetSchedule(
            user_id="test_user",
            reset_type=ResetPeriod.DAILY,
            reset_interval="1 day",
            reset_time="00:00:00"
        )
        
        self.assertEqual(schedule.user_id, "test_user")
        self.assertEqual(schedule.reset_type, ResetPeriod.DAILY)
        self.assertEqual(schedule.reset_interval, "1 day")
        self.assertEqual(schedule.reset_time, "00:00:00")
        self.assertTrue(schedule.is_active)
        self.assertIsNone(schedule.last_reset)
        self.assertIsNone(schedule.next_reset)
    
    def test_schedule_with_metadata(self):
        """Test creating a schedule with metadata."""
        metadata = {"priority": "high", "description": "Test schedule"}
        schedule = QuotaResetSchedule(metadata=metadata)
        
        self.assertEqual(schedule.metadata, metadata)
    
    def test_schedule_string_enum_conversion(self):
        """Test automatic conversion of string enums."""
        schedule = QuotaResetSchedule(reset_type=ResetPeriod.DAILY)
        self.assertEqual(schedule.reset_type, ResetPeriod.DAILY)


class TestQuotaResetOperation(unittest.TestCase):
    """Test cases for QuotaResetOperation dataclass."""
    
    def test_operation_creation(self):
        """Test creating a quota reset operation."""
        operation = QuotaResetOperation(
            user_id="test_user",
            reset_type=ResetPeriod.DAILY,
            status=ResetStatus.PENDING
        )
        
        self.assertEqual(operation.user_id, "test_user")
        self.assertEqual(operation.reset_type, ResetPeriod.DAILY)
        self.assertEqual(operation.status, ResetStatus.PENDING)
        self.assertEqual(operation.tokens_reset, 0)
        self.assertEqual(operation.users_affected, 0)
    
    def test_operation_with_metadata(self):
        """Test creating an operation with metadata."""
        metadata = {"batch_id": "12345", "source": "manual"}
        operation = QuotaResetOperation(metadata=metadata)
        
        self.assertEqual(operation.metadata, metadata)
    
    def test_operation_string_enum_conversion(self):
        """Test automatic conversion of string enums."""
        operation = QuotaResetOperation(reset_type=ResetPeriod.DAILY, status=ResetStatus.PENDING)
        self.assertEqual(operation.reset_type, ResetPeriod.DAILY)
        self.assertEqual(operation.status, ResetStatus.PENDING)


class TestQuotaResetScheduler(unittest.TestCase):
    """Test cases for QuotaResetScheduler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = MagicMock(spec=PostgresDB)
        self.mock_lock_manager = MagicMock()
        self.scheduler = QuotaResetScheduler(self.mock_db, self.mock_lock_manager)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.scheduler._running:
            self.scheduler.stop()
    
    def test_scheduler_initialization(self):
        """Test scheduler initialization."""
        self.assertEqual(self.scheduler.db, self.mock_db)
        self.assertEqual(self.scheduler.lock_manager, self.mock_lock_manager)
        self.assertFalse(self.scheduler._running)
        self.assertEqual(self.scheduler.metrics['total_scheduled'], 0)
        self.assertEqual(self.scheduler.metrics['total_executed'], 0)
    
    def test_start_stop_scheduler(self):
        """Test starting and stopping the scheduler."""
        # Start scheduler
        self.scheduler.start()
        self.assertTrue(self.scheduler._running)
        self.assertIsNotNone(self.scheduler._monitor_thread)
        if self.scheduler._monitor_thread:
            self.assertTrue(self.scheduler._monitor_thread.is_alive())
        
        # Stop scheduler
        self.scheduler.stop()
        self.assertFalse(self.scheduler._running)
    
    def test_schedule_quota_reset(self):
        """Test scheduling a quota reset."""
        # Mock database response
        mock_result = {'id': 123}
        self.mock_db.fetch_one.return_value = mock_result
        
        # Schedule a reset
        schedule_id = self.scheduler.schedule_quota_reset(
            user_id="test_user",
            reset_type=ResetPeriod.DAILY,
            reset_interval="1 day",
            reset_time="00:00:00"
        )
        
        # Verify database call
        self.mock_db.fetch_one.assert_called_once()
        self.assertEqual(schedule_id, 123)
        self.assertEqual(self.scheduler.metrics['total_scheduled'], 1)
    
    def test_schedule_quota_reset_with_metadata(self):
        """Test scheduling a quota reset with metadata."""
        # Mock database response
        mock_result = {'id': 456}
        self.mock_db.fetch_one.return_value = mock_result
        
        # Schedule a reset with metadata
        metadata = {"priority": "high", "description": "Test schedule"}
        schedule_id = self.scheduler.schedule_quota_reset(
            user_id="test_user",
            reset_type=ResetPeriod.WEEKLY,
            reset_interval="7 days",
            reset_time="02:00:00",
            metadata=metadata
        )
        
        # Verify database call
        self.mock_db.fetch_one.assert_called_once()
        self.assertEqual(schedule_id, 456)
    
    def test_schedule_quota_reset_invalid_config(self):
        """Test scheduling with invalid configuration."""
        # Test invalid configuration
        with self.assertRaises(ValueError):
            self.scheduler.schedule_quota_reset(
                reset_type=ResetPeriod.DAILY,
                reset_interval="invalid_interval",
                reset_time="invalid_time"
            )
    
    def test_execute_quota_reset_single_user(self):
        """Test executing a quota reset for a single user."""
        # Mock database responses
        self.mock_db.fetch_one.return_value = {
            'id': 789,
            'user_id': 'test_user',
            'reset_type': 'daily',
            'reset_interval': '1 day',
            'reset_time': '00:00:00',
            'is_active': True,
            'last_reset': datetime.utcnow() - timedelta(days=1),
            'next_reset': datetime.utcnow() + timedelta(days=1)
        }
        
        # Mock lock manager
        self.mock_lock_manager.lock.return_value.__enter__ = MagicMock()
        self.mock_lock_manager.lock.return_value.__exit__ = MagicMock()
        
        # Mock database update
        self.mock_db.execute_query.return_value = 1
        
        # Execute reset
        operation = self.scheduler.execute_quota_reset(
            schedule_id=789,
            user_id="test_user"
        )
        
        # Verify operation
        self.assertEqual(operation.schedule_id, 789)
        self.assertEqual(operation.user_id, "test_user")
        self.assertEqual(operation.status, ResetStatus.PENDING)
        self.assertEqual(self.scheduler.metrics['total_executed'], 1)
    
    def test_execute_quota_reset_all_users(self):
        """Test executing a quota reset for all users."""
        # Mock database responses
        self.mock_db.fetch_one.return_value = {
            'id': 789,
            'user_id': None,
            'reset_type': 'daily',
            'reset_interval': '1 day',
            'reset_time': '00:00:00',
            'is_active': True,
            'last_reset': datetime.utcnow() - timedelta(days=1),
            'next_reset': datetime.utcnow() + timedelta(days=1)
        }
        
        # Mock lock manager
        self.mock_lock_manager.lock.return_value.__enter__ = MagicMock()
        self.mock_lock_manager.lock.return_value.__exit__ = MagicMock()
        
        # Mock database update
        self.mock_db.execute_query.return_value = 1
        
        # Execute reset
        operation = self.scheduler.execute_quota_reset(schedule_id=789)
        
        # Verify operation
        self.assertEqual(operation.schedule_id, 789)
        self.assertIsNone(operation.user_id)
        self.assertEqual(operation.status, ResetStatus.PENDING)
        self.assertEqual(self.scheduler.metrics['total_executed'], 1)
    
    def test_cancel_scheduled_reset(self):
        """Test cancelling a scheduled reset."""
        # Mock database response
        self.mock_db.execute_query.return_value = 1
        
        # Cancel schedule
        success = self.scheduler.cancel_scheduled_reset(123)
        
        # Verify database call
        self.mock_db.execute_query.assert_called_once()
        self.assertTrue(success)
    
    def test_cancel_nonexistent_schedule(self):
        """Test cancelling a non-existent schedule."""
        # Mock database response
        self.mock_db.execute_query.return_value = 0
        
        # Cancel schedule
        success = self.scheduler.cancel_scheduled_reset(999)
        
        # Verify database call
        self.mock_db.execute_query.assert_called_once()
        self.assertFalse(success)
    
    def test_get_pending_resets(self):
        """Test getting pending resets."""
        # Mock database response
        mock_results = [
            {'id': 1, 'user_id': 'user1', 'reset_type': 'daily'},
            {'id': 2, 'user_id': 'user2', 'reset_type': 'weekly'}
        ]
        self.mock_db.fetch_all.return_value = mock_results
        
        # Get pending resets
        pending_resets = self.scheduler.get_pending_resets(limit=10)
        
        # Verify database call
        self.mock_db.fetch_all.assert_called_once()
        self.assertEqual(len(pending_resets), 2)
        self.assertEqual(pending_resets[0].id, 1)
        self.assertEqual(pending_resets[1].id, 2)
    
    def test_get_reset_history(self):
        """Test getting reset history."""
        # Mock database response
        mock_results = [
            {'id': 1, 'user_id': 'user1', 'status': 'completed'},
            {'id': 2, 'user_id': 'user2', 'status': 'failed'}
        ]
        self.mock_db.fetch_all.return_value = mock_results
        
        # Get reset history
        history = self.scheduler.get_reset_history(limit=10)
        
        # Verify database call
        self.mock_db.fetch_all.assert_called_once()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].id, 1)
        self.assertEqual(history[1].id, 2)
    
    def test_validate_reset_configuration(self):
        """Test reset configuration validation."""
        # Test valid configurations
        self.assertTrue(self.scheduler.validate_reset_configuration(
            ResetPeriod.DAILY, "1 day", "00:00:00"
        ))
        self.assertTrue(self.scheduler.validate_reset_configuration(
            ResetPeriod.WEEKLY, "7 days", "02:00:00"
        ))
        self.assertTrue(self.scheduler.validate_reset_configuration(
            ResetPeriod.MONTHLY, "30 days", "03:00:00"
        ))
        self.assertTrue(self.scheduler.validate_reset_configuration(
            ResetPeriod.CUSTOM, "2 hours", "12:00:00"
        ))
        
        # Test invalid configurations
        self.assertFalse(self.scheduler.validate_reset_configuration(
            ResetPeriod.DAILY, "invalid", "00:00:00"
        ))
        self.assertFalse(self.scheduler.validate_reset_configuration(
            ResetPeriod.DAILY, "1 day", "invalid"
        ))
        self.assertFalse(self.scheduler.validate_reset_configuration(
            ResetPeriod.CUSTOM, "invalid_interval", "00:00:00"
        ))
    
    def test_calculate_next_reset_time(self):
        """Test next reset time calculation."""
        # Test daily reset
        next_reset = self.scheduler._calculate_next_reset_time(
            ResetPeriod.DAILY, "1 day", "00:00:00"
        )
        self.assertIsInstance(next_reset, datetime)
        
        # Test weekly reset
        next_reset = self.scheduler._calculate_next_reset_time(
            ResetPeriod.WEEKLY, "7 days", "02:00:00"
        )
        self.assertIsInstance(next_reset, datetime)
        
        # Test monthly reset
        next_reset = self.scheduler._calculate_next_reset_time(
            ResetPeriod.MONTHLY, "30 days", "03:00:00"
        )
        self.assertIsInstance(next_reset, datetime)
        
        # Test custom reset
        next_reset = self.scheduler._calculate_next_reset_time(
            ResetPeriod.CUSTOM, "2 hours", "12:00:00"
        )
        self.assertIsInstance(next_reset, datetime)
    
    def test_get_system_health(self):
        """Test getting system health."""
        # Mock database health check
        self.mock_db.health_check.return_value = True
        
        # Get system health
        health = self.scheduler.get_system_health()
        
        # Verify health status
        self.assertIn('scheduler_status', health)
        self.assertIn('database_status', health)
        self.assertIn('active_operations', health)
        self.assertIn('pending_operations', health)
        self.assertIn('metrics', health)
        self.assertIn('timestamp', health)
    
    def test_get_performance_metrics(self):
        """Test getting performance metrics."""
        # Get metrics
        metrics = self.scheduler.get_performance_metrics()
        
        # Verify metrics
        self.assertIn('total_scheduled', metrics)
        self.assertIn('total_executed', metrics)
        self.assertIn('successful_resets', metrics)
        self.assertIn('failed_resets', metrics)
        self.assertIn('average_execution_time', metrics)
    
    def test_context_manager(self):
        """Test using scheduler as context manager."""
        with QuotaResetScheduler(self.mock_db, self.mock_lock_manager) as scheduler:
            self.assertTrue(scheduler._running)
        
        self.assertFalse(scheduler._running)


class TestQuotaResetCronManager(unittest.TestCase):
    """Test cases for QuotaResetCronManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = MagicMock(spec=PostgresDB)
        self.mock_scheduler = MagicMock()
        self.temp_config = "test_cron_config.json"
        
        # Create test config
        test_config = {
            "cron_jobs": {
                "test_job": {
                    "schedule": "0 0 * * *",
                    "command": "echo 'test'",
                    "enabled": True
                }
            }
        }
        
        with open(self.temp_config, 'w') as f:
            json.dump(test_config, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_config):
            os.remove(self.temp_config)
    
    def test_cron_manager_initialization(self):
        """Test cron manager initialization."""
        cron_manager = QuotaResetCronManager(
            config_file=self.temp_config,
            scheduler=self.mock_scheduler,
            db=self.mock_db
        )
        
        self.assertEqual(cron_manager.config_file, self.temp_config)
        self.assertEqual(cron_manager.scheduler, self.mock_scheduler)
        self.assertEqual(cron_manager.db, self.mock_db)
        self.assertIn('test_job', cron_manager.cron_jobs)
    
    def test_add_cron_job(self):
        """Test adding a cron job."""
        cron_manager = QuotaResetCronManager(
            config_file=self.temp_config,
            scheduler=self.mock_scheduler,
            db=self.mock_db
        )
        
        job = CronJobConfig(
            name="new_job",
            schedule="0 1 * * *",
            command="echo 'new job'"
        )
        
        cron_manager.add_cron_job(job)
        
        self.assertIn('new_job', cron_manager.cron_jobs)
        self.assertEqual(cron_manager.cron_jobs['new_job'], job)
    
    def test_remove_cron_job(self):
        """Test removing a cron job."""
        cron_manager = QuotaResetCronManager(
            config_file=self.temp_config,
            scheduler=self.mock_scheduler,
            db=self.mock_db
        )
        
        cron_manager.remove_cron_job("test_job")
        
        self.assertNotIn('test_job', cron_manager.cron_jobs)
    
    def test_enable_disable_cron_job(self):
        """Test enabling and disabling cron jobs."""
        cron_manager = QuotaResetCronManager(
            config_file=self.temp_config,
            scheduler=self.mock_scheduler,
            db=self.mock_db
        )
        
        # Disable job
        cron_manager.disable_cron_job("test_job")
        self.assertFalse(cron_manager.cron_jobs["test_job"].enabled)
        
        # Enable job
        cron_manager.enable_cron_job("test_job")
        self.assertTrue(cron_manager.cron_jobs["test_job"].enabled)
    
    def test_execute_cron_job(self):
        """Test executing a cron job."""
        cron_manager = QuotaResetCronManager(
            config_file=self.temp_config,
            scheduler=self.mock_scheduler,
            db=self.mock_db
        )
        
        # Mock subprocess result
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            result = cron_manager.execute_cron_job("test_job")
        
        self.assertTrue(result['success'])
        self.assertEqual(result['return_code'], 0)
        self.assertEqual(result['stdout'], "test output")
    
    def test_execute_disabled_cron_job(self):
        """Test executing a disabled cron job."""
        cron_manager = QuotaResetCronManager(
            config_file=self.temp_config,
            scheduler=self.mock_scheduler,
            db=self.mock_db
        )
        
        # Disable job
        cron_manager.disable_cron_job("test_job")
        
        # Try to execute
        result = cron_manager.execute_cron_job("test_job")
        
        self.assertFalse(result['success'])
        self.assertIn('disabled', result['error'])
    
    def test_execute_nonexistent_cron_job(self):
        """Test executing a non-existent cron job."""
        cron_manager = QuotaResetCronManager(
            config_file=self.temp_config,
            scheduler=self.mock_scheduler,
            db=self.mock_db
        )
        
        # Try to execute non-existent job
        result = cron_manager.execute_cron_job("nonexistent_job")
        
        self.assertFalse(result['success'])
        self.assertIn('not found', result['error'])
    
    def test_get_cron_jobs(self):
        """Test getting all cron jobs."""
        cron_manager = QuotaResetCronManager(
            config_file=self.temp_config,
            scheduler=self.mock_scheduler,
            db=self.mock_db
        )
        
        jobs = cron_manager.get_cron_jobs()
        
        self.assertIn('test_job', jobs)
        self.assertEqual(len(jobs), 1)
    
    def test_get_cron_job(self):
        """Test getting a specific cron job."""
        cron_manager = QuotaResetCronManager(
            config_file=self.temp_config,
            scheduler=self.mock_scheduler,
            db=self.mock_db
        )
        
        job = cron_manager.get_cron_job("test_job")
        
        self.assertIsNotNone(job)
        if job:
            self.assertEqual(job.name, "test_job")
        
        # Test non-existent job
        nonexistent_job = cron_manager.get_cron_job("nonexistent_job")
        self.assertIsNone(nonexistent_job)


class TestIntegration(unittest.TestCase):
    """Integration tests for the quota reset system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = MagicMock(spec=PostgresDB)
        self.mock_lock_manager = MagicMock()
    
    def test_full_workflow(self):
        """Test a complete workflow from scheduling to execution."""
        # Create scheduler
        scheduler = QuotaResetScheduler(self.mock_db, self.mock_lock_manager)
        
        try:
            # Start scheduler
            scheduler.start()
            
            # Mock database responses
            self.mock_db.fetch_one.return_value = {'id': 123}
            self.mock_db.fetch_all.return_value = []
            
            # Schedule a reset
            schedule_id = scheduler.schedule_quota_reset(
                user_id="test_user",
                reset_type=ResetPeriod.DAILY,
                reset_interval="1 day",
                reset_time="00:00:00"
            )
            
            self.assertEqual(schedule_id, 123)
            
            # Get pending resets
            pending_resets = scheduler.get_pending_resets()
            self.assertEqual(len(pending_resets), 0)
            
            # Get system health
            health = scheduler.get_system_health()
            self.assertIn('scheduler_status', health)
            
            # Get performance metrics
            metrics = scheduler.get_performance_metrics()
            self.assertIn('total_scheduled', metrics)
            
        finally:
            # Stop scheduler
            scheduler.stop()
    
    def test_error_handling(self):
        """Test error handling in various scenarios."""
        scheduler = QuotaResetScheduler(self.mock_db, self.mock_lock_manager)
        
        try:
            # Start scheduler
            scheduler.start()
            
            # Mock database to raise exception
            self.mock_db.fetch_one.side_effect = Exception("Database error")
            
            # Try to schedule a reset (should handle error gracefully)
            with self.assertRaises(Exception):
                scheduler.schedule_quota_reset()
            
            # Get system health (should handle error gracefully)
            health = scheduler.get_system_health()
            self.assertIn('error', health)
            
        finally:
            # Stop scheduler
            scheduler.stop()


if __name__ == '__main__':
    # Import os for cleanup
    import os
    
    # Run tests
    unittest.main()