# Token Management System - Developer Guide

## Table of Contents
- [Overview](#overview)
- [Getting Started](#getting-started)
- [Architecture Overview](#architecture-overview)
- [Core Components](#core-components)
- [API Integration](#api-integration)
- [Database Integration](#database-integration)
- [Token Counting](#token-counting)
- [Quota Management](#quota-management)
- [Monitoring and Analytics](#monitoring-and-analytics)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)

## Overview

The Token Management System Developer Guide provides comprehensive instructions for developers who want to integrate with, extend, or contribute to the token management infrastructure. This guide covers system architecture, API integration, database operations, and development best practices.

### Key Concepts

- **Token Counting**: Accurate counting of AI model tokens using pg_tiktoken
- **Quota Management**: Enforcing usage limits and preventing abuse
- **Real-time Monitoring**: Tracking usage patterns and system health
- **Integration Layer**: Seamless integration with MCP servers and external APIs
- **Analytics Engine**: Comprehensive usage analysis and reporting

### Development Environment Setup

```bash
# Clone the repository
git clone https://github.com/your-org/token-management.git
cd token-management

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
python -m pytest tests/
```

## Architecture Overview

### System Architecture

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

1. **Request Processing**: Incoming requests are validated and authenticated
2. **Token Counting**: System counts tokens using pg_tiktoken extension
3. **Quota Validation**: System checks if user has sufficient quota
4. **Request Execution**: Request processed if quota available
5. **Usage Tracking**: Token usage recorded in database
6. **Analytics Update**: Usage data analyzed for reporting

## Core Components

### Token Counter

```python
from src.token_counter import TokenCounter

# Initialize token counter
counter = TokenCounter()

# Count tokens in text
text = "Hello, world! This is a test sentence."
token_count = counter.count_tokens(text)
print(f"Token count: {token_count}")

# Count tokens for different models
gpt4_tokens = counter.count_tokens(text, model="gpt-4")
claude_tokens = counter.count_tokens(text, model="claude-3")
print(f"GPT-4 tokens: {gpt4_tokens}")
print(f"Claude tokens: {claude_tokens}")
```

### Quota Manager

```python
from src.quota_manager import QuotaManager

# Initialize quota manager
quota_manager = QuotaManager()

# Check user quota
user_id = "john.doe"
quota_info = quota_manager.get_user_quota(user_id)
print(f"Daily quota: {quota_info.daily_limit}")
print(f"Used today: {quota_info.daily_used}")
print(f"Remaining: {quota_info.daily_remaining}")

# Check if user has sufficient quota
if quota_manager.has_sufficient_quota(user_id, required_tokens=1000):
    print("User has sufficient quota")
else:
    print("Insufficient quota")
```

### Usage Tracker

```python
from src.usage_tracker import UsageTracker

# Initialize usage tracker
tracker = UsageTracker()

# Record token usage
usage_data = {
    'user_id': 'john.doe',
    'application': 'chat-assistant',
    'tokens_used': 150,
    'timestamp': datetime.now(),
    'cost': 0.0015
}

tracker.record_usage(usage_data)

# Get usage statistics
stats = tracker.get_user_stats('john.doe', days=7)
print(f"Total tokens used: {stats.total_tokens}")
print(f"Average tokens per request: {stats.average_tokens}")
print(f"Total cost: ${stats.total_cost}")
```

## API Integration

### Basic API Usage

```python
import requests
from src.api_client import TokenManagementClient

# Initialize API client
client = TokenManagementClient(
    base_url="https://api.tokenmanagement.com",
    api_key="your-api-key"
)

# Check user quota
quota = client.get_user_quota("john.doe")
print(f"Quota: {quota}")

# Record token usage
usage_data = {
    'user_id': 'john.doe',
    'application': 'chat-assistant',
    'tokens_used': 150
}

response = client.record_usage(usage_data)
if response.status_code == 200:
    print("Usage recorded successfully")
```

### Advanced API Integration

```python
# Batch API operations
def batch_process_requests(requests_data):
    """Process multiple requests in batch."""
    results = []
    
    for request_data in requests_data:
        try:
            # Check quota
            quota = client.get_user_quota(request_data['user_id'])
            
            if quota['daily_remaining'] >= request_data['required_tokens']:
                # Process request
                response = client.process_request(request_data)
                results.append({
                    'success': True,
                    'response': response.json()
                })
            else:
                results.append({
                    'success': False,
                    'error': 'Insufficient quota'
                })
        except Exception as e:
            results.append({
                'success': False,
                'error': str(e)
            })
    
    return results

# Usage
requests_data = [
    {'user_id': 'john.doe', 'required_tokens': 100},
    {'user_id': 'jane.smith', 'required_tokens': 200},
    {'user_id': 'bob.wilson', 'required_tokens': 150}
]

results = batch_process_requests(requests_data)
```

### Webhook Integration

```python
from src.webhook import WebhookManager

# Initialize webhook manager
webhook_manager = WebhookManager()

# Register webhook
webhook_config = {
    'url': 'https://your-app.com/webhooks/token-usage',
    'events': ['usage_recorded', 'quota_warning', 'quota_critical'],
    'secret': 'your-webhook-secret'
}

webhook_manager.register_webhook(webhook_config)

# Send webhook notification
def send_usage_notification(user_id, tokens_used):
    """Send usage notification via webhook."""
    payload = {
        'event': 'usage_recorded',
        'user_id': user_id,
        'tokens_used': tokens_used,
        'timestamp': datetime.now().isoformat()
    }
    
    webhook_manager.send_notification(payload)

# Usage
send_usage_notification('john.doe', 150)
```

## Database Integration

### Database Models

```python
from src.database.models import User, Quota, UsageRecord
from src.database import Database

# Initialize database connection
db = Database()

# Create user record
user = User(
    username='john.doe',
    email='john.doe@example.com',
    full_name='John Doe',
    department='Engineering'
)

db.session.add(user)
db.session.commit()

# Create quota record
quota = Quota(
    user_id=user.id,
    daily_limit=10000,
    monthly_limit=300000,
    hard_limit=1000000
)

db.session.add(quota)
db.session.commit()

# Record usage
usage = UsageRecord(
    user_id=user.id,
    application='chat-assistant',
    tokens_used=150,
    cost=0.0015,
    timestamp=datetime.now()
)

db.session.add(usage)
db.session.commit()
```

### Database Queries

```python
# Get user with quota
def get_user_with_quota(username):
    """Get user and their quota information."""
    user = db.session.query(User).filter_by(username=username).first()
    
    if user:
        quota = db.session.query(Quota).filter_by(user_id=user.id).first()
        return {
            'user': user,
            'quota': quota
        }
    return None

# Get usage statistics
def get_usage_statistics(user_id, days=7):
    """Get usage statistics for user."""
    from datetime import datetime, timedelta
    
    start_date = datetime.now() - timedelta(days=days)
    
    usage_records = db.session.query(UsageRecord).filter(
        UsageRecord.user_id == user_id,
        UsageRecord.timestamp >= start_date
    ).all()
    
    total_tokens = sum(record.tokens_used for record in usage_records)
    total_cost = sum(record.cost for record in usage_records)
    
    return {
        'total_tokens': total_tokens,
        'total_cost': total_cost,
        'average_tokens_per_request': total_tokens / len(usage_records) if usage_records else 0,
        'request_count': len(usage_records)
    }
```

### Database Migrations

```python
# Create migration
def create_quota_migration():
    """Create database migration for quota management."""
    migration_content = '''
"""Add quota management tables

Revision ID: 002_add_quota_tables
Revises: 001_initial_setup
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create quota table
    op.create_table('quotas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('daily_limit', sa.Integer(), nullable=False),
        sa.Column('monthly_limit', sa.Integer(), nullable=False),
        sa.Column('hard_limit', sa.Integer(), nullable=False),
        sa.Column('warning_threshold', sa.Float(), nullable=False),
        sa.Column('critical_threshold', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create usage record table
    op.create_table('usage_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('application', sa.String(), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=False),
        sa.Column('cost', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('usage_records')
    op.drop_table('quotas')
    '''
    
    # Write migration file
    with open('migrations/002_add_quota_tables.py', 'w') as f:
        f.write(migration_content)
```

## Token Counting

### Basic Token Counting

```python
from src.token_counter import TokenCounter

# Initialize counter
counter = TokenCounter()

# Count tokens
text = "Hello, world! This is a test sentence."
tokens = counter.count_tokens(text)
print(f"Token count: {tokens}")

# Count tokens for different models
models = ['gpt-4', 'claude-3', 'llama-2']
for model in models:
    model_tokens = counter.count_tokens(text, model=model)
    print(f"{model}: {model_tokens} tokens")
```

### Advanced Token Counting

```python
# Batch token counting
def batch_count_tokens(texts, model='gpt-4'):
    """Count tokens for multiple texts."""
    counter = TokenCounter()
    
    results = []
    for text in texts:
        tokens = counter.count_tokens(text, model=model)
        results.append({
            'text': text,
            'tokens': tokens,
            'cost': tokens * 0.00001  # Example cost calculation
        })
    
    return results

# Usage
texts = [
    "Hello, world!",
    "This is a longer text that will use more tokens.",
    "A very short text."
]

results = batch_count_tokens(texts)
for result in results:
    print(f"Text: {result['text'][:20]}...")
    print(f"Tokens: {result['tokens']}, Cost: ${result['cost']:.4f}")
```

### Token Counting with Context

```python
# Count tokens with context
def count_tokens_with_context(text, context=None):
    """Count tokens including context."""
    counter = TokenCounter()
    
    if context:
        full_text = f"{context}\n\n{text}"
    else:
        full_text = text
    
    tokens = counter.count_tokens(full_text)
    
    return {
        'text_tokens': counter.count_tokens(text),
        'context_tokens': counter.count_tokens(context) if context else 0,
        'total_tokens': tokens,
        'context_ratio': (counter.count_tokens(context) / tokens) if context else 0
    }

# Usage
context = "You are a helpful assistant. Answer the user's question:"
text = "What is the capital of France?"

result = count_tokens_with_context(text, context)
print(f"Context tokens: {result['context_tokens']}")
print(f"Question tokens: {result['text_tokens']}")
print(f"Total tokens: {result['total_tokens']}")
```

## Quota Management

### Quota Validation

```python
from src.quota_manager import QuotaManager

# Initialize quota manager
quota_manager = QuotaManager()

# Check quota
def check_user_quota(user_id, required_tokens):
    """Check if user has sufficient quota."""
    quota_info = quota_manager.get_user_quota(user_id)
    
    if quota_info.daily_remaining >= required_tokens:
        return {
            'has_quota': True,
            'quota_info': quota_info
        }
    else:
        return {
            'has_quota': False,
            'quota_info': quota_info,
            'error': f'Insufficient quota. Required: {required_tokens}, Available: {quota_info.daily_remaining}'
        }

# Usage
result = check_user_quota('john.doe', 1000)
if result['has_quota']:
    print("User has sufficient quota")
else:
    print(result['error'])
```

### Quota Management Operations

```python
# Update user quota
def update_user_quota(user_id, new_limits):
    """Update user quota limits."""
    quota_manager = QuotaManager()
    
    try:
        quota_manager.update_user_quota(user_id, new_limits)
        return {'success': True, 'message': 'Quota updated successfully'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Usage
new_limits = {
    'daily_limit': 15000,
    'monthly_limit': 450000,
    'hard_limit': 1500000,
    'warning_threshold': 0.8,
    'critical_threshold': 0.95
}

result = update_user_quota('john.doe', new_limits)
print(result)
```

### Quota Templates

```python
# Apply quota template
def apply_quota_template(user_id, template_name):
    """Apply predefined quota template to user."""
    templates = {
        'basic': {
            'daily_limit': 5000,
            'monthly_limit': 150000,
            'hard_limit': 500000,
            'warning_threshold': 0.8,
            'critical_threshold': 0.95
        },
        'premium': {
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
    
    if template_name in templates:
        template = templates[template_name]
        return update_user_quota(user_id, template)
    else:
        return {'success': False, 'error': f'Unknown template: {template_name}'}

# Usage
result = apply_quota_template('john.doe', 'premium')
print(result)
```

## Monitoring and Analytics

### Usage Analytics

```python
from src.analytics import TokenAnalytics

# Initialize analytics
analytics = TokenAnalytics()

# Generate usage report
def generate_usage_report(user_id=None, days=7):
    """Generate usage report for user or all users."""
    report = analytics.generate_usage_report(user_id, days)
    
    return {
        'total_tokens': report.total_tokens,
        'total_cost': report.total_cost,
        'average_tokens_per_request': report.average_tokens_per_request,
        'request_count': report.request_count,
        'daily_breakdown': report.daily_breakdown,
        'application_breakdown': report.application_breakdown
    }

# Usage
report = generate_usage_report('john.doe', 7)
print(f"Total tokens used: {report['total_tokens']}")
print(f"Total cost: ${report['total_cost']:.2f}")
print(f"Average tokens per request: {report['average_tokens_per_request']}")
```

### Performance Monitoring

```python
from src.monitoring import PerformanceMonitor

# Initialize monitor
monitor = PerformanceMonitor()

# Track performance
def track_performance(operation, duration, success=True):
    """Track performance metrics."""
    monitor.track_metric({
        'operation': operation,
        'duration': duration,
        'success': success,
        'timestamp': datetime.now()
    })

# Usage
track_performance('token_counting', 0.015, True)
track_performance('quota_check', 0.008, True)
track_performance('api_request', 0.250, False)
```

### Alert System

```python
from src.alerting import AlertManager

# Initialize alert manager
alert_manager = AlertManager()

# Send alert
def send_alert(user_id, message, severity='warning'):
    """Send alert to user."""
    alert_manager.send_alert({
        'user_id': user_id,
        'message': message,
        'severity': severity,
        'timestamp': datetime.now()
    })

# Usage
send_alert('john.doe', 'You have used 80% of your daily quota', 'warning')
send_alert('john.doe', 'CRITICAL: You have exceeded your daily quota', 'critical')
```

## Testing

### Unit Tests

```python
import pytest
from src.token_counter import TokenCounter
from src.quota_manager import QuotaManager

class TestTokenCounter:
    def test_token_counting(self):
        """Test basic token counting functionality."""
        counter = TokenCounter()
        text = "Hello, world!"
        tokens = counter.count_tokens(text)
        
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_different_models(self):
        """Test token counting for different models."""
        counter = TokenCounter()
        text = "Hello, world!"
        
        gpt4_tokens = counter.count_tokens(text, model='gpt-4')
        claude_tokens = counter.count_tokens(text, model='claude-3')
        
        assert gpt4_tokens > 0
        assert claude_tokens > 0

class TestQuotaManager:
    def test_quota_check(self):
        """Test quota validation."""
        quota_manager = QuotaManager()
        
        # Mock user quota
        quota_manager._mock_quotas = {
            'john.doe': {
                'daily_limit': 10000,
                'daily_used': 5000,
                'monthly_limit': 300000,
                'monthly_used': 150000,
                'hard_limit': 1000000
            }
        }
        
        result = quota_manager.has_sufficient_quota('john.doe', 1000)
        assert result['has_quota'] == True
        
        result = quota_manager.has_sufficient_quota('john.doe', 10000)
        assert result['has_quota'] == False
```

### Integration Tests

```python
import pytest
from src.api_client import TokenManagementClient
from src.database import Database

class TestAPIIntegration:
    def test_api_client(self):
        """Test API client functionality."""
        client = TokenManagementClient(
            base_url="https://api.tokenmanagement.com",
            api_key="test-key"
        )
        
        # Mock response
        client._mock_responses = {
            '/quota/john.doe': {
                'daily_limit': 10000,
                'daily_used': 5000,
                'daily_remaining': 5000
            }
        }
        
        quota = client.get_user_quota('john.doe')
        assert quota['daily_limit'] == 10000
        assert quota['daily_used'] == 5000

class TestDatabaseIntegration:
    def test_database_operations(self):
        """Test database operations."""
        db = Database()
        
        # Create test user
        user = {
            'username': 'testuser',
            'email': 'test@example.com',
            'full_name': 'Test User'
        }
        
        user_id = db.create_user(user)
        assert user_id is not None
        
        # Get user
        retrieved_user = db.get_user(user_id)
        assert retrieved_user['username'] == 'testuser'
        
        # Delete user
        db.delete_user(user_id)
        deleted_user = db.get_user(user_id)
        assert deleted_user is None
```

### Test Configuration

```python
# pytest configuration
pytest_plugins = ['pytest_asyncio']

@pytest.fixture
def test_database():
    """Create test database fixture."""
    from src.database import Database
    db = Database(testing=True)
    yield db
    db.cleanup()

@pytest.fixture
def test_token_counter():
    """Create test token counter fixture."""
    from src.token_counter import TokenCounter
    counter = TokenCounter(testing=True)
    return counter

@pytest.fixture
def test_quota_manager():
    """Create test quota manager fixture."""
    from src.quota_manager import QuotaManager
    manager = QuotaManager(testing=True)
    return manager
```

## Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# Expose port
EXPOSE 8000

# Start application
CMD ["python", "-m", "uvicorn", "token_management.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  token-management:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_HOST=postgres
      - DATABASE_PORT=5432
      - DATABASE_NAME=token_management
      - DATABASE_USER=token_user
      - DATABASE_PASSWORD=secure_password
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=token_management
      - POSTGRES_USER=token_user
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: token-management
spec:
  replicas: 3
  selector:
    matchLabels:
      app: token-management
  template:
    metadata:
      labels:
        app: token-management
    spec:
      containers:
      - name: token-management
        image: your-registry/token-management:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_HOST
          value: "postgres-service"
        - name: DATABASE_PORT
          value: "5432"
        - name: DATABASE_NAME
          value: "token_management"
        - name: DATABASE_USER
          value: "token_user"
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: password
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: token-management-service
spec:
  selector:
    app: token-management
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Contributing

### Development Workflow

```bash
# Fork the repository
git clone https://github.com/your-username/token-management.git
cd token-management

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes
# Add tests
# Update documentation

# Run tests
python -m pytest tests/

# Run linting
flake8 src/
black src/

# Commit changes
git add .
git commit -m "Add your feature description"

# Push to your fork
git push origin feature/your-feature-name

# Create pull request
```

### Code Style

```python
# Follow PEP 8 style guide
# Use black for code formatting
# Use flake8 for linting

# Example of good code style
def calculate_token_cost(tokens_used, model="gpt-4"):
    """
    Calculate the cost of token usage.
    
    Args:
        tokens_used (int): Number of tokens used
        model (str): Model used for token counting
        
    Returns:
        float: Cost in USD
    """
    # Define cost per token for different models
    cost_per_token = {
        "gpt-4": 0.00001,
        "claude-3": 0.000015,
        "llama-2": 0.000008
    }
    
    if model not in cost_per_token:
        raise ValueError(f"Unsupported model: {model}")
    
    return tokens_used * cost_per_token[model]
```

### Documentation Standards

```python
# All functions should have docstrings
def record_token_usage(user_id, tokens_used, application, cost=None):
    """
    Record token usage in the database.
    
    Args:
        user_id (str): User identifier
        tokens_used (int): Number of tokens used
        application (str): Application that used the tokens
        cost (float, optional): Cost of token usage
        
    Returns:
        dict: Record information
        
    Raises:
        ValueError: If tokens_used is negative
    """
    if tokens_used < 0:
        raise ValueError("tokens_used cannot be negative")
    
    # Record usage
    usage_record = {
        'user_id': user_id,
        'tokens_used': tokens_used,
        'application': application,
        'cost': cost or calculate_token_cost(tokens_used),
        'timestamp': datetime.now()
    }
    
    # Save to database
    db.session.add(usage_record)
    db.session.commit()
    
    return usage_record
```

### Release Process

```bash
# Create release branch
git checkout main
git pull origin main
git checkout -b release/v1.0.0

# Update version numbers
sed -i 's/__version__ = ".*"/__version__ = "1.0.0"/' src/__init__.py

# Update changelog
echo "## Version 1.0.0" >> CHANGELOG.md
echo "- Added new feature" >> CHANGELOG.md
echo "- Fixed bug" >> CHANGELOG.md

# Commit and tag
git add .
git commit -m "Release version 1.0.0"
git tag v1.0.0

# Push to main
git push origin release/v1.0.0
git push origin v1.0.0

# Create release on GitHub
# (Manual step)
```

---

*This Developer Guide provides comprehensive instructions for working with the Token Management System. For additional information, please refer to the other documentation guides or contact the development team.*