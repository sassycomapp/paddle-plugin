#!/usr/bin/env python3
"""
MCP Token Integration Module

This module provides integration between the Token Management System and MCP (Model Context Protocol) servers.
It enables automatic token counting, budget management, and quota enforcement for MCP tool calls.

Key Features:
- Automatic token counting for MCP tool calls
- User session-based token budget coordination
- Decorator pattern for MCP tool integration
- Budget enforcement and quota management
- Integration with existing token counting infrastructure
- Comprehensive error handling and logging
"""

import asyncio
import logging
import time
from functools import wraps
from typing import Dict, List, Optional, Any, Callable, Union, Awaitable
from dataclasses import dataclass
from datetime import datetime, timezone
import traceback

# Configure logging first
logger = logging.getLogger(__name__)

# Import token management components
try:
    from .token_counter import TokenCounter
    from .decorators import token_counter_decorator
    from .middleware import TokenQuotaMiddleware
    from ..database.models import User, TokenUsage, TokenLimit
    from ..database.connection import get_db_session
except ImportError as e:
    logger.warning(f"Import error in MCP token integration: {e}")
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
class MCPToolContext:
    """Context information for MCP tool calls."""
    tool_name: str
    user_id: str
    session_id: str
    arguments: Dict[str, Any]
    timestamp: datetime
    tool_call_id: Optional[str] = None


@dataclass
class TokenBudgetResult:
    """Result of token budget check."""
    allowed: bool
    tokens_available: int
    tokens_required: int
    tokens_used: int
    budget_remaining: int
    message: str


