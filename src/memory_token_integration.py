#!/usr/bin/env python3
"""
Memory Token Integration Module

This module provides integration between the Token Management System and memory systems.
It enables automatic token counting, budget management, and quota enforcement for memory operations.

Key Features:
- Token counting for memory storage and retrieval operations
- User session-based token management for memory operations
- Integration with various memory backends (SQLite-vec, PGvector, etc.)
- Budget enforcement and quota management
- Comprehensive error handling and logging
- Memory operation optimization based on token usage
"""

import asyncio
import logging
import time
from functools import wraps
from typing import Dict, List, Optional, Any, Callable, Union, Awaitable
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import traceback
import hashlib

# Import token management components
try:
    from .token_counter import TokenCounter
    from .decorators import token_counter_decorator
    from .middleware import TokenQuotaMiddleware
    from ..database.models import User, TokenUsage, TokenLimit
    from ..database.connection import get_db_session
except ImportError as e:
    logging.warning(f"Import error in memory token integration: {e}")
    # Create placeholder classes for missing dependencies
    class TokenCounter:
        async def count_tokens(self, text: str) -> int:
            return len(text.split())  # Simple word count as fallback
        
        async def count_tokens_batch(self, texts: List[str]) -> List[int]:
            return [len(text.split()) for text in texts]
    
    class TokenQuotaMiddleware:
        pass
    
    class User:
        id = "default_user"
    
    class TokenUsage:
        def __init__(self, *args, **kwargs):
            pass
    
    class TokenLimit:
        daily_limit = 10000
        tokens_used_today = 0
    
    def get_db_session():
        class MockSession:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def query(self, *args):
                return self
            def filter(self, *args):
                return self
            def first(self):
                return None
            def add(self, obj):
                pass
            def commit(self):
                pass
        return MockSession()

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class MemoryOperationContext:
    """Context information for memory operations."""
    operation: str  # 'store', 'retrieve', 'delete', 'search'
    user_id: str
    session_id: str
    memory_type: str
    content_hash: Optional[str] = None
    query: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class MemoryTokenResult:
    """Result of memory token operation."""
    success: bool
    tokens_used: int
    tokens_available: int
    budget_remaining: int
    message: str
    operation_id: Optional[str] = None


