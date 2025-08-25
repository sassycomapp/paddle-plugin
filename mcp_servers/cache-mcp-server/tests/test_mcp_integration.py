"""
Integration tests for MCP server functionality.

This module contains integration tests for the MCP server and tools.

Author: KiloCode
License: Apache 2.0
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from fastmcp import FastMCP, Context

from src.mcp.tools import CacheMCPTools, CacheRequest, CacheResponse
from src.mcp.server import mcp_server_lifespan, MCPServerContext
from src.core.base_cache import CacheLayer, CacheStatus
from src.cache_layers.predictive_cache import PredictiveCache
from src.cache_layers.semantic_cache import SemanticCache


class TestCacheMCPTools:
    """Test MCP tools for cache management."""
    
    @pytest.fixture
    def cache_tools(self):
        """Create cache tools instance."""
        return CacheMCPTools()
    
    @pytest.fixture
    def mock_cache(self):
        """Create a mock cache instance."""
        cache = Mock()
        cache.get_layer.return_value = CacheLayer.SEMANTIC
        cache.get = AsyncMock(return_value=Mock(status=CacheStatus.HIT, entry=Mock(value="test_value")))
        cache.set = AsyncMock(return_value=True)
        cache.delete = AsyncMock(return_value=True)
        cache.clear = AsyncMock(return_value=True)
        cache.get_stats = AsyncMock(return_value={"total_entries": 10})
        return cache
    
    def test_cache_tools_initialization(self, cache_tools):
        """Test cache tools initialization."""
        assert cache_tools.caches == {}
        assert cache_tools.request_count == 0
        assert cache_tools.hit_count == 0
        assert cache_tools.miss_count == 0
        assert cache_tools.error_count == 0
    
    def test_register_cache(self, cache_tools, mock_cache):
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


class TestMCPServer:
    """Test MCP server functionality."""
    
    @pytest.mark.asyncio
    async def test_server_lifespan_initialization(self):
        """Test server lifespan initialization."""
        with patch('src.mcp.server.CacheMCPTools') as mock_tools_class:
            mock_tools = Mock()
            mock_tools.initialize_all.return_value = True
            mock_tools_class.return_value = mock_tools
            
            async with mcp_server_lifespan(None) as context:
                assert isinstance(context, MCPServerContext)
                assert context.cache_tools == mock_tools
                assert "caches" in context.__dict__
    
    @pytest.mark.asyncio
    async def test_server_lifespan_initialization_failure(self):
        """Test server lifespan initialization failure."""
        with patch('src.mcp.server.CacheMCPTools') as mock_tools_class:
            mock_tools = Mock()
            mock_tools.initialize_all.return_value = False
            mock_tools_class.return_value = mock_tools
            
            with pytest.raises(RuntimeError):
                async with mcp_server_lifespan(None) as context:
                    pass


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
        
        # Import the tool function
        from src.mcp.server import cache_get
        
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
        
        # Import the tool function
        from src.mcp.server import cache_set
        
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
        
        # Import the tool function
        from src.mcp.server import cache_delete
        
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
        
        # Import the tool function
        from src.mcp.server import cache_search
        
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
        
        # Import the tool function
        from src.mcp.server import cache_stats
        
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
        
        # Import the tool function
        from src.mcp.server import cache_clear
        
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
        
        # Import the tool function
        from src.mcp.server import predictive_cache_predict
        
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
        
        # Import the tool function
        from src.mcp.server import semantic_cache_similar
        
        result = await semantic_cache_similar("test query", mock_context)
        
        assert result["success"] is True
        assert result["status"] == "ok"
        assert len(result["data"]) == 2
        assert result["data"][0]["similarity"] == 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])