"""
Allocation Strategies for Dynamic Token Allocation

This module implements different token allocation strategies based on priority levels
and system requirements for the rate limiting system.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import math

from .lock_manager import LockManager, LockType

logger = logging.getLogger(__name__)


class PriorityLevel(Enum):
    """Priority levels for token allocation."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class AllocationStrategy(ABC):
    """Abstract base class for token allocation strategies."""
    
    @abstractmethod
    def allocate_tokens(self, available_tokens: int, priority_level: PriorityLevel, 
                       user_context: Optional[Dict[str, Any]] = None) -> int:
        """
        Allocate tokens based on the strategy.
        
        Args:
            available_tokens: Number of tokens available for allocation
            priority_level: Priority level of the request
            user_context: Additional context about the user
            
        Returns:
            Number of tokens to allocate
        """
        pass
    
    @abstractmethod
    def get_allocation_percentage(self, priority_level: PriorityLevel) -> float:
        """
        Get the allocation percentage for a priority level.
        
        Args:
            priority_level: Priority level to get percentage for
            
        Returns:
            Allocation percentage (0.0 to 1.0)
        """
        pass


class PriorityBasedAllocation(AllocationStrategy):
    """
    Priority-based token allocation strategy.
    
    Implements the standard allocation:
    - High: 50% of remaining quota
    - Medium: 30% of remaining quota  
    - Low: 20% of remaining quota
    """
    
    def __init__(self, high_percentage: float = 0.5, medium_percentage: float = 0.3, 
                 low_percentage: float = 0.2):
        """
        Initialize priority-based allocation.
        
        Args:
            high_percentage: Allocation percentage for high priority
            medium_percentage: Allocation percentage for medium priority
            low_percentage: Allocation percentage for low priority
        """
        self.percentages = {
            PriorityLevel.HIGH: high_percentage,
            PriorityLevel.MEDIUM: medium_percentage,
            PriorityLevel.LOW: low_percentage
        }
        
        # Validate percentages sum to 1.0
        total = sum(self.percentages.values())
        if not math.isclose(total, 1.0, rel_tol=1e-9):
            raise ValueError(f"Allocation percentages must sum to 1.0, got {total}")
        
        logger.info(f"PriorityBasedAllocation initialized with High: {high_percentage}, "
                   f"Medium: {medium_percentage}, Low: {low_percentage}")
    
    def allocate_tokens(self, available_tokens: int, priority_level: PriorityLevel,
                       user_context: Optional[Dict[str, Any]] = None) -> int:
        """
        Allocate tokens based on priority level.
        
        Args:
            available_tokens: Number of tokens available for allocation
            priority_level: Priority level of the request
            user_context: Additional context about the user (unused in basic strategy)
            
        Returns:
            Number of tokens to allocate
        """
        if available_tokens <= 0:
            return 0
        
        percentage = self.get_allocation_percentage(priority_level)
        allocated_tokens = int(available_tokens * percentage)
        
        # Ensure we don't allocate more than available
        allocated_tokens = min(allocated_tokens, available_tokens)
        
        logger.debug(f"Allocated {allocated_tokens} tokens for {priority_level.value} "
                    f"priority ({percentage*100:.1f}% of {available_tokens} available)")
        
        return allocated_tokens
    
    def get_allocation_percentage(self, priority_level: PriorityLevel) -> float:
        """Get the allocation percentage for a priority level."""
        return self.percentages.get(priority_level, 0.0)


