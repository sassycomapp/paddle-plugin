"""
Integration tests for MCP Server functionality.

This module contains comprehensive integration tests for the MCP server,
testing tool exposure, routing, protocol compliance, and server lifecycle.
"""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastmcp import FastMCP, Context
from typing import Dict, List, Any, Optional

from src.mcp.server import (
    mcp_server_lifespan,
    MCPServerContext,
    cache_get,
    cache_set,
    cache_delete,
    cache_search,
    cache_stats,
    cache_clear,
    predictive_cache_predict,
    semantic_cache_similar,
    vector_cache_search,
    global_cache_query,
    vector_diary_session,
    cache_tools
)
from src.mcp.tools import CacheMCPTools, CacheRequest, CacheResponse
from src.core.base_cache import CacheLayer, CacheStatus
from src.cache_layers.predictive_cache import PredictiveCache
from src.cache_layers.semantic_cache import SemanticCache
from src.cache_layers.vector_cache import VectorCache
from src.cache_layers.global_cache import GlobalCache
from src.cache_layers.vector_diary import VectorDiary


class TestMCPServerLifecycle:
    """Test MCP server lifecycle management."""
    
    @pytest.mark.asyncio
    async def test_server_lifespan_initialization(self):
        """Test server lifespan initialization."""
        # Mock cache tools
        mock_tools = Mock()
        mock_tools.initialize_all.return_value = True
        
        with patch('src.mcp.server.CacheMCPTools', return_value=mock_tools):
            async with mcp_server_lifespan(None) as context:
                assert isinstance(context, MCPServerContext)
                assert context.cache_tools == mock_tools
                assert "caches" in context.__dict__
    
    @pytest.mark.asyncio
    async def test_server_lifespan_initialization_failure(self):
        """Test server lifespan initialization failure."""
        # Mock cache tools that fail to initialize
        mock_tools = Mock()
        mock_tools.initialize_all.return_value = False
        
        with patch('src.mcp.server.CacheMCPTools', return_value=mock_tools):
            with pytest.raises(RuntimeError):
                async with mcp_server_lifespan(None) as context:
                    pass
    
    @pytest.mark.asyncio
    async def test_server_lifespan_cleanup(self):
        """Test server lifespan cleanup."""
        mock_tools = Mock()
        mock_tools.initialize_all.return_value = True
        mock_tools.close_all = AsyncMock()
        
        with patch('src.mcp.server.CacheMCPTools', return_value=mock_tools):
            async with mcp_server_lifespan(None) as context:
                pass  # Server context should be cleaned up after this block
            
            # Verify cleanup was called
            mock_tools.close_all.assert_called_once()


