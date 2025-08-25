"""
Middleware for Token Counting API Integration

This module provides middleware components for integrating token counting
into API frameworks and request/response handling.
"""

import logging
import time
import json
from typing import Callable, Any, Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

# Optional imports for FastAPI integration
FASTAPI_AVAILABLE = False
try:
    from fastapi import Request, Response, HTTPException
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    # Create dummy classes for when FastAPI is not available
    class Url:
        def __init__(self):
            self.path = '/'
    
    class Request:
        def __init__(self):
            self.method = "GET"
            self.url = Url()
            self.headers = {}
            self.query_params = {}
            self.cookies = {}
            self.state = type('State', (), {})()
        
        async def body(self):
            return b'{"dummy": "body"}'
        
        async def form(self):
            return {}
    
    class Response:
        def __init__(self):
            self.status_code = 200
            self.headers = {}
            self._body_chunks = [b'{"dummy": "response"}']
            self.body_iterator = self._create_async_iterator()
        
        def _create_async_iterator(self):
            async def async_iterator():
                for chunk in self._body_chunks:
                    yield chunk
            return async_iterator()
        
        def set_body(self, body_bytes):
            self._body_chunks = [body_bytes]
            self.body_iterator = self._create_async_iterator()
    
    class HTTPException(Exception):
        def __init__(self, status_code, detail):
            self.status_code = status_code
            self.detail = detail
    
    class BaseHTTPMiddleware:
        def __init__(self, app):
            self.app = app
        async def dispatch(self, request, call_next):
            return await call_next(request)
    
    class JSONResponse:
        def __init__(self, content, status_code):
            self.content = content
            self.status_code = status_code

from .token_counter import TokenCounter, TokenizationModel, TokenCountResult
from .decorators import TokenUsageRecord

logger = logging.getLogger(__name__)


@dataclass
class APITokenUsage:
    """API token usage record."""
    endpoint: str
    method: str
    user_id: Optional[str]
    session_id: Optional[str]
    input_tokens: int
    output_tokens: int
    total_tokens: int
    processing_time: float
    timestamp: datetime
    status_code: int
    model: TokenizationModel


class TokenCountingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic token counting of API requests and responses.
    
    This middleware intercepts API requests and responses to count tokens
    and log usage to the database.
    """
    
    def __init__(self, app, token_counter: Optional[TokenCounter] = None,
                 model: TokenizationModel = TokenizationModel.CL100K_BASE,
                 exclude_paths: Optional[List[str]] = None,
                 include_methods: Optional[List[str]] = None):
        """
        Initialize the token counting middleware.
        
        Args:
            app: FastAPI application
            token_counter: TokenCounter instance (optional)
            model: Tokenization model to use
            exclude_paths: List of paths to exclude from token counting
            include_methods: List of HTTP methods to include (None means all)
        """
        if not FASTAPI_AVAILABLE:
            logger.warning("FastAPI not available, TokenCountingMiddleware will be disabled")
            app = None
        
        super().__init__(app)
        self.token_counter = token_counter or TokenCounter()
        self.model = model
        self.exclude_paths = exclude_paths or ['/health', '/metrics', '/docs', '/redoc']
        self.include_methods = include_methods or ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        
        logger.info(f"TokenCountingMiddleware initialized with model: {model.value}")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and count tokens.
        
        Args:
            request: FastAPI request
            call_next: Next middleware in chain
            
        Returns:
            Response with token usage information
        """
        # Check if we should skip token counting for this request
        if self._should_skip_token_counting(request):
            return await call_next(request)
        
        start_time = time.time()
        user_id = self._extract_user_id(request)
        session_id = self._extract_session_id(request)
        
        # Count input tokens
        input_tokens = await self._count_input_tokens(request)
        
        # Process the request
        response = await call_next(request)
        
        # Count output tokens
        output_tokens = await self._count_output_tokens(response)
        
        # Calculate metrics
        processing_time = time.time() - start_time
        total_tokens = input_tokens + output_tokens
        
        # Log token usage
        if total_tokens > 0:
            await self._log_api_token_usage(
                request=request,
                response=response,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                processing_time=processing_time,
                user_id=user_id,
                session_id=session_id
            )
        
        # Add token usage header to response
        response.headers['X-Token-Usage'] = str(total_tokens)
        response.headers['X-Token-Input'] = str(input_tokens)
        response.headers['X-Token-Output'] = str(output_tokens)
        response.headers['X-Token-Processing-Time'] = f"{processing_time:.3f}"
        
        return response
    
    def _should_skip_token_counting(self, request: Request) -> bool:
        """Check if token counting should be skipped for this request."""
        # Check method
        if request.method not in self.include_methods:
            return True
        
        # Check path
        request_path = request.url.path
        for exclude_path in self.exclude_paths:
            if request_path.startswith(exclude_path):
                return True
        
        return False
    
    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request."""
        # Try common user ID locations
        user_id = None
        
        # From headers
        user_id = request.headers.get('X-User-ID') or request.headers.get('X-Auth-User')
        
        # From query parameters
        if not user_id:
            user_id = request.query_params.get('user_id')
        
        # From cookies
        if not user_id:
            user_id = request.cookies.get('user_id')
        
        # From request state (set by auth middleware)
        if not user_id:
            user_id = getattr(request.state, 'user_id', None)
        
        return user_id
    
    def _extract_session_id(self, request: Request) -> Optional[str]:
        """Extract session ID from request."""
        # Try common session ID locations
        session_id = None
        
        # From headers
        session_id = request.headers.get('X-Session-ID') or request.headers.get('X-Auth-Session')
        
        # From query parameters
        if not session_id:
            session_id = request.query_params.get('session_id')
        
        # From cookies
        if not session_id:
            session_id = request.cookies.get('session_id')
        
        # From request state (set by session middleware)
        if not session_id:
            session_id = getattr(request.state, 'session_id', None)
        
        return session_id
    
    async def _count_input_tokens(self, request: Request) -> int:
        """Count tokens in the request body."""
        try:
            # For GET requests, count query parameters
            if request.method == 'GET':
                query_str = str(request.query_params)
                result = self.token_counter.count_tokens(query_str, self.model)
                return result.token_count
            
            # For other methods, try to read the body
            content_type = request.headers.get('content-type', '')
            
            if 'application/json' in content_type:
                try:
                    body = await request.body()
                    body_str = body.decode('utf-8')
                    result = self.token_counter.count_tokens(body_str, self.model)
                    return result.token_count
                except Exception as e:
                    logger.warning(f"Failed to count JSON request tokens: {e}")
            
            elif 'application/x-www-form-urlencoded' in content_type:
                try:
                    form_data = await request.form()
                    form_str = str(form_data)
                    result = self.token_counter.count_tokens(form_str, self.model)
                    return result.token_count
                except Exception as e:
                    logger.warning(f"Failed to count form request tokens: {e}")
            
            # For other content types, count a basic representation
            try:
                body = await request.body()
                body_str = body.decode('utf-8', errors='ignore')
                result = self.token_counter.count_tokens(body_str, self.model)
                return result.token_count
            except Exception as e:
                logger.warning(f"Failed to count generic request tokens: {e}")
        
        except Exception as e:
            logger.warning(f"Error counting input tokens: {e}")
        
        return 0
    
    async def _count_output_tokens(self, response: Response) -> int:
        """Count tokens in the response body."""
        try:
            # Only count JSON responses
            content_type = response.headers.get('content-type', '')
            if 'application/json' not in content_type:
                return 0
            
            # Get response body
            body = b''
            async for chunk in response.body_iterator:
                body += chunk
            
            # Count tokens
            body_str = body.decode('utf-8')
            result = self.token_counter.count_tokens(body_str, self.model)
            
            # Restore response body
            response.set_body(body)
            
            return result.token_count
        
        except Exception as e:
            logger.warning(f"Error counting output tokens: {e}")
            return 0
    
    async def _log_api_token_usage(self, request: Request, response: Response,
                                 input_tokens: int, output_tokens: int,
                                 total_tokens: int, processing_time: float,
                                 user_id: Optional[str], session_id: Optional[str]):
        """Log API token usage to the database."""
        try:
            usage_record = APITokenUsage(
                endpoint=request.url.path,
                method=request.method,
                user_id=user_id,
                session_id=session_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                processing_time=processing_time,
                timestamp=datetime.now(),
                status_code=response.status_code,
                model=self.model
            )
            
            # Log to database
            self.token_counter.log_token_usage(
                user_id=user_id or "anonymous",
                session_id=session_id or "anonymous",
                tokens_used=total_tokens,
                api_endpoint=f"{request.method} {request.url.path}",
                priority_level=self._get_priority_level(response.status_code)
            )
            
            logger.info(f"API token usage logged: {total_tokens} tokens for {request.method} {request.url.path}")
        
        except Exception as e:
            logger.warning(f"Failed to log API token usage: {e}")
    
    def _get_priority_level(self, status_code: int) -> str:
        """Get priority level based on HTTP status code."""
        if 200 <= status_code < 300:
            return "Low"  # Successful requests are lower priority
        elif 400 <= status_code < 500:
            return "Medium"  # Client errors are medium priority
        elif 500 <= status_code < 600:
            return "High"  # Server errors are high priority
        else:
            return "Medium"


class TokenQuotaMiddleware(BaseHTTPMiddleware):
    """
    Middleware for enforcing token quotas and limits.
    
    This middleware checks if users have sufficient token quota
    before processing API requests.
    """
    
    def __init__(self, app, token_counter: Optional[TokenCounter] = None,
                 default_quota: int = 10000, quota_header: str = "X-Token-Quota"):
        """
        Initialize the token quota middleware.
        
        Args:
            app: FastAPI application
            token_counter: TokenCounter instance (optional)
            default_quota: Default token quota for users
            quota_header: Header name for quota information
        """
        if not FASTAPI_AVAILABLE:
            logger.warning("FastAPI not available, TokenQuotaMiddleware will be disabled")
            app = None
        
        super().__init__(app)
        self.token_counter = token_counter or TokenCounter()
        self.default_quota = default_quota
        self.quota_header = quota_header
        
        logger.info(f"TokenQuotaMiddleware initialized with default quota: {default_quota}")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and check token quota.
        
        Args:
            request: FastAPI request
            call_next: Next middleware in chain
            
        Returns:
            Response or error response if quota exceeded
        """
        user_id = self._extract_user_id(request)
        
        if not user_id:
            # No user ID, skip quota check
            return await call_next(request)
        
        # Estimate tokens needed for this request
        estimated_tokens = await self._estimate_request_tokens(request)
        
        # Check quota
        quota_check = self.token_counter.db.check_token_quota(
            user_id=user_id,
            tokens_requested=estimated_tokens,
            priority_level="Medium"
        )
        
        if not quota_check['allowed']:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Token quota exceeded",
                    "message": quota_check['reason'],
                    "remaining_tokens": quota_check['remaining_tokens'],
                    "requested_tokens": estimated_tokens,
                    "quota_info": quota_check
                }
            )
        
        # Add quota information to response
        response = await call_next(request)
        response.headers[self.quota_header] = json.dumps(quota_check)
        
        return response
    
    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request."""
        # Same logic as in TokenCountingMiddleware
        user_id = request.headers.get('X-User-ID') or request.headers.get('X-Auth-User')
        if not user_id:
            user_id = request.query_params.get('user_id')
        if not user_id:
            user_id = request.cookies.get('user_id')
        if not user_id:
            user_id = getattr(request.state, 'user_id', None)
        
        return user_id
    
    async def _estimate_request_tokens(self, request: Request) -> int:
        """Estimate tokens needed for the request."""
        try:
            # Simple estimation based on request method and content type
            base_tokens = 100  # Base tokens for request processing
            
            # Add tokens based on method
            if request.method == 'GET':
                base_tokens += 50
            elif request.method in ['POST', 'PUT', 'PATCH']:
                base_tokens += 200
            elif request.method == 'DELETE':
                base_tokens += 100
            
            # Add tokens based on content length
            content_length = int(request.headers.get('content-length', 0))
            base_tokens += content_length // 4  # Rough estimate: 4 chars per token
            
            return base_tokens
        
        except Exception as e:
            logger.warning(f"Error estimating request tokens: {e}")
            return 100  # Default estimate


# Utility functions for integration
def create_token_middleware(token_counter: Optional[TokenCounter] = None,
                          model: TokenizationModel = TokenizationModel.CL100K_BASE,
                          enable_quota: bool = True) -> BaseHTTPMiddleware:
    """
    Create token counting middleware with optional quota enforcement.
    
    Args:
        token_counter: TokenCounter instance (optional)
        model: Tokenization model to use
        enable_quota: Whether to enable quota checking
        
    Returns:
        Middleware instance
    """
    if not FASTAPI_AVAILABLE:
        logger.warning("FastAPI not available, returning dummy middleware")
        return BaseHTTPMiddleware(None)
    
    if enable_quota:
        # Create middleware chain
        class TokenMiddlewareChain(BaseHTTPMiddleware):
            def __init__(self, app):
                super().__init__(app)
                self.token_counter = token_counter or TokenCounter()
                self.counting_middleware = TokenCountingMiddleware(
                    app, token_counter, model
                )
                self.quota_middleware = TokenQuotaMiddleware(
                    app, token_counter
                )
            
            async def dispatch(self, request, call_next):
                # Apply quota middleware first
                quota_response = await self.quota_middleware.dispatch(request, call_next)
                if quota_response.status_code == 429:
                    return quota_response
                
                # Apply token counting middleware
                return await self.counting_middleware.dispatch(request, call_next)
        
        return TokenMiddlewareChain
    else:
        return TokenCountingMiddleware(None, token_counter, model)


# FastAPI dependency for token counting
def get_token_counter() -> TokenCounter:
    """FastAPI dependency to get TokenCounter instance."""
    return TokenCounter()


def get_token_model() -> TokenizationModel:
    """FastAPI dependency to get default token model."""
    return TokenizationModel.CL100K_BASE