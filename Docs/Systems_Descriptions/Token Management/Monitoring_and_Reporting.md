# Token Management System - Monitoring and Reporting

## Overview

The Token Management System provides comprehensive monitoring and reporting capabilities to track token usage, detect anomalies, generate insights, and maintain system health. This system ensures optimal resource utilization, cost control, and proactive issue detection.

## Architecture

### Core Components

1. **TokenMonitoringSystem** - Main monitoring engine
2. **TokenAlertingSystem** - Alerting and notification system
3. **TokenAnalytics** - Analytics and reporting engine
4. **TokenDashboard** - Interactive dashboard and CLI interface
5. **Monitoring Script** - Standalone monitoring service

### Data Flow

```
Token Usage → Monitoring System → Analytics Engine → Reports/Dashboards
     ↓
Alerting System → Notifications → Escalation
```

## Configuration

### Monitoring Configuration

```python
{
    "monitoring": {
        "check_interval": 60,  # seconds
        "alert_thresholds": {
            "cpu_usage": 80,
            "memory_usage": 85,
            "error_rate": 5.0,
            "response_time": 2.0,
            "quota_usage": 90
        }
    }
}
```

### Alerting Configuration

```python
{
    "alerting": {
        "enabled": true,
        "check_interval": 60,
        "channels": [
            {
                "type": "console",
                "enabled": true
            },
            {
                "type": "email",
                "enabled": false,
                "config": {
                    "smtp_server": "localhost",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "recipients": []
                }
            }
        ]
    }
}
```

### Analytics Configuration

```python
{
    "analytics": {
        "enabled": true,
        "forecast_horizon": 7,  # days
        "retention_days": 30,
        "cost_model": {
            "cost_per_token": 0.000002,
            "budget_threshold": 1000
        }
    }
}
```

## Usage

### Basic Monitoring

```python
from src.token_monitoring import TokenMonitoringSystem
from simba.simba.database.postgres import PostgresDB

# Initialize monitoring system
db = PostgresDB()
monitoring = TokenMonitoringSystem(db)

# Get token usage status
status = monitoring.get_token_usage_status('user123')
print(f"Tokens used: {status.total_tokens}")
print(f"Quota used: {status.quota_used_percentage}%")

# Get system health
health = monitoring.get_system_health()
print(f"CPU usage: {health.cpu_usage}%")
print(f"Memory usage: {health.memory_usage}%")
```

### Alerting Setup

```python
from src.token_alerting import TokenAlertingSystem, AlertingConfig

# Initialize alerting system
alerting = TokenAlertingSystem(db)

# Configure alerting
config = AlertingConfig(
    enabled=True,
    check_interval=60,
    thresholds={
        'cpu_usage': 80,
        'memory_usage': 85,
        'error_rate': 5.0
    }
)
alerting.configure(config)

# Add notification channels
alerting.add_notification_channel('console')
alerting.add_notification_channel('email', {
    'smtp_server': 'smtp.example.com',
    'smtp_port': 587,
    'username': 'alerts@example.com',
    'password': 'password',
    'recipients': ['admin@example.com']
})

# Check for alerts
alerts = alerting.get_active_alerts()
for alert in alerts:
    print(f"[{alert.severity.value}] {alert.message}")
```

### Analytics and Reporting

```python
from src.token_analytics import TokenAnalytics, ReportFormat

# Initialize analytics
analytics = TokenAnalytics(db)

# Generate usage report
report = analytics.generate_usage_report(
    user_id='user123',
    days=7,
    format=ReportFormat.JSON
)

print(f"Total tokens: {report.total_tokens}")
print(f"Average tokens per request: {report.average_tokens_per_request}")

# Generate forecast
forecast = analytics.generate_forecast(days=30)
print(f"Predicted usage: {forecast.predicted_tokens}")

# Get recommendations
recommendations = analytics.get_recommendations()
for rec in recommendations:
    print(f"[{rec.priority}] {rec.description}")
```

### Dashboard Interface

```python
from src.token_dashboard import TokenDashboard

# Initialize dashboard
dashboard = TokenDashboard(db)

# Setup widgets
dashboard.setup_default_widgets('user123')

# Start real-time dashboard
dashboard.start_real_time('user123')

# Generate report
report = dashboard.generate_report('user123', days=7)
print(report)
```

### CLI Usage

```bash
# Show token usage status
python -m src.token_dashboard status --user user123

# Start interactive dashboard
python -m src.token_dashboard dashboard --user user123 --real-time

# Generate report
python -m src.token_dashboard report --days 7 --format json

# List alerts
python -m src.token_dashboard alerts --list --active

# Show analytics
python -m src.token_dashboard analytics --forecast --days 30

# Show system health
python -m src.token_dashboard system --health
```

### Standalone Monitoring Script