class TestCacheMCPTools:
    """Test CacheMCPTools integration."""
    
    @pytest.fixture
    def cache_tools(self):
        """Create cache tools instance."""
        return CacheMCPTools()
    
    @pytest.fixture
    def mock_cache(self):
        """Create a mock cache instance."""
        cache = Mock()
        cache.get_layer.return_value = CacheLayer.SEMANTIC
        cache.get = AsyncMock(return_value=Mock(
            status=CacheStatus.HIT, 
            entry=Mock(value="test_value")
        ))
        cache.set = AsyncMock(return_value=True)
        cache.delete = AsyncMock(return_value=True)
        cache.clear = AsyncMock(return_value=True)
        cache.get_stats = AsyncMock(return_value={"total_entries": 10})
        return cache
    
    @pytest.mark.asyncio
    async def test_cache_tools_initialization(self, cache_tools):
        """Test cache tools initialization."""
        assert cache_tools.caches == {}
        assert cache_tools.request_count == 0
        assert cache_tools.hit_count == 0
        assert cache_tools.miss_count == 0
        assert cache_tools.error_count == 0
    
    @pytest.mark.asyncio
    async def test_register_cache(self, cache_tools, mock_cache):
        """Test cache registration."""
        cache_tools.register_cache(mock_cache)
        
        assert CacheLayer.SEMANTIC in cache_tools.caches
        assert cache_tools.caches[CacheLayer.SEMANTIC] == mock_cache
    
    @pytest.mark.asyncio
    async def test_initialize_all_success(self, cache_tools, mock_cache):
        """Test successful initialization of all caches."""
        cache_tools.register_cache(mock_cache)
        
        result = await cache_tools.initialize_all()
        assert result is True
        mock_cache.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_all_partial_failure(self, cache_tools, mock_cache):
        """Test partial failure in cache initialization."""
        mock_cache.initialize.return_value = False
        cache_tools.register_cache(mock_cache)
        
        result = await cache_tools.initialize_all()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_cache_hit(self, cache_tools, mock_cache):
        """Test successful cache get operation."""
        cache_tools.register_cache(mock_cache)
        
        result = await cache_tools.get("test_key")
        
        assert result.success is True
        assert result.status == CacheStatus.HIT
        assert result.data == "test_value"
        assert result.cache_layer == CacheLayer.SEMANTIC
        assert cache_tools.hit_count == 1
        assert cache_tools.request_count == 1
    
    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache_tools, mock_cache):
        """Test cache miss scenario."""
        mock_cache.get.return_value = Mock(status=CacheStatus.MISS)
        cache_tools.register_cache(mock_cache)
        
        result = await cache_tools.get("nonexistent_key")
        
        assert result.success is False
        assert result.status == CacheStatus.MISS
        assert result.data is None
        assert cache_tools.miss_count == 1
        assert cache_tools.request_count == 1
    
    @pytest.mark.asyncio
    async def test_set_cache(self, cache_tools, mock_cache):
        """Test cache set operation."""
        cache_tools.register_cache(mock_cache)
        
        result = await cache_tools.set("test_key", "test_value")
        
        assert result.success is True
        assert result.status == CacheStatus.HIT
        mock_cache.set.assert_called_once_with(
            key="test_key",
            value="test_value",
            ttl_seconds=None,
            metadata=None,
            embedding=None
        )
    
    @pytest.mark.asyncio
    async def test_delete_cache(self, cache_tools, mock_cache):
        """Test cache delete operation."""
        cache_tools.register_cache(mock_cache)
        
        result = await cache_tools.delete("test_key")
        
        assert result.success is True
        assert result.status == CacheStatus.HIT
        mock_cache.delete.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_get_stats(self, cache_tools, mock_cache):
        """Test getting cache statistics."""
        cache_tools.register_cache(mock_cache)
        
        result = await cache_tools.get_stats()
        
        assert result.success is True
        assert result.status == CacheStatus.HIT
        assert "total_requests" in result.data
        assert "cache_layers" in result.data
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, cache_tools, mock_cache):
        """Test clearing cache."""
        cache_tools.register_cache(mock_cache)
        
        result = await cache_tools.clear_cache()
        
        assert result.success is True
        assert result.status == CacheStatus.HIT
        mock_cache.clear.assert_called_once()
    
    def test_determine_cache_layers(self, cache_tools):
        """Test cache layer determination logic."""
        # Test predictive cache routing
        layers = cache_tools._determine_cache_layers("predict something")
        assert CacheLayer.PREDICTIVE in layers
        
        # Test semantic cache routing
        layers = cache_tools._determine_cache_layers("what is the meaning of life")
        assert CacheLayer.SEMANTIC in layers
        
        # Test vector cache routing
        layers = cache_tools._determine_cache_layers("embedding search")
        assert CacheLayer.VECTOR in layers
        
        # Test global cache routing
        layers = cache_tools._determine_cache_layers("knowledge base query")
        assert CacheLayer.GLOBAL in layers
        
        # Test vector diary routing
        layers = cache_tools._determine_cache_layers("conversation history")
        assert CacheLayer.VECTOR_DIARY in layers
    
    def test_get_performance_metrics(self, cache_tools):
        """Test performance metrics retrieval."""
        # Add some mock data
        cache_tools.request_count = 100
        cache_tools.hit_count = 80
        cache_tools.miss_count = 20
        cache_tools.error_count = 5
        
        metrics = cache_tools.get_performance_metrics()
        
        assert metrics["total_requests"] == 100
        assert metrics["total_hits"] == 80
        assert metrics["total_misses"] == 20
        assert metrics["total_errors"] == 5
        assert metrics["hit_rate"] == 0.8
        assert metrics["cache_layers"] == 0  # No caches registered yet


