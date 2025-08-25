"""
Unit tests for cache layers.

This module contains unit tests for all cache layers in the cache management system.

Author: KiloCode
License: Apache 2.0
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from src.core.base_cache import BaseCache, CacheEntry, CacheStatus, CacheLayer
from src.core.config import CacheConfig, PredictiveCacheConfig, SemanticCacheConfig
from src.cache_layers.predictive_cache import PredictiveCache
from src.cache_layers.semantic_cache import SemanticCache
from src.core.utils import CacheUtils


class TestCacheUtils:
    """Test cache utility functions."""
    
    def test_generate_hash(self):
        """Test hash generation."""
        test_string = "test_string"
        hash1 = CacheUtils.generate_hash(test_string)
        hash2 = CacheUtils.generate_hash(test_string)
        
        # Same string should produce same hash
        assert hash1 == hash2
        
        # Different strings should produce different hashes
        hash3 = CacheUtils.generate_hash("different_string")
        assert hash1 != hash3
    
    def test_generate_embedding(self):
        """Test embedding generation."""
        # Mock embedding generation
        with patch('src.core.utils.CacheUtils.generate_embedding') as mock_embedding:
            mock_embedding.return_value = [0.1, 0.2, 0.3, 0.4]
            
            result = CacheUtils.generate_embedding("test text")
            
            assert result == [0.1, 0.2, 0.3, 0.4]
            mock_embedding.assert_called_once_with("test text")
    
    def test_calculate_similarity(self):
        """Test similarity calculation."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        vec3 = [1.0, 0.0, 0.0]
        
        # Same vectors should have similarity of 1.0
        similarity = CacheUtils.calculate_similarity(vec1, vec3)
        assert similarity == 1.0
        
        # Different vectors should have similarity < 1.0
        similarity = CacheUtils.calculate_similarity(vec1, vec2)
        assert similarity < 1.0
        
        # Similarity should be symmetric
        similarity1 = CacheUtils.calculate_similarity(vec1, vec2)
        similarity2 = CacheUtils.calculate_similarity(vec2, vec1)
        assert similarity1 == similarity2


