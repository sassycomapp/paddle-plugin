# Token Management System - Administrator Guide

## Table of Contents
- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Installation and Setup](#installation-and-setup)
- [Configuration Management](#configuration-management)
- [User Management](#user-management)
- [Quota Management](#quota-management)
- [Monitoring and Alerting](#monitoring-and-alerting)
- [Security Management](#security-management)
- [Performance Optimization](#performance-optimization)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

## Overview

The Token Management System Administrator Guide provides comprehensive instructions for system administrators to manage, configure, and maintain the token management infrastructure. This guide covers installation, configuration, user management, monitoring, and advanced administrative tasks.

### Key Responsibilities

- **System Installation and Deployment**: Set up and configure the token management system
- **User and Quota Management**: Manage user accounts and token quotas
- **Monitoring and Alerting**: Monitor system health and configure alerts
- **Security Management**: Implement security measures and access controls
- **Performance Optimization**: Ensure optimal system performance
- **Backup and Recovery**: Implement backup strategies and recovery procedures

### Prerequisites

- **System Requirements**: 
  - PostgreSQL 12+ database
  - Python 3.8+ runtime
  - Redis for caching (optional)
  - 4GB+ RAM recommended
- **Administrative Access**: 
  - Database administrator privileges
  - System administrator access
  - API access for automation

## System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Token Management System                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   API Gateway   │  │   Web Interface  │  │   CLI Tools     │  │
│  │                 │  │                 │  │                 │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│           │                   │                   │              │
│           ▼                   ▼                   ▼              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Token Counter   │  │ Token Budget    │  │ Token Tracking  │  │
│  │ (pg_tiktoken)   │  │ Manager         │  │ & Analytics     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│           │                   │                   │              │
│           ▼                   ▼                   ▼              │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    Database Layer                           │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  │ PostgreSQL      │  │ Redis Cache     │  │ Audit Logs      │  │
│  │  │ (Token Data)   │  │ (Session Data)  │  │ (Activity)      │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┐  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Request**: User makes API call or uses web interface
2. **Token Counting**: System counts tokens using pg_tiktoken
3. **Budget Check**: System verifies user has sufficient quota
4. **Processing**: Request processed if quota available
5. **Tracking**: Token usage recorded in database
6. **Analytics**: Usage data analyzed for reporting

## Installation and Setup

### Prerequisites Check

```bash
# Check system requirements
python --version  # Should be 3.8+
psql --version   # Should be 12+
redis-cli ping   # Should return PONG

# Check available disk space
df -h
```

### Database Setup

1. **Create Database**
```sql
-- Create token management database
CREATE DATABASE token_management;
CREATE USER token_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE token_management TO token_user;

-- Enable required extensions
\c token_management
CREATE EXTENSION IF NOT EXISTS pg_tiktoken;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

2. **Run Migrations**
```bash
# Apply database migrations
alembic upgrade head

# Verify schema
alembic current
```

### Application Installation

```bash
# Clone the repository
git clone https://github.com/your-org/token-management.git
cd token-management

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp config.example.json config.json
```

### Configuration Setup

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "token_management",
    "user": "token_user",
    "password": "secure_password"
  },
  "redis": {
    "host": "localhost",
    "port": 6379,
    "db": 0
  },
  "api": {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": false
  },
  "security": {
    "secret_key": "your-secret-key-here",
    "jwt_algorithm": "HS256",
    "token_expiry": 3600
  },
  "monitoring": {
    "enabled": true,
    "check_interval": 60,
    "alert_thresholds": {
      "cpu_usage": 80,
      "memory_usage": 85,
      "error_rate": 5.0
    }
  }
}
```

### Service Deployment

```bash
# Create systemd service
sudo tee /etc/systemd/system/token-management.service << EOF
[Unit]
Description=Token Management System
After=network.target postgresql.service

[Service]
Type=exec
User=token_user
WorkingDirectory=/opt/token-management
Environment=PATH=/opt/token-management/venv/bin
ExecStart=/opt/token-management/venv/bin/python -m uvicorn token_management.main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable token-management
sudo systemctl start token-management
```

## Configuration Management

### Environment Variables

```bash
# Database Configuration
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
export DATABASE_NAME=token_management
export DATABASE_USER=token_user
export DATABASE_PASSWORD=secure_password

# API Configuration
export API_HOST=0.0.0.0
export API_PORT=8000
export API_SECRET=your-secret-key

# Monitoring Configuration
export MONITORING_ENABLED=true
export MONITORING_INTERVAL=60
export LOG_LEVEL=INFO

# Security Configuration
export JWT_SECRET=your-jwt-secret
export TOKEN_EXPIRY=3600
```

### Configuration File Management

```bash
# Validate configuration
python -c "import json; print(json.load(open('config.json'))['database']['host'])"

# Backup configuration
cp config.json config.json.backup.$(date +%Y%m%d)

# Update configuration
python scripts/update_config.py --config config.json --set monitoring.alert_thresholds.cpu_usage=90
```

### Configuration Validation

```python
import json
from pathlib import Path

def validate_config(config_path):
    """Validate configuration file structure."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        required_sections = ['database', 'api', 'security']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required section: {section}")
        
        # Validate database configuration
        db_config = config['database']
        required_db_fields = ['host', 'port', 'name', 'user', 'password']
        for field in required_db_fields:
            if field not in db_config:
                raise ValueError(f"Missing database field: {field}")
        
        print("Configuration validation passed")
        return True
        
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        return False

# Usage
validate_config('config.json')
```

## User Management

### User Account Management

```python
from src.user_management import UserManager

# Initialize user manager
user_manager = UserManager()

# Create new user
user_data = {
    'username': 'john.doe',
    'email': 'john.doe@example.com',
    'full_name': 'John Doe',
    'department': 'Engineering',
    'role': 'user'
}

user = user_manager.create_user(user_data)
print(f"Created user: {user.user_id}")

# Update user information
update_data = {
    'full_name': 'Johnathan Doe',
    'department': 'Product'
}
user_manager.update_user(user.user_id, update_data)

# Deactivate user
user_manager.deactivate_user(user.user_id)
```

### Bulk User Operations

```python
# Import users from CSV
import csv

def bulk_import_users(csv_file_path):
    """Import users from CSV file."""
    user_manager = UserManager()
    
    with open(csv_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                user_manager.create_user(row)
                print(f"Imported user: {row['username']}")
            except Exception as e:
                print(f"Failed to import {row['username']}: {e}")

# Usage
bulk_import_users('users.csv')
```

### User Role Management

```python
# Define user roles
USER_ROLES = {
    'admin': {
        'permissions': [
            'manage_users',
            'manage_quotas',
            'view_system_metrics',
            'manage_configuration'
        ]
    },
    'manager': {
        'permissions': [
            'manage_team_users',
            'view_team_metrics',
            'adjust_team_quotas'
        ]
    },
    'user': {
        'permissions': [
            'view_usage',
            'request_quota_increase'
        ]
    }
}

# Assign role to user
user_manager.assign_role(user.user_id, 'manager')

# Check user permissions
if user_manager.has_permission(user.user_id, 'manage_team_users'):
    print("User can manage team users")
```

## Quota Management

### Quota Configuration

```python
from src.quota_management import QuotaManager

# Initialize quota manager
quota_manager = QuotaManager()

# Set user quotas
quota_config = {
    'daily_limit': 10000,
    'monthly_limit': 300000,
    'hard_limit': 1000000,
    'warning_threshold': 0.8,
    'critical_threshold': 0.95
}

quota_manager.set_user_quota('john.doe', quota_config)

# Set team quotas
team_quota_config = {
    'daily_limit': 50000,
    'monthly_limit': 1500000,
    'member_count': 10
}

quota_manager.set_team_quota('engineering-team', team_quota_config)
```

### Quota Templates

```python
# Define quota templates
QUOTA_TEMPLATES = {
    'basic_user': {
        'daily_limit': 5000,
        'monthly_limit': 150000,
        'hard_limit': 500000,
        'warning_threshold': 0.8,
        'critical_threshold': 0.95
    },
    'power_user': {
        'daily_limit': 20000,
        'monthly_limit': 600000,
        'hard_limit': 2000000,
        'warning_threshold': 0.85,
        'critical_threshold': 0.95
    },
    'enterprise': {
        'daily_limit': 100000,
        'monthly_limit': 3000000,
        'hard_limit': 10000000,
        'warning_threshold': 0.9,
        'critical_threshold': 0.98
    }
}

# Apply template to user
quota_manager.apply_template('john.doe', 'power_user')
```

### Quota Monitoring and Alerts

```python
# Monitor quota usage
def monitor_quota_usage():
    """Monitor quota usage across all users."""
    quota_manager = QuotaManager()
    
    # Get all users approaching limits
    warning_users = quota_manager.get_users_at_threshold('warning')
    critical_users = quota_manager.get_users_at_threshold('critical')
    
    # Send alerts
    for user in warning_users:
        quota_manager.send_alert(
            user_id=user['user_id'],
            message=f"Warning: You've used {user['usage_percentage']}% of your daily quota",
            severity='warning'
        )
    
    for user in critical_users:
        quota_manager.send_alert(
            user_id=user['user_id'],
            message=f"CRITICAL: You've used {user['usage_percentage']}% of your daily quota",
            severity='critical'
        )

# Schedule monitoring
import schedule
import time

schedule.every().hour.do(monitor_quota_usage)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Monitoring and Alerting

### System Monitoring

```python
from src.monitoring import TokenMonitoringSystem

# Initialize monitoring system
monitoring = TokenMonitoringSystem()

# Get system health
health = monitoring.get_system_health()
print(f"CPU Usage: {health.cpu_usage}%")
print(f"Memory Usage: {health.memory_usage}%")
print(f"Active Users: {health.active_users}")

# Get token usage metrics
usage_metrics = monitoring.get_token_usage_status()
print(f"Total Tokens Today: {usage_metrics.total_tokens}")
print(f"Average Tokens per Request: {usage_metrics.average_tokens_per_request}")
```

### Alert Configuration

```python
from src.alerting import AlertingConfig, AlertSeverity

# Configure alerting
alert_config = AlertingConfig(
    enabled=True,
    check_interval=60,
    thresholds={
        'cpu_usage': 80,
        'memory_usage': 85,
        'error_rate': 5.0,
        'response_time': 2.0,
        'quota_usage': 90
    }
)

# Setup notification channels
alerting = TokenAlertingSystem()
alerting.configure(alert_config)

# Add notification channels
alerting.add_notification_channel('console')
alerting.add_notification_channel('email', {
    'smtp_server': 'smtp.example.com',
    'smtp_port': 587,
    'username': 'alerts@example.com',
    'password': 'password',
    'recipients': ['admin@example.com']
})
alerting.add_notification_channel('slack', {
    'webhook_url': 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
})
```

### Performance Monitoring

```python
# Monitor performance metrics
def monitor_performance():
    """Monitor system performance metrics."""
    monitoring = TokenMonitoringSystem()
    
    # Get performance metrics
    metrics = monitoring.get_performance_metrics()
    
    # Log performance data
    print(f"Average Response Time: {metrics['average_response_time']:.3f}s")
    print(f"Total Requests: {metrics['total_requests']}")
    print(f"Success Rate: {metrics['success_rate']:.1%}")
    
    # Check for performance issues
    if metrics['average_response_time'] > 1.0:
        print("WARNING: High response time detected")
    
    if metrics['success_rate'] < 0.95:
        print("WARNING: Low success rate detected")

# Schedule performance monitoring
schedule.every(5).minutes.do(monitor_performance)
```

## Security Management

### Authentication and Authorization

```python
from src.security import AuthManager, Permission

# Initialize authentication manager
auth_manager = AuthManager()

# Create admin user
admin_user = auth_manager.create_user(
    username='admin',
    email='admin@example.com',
    password='secure_password',
    role='admin'
)

# Assign permissions
auth_manager.assign_permission(
    user_id=admin_user.user_id,
    permission=Permission.MANAGE_USERS
)

# Verify permissions
if auth_manager.has_permission(admin_user.user_id, Permission.MANAGE_USERS):
    print("Admin has user management permissions")
```

### API Security

```python
# Configure API security
API_SECURITY_CONFIG = {
    'rate_limiting': {
        'requests_per_minute': 100,
        'burst_limit': 200
    },
    'authentication': {
        'jwt_expiry': 3600,
        'refresh_token_expiry': 86400
    },
    'cors': {
        'allowed_origins': ['https://yourapp.com'],
        'allowed_methods': ['GET', 'POST', 'PUT', 'DELETE'],
        'allowed_headers': ['Content-Type', 'Authorization']
    }
}

# Apply security configuration
auth_manager.configure_api_security(API_SECURITY_CONFIG)
```

### Audit Logging

```python
from src.audit import AuditLogger

# Initialize audit logger
audit_logger = AuditLogger()

# Log administrative actions
def log_admin_action(user_id, action, details):
    """Log administrative actions for audit purposes."""
    audit_logger.log_event(
        user_id=user_id,
        action=action,
        details=details,
        severity='info'
    )

# Example usage
log_admin_action(
    user_id='admin_user',
    action='create_user',
    details={'username': 'john.doe', 'email': 'john.doe@example.com'}
)
```

## Performance Optimization

### Database Optimization

```python
# Optimize database queries
def optimize_database():
    """Optimize database performance."""
    from src.database import Database
    
    db = Database()
    
    # Create indexes for frequently queried columns
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_token_usage_user_id 
        ON token_usage(user_id);
    """)
    
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_token_usage_timestamp 
        ON token_usage(timestamp);
    """)
    
    # Analyze tables for better query planning
    db.execute("ANALYZE token_usage;")
    db.execute("ANALYZE user_quotas;")

# Run optimization
optimize_database()
```

### Caching Strategy

```python
# Configure Redis caching
import redis
from src.cache import CacheManager

# Initialize Redis client
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

# Setup cache manager
cache_manager = CacheManager(redis_client)

# Configure cache strategies
CACHE_CONFIG = {
    'user_sessions': {
        'ttl': 3600,  # 1 hour
        'max_size': 10000
    },
    'token_counts': {
        'ttl': 300,   # 5 minutes
        'max_size': 50000
    },
    'quota_cache': {
        'ttl': 60,    # 1 minute
        'max_size': 1000
    }
}

cache_manager.configure(CACHE_CONFIG)
```

### Load Balancing

```python
# Configure load balancing
LOAD_BALANCER_CONFIG = {
    'strategy': 'round_robin',
    'servers': [
        {'host': 'api1.example.com', 'port': 8000, 'weight': 1},
        {'host': 'api2.example.com', 'port': 8000, 'weight': 1},
        {'host': 'api3.example.com', 'port': 8000, 'weight': 2}
    ],
    'health_check': {
        'interval': 30,
        'timeout': 5,
        'path': '/health'
    }
}

# Apply load balancer configuration
from src.load_balancer import LoadBalancer
load_balancer = LoadBalancer(LOAD_BALANCER_CONFIG)
load_balancer.start()
```

## Backup and Recovery

### Database Backup

```bash
# Create daily database backup
backup_script="""
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/token_management"
DB_NAME="token_management"
DB_USER="token_user"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
pg_dump -U $DB_USER -h localhost $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/backup_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/backup_$DATE.sql.gz"
"""

# Save backup script
echo "$backup_script" > /usr/local/bin/backup_token_management.sh
chmod +x /usr/local/bin/backup_token_management.sh

# Schedule daily backup
echo "0 2 * * * /usr/local/bin/backup_token_management.sh" | sudo crontab -
```

### Configuration Backup

```python
import shutil
from datetime import datetime

def backup_configuration():
    """Backup configuration files."""
    config_dir = '/opt/token-management/config'
    backup_dir = f'/var/backups/token_management/config_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    # Create backup
    shutil.copytree(config_dir, backup_dir)
    
    # Keep only last 5 backups
    backups = sorted([
        d for d in '/var/backups/token_management'.iterdir() 
        if d.is_dir() and d.name.startswith('config_')
    ], reverse=True)
    
    for backup in backups[5:]:
        shutil.rmtree(backup)
    
    print(f"Configuration backup completed: {backup_dir}")

# Run backup
backup_configuration()
```

### Disaster Recovery Plan

```python
# Disaster recovery procedures
def disaster_recovery():
    """Execute disaster recovery procedures."""
    print("Starting disaster recovery...")
    
    # Step 1: Stop services
    print("Stopping services...")
    subprocess.run(['systemctl', 'stop', 'token-management'])
    
    # Step 2: Restore from backup
    print("Restoring from backup...")
    subprocess.run([
        'pg_restore', '-U', 'token_user', '-d', 'token_management',
        '/var/backups/token_management/latest_backup.dump'
    ])
    
    # Step 3: Restart services
    print("Restarting services...")
    subprocess.run(['systemctl', 'start', 'token-management'])
    
    # Step 4: Verify system health
    print("Verifying system health...")
    monitoring = TokenMonitoringSystem()
    health = monitoring.get_system_health()
    
    if health.cpu_usage < 90 and health.memory_usage < 90:
        print("Disaster recovery completed successfully")
    else:
        print("WARNING: System health issues detected after recovery")

# Test disaster recovery
disaster_recovery()
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: Database Connection Failed

**Problem**: System cannot connect to PostgreSQL database.

**Diagnosis**:
```bash
# Check database connectivity
psql -U token_user -h localhost -d token_management -c "SELECT 1;"

# Check database status
systemctl status postgresql
```

**Solution**:
```python
# Fix database connection
def fix_database_connection():
    """Fix database connection issues."""
    try:
        # Test connection
        db = Database()
        db.execute("SELECT 1;")
        print("Database connection successful")
    except Exception as e:
        print(f"Database connection failed: {e}")
        
        # Check configuration
        config = load_config()
        print(f"Database config: {config['database']}")
        
        # Verify database is running
        import subprocess
        result = subprocess.run(['systemctl', 'is-active', 'postgresql'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("PostgreSQL is not running")
            subprocess.run(['systemctl', 'start', 'postgresql'])
```

#### Issue: High Memory Usage

**Problem**: System memory usage is consistently high.

**Diagnosis**:
```bash
# Check memory usage
free -h
top -p $(pgrep -f token-management)

# Check database memory usage
psql -U token_user -d token_management -c "SELECT * FROM pg_stat_activity;"
```

**Solution**:
```python
# Optimize memory usage
def optimize_memory_usage():
    """Optimize system memory usage."""
    # Clear cache
    cache_manager.clear_all()
    
    # Optimize database queries
    db = Database()
    db.execute("VACUUM ANALYZE token_usage;")
    
    # Restart services
    subprocess.run(['systemctl', 'restart', 'token-management'])
    
    # Monitor improvement
    import time
    time.sleep(60)
    monitoring = TokenMonitoringSystem()
    health = monitoring.get_system_health()
    print(f"Memory usage after optimization: {health.memory_usage}%")
```

#### Issue: Token Counting Inaccuracies

**Problem**: Token counts don't match expected values.

**Diagnosis**:
```bash
# Check pg_tiktoken extension
psql -U token_user -d token_management -c "SELECT * FROM pg_extension WHERE extname = 'pg_tiktoken';"

# Test token counting
python -c "
from src.token_counter import TokenCounter
counter = TokenCounter()
text = 'Hello, world!'
print(f'Token count: {counter.count_tokens(text)}')
"
```

**Solution**:
```python
# Fix token counting issues
def fix_token_counting():
    """Fix token counting inaccuracies."""
    # Verify pg_tiktoken extension
    db = Database()
    result = db.execute("SELECT * FROM pg_extension WHERE extname = 'pg_tiktoken';")
    
    if not result:
        print("Installing pg_tiktoken extension...")
        db.execute("CREATE EXTENSION IF NOT EXISTS pg_tiktoken;")
    
    # Test token counting
    from src.token_counter import TokenCounter
    counter = TokenCounter()
    
    # Test with known text
    test_text = "This is a test sentence for token counting."
    tokens = counter.count_tokens(test_text)
    print(f"Test token count: {tokens}")
    
    # Verify accuracy
    if tokens < 5 or tokens > 20:
        print("WARNING: Token count seems unusual")
```

### Debug Mode

```python
# Enable debug logging
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/token_management/debug.log'),
        logging.StreamHandler()
    ]
)

# Enable debug mode for specific components
from src.config import Config
Config.set('debug', True)
Config.set('debug_database', True)
Config.set('debug_api', True)
```

### Performance Analysis

```python
# Analyze system performance
def analyze_performance():
    """Analyze system performance and identify bottlenecks."""
    import time
    import psutil
    
    # Monitor system resources
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_percent = psutil.virtual_memory().percent
    disk_percent = psutil.disk_usage('/').percent
    
    print(f"CPU Usage: {cpu_percent}%")
    print(f"Memory Usage: {memory_percent}%")
    print(f"Disk Usage: {disk_percent}%")
    
    # Analyze database performance
    db = Database()
    slow_queries = db.execute("""
        SELECT query, mean_time, calls 
        FROM pg_stat_statements 
        WHERE mean_time > 100 
        ORDER BY mean_time DESC 
        LIMIT 10;
    """)
    
    if slow_queries:
        print("Slow queries detected:")
        for query in slow_queries:
            print(f"Query: {query['query']}")
            print(f"Mean time: {query['mean_time']}ms")
            print(f"Calls: {query['calls']}")
    
    # Generate performance report
    performance_report = {
        'timestamp': datetime.now().isoformat(),
        'cpu_usage': cpu_percent,
        'memory_usage': memory_percent,
        'disk_usage': disk_percent,
        'slow_queries': slow_queries
    }
    
    # Save report
    import json
    with open('/var/log/token_management/performance_report.json', 'w') as f:
        json.dump(performance_report, f, indent=2)
    
    return performance_report
```

## Maintenance

### Regular Maintenance Tasks

```bash
#!/bin/bash
# maintenance_script.sh

# Daily maintenance
echo "Starting daily maintenance..."
DATE=$(date +%Y%m%d)

# Clean up old logs
find /var/log/token_management -name "*.log" -mtime +7 -delete

# Rotate logs
logrotate -f /etc/logrotate.d/token-management

# Check disk space
df -h | grep -E "Filesystem|/var"

# Weekly maintenance
if [ "$(date +%u)" -eq 1 ]; then
    echo "Starting weekly maintenance..."
    
    # Update system packages
    apt update && apt upgrade -y
    
    # Optimize database
    psql -U token_user -d token_management -c "VACUUM ANALYZE;"
    
    # Generate weekly report
    python scripts/generate_weekly_report.py
fi

# Monthly maintenance
if [ "$(date +%d)" -eq 1 ]; then
    echo "Starting monthly maintenance..."
    
    # Generate monthly report
    python scripts/generate_monthly_report.py
    
    # Archive old data
    python scripts/archive_old_data.py
    
    # Update system documentation
    python scripts/update_documentation.py
fi

echo "Maintenance completed"
```

### System Health Checks

```python
def system_health_check():
    """Perform comprehensive system health check."""
    health_status = {
        'timestamp': datetime.now().isoformat(),
        'overall_status': 'healthy',
        'components': {}
    }
    
    # Check database
    try:
        db = Database()
        db.execute("SELECT 1;")
        health_status['components']['database'] = 'healthy'
    except Exception as e:
        health_status['components']['database'] = f'unhealthy: {e}'
        health_status['overall_status'] = 'degraded'
    
    # Check Redis
    try:
        redis_client = redis.Redis(host='localhost', port=6379)
        redis_client.ping()
        health_status['components']['redis'] = 'healthy'
    except Exception as e:
        health_status['components']['redis'] = f'unhealthy: {e}'
        health_status['overall_status'] = 'degraded'
    
    # Check API services
    try:
        import requests
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            health_status['components']['api'] = 'healthy'
        else:
            health_status['components']['api'] = f'unhealthy: HTTP {response.status_code}'
            health_status['overall_status'] = 'degraded'
    except Exception as e:
        health_status['components']['api'] = f'unhealthy: {e}'
        health_status['overall_status'] = 'degraded'
    
    # Check disk space
    import shutil
    total, used, free = shutil.disk_usage('/var')
    free_percent = (free / total) * 100
    if free_percent < 10:
        health_status['components']['disk_space'] = f'critical: {free_percent:.1f}% free'
        health_status['overall_status'] = 'critical'
    elif free_percent < 20:
        health_status['components']['disk_space'] = f'warning: {free_percent:.1f}% free'
        health_status['overall_status'] = 'degraded'
    else:
        health_status['components']['disk_space'] = f'healthy: {free_percent:.1f}% free'
    
    # Log health status
    print(f"System health: {health_status['overall_status']}")
    for component, status in health_status['components'].items():
        print(f"  {component}: {status}")
    
    return health_status

# Schedule health checks
schedule.every(5).minutes.do(system_health_check)
```

### Automated Maintenance Scripts

```python
# Automated maintenance script
def automated_maintenance():
    """Run automated maintenance tasks."""
    print("Starting automated maintenance...")
    
    # Clean up old sessions
    from src.session_manager import SessionManager
    session_manager = SessionManager()
    session_manager.cleanup_expired_sessions()
    
    # Optimize database
    db = Database()
    db.execute("VACUUM ANALYZE token_usage;")
    db.execute("VACUUM ANALYZE user_quotas;")
    
    # Update statistics
    db.execute("ANALYZE token_usage;")
    db.execute("ANALYZE user_quotas;")
    
    # Clean up cache
    cache_manager.clear_expired()
    
    # Generate maintenance report
    maintenance_report = {
        'timestamp': datetime.now().isoformat(),
        'tasks_completed': [
            'session_cleanup',
            'database_optimization',
            'statistics_update',
            'cache_cleanup'
        ],
        'system_health': system_health_check()
    }
    
    # Save report
    import json
    with open('/var/log/token_management/maintenance_report.json', 'w') as f:
        json.dump(maintenance_report, f, indent=2)
    
    print("Automated maintenance completed")

# Schedule automated maintenance
schedule.every().day.at("02:00").do(automated_maintenance)
```

### Version Management

```python
# Version management utilities
def check_for_updates():
    """Check for system updates."""
    import subprocess
    
    try:
        # Check for package updates
        result = subprocess.run(['apt', 'list', '--upgradable'], 
                              capture_output=True, text=True)
        
        if result.stdout:
            print("Available updates:")
            print(result.stdout)
            
            # Schedule update
            schedule.every().sunday.at("03:00").do(update_system)
        else:
            print("System is up to date")
            
    except Exception as e:
        print(f"Error checking for updates: {e}")

def update_system():
    """Update system packages."""
    print("Starting system update...")
    
    try:
        # Update packages
        subprocess.run(['apt', 'update'], check=True)
        subprocess.run(['apt', 'upgrade', '-y'], check=True)
        
        # Restart services if needed
        subprocess.run(['systemctl', 'restart', 'token-management'])
        
        print("System update completed")
        
    except Exception as e:
        print(f"Error during system update: {e}")
        # Send alert
        from src.alerting import TokenAlertingSystem
        alerting = TokenAlertingSystem()
        alerting.send_alert(
            user_id='admin',
            message=f"System update failed: {e}",
            severity='critical'
        )

# Schedule update checks
schedule.every().day.at("01:00").do(check_for_updates)
```

---

*This Administrator Guide provides comprehensive instructions for managing the Token Management System. For additional support, please refer to the other documentation guides or contact the system administrator team.*