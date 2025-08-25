"""
Unit tests for Base Cache functionality.

This module contains comprehensive unit tests for the Base Cache abstract class,
testing the interface contract and common functionality that all cache layers must implement.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from src.core.base_cache import (
    BaseCache, CacheEntry, CacheResult, CacheStatus, CacheLayer
)


class MockCache(BaseCache):
    """Mock implementation of BaseCache for testing."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None, layer_type: CacheLayer = CacheLayer.SEMANTIC):
        super().__init__(name, config)
        self._cache = {}
        self._layer_type = layer_type
    
    async def initialize(self) -> bool:
        return True
    
    async def get(self, key: str) -> CacheResult:
        if key in self._cache:
            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                return CacheResult(status=CacheStatus.EXPIRED, error_message="Cache entry expired")
            entry.increment_access()
            self.update_stats(CacheStatus.HIT)
            return CacheResult(status=CacheStatus.HIT, entry=entry)
        else:
            self.update_stats(CacheStatus.MISS)
            return CacheResult(status=CacheStatus.MISS)
    
    async def set(self, key: str, value: Any, 
                 ttl_seconds: Optional[int] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 embedding: Optional[List[float]] = None) -> bool:
        entry = self._create_entry(key, value, ttl_seconds, metadata, embedding)
        self._cache[key] = entry
        return True
    
    async def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    async def clear(self) -> bool:
        self._cache.clear()
        return True
    
    async def exists(self, key: str) -> bool:
        return key in self._cache and not self._cache[key].is_expired()
    
    async def get_stats(self) -> Dict[str, Any]:
        return self.stats
    
    async def cleanup_expired(self) -> int:
        removed_count = 0
        expired_keys = []
        for key, entry in self._cache.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            removed_count += 1
        
        return removed_count
    
    def get_layer(self) -> CacheLayer:
        return self._layer_type


class TestBaseCacheInitialization:
    """Test BaseCache initialization and basic properties."""
    
    def test_cache_creation(self):
        """Test cache instance creation."""
        cache = MockCache("test_cache")
        
        assert cache.name == "test_cache"
        assert cache.config == {}
        assert cache.stats == {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "total_operations": 0
        }
        assert cache.get_layer() == CacheLayer.SEMANTIC
    
    def test_cache_creation_with_config(self):
        """Test cache instance creation with configuration."""
        config = {"ttl": 3600, "max_size": 1000}
        cache = MockCache("test_cache", config)
        
        assert cache.name == "test_cache"
        assert cache.config == config
        assert cache.stats == {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "total_operations": 0
        }
    
    def test_cache_creation_with_different_layer(self):
        """Test cache instance creation with different layer types."""
        cache = MockCache("predictive_cache", layer_type=CacheLayer.PREDICTIVE)
        
        assert cache.get_layer() == CacheLayer.PREDICTIVE
    
    def test_cache_string_representation(self):
        """Test string representation of cache."""
        cache = MockCache("test_cache")
        
        assert str(cache) == "MockCache(name=test_cache, layer=CacheLayer.SEMANTIC)"
        assert repr(cache) == "MockCache(name='test_cache', layer=CacheLayer.SEMANTIC, stats={'hits': 0, 'misses': 0, 'errors': 0, 'total_operations': 0})"