class DynamicPriorityAllocation(AllocationStrategy):
    """
    Dynamic priority allocation that adjusts based on user history and system load.
    
    This strategy considers:
    - User's historical usage patterns
    - Current system load
    - Priority level
    - Time-based factors
    """
    
    def __init__(self, base_strategy: AllocationStrategy,
                 user_history_weight: float = 0.3,
                 system_load_weight: float = 0.2,
                 time_factor_weight: float = 0.1):
        """
        Initialize dynamic priority allocation.
        
        Args:
            base_strategy: Base allocation strategy to use
            user_history_weight: Weight for user history adjustments
            system_load_weight: Weight for system load adjustments
            time_factor_weight: Weight for time-based adjustments
        """
        self.base_strategy = base_strategy
        self.user_history_weight = user_history_weight
        self.system_load_weight = system_load_weight
        self.time_factor_weight = time_factor_weight
        
        logger.info(f"DynamicPriorityAllocation initialized with weights: "
                   f"user_history={user_history_weight}, system_load={system_load_weight}, "
                   f"time_factor={time_factor_weight}")
    
    def allocate_tokens(self, available_tokens: int, priority_level: PriorityLevel,
                       user_context: Optional[Dict[str, Any]] = None) -> int:
        """
        Allocate tokens with dynamic adjustments.
        
        Args:
            available_tokens: Number of tokens available for allocation
            priority_level: Priority level of the request
            user_context: Additional context about the user including history and load
            
        Returns:
            Number of tokens to allocate
        """
        if available_tokens <= 0:
            return 0
        
        # Get base allocation
        base_allocation = self.base_strategy.allocate_tokens(
            available_tokens, priority_level, user_context
        )
        
        # Apply dynamic adjustments
        adjustment_factor = self._calculate_adjustment_factor(user_context)
        adjusted_allocation = int(base_allocation * adjustment_factor)
        
        # Ensure we don't allocate more than available
        adjusted_allocation = min(adjusted_allocation, available_tokens)
        
        logger.debug(f"Dynamic allocation: base={base_allocation}, "
                    f"adjustment_factor={adjustment_factor:.2f}, "
                    f"adjusted={adjusted_allocation}")
        
        return adjusted_allocation
    
    def _calculate_adjustment_factor(self, user_context: Optional[Dict[str, Any]]) -> float:
        """Calculate adjustment factor based on various factors."""
        if not user_context:
            return 1.0
        
        adjustment_factor = 1.0
        
        # User history adjustment
        if 'user_history' in user_context:
            history_factor = self._calculate_user_history_factor(
                user_context['user_history']
            )
            adjustment_factor += (history_factor - 1.0) * self.user_history_weight
        
        # System load adjustment
        if 'system_load' in user_context:
            load_factor = self._calculate_system_load_factor(
                user_context['system_load']
            )
            adjustment_factor += (load_factor - 1.0) * self.system_load_weight
        
        # Time-based adjustment
        if 'time_factor' in user_context:
            time_factor = user_context['time_factor']
            adjustment_factor += (time_factor - 1.0) * self.time_factor_weight
        
        # Clamp adjustment factor to reasonable bounds
        adjustment_factor = max(0.1, min(3.0, adjustment_factor))
        
        return adjustment_factor
    
    def _calculate_user_history_factor(self, user_history: Dict[str, Any]) -> float:
        """Calculate adjustment factor based on user history."""
        if not user_history:
            return 1.0
        
        # Consider usage patterns, compliance, etc.
        usage_ratio = user_history.get('usage_ratio', 1.0)
        compliance_score = user_history.get('compliance_score', 1.0)
        
        # Users with good compliance and moderate usage get slight boost
        if compliance_score > 0.8 and 0.5 < usage_ratio < 0.9:
            return 1.1
        # Users with high usage get penalty
        elif usage_ratio > 0.95:
            return 0.8
        # Users with low usage get boost
        elif usage_ratio < 0.3:
            return 1.2
        
        return 1.0
    
    def _calculate_system_load_factor(self, system_load: Dict[str, Any]) -> float:
        """Calculate adjustment factor based on system load."""
        if not system_load:
            return 1.0
        
        load_percentage = system_load.get('load_percentage', 50.0)
        
        # Reduce allocation when system is heavily loaded
        if load_percentage > 80:
            return 0.7
        elif load_percentage > 60:
            return 0.85
        elif load_percentage < 20:
            return 1.1
        
        return 1.0
    
    def get_allocation_percentage(self, priority_level: PriorityLevel) -> float:
        """Get the base allocation percentage for a priority level."""
        return self.base_strategy.get_allocation_percentage(priority_level)