class TestMCPTools:
    """Test individual MCP tools."""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock context."""
        context = Mock()
        context.request_context = Mock()
        context.request_context.lifespan_context = Mock()
        context.request_context.lifespan_context.cache_tools = Mock()
        return context
    
    @pytest.mark.asyncio
    async def test_cache_get_tool(self, mock_context):
        """Test cache get MCP tool."""
        # Mock the cache tools
        mock_context.request_context.lifespan_context.cache_tools.get = AsyncMock(
            return_value=Mock(
                success=True,
                status=CacheStatus.HIT,
                message="Cache hit",
                data="test_value",
                execution_time_ms=10.5,
                cache_layer=CacheLayer.SEMANTIC
            )
        )
        
        result = await cache_get("test_key", mock_context)
        
        assert result["success"] is True
        assert result["status"] == "hit"
        assert result["data"] == "test_value"
        assert result["execution_time_ms"] == 10.5
    
    @pytest.mark.asyncio
    async def test_cache_set_tool(self, mock_context):
        """Test cache set MCP tool."""
        # Mock the cache tools
        mock_context.request_context.lifespan_context.cache_tools.set = AsyncMock(
            return_value=Mock(
                success=True,
                status=CacheStatus.HIT,
                message="Stored successfully",
                execution_time_ms=15.2
            )
        )
        
        result = await cache_set(
            "test_key",
            "test_value",
            mock_context,
            layer="semantic",
            ttl_seconds=3600,
            metadata={"test": "metadata"}
        )
        
        assert result["success"] is True
        assert result["status"] == "hit"
        assert result["execution_time_ms"] == 15.2
    
    @pytest.mark.asyncio
    async def test_cache_delete_tool(self, mock_context):
        """Test cache delete MCP tool."""
        # Mock the cache tools
        mock_context.request_context.lifespan_context.cache_tools.delete = AsyncMock(
            return_value=Mock(
                success=True,
                status=CacheStatus.HIT,
                message="Deleted successfully",
                execution_time_ms=5.0
            )
        )
        
        result = await cache_delete("test_key", mock_context)
        
        assert result["success"] is True
        assert result["status"] == "hit"
        assert result["execution_time_ms"] == 5.0
    
    @pytest.mark.asyncio
    async def test_cache_search_tool(self, mock_context):
        """Test cache search MCP tool."""
        # Mock the cache tools
        mock_context.request_context.lifespan_context.cache_tools.search = AsyncMock(
            return_value=Mock(
                success=True,
                status=CacheStatus.HIT,
                message="Search completed",
                data=[{"key": "result1", "score": 0.9}],
                execution_time_ms=25.0
            )
        )
        
        result = await cache_search(
            "search query",
            mock_context,
            n_results=5,
            min_similarity=0.7
        )
        
        assert result["success"] is True
        assert result["status"] == "hit"
        assert result["data"] == [{"key": "result1", "score": 0.9}]
        assert result["execution_time_ms"] == 25.0
    
    @pytest.mark.asyncio
    async def test_cache_stats_tool(self, mock_context):
        """Test cache stats MCP tool."""
        # Mock the cache tools
        mock_context.request_context.lifespan_context.cache_tools.get_stats = AsyncMock(
            return_value=Mock(
                success=True,
                status=CacheStatus.HIT,
                message="Stats retrieved",
                data={"total_requests": 100, "hit_rate": 0.8}
            )
        )
        
        result = await cache_stats(mock_context)
        
        assert result["success"] is True
        assert result["status"] == "hit"
        assert result["data"]["total_requests"] == 100
        assert result["data"]["hit_rate"] == 0.8
    
    @pytest.mark.asyncio
    async def test_cache_clear_tool(self, mock_context):
        """Test cache clear MCP tool."""
        # Mock the cache tools
        mock_context.request_context.lifespan_context.cache_tools.clear_cache = AsyncMock(
            return_value=Mock(
                success=True,
                status=CacheStatus.HIT,
                message="Cache cleared"
            )
        )
        
        result = await cache_clear(mock_context)
        
        assert result["success"] is True
        assert result["status"] == "hit"
        assert result["message"] == "Cache cleared"


class TestPredictiveCacheTools:
    """Test predictive cache specific tools."""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock context."""
        context = Mock()
        context.request_context = Mock()
        context.request_context.lifespan_context = Mock()
        context.request_context.lifespan_context.caches = Mock()
        return context
    
    @pytest.mark.asyncio
    async def test_predictive_cache_predict_tool(self, mock_context):
        """Test predictive cache predict tool."""
        # Mock the predictive cache
        mock_cache = Mock()
        mock_cache.predict = AsyncMock(return_value=[
            {"query": "predicted_query", "confidence": 0.8, "response": "predicted_response"}
        ])
        mock_context.request_context.lifespan_context.caches = {"predictive": mock_cache}
        
        result = await predictive_cache_predict("test query", mock_context)
        
        assert result["success"] is True
        assert result["status"] == "ok"
        assert len(result["data"]) == 1
        assert result["data"][0]["query"] == "predicted_query"
        assert result["data"][0]["confidence"] == 0.8


