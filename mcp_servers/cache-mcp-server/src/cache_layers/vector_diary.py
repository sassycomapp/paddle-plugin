"""
Vector Diary Implementation (Persistent Context Memory)

This cache layer provides persistent context memory with longitudinal reasoning
across sessions, serving as the foundation for longitudinal reasoning capabilities.

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
from ..core.config import VectorDiaryConfig
from ..core.utils import CacheUtils

logger = logging.getLogger(__name__)


@dataclass
class ContextMemory:
    """Represents a persistent context memory entry."""
    memory_id: str
    session_id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    created_at: datetime
    last_accessed: datetime
    access_count: int
    importance_score: float
    context_type: str  # "conversation", "decision", "observation", "insight"
    relationships: List[str]  # Related memory IDs
    decay_factor: float


@dataclass
class LongitudinalInsight:
    """Represents a longitudinal insight derived from context memories."""
    insight_id: str
    title: str
    description: str
    supporting_memories: List[str]
    confidence_score: float
    created_at: datetime
    last_updated: datetime
    category: str


class VectorDiary(BaseCache):
    """
    Vector Diary that provides persistent context memory with longitudinal reasoning.
    
    This cache layer serves as the foundation for longitudinal reasoning across sessions,
    storing and analyzing context patterns over time.
    """
    
    def __init__(self, name: str, config: VectorDiaryConfig):
        """
        Initialize the vector diary.
        
        Args:
            name: Unique name for this cache instance
            config: Vector diary configuration
        """
        super().__init__(name, asdict(config))
        self.config = config
        
        # Internal storage
        self._cache: Dict[str, CacheEntry] = {}
        self._memories: Dict[str, ContextMemory] = {}
        self._insights: Dict[str, LongitudinalInsight] = {}
        self._session_index: Dict[str, List[str]] = defaultdict(list)  # session_id -> memory_ids
        self._type_index: Dict[str, List[str]] = defaultdict(list)  # context_type -> memory_ids
        self._relationship_graph: Dict[str, List[str]] = defaultdict(list)  # memory_id -> related_ids
        
        # Longitudinal analysis
        self._analysis_interval = getattr(config, 'analysis_interval', 3600)  # 1 hour
        self._min_insight_confidence = getattr(config, 'min_insight_confidence', 0.6)
        self._max_memory_age = getattr(config, 'max_memory_age', 90)  # 90 days
        
        # Performance tracking
        self._analysis_runs = 0
        self._insights_generated = 0
        self._memories_processed = 0
        
        # Background tasks
        self._analysis_task = None
        self._cleanup_task = None
        self._running = False
    
    async def initialize(self) -> bool:
        """
        Initialize the vector diary.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            self.logger.info("Initializing Vector Diary...")
            
            # Start background tasks
            self._running = True
            self._analysis_task = asyncio.create_task(self._analysis_loop())
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            self.logger.info("Vector Diary initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Vector Diary: {e}")
            return False
    
    def get_layer(self) -> CacheLayer:
        """Get the cache layer type."""
        return CacheLayer.VECTOR_DIARY
    
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
            
            # Add to vector diary if it's context content
            if self._is_context_content(entry):
                await self._add_memory(key, entry)
            
            self.logger.debug(f"Stored key {key} in Vector Diary")
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
                
                # Remove from memories if it exists
                if key in self._memories:
                    await self._remove_memory(key)
                
                del self._cache[key]
                self.logger.debug(f"Deleted key {key} from Vector Diary")
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
            self._memories.clear()
            self._insights.clear()
            self._session_index.clear()
            self._type_index.clear()
            self._relationship_graph.clear()
            self.logger.info("Cleared Vector Diary")
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
        return {
            "cache_hits": self.stats["hits"],
            "cache_misses": self.stats["misses"],
            "cache_errors": self.stats["errors"],
            "total_operations": self.stats["total_operations"],
            "hit_rate": self.get_hit_rate(),
            "total_cached_items": len(self._cache),
            "context_memories": len(self._memories),
            "longitudinal_insights": len(self._insights),
            "analysis_runs": self._analysis_runs,
            "insights_generated": self._insights_generated,
            "memories_processed": self._memories_processed,
            "session_count": len(self._session_index),
            "type_count": len(self._type_index),
            "relationship_count": len(self._relationship_graph)
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
                if key in self._memories:
                    await self._remove_memory(key)
                del self._cache[key]
                removed_count += 1
            
            self.logger.info(f"Removed {removed_count} expired entries from Vector Diary")
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired entries: {e}")
            return 0
    
    async def get_session_memories(self, session_id: str, 
                                 context_type: Optional[str] = None,
                                 limit: int = 50) -> List[ContextMemory]:
        """
        Get memories for a specific session.
        
        Args:
            session_id: Session ID to retrieve memories for
            context_type: Optional context type filter
            limit: Maximum number of memories to return
            
        Returns:
            List of context memories
        """
        try:
            if session_id not in self._session_index:
                return []
            
            memory_ids = self._session_index[session_id]
            
            # Filter by context type if specified
            if context_type:
                memory_ids = [mid for mid in memory_ids 
                            if mid in self._type_index.get(context_type, [])]
            
            # Sort by importance and recency
            memories = []
            for memory_id in memory_ids:
                if memory_id in self._memories:
                    memories.append(self._memories[memory_id])
            
            # Sort by importance score and recency
            memories.sort(key=lambda m: (m.importance_score, m.last_accessed), reverse=True)
            
            return memories[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting session memories: {e}")
            return []
    
    async def get_related_memories(self, memory_id: str, 
                                 max_depth: int = 2) -> List[ContextMemory]:
        """
        Get memories related to a specific memory.
        
        Args:
            memory_id: Memory ID to find related memories for
            max_depth: Maximum depth of relationship traversal
            
        Returns:
            List of related context memories
        """
        try:
            if memory_id not in self._memories:
                return []
            
            related_ids = set()
            queue = deque([(memory_id, 0)])
            
            while queue and len(related_ids) < 20:  # Limit to prevent infinite loops
                current_id, depth = queue.popleft()
                
                if depth >= max_depth:
                    continue
                
                # Get direct relationships
                for related_id in self._relationship_graph.get(current_id, []):
                    if related_id != memory_id and related_id not in related_ids:
                        related_ids.add(related_id)
                        queue.append((related_id, depth + 1))
            
            # Get memory objects
            related_memories = []
            for related_id in related_ids:
                if related_id in self._memories:
                    related_memories.append(self._memories[related_id])
            
            # Sort by importance
            related_memories.sort(key=lambda m: m.importance_score, reverse=True)
            
            return related_memories
            
        except Exception as e:
            self.logger.error(f"Error getting related memories: {e}")
            return []
    
    async def generate_insights(self, session_id: Optional[str] = None,
                               category: Optional[str] = None) -> List[LongitudinalInsight]:
        """
        Generate longitudinal insights from context memories.
        
        Args:
            session_id: Optional session ID to focus analysis on
            category: Optional insight category filter
            
        Returns:
            List of generated insights
        """
        try:
            # Get relevant memories
            if session_id:
                memories = await self.get_session_memories(session_id)
            else:
                memories = list(self._memories.values())
            
            # Filter by category if specified
            if category:
                memories = [m for m in memories if m.metadata.get("insight_category") == category]
            
            if len(memories) < 3:
                return []
            
            # Generate insights
            insights = []
            
            # Pattern-based insights
            pattern_insights = await self._generate_pattern_insights(memories)
            insights.extend(pattern_insights)
            
            # Temporal insights
            temporal_insights = await self._generate_temporal_insights(memories)
            insights.extend(temporal_insights)
            
            # Relationship insights
            relationship_insights = await self._generate_relationship_insights(memories)
            insights.extend(relationship_insights)
            
            # Filter by confidence
            insights = [i for i in insights if i.confidence_score >= self._min_insight_confidence]
            
            # Sort by confidence
            insights.sort(key=lambda i: i.confidence_score, reverse=True)
            
            # Store insights
            for insight in insights:
                if insight.insight_id not in self._insights:
                    self._insights[insight.insight_id] = insight
                    self._insights_generated += 1
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
            return []
    
    async def add_memory_relationship(self, memory_id1: str, memory_id2: str, 
                                    relationship_type: str = "related") -> bool:
        """
        Add a relationship between two memories.
        
        Args:
            memory_id1: First memory ID
            memory_id2: Second memory ID
            relationship_type: Type of relationship
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if memory_id1 not in self._memories or memory_id2 not in self._memories:
                return False
            
            # Add bidirectional relationship
            self._relationship_graph[memory_id1].append(memory_id2)
            self._relationship_graph[memory_id2].append(memory_id1)
            
            # Update memory metadata
            self._memories[memory_id1].relationships.append(memory_id2)
            self._memories[memory_id2].relationships.append(memory_id1)
            
            self.logger.debug(f"Added relationship between {memory_id1} and {memory_id2}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding memory relationship: {e}")
            return False
    
    async def _add_memory(self, key: str, entry: CacheEntry):
        """
        Add a cache entry to the vector diary as a context memory.
        
        Args:
            key: Cache key
            entry: Cache entry
        """
        try:
            # Create context memory
            memory = ContextMemory(
                memory_id=key,
                session_id=entry.metadata.get("session_id", "default") if entry.metadata else "default",
                content=str(entry.value),
                embedding=entry.embedding or CacheUtils.generate_embedding(str(entry.value)),
                metadata=entry.metadata or {},
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow(),
                access_count=0,
                importance_score=self._calculate_importance(entry),
                context_type=entry.metadata.get("context_type", "conversation") if entry.metadata else "conversation",
                relationships=[],
                decay_factor=self._calculate_decay_factor(entry)
            )
            
            # Store memory
            self._memories[key] = memory
            
            # Update indexes
            await self._update_memory_indexes(memory)
            
            self.logger.debug(f"Added memory {key} to Vector Diary")
            
        except Exception as e:
            self.logger.error(f"Error adding memory: {e}")
    
    async def _remove_memory(self, memory_id: str):
        """
        Remove a memory from the vector diary.
        
        Args:
            memory_id: Memory ID to remove
        """
        try:
            if memory_id in self._memories:
                memory = self._memories[memory_id]
                
                # Remove from indexes
                await self._remove_from_memory_indexes(memory)
                
                # Remove from relationship graph
                for related_id in memory.relationships:
                    if related_id in self._relationship_graph:
                        self._relationship_graph[related_id].remove(memory_id)
                
                # Remove memory
                del self._memories[memory_id]
                
                self.logger.debug(f"Removed memory {memory_id} from Vector Diary")
            
        except Exception as e:
            self.logger.error(f"Error removing memory: {e}")
    
    async def _update_memory_indexes(self, memory: ContextMemory):
        """
        Update memory indexes for a context memory.
        
        Args:
            memory: Context memory to index
        """
        try:
            # Update session index
            self._session_index[memory.session_id].append(memory.memory_id)
            
            # Update type index
            self._type_index[memory.context_type].append(memory.memory_id)
            
        except Exception as e:
            self.logger.error(f"Error updating memory indexes: {e}")
    
    async def _remove_from_memory_indexes(self, memory: ContextMemory):
        """
        Remove a memory from indexes.
        
        Args:
            memory: Context memory to remove from indexes
        """
        try:
            # Remove from session index
            if memory.session_id in self._session_index:
                self._session_index[memory.session_id].remove(memory.memory_id)
                if not self._session_index[memory.session_id]:
                    del self._session_index[memory.session_id]
            
            # Remove from type index
            if memory.context_type in self._type_index:
                self._type_index[memory.context_type].remove(memory.memory_id)
                if not self._type_index[memory.context_type]:
                    del self._type_index[memory.context_type]
            
        except Exception as e:
            self.logger.error(f"Error removing from memory indexes: {e}")
    
    def _is_context_content(self, entry: CacheEntry) -> bool:
        """
        Check if an entry represents context content.
        
        Args:
            entry: Cache entry to check
            
        Returns:
            True if it's context content, False otherwise
        """
        # Simple heuristic: check if content looks like context
        content = str(entry.value).lower()
        
        # Check for context indicators
        context_indicators = ["conversation", "chat", "dialog", "message", "query", "response"]
        is_context = any(indicator in content for indicator in context_indicators)
        
        return is_context
    
    def _calculate_importance(self, entry: CacheEntry) -> float:
        """
        Calculate importance score for a memory.
        
        Args:
            entry: Cache entry
            
        Returns:
            Importance score (0.0 to 1.0)
        """
        try:
            importance = 0.5  # Base importance
            
            # Boost for certain context types
            context_type = entry.metadata.get("context_type", "conversation") if entry.metadata else "conversation"
            if context_type == "decision":
                importance += 0.3
            elif context_type == "insight":
                importance += 0.4
            
            # Boost for access count
            access_count = entry.metadata.get("access_count", 0) if entry.metadata else 0
            importance += min(access_count * 0.05, 0.3)
            
            # Boost for certain keywords
            content = str(entry.value).lower()
            if any(keyword in content for keyword in ["important", "key", "critical", "essential"]):
                importance += 0.2
            
            return min(importance, 1.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating importance: {e}")
            return 0.5
    
    def _calculate_decay_factor(self, entry: CacheEntry) -> float:
        """
        Calculate decay factor for a memory.
        
        Args:
            entry: Cache entry
            
        Returns:
            Decay factor (0.0 to 1.0)
        """
        try:
            # Base decay factor
            decay = 0.95
            
            # Adjust based on context type
            context_type = entry.metadata.get("context_type", "conversation") if entry.metadata else "conversation"
            if context_type == "observation":
                decay = 0.9  # Faster decay for observations
            elif context_type == "insight":
                decay = 0.98  # Slower decay for insights
            
            return decay
            
        except Exception as e:
            self.logger.error(f"Error calculating decay factor: {e}")
            return 0.95
    
    async def _generate_pattern_insights(self, memories: List[ContextMemory]) -> List[LongitudinalInsight]:
        """
        Generate pattern-based insights from memories.
        
        Args:
            memories: List of context memories
            
        Returns:
            List of pattern insights
        """
        try:
            insights = []
            
            # Group by context type
            type_groups = defaultdict(list)
            for memory in memories:
                type_groups[memory.context_type].append(memory)
            
            # Generate insights for each type
            for context_type, type_memories in type_groups.items():
                if len(type_memories) >= 3:
                    # Calculate frequency patterns
                    frequencies = {}
                    for memory in type_memories:
                        # Extract keywords
                        keywords = self._extract_keywords(memory.content)
                        for keyword in keywords:
                            frequencies[keyword] = frequencies.get(keyword, 0) + 1
                    
                    # Find frequent patterns
                    frequent_patterns = [(k, v) for k, v in frequencies.items() if v >= 2]
                    frequent_patterns.sort(key=lambda x: x[1], reverse=True)
                    
                    if frequent_patterns:
                        insight = LongitudinalInsight(
                            insight_id=f"pattern_{context_type}_{hash(str(frequent_patterns))}",
                            title=f"Pattern in {context_type} context",
                            description=f"Frequent patterns detected: {', '.join([k for k, v in frequent_patterns[:3]])}",
                            supporting_memories=[m.memory_id for m in type_memories[:5]],
                            confidence_score=min(len(frequent_patterns) * 0.2, 1.0),
                            created_at=datetime.utcnow(),
                            last_updated=datetime.utcnow(),
                            category="pattern"
                        )
                        insights.append(insight)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating pattern insights: {e}")
            return []
    
    async def _generate_temporal_insights(self, memories: List[ContextMemory]) -> List[LongitudinalInsight]:
        """
        Generate temporal insights from memories.
        
        Args:
            memories: List of context memories
            
        Returns:
            List of temporal insights
        """
        try:
            insights = []
            
            if len(memories) < 5:
                return insights
            
            # Sort by creation time
            sorted_memories = sorted(memories, key=lambda m: m.created_at)
            
            # Analyze time gaps
            time_gaps = []
            for i in range(1, len(sorted_memories)):
                gap = (sorted_memories[i].created_at - sorted_memories[i-1].created_at).total_seconds()
                time_gaps.append(gap)
            
            # Find unusual gaps
            avg_gap = sum(time_gaps) / len(time_gaps) if time_gaps else 3600
            unusual_gaps = [gap for gap in time_gaps if gap > avg_gap * 2 or gap < avg_gap * 0.5]
            
            if unusual_gaps:
                insight = LongitudinalInsight(
                    insight_id=f"temporal_{hash(str(unusual_gaps))}",
                    title="Temporal Pattern Detected",
                    description=f"Unusual time gaps detected in conversation patterns",
                    supporting_memories=[m.memory_id for m in sorted_memories[:10]],
                    confidence_score=min(len(unusual_gaps) * 0.15, 1.0),
                    created_at=datetime.utcnow(),
                    last_updated=datetime.utcnow(),
                    category="temporal"
                )
                insights.append(insight)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating temporal insights: {e}")
            return []
    
    async def _generate_relationship_insights(self, memories: List[ContextMemory]) -> List[LongitudinalInsight]:
        """
        Generate relationship-based insights from memories.
        
        Args:
            memories: List of context memories
            
        Returns:
            List of relationship insights
        """
        try:
            insights = []
            
            # Analyze relationship density
            relationship_counts = defaultdict(int)
            for memory in memories:
                relationship_counts[memory.memory_id] = len(memory.relationships)
            
            # Find highly connected memories
            highly_connected = [(mid, count) for mid, count in relationship_counts.items() if count >= 3]
            
            if highly_connected:
                insight = LongitudinalInsight(
                    insight_id=f"relationship_{hash(str(highly_connected))}",
                    title="Highly Connected Topics",
                    description=f"Several topics show strong interconnections",
                    supporting_memories=[mid for mid, _ in highly_connected[:5]],
                    confidence_score=min(len(highly_connected) * 0.2, 1.0),
                    created_at=datetime.utcnow(),
                    last_updated=datetime.utcnow(),
                    category="relationship"
                )
                insights.append(insight)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating relationship insights: {e}")
            return []
    
    def _extract_keywords(self, content: str) -> List[str]:
        """
        Extract keywords from content.
        
        Args:
            content: Content to extract keywords from
            
        Returns:
            List of keywords
        """
        try:
            # Simple keyword extraction (placeholder)
            words = content.lower().split()
            keywords = []
            
            for word in words:
                # Filter out common words and short words
                if (len(word) > 3 and 
                    word not in ["the", "and", "for", "are", "but", "not", "you", "all", "can", "had", "her", "was", "one", "our", "out", "day", "get", "has", "him", "his", "how", "its", "may", "new", "now", "old", "see", "two", "way", "who", "boy", "did", "does", "let", "put", "say", "she", "too", "use"]):
                    keywords.append(word)
            
            return list(set(keywords))  # Remove duplicates
            
        except Exception as e:
            self.logger.error(f"Error extracting keywords: {e}")
            return []
    
    async def _analysis_loop(self):
        """Background task for periodic longitudinal analysis."""
        while self._running:
            try:
                await asyncio.sleep(self._analysis_interval)
                
                # Generate insights
                insights = await self.generate_insights()
                
                if insights:
                    self.logger.info(f"Generated {len(insights)} longitudinal insights")
                
                self._analysis_runs += 1
                
            except Exception as e:
                self.logger.error(f"Error in analysis loop: {e}")
    
    async def _cleanup_loop(self):
        """Background task for periodic cleanup."""
        while self._running:
            try:
                await asyncio.sleep(300)  # 5 minutes
                
                # Clean up expired entries
                removed = await self.cleanup_expired()
                
                # Clean up old memories
                self._cleanup_old_memories()
                
                if removed > 0:
                    self.logger.info(f"Background cleanup removed {removed} expired entries")
                
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
    
    def _cleanup_old_memories(self):
        """Clean up old memories based on decay factor."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=self._max_memory_age)
            
            old_memories = []
            for memory_id, memory in self._memories.items():
                # Check if memory is too old or has decayed too much
                age = (datetime.utcnow() - memory.created_at).total_seconds()
                decayed_importance = memory.importance_score * (memory.decay_factor ** (age / 86400))
                
                if memory.created_at < cutoff_time or decayed_importance < 0.1:
                    old_memories.append(memory_id)
            
            for memory_id in old_memories:
                # Remove memory synchronously
                if memory_id in self._memories:
                    memory = self._memories[memory_id]
                    
                    # Remove from indexes
                    # Remove from indexes synchronously
                    if memory.session_id in self._session_index:
                        self._session_index[memory.session_id].remove(memory.memory_id)
                        if not self._session_index[memory.session_id]:
                            del self._session_index[memory.session_id]
                    
                    if memory.context_type in self._type_index:
                        self._type_index[memory.context_type].remove(memory.memory_id)
                        if not self._type_index[memory.context_type]:
                            del self._type_index[memory.context_type]
                    
                    # Remove from relationship graph
                    for related_id in memory.relationships:
                        if related_id in self._relationship_graph:
                            self._relationship_graph[related_id].remove(memory_id)
                    
                    # Remove memory
                    del self._memories[memory_id]
            
            if old_memories:
                self.logger.info(f"Cleaned up {len(old_memories)} old memories")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old memories: {e}")
    
    async def close(self):
        """Clean up resources when the cache is being shut down."""
        try:
            self._running = False
            
            # Cancel background tasks
            if self._analysis_task:
                self._analysis_task.cancel()
            if self._cleanup_task:
                self._cleanup_task.cancel()
            
            # Wait for tasks to complete
            if self._analysis_task:
                await self._analysis_task
            if self._cleanup_task:
                await self._cleanup_task
            
            self.logger.info("Vector Diary shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Error shutting down Vector Diary: {e}")