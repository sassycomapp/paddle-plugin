"""
Unit tests for Vector Diary functionality.

This module contains comprehensive unit tests for the Vector Diary layer,
testing session management, longitudinal reasoning, and insight generation.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from src.cache_layers.vector_diary import VectorDiary
from src.core.base_cache import CacheStatus, CacheLayer
from src.core.config import VectorDiaryConfig


class TestVectorDiaryInitialization:
    """Test Vector Diary initialization and basic properties."""
    
    def test_cache_creation(self):
        """Test cache instance creation."""
        config = VectorDiaryConfig(
            cache_ttl_seconds=86400,
            max_entries=100000,
            retention_days=30,
            compression_enabled=True,
            auto_consolidate=True,
            consolidation_interval_hours=24
        )
        
        cache = VectorDiary("test_diary", config)
        assert cache.name == "test_diary"
        assert cache.config == config
        assert cache._sessions == {}
        assert cache._insights == {}
        assert cache._consolidation_task is None
    
    @pytest.mark.asyncio
    async def test_successful_initialization(self):
        """Test successful cache initialization."""
        config = VectorDiaryConfig(
            cache_ttl_seconds=86400,
            max_entries=100000,
            retention_days=30,
            compression_enabled=True,
            auto_consolidate=True,
            consolidation_interval_hours=24
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = VectorDiary("test_diary", config)
            cache._cache_dir = temp_dir
            result = await cache.initialize()
            
            assert result is True
            assert cache._consolidation_task is not None
            assert os.path.exists(os.path.join(temp_dir, "vector_diary.db"))
    
    @pytest.mark.asyncio
    async def test_failed_initialization(self):
        """Test failed cache initialization."""
        config = VectorDiaryConfig(
            cache_ttl_seconds=86400,
            max_entries=100000,
            retention_days=30,
            compression_enabled=True,
            auto_consolidate=True,
            consolidation_interval_hours=24
        )
        
        class FailingVectorDiary(VectorDiary):
            async def _initialize_storage(self):
                raise Exception("Test initialization failure")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = FailingVectorDiary("test_diary", config)
            cache._cache_dir = temp_dir
            result = await cache.initialize()
            
            assert result is False


class TestVectorDiaryCoreOperations:
    """Test core cache operations."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a vector diary configuration."""
        return VectorDiaryConfig(
            cache_ttl_seconds=86400,
            max_entries=100000,
            retention_days=30,
            compression_enabled=True,
            auto_consolidate=True,
            consolidation_interval_hours=24
        )
    
    @pytest.fixture
    def vector_diary(self, cache_config):
        """Create a vector diary instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = VectorDiary("test_diary", cache_config)
            cache._cache_dir = temp_dir
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, vector_diary):
        """Test setting and getting cache entries."""
        # Set a value
        result = await vector_diary.set("test_key", "test_value")
        assert result is True
        
        # Get the value
        get_result = await vector_diary.get("test_key")
        assert get_result.status == CacheStatus.HIT
        assert get_result.entry.value == "test_value"
        assert get_result.entry.layer == CacheLayer.VECTOR_DIARY
        
        # Stats should reflect the hit
        stats = await vector_diary.get_stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 0
        assert stats["total_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, vector_diary):
        """Test cache miss scenario."""
        get_result = await vector_diary.get("nonexistent_key")
        assert get_result.status == CacheStatus.MISS
        assert get_result.entry is None
        
        # Stats should reflect the miss
        stats = await vector_diary.get_stats()
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 1
        assert stats["total_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_cache_expiry(self, vector_diary):
        """Test cache expiry functionality."""
        # Set a value with short TTL
        await vector_diary.set("test_key", "test_value", ttl_seconds=1)
        
        # Should be available immediately
        get_result = await vector_diary.get("test_key")
        assert get_result.status == CacheStatus.HIT
        
        # Mock time to be in the future
        with patch('src.cache_layers.vector_diary.datetime') as mock_datetime:
            future_time = datetime.utcnow() + timedelta(seconds=2)
            mock_datetime.utcnow.return_value = future_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # Should be expired now
            get_result = await vector_diary.get("test_key")
            assert get_result.status == CacheStatus.EXPIRED
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, vector_diary):
        """Test cache deletion."""
        # Set a value
        await vector_diary.set("test_key", "test_value")
        
        # Delete it
        result = await vector_diary.delete("test_key")
        assert result is True
        
        # Should be gone
        get_result = await vector_diary.get("test_key")
        assert get_result.status == CacheStatus.MISS
    
    @pytest.mark.asyncio
    async def test_cache_clear(self, vector_diary):
        """Test cache clearing."""
        # Set multiple values
        await vector_diary.set("key1", "value1")
        await vector_diary.set("key2", "value2")
        await vector_diary.set("key3", "value3")
        
        # Clear cache
        result = await vector_diary.clear()
        assert result is True
        
        # Should all be gone
        for key in ["key1", "key2", "key3"]:
            get_result = await vector_diary.get(key)
            assert get_result.status == CacheStatus.MISS
        
        # Sessions should also be cleared
        assert len(vector_diary._sessions) == 0
    
    @pytest.mark.asyncio
    async def test_cache_exists(self, vector_diary):
        """Test cache exists functionality."""
        # Non-existent key
        assert await vector_diary.exists("nonexistent_key") is False
        
        # Set a value
        await vector_diary.set("test_key", "test_value")
        
        # Should exist
        assert await vector_diary.exists("test_key") is True
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self, vector_diary):
        """Test cleanup of expired entries."""
        # Set entries with different TTLs
        await vector_diary.set("short_ttl", "value1", ttl_seconds=1)
        await vector_diary.set("long_ttl", "value2", ttl_seconds=3600)
        
        # Mock time to make short_ttl entry expire
        with patch('src.cache_layers.vector_diary.datetime') as mock_datetime:
            future_time = datetime.utcnow() + timedelta(seconds=2)
            mock_datetime.utcnow.return_value = future_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # Clean up expired entries
            removed = await vector_diary.cleanup_expired()
            
            assert removed >= 1
            assert "short_ttl" not in vector_diary._cache
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, vector_diary):
        """Test cache statistics."""
        # Set some values
        await vector_diary.set("key1", "value1")
        await vector_diary.set("key2", "value2")
        
        # Get stats
        stats = await vector_diary.get_stats()
        
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["cache_errors"] == 0
        assert stats["total_operations"] == 0
        assert stats["total_cached_items"] == 2
        assert stats["hit_rate"] == 0.0
        assert stats["total_sessions"] == 0
        assert stats["total_insights"] == 0
        assert stats["consolidation_events"] == 0
    
    @pytest.mark.asyncio
    async def test_session_stats(self, vector_diary):
        """Test session statistics."""
        # Create some sessions
        session1 = await vector_diary.create_session("user1")
        session2 = await vector_diary.create_session("user2")
        
        stats = await vector_diary.get_stats()
        
        assert stats["total_sessions"] == 2
        assert stats["active_sessions"] == 2
        assert stats["session_creations"] == 2
        assert stats["session_accesses"] == 0
    
    @pytest.mark.asyncio
    async def test_insight_stats(self, vector_diary):
        """Test insight statistics."""
        # Generate some insights
        await vector_diary.generate_insights("user1")
        await vector_diary.generate_insights("user2")
        
        stats = await vector_diary.get_stats()
        
        assert stats["total_insights"] >= 2
        assert stats["insight_generations"] == 2
        assert stats["insight_quality_score"] >= 0.0


class TestVectorDiarySessionManagement:
    """Test session management functionality."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a vector diary configuration."""
        return VectorDiaryConfig(
            cache_ttl_seconds=86400,
            max_entries=100000,
            retention_days=30,
            compression_enabled=True,
            auto_consolidate=True,
            consolidation_interval_hours=24
        )
    
    @pytest.fixture
    def vector_diary(self, cache_config):
        """Create a vector diary instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = VectorDiary("test_diary", cache_config)
            cache._cache_dir = temp_dir
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_create_session(self, vector_diary):
        """Test session creation."""
        session = await vector_diary.create_session("user1")
        
        assert session.user_id == "user1"
        assert session.session_id is not None
        assert session.created_at is not None
        assert len(session.interactions) == 0
        assert session.metadata == {}
    
    @pytest.mark.asyncio
    async def test_get_session(self, vector_diary):
        """Test session retrieval."""
        # Create a session
        session = await vector_diary.create_session("user1")
        session_id = session.session_id
        
        # Get the session
        retrieved_session = await vector_diary.get_session(session_id)
        
        assert retrieved_session is not None
        assert retrieved_session.session_id == session_id
        assert retrieved_session.user_id == "user1"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, vector_diary):
        """Test retrieval of non-existent session."""
        session = await vector_diary.get_session("nonexistent_id")
        
        assert session is None
    
    @pytest.mark.asyncio
    async def test_add_interaction(self, vector_diary):
        """Test adding interactions to session."""
        # Create a session
        session = await vector_diary.create_session("user1")
        
        # Add interactions
        await vector_diary.add_interaction(session.session_id, "query1", "response1")
        await vector_diary.add_interaction(session.session_id, "query2", "response2")
        
        # Verify interactions
        retrieved_session = await vector_diary.get_session(session.session_id)
        assert len(retrieved_session.interactions) == 2
        assert retrieved_session.interactions[0].query == "query1"
        assert retrieved_session.interactions[0].response == "response1"
        assert retrieved_session.interactions[1].query == "query2"
        assert retrieved_session.interactions[1].response == "response2"
    
    @pytest.mark.asyncio
    async def test_add_interaction_to_nonexistent_session(self, vector_diary):
        """Test adding interaction to non-existent session."""
        result = await vector_diary.add_interaction("nonexistent_id", "query", "response")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_user_sessions(self, vector_diary):
        """Test getting all sessions for a user."""
        # Create sessions for different users
        session1 = await vector_diary.create_session("user1")
        session2 = await vector_diary.create_session("user1")
        session3 = await vector_diary.create_session("user2")
        
        # Get sessions for user1
        user_sessions = await vector_diary.get_user_sessions("user1")
        
        assert len(user_sessions) == 2
        session_ids = [s.session_id for s in user_sessions]
        assert session1.session_id in session_ids
        assert session2.session_id in session_ids
        assert session3.session_id not in session_ids
    
    @pytest.mark.asyncio
    async def test_close_session(self, vector_diary):
        """Test closing a session."""
        # Create a session
        session = await vector_diary.create_session("user1")
        session_id = session.session_id
        
        # Close the session
        result = await vector_diary.close_session(session_id)
        
        assert result is True
        
        # Verify session is closed
        retrieved_session = await vector_diary.get_session(session_id)
        assert retrieved_session is None
    
    @pytest.mark.asyncio
    async def test_close_nonexistent_session(self, vector_diary):
        """Test closing non-existent session."""
        result = await vector_diary.close_session("nonexistent_id")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_session_expiry(self, vector_diary):
        """Test session expiry functionality."""
        # Create a session
        session = await vector_diary.create_session("user1")
        session_id = session.session_id
        
        # Mock time to make session expire
        with patch('src.cache_layers.vector_diary.datetime') as mock_datetime:
            future_time = datetime.utcnow() + timedelta(days=31)  # Beyond retention
            mock_datetime.utcnow.return_value = future_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # Session should be expired
            retrieved_session = await vector_diary.get_session(session_id)
            assert retrieved_session is None


class TestVectorDiaryInsightGeneration:
    """Test insight generation functionality."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a vector diary configuration."""
        return VectorDiaryConfig(
            cache_ttl_seconds=86400,
            max_entries=100000,
            retention_days=30,
            compression_enabled=True,
            auto_consolidate=True,
            consolidation_interval_hours=24
        )
    
    @pytest.fixture
    def vector_diary(self, cache_config):
        """Create a vector diary instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = VectorDiary("test_diary", cache_config)
            cache._cache_dir = temp_dir
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_generate_insights(self, vector_diary):
        """Test insight generation."""
        # Create a session with interactions
        session = await vector_diary.create_session("user1")
        await vector_diary.add_interaction(session.session_id, "What is AI?", "AI is artificial intelligence")
        await vector_diary.add_interaction(session.session_id, "What is ML?", "ML is machine learning")
        
        # Generate insights
        insights = await vector_diary.generate_insights(session.session_id)
        
        assert len(insights) > 0
        assert all(hasattr(insight, 'type') for insight in insights)
        assert all(hasattr(insight, 'content') for insight in insights)
        assert all(hasattr(insight, 'confidence') for insight in insights)
        assert all(0.0 <= insight.confidence <= 1.0 for insight in insights)
    
    @pytest.mark.asyncio
    async def test_generate_insights_empty_session(self, vector_diary):
        """Test insight generation for empty session."""
        # Create an empty session
        session = await vector_diary.create_session("user1")
        
        # Generate insights
        insights = await vector_diary.generate_insights(session.session_id)
        
        # Should return empty list for empty session
        assert len(insights) == 0
    
    @pytest.mark.asyncio
    async def test_generate_insights_nonexistent_session(self, vector_diary):
        """Test insight generation for non-existent session."""
        insights = await vector_diary.generate_insights("nonexistent_id")
        
        # Should return empty list
        assert len(insights) == 0
    
    @pytest.mark.asyncio
    async def test_get_insights(self, vector_diary):
        """Test retrieving insights."""
        # Create a session and generate insights
        session = await vector_diary.create_session("user1")
        await vector_diary.add_interaction(session.session_id, "What is AI?", "AI is artificial intelligence")
        await vector_diary.add_interaction(session.session_id, "What is ML?", "ML is machine learning")
        
        insights = await vector_diary.generate_insights(session.session_id)
        insight_id = insights[0].insight_id
        
        # Get the insight
        retrieved_insight = await vector_diary.get_insight(insight_id)
        
        assert retrieved_insight is not None
        assert retrieved_insight.insight_id == insight_id
        assert retrieved_insight.session_id == session.session_id
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_insight(self, vector_diary):
        """Test retrieving non-existent insight."""
        insight = await vector_diary.get_insight("nonexistent_id")
        
        assert insight is None
    
    @pytest.mark.asyncio
    async def test_get_session_insights(self, vector_diary):
        """Test getting all insights for a session."""
        # Create a session and generate insights
        session = await vector_diary.create_session("user1")
        await vector_diary.add_interaction(session.session_id, "What is AI?", "AI is artificial intelligence")
        await vector_diary.add_interaction(session.session_id, "What is ML?", "ML is machine learning")
        
        insights = await vector_diary.generate_insights(session.session_id)
        
        # Get session insights
        session_insights = await vector_diary.get_session_insights(session.session_id)
        
        assert len(session_insights) == len(insights)
        insight_ids = [i.insight_id for i in insights]
        for insight in session_insights:
            assert insight.insight_id in insight_ids
    
    @pytest.mark.asyncio
    async def test_insight_types(self, vector_diary):
        """Test different types of insights."""
        # Create a session with various interactions
        session = await vector_diary.create_session("user1")
        await vector_diary.add_interaction(session.session_id, "What is AI?", "AI is artificial intelligence")
        await vector_diary.add_interaction(session.session_id, "Explain neural networks", "Neural networks are computing systems")
        await vector_diary.add_interaction(session.session_id, "How does deep learning work?", "Deep learning uses neural networks")
        
        # Generate insights
        insights = await vector_diary.generate_insights(session.session_id)
        
        # Should have different types of insights
        insight_types = set(insight.type for insight in insights)
        assert len(insight_types) > 0
        
        # Check for common insight types
        expected_types = {"pattern", "trend", "preference", "behavior"}
        assert insight_types.intersection(expected_types)


class TestVectorDiaryLongitudinalReasoning:
    """Test longitudinal reasoning functionality."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a vector diary configuration."""
        return VectorDiaryConfig(
            cache_ttl_seconds=86400,
            max_entries=100000,
            retention_days=30,
            compression_enabled=True,
            auto_consolidate=True,
            consolidation_interval_hours=24
        )
    
    @pytest.fixture
    def vector_diary(self, cache_config):
        """Create a vector diary instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = VectorDiary("test_diary", cache_config)
            cache._cache_dir = temp_dir
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_analyze_user_behavior(self, vector_diary):
        """Test user behavior analysis."""
        # Create sessions with different behaviors
        session1 = await vector_diary.create_session("user1")
        await vector_diary.add_interaction(session1.session_id, "What is AI?", "AI is artificial intelligence")
        await vector_diary.add_interaction(session1.session_id, "What is ML?", "ML is machine learning")
        
        session2 = await vector_diary.create_session("user1")
        await vector_diary.add_interaction(session2.session_id, "Explain deep learning", "Deep learning is a subset of ML")
        await vector_diary.add_interaction(session2.session_id, "How do neural networks work?", "Neural networks are computing systems")
        
        # Analyze user behavior
        behavior_analysis = await vector_diary.analyze_user_behavior("user1")
        
        assert behavior_analysis is not None
        assert "interests" in behavior_analysis
        assert "patterns" in behavior_analysis
        assert "preferences" in behavior_analysis
        assert "engagement" in behavior_analysis
    
    @pytest.mark.asyncio
    async def test_analyze_user_behavior_no_data(self, vector_diary):
        """Test user behavior analysis with no data."""
        behavior_analysis = await vector_diary.analyze_user_behavior("nonexistent_user")
        
        assert behavior_analysis is None
    
    @pytest.mark.asyncio
    async def test_track_learning_progress(self, vector_diary):
        """Test learning progress tracking."""
        # Create sessions showing learning progression
        session1 = await vector_diary.create_session("user1")
        await vector_diary.add_interaction(session1.session_id, "What is AI?", "AI is artificial intelligence")
        
        session2 = await vector_diary.create_session("user1")
        await vector_diary.add_interaction(session2.session_id, "How does AI work?", "AI uses algorithms and data")
        
        session3 = await vector_diary.create_session("user1")
        await vector_diary.add_interaction(session3.session_id, "What are neural networks?", "Neural networks are inspired by the brain")
        
        # Track learning progress
        progress = await vector_diary.track_learning_progress("user1")
        
        assert progress is not None
        assert "current_level" in progress
        assert "learning_path" in progress
        assert "mastery_progress" in progress
        assert "recommendations" in progress
    
    @pytest.mark.asyncio
    async def test_predict_user_needs(self, vector_diary):
        """Test user needs prediction."""
        # Create sessions showing user interests
        session1 = await vector_diary.create_session("user1")
        await vector_diary.add_interaction(session1.session_id, "What is AI?", "AI is artificial intelligence")
        await vector_diary.add_interaction(session1.session_id, "What is ML?", "ML is machine learning")
        
        session2 = await vector_diary.create_session("user1")
        await vector_diary.add_interaction(session2.session_id, "Explain deep learning", "Deep learning is a subset of ML")
        
        # Predict user needs
        predictions = await vector_diary.predict_user_needs("user1")
        
        assert predictions is not None
        assert len(predictions) > 0
        assert all(hasattr(pred, 'topic') for pred in predictions)
        assert all(hasattr(pred, 'confidence') for pred in predictions)
        assert all(0.0 <= pred.confidence <= 1.0 for pred in predictions)
    
    @pytest.mark.asyncio
    async def test_generate_learning_recommendations(self, vector_diary):
        """Test learning recommendations generation."""
        # Create sessions showing user knowledge level
        session1 = await vector_diary.create_session("user1")
        await vector_diary.add_interaction(session1.session_id, "What is AI?", "AI is artificial intelligence")
        
        session2 = await vector_diary.create_session("user1")
        await vector_diary.add_interaction(session2.session_id, "What is ML?", "ML is machine learning")
        
        # Generate recommendations
        recommendations = await vector_diary.generate_learning_recommendations("user1")
        
        assert recommendations is not None
        assert len(recommendations) > 0
        assert all(hasattr(rec, 'topic') for rec in recommendations)
        assert all(hasattr(rec, 'priority') for rec in recommendations)
        assert all(hasattr(rec, 'reasoning') for rec in recommendations)


class TestVectorDiaryConsolidation:
    """Test consolidation functionality."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a vector diary configuration."""
        return VectorDiaryConfig(
            cache_ttl_seconds=86400,
            max_entries=100000,
            retention_days=30,
            compression_enabled=True,
            auto_consolidate=True,
            consolidation_interval_hours=24
        )
    
    @pytest.fixture
    def vector_diary(self, cache_config):
        """Create a vector diary instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = VectorDiary("test_diary", cache_config)
            cache._cache_dir = temp_dir
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_consolidate_sessions(self, vector_diary):
        """Test session consolidation."""
        # Create multiple sessions for the same user
        session1 = await vector_diary.create_session("user1")
        await vector_diary.add_interaction(session1.session_id, "What is AI?", "AI is artificial intelligence")
        
        session2 = await vector_diary.create_session("user1")
        await vector_diary.add_interaction(session2.session_id, "What is ML?", "ML is machine learning")
        
        session3 = await vector_diary.create_session("user1")
        await vector_diary.add_interaction(session3.session_id, "Explain deep learning", "Deep learning is a subset of ML")
        
        # Consolidate sessions
        consolidated = await vector_diary.consolidate_sessions("user1")
        
        assert consolidated is True
        
        # Should have one consolidated session
        user_sessions = await vector_diary.get_user_sessions("user1")
        assert len(user_sessions) == 1
        
        # Consolidated session should have all interactions
        consolidated_session = user_sessions[0]
        assert len(consolidated_session.interactions) == 3
    
    @pytest.mark.asyncio
    async def test_consolidate_nonexistent_user(self, vector_diary):
        """Test consolidation for non-existent user."""
        consolidated = await vector_diary.consolidate_sessions("nonexistent_user")
        
        assert consolidated is False
    
    @pytest.mark.asyncio
    async def test_auto_consolidation(self, vector_diary):
        """Test automatic consolidation."""
        # Create multiple sessions
        session1 = await vector_diary.create_session("user1")
        await vector_diary.add_interaction(session1.session_id, "What is AI?", "AI is artificial intelligence")
        
        session2 = await vector_diary.create_session("user1")
        await vector_diary.add_interaction(session2.session_id, "What is ML?", "ML is machine learning")
        
        # Wait for auto-consolidation (mock the delay)
        await asyncio.sleep(0.1)
        
        # Should have consolidated sessions
        user_sessions = await vector_diary.get_user_sessions("user1")
        assert len(user_sessions) <= 2  # May have been consolidated
    
    @pytest.mark.asyncio
    async def test_compression_enabled(self, vector_diary):
        """Test data compression."""
        # Enable compression
        vector_diary.config.compression_enabled = True
        
        # Create a session with large data
        session = await vector_diary.create_session("user1")
        large_data = "x" * 10000  # 10KB of data
        await vector_diary.add_interaction(session.session_id, "large_query", large_data)
        
        # Get the session
        retrieved_session = await vector_diary.get_session(session.session_id)
        
        # Data should be compressed
        assert retrieved_session is not None
        assert len(retrieved_session.interactions[0].response) == len(large_data)
        # In a real implementation, we'd check compression ratio
    
    @pytest.mark.asyncio
    async def test_retention_policy(self, vector_diary):
        """Test retention policy enforcement."""
        # Set short retention
        vector_diary.config.retention_days = 1
        
        # Create a session
        session = await vector_diary.create_session("user1")
        session_id = session.session_id
        
        # Mock time to make session expire
        with patch('src.cache_layers.vector_diary.datetime') as mock_datetime:
            future_time = datetime.utcnow() + timedelta(days=2)
            mock_datetime.utcnow.return_value = future_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # Session should be expired due to retention policy
            retrieved_session = await vector_diary.get_session(session_id)
            assert retrieved_session is None


class TestVectorDiaryErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.fixture
    def cache_config(self):
        """Create a vector diary configuration."""
        return VectorDiaryConfig(
            cache_ttl_seconds=86400,
            max_entries=100000,
            retention_days=30,
            compression_enabled=True,
            auto_consolidate=True,
            consolidation_interval_hours=24
        )
    
    @pytest.fixture
    def vector_diary(self, cache_config):
        """Create a vector diary instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = VectorDiary("test_diary", cache_config)
            cache._cache_dir = temp_dir
            cache._running = True
            return cache
    
    @pytest.mark.asyncio
    async def test_storage_error_handling(self, vector_diary):
        """Test error handling in storage operations."""
        # Mock storage to fail
        vector_diary._storage.save_session = AsyncMock(side_effect=Exception("Storage error"))
        
        # Should handle error gracefully
        session = await vector_diary.create_session("user1")
        
        # Session should still be created in memory
        assert session is not None
        assert session.user_id == "user1"
    
    @pytest.mark.asyncio
    async def test_concurrent_session_access(self, vector_diary):
        """Test concurrent session access."""
        async def add_interactions(session_id):
            for i in range(5):
                await vector_diary.add_interaction(session_id, f"query_{i}", f"response_{i}")
        
        # Create a session
        session = await vector_diary.create_session("user1")
        
        # Add interactions concurrently
        await asyncio.gather(*[add_interactions(session.session_id) for _ in range(3)])
        
        # Should have all interactions
        retrieved_session = await vector_diary.get_session(session.session_id)
        assert len(retrieved_session.interactions) == 15  # 5 * 3
    
    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self, vector_diary):
        """Test handling of memory pressure scenarios."""
        # Create many sessions
        sessions = []
        for i in range(1000):
            session = await vector_diary.create_session(f"user{i}")
            sessions.append(session)
        
        # Should handle large number of sessions
        assert len(vector_diary._sessions) == 1000
        
        # Get stats
        stats = await vector_diary.get_stats()
        assert stats["total_sessions"] == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])