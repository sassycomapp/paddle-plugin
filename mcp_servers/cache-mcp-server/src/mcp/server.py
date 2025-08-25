"""
MCP Server for Cache Management System

This module implements the MCP server that exposes cache management
tools through the MCP protocol.

Author: KiloCode
License: Apache 2.0
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from fastmcp import FastMCP, Context
from mcp.types import TextContent

from .tools import CacheMCPTools
from ..core.config import CacheConfig
from ..cache_layers.predictive_cache import PredictiveCache, PredictiveCacheConfig
from ..cache_layers.semantic_cache import SemanticCache, SemanticCacheConfig
from ..cache_layers.vector_cache import VectorCache, VectorCacheConfig
from ..cache_layers.global_cache import GlobalCache, GlobalCacheConfig
from ..cache_layers.vector_diary import VectorDiary, VectorDiaryConfig

logger = logging.getLogger(__name__)


@dataclass
class MCPServerContext:
    """Application context for the MCP server with all required components."""
    cache_tools: CacheMCPTools
    caches: Dict[str, Any]  # Cache instances


async def mcp_server_lifespan(server: FastMCP) -> MCPServerContext:
    """
    Manage MCP server lifecycle with proper resource initialization and cleanup.
    
    Args:
        server: FastMCP server instance
        
    Returns:
        MCPServerContext with initialized components
    """
    logger.info("Initializing Cache MCP Server components...")
    
    try:
        # Initialize cache tools
        cache_tools = CacheMCPTools()
        
        # Initialize cache configurations
        predictive_config = PredictiveCacheConfig(
            cache_ttl_seconds=300,  # 5 minutes
            max_cache_size=1000,
            prediction_window=60,   # 1 minute
            confidence_threshold=0.7
        )
        
        semantic_config = SemanticCacheConfig(
            cache_ttl_seconds=3600,  # 1 hour
            max_cache_size=2000,
            similarity_threshold=0.8,
            embedding_dimension=384
        )
        
        vector_config = VectorCacheConfig(
            cache_ttl_seconds=1800,  # 30 minutes
            max_cache_size=1500,
            similarity_threshold=0.75,
            reranking_enabled=True,
            context_window_size=10
        )
        
        global_config = GlobalCacheConfig(
            cache_ttl_seconds=86400,  # 24 hours
            max_cache_size=5000,
            knowledge_base_enabled=True,
            fallback_enabled=True,
            consolidation_enabled=True
        )
        
        vector_diary_config = VectorDiaryConfig(
            cache_ttl_seconds=2592000,  # 30 days
            max_cache_size=10000,
            analysis_interval=3600,     # 1 hour
            min_insight_confidence=0.6,
            max_memory_age=90           # 90 days
        )
        
        # Initialize cache instances
        predictive_cache = PredictiveCache("predictive", predictive_config)
        semantic_cache = SemanticCache("semantic", semantic_config)
        vector_cache = VectorCache("vector", vector_config)
        global_cache = GlobalCache("global", global_config)
        vector_diary = VectorDiary("vector_diary", vector_diary_config)
        
        # Register caches
        cache_tools.register_cache(predictive_cache)
        cache_tools.register_cache(semantic_cache)
        cache_tools.register_cache(vector_cache)
        cache_tools.register_cache(global_cache)
        cache_tools.register_cache(vector_diary)
        
        # Initialize all caches
        success = await cache_tools.initialize_all()
        if not success:
            logger.error("Failed to initialize all cache layers")
            raise RuntimeError("Cache initialization failed")
        
        logger.info("Cache MCP Server initialized successfully")
        
        return MCPServerContext(
            cache_tools=cache_tools,
            caches={
                "predictive": predictive_cache,
                "semantic": semantic_cache,
                "vector": vector_cache,
                "global": global_cache,
                "vector_diary": vector_diary
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize MCP server: {e}")
        raise


# Create FastMCP server instance
mcp = FastMCP(
    name="Cache MCP Server",
    host="0.0.0.0",
    port=8001,
    lifespan=mcp_server_lifespan,
    stateless_http=True
)


# =============================================================================
# CORE CACHE OPERATIONS
# =============================================================================

@mcp.tool()
async def cache_get(
    key: str,
    ctx: Context,
    layer: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get a value from the cache.
    
    Args:
        key: Cache key to retrieve
        layer: Optional specific cache layer to use (predictive, semantic, vector, global, vector_diary)
    
    Returns:
        Dictionary with cache result and metadata
    """
    try:
        cache_tools = ctx.request_context.lifespan_context.cache_tools
        
        # Parse layer parameter
        cache_layer = None
        if layer:
            cache_layer = layer.lower()
        
        # Get from cache
        result = await cache_tools.get(key, cache_layer)
        
        return {
            "success": result.success,
            "status": result.status.value,
            "message": result.message,
            "data": result.data,
            "execution_time_ms": result.execution_time_ms,
            "cache_layer": result.cache_layer.value if result.cache_layer else None
        }
        
    except Exception as e:
        logger.error(f"Error in cache_get: {e}")
        return {
            "success": False,
            "status": "error",
            "message": f"Failed to get from cache: {str(e)}",
            "data": None,
            "execution_time_ms": None,
            "cache_layer": None
        }


