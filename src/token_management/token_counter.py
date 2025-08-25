"""
Token Counter Module with pg_tiktoken Integration

This module provides comprehensive token counting functionality with pg_tiktoken
integration for accurate token counting aligned with OpenAI models.
"""

import logging
import time
import functools
from typing import List, Dict, Any, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import hashlib
import json

from simba.simba.database.postgres import PostgresDB
from simba.simba.database.token_models import TokenUsage

logger = logging.getLogger(__name__)


class TokenizationModel(Enum):
    """Supported tokenization models."""
    CL100K_BASE = "cl100k_base"  # OpenAI's standard tokenizer
    P50K_BASE = "p50k_base"      # For code, use with gpt-3.5-turbo, gpt-4
    P50K_EDIT = "p50k_edit"      # For edits
    R50K_BASE = "r50k_base"      # Older models like GPT-3


@dataclass
class TokenCountResult:
    """Result of token counting operation."""
    text: str
    token_count: int
    model: TokenizationModel
    method: str  # 'pg_tiktoken' or 'fallback'
    processing_time: float
    cache_hit: bool = False


@dataclass
class BatchTokenCountResult:
    """Result of batch token counting operation."""
    results: List[TokenCountResult]
    total_tokens: int
    total_processing_time: float
    cache_hits: int
    cache_misses: int


