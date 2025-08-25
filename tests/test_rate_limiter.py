"""
Comprehensive Test Suite for Rate Limiter

This module contains unit tests for the rate limiting and dynamic token allocation system.
"""

import unittest
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from token_management.rate_limiter import (
    RateLimiter, RateLimitConfig, RateLimitWindow, TokenAllocationRequest,
    PriorityLevel, RateLimitExceededError
)
from token_management.allocation_strategies import (
    PriorityBasedAllocation, DynamicPriorityAllocation, EmergencyOverrideAllocation,
    BurstTokenAllocation, AllocationStrategyFactory, AllocationStrategy
)
from token_management.lock_manager import LockManager, LockType, LockTimeoutError
from simba.simba.database.postgres import PostgresDB


class TestRateLimitConfig(unittest.TestCase):
    """Test cases for RateLimitConfig."""
    
    def test_rate_limit_config_creation(self):
        """Test creating a rate limit configuration."""
        config = RateLimitConfig(
            max_requests_per_window=100,
            window_duration=RateLimitWindow.HOUR
        )
        
        self.assertEqual(config.max_requests_per_window, 100)
        self.assertEqual(config.window_duration, RateLimitWindow.HOUR)
        self.assertFalse(config.enable_dynamic_allocation)
    
    def test_rate_limit_config_with_burst(self):
        """Test creating a rate limit configuration with burst limits."""
        config = RateLimitConfig(
            max_requests_per_window=100,
            window_duration=RateLimitWindow.HOUR,
            burst_limit=200,
            burst_window_seconds=300
        )
        
        self.assertEqual(config.burst_limit, 200)
        self.assertEqual(config.burst_window_seconds, 300)


class TestPriorityBasedAllocation(unittest.TestCase):
    """Test cases for PriorityBasedAllocation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.allocation = PriorityBasedAllocation()
    
    def test_allocation_percentages(self):
        """Test allocation percentages for different priority levels."""
        self.assertEqual(self.allocation.get_allocation_percentage(PriorityLevel.HIGH), 0.5)
        self.assertEqual(self.allocation.get_allocation_percentage(PriorityLevel.MEDIUM), 0.3)
        self.assertEqual(self.allocation.get_allocation_percentage(PriorityLevel.LOW), 0.2)
    
    def test_token_allocation(self):
        """Test token allocation based on priority."""
        available_tokens = 1000
        
        # High priority gets 50%
        high_allocated = self.allocation.allocate_tokens(available_tokens, PriorityLevel.HIGH)
        self.assertEqual(high_allocated, 500)
        
        # Medium priority gets 30%
        medium_allocated = self.allocation.allocate_tokens(available_tokens, PriorityLevel.MEDIUM)
        self.assertEqual(medium_allocated, 300)
        
        # Low priority gets 20%
        low_allocated = self.allocation.allocate_tokens(available_tokens, PriorityLevel.LOW)
        self.assertEqual(low_allocated, 200)
    
    def test_allocation_with_zero_tokens(self):
        """Test allocation when no tokens are available."""
        allocated = self.allocation.allocate_tokens(0, PriorityLevel.HIGH)
        self.assertEqual(allocated, 0)
    
    def test_allocation_with_insufficient_tokens(self):
        """Test allocation when available tokens are less than allocation percentage."""
        allocated = self.allocation.allocate_tokens(10, PriorityLevel.HIGH)
        self.assertEqual(allocated, 5)  # 50% of 10


class TestDynamicPriorityAllocation(unittest.TestCase):
    """Test cases for DynamicPriorityAllocation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.base_strategy = PriorityBasedAllocation()
        self.dynamic_strategy = DynamicPriorityAllocation(self.base_strategy)
    
    def test_base_allocation_passthrough(self):
        """Test that base allocation is used when no context is provided."""
        allocated = self.dynamic_strategy.allocate_tokens(1000, PriorityLevel.HIGH)
        self.assertEqual(allocated, 500)  # 50% from base strategy
    
    def test_user_history_boost(self):
        """Test allocation boost for users with good history."""
        context = {
            'user_history': {
                'usage_ratio': 0.6,
                'compliance_score': 0.9
            }
        }
        
        allocated = self.dynamic_strategy.allocate_tokens(1000, PriorityLevel.HIGH, context)
        # Should get boost due to good compliance and moderate usage
        self.assertGreater(allocated, 500)
    
    def test_user_history_penalty(self):
        """Test allocation penalty for users with high usage."""
        context = {
            'user_history': {
                'usage_ratio': 0.96,
                'compliance_score': 0.8
            }
        }
        
        allocated = self.dynamic_strategy.allocate_tokens(1000, PriorityLevel.HIGH, context)
        # Should get penalty due to high usage
        self.assertLess(allocated, 500)
    
    def test_system_load_adjustment(self):
        """Test allocation adjustment based on system load."""
        context = {
            'system_load': {
                'load_percentage': 85.0,
                'system_load': 'high'
            }
        }
        
        allocated = self.dynamic_strategy.allocate_tokens(1000, PriorityLevel.HIGH, context)
        # Should get reduction due to high system load
        self.assertLess(allocated, 500)


