"""
Semantic Cache Implementation (Adaptive Prompt Reuse Layer)

This cache layer reuses previously successful prompts and responses by storing
them with semantic hashes and embeddings, enabling similarity-based retrieval
and adaptive prompt reuse.

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
from collections import defaultdict
import hashlib
import re

from ..core.base_cache import BaseCache, CacheEntry, CacheResult, CacheStatus, CacheLayer
from ..core.config import SemanticCacheConfig
from ..core.utils import CacheUtils

logger = logging.getLogger(__name__)


@dataclass
class SemanticHash:
    """Represents a semantic hash for prompt/response pairs."""
    hash_id: str
    prompt_hash: str
    response_hash: str
    prompt_embedding: List[float]
    response_embedding: List[float]
    similarity_score: float
    created_at: datetime
    last_used: Optional[datetime]
    usage_count: int
    metadata: Dict[str, Any]


@dataclass
class SimilarityResult:
    """Represents a similarity search result."""
    entry: CacheEntry
    similarity_score: float
    prompt_similarity: float
    response_similarity: float


class SemanticCache(BaseCache):
    """
    Semantic Cache that stores and retrieves prompt/response pairs based on similarity.
    
    This cache layer uses semantic hashing and embeddings to find similar
    prompts and responses, enabling adaptive prompt reuse.
    """
    
    def __init__(self, name: str, config: SemanticCacheConfig):
        """
        Initialize the semantic cache.
        
        Args:
            name: Unique name for this cache instance
            config: Semantic cache configuration
        """
        super().__init__(name, asdict(config))
        self.config = config
        
        # Internal storage
        self._cache: Dict[str, CacheEntry] = {}
        self._semantic_hashes: Dict[str, SemanticHash] = {}
        self._prompt_index: Dict[str, List[str]] = defaultdict(list)  # prompt_hash -> hash_ids
        self._response_index: Dict[str, List[str]] = defaultdict(list)  # response_hash -> hash_ids
        
        # Similarity search
        self._similarity_threshold = config.similarity_threshold
        self._hash_algorithm = config.hash_algorithm
        
        # Performance tracking
        self._similarity_hits = 0
        self._similarity_misses = 0
        self._reuse_count = 0
        
        # Background tasks
        self._cleanup_task = None
        self._running = False
    
    async def initialize(self) -> bool:
        """
        Initialize the semantic cache.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            self.logger.info("Initializing Semantic Cache...")
            
            # Start background cleanup task
            self._running = True
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            self.logger.info("Semantic Cache initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Semantic Cache: {e}")
            return False
    
    def get_layer(self) -> CacheLayer:
        """Get the cache layer type."""
        return CacheLayer.SEMANTIC
    
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
            
            # Create semantic hash if this is a prompt/response pair
            if self._is_prompt_response_pair(entry):
                await self._create_semantic_hash(entry)
            
            self.logger.debug(f"Stored key {key} in Semantic Cache")
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
                
                # Remove semantic hash if it exists
                if self._is_prompt_response_pair(entry):
                    await self._remove_semantic_hash(entry)
                
                del self._cache[key]
                self.logger.debug(f"Deleted key {key} from Semantic Cache")
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
            self._semantic_hashes.clear()
            self._prompt_index.clear()
            self._response_index.clear()
            self.logger.info("Cleared Semantic Cache")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: The cache key to check
            
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
        total_similarity_searches = self._similarity_hits + self._similarity_misses
        
        return {
            "cache_hits": self.stats["hits"],
            "cache_misses": self.stats["misses"],
            "cache_errors": self.stats["errors"],
            "total_operations": self.stats["total_operations"],
            "hit_rate": self.get_hit_rate(),
            "total_cached_items": len(self._cache),
            "semantic_hashes": len(self._semantic_hashes),
            "similarity_hits": self._similarity_hits,
            "similarity_misses": self._similarity_misses,
            "similarity_accuracy": self._similarity_hits / total_similarity_searches if total_similarity_searches > 0 else 0.0,
            "reuse_count": self._reuse_count,
            "prompt_index_size": len(self._prompt_index),
            "response_index_size": len(self._response_index)
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
                entry = self._cache[key]
                if self._is_prompt_response_pair(entry):
                    await self._remove_semantic_hash(entry)
                del self._cache[key]
                removed_count += 1
            
            self.logger.info(f"Removed {removed_count} expired entries from Semantic Cache")
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired entries: {e}")
            return 0
    
    async def find_similar_prompts(self, prompt: str, max_results: int = 5) -> List[SimilarityResult]:
        """
        Find similar prompts in the cache.
        
        Args:
            prompt: Input prompt to find similar matches for
            max_results: Maximum number of results to return
            
        Returns:
            List of similarity results
        """
        try:
            # Generate embedding for input prompt
            prompt_embedding = CacheUtils.generate_embedding(prompt)
            
            # Search for similar prompts
            similar_hashes = await self._search_similar_prompts(prompt_embedding, max_results)
            
            # Convert to similarity results
            results = []
            for hash_id, similarity_score in similar_hashes:
                if hash_id in self._semantic_hashes:
                    semantic_hash = self._semantic_hashes[hash_id]
                    
                    # Find corresponding cache entry
                    for key, entry in self._cache.items():
                        if self._is_prompt_response_pair(entry):
                            entry_prompt_hash = CacheUtils.generate_semantic_hash(
                                str(entry.value), self._hash_algorithm
                            )
                            if entry_prompt_hash == semantic_hash.prompt_hash:
                                result = SimilarityResult(
                                    entry=entry,
                                    similarity_score=similarity_score,
                                    prompt_similarity=similarity_score,
                                    response_similarity=0.0  # Would need separate calculation
                                )
                                results.append(result)
                                break
            
            # Sort by similarity score
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            self._similarity_hits += len(results)
            self._similarity_misses += (max_results - len(results))
            
            return results[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error finding similar prompts: {e}")
            return []
    
    async def find_similar_responses(self, response: str, max_results: int = 5) -> List[SimilarityResult]:
        """
        Find similar responses in the cache.
        
        Args:
            response: Input response to find similar matches for
            max_results: Maximum number of results to return
            
        Returns:
            List of similarity results
        """
        try:
            # Generate embedding for input response
            response_embedding = CacheUtils.generate_embedding(response)
            
            # Search for similar responses
            similar_hashes = await self._search_similar_responses(response_embedding, max_results)
            
            # Convert to similarity results
            results = []
            for hash_id, similarity_score in similar_hashes:
                if hash_id in self._semantic_hashes:
                    semantic_hash = self._semantic_hashes[hash_id]
                    
                    # Find corresponding cache entry
                    for key, entry in self._cache.items():
                        if self._is_prompt_response_pair(entry):
                            entry_response_hash = CacheUtils.generate_semantic_hash(
                                str(entry.value), self._hash_algorithm
                            )
                            if entry_response_hash == semantic_hash.response_hash:
                                result = SimilarityResult(
                                    entry=entry,
                                    similarity_score=similarity_score,
                                    prompt_similarity=0.0,  # Would need separate calculation
                                    response_similarity=similarity_score
                                )
                                results.append(result)
                                break
            
            # Sort by similarity score
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            self._similarity_hits += len(results)
            self._similarity_misses += (max_results - len(results))
            
            return results[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error finding similar responses: {e}")
            return []
    
    async def get_recommended_prompts(self, context: str, max_recommendations: int = 3) -> List[str]:
        """
        Get recommended prompts based on context.
        
        Args:
            context: Current context for recommendations
            max_recommendations: Maximum number of recommendations
            
        Returns:
            List of recommended prompt strings
        """
        try:
            # Find similar prompts based on context
            similar_results = await self.find_similar_prompts(context, max_recommendations * 2)
            
            # Extract and return unique prompts
            recommended_prompts = []
            seen_hashes = set()
            
            for result in similar_results:
                if result.entry.key not in seen_hashes:
                    recommended_prompts.append(str(result.entry.value))
                    seen_hashes.add(result.entry.key)
                    
                    if len(recommended_prompts) >= max_recommendations:
                        break
            
            return recommended_prompts
            
        except Exception as e:
            self.logger.error(f"Error getting recommended prompts: {e}")
            return []
    
    def _is_prompt_response_pair(self, entry: CacheEntry) -> bool:
        """
        Check if an entry represents a prompt/response pair.
        
        Args:
            entry: Cache entry to check
            
        Returns:
            True if it's a prompt/response pair, False otherwise
        """
        # Simple heuristic: check if content looks like a prompt or response
        content = str(entry.value).lower()
        
        # Check for prompt indicators
        prompt_indicators = ["question:", "query:", "ask:", "what", "how", "why", "when", "where"]
        is_prompt = any(indicator in content for indicator in prompt_indicators)
        
        # Check for response indicators
        response_indicators = ["answer:", "response:", "reply:", "here", "the", "i think"]
        is_response = any(indicator in content for indicator in response_indicators)
        
        return is_prompt or is_response
    
    async def _create_semantic_hash(self, entry: CacheEntry):
        """
        Create a semantic hash for a prompt/response pair.
        
        Args:
            entry: Cache entry to create hash for
        """
        try:
            content = str(entry.value)
            
            # Generate hashes
            prompt_hash = CacheUtils.generate_semantic_hash(content, self._hash_algorithm)
            response_hash = prompt_hash  # For now, use same hash for both
            
            # Generate embeddings
            prompt_embedding = CacheUtils.generate_embedding(content)
            response_embedding = prompt_embedding  # For now, use same embedding
            
            # Calculate similarity (will be 1.0 for same content)
            similarity_score = CacheUtils.calculate_similarity(prompt_embedding, response_embedding)
            
            # Create semantic hash
            semantic_hash = SemanticHash(
                hash_id=CacheUtils.create_cache_key("semantic", entry.key),
                prompt_hash=prompt_hash,
                response_hash=response_hash,
                prompt_embedding=prompt_embedding,
                response_embedding=response_embedding,
                similarity_score=similarity_score,
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
                usage_count=1,
                metadata=entry.metadata or {}
            )
            
            # Store semantic hash
            self._semantic_hashes[semantic_hash.hash_id] = semantic_hash
            
            # Update indexes
            self._prompt_index[prompt_hash].append(semantic_hash.hash_id)
            self._response_index[response_hash].append(semantic_hash.hash_id)
            
            self.logger.debug(f"Created semantic hash for key {entry.key}")
            
        except Exception as e:
            self.logger.error(f"Error creating semantic hash: {e}")
    
    async def _remove_semantic_hash(self, entry: CacheEntry):
        """
        Remove a semantic hash from the cache.
        
        Args:
            entry: Cache entry to remove hash for
        """
        try:
            # Find semantic hash for this entry
            semantic_hash = None
            for hash_id, sh in self._semantic_hashes.items():
                if sh.metadata.get("original_key") == entry.key:
                    semantic_hash = sh
                    break
            
            if semantic_hash:
                # Remove from indexes
                if semantic_hash.prompt_hash in self._prompt_index:
                    self._prompt_index[semantic_hash.prompt_hash].remove(semantic_hash.hash_id)
                    if not self._prompt_index[semantic_hash.prompt_hash]:
                        del self._prompt_index[semantic_hash.prompt_hash]
                
                if semantic_hash.response_hash in self._response_index:
                    self._response_index[semantic_hash.response_hash].remove(semantic_hash.hash_id)
                    if not self._response_index[semantic_hash.response_hash]:
                        del self._response_index[semantic_hash.response_hash]
                
                # Remove semantic hash
                del self._semantic_hashes[semantic_hash.hash_id]
                
                self.logger.debug(f"Removed semantic hash for key {entry.key}")
            
        except Exception as e:
            self.logger.error(f"Error removing semantic hash: {e}")
    
    async def _search_similar_prompts(self, query_embedding: List[float], max_results: int) -> List[Tuple[str, float]]:
        """
        Search for similar prompts using embeddings.
        
        Args:
            query_embedding: Embedding vector for the query
            max_results: Maximum number of results
            
        Returns:
            List of (hash_id, similarity_score) tuples
        """
        try:
            results = []
            
            # Search through all semantic hashes
            for hash_id, semantic_hash in self._semantic_hashes.items():
                similarity = CacheUtils.calculate_similarity(query_embedding, semantic_hash.prompt_embedding)
                
                if similarity >= self._similarity_threshold:
                    results.append((hash_id, similarity))
            
            # Sort by similarity score
            results.sort(key=lambda x: x[1], reverse=True)
            
            return results[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error searching similar prompts: {e}")
            return []
    
    async def _search_similar_responses(self, query_embedding: List[float], max_results: int) -> List[Tuple[str, float]]:
        """
        Search for similar responses using embeddings.
        
        Args:
            query_embedding: Embedding vector for the query
            max_results: Maximum number of results
            
        Returns:
            List of (hash_id, similarity_score) tuples
        """
        try:
            results = []
            
            # Search through all semantic hashes
            for hash_id, semantic_hash in self._semantic_hashes.items():
                similarity = CacheUtils.calculate_similarity(query_embedding, semantic_hash.response_embedding)
                
                if similarity >= self._similarity_threshold:
                    results.append((hash_id, similarity))
            
            # Sort by similarity score
            results.sort(key=lambda x: x[1], reverse=True)
            
            return results[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error searching similar responses: {e}")
            return []
    
    async def _cleanup_loop(self):
        """Background task for periodic cleanup."""
        while self._running:
            try:
                await asyncio.sleep(300)  # 5 minutes
                
                # Clean up expired entries
                removed = await self.cleanup_expired()
                
                # Clean up unused semantic hashes
                self._cleanup_unused_hashes()
                
                if removed > 0:
                    self.logger.info(f"Background cleanup removed {removed} expired entries")
                
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
    
    def _cleanup_unused_hashes(self):
        """Clean up unused semantic hashes."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=30)
            
            unused_hashes = []
            for hash_id, semantic_hash in self._semantic_hashes.items():
                if (semantic_hash.last_used and semantic_hash.last_used < cutoff_time and
                    semantic_hash.usage_count == 1):
                    unused_hashes.append(hash_id)
            
            for hash_id in unused_hashes:
                semantic_hash = self._semantic_hashes[hash_id]
                
                # Remove from indexes
                if semantic_hash.prompt_hash in self._prompt_index:
                    self._prompt_index[semantic_hash.prompt_hash].remove(hash_id)
                if semantic_hash.response_hash in self._response_index:
                    self._response_index[semantic_hash.response_hash].remove(hash_id)
                
                # Remove semantic hash
                del self._semantic_hashes[hash_id]
            
            if unused_hashes:
                self.logger.info(f"Cleaned up {len(unused_hashes)} unused semantic hashes")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up unused hashes: {e}")
    
    async def close(self):
        """Clean up resources when the cache is being shut down."""
        try:
            self._running = False
            
            # Cancel background tasks
            if self._cleanup_task:
                self._cleanup_task.cancel()
                await self._cleanup_task
            
            self.logger.info("Semantic Cache shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Error shutting down Semantic Cache: {e}")