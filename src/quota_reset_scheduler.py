"""
Quota Reset Scheduler System

This module implements the main automated quota reset scheduling system
that supports different reset periods and integrates with PostgreSQL
scheduled jobs and OS cron tasks.
"""

import logging
import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid
from contextlib import contextmanager

from simba.simba.database.postgres import PostgresDB
from src.token_management.lock_manager import LockManager, LockType, LockTimeoutError

logger = logging.getLogger(__name__)


class ResetPeriod(Enum):
    """Supported reset periods."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class ResetStatus(Enum):
    """Reset operation status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QuotaResetSchedule:
    """Quota reset schedule configuration."""
    id: Optional[int] = None
    user_id: Optional[str] = None
    reset_type: ResetPeriod = ResetPeriod.DAILY
    reset_interval: str = "1 day"
    reset_time: str = "00:00:00"
    is_active: bool = True
    last_reset: Optional[datetime] = None
    next_reset: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        
        # Convert string enums to enum values
        if isinstance(self.reset_type, str):
            self.reset_type = ResetPeriod(self.reset_type)


@dataclass
class QuotaResetOperation:
    """Quota reset operation details."""
    id: Optional[int] = None
    schedule_id: Optional[int] = None
    user_id: Optional[str] = None
    reset_type: ResetPeriod = ResetPeriod.DAILY
    reset_start: Optional[datetime] = None
    reset_end: Optional[datetime] = None
    tokens_reset: int = 0
    users_affected: int = 0
    status: ResetStatus = ResetStatus.PENDING
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        
        # Convert string enums to enum values
        if isinstance(self.reset_type, str):
            self.reset_type = ResetPeriod(self.reset_type)
        if isinstance(self.status, str):
            self.status = ResetStatus(self.status)


