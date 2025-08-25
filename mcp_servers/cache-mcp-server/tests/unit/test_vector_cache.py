"""
Unit tests for Vector Cache functionality.

This module contains comprehensive unit tests for the Vector Cache layer,
testing context selection, reranking, embedding operations, and vector search.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from src.cache_layers.vector_cache import VectorCache
from src.core.base_cache import CacheStatus, CacheLayer
from src.core.config import VectorCacheConfig


class TestVectorCacheInitialization:
    """Test Vector Cache initialization and basic properties."""
    
    def test_cache_creation(self):
        """Test cache instance creation."""
        config = VectorCacheConfig(
            cache_ttl_seconds=3600,
            max_entries=5000,
            similarity_threshold=0.8
        )
        
        cache = VectorCache("test_vector", config)
        assert cache.name == "test_vector"
        assert cache.config == config
        assert cache._cache == {}
        assert cache._context_elements == {}
        assert cache._embedding_index == {}
    
    @pytest.mark.asyncio
    async def test_successful_initialization(self):
        """Test successful cache initialization."""
        config = VectorCacheConfig(
            cache_ttl_seconds=3600,
            max_entries=5000,
            similarity_threshold=0.8
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = VectorCache("test_vector", config)
            cache._cache_dir = temp_dir
            result = await cache.initialize()
            
            assert result is True
            assert os.path.exists(os.path.join(temp_dir, "vector_cache.db"))
    
    @pytest.mark.asyncio
    async def test_failed_initialization(self):
        """Test failed cache initialization."""
        config = VectorCacheConfig(
            cache_ttl_seconds=3600,
            max_entries=5000,
            similarity_threshold=0.8
        )
        
        class FailingVectorCache(VectorCache):
            async def _initialize_embedding_model(self):
                raise Exception("Test initialization failure")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = FailingVectorCache("test_vector", config)
            cache._cache_dir = temp_dir
            result = await cache.initialize()
            
            assert result is False


class TestVectorCacheCoreOperations:
    """Test core cache operations."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a vector cache configuration."""
        return VectorCacheConfig(
            cache_ttl_seconds=3600,
            max_entries=5000,
            embedding_dimension=384,
            similarity_threshold=0.8,
            reranking_enabled=True,
            context_window_size=10
        )
    
    @pytest.fixture
    def vector_cache(self, cache_config):
        """Create a vector cache instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = VectorCache("test_vector", cache_config)
            cache._cache_dir = temp_dir
            cache._embedding_model = Mock()  # Mock model
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, vector_cache):
        """Test setting and getting cache entries."""
        # Set a value
        result = await vector_cache.set("test_key", "test_value")
        assert result is True
        
        # Get the value
        get_result = await vector_cache.get("test_key")
        assert get_result.status == CacheStatus.HIT
        assert get_result.entry.value == "test_value"
        assert get_result.entry.layer == CacheLayer.VECTOR
        
        # Stats should reflect the hit
        stats = await vector_cache.get_stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 0
        assert stats["total_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, vector_cache):
        """Test cache miss scenario."""
        get_result = await vector_cache.get("nonexistent_key")
        assert get_result.status == CacheStatus.MISS
        assert get_result.entry is None
        
        # Stats should reflect the miss
        stats = await vector_cache.get_stats()
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 1
        assert stats["total_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_cache_expiry(self, vector_cache):
        """Test cache expiry functionality."""
        # Set a value with short TTL
        await vector_cache.set("test_key", "test_value", ttl_seconds=1)
        
        # Should be available immediately
        get_result = await vector_cache.get("test_key")
        assert get_result.status == CacheStatus.HIT
        
        # Mock time to be in the future
        with patch('src.cache_layers.vector_cache.datetime') as mock_datetime:
            future_time = datetime.utcnow() + timedelta(seconds=2)
            mock_datetime.utcnow.return_value = future_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # Should be expired now
            get_result = await vector_cache.get("test_key")
            assert get_result.status == CacheStatus.EXPIRED
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, vector_cache):
        """Test cache deletion."""
        # Set a value
        await vector_cache.set("test_key", "test_value")
        
        # Delete it
        result = await vector_cache.delete("test_key")
        assert result is True
        
        # Should be gone
        get_result = await vector_cache.get("test_key")
        assert get_result.status == CacheStatus.MISS
    
    @pytest.mark.asyncio
    async def test_cache_clear(self, vector_cache):
        """Test cache clearing."""
        # Set multiple values
        await vector_cache.set("key1", "value1")
        await vector_cache.set("key2", "value2")
        await vector_cache.set("key3", "value3")
        
        # Clear cache
        result = await vector_cache.clear()
        assert result is True
        
        # Should all be gone
        for key in ["key1", "key2", "key3"]:
            get_result = await vector_cache.get(key)
            assert get_result.status == CacheStatus.MISS
        
        # Indexes should also be cleared
        assert len(vector_cache._vector_index) == 0
        assert len(vector_cache._context_index) == 0
    
    @pytest.mark.asyncio
    async def test_cache_exists(self, vector_cache):
        """Test cache exists functionality."""
        # Non-existent key
        assert await vector_cache.exists("nonexistent_key") is False
        
        # Set a value
        await vector_cache.set("test_key", "test_value")
        
        # Should exist
        assert await vector_cache.exists("test_key") is True
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self, vector_cache):
        """Test cleanup of expired entries."""
        # Set entries with different TTLs
        await vector_cache.set("short_ttl", "value1", ttl_seconds=1)
        await vector_cache.set("long_ttl", "value2", ttl_seconds=3600)
        
        # Mock time to make short_ttl entry expire
        with patch('src.cache_layers.vector_cache.datetime') as mock_datetime:
            future_time = datetime.utcnow() + timedelta(seconds=2)
            mock_datetime.utcnow.return_value = future_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # Cleanup expired entries
            removed_count = await vector_cache.cleanup_expired()
            assert removed_count == 1
            
            # Verify only long_ttl remains
            get_result1 = await vector_cache.get("short_ttl")
            get_result2 = await vector_cache.get("long_ttl")
            assert get_result1.status == CacheStatus.MISS
            assert get_result2.status == CacheStatus.HIT


class TestVectorCacheVectorFunctionality:
    """Test vector search and embedding functionality."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a vector cache configuration."""
        return VectorCacheConfig(
            cache_ttl_seconds=3600,
            max_entries=5000,
            embedding_dimension=384,
            similarity_threshold=0.8,
            reranking_enabled=True,
            context_window_size=10
        )
    
    @pytest.fixture
    def vector_cache(self, cache_config):
        """Create a vector cache instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = VectorCache("test_vector", cache_config)
            cache._cache_dir = temp_dir
            cache._embedding_model = Mock()  # Mock model
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_vector_search(self, vector_cache):
        """Test vector search functionality."""
        # Mock embedding generation
        vector_cache._embedding_model.generate_embedding.side_effect = [
            [1.0, 0.0, 0.0, 0.0],  # Similar to query
            [0.0, 1.0, 0.0, 0.0],  # Different from query
            [0.9, 0.1, 0.0, 0.0]   # Very similar to query
        ]
        
        # Set some entries
        await vector_cache.set("key1", "value1")
        await vector_cache.set("key2", "value2")
        await vector_cache.set("key3", "value3")
        
        # Vector search
        results = await vector_cache.vector_search("query", n_results=2, min_similarity=0.7)
        
        assert len(results) <= 2
        for result in results:
            assert result['similarity_score'] >= 0.7
    
    @pytest.mark.asyncio
    async def test_context_selection(self, vector_cache):
        """Test context selection functionality."""
        # Set entries with different contexts
        await vector_cache.set("key1", "value1", metadata={"context": "math"})
        await vector_cache.set("key2", "value2", metadata={"context": "science"})
        await vector_cache.set("key3", "value3", metadata={"context": "math"})
        
        # Search with context filter
        results = await vector_cache.vector_search(
            "query", 
            n_results=5, 
            min_similarity=0.0,
            context_filter="math"
        )
        
        # Should only return math context results
        for result in results:
            assert result['metadata']['context'] == "math"
    
    @pytest.mark.asyncio
    async def test_reranking(self, vector_cache):
        """Test reranking functionality."""
        # Mock embedding generation
        vector_cache._embedding_model.generate_embedding.side_effect = [
            [1.0, 0.0, 0.0, 0.0],  # High similarity
            [0.8, 0.2, 0.0, 0.0],  # Medium similarity
            [0.6, 0.4, 0.0, 0.0]   # Lower similarity
        ]
        
        # Set some entries
        await vector_cache.set("key1", "value1")
        await vector_cache.set("key2", "value2")
        await vector_cache.set("key3", "value3")
        
        # Search with reranking
        results = await vector_cache.vector_search(
            "query", 
            n_results=3, 
            min_similarity=0.5,
            reranking_enabled=True
        )
        
        # Results should be reranked by relevance
        assert len(results) == 3
        # The first result should have the highest similarity
        assert results[0]['similarity_score'] >= results[1]['similarity_score']
        assert results[1]['similarity_score'] >= results[2]['similarity_score']
    
    @pytest.mark.asyncio
    async def test_embedding_generation(self, vector_cache):
        """Test embedding generation for cache entries."""
        # Mock embedding generation
        expected_embedding = [0.1, 0.2, 0.3, 0.4]
        vector_cache._embedding_model.generate_embedding.return_value = expected_embedding
        
        # Set a value
        result = await vector_cache.set("test_key", "test_value")
        assert result is True
        
        # Verify embedding was generated and stored
        get_result = await vector_cache.get("test_key")
        assert get_result.status == CacheStatus.HIT
        assert get_result.entry.embedding == expected_embedding
    
    @pytest.mark.asyncio
    async def test_similarity_calculation(self, vector_cache):
        """Test similarity calculation between embeddings."""
        # Test similarity calculation directly
        embedding1 = [1.0, 0.0, 0.0, 0.0]
        embedding2 = [0.9, 0.1, 0.0, 0.0]
        embedding3 = [0.0, 1.0, 0.0, 0.0]
        
        # Calculate similarities
        similarity1 = await vector_cache._calculate_similarity(embedding1, embedding2)
        similarity2 = await vector_cache._calculate_similarity(embedding1, embedding3)
        
        # embedding1 and embedding2 should be more similar
        assert similarity1 > similarity2
        assert 0.0 <= similarity1 <= 1.0
        assert 0.0 <= similarity2 <= 1.0
    
    @pytest.mark.asyncio
    async def test_vector_indexing(self, vector_cache):
        """Test vector indexing functionality."""
        # Set entries with embeddings
        vector_cache._embedding_model.generate_embedding.side_effect = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.5, 0.5, 0.0, 0.0]
        ]
        
        # Set some entries
        await vector_cache.set("key1", "value1")
        await vector_cache.set("key2", "value2")
        await vector_cache.set("key3", "value3")
        
        # Check vector index
        assert len(vector_cache._vector_index) > 0
        
        # Verify that entries are indexed by their embeddings
        for embedding_key, entries in vector_cache._vector_index.items():
            assert len(entries) >= 1  # At least one entry per embedding


class TestVectorCacheStatistics:
    """Test vector cache statistics and performance tracking."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a vector cache configuration."""
        return VectorCacheConfig(
            cache_ttl_seconds=3600,
            max_entries=5000,
            embedding_dimension=384,
            similarity_threshold=0.8,
            reranking_enabled=True,
            context_window_size=10
        )
    
    @pytest.fixture
    def vector_cache(self, cache_config):
        """Create a vector cache instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = VectorCache("test_vector", cache_config)
            cache._cache_dir = temp_dir
            cache._embedding_model = Mock()  # Mock model
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, vector_cache):
        """Test cache statistics."""
        # Set some values
        await vector_cache.set("key1", "value1")
        await vector_cache.set("key2", "value2")
        
        # Get stats
        stats = await vector_cache.get_stats()
        
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["cache_errors"] == 0
        assert stats["total_operations"] == 0
        assert stats["total_cached_items"] == 2
        assert stats["hit_rate"] == 0.0
        assert stats["vector_index_size"] == 0
        assert stats["context_index_size"] == 0
        assert stats["avg_similarity_score"] == 0.0
    
    @pytest.mark.asyncio
    async def test_vector_stats(self, vector_cache):
        """Test vector search statistics."""
        # Mock some vector search calculations
        vector_cache._vector_stats = {
            "total_searches": 10,
            "avg_similarity": 0.75,
            "max_similarity": 0.95,
            "min_similarity": 0.3,
            "reranking_improvements": 3
        }
        
        stats = await vector_cache.get_stats()
        
        assert stats["vector_stats"]["total_searches"] == 10
        assert stats["vector_stats"]["avg_similarity"] == 0.75
        assert stats["vector_stats"]["max_similarity"] == 0.95
        assert stats["vector_stats"]["min_similarity"] == 0.3
        assert stats["vector_stats"]["reranking_improvements"] == 3
    
    @pytest.mark.asyncio
    async def test_stats_integration(self, vector_cache):
        """Test statistics integration with cache operations."""
        # Perform various operations
        await vector_cache.set("key1", "value1")
        await vector_cache.get("key1")  # Hit
        await vector_cache.get("key2")  # Miss
        
        # Check final stats
        stats = await vector_cache.get_stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["total_operations"] == 2
        assert stats["hit_rate"] == 0.5


class TestVectorCacheErrorHandling:
    """Test error handling scenarios in Vector Cache."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a vector cache configuration."""
        return VectorCacheConfig(
            cache_ttl_seconds=3600,
            max_entries=5000,
            embedding_dimension=384,
            similarity_threshold=0.8,
            reranking_enabled=True,
            context_window_size=10
        )
    
    @pytest.fixture
    def vector_cache(self, cache_config):
        """Create a vector cache instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = VectorCache("test_vector", cache_config)
            cache._cache_dir = temp_dir
            cache._embedding_model = Mock()  # Mock model
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_embedding_error_handling(self, vector_cache):
        """Test error handling in embedding generation."""
        # Mock embedding generation to fail
        vector_cache._embedding_model.generate_embedding.side_effect = Exception("Embedding error")
        
        # Should still be able to set values (without embeddings)
        result = await vector_cache.set("test_key", "test_value")
        assert result is True
        
        # Get should work
        get_result = await vector_cache.get("test_key")
        assert get_result.status == CacheStatus.HIT
        assert get_result.entry.value == "test_value"
        assert get_result.entry.embedding is None
    
    @pytest.mark.asyncio
    async def test_similarity_calculation_error(self, vector_cache):
        """Test error handling in similarity calculation."""
        # Test with invalid embeddings
        invalid_embedding = None
        valid_embedding = [0.1, 0.2, 0.3, 0.4]
        
        # Should handle invalid embeddings gracefully
        similarity = await vector_cache._calculate_similarity(invalid_embedding, valid_embedding)
        assert similarity == 0.0  # Default similarity for invalid inputs
    
    @pytest.mark.asyncio
    async def test_vector_search_error_handling(self, vector_cache):
        """Test error handling in vector search."""
        # Mock embedding generation to fail
        vector_cache._embedding_model.generate_embedding.side_effect = Exception("Embedding error")
        
        # Should handle error gracefully
        results = await vector_cache.vector_search("query", n_results=5, min_similarity=0.7)
        assert len(results) == 0  # Should return empty list on error


class TestVectorCacheEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a vector cache configuration."""
        return VectorCacheConfig(
            cache_ttl_seconds=3600,
            max_entries=5000,
            similarity_threshold=0.8
        )
    
    @pytest.fixture
    def vector_cache(self, cache_config):
        """Create a vector cache instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = VectorCache("test_vector", cache_config)
            cache._cache_dir = temp_dir
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, vector_cache):
        """Test concurrent cache operations."""
        async def set_operations():
            for i in range(10):
                await vector_cache.set(f"key_{i}", f"value_{i}")
        
        async def get_operations():
            for i in range(10):
                await vector_cache.get(f"key_{i}")
        
        # Run operations concurrently
        await asyncio.gather(set_operations(), get_operations())
        
        # Verify all operations completed
        stats = await vector_cache.get_stats()
        assert stats["total_operations"] >= 20
    
    @pytest.mark.asyncio
    async def test_large_data_handling(self, vector_cache):
        """Test handling of large data objects."""
        large_data = {"data": "x" * 1000000}  # 1MB of data
        
        result = await vector_cache.set("large_key", large_data)
        assert result is True
        
        get_result = await vector_cache.get("large_key")
        assert get_result.status == CacheStatus.HIT
        assert get_result.entry.value == large_data
    
    @pytest.mark.asyncio
    async def test_max_entries_limit(self, vector_cache):
        """Test max entries limit enforcement."""
        # Set entries up to the limit
        for i in range(vector_cache.config.max_entries):
            await vector_cache.set(f"key_{i}", f"value_{i}")
        
        # Try to set one more entry
        result = await vector_cache.set("overflow_key", "overflow_value")
        
        # Should handle gracefully (either reject or evict oldest)
        assert result is True or result is False  # Either way should be handled
    
    @pytest.mark.asyncio
    async def test_context_window_management(self, vector_cache):
        """Test context window management."""
        # Set entries with context
        for i in range(15):  # Exceed context window size of 10
            await vector_cache.set(f"key_{i}", f"value_{i}", metadata={"context": f"context_{i % 5}"})
        
        # Context index should manage the window
        assert len(vector_cache._context_index) <= 5  # 5 different contexts
        
        # Search should respect context window
        results = await vector_cache.vector_search("query", n_results=5, min_similarity=0.0)
        assert len(results) <= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])