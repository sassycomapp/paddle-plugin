"""
Base Cache Interface and Abstract Classes

This module defines the foundational interface and abstract classes for all cache layers
in the intelligent caching architecture. It provides a common contract that all cache
implementations must follow.

Author: KiloCode
License: Apache 2.0
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
import hashlib
import json

logger = logging.getLogger(__name__)


class CacheLayer(Enum):
    """Enumeration of cache layers in the architecture."""
    PREDICTIVE = "predictive"
    SEMANTIC = "semantic"
    VECTOR = "vector"
    GLOBAL = "global"
    VECTOR_DIARY = "vector_diary"


class CacheStatus(Enum):
    """Cache operation status codes."""
    HIT = "hit"
    MISS = "miss"
    ERROR = "error"
    INVALIDATED = "invalidated"
    EXPIRED = "expired"


@dataclass
class CacheEntry:
    """Represents a single cache entry with metadata."""
    key: str
    value: Any
    layer: CacheLayer
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None
    similarity_score: Optional[float] = None
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def increment_access(self):
        """Increment access count and update last accessed time."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cache entry to dictionary representation."""
        return {
            "key": self.key,
            "value": self.value,
            "layer": self.layer.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "metadata": self.metadata,
            "embedding": self.embedding,
            "similarity_score": self.similarity_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create cache entry from dictionary representation."""
        return cls(
            key=data["key"],
            value=data["value"],
            layer=CacheLayer(data["layer"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None,
            metadata=data.get("metadata"),
            embedding=data.get("embedding"),
            similarity_score=data.get("similarity_score")
        )


@dataclass
class CacheResult:
    """Represents the result of a cache operation."""
    status: CacheStatus
    entry: Optional[CacheEntry] = None
    error_message: Optional[str] = None
    source_layer: Optional[CacheLayer] = None
    execution_time_ms: Optional[float] = None
    
    def is_hit(self) -> bool:
        """Check if the cache operation was a hit."""
        return self.status == CacheStatus.HIT
    
    def is_miss(self) -> bool:
        """Check if the cache operation was a miss."""
        return self.status == CacheStatus.MISS
    
    def has_error(self) -> bool:
        """Check if the cache operation resulted in an error."""
        return self.status == CacheStatus.ERROR


class BaseCache(ABC):
    """
    Abstract base class for all cache layers.
    
    This class defines the interface that all cache implementations must follow,
    ensuring consistency across the five-layer caching architecture.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the cache layer.
        
        Args:
            name: Unique name for this cache instance
            config: Configuration dictionary for the cache layer
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "total_operations": 0
        }
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the cache layer.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get(self, key: str) -> CacheResult:
        """
        Retrieve a value from the cache.
        
        Args:
            key: The cache key to retrieve
            
        Returns:
            CacheResult containing the status and retrieved entry
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, 
                 ttl_seconds: Optional[int] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 embedding: Optional[List[float]] = None) -> bool:
        """
        Store a value in the cache.
        
        Args:
            key: The cache key
            value: The value to store
            ttl_seconds: Optional time-to-live in seconds
            metadata: Optional metadata dictionary
            embedding: Optional embedding vector for similarity search
            
        Returns:
            True if the value was stored successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key to delete
            
        Returns:
            True if the value was deleted successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """
        Clear all values from the cache.
        
        Returns:
            True if the cache was cleared successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: The cache key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        pass
    
    @abstractmethod
    async def cleanup_expired(self) -> int:
        """
        Remove expired entries from the cache.
        
        Returns:
            Number of expired entries removed
        """
        pass
    
    def _generate_key(self, key: str) -> str:
        """
        Generate a consistent cache key.
        
        Args:
            key: Original key string
            
        Returns:
            Generated cache key
        """
        return hashlib.sha256(key.encode()).hexdigest()
    
    def _create_entry(self, key: str, value: Any, 
                     ttl_seconds: Optional[int] = None,
                     metadata: Optional[Dict[str, Any]] = None,
                     embedding: Optional[List[float]] = None) -> CacheEntry:
        """
        Create a cache entry with proper timestamps.
        
        Args:
            key: Cache key
            value: Cache value
            ttl_seconds: Optional time-to-live in seconds
            metadata: Optional metadata
            embedding: Optional embedding vector
            
        Returns:
            CacheEntry instance
        """
        expires_at = None
        if ttl_seconds is not None:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        
        return CacheEntry(
            key=self._generate_key(key),
            value=value,
            layer=self.get_layer(),
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            metadata=metadata or {},
            embedding=embedding
        )
    
    @abstractmethod
    def get_layer(self) -> CacheLayer:
        """
        Get the cache layer type.
        
        Returns:
            CacheLayer enum value
        """
        pass
    
    def update_stats(self, status: CacheStatus):
        """
        Update cache statistics.
        
        Args:
            status: The status of the operation
        """
        self.stats["total_operations"] += 1
        
        if status == CacheStatus.HIT:
            self.stats["hits"] += 1
        elif status == CacheStatus.MISS:
            self.stats["misses"] += 1
        elif status == CacheStatus.ERROR:
            self.stats["errors"] += 1
    
    def get_hit_rate(self) -> float:
        """
        Calculate the cache hit rate.
        
        Returns:
            Hit rate as a percentage (0.0 to 1.0)
        """
        total = self.stats["hits"] + self.stats["misses"]
        if total == 0:
            return 0.0
        return self.stats["hits"] / total
    
    async def close(self):
        """
        Clean up resources when the cache is being shut down.
        
        This method should be overridden by subclasses to perform
        any necessary cleanup operations.
        """
        pass
    
    def __str__(self) -> str:
        """String representation of the cache."""
        return f"{self.__class__.__name__}(name={self.name}, layer={self.get_layer().value})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the cache."""
        return (f"{self.__class__.__name__}(name={self.name!r}, "
                f"layer={self.get_layer()}, stats={self.stats})")