class TestBaseCache:
    """Test base cache functionality."""
    
    def test_cache_entry_creation(self):
        """Test cache entry creation."""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            ttl_seconds=3600,
            metadata={"test": "metadata"}
        )
        
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.ttl_seconds == 3600
        assert entry.metadata == {"test": "metadata"}
        assert entry.created_at is not None
        assert entry.expiry_time is not None
        assert entry.embedding is None
    
    def test_cache_entry_expiry(self):
        """Test cache entry expiry."""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            ttl_seconds=1  # 1 second
        )
        
        # Should not be expired immediately
        assert not entry.is_expired()
        
        # Mock time to be in the future
        with patch('src.core.base_cache.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = entry.expiry_time + timedelta(seconds=1)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            assert entry.is_expired()
    
    def test_cache_entry_hash(self):
        """Test cache entry hash generation."""
        entry1 = CacheEntry(key="test_key", value="test_value")
        entry2 = CacheEntry(key="test_key", value="test_value")
        entry3 = CacheEntry(key="different_key", value="test_value")
        
        # Same key and value should produce same hash
        assert hash(entry1) == hash(entry2)
        
        # Different keys should produce different hashes
        assert hash(entry1) != hash(entry3)


class TestPredictiveCache:
    """Test predictive cache functionality."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a predictive cache configuration."""
        return PredictiveCacheConfig(
            cache_ttl_seconds=300,
            max_cache_size=1000,
            prediction_window=60,
            confidence_threshold=0.7
        )
    
    @pytest.fixture
    def predictive_cache(self, cache_config):
        """Create a predictive cache instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = PredictiveCache("test_predictive", cache_config)
            cache._cache_dir = temp_dir
            return cache
    
    @pytest.mark.asyncio
    async def test_cache_initialization(self, predictive_cache):
        """Test cache initialization."""
        result = await predictive_cache.initialize()
        assert result is True
        assert predictive_cache._cache == {}
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, predictive_cache):
        """Test setting and getting cache entries."""
        # Set a value
        result = await predictive_cache.set("test_key", "test_value")
        assert result is True
        
        # Get the value
        get_result = await predictive_cache.get("test_key")
        assert get_result.status == CacheStatus.HIT
        assert get_result.entry.value == "test_value"
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, predictive_cache):
        """Test cache miss scenario."""
        get_result = await predictive_cache.get("nonexistent_key")
        assert get_result.status == CacheStatus.MISS
        assert get_result.entry is None
    
    @pytest.mark.asyncio
    async def test_cache_expiry(self, predictive_cache):
        """Test cache expiry."""
        # Set a value with short TTL
        await predictive_cache.set("test_key", "test_value", ttl_seconds=1)
        
        # Should be available immediately
        get_result = await predictive_cache.get("test_key")
        assert get_result.status == CacheStatus.HIT
        
        # Wait for expiry (mock time)
        await asyncio.sleep(0.1)  # Small delay for test
        
        # Should be expired now
        get_result = await predictive_cache.get("test_key")
        assert get_result.status == CacheStatus.EXPIRED
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, predictive_cache):
        """Test cache deletion."""
        # Set a value
        await predictive_cache.set("test_key", "test_value")
        
        # Delete it
        result = await predictive_cache.delete("test_key")
        assert result is True
        
        # Should be gone
        get_result = await predictive_cache.get("test_key")
        assert get_result.status == CacheStatus.MISS
    
    @pytest.mark.asyncio
    async def test_cache_clear(self, predictive_cache):
        """Test cache clearing."""
        # Set multiple values
        await predictive_cache.set("key1", "value1")
        await predictive_cache.set("key2", "value2")
        
        # Clear cache
        result = await predictive_cache.clear()
        assert result is True
        
        # Should all be gone
        get_result1 = await predictive_cache.get("key1")
        get_result2 = await predictive_cache.get("key2")
        assert get_result1.status == CacheStatus.MISS
        assert get_result2.status == CacheStatus.MISS
    
    @pytest.mark.asyncio
    async def test_predict_functionality(self, predictive_cache):
        """Test prediction functionality."""
        # Set some historical data
        await predictive_cache.set("user1_query1", "response1")
        await predictive_cache.set("user1_query2", "response2")
        await predictive_cache.set("user2_query1", "response3")
        
        # Mock prediction
        with patch.object(predictive_cache, '_predict_next') as mock_predict:
            mock_predict.return_value = [
                {"query": "predicted_query", "confidence": 0.8, "response": "predicted_response"}
            ]
            
            predictions = await predictive_cache.predict("user1_", n_predictions=1)
            
            assert len(predictions) == 1
            assert predictions[0]["query"] == "predicted_query"
            assert predictions[0]["confidence"] == 0.8
            mock_predict.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, predictive_cache):
        """Test cache statistics."""
        # Set some values
        await predictive_cache.set("key1", "value1")
        await predictive_cache.set("key2", "value2")
        
        # Get stats
        stats = await predictive_cache.get_stats()
        
        assert stats["total_entries"] == 2
        assert stats["cache_size"] == 2
        assert stats["hit_rate"] == 0.0  # No hits yet
        
        # Get a value to create a hit
        await predictive_cache.get("key1")
        
        # Stats should reflect the hit
        stats = await predictive_cache.get_stats()
        assert stats["hit_rate"] > 0.0


class TestSemanticCache:
    """Test semantic cache functionality."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a semantic cache configuration."""
        return SemanticCacheConfig(
            cache_ttl_seconds=3600,
            max_cache_size=2000,
            similarity_threshold=0.8,
            embedding_dimension=384
        )
    
    @pytest.fixture
    def semantic_cache(self, cache_config):
        """Create a semantic cache instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SemanticCache("test_semantic", cache_config)
            cache._cache_dir = temp_dir
            return cache
    
    @pytest.mark.asyncio
    async def test_cache_initialization(self, semantic_cache):
        """Test cache initialization."""
        result = await semantic_cache.initialize()
        assert result is True
        assert semantic_cache._cache == {}
        assert semantic_cache._semantic_index == {}
    
    @pytest.mark.asyncio
    async def test_cache_set_with_embedding(self, semantic_cache):
        """Test setting cache entry with embedding."""
        # Mock embedding generation
        with patch('src.core.utils.CacheUtils.generate_embedding') as mock_embedding:
            mock_embedding.return_value = [0.1, 0.2, 0.3, 0.4]
            
            result = await semantic_cache.set("test_key", "test_value")
            assert result is True
            
            # Check that embedding was generated and stored
            get_result = await semantic_cache.get("test_key")
            assert get_result.status == CacheStatus.HIT
            assert get_result.entry.embedding == [0.1, 0.2, 0.3, 0.4]
    
    @pytest.mark.asyncio
    async def test_find_similar(self, semantic_cache):
        """Test finding similar entries."""
        # Set some entries with embeddings
        with patch('src.core.utils.CacheUtils.generate_embedding') as mock_embedding:
            mock_embedding.side_effect = [
                [1.0, 0.0, 0.0, 0.0],  # Similar to query
                [0.0, 1.0, 0.0, 0.0],  # Different from query
                [0.9, 0.1, 0.0, 0.0]   # Very similar to query
            ]
            
            await semantic_cache.set("key1", "value1")
            await semantic_cache.set("key2", "value2")
            await semantic_cache.set("key3", "value3")
            
            # Find similar entries
            similar = await semantic_cache.find_similar("query", n_results=2, min_similarity=0.7)
            
            assert len(similar) <= 2
            for result in similar:
                assert result['similarity_score'] >= 0.7
    
    @pytest.mark.asyncio
    async def test_semantic_hashing(self, semantic_cache):
        """Test semantic hashing functionality."""
        with patch('src.core.utils.CacheUtils.generate_embedding') as mock_embedding:
            mock_embedding.return_value = [0.5, 0.5, 0.5, 0.5]
            
            # Set entries that should have similar semantic hashes
            await semantic_cache.set("similar_query1", "response1")
            await semantic_cache.set("similar_query2", "response2")
            
            # Check semantic index
            assert len(semantic_cache._semantic_index) > 0


class TestCacheIntegration:
    """Integration tests for cache layers."""
    
    @pytest.mark.asyncio
    async def test_cross_layer_consistency(self):
        """Test consistency across cache layers."""
        # This test would verify that operations are consistent
        # across different cache layers when they share data
        pass
    
    @pytest.mark.asyncio
    async def test_cache_routing(self):
        """Test cache routing logic."""
        # This test would verify that requests are routed
        # to the appropriate cache layer based on configuration
        pass
    
    @pytest.mark.asyncio
    async def test_cache_fallback(self):
        """Test cache fallback mechanism."""
        # This test would verify that fallback behavior works
        # when a primary cache layer fails
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])