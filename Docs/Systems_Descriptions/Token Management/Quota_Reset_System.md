# Quota Reset System

## Overview

The Quota Reset System provides an automated mechanism for resetting token usage counters at regular intervals. This system ensures that users' token quotas are properly reset according to their configured periods, maintaining fair usage and preventing quota exhaustion.

## Architecture

### Core Components

1. **QuotaResetScheduler** - Main scheduling system
2. **QuotaResetCronManager** - OS-level cron job integration
3. **PostgreSQL Functions** - Database-level operations
4. **Standalone Script** - Command-line interface

### Data Flow

```
User Request → QuotaResetScheduler → PostgreSQL Functions → Token Limits Table
     ↓
QuotaResetCronManager → OS Cron Jobs → Standalone Script
     ↓
Monitoring & Alerting → Health Checks → Performance Metrics
```

## Database Schema

### Quota Reset Tables

#### `quota_reset_schedules`
Stores scheduled quota reset operations.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| user_id | TEXT | User ID (NULL for all users) |
| reset_type | TEXT | Reset period type |
| reset_interval | INTERVAL | Reset interval |
| reset_time | TEXT | Time of day for resets |
| is_active | BOOLEAN | Whether schedule is active |
| metadata | JSONB | Additional metadata |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |
| last_reset | TIMESTAMP | Last reset time |
| next_reset | TIMESTAMP | Next scheduled reset |

#### `quota_reset_operations`
Tracks individual quota reset operations.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| schedule_id | INTEGER | Reference to schedule |
| user_id | TEXT | User ID (NULL for all users) |
| reset_type | TEXT | Reset period type |
| reset_start | TIMESTAMP | Reset start time |
| reset_end | TIMESTAMP | Reset end time |
| tokens_reset | INTEGER | Number of tokens reset |
| users_affected | INTEGER | Number of users affected |
| status | TEXT | Operation status |
| error_message | TEXT | Error details |
| execution_time | FLOAT | Execution duration |
| created_at | TIMESTAMP | Creation timestamp |

#### `quota_reset_history`
Historical record of all quota reset operations.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| schedule_id | INTEGER | Reference to schedule |
| user_id | TEXT | User ID (NULL for all users) |
| reset_type | TEXT | Reset period type |
| reset_start | TIMESTAMP | Reset start time |
| reset_end | TIMESTAMP | Reset end time |
| tokens_reset | INTEGER | Number of tokens reset |
| users_affected | INTEGER | Number of users affected |
| status | TEXT | Operation status |
| error_message | TEXT | Error details |
| execution_time | FLOAT | Execution duration |
| created_at | TIMESTAMP | Creation timestamp |

#### `quota_reset_cron_history`
Tracks cron job execution history.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| job_name | TEXT | Cron job name |
| success | BOOLEAN | Whether job succeeded |
| return_code | INTEGER | Process return code |
| stdout | TEXT | Standard output |
| stderr | TEXT | Standard error |
| execution_time | FLOAT | Execution duration |
| attempt | INTEGER | Attempt number |
| created_at | TIMESTAMP | Creation timestamp |

## Core Functionality

### Scheduling Mechanisms

#### 1. PostgreSQL pg_cron Integration
- Uses database-level scheduling for precise timing
- Supports complex scheduling patterns
- Provides transactional consistency

#### 2. OS Cron Job Integration
- System-level scheduling for reliability
- Fallback mechanism when database scheduling fails
- Integration with system monitoring tools

#### 3. Event-Driven Scheduling
- Custom triggers for specific events
- Integration with application events
- Dynamic scheduling adjustments

### Reset Period Types

| Period Type | Description | Example Interval |
|-------------|-------------|------------------|
| DAILY | Reset every day | "1 day" |
| WEEKLY | Reset every week | "7 days" |
| MONTHLY | Reset every month | "30 days" |
| CUSTOM | Custom interval | "2 hours", "15 minutes" |

### Core Functions

#### `schedule_quota_reset()`
```python
def schedule_quota_reset(
    user_id: Optional[str] = None,
    reset_type: ResetPeriod = ResetPeriod.DAILY,
    reset_interval: str = "1 day",
    reset_time: str = "00:00:00",
    metadata: Optional[Dict[str, Any]] = None
) -> int
```

Schedules a quota reset operation.

#### `execute_quota_reset()`
```python
def execute_quota_reset(
    schedule_id: int,
    user_id: Optional[str] = None,
    reset_start: Optional[datetime] = None,
    reset_end: Optional[datetime] = None
) -> QuotaResetOperation
```

Executes a quota reset operation.

