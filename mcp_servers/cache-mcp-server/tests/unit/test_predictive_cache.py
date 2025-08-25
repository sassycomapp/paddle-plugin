"""
Unit tests for Predictive Cache functionality.

This module contains comprehensive unit tests for the Predictive Cache layer,
testing prediction algorithms, temporal analysis, user behavior modeling,
and zero-token hinting capabilities.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from src.cache_layers.predictive_cache import (
    PredictiveCache, PredictionPattern, PredictionRequest
)
from src.core.base_cache import CacheStatus, CacheLayer
from src.core.config import PredictiveCacheConfig


class TestPredictiveCacheInitialization:
    """Test Predictive Cache initialization and basic properties."""
    
    def test_cache_creation(self):
        """Test cache instance creation."""
        config = PredictiveCacheConfig(
            cache_ttl_seconds=3600,
            confidence_threshold=0.7,
            prediction_window_seconds=300,
            max_predictions=10
        )
        
        cache = PredictiveCache("test_predictive", config)
        assert cache.name == "test_predictive"
        assert cache.config == config
        assert cache._cache == {}
        assert cache._patterns == {}
        assert cache._user_sessions == {}
        assert cache._prediction_model is None
        assert cache._prediction_hits == 0
        assert cache._prediction_misses == 0
        assert cache._prefetch_hits == 0
        assert cache._prefetch_misses == 0
        assert cache._prediction_task is None
        assert cache._cleanup_task is None
        assert cache._running is False
    
    @pytest.mark.asyncio
    async def test_successful_initialization(self):
        """Test successful cache initialization."""
        config = PredictiveCacheConfig(
            cache_ttl_seconds=3600,
            confidence_threshold=0.7,
            prediction_window_seconds=300,
            max_predictions=10
        )
        
        cache = PredictiveCache("test_predictive", config)
        result = await cache.initialize()
        
        assert result is True
        assert cache._prediction_model == "pattern_based"
        assert cache._running is True
        assert cache._prediction_task is not None
        assert cache._cleanup_task is not None
    
    @pytest.mark.asyncio
    async def test_failed_initialization(self):
        """Test failed cache initialization."""
        config = PredictiveCacheConfig(
            cache_ttl_seconds=3600,
            confidence_threshold=0.7,
            prediction_window_seconds=300,
            max_predictions=10
        )
        
        class FailingPredictiveCache(PredictiveCache):
            async def _initialize_prediction_model(self):
                raise Exception("Test initialization failure")
        
        cache = FailingPredictiveCache("test_predictive", config)
        result = await cache.initialize()
        
        assert result is False
        assert cache._running is False
    
    @pytest.mark.asyncio
    async def test_cache_shutdown(self):
        """Test cache shutdown and cleanup."""
        config = PredictiveCacheConfig(
            cache_ttl_seconds=3600,
            confidence_threshold=0.7,
            prediction_window_seconds=300,
            max_predictions=10
        )
        
        cache = PredictiveCache("test_predictive", config)
        await cache.initialize()
        
        # Shutdown cache
        await cache.close()
        
        # Should be stopped
        assert cache._running is False


class TestPredictiveCacheCoreOperations:
    """Test core cache operations."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a predictive cache configuration."""
        return PredictiveCacheConfig(
            cache_ttl_seconds=3600,
            confidence_threshold=0.7,
            prediction_window_seconds=300,
            max_predictions=10
        )
    
    @pytest.fixture
    def predictive_cache(self, cache_config):
        """Create a predictive cache instance."""
        cache = PredictiveCache("test_predictive", cache_config)
        cache._prediction_model = "pattern_based"  # Mock model
        cache._running = True
        return cache
    
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
        assert get_result.entry.layer == CacheLayer.PREDICTIVE
        
        # Stats should reflect the hit
        stats = await predictive_cache.get_stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 0
        assert stats["total_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, predictive_cache):
        """Test cache miss scenario."""
        get_result = await predictive_cache.get("nonexistent_key")
        assert get_result.status == CacheStatus.MISS
        assert get_result.entry is None
        
        # Stats should reflect the miss
        stats = await predictive_cache.get_stats()
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 1
        assert stats["total_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_cache_expiry(self, predictive_cache):
        """Test cache expiry functionality."""
        # Set a value with short TTL
        await predictive_cache.set("test_key", "test_value", ttl_seconds=1)
        
        # Should be available immediately
        get_result = await predictive_cache.get("test_key")
        assert get_result.status == CacheStatus.HIT
        
        # Mock time to be in the future
        with patch('src.cache_layers.predictive_cache.datetime') as mock_datetime:
            future_time = datetime.utcnow() + timedelta(seconds=2)
            mock_datetime.utcnow.return_value = future_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
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
        await predictive_cache.set("key3", "value3")
        
        # Clear cache
        result = await predictive_cache.clear()
        assert result is True
        
        # Should all be gone
        for key in ["key1", "key2", "key3"]:
            get_result = await predictive_cache.get(key)
            assert get_result.status == CacheStatus.MISS
        
        # Patterns and sessions should also be cleared
        assert len(predictive_cache._patterns) == 0
        assert len(predictive_cache._user_sessions) == 0
    
    @pytest.mark.asyncio
    async def test_cache_exists(self, predictive_cache):
        """Test cache exists functionality."""
        # Non-existent key
        assert await predictive_cache.exists("nonexistent_key") is False
        
        # Set a value
        await predictive_cache.set("test_key", "test_value")
        
        # Should exist
        assert await predictive_cache.exists("test_key") is True
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self, predictive_cache):
        """Test cleanup of expired entries."""
        # Set entries with different TTLs
        await predictive_cache.set("short_ttl", "value1", ttl_seconds=1)
        await predictive_cache.set("long_ttl", "value2", ttl_seconds=3600)
        
        # Mock time to make short_ttl entry expire
        with patch('src.cache_layers.predictive_cache.datetime') as mock_datetime:
            future_time = datetime.utcnow() + timedelta(seconds=2)
            mock_datetime.utcnow.return_value = future_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # Cleanup expired entries
            removed_count = await predictive_cache.cleanup_expired()
            assert removed_count == 1
            
            # Verify only long_ttl remains
            get_result1 = await predictive_cache.get("short_ttl")
            get_result2 = await predictive_cache.get("long_ttl")
            assert get_result1.status == CacheStatus.MISS
            assert get_result2.status == CacheStatus.HIT


class TestPredictiveCachePredictionFunctionality:
    """Test prediction algorithms and functionality."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a predictive cache configuration."""
        return PredictiveCacheConfig(
            cache_ttl_seconds=3600,
            confidence_threshold=0.7,
            prediction_window_seconds=300,
            max_predictions=10
        )
    
    @pytest.fixture
    def predictive_cache(self, cache_config):
        """Create a predictive cache instance."""
        cache = PredictiveCache("test_predictive", cache_config)
        cache._prediction_model = "pattern_based"  # Mock model
        cache._running = True
        return cache
    
    @pytest.mark.asyncio
    async def test_predict_next_queries(self, predictive_cache):
        """Test next query prediction."""
        # Create a prediction request
        request = PredictionRequest(
            context="user is asking about machine learning",
            user_id="user123",
            timestamp=datetime.utcnow(),
            max_predictions=3
        )
        
        # Mock the prediction generation
        with patch.object(predictive_cache, '_generate_predictions') as mock_generate:
            mock_generate.return_value = [
                {"query": "what is neural networks", "confidence": 0.9},
                {"query": "how does deep learning work", "confidence": 0.8},
                {"query": "explain backpropagation", "confidence": 0.7}
            ]
            
            predictions = await predictive_cache.predict_next_queries(request)
            
            assert len(predictions) == 3
            assert predictions[0] == "what is neural networks"
            assert predictions[1] == "how does deep learning work"
            assert predictions[2] == "explain backpropagation"
    
    @pytest.mark.asyncio
    async def test_predict_next_queries_with_threshold(self, predictive_cache):
        """Test next query prediction with confidence threshold."""
        # Set high threshold
        predictive_cache.config.confidence_threshold = 0.85
        
        request = PredictionRequest(
            context="user is asking about machine learning",
            user_id="user123",
            timestamp=datetime.utcnow(),
            max_predictions=3
        )
        
        # Mock predictions with varying confidence
        with patch.object(predictive_cache, '_generate_predictions') as mock_generate:
            mock_generate.return_value = [
                {"query": "what is neural networks", "confidence": 0.9},
                {"query": "how does deep learning work", "confidence": 0.8},
                {"query": "explain backpropagation", "confidence": 0.7}
            ]
            
            predictions = await predictive_cache.predict_next_queries(request)
            
            # Only predictions above threshold should be returned
            assert len(predictions) == 1
            assert predictions[0] == "what is neural networks"
    
    @pytest.mark.asyncio
    async def test_record_access_pattern(self, predictive_cache):
        """Test recording user access patterns."""
        # Mock user session
        predictive_cache._user_sessions["user123"] = Mock()
        
        # Create a cache entry
        entry = predictive_cache._create_entry(
            key="test_key",
            value="test_value",
            ttl_seconds=3600,
            metadata={"category": "ml", "difficulty": "intermediate"}
        )
        
        # Record access pattern
        await predictive_cache._record_access_pattern("test_key", entry)
        
        # Verify pattern was recorded
        assert len(predictive_cache._patterns) > 0
        
        # Check that user session was updated
        assert "user123" in predictive_cache._user_sessions
    
    @pytest.mark.asyncio
    async def test_trigger_predictions(self, predictive_cache):
        """Test triggering predictions on cache set."""
        # Mock prediction methods
        with patch.object(predictive_cache, '_generate_predictions') as mock_generate, \
             patch.object(predictive_cache, '_prefetch_related_keys') as mock_prefetch:
            
            mock_generate.return_value = []
            mock_prefetch.return_value = []
            
            # Set a value
            result = await predictive_cache.set("test_key", "test_value")
            
            # Verify predictions were triggered
            mock_generate.assert_called_once()
            mock_prefetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_prefetch_related_keys(self, predictive_cache):
        """Test prefetching of related keys."""
        # Mock cache with existing entries
        predictive_cache._cache = {
            "related_key1": Mock(),
            "related_key2": Mock(),
            "unrelated_key": Mock()
        }
        
        # Mock prefetch logic
        with patch.object(predictive_cache, '_should_prefetch') as mock_should:
            mock_should.side_effect = lambda key: key in ["related_key1", "related_key2"]
            
            # Trigger prefetch
            await predictive_cache._prefetch_related_keys("test_key", Mock())
            
            # Verify that related keys would be prefetched
            # (In a real implementation, this would actually prefetch)
            assert mock_should.call_count == 3


class TestPredictiveCacheStatistics:
    """Test predictive cache statistics and performance tracking."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a predictive cache configuration."""
        return PredictiveCacheConfig(
            cache_ttl_seconds=3600,
            confidence_threshold=0.7,
            prediction_window_seconds=300,
            max_predictions=10
        )
    
    @pytest.fixture
    def predictive_cache(self, cache_config):
        """Create a predictive cache instance."""
        cache = PredictiveCache("test_predictive", cache_config)
        cache._prediction_model = "pattern_based"  # Mock model
        cache._running = True
        return cache
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, predictive_cache):
        """Test cache statistics."""
        # Set some values
        await predictive_cache.set("key1", "value1")
        await predictive_cache.set("key2", "value2")
        
        # Get stats
        stats = await predictive_cache.get_stats()
        
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["cache_errors"] == 0
        assert stats["total_operations"] == 0
        assert stats["total_cached_items"] == 2
        assert stats["hit_rate"] == 0.0
        assert stats["prediction_hits"] == 0
        assert stats["prediction_misses"] == 0
        assert stats["prediction_accuracy"] == 0.0
        assert stats["prefetch_hits"] == 0
        assert stats["prefetch_misses"] == 0
        assert stats["prefetch_efficiency"] == 0.0
        assert stats["total_patterns"] == 0
        assert stats["active_sessions"] == 0
    
    @pytest.mark.asyncio
    async def test_prediction_stats(self, predictive_cache):
        """Test prediction statistics."""
        # Simulate some prediction activity
        predictive_cache._prediction_hits = 10
        predictive_cache._prediction_misses = 5
        predictive_cache._prefetch_hits = 8
        predictive_cache._prefetch_misses = 2
        
        stats = await predictive_cache.get_stats()
        
        assert stats["prediction_hits"] == 10
        assert stats["prediction_misses"] == 5
        assert stats["prediction_accuracy"] == 10/15  # 10/(10+5)
        assert stats["prefetch_hits"] == 8
        assert stats["prefetch_misses"] == 2
        assert stats["prefetch_efficiency"] == 8/10  # 8/(8+2)
    
    @pytest.mark.asyncio
    async def test_stats_integration(self, predictive_cache):
        """Test statistics integration with cache operations."""
        # Perform various operations
        await predictive_cache.set("key1", "value1")
        await predictive_cache.get("key1")  # Hit
        await predictive_cache.get("key2")  # Miss
        
        # Check final stats
        stats = await predictive_cache.get_stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["total_operations"] == 2
        assert stats["hit_rate"] == 0.5