class MemoryTokenIntegration:
    """
    Main integration class for memory token management.
    
    Coordinates token counting, budget management, and quota enforcement
    for memory storage and retrieval operations.
    """
    
    def __init__(self, token_counter: Optional[TokenCounter] = None):
        """Initialize memory token integration."""
        self.token_counter = token_counter or TokenCounter()
        self.middleware = TokenQuotaMiddleware()
        self.memory_stats: Dict[str, Dict] = {}
        self.operation_history: List[MemoryOperationContext] = []
        self.content_cache: Dict[str, int] = {}  # Cache content hash to token count
        
        logger.info("Memory Token Integration initialized")
    
    async def store_memory_with_tokens(
        self,
        content: str,
        user_id: str,
        session_id: str,
        memory_type: str = "note",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryTokenResult:
        """
        Store memory with automatic token counting and budget management.
        
        Args:
            content: Memory content to store
            user_id: User identifier
            session_id: Session identifier
            memory_type: Type of memory (note, decision, task, reference)
            tags: Optional tags for the memory
            metadata: Additional metadata
            
        Returns:
            MemoryTokenResult with operation details
        """
        try:
            # Generate content hash for deduplication
            content_hash = self._generate_content_hash(content)
            
            # Check if content already exists (token optimization)
            if content_hash in self.content_cache:
                cached_tokens = self.content_cache[content_hash]
                logger.info(f"Content hash {content_hash[:8]}... found in cache, using {cached_tokens} tokens")
                return MemoryTokenResult(
                    success=True,
                    tokens_used=cached_tokens,
                    tokens_available=0,
                    budget_remaining=0,
                    message="Content found in cache, using cached token count",
                    operation_id=content_hash
                )
            
            # Count tokens in content
            tokens_used = await self.token_counter.count_tokens(content)
            
            # Check token budget
            budget_result = await self._check_token_budget(user_id, session_id, tokens_used)
            
            if not budget_result.success:
                logger.warning(f"Token budget exceeded for memory storage: {budget_result.message}")
                return MemoryTokenResult(
                    success=False,
                    tokens_used=tokens_used,
                    tokens_available=budget_result.tokens_available,
                    budget_remaining=budget_result.budget_remaining,
                    message=budget_result.message,
                    operation_id=content_hash
                )
            
            # Create context
            context = MemoryOperationContext(
                operation='store',
                user_id=user_id,
                session_id=session_id,
                memory_type=memory_type,
                content_hash=content_hash,
                tags=tags,
                metadata=metadata or {}
            )
            
            # Record token usage
            await self._record_token_usage(context, tokens_used)
            
            # Cache the token count
            self.content_cache[content_hash] = tokens_used
            
            # Update statistics
            await self._update_memory_stats(context, tokens_used)
            
            logger.info(f"Memory stored successfully. Tokens used: {tokens_used}, Content hash: {content_hash[:8]}...")
            
            return MemoryTokenResult(
                success=True,
                tokens_used=tokens_used,
                tokens_available=budget_result.tokens_available,
                budget_remaining=budget_result.budget_remaining,
                message="Memory stored successfully with token tracking",
                operation_id=content_hash
            )
            
        except Exception as e:
            logger.error(f"Error storing memory with tokens: {str(e)}")
            logger.error(traceback.format_exc())
            return MemoryTokenResult(
                success=False,
                tokens_used=0,
                tokens_available=0,
                budget_remaining=0,
                message=f"Failed to store memory: {str(e)}"
            )
    
    async def retrieve_memory_with_tokens(
        self,
        query: str,
        user_id: str,
        session_id: str,
        n_results: int = 5,
        min_similarity: float = 0.0,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> MemoryTokenResult:
        """
        Retrieve memories with automatic token counting and budget management.
        
        Args:
            query: Search query for semantic similarity
            user_id: User identifier
            session_id: Session identifier
            n_results: Maximum number of results to return
            min_similarity: Minimum similarity score threshold
            memory_type: Optional memory type filter
            tags: Optional tags filter
            
        Returns:
            MemoryTokenResult with operation details
        """
        try:
            # Count tokens in query
            query_tokens = await self.token_counter.count_tokens(query)
            
            # Estimate retrieval tokens (based on expected results)
            estimated_retrieval_tokens = query_tokens + (n_results * 50)  # 50 tokens per result
            
            # Check token budget
            budget_result = await self._check_token_budget(user_id, session_id, estimated_retrieval_tokens)
            
            if not budget_result.success:
                logger.warning(f"Token budget exceeded for memory retrieval: {budget_result.message}")
                return MemoryTokenResult(
                    success=False,
                    tokens_used=query_tokens,
                    tokens_available=budget_result.tokens_available,
                    budget_remaining=budget_result.budget_remaining,
                    message=budget_result.message
                )
            
            # Create context
            context = MemoryOperationContext(
                operation='retrieve',
                user_id=user_id,
                session_id=session_id,
                memory_type=memory_type or 'any',
                query=query,
                tags=tags
            )
            
            # Record token usage (query tokens only, results will be counted separately)
            await self._record_token_usage(context, query_tokens)
            
            # Update statistics
            await self._update_memory_stats(context, query_tokens)
            
            logger.info(f"Memory retrieval initiated. Query tokens: {query_tokens}, Estimated total: {estimated_retrieval_tokens}")
            
            return MemoryTokenResult(
                success=True,
                tokens_used=query_tokens,
                tokens_available=budget_result.tokens_available,
                budget_remaining=budget_result.budget_remaining,
                message="Memory retrieval initiated with token tracking",
                operation_id=f"retrieve_{hash(query)}"
            )
            
        except Exception as e:
            logger.error(f"Error retrieving memories with tokens: {str(e)}")
            logger.error(traceback.format_exc())
            return MemoryTokenResult(
                success=False,
                tokens_used=0,
                tokens_available=0,
                budget_remaining=0,
                message=f"Failed to retrieve memories: {str(e)}"
            )
    
    async def delete_memory_with_tokens(
        self,
        content_hash: str,
        user_id: str,
        session_id: str
    ) -> MemoryTokenResult:
        """
        Delete memory with automatic token counting and budget management.
        
        Args:
            content_hash: Hash of the memory content to delete
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            MemoryTokenResult with operation details
        """
        try:
            # Get cached token count for content hash
            tokens_used = self.content_cache.get(content_hash, 0)
            
            # If not in cache, estimate deletion tokens
            if tokens_used == 0:
                tokens_used = 30  # Default estimate for deletion
            
            # Check token budget (deletion typically doesn't consume many tokens)
            budget_result = await self._check_token_budget(user_id, session_id, tokens_used)
            
            if not budget_result.success:
                logger.warning(f"Token budget exceeded for memory deletion: {budget_result.message}")
                return MemoryTokenResult(
                    success=False,
                    tokens_used=tokens_used,
                    tokens_available=budget_result.tokens_available,
                    budget_remaining=budget_result.budget_remaining,
                    message=budget_result.message,
                    operation_id=content_hash
                )
            
            # Create context
            context = MemoryOperationContext(
                operation='delete',
                user_id=user_id,
                session_id=session_id,
                memory_type='any',
                content_hash=content_hash
            )
            
            # Record token usage
            await self._record_token_usage(context, tokens_used)
            
            # Remove from cache
            if content_hash in self.content_cache:
                del self.content_cache[content_hash]
            
            # Update statistics
            await self._update_memory_stats(context, tokens_used)
            
            logger.info(f"Memory deletion initiated. Tokens used: {tokens_used}, Content hash: {content_hash[:8]}...")
            
            return MemoryTokenResult(
                success=True,
                tokens_used=tokens_used,
                tokens_available=budget_result.tokens_available,
                budget_remaining=budget_result.budget_remaining,
                message="Memory deletion initiated with token tracking",
                operation_id=content_hash
            )
            
        except Exception as e:
            logger.error(f"Error deleting memory with tokens: {str(e)}")
            logger.error(traceback.format_exc())
            return MemoryTokenResult(
                success=False,
                tokens_used=0,
                tokens_available=0,
                budget_remaining=0,
                message=f"Failed to delete memory: {str(e)}"
            )
    
    async def search_memories_with_tokens(
        self,
        query: str,
        user_id: str,
        session_id: str,
        n_results: int = 5,
        search_type: str = "semantic",
        filters: Optional[Dict[str, Any]] = None
    ) -> MemoryTokenResult:
        """
        Search memories with automatic token counting and budget management.
        
        Args:
            query: Search query
            user_id: User identifier
            session_id: Session identifier
            n_results: Maximum number of results to return
            search_type: Type of search (semantic, keyword, hybrid)
            filters: Additional search filters
            
        Returns:
            MemoryTokenResult with operation details
        """
        try:
            # Count tokens in query
            query_tokens = await self.token_counter.count_tokens(query)
            
            # Estimate search tokens based on search type
            if search_type == "semantic":
                estimated_tokens = query_tokens + (n_results * 75)  # Higher cost for semantic search
            elif search_type == "keyword":
                estimated_tokens = query_tokens + (n_results * 25)  # Lower cost for keyword search
            else:  # hybrid
                estimated_tokens = query_tokens + (n_results * 50)  # Medium cost for hybrid search
            
            # Check token budget
            budget_result = await self._check_token_budget(user_id, session_id, estimated_tokens)
            
            if not budget_result.success:
                logger.warning(f"Token budget exceeded for memory search: {budget_result.message}")
                return MemoryTokenResult(
                    success=False,
                    tokens_used=query_tokens,
                    tokens_available=budget_result.tokens_available,
                    budget_remaining=budget_result.budget_remaining,
                    message=budget_result.message
                )
            
            # Create context
            context = MemoryOperationContext(
                operation='search',
                user_id=user_id,
                session_id=session_id,
                memory_type='any',
                query=query,
                metadata={'search_type': search_type, 'filters': filters or {}}
            )
            
            # Record token usage
            await self._record_token_usage(context, query_tokens)
            
            # Update statistics
            await self._update_memory_stats(context, query_tokens)
            
            logger.info(f"Memory search initiated. Query tokens: {query_tokens}, Estimated total: {estimated_tokens}")
            
            return MemoryTokenResult(
                success=True,
                tokens_used=query_tokens,
                tokens_available=budget_result.tokens_available,
                budget_remaining=budget_result.budget_remaining,
                message="Memory search initiated with token tracking",
                operation_id=f"search_{hash(query)}"
            )
            
        except Exception as e:
            logger.error(f"Error searching memories with tokens: {str(e)}")
            logger.error(traceback.format_exc())
            return MemoryTokenResult(
                success=False,
                tokens_used=0,
                tokens_available=0,
                budget_remaining=0,
                message=f"Failed to search memories: {str(e)}"
            )
    
    async def get_memory_stats(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Get memory operation statistics for a user session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Dictionary with memory statistics
        """
        try:
            session_key = f"{user_id}_{session_id}"
            
            if session_key not in self.memory_stats:
                return {
                    'total_operations': 0,
                    'total_tokens_used': 0,
                    'operations_by_type': {},
                    'average_tokens_per_operation': 0,
                    'cache_hit_rate': 0
                }
            
            stats = self.memory_stats[session_key]
            
            # Calculate cache hit rate
            total_cache_lookups = sum(self.content_cache.values()) if self.content_cache else 0
            cache_hits = len([v for v in self.content_cache.values() if v > 0])
            cache_hit_rate = (cache_hits / max(total_cache_lookups, 1)) * 100
            
            return {
                'total_operations': stats.get('total_operations', 0),
                'total_tokens_used': stats.get('total_tokens_used', 0),
                'operations_by_type': stats.get('operations_by_type', {}),
                'average_tokens_per_operation': stats.get('average_tokens_per_operation', 0),
                'cache_hit_rate': round(cache_hit_rate, 2),
                'cached_content_count': len(self.content_cache)
            }
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {str(e)}")
            return {
                'error': str(e),
                'total_operations': 0,
                'total_tokens_used': 0,
                'operations_by_type': {},
                'average_tokens_per_operation': 0,
                'cache_hit_rate': 0
            }
    
    async def optimize_memory_operations(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Optimize memory operations based on token usage patterns.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Dictionary with optimization recommendations
        """
        try:
            stats = await self.get_memory_stats(user_id, session_id)
            
            recommendations = []
            
            # Check for high token usage operations
            if stats['total_tokens_used'] > 1000:
                recommendations.append({
                    'type': 'high_token_usage',
                    'message': 'High token usage detected. Consider batching operations or using more concise content.',
                    'priority': 'high'
                })
            
            # Check for low cache hit rate
            if stats['cache_hit_rate'] < 20:
                recommendations.append({
                    'type': 'low_cache_hit_rate',
                    'message': 'Low cache hit rate. Consider using more consistent content formatting.',
                    'priority': 'medium'
                })
            
            # Check for frequent deletion operations
            operations_by_type = stats.get('operations_by_type', {})
            if operations_by_type.get('delete', 0) > operations_by_type.get('store', 0) * 2:
                recommendations.append({
                    'type': 'high_deletion_rate',
                    'message': 'High deletion rate compared to storage. Consider reviewing content retention policies.',
                    'priority': 'medium'
                })
            
            return {
                'user_id': user_id,
                'session_id': session_id,
                'current_stats': stats,
                'recommendations': recommendations,
                'optimization_score': len(recommendations)  # Lower is better
            }
            
        except Exception as e:
            logger.error(f"Error optimizing memory operations: {str(e)}")
            return {
                'error': str(e),
                'user_id': user_id,
                'session_id': session_id,
                'recommendations': []
            }
    
    async def _check_token_budget(self, user_id: str, session_id: str, tokens_required: int) -> MemoryTokenResult:
        """Check if user has sufficient token budget."""
        try:
            with get_db_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return MemoryTokenResult(
                        success=False,
                        tokens_used=0,
                        tokens_available=0,
                        budget_remaining=0,
                        message="User not found"
                    )
                
                token_limit = db.query(TokenLimit).filter(
                    getattr(TokenLimit, 'user_id', None) == user_id,
                    getattr(TokenLimit, 'session_id', None) == session_id
                ).first()
                
                if not token_limit:
                    return MemoryTokenResult(
                        success=False,
                        tokens_used=0,
                        tokens_available=0,
                        budget_remaining=0,
                        message="Token limit not found for session"
                    )
                
                tokens_available = token_limit.daily_limit - token_limit.tokens_used_today
                budget_remaining = max(0, tokens_available - tokens_required)
                
                return MemoryTokenResult(
                    success=budget_remaining >= 0,
                    tokens_used=tokens_required,
                    tokens_available=tokens_available,
                    budget_remaining=budget_remaining,
                    message=f"Budget check {'passed' if budget_remaining >= 0 else 'failed'}"
                )
                
        except Exception as e:
            logger.error(f"Error checking token budget: {str(e)}")
            return MemoryTokenResult(
                success=False,
                tokens_used=tokens_required,
                tokens_available=0,
                budget_remaining=0,
                message=f"Budget check failed: {str(e)}"
            )
    
    async def _record_token_usage(self, context: MemoryOperationContext, tokens_used: int, success: bool = True) -> None:
        """Record token usage in the database."""
        try:
            with get_db_session() as db:
                token_usage = TokenUsage(
                    user_id=context.user_id,
                    session_id=context.session_id,
                    tool_name=f"memory_{context.operation}",
                    tokens_used=tokens_used,
                    timestamp=context.timestamp,
                    success=success,
                    tool_call_id=context.content_hash or f"{context.operation}_{hash(context.query)}"
                )
                
                db.add(token_usage)
                db.commit()
                
        except Exception as e:
            logger.error(f"Error recording token usage: {str(e)}")
    
    async def _update_memory_stats(self, context: MemoryOperationContext, tokens_used: int) -> None:
        """Update memory operation statistics."""
        try:
            session_key = f"{context.user_id}_{context.session_id}"
            
            if session_key not in self.memory_stats:
                self.memory_stats[session_key] = {
                    'total_operations': 0,
                    'total_tokens_used': 0,
                    'operations_by_type': {},
                    'start_time': context.timestamp
                }
            
            stats = self.memory_stats[session_key]
            stats['total_operations'] += 1
            stats['total_tokens_used'] += tokens_used
            
            # Update operation type statistics
            op_type = context.operation
            if op_type not in stats['operations_by_type']:
                stats['operations_by_type'][op_type] = 0
            stats['operations_by_type'][op_type] += 1
            
            # Calculate average tokens per operation
            stats['average_tokens_per_operation'] = stats['total_tokens_used'] / stats['total_operations']
            
            # Add to operation history
            self.operation_history.append(context)
            
            # Keep history size manageable
            if len(self.operation_history) > 1000:
                self.operation_history = self.operation_history[-500:]
            
        except Exception as e:
            logger.error(f"Error updating memory stats: {str(e)}")
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate hash for content deduplication."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def clear_cache(self) -> None:
        """Clear the content cache."""
        self.content_cache.clear()
        logger.info("Memory token cache cleared")


# Global memory token integration instance
memory_token_integration = MemoryTokenIntegration()


# Convenience functions for direct use
async def store_memory_with_tokens(content: str, user_id: str, session_id: str, memory_type: str = "note", tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None):
    """Convenience function for storing memory with tokens."""
    return await memory_token_integration.store_memory_with_tokens(content, user_id, session_id, memory_type, tags, metadata)


async def retrieve_memory_with_tokens(query: str, user_id: str, session_id: str, n_results: int = 5, min_similarity: float = 0.0, memory_type: Optional[str] = None, tags: Optional[List[str]] = None):
    """Convenience function for retrieving memories with tokens."""
    return await memory_token_integration.retrieve_memory_with_tokens(query, user_id, session_id, n_results, min_similarity, memory_type, tags)


async def delete_memory_with_tokens(content_hash: str, user_id: str, session_id: str):
    """Convenience function for deleting memory with tokens."""
    return await memory_token_integration.delete_memory_with_tokens(content_hash, user_id, session_id)


async def search_memories_with_tokens(query: str, user_id: str, session_id: str, n_results: int = 5, search_type: str = "semantic", filters: Optional[Dict[str, Any]] = None):
    """Convenience function for searching memories with tokens."""
    return await memory_token_integration.search_memories_with_tokens(query, user_id, session_id, n_results, search_type, filters)


async def get_memory_stats(user_id: str, session_id: str):
    """Convenience function for getting memory statistics."""
    return await memory_token_integration.get_memory_stats(user_id, session_id)


async def optimize_memory_operations(user_id: str, session_id: str):
    """Convenience function for optimizing memory operations."""
    return await memory_token_integration.optimize_memory_operations(user_id, session_id)