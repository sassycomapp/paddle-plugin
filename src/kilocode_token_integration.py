#!/usr/bin/env python3
"""
KiloCode Token Integration Module

This module provides integration between the Token Management System and KiloCode orchestration system.
It enables automatic token counting, budget management, and quota enforcement for KiloCode workflows.

Key Features:
- Token budget coordination for KiloCode workflows
- Automatic token counting for workflow steps
- User session-based token management
- Integration with KiloCode configuration and caching
- Budget enforcement and quota management
- Comprehensive error handling and logging
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
import os
from pathlib import Path

# Import token management components
try:
    from .token_counter import TokenCounter
    from .decorators import token_counter_decorator
    from .middleware import TokenQuotaMiddleware
    from ..database.models import User, TokenUsage, TokenLimit
    from ..database.connection import get_db_session
except ImportError as e:
    logging.warning(f"Import error in KiloCode token integration: {e}")
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
class KiloCodeWorkflowContext:
    """Context information for KiloCode workflows."""
    workflow_id: str
    user_id: str
    session_id: str
    workflow_name: str
    step_name: str
    arguments: Dict[str, Any]
    timestamp: datetime
    workflow_config: Optional[Dict[str, Any]] = None


@dataclass
class TokenBudgetResult:
    """Result of token budget check."""
    allowed: bool
    tokens_available: int
    tokens_required: int
    tokens_used: int
    budget_remaining: int
    message: str


class KiloCodeTokenIntegration:
    """
    Main integration class for KiloCode token management.
    
    Coordinates token counting, budget management, and quota enforcement
    for KiloCode orchestration workflows.
    """
    
    def __init__(self, token_counter: Optional[TokenCounter] = None):
        """Initialize KiloCode token integration."""
        self.token_counter = token_counter or TokenCounter()
        self.middleware = TokenQuotaMiddleware()
        self.active_workflows: Dict[str, Dict] = {}
        self.workflow_stats: Dict[str, Dict] = {}
        self.budget_allocations: Dict[str, Dict] = {}
        
        # Load KiloCode configuration
        self.config = self._load_kilocode_config()
        
        logger.info("KiloCode Token Integration initialized")
    
    def _load_kilocode_config(self) -> Dict[str, Any]:
        """Load KiloCode configuration from cache integration file."""
        try:
            config_path = Path(".kilocode/config/cache_integration.yaml")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    import yaml
                    return yaml.safe_load(f) or {}
            else:
                logger.warning("KiloCode config file not found, using defaults")
                return {
                    'cache': {
                        'enabled': True,
                        'provider': 'redis',
                        'config': {}
                    },
                    'token_management': {
                        'enabled': True,
                        'budget_check': True,
                        'quota_enforcement': True
                    }
                }
        except Exception as e:
            logger.error(f"Error loading KiloCode config: {e}")
            return {}
    
    async def kilocode_token_budget(
        self, 
        user_id: str, 
        session_id: str,
        workflow_id: str,
        step_name: str,
        estimated_tokens: Optional[int] = None
    ) -> TokenBudgetResult:
        """
        Check token budget for KiloCode workflow execution.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            workflow_id: Workflow identifier
            step_name: Name of the workflow step
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
                    # Estimate based on workflow and step
                    estimated_tokens = self._estimate_workflow_tokens(workflow_id, step_name)
                
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
                    message=f"Budget check {'passed' if allowed else 'failed'} for {workflow_id}.{step_name}"
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
    
    async def setup_token_hooks(self, kilocode_instance: Any) -> None:
        """
        Setup token management hooks for KiloCode initialization.
        
        Args:
            kilocode_instance: KiloCode instance to hook into
        """
        try:
            # Add token counting middleware to KiloCode
            if hasattr(kilocode_instance, 'middleware'):
                kilocode_instance.middleware.insert(0, self.middleware)
            
            # Add token tracking to KiloCode lifecycle
            if hasattr(kilocode_instance, 'lifespan'):
                original_lifespan = kilocode_instance.lifespan
                
                async def token_lifespan(app: Any):
                    # Initialize token tracking for KiloCode startup
                    logger.info("Setting up token management hooks for KiloCode")
                    
                    # Add token counting to KiloCode capabilities
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
                
                kilocode_instance.lifespan = token_lifespan
            
            logger.info("Token management hooks setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up token hooks: {str(e)}")
            logger.error(traceback.format_exc())
    
    async def route_with_token_budget(
        self, 
        user_id: str, 
        session_id: str,
        workflow_id: str,
        step_name: str,
        workflow_func: Callable,
        *args, 
        **kwargs
    ) -> Any:
        """
        Route workflow step with token budget management.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            workflow_id: Workflow identifier
            step_name: Name of the workflow step
            workflow_func: Workflow function to execute
            *args, **kwargs: Arguments for the workflow function
            
        Returns:
            Result of workflow execution
        """
        try:
            # Check token budget
            budget_result = await self.kilocode_token_budget(
                user_id, session_id, workflow_id, step_name
            )
            
            if not budget_result.allowed:
                logger.warning(f"Token budget exceeded for {workflow_id}.{step_name}: {budget_result.message}")
                raise ValueError(budget_result.message)
            
            # Execute workflow with token counting
            async def _execute_workflow():
                return await workflow_func(*args, **kwargs)
            
            # Apply token counting decorator
            try:
                # Get the decorator function
                decorator_func = await self.mcp_token_decorator(step_name, budget_check=False, quota_enforcement=False)
                
                # Apply the decorator
                if asyncio.iscoroutinefunction(decorator_func):
                    # If decorator returns a coroutine, await it and then call the result
                    decorated_workflow = await decorator_func(_execute_workflow)
                else:
                    # If decorator is synchronous, call it directly
                    if hasattr(decorator_func, '__call__'):
                        decorated_workflow = decorator_func(_execute_workflow)
                    else:
                        decorated_workflow = _execute_workflow
                
                return await decorated_workflow()
            except Exception as e:
                logger.error(f"Error applying token decorator: {e}")
                return await _execute_workflow()
            
        except Exception as e:
            logger.error(f"Error routing workflow step with token budget: {str(e)}")
            raise
    
    async def integrate_with_memory(self, memory_service: Any) -> None:
        """
        Integrate token management with memory service for KiloCode workflows.
        
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
                    decorator_func = await self.mcp_token_decorator('store_memory')
                    if asyncio.iscoroutinefunction(decorator_func):
                        decorated_store = await decorator_func(_token_counting_store)
                    else:
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
                    decorator_func = await self.mcp_token_decorator('retrieve_memory')
                    if asyncio.iscoroutinefunction(decorator_func):
                        decorated_retrieve = await decorator_func(_token_counting_retrieve)
                    else:
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
                    decorator_func = await self.mcp_token_decorator('delete_memory')
                    if asyncio.iscoroutinefunction(decorator_func):
                        decorated_delete = await decorator_func(_token_counting_delete)
                    else:
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
        Integrate token management with external API clients for KiloCode workflows.
        
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
                    decorator_func = await self.mcp_token_decorator('api_call')
                    if asyncio.iscoroutinefunction(decorator_func):
                        decorated_call = await decorator_func(_token_counting_call)
                    else:
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
                    decorator_func = await self.mcp_token_decorator('batch_api_call')
                    if asyncio.iscoroutinefunction(decorator_func):
                        decorated_batch = await decorator_func(_token_counting_batch)
                    else:
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
    
    def _extract_mcp_context(self, tool_name: str, args: tuple, kwargs: dict) -> Optional[KiloCodeWorkflowContext]:
        """Extract MCP tool context from function arguments."""
        try:
            # Try to extract user and session information from kwargs
            user_id = kwargs.get('user_id') or kwargs.get('user', {}).get('id')
            session_id = kwargs.get('session_id') or kwargs.get('session', {}).get('id')
            workflow_id = kwargs.get('workflow_id')
            step_name = kwargs.get('step_name', tool_name)
            
            if not user_id or not session_id:
                logger.warning(f"Missing user_id or session_id for tool {tool_name}")
                return None
            
            return KiloCodeWorkflowContext(
                workflow_id=workflow_id or tool_name,
                user_id=user_id,
                session_id=session_id,
                workflow_name=workflow_id or tool_name,
                step_name=step_name,
                arguments=kwargs,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Error extracting MCP context: {str(e)}")
            return None
    
    async def _check_token_budget(self, context: KiloCodeWorkflowContext) -> TokenBudgetResult:
        """Check if user has sufficient token budget."""
        return await self.kilocode_token_budget(
            context.user_id,
            context.session_id,
            context.workflow_id,
            context.step_name
        )
    
    async def _count_tokens_in_result(self, result: Any, context: KiloCodeWorkflowContext) -> int:
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
    
    async def _record_token_usage(self, context: KiloCodeWorkflowContext, tokens_used: int, success: bool = True) -> None:
        """Record token usage in the database."""
        try:
            with get_db_session() as db:
                # Create token usage record
                token_usage = TokenUsage(
                    user_id=context.user_id,
                    session_id=context.session_id,
                    tool_name=f"{context.workflow_id}.{context.step_name}",
                    tokens_used=tokens_used,
                    timestamp=context.timestamp,
                    success=success,
                    tool_call_id=context.workflow_id
                )
                
                db.add(token_usage)
                db.commit()
                
        except Exception as e:
            logger.error(f"Error recording token usage: {str(e)}")
    
    async def _update_session_stats(self, context: KiloCodeWorkflowContext, tokens_used: int, duration: float) -> None:
        """Update session statistics."""
        try:
            if context.session_id not in self.active_workflows:
                self.active_workflows[context.session_id] = {
                    'start_time': context.timestamp,
                    'total_tokens': 0,
                    'total_calls': 0,
                    'total_duration': 0.0,
                    'workflows': {}
                }
            
            session = self.active_workflows[context.session_id]
            session['total_tokens'] += tokens_used
            session['total_calls'] += 1
            session['total_duration'] += duration
            
            # Update workflow-specific stats
            if context.workflow_id not in session['workflows']:
                session['workflows'][context.workflow_id] = {
                    'count': 0,
                    'total_tokens': 0,
                    'total_duration': 0.0,
                    'steps': {}
                }
            
            workflow_stats = session['workflows'][context.workflow_id]
            workflow_stats['count'] += 1
            workflow_stats['total_tokens'] += tokens_used
            workflow_stats['total_duration'] += duration
            
            # Update step-specific stats
            if context.step_name not in workflow_stats['steps']:
                workflow_stats['steps'][context.step_name] = {
                    'count': 0,
                    'total_tokens': 0,
                    'total_duration': 0.0
                }
            
            step_stats = workflow_stats['steps'][context.step_name]
            step_stats['count'] += 1
            step_stats['total_tokens'] += tokens_used
            step_stats['total_duration'] += duration
            
        except Exception as e:
            logger.error(f"Error updating session stats: {str(e)}")
    
    def _estimate_workflow_tokens(self, workflow_id: str, step_name: str) -> int:
        """Estimate token usage for a workflow step based on historical data."""
        try:
            # Base estimates for common workflow steps
            base_estimates = {
                'data_processing': 200,
                'api_call': 150,
                'memory_retrieval': 100,
                'memory_storage': 50,
                'analysis': 300,
                'generation': 250,
                'validation': 75,
                'transformation': 125
            }
            
            # Get step-specific estimates
            step_key = f"{workflow_id}.{step_name}"
            estimate = base_estimates.get(step_name, 100)
            
            # Adjust based on historical data
            for session_id, session_data in self.active_workflows.items():
                if workflow_id in session_data['workflows']:
                    workflow_stats = session_data['workflows'][workflow_id]
                    if step_name in workflow_stats['steps']:
                        step_stats = workflow_stats['steps'][step_name]
                        avg_tokens = step_stats['total_tokens'] / step_stats['count']
                        estimate = int(avg_tokens * 1.1)  # Add 10% buffer
            
            return estimate
            
        except Exception as e:
            logger.error(f"Error estimating workflow tokens: {str(e)}")
            return 100  # Default estimate


# Global KiloCode token integration instance
kilocode_token_integration = KiloCodeTokenIntegration()


# Convenience functions for direct use
async def kilocode_token_budget(user_id: str, session_id: str, workflow_id: str, step_name: str, estimated_tokens: Optional[int] = None):
    """Convenience function for KiloCode token budget check."""
    return await kilocode_token_integration.kilocode_token_budget(user_id, session_id, workflow_id, step_name, estimated_tokens)


async def setup_token_hooks(kilocode_instance: Any) -> None:
    """Convenience function for setting up token hooks."""
    await kilocode_token_integration.setup_token_hooks(kilocode_instance)


async def route_with_token_budget(user_id: str, session_id: str, workflow_id: str, step_name: str, workflow_func: Callable, *args, **kwargs):
    """Convenience function for routing with token budget."""
    return await kilocode_token_integration.route_with_token_budget(user_id, session_id, workflow_id, step_name, workflow_func, *args, **kwargs)


async def integrate_with_memory(memory_service: Any) -> None:
    """Convenience function for memory integration."""
    await kilocode_token_integration.integrate_with_memory(memory_service)


async def integrate_with_external_apis(api_client: Any) -> None:
    """Convenience function for external API integration."""
    await kilocode_token_integration.integrate_with_external_apis(api_client)