class QuotaResetScheduler:
    """
    Main quota reset scheduler system.
    
    Provides comprehensive quota reset scheduling with support for different
    reset periods, concurrent operation handling, and monitoring.
    """
    
    def __init__(self, db: Optional[PostgresDB] = None, lock_manager: Optional[LockManager] = None):
        """
        Initialize the quota reset scheduler.
        
        Args:
            db: Database instance for quota reset operations
            lock_manager: Lock manager for concurrent operation handling
        """
        self.db = db or PostgresDB()
        from src.token_management.lock_manager import get_lock_manager
        self.lock_manager = lock_manager or get_lock_manager()
        
        # In-memory tracking for active operations
        self._active_operations: Dict[str, QuotaResetOperation] = {}
        self._operation_lock = threading.Lock()
        
        # Background task for monitoring
        self._monitor_task = None
        self._monitor_thread = None
        self._running = False
        
        # Performance metrics
        self.metrics = {
            'total_scheduled': 0,
            'total_executed': 0,
            'successful_resets': 0,
            'failed_resets': 0,
            'average_execution_time': 0.0,
            'last_execution_time': None,
            'pending_operations': 0,
            'active_operations': 0
        }
        
        logger.info("QuotaResetScheduler initialized")
    
    def start(self):
        """Start the quota reset scheduler."""
        if self._running:
            logger.warning("QuotaResetScheduler is already running")
            return
        
        self._running = True
        
        # Start background monitoring thread
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        logger.info("QuotaResetScheduler started")
    
    def stop(self):
        """Stop the quota reset scheduler."""
        if not self._running:
            logger.warning("QuotaResetScheduler is not running")
            return
        
        self._running = False
        
        # Wait for monitoring thread to finish
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
        
        # Cancel any active operations
        with self._operation_lock:
            for operation_id, operation in self._active_operations.items():
                if operation.status == ResetStatus.RUNNING:
                    operation.status = ResetStatus.CANCELLED
                    self._update_operation_status(operation_id, operation)
        
        logger.info("QuotaResetScheduler stopped")
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self._running:
            try:
                # Check for pending resets
                self._check_pending_resets()
                
                # Clean up old operations
                self._cleanup_old_operations()
                
                # Update metrics
                self._update_metrics()
                
                # Sleep for monitoring interval
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)  # Short sleep on error
    
    def _check_pending_resets(self):
        """Check for and execute pending quota resets."""
        try:
            # Get pending resets from database
            pending_resets = self.db.fetch_all(
                "SELECT id, user_id, reset_type, reset_interval, reset_time, "
                "last_reset, next_reset FROM quota_reset_schedules "
                "WHERE is_active = true AND next_reset <= NOW() + INTERVAL '1 hour' "
                "ORDER BY next_reset ASC LIMIT 10"
            )
            
            for reset_data in pending_resets:
                schedule_id = reset_data['id']
                user_id = reset_data['user_id']
                reset_type = ResetPeriod(reset_data['reset_type'])
                reset_interval = reset_data['reset_interval']
                reset_time = reset_data['reset_time']
                last_reset = reset_data['last_reset']
                next_reset = reset_data['next_reset']
                
                # Create operation
                operation = QuotaResetOperation(
                    schedule_id=schedule_id,
                    user_id=user_id,
                    reset_type=reset_type,
                    reset_start=last_reset,
                    reset_end=next_reset,
                    status=ResetStatus.PENDING,
                    created_at=datetime.utcnow()
                )
                
                # Execute the reset
                asyncio.run(self._execute_quota_reset(operation))
                
        except Exception as e:
            logger.error(f"Error checking pending resets: {e}")
    
    def _cleanup_old_operations(self):
        """Clean up old completed operations."""
        cutoff_time = datetime.utcnow() - timedelta(days=7)
        
        with self._operation_lock:
            # Remove old completed operations from memory
            operations_to_remove = [
                op_id for op_id, op in self._active_operations.items()
                if op.status in [ResetStatus.COMPLETED, ResetStatus.FAILED, ResetStatus.CANCELLED]
                and op.created_at and op.created_at < cutoff_time
            ]
            
            for op_id in operations_to_remove:
                del self._active_operations[op_id]
            
            logger.debug(f"Cleaned up {len(operations_to_remove)} old operations")
    
    def _update_metrics(self):
        """Update performance metrics."""
        with self._operation_lock:
            self.metrics['active_operations'] = len([
                op for op in self._active_operations.values()
                if op.status == ResetStatus.RUNNING
            ])
            self.metrics['pending_operations'] = len([
                op for op in self._active_operations.values()
                if op.status == ResetStatus.PENDING
            ])
    
    def schedule_quota_reset(self, user_id: Optional[str] = None, 
                           reset_type: ResetPeriod = ResetPeriod.DAILY,
                           reset_interval: str = "1 day",
                           reset_time: str = "00:00:00",
                           metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Schedule a quota reset operation.
        
        Args:
            user_id: Specific user to reset (None for all users)
            reset_type: Type of reset period
            reset_interval: Interval for custom resets
            reset_time: Time of day for daily/weekly/monthly resets
            metadata: Additional metadata for the schedule
            
        Returns:
            Schedule ID
        """
        try:
            # Validate configuration
            if not self.validate_reset_configuration(reset_type, reset_interval, reset_time):
                raise ValueError("Invalid reset configuration")
            
            # Calculate next reset time
            next_reset = self._calculate_next_reset_time(reset_type, reset_interval, reset_time)
            
            # Insert schedule into database
            query = """
                INSERT INTO quota_reset_schedules 
                (user_id, reset_type, reset_interval, reset_time, next_reset, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            result = self.db.fetch_one(
                query,
                (
                    user_id,
                    reset_type.value,
                    reset_interval,
                    reset_time,
                    next_reset,
                    json.dumps(metadata or {})
                )
            )
            
            if result is None:
                raise Exception("Failed to create schedule")
            
            schedule_id = result['id']
            self.metrics['total_scheduled'] += 1
            
            logger.info(f"Scheduled quota reset: ID {schedule_id}, "
                       f"User: {user_id or 'all'}, Type: {reset_type.value}")
            
            return schedule_id
            
        except Exception as e:
            logger.error(f"Error scheduling quota reset: {e}")
            raise
    
    def execute_quota_reset(self, schedule_id: Optional[int] = None,
                          user_id: Optional[str] = None,
                          reset_type: Optional[ResetPeriod] = None,
                          reset_start: Optional[datetime] = None,
                          reset_end: Optional[datetime] = None) -> QuotaResetOperation:
        """
        Execute a quota reset operation.
        
        Args:
            schedule_id: ID of schedule to execute (optional)
            user_id: Specific user to reset (optional)
            reset_type: Type of reset (optional)
            reset_start: Start time for reset window (optional)
            reset_end: End time for reset window (optional)
            
        Returns:
            QuotaResetOperation with execution details
        """
        try:
            # Create operation
            operation = QuotaResetOperation(
                schedule_id=schedule_id,
                user_id=user_id,
                reset_type=reset_type or ResetPeriod.DAILY,
                reset_start=reset_start,
                reset_end=reset_end,
                status=ResetStatus.PENDING,
                created_at=datetime.utcnow()
            )
            
            # Execute the reset
            return asyncio.run(self._execute_quota_reset(operation))
            
        except Exception as e:
            logger.error(f"Error executing quota reset: {e}")
            operation.status = ResetStatus.FAILED
            operation.error_message = str(e)
            return operation
    
    async def _execute_quota_reset(self, operation: QuotaResetOperation) -> QuotaResetOperation:
        """Execute a quota reset operation asynchronously."""
        operation_id = str(uuid.uuid4())
        operation.created_at = datetime.utcnow()
        
        # Track operation
        with self._operation_lock:
            self._active_operations[operation_id] = operation
        
        try:
            # Update status to running
            operation.status = ResetStatus.RUNNING
            self._update_operation_status(operation_id, operation)
            
            start_time = time.time()
            
            # Execute reset based on type
            if operation.user_id:
                # Single user reset
                result = await self._reset_single_user(operation)
            else:
                # All users reset
                result = await self._reset_all_users(operation)
            
            # Update operation with results
            operation.tokens_reset = result['tokens_reset']
            operation.users_affected = result['users_affected']
            operation.status = ResetStatus.COMPLETED
            operation.execution_time = time.time() - start_time
            
            self.metrics['total_executed'] += 1
            self.metrics['successful_resets'] += 1
            self.metrics['average_execution_time'] = (
                (self.metrics['average_execution_time'] * (self.metrics['successful_resets'] - 1) + 
                 operation.execution_time) / self.metrics['successful_resets']
            )
            self.metrics['last_execution_time'] = operation.execution_time
            
            logger.info(f"Quota reset completed: {operation.tokens_reset} tokens "
                       f"for {operation.users_affected} users in {operation.execution_time:.2f}s")
            
        except Exception as e:
            # Handle failure
            operation.status = ResetStatus.FAILED
            operation.error_message = str(e)
            operation.execution_time = time.time() - start_time
            
            self.metrics['total_executed'] += 1
            self.metrics['failed_resets'] += 1
            
            logger.error(f"Quota reset failed: {e}")
            
        finally:
            # Update operation status
            self._update_operation_status(operation_id, operation)
            
            # Remove from active operations
            with self._operation_lock:
                if operation_id in self._active_operations:
                    del self._active_operations[operation_id]
        
        return operation
    
    async def _reset_single_user(self, operation: QuotaResetOperation) -> Dict[str, Any]:
        """Reset token usage for a single user."""
        try:
            with self.lock_manager.lock(LockType.USAGE_UPDATE, f"user_{operation.user_id}"):
                # Execute database function
                query = """
                    SELECT reset_user_token_usage(%s, %s, %s) as tokens_reset
                """
                
                result = self.db.fetch_one(
                    query,
                    (
                        operation.user_id,
                        operation.reset_start,
                        operation.reset_end
                    )
                )
                
                return {
                    'tokens_reset': result['tokens_reset'] if result else 0,
                    'users_affected': 1
                }
                
        except LockTimeoutError:
            raise Exception(f"Timeout resetting tokens for user {operation.user_id}")
        except Exception as e:
            raise Exception(f"Error resetting tokens for user {operation.user_id}: {e}")
    
    async def _reset_all_users(self, operation: QuotaResetOperation) -> Dict[str, Any]:
        """Reset token usage for all users."""
        try:
            with self.lock_manager.lock(LockType.USAGE_UPDATE, "all_users"):
                # Execute database function
                query = """
                    SELECT * FROM reset_all_token_usage(%s, %s)
                """
                
                results = self.db.fetch_all(
                    query,
                    (
                        operation.reset_start,
                        operation.reset_end
                    )
                )
                
                tokens_reset = sum(row['tokens_reset'] for row in results)
                users_affected = len(results)
                
                return {
                    'tokens_reset': tokens_reset,
                    'users_affected': users_affected
                }
                
        except LockTimeoutError:
            raise Exception("Timeout resetting tokens for all users")
        except Exception as e:
            raise Exception(f"Error resetting tokens for all users: {e}")
    
    def get_pending_resets(self, limit: int = 10) -> List[QuotaResetSchedule]:
        """
        Get pending quota reset schedules.
        
        Args:
            limit: Maximum number of schedules to return
            
        Returns:
            List of pending quota reset schedules
        """
        try:
            query = """
                SELECT id, user_id, reset_type, reset_interval, reset_time,
                       is_active, last_reset, next_reset, created_at, updated_at, metadata
                FROM quota_reset_schedules
                WHERE is_active = true AND next_reset <= NOW() + INTERVAL '1 hour'
                ORDER BY next_reset ASC
                LIMIT %s
            """
            
            results = self.db.fetch_all(query, (limit,))
            
            schedules = []
            for result in results:
                schedule = QuotaResetSchedule(
                    id=result['id'],
                    user_id=result['user_id'],
                    reset_type=ResetPeriod(result['reset_type']),
                    reset_interval=str(result['reset_interval']),
                    reset_time=str(result['reset_time']),
                    is_active=result['is_active'],
                    last_reset=result['last_reset'],
                    next_reset=result['next_reset'],
                    created_at=result['created_at'],
                    updated_at=result['updated_at'],
                    metadata=json.loads(result['metadata'] or '{}')
                )
                schedules.append(schedule)
            
            return schedules
            
        except Exception as e:
            logger.error(f"Error getting pending resets: {e}")
            return []
    
    def cancel_scheduled_reset(self, schedule_id: int) -> bool:
        """
        Cancel a scheduled quota reset.
        
        Args:
            schedule_id: ID of schedule to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        try:
            query = """
                UPDATE quota_reset_schedules
                SET is_active = false, updated_at = NOW()
                WHERE id = %s
            """
            
            result = self.db.execute_query(query, (schedule_id,))
            
            if result > 0:
                logger.info(f"Cancelled scheduled quota reset: ID {schedule_id}")
                return True
            else:
                logger.warning(f"Schedule not found for cancellation: ID {schedule_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error cancelling scheduled reset: {e}")
            return False
    
    def get_reset_history(self, user_id: Optional[str] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         limit: int = 100) -> List[QuotaResetOperation]:
        """
        Get quota reset history.
        
        Args:
            user_id: Filter by user ID (optional)
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of quota reset operations
        """
        try:
            query = """
                SELECT id, schedule_id, user_id, reset_type, reset_start, reset_end,
                       tokens_reset, users_affected, status, error_message, 
                       execution_time, created_at
                FROM quota_reset_history
                WHERE (%s::text IS NULL OR user_id = %s)
                AND (%s IS NULL OR created_at >= %s)
                AND (%s IS NULL OR created_at <= %s)
                ORDER BY created_at DESC
                LIMIT %s
            """
            
            results = self.db.fetch_all(
                query,
                (
                    user_id,
                    user_id,
                    start_date,
                    start_date,
                    end_date,
                    end_date,
                    limit
                )
            )
            
            operations = []
            for result in results:
                operation = QuotaResetOperation(
                    id=result['id'],
                    schedule_id=result['schedule_id'],
                    user_id=result['user_id'],
                    reset_type=ResetPeriod(result['reset_type']),
                    reset_start=result['reset_start'],
                    reset_end=result['reset_end'],
                    tokens_reset=result['tokens_reset'],
                    users_affected=result['users_affected'],
                    status=ResetStatus(result['status']),
                    error_message=result['error_message'],
                    execution_time=result['execution_time'],
                    created_at=result['created_at']
                )
                operations.append(operation)
            
            return operations
            
        except Exception as e:
            logger.error(f"Error getting reset history: {e}")
            return []
    
    def validate_reset_configuration(self, reset_type: ResetPeriod,
                                   reset_interval: str,
                                   reset_time: str) -> bool:
        """
        Validate reset configuration.
        
        Args:
            reset_type: Type of reset period
            reset_interval: Interval for custom resets
            reset_time: Time of day for resets
            
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Validate reset type
            if not isinstance(reset_type, ResetPeriod):
                return False
            
            # Validate reset interval for custom type
            if reset_type == ResetPeriod.CUSTOM:
                try:
                    # Parse interval string
                    interval_parts = reset_interval.split()
                    if len(interval_parts) != 2:
                        return False
                    
                    value = int(interval_parts[0])
                    unit = interval_parts[1].lower()
                    
                    if value <= 0:
                        return False
                    
                    if unit not in ['second', 'seconds', 'minute', 'minutes', 
                                   'hour', 'hours', 'day', 'days', 'week', 'weeks']:
                        return False
                        
                except (ValueError, IndexError):
                    return False
            
            # Validate reset time format
            try:
                time_parts = reset_time.split(':')
                if len(time_parts) != 3:
                    return False
                
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                second = int(time_parts[2])
                
                if hour < 0 or hour > 23:
                    return False
                if minute < 0 or minute > 59:
                    return False
                if second < 0 or second > 59:
                    return False
                    
            except (ValueError, IndexError):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating reset configuration: {e}")
            return False
    
    def _calculate_next_reset_time(self, reset_type: ResetPeriod,
                                 reset_interval: str,
                                 reset_time: str) -> datetime:
        """
        Calculate next reset time.
        
        Args:
            reset_type: Type of reset period
            reset_interval: Interval for custom resets
            reset_time: Time of day for resets
            
        Returns:
            Next reset time
        """
        try:
            current_time = datetime.utcnow()
            
            if reset_type == ResetPeriod.DAILY:
                # Daily reset at specified time
                reset_time_obj = datetime.strptime(reset_time, '%H:%M:%S').time()
                next_reset = datetime.combine(current_time.date(), reset_time_obj)
                
                # If time has passed today, schedule for tomorrow
                if next_reset <= current_time:
                    next_reset += timedelta(days=1)
                    
            elif reset_type == ResetPeriod.WEEKLY:
                # Weekly reset on Monday at specified time
                reset_time_obj = datetime.strptime(reset_time, '%H:%M:%S').time()
                days_until_monday = (0 - current_time.weekday()) % 7
                if days_until_monday == 0 and current_time.time() < reset_time_obj:
                    days_until_monday = 7
                
                next_reset = datetime.combine(
                    current_time.date() + timedelta(days=days_until_monday),
                    reset_time_obj
                )
                
            elif reset_type == ResetPeriod.MONTHLY:
                # Monthly reset on 1st at specified time
                reset_time_obj = datetime.strptime(reset_time, '%H:%M:%S').time()
                
                # Get first day of next month
                if current_time.month == 12:
                    next_month = current_time.year + 1
                    next_month_day = 1
                else:
                    next_month = current_time.year
                    next_month_day = 1
                
                next_reset = datetime.combine(
                    datetime(next_month, next_month_day, 1),
                    reset_time_obj
                )
                
            elif reset_type == ResetPeriod.CUSTOM:
                # Custom interval
                interval_parts = reset_interval.split()
                value = int(interval_parts[0])
                unit = interval_parts[1].lower()
                
                if unit.startswith('second'):
                    delta = timedelta(seconds=value)
                elif unit.startswith('minute'):
                    delta = timedelta(minutes=value)
                elif unit.startswith('hour'):
                    delta = timedelta(hours=value)
                elif unit.startswith('day'):
                    delta = timedelta(days=value)
                elif unit.startswith('week'):
                    delta = timedelta(weeks=value)
                else:
                    delta = timedelta(days=1)  # Default
                
                next_reset = current_time + delta
                
            else:
                next_reset = current_time + timedelta(days=1)  # Default
            
            return next_reset
            
        except Exception as e:
            logger.error(f"Error calculating next reset time: {e}")
            return datetime.utcnow() + timedelta(days=1)
    
    def _update_operation_status(self, operation_id: str, operation: QuotaResetOperation):
        """Update operation status in database."""
        try:
            query = """
                INSERT INTO quota_reset_history 
                (schedule_id, user_id, reset_type, reset_start, reset_end,
                 tokens_reset, users_affected, status, error_message, execution_time, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            self.db.execute_query(
                query,
                (
                    operation.schedule_id,
                    operation.user_id,
                    operation.reset_type.value,
                    operation.reset_start,
                    operation.reset_end,
                    operation.tokens_reset,
                    operation.users_affected,
                    operation.status.value,
                    operation.error_message,
                    operation.execution_time,
                    operation.created_at
                )
            )
            
        except Exception as e:
            logger.error(f"Error updating operation status: {e}")
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get system health status.
        
        Returns:
            Dictionary with system health information
        """
        try:
            # Get database health
            db_health = self.db.health_check()
            
            # Get scheduler metrics
            with self._operation_lock:
                active_operations = len([
                    op for op in self._active_operations.values()
                    if op.status == ResetStatus.RUNNING
                ])
                pending_operations = len([
                    op for op in self._active_operations.values()
                    if op.status == ResetStatus.PENDING
                ])
            
            # Get pending schedules
            pending_schedules = len(self.get_pending_resets(1))
            
            return {
                'scheduler_status': 'running' if self._running else 'stopped',
                'database_status': 'healthy' if db_health else 'unhealthy',
                'active_operations': active_operations,
                'pending_operations': pending_operations,
                'pending_schedules': pending_schedules,
                'metrics': self.metrics.copy(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                'scheduler_status': 'error',
                'database_status': 'unknown',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the quota reset scheduler."""
        return self.metrics.copy()
    
    def emergency_release_all_locks(self):
        """Emergency release all locks."""
        self.lock_manager.emergency_release_all()
        logger.warning("Emergency released all quota reset locks")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


# Convenience functions
def get_quota_reset_scheduler() -> QuotaResetScheduler:
    """Get a global quota reset scheduler instance."""
    return QuotaResetScheduler()


def schedule_quota_reset(user_id: Optional[str] = None,
                        reset_type: ResetPeriod = ResetPeriod.DAILY,
                        reset_interval: str = "1 day",
                        reset_time: str = "00:00:00") -> int:
    """
    Convenience function to schedule a quota reset.
    
    Args:
        user_id: Specific user to reset (None for all users)
        reset_type: Type of reset period
        reset_interval: Interval for custom resets
        reset_time: Time of day for resets
        
    Returns:
        Schedule ID
    """
    scheduler = get_quota_reset_scheduler()
    return scheduler.schedule_quota_reset(user_id, reset_type, reset_interval, reset_time)


def execute_quota_reset(schedule_id: Optional[int] = None,
                       user_id: Optional[str] = None) -> QuotaResetOperation:
    """
    Convenience function to execute a quota reset.
    
    Args:
        schedule_id: ID of schedule to execute (optional)
        user_id: Specific user to reset (optional)
        
    Returns:
        QuotaResetOperation with execution details
    """
    scheduler = get_quota_reset_scheduler()
    return scheduler.execute_quota_reset(schedule_id, user_id)