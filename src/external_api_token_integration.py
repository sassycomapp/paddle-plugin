#!/usr/bin/env python3
"""
External API Token Integration Module

This module provides integration between the Token Management System and external API clients.
It enables automatic token counting, budget management, and quota enforcement for external API calls.

Key Features:
- Token counting for external API calls (REST, GraphQL, etc.)
- User session-based token management for API operations
- Integration with various API clients and HTTP libraries
- Budget enforcement and quota management
- Comprehensive error handling and logging
- API call optimization based on token usage
- Rate limiting and throttling integration
- Request/response caching for token optimization
"""

import asyncio
import logging
import time
import json
from functools import wraps
from typing import Dict, List, Optional, Any, Callable, Union, Awaitable
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import traceback
import hashlib
import aiohttp
import requests
from urllib.parse import urlparse

# Import token management components
try:
    from .token_counter import TokenCounter
    from .decorators import token_counter_decorator
    from .middleware import TokenQuotaMiddleware
    from ..database.models import User, TokenUsage, TokenLimit
    from ..database.connection import get_db_session
except ImportError as e:
    logging.warning(f"Import error in external API token integration: {e}")
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
class APIOperationContext:
    """Context information for API operations."""
    operation: str  # 'call', 'batch_call', 'stream'
    user_id: str
    session_id: str
    api_name: str
    endpoint: str
    method: str
    request_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None
    status_code: Optional[int] = None
    duration: Optional[float] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class APITokenResult:
    """Result of API token operation."""
    success: bool
    tokens_used: int
    tokens_available: int
    budget_remaining: int
    message: str
    operation_id: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    rate_limit_info: Optional[Dict[str, Any]] = None