class TestSemanticCacheTools:
    """Test semantic cache specific tools."""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock context."""
        context = Mock()
        context.request_context = Mock()
        context.request_context.lifespan_context = Mock()
        context.request_context.lifespan_context.caches = Mock()
        return context
    
    @pytest.mark.asyncio
    async def test_semantic_cache_similar_tool(self, mock_context):
        """Test semantic cache similar tool."""
        # Mock the semantic cache
        mock_cache = Mock()
        mock_cache.find_similar = AsyncMock(return_value=[
            {"key": "similar1", "similarity": 0.9},
            {"key": "similar2", "similarity": 0.8}
        ])
        mock_context.request_context.lifespan_context.caches = {"semantic": mock_cache}
        
        result = await semantic_cache_similar("test query", mock_context)
        
        assert result["success"] is True
        assert result["status"] == "ok"
        assert len(result["data"]) == 2
        assert result["data"][0]["similarity"] == 0.9


class TestVectorCacheTools:
    """Test vector cache specific tools."""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock context."""
        context = Mock()
        context.request_context = Mock()
        context.request_context.lifespan_context = Mock()
        context.request_context.lifespan_context.caches = Mock()
        return context
    
    @pytest.mark.asyncio
    async def test_vector_cache_search_tool(self, mock_context):
        """Test vector cache search tool."""
        # Mock the vector cache
        mock_cache = Mock()
        mock_cache.search = AsyncMock(return_value=[
            {"key": "vector1", "score": 0.95, "context": "relevant context"},
            {"key": "vector2", "score": 0.85, "context": "somewhat relevant"}
        ])
        mock_context.request_context.lifespan_context.caches = {"vector": mock_cache}
        
        result = await vector_cache_search(
            "search vector",
            mock_context,
            n_results=5,
            min_similarity=0.7,
            use_reranking=True
        )
        
        assert result["success"] is True
        assert result["status"] == "ok"
        assert len(result["data"]) == 2
        assert result["data"][0]["score"] == 0.95