class EmergencyOverrideAllocation(AllocationStrategy):
    """
    Emergency override allocation for critical situations.
    
    This strategy allows administrators to override normal allocation
    rules during emergencies or special circumstances.
    """
    
    def __init__(self, base_strategy: AllocationStrategy,
                 emergency_threshold: float = 0.95,
                 override_percentage: float = 0.8):
        """
        Initialize emergency override allocation.
        
        Args:
            base_strategy: Base allocation strategy to use
            emergency_threshold: Threshold for emergency condition (0.0 to 1.0)
            override_percentage: Percentage of quota to allocate during emergency (0.0 to 1.0)
        """
        self.base_strategy = base_strategy
        self.emergency_threshold = emergency_threshold
        self.override_percentage = override_percentage
        
        logger.info(f"EmergencyOverrideAllocation initialized with threshold={emergency_threshold}, "
                   f"override_percentage={override_percentage}")
    
    def allocate_tokens(self, available_tokens: int, priority_level: PriorityLevel,
                       user_context: Optional[Dict[str, Any]] = None) -> int:
        """
        Allocate tokens with emergency override capability.
        
        Args:
            available_tokens: Number of tokens available for allocation
            priority_level: Priority level of the request
            user_context: Additional context including emergency status
            
        Returns:
            Number of tokens to allocate
        """
        if available_tokens <= 0:
            return 0
        
        # Check for emergency override
        if user_context and user_context.get('emergency_override', False):
            emergency_allocation = int(available_tokens * self.override_percentage)
            logger.warning(f"Emergency override activated, allocating {emergency_allocation} tokens")
            return emergency_allocation
        
        # Check if system is in emergency state
        if user_context and user_context.get('system_emergency', False):
            emergency_allocation = int(available_tokens * self.override_percentage)
            logger.warning(f"System emergency detected, allocating {emergency_allocation} tokens")
            return emergency_allocation
        
        # Use normal allocation
        return self.base_strategy.allocate_tokens(
            available_tokens, priority_level, user_context
        )
    
    def get_allocation_percentage(self, priority_level: PriorityLevel) -> float:
        """Get the base allocation percentage for a priority level."""
        return self.base_strategy.get_allocation_percentage(priority_level)


class BurstTokenAllocation(AllocationStrategy):
    """
    Burst token allocation for handling spike traffic.
    
    This strategy allows for temporary allocation of additional tokens
    during periods of high demand, with mechanisms to prevent abuse.
    """
    
    def __init__(self, base_strategy: AllocationStrategy,
                 burst_multiplier: float = 2.0,
                 burst_window_minutes: int = 15,
                 max_burst_tokens: int = 1000):
        """
        Initialize burst token allocation.
        
        Args:
            base_strategy: Base allocation strategy to use
            burst_multiplier: Multiplier for burst allocation
            burst_window_minutes: Time window for burst allocation
            max_burst_tokens: Maximum tokens that can be allocated in burst mode
        """
        self.base_strategy = base_strategy
        self.burst_multiplier = burst_multiplier
        self.burst_window = timedelta(minutes=burst_window_minutes)
        self.max_burst_tokens = max_burst_tokens
        
        logger.info(f"BurstTokenAllocation initialized with multiplier={burst_multiplier}, "
                   f"window={burst_window_minutes}min, max_tokens={max_burst_tokens}")
    
    def allocate_tokens(self, available_tokens: int, priority_level: PriorityLevel,
                       user_context: Optional[Dict[str, Any]] = None) -> int:
        """
        Allocate tokens with burst capability.
        
        Args:
            available_tokens: Number of tokens available for allocation
            priority_level: Priority level of the request
            user_context: Additional context including burst status
            
        Returns:
            Number of tokens to allocate
        """
        if available_tokens <= 0:
            return 0
        
        # Check if burst mode is enabled
        if user_context and user_context.get('burst_mode', False):
            base_allocation = self.base_strategy.allocate_tokens(
                available_tokens, priority_level, user_context
            )
            
            # Apply burst multiplier
            burst_allocation = int(base_allocation * self.burst_multiplier)
            
            # Apply burst limits
            burst_allocation = min(burst_allocation, self.max_burst_tokens)
            burst_allocation = min(burst_allocation, available_tokens)
            
            logger.debug(f"Burst allocation: base={base_allocation}, "
                        f"multiplied={burst_allocation}")
            
            return burst_allocation
        
        # Use normal allocation
        return self.base_strategy.allocate_tokens(
            available_tokens, priority_level, user_context
        )
    
    def get_allocation_percentage(self, priority_level: PriorityLevel) -> float:
        """Get the base allocation percentage for a priority level."""
        return self.base_strategy.get_allocation_percentage(priority_level)


