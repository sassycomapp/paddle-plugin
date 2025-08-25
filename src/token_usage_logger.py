"""
Token Usage Logger System

This module provides comprehensive token usage logging functionality for auditing and monitoring.
It supports real-time logging, batch processing, and various logging strategies.
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue
import time
from contextlib import contextmanager
import uuid

from simba.simba.database.postgres import PostgresDB
from simba.simba.database.token_models import TokenUsage
from src.token_management.token_counter import TokenCounter, TokenizationModel

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels for token usage logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LoggingStrategy(Enum):
    """Logging strategies for different scenarios."""
    REAL_TIME = "real_time"
    BATCH = "batch"
    ASYNC = "async"


@dataclass
class TokenUsageRecord:
    """Represents a single token usage record."""
    user_id: str
    session_id: str
    tokens_used: int
    api_endpoint: str
    priority_level: str = "Medium"
    timestamp: Optional[datetime] = None
    request_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())
        if self.metadata is None:
            self.metadata = {}


@dataclass
class LoggingConfig:
    """Configuration for token usage logging."""
    strategy: LoggingStrategy = LoggingStrategy.REAL_TIME
    batch_size: int = 100
    batch_timeout: float = 5.0
    max_queue_size: int = 10000
    log_level: LogLevel = LogLevel.INFO
    enable_async: bool = True
    fallback_to_file: bool = True
    retention_days: int = 90
    enable_compression: bool = True
    performance_monitoring: bool = True


class TokenUsageLogger:
    """
    Comprehensive token usage logging system with multiple strategies.
    
    Supports real-time logging, batch processing, and asynchronous logging
    with fallback mechanisms and performance monitoring.
    """
    
    def __init__(self, db: Optional[PostgresDB] = None, config: Optional[LoggingConfig] = None):
        """
        Initialize the token usage logger.
        
        Args:
            db: Database instance for logging
            config: Logging configuration
        """
        self.db = db or PostgresDB()
        self.config = config or LoggingConfig()
        self.token_counter = TokenCounter(self.db)
        
        # Threading and queue for async logging
        self._queue = queue.Queue(maxsize=self.config.max_queue_size)
        self._stop_event = threading.Event()
        self._worker_thread = None
        self._lock = threading.Lock()
        self._batch_buffer = []
        
        # Performance metrics
        self.metrics = {
            'total_logs': 0,
            'successful_logs': 0,
            'failed_logs': 0,
            'batch_logs': 0,
            'async_logs': 0,
            'fallback_logs': 0,
            'processing_time': 0.0,
            'last_error': None,
            'error_timestamp': None
        }
        
        # Fallback file logger
        self.fallback_file = "token_usage_fallback.log"
        
        # Start async worker if enabled
        if self.config.enable_async:
            self._start_async_worker()
        
        logger.info(f"TokenUsageLogger initialized with strategy: {self.config.strategy}")
    
    def _start_async_worker(self):
        """Start the asynchronous logging worker thread."""
        if self._worker_thread and self._worker_thread.is_alive():
            logger.warning("Async worker already running")
            return
        
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._async_worker, daemon=True)
        self._worker_thread.start()
        logger.info("Async logging worker started")
    
    def _stop_async_worker(self):
        """Stop the asynchronous logging worker thread."""
        if not self._worker_thread or not self._worker_thread.is_alive():
            return
        
        self._stop_event.set()
        # Add sentinel to wake up worker
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        
        self._worker_thread.join(timeout=5.0)
        logger.info("Async logging worker stopped")
    
    def _async_worker(self):
        """Asynchronous worker thread for processing log entries."""
        batch_buffer = []
        last_batch_time = time.time()
        
        while not self._stop_event.is_set():
            try:
                # Get item from queue with timeout
                item = self._queue.get(timeout=1.0)
                
                if item is None:  # Sentinel to stop
                    break
                
                batch_buffer.append(item)
                
                # Check if we should process batch
                current_time = time.time()
                should_process = (
                    len(batch_buffer) >= self.config.batch_size or
                    current_time - last_batch_time >= self.config.batch_timeout or
                    self._stop_event.is_set()
                )
                
                if should_process and batch_buffer:
                    self._process_batch(batch_buffer)
                    batch_buffer = []
                    last_batch_time = current_time
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Async worker error: {e}")
                # Try to process any remaining items
                if batch_buffer:
                    try:
                        self._process_batch(batch_buffer)
                    except Exception as batch_error:
                        logger.error(f"Failed to process remaining batch: {batch_error}")
                    batch_buffer = []
    
    def _process_batch(self, records: List[TokenUsageRecord]):
        """Process a batch of token usage records."""
        if not records:
            return
        
        start_time = time.time()
        
        try:
            # Convert to database format
            db_records = []
            for record in records:
                db_record = TokenUsage(
                    user_id=record.user_id,
                    session_id=record.session_id,
                    tokens_used=record.tokens_used,
                    api_endpoint=record.api_endpoint,
                    priority_level=record.priority_level
                )
                db_records.append(db_record)
            
            # Batch insert using SQLAlchemy
            if self.db:
                session = self.db._Session()
                try:
                    session.add_all(db_records)
                    session.commit()
                except Exception:
                    session.rollback()
                    raise
                finally:
                    session.close()
            
            # Update metrics
            with self._lock:
                self.metrics['successful_logs'] += len(records)
                self.metrics['batch_logs'] += len(records)
                self.metrics['total_logs'] += len(records)
            
            processing_time = time.time() - start_time
            with self._lock:
                self.metrics['processing_time'] += processing_time
            
            logger.debug(f"Successfully logged batch of {len(records)} records in {processing_time:.3f}s")
            
        except Exception as e:
            logger.error(f"Failed to process batch of {len(records)} records: {e}")
            
            # Fallback to individual logging
            self._fallback_individual_logging(records)
            
            # Update metrics
            with self._lock:
                self.metrics['failed_logs'] += len(records)
                self.metrics['total_logs'] += len(records)
                self.metrics['last_error'] = str(e)
                self.metrics['error_timestamp'] = datetime.utcnow().isoformat()
    
    def _fallback_individual_logging(self, records: List[TokenUsageRecord]):
        """Fallback to individual logging when batch fails."""
        success_count = 0
        
        for record in records:
            try:
                # Try individual logging
                if self.db:
                    session = self.db._Session()
                    try:
                        db_record = TokenUsage(
                            user_id=record.user_id,
                            session_id=record.session_id,
                            tokens_used=record.tokens_used,
                            api_endpoint=record.api_endpoint,
                            priority_level=record.priority_level
                        )
                        session.add(db_record)
                        session.commit()
                        success_count += 1
                    except Exception:
                        session.rollback()
                        raise
                    finally:
                        session.close()
                
            except Exception as e:
                logger.error(f"Failed to log individual record for user {record.user_id}: {e}")
                
                # Fallback to file logging
                if self.config.fallback_to_file:
                    self._fallback_file_logging(record)
        
        if success_count > 0:
            logger.info(f"Successfully logged {success_count}/{len(records)} records individually")
        
        # Update fallback metrics
        if success_count < len(records):
            with self._lock:
                self.metrics['fallback_logs'] += (len(records) - success_count)
    
    def _fallback_file_logging(self, record: TokenUsageRecord):
        """Fallback to file logging when database is unavailable."""
        try:
            if record.timestamp:
                timestamp_str = record.timestamp.isoformat()
            else:
                timestamp_str = datetime.utcnow().isoformat()
                
            log_entry = {
                'timestamp': timestamp_str,
                'user_id': record.user_id,
                'session_id': record.session_id,
                'tokens_used': record.tokens_used,
                'api_endpoint': record.api_endpoint,
                'priority_level': record.priority_level,
                'request_id': record.request_id,
                'metadata': record.metadata
            }
            
            with open(self.fallback_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to fallback to file logging: {e}")
    
    def log_token_usage(self, user_id: str, session_id: str, tokens_used: int,
                       api_endpoint: str, priority_level: str = "Medium",
                       strategy: Optional[LoggingStrategy] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log token usage for a specific request.
        
        Args:
            user_id: The user identifier
            session_id: The session identifier
            tokens_used: Number of tokens consumed
            api_endpoint: API endpoint or service used
            priority_level: Priority level ('Low', 'Medium', 'High')
            strategy: Logging strategy to use (overrides config)
            metadata: Additional metadata for the log entry
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            if not user_id or not session_id:
                raise ValueError("user_id and session_id are required")
            
            if tokens_used < 0:
                raise ValueError("tokens_used must be non-negative")
            
            if priority_level not in ['Low', 'Medium', 'High']:
                raise ValueError("priority_level must be 'Low', 'Medium', or 'High'")
            
            # Create record
            record = TokenUsageRecord(
                user_id=user_id,
                session_id=session_id,
                tokens_used=tokens_used,
                api_endpoint=api_endpoint,
                priority_level=priority_level,
                metadata=metadata or {}
            )
            
            # Ensure timestamp is set
            if record.timestamp is None:
                record.timestamp = datetime.utcnow()
            
            # Determine logging strategy
            strategy = strategy or self.config.strategy
            
            if strategy == LoggingStrategy.REAL_TIME:
                success = self._log_real_time(record)
            elif strategy == LoggingStrategy.BATCH:
                success = self._log_batch(record)
            elif strategy == LoggingStrategy.ASYNC:
                success = self._log_async(record)
            else:
                raise ValueError(f"Unknown logging strategy: {strategy}")
            
            # Update metrics
            processing_time = time.time() - start_time
            with self._lock:
                self.metrics['total_logs'] += 1
                if success:
                    self.metrics['successful_logs'] += 1
                else:
                    self.metrics['failed_logs'] += 1
                self.metrics['processing_time'] += processing_time
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to log token usage: {e}")
            with self._lock:
                self.metrics['failed_logs'] += 1
                self.metrics['total_logs'] += 1
                self.metrics['last_error'] = str(e)
                self.metrics['error_timestamp'] = datetime.utcnow().isoformat()
            return False
    
    def _log_real_time(self, record: TokenUsageRecord) -> bool:
        """Log token usage in real-time."""
        if not self.db:
            logger.error("Database not available for real-time logging")
            return False
            
        session = self.db._Session()
        try:
            db_record = TokenUsage(
                user_id=record.user_id,
                session_id=record.session_id,
                tokens_used=record.tokens_used,
                api_endpoint=record.api_endpoint,
                priority_level=record.priority_level
            )
            session.add(db_record)
            session.commit()
            
            logger.debug(f"Real-time logged token usage: {record.tokens_used} tokens for user {record.user_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Real-time logging failed: {e}")
            return False
        finally:
            session.close()
    
    def _log_batch(self, record: TokenUsageRecord) -> bool:
        """Log token usage using batch strategy."""
        try:
            # Add to batch buffer
            batch_buffer = getattr(self, '_batch_buffer', [])
            batch_buffer.append(record)
            
            # Process batch if it reaches the batch size
            if len(batch_buffer) >= self.config.batch_size:
                success = self._process_batch(batch_buffer)
                self._batch_buffer = []
                return success or False
            
            # Store buffer for later processing
            self._batch_buffer = batch_buffer
            return True
            
        except Exception as e:
            logger.error(f"Batch logging failed: {e}")
            return False
    
    def _log_async(self, record: TokenUsageRecord) -> bool:
        """Log token usage asynchronously."""
        try:
            if not self.config.enable_async:
                logger.warning("Async logging disabled, falling back to real-time")
                return self._log_real_time(record)
            
            # Add to queue
            self._queue.put_nowait(record)
            
            with self._lock:
                self.metrics['async_logs'] += 1
            
            logger.debug(f"Async queued token usage: {record.tokens_used} tokens for user {record.user_id}")
            return True
            
        except queue.Full:
            logger.warning("Async queue full, falling back to real-time")
            return self._log_real_time(record)
        except Exception as e:
            logger.error(f"Async logging failed: {e}")
            return False
    
    def log_token_usage_batch(self, records: List[TokenUsageRecord]) -> Dict[str, Any]:
        """
        Log multiple token usage records efficiently.
        
        Args:
            records: List of TokenUsageRecord objects
            
        Returns:
            Dictionary with logging results
        """
        if not records:
            return {'success': True, 'message': 'No records to log'}
        
        start_time = time.time()
        results = {
            'total_records': len(records),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            # Process records based on strategy
            if self.config.strategy == LoggingStrategy.REAL_TIME:
                # Process each record individually
                for record in records:
                    if self._log_real_time(record):
                        results['successful'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"Failed to log record for user {record.user_id}")
            
            elif self.config.strategy == LoggingStrategy.BATCH:
                # Process as single batch
                success = self._process_batch(records)
                if success:
                    results['successful'] = len(records)
                else:
                    results['failed'] = len(records)
                    results['errors'].append("Batch processing failed")
            
            elif self.config.strategy == LoggingStrategy.ASYNC:
                # Queue all records
                for record in records:
                    try:
                        self._queue.put_nowait(record)
                        results['successful'] += 1
                    except queue.Full:
                        results['failed'] += 1
                        results['errors'].append(f"Queue full for user {record.user_id}")
                        # Try real-time fallback
                        if self._log_real_time(record):
                            results['successful'] += 1
                            results['failed'] -= 1
                        else:
                            results['errors'].append(f"Real-time fallback failed for user {record.user_id}")
            
            # Update metrics
            processing_time = time.time() - start_time
            with self._lock:
                self.metrics['total_logs'] += len(records)
                self.metrics['successful_logs'] += results['successful']
                self.metrics['failed_logs'] += results['failed']
                self.metrics['processing_time'] += processing_time
            
            logger.info(f"Batch logging completed: {results['successful']}/{results['total_records']} successful")
            
        except Exception as e:
            logger.error(f"Batch logging failed: {e}")
            results['failed'] = len(records)
            results['errors'].append(str(e))
        
        return results
    
    def get_token_usage_history(self, user_id: Optional[str] = None,
                              session_id: Optional[str] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None,
                              api_endpoint: Optional[str] = None,
                              limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Retrieve historical token usage data.
        
        Args:
            user_id: Filter by user ID (optional)
            session_id: Filter by session ID (optional)
            start_date: Start date for the query (optional)
            end_date: End date for the query (optional)
            api_endpoint: Filter by API endpoint (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of token usage records
        """
        if not self.db:
            return []
            
        session = self.db._Session()
        try:
            query = session.query(TokenUsage)
            
            # Apply filters
            if user_id:
                query = query.filter(TokenUsage.user_id == user_id)
            if session_id:
                query = query.filter(TokenUsage.session_id == session_id)
            if start_date:
                query = query.filter(TokenUsage.timestamp >= start_date)
            if end_date:
                query = query.filter(TokenUsage.timestamp <= end_date)
            if api_endpoint:
                query = query.filter(TokenUsage.api_endpoint == api_endpoint)
            
            # Order by timestamp descending and limit results
            results = query.order_by(TokenUsage.timestamp.desc()).limit(limit).all()
            
            return [
                {
                    'id': record.id,
                    'user_id': record.user_id,
                    'session_id': record.session_id,
                    'tokens_used': record.tokens_used,
                    'api_endpoint': record.api_endpoint,
                    'priority_level': record.priority_level,
                    'timestamp': record.timestamp.isoformat()
                }
                for record in results
            ]
        except Exception as e:
            logger.error(f"Failed to get token usage history: {e}")
            return []
        finally:
            session.close()
    
    def get_token_usage_summary(self, user_id: Optional[str] = None,
                              days: int = 7,
                              group_by: str = "day") -> Dict[str, Any]:
        """
        Generate usage summaries for reporting.
        
        Args:
            user_id: Specific user to get summary for (optional)
            days: Number of days to include in summary
            group_by: How to group results ('day', 'hour', 'api_endpoint')
            
        Returns:
            Dictionary with usage summary
        """
        if not self.db:
            return {
                'total_tokens': 0,
                'total_requests': 0,
                'unique_users': 0,
                'grouped_usage': {},
                'period_days': days,
                'start_date': (datetime.utcnow() - timedelta(days=days)).isoformat(),
                'end_date': datetime.utcnow().isoformat(),
                'error': 'Database not available'
            }
            
        start_date = datetime.utcnow() - timedelta(days=days)
        session = self.db._Session()
        try:
            query = session.query(TokenUsage).filter(TokenUsage.timestamp >= start_date)
            
            if user_id:
                query = query.filter(TokenUsage.user_id == user_id)
            
            results = query.all()
            
            if not results:
                return {
                    'total_tokens': 0,
                    'total_requests': 0,
                    'unique_users': 0 if not user_id else 1,
                    'grouped_usage': {},
                    'period_days': days,
                    'start_date': start_date.isoformat(),
                    'end_date': datetime.utcnow().isoformat()
                }
            
            # Calculate basic metrics
            total_tokens = sum(record.tokens_used for record in results)
            unique_users = set(record.user_id for record in results) if not user_id else {user_id}
            
            # Group usage
            grouped_usage = {}
            for record in results:
                if group_by == "day":
                    key = record.timestamp.strftime('%Y-%m-%d')
                elif group_by == "hour":
                    key = record.timestamp.strftime('%Y-%m-%d %H:00')
                elif group_by == "api_endpoint":
                    key = record.api_endpoint
                else:
                    key = record.timestamp.strftime('%Y-%m-%d')
                
                if key not in grouped_usage:
                    grouped_usage[key] = 0
                grouped_usage[key] += record.tokens_used
            
            return {
                'total_tokens': total_tokens,
                'total_requests': len(results),
                'unique_users': len(unique_users),
                'grouped_usage': grouped_usage,
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': datetime.utcnow().isoformat(),
                'average_tokens_per_request': total_tokens / len(results) if results else 0
            }
        except Exception as e:
            logger.error(f"Failed to get token usage summary: {e}")
            return {
                'total_tokens': 0,
                'total_requests': 0,
                'unique_users': 0,
                'grouped_usage': {},
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': datetime.utcnow().isoformat(),
                'error': str(e)
            }
        finally:
            session.close()
    
    def export_token_usage_logs(self, format: str = "json",
                              user_id: Optional[str] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> Union[str, bytes]:
        """
        Export logs for external analysis.
        
        Args:
            format: Export format ('json', 'csv')
            user_id: Filter by user ID (optional)
            start_date: Start date for export (optional)
            end_date: End date for export (optional)
            
        Returns:
            Exported data as string or bytes
        """
        try:
            # Get the data
            records = self.get_token_usage_history(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                limit=10000  # Reasonable limit for export
            )
            
            if format.lower() == "json":
                return json.dumps(records, indent=2, ensure_ascii=False)
            
            elif format.lower() == "csv":
                import csv
                import io
                
                output = io.StringIO()
                if records:
                    writer = csv.DictWriter(output, fieldnames=records[0].keys())
                    writer.writeheader()
                    writer.writerows(records)
                
                return output.getvalue()
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export token usage logs: {e}")
            raise
    
    def cleanup_old_logs(self, retention_days: Optional[int] = None) -> Dict[str, Any]:
        """
        Automatic cleanup of old log data based on retention policies.
        
        Args:
            retention_days: Number of days to retain logs (uses config if not provided)
            
        Returns:
            Dictionary with cleanup results
        """
        retention_days = retention_days or self.config.retention_days
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        if not self.db:
            return {
                'success': False,
                'error': 'Database not available',
                'deleted_count': 0,
                'retention_days': retention_days,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        session = self.db._Session()
        try:
            # Count records to be deleted
            count_query = session.query(TokenUsage).filter(
                TokenUsage.timestamp < cutoff_date
            )
            records_to_delete = count_query.count()
            
            # Delete old records
            deleted_count = session.query(TokenUsage).filter(
                TokenUsage.timestamp < cutoff_date
            ).delete(synchronize_session=False)
            
            session.commit()
            
            logger.info(f"Cleaned up {deleted_count} old token usage records older than {retention_days} days")
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'retention_days': retention_days,
                'cutoff_date': cutoff_date.isoformat(),
                'records_to_delete': records_to_delete
            }
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            return {
                'success': False,
                'error': str(e),
                'deleted_count': 0,
                'retention_days': retention_days,
                'cutoff_date': cutoff_date.isoformat()
            }
        finally:
            session.close()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for logging operations."""
        with self._lock:
            metrics = self.metrics.copy()
        
        # Calculate additional metrics
        total_logs = metrics['total_logs']
        if total_logs > 0:
            metrics['success_rate'] = metrics['successful_logs'] / total_logs
            metrics['failure_rate'] = metrics['failed_logs'] / total_logs
        else:
            metrics['success_rate'] = 0.0
            metrics['failure_rate'] = 0.0
        
        metrics['average_processing_time'] = (
            metrics['processing_time'] / total_logs if total_logs > 0 else 0.0
        )
        
        # Queue status
        metrics['queue_size'] = self._queue.qsize()
        metrics['queue_max_size'] = self._queue.maxsize
        metrics['queue_full'] = self._queue.full()
        
        # Async worker status
        metrics['async_worker_running'] = (
            self._worker_thread and self._worker_thread.is_alive()
        )
        
        return metrics
    
    def configure_logging(self, config: LoggingConfig):
        """Update logging configuration."""
        self.config = config
        
        # Restart async worker if needed
        if self.config.enable_async and not (
            self._worker_thread and self._worker_thread.is_alive()
        ):
            self._start_async_worker()
        elif not self.config.enable_async and (
            self._worker_thread and self._worker_thread.is_alive()
        ):
            self._stop_async_worker()
        
        logger.info(f"Logging configuration updated: {config}")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the logging system."""
        try:
            # Check database connection
            db_health = self.db.health_check()
            
            # Check async worker
            async_worker_running = (
                self._worker_thread and self._worker_thread.is_alive()
            )
            
            # Check queue health
            queue_size = self._queue.qsize()
            queue_healthy = queue_size < self.config.max_queue_size * 0.8
            
            # Get recent errors
            with self._lock:
                last_error = self.metrics['last_error']
                error_timestamp = self.metrics['error_timestamp']
            
            overall_health = (
                db_health and
                async_worker_running == self.config.enable_async and
                queue_healthy
            )
            
            return {
                'healthy': overall_health,
                'database_healthy': db_health,
                'async_worker_running': async_worker_running,
                'queue_size': queue_size,
                'queue_healthy': queue_healthy,
                'last_error': last_error,
                'error_timestamp': error_timestamp,
                'config': {
                    'strategy': self.config.strategy.value,
                    'enable_async': self.config.enable_async,
                    'batch_size': self.config.batch_size,
                    'retention_days': self.config.retention_days
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'healthy': False,
                'error': str(e),
                'database_healthy': False,
                'async_worker_running': False,
                'queue_size': 0,
                'queue_healthy': False
            }
    
    def shutdown(self):
        """Shutdown the logging system gracefully."""
        logger.info("Shutting down TokenUsageLogger")
        
        # Stop async worker
        self._stop_async_worker()
        
        # Process any remaining batch items
        if hasattr(self, '_batch_buffer') and self._batch_buffer:
            try:
                self._process_batch(self._batch_buffer)
                logger.info(f"Processed remaining {len(self._batch_buffer)} batch items")
            except Exception as e:
                logger.error(f"Failed to process remaining batch items: {e}")
        
        logger.info("TokenUsageLogger shutdown complete")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


# Convenience functions for direct usage
def log_token_usage(user_id: str, session_id: str, tokens_used: int,
                   api_endpoint: str, priority_level: str = "Medium",
                   db: Optional[PostgresDB] = None,
                   config: Optional[LoggingConfig] = None) -> bool:
    """
    Convenience function to log token usage.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        tokens_used: Number of tokens used
        api_endpoint: API endpoint used
        priority_level: Priority level ('Low', 'Medium', 'High')
        db: Database instance (optional)
        config: Logging configuration (optional)
        
    Returns:
        True if successful, False otherwise
    """
    logger = TokenUsageLogger(db, config)
    return logger.log_token_usage(user_id, session_id, tokens_used, api_endpoint, priority_level)


def get_token_usage_history(user_id: Optional[str] = None,
                           session_id: Optional[str] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           api_endpoint: Optional[str] = None,
                           limit: int = 1000,
                           db: Optional[PostgresDB] = None) -> List[Dict[str, Any]]:
    """
    Convenience function to get token usage history.
    
    Args:
        user_id: Filter by user ID (optional)
        session_id: Filter by session ID (optional)
        start_date: Start date for the query (optional)
        end_date: End date for the query (optional)
        api_endpoint: Filter by API endpoint (optional)
        limit: Maximum number of records to return
        db: Database instance (optional)
        
    Returns:
        List of token usage records
    """
    logger = TokenUsageLogger(db)
    return logger.get_token_usage_history(user_id, session_id, start_date, end_date, api_endpoint, limit)