class TestGlobalCacheTools:
    """Test global cache specific tools."""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock context."""
        context = Mock()
        context.request_context = Mock()
        context.request_context.lifespan_context = Mock()
        context.request_context.lifespan_context.caches = Mock()
        return context
    
    @pytest.mark.asyncio
    async def test_global_cache_query_tool(self, mock_context):
        """Test global cache query tool."""
        # Mock the global cache
        mock_cache = Mock()
        mock_cache.query_rag = AsyncMock(return_value=[
            {"source": "doc1", "content": "Relevant content 1", "score": 0.9},
            {"source": "doc2", "content": "Relevant content 2", "score": 0.8}
        ])
        mock_context.request_context.lifespan_context.caches = {"global": mock_cache}
        
        result = await global_cache_query(
            "knowledge query",
            mock_context,
            n_results=5,
            use_fallback=True
        )
        
        assert result["success"] is True
        assert result["status"] == "ok"
        assert len(result["data"]) == 2
        assert result["data"][0]["source"] == "doc1"


class TestVectorDiaryTools:
    """Test vector diary specific tools."""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock context."""
        context = Mock()
        context.request_context = Mock()
        context.request_context.lifespan_context = Mock()
        context.request_context.lifespan_context.caches = Mock()
        return context
    
    @pytest.mark.asyncio
    async def test_vector_diary_session_tool(self, mock_context):
        """Test vector diary session tool."""
        # Mock the vector diary
        mock_cache = Mock()
        mock_cache.create_session = AsyncMock(return_value=Mock(
            session_id="session_123",
            user_id="user_456",
            created_at="2023-01-01T00:00:00Z"
        ))
        mock_cache.add_interaction = AsyncMock(return_value=True)
        mock_cache.get_session = AsyncMock(return_value=Mock(
            session_id="session_123",
            user_id="user_456",
            interactions=[
                {"query": "test query", "response": "test response", "timestamp": "2023-01-01T00:00:00Z"}
            ]
        ))
        mock_context.request_context.lifespan_context.caches = {"vector_diary": mock_cache}
        
        # Test session creation
        result = await vector_diary_session(
            "user_456",
            mock_context,
            create_if_missing=True
        )
        
        assert result["success"] is True
        assert result["status"] == "ok"
        assert result["data"]["session_id"] == "session_123"
        
        # Test adding interaction
        result = await vector_diary_session(
            "user_456",
            mock_context,
            session_id="session_123",
            add_interaction=True,
            query="new query",
            response="new response"
        )
        
        assert result["success"] is True
        assert result["status"] == "ok"


class TestMCPProtocolCompliance:
    """Test MCP protocol compliance."""
    
    @pytest.mark.asyncio
    async def test_tool_response_format(self):
        """Test that tool responses comply with MCP protocol."""
        mock_context = Mock()
        mock_context.request_context = Mock()
        mock_context.request_context.lifespan_context = Mock()
        mock_context.request_context.lifespan_context.cache_tools = Mock()
        
        # Mock successful response
        mock_context.request_context.lifespan_context.cache_tools.get = AsyncMock(
            return_value=Mock(
                success=True,
                status=CacheStatus.HIT,
                message="Cache hit",
                data="test_value",
                execution_time_ms=10.5,
                cache_layer=CacheLayer.SEMANTIC
            )
        )
        
        result = await cache_get("test_key", mock_context)
        
        # Check response format
        assert isinstance(result, dict)
        assert "success" in result
        assert "status" in result
        assert "message" in result
        assert "data" in result
        assert "execution_time_ms" in result
        
        # Check data types
        assert isinstance(result["success"], bool)
        assert isinstance(result["status"], str)
        assert isinstance(result["message"], str)
        assert isinstance(result["data"], str)
        assert isinstance(result["execution_time_ms"], (int, float))
    
    @pytest.mark.asyncio
    async def test_error_response_format(self):
        """Test that error responses comply with MCP protocol."""
        mock_context = Mock()
        mock_context.request_context = Mock()
        mock_context.request_context.lifespan_context = Mock()
        mock_context.request_context.lifespan_context.cache_tools = Mock()
        
        # Mock error response
        mock_context.request_context.lifespan_context.cache_tools.get = AsyncMock(
            return_value=Mock(
                success=False,
                status=CacheStatus.ERROR,
                message="Cache error",
                error="Something went wrong",
                execution_time_ms=5.0
            )
        )
        
        result = await cache_get("error_key", mock_context)
        
        # Check error response format
        assert isinstance(result, dict)
        assert "success" in result
        assert "status" in result
        assert "message" in result
        assert "error" in result
        assert "execution_time_ms" in result
        
        # Check error-specific fields
        assert result["success"] is False
        assert result["status"] == "error"
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_tool_parameter_validation(self):
        """Test tool parameter validation."""
        mock_context = Mock()
        mock_context.request_context = Mock()
        mock_context.request_context.lifespan_context = Mock()
        mock_context.request_context.lifespan_context.cache_tools = Mock()
        
        # Test missing required parameter
        with pytest.raises(Exception):
            await cache_get(None, mock_context)
        
        # Test invalid parameter types
        with pytest.raises(Exception):
            await cache_get(123, mock_context)  # Should be string
    
    @pytest.mark.asyncio
    async def test_tool_timeout_handling(self):
        """Test tool timeout handling."""
        mock_context = Mock()
        mock_context.request_context = Mock()
        mock_context.request_context.lifespan_context = Mock()
        mock_context.request_context.lifespan_context.cache_tools = Mock()
        
        # Mock timeout
        mock_context.request_context.lifespan_context.cache_tools.get = AsyncMock(
            side_effect=asyncio.TimeoutError("Operation timed out")
        )
        
        result = await cache_get("timeout_key", mock_context)
        
        # Should return error response
        assert result["success"] is False
        assert result["status"] == "error"
        assert "timeout" in result["message"].lower()