@dataclass
class AllocationResult:
    """Result of token allocation operation."""
    allocated_tokens: int
    available_tokens: int
    priority_level: PriorityLevel
    strategy_used: str
    adjustment_factor: float = 1.0
    emergency_override: bool = False
    burst_mode: bool = False


class AllocationStrategyFactory:
    """Factory for creating allocation strategies."""
    
    @staticmethod
    def create_priority_based(high_percentage: float = 0.5, medium_percentage: float = 0.3,
                            low_percentage: float = 0.2) -> PriorityBasedAllocation:
        """Create a priority-based allocation strategy."""
        return PriorityBasedAllocation(high_percentage, medium_percentage, low_percentage)
    
    @staticmethod
    def create_dynamic_priority(base_strategy: Optional[AllocationStrategy] = None,
                              user_history_weight: float = 0.3,
                              system_load_weight: float = 0.2,
                              time_factor_weight: float = 0.1) -> DynamicPriorityAllocation:
        """Create a dynamic priority allocation strategy."""
        if base_strategy is None:
            base_strategy = AllocationStrategyFactory.create_priority_based()
        
        return DynamicPriorityAllocation(
            base_strategy, user_history_weight, system_load_weight, time_factor_weight
        )
    
    @staticmethod
    def create_emergency_override(base_strategy: Optional[AllocationStrategy] = None,
                                emergency_threshold: float = 0.95,
                                override_percentage: float = 0.8) -> EmergencyOverrideAllocation:
        """Create an emergency override allocation strategy."""
        if base_strategy is None:
            base_strategy = AllocationStrategyFactory.create_priority_based()
        
        return EmergencyOverrideAllocation(base_strategy, emergency_threshold, override_percentage)
    
    @staticmethod
    def create_burst_token(base_strategy: Optional[AllocationStrategy] = None,
                          burst_multiplier: float = 2.0,
                          burst_window_minutes: int = 15,
                          max_burst_tokens: int = 1000) -> BurstTokenAllocation:
        """Create a burst token allocation strategy."""
        if base_strategy is None:
            base_strategy = AllocationStrategyFactory.create_priority_based()
        
        return BurstTokenAllocation(
            base_strategy, burst_multiplier, burst_window_minutes, max_burst_tokens
        )
    
    @staticmethod
    def create_comprehensive_strategy() -> AllocationStrategy:
        """Create a comprehensive allocation strategy with all features."""
        # Start with priority-based
        base = AllocationStrategyFactory.create_priority_based()
        
        # Add dynamic adjustments
        dynamic = AllocationStrategyFactory.create_dynamic_priority(base)
        
        # Add emergency override
        emergency = AllocationStrategyFactory.create_emergency_override(dynamic)
        
        # Add burst capability
        burst = AllocationStrategyFactory.create_burst_token(emergency)
        
        return burst