```bash
# Run as continuous service
python scripts/monitor_token_usage.py --config config.json --service

# Run monitoring once
python scripts/monitor_token_usage.py --once

# Start dashboard
python scripts/monitor_token_usage.py --dashboard --real-time

# Generate report
python scripts/monitor_token_usage.py --report --days 7 --format json
```

## API Reference

### TokenMonitoringSystem

#### Methods

- `get_token_usage_status(user_id: str = None) -> TokenUsageStatus`
  - Get current token usage status for a user or all users
  - Returns TokenUsageStatus with usage metrics

- `get_system_health() -> SystemHealthMetrics`
  - Get current system health metrics
  - Returns SystemHealthMetrics with performance data

- `detect_anomalies(user_id: str = None) -> List[Anomaly]`
  - Detect anomalous token consumption patterns
  - Returns list of detected anomalies

- `send_alerts(user_id: str, message: str, severity: AlertSeverity) -> bool`
  - Send alerts for threshold violations
  - Returns True if alert was sent successfully

- `export_metrics() -> Dict[str, Any]`
  - Export metrics for external monitoring systems
  - Returns dictionary of system metrics

- `get_performance_metrics() -> Dict[str, Any]`
  - Get performance metrics for the monitoring system
  - Returns dictionary of performance data

### TokenAlertingSystem

#### Methods

- `configure(config: AlertingConfig) -> None`
  - Configure alerting system settings

- `add_alert(user_id: str, message: str, severity: AlertSeverity) -> bool`
  - Add a new alert
  - Returns True if alert was added successfully

- `get_active_alerts(user_id: str = None) -> List[Alert]`
  - Get active alerts for a user or all users
  - Returns list of active alerts

- `get_alert_history(user_id: str = None, days: int = 7) -> List[Alert]`
  - Get alert history for a time period
  - Returns list of historical alerts

- `acknowledge_alert(alert_id: str) -> bool`
  - Acknowledge an alert
  - Returns True if alert was acknowledged

- `resolve_alert(alert_id: str) -> bool`
  - Resolve an alert
  - Returns True if alert was resolved

- `get_alerting_metrics() -> Dict[str, Any]`
  - Get alerting system metrics
  - Returns dictionary of alerting metrics

### TokenAnalytics

#### Methods

- `generate_usage_report(user_id: str = None, days: int = 7, format: ReportFormat = ReportFormat.JSON) -> AnalyticsReport`
  - Generate comprehensive usage report
  - Returns AnalyticsReport with usage data and insights

- `generate_forecast(user_id: str = None, days: int = 7) -> ForecastData`
  - Generate usage forecast
  - Returns ForecastData with predicted usage

- `get_recommendations(user_id: str = None) -> List[Recommendation]`
  - Get optimization recommendations
  - Returns list of recommendations

- `export_metrics() -> Dict[str, Any]`
  - Export analytics metrics
  - Returns dictionary of analytics data

- `get_analytics_metrics() -> Dict[str, Any]`
  - Get analytics system metrics
  - Returns dictionary of performance metrics

### TokenDashboard

#### Methods

- `add_widget(widget: DashboardWidget) -> None`
  - Add a widget to the dashboard

- `remove_widget(title: str) -> None`
  - Remove a widget by title

- `clear_widgets() -> None`
  - Clear all widgets

- `setup_default_widgets(user_id: str = None) -> None`
  - Setup default dashboard widgets

- `render_dashboard() -> str`
  - Render the complete dashboard
  - Returns formatted dashboard output

- `start_real_time(user_id: str = None) -> None`
  - Start real-time dashboard updates

- `stop_real_time() -> None`
  - Stop real-time dashboard updates

- `generate_report(user_id: str = None, days: int = 7) -> str`
  - Generate a comprehensive report
  - Returns formatted report output

### TokenCLI

#### Methods

- `run(args: List[str] = None) -> None`
  - Run the CLI with given arguments

- `handle_status(args) -> None`
  - Handle status command

- `handle_dashboard(args) -> None`
  - Handle dashboard command

- `handle_report(args) -> None`
  - Handle report command

- `handle_alerts(args) -> None`
  - Handle alerts command

- `handle_analytics(args) -> None`
  - Handle analytics command

- `handle_system(args) -> None`
  - Handle system command

## Data Models

### TokenUsageStatus

```python
@dataclass
class TokenUsageStatus:
    user_id: Optional[str]
    period_start: datetime
    period_end: datetime
    total_tokens: int
    total_requests: int
    average_tokens_per_request: float
    quota_used_percentage: float
    quota_remaining: int
    top_endpoints: List[str]
```

### SystemHealthMetrics

```python
@dataclass
class SystemHealthMetrics:
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    error_rate: float
    average_response_time: float
    active_users: int
    total_requests: int
    timestamp: datetime
```

### Alert

```python
@dataclass
class Alert:
    alert_id: str
    user_id: str
    message: str
    severity: AlertSeverity
    timestamp: datetime
    resolved: bool
    acknowledged: bool
    metadata: Optional[Dict[str, Any]]
```

