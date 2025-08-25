"""
Lock Manager for Concurrent Request Handling

This module provides thread-safe locking mechanisms for rate limiting and token allocation
to ensure proper handling of concurrent requests and prevent race conditions.
"""

import logging
import threading
import time
from typing import Dict, Optional, Any, Set
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class LockType(Enum):
    """Types of locks supported by the lock manager."""
    TOKEN_ALLOCATION = "token_allocation"
    RATE_LIMIT_CHECK = "rate_limit_check"
    USAGE_UPDATE = "usage_update"
    EMERGENCY_OVERRIDE = "emergency_override"


@dataclass
class LockInfo:
    """Information about a lock."""
    lock_id: str
    lock_type: LockType
    resource_id: str
    acquired_at: datetime
    timeout: float
    thread_id: int
    recursive_count: int = 0


class LockTimeoutError(Exception):
    """Raised when a lock cannot be acquired within the specified timeout."""
    pass


class LockManager:
    """
    Thread-safe lock manager for rate limiting and token allocation.
    
    Provides various types of locks with timeout handling and deadlock prevention.
    Supports recursive locking for the same thread and automatic cleanup.
    """
    
    def __init__(self, default_timeout: float = 30.0, cleanup_interval: float = 60.0):
        """
        Initialize the lock manager.
        
        Args:
            default_timeout: Default timeout for acquiring locks in seconds
            cleanup_interval: Interval for cleaning up expired locks in seconds
        """
        self.default_timeout = default_timeout
        self.cleanup_interval = cleanup_interval
        self._locks: Dict[str, threading.Lock] = {}
        self._lock_info: Dict[str, LockInfo] = {}
        self._thread_local = threading.local()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()
        
        # Start cleanup thread
        self._start_cleanup_thread()
        
        logger.info(f"LockManager initialized with default_timeout={default_timeout}s, cleanup_interval={cleanup_interval}s")
    
    def _start_cleanup_thread(self):
        """Start the background cleanup thread."""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._running = True
            self._cleanup_thread = threading.Thread(target=self._cleanup_expired_locks, daemon=True)
            self._cleanup_thread.start()
            logger.info("Lock cleanup thread started")
    
    def _cleanup_expired_locks(self):
        """Background thread to clean up expired locks."""
        while self._running:
            try:
                time.sleep(self.cleanup_interval)
                self._remove_expired_locks()
            except Exception as e:
                logger.error(f"Error in lock cleanup thread: {e}")
    
    def _remove_expired_locks(self):
        """Remove expired locks from the manager."""
        current_time = datetime.utcnow()
        expired_locks = []
        
        with self._lock:
            for lock_id, info in self._lock_info.items():
                if (current_time - info.acquired_at).total_seconds() > info.timeout:
                    expired_locks.append(lock_id)
            
            for lock_id in expired_locks:
                self._force_release_lock(lock_id)
                logger.warning(f"Force released expired lock: {lock_id}")
    
    def _force_release_lock(self, lock_id: str):
        """Force release a lock without checking thread ownership."""
        if lock_id in self._locks:
            try:
                self._locks[lock_id].release()
                del self._locks[lock_id]
                del self._lock_info[lock_id]
                logger.debug(f"Force released lock: {lock_id}")
            except Exception as e:
                logger.error(f"Error force releasing lock {lock_id}: {e}")
    
    def _get_thread_id(self) -> int:
        """Get the current thread ID, creating thread-local storage if needed."""
        if not hasattr(self._thread_local, 'id'):
            self._thread_local.id = threading.current_thread().ident
        thread_id = self._thread_local.id
        return thread_id if thread_id is not None else 0
    
    def _generate_lock_id(self, lock_type: LockType, resource_id: str) -> str:
        """Generate a unique lock ID."""
        return f"{lock_type.value}_{resource_id}_{uuid.uuid4().hex[:8]}"
    
    def _can_acquire_lock(self, lock_id: str, thread_id: int) -> bool:
        """Check if the current thread can acquire a lock."""
        if lock_id not in self._lock_info:
            return True
        
        info = self._lock_info[lock_id]
        # Allow recursive locking by the same thread
        if info.thread_id == thread_id:
            return True
        
        # Check if lock has expired
        if (datetime.utcnow() - info.acquired_at).total_seconds() > info.timeout:
            return True
        
        return False
    
    def acquire_lock(self, lock_type: LockType, resource_id: str, 
                   timeout: Optional[float] = None) -> str:
        """
        Acquire a lock of the specified type for a resource.
        
        Args:
            lock_type: Type of lock to acquire
            resource_id: Resource identifier to lock
            timeout: Timeout in seconds (uses default if None)
            
        Returns:
            Lock ID that can be used to release the lock
            
        Raises:
            LockTimeoutError: If lock cannot be acquired within timeout
        """
        if timeout is None:
            timeout = self.default_timeout
        
        lock_id = self._generate_lock_id(lock_type, resource_id)
        thread_id = self._get_thread_id()
        start_time = time.time()
        
        logger.debug(f"Attempting to acquire lock: {lock_id} for resource: {resource_id}")
        
        while True:
            # Check if we can acquire the lock
            if self._can_acquire_lock(lock_id, thread_id):
                break
            
            # Check timeout
            if time.time() - start_time > timeout:
                raise LockTimeoutError(f"Could not acquire lock {lock_id} within {timeout} seconds")
            
            # Sleep briefly before retrying
            time.sleep(0.1)
        
        # Acquire the lock
        with self._lock:
            # Create lock if it doesn't exist
            if lock_id not in self._locks:
                self._locks[lock_id] = threading.Lock()
            
            # Acquire the actual lock
            self._locks[lock_id].acquire()
            
            # Update lock info
            if lock_id in self._lock_info and self._lock_info[lock_id].thread_id == thread_id:
                # Recursive lock
                self._lock_info[lock_id].recursive_count += 1
            else:
                # New lock
                self._lock_info[lock_id] = LockInfo(
                    lock_id=lock_id,
                    lock_type=lock_type,
                    resource_id=resource_id,
                    acquired_at=datetime.utcnow(),
                    timeout=timeout,
                    thread_id=thread_id,
                    recursive_count=1
                )
            
            logger.debug(f"Acquired lock: {lock_id} (recursive: {self._lock_info[lock_id].recursive_count})")
            return lock_id
    
    def release_lock(self, lock_id: str):
        """
        Release a lock.
        
        Args:
            lock_id: Lock ID to release
        """
        with self._lock:
            if lock_id not in self._lock_info:
                logger.warning(f"Attempted to release unknown lock: {lock_id}")
                return
            
            info = self._lock_info[lock_id]
            thread_id = self._get_thread_id()
            
            # Check if current thread owns the lock
            if info.thread_id != thread_id:
                logger.error(f"Thread {thread_id} attempted to release lock {lock_id} owned by thread {info.thread_id}")
                return
            
            # Release the lock
            if info.recursive_count > 1:
                # Recursive lock, just decrement count
                info.recursive_count -= 1
                logger.debug(f"Released recursive lock: {lock_id} (remaining: {info.recursive_count})")
            else:
                # Final release
                try:
                    self._locks[lock_id].release()
                    del self._locks[lock_id]
                    del self._lock_info[lock_id]
                    logger.debug(f"Released lock: {lock_id}")
                except Exception as e:
                    logger.error(f"Error releasing lock {lock_id}: {e}")
    
    @contextmanager
    def lock(self, lock_type: LockType, resource_id: str, timeout: Optional[float] = None):
        """
        Context manager for acquiring and releasing locks.
        
        Args:
            lock_type: Type of lock to acquire
            resource_id: Resource identifier to lock
            timeout: Timeout in seconds (uses default if None)
            
        Yields:
            Lock ID that can be used for additional operations
            
        Raises:
            LockTimeoutError: If lock cannot be acquired within timeout
        """
        lock_id = None
        try:
            lock_id = self.acquire_lock(lock_type, resource_id, timeout)
            yield lock_id
        finally:
            if lock_id:
                self.release_lock(lock_id)
    
    def is_locked(self, lock_type: LockType, resource_id: str) -> bool:
        """
        Check if a resource is currently locked.
        
        Args:
            lock_type: Type of lock to check
            resource_id: Resource identifier to check
            
        Returns:
            True if the resource is locked, False otherwise
        """
        with self._lock:
            # Look for any lock of this type for this resource
            for info in self._lock_info.values():
                if info.lock_type == lock_type and info.resource_id == resource_id:
                    return True
            return False
    
    def get_lock_info(self, lock_id: str) -> Optional[LockInfo]:
        """
        Get information about a specific lock.
        
        Args:
            lock_id: Lock ID to get information for
            
        Returns:
            LockInfo if the lock exists, None otherwise
        """
        with self._lock:
            return self._lock_info.get(lock_id)
    
    def get_active_locks(self) -> Dict[str, LockInfo]:
        """
        Get all currently active locks.
        
        Returns:
            Dictionary of lock_id to LockInfo for all active locks
        """
        with self._lock:
            return self._lock_info.copy()
    
    def emergency_release_all(self, lock_type: Optional[LockType] = None):
        """
        Emergency release of all locks or locks of a specific type.
        
        Args:
            lock_type: Specific lock type to release (None for all types)
        """
        with self._lock:
            locks_to_release = []
            for lock_id, info in self._lock_info.items():
                if lock_type is None or info.lock_type == lock_type:
                    locks_to_release.append(lock_id)
            
            for lock_id in locks_to_release:
                self._force_release_lock(lock_id)
            
            logger.warning(f"Emergency released {len(locks_to_release)} locks")
    
    def shutdown(self):
        """Shutdown the lock manager and cleanup resources."""
        self._running = False
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5.0)
        
        # Release all remaining locks
        self.emergency_release_all()
        
        logger.info("LockManager shutdown complete")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


# Global lock manager instance
_global_lock_manager = None


def get_lock_manager() -> LockManager:
    """Get the global lock manager instance."""
    global _global_lock_manager
    if _global_lock_manager is None:
        _global_lock_manager = LockManager()
    return _global_lock_manager


def set_lock_manager(manager: LockManager):
    """Set the global lock manager instance."""
    global _global_lock_manager
    _global_lock_manager = manager