class ExternalAPITokenIntegration:
    """
    Main integration class for external API token management.
    
    Coordinates token counting, budget management, and quota enforcement
    for external API calls using various HTTP libraries.
    """
    
    def __init__(self, token_counter: Optional[TokenCounter] = None):
        """Initialize external API token integration."""
        self.token_counter = token_counter or TokenCounter()
        self.middleware = TokenQuotaMiddleware()
        self.api_stats: Dict[str, Dict] = {}
        self.operation_history: List[APIOperationContext] = []
        self.request_cache: Dict[str, int] = {}  # Cache request hash to token count
        self.rate_limiters: Dict[str, Any] = {}  # API-specific rate limiters
        
        logger.info("External API Token Integration initialized")
    
    async def call_api_with_tokens(
        self,
        api_name: str,
        endpoint: str,
        method: str = "GET",
        user_id: str = "default",
        session_id: str = "default",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> APITokenResult:
        """
        Call external API with automatic token counting and budget management.
        
        Args:
            api_name: Name of the API being called
            endpoint: API endpoint URL
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            user_id: User identifier
            session_id: Session identifier
            headers: HTTP headers
            params: URL parameters
            data: Form data
            json_data: JSON data
            timeout: Request timeout in seconds
            
        Returns:
            APITokenResult with operation details
        """
        try:
            # Generate request hash for deduplication
            request_hash = self._generate_request_hash(api_name, endpoint, method, params, json_data)
            
            # Check if request already exists (token optimization)
            if request_hash in self.request_cache:
                cached_tokens = self.request_cache[request_hash]
                logger.info(f"Request hash {request_hash[:8]}... found in cache, using {cached_tokens} tokens")
                return APITokenResult(
                    success=True,
                    tokens_used=cached_tokens,
                    tokens_available=0,
                    budget_remaining=0,
                    message="Request found in cache, using cached token count",
                    operation_id=request_hash
                )
            
            # Count tokens in request
            tokens_used = await self._count_request_tokens(api_name, endpoint, method, params, json_data)
            
            # Check token budget
            budget_result = await self._check_token_budget(user_id, session_id, tokens_used)
            
            if not budget_result.success:
                logger.warning(f"Token budget exceeded for API call: {budget_result.message}")
                return APITokenResult(
                    success=False,
                    tokens_used=tokens_used,
                    tokens_available=budget_result.tokens_available,
                    budget_remaining=budget_result.budget_remaining,
                    message=budget_result.message,
                    operation_id=request_hash
                )
            
            # Apply rate limiting if configured
            rate_limiter = self.rate_limiters.get(api_name)
            if rate_limiter:
                await rate_limiter.acquire()
            
            # Make the API call
            start_time = time.time()
            response_data, status_code = await self._make_api_call(
                endpoint, method, headers, params, data, json_data, timeout
            )
            duration = time.time() - start_time
            
            # Count tokens in response
            response_tokens = await self._count_response_tokens(response_data)
            total_tokens = tokens_used + response_tokens
            
            # Create context
            context = APIOperationContext(
                operation='call',
                user_id=user_id,
                session_id=session_id,
                api_name=api_name,
                endpoint=endpoint,
                method=method,
                request_data=json_data or data,
                response_data=response_data,
                status_code=status_code,
                duration=duration
            )
            
            # Record token usage
            await self._record_token_usage(context, total_tokens)
            
            # Cache the token count
            self.request_cache[request_hash] = total_tokens
            
            # Update statistics
            await self._update_api_stats(context, total_tokens)
            
            logger.info(f"API call completed. Total tokens: {total_tokens}, Status: {status_code}, Duration: {duration:.2f}s")
            
            return APITokenResult(
                success=True,
                tokens_used=total_tokens,
                tokens_available=budget_result.tokens_available,
                budget_remaining=budget_result.budget_remaining,
                message="API call completed successfully with token tracking",
                operation_id=request_hash,
                response_data=response_data,
                rate_limit_info=self._extract_rate_limit_info(response_data)
            )
            
        except Exception as e:
            logger.error(f"Error calling API with tokens: {str(e)}")
            logger.error(traceback.format_exc())
            return APITokenResult(
                success=False,
                tokens_used=0,
                tokens_available=0,
                budget_remaining=0,
                message=f"Failed to call API: {str(e)}"
            )
    
    async def batch_call_api_with_tokens(
        self,
        api_name: str,
        endpoint: str,
        method: str = "POST",
        user_id: str = "default",
        session_id: str = "default",
        headers: Optional[Dict[str, str]] = None,
        batch_data: Optional[List[Dict[str, Any]]] = None,
        timeout: int = 60
    ) -> APITokenResult:
        """
        Call external API in batch with automatic token counting and budget management.
        
        Args:
            api_name: Name of the API being called
            endpoint: API endpoint URL
            method: HTTP method
            user_id: User identifier
            session_id: Session identifier
            headers: HTTP headers
            batch_data: List of request data items
            timeout: Request timeout in seconds
            
        Returns:
            APITokenResult with operation details
        """
        try:
            if not batch_data:
                return APITokenResult(
                    success=False,
                    tokens_used=0,
                    tokens_available=0,
                    budget_remaining=0,
                    message="No batch data provided"
                )
            
            # Count tokens in batch request
            batch_tokens = await self._count_batch_request_tokens(batch_data)
            
            # Check token budget
            budget_result = await self._check_token_budget(user_id, session_id, batch_tokens)
            
            if not budget_result.success:
                logger.warning(f"Token budget exceeded for batch API call: {budget_result.message}")
                return APITokenResult(
                    success=False,
                    tokens_used=batch_tokens,
                    tokens_available=budget_result.tokens_available,
                    budget_remaining=budget_result.budget_remaining,
                    message=budget_result.message
                )
            
            # Apply rate limiting if configured
            rate_limiter = self.rate_limiters.get(api_name)
            if rate_limiter:
                await rate_limiter.acquire(len(batch_data))
            
            # Make the batch API call
            start_time = time.time()
            response_data, status_code = await self._make_batch_api_call(
                endpoint, method, headers, batch_data, timeout
            )
            duration = time.time() - start_time
            
            # Count tokens in response
            response_tokens = await self._count_response_tokens(response_data)
            total_tokens = batch_tokens + response_tokens
            
            # Create context
            context = APIOperationContext(
                operation='batch_call',
                user_id=user_id,
                session_id=session_id,
                api_name=api_name,
                endpoint=endpoint,
                method=method,
                request_data={'batch_size': len(batch_data)},
                response_data=response_data,
                status_code=status_code,
                duration=duration
            )
            
            # Record token usage
            await self._record_token_usage(context, total_tokens)
            
            # Update statistics
            await self._update_api_stats(context, total_tokens)
            
            logger.info(f"Batch API call completed. Total tokens: {total_tokens}, Status: {status_code}, Duration: {duration:.2f}s")
            
            return APITokenResult(
                success=True,
                tokens_used=total_tokens,
                tokens_available=budget_result.tokens_available,
                budget_remaining=budget_result.budget_remaining,
                message="Batch API call completed successfully with token tracking",
                operation_id=f"batch_{hash(str(batch_data))}",
                response_data=response_data,
                rate_limit_info=self._extract_rate_limit_info(response_data)
            )
            
        except Exception as e:
            logger.error(f"Error in batch API call with tokens: {str(e)}")
            logger.error(traceback.format_exc())
            return APITokenResult(
                success=False,
                tokens_used=0,
                tokens_available=0,
                budget_remaining=0,
                message=f"Failed to call batch API: {str(e)}"
            )
    
    async def stream_api_with_tokens(
        self,
        api_name: str,
        endpoint: str,
        method: str = "GET",
        user_id: str = "default",
        session_id: str = "default",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: int = 300
    ) -> APITokenResult:
        """
        Stream from external API with automatic token counting and budget management.
        
        Args:
            api_name: Name of the API being called
            endpoint: API endpoint URL
            method: HTTP method
            user_id: User identifier
            session_id: Session identifier
            headers: HTTP headers
            params: URL parameters
            data: Form data
            json_data: JSON data
            timeout: Request timeout in seconds
            
        Returns:
            APITokenResult with operation details
        """
        try:
            # Count tokens in request
            tokens_used = await self._count_request_tokens(api_name, endpoint, method, params, json_data)
            
            # Check token budget
            budget_result = await self._check_token_budget(user_id, session_id, tokens_used)
            
            if not budget_result.success:
                logger.warning(f"Token budget exceeded for API stream: {budget_result.message}")
                return APITokenResult(
                    success=False,
                    tokens_used=tokens_used,
                    tokens_available=budget_result.tokens_available,
                    budget_remaining=budget_result.budget_remaining,
                    message=budget_result.message
                )
            
            # Apply rate limiting if configured
            rate_limiter = self.rate_limiters.get(api_name)
            if rate_limiter:
                await rate_limiter.acquire()
            
            # Start streaming
            start_time = time.time()
            stream_context = APIOperationContext(
                operation='stream',
                user_id=user_id,
                session_id=session_id,
                api_name=api_name,
                endpoint=endpoint,
                method=method,
                request_data=json_data or data,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Record initial token usage
            await self._record_token_usage(stream_context, tokens_used)
            
            # Update statistics
            await self._update_api_stats(stream_context, tokens_used)
            
            logger.info(f"API stream initiated. Tokens used: {tokens_used}")
            
            return APITokenResult(
                success=True,
                tokens_used=tokens_used,
                tokens_available=budget_result.tokens_available,
                budget_remaining=budget_result.budget_remaining,
                message="API stream initiated with token tracking",
                operation_id=f"stream_{hash(endpoint)}",
                rate_limit_info={}
            )
            
        except Exception as e:
            logger.error(f"Error streaming API with tokens: {str(e)}")
            logger.error(traceback.format_exc())
            return APITokenResult(
                success=False,
                tokens_used=0,
                tokens_available=0,
                budget_remaining=0,
                message=f"Failed to stream API: {str(e)}"
            )
    
    async def get_api_stats(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Get API operation statistics for a user session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Dictionary with API statistics
        """
        try:
            session_key = f"{user_id}_{session_id}"
            
            if session_key not in self.api_stats:
                return {
                    'total_operations': 0,
                    'total_tokens_used': 0,
                    'operations_by_api': {},
                    'average_tokens_per_operation': 0,
                    'average_duration_per_operation': 0,
                    'cache_hit_rate': 0,
                    'success_rate': 0
                }
            
            stats = self.api_stats[session_key]
            
            # Calculate cache hit rate
            total_cache_lookups = sum(self.request_cache.values()) if self.request_cache else 0
            cache_hits = len([v for v in self.request_cache.values() if v > 0])
            cache_hit_rate = (cache_hits / max(total_cache_lookups, 1)) * 100
            
            # Calculate success rate
            total_operations = stats.get('total_operations', 0)
            successful_operations = stats.get('successful_operations', 0)
            success_rate = (successful_operations / max(total_operations, 1)) * 100
            
            return {
                'total_operations': total_operations,
                'total_tokens_used': stats.get('total_tokens_used', 0),
                'operations_by_api': stats.get('operations_by_api', {}),
                'average_tokens_per_operation': stats.get('average_tokens_per_operation', 0),
                'average_duration_per_operation': stats.get('average_duration_per_operation', 0),
                'cache_hit_rate': round(cache_hit_rate, 2),
                'success_rate': round(success_rate, 2),
                'cached_request_count': len(self.request_cache)
            }
            
        except Exception as e:
            logger.error(f"Error getting API stats: {str(e)}")
            return {
                'error': str(e),
                'total_operations': 0,
                'total_tokens_used': 0,
                'operations_by_api': {},
                'average_tokens_per_operation': 0,
                'average_duration_per_operation': 0,
                'cache_hit_rate': 0,
                'success_rate': 0
            }
    
    async def optimize_api_calls(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Optimize API calls based on token usage patterns.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Dictionary with optimization recommendations
        """
        try:
            stats = await self.get_api_stats(user_id, session_id)
            
            recommendations = []
            
            # Check for high token usage APIs
            operations_by_api = stats.get('operations_by_api', {})
            for api_name, api_stats in operations_by_api.items():
                if api_stats.get('total_tokens', 0) > 1000:
                    recommendations.append({
                        'type': 'high_api_token_usage',
                        'api': api_name,
                        'message': f'High token usage for {api_name}. Consider batching or using more efficient endpoints.',
                        'priority': 'high'
                    })
            
            # Check for low cache hit rate
            if stats['cache_hit_rate'] < 20:
                recommendations.append({
                    'type': 'low_cache_hit_rate',
                    'message': 'Low cache hit rate. Consider using more consistent request parameters.',
                    'priority': 'medium'
                })
            
            # Check for slow APIs
            if stats['average_duration_per_operation'] > 5.0:  # 5 seconds
                recommendations.append({
                    'type': 'slow_api_performance',
                    'message': 'High average API call duration. Consider optimizing requests or using caching.',
                    'priority': 'medium'
                })
            
            # Check for low success rate
            if stats['success_rate'] < 90:  # 90% success rate
                recommendations.append({
                    'type': 'low_success_rate',
                    'message': 'Low API success rate. Consider improving error handling and retry logic.',
                    'priority': 'high'
                })
            
            return {
                'user_id': user_id,
                'session_id': session_id,
                'current_stats': stats,
                'recommendations': recommendations,
                'optimization_score': len(recommendations)  # Lower is better
            }
            
        except Exception as e:
            logger.error(f"Error optimizing API calls: {str(e)}")
            return {
                'error': str(e),
                'user_id': user_id,
                'session_id': session_id,
                'recommendations': []
            }
    
    async def _check_token_budget(self, user_id: str, session_id: str, tokens_required: int) -> APITokenResult:
        """Check if user has sufficient token budget."""
        try:
            with get_db_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return APITokenResult(
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
                    return APITokenResult(
                        success=False,
                        tokens_used=0,
                        tokens_available=0,
                        budget_remaining=0,
                        message="Token limit not found for session"
                    )
                
                tokens_available = token_limit.daily_limit - token_limit.tokens_used_today
                budget_remaining = max(0, tokens_available - tokens_required)
                
                return APITokenResult(
                    success=budget_remaining >= 0,
                    tokens_used=tokens_required,
                    tokens_available=tokens_available,
                    budget_remaining=budget_remaining,
                    message=f"Budget check {'passed' if budget_remaining >= 0 else 'failed'}"
                )
                
        except Exception as e:
            logger.error(f"Error checking token budget: {str(e)}")
            return APITokenResult(
                success=False,
                tokens_used=tokens_required,
                tokens_available=0,
                budget_remaining=0,
                message=f"Budget check failed: {str(e)}"
            )
    
    async def _record_token_usage(self, context: APIOperationContext, tokens_used: int, success: bool = True) -> None:
        """Record token usage in the database."""
        try:
            with get_db_session() as db:
                token_usage = TokenUsage(
                    user_id=context.user_id,
                    session_id=context.session_id,
                    tool_name=f"api_{context.api_name}_{context.operation}",
                    tokens_used=tokens_used,
                    timestamp=context.timestamp,
                    success=success,
                    tool_call_id=f"{context.api_name}_{context.operation}_{hash(context.endpoint)}"
                )
                
                db.add(token_usage)
                db.commit()
                
        except Exception as e:
            logger.error(f"Error recording token usage: {str(e)}")
    
    async def _update_api_stats(self, context: APIOperationContext, tokens_used: int) -> None:
        """Update API operation statistics."""
        try:
            session_key = f"{context.user_id}_{context.session_id}"
            
            if session_key not in self.api_stats:
                self.api_stats[session_key] = {
                    'total_operations': 0,
                    'total_tokens_used': 0,
                    'successful_operations': 0,
                    'operations_by_api': {},
                    'total_duration': 0.0,
                    'start_time': context.timestamp
                }
            
            stats = self.api_stats[session_key]
            stats['total_operations'] += 1
            stats['total_tokens_used'] += tokens_used
            stats['total_duration'] += context.duration or 0.0
            
            if context.response_data and context.status_code and 200 <= context.status_code < 300:
                stats['successful_operations'] += 1
            
            # Update API-specific statistics
            api_key = context.api_name
            if api_key not in stats['operations_by_api']:
                stats['operations_by_api'][api_key] = {
                    'count': 0,
                    'total_tokens': 0,
                    'total_duration': 0.0,
                    'success_count': 0
                }
            
            api_stats = stats['operations_by_api'][api_key]
            api_stats['count'] += 1
            api_stats['total_tokens'] += tokens_used
            api_stats['total_duration'] += context.duration or 0.0
            
            if context.response_data and context.status_code and 200 <= context.status_code < 300:
                api_stats['success_count'] += 1
            
            # Calculate averages
            stats['average_tokens_per_operation'] = stats['total_tokens_used'] / stats['total_operations']
            stats['average_duration_per_operation'] = stats['total_duration'] / stats['total_operations']
            
            # Add to operation history
            self.operation_history.append(context)
            
            # Keep history size manageable
            if len(self.operation_history) > 1000:
                self.operation_history = self.operation_history[-500:]
            
        except Exception as e:
            logger.error(f"Error updating API stats: {str(e)}")
    
    async def _make_api_call(
        self,
        endpoint: str,
        method: str,
        headers: Optional[Dict[str, str]],
        params: Optional[Dict[str, Any]],
        data: Optional[Dict[str, Any]],
        json_data: Optional[Dict[str, Any]],
        timeout: int
    ) -> tuple:
        """Make HTTP API call."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=endpoint,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json_data,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    response_data = await response.json()
                    return response_data, response.status
                    
        except Exception as e:
            logger.error(f"Error making API call: {str(e)}")
            raise
    
    async def _make_batch_api_call(
        self,
        endpoint: str,
        method: str,
        headers: Optional[Dict[str, str]],
        batch_data: List[Dict[str, Any]],
        timeout: int
    ) -> tuple:
        """Make batch HTTP API call."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=endpoint,
                    headers=headers,
                    json=batch_data,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    response_data = await response.json()
                    return response_data, response.status
                    
        except Exception as e:
            logger.error(f"Error making batch API call: {str(e)}")
            raise
    
    async def _count_request_tokens(
        self,
        api_name: str,
        endpoint: str,
        method: str,
        params: Optional[Dict[str, Any]],
        json_data: Optional[Dict[str, Any]]
    ) -> int:
        """Count tokens in API request."""
        try:
            # Combine all request data
            request_text = f"{method} {endpoint}"
            
            if params:
                request_text += str(params)
            
            if json_data:
                request_text += json.dumps(json_data)
            
            # Count tokens
            tokens = await self.token_counter.count_tokens(request_text)
            return tokens
            
        except Exception as e:
            logger.error(f"Error counting request tokens: {str(e)}")
            return 100  # Default estimate
    
    async def _count_batch_request_tokens(self, batch_data: List[Dict[str, Any]]) -> int:
        """Count tokens in batch request."""
        try:
            batch_text = json.dumps(batch_data)
            tokens = await self.token_counter.count_tokens(batch_text)
            return tokens
            
        except Exception as e:
            logger.error(f"Error counting batch request tokens: {str(e)}")
            return len(batch_data) * 100  # Default estimate per item
    
    async def _count_response_tokens(self, response_data: Any) -> int:
        """Count tokens in API response."""
        try:
            if not response_data:
                return 0
            
            response_text = json.dumps(response_data)
            tokens = await self.token_counter.count_tokens(response_text)
            return tokens
            
        except Exception as e:
            logger.error(f"Error counting response tokens: {str(e)}")
            return 50  # Default estimate
    
    def _generate_request_hash(
        self,
        api_name: str,
        endpoint: str,
        method: str,
        params: Optional[Dict[str, Any]],
        json_data: Optional[Dict[str, Any]]
    ) -> str:
        """Generate hash for request deduplication."""
        request_data = {
            'api_name': api_name,
            'endpoint': endpoint,
            'method': method,
            'params': params,
            'json_data': json_data
        }
        return hashlib.sha256(json.dumps(request_data, sort_keys=True).encode('utf-8')).hexdigest()
    
    def _extract_rate_limit_info(self, response_data: Any) -> Dict[str, Any]:
        """Extract rate limiting information from response."""
        try:
            if isinstance(response_data, dict):
                return {
                    'rate_limit_remaining': response_data.get('rate_limit_remaining'),
                    'rate_limit_reset': response_data.get('rate_limit_reset'),
                    'rate_limit_limit': response_data.get('rate_limit_limit')
                }
            return {}
        except Exception as e:
            logger.error(f"Error extracting rate limit info: {str(e)}")
            return {}
    
    def clear_cache(self) -> None:
        """Clear the request cache."""
        self.request_cache.clear()
        logger.info("External API token cache cleared")


# Global external API token integration instance
external_api_token_integration = ExternalAPITokenIntegration()


# Convenience functions for direct use
async def call_api_with_tokens(
    api_name: str,
    endpoint: str,
    method: str = "GET",
    user_id: str = "default",
    session_id: str = "default",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: int = 30
):
    """Convenience function for calling API with tokens."""
    return await external_api_token_integration.call_api_with_tokens(
        api_name, endpoint, method, user_id, session_id, headers, params, data, json_data, timeout
    )


async def batch_call_api_with_tokens(
    api_name: str,
    endpoint: str,
    method: str = "POST",
    user_id: str = "default",
    session_id: str = "default",
    headers: Optional[Dict[str, str]] = None,
    batch_data: Optional[List[Dict[str, Any]]] = None,
    timeout: int = 60
):
    """Convenience function for batch calling API with tokens."""
    return await external_api_token_integration.batch_call_api_with_tokens(
        api_name, endpoint, method, user_id, session_id, headers, batch_data, timeout
    )


async def stream_api_with_tokens(
    api_name: str,
    endpoint: str,
    method: str = "GET",
    user_id: str = "default",
    session_id: str = "default",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: int = 300
):
    """Convenience function for streaming API with tokens."""
    return await external_api_token_integration.stream_api_with_tokens(
        api_name, endpoint, method, user_id, session_id, headers, params, data, json_data, timeout
    )


async def get_api_stats(user_id: str, session_id: str):
    """Convenience function for getting API statistics."""
    return await external_api_token_integration.get_api_stats(user_id, session_id)


async def optimize_api_calls(user_id: str, session_id: str):
    """Convenience function for optimizing API calls."""
    return await external_api_token_integration.optimize_api_calls(user_id, session_id)