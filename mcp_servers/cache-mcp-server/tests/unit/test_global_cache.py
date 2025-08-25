"""
Unit tests for Global Cache functionality.

This module contains comprehensive unit tests for the Global Cache layer,
testing RAG server integration, fallback mechanisms, and global knowledge management.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from src.cache_layers.global_cache import GlobalCache
from src.core.base_cache import CacheStatus, CacheLayer
from src.core.config import GlobalCacheConfig


class TestGlobalCacheInitialization:
    """Test Global Cache initialization and basic properties."""
    
    def test_cache_creation(self):
        """Test cache instance creation."""
        config = GlobalCacheConfig(
            cache_ttl_seconds=7200,
            rag_server_url="http://localhost:8000",
            rag_server_timeout=30,
            fallback_enabled=True,
            max_fallback_entries=1000
        )
        
        cache = GlobalCache("test_global", config)
        assert cache.name == "test_global"
        assert cache.config == config
        assert cache._cache == {}
        assert cache._fallback_cache == {}
        assert cache._rag_client is None
    
    @pytest.mark.asyncio
    async def test_successful_initialization(self):
        """Test successful cache initialization."""
        config = GlobalCacheConfig(
            cache_ttl_seconds=7200,
            rag_server_url="http://localhost:8000",
            rag_server_timeout=30,
            fallback_enabled=True,
            max_fallback_entries=1000
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = GlobalCache("test_global", config)
            cache._cache_dir = temp_dir
            result = await cache.initialize()
            
            assert result is True
            assert cache._rag_client is not None
            assert os.path.exists(os.path.join(temp_dir, "global_cache.db"))
    
    @pytest.mark.asyncio
    async def test_failed_initialization(self):
        """Test failed cache initialization."""
        config = GlobalCacheConfig(
            cache_ttl_seconds=7200,
            rag_server_url="http://localhost:8000",
            rag_server_timeout=30,
            fallback_enabled=True,
            max_fallback_entries=1000
        )
        
        class FailingGlobalCache(GlobalCache):
            async def _initialize_rag_client(self):
                raise Exception("Test initialization failure")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = FailingGlobalCache("test_global", config)
            cache._cache_dir = temp_dir
            result = await cache.initialize()
            
            assert result is False


class TestGlobalCacheCoreOperations:
    """Test core cache operations."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a global cache configuration."""
        return GlobalCacheConfig(
            cache_ttl_seconds=7200,
            rag_server_url="http://localhost:8000",
            rag_server_timeout=30,
            fallback_enabled=True,
            max_fallback_entries=1000
        )
    
    @pytest.fixture
    def global_cache(self, cache_config):
        """Create a global cache instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = GlobalCache("test_global", cache_config)
            cache._cache_dir = temp_dir
            cache._rag_client = Mock()  # Mock RAG client
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, global_cache):
        """Test setting and getting cache entries."""
        # Set a value
        result = await global_cache.set("test_key", "test_value")
        assert result is True
        
        # Get the value
        get_result = await global_cache.get("test_key")
        assert get_result.status == CacheStatus.HIT
        assert get_result.entry.value == "test_value"
        assert get_result.entry.layer == CacheLayer.GLOBAL
        
        # Stats should reflect the hit
        stats = await global_cache.get_stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 0
        assert stats["total_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, global_cache):
        """Test cache miss scenario."""
        get_result = await global_cache.get("nonexistent_key")
        assert get_result.status == CacheStatus.MISS
        assert get_result.entry is None
        
        # Stats should reflect the miss
        stats = await global_cache.get_stats()
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 1
        assert stats["total_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_cache_expiry(self, global_cache):
        """Test cache expiry functionality."""
        # Set a value with short TTL
        await global_cache.set("test_key", "test_value", ttl_seconds=1)
        
        # Should be available immediately
        get_result = await global_cache.get("test_key")
        assert get_result.status == CacheStatus.HIT
        
        # Mock time to be in the future
        with patch('src.cache_layers.global_cache.datetime') as mock_datetime:
            future_time = datetime.utcnow() + timedelta(seconds=2)
            mock_datetime.utcnow.return_value = future_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # Should be expired now
            get_result = await global_cache.get("test_key")
            assert get_result.status == CacheStatus.EXPIRED
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, global_cache):
        """Test cache deletion."""
        # Set a value
        await global_cache.set("test_key", "test_value")
        
        # Delete it
        result = await global_cache.delete("test_key")
        assert result is True
        
        # Should be gone
        get_result = await global_cache.get("test_key")
        assert get_result.status == CacheStatus.MISS
    
    @pytest.mark.asyncio
    async def test_cache_clear(self, global_cache):
        """Test cache clearing."""
        # Set multiple values
        await global_cache.set("key1", "value1")
        await global_cache.set("key2", "value2")
        await global_cache.set("key3", "value3")
        
        # Clear cache
        result = await global_cache.clear()
        assert result is True
        
        # Should all be gone
        for key in ["key1", "key2", "key3"]:
            get_result = await global_cache.get(key)
            assert get_result.status == CacheStatus.MISS
        
        # Fallback cache should also be cleared
        assert len(global_cache._fallback_cache) == 0
    
    @pytest.mark.asyncio
    async def test_cache_exists(self, global_cache):
        """Test cache exists functionality."""
        # Non-existent key
        assert await global_cache.exists("nonexistent_key") is False
        
        # Set a value
        await global_cache.set("test_key", "test_value")
        
        # Should exist
        assert await global_cache.exists("test_key") is True
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self, global_cache):
        """Test cleanup of expired entries."""
        # Set entries with different TTLs
        await global_cache.set("short_ttl", "value1", ttl_seconds=1)
        await global_cache.set("long_ttl", "value2", ttl_seconds=3600)
        
        # Mock time to make short_ttl entry expire
        with patch('src.cache_layers.global_cache.datetime') as mock_datetime:
            future_time = datetime.utcnow() + timedelta(seconds=2)
            mock_datetime.utcnow.return_value = future_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # Clean up expired entries
            removed = await global_cache.cleanup_expired()
            
            assert removed >= 1
            assert "short_ttl" not in global_cache._cache
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, global_cache):
        """Test cache statistics."""
        # Set some values
        await global_cache.set("key1", "value1")
        await global_cache.set("key2", "value2")
        
        # Get stats
        stats = await global_cache.get_stats()
        
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["cache_errors"] == 0
        assert stats["total_operations"] == 0
        assert stats["total_cached_items"] == 2
        assert stats["hit_rate"] == 0.0
        assert stats["rag_requests"] == 0
        assert stats["rag_hits"] == 0
        assert stats["rag_errors"] == 0
        assert stats["fallback_entries"] == 0
    
    @pytest.mark.asyncio
    async def test_global_stats(self, global_cache):
        """Test global cache statistics."""
        # Mock some RAG operations
        global_cache._rag_stats = {
            "total_requests": 10,
            "successful_requests": 8,
            "failed_requests": 2,
            "avg_response_time": 150.0,
            "cache_hits": 5,
            "cache_misses": 5
        }
        
        stats = await global_cache.get_stats()
        
        assert stats["rag_stats"]["total_requests"] == 10
        assert stats["rag_stats"]["successful_requests"] == 8
        assert stats["rag_stats"]["failed_requests"] == 2
        assert stats["rag_stats"]["avg_response_time"] == 150.0
        assert stats["rag_stats"]["cache_hits"] == 5
        assert stats["rag_stats"]["cache_misses"] == 5
    
    @pytest.mark.asyncio
    async def test_stats_integration(self, global_cache):
        """Test statistics integration with cache operations."""
        # Perform various operations
        await global_cache.set("key1", "value1")
        await global_cache.get("key1")  # Hit
        await global_cache.get("key2")  # Miss
        
        # Check final stats
        stats = await global_cache.get_stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["total_operations"] == 2
        assert stats["hit_rate"] == 0.5


class TestGlobalCacheRAGIntegration:
    """Test RAG server integration functionality."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a global cache configuration."""
        return GlobalCacheConfig(
            cache_ttl_seconds=7200,
            rag_server_url="http://localhost:8000",
            rag_server_timeout=30,
            fallback_enabled=True,
            max_fallback_entries=1000
        )
    
    @pytest.fixture
    def global_cache(self, cache_config):
        """Create a global cache instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = GlobalCache("test_global", cache_config)
            cache._cache_dir = temp_dir
            cache._rag_client = Mock()  # Mock RAG client
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_rag_server_success(self, global_cache):
        """Test successful RAG server response."""
        # Mock RAG client to return successful response
        global_cache._rag_client.query.return_value = {
            "success": True,
            "data": "RAG response data",
            "source": "knowledge_base",
            "confidence": 0.95
        }
        
        # Query RAG server
        result = await global_cache.query_rag_server("test query")
        
        assert result["success"] is True
        assert result["data"] == "RAG response data"
        assert result["source"] == "knowledge_base"
        assert result["confidence"] == 0.95
        
        # RAG client should have been called
        global_cache._rag_client.query.assert_called_once_with("test query")
    
    @pytest.mark.asyncio
    async def test_rag_server_failure(self, global_cache):
        """Test RAG server failure scenario."""
        # Mock RAG client to return failure
        global_cache._rag_client.query.return_value = {
            "success": False,
            "error": "RAG server error",
            "source": None,
            "confidence": 0.0
        }
        
        # Query RAG server
        result = await global_cache.query_rag_server("test query")
        
        assert result["success"] is False
        assert result["error"] == "RAG server error"
        assert result["source"] is None
        assert result["confidence"] == 0.0
    
    @pytest.mark.asyncio
    async def test_rag_server_timeout(self, global_cache):
        """Test RAG server timeout scenario."""
        # Mock RAG client to raise timeout exception
        global_cache._rag_client.query.side_effect = asyncio.TimeoutError("Request timeout")
        
        # Query RAG server
        result = await global_cache.query_rag_server("test query")
        
        assert result["success"] is False
        assert "timeout" in result["error"].lower()
        assert result["source"] is None
        assert result["confidence"] == 0.0
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, global_cache):
        """Test fallback mechanism when RAG server fails."""
        # Mock RAG client to fail
        global_cache._rag_client.query.return_value = {
            "success": False,
            "error": "RAG server error",
            "source": None,
            "confidence": 0.0
        }
        
        # Set some fallback data
        await global_cache._fallback_cache.set("fallback_key", "fallback_value")
        
        # Query should use fallback
        result = await global_cache.query_rag_server("test query")
        
        # Should return fallback data
        assert result["success"] is True
        assert result["data"] == "fallback_value"
        assert result["source"] == "fallback"
        assert result["confidence"] == 0.5  # Default fallback confidence
    
    @pytest.mark.asyncio
    async def test_fallback_cache_limit(self, global_cache):
        """Test fallback cache size limit enforcement."""
        # Set many fallback entries
        for i in range(global_cache.config.max_fallback_entries + 10):
            await global_cache._fallback_cache.set(f"fallback_key_{i}", f"fallback_value_{i}")
        
        # Should not exceed max limit
        assert len(global_cache._fallback_cache) <= global_cache.config.max_fallback_entries


class TestGlobalCacheErrorHandling:
    """Test error handling scenarios in Global Cache."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a global cache configuration."""
        return GlobalCacheConfig(
            cache_ttl_seconds=7200,
            rag_server_url="http://localhost:8000",
            rag_server_timeout=30,
            fallback_enabled=True,
            max_fallback_entries=1000
        )
    
    @pytest.fixture
    def global_cache(self, cache_config):
        """Create a global cache instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = GlobalCache("test_global", cache_config)
            cache._cache_dir = temp_dir
            cache._rag_client = Mock()  # Mock RAG client
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_rag_client_error_handling(self, global_cache):
        """Test error handling in RAG client operations."""
        # Mock RAG client to raise exception
        global_cache._rag_client.query.side_effect = Exception("RAG client error")
        
        # Should handle error gracefully
        result = await global_cache.query_rag_server("test query")
        
        assert result["success"] is False
        assert "error" in result["error"].lower()
        assert result["source"] is None
        assert result["confidence"] == 0.0
    
    @pytest.mark.asyncio
    async def test_fallback_cache_error_handling(self, global_cache):
        """Test error handling in fallback cache operations."""
        # Mock fallback cache to fail
        global_cache._fallback_cache.set = AsyncMock(return_value=False)
        
        # Should handle error gracefully
        result = await global_cache._add_to_fallback("test_key", "test_value")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, global_cache):
        """Test error handling in network operations."""
        # Mock network error
        global_cache._rag_client.query.side_effect = ConnectionError("Network error")
        
        # Should handle error gracefully
        result = await global_cache.query_rag_server("test query")
        
        assert result["success"] is False
        assert "network" in result["error"].lower()
        assert result["source"] is None
        assert result["confidence"] == 0.0


class TestGlobalCacheEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a global cache configuration."""
        return GlobalCacheConfig(
            cache_ttl_seconds=7200,
            rag_server_url="http://localhost:8000",
            rag_server_timeout=30,
            fallback_enabled=True,
            max_fallback_entries=1000
        )
    
    @pytest.fixture
    def global_cache(self, cache_config):
        """Create a global cache instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = GlobalCache("test_global", cache_config)
            cache._cache_dir = temp_dir
            cache._rag_client = Mock()  # Mock RAG client
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, global_cache):
        """Test concurrent cache operations."""
        async def set_operations():
            for i in range(10):
                await global_cache.set(f"key_{i}", f"value_{i}")
        
        async def get_operations():
            for i in range(10):
                await global_cache.get(f"key_{i}")
        
        # Run operations concurrently
        await asyncio.gather(set_operations(), get_operations())
        
        # Verify all operations completed
        stats = await global_cache.get_stats()
        assert stats["total_operations"] >= 20
    
    @pytest.mark.asyncio
    async def test_large_data_handling(self, global_cache):
        """Test handling of large data objects."""
        large_data = {"data": "x" * 1000000}  # 1MB of data
        
        result = await global_cache.set("large_key", large_data)
        assert result is True
        
        get_result = await global_cache.get("large_key")
        assert get_result.status == CacheStatus.HIT
        assert get_result.entry.value == large_data
    
    @pytest.mark.asyncio
    async def test_rag_server_unavailable(self, global_cache):
        """Test behavior when RAG server is unavailable."""
        # Mock RAG client to be unavailable
        global_cache._rag_client.query.side_effect = ConnectionError("Server unavailable")
        
        # Should still work with fallback
        result = await global_cache.query_rag_server("test query")
        
        # Should return fallback response
        assert result["success"] is True
        assert result["source"] == "fallback"
        assert result["confidence"] == 0.5
    
    @pytest.mark.asyncio
    async def test_fallback_disabled(self, global_cache):
        """Test behavior when fallback is disabled."""
        # Disable fallback
        global_cache.config.fallback_enabled = False
        
        # Mock RAG client to fail
        global_cache._rag_client.query.return_value = {
            "success": False,
            "error": "RAG server error",
            "source": None,
            "confidence": 0.0
        }
        
        # Should return failure without fallback
        result = await global_cache.query_rag_server("test query")
        
        assert result["success"] is False
        assert result["source"] is None
        assert result["confidence"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])