class TestPredictiveCacheErrorHandling:
    """Test error handling scenarios in Predictive Cache."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a predictive cache configuration."""
        return PredictiveCacheConfig(
            cache_ttl_seconds=3600,
            confidence_threshold=0.7,
            prediction_window_seconds=300,
            max_predictions=10
        )
    
    @pytest.fixture
    def predictive_cache(self, cache_config):
        """Create a predictive cache instance."""
        cache = PredictiveCache("test_predictive", cache_config)
        cache._prediction_model = "pattern_based"  # Mock model
        cache._running = True
        return cache
    
    @pytest.mark.asyncio
    async def test_get_error_handling(self, predictive_cache):
        """Test error handling in get operation."""
        with patch.object(predictive_cache, 'get', side_effect=Exception("Test error")):
            get_result = await predictive_cache.get("test_key")
            assert get_result.status == CacheStatus.ERROR
            assert get_result.error_message == "Test error"
            
            # Stats should reflect the error
            stats = await predictive_cache.get_stats()
            assert stats["cache_errors"] == 1
            assert stats["total_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_set_error_handling(self, predictive_cache):
        """Test error handling in set operation."""
        with patch.object(predictive_cache, 'set', side_effect=Exception("Test error")):
            result = await predictive_cache.set("test_key", "test_value")
            assert result is False
    
    @pytest.mark.asyncio
    async def test_prediction_error_handling(self, predictive_cache):
        """Test error handling in prediction functionality."""
        request = PredictionRequest(
            context="test context",
            user_id="user123",
            timestamp=datetime.utcnow()
        )
        
        with patch.object(predictive_cache, '_generate_predictions', side_effect=Exception("Prediction error")):
            predictions = await predictive_cache.predict_next_queries(request)
            assert len(predictions) == 0  # Should return empty list on error


class TestPredictiveCacheEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a predictive cache configuration."""
        return PredictiveCacheConfig(
            cache_ttl_seconds=3600,
            confidence_threshold=0.7,
            prediction_window_seconds=300,
            max_predictions=10
        )
    
    @pytest.fixture
    def predictive_cache(self, cache_config):
        """Create a predictive cache instance."""
        cache = PredictiveCache("test_predictive", cache_config)
        cache._prediction_model = "pattern_based"  # Mock model
        cache._running = True
        return cache
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, predictive_cache):
        """Test concurrent cache operations."""
        async def set_operations():
            for i in range(10):
                await predictive_cache.set(f"key_{i}", f"value_{i}")
        
        async def get_operations():
            for i in range(10):
                await predictive_cache.get(f"key_{i}")
        
        # Run operations concurrently
        await asyncio.gather(set_operations(), get_operations())
        
        # Verify all operations completed
        stats = await predictive_cache.get_stats()
        assert stats["total_operations"] >= 20
    
    @pytest.mark.asyncio
    async def test_large_data_handling(self, predictive_cache):
        """Test handling of large data objects."""
        large_data = {"data": "x" * 1000000}  # 1MB of data
        
        result = await predictive_cache.set("large_key", large_data)
        assert result is True
        
        get_result = await predictive_cache.get("large_key")
        assert get_result.status == CacheStatus.HIT
        assert get_result.entry.value == large_data
    
    @pytest.mark.asyncio
    async def test_user_session_management(self, predictive_cache):
        """Test user session management."""
        # Simulate multiple user sessions
        user_ids = ["user1", "user2", "user3"]
        
        for user_id in user_ids:
            # Add some entries to user session
            predictive_cache._user_sessions[user_id] = Mock()
            for i in range(5):
                predictive_cache._user_sessions[user_id].append(f"query_{i}")
        
        # Verify sessions are tracked
        assert len(predictive_cache._user_sessions) == 3
        
        # Test session cleanup (maxlen behavior)
        user_session = predictive_cache._user_sessions["user1"]
        # Simulate deque maxlen behavior
        for i in range(15):  # Exceed maxlen of 10
            user_session.append(f"query_{i}")
        
        # Should only keep last 10 items
        assert len(user_session) <= 10


class TestPredictionPattern:
    """Test PredictionPattern dataclass."""
    
    def test_prediction_pattern_creation(self):
        """Test creating prediction patterns."""
        pattern = PredictionPattern(
            pattern_id="pattern1",
            user_id="user123",
            query_sequence=["query1", "query2"],
            response_sequence=["response1", "response2"],
            timestamp=datetime.utcnow(),
            confidence=0.8,
            access_frequency=5,
            last_used=datetime.utcnow()
        )
        
        assert pattern.pattern_id == "pattern1"
        assert pattern.user_id == "user123"
        assert pattern.query_sequence == ["query1", "query2"]
        assert pattern.response_sequence == ["response1", "response2"]
        assert pattern.confidence == 0.8
        assert pattern.access_frequency == 5
        assert pattern.last_used is not None
    
    def test_prediction_pattern_serialization(self):
        """Test prediction pattern serialization."""
        pattern = PredictionPattern(
            pattern_id="pattern1",
            user_id="user123",
            query_sequence=["query1", "query2"],
            response_sequence=["response1", "response2"],
            timestamp=datetime.utcnow(),
            confidence=0.8,
            access_frequency=5,
            last_used=datetime.utcnow()
        )
        
        # Test to_dict
        data = asdict(pattern)
        assert data["pattern_id"] == "pattern1"
        assert data["user_id"] == "user123"
        assert data["query_sequence"] == ["query1", "query2"]
        assert data["response_sequence"] == ["response1", "response2"]
        assert data["confidence"] == 0.8
        assert data["access_frequency"] == 5
        
        # Test from_dict would be similar
        pattern2 = PredictionPattern(**data)
        assert pattern2.pattern_id == pattern.pattern_id
        assert pattern2.user_id == pattern.user_id
        assert pattern2.query_sequence == pattern.query_sequence
        assert pattern2.response_sequence == pattern.response_sequence
        assert pattern2.confidence == pattern.confidence
        assert pattern2.access_frequency == pattern.access_frequency


class TestPredictionRequest:
    """Test PredictionRequest dataclass."""
    
    def test_prediction_request_creation(self):
        """Test creating prediction requests."""
        request = PredictionRequest(
            context="user is asking about machine learning",
            user_id="user123",
            timestamp=datetime.utcnow(),
            max_predictions=5
        )
        
        assert request.context == "user is asking about machine learning"
        assert request.user_id == "user123"
        assert request.timestamp is not None
        assert request.max_predictions == 5
    
    def test_prediction_request_defaults(self):
        """Test prediction request with default values."""
        request = PredictionRequest(
            context="test context",
            user_id="user123",
            timestamp=datetime.utcnow()
        )
        
        assert request.context == "test context"
        assert request.user_id == "user123"
        assert request.timestamp is not None
        assert request.max_predictions == 5  # Default value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])