@mcp.tool()
async def cache_set(
    key: str,
    value: Any,
    ctx: Context,
    layer: Optional[str] = None,
    ttl_seconds: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Store a value in the cache.
    
    Args:
        key: Cache key
        value: Value to store
        layer: Optional specific cache layer to use
        ttl_seconds: Optional time-to-live in seconds
        metadata: Optional metadata dictionary
    
    Returns:
        Dictionary with cache result and metadata
    """
    try:
        cache_tools = ctx.request_context.lifespan_context.cache_tools
        
        # Parse layer parameter
        cache_layer = None
        if layer:
            cache_layer = layer.lower()
        
        # Store in cache
        result = await cache_tools.set(
            key=key,
            value=value,
            layer=cache_layer,
            ttl_seconds=ttl_seconds,
            metadata=metadata
        )
        
        return {
            "success": result.success,
            "status": result.status.value,
            "message": result.message,
            "execution_time_ms": result.execution_time_ms
        }
        
    except Exception as e:
        logger.error(f"Error in cache_set: {e}")
        return {
            "success": False,
            "status": "error",
            "message": f"Failed to store in cache: {str(e)}",
            "execution_time_ms": None
        }


@mcp.tool()
async def cache_delete(
    key: str,
    ctx: Context,
    layer: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete a value from the cache.
    
    Args:
        key: Cache key to delete
        layer: Optional specific cache layer to use
    
    Returns:
        Dictionary with cache result and metadata
    """
    try:
        cache_tools = ctx.request_context.lifespan_context.cache_tools
        
        # Parse layer parameter
        cache_layer = None
        if layer:
            cache_layer = layer.lower()
        
        # Delete from cache
        result = await cache_tools.delete(key, cache_layer)
        
        return {
            "success": result.success,
            "status": result.status.value,
            "message": result.message,
            "execution_time_ms": result.execution_time_ms
        }
        
    except Exception as e:
        logger.error(f"Error in cache_delete: {e}")
        return {
            "success": False,
            "status": "error",
            "message": f"Failed to delete from cache: {str(e)}",
            "execution_time_ms": None
        }


@mcp.tool()
async def cache_search(
    query: str,
    ctx: Context,
    layer: Optional[str] = None,
    n_results: int = 5,
    min_similarity: float = 0.0
) -> Dict[str, Any]:
    """
    Search for values in the cache.
    
    Args:
        query: Search query
        layer: Optional specific cache layer to use
        n_results: Maximum number of results to return
        min_similarity: Minimum similarity threshold
    
    Returns:
        Dictionary with search results
    """
    try:
        cache_tools = ctx.request_context.lifespan_context.cache_tools
        
        # Parse layer parameter
        cache_layer = None
        if layer:
            cache_layer = layer.lower()
        
        # Search in cache
        result = await cache_tools.search(
            query=query,
            layer=cache_layer,
            n_results=n_results,
            min_similarity=min_similarity
        )
        
        return {
            "success": result.success,
            "status": result.status.value,
            "message": result.message,
            "data": result.data,
            "execution_time_ms": result.execution_time_ms
        }
        
    except Exception as e:
        logger.error(f"Error in cache_search: {e}")
        return {
            "success": False,
            "status": "error",
            "message": f"Failed to search cache: {str(e)}",
            "data": None,
            "execution_time_ms": None
        }


# =============================================================================
# CACHE MANAGEMENT TOOLS
# =============================================================================

@mcp.tool()
async def cache_stats(ctx: Context) -> Dict[str, Any]:
    """
    Get overall cache statistics.
    
    Returns:
        Dictionary with cache statistics
    """
    try:
        cache_tools = ctx.request_context.lifespan_context.cache_tools
        
        # Get cache statistics
        result = await cache_tools.get_stats()
        
        return {
            "success": result.success,
            "status": result.status.value,
            "message": result.message,
            "data": result.data
        }
        
    except Exception as e:
        logger.error(f"Error in cache_stats: {e}")
        return {
            "success": False,
            "status": "error",
            "message": f"Failed to get cache stats: {str(e)}",
            "data": None
        }


@mcp.tool()
async def cache_clear(
    ctx: Context,
    layer: Optional[str] = None
) -> Dict[str, Any]:
    """
    Clear the cache.
    
    Args:
        layer: Optional specific cache layer to clear
    
    Returns:
        Dictionary with cache result
    """
    try:
        cache_tools = ctx.request_context.lifespan_context.cache_tools
        
        # Parse layer parameter
        cache_layer = None
        if layer:
            cache_layer = layer.lower()
        
        # Clear cache
        result = await cache_tools.clear_cache(cache_layer)
        
        return {
            "success": result.success,
            "status": result.status.value,
            "message": result.message
        }
        
    except Exception as e:
        logger.error(f"Error in cache_clear: {e}")
        return {
            "success": False,
            "status": "error",
            "message": f"Failed to clear cache: {str(e)}"
        }


@mcp.tool()
async def cache_performance(ctx: Context) -> Dict[str, Any]:
    """
    Get cache performance metrics.
    
    Returns:
        Dictionary with performance metrics
    """
    try:
        cache_tools = ctx.request_context.lifespan_context.cache_tools
        
        # Get performance metrics
        metrics = cache_tools.get_performance_metrics()
        
        return {
            "success": True,
            "status": "ok",
            "message": "Performance metrics retrieved",
            "data": metrics
        }
        
    except Exception as e:
        logger.error(f"Error in cache_performance: {e}")
        return {
            "success": False,
            "status": "error",
            "message": f"Failed to get performance metrics: {str(e)}",
            "data": None
        }


# =============================================================================
# PREDICTIVE CACHE TOOLS
# =============================================================================

@mcp.tool()
async def predictive_cache_predict(
    query: str,
    ctx: Context,
    n_predictions: int = 3
) -> Dict[str, Any]:
    """
    Get predictions from the predictive cache.
    
    Args:
        query: Query for prediction
        n_predictions: Number of predictions to return
    
    Returns:
        Dictionary with predictions
    """
    try:
        caches = ctx.request_context.lifespan_context.caches
        predictive_cache = caches["predictive"]
        
        # Get predictions
        predictions = await predictive_cache.predict(query, n_predictions)
        
        return {
            "success": True,
            "status": "ok",
            "message": "Predictions retrieved",
            "data": predictions
        }
        
    except Exception as e:
        logger.error(f"Error in predictive_cache_predict: {e}")
        return {
            "success": False,
            "status": "error",
            "message": f"Failed to get predictions: {str(e)}",
            "data": None
        }


# =============================================================================
# SEMANTIC CACHE TOOLS
# =============================================================================

@mcp.tool()
async def semantic_cache_similar(
    query: str,
    ctx: Context,
    n_results: int = 5,
    min_similarity: float = 0.7
) -> Dict[str, Any]:
    """
    Find similar entries in the semantic cache.
    
    Args:
        query: Query for similarity search
        n_results: Number of results to return
        min_similarity: Minimum similarity threshold
    
    Returns:
        Dictionary with similar entries
    """
    try:
        caches = ctx.request_context.lifespan_context.caches
        semantic_cache = caches["semantic"]
        
        # Find similar entries
        similar_entries = await semantic_cache.find_similar(
            query=query,
            n_results=n_results,
            min_similarity=min_similarity
        )
        
        return {
            "success": True,
            "status": "ok",
            "message": "Similar entries retrieved",
            "data": similar_entries
        }
        
    except Exception as e:
        logger.error(f"Error in semantic_cache_similar: {e}")
        return {
            "success": False,
            "status": "error",
            "message": f"Failed to find similar entries: {str(e)}",
            "data": None
        }


# =============================================================================
# VECTOR CACHE TOOLS
# =============================================================================

@mcp.tool()
async def vector_cache_select_context(
    query: str,
    ctx: Context,
    n_context: int = 5,
    min_similarity: float = 0.6
) -> Dict[str, Any]:
    """
    Select context from the vector cache.
    
    Args:
        query: Query for context selection
        n_context: Number of context elements to return
        min_similarity: Minimum similarity threshold
    
    Returns:
        Dictionary with selected context
    """
    try:
        caches = ctx.request_context.lifespan_context.caches
        vector_cache = caches["vector"]
        
        # Select context
        context = await vector_cache.select_context(
            query=query,
            n_context=n_context,
            min_similarity=min_similarity
        )
        
        return {
            "success": True,
            "status": "ok",
            "message": "Context selected",
            "data": context
        }
        
    except Exception as e:
        logger.error(f"Error in vector_cache_select_context: {e}")
        return {
            "success": False,
            "status": "error",
            "message": f"Failed to select context: {str(e)}",
            "data": None
        }


# =============================================================================
# GLOBAL CACHE TOOLS
# =============================================================================

@mcp.tool()
async def global_cache_search_knowledge(
    query: str,
    ctx: Context,
    n_results: int = 5,
    min_relevance: float = 0.5
) -> Dict[str, Any]:
    """
    Search the global knowledge cache.
    
    Args:
        query: Query for knowledge search
        n_results: Number of results to return
        min_relevance: Minimum relevance threshold
    
    Returns:
        Dictionary with knowledge search results
    """
    try:
        caches = ctx.request_context.lifespan_context.caches
        global_cache = caches["global"]
        
        # Search knowledge base
        results = await global_cache.search_knowledge(
            query=query,
            n_results=n_results,
            min_relevance=min_relevance
        )
        
        return {
            "success": True,
            "status": "ok",
            "message": "Knowledge search completed",
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Error in global_cache_search_knowledge: {e}")
        return {
            "success": False,
            "status": "error",
            "message": f"Failed to search knowledge: {str(e)}",
            "data": None
        }


# =============================================================================
# VECTOR DIARY TOOLS
# =============================================================================

@mcp.tool()
async def vector_diary_get_session_memories(
    session_id: str,
    ctx: Context,
    context_type: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Get session memories from the vector diary.
    
    Args:
        session_id: Session ID to retrieve memories for
        context_type: Optional context type filter
        limit: Maximum number of memories to return
    
    Returns:
        Dictionary with session memories
    """
    try:
        caches = ctx.request_context.lifespan_context.caches
        vector_diary = caches["vector_diary"]
        
        # Get session memories
        memories = await vector_diary.get_session_memories(
            session_id=session_id,
            context_type=context_type,
            limit=limit
        )
        
        return {
            "success": True,
            "status": "ok",
            "message": "Session memories retrieved",
            "data": [memory.__dict__ for memory in memories]
        }
        
    except Exception as e:
        logger.error(f"Error in vector_diary_get_session_memories: {e}")
        return {
            "success": False,
            "status": "error",
            "message": f"Failed to get session memories: {str(e)}",
            "data": None
        }


@mcp.tool()
async def vector_diary_generate_insights(
    ctx: Context,
    session_id: Optional[str] = None,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate longitudinal insights from the vector diary.
    
    Args:
        session_id: Optional session ID to focus analysis on
        category: Optional insight category filter
    
    Returns:
        Dictionary with generated insights
    """
    try:
        caches = ctx.request_context.lifespan_context.caches
        vector_diary = caches["vector_diary"]
        
        # Generate insights
        insights = await vector_diary.generate_insights(
            session_id=session_id,
            category=category
        )
        
        return {
            "success": True,
            "status": "ok",
            "message": "Insights generated",
            "data": [insight.__dict__ for insight in insights]
        }
        
    except Exception as e:
        logger.error(f"Error in vector_diary_generate_insights: {e}")
        return {
            "success": False,
            "status": "error",
            "message": f"Failed to generate insights: {str(e)}",
            "data": None
        }


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point for the FastAPI MCP server."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Get port from environment or use default
    port = int(os.getenv("CACHE_MCP_PORT", "8001"))
    host = os.getenv("CACHE_MCP_HOST", "0.0.0.0")
    
    logger.info(f"Starting Cache MCP Server on {host}:{port}")
    
    # Run server
    mcp.run("streamable-http")


if __name__ == "__main__":
    main()