#### `get_pending_resets()`
```python
def get_pending_resets(limit: int = 10) -> List[Dict[str, Any]]
```

Gets pending quota reset schedules.

#### `cancel_scheduled_reset()`
```python
def cancel_scheduled_reset(schedule_id: int) -> bool
```

Cancels a scheduled reset operation.

#### `get_reset_history()`
```python
def get_reset_history(
    user_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100
) -> List[Dict[str, Any]]
```

Gets quota reset operation history.

#### `validate_reset_configuration()`
```python
def validate_reset_configuration(
    reset_type: ResetPeriod,
    reset_interval: str,
    reset_time: str
) -> bool
```

Validates reset configuration parameters.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| QUOTA_RESET_ENABLED | Enable/disable quota reset system | "true" |
| QUOTA_RESET_LOG_LEVEL | Logging level | "INFO" |
| QUOTA_RESET_MONITOR_INTERVAL | Monitoring interval (seconds) | 60 |
| QUOTA_RESET_MAX_RETRIES | Maximum retry attempts | 3 |
| QUOTA_RESET_RETRY_DELAY | Retry delay (seconds) | 60 |

### Configuration File

```json
{
  "scheduler": {
    "monitor_interval": 60,
    "max_retries": 3,
    "retry_delay": 60,
    "batch_size": 1000
  },
  "cron_jobs": {
    "daily_reset": {
      "schedule": "0 0 * * *",
      "command": "python scripts/reset_quotas.py --reset --type daily",
      "enabled": true,
      "timeout": 300,
      "retry_count": 3,
      "retry_delay": 60
    },
    "weekly_reset": {
      "schedule": "0 0 * * 1",
      "command": "python scripts/reset_quotas.py --reset --type weekly",
      "enabled": true,
      "timeout": 300,
      "retry_count": 3,
      "retry_delay": 60
    },
    "monthly_reset": {
      "schedule": "0 0 1 * *",
      "command": "python scripts/reset_quotas.py --reset --type monthly",
      "enabled": true,
      "timeout": 300,
      "retry_count": 3,
      "retry_delay": 60
    },
    "monitor": {
      "schedule": "*/5 * * * *",
      "command": "python scripts/reset_quotas.py --monitor",
      "enabled": true,
      "timeout": 60,
      "retry_count": 1,
      "retry_delay": 30
    }
  }
}
```

## Usage Examples

### Basic Usage

```python
from src.quota_reset_scheduler import QuotaResetScheduler
from simba.simba.database.postgres import PostgresDB

# Initialize scheduler
db = PostgresDB()
scheduler = QuotaResetScheduler(db=db)

# Start scheduler
scheduler.start()

# Schedule daily reset
schedule_id = scheduler.schedule_quota_reset(
    reset_type="daily",
    reset_interval="1 day",
    reset_time="00:00:00"
)

# Execute reset
operation = scheduler.execute_quota_reset(schedule_id)

# Stop scheduler
scheduler.stop()
```

### Advanced Usage

```python
# Schedule custom reset
schedule_id = scheduler.schedule_quota_reset(
    user_id="user123",
    reset_type="custom",
    reset_interval="2 hours",
    reset_time="09:00:00",
    metadata={"priority": "high", "description": "Priority user reset"}
)

# Get pending resets
pending_resets = scheduler.get_pending_resets(limit=5)

# Get system health
health = scheduler.get_system_health()

# Get performance metrics
metrics = scheduler.get_performance_metrics()
```

### Command Line Interface

```bash
# Reset all users' quotas daily
python scripts/reset_quotas.py --reset --type daily

# Reset specific user's quotas
python scripts/reset_quotas.py --reset --user-id user123 --type daily

# Schedule a weekly reset
python scripts/reset_quotas.py --schedule --type weekly --interval "7 days" --time "02:00:00"

# List pending schedules
python scripts/reset_quotas.py --list-schedules --limit 10

# Cancel a schedule
python scripts/reset_quotas.py --cancel --schedule-id 123

# Show reset history
python scripts/reset_quotas.py --history --limit 50

# Show system health
python scripts/reset_quotas.py --health

# Monitor system
python scripts/reset_quotas.py --monitor --interval 60
```

## Monitoring and Alerting

### Health Checks

The system provides comprehensive health monitoring:

- **Scheduler Status**: Running/stopped status
- **Database Status**: Connection health
- **Active Operations**: Number of active operations
- **Pending Operations**: Number of pending operations
- **Performance Metrics**: Execution times, success rates

### Alerting

The system supports various alerting mechanisms:

1. **Email Alerts**: For critical failures
2. **Slack Integration**: For team notifications
3. **Custom Webhooks**: For integration with external systems
4. **Log Monitoring**: For operational insights

### Performance Metrics

| Metric | Description |
|--------|-------------|
| total_scheduled | Total number of scheduled operations |
| total_executed | Total number of executed operations |
| successful_resets | Number of successful resets |
| failed_resets | Number of failed resets |
| average_execution_time | Average execution time |
| last_execution_time | Last execution timestamp |

## Error Handling

### Error Types

1. **Configuration Errors**: Invalid reset parameters
2. **Database Errors**: Connection or query failures
3. **Concurrency Errors**: Race conditions in reset operations
4. **System Errors**: Resource unavailability

### Error Recovery

The system implements multiple recovery strategies:

1. **Retry Logic**: Automatic retry with exponential backoff
2. **Rollback Mechanisms**: Rollback failed operations
3. **Circuit Breakers**: Prevent cascading failures
4. **Graceful Degradation**: Continue operation with reduced functionality

### Logging

Comprehensive logging is provided:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quota_reset.log'),
        logging.StreamHandler()
    ]
)

# Log levels
logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning conditions")
logger.error("Error conditions")
logger.critical("Critical conditions")
```

## Security Considerations

### Access Control

1. **Authentication**: User authentication for API access
2. **Authorization**: Role-based access control
3. **Audit Logging**: Complete audit trail of all operations

### Data Protection

1. **Encryption**: Sensitive data encryption at rest and in transit
2. **Backup**: Regular backups of configuration and data
3. **Retention**: Configurable data retention policies

### Compliance

1. **GDPR**: Compliance with data protection regulations
2. **SOC2**: Security controls for service organizations
3. **HIPAA**: Healthcare data protection requirements

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "scripts/reset_quotas.py", "--daemon"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quota-reset-scheduler
spec:
  replicas: 1
  selector:
    matchLabels:
      app: quota-reset-scheduler
  template:
    metadata:
      labels:
        app: quota-reset-scheduler
    spec:
      containers:
      - name: scheduler
        image: quota-reset-scheduler:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### System Requirements

| Component | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| Memory | 4GB | 8GB |
| Storage | 50GB | 100GB |
| Network | 100Mbps | 1Gbps |

## Troubleshooting

### Common Issues

1. **Scheduler Not Starting**
   - Check database connection
   - Verify configuration file
   - Check log files for errors

2. **Reset Operations Failing**
   - Check database permissions
   - Verify token limits table exists
   - Check for concurrent operations

3. **Performance Issues**
   - Monitor database performance
   - Optimize query indexes
   - Adjust batch sizes

### Debug Mode

Enable debug mode for detailed troubleshooting:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)

# Or via environment variable
export QUOTA_RESET_LOG_LEVEL=DEBUG
```

### Health Check Endpoints

The system provides health check endpoints:

```bash
# Check system health
curl http://localhost:8080/health

# Check database health
curl http://localhost:8080/health/database

# Check scheduler health
curl http://localhost:8080/health/scheduler
```

## Best Practices

### 1. Configuration Management

- Use environment variables for sensitive data
- Store configuration in version control
- Implement configuration validation
- Use configuration templates for different environments

### 2. Monitoring

- Set up comprehensive logging
- Implement alerting for critical events
- Monitor performance metrics
- Regular health checks

### 3. Security

- Implement proper authentication
- Use encryption for sensitive data
- Regular security audits
- Keep dependencies updated

### 4. Performance

- Optimize database queries
- Use appropriate batch sizes
- Implement caching where possible
- Monitor resource usage

### 5. Reliability

- Implement retry logic
- Use circuit breakers
- Plan for failover scenarios
- Regular backups

## Future Enhancements

### Planned Features

1. **Advanced Scheduling**: Complex scheduling patterns
2. **Machine Learning**: Predictive quota management
3. **Multi-tenant Support**: Enhanced tenant isolation
4. **API Gateway**: RESTful API for external integration
5. **Dashboard**: Web-based monitoring dashboard

### Integration Opportunities

1. **Monitoring Systems**: Prometheus, Grafana
2. **Logging Systems**: ELK Stack, Splunk
3. **Notification Systems**: Slack, Teams, Email
4. **CI/CD Pipelines**: Automated deployment and testing

## Support

For support and questions:

1. **Documentation**: Refer to this document and code comments
2. **Issue Tracking**: GitHub issues for bug reports
3. **Community**: Join our community forums
4. **Professional Support**: Contact for enterprise support

---

*This document provides a comprehensive overview of the Quota Reset System. For additional information, refer to the source code and implementation details.*