class TokenCounter:
    """
    Comprehensive token counting module with pg_tiktoken integration.
    
    Provides accurate token counting using pg_tiktoken when available,
    with fallback estimation and caching for performance.
    """
    
    def __init__(self, db: Optional[PostgresDB] = None, cache_size: int = 1000):
        """
        Initialize the token counter.
        
        Args:
            db: Database instance for pg_tiktoken integration
            cache_size: Maximum number of entries in the token count cache
        """
        self.db = db or PostgresDB()
        self.cache_size = cache_size
        self.token_cache: Dict[str, TokenCountResult] = {}
        self.performance_metrics = {
            'pg_tiktoken_calls': 0,
            'fallback_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_processing_time': 0.0
        }
        
        logger.info(f"TokenCounter initialized with cache size: {cache_size}")
    
    def _generate_cache_key(self, text: str, model: TokenizationModel) -> str:
        """Generate a cache key for the given text and model."""
        # Use SHA256 hash to avoid storing large texts in cache
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        return f"{model.value}_{text_hash}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[TokenCountResult]:
        """Get token count from cache if available."""
        if cache_key in self.token_cache:
            result = self.token_cache[cache_key]
            result.cache_hit = True
            self.performance_metrics['cache_hits'] += 1
            logger.debug(f"Cache hit for key: {cache_key[:16]}...")
            return result
        return None
    
    def _add_to_cache(self, cache_key: str, result: TokenCountResult):
        """Add token count result to cache."""
        # Simple LRU cache implementation
        if len(self.token_cache) >= self.cache_size:
            # Remove the oldest entry (first item in dict)
            oldest_key = next(iter(self.token_cache))
            del self.token_cache[oldest_key]
            logger.debug(f"Cache evicted: {oldest_key[:16]}...")
        
        self.token_cache[cache_key] = result
        self.performance_metrics['cache_misses'] += 1
        logger.debug(f"Cache added for key: {cache_key[:16]}...")
    
    def count_tokens(self, text: str, model: TokenizationModel = TokenizationModel.CL100K_BASE) -> TokenCountResult:
        """
        Count tokens in text using pg_tiktoken if available, fallback to estimation.
        
        Args:
            text: Text to count tokens for
            model: Tokenization model to use
            
        Returns:
            TokenCountResult with token count and metadata
        """
        if not text or not text.strip():
            return TokenCountResult(
                text=text,
                token_count=0,
                model=model,
                method='fallback',
                processing_time=0.0
            )
        
        start_time = time.time()
        cache_key = self._generate_cache_key(text, model)
        
        # Check cache first
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Try pg_tiktoken if available
        if self.db.is_tiktoken_available():
            try:
                token_count = self.db.get_token_count(text)
                method = 'pg_tiktoken'
                self.performance_metrics['pg_tiktoken_calls'] += 1
                logger.debug(f"Used pg_tiktoken for {len(text)} characters, got {token_count} tokens")
            except Exception as e:
                logger.warning(f"pg_tiktoken failed, falling back: {e}")
                token_count = self.estimate_tokens_fallback(text, model)
                method = 'fallback'
                self.performance_metrics['fallback_calls'] += 1
        else:
            # Use fallback estimation
            token_count = self.estimate_tokens_fallback(text, model)
            method = 'fallback'
            self.performance_metrics['fallback_calls'] += 1
        
        processing_time = time.time() - start_time
        self.performance_metrics['total_processing_time'] += processing_time
        
        result = TokenCountResult(
            text=text,
            token_count=int(token_count),
            model=model,
            method=method,
            processing_time=processing_time
        )
        
        # Add to cache
        self._add_to_cache(cache_key, result)
        
        logger.info(f"Token count: {token_count} tokens using {method} for {len(text)} characters")
        return result
    
    def count_tokens_batch(self, texts: List[str], model: TokenizationModel = TokenizationModel.CL100K_BASE) -> BatchTokenCountResult:
        """
        Count tokens for multiple texts efficiently.
        
        Args:
            texts: List of texts to count tokens for
            model: Tokenization model to use
            
        Returns:
            BatchTokenCountResult with individual results and summary
        """
        start_time = time.time()
        results = []
        total_tokens = 0
        cache_hits = 0
        cache_misses = 0
        
        for text in texts:
            result = self.count_tokens(text, model)
            results.append(result)
            total_tokens += result.token_count
            if result.cache_hit:
                cache_hits += 1
            else:
                cache_misses += 1
        
        total_processing_time = time.time() - start_time
        
        return BatchTokenCountResult(
            results=results,
            total_tokens=total_tokens,
            total_processing_time=total_processing_time,
            cache_hits=cache_hits,
            cache_misses=cache_misses
        )
    
    def estimate_tokens_fallback(self, text: str, model: TokenizationModel = TokenizationModel.CL100K_BASE) -> int:
        """
        Fallback token estimation when pg_tiktoken is not available.
        
        Uses various heuristics to estimate token count based on the model.
        
        Args:
            text: Text to estimate tokens for
            model: Tokenization model to use
            
        Returns:
            Estimated token count
        """
        if not text or not text.strip():
            return 0
        
        # Basic word-based estimation (rough approximation)
        words = text.split()
        word_count = len(words)
        
        # Character-based adjustment
        char_count = len(text)
        
        # Model-specific adjustments
        if model == TokenizationModel.CL100K_BASE:
            # OpenAI's standard tokenizer: ~1.3 tokens per word
            estimated_tokens = int(word_count * 1.3)
            # Add adjustment for punctuation and special characters
            punctuation_count = sum(1 for char in text if char in '.,!?;:()[]{}"\'')
            estimated_tokens += int(punctuation_count * 0.1)
        elif model == TokenizationModel.P50K_BASE:
            # Code tokenizer: ~1.5 tokens per word for code
            estimated_tokens = int(word_count * 1.5)
        elif model == TokenizationModel.P50K_EDIT:
            # Edit tokenizer: similar to P50K_BASE but with edit markers
            estimated_tokens = int(word_count * 1.4)
        else:  # R50K_BASE
            # Older tokenizer: ~1.25 tokens per word
            estimated_tokens = int(word_count * 1.25)
        
        # Ensure minimum of 1 token for non-empty text
        return max(1, estimated_tokens)
    
    def get_token_count_for_api(self, text: str, model: TokenizationModel = TokenizationModel.CL100K_BASE) -> Dict[str, Any]:
        """
        Get token count specialized for API responses.
        
        Args:
            text: Text to count tokens for
            model: Tokenization model to use
            
        Returns:
            Dictionary with token count and API-specific metadata
        """
        result = self.count_tokens(text, model)
        
        return {
            'token_count': result.token_count,
            'model': model.value,
            'method': result.method,
            'processing_time': result.processing_time,
            'cache_hit': result.cache_hit,
            'text_length': len(text),
            'text_preview': text[:100] + '...' if len(text) > 100 else text
        }
    
    def get_token_count_for_context(self, text: str, max_context_tokens: int, 
                                   model: TokenizationModel = TokenizationModel.CL100K_BASE) -> Dict[str, Any]:
        """
        Handle context window calculations.
        
        Args:
            text: Text to analyze for context
            max_context_tokens: Maximum context window size
            model: Tokenization model to use
            
        Returns:
            Dictionary with context analysis
        """
        result = self.count_tokens(text, model)
        
        return {
            'token_count': result.token_count,
            'max_context_tokens': max_context_tokens,
            'context_usage_percentage': (result.token_count / max_context_tokens) * 100,
            'remaining_tokens': max(0, max_context_tokens - result.token_count),
            'context_fit': result.token_count <= max_context_tokens,
            'model': model.value,
            'method': result.method
        }
    
    def clear_cache(self):
        """Clear the token count cache."""
        self.token_cache.clear()
        logger.info("Token count cache cleared")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the token counter."""
        total_calls = (self.performance_metrics['pg_tiktoken_calls'] + 
                      self.performance_metrics['fallback_calls'])
        
        return {
            'cache_size': len(self.token_cache),
            'max_cache_size': self.cache_size,
            'total_calls': total_calls,
            'pg_tiktoken_calls': self.performance_metrics['pg_tiktoken_calls'],
            'fallback_calls': self.performance_metrics['fallback_calls'],
            'cache_hits': self.performance_metrics['cache_hits'],
            'cache_misses': self.performance_metrics['cache_misses'],
            'cache_hit_rate': (self.performance_metrics['cache_hits'] / total_calls * 100) if total_calls > 0 else 0,
            'total_processing_time': self.performance_metrics['total_processing_time'],
            'average_processing_time': (self.performance_metrics['total_processing_time'] / total_calls) if total_calls > 0 else 0
        }
    
    def log_token_usage(self, user_id: str, session_id: str, tokens_used: int,
                       api_endpoint: str, priority_level: str = "Medium") -> bool:
        """
        Log token usage to the database.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            tokens_used: Number of tokens used
            api_endpoint: API endpoint used
            priority_level: Priority level ('Low', 'Medium', 'High')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.db.log_token_usage(user_id, session_id, tokens_used, api_endpoint, priority_level)
        except Exception as e:
            logger.error(f"Failed to log token usage: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.clear_cache()


# Convenience function for direct usage
def count_tokens(text: str, model: TokenizationModel = TokenizationModel.CL100K_BASE, 
                db: Optional[PostgresDB] = None) -> TokenCountResult:
    """
    Convenience function to count tokens.
    
    Args:
        text: Text to count tokens for
        model: Tokenization model to use
        db: Database instance (optional)
        
    Returns:
        TokenCountResult with token count and metadata
    """
    counter = TokenCounter(db)
    return counter.count_tokens(text, model)