class TestMCPServerIntegration:
    """Test MCP server integration with cache layers."""
    
    @pytest.mark.asyncio
    async def test_cross_cache_consistency(self):
        """Test consistency across cache layers."""
        # Create mock caches
        predictive_cache = Mock()
        semantic_cache = Mock()
        vector_cache = Mock()
        global_cache = Mock()
        vector_diary = Mock()
        
        # Set up mock responses
        predictive_cache.get_layer.return_value = CacheLayer.PREDICTIVE
        semantic_cache.get_layer.return_value = CacheLayer.SEMANTIC
        vector_cache.get_layer.return_value = CacheLayer.VECTOR
        global_cache.get_layer.return_value = CacheLayer.GLOBAL
        vector_diary.get_layer.return_value = CacheLayer.VECTOR_DIARY
        
        # Mock successful operations
        predictive_cache.get = AsyncMock(return_value=Mock(status=CacheStatus.HIT, entry=Mock(value="predictive_value")))
        semantic_cache.get = AsyncMock(return_value=Mock(status=CacheStatus.HIT, entry=Mock(value="semantic_value")))
        vector_cache.get = AsyncMock(return_value=Mock(status=CacheStatus.HIT, entry=Mock(value="vector_value")))
        global_cache.get = AsyncMock(return_value=Mock(status=CacheStatus.HIT, entry=Mock(value="global_value")))
        vector_diary.get = AsyncMock(return_value=Mock(status=CacheStatus.HIT, entry=Mock(value="diary_value")))
        
        # Create cache tools and register all caches
        cache_tools = CacheMCPTools()
        cache_tools.register_cache(predictive_cache)
        cache_tools.register_cache(semantic_cache)
        cache_tools.register_cache(vector_cache)
        cache_tools.register_cache(global_cache)
        cache_tools.register_cache(vector_diary)
        
        # Test cross-layer operations
        result = await cache_tools.get("test_key")
        
        # Should have tried all layers
        predictive_cache.get.assert_called_once()
        semantic_cache.get.assert_called_once()
        vector_cache.get.assert_called_once()
        global_cache.get.assert_called_once()
        vector_diary.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_routing_logic(self):
        """Test cache routing logic."""
        # Create mock caches
        predictive_cache = Mock()
        semantic_cache = Mock()
        vector_cache = Mock()
        global_cache = Mock()
        vector_diary = Mock()
        
        # Set up mock responses
        predictive_cache.get_layer.return_value = CacheLayer.PREDICTIVE
        semantic_cache.get_layer.return_value = CacheLayer.SEMANTIC
        vector_cache.get_layer.return_value = CacheLayer.VECTOR
        global_cache.get_layer.return_value = CacheLayer.GLOBAL
        vector_diary.get_layer.return_value = CacheLayer.VECTOR_DIARY
        
        # Mock successful operations
        predictive_cache.get = AsyncMock(return_value=Mock(status=CacheStatus.HIT, entry=Mock(value="predictive_value")))
        semantic_cache.get = AsyncMock(return_value=Mock(status=CacheStatus.MISS))
        vector_cache.get = AsyncMock(return_value=Mock(status=CacheStatus.MISS))
        global_cache.get = AsyncMock(return_value=Mock(status=CacheStatus.MISS))
        vector_diary.get = AsyncMock(return_value=Mock(status=CacheStatus.MISS))
        
        # Create cache tools and register all caches
        cache_tools = CacheMCPTools()
        cache_tools.register_cache(predictive_cache)
        cache_tools.register_cache(semantic_cache)
        cache_tools.register_cache(vector_cache)
        cache_tools.register_cache(global_cache)
        cache_tools.register_cache(vector_diary)
        
        # Test predictive routing
        result = await cache_tools.get("predict something")
        
        # Should have hit predictive cache first
        predictive_cache.get.assert_called_once()
        assert result.success is True
        assert result.data == "predictive_value"
    
    @pytest.mark.asyncio
    async def test_cache_fallback_mechanism(self):
        """Test cache fallback mechanism."""
        # Create mock caches
        primary_cache = Mock()
        fallback_cache = Mock()
        
        # Set up mock responses
        primary_cache.get_layer.return_value = CacheLayer.SEMANTIC
        fallback_cache.get_layer.return_value = CacheLayer.GLOBAL
        
        # Mock primary cache miss, fallback cache hit
        primary_cache.get = AsyncMock(return_value=Mock(status=CacheStatus.MISS))
        fallback_cache.get = AsyncMock(return_value=Mock(status=CacheStatus.HIT, entry=Mock(value="fallback_value")))
        
        # Create cache tools and register caches
        cache_tools = CacheMCPTools()
        cache_tools.register_cache(primary_cache)
        cache_tools.register_cache(fallback_cache)
        
        # Test fallback behavior
        result = await cache_tools.get("test_key")
        
        # Should have tried primary first, then fallback
        primary_cache.get.assert_called_once()
        fallback_cache.get.assert_called_once()
        assert result.success is True
        assert result.data == "fallback_value"
        assert result.cache_layer == CacheLayer.GLOBAL


