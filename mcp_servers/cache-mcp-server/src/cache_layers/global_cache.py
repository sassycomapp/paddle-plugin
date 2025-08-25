"""
Global Knowledge Cache Implementation (Fallback Memory)

This cache layer provides a fallback knowledge base using persistent LLM training data,
integrating with existing MCP RAG server to serve as the global knowledge repository.

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

from ..core.base_cache import BaseCache, CacheEntry, CacheResult, CacheStatus, CacheLayer
from ..core.config import GlobalCacheConfig
from ..core.utils import CacheUtils

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeDocument:
    """Represents a knowledge document in the global cache."""
    document_id: str
    title: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    source: str
    created_at: datetime
    last_updated: datetime
    access_count: int
    relevance_score: float


@dataclass
class SearchResult:
    """Represents a search result from the global cache."""
    document: KnowledgeDocument
    similarity_score: float
    source_relevance: float
    freshness_score: float
    combined_score: float


class GlobalCache(BaseCache):
    """
    Global Knowledge Cache that serves as a fallback memory using persistent LLM training data.
    
    This cache layer integrates with existing MCP RAG server to provide
    a comprehensive knowledge base for the caching system.
    """
    
    def __init__(self, name: str, config: GlobalCacheConfig):
        """
        Initialize the global cache.
        
        Args:
            name: Unique name for this cache instance
            config: Global cache configuration
        """
        super().__init__(name, asdict(config))
        self.config = config
        
        # Internal storage
        self._cache: Dict[str, CacheEntry] = {}
        self._knowledge_base: Dict[str, KnowledgeDocument] = {}
        self._document_index: Dict[str, List[str]] = defaultdict(list)  # keyword -> document_ids
        self._source_index: Dict[str, List[str]] = defaultdict(list)  # source -> document_ids
        
        # MCP RAG integration
        self._rag_server_client = None
        self._rag_server_url = config.rag_server_url
        self._rag_server_timeout = config.rag_server_timeout
        
        # Search configuration
        self._max_search_results = getattr(config, 'max_search_results', 10)
        self._min_relevance_score = getattr(config, 'min_relevance_score', 0.3)
        
        # Performance tracking
        self._search_hits = 0
        self._search_misses = 0
        self._rag_integration_hits = 0
        self._rag_integration_errors = 0
        
        # Background tasks
        self._sync_task = None
        self._cleanup_task = None
        self._running = False
    
    async def initialize(self) -> bool:
        """
        Initialize the global cache.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            self.logger.info("Initializing Global Cache...")
            
            # Initialize MCP RAG server client
            await self._initialize_rag_client()
            
            # Start background tasks
            self._running = True
            self._sync_task = asyncio.create_task(self._sync_loop())
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            self.logger.info("Global Cache initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Global Cache: {e}")
            return False
    
    def get_layer(self) -> CacheLayer:
        """Get the cache layer type."""
        return CacheLayer.GLOBAL
    
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
            
            # Cache miss - try to fetch from RAG server
            if self._rag_server_client:
                rag_result = await self._fetch_from_rag_server(key)
                if rag_result:
                    # Store in cache for future access
                    await self.set(key, rag_result, ttl_seconds=self.config.cache_ttl_seconds)
                    self.update_stats(CacheStatus.HIT)
                    execution_time = (time.time() - start_time) * 1000
                    return CacheResult(
                        status=CacheStatus.HIT,
                        entry=CacheEntry(
                            key=key,
                            value=rag_result,
                            ttl_seconds=self.config.cache_ttl_seconds,
                            metadata={"source": "rag_server", "fetched_at": datetime.utcnow().isoformat()},
                            layer=self.get_layer(),
                            created_at=datetime.utcnow()
                        ),
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
            
            # Add to knowledge base if it's knowledge content
            if self._is_knowledge_content(entry):
                await self._add_to_knowledge_base(key, entry)
            
            self.logger.debug(f"Stored key {key} in Global Cache")
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
                
                # Remove from knowledge base if it exists
                if key in self._knowledge_base:
                    await self._remove_from_knowledge_base(key)
                
                del self._cache[key]
                self.logger.debug(f"Deleted key {key} from Global Cache")
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
            self._knowledge_base.clear()
            self._document_index.clear()
            self._source_index.clear()
            self.logger.info("Cleared Global Cache")
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
        total_searches = self._search_hits + self._search_misses
        total_rag_operations = self._rag_integration_hits + self._rag_integration_errors
        
        return {
            "cache_hits": self.stats["hits"],
            "cache_misses": self.stats["misses"],
            "cache_errors": self.stats["errors"],
            "total_operations": self.stats["total_operations"],
            "hit_rate": self.get_hit_rate(),
            "total_cached_items": len(self._cache),
            "knowledge_documents": len(self._knowledge_base),
            "search_hits": self._search_hits,
            "search_misses": self._search_misses,
            "search_accuracy": self._search_hits / total_searches if total_searches > 0 else 0.0,
            "rag_integration_hits": self._rag_integration_hits,
            "rag_integration_errors": self._rag_integration_errors,
            "rag_success_rate": self._rag_integration_hits / total_rag_operations if total_rag_operations > 0 else 0.0,
            "document_index_size": len(self._document_index),
            "source_index_size": len(self._source_index)
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
                if key in self._knowledge_base:
                    await self._remove_from_knowledge_base(key)
                del self._cache[key]
                removed_count += 1
            
            self.logger.info(f"Removed {removed_count} expired entries from Global Cache")
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired entries: {e}")
            return 0
    
    async def search_knowledge_base(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search the knowledge base for relevant documents.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results
        """
        try:
            # Search local knowledge base
            local_results = await self._search_local_knowledge_base(query, max_results)
            
            # Search RAG server if available
            rag_results = []
            if self._rag_server_client:
                rag_results = await self._search_rag_server(query, max_results)
            
            # Combine and rank results
            combined_results = await self._combine_and_rank_results(local_results, rag_results, max_results)
            
            self._search_hits += len(combined_results)
            self._search_misses += (max_results - len(combined_results))
            
            return combined_results
            
        except Exception as e:
            self.logger.error(f"Error searching knowledge base: {e}")
            return []
    
    async def add_knowledge_document(self, title: str, content: str, 
                                   source: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a knowledge document to the global cache.
        
        Args:
            title: Document title
            content: Document content
            source: Document source
            metadata: Optional metadata
            
        Returns:
            Document ID if successful, None otherwise
        """
        try:
            # Generate document ID
            document_id = hashlib.sha256(f"{title}:{content}:{source}".encode()).hexdigest()
            
            # Generate embedding
            embedding = CacheUtils.generate_embedding(content)
            
            # Create knowledge document
            document = KnowledgeDocument(
                document_id=document_id,
                title=title,
                content=content,
                embedding=embedding,
                metadata=metadata or {},
                source=source,
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow(),
                access_count=0,
                relevance_score=0.0
            )
            
            # Store in knowledge base
            self._knowledge_base[document_id] = document
            
            # Update indexes
            await self._update_document_indexes(document)
            
            self.logger.info(f"Added knowledge document '{title}' to Global Cache")
            return document_id
            
        except Exception as e:
            self.logger.error(f"Error adding knowledge document: {e}")
            return ""  # Return empty string instead of None
    
    async def get_document_by_id(self, document_id: str) -> Optional[KnowledgeDocument]:
        """
        Get a knowledge document by ID.
        
        Args:
            document_id: Document ID to retrieve
            
        Returns:
            Knowledge document if found, None otherwise
        """
        try:
            if document_id in self._knowledge_base:
                document = self._knowledge_base[document_id]
                document.access_count += 1
                document.last_updated = datetime.utcnow()
                return document
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting document {document_id}: {e}")
            return None
    
    async def update_document_metadata(self, document_id: str, 
                                     metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a knowledge document.
        
        Args:
            document_id: Document ID to update
            metadata: New metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if document_id in self._knowledge_base:
                document = self._knowledge_base[document_id]
                document.metadata.update(metadata)
                document.last_updated = datetime.utcnow()
                self.logger.info(f"Updated metadata for document {document_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating document metadata: {e}")
            return False
    
    async def _initialize_rag_client(self):
        """Initialize the MCP RAG server client."""
        try:
            # Placeholder for RAG client initialization
            # In a real implementation, this would connect to the RAG server
            self._rag_server_client = "mock_rag_client"
            self.logger.info("RAG server client initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG client: {e}")
            self._rag_server_client = None
    
    async def _fetch_from_rag_server(self, key: str) -> Optional[Any]:
        """
        Fetch data from RAG server.
        
        Args:
            key: Key to fetch
            
        Returns:
            Fetched data if successful, None otherwise
        """
        try:
            if not self._rag_server_client:
                return None
            
            # Placeholder for RAG server fetch
            # In a real implementation, this would make an HTTP request to the RAG server
            mock_response = {
                "content": f"Mock response for key: {key}",
                "source": "rag_server",
                "confidence": 0.8,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._rag_integration_hits += 1
            return mock_response
            
        except Exception as e:
            self.logger.error(f"Error fetching from RAG server: {e}")
            self._rag_integration_errors += 1
            return None
    
    async def _search_local_knowledge_base(self, query: str, max_results: int) -> List[SearchResult]:
        """
        Search the local knowledge base.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of search results
        """
        try:
            query_embedding = CacheUtils.generate_embedding(query)
            results = []
            
            # Search through all documents
            for document in self._knowledge_base.values():
                similarity = CacheUtils.calculate_similarity(query_embedding, document.embedding)
                
                if similarity >= self._min_relevance_score:
                    result = SearchResult(
                        document=document,
                        similarity_score=similarity,
                        source_relevance=self._calculate_source_relevance(document.source),
                        freshness_score=self._calculate_freshness_score(document),
                        combined_score=similarity  # Simple combination for now
                    )
                    results.append(result)
            
            # Sort by combined score
            results.sort(key=lambda x: x.combined_score, reverse=True)
            return results[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error searching local knowledge base: {e}")
            return []
    
    async def _search_rag_server(self, query: str, max_results: int) -> List[SearchResult]:
        """
        Search the RAG server.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of search results
        """
        try:
            if not self._rag_server_client:
                return []
            
            # Placeholder for RAG server search
            # In a real implementation, this would make an HTTP request to the RAG server
            mock_results = []
            for i in range(min(max_results, 3)):
                mock_document = KnowledgeDocument(
                    document_id=f"rag_doc_{i}",
                    title=f"RAG Document {i}",
                    content=f"Mock RAG content for query: {query}",
                    embedding=[0.1] * 384,  # Mock embedding
                    metadata={"source": "rag_server", "relevance": 0.8 - i * 0.1},
                    source="rag_server",
                    created_at=datetime.utcnow(),
                    last_updated=datetime.utcnow(),
                    access_count=0,
                    relevance_score=0.8 - i * 0.1
                )
                
                result = SearchResult(
                    document=mock_document,
                    similarity_score=0.8 - i * 0.1,
                    source_relevance=1.0,
                    freshness_score=1.0,
                    combined_score=0.8 - i * 0.1
                )
                mock_results.append(result)
            
            return mock_results
            
        except Exception as e:
            self.logger.error(f"Error searching RAG server: {e}")
            return []
    
    async def _combine_and_rank_results(self, local_results: List[SearchResult], 
                                      rag_results: List[SearchResult], 
                                      max_results: int) -> List[SearchResult]:
        """
        Combine and rank results from local and RAG sources.
        
        Args:
            local_results: Results from local knowledge base
            rag_results: Results from RAG server
            max_results: Maximum number of results to return
            
        Returns:
            Combined and ranked results
        """
        try:
            # Combine results
            combined_results = local_results + rag_results
            
            # Remove duplicates based on document ID
            seen_ids = set()
            unique_results = []
            
            for result in combined_results:
                if result.document.document_id not in seen_ids:
                    seen_ids.add(result.document.document_id)
                    unique_results.append(result)
            
            # Sort by combined score
            unique_results.sort(key=lambda x: x.combined_score, reverse=True)
            
            return unique_results[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error combining and ranking results: {e}")
            return local_results[:max_results]
    
    def _is_knowledge_content(self, entry: CacheEntry) -> bool:
        """
        Check if an entry represents knowledge content.
        
        Args:
            entry: Cache entry to check
            
        Returns:
            True if it's knowledge content, False otherwise
        """
        # Simple heuristic: check if content looks like knowledge
        content = str(entry.value).lower()
        
        # Check for knowledge indicators
        knowledge_indicators = ["fact", "information", "data", "reference", "document", "article"]
        is_knowledge = any(indicator in content for indicator in knowledge_indicators)
        
        return is_knowledge
    
    async def _add_to_knowledge_base(self, key: str, entry: CacheEntry):
        """
        Add a cache entry to the knowledge base.
        
        Args:
            key: Cache key
            entry: Cache entry
        """
        try:
            # Create knowledge document
            document = KnowledgeDocument(
                document_id=key,
                title=entry.metadata.get("title", f"Document {key}") if entry.metadata else f"Document {key}",
                content=str(entry.value),
                embedding=entry.embedding or CacheUtils.generate_embedding(str(entry.value)),
                metadata=entry.metadata or {},
                source="cache",
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow(),
                access_count=0,
                relevance_score=0.0
            )
            
            # Store in knowledge base
            self._knowledge_base[key] = document
            
            # Update indexes
            await self._update_document_indexes(document)
            
            self.logger.debug(f"Added entry {key} to knowledge base")
            
        except Exception as e:
            self.logger.error(f"Error adding to knowledge base: {e}")
    
    async def _remove_from_knowledge_base(self, key: str):
        """
        Remove a document from the knowledge base.
        
        Args:
            key: Document key to remove
        """
        try:
            if key in self._knowledge_base:
                document = self._knowledge_base[key]
                
                # Remove from indexes
                await self._remove_from_document_indexes(document)
                
                # Remove from knowledge base
                del self._knowledge_base[key]
                
                self.logger.debug(f"Removed document {key} from knowledge base")
            
        except Exception as e:
            self.logger.error(f"Error removing from knowledge base: {e}")
    
    async def _update_document_indexes(self, document: KnowledgeDocument):
        """
        Update document indexes for a knowledge document.
        
        Args:
            document: Knowledge document to index
        """
        try:
            # Update keyword index
            keywords = self._extract_keywords(document.content)
            for keyword in keywords:
                self._document_index[keyword].append(document.document_id)
            
            # Update source index
            self._source_index[document.source].append(document.document_id)
            
        except Exception as e:
            self.logger.error(f"Error updating document indexes: {e}")
    
    async def _remove_from_document_indexes(self, document: KnowledgeDocument):
        """
        Remove a document from indexes.
        
        Args:
            document: Knowledge document to remove from indexes
        """
        try:
            # Remove from keyword index
            keywords = self._extract_keywords(document.content)
            for keyword in keywords:
                if keyword in self._document_index:
                    self._document_index[keyword].remove(document.document_id)
                    if not self._document_index[keyword]:
                        del self._document_index[keyword]
            
            # Remove from source index
            if document.source in self._source_index:
                self._source_index[document.source].remove(document.document_id)
                if not self._source_index[document.source]:
                    del self._source_index[document.source]
            
        except Exception as e:
            self.logger.error(f"Error removing from document indexes: {e}")
    
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
    
    def _calculate_source_relevance(self, source: str) -> float:
        """
        Calculate source relevance score.
        
        Args:
            source: Document source
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        try:
            # Placeholder source relevance calculation
            source_scores = {
                "rag_server": 1.0,
                "cache": 0.8,
                "manual": 0.6,
                "web": 0.4
            }
            
            return source_scores.get(source, 0.5)
            
        except Exception as e:
            self.logger.error(f"Error calculating source relevance: {e}")
            return 0.5
    
    def _calculate_freshness_score(self, document: KnowledgeDocument) -> float:
        """
        Calculate freshness score for a document.
        
        Args:
            document: Knowledge document
            
        Returns:
            Freshness score (0.0 to 1.0)
        """
        try:
            if document.last_updated is None:
                return 0.0
            
            # Calculate time difference in days
            time_diff = (datetime.utcnow() - document.last_updated).total_seconds() / 86400.0
            
            # Exponential decay for freshness
            freshness_score = 0.7 ** (time_diff / 30.0)  # 30-day half-life
            return freshness_score
            
        except Exception as e:
            self.logger.error(f"Error calculating freshness score: {e}")
            return 0.0
    
    async def _sync_loop(self):
        """Background task for periodic synchronization with RAG server."""
        while self._running:
            try:
                await asyncio.sleep(3600)  # 1 hour
                
                # Sync with RAG server
                await self._sync_with_rag_server()
                
                self.logger.info("Synchronized with RAG server")
                
            except Exception as e:
                self.logger.error(f"Error in sync loop: {e}")
    
    async def _sync_with_rag_server(self):
        """
        Synchronize with RAG server to get latest knowledge.
        """
        try:
            if not self._rag_server_client:
                return
            
            # Placeholder for RAG server sync
            # In a real implementation, this would fetch updates from the RAG server
            self.logger.debug("Syncing with RAG server...")
            
        except Exception as e:
            self.logger.error(f"Error syncing with RAG server: {e}")
    
    async def _cleanup_loop(self):
        """Background task for periodic cleanup."""
        while self._running:
            try:
                await asyncio.sleep(300)  # 5 minutes
                
                # Clean up expired entries
                removed = await self.cleanup_expired()
                
                # Clean up old knowledge documents
                self._cleanup_old_documents()
                
                if removed > 0:
                    self.logger.info(f"Background cleanup removed {removed} expired entries")
                
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
    
    def _cleanup_old_documents(self):
        """Clean up old knowledge documents."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=90)
            
            old_documents = []
            for doc_id, document in self._knowledge_base.items():
                if document.created_at < cutoff_time and document.access_count == 0:
                    old_documents.append(doc_id)
            
            for doc_id in old_documents:
                # Remove knowledge base entry synchronously
                if doc_id in self._knowledge_base:
                    document = self._knowledge_base[doc_id]
                    
                    # Remove from indexes
                    # Remove from indexes synchronously
                    keywords = self._extract_keywords(document.content)
                    for keyword in keywords:
                        if keyword in self._document_index:
                            self._document_index[keyword].remove(document.document_id)
                            if not self._document_index[keyword]:
                                del self._document_index[keyword]
                    
                    # Remove from source index
                    if document.source in self._source_index:
                        self._source_index[document.source].remove(document.document_id)
                        if not self._source_index[document.source]:
                            del self._source_index[document.source]
                    
                    # Remove from knowledge base
                    del self._knowledge_base[doc_id]
            
            if old_documents:
                self.logger.info(f"Cleaned up {len(old_documents)} old knowledge documents")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old documents: {e}")
    
    async def close(self):
        """Clean up resources when the cache is being shut down."""
        try:
            self._running = False
            
            # Cancel background tasks
            if self._sync_task:
                self._sync_task.cancel()
            if self._cleanup_task:
                self._cleanup_task.cancel()
            
            # Wait for tasks to complete
            if self._sync_task:
                await self._sync_task
            if self._cleanup_task:
                await self._cleanup_task
            
            self.logger.info("Global Cache shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Error shutting down Global Cache: {e}")