class TestBaseCacheCoreOperations:
    """Test core cache operations."""
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """Test setting and getting cache entries."""
        cache = MockCache("test_cache")
        
        # Set a value
        result = await cache.set("test_key", "test_value")
        assert result is True
        
        # Get the value
        get_result = await cache.get("test_key")
        assert get_result.status == CacheStatus.HIT
        assert get_result.entry.value == "test_value"
        assert get_result.entry.layer == CacheLayer.SEMANTIC
        
        # Stats should reflect the hit
        stats = await cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0
        assert stats["total_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """Test cache miss scenario."""
        cache = MockCache("test_cache")
        
        get_result = await cache.get("nonexistent_key")
        assert get_result.status == CacheStatus.MISS
        assert get_result.entry is None
        
        # Stats should reflect the miss
        stats = await cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1
        assert stats["total_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_cache_delete(self):
        """Test cache deletion."""
        cache = MockCache("test_cache")
        
        # Set a value
        await cache.set("test_key", "test_value")
        
        # Delete it
        result = await cache.delete("test_key")
        assert result is True
        
        # Should be gone
        get_result = await cache.get("test_key")
        assert get_result.status == CacheStatus.MISS
    
    @pytest.mark.asyncio
    async def test_cache_clear(self):
        """Test cache clearing."""
        cache = MockCache("test_cache")
        
        # Set multiple values
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        
        # Clear cache
        result = await cache.clear()
        assert result is True
        
        # Should all be gone
        for key in ["key1", "key2", "key3"]:
            get_result = await cache.get(key)
            assert get_result.status == CacheStatus.MISS
    
    @pytest.mark.asyncio
    async def test_cache_exists(self):
        """Test cache exists functionality."""
        cache = MockCache("test_cache")
        
        # Non-existent key
        assert await cache.exists("nonexistent_key") is False
        
        # Set a value
        await cache.set("test_key", "test_value")
        
        # Should exist
        assert await cache.exists("test_key") is True
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = MockCache("test_cache")
        
        # Set entries with different TTLs
        await cache.set("short_ttl", "value1", ttl_seconds=1)
        await cache.set("long_ttl", "value2", ttl_seconds=3600)
        
        # Mock time to make short_ttl entry expire
        with patch('src.core.base_cache.datetime') as mock_datetime:
            future_time = datetime.utcnow() + timedelta(seconds=2)
            mock_datetime.utcnow.return_value = future_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # Clean up expired entries
            removed = await cache.cleanup_expired()
            
            assert removed >= 1
            assert "short_ttl" not in cache._cache


class TestBaseCacheEntryManagement:
    """Test cache entry management functionality."""
    
    @pytest.mark.asyncio
    async def test_entry_creation(self):
        """Test cache entry creation."""
        cache = MockCache("test_cache")
        
        entry = cache._create_entry(
            key="test_key",
            value="test_value",
            ttl_seconds=3600,
            metadata={"test": "metadata"},
            embedding=[0.1, 0.2, 0.3]
        )
        
        assert entry.key == cache._generate_key("test_key")
        assert entry.value == "test_value"
        assert entry.layer == CacheLayer.SEMANTIC
        assert entry.created_at is not None
        assert entry.expires_at is not None
        assert entry.metadata == {"test": "metadata"}
        assert entry.embedding == [0.1, 0.2, 0.3]
        assert entry.access_count == 0
        assert entry.last_accessed is None
    
    @pytest.mark.asyncio
    async def test_entry_expiry(self):
        """Test cache entry expiry."""
        cache = MockCache("test_cache")
        
        # Set a value with short TTL
        await cache.set("test_key", "test_value", ttl_seconds=1)
        
        # Should be available immediately
        get_result = await cache.get("test_key")
        assert get_result.status == CacheStatus.HIT
        
        # Mock time to be in the future
        with patch('src.core.base_cache.datetime') as mock_datetime:
            future_time = datetime.utcnow() + timedelta(seconds=2)
            mock_datetime.utcnow.return_value = future_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # Should be expired now
            get_result = await cache.get("test_key")
            assert get_result.status == CacheStatus.EXPIRED
    
    @pytest.mark.asyncio
    async def test_entry_access_tracking(self):
        """Test entry access tracking."""
        cache = MockCache("test_cache")
        
        # Set a value
        await cache.set("test_key", "test_value")
        
        # Access it multiple times
        for _ in range(5):
            await cache.get("test_key")
        
        # Check entry access count
        get_result = await cache.get("test_key")
        assert get_result.entry.access_count == 5
        assert get_result.entry.last_accessed is not None
        
        # Check stats
        stats = await cache.get_stats()
        assert stats["hits"] == 5
        assert stats["total_operations"] == 5
    
    def test_key_generation(self):
        """Test key generation consistency."""
        cache = MockCache("test_cache")
        
        # Same key should generate same hash
        key1 = cache._generate_key("test_key")
        key2 = cache._generate_key("test_key")
        assert key1 == key2
        
        # Different keys should generate different hashes
        key3 = cache._generate_key("different_key")
        assert key1 != key3
        
        # Keys should be proper SHA256 hashes
        assert len(key1) == 64  # SHA256 hash length
        assert all(c in '0123456789abcdef' for c in key1)
    
    def test_entry_serialization(self):
        """Test cache entry serialization."""
        cache = MockCache("test_cache")
        
        entry = cache._create_entry(
            key="test_key",
            value="test_value",
            ttl_seconds=3600,
            metadata={"test": "metadata"},
            embedding=[0.1, 0.2, 0.3]
        )
        
        # Test to_dict
        entry_dict = entry.to_dict()
        assert entry_dict["key"] == entry.key
        assert entry_dict["value"] == entry.value
        assert entry_dict["layer"] == entry.layer.value
        assert entry_dict["created_at"] == entry.created_at.isoformat()
        assert entry_dict["expires_at"] == entry.expires_at.isoformat()
        assert entry_dict["metadata"] == entry.metadata
        assert entry_dict["embedding"] == entry.embedding
        assert entry_dict["access_count"] == entry.access_count
        assert entry_dict["last_accessed"] == entry.last_accessed.isoformat()
        
        # Test from_dict
        restored_entry = CacheEntry.from_dict(entry_dict)
        assert restored_entry.key == entry.key
        assert restored_entry.value == entry.value
        assert restored_entry.layer == entry.layer
        assert restored_entry.created_at == entry.created_at
        assert restored_entry.expires_at == entry.expires_at
        assert restored_entry.metadata == entry.metadata
        assert restored_entry.embedding == entry.embedding
        assert restored_entry.access_count == entry.access_count
        assert restored_entry.last_accessed == entry.last_accessed


class TestBaseCacheStatistics:
    """Test cache statistics functionality."""
    
    @pytest.mark.asyncio
    async def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        cache = MockCache("test_cache")
        
        # Initially no hits or misses
        assert cache.get_hit_rate() == 0.0
        
        # Add some hits and misses
        await cache.set("key1", "value1")
        await cache.get("key1")  # Hit
        await cache.get("key2")  # Miss
        await cache.get("key1")  # Hit
        await cache.get("key3")  # Miss
        
        # Hit rate should be 2/4 = 0.5
        assert cache.get_hit_rate() == 0.5
        
        # Check detailed stats
        stats = await cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 2
        assert stats["total_operations"] == 4
        assert stats["hit_rate"] == 0.5
    
    @pytest.mark.asyncio
    async def test_error_tracking(self):
        """Test error tracking."""
        cache = MockCache("test_cache")
        
        # Simulate some operations
        await cache.set("key1", "value1")
        await cache.get("key1")
        await cache.get("key2")
        
        # Manually update error stats
        cache.update_stats(CacheStatus.ERROR)
        cache.update_stats(CacheStatus.ERROR)
        
        # Check error stats
        stats = await cache.get_stats()
        assert stats["errors"] == 2
        assert stats["total_operations"] == 4
    
    @pytest.mark.asyncio
    async def test_stats_reset(self):
        """Test statistics reset."""
        cache = MockCache("test_cache")
        
        # Perform some operations
        await cache.set("key1", "value1")
        await cache.get("key1")
        await cache.get("key2")
        cache.update_stats(CacheStatus.ERROR)
        
        # Reset stats by creating new cache
        new_cache = MockCache("test_cache")
        assert new_cache.stats == {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "total_operations": 0
        }


class TestBaseCacheErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_get_error_handling(self):
        """Test error handling in get operations."""
        cache = MockCache("test_cache")
        
        # Mock get to raise exception
        original_get = cache.get
        async def failing_get(key: str):
            if key == "error_key":
                raise Exception("Test error")
            return await original_get(key)
        
        cache.get = failing_get
        
        # Should handle error gracefully
        result = await cache.get("error_key")
        assert result.status == CacheStatus.ERROR
        assert "error" in result.error_message
        
        # Stats should reflect the error
        stats = await cache.get_stats()
        assert stats["errors"] == 1
        assert stats["total_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_set_error_handling(self):
        """Test error handling in set operations."""
        cache = MockCache("test_cache")
        
        # Mock set to raise exception
        original_set = cache.set
        async def failing_set(key: str, value: Any, **kwargs):
            if key == "error_key":
                raise Exception("Test error")
            return await original_set(key, value, **kwargs)
        
        cache.set = failing_set
        
        # Should handle error gracefully
        result = await cache.set("error_key", "test_value")
        assert result is False
        
        # Stats should not be updated for failed operations
        stats = await cache.get_stats()
        assert stats["total_operations"] == 0
    
    @pytest.mark.asyncio
    async def test_delete_error_handling(self):
        """Test error handling in delete operations."""
        cache = MockCache("test_cache")
        
        # Mock delete to raise exception
        original_delete = cache.delete
        async def failing_delete(key: str):
            if key == "error_key":
                raise Exception("Test error")
            return await original_delete(key)
        
        cache.delete = failing_delete
        
        # Should handle error gracefully
        result = await cache.delete("error_key")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_clear_error_handling(self):
        """Test error handling in clear operations."""
        cache = MockCache("test_cache")
        
        # Mock clear to raise exception
        original_clear = cache.clear
        async def failing_clear():
            raise Exception("Test error")
        
        cache.clear = failing_clear
        
        # Should handle error gracefully
        result = await cache.clear()
        assert result is False


class TestBaseCacheEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent cache operations."""
        cache = MockCache("test_cache")
        
        async def set_operations():
            for i in range(10):
                await cache.set(f"key_{i}", f"value_{i}")
        
        async def get_operations():
            for i in range(10):
                await cache.get(f"key_{i}")
        
        # Run operations concurrently
        await asyncio.gather(set_operations(), get_operations())
        
        # Verify all operations completed
        stats = await cache.get_stats()
        assert stats["total_operations"] >= 20
    
    @pytest.mark.asyncio
    async def test_large_data_handling(self):
        """Test handling of large data objects."""
        cache = MockCache("test_cache")
        
        large_data = {"data": "x" * 1000000}  # 1MB of data
        
        result = await cache.set("large_key", large_data)
        assert result is True
        
        get_result = await cache.get("large_key")
        assert get_result.status == CacheStatus.HIT
        assert get_result.entry.value == large_data
    
    @pytest.mark.asyncio
    async def test_none_values(self):
        """Test handling of None values."""
        cache = MockCache("test_cache")
        
        # Set None value
        result = await cache.set("none_key", None)
        assert result is True
        
        # Get None value
        get_result = await cache.get("none_key")
        assert get_result.status == CacheStatus.HIT
        assert get_result.entry.value is None
    
    @pytest.mark.asyncio
    async def test_empty_string_values(self):
        """Test handling of empty string values."""
        cache = MockCache("test_cache")
        
        # Set empty string
        result = await cache.set("empty_key", "")
        assert result is True
        
        # Get empty string
        get_result = await cache.get("empty_key")
        assert get_result.status == CacheStatus.HIT
        assert get_result.entry.value == ""
    
    @pytest.mark.asyncio
    async def test_special_characters_in_keys(self):
        """Test handling of special characters in keys."""
        cache = MockCache("test_cache")
        
        # Set values with special characters in keys
        special_keys = ["key_with_underscores", "key-with-dashes", "key with spaces", "key@with#special$chars"]
        
        for key in special_keys:
            result = await cache.set(key, f"value_for_{key}")
            assert result is True
        
        # Get all values
        for key in special_keys:
            get_result = await cache.get(key)
            assert get_result.status == CacheStatus.HIT
            assert get_result.entry.value == f"value_for_{key}"
    
    @pytest.mark.asyncio
    async def test_unicode_values(self):
        """Test handling of Unicode values."""
        cache = MockCache("test_cache")
        
        # Set Unicode values
        unicode_values = [
            "Hello, 世界!",
            "Café",
            "🚀 Rocket",
            "Ñoñoño"
        ]
        
        for i, value in enumerate(unicode_values):
            result = await cache.set(f"unicode_key_{i}", value)
            assert result is True
        
        # Get all values
        for i, value in enumerate(unicode_values):
            get_result = await cache.get(f"unicode_key_{i}")
            assert get_result.status == CacheStatus.HIT
            assert get_result.entry.value == value


class TestBaseCacheResult:
    """Test CacheResult functionality."""
    
    def test_cache_result_creation(self):
        """Test CacheResult creation."""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            layer=CacheLayer.SEMANTIC,
            created_at=datetime.utcnow()
        )
        
        # Create hit result
        hit_result = CacheResult(status=CacheStatus.HIT, entry=entry)
        assert hit_result.is_hit() is True
        assert hit_result.is_miss() is False
        assert hit_result.has_error() is False
        
        # Create miss result
        miss_result = CacheResult(status=CacheStatus.MISS)
        assert miss_result.is_hit() is False
        assert miss_result.is_miss() is True
        assert miss_result.has_error() is False
        
        # Create error result
        error_result = CacheResult(status=CacheStatus.ERROR, error_message="Test error")
        assert error_result.is_hit() is False
        assert error_result.is_miss() is False
        assert error_result.has_error() is True
    
    def test_cache_result_with_execution_time(self):
        """Test CacheResult with execution time."""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            layer=CacheLayer.SEMANTIC,
            created_at=datetime.utcnow()
        )
        
        result = CacheResult(
            status=CacheStatus.HIT,
            entry=entry,
            execution_time_ms=15.5
        )
        
        assert result.execution_time_ms == 15.5