class TestMCPServerPerformance:
    """Test MCP server performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        # Create mock cache
        mock_cache = Mock()
        mock_cache.get_layer.return_value = CacheLayer.SEMANTIC
        mock_cache.get = AsyncMock(return_value=Mock(status=CacheStatus.HIT, entry=Mock(value="test_value")))
        
        # Create cache tools
        cache_tools = CacheMCPTools()
        cache_tools.register_cache(mock_cache)
        
        # Create multiple concurrent requests
        async def make_request(i):
            return await cache_tools.get(f"key_{i}")
        
        requests = [make_request(i) for i in range(10)]
        results = await asyncio.gather(*requests)
        
        # All requests should succeed
        assert all(result.success for result in results)
        
        # Cache should have been called for each request
        assert mock_cache.get.call_count == 10
    
    @pytest.mark.asyncio
    async def test_request_timeout_handling(self):
        """Test request timeout handling."""
        # Create mock cache with slow response
        mock_cache = Mock()
        mock_cache.get_layer.return_value = CacheLayer.SEMANTIC
        mock_cache.get = AsyncMock(
            side_effect=asyncio.sleep(0.1) or Mock(status=CacheStatus.HIT, entry=Mock(value="slow_value"))
        )
        
        # Create cache tools
        cache_tools = CacheMCPTools()
        cache_tools.register_cache(mock_cache)
        
        # Test with timeout
        result = await cache_tools.get("slow_key", timeout=0.05)
        
        # Should timeout and return error
        assert result.success is False
        assert result.status == CacheStatus.ERROR
    
    @pytest.mark.asyncio
    async def test_memory_usage_monitoring(self):
        """Test memory usage monitoring."""
        # Create cache tools
        cache_tools = CacheMCPTools()
        
        # Add some data to simulate memory usage
        cache_tools.request_count = 1000
        cache_tools.hit_count = 800
        cache_tools.miss_count = 150
        cache_tools.error_count = 50
        
        # Get performance metrics
        metrics = cache_tools.get_performance_metrics()
        
        # Should include memory-related metrics
        assert "total_requests" in metrics
        assert "hit_rate" in metrics
        assert "error_rate" in metrics
        assert "cache_layers" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])