class MCPTokenIntegration:
    """
    Main integration class for MCP token management.
    
    Coordinates token counting, budget management, and quota enforcement
    for MCP server operations.
    """
    
    def __init__(self, token_counter: Optional[TokenCounter] = None):
        """Initialize MCP token integration."""
        self.token_counter = token_counter or TokenCounter()
        self.middleware = TokenQuotaMiddleware()
        self.active_sessions: Dict[str, Dict] = {}
        self.tool_call_stats: Dict[str, Dict] = {}
        
        logger.info("MCP Token Integration initialized")
    
    async def mcp_token_decorator(
        self, 
        tool_name: str,
        budget_check: bool = True,
        quota_enforcement: bool = True
    ) -> Callable:
        """
        Decorator for MCP tools to enable automatic token counting and budget management.
        
        Args:
            tool_name: Name of the MCP tool being decorated
            budget_check: Whether to check token budget before execution
            quota_enforcement: Whether to enforce token quotas
            
        Returns:
            Decorated function with token counting capabilities
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract context from MCP tool call
                context = self._extract_mcp_context(tool_name, args, kwargs)
                
                if not context:
                    logger.warning(f"Could not extract MCP context for {tool_name}")
                    return await func(*args, **kwargs)
                
                # Start token counting
                token_count_start = time.time()
                tokens_used = 0
                
                try:
                    # Check token budget if enabled
                    if budget_check:
                        budget_result = await self._check_token_budget(context)
                        if not budget_result.allowed and quota_enforcement:
                            logger.warning(f"Token budget exceeded for {tool_name}: {budget_result.message}")
                            return {
                                "success": False,
                                "error": budget_result.message,
                                "tokens_used": tokens_used,
                                "tokens_required": budget_result.tokens_required,
                                "budget_remaining": budget_result.budget_remaining
                            }
                    
                    # Execute the tool function
                    result = await func(*args, **kwargs)
                    
                    # Count tokens in the result
                    if result:
                        tokens_used = await self._count_tokens_in_result(result, context)
                    
                    # Record token usage
                    await self._record_token_usage(context, tokens_used)
                    
                    # Update session statistics
                    await self._update_session_stats(context, tokens_used, time.time() - token_count_start)
                    
                    logger.info(f"Tool {tool_name} completed. Tokens used: {tokens_used}")
                    return result
                    
                except Exception as e:
                    logger.error(f"Error in MCP tool {tool_name}: {str(e)}")
                    logger.error(traceback.format_exc())
                    
                    # Still record token usage for failed operations
                    await self._record_token_usage(context, tokens_used, success=False)
                    raise
            
            return wrapper
        return decorator
    
    async def kilocode_token_budget(
        self, 
        user_id: str, 
        session_id: str,
        tool_name: str,
        estimated_tokens: Optional[int] = None
    ) -> TokenBudgetResult:
        """
        Check token budget for KiloCode orchestration.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            tool_name: Name of the tool to be executed
            estimated_tokens: Estimated token count (if None, will be calculated)
            
        Returns:
            TokenBudgetResult with budget information
        """
        try:
            # Get user's token limits
            with get_db_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return TokenBudgetResult(
                        allowed=False,
                        tokens_available=0,
                        tokens_required=estimated_tokens or 0,
                        tokens_used=0,
                        budget_remaining=0,
                        message="User not found"
                    )
                
                # Get token limits
                token_limit = db.query(TokenLimit).filter(
                    getattr(TokenLimit, 'user_id', None) == user_id,
                    getattr(TokenLimit, 'session_id', None) == session_id
                ).first()
                
                if not token_limit:
                    return TokenBudgetResult(
                        allowed=False,
                        tokens_available=0,
                        tokens_required=estimated_tokens or 0,
                        tokens_used=0,
                        budget_remaining=0,
                        message="Token limit not found for session"
                    )
                
                # Calculate required tokens
                if estimated_tokens is None:
                    # Estimate based on tool name and typical usage
                    estimated_tokens = self._estimate_tool_tokens(tool_name)
                
                # Check budget
                tokens_available = token_limit.daily_limit - token_limit.tokens_used_today
                tokens_required = estimated_tokens
                budget_remaining = max(0, tokens_available - tokens_required)
                
                allowed = budget_remaining >= 0
                
                return TokenBudgetResult(
                    allowed=allowed,
                    tokens_available=tokens_available,
                    tokens_required=tokens_required,
                    tokens_used=token_limit.tokens_used_today,
                    budget_remaining=budget_remaining,
                    message=f"Budget check {'passed' if allowed else 'failed'} for {tool_name}"
                )
                
        except Exception as e:
            logger.error(f"Error checking token budget: {str(e)}")
            return TokenBudgetResult(
                allowed=False,
                tokens_available=0,
                tokens_required=estimated_tokens or 0,
                tokens_used=0,
                budget_remaining=0,
                message=f"Budget check failed: {str(e)}"
            )
    
    async def setup_token_hooks(self, server_instance: Any) -> None:
        """
        Setup token management hooks for MCP server initialization.
        
        Args:
            server_instance: MCP server instance to hook into
        """
        try:
            # Add token counting middleware to server
            if hasattr(server_instance, 'middleware'):
                server_instance.middleware.insert(0, self.middleware)
            
            # Add token tracking to server lifecycle
            if hasattr(server_instance, 'lifespan'):
                original_lifespan = server_instance.lifespan
                
                async def token_lifespan(app: Any):
                    # Initialize token tracking for server startup
                    logger.info("Setting up token management hooks for MCP server")
                    
                    # Add token counting to server capabilities
                    if hasattr(app, 'capabilities'):
                        app.capabilities['token_management'] = {
                            'enabled': True,
                            'counter': self.token_counter,
                            'budget_tracking': True
                        }
                    
                    # Run original lifespan
                    if original_lifespan:
                        async with original_lifespan(app) as app_state:
                            yield app_state
                    else:
                        app_state = {}
                        yield app_state
                
                server_instance.lifespan = token_lifespan
            
            logger.info("Token management hooks setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up token hooks: {str(e)}")
            logger.error(traceback.format_exc())
    
    async def route_with_token_budget(
        self, 
        user_id: str, 
        session_id: str,
        tool_name: str,
        tool_func: Callable,
        *args, 
        **kwargs
    ) -> Any:
        """
        Route tool call with token budget management.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            tool_name: Name of the tool to execute
            tool_func: Tool function to execute
            *args, **kwargs: Arguments for the tool function
            
        Returns:
            Result of tool execution
        """
        try:
            # Check token budget
            budget_result = await self.kilocode_token_budget(user_id, session_id, tool_name)
            
            if not budget_result.allowed:
                logger.warning(f"Token budget exceeded for {tool_name}: {budget_result.message}")
                raise ValueError(budget_result.message)
            
            # Execute tool with token counting
            async def _execute_tool():
                return await tool_func(*args, **kwargs)
            
            # Apply token counting decorator
            try:
                # Get the decorator function
                decorator_func = await self.mcp_token_decorator(tool_name, budget_check=False, quota_enforcement=False)
                
                # Apply the decorator
                if asyncio.iscoroutinefunction(decorator_func):
                    # If decorator returns a coroutine, await it and then call the result
                    decorated_tool = await decorator_func(_execute_tool)
                else:
                    # If decorator is synchronous, call it directly
                    if hasattr(decorator_func, '__call__'):
                        decorated_tool = decorator_func(_execute_tool)
                    else:
                        decorated_tool = _execute_tool
                
                return await decorated_tool()
            except Exception as e:
                logger.error(f"Error applying token decorator: {e}")
                return await _execute_tool()
            
        except Exception as e:
            logger.error(f"Error routing tool call with token budget: {str(e)}")
            raise
    
    async def integrate_with_memory(self, memory_service: Any) -> None:
        """
        Integrate token management with memory service.
        
        Args:
            memory_service: Memory service instance to integrate with
        """
        try:
            # Add token counting to memory operations
            if hasattr(memory_service, 'store_memory'):
                original_store = memory_service.store_memory
                
                async def _token_counting_store(*args, **kwargs):
                    return await original_store(*args, **kwargs)
                
                # Apply token counting decorator
                try:
                    # Get the decorator function
                    decorator_func = await self.mcp_token_decorator('store_memory')
                    
                    # Apply the decorator
                    if asyncio.iscoroutinefunction(decorator_func):
                        # If decorator returns a coroutine, await it and then call the result
                        decorated_store = await decorator_func(_token_counting_store)
                    else:
                        # If decorator is synchronous, call it directly
                        if hasattr(decorator_func, '__call__'):
                            decorated_store = decorator_func(_token_counting_store)
                        else:
                            decorated_store = _token_counting_store
                    
                    memory_service.store_memory = decorated_store
                except Exception as e:
                    logger.error(f"Error applying token decorator to store_memory: {e}")
                    memory_service.store_memory = _token_counting_store
            
            if hasattr(memory_service, 'retrieve_memory'):
                original_retrieve = memory_service.retrieve_memory
                
                async def _token_counting_retrieve(*args, **kwargs):
                    return await original_retrieve(*args, **kwargs)
                
                # Apply token counting decorator
                try:
                    # Get the decorator function
                    decorator_func = await self.mcp_token_decorator('retrieve_memory')
                    
                    # Apply the decorator
                    if asyncio.iscoroutinefunction(decorator_func):
                        # If decorator returns a coroutine, await it and then call the result
                        decorated_retrieve = await decorator_func(_token_counting_retrieve)
                    else:
                        # If decorator is synchronous, call it directly
                        if hasattr(decorator_func, '__call__'):
                            decorated_retrieve = decorator_func(_token_counting_retrieve)
                        else:
                            decorated_retrieve = _token_counting_retrieve
                    
                    memory_service.retrieve_memory = decorated_retrieve
                except Exception as e:
                    logger.error(f"Error applying token decorator to retrieve_memory: {e}")
                    memory_service.retrieve_memory = _token_counting_retrieve
            
            if hasattr(memory_service, 'delete_memory'):
                original_delete = memory_service.delete_memory
                
                async def _token_counting_delete(*args, **kwargs):
                    return await original_delete(*args, **kwargs)
                
                # Apply token counting decorator
                try:
                    # Get the decorator function
                    decorator_func = await self.mcp_token_decorator('delete_memory')
                    
                    # Apply the decorator
                    if asyncio.iscoroutinefunction(decorator_func):
                        # If decorator returns a coroutine, await it and then call the result
                        decorated_delete = await decorator_func(_token_counting_delete)
                    else:
                        # If decorator is synchronous, call it directly
                        if hasattr(decorator_func, '__call__'):
                            decorated_delete = decorator_func(_token_counting_delete)
                        else:
                            decorated_delete = _token_counting_delete
                    
                    memory_service.delete_memory = decorated_delete
                except Exception as e:
                    logger.error(f"Error applying token decorator to delete_memory: {e}")
                    memory_service.delete_memory = _token_counting_delete
            
            logger.info("Token management integration with memory service completed")
            
        except Exception as e:
            logger.error(f"Error integrating with memory service: {str(e)}")
            logger.error(traceback.format_exc())
    
    async def integrate_with_external_apis(self, api_client: Any) -> None:
        """
        Integrate token management with external API clients.
        
        Args:
            api_client: External API client instance to integrate with
        """
        try:
            # Add token counting to API calls
            if hasattr(api_client, 'call_api'):
                original_call = api_client.call_api
                
                async def _token_counting_call(*args, **kwargs):
                    return await original_call(*args, **kwargs)
                
                # Apply token counting decorator
                try:
                    # Get the decorator function
                    decorator_func = await self.mcp_token_decorator('api_call')
                    
                    # Apply the decorator
                    if asyncio.iscoroutinefunction(decorator_func):
                        # If decorator returns a coroutine, await it and then call the result
                        decorated_call = await decorator_func(_token_counting_call)
                    else:
                        # If decorator is synchronous, call it directly
                        if hasattr(decorator_func, '__call__'):
                            decorated_call = decorator_func(_token_counting_call)
                        else:
                            decorated_call = _token_counting_call
                    
                    api_client.call_api = decorated_call
                except Exception as e:
                    logger.error(f"Error applying token decorator to call_api: {e}")
                    api_client.call_api = _token_counting_call
            
            if hasattr(api_client, 'batch_call'):
                original_batch = api_client.batch_call
                
                async def _token_counting_batch(*args, **kwargs):
                    return await original_batch(*args, **kwargs)
                
                # Apply token counting decorator
                try:
                    # Get the decorator function
                    decorator_func = await self.mcp_token_decorator('batch_api_call')
                    
                    # Apply the decorator
                    if asyncio.iscoroutinefunction(decorator_func):
                        # If decorator returns a coroutine, await it and then call the result
                        decorated_batch = await decorator_func(_token_counting_batch)
                    else:
                        # If decorator is synchronous, call it directly
                        if hasattr(decorator_func, '__call__'):
                            decorated_batch = decorator_func(_token_counting_batch)
                        else:
                            decorated_batch = _token_counting_batch
                    
                    api_client.batch_call = decorated_batch
                except Exception as e:
                    logger.error(f"Error applying token decorator to batch_call: {e}")
                    api_client.batch_call = _token_counting_batch
            
            logger.info("Token management integration with external APIs completed")
            
        except Exception as e:
            logger.error(f"Error integrating with external APIs: {str(e)}")
            logger.error(traceback.format_exc())
    
    def _extract_mcp_context(self, tool_name: str, args: tuple, kwargs: dict) -> Optional[MCPToolContext]:
        """Extract MCP tool context from function arguments."""
        try:
            # Try to extract user and session information from kwargs
            user_id = kwargs.get('user_id') or kwargs.get('user', {}).get('id')
            session_id = kwargs.get('session_id') or kwargs.get('session', {}).get('id')
            
            if not user_id or not session_id:
                logger.warning(f"Missing user_id or session_id for tool {tool_name}")
                return None
            
            return MCPToolContext(
                tool_name=tool_name,
                user_id=user_id,
                session_id=session_id,
                arguments=kwargs,
                timestamp=datetime.now(timezone.utc),
                tool_call_id=kwargs.get('tool_call_id')
            )
            
        except Exception as e:
            logger.error(f"Error extracting MCP context: {str(e)}")
            return None
    
    async def _check_token_budget(self, context: MCPToolContext) -> TokenBudgetResult:
        """Check if user has sufficient token budget."""
        return await self.kilocode_token_budget(
            context.user_id,
            context.session_id,
            context.tool_name
        )
    
    async def _count_tokens_in_result(self, result: Any, context: MCPToolContext) -> int:
        """Count tokens in the result of a tool call."""
        try:
            # Convert result to string for token counting
            if isinstance(result, dict):
                result_str = str(result)
            elif isinstance(result, list):
                result_str = str(result)
            else:
                result_str = str(result)
            
            # Count tokens
            tokens = await self.token_counter.count_tokens(result_str)
            return tokens
            
        except Exception as e:
            logger.error(f"Error counting tokens in result: {str(e)}")
            return 0
    
    async def _record_token_usage(self, context: MCPToolContext, tokens_used: int, success: bool = True) -> None:
        """Record token usage in the database."""
        try:
            with get_db_session() as db:
                # Create token usage record
                token_usage = TokenUsage(
                    user_id=context.user_id,
                    session_id=context.session_id,
                    tool_name=context.tool_name,
                    tokens_used=tokens_used,
                    timestamp=context.timestamp,
                    success=success,
                    tool_call_id=context.tool_call_id
                )
                
                db.add(token_usage)
                db.commit()
                
        except Exception as e:
            logger.error(f"Error recording token usage: {str(e)}")
    
    async def _update_session_stats(self, context: MCPToolContext, tokens_used: int, duration: float) -> None:
        """Update session statistics."""
        try:
            if context.session_id not in self.active_sessions:
                self.active_sessions[context.session_id] = {
                    'start_time': context.timestamp,
                    'total_tokens': 0,
                    'total_calls': 0,
                    'total_duration': 0.0,
                    'tool_calls': {}
                }
            
            session = self.active_sessions[context.session_id]
            session['total_tokens'] += tokens_used
            session['total_calls'] += 1
            session['total_duration'] += duration
            
            # Update tool-specific stats
            if context.tool_name not in session['tool_calls']:
                session['tool_calls'][context.tool_name] = {
                    'count': 0,
                    'total_tokens': 0,
                    'total_duration': 0.0
                }
            
            tool_stats = session['tool_calls'][context.tool_name]
            tool_stats['count'] += 1
            tool_stats['total_tokens'] += tokens_used
            tool_stats['total_duration'] += duration
            
        except Exception as e:
            logger.error(f"Error updating session stats: {str(e)}")
    
    def _estimate_tool_tokens(self, tool_name: str) -> int:
        """Estimate token usage for a tool based on historical data."""
        try:
            # Base estimates for common tools
            base_estimates = {
                'store_memory': 50,
                'retrieve_memory': 100,
                'delete_memory': 30,
                'search_by_tag': 75,
                'recall_memory': 150,
                'api_call': 200,
                'batch_api_call': 500
            }
            
            # Get session-specific estimates if available
            estimate = base_estimates.get(tool_name, 100)
            
            # Adjust based on historical data
            for session_id, session_data in self.active_sessions.items():
                if tool_name in session_data['tool_calls']:
                    tool_stats = session_data['tool_calls'][tool_name]
                    avg_tokens = tool_stats['total_tokens'] / tool_stats['count']
                    estimate = int(avg_tokens * 1.1)  # Add 10% buffer
            
            return estimate
            
        except Exception as e:
            logger.error(f"Error estimating tool tokens: {str(e)}")
            return 100  # Default estimate


# Global MCP token integration instance
mcp_token_integration = MCPTokenIntegration()


# Convenience functions for direct use
async def mcp_token_decorator(tool_name: str, budget_check: bool = True, quota_enforcement: bool = True):
    """Convenience function for MCP token decorator."""
    return await mcp_token_integration.mcp_token_decorator(tool_name, budget_check, quota_enforcement)


async def kilocode_token_budget(user_id: str, session_id: str, tool_name: str, estimated_tokens: Optional[int] = None):
    """Convenience function for KiloCode token budget check."""
    return await mcp_token_integration.kilocode_token_budget(user_id, session_id, tool_name, estimated_tokens)


async def setup_token_hooks(server_instance: Any) -> None:
    """Convenience function for setting up token hooks."""
    await mcp_token_integration.setup_token_hooks(server_instance)


async def route_with_token_budget(user_id: str, session_id: str, tool_name: str, tool_func: Callable, *args, **kwargs):
    """Convenience function for routing with token budget."""
    return await mcp_token_integration.route_with_token_budget(user_id, session_id, tool_name, tool_func, *args, **kwargs)


async def integrate_with_memory(memory_service: Any) -> None:
    """Convenience function for memory integration."""
    await mcp_token_integration.integrate_with_memory(memory_service)


async def integrate_with_external_apis(api_client: Any) -> None:
    """Convenience function for external API integration."""
    await mcp_token_integration.integrate_with_external_apis(api_client)