### AnalyticsReport

```python
@dataclass
class AnalyticsReport:
    report_id: str
    title: str
    generated_at: datetime
    time_period: Dict[str, datetime]
    summary: Dict[str, Any]
    usage_trends: List[UsageTrend]
    cost_analysis: Optional[CostAnalysis]
    forecast_data: Optional[ForecastData]
    format: ReportFormat
    recommendations: List[Recommendation]
    metadata: Optional[Dict[str, Any]]
```

## Alert Severity Levels

- **LOW**: Informational alerts, no immediate action required
- **MEDIUM**: Warning alerts, attention recommended
- **HIGH**: Critical alerts, immediate attention required
- **CRITICAL**: Emergency alerts, immediate action required

## Notification Channels

### Console
- Outputs alerts to console/stdout
- Suitable for development and testing

### Email
- Sends alerts via SMTP
- Requires SMTP server configuration
- Supports multiple recipients

### Webhook
- Sends alerts via HTTP POST
- Supports custom webhook URLs
- Includes alert metadata

### Slack
- Sends alerts to Slack channels
- Requires Slack webhook URL
- Supports formatted messages

## Report Formats

### JSON
- Machine-readable format
- Suitable for API integration
- Contains complete data structure

### CSV
- Tabular format
- Suitable for spreadsheet analysis
- Flat structure with columns

### HTML
- Web-friendly format
- Suitable for web dashboards
- Includes styling and formatting

### PDF
- Print-friendly format
- Suitable for reports and documentation
- Professional layout

## Performance Considerations

### Monitoring Overhead
- Monitoring checks should have minimal impact on system performance
- Use appropriate check intervals (60-300 seconds)
- Implement efficient data aggregation

### Database Optimization
- Use proper indexing on token_usage tables
- Implement data partitioning for large datasets
- Use connection pooling for database connections

### Memory Management
- Implement proper caching strategies
- Use efficient data structures
- Monitor memory usage of monitoring processes

## Security Considerations

### Data Privacy
- Token usage data may contain sensitive information
- Implement proper access controls
- Anonymize data when necessary

### Alert Security
- Alert notifications should be secure
- Use encrypted channels for sensitive alerts
- Implement proper authentication for alert endpoints

### Configuration Security
- Monitor configuration files
- Use secure storage for sensitive configuration
- Implement configuration validation

## Troubleshooting

### Common Issues

1. **High CPU Usage**
   - Increase monitoring check interval
   - Optimize database queries
   - Reduce monitoring scope

2. **Missing Alerts**
   - Check alert configuration
   - Verify notification channels
   - Test alert thresholds

3. **Slow Report Generation**
   - Optimize database queries
   - Use data aggregation
   - Implement caching

4. **Dashboard Not Updating**
   - Check real-time configuration
   - Verify database connectivity
   - Check widget configuration

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Monitoring

Monitor system performance:

```python
# Get performance metrics
metrics = monitoring.get_performance_metrics()
print(f"Average check time: {metrics['average_check_time']:.3f}s")
print(f"Total checks: {metrics['total_checks']}")
print(f"Success rate: {metrics['success_rate']:.1%}")
```

## Best Practices

### Monitoring Strategy
- Monitor key metrics regularly
- Set appropriate alert thresholds
- Implement alert escalation
- Monitor system health alongside usage

### Alert Management
- Prioritize alerts by severity
- Implement alert acknowledgment
- Track alert resolution times
- Analyze alert patterns

### Reporting
- Generate reports regularly
- Use appropriate report formats
- Include actionable insights
- Archive historical reports

### Performance
- Optimize database queries
- Use efficient data structures
- Implement proper caching
- Monitor system resources

## Integration

### External Monitoring Systems
- Prometheus integration
- Grafana dashboards
- ELK stack integration
- Custom monitoring APIs

### CI/CD Integration
- Include monitoring in deployment pipeline
- Test monitoring configurations
- Validate alert thresholds
- Monitor deployment health

### Third-party Services
- Cloud monitoring services
- Alert management platforms
- Analytics platforms
- Cost management tools

## Future Enhancements

### Planned Features
- Machine learning-based anomaly detection
- Advanced forecasting algorithms
- Multi-tenant support
- Real-time analytics
- Cost optimization recommendations

### Scalability Improvements
- Distributed monitoring
- Horizontal scaling
- Load balancing
- Database sharding

### User Experience
- Enhanced dashboard features
- Mobile app support
- Advanced reporting
- Custom alert templates

## Support

For issues and questions:
- Check the troubleshooting section
- Review the API documentation
- Enable debug logging
- Contact the development team

## Version History

### v1.0.0
- Initial release
- Basic monitoring and alerting
- CLI interface
- Standalone monitoring script

### v1.1.0
- Enhanced analytics
- Dashboard widgets
- Multiple report formats
- Improved performance

### v1.2.0
- Advanced alerting
- Forecasting capabilities
- Integration support
- Security improvements