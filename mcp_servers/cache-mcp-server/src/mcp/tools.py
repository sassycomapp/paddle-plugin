"""
MCP Tools for Cache Management System

This module implements MCP tools for each cache layer, providing
exposure through the MCP protocol.

Author: KiloCode
License: Apache 2.0
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ..core.base_cache import BaseCache, CacheLayer, CacheStatus
from ..cache_layers.predictive_cache import PredictiveCache
from ..cache_layers.semantic_cache import SemanticCache
from ..cache_layers.vector_cache import VectorCache
from ..cache_layers.global_cache import GlobalCache
from ..cache_layers.vector_diary import VectorDiary

logger = logging.getLogger(__name__)


@dataclass
class CacheRequest:
    """Represents a cache request."""
    layer: CacheLayer
    key: str
    value: Optional[Any] = None
    ttl_seconds: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None


@dataclass
class CacheResponse:
    """Represents a cache response."""
    success: bool
    status: CacheStatus
    message: str
    data: Optional[Any] = None
    execution_time_ms: Optional[float] = None
    cache_layer: Optional[CacheLayer] = None


class CacheMCPTools:
    """
    MCP Tools for the cache management system.
    
    This class provides MCP tools for each cache layer and handles
    routing between different cache layers.
    """
    
    def __init__(self):
        """Initialize the cache MCP tools."""
        self.logger = logging.getLogger(__name__)
        
        # Cache layer instances
        self.caches: Dict[CacheLayer, BaseCache] = {}
        
        # Cache routing configuration
        self.routing_enabled = True
        self.fallback_order = [
            CacheLayer.PREDICTIVE,
            CacheLayer.SEMANTIC,
            CacheLayer.VECTOR,
            CacheLayer.GLOBAL,
            CacheLayer.VECTOR_DIARY
        ]
        
        # Performance tracking
        self.request_count = 0
        self.hit_count = 0
        self.miss_count = 0
        self.error_count = 0
        
        # Cache hit tracking
        self.cache_hits: Dict[CacheLayer, int] = {layer: 0 for layer in CacheLayer}
        self.cache_misses: Dict[CacheLayer, int] = {layer: 0 for layer in CacheLayer}
    
    def register_cache(self, cache: BaseCache):
        """
        Register a cache instance.
        
        Args:
            cache: Cache instance to register
        """
        self.caches[cache.get_layer()] = cache
        self.logger.info(f"Registered cache layer: {cache.get_layer()}")
    
    async def initialize_all(self) -> bool:
        """
        Initialize all registered cache layers.
        
        Returns:
            True if all caches initialized successfully, False otherwise
        """
        try:
            self.logger.info("Initializing all cache layers...")
            
            success_count = 0
            for layer, cache in self.caches.items():
                try:
                    result = await cache.initialize()
                    if result:
                        success_count += 1
                        self.logger.info(f"Initialized cache layer: {layer}")
                    else:
                        self.logger.error(f"Failed to initialize cache layer: {layer}")
                except Exception as e:
                    self.logger.error(f"Error initializing cache layer {layer}: {e}")
            
            if success_count == len(self.caches):
                self.logger.info("All cache layers initialized successfully")
                return True
            else:
                self.logger.warning(f"Only {success_count}/{len(self.caches)} cache layers initialized successfully")
                return False
                
        except Exception as e:
            self.logger.error(f"Error initializing cache layers: {e}")
            return False
    
    async def get(self, key: str, layer: Optional[CacheLayer] = None) -> CacheResponse:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key to retrieve
            layer: Optional specific cache layer to use
            
        Returns:
            CacheResponse containing the result
        """
        start_time = asyncio.get_event_loop().time()
        self.request_count += 1
        
        try:
            # Determine which cache layer(s) to use
            if layer:
                cache_layers = [layer]
            elif self.routing_enabled:
                # Use routing logic
                cache_layers = self._determine_cache_layers(key)
            else:
                # Default to semantic cache
                cache_layers = [CacheLayer.SEMANTIC]
            
            # Try each cache layer in order
            for cache_layer in cache_layers:
                if cache_layer in self.caches:
                    cache = self.caches[cache_layer]
                    
                    try:
                        result = await cache.get(key)
                        
                        if result.status == CacheStatus.HIT:
                            self.hit_count += 1
                            self.cache_hits[cache_layer] += 1
                            
                            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
                            
                            return CacheResponse(
                                success=True,
                                status=result.status,
                                message=f"Cache hit in {cache_layer}",
                                data=result.entry.value if result.entry else None,
                                execution_time_ms=execution_time,
                                cache_layer=cache_layer
                            )
                        
                        elif result.status == CacheStatus.MISS:
                            self.miss_count += 1
                            self.cache_misses[cache_layer] += 1
                            
                        elif result.status == CacheStatus.EXPIRED:
                            self.miss_count += 1
                            self.cache_misses[cache_layer] += 1
                            
                    except Exception as e:
                        self.logger.error(f"Error getting from cache {cache_layer}: {e}")
                        self.error_count += 1
                        continue
            
            # All cache layers missed
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            return CacheResponse(
                success=False,
                status=CacheStatus.MISS,
                message="Cache miss in all layers",
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Error in get operation: {e}")
            self.error_count += 1
            
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            return CacheResponse(
                success=False,
                status=CacheStatus.ERROR,
                message=f"Error: {str(e)}",
                execution_time_ms=execution_time
            )
    
    async def set(self, key: str, value: Any, 
                 layer: Optional[CacheLayer] = None,
                 ttl_seconds: Optional[int] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 embedding: Optional[List[float]] = None) -> CacheResponse:
        """
        Store a value in the cache.
        
        Args:
            key: Cache key
            value: Value to store
            layer: Optional specific cache layer to use
            ttl_seconds: Optional time-to-live in seconds
            metadata: Optional metadata dictionary
            embedding: Optional embedding vector
            
        Returns:
            CacheResponse containing the result
        """
        start_time = asyncio.get_event_loop().time()
        self.request_count += 1
        
        try:
            # Determine which cache layer(s) to use
            if layer:
                cache_layers = [layer]
            elif self.routing_enabled:
                # Use routing logic
                cache_layers = self._determine_cache_layers(key, operation="set")
            else:
                # Default to semantic cache
                cache_layers = [CacheLayer.SEMANTIC]
            
            # Store in each cache layer
            success_count = 0
            for cache_layer in cache_layers:
                if cache_layer in self.caches:
                    cache = self.caches[cache_layer]
                    
                    try:
                        result = await cache.set(
                            key=key,
                            value=value,
                            ttl_seconds=ttl_seconds,
                            metadata=metadata,
                            embedding=embedding
                        )
                        
                        if result:
                            success_count += 1
                            
                    except Exception as e:
                        self.logger.error(f"Error setting in cache {cache_layer}: {e}")
                        self.error_count += 1
                        continue
            
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            if success_count > 0:
                return CacheResponse(
                    success=True,
                    status=CacheStatus.HIT,
                    message=f"Successfully stored in {success_count} cache layer(s)",
                    execution_time_ms=execution_time
                )
            else:
                return CacheResponse(
                    success=False,
                    status=CacheStatus.ERROR,
                    message="Failed to store in any cache layer",
                    execution_time_ms=execution_time
                )
            
        except Exception as e:
            self.logger.error(f"Error in set operation: {e}")
            self.error_count += 1
            
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            return CacheResponse(
                success=False,
                status=CacheStatus.ERROR,
                message=f"Error: {str(e)}",
                execution_time_ms=execution_time
            )
    
    async def delete(self, key: str, layer: Optional[CacheLayer] = None) -> CacheResponse:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key to delete
            layer: Optional specific cache layer to use
            
        Returns:
            CacheResponse containing the result
        """
        start_time = asyncio.get_event_loop().time()
        self.request_count += 1
        
        try:
            # Determine which cache layer(s) to use
            if layer:
                cache_layers = [layer]
            elif self.routing_enabled:
                # Use routing logic
                cache_layers = self._determine_cache_layers(key, operation="delete")
            else:
                # Default to semantic cache
                cache_layers = [CacheLayer.SEMANTIC]
            
            # Delete from each cache layer
            success_count = 0
            for cache_layer in cache_layers:
                if cache_layer in self.caches:
                    cache = self.caches[cache_layer]
                    
                    try:
                        result = await cache.delete(key)
                        
                        if result:
                            success_count += 1
                            
                    except Exception as e:
                        self.logger.error(f"Error deleting from cache {cache_layer}: {e}")
                        self.error_count += 1
                        continue
            
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            if success_count > 0:
                return CacheResponse(
                    success=True,
                    status=CacheStatus.HIT,
                    message=f"Successfully deleted from {success_count} cache layer(s)",
                    execution_time_ms=execution_time
                )
            else:
                return CacheResponse(
                    success=False,
                    status=CacheStatus.ERROR,
                    message="Failed to delete from any cache layer",
                    execution_time_ms=execution_time
                )
            
        except Exception as e:
            self.logger.error(f"Error in delete operation: {e}")
            self.error_count += 1
            
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            return CacheResponse(
                success=False,
                status=CacheStatus.ERROR,
                message=f"Error: {str(e)}",
                execution_time_ms=execution_time
            )
    
    async def search(self, query: str, layer: Optional[CacheLayer] = None,
                    n_results: int = 5, min_similarity: float = 0.0) -> CacheResponse:
        """
        Search for values in the cache.
        
        Args:
            query: Search query
            layer: Optional specific cache layer to use
            n_results: Maximum number of results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            CacheResponse containing search results
        """
        start_time = asyncio.get_event_loop().time()
        self.request_count += 1
        
        try:
            # Determine which cache layer(s) to use
            if layer:
                cache_layers = [layer]
            elif self.routing_enabled:
                # Use routing logic
                cache_layers = self._determine_cache_layers(query, operation="search")
            else:
                # Default to semantic cache
                cache_layers = [CacheLayer.SEMANTIC]
            
            # Search in each cache layer
            all_results = []
            for cache_layer in cache_layers:
                if cache_layer in self.caches:
                    cache = self.caches[cache_layer]
                    
                    try:
                        # Skip search for now - only VectorCache has search but it's not implemented yet
                        # TODO: Implement search method in VectorCache
                        pass
                                
                    except Exception as e:
                        self.logger.error(f"Error searching in cache {cache_layer}: {e}")
                        self.error_count += 1
                        continue
            
            # Remove duplicates and sort by relevance
            unique_results = {}
            for result in all_results:
                key = result.get('key') or result.get('content_hash')
                if key and key not in unique_results:
                    unique_results[key] = result
            
            # Sort by relevance (assuming higher similarity is better)
            sorted_results = sorted(
                unique_results.values(),
                key=lambda x: x.get('similarity_score', 0.0),
                reverse=True
            )
            
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return CacheResponse(
                success=True,
                status=CacheStatus.HIT,
                message=f"Found {len(sorted_results)} results",
                data=sorted_results[:n_results],
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Error in search operation: {e}")
            self.error_count += 1
            
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            return CacheResponse(
                success=False,
                status=CacheStatus.ERROR,
                message=f"Error: {str(e)}",
                execution_time_ms=execution_time
            )
    
    async def get_stats(self) -> CacheResponse:
        """
        Get overall cache statistics.
        
        Returns:
            CacheResponse containing cache statistics
        """
        try:
            stats = {
                "total_requests": self.request_count,
                "total_hits": self.hit_count,
                "total_misses": self.miss_count,
                "total_errors": self.error_count,
                "hit_rate": self.hit_count / max(self.request_count, 1),
                "cache_layers": {}
            }
            
            # Get stats for each cache layer
            for layer, cache in self.caches.items():
                try:
                    layer_stats = await cache.get_stats()
                    stats["cache_layers"][layer.value] = layer_stats
                except Exception as e:
                    self.logger.error(f"Error getting stats for cache {layer}: {e}")
                    stats["cache_layers"][layer.value] = {"error": str(e)}
            
            return CacheResponse(
                success=True,
                status=CacheStatus.HIT,
                message="Cache statistics retrieved",
                data=stats
            )
            
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return CacheResponse(
                success=False,
                status=CacheStatus.ERROR,
                message=f"Error: {str(e)}"
            )
    
    async def clear_cache(self, layer: Optional[CacheLayer] = None) -> CacheResponse:
        """
        Clear the cache.
        
        Args:
            layer: Optional specific cache layer to clear
            
        Returns:
            CacheResponse containing the result
        """
        try:
            # Determine which cache layer(s) to clear
            if layer:
                cache_layers = [layer]
            else:
                cache_layers = list(self.caches.keys())
            
            # Clear each cache layer
            success_count = 0
            for cache_layer in cache_layers:
                if cache_layer in self.caches:
                    cache = self.caches[cache_layer]
                    
                    try:
                        result = await cache.clear()
                        
                        if result:
                            success_count += 1
                            
                    except Exception as e:
                        self.logger.error(f"Error clearing cache {cache_layer}: {e}")
                        self.error_count += 1
                        continue
            
            if success_count > 0:
                return CacheResponse(
                    success=True,
                    status=CacheStatus.HIT,
                    message=f"Successfully cleared {success_count} cache layer(s)"
                )
            else:
                return CacheResponse(
                    success=False,
                    status=CacheStatus.ERROR,
                    message="Failed to clear any cache layer"
                )
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            return CacheResponse(
                success=False,
                status=CacheStatus.ERROR,
                message=f"Error: {str(e)}"
            )
    
    def _determine_cache_layers(self, key: str, operation: str = "get") -> List[CacheLayer]:
        """
        Determine which cache layers to use based on routing logic.
        
        Args:
            key: Cache key or query
            operation: Type of operation (get, set, delete, search)
            
        Returns:
            List of cache layers to use
        """
        try:
            # Simple routing logic based on key characteristics
            key_lower = str(key).lower()
            
            # Predictive cache for certain patterns
            if any(pattern in key_lower for pattern in ["predict", "forecast", "anticipate", "expect"]):
                return [CacheLayer.PREDICTIVE]
            
            # Semantic cache for general queries
            if operation in ["get", "search"] and len(key) > 10:
                return [CacheLayer.SEMANTIC]
            
            # Vector cache for embedding-based operations
            if operation in ["search"] or "embedding" in key_lower:
                return [CacheLayer.VECTOR]
            
            # Global cache for knowledge content
            if any(pattern in key_lower for pattern in ["knowledge", "fact", "information", "reference"]):
                return [CacheLayer.GLOBAL]
            
            # Vector diary for context content
            if any(pattern in key_lower for pattern in ["conversation", "chat", "dialog", "context"]):
                return [CacheLayer.VECTOR_DIARY]
            
            # Default fallback order
            return self.fallback_order
            
        except Exception as e:
            self.logger.error(f"Error determining cache layers: {e}")
            return self.fallback_order
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the cache system.
        
        Returns:
            Dictionary containing performance metrics
        """
        return {
            "total_requests": self.request_count,
            "total_hits": self.hit_count,
            "total_misses": self.miss_count,
            "total_errors": self.error_count,
            "hit_rate": self.hit_count / max(self.request_count, 1),
            "cache_hits": dict(self.cache_hits),
            "cache_misses": dict(self.cache_misses),
            "cache_layers": len(self.caches),
            "routing_enabled": self.routing_enabled
        }