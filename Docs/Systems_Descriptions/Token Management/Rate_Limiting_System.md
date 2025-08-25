# Rate Limiting and Dynamic Token Allocation System

## Overview

The Rate Limiting and Dynamic Token Allocation System is a comprehensive solution for enforcing configurable rate limits and implementing priority-based token allocation. The system provides robust rate limiting with graceful degradation, concurrent request handling, and dynamic allocation strategies.

## Architecture

### Core Components

1. **RateLimiter** - Main rate limiting and allocation logic
2. **Allocation Strategies** - Different token allocation strategies
3. **Lock Manager** - Concurrent request handling
4. **Database Integration** - PostgreSQL integration for persistent storage

### System Flow

```
Request → Rate Limit Check → Token Allocation → Usage Tracking → Response
    ↓            ↓              ↓            ↓
 Config    Priority Check   Strategy    Database
           Allocation      Selection   Update
```

## Features

### 1. Configurable Rate Limits
- **Per-user rate limits** with configurable windows
- **Per-API rate limits** for endpoint-specific restrictions
- **Multiple time windows**: minute, hour, day, week, custom
- **Burst traffic handling** with configurable burst limits
- **Graceful degradation** when limits are exceeded

### 2. Priority-Based Token Allocation
- **High Priority**: 50% of remaining quota
- **Medium Priority**: 30% of remaining quota
- **Low Priority**: 20% of remaining quota
- **Dynamic adjustments** based on user history and system load
- **Emergency override capabilities** for critical situations

### 3. Concurrent Request Handling
- **Thread-safe locking** mechanisms
- **Deadlock prevention** with timeout handling
- **Recursive locking** support
- **Emergency release** capabilities
- **Performance optimized** with in-memory tracking

### 4. Comprehensive Monitoring
- **Real-time metrics** tracking
- **Performance monitoring** with moving averages
- **Usage analytics** and reporting
- **Alerting** on quota exhaustion and abuse attempts

## Implementation Details

### RateLimiter Class

The `RateLimiter` class is the main entry point for the system:

```python
from token_management.rate_limiter import RateLimiter, RateLimitConfig, RateLimitWindow

# Initialize rate limiter
rate_limiter = RateLimiter()

# Configure rate limits
config = RateLimitConfig(
    max_requests_per_window=1000,
    window_duration=RateLimitWindow.HOUR,
    enable_dynamic_allocation=True,
    emergency_override_enabled=True,
    burst_mode_enabled=True
)

rate_limiter.set_user_rate_limit("user123", config)
```

### Allocation Strategies

#### Priority-Based Allocation
```python
from token_management.allocation_strategies import PriorityBasedAllocation

strategy = PriorityBasedAllocation(high_percentage=0.5, medium_percentage=0.3, low_percentage=0.2)
allocated_tokens = strategy.allocate_tokens(available_tokens, priority_level)
```

#### Dynamic Priority Allocation
```python
from token_management.allocation_strategies import DynamicPriorityAllocation

dynamic_strategy = DynamicPriorityAllocation(
    base_strategy=strategy,
    user_history_weight=0.3,
    system_load_weight=0.2,
    time_factor_weight=0.1
)
```

#### Emergency Override Allocation
```python
from token_management.allocation_strategies import EmergencyOverrideAllocation

emergency_strategy = EmergencyOverrideAllocation(
    base_strategy=strategy,
    emergency_threshold=0.95,
    override_percentage=0.8
)
```

#### Burst Token Allocation
```python
from token_management.allocation_strategies import BurstTokenAllocation

burst_strategy = BurstTokenAllocation(
    base_strategy=strategy,
    burst_multiplier=2.0,
    burst_window_minutes=15,
    max_burst_tokens=1000
)
```

### Token Allocation Request

```python
from token_management.rate_limiter import TokenAllocationRequest, PriorityLevel

request = TokenAllocationRequest(
    user_id="user123",
    tokens_requested=100,
    priority_level=PriorityLevel.HIGH,
    api_endpoint="chat/completions",
    session_id="session_abc",
    context={'emergency_override': True}  # Optional context
)

result = rate_limiter.check_and_allocate_tokens(request)
```

## Database Integration

### PostgreSQL Methods

The system integrates with PostgreSQL through the `PostgresDB` class:

```python
from simba.simba.database.postgres import PostgresDB

db = PostgresDB()

# Check rate limits
result = db.check_rate_limit("user123", "chat/completions")

# Enforce rate limits (raises exception if exceeded)
db.enforce_rate_limit("user123", "chat/completions")

# Get rate limit status
status = db.get_rate_limit_status("user123")

# Set rate limits
db.set_rate_limit("user123", max_tokens_per_period=1000, period_interval="1 day")

# Reset rate limits
db.reset_rate_limit("user123")

# Get usage history
history = db.get_rate_limit_history("user123", days=7)
```

### Database Schema

The system uses the following tables:

#### `token_usage`
- Logs tokens consumed per request
- Fields: `id`, `user_id`, `session_id`, `tokens_used`, `api_endpoint`, `priority_level`, `timestamp`

#### `token_limits`
- Stores per-user token quota and limits
- Fields: `id`, `user_id`, `max_tokens_per_period`, `period_interval`, `tokens_used_in_period`, `period_start`

#### `token_revocations`
- Optional table for revoked tokens
- Fields: `token`, `revoked_at`, `reason`

## Configuration

### Rate Limit Configuration

```python
@dataclass
class RateLimitConfig:
    max_requests_per_window: int
    window_duration: RateLimitWindow
    custom_window_seconds: Optional[int] = None
    burst_limit: Optional[int] = None
    burst_window_seconds: Optional[int] = None
    enable_dynamic_allocation: bool = True
    emergency_override_enabled: bool = True
    burst_mode_enabled: bool = True
```

### Priority Levels

```python
class PriorityLevel(Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
```

### Rate Limit Windows

```python
class RateLimitWindow(Enum):
    MINUTE = "1 minute"
    HOUR = "1 hour"
    DAY = "1 day"
    WEEK = "1 week"
    CUSTOM = "custom"
```

## Usage Examples

### Basic Rate Limiting

```python
from token_management.rate_limiter import RateLimiter, RateLimitConfig, RateLimitWindow

# Initialize rate limiter
rate_limiter = RateLimiter()

# Configure rate limits
config = RateLimitConfig(
    max_requests_per_window=100,
    window_duration=RateLimitWindow.HOUR
)
rate_limiter.set_user_rate_limit("user123", config)

# Check rate limits
try:
    result = rate_limiter.enforce_rate_limit("user123", "chat/completions")
    print(f"Request allowed: {result.allowed}")
except RateLimitExceededError as e:
    print(f"Request denied: {e}")
```

### Token Allocation

```python
from token_management.rate_limiter import TokenAllocationRequest, PriorityLevel

# Create allocation request
request = TokenAllocationRequest(
    user_id="user123",
    tokens_requested=50,
    priority_level=PriorityLevel.HIGH,
    api_endpoint="chat/completions",
    session_id="session_abc"
)

# Allocate tokens
result = rate_limiter.check_and_allocate_tokens(request)

if result.success:
    print(f"Allocated {result.tokens_allocated} tokens")
    print(f"Remaining tokens: {result.tokens_remaining}")
    print(f"Strategy used: {result.allocation_strategy}")
else:
    print(f"Allocation failed: {result.reason}")
```

### Emergency Override

```python
# Emergency allocation request
emergency_request = TokenAllocationRequest(
    user_id="user123",
    tokens_requested=1000,
    priority_level=PriorityLevel.HIGH,
    api_endpoint="chat/completions",
    session_id="session_abc",
    context={'emergency_override': True}
)

# Emergency allocation will bypass normal limits
result = rate_limiter.check_and_allocate_tokens(emergency_request)
```

### Burst Mode

```python
# Burst mode request
burst_request = TokenAllocationRequest(
    user_id="user123",
    tokens_requested=200,
    priority_level=PriorityLevel.HIGH,
    api_endpoint="chat/completions",
    session_id="session_abc",
    context={'burst_mode': True}
)

# Burst mode allows higher allocation
result = rate_limiter.check_and_allocate_tokens(burst_request)
```

## Performance Considerations

### In-Memory Tracking
- Uses in-memory tracking for performance
- Automatic cleanup of old tracking data
- Thread-safe with proper locking

### Database Optimization
- Efficient SQL queries with proper indexing
- Connection pooling for database access
- Batch operations for bulk updates