class TestEmergencyOverrideAllocation(unittest.TestCase):
    """Test cases for EmergencyOverrideAllocation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.base_strategy = PriorityBasedAllocation()
        self.emergency_strategy = EmergencyOverrideAllocation(self.base_strategy)
    
    def test_normal_allocation(self):
        """Test normal allocation when no emergency is present."""
        allocated = self.emergency_strategy.allocate_tokens(1000, PriorityLevel.HIGH)
        self.assertEqual(allocated, 500)  # Normal allocation
    
    def test_emergency_override(self):
        """Test emergency override allocation."""
        context = {
            'emergency_override': True
        }
        
        allocated = self.emergency_strategy.allocate_tokens(1000, PriorityLevel.HIGH, context)
        # Should get emergency allocation (80% of available)
        self.assertEqual(allocated, 800)
    
    def test_system_emergency(self):
        """Test system emergency allocation."""
        context = {
            'system_emergency': True
        }
        
        allocated = self.emergency_strategy.allocate_tokens(1000, PriorityLevel.HIGH, context)
        # Should get emergency allocation (80% of available)
        self.assertEqual(allocated, 800)


class TestBurstTokenAllocation(unittest.TestCase):
    """Test cases for BurstTokenAllocation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.base_strategy = PriorityBasedAllocation()
        self.burst_strategy = BurstTokenAllocation(self.base_strategy, burst_multiplier=2.0)
    
    def test_normal_allocation(self):
        """Test normal allocation when burst mode is not enabled."""
        allocated = self.burst_strategy.allocate_tokens(1000, PriorityLevel.HIGH)
        self.assertEqual(allocated, 500)  # Normal allocation
    
    def test_burst_allocation(self):
        """Test burst allocation when burst mode is enabled."""
        context = {
            'burst_mode': True
        }
        
        allocated = self.burst_strategy.allocate_tokens(1000, PriorityLevel.HIGH, context)
        # Should get burst allocation (100% = 50% * 2.0)
        self.assertEqual(allocated, 1000)
    
    def test_burst_with_limit(self):
        """Test burst allocation with maximum burst limit."""
        burst_strategy = BurstTokenAllocation(
            self.base_strategy, 
            burst_multiplier=3.0, 
            max_burst_tokens=800
        )
        
        context = {
            'burst_mode': True
        }
        
        allocated = burst_strategy.allocate_tokens(1000, PriorityLevel.HIGH, context)
        # Should be limited to max_burst_tokens
        self.assertEqual(allocated, 800)


