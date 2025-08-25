"""
Vector Cache Implementation (Embedding-Based Context Selector)

This cache layer selects and reranks context elements based on embedding similarity,
providing intelligent context selection and ranking capabilities.

Author: KiloCode
License: Apache 2.0
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import hashlib
import numpy as np

from ..core.base_cache import BaseCache, CacheEntry, CacheResult, CacheStatus, CacheLayer
from ..core.config import VectorCacheConfig
from ..core.utils import CacheUtils

logger = logging.getLogger(__name__)


@dataclass
class ContextElement:
    """Represents a context element with embedding."""
    element_id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    created_at: datetime
    last_accessed: Optional[datetime]
    access_count: int
    relevance_score: float


@dataclass
class RankingResult:
    """Represents a ranking result."""
    element: ContextElement
    relevance_score: float
    diversity_score: float
    recency_score: float
    combined_score: float


class VectorCache(BaseCache):
    """
    Vector Cache that stores and retrieves context elements based on embedding similarity.
    
    This cache layer provides intelligent context selection and ranking capabilities
    using vector embeddings and similarity search.
    """
    
    def __init__(self, name: str, config: VectorCacheConfig):
        """
        Initialize the vector cache.
        
        Args:
            name: Unique name for this cache instance
            config: Vector cache configuration
        """
        super().__init__(name, asdict(config))
        self.config = config
        
        # Internal storage
        self._cache: Dict[str, CacheEntry] = {}
        self._context_elements: Dict[str, ContextElement] = {}
        self._embedding_index: Dict[str, List[str]] = defaultdict(list)  # embedding_hash -> element_ids
        
        # Similarity search
        self._similarity_threshold = config.similarity_threshold
        self._max_elements = getattr(config, 'max_elements', 1000)
        
        # Ranking configuration
        self._relevance_weight = getattr(config, 'relevance_weight', 0.5)
        self._diversity_weight = getattr(config, 'diversity_weight', 0.3)
        self._recency_weight = getattr(config, 'recency_weight', 0.2)
        
        # Performance tracking
        self._ranking_hits = 0
        self._ranking_misses = 0
        self._diversity_improvements = 0
        
        # Background tasks
        self._cleanup_task = None
        self._reindex_task = None
        self._running = False
    
    async def initialize(self) -> bool:
        """
        Initialize the vector cache.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            self.logger.info("Initializing Vector Cache...")
            
            # Start background tasks
            self._running = True
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._reindex_task = asyncio.create_task(self._reindex_loop())
            
            self.logger.info("Vector Cache initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Vector Cache: {e}")
            return False
    
    def get_layer(self) -> CacheLayer:
        """Get the cache layer type."""
        return CacheLayer.VECTOR
    
    async def get(self, key: str) -> CacheResult:
        """
        Retrieve a value from the cache.
        
        Args:
            key: The cache key to retrieve
            
        Returns:
            CacheResult containing the status and retrieved entry
        """
        start_time = time.time()
        
        try:
            # Check if key exists in cache
            if key in self._cache:
                entry = self._cache[key]
                
                # Check if expired
                if entry.is_expired():
                    del self._cache[key]
                    self.update_stats(CacheStatus.EXPIRED)
                    return CacheResult(
                        status=CacheStatus.EXPIRED,
                        error_message="Cache entry expired"
                    )
                
                # Update access statistics
                entry.increment_access()
                self.update_stats(CacheStatus.HIT)
                
                execution_time = (time.time() - start_time) * 1000
                return CacheResult(
                    status=CacheStatus.HIT,
                    entry=entry,
                    execution_time_ms=execution_time
                )
            
            # Cache miss
            self.update_stats(CacheStatus.MISS)
            execution_time = (time.time() - start_time) * 1000
            return CacheResult(
                status=CacheStatus.MISS,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Error getting key {key}: {e}")
            self.update_stats(CacheStatus.ERROR)
            return CacheResult(
                status=CacheStatus.ERROR,
                error_message=str(e)
            )
    
    async def set(self, key: str, value: Any, 
                 ttl_seconds: Optional[int] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 embedding: Optional[List[float]] = None) -> bool:
        """
        Store a value in the cache.
        
        Args:
            key: The cache key
            value: The value to store
            ttl_seconds: Optional time-to-live in seconds
            metadata: Optional metadata dictionary
            embedding: Optional embedding vector
            
        Returns:
            True if the value was stored successfully, False otherwise
        """
        try:
            # Use default TTL if not specified
            if ttl_seconds is None:
                ttl_seconds = self.config.cache_ttl_seconds
            
            # Create cache entry
            entry = self._create_entry(
                key=key,
                value=value,
                ttl_seconds=ttl_seconds,
                metadata=metadata or {},
                embedding=embedding
            )
            
            # Store in cache
            self._cache[key] = entry
            
            # Create context element if embedding is provided
            if embedding:
                await self._create_context_element(key, entry, embedding)
            
            self.logger.debug(f"Stored key {key} in Vector Cache")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key to delete
            
        Returns:
            True if the value was deleted successfully, False otherwise
        """
        try:
            if key in self._cache:
                entry = self._cache[key]
                
                # Remove context element if it exists
                if key in self._context_elements:
                    await self._remove_context_element(key)
                
                del self._cache[key]
                self.logger.debug(f"Deleted key {key} from Vector Cache")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error deleting key {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """
        Clear all values from the cache.
        
        Returns:
            True if the cache was cleared successfully, False otherwise
        """
        try:
            self._cache.clear()
            self._context_elements.clear()
            self._embedding_index.clear()
            self.logger.info("Cleared Vector Cache")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Returns:
            True if the key exists, False otherwise
        """
        return key in self._cache and not self._cache[key].is_expired()
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        total_ranking_operations = self._ranking_hits + self._ranking_misses
        
        return {
            "cache_hits": self.stats["hits"],
            "cache_misses": self.stats["misses"],
            "cache_errors": self.stats["errors"],
            "total_operations": self.stats["total_operations"],
            "hit_rate": self.get_hit_rate(),
            "total_cached_items": len(self._cache),
            "context_elements": len(self._context_elements),
            "ranking_hits": self._ranking_hits,
            "ranking_misses": self._ranking_misses,
            "ranking_accuracy": self._ranking_hits / total_ranking_operations if total_ranking_operations > 0 else 0.0,
            "diversity_improvements": self._diversity_improvements,
            "embedding_index_size": len(self._embedding_index),
            "average_relevance_score": self._get_average_relevance_score()
        }
    
    async def cleanup_expired(self) -> int:
        """
        Remove expired entries from the cache.
        
        Returns:
            Number of expired entries removed
        """
        removed_count = 0
        
        try:
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                if key in self._context_elements:
                    await self._remove_context_element(key)
                del self._cache[key]
                removed_count += 1
            
            self.logger.info(f"Removed {removed_count} expired entries from Vector Cache")
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired entries: {e}")
            return 0
    
    async def find_similar_context(self, query: str, max_results: int = 5) -> List[ContextElement]:
        """
        Find similar context elements based on query.
        
        Args:
            query: Query string to find similar context for
            max_results: Maximum number of results to return
            
        Returns:
            List of similar context elements
        """
        try:
            # Generate embedding for query
            query_embedding = CacheUtils.generate_embedding(query)
            
            # Find similar elements
            similar_elements = await self._find_similar_elements(query_embedding, max_results)
            
            # Update access statistics
            for element in similar_elements:
                element.last_accessed = datetime.utcnow()
                element.access_count += 1
            
            self._ranking_hits += len(similar_elements)
            self._ranking_misses += (max_results - len(similar_elements))
            
            return similar_elements
            
        except Exception as e:
            self.logger.error(f"Error finding similar context: {e}")
            return []
    
    async def rank_context_elements(self, elements: List[ContextElement], 
                                  query_embedding: Optional[List[float]] = None,
                                  max_results: int = 10) -> List[RankingResult]:
        """
        Rank context elements based on relevance, diversity, and recency.
        
        Args:
            elements: List of context elements to rank
            query_embedding: Optional query embedding for relevance calculation
            max_results: Maximum number of results to return
            
        Returns:
            List of ranking results sorted by combined score
        """
        try:
            if not elements:
                return []
            
            # Calculate scores for each element
            ranking_results = []
            for element in elements:
                relevance_score = await self._calculate_relevance_score(element, query_embedding)
                diversity_score = await self._calculate_diversity_score(element, elements)
                recency_score = await self._calculate_recency_score(element)
                
                # Combine scores with weights
                combined_score = (
                    self._relevance_weight * relevance_score +
                    self._diversity_weight * diversity_score +
                    self._recency_weight * recency_score
                )
                
                result = RankingResult(
                    element=element,
                    relevance_score=relevance_score,
                    diversity_score=diversity_score,
                    recency_score=recency_score,
                    combined_score=combined_score
                )
                ranking_results.append(result)
            
            # Sort by combined score
            ranking_results.sort(key=lambda x: x.combined_score, reverse=True)
            
            # Apply diversity improvement
            diversified_results = await self._apply_diversity_improvement(ranking_results)
            
            self._ranking_hits += len(diversified_results)
            self._diversity_improvements += 1
            
            return diversified_results[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error ranking context elements: {e}")
            return []
    
    async def select_optimal_context(self, query: str, max_context_size: int = 5) -> List[ContextElement]:
        """
        Select optimal context elements for a given query.
        
        Args:
            query: Query string
            max_context_size: Maximum number of context elements to select
            
        Returns:
            List of optimal context elements
        """
        try:
            # Find similar elements
            similar_elements = await self.find_similar_context(query, max_context_size * 2)
            
            if not similar_elements:
                return []
            
            # Generate query embedding for ranking
            query_embedding = CacheUtils.generate_embedding(query)
            
            # Rank elements
            ranking_results = await self.rank_context_elements(similar_elements, query_embedding, max_context_size)
            
            # Extract and return context elements
            optimal_context = [result.element for result in ranking_results]
            
            return optimal_context
            
        except Exception as e:
            self.logger.error(f"Error selecting optimal context: {e}")
            return []
    
    async def _create_context_element(self, key: str, entry: CacheEntry, embedding: List[float]):
        """
        Create a context element from cache entry.
        
        Args:
            key: Cache key
            entry: Cache entry
            embedding: Embedding vector
        """
        try:
            # Validate embedding
            if not CacheUtils.validate_embedding(embedding):
                self.logger.warning(f"Invalid embedding for key {key}")
                return
            
            # Create context element
            element = ContextElement(
                element_id=key,
                content=str(entry.value),
                embedding=embedding,
                metadata=entry.metadata or {},
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow(),
                access_count=1,
                relevance_score=0.0
            )
            
            # Store context element
            self._context_elements[key] = element
            
            # Update embedding index
            embedding_hash = hashlib.sha256(str(embedding).encode()).hexdigest()
            self._embedding_index[embedding_hash].append(key)
            
            self.logger.debug(f"Created context element for key {key}")
            
        except Exception as e:
            self.logger.error(f"Error creating context element: {e}")
    
    async def _remove_context_element(self, key: str):
        """
        Remove a context element from the cache.
        
        Args:
            key: Cache key
        """
        try:
            if key in self._context_elements:
                element = self._context_elements[key]
                
                # Remove from embedding index
                embedding_hash = hashlib.sha256(str(element.embedding).encode()).hexdigest()
                if embedding_hash in self._embedding_index:
                    self._embedding_index[embedding_hash].remove(key)
                    if not self._embedding_index[embedding_hash]:
                        del self._embedding_index[embedding_hash]
                
                # Remove context element
                del self._context_elements[key]
                
                self.logger.debug(f"Removed context element for key {key}")
            
        except Exception as e:
            self.logger.error(f"Error removing context element: {e}")
    
    async def _find_similar_elements(self, query_embedding: List[float], max_results: int) -> List[ContextElement]:
        """
        Find elements similar to the query embedding.
        
        Args:
            query_embedding: Query embedding vector
            max_results: Maximum number of results
            
        Returns:
            List of similar context elements
        """
        try:
            results = []
            
            # Search through all context elements
            for element in self._context_elements.values():
                similarity = CacheUtils.calculate_similarity(query_embedding, element.embedding)
                
                if similarity >= self._similarity_threshold:
                    element.relevance_score = similarity
                    results.append(element)
            
            # Sort by relevance score
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return results[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error finding similar elements: {e}")
            return []
    
    async def _calculate_relevance_score(self, element: ContextElement, 
                                       query_embedding: Optional[List[float]] = None) -> float:
        """
        Calculate relevance score for a context element.
        
        Args:
            element: Context element to score
            query_embedding: Optional query embedding
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        try:
            if query_embedding is None:
                return element.relevance_score
            
            similarity = CacheUtils.calculate_similarity(query_embedding, element.embedding)
            return similarity
            
        except Exception as e:
            self.logger.error(f"Error calculating relevance score: {e}")
            return 0.0
    
    async def _calculate_diversity_score(self, element: ContextElement, 
                                       all_elements: List[ContextElement]) -> float:
        """
        Calculate diversity score for a context element.
        
        Args:
            element: Context element to score
            all_elements: All elements to consider for diversity
            
        Returns:
            Diversity score (0.0 to 1.0)
        """
        try:
            if len(all_elements) <= 1:
                return 1.0
            
            # Calculate average similarity to other elements
            total_similarity = 0.0
            count = 0
            
            for other_element in all_elements:
                if other_element != element:
                    similarity = CacheUtils.calculate_similarity(element.embedding, other_element.embedding)
                    total_similarity += similarity
                    count += 1
            
            if count == 0:
                return 1.0
            
            avg_similarity = total_similarity / count
            
            # Diversity is inverse of similarity
            diversity = 1.0 - avg_similarity
            return max(0.0, diversity)
            
        except Exception as e:
            self.logger.error(f"Error calculating diversity score: {e}")
            return 0.0
    
    async def _calculate_recency_score(self, element: ContextElement) -> float:
        """
        Calculate recency score for a context element.
        
        Args:
            element: Context element to score
            
        Returns:
            Recency score (0.0 to 1.0)
        """
        try:
            if element.last_accessed is None:
                return 0.0
            
            # Calculate time difference in hours
            time_diff = (datetime.utcnow() - element.last_accessed).total_seconds() / 3600.0
            
            # Exponential decay for recency
            recency_score = np.exp(-time_diff / 24.0)  # 24-hour half-life
            return recency_score
            
        except Exception as e:
            self.logger.error(f"Error calculating recency score: {e}")
            return 0.0
    
    async def _apply_diversity_improvement(self, ranking_results: List[RankingResult]) -> List[RankingResult]:
        """
        Apply diversity improvement to ranking results.
        
        Args:
            ranking_results: Original ranking results
            
        Returns:
            Improved ranking results with better diversity
        """
        try:
            if len(ranking_results) <= 3:
                return ranking_results
            
            improved_results = []
            selected_elements = set()
            
            # Select elements with maximum diversity
            for result in ranking_results:
                if len(improved_results) >= self._max_elements:
                    break
                
                # Check if element is diverse enough from selected ones
                is_diverse = True
                for selected_result in improved_results:
                    similarity = CacheUtils.calculate_similarity(
                        result.element.embedding, selected_result.element.embedding
                    )
                    
                    if similarity > 0.7:  # diversity_threshold
                        is_diverse = False
                        break
                
                if is_diverse:
                    improved_results.append(result)
                    selected_elements.add(result.element)
                else:
                    # Add to a pool for potential later selection
                    pass
            
            # If we didn't get enough results, add remaining ones
            if len(improved_results) < self._max_elements:
                for result in ranking_results:
                    if len(improved_results) >= self._max_elements:
                        break
                    
                    if result.element not in selected_elements:
                        improved_results.append(result)
                        selected_elements.add(result.element)
            
            return improved_results
            
        except Exception as e:
            self.logger.error(f"Error applying diversity improvement: {e}")
            return ranking_results
    
    def _get_average_relevance_score(self) -> float:
        """Get average relevance score of all context elements."""
        try:
            if not self._context_elements:
                return 0.0
            
            total_score = sum(element.relevance_score for element in self._context_elements.values())
            return total_score / len(self._context_elements)
            
        except Exception as e:
            self.logger.error(f"Error calculating average relevance score: {e}")
            return 0.0
    
    async def _cleanup_loop(self):
        """Background task for periodic cleanup."""
        while self._running:
            try:
                await asyncio.sleep(300)  # 5 minutes
                
                # Clean up expired entries
                removed = await self.cleanup_expired()
                
                # Clean up old context elements
                self._cleanup_old_elements()
                
                if removed > 0:
                    self.logger.info(f"Background cleanup removed {removed} expired entries")
                
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
    
    def _cleanup_old_elements(self):
        """Clean up old context elements."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            
            old_elements = []
            for element_id, element in self._context_elements.items():
                if element.created_at < cutoff_time and element.access_count == 0:
                    old_elements.append(element_id)
            
            for element_id in old_elements:
                # Remove context element synchronously
                if element_id in self._context_elements:
                    element = self._context_elements[element_id]
                    
                    # Remove from embedding index
                    embedding_hash = hashlib.sha256(str(element.embedding).encode()).hexdigest()
                    if embedding_hash in self._embedding_index:
                        self._embedding_index[embedding_hash].remove(element_id)
                        if not self._embedding_index[embedding_hash]:
                            del self._embedding_index[embedding_hash]
                    
                    # Remove context element
                    del self._context_elements[element_id]
            
            if old_elements:
                self.logger.info(f"Cleaned up {len(old_elements)} old context elements")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old elements: {e}")
    
    async def _reindex_loop(self):
        """Background task for periodic reindexing."""
        while self._running:
            try:
                await asyncio.sleep(3600)  # 1 hour
                
                # Rebuild embedding index
                self._rebuild_embedding_index()
                
                self.logger.info("Rebuilt embedding index")
                
            except Exception as e:
                self.logger.error(f"Error in reindex loop: {e}")
    
    def _rebuild_embedding_index(self):
        """Rebuild the embedding index."""
        try:
            self._embedding_index.clear()
            
            for element_id, element in self._context_elements.items():
                embedding_hash = hashlib.sha256(str(element.embedding).encode()).hexdigest()
                self._embedding_index[embedding_hash].append(element_id)
            
            self.logger.debug(f"Rebuilt embedding index with {len(self._embedding_index)} entries")
            
        except Exception as e:
            self.logger.error(f"Error rebuilding embedding index: {e}")
    
    async def close(self):
        """Clean up resources when the cache is being shut down."""
        try:
            self._running = False
            
            # Cancel background tasks
            if self._cleanup_task:
                self._cleanup_task.cancel()
            if self._reindex_task:
                self._reindex_task.cancel()
            
            # Wait for tasks to complete
            if self._cleanup_task:
                await self._cleanup_task
            if self._reindex_task:
                await self._reindex_task
            
            self.logger.info("Vector Cache shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Error shutting down Vector Cache: {e}")