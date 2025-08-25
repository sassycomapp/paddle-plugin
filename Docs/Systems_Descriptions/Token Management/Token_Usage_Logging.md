# Token Usage Logging System

## Overview

The Token Usage Logging System provides comprehensive tracking and monitoring of token consumption across all API calls and agent interactions. This system enables accurate auditing, usage reporting, and cost analysis for the token management infrastructure.

## Architecture

### Core Components

1. **TokenUsageLogger** - Main logging interface with multiple strategies
2. **TokenUsageBatchProcessor** - High-performance batch processing
3. **TokenUsageAnalytics** - Analytics and reporting functions
4. **PostgreSQL Extensions** - Database methods for logging operations

### Data Flow

```
API Request → Token Counter → Logger → Batch Processor → Database → Analytics
```

## Features

### 1. Comprehensive Logging

- **Real-time Logging**: Immediate logging of token consumption
- **Batch Logging**: Efficient batch processing for high-throughput scenarios
- **Asynchronous Logging**: Non-blocking logging operations
- **Atomic Operations**: Database transactions ensure data integrity

### 2. Rich Metadata Capture

- User ID and session tracking
- API endpoint identification
- Priority level classification
- Timestamp precision
- Optional metadata attachment

### 3. Performance Optimization

- Connection pooling
- Batch processing
- Index optimization
- Caching for analytics
- Asynchronous operations

### 4. Analytics and Reporting

- Usage summaries and statistics
- Trend analysis
- Export capabilities (JSON, CSV)
- Customizable time ranges
- User and endpoint filtering

## Configuration

### Logging Configuration

```python
from src.token_usage_logger import LoggingConfig, LoggingStrategy

config = LoggingConfig(
    strategy=LoggingStrategy.BATCH,  # REALTIME, BATCH, ASYNC
    batch_size=100,                  # Records per batch
    batch_timeout=5.0,               # Seconds before forced batch
    enable_async=True,               # Enable async processing
    log_level="INFO"                 # Logging level
)
```

### Batch Processing Configuration

```python
from src.token_usage_batch_processor import BatchProcessorConfig

config = BatchProcessorConfig(
    batch_size=100,                  # Maximum batch size
    batch_timeout=5.0,               # Batch timeout in seconds
    max_queue_size=1000,             # Maximum queue size
    enable_compression=True,         # Enable batch compression
    enable_retry=True,               # Enable retry on failure
    max_retries=3                    # Maximum retry attempts
)
```

### Analytics Configuration

```python
from src.token_usage_analytics import AnalyticsConfig

config = AnalyticsConfig(
    default_granularity=AnalyticsGranularity.DAY,
    default_time_range=30,           # Days
    max_records=10000,               # Maximum records to process
    enable_trend_analysis=True,      # Enable trend detection
    enable_anomaly_detection=True,   # Enable anomaly detection
    enable_forecasting=False,        # Enable usage forecasting
    cache_results=True,              # Enable result caching
    cache_ttl=3600                   # Cache TTL in seconds
)
```

## Usage Examples

### Basic Logging

```python
from src.token_usage_logger import TokenUsageLogger, LoggingConfig
from simba.simba.database.postgres import PostgresDB

# Initialize logger
db = PostgresDB()
config = LoggingConfig(strategy=LoggingStrategy.REALTIME)
logger = TokenUsageLogger(db, config)

# Log token usage
success = logger.log_token_usage(
    user_id="user-123",
    session_id="session-456",
    tokens_used=150,
    api_endpoint="/chat/completions",
    priority_level="Medium"
)
```

### Batch Logging

```python
# Create multiple records
records = [
    {
        'user_id': 'user-1',
        'session_id': 'session-1',
        'tokens_used': 100,
        'api_endpoint': '/chat/completions',
        'priority_level': 'High'
    },
    {
        'user_id': 'user-2',
        'session_id': 'session-2',
        'tokens_used': 200,
        'api_endpoint': '/embeddings',
        'priority_level': 'Medium'
    }
]

# Log in batch
success = logger.log_token_usage_batch(records)
```

### Usage Analytics