class TestLockManager(unittest.TestCase):
    """Test cases for LockManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.lock_manager = LockManager(default_timeout=1.0)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.lock_manager.shutdown()
    
    def test_lock_acquisition_and_release(self):
        """Test basic lock acquisition and release."""
        lock_id = self.lock_manager.acquire_lock(LockType.TOKEN_ALLOCATION, "test_resource")
        self.assertIsNotNone(lock_id)
        
        # Check if resource is locked
        self.assertTrue(self.lock_manager.is_locked(LockType.TOKEN_ALLOCATION, "test_resource"))
        
        # Release the lock
        self.lock_manager.release_lock(lock_id)
        
        # Check if resource is no longer locked
        self.assertFalse(self.lock_manager.is_locked(LockType.TOKEN_ALLOCATION, "test_resource"))
    
    def test_lock_timeout(self):
        """Test lock timeout behavior."""
        # Acquire lock
        lock_id = self.lock_manager.acquire_lock(LockType.TOKEN_ALLOCATION, "test_resource")
        
        # Try to acquire same lock with timeout
        with self.assertRaises(LockTimeoutError):
            self.lock_manager.acquire_lock(LockType.TOKEN_ALLOCATION, "test_resource", timeout=0.5)
        
        # Release lock
        self.lock_manager.release_lock(lock_id)
    
    def test_context_manager(self):
        """Test lock manager as context manager."""
        with self.lock_manager.lock(LockType.TOKEN_ALLOCATION, "test_resource") as lock_id:
            self.assertIsNotNone(lock_id)
            self.assertTrue(self.lock_manager.is_locked(LockType.TOKEN_ALLOCATION, "test_resource"))
        
        # Lock should be released after context manager exits
        self.assertFalse(self.lock_manager.is_locked(LockType.TOKEN_ALLOCATION, "test_resource"))
    
    def test_recursive_locking(self):
        """Test recursive locking by the same thread."""
        lock_id = self.lock_manager.acquire_lock(LockType.TOKEN_ALLOCATION, "test_resource")
        
        # Try to acquire same lock again (should succeed for same thread)
        lock_id2 = self.lock_manager.acquire_lock(LockType.TOKEN_ALLOCATION, "test_resource")
        self.assertEqual(lock_id, lock_id2)
        
        # Release lock twice
        self.lock_manager.release_lock(lock_id)
        self.lock_manager.release_lock(lock_id2)
        
        # Lock should still be held (recursive)
        self.assertTrue(self.lock_manager.is_locked(LockType.TOKEN_ALLOCATION, "test_resource"))
        
        # Final release
        self.lock_manager.release_lock(lock_id)
        self.assertFalse(self.lock_manager.is_locked(LockType.TOKEN_ALLOCATION, "test_resource"))


class TestRateLimiter(unittest.TestCase):
    """Test cases for RateLimiter."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock database
        self.mock_db = Mock(spec=PostgresDB)
        self.mock_db.get_user_token_limit.return_value = {
            'max_tokens_per_period': 1000,
            'tokens_used_in_period': 100,
            'period_start': datetime.utcnow() - timedelta(hours=1)
        }
        self.mock_db.update_token_usage.return_value = True
        self.mock_db.log_token_usage.return_value = True
        
        # Create rate limiter with mock database
        self.rate_limiter = RateLimiter(db=self.mock_db)
        
        # Set up user configuration
        config = RateLimitConfig(
            max_requests_per_window=100,
            window_duration=RateLimitWindow.HOUR
        )
        self.rate_limiter.set_user_rate_limit("test_user", config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.rate_limiter.shutdown()
    
    def test_rate_limit_check_allowed(self):
        """Test rate limit check when request is allowed."""
        result = self.rate_limiter.enforce_rate_limit("test_user", "test_api")
        
        self.assertTrue(result.allowed)
        self.assertEqual(result.remaining_requests, 99)
        self.assertEqual(result.reason, "Request allowed")
    
    def test_rate_limit_check_denied(self):
        """Test rate limit check when request is denied."""
        # Set up to exceed limit
        self.mock_db.get_user_token_limit.return_value = {
            'max_tokens_per_period': 100,
            'tokens_used_in_period': 100,
            'period_start': datetime.utcnow() - timedelta(hours=1)
        }
        
        with self.assertRaises(RateLimitExceededError):
            self.rate_limiter.enforce_rate_limit("test_user", "test_api")
    
    def test_token_allocation_success(self):
        """Test successful token allocation."""
        request = TokenAllocationRequest(
            user_id="test_user",
            tokens_requested=50,
            priority_level=PriorityLevel.HIGH,
            api_endpoint="test_api",
            session_id="test_session"
        )
        
        result = self.rate_limiter.check_and_allocate_tokens(request)
        
        self.assertTrue(result.success)
        self.assertEqual(result.tokens_allocated, 50)
        self.assertEqual(result.priority_level, PriorityLevel.HIGH)
    
    def test_token_allocation_failure(self):
        """Test token allocation failure when quota is exhausted."""
        # Set up exhausted quota
        self.mock_db.get_user_token_limit.return_value = {
            'max_tokens_per_period': 100,
            'tokens_used_in_period': 100,
            'period_start': datetime.utcnow() - timedelta(hours=1)
        }
        
        request = TokenAllocationRequest(
            user_id="test_user",
            tokens_requested=50,
            priority_level=PriorityLevel.HIGH,
            api_endpoint="test_api",
            session_id="test_session"
        )
        
        result = self.rate_limiter.check_and_allocate_tokens(request)
        
        self.assertFalse(result.success)
        self.assertEqual(result.tokens_allocated, 0)
        self.assertEqual(result.reason, "Token quota exhausted")
    
    def test_get_available_tokens(self):
        """Test getting available tokens for a user."""
        result = self.rate_limiter.get_available_tokens("test_user")
        
        self.assertEqual(result['user_id'], "test_user")
        self.assertEqual(result['max_tokens'], 1000)
        self.assertEqual(result['used_tokens'], 100)
        self.assertEqual(result['available_tokens'], 900)
    
    def test_get_available_tokens_no_limit(self):
        """Test getting available tokens when no limit is set."""
        self.mock_db.get_user_token_limit.return_value = None
        
        result = self.rate_limiter.get_available_tokens("test_user")
        
        self.assertEqual(result['user_id'], "test_user")
        self.assertEqual(result['max_tokens'], 0)
        self.assertEqual(result['available_tokens'], 0)
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        results = []
        
        def make_request():
            try:
                result = self.rate_limiter.enforce_rate_limit("test_user", "test_api")
                results.append(result)
            except RateLimitExceededError:
                results.append("denied")
        
        # Make multiple concurrent requests
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should be allowed (within limit)
        self.assertEqual(len(results), 10)
        for result in results:
            self.assertTrue(result.allowed if hasattr(result, 'allowed') else result != "denied")


class TestAllocationStrategyFactory(unittest.TestCase):
    """Test cases for AllocationStrategyFactory."""
    
    def test_create_priority_based(self):
        """Test creating priority-based allocation strategy."""
        strategy = AllocationStrategyFactory.create_priority_based()
        
        self.assertIsInstance(strategy, PriorityBasedAllocation)
        self.assertEqual(strategy.get_allocation_percentage(PriorityLevel.HIGH), 0.5)
    
    def test_create_dynamic_priority(self):
        """Test creating dynamic priority allocation strategy."""
        strategy = AllocationStrategyFactory.create_dynamic_priority()
        
        self.assertIsInstance(strategy, DynamicPriorityAllocation)
        self.assertIsInstance(strategy.base_strategy, PriorityBasedAllocation)
    
    def test_create_emergency_override(self):
        """Test creating emergency override allocation strategy."""
        strategy = AllocationStrategyFactory.create_emergency_override()
        
        self.assertIsInstance(strategy, EmergencyOverrideAllocation)
        self.assertIsInstance(strategy.base_strategy, PriorityBasedAllocation)
    
    def test_create_burst_token(self):
        """Test creating burst token allocation strategy."""
        strategy = AllocationStrategyFactory.create_burst_token()
        
        self.assertIsInstance(strategy, BurstTokenAllocation)
        self.assertIsInstance(strategy.base_strategy, PriorityBasedAllocation)
    
    def test_create_comprehensive_strategy(self):
        """Test creating comprehensive allocation strategy."""
        strategy = AllocationStrategyFactory.create_comprehensive_strategy()
        
        # Should be a composite strategy with all features
        self.assertIsInstance(strategy, BurstTokenAllocation)
        self.assertIsInstance(strategy.base_strategy, EmergencyOverrideAllocation)
        self.assertIsInstance(strategy.base_strategy.base_strategy, DynamicPriorityAllocation)
        self.assertIsInstance(strategy.base_strategy.base_strategy.base_strategy, PriorityBasedAllocation)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete rate limiting system."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create real database (in-memory SQLite for testing)
        self.mock_db = Mock(spec=PostgresDB)
        self.mock_db.get_user_token_limit.return_value = {
            'max_tokens_per_period': 1000,
            'tokens_used_in_period': 0,
            'period_start': datetime.utcnow()
        }
        self.mock_db.update_token_usage.return_value = True
        self.mock_db.log_token_usage.return_value = True
        
        # Create rate limiter
        self.rate_limiter = RateLimiter(db=self.mock_db)
        
        # Set up configurations
        user_config = RateLimitConfig(
            max_requests_per_window=100,
            window_duration=RateLimitWindow.HOUR,
            enable_dynamic_allocation=True,
            emergency_override_enabled=True,
            burst_mode_enabled=True
        )
        self.rate_limiter.set_user_rate_limit("test_user", user_config)
        
        api_config = RateLimitConfig(
            max_requests_per_window=50,
            window_duration=RateLimitWindow.MINUTE
        )
        self.rate_limiter.set_api_rate_limit("test_api", api_config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.rate_limiter.shutdown()
    
    def test_end_to_end_rate_limiting(self):
        """Test end-to-end rate limiting with all components."""
        # Test rate limit enforcement
        result = self.rate_limiter.enforce_rate_limit("test_user", "test_api")
        self.assertTrue(result.allowed)
        
        # Test token allocation
        request = TokenAllocationRequest(
            user_id="test_user",
            tokens_requested=100,
            priority_level=PriorityLevel.HIGH,
            api_endpoint="test_api",
            session_id="test_session"
        )
        
        allocation_result = self.rate_limiter.check_and_allocate_tokens(request)
        self.assertTrue(allocation_result.success)
        self.assertEqual(allocation_result.tokens_allocated, 100)
        
        # Test that usage was updated
        self.mock_db.update_token_usage.assert_called_once_with("test_user", 100)
        self.mock_db.log_token_usage.assert_called_once()
    
    def test_emergency_override_scenario(self):
        """Test emergency override scenario."""
        request = TokenAllocationRequest(
            user_id="test_user",
            tokens_requested=1000,
            priority_level=PriorityLevel.HIGH,
            api_endpoint="test_api",
            session_id="test_session",
            context={'emergency_override': True}
        )
        
        allocation_result = self.rate_limiter.check_and_allocate_tokens(request)
        
        # Emergency override should allow allocation
        self.assertTrue(allocation_result.success)
        self.assertTrue(allocation_result.emergency_override)
    
    def test_burst_mode_scenario(self):
        """Test burst mode scenario."""
        request = TokenAllocationRequest(
            user_id="test_user",
            tokens_requested=200,
            priority_level=PriorityLevel.HIGH,
            api_endpoint="test_api",
            session_id="test_session",
            context={'burst_mode': True}
        )
        
        allocation_result = self.rate_limiter.check_and_allocate_tokens(request)
        
        # Burst mode should allow higher allocation
        self.assertTrue(allocation_result.success)
        self.assertTrue(allocation_result.burst_mode)
        self.assertGreater(allocation_result.tokens_allocated, 100)  # More than normal allocation
    
    def test_performance_metrics(self):
        """Test performance metrics tracking."""
        # Make some requests
        for i in range(5):
            self.rate_limiter.enforce_rate_limit("test_user", "test_api")
        
        # Get metrics
        metrics = self.rate_limiter.get_performance_metrics()
        
        self.assertEqual(metrics['total_checks'], 5)
        self.assertEqual(metrics['allowed_requests'], 5)
        self.assertEqual(metrics['denied_requests'], 0)
        self.assertGreater(metrics['average_check_time'], 0)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)