### Concurrency Handling
- Fine-grained locking per resource
- Timeout handling to prevent deadlocks
- Recursive locking support for nested operations

## Monitoring and Metrics

### Performance Metrics

```python
# Get performance metrics
metrics = rate_limiter.get_performance_metrics()

print(f"Total checks: {metrics['total_checks']}")
print(f"Allowed requests: {metrics['allowed_requests']}")
print(f"Denied requests: {metrics['denied_requests']}")
print(f"Average check time: {metrics['average_check_time']:.4f}s")
print(f"Emergency overrides: {metrics['emergency_overrides']}")
print(f"Burst allocations: {metrics['burst_allocations']}")
```

### Database Metrics

```python
# Get usage history
history = db.get_rate_limit_history("user123", days=7)

print(f"Total tokens used: {history['total_tokens']}")
print(f"Total requests: {history['total_requests']}")
print(f"Average tokens per request: {history['average_tokens_per_request']}")
print(f"Daily usage: {history['daily_usage']}")
print(f"Endpoint usage: {history['endpoint_usage']}")
```

## Error Handling

### Common Exceptions

```python
from token_management.rate_limiter import RateLimitExceededError
from token_management.lock_manager import LockTimeoutError

try:
    result = rate_limiter.enforce_rate_limit("user123", "chat/completions")
except RateLimitExceededError as e:
    # Handle rate limit exceeded
    print(f"Rate limit exceeded: {e}")
except LockTimeoutError as e:
    # Handle lock timeout
    print(f"Lock timeout: {e}")
except Exception as e:
    # Handle other errors
    print(f"Unexpected error: {e}")
```

### Graceful Degradation

The system provides graceful degradation when:
- Database connectivity issues occur
- Rate limit configuration is missing
- Lock acquisition fails

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/test_rate_limiter.py -v

# Run specific test class
python -m pytest tests/test_rate_limiter.py::TestRateLimiter -v

# Run with coverage
python -m pytest tests/test_rate_limiter.py --cov=src/token_management --cov-report=html
```

### Test Coverage

The test suite covers:
- Rate limit enforcement
- Token allocation strategies
- Concurrent request handling
- Error scenarios
- Integration with database
- Performance metrics

## Deployment

### Requirements

- Python 3.8+
- PostgreSQL 12+
- psycopg2-binary
- FastAPI (for HTTP integration)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
python src/database/migrations/002_create_token_management_tables.sql

# Initialize rate limiter
from token_management.rate_limiter import RateLimiter
rate_limiter = RateLimiter()
```

### Configuration

Configure rate limits through:
- Database initialization
- Runtime configuration
- Environment variables

## Best Practices

### 1. Rate Limit Configuration
- Set appropriate limits based on user tier
- Use different limits for different API endpoints
- Consider burst traffic patterns

### 2. Priority Management
- Use priority levels appropriately
- Monitor allocation effectiveness
- Adjust percentages based on usage patterns

### 3. Monitoring
- Set up alerts for quota exhaustion
- Monitor performance metrics
- Regular review of allocation strategies

### 4. Error Handling
- Implement proper error handling
- Provide meaningful error messages
- Log all allocation decisions

### 5. Performance Optimization
- Use in-memory tracking for performance
- Optimize database queries
- Monitor system load

## Troubleshooting

### Common Issues

1. **Rate limits not working**
   - Check configuration in database
   - Verify user has proper limits set
   - Check for database connectivity issues

2. **Token allocation not working**
   - Verify user has available quota
   - Check priority level configuration
   - Review allocation strategy settings

3. **Performance issues**
   - Monitor in-memory usage
   - Check database query performance
   - Review lock contention

4. **Concurrency issues**
   - Check lock timeout settings
   - Monitor thread contention
   - Review recursive locking usage

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.getLogger('token_management').setLevel(logging.DEBUG)
```

## Future Enhancements

1. **Machine Learning-based allocation**
2. **Real-time analytics dashboard**
3. **Advanced rate limiting algorithms**
4. **Integration with external monitoring systems**
5. **Automated limit adjustment based on usage patterns**

## Support

For support and questions:
- Review the documentation
- Check the test suite for usage examples
- Monitor system logs for error information
- Contact the development team for assistance