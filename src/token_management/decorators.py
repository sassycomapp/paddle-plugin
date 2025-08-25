"""
Decorators for Automatic Token Counting

This module provides decorators that automatically count tokens for function inputs and outputs,
integrating seamlessly with the token counting system.
"""

import logging
import functools
import inspect
from typing import Callable, Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime

from .token_counter import TokenCounter, TokenizationModel, TokenCountResult

logger = logging.getLogger(__name__)


@dataclass
class TokenUsageRecord:
    """Record of token usage for a decorated function call."""
    function_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model: TokenizationModel
    processing_time: float
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    api_endpoint: Optional[str] = None
    priority_level: str = "Medium"


def token_counter_decorator(
    model: TokenizationModel = TokenizationModel.CL100K_BASE,
    count_inputs: bool = True,
    count_outputs: bool = True,
    log_usage: bool = False,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    api_endpoint: Optional[str] = None,
    priority_level: str = "Medium",
    counter: Optional[TokenCounter] = None
):
    """
    Decorator to automatically count tokens for function inputs and outputs.
    
    Args:
        model: Tokenization model to use
        count_inputs: Whether to count tokens in function inputs
        count_outputs: Whether to count tokens in function outputs
        log_usage: Whether to log token usage to database
        user_id: User identifier for logging
        session_id: Session identifier for logging
        api_endpoint: API endpoint for logging
        priority_level: Priority level for logging
        counter: TokenCounter instance (optional)
        
    Returns:
        Decorated function with automatic token counting
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Initialize token counter if not provided
            token_counter = counter or TokenCounter()
            
            # Get function signature for better parameter handling
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            start_time = datetime.now()
            
            # Count input tokens if enabled
            input_tokens = 0
            if count_inputs:
                try:
                    # Convert arguments to string for token counting
                    input_str = _format_function_inputs(bound_args.arguments, func.__name__)
                    input_result = token_counter.count_tokens(input_str, model)
                    input_tokens = input_result.token_count
                    logger.debug(f"Input tokens for {func.__name__}: {input_tokens}")
                except Exception as e:
                    logger.warning(f"Failed to count input tokens for {func.__name__}: {e}")
            
            # Execute the function
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                # Count tokens in error message if enabled
                if count_outputs:
                    try:
                        error_str = str(e)
                        error_result = token_counter.count_tokens(error_str, model)
                        output_tokens = error_result.token_count
                        logger.debug(f"Error tokens for {func.__name__}: {output_tokens}")
                    except Exception:
                        output_tokens = 0
                raise
            
            # Count output tokens if enabled
            output_tokens = 0
            if count_outputs:
                try:
                    # Convert result to string for token counting
                    output_str = _format_function_output(result, func.__name__)
                    output_result = token_counter.count_tokens(output_str, model)
                    output_tokens = output_result.token_count
                    logger.debug(f"Output tokens for {func.__name__}: {output_tokens}")
                except Exception as e:
                    logger.warning(f"Failed to count output tokens for {func.__name__}: {e}")
            
            # Calculate total tokens and processing time
            total_tokens = input_tokens + output_tokens
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Log usage if enabled
            if log_usage and total_tokens > 0:
                try:
                    usage_record = TokenUsageRecord(
                        function_name=func.__name__,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=total_tokens,
                        model=model,
                        processing_time=processing_time,
                        timestamp=start_time,
                        user_id=user_id,
                        session_id=session_id,
                        api_endpoint=api_endpoint or f"function.{func.__name__}",
                        priority_level=priority_level
                    )
                    
                    # Log to database
                    token_counter.log_token_usage(
                        user_id=user_id or "anonymous",
                        session_id=session_id or "anonymous",
                        tokens_used=total_tokens,
                        api_endpoint=api_endpoint or f"function.{func.__name__}",
                        priority_level=priority_level
                    )
                    
                    logger.info(f"Token usage logged for {func.__name__}: {total_tokens} tokens")
                except Exception as e:
                    logger.warning(f"Failed to log token usage: {e}")
            
            logger.info(f"Function {func.__name__} processed {total_tokens} tokens in {processing_time:.3f}s")
            return result
        
        return wrapper
    return decorator


def track_token_usage(
    model: TokenizationModel = TokenizationModel.CL100K_BASE,
    counter: Optional[TokenCounter] = None
):
    """
    Decorator to track token usage for specific function parameters.
    
    This decorator is useful for functions that already handle token counting
    but want to integrate with the broader token management system.
    
    Args:
        model: Tokenization model to use
        counter: TokenCounter instance (optional)
        
    Returns:
        Decorated function with token usage tracking
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            token_counter = counter or TokenCounter()
            
            start_time = datetime.now()
            
            # Execute the function
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                # Handle error case
                processing_time = (datetime.now() - start_time).total_seconds()
                logger.error(f"Function {func.__name__} failed after {processing_time:.3f}s")
                raise
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Check if result contains token usage information
            if isinstance(result, dict) and 'token_count' in result:
                total_tokens = result['token_count']
                logger.info(f"Function {func.__name__} processed {total_tokens} tokens in {processing_time:.3f}s")
                
                # Log to database if user_id and session_id are available
                if 'user_id' in kwargs and 'session_id' in kwargs:
                    try:
                        token_counter.log_token_usage(
                            user_id=kwargs['user_id'],
                            session_id=kwargs['session_id'],
                            tokens_used=total_tokens,
                            api_endpoint=kwargs.get('api_endpoint', f"function.{func.__name__}"),
                            priority_level=kwargs.get('priority_level', 'Medium')
                        )
                    except Exception as e:
                        logger.warning(f"Failed to log token usage: {e}")
            
            return result
        
        return wrapper
    return decorator


def batch_token_counter(
    model: TokenizationModel = TokenizationModel.CL100K_BASE,
    counter: Optional[TokenCounter] = None
):
    """
    Decorator for functions that process batches of text for token counting.
    
    Args:
        model: Tokenization model to use
        counter: TokenCounter instance (optional)
        
    Returns:
        Decorated function with batch token counting
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            token_counter = counter or TokenCounter()
            
            # Extract texts from arguments (common patterns)
            texts = []
            
            # Check if first argument is a list of texts
            if args and isinstance(args[0], list):
                texts = args[0]
            # Check if there's a 'texts' keyword argument
            elif 'texts' in kwargs:
                texts = kwargs['texts']
            # Check if there's a 'batch' keyword argument
            elif 'batch' in kwargs:
                texts = kwargs['batch']
            
            if not texts:
                logger.warning(f"No texts found for batch token counting in {func.__name__}")
                return func(*args, **kwargs)
            
            start_time = datetime.now()
            
            # Count tokens for the batch
            batch_result = token_counter.count_tokens_batch(texts, model)
            
            # Execute the original function
            result = func(*args, **kwargs)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Log batch token usage
            logger.info(f"Batch function {func.__name__} processed {batch_result.total_tokens} tokens "
                       f"({len(texts)} items) in {processing_time:.3f}s")
            
            # Add token information to result if it's a dictionary
            if isinstance(result, dict):
                result['token_count'] = batch_result.total_tokens
                result['token_count_details'] = {
                    'total_tokens': batch_result.total_tokens,
                    'items_count': len(texts),
                    'average_tokens_per_item': batch_result.total_tokens / len(texts) if texts else 0,
                    'processing_time': processing_time,
                    'cache_hits': batch_result.cache_hits,
                    'cache_misses': batch_result.cache_misses
                }
            
            return result
        
        return wrapper
    return decorator


def _format_function_inputs(arguments: Dict[str, Any], function_name: str) -> str:
    """Format function arguments for token counting."""
    try:
        # Convert arguments to a readable string format
        input_parts = []
        
        for param_name, param_value in arguments.items():
            # Skip special parameters that don't need token counting
            if param_name in ['self', 'cls', 'token_counter', 'counter']:
                continue
            
            # Format the parameter value
            if param_value is None:
                input_parts.append(f"{param_name}=None")
            elif isinstance(param_value, (str, int, float, bool)):
                input_parts.append(f"{param_name}={param_value}")
            elif isinstance(param_value, (list, tuple)):
                # For collections, show length and first few items
                if len(param_value) > 0:
                    first_item = str(param_value[0])[:50]
                    input_parts.append(f"{param_name}=list[{len(param_value)}] (first: {first_item}...)")
                else:
                    input_parts.append(f"{param_name}=list[{len(param_value)}]")
            elif isinstance(param_value, dict):
                # For dictionaries, show keys
                keys = list(param_value.keys())[:5]  # Show first 5 keys
                input_parts.append(f"{param_name}=dict[{len(param_value)}] (keys: {keys})")
            else:
                # For other types, show type and string representation
                str_value = str(param_value)[:100]
                input_parts.append(f"{param_name}={type(param_value).__name__}({str_value}...)")
        
        return f"Function {function_name} inputs: {', '.join(input_parts)}"
    
    except Exception as e:
        logger.warning(f"Failed to format function inputs: {e}")
        return f"Function {function_name} inputs: [formatting error]"


def _format_function_output(output: Any, function_name: str) -> str:
    """Format function output for token counting."""
    try:
        if output is None:
            return f"Function {function_name} output: None"
        elif isinstance(output, (str, int, float, bool)):
            return f"Function {function_name} output: {output}"
        elif isinstance(output, (list, tuple)):
            if len(output) > 0:
                first_item = str(output[0])[:50]
                return f"Function {function_name} output: list[{len(output)}] (first: {first_item}...)"
            else:
                return f"Function {function_name} output: list[{len(output)}]"
        elif isinstance(output, dict):
            keys = list(output.keys())[:5]
            return f"Function {function_name} output: dict[{len(output)}] (keys: {keys})"
        else:
            str_output = str(output)[:100]
            return f"Function {function_name} output: {type(output).__name__}({str_output}...)"
    
    except Exception as e:
        logger.warning(f"Failed to format function output: {e}")
        return f"Function {function_name} output: [formatting error]"


# Convenience decorators for common use cases
def count_api_tokens(
    model: TokenizationModel = TokenizationModel.CL100K_BASE,
    counter: Optional[TokenCounter] = None
):
    """
    Specialized decorator for API endpoint token counting.
    
    Args:
        model: Tokenization model to use
        counter: TokenCounter instance (optional)
        
    Returns:
        Decorated function with API token counting
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            token_counter = counter or TokenCounter()
            
            # Extract user and session information from common locations
            user_id = kwargs.get('user_id') or kwargs.get('current_user', {}).get('id')
            session_id = kwargs.get('session_id') or kwargs.get('request', {}).get('session_id')
            
            start_time = datetime.now()
            
            # Execute the function
            result = func(*args, **kwargs)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Count tokens in the response
            try:
                response_str = _format_function_output(result, func.__name__)
                token_result = token_counter.count_tokens(response_str, model)
                total_tokens = token_result.token_count
                
                logger.info(f"API {func.__name__} processed {total_tokens} tokens in {processing_time:.3f}s")
                
                # Log to database if we have user and session info
                if user_id and session_id:
                    try:
                        token_counter.log_token_usage(
                            user_id=user_id,
                            session_id=session_id,
                            tokens_used=total_tokens,
                            api_endpoint=func.__name__,
                            priority_level=kwargs.get('priority_level', 'Medium')
                        )
                    except Exception as e:
                        logger.warning(f"Failed to log API token usage: {e}")
                
                # Add token information to response
                if isinstance(result, dict):
                    result['token_usage'] = {
                        'tokens': total_tokens,
                        'processing_time': processing_time,
                        'model': model.value
                    }
                
            except Exception as e:
                logger.warning(f"Failed to count API tokens for {func.__name__}: {e}")
            
            return result
        
        return wrapper
    return decorator