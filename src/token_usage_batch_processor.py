"""
Token Usage Batch Processor

This module provides high-performance batch processing for token usage logging,
optimized for high-throughput scenarios with automatic batching and compression.
"""

import logging
import asyncio
import json
import gzip
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

from simba.simba.database.postgres import PostgresDB
from simba.simba.database.token_models import TokenUsage
from src.token_usage_logger import TokenUsageRecord, LoggingConfig, LoggingStrategy

logger = logging.getLogger(__name__)


class BatchCompression(Enum):
    """Compression strategies for batch data."""
    NONE = "none"
    GZIP = "gzip"
    PICKLE = "pickle"


class BatchPriority(Enum):
    """Priority levels for batch processing."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class BatchJob:
    """Represents a batch processing job."""
    batch_id: str
    records: List[TokenUsageRecord]
    priority: BatchPriority
    compression: BatchCompression
    created_at: datetime
    max_retries: int = 3
    retry_count: int = 0
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BatchProcessorConfig:
    """Configuration for batch processing."""
    max_batch_size: int = 1000
    max_batch_wait_time: float = 10.0  # seconds
    max_queue_size: int = 50000
    compression: BatchCompression = BatchCompression.GZIP
    max_workers: int = 5
    enable_compression: bool = True
    enable_deduplication: bool = True
    retry_failed_batches: bool = True
    batch_timeout: float = 30.0  # seconds
    health_check_interval: float = 60.0  # seconds


class TokenUsageBatchProcessor:
    """
    High-performance batch processor for token usage logging.
    
    Features:
    - Automatic batching with configurable size and timeout
    - Compression for storage efficiency
    - Priority-based processing
    - Retry mechanisms for failed batches
    - Performance monitoring and metrics
    - Thread-safe operations
    """
    
    def __init__(self, db: Optional[PostgresDB] = None, config: Optional[BatchProcessorConfig] = None):
        """
        Initialize the batch processor.
        
        Args:
            db: Database instance for batch operations
            config: Batch processor configuration
        """
        self.db = db or PostgresDB()
        self.config = config or BatchProcessorConfig()
        
        # Threading and synchronization
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        
        # Initialize processed requests set for deduplication
        self._processed_requests = set()
        
        # Queues for different priorities
        self._queues = {
            BatchPriority.CRITICAL: queue.Queue(maxsize=self.config.max_queue_size // 4),
            BatchPriority.HIGH: queue.Queue(maxsize=self.config.max_queue_size // 4),
            BatchPriority.MEDIUM: queue.Queue(maxsize=self.config.max_queue_size // 4),
            BatchPriority.LOW: queue.Queue(maxsize=self.config.max_queue_size // 4)
        }
        
        # Batch buffers
        self._batch_buffers = {
            BatchPriority.CRITICAL: [],
            BatchPriority.HIGH: [],
            BatchPriority.MEDIUM: [],
            BatchPriority.LOW: []
        }
        
        # Performance metrics
        self.metrics = {
            'total_batches_processed': 0,
            'total_records_processed': 0,
            'successful_batches': 0,
            'failed_batches': 0,
            'compression_savings': 0,
            'processing_time': 0.0,
            'queue_sizes': {priority.value: 0 for priority in BatchPriority},
            'last_error': None,
            'error_timestamp': None
        }
        
        # Start background workers
        self._start_workers()
        self._start_health_monitor()
        
        logger.info(f"TokenUsageBatchProcessor initialized with {self.config.max_workers} workers")
    
    def _start_workers(self):
        """Start background processing workers."""
        for priority in BatchPriority:
            worker = threading.Thread(
                target=self._worker_loop,
                args=(priority,),
                daemon=True,
                name=f"BatchWorker-{priority.value}"
            )
            worker.start()
            logger.debug(f"Started worker for priority {priority.value}")
    
    def _start_health_monitor(self):
        """Start health monitoring thread."""
        monitor = threading.Thread(
            target=self._health_monitor_loop,
            daemon=True,
            name="BatchHealthMonitor"
        )
        monitor.start()
        logger.debug("Started health monitor")
    
    def _health_monitor_loop(self):
        """Health monitoring loop."""
        while not self._stop_event.is_set():
            try:
                # Update queue sizes
                with self._lock:
                    for priority in BatchPriority:
                        self.metrics['queue_sizes'][priority.value] = self._queues[priority].qsize()
                
                # Check for potential issues
                self._check_health()
                
                # Wait for next check
                self._stop_event.wait(timeout=self.config.health_check_interval)
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                self._stop_event.wait(1.0)  # Wait 1 second before retrying
    
    def _check_health(self):
        """Check system health and handle potential issues."""
        # Check queue sizes
        for priority, queue_obj in self._queues.items():
            if queue_obj.qsize() > self.config.max_queue_size * 0.8:
                logger.warning(f"High queue size for priority {priority.value}: {queue_obj.qsize()}")
        
        # Check processing time
        if self.metrics['processing_time'] > 0:
            avg_processing_time = self.metrics['processing_time'] / max(1, self.metrics['total_batches_processed'])
            if avg_processing_time > self.config.batch_timeout:
                logger.warning(f"High average processing time: {avg_processing_time:.2f}s")
    
    def _worker_loop(self, priority: BatchPriority):
        """Worker loop for processing batches."""
        while not self._stop_event.is_set():
            try:
                # Get batch from buffer or queue
                batch = self._get_batch_for_processing(priority)
                if not batch:
                    time.sleep(0.1)  # Small delay if no work
                    continue
                
                # Process the batch
                self._process_batch(batch)
                
            except Exception as e:
                logger.error(f"Worker error for priority {priority.value}: {e}")
                time.sleep(1.0)  # Wait before retrying
    
    def _get_batch_for_processing(self, priority: BatchPriority) -> Optional[BatchJob]:
        """Get a batch for processing from the given priority level."""
        # Check buffer first
        buffer = self._batch_buffers[priority]
        if buffer:
            with self._lock:
                if buffer:
                    batch = buffer.pop(0)
                    return batch
        
        # Check queue
        try:
            record = self._queues[priority].get(timeout=1.0)
            if record is None:  # Sentinel
                return None
            
            # Create batch from single record
            return BatchJob(
                batch_id=str(uuid.uuid4()),
                records=[record],
                priority=priority,
                compression=self.config.compression,
                created_at=datetime.utcnow()
            )
            
        except queue.Empty:
            return None
    
    def _process_batch(self, batch: BatchJob):
        """Process a batch of token usage records."""
        start_time = time.time()
        
        try:
            # Compress batch if enabled
            compressed_data = self._compress_batch(batch)
            
            # Insert into database
            success = self._insert_batch_to_db(batch, compressed_data)
            
            # Update metrics
            processing_time = time.time() - start_time
            with self._lock:
                self.metrics['total_batches_processed'] += 1
                self.metrics['total_records_processed'] += len(batch.records)
                self.metrics['processing_time'] += processing_time
                
                if success:
                    self.metrics['successful_batches'] += 1
                    logger.debug(f"Successfully processed batch {batch.batch_id} with {len(batch.records)} records")
                else:
                    self.metrics['failed_batches'] += 1
                    self.metrics['last_error'] = f"Batch {batch.batch_id} failed"
                    self.metrics['error_timestamp'] = datetime.utcnow().isoformat()
                    
                    # Retry if enabled and within retry limit
                    if self.config.retry_failed_batches and batch.retry_count < batch.max_retries:
                        batch.retry_count += 1
                        self._retry_batch(batch)
            
        except Exception as e:
            logger.error(f"Failed to process batch {batch.batch_id}: {e}")
            with self._lock:
                self.metrics['failed_batches'] += 1
                self.metrics['last_error'] = str(e)
                self.metrics['error_timestamp'] = datetime.utcnow().isoformat()
    
    def _compress_batch(self, batch: BatchJob) -> bytes:
        """Compress batch data for storage efficiency."""
        if not self.config.enable_compression:
            return pickle.dumps(batch.records)
        
        try:
            if batch.compression == BatchCompression.GZIP:
                # Convert to JSON and compress
                json_data = json.dumps([asdict(record) for record in batch.records], default=str)
                compressed = gzip.compress(json_data.encode('utf-8'))
                savings = len(json_data.encode('utf-8')) - len(compressed)
                
                with self._lock:
                    self.metrics['compression_savings'] += savings
                
                return compressed
                
            elif batch.compression == BatchCompression.PICKLE:
                return pickle.dumps(batch.records)
                
            else:  # NONE
                return pickle.dumps(batch.records)
                
        except Exception as e:
            logger.error(f"Compression failed for batch {batch.batch_id}: {e}")
            return pickle.dumps(batch.records)
    
    def _insert_batch_to_db(self, batch: BatchJob, compressed_data: bytes) -> bool:
        """Insert batch data into database."""
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
        
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        if not self.db:
            logger.error("Database not available for batch insertion")
            return False
            
        session = self.db._Session()
        try:
            # Create batch records
            db_records = []
            for record in batch.records:
                db_record = TokenUsage(
                    user_id=record.user_id,
                    session_id=record.session_id,
                    tokens_used=record.tokens_used,
                    api_endpoint=record.api_endpoint,
                    priority_level=record.priority_level
                )
                db_records.append(db_record)
            
            # Batch insert
            session.add_all(db_records)
            session.commit()
            
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Database insertion failed for batch {batch.batch_id}: {e}")
            return False
        finally:
            session.close()
    
    def _retry_batch(self, batch: BatchJob):
        """Retry a failed batch."""
        try:
            # Reduce priority for retry
            new_priority = min(batch.priority.value - 1, BatchPriority.LOW.value)
            retry_priority = BatchPriority(new_priority)
            
            # Add back to queue with lower priority
            self._queues[retry_priority].put_nowait(batch)
            logger.info(f"Retrying batch {batch.batch_id} with priority {retry_priority.value}")
            
        except queue.Full:
            logger.error(f"Cannot retry batch {batch.batch_id} - queue full")
        except Exception as e:
            logger.error(f"Failed to retry batch {batch.batch_id}: {e}")
    
    def add_record(self, record: TokenUsageRecord, priority: BatchPriority = BatchPriority.MEDIUM) -> bool:
        """
        Add a record to the batch processor.
        
        Args:
            record: Token usage record to add
            priority: Priority level for the record
            
        Returns:
            True if successfully added, False otherwise
        """
        try:
            # Check for duplicates if enabled
            if self.config.enable_deduplication:
                if self._is_duplicate_record(record):
                    logger.debug(f"Duplicate record detected, skipping: {record.request_id}")
                    return True
            
            # Add to appropriate buffer
            buffer = self._batch_buffers[priority]
            buffer.append(record)
            
            # Check if buffer should be processed
            if len(buffer) >= self.config.max_batch_size:
                self._flush_buffer(priority)
            
            # Update metrics
            with self._lock:
                self.metrics['queue_sizes'][priority.value] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add record to batch processor: {e}")
            return False
    
    def _is_duplicate_record(self, record: TokenUsageRecord) -> bool:
        """Check if a record is a duplicate."""
        # Simple deduplication based on request_id
        # In production, you might want a more sophisticated approach
        return hasattr(record, 'request_id') and record.request_id in getattr(self, '_processed_requests', set())
    
    def _flush_buffer(self, priority: BatchPriority):
        """Flush a buffer by creating a batch job."""
        buffer = self._batch_buffers[priority]
        if not buffer:
            return
        
        # Create batch job
        batch = BatchJob(
            batch_id=str(uuid.uuid4()),
            records=buffer.copy(),
            priority=priority,
            compression=self.config.compression,
            created_at=datetime.utcnow()
        )
        
        # Clear buffer
        buffer.clear()
        
        # Add to queue
        try:
            self._queues[priority].put_nowait(batch)
            logger.debug(f"Flushed buffer with {len(batch.records)} records to priority {priority.value}")
        except queue.Full:
            logger.error(f"Queue full for priority {priority.value}, dropping batch")
            # Update metrics
            with self._lock:
                self.metrics['failed_batches'] += 1
    
    def add_records_batch(self, records: List[TokenUsageRecord], priority: BatchPriority = BatchPriority.MEDIUM) -> Dict[str, Any]:
        """
        Add multiple records to the batch processor.
        
        Args:
            records: List of token usage records
            priority: Priority level for the records
            
        Returns:
            Dictionary with operation results
        """
        results = {
            'total_records': len(records),
            'successful': 0,
            'failed': 0,
            'duplicates': 0
        }
        
        for record in records:
            if self.config.enable_deduplication and self._is_duplicate_record(record):
                results['duplicates'] += 1
                continue
            
            if self.add_record(record, priority):
                results['successful'] += 1
            else:
                results['failed'] += 1
        
        return results
    
    def flush_all_buffers(self):
        """Flush all buffers immediately."""
        logger.info("Flushing all buffers")
        
        for priority in BatchPriority:
            self._flush_buffer(priority)
    
    def get_queue_sizes(self) -> Dict[str, int]:
        """Get current queue sizes for all priorities."""
        sizes = {}
        for priority, queue_obj in self._queues.items():
            sizes[priority.value] = queue_obj.qsize()
        return sizes
    
    def get_buffer_sizes(self) -> Dict[str, int]:
        """Get current buffer sizes for all priorities."""
        sizes = {}
        for priority, buffer in self._batch_buffers.items():
            sizes[priority.value] = len(buffer)
        return sizes
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the batch processor."""
        with self._lock:
            metrics = self.metrics.copy()
        
        # Calculate additional metrics
        total_batches = metrics['total_batches_processed']
        if total_batches > 0:
            metrics['success_rate'] = metrics['successful_batches'] / total_batches
            metrics['failure_rate'] = metrics['failed_batches'] / total_batches
            metrics['avg_records_per_batch'] = metrics['total_records_processed'] / total_batches
        else:
            metrics['success_rate'] = 0.0
            metrics['failure_rate'] = 0.0
            metrics['avg_records_per_batch'] = 0.0
        
        metrics['avg_processing_time'] = (
            metrics['processing_time'] / total_batches if total_batches > 0 else 0.0
        )
        
        # Add queue and buffer sizes
        metrics['queue_sizes'] = self.get_queue_sizes()
        metrics['buffer_sizes'] = self.get_buffer_sizes()
        
        return metrics
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the batch processor."""
        try:
            # Check database connection
            db_health = self.db.health_check() if self.db else False
            
            # Check queue health
            queue_sizes = self.get_queue_sizes()
            total_queue_size = sum(queue_sizes.values())
            queue_healthy = total_queue_size < self.config.max_queue_size * 0.8
            
            # Check buffer health
            buffer_sizes = self.get_buffer_sizes()
            total_buffer_size = sum(buffer_sizes.values())
            buffer_healthy = total_buffer_size < self.config.max_batch_size * 2
            
            # Get recent errors
            with self._lock:
                last_error = self.metrics['last_error']
                error_timestamp = self.metrics['error_timestamp']
            
            overall_health = db_health and queue_healthy and buffer_healthy
            
            return {
                'healthy': overall_health,
                'database_healthy': db_health,
                'queue_healthy': queue_healthy,
                'buffer_healthy': buffer_healthy,
                'total_queue_size': total_queue_size,
                'total_buffer_size': total_buffer_size,
                'queue_sizes': queue_sizes,
                'buffer_sizes': buffer_sizes,
                'last_error': last_error,
                'error_timestamp': error_timestamp,
                'config': {
                    'max_batch_size': self.config.max_batch_size,
                    'max_queue_size': self.config.max_queue_size,
                    'max_workers': self.config.max_workers
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'healthy': False,
                'error': str(e),
                'database_healthy': False,
                'queue_healthy': False,
                'buffer_healthy': False
            }
    
    def shutdown(self):
        """Shutdown the batch processor gracefully."""
        logger.info("Shutting down TokenUsageBatchProcessor")
        
        # Signal stop
        self._stop_event.set()
        
        # Flush all buffers
        self.flush_all_buffers()
        
        # Wait for workers to finish
        time.sleep(2.0)
        
        # Shutdown executor
        self._executor.shutdown(wait=True)
        
        logger.info("TokenUsageBatchProcessor shutdown complete")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


# Convenience functions for direct usage
def create_batch_processor(db: Optional[PostgresDB] = None, 
                          config: Optional[BatchProcessorConfig] = None) -> TokenUsageBatchProcessor:
    """
    Create a batch processor instance.
    
    Args:
        db: Database instance
        config: Batch processor configuration
        
    Returns:
        TokenUsageBatchProcessor instance
    """
    return TokenUsageBatchProcessor(db, config)


def batch_log_records(records: List[TokenUsageRecord],
                     priority: BatchPriority = BatchPriority.MEDIUM,
                     db: Optional[PostgresDB] = None,
                     config: Optional[BatchProcessorConfig] = None) -> Dict[str, Any]:
    """
    Convenience function to batch log records.
    
    Args:
        records: List of token usage records
        priority: Priority level for processing
        db: Database instance
        config: Batch processor configuration
        
    Returns:
        Dictionary with operation results
    """
    processor = TokenUsageBatchProcessor(db, config)
    try:
        return processor.add_records_batch(records, priority)
    finally:
        processor.shutdown()