```python
from src.token_usage_analytics import TokenUsageAnalytics

# Initialize analytics
analytics = TokenUsageAnalytics(db)

# Get usage history
history = analytics.get_token_usage_history(
    user_id='user-123',
    start_date=datetime.utcnow() - timedelta(days=7),
    end_date=datetime.utcnow()
)

# Get usage summary
summary = analytics.get_token_usage_summary(
    user_id='user-123',
    start_date=datetime.utcnow() - timedelta(days=30)
)

# Get trend analysis
trend = analytics.get_trend_analysis(
    user_id='user-123',
    start_date=datetime.utcnow() - timedelta(days=90)
)

# Export logs
json_export = analytics.export_token_usage_logs(
    format='json',
    start_date=datetime.utcnow() - timedelta(days=7)
)
```

### Batch Processing

```python
from src.token_usage_batch_processor import TokenUsageBatchProcessor

# Initialize batch processor
processor = TokenUsageBatchProcessor(db)

# Add records to batch
record = {
    'user_id': 'user-123',
    'session_id': 'session-456',
    'tokens_used': 150,
    'api_endpoint': '/chat/completions',
    'priority_level': 'Medium'
}

processor.add_record(record)

# Process batch
result = processor.process_batch()
print(f"Processed {result['records_processed']} records")
```

## Database Schema

### Token Usage Table

```sql
CREATE TABLE token_usage (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    tokens_used INT NOT NULL,
    api_endpoint TEXT NOT NULL,
    priority_level TEXT NOT NULL CHECK (priority_level IN ('Low', 'Medium', 'High')),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Performance Indexes

The system includes comprehensive indexes for optimal query performance:

- User and session filtering
- Time-based queries
- Analytics aggregations
- Export operations
- Trend analysis

## Error Handling

### Database Failures

- Automatic fallback to console logging
- Retry mechanisms for batch operations
- Transaction rollback on errors
- Detailed error logging

### Performance Monitoring

- Query performance tracking
- Batch processing metrics
- Cache hit/miss ratios
- Error rate monitoring

## Security Considerations

### Data Protection

- User data encryption at rest
- Secure database connections
- Access control on logging operations
- Audit trail for all modifications

### Privacy

- Configurable data retention
- PII handling policies
- Access logging and monitoring
- Data anonymization options

## Performance Optimization

### Database Optimization

- Connection pooling
- Index optimization
- Query optimization
- Partitioning strategies

### Application Optimization

- Asynchronous processing
- Batch operations
- Caching strategies
- Memory management

## Monitoring and Alerting

### Metrics Collection

- Token consumption rates
- API call frequencies
- Error rates
- Performance metrics

### Alerting

- Threshold-based alerts
- Anomaly detection
- System health monitoring
- Capacity planning

## Integration

### With Token Management System

- Seamless integration with existing token counter
- Compatible with rate limiting system
- Shared database schema
- Consistent error handling

### With External Systems

- Export capabilities for BI tools
- API endpoints for reporting
- Webhook support for real-time notifications
- Integration with monitoring systems

## Deployment

### Database Setup

1. Run migrations to create tables
2. Create performance indexes
3. Set up backup strategies
4. Configure monitoring

### Application Setup

1. Configure logging strategies
2. Set up batch processing
3. Configure analytics settings
4. Set up monitoring and alerting

### Scaling Considerations

- Horizontal scaling for batch processing
- Database read replicas for analytics
- Caching layer for performance
- Load balancing for high availability

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Check connection pool settings
   - Verify database credentials
   - Monitor connection health

2. **Performance Issues**
   - Check query execution plans
   - Monitor index usage
   - Optimize batch sizes

3. **Data Integrity Issues**
   - Verify transaction isolation
   - Check error handling
   - Monitor retry mechanisms

### Debug Tools

- Query logging
- Performance monitoring
- Error tracking
- Health check endpoints

## Future Enhancements

### Planned Features

- Machine learning-based anomaly detection
- Predictive usage forecasting
- Real-time dashboard integration
- Advanced reporting capabilities
- Multi-tenant optimization

### Scalability Improvements

- Sharding strategies
- Database partitioning
- Distributed batch processing
- Stream-based architecture

## Conclusion

The Token Usage Logging System provides a robust, scalable solution for tracking and analyzing token consumption across the platform. With comprehensive logging, powerful analytics, and optimized performance, it enables effective cost management and operational monitoring.

For support and questions, please refer to the project documentation or contact the development team.