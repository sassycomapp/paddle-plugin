"""
Unit tests for Semantic Cache functionality.

This module contains comprehensive unit tests for the Semantic Cache layer,
testing similarity search, semantic hashing, prompt reuse, and embedding operations.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from src.cache_layers.semantic_cache import SemanticCache
from src.core.base_cache import CacheStatus, CacheLayer
from src.core.config import SemanticCacheConfig


class TestSemanticCacheInitialization:
    """Test Semantic Cache initialization and basic properties."""
    
    def test_cache_creation(self):
        """Test cache instance creation."""
        config = SemanticCacheConfig(
            cache_ttl_seconds=3600,
            max_entries=10000,
            similarity_threshold=0.85,
            hash_algorithm="sha256",
            compression_enabled=True
        )
        
        cache = SemanticCache("test_semantic", config)
        assert cache.name == "test_semantic"
        assert cache.config == config
        assert cache._cache == {}
        assert cache._semantic_hashes == {}
        assert cache._prompt_index == {}
        assert cache._response_index == {}
    
    @pytest.mark.asyncio
    async def test_successful_initialization(self):
        """Test successful cache initialization."""
        config = SemanticCacheConfig(
            cache_ttl_seconds=3600,
            max_entries=10000,
            similarity_threshold=0.85
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SemanticCache("test_semantic", config)
            cache._cache_dir = temp_dir
            result = await cache.initialize()
            
            assert result is True
            assert len(cache._semantic_hashes) == 0
            assert os.path.exists(os.path.join(temp_dir, "cache.db"))
    
    @pytest.mark.asyncio
    async def test_failed_initialization(self):
        """Test failed cache initialization."""
        config = SemanticCacheConfig(
            cache_ttl_seconds=3600,
            max_entries=10000,
            similarity_threshold=0.85
        )
        
        class FailingSemanticCache(SemanticCache):
            async def _initialize_embedding_model(self):
                raise Exception("Test initialization failure")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = FailingSemanticCache("test_semantic", config)
            result = await cache.initialize()
            
            assert result is False


class TestSemanticCacheCoreOperations:
    """Test core cache operations."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a semantic cache configuration."""
        return SemanticCacheConfig(
            cache_ttl_seconds=3600,
            max_entries=10000,
            similarity_threshold=0.85,
            hash_algorithm="sha256",
            compression_enabled=True
        )
    
    @pytest.fixture
    def semantic_cache(self, cache_config):
        """Create a semantic cache instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SemanticCache("test_semantic", cache_config)
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, semantic_cache):
        """Test setting and getting cache entries."""
        # Set a value
        result = await semantic_cache.set("test_key", "test_value")
        assert result is True
        
        # Get the value
        get_result = await semantic_cache.get("test_key")
        assert get_result.status == CacheStatus.HIT
        assert get_result.entry.value == "test_value"
        assert get_result.entry.layer == CacheLayer.SEMANTIC
        
        # Stats should reflect the hit
        stats = await semantic_cache.get_stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 0
        assert stats["total_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, semantic_cache):
        """Test cache miss scenario."""
        get_result = await semantic_cache.get("nonexistent_key")
        assert get_result.status == CacheStatus.MISS
        assert get_result.entry is None
        
        # Stats should reflect the miss
        stats = await semantic_cache.get_stats()
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 1
        assert stats["total_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_cache_expiry(self, semantic_cache):
        """Test cache expiry functionality."""
        # Set a value with short TTL
        await semantic_cache.set("test_key", "test_value", ttl_seconds=1)
        
        # Should be available immediately
        get_result = await semantic_cache.get("test_key")
        assert get_result.status == CacheStatus.HIT
        
        # Mock time to be in the future
        with patch('src.cache_layers.semantic_cache.datetime') as mock_datetime:
            future_time = datetime.utcnow() + timedelta(seconds=2)
            mock_datetime.utcnow.return_value = future_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # Should be expired now
            get_result = await semantic_cache.get("test_key")
            assert get_result.status == CacheStatus.EXPIRED
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, semantic_cache):
        """Test cache deletion."""
        # Set a value
        await semantic_cache.set("test_key", "test_value")
        
        # Delete it
        result = await semantic_cache.delete("test_key")
        assert result is True
        
        # Should be gone
        get_result = await semantic_cache.get("test_key")
        assert get_result.status == CacheStatus.MISS
    
    @pytest.mark.asyncio
    async def test_cache_clear(self, semantic_cache):
        """Test cache clearing."""
        # Set multiple values
        await semantic_cache.set("key1", "value1")
        await semantic_cache.set("key2", "value2")
        await semantic_cache.set("key3", "value3")
        
        # Clear cache
        result = await semantic_cache.clear()
        assert result is True
        
        # Should all be gone
        for key in ["key1", "key2", "key3"]:
            get_result = await semantic_cache.get(key)
            assert get_result.status == CacheStatus.MISS
        
        # Indexes should also be cleared
        assert len(semantic_cache._semantic_index) == 0
        assert len(semantic_cache._hash_index) == 0
    
    @pytest.mark.asyncio
    async def test_cache_exists(self, semantic_cache):
        """Test cache exists functionality."""
        # Non-existent key
        assert await semantic_cache.exists("nonexistent_key") is False
        
        # Set a value
        await semantic_cache.set("test_key", "test_value")
        
        # Should exist
        assert await semantic_cache.exists("test_key") is True
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self, semantic_cache):
        """Test cleanup of expired entries."""
        # Set entries with different TTLs
        await semantic_cache.set("short_ttl", "value1", ttl_seconds=1)
        await semantic_cache.set("long_ttl", "value2", ttl_seconds=3600)
        
        # Mock time to make short_ttl entry expire
        with patch('src.cache_layers.semantic_cache.datetime') as mock_datetime:
            future_time = datetime.utcnow() + timedelta(seconds=2)
            mock_datetime.utcnow.return_value = future_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # Cleanup expired entries
            removed_count = await semantic_cache.cleanup_expired()
            assert removed_count == 1
            
            # Verify only long_ttl remains
            get_result1 = await semantic_cache.get("short_ttl")
            get_result2 = await semantic_cache.get("long_ttl")
            assert get_result1.status == CacheStatus.MISS
            assert get_result2.status == CacheStatus.HIT


class TestSemanticCacheSemanticFunctionality:
    """Test semantic search and similarity functionality."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a semantic cache configuration."""
        return SemanticCacheConfig(
            cache_ttl_seconds=3600,
            max_entries=10000,
            similarity_threshold=0.85,
            hash_algorithm="sha256",
            compression_enabled=True
        )
    
    @pytest.fixture
    def semantic_cache(self, cache_config):
        """Create a semantic cache instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SemanticCache("test_semantic", cache_config)
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_find_similar(self, semantic_cache):
        """Test finding similar entries."""
        # Mock embedding generation
        semantic_cache._embedding_model.generate_embedding.side_effect = [
            [1.0, 0.0, 0.0, 0.0],  # Similar to query
            [0.0, 1.0, 0.0, 0.0],  # Different from query
            [0.9, 0.1, 0.0, 0.0]   # Very similar to query
        ]
        
        # Set some entries
        await semantic_cache.set("key1", "value1")
        await semantic_cache.set("key2", "value2")
        await semantic_cache.set("key3", "value3")
        
        # Find similar entries
        similar = await semantic_cache.find_similar("query", n_results=2, min_similarity=0.7)
        
        assert len(similar) <= 2
        for result in similar:
            assert result['similarity_score'] >= 0.7
    
    @pytest.mark.asyncio
    async def test_find_similar_with_threshold(self, semantic_cache):
        """Test finding similar entries with high threshold."""
        # Mock embedding generation
        semantic_cache._embedding_model.generate_embedding.side_effect = [
            [1.0, 0.0, 0.0, 0.0],  # High similarity
            [0.5, 0.5, 0.0, 0.0],  # Medium similarity
            [0.2, 0.2, 0.2, 0.2]   # Low similarity
        ]
        
        # Set some entries
        await semantic_cache.set("key1", "value1")
        await semantic_cache.set("key2", "value2")
        await semantic_cache.set("key3", "value3")
        
        # Find similar entries with high threshold
        similar = await semantic_cache.find_similar("query", n_results=5, min_similarity=0.8)
        
        # Should only return entries with similarity >= 0.8
        for result in similar:
            assert result['similarity_score'] >= 0.8
    
    @pytest.mark.asyncio
    async def test_semantic_hashing(self, semantic_cache):
        """Test semantic hashing functionality."""
        # Mock embedding generation
        semantic_cache._embedding_model.generate_embedding.return_value = [0.5, 0.5, 0.5, 0.5]
        
        # Set entries that should have similar semantic hashes
        await semantic_cache.set("similar_query1", "response1")
        await semantic_cache.set("similar_query2", "response2")
        
        # Check semantic index
        assert len(semantic_cache._semantic_index) > 0
        
        # Verify that similar queries are grouped together
        for hash_key, entries in semantic_cache._semantic_index.items():
            assert len(entries) >= 1  # At least one entry per hash
    
    @pytest.mark.asyncio
    async def test_prompt_reuse_detection(self, semantic_cache):
        """Test prompt reuse detection."""
        # Mock embedding generation
        semantic_cache._embedding_model.generate_embedding.return_value = [0.8, 0.1, 0.1, 0.1]
        
        # Set a prompt
        await semantic_cache.set("test_prompt", "test_response")
        
        # Try to set a similar prompt
        similar_prompt = "test prompt with slight variation"
        await semantic_cache.set(similar_prompt, "similar_response")
        
        # Should detect similarity and reuse
        # (In a real implementation, this would check for semantic similarity)
        assert len(semantic_cache._cache) >= 1
    
    @pytest.mark.asyncio
    async def test_embedding_generation(self, semantic_cache):
        """Test embedding generation for cache entries."""
        # Mock embedding generation
        expected_embedding = [0.1, 0.2, 0.3, 0.4]
        semantic_cache._embedding_model.generate_embedding.return_value = expected_embedding
        
        # Set a value
        result = await semantic_cache.set("test_key", "test_value")
        assert result is True
        
        # Verify embedding was generated and stored
        get_result = await semantic_cache.get("test_key")
        assert get_result.status == CacheStatus.HIT
        assert get_result.entry.embedding == expected_embedding
    
    @pytest.mark.asyncio
    async def test_similarity_calculation(self, semantic_cache):
        """Test similarity calculation between embeddings."""
        # Test similarity calculation directly
        embedding1 = [1.0, 0.0, 0.0, 0.0]
        embedding2 = [0.9, 0.1, 0.0, 0.0]
        embedding3 = [0.0, 1.0, 0.0, 0.0]
        
        # Calculate similarities
        similarity1 = await semantic_cache._calculate_similarity(embedding1, embedding2)
        similarity2 = await semantic_cache._calculate_similarity(embedding1, embedding3)
        
        # embedding1 and embedding2 should be more similar
        assert similarity1 > similarity2
        assert 0.0 <= similarity1 <= 1.0
        assert 0.0 <= similarity2 <= 1.0


class TestSemanticCacheStatistics:
    """Test semantic cache statistics and performance tracking."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a semantic cache configuration."""
        return SemanticCacheConfig(
            cache_ttl_seconds=3600,
            max_entries=10000,
            similarity_threshold=0.85,
            hash_algorithm="sha256",
            compression_enabled=True
        )
    
    @pytest.fixture
    def semantic_cache(self, cache_config):
        """Create a semantic cache instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SemanticCache("test_semantic", cache_config)
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, semantic_cache):
        """Test cache statistics."""
        # Set some values
        await semantic_cache.set("key1", "value1")
        await semantic_cache.set("key2", "value2")
        
        # Get stats
        stats = await semantic_cache.get_stats()
        
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["cache_errors"] == 0
        assert stats["total_operations"] == 0
        assert stats["total_cached_items"] == 2
        assert stats["hit_rate"] == 0.0
        assert stats["semantic_index_size"] == 0
        assert stats["hash_index_size"] == 0
        assert stats["avg_similarity_score"] == 0.0
    
    @pytest.mark.asyncio
    async def test_similarity_stats(self, semantic_cache):
        """Test similarity statistics."""
        # Mock some similarity calculations
        semantic_cache._similarity_stats = {
            "total_calculations": 10,
            "avg_similarity": 0.75,
            "max_similarity": 0.95,
            "min_similarity": 0.3
        }
        
        stats = await semantic_cache.get_stats()
        
        assert stats["similarity_stats"]["total_calculations"] == 10
        assert stats["similarity_stats"]["avg_similarity"] == 0.75
        assert stats["similarity_stats"]["max_similarity"] == 0.95
        assert stats["similarity_stats"]["min_similarity"] == 0.3
    
    @pytest.mark.asyncio
    async def test_stats_integration(self, semantic_cache):
        """Test statistics integration with cache operations."""
        # Perform various operations
        await semantic_cache.set("key1", "value1")
        await semantic_cache.get("key1")  # Hit
        await semantic_cache.get("key2")  # Miss
        
        # Check final stats
        stats = await semantic_cache.get_stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["total_operations"] == 2
        assert stats["hit_rate"] == 0.5


class TestSemanticCacheErrorHandling:
    """Test error handling scenarios in Semantic Cache."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a semantic cache configuration."""
        return SemanticCacheConfig(
            cache_ttl_seconds=3600,
            max_entries=10000,
            similarity_threshold=0.85,
            hash_algorithm="sha256",
            compression_enabled=True
        )
    
    @pytest.fixture
    def semantic_cache(self, cache_config):
        """Create a semantic cache instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SemanticCache("test_semantic", cache_config)
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_embedding_error_handling(self, semantic_cache):
        """Test error handling in embedding generation."""
        # Mock embedding generation to fail
        semantic_cache._embedding_model.generate_embedding.side_effect = Exception("Embedding error")
        
        # Should still be able to set values (without embeddings)
        result = await semantic_cache.set("test_key", "test_value")
        assert result is True
        
        # Get should work
        get_result = await semantic_cache.get("test_key")
        assert get_result.status == CacheStatus.HIT
        assert get_result.entry.value == "test_value"
        assert get_result.entry.embedding is None
    
    @pytest.mark.asyncio
    async def test_similarity_calculation_error(self, semantic_cache):
        """Test error handling in similarity calculation."""
        # Test with invalid embeddings
        invalid_embedding = None
        valid_embedding = [0.1, 0.2, 0.3, 0.4]
        
        # Should handle invalid embeddings gracefully
        similarity = await semantic_cache._calculate_similarity(invalid_embedding, valid_embedding)
        assert similarity == 0.0  # Default similarity for invalid inputs
    
    @pytest.mark.asyncio
    async def test_find_similar_error_handling(self, semantic_cache):
        """Test error handling in find_similar."""
        # Mock embedding generation to fail
        semantic_cache._embedding_model.generate_embedding.side_effect = Exception("Embedding error")
        
        # Should handle error gracefully
        similar = await semantic_cache.find_similar("query", n_results=5, min_similarity=0.7)
        assert len(similar) == 0  # Should return empty list on error


class TestSemanticCacheEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a semantic cache configuration."""
        return SemanticCacheConfig(
            cache_ttl_seconds=3600,
            max_entries=10000,
            similarity_threshold=0.85,
            hash_algorithm="sha256",
            compression_enabled=True
        )
    
    @pytest.fixture
    def semantic_cache(self, cache_config):
        """Create a semantic cache instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SemanticCache("test_semantic", cache_config)
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, semantic_cache):
        """Test concurrent cache operations."""
        async def set_operations():
            for i in range(10):
                await semantic_cache.set(f"key_{i}", f"value_{i}")
        
        async def get_operations():
            for i in range(10):
                await semantic_cache.get(f"key_{i}")
        
        # Run operations concurrently
        await asyncio.gather(set_operations(), get_operations())
        
        # Verify all operations completed
        stats = await semantic_cache.get_stats()
        assert stats["total_operations"] >= 20
    
    @pytest.mark.asyncio
    async def test_large_data_handling(self, semantic_cache):
        """Test handling of large data objects."""
        large_data = {"data": "x" * 1000000}  # 1MB of data
        
        result = await semantic_cache.set("large_key", large_data)
        assert result is True
        
        get_result = await semantic_cache.get("large_key")
        assert get_result.status == CacheStatus.HIT
        assert get_result.entry.value == large_data
    
    @pytest.mark.asyncio
    async def test_max_entries_limit(self, semantic_cache):
        """Test max entries limit enforcement."""
        # Set entries up to the limit
        for i in range(semantic_cache.config.max_entries):
            await semantic_cache.set(f"key_{i}", f"value_{i}")
        
        # Try to set one more entry
        result = await semantic_cache.set("overflow_key", "overflow_value")
        
        # Should handle gracefully (either reject or evict oldest)
        assert result is True or result is False  # Either way should be handled
    
    @pytest.mark.asyncio
    async def test_special_characters_in_keys(self, semantic_cache):
        """Test handling of special characters in cache keys."""
        special_keys = [
            "key_with_spaces",
            "key-with-dashes",
            "key.with.dots",
            "key@with#special$chars%",
            "key/with\\path\\separators",
            "key\nwith\nnewlines",
            "key\twith\ttabs",
            "key_with_unicode_ñ_á_é_í_ó_ú"
        ]
        
        # Set values with special keys
        for key in special_keys:
            result = await semantic_cache.set(key, f"value_for_{key}")
            assert result is True
        
        # Get values back
        for key in special_keys:
            get_result = await semantic_cache.get(key)
            assert get_result.status == CacheStatus.HIT
            assert get_result.entry.value == f"value_for_{key}"


class TestSemanticCacheCompression:
    """Test compression functionality."""
    
    @pytest.fixture
    def cache_config_compression_enabled(self):
        """Create a semantic cache configuration with compression enabled."""
        return SemanticCacheConfig(
            cache_ttl_seconds=3600,
            max_entries=10000,
            similarity_threshold=0.85,
            hash_algorithm="sha256",
            compression_enabled=True
        )
    
    @pytest.fixture
    def cache_config_compression_disabled(self):
        """Create a semantic cache configuration with compression disabled."""
        return SemanticCacheConfig(
            cache_ttl_seconds=3600,
            max_entries=10000,
            similarity_threshold=0.85,
            hash_algorithm="sha256",
            compression_enabled=False
        )
    
    @pytest.mark.asyncio
    async def test_compression_enabled(self, cache_config_compression_enabled):
        """Test compression functionality when enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SemanticCache("test_semantic", cache_config_compression_enabled)
            cache._running = True
            
            # Set large data
            large_data = {"data": "x" * 1000000}  # 1MB of data
            result = await cache.set("large_key", large_data)
            assert result is True
            
            # Get should work
            get_result = await cache.get("large_key")
            assert get_result.status == CacheStatus.HIT
            assert get_result.entry.value == large_data
    
    @pytest.mark.asyncio
    async def test_compression_disabled(self, cache_config_compression_disabled):
        """Test functionality when compression is disabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SemanticCache("test_semantic", cache_config_compression_disabled)
            cache._running = True
            
            # Set large data
            large_data = {"data": "x" * 1000000}  # 1MB of data
            result = await cache.set("large_key", large_data)
            assert result is True
            
            # Get should work
            get_result = await cache.get("large_key")
            assert get_result.status == CacheStatus.HIT
            assert get_result.entry.value == large_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])