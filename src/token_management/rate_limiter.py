"""
Rate Limiter with Dynamic Token Allocation

This module implements the main rate limiting and dynamic token allocation system
that integrates with the database and provides comprehensive rate limiting functionality.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import threading
from contextlib import contextmanager

from .lock_manager import LockManager, LockType, LockTimeoutError
from .allocation_strategies import (
    AllocationStrategy, PriorityBasedAllocation, DynamicPriorityAllocation,
    EmergencyOverrideAllocation, BurstTokenAllocation, AllocationResult,
    AllocationStrategyFactory, PriorityLevel
)
from simba.simba.database.postgres import PostgresDB
from simba.simba.database.token_models import TokenLimits, TokenUsage

logger = logging.getLogger(__name__)


class RateLimitWindow(Enum):
    """Rate limit time windows."""
    MINUTE = "1 minute"
    HOUR = "1 hour"
    DAY = "1 day"
    WEEK = "1 week"
    CUSTOM = "custom"


class RateLimitExceededError(Exception):
    """Raised when rate limits are exceeded."""
    pass


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    max_requests_per_window: int
    window_duration: RateLimitWindow
    custom_window_seconds: Optional[int] = None
    burst_limit: Optional[int] = None
    burst_window_seconds: Optional[int] = None
    enable_dynamic_allocation: bool = True
    emergency_override_enabled: bool = True
    burst_mode_enabled: bool = True


@dataclass
class TokenAllocationRequest:
    """Request for token allocation."""
    user_id: str
    tokens_requested: int
    priority_level: PriorityLevel
    api_endpoint: str
    session_id: str
    context: Optional[Dict[str, Any]] = None


@dataclass
class RateLimitCheckResult:
    """Result of rate limit check."""
    allowed: bool
    remaining_requests: int
    reset_time: datetime
    window_start: datetime
    window_duration: timedelta
    reason: str
    retry_after: Optional[int] = None


@dataclass
class TokenAllocationResult:
    """Result of token allocation."""
    success: bool
    tokens_allocated: int
    tokens_remaining: int
    priority_level: PriorityLevel
    allocation_strategy: str
    adjustment_factor: float
    emergency_override: bool
    burst_mode: bool
    reason: str
    next_reset_time: datetime


class RateLimiter:
    """
    Comprehensive rate limiter with dynamic token allocation.
    
    Provides rate limiting with configurable windows, priority-based token allocation,
    and graceful degradation when limits are exceeded.
    """
    
    def __init__(self, db: Optional[PostgresDB] = None, lock_manager: Optional[LockManager] = None):
        """
        Initialize the rate limiter.
        
        Args:
            db: Database instance for token tracking
            lock_manager: Lock manager for concurrent request handling
        """
        self.db = db or PostgresDB()
        from .lock_manager import get_lock_manager
        self.lock_manager = lock_manager or get_lock_manager()
        
        # Default allocation strategy
        self.allocation_strategy = AllocationStrategyFactory.create_comprehensive_strategy()
        
        # Rate limit configurations per user/API
        self.user_configs: Dict[str, RateLimitConfig] = {}
        self.api_configs: Dict[str, RateLimitConfig] = {}
        
        # In-memory rate tracking for performance
        self._rate_tracking: Dict[str, List[Tuple[datetime, int]]] = {}
        self._tracking_lock = threading.Lock()
        
        # Performance metrics
        self.metrics = {
            'total_checks': 0,
            'allowed_requests': 0,
            'denied_requests': 0,
            'total_allocations': 0,
            'successful_allocations': 0,
            'failed_allocations': 0,
            'emergency_overrides': 0,
            'burst_allocations': 0,
            'average_check_time': 0.0,
            'average_allocation_time': 0.0
        }
        
        # Start cleanup thread
        self._start_cleanup_thread()
        
        logger.info("RateLimiter initialized with comprehensive allocation strategy")
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread for old rate tracking data."""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(300)  # Clean every 5 minutes
                    self._cleanup_old_tracking_data()
                except Exception as e:
                    logger.error(f"Error in rate limiter cleanup: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.info("Rate limiter cleanup thread started")
    
    def _cleanup_old_tracking_data(self):
        """Clean up old rate tracking data."""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        with self._tracking_lock:
            keys_to_remove = []
            for key, timestamps in self._rate_tracking.items():
                # Remove old timestamps
                self._rate_tracking[key] = [
                    (ts, count) for ts, count in timestamps 
                    if ts > cutoff_time
                ]
                
                # Remove empty entries
                if not self._rate_tracking[key]:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._rate_tracking[key]
        
        logger.debug(f"Cleaned up {len(keys_to_remove)} old rate tracking entries")
    
    def set_user_rate_limit(self, user_id: str, config: RateLimitConfig):
        """
        Set rate limit configuration for a user.
        
        Args:
            user_id: User identifier
            config: Rate limit configuration
        """
        self.user_configs[user_id] = config
        
        # Also set in database for persistence
        window_days = self._convert_window_to_days(config.window_duration)
        self.db.set_user_token_limit(
            user_id=user_id,
            max_tokens_per_period=config.max_requests_per_window,
            period_interval=f"{window_days} days"
        )
        
        logger.info(f"Set rate limit for user {user_id}: {config.max_requests_per_window} "
                   f"requests per {config.window_duration.value}")
    
    def set_api_rate_limit(self, api_endpoint: str, config: RateLimitConfig):
        """
        Set rate limit configuration for an API endpoint.
        
        Args:
            api_endpoint: API endpoint identifier
            config: Rate limit configuration
        """
        self.api_configs[api_endpoint] = config
        logger.info(f"Set rate limit for API {api_endpoint}: {config.max_requests_per_window} "
                   f"requests per {config.window_duration.value}")
    
    def _convert_window_to_days(self, window: RateLimitWindow, custom_seconds: Optional[int] = None) -> float:
        """Convert rate limit window to days for database storage."""
        if window == RateLimitWindow.MINUTE:
            return 1/1440  # 1 minute in days
        elif window == RateLimitWindow.HOUR:
            return 1/24    # 1 hour in days
        elif window == RateLimitWindow.DAY:
            return 1.0     # 1 day
        elif window == RateLimitWindow.WEEK:
            return 7.0     # 1 week
        elif window == RateLimitWindow.CUSTOM and custom_seconds:
            return custom_seconds / 86400  # Convert seconds to days
        else:
            return 1.0  # Default to 1 day
    
    def enforce_rate_limit(self, user_id: str, api_endpoint: str, 
                          request_weight: int = 1) -> RateLimitCheckResult:
        """
        Enforce rate limits for a user and API endpoint.
        
        Args:
            user_id: User identifier
            api_endpoint: API endpoint identifier
            request_weight: Weight of the current request
            
        Returns:
            RateLimitCheckResult with check details
            
        Raises:
            RateLimitExceededError: If rate limits are exceeded
        """
        start_time = time.time()
        self.metrics['total_checks'] += 1
        
        try:
            # Get configuration
            config = self._get_effective_config(user_id, api_endpoint)
            if not config:
                # No limits configured, allow request
                result = RateLimitCheckResult(
                    allowed=True,
                    remaining_requests=999999,
                    reset_time=datetime.utcnow() + timedelta(hours=24),
                    window_start=datetime.utcnow(),
                    window_duration=timedelta(hours=24),
                    reason="No rate limits configured"
                )
                self.metrics['allowed_requests'] += 1
                return result
            
            # Check rate limits
            with self.lock_manager.lock(LockType.RATE_LIMIT_CHECK, f"{user_id}_{api_endpoint}"):
                limit_result = self._check_rate_limits(user_id, api_endpoint, config, request_weight)
                
                if not limit_result.allowed:
                    self.metrics['denied_requests'] += 1
                    raise RateLimitExceededError(
                        f"Rate limit exceeded for user {user_id} on API {api_endpoint}: "
                        f"{limit_result.reason}"
                    )
                
                self.metrics['allowed_requests'] += 1
                return limit_result
                
        except RateLimitExceededError:
            raise
        except Exception as e:
            logger.error(f"Error enforcing rate limit: {e}")
            # Allow request on error to prevent service disruption
            result = RateLimitCheckResult(
                allowed=True,
                remaining_requests=999999,
                reset_time=datetime.utcnow() + timedelta(hours=24),
                window_start=datetime.utcnow(),
                window_duration=timedelta(hours=24),
                reason=f"Error checking rate limits: {str(e)}"
            )
            self.metrics['allowed_requests'] += 1
            return result
        finally:
            # Update performance metrics
            check_time = time.time() - start_time
            self._update_performance_metric('average_check_time', check_time)
    
    def _get_effective_config(self, user_id: str, api_endpoint: str) -> Optional[RateLimitConfig]:
        """Get effective rate limit configuration for user and API."""
        # API-specific config takes precedence
        if api_endpoint in self.api_configs:
            return self.api_configs[api_endpoint]
        
        # User-specific config
        if user_id in self.user_configs:
            return self.user_configs[user_id]
        
        # Default config (if any)
        return None
    
    def _check_rate_limits(self, user_id: str, api_endpoint: str, 
                          config: RateLimitConfig, request_weight: int) -> RateLimitCheckResult:
        """Check rate limits with the given configuration."""
        current_time = datetime.utcnow()
        
        # Calculate window start
        window_start = self._get_window_start(current_time, config.window_duration, config.custom_window_seconds)
        
        # Get current usage
        usage = self._get_current_usage(user_id, api_endpoint, window_start, current_time)
        
        # Calculate remaining requests
        remaining_requests = config.max_requests_per_window - usage
        
        # Check if request is allowed
        allowed = remaining_requests >= request_weight
        
        if not allowed:
            # Calculate retry after time
            retry_after = self._calculate_retry_after(window_start, config.window_duration)
            
            return RateLimitCheckResult(
                allowed=False,
                remaining_requests=remaining_requests,
                reset_time=window_start + self._get_window_duration(config.window_duration, config.custom_window_seconds),
                window_start=window_start,
                window_duration=self._get_window_duration(config.window_duration, config.custom_window_seconds),
                reason=f"Rate limit exceeded: {usage}/{config.max_requests_per_window} requests used",
                retry_after=retry_after
            )
        
        # Update usage tracking
        self._update_usage_tracking(user_id, api_endpoint, request_weight, current_time)
        
        return RateLimitCheckResult(
            allowed=True,
            remaining_requests=remaining_requests,
            reset_time=window_start + self._get_window_duration(config.window_duration, config.custom_window_seconds),
            window_start=window_start,
            window_duration=self._get_window_duration(config.window_duration, config.custom_window_seconds),
            reason="Request allowed"
        )
    
    def _get_window_start(self, current_time: datetime, window: RateLimitWindow, 
                         custom_seconds: Optional[int] = None) -> datetime:
        """Get the start time of the current window."""
        if window == RateLimitWindow.MINUTE:
            return current_time.replace(second=0, microsecond=0)
        elif window == RateLimitWindow.HOUR:
            return current_time.replace(minute=0, second=0, microsecond=0)
        elif window == RateLimitWindow.DAY:
            return current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        elif window == RateLimitWindow.WEEK:
            # Start of week (Monday)
            days_since_monday = current_time.weekday()
            return current_time.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday)
        elif window == RateLimitWindow.CUSTOM and custom_seconds:
            return current_time.replace(microsecond=0) - timedelta(seconds=custom_seconds)
        else:
            return current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def _get_window_duration(self, window: RateLimitWindow, custom_seconds: Optional[int] = None) -> timedelta:
        """Get the duration of the window."""
        if window == RateLimitWindow.MINUTE:
            return timedelta(minutes=1)
        elif window == RateLimitWindow.HOUR:
            return timedelta(hours=1)
        elif window == RateLimitWindow.DAY:
            return timedelta(days=1)
        elif window == RateLimitWindow.WEEK:
            return timedelta(weeks=1)
        elif window == RateLimitWindow.CUSTOM and custom_seconds:
            return timedelta(seconds=custom_seconds)
        else:
            return timedelta(days=1)
    
    def _get_current_usage(self, user_id: str, api_endpoint: str, 
                          window_start: datetime, current_time: datetime) -> int:
        """Get current usage for user and API in the specified window."""
        # Check in-memory tracking first for performance
        tracking_key = f"{user_id}_{api_endpoint}"
        
        with self._tracking_lock:
            if tracking_key in self._rate_tracking:
                window_usage = sum(count for ts, count in self._rate_tracking[tracking_key] 
                                 if ts >= window_start)
                return window_usage
        
        # Fallback to database query
        try:
            usage_records = self.db.get_user_token_usage(
                user_id=user_id,
                start_date=window_start,
                end_date=current_time
            )
            
            # Filter by API endpoint if specified
            if api_endpoint:
                usage_records = [
                    record for record in usage_records 
                    if record.get('api_endpoint') == api_endpoint
                ]
            
            total_usage = sum(record.get('tokens_used', 0) for record in usage_records)
            return total_usage
            
        except Exception as e:
            logger.error(f"Error getting current usage from database: {e}")
            return 0
    
    def _update_usage_tracking(self, user_id: str, api_endpoint: str, 
                              weight: int, timestamp: datetime):
        """Update in-memory usage tracking."""
        tracking_key = f"{user_id}_{api_endpoint}"
        
        with self._tracking_lock:
            if tracking_key not in self._rate_tracking:
                self._rate_tracking[tracking_key] = []
            
            self._rate_tracking[tracking_key].append((timestamp, weight))
            
            # Keep only recent entries (last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            self._rate_tracking[tracking_key] = [
                (ts, count) for ts, count in self._rate_tracking[tracking_key]
                if ts > cutoff_time
            ]
    
    def _calculate_retry_after(self, window_start: datetime, window: RateLimitWindow) -> int:
        """Calculate retry after time in seconds."""
        window_end = window_start + self._get_window_duration(window)
        retry_after = int((window_end - datetime.utcnow()).total_seconds())
        return max(0, retry_after)
    
    def check_and_allocate_tokens(self, request: TokenAllocationRequest) -> TokenAllocationResult:
        """
        Check token limits and allocate tokens based on priority.
        
        Args:
            request: Token allocation request
            
        Returns:
            TokenAllocationResult with allocation details
            
        Raises:
            RateLimitExceededError: If token limits are exceeded
        """
        start_time = time.time()
        self.metrics['total_allocations'] += 1
        
        try:
            # Get user's token limit
            token_limit = self.db.get_user_token_limit(request.user_id)
            if not token_limit:
                return TokenAllocationResult(
                    success=False,
                    tokens_allocated=0,
                    tokens_remaining=0,
                    priority_level=request.priority_level,
                    allocation_strategy="none",
                    adjustment_factor=1.0,
                    emergency_override=False,
                    burst_mode=False,
                    reason="No token limit set for user",
                    next_reset_time=datetime.utcnow() + timedelta(days=1)
                )
            
            # Calculate remaining tokens
            remaining_tokens = token_limit['max_tokens_per_period'] - token_limit['tokens_used_in_period']
            
            # Check if user has any quota
            if remaining_tokens <= 0:
                return TokenAllocationResult(
                    success=False,
                    tokens_allocated=0,
                    tokens_remaining=0,
                    priority_level=request.priority_level,
                    allocation_strategy="quota_exceeded",
                    adjustment_factor=1.0,
                    emergency_override=False,
                    burst_mode=False,
                    reason="Token quota exhausted",
                    next_reset_time=datetime.utcnow() + timedelta(days=1)
                )
            
            # Prepare allocation context
            allocation_context = self._prepare_allocation_context(request, token_limit)
            
            # Allocate tokens based on priority
            with self.lock_manager.lock(LockType.TOKEN_ALLOCATION, request.user_id):
                allocated_tokens = self.allocation_strategy.allocate_tokens(
                    remaining_tokens, request.priority_level, allocation_context
                )
                
                # Ensure we don't allocate more than requested or available
                allocated_tokens = min(allocated_tokens, request.tokens_requested, remaining_tokens)
                
                # Update database usage
                if allocated_tokens > 0:
                    success = self.db.update_token_usage(request.user_id, allocated_tokens)
                    if success:
                        self.metrics['successful_allocations'] += 1
                        # Log the allocation
                        self.db.log_token_usage(
                            user_id=request.user_id,
                            session_id=request.session_id,
                            tokens_used=allocated_tokens,
                            api_endpoint=request.api_endpoint,
                            priority_level=request.priority_level.value
                        )
                    else:
                        self.metrics['failed_allocations'] += 1
                        allocated_tokens = 0
                
                # Get updated token limit
                updated_token_limit = self.db.get_user_token_limit(request.user_id)
                updated_remaining_tokens = (
                    updated_token_limit['max_tokens_per_period'] - 
                    updated_token_limit['tokens_used_in_period']
                ) if updated_token_limit else 0
                
                # Determine strategy used
                strategy_name = self.allocation_strategy.__class__.__name__
                
                # Check for emergency override or burst mode
                emergency_override = allocation_context.get('emergency_override', False)
                burst_mode = allocation_context.get('burst_mode', False)
                
                if emergency_override:
                    self.metrics['emergency_overrides'] += 1
                if burst_mode:
                    self.metrics['burst_allocations'] += 1
                
                return TokenAllocationResult(
                    success=allocated_tokens > 0,
                    tokens_allocated=allocated_tokens,
                    tokens_remaining=updated_remaining_tokens,
                    priority_level=request.priority_level,
                    allocation_strategy=strategy_name,
                    adjustment_factor=allocation_context.get('adjustment_factor', 1.0),
                    emergency_override=emergency_override,
                    burst_mode=burst_mode,
                    reason="Token allocation successful" if allocated_tokens > 0 else "Token allocation failed",
                    next_reset_time=updated_token_limit['period_start'] + timedelta(
                        days=int(updated_token_limit['period_interval'].split()[0])
                    ) if updated_token_limit else datetime.utcnow() + timedelta(days=1)
                )
                
        except Exception as e:
            logger.error(f"Error allocating tokens: {e}")
            self.metrics['failed_allocations'] += 1
            return TokenAllocationResult(
                success=False,
                tokens_allocated=0,
                tokens_remaining=0,
                priority_level=request.priority_level,
                allocation_strategy="error",
                adjustment_factor=1.0,
                emergency_override=False,
                burst_mode=False,
                reason=f"Error allocating tokens: {str(e)}",
                next_reset_time=datetime.utcnow() + timedelta(days=1)
            )
        finally:
            # Update performance metrics
            allocation_time = time.time() - start_time
            self._update_performance_metric('average_allocation_time', allocation_time)
    
    def _prepare_allocation_context(self, request: TokenAllocationRequest, 
                                   token_limit: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare allocation context with user and system information."""
        context = {
            'user_id': request.user_id,
            'priority_level': request.priority_level,
            'api_endpoint': request.api_endpoint,
            'tokens_requested': request.tokens_requested,
            'max_tokens': token_limit['max_tokens_per_period'],
            'used_tokens': token_limit['tokens_used_in_period'],
            'remaining_tokens': token_limit['max_tokens_per_period'] - token_limit['tokens_used_in_period']
        }
        
        # Add user history if available
        try:
            user_history = self._get_user_history(request.user_id)
            context['user_history'] = user_history
        except Exception as e:
            logger.warning(f"Error getting user history: {e}")
        
        # Add system load information
        try:
            system_load = self._get_system_load()
            context['system_load'] = system_load
        except Exception as e:
            logger.warning(f"Error getting system load: {e}")
        
        # Add time-based factor
        context['time_factor'] = self._get_time_factor()
        
        # Add emergency override if enabled
        if request.context and request.context.get('emergency_override'):
            context['emergency_override'] = True
        
        # Add burst mode if enabled
        if request.context and request.context.get('burst_mode'):
            context['burst_mode'] = True
        
        return context
    
    def _get_user_history(self, user_id: str) -> Dict[str, Any]:
        """Get user's token usage history for dynamic allocation."""
        try:
            # Get usage from last 7 days
            start_date = datetime.utcnow() - timedelta(days=7)
            usage_records = self.db.get_user_token_usage(user_id, start_date)
            
            if not usage_records:
                return {'usage_ratio': 0.0, 'compliance_score': 1.0}
            
            total_used = sum(record['tokens_used'] for record in usage_records)
            max_possible = len(usage_records) * 1000  # Assuming 1000 max per request
            
            usage_ratio = min(1.0, total_used / max_possible) if max_possible > 0 else 0.0
            
            # Calculate compliance score (how often user stays within limits)
            compliant_requests = sum(1 for record in usage_records if record['tokens_used'] <= 1000)
            compliance_score = compliant_requests / len(usage_records) if usage_records else 1.0
            
            return {
                'usage_ratio': usage_ratio,
                'compliance_score': compliance_score,
                'total_requests': len(usage_records),
                'total_tokens': total_used
            }
            
        except Exception as e:
            logger.error(f"Error getting user history: {e}")
            return {'usage_ratio': 1.0, 'compliance_score': 1.0}
    
    def _get_system_load(self) -> Dict[str, Any]:
        """Get current system load information."""
        try:
            # This is a simplified implementation
            # In a real system, you would get actual system metrics
            active_users = len(self.user_configs)
            total_configs = len(self.user_configs) + len(self.api_configs)
            
            load_percentage = min(100.0, (active_users / max(1, total_configs)) * 100)
            
            return {
                'load_percentage': load_percentage,
                'active_users': active_users,
                'total_configs': total_configs,
                'system_load': 'normal' if load_percentage < 70 else 'high'
            }
            
        except Exception as e:
            logger.error(f"Error getting system load: {e}")
            return {'load_percentage': 50.0, 'system_load': 'normal'}
    
    def _get_time_factor(self) -> float:
        """Get time-based adjustment factor."""
        current_hour = datetime.utcnow().hour
        
        # Higher allocation during off-peak hours
        if 2 <= current_hour <= 5:  # 2 AM - 5 AM
            return 1.2
        elif 22 <= current_hour or current_hour <= 6:  # 10 PM - 6 AM
            return 1.1
        elif 9 <= current_hour <= 17:  # 9 AM - 5 PM (business hours)
            return 0.9
        else:
            return 1.0
    
    def get_available_tokens(self, user_id: str) -> Dict[str, Any]:
        """
        Get available tokens for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with token information
        """
        try:
            token_limit = self.db.get_user_token_limit(user_id)
            if not token_limit:
                return {
                    'user_id': user_id,
                    'max_tokens': 0,
                    'used_tokens': 0,
                    'available_tokens': 0,
                    'period_start': datetime.utcnow().isoformat(),
                    'period_end': (datetime.utcnow() + timedelta(days=1)).isoformat()
                }
            
            available_tokens = token_limit['max_tokens_per_period'] - token_limit['tokens_used_in_period']
            period_end = token_limit['period_start'] + timedelta(
                days=int(token_limit['period_interval'].split()[0])
            )
            
            return {
                'user_id': user_id,
                'max_tokens': token_limit['max_tokens_per_period'],
                'used_tokens': token_limit['tokens_used_in_period'],
                'available_tokens': max(0, available_tokens),
                'period_start': token_limit['period_start'].isoformat(),
                'period_end': period_end.isoformat(),
                'usage_percentage': (token_limit['tokens_used_in_period'] / token_limit['max_tokens_per_period']) * 100
            }
            
        except Exception as e:
            logger.error(f"Error getting available tokens: {e}")
            return {
                'user_id': user_id,
                'max_tokens': 0,
                'used_tokens': 0,
                'available_tokens': 0,
                'period_start': datetime.utcnow().isoformat(),
                'period_end': (datetime.utcnow() + timedelta(days=1)).isoformat(),
                'error': str(e)
            }
    
    def reset_period_counters(self, user_id: Optional[str] = None):
        """
        Reset usage counters at period boundaries.
        
        Args:
            user_id: Specific user to reset (None for all users)
        """
        try:
            if user_id:
                # Reset specific user
                config = self.user_configs.get(user_id, RateLimitConfig(1000, RateLimitWindow.DAY))
                self.db.set_user_token_limit(
                    user_id=user_id,
                    max_tokens_per_period=config.max_requests_per_window,
                    period_interval="1 day"
                )
                logger.info(f"Reset period counters for user {user_id}")
            else:
                # Reset all users
                for uid in self.user_configs:
                    config = self.user_configs[uid]
                    self.db.set_user_token_limit(
                        user_id=uid,
                        max_tokens_per_period=config.max_requests_per_window,
                        period_interval="1 day"
                    )
                logger.info("Reset period counters for all users")
                
        except Exception as e:
            logger.error(f"Error resetting period counters: {e}")
    
    def _update_performance_metric(self, metric_name: str, value: float):
        """Update performance metric with exponential moving average."""
        if metric_name in self.metrics:
            current_avg = self.metrics[metric_name]
            alpha = 0.1  # Smoothing factor
            self.metrics[metric_name] = alpha * value + (1 - alpha) * current_avg
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the rate limiter."""
        return self.metrics.copy()
    
    def emergency_release_all_locks(self):
        """Emergency release all locks."""
        self.lock_manager.emergency_release_all()
        logger.warning("Emergency released all rate limiter locks")
    
    def shutdown(self):
        """Shutdown the rate limiter and cleanup resources."""
        self.emergency_release_all_locks()
        logger.info("RateLimiter shutdown complete")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


# Convenience functions
def get_rate_limiter() -> RateLimiter:
    """Get a global rate limiter instance."""
    return RateLimiter()


def set_allocation_strategy(strategy: AllocationStrategy):
    """Set the global allocation strategy."""
    global _global_allocation_strategy
    _global_allocation_strategy = strategy


# Global allocation strategy
_global_allocation_strategy = None