class TestBaseCacheLayerEnum:
    """Test CacheLayer enum functionality."""
    
    def test_cache_layer_values(self):
        """Test CacheLayer enum values."""
        assert CacheLayer.PREDICTIVE.value == "predictive"
        assert CacheLayer.SEMANTIC.value == "semantic"
        assert CacheLayer.VECTOR.value == "vector"
        assert CacheLayer.GLOBAL.value == "global"
        assert CacheLayer.VECTOR_DIARY.value == "vector_diary"
    
    def test_cache_layer_comparison(self):
        """Test CacheLayer enum comparison."""
        assert CacheLayer.PREDICTIVE != CacheLayer.SEMANTIC
        assert CacheLayer.SEMANTIC == CacheLayer.SEMANTIC


class TestBaseCacheStatusEnum:
    """Test CacheStatus enum functionality."""
    
    def test_cache_status_values(self):
        """Test CacheStatus enum values."""
        assert CacheStatus.HIT.value == "hit"
        assert CacheStatus.MISS.value == "miss"
        assert CacheStatus.ERROR.value == "error"
        assert CacheStatus.INVALIDATED.value == "invalidated"
        assert CacheStatus.EXPIRED.value == "expired"
    
    def test_cache_status_comparison(self):
        """Test CacheStatus enum comparison."""
        assert CacheStatus.HIT != CacheStatus.MISS
        assert CacheStatus.HIT == CacheStatus.HIT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])