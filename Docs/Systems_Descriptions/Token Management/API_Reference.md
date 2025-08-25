# Token Management System - API Reference

## Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [API Endpoints](#api-endpoints)
  - [User Management](#user-management)
  - [Quota Management](#quota-management)
  - [Token Counting](#token-counting)
  - [Usage Tracking](#usage-tracking)
  - [Analytics](#analytics)
  - [Monitoring](#monitoring)
- [Webhooks](#webhooks)
- [SDK Reference](#sdk-reference)
- [Examples](#examples)

## Overview

The Token Management System provides a comprehensive REST API for managing token usage, quotas, and analytics. This API reference covers all available endpoints, request/response formats, and usage examples.

### API Features

- **User Management**: Create, update, and manage user accounts
- **Quota Management**: Set and enforce token usage limits
- **Token Counting**: Accurate token counting for multiple AI models
- **Usage Tracking**: Real-time tracking of token consumption
- **Analytics**: Comprehensive usage analytics and reporting
- **Monitoring**: System health and performance monitoring
- **Webhooks**: Real-time notifications for important events

## Authentication

### API Key Authentication

All API requests require authentication using an API key. Include your API key in the request headers:

```http
Authorization: Bearer your-api-key-here
```

### API Key Management

```python
import requests

# Set API key in headers
headers = {
    'Authorization': 'Bearer your-api-key-here',
    'Content-Type': 'application/json'
}

# Make API request
response = requests.get('https://api.tokenmanagement.com/v1/users', headers=headers)
```

### JWT Authentication

For certain endpoints, JWT tokens are required:

```http
Authorization: Bearer your-jwt-token
```

## Base URL

```
Production: https://api.tokenmanagement.com/v1
Staging:    https://staging-api.tokenmanagement.com/v1
Development: http://localhost:8000/v1
```

## Rate Limiting

API requests are subject to rate limiting to ensure fair usage:

- **Requests per minute**: 60 requests per minute per API key
- **Requests per hour**: 1000 requests per hour per API key
- **Burst limit**: 100 concurrent requests

Rate limit headers in responses:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1640995200
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "INSUFFICIENT_QUOTA",
    "message": "User has insufficient token quota",
    "details": {
      "required_tokens": 1000,
      "available_tokens": 500
    },
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid request parameters |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |
| 503 | Service Unavailable - System maintenance |

### Common Error Codes

| Error Code | Description |
|------------|-------------|
| `INSUFFICIENT_QUOTA` | User has insufficient token quota |
| `INVALID_API_KEY` | Invalid or expired API key |
| `USER_NOT_FOUND` | User not found |
| `QUOTA_NOT_FOUND` | Quota configuration not found |
| `TOKEN_COUNTING_ERROR` | Error counting tokens |
| `DATABASE_ERROR` | Database operation failed |
| `RATE_LIMIT_EXCEEDED` | API rate limit exceeded |

## API Endpoints

### User Management

#### Create User

Create a new user account.

**Endpoint:** `POST /users`

**Request Body:**
```json
{
  "username": "john.doe",
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "department": "Engineering",
  "role": "user"
}
```

**Response:**
```json
{
  "user": {
    "id": "user_123456",
    "username": "john.doe",
    "email": "john.doe@example.com",
    "full_name": "John Doe",
    "department": "Engineering",
    "role": "user",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

**Example:**
```python
import requests

url = "https://api.tokenmanagement.com/v1/users"
headers = {
    'Authorization': 'Bearer your-api-key',
    'Content-Type': 'application/json'
}

data = {
    "username": "john.doe",
    "email": "john.doe@example.com",
    "full_name": "John Doe",
    "department": "Engineering",
    "role": "user"
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

#### Get User

Retrieve user information by ID or username.

**Endpoint:** `GET /users/{user_id}` or `GET /users?username={username}`

**Response:**
```json
{
  "user": {
    "id": "user_123456",
    "username": "john.doe",
    "email": "john.doe@example.com",
    "full_name": "John Doe",
    "department": "Engineering",
    "role": "user",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

**Example:**
```python
import requests

# Get user by ID
url = "https://api.tokenmanagement.com/v1/users/user_123456"
headers = {'Authorization': 'Bearer your-api-key'}

response = requests.get(url, headers=headers)
print(response.json())

# Get user by username
url = "https://api.tokenmanagement.com/v1/users?username=john.doe"
response = requests.get(url, headers=headers)
print(response.json())
```

#### Update User

Update user information.

**Endpoint:** `PUT /users/{user_id}`

**Request Body:**
```json
{
  "full_name": "Johnathan Doe",
  "department": "Product",
  "role": "manager"
}
```

**Response:**
```json
{
  "user": {
    "id": "user_123456",
    "username": "john.doe",
    "email": "john.doe@example.com",
    "full_name": "Johnathan Doe",
    "department": "Product",
    "role": "manager",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

#### Delete User

Delete a user account.

**Endpoint:** `DELETE /users/{user_id}`

**Response:**
```json
{
  "message": "User deleted successfully"
}
```

#### List Users

List all users with pagination.

**Endpoint:** `GET /users`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20, max: 100)
- `department` (optional): Filter by department
- `role` (optional): Filter by role

**Response:**
```json
{
  "users": [
    {
      "id": "user_123456",
      "username": "john.doe",
      "email": "john.doe@example.com",
      "full_name": "John Doe",
      "department": "Engineering",
      "role": "user"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_items": 100,
    "total_pages": 5
  }
}
```

### Quota Management

#### Get User Quota

Retrieve user's current quota information.

**Endpoint:** `GET /quotas/{user_id}`

**Response:**
```json
{
  "quota": {
    "user_id": "user_123456",
    "daily_limit": 10000,
    "daily_used": 5000,
    "daily_remaining": 5000,
    "monthly_limit": 300000,
    "monthly_used": 150000,
    "monthly_remaining": 150000,
    "hard_limit": 1000000,
    "warning_threshold": 0.8,
    "critical_threshold": 0.95,
    "last_updated": "2024-01-01T12:00:00Z"
  }
}
```

**Example:**
```python
import requests

url = "https://api.tokenmanagement.com/v1/quotas/user_123456"
headers = {'Authorization': 'Bearer your-api-key'}

response = requests.get(url, headers=headers)
quota = response.json()['quota']
print(f"Daily remaining: {quota['daily_remaining']}")
```

#### Update User Quota

Update user's quota limits.

**Endpoint:** `PUT /quotas/{user_id}`

**Request Body:**
```json
{
  "daily_limit": 15000,
  "monthly_limit": 450000,
  "hard_limit": 1500000,
  "warning_threshold": 0.8,
  "critical_threshold": 0.95
}
```

**Response:**
```json
{
  "quota": {
    "user_id": "user_123456",
    "daily_limit": 15000,
    "daily_used": 5000,
    "daily_remaining": 10000,
    "monthly_limit": 450000,
    "monthly_used": 150000,
    "monthly_remaining": 300000,
    "hard_limit": 1500000,
    "warning_threshold": 0.8,
    "critical_threshold": 0.95,
    "last_updated": "2024-01-01T12:00:00Z"
  }
}
```

#### Apply Quota Template

Apply a predefined quota template to a user.

**Endpoint:** `POST /quotas/{user_id}/templates/{template_name}`

**Available Templates:**
- `basic`: 5,000 daily, 150,000 monthly, 500,000 hard limit
- `premium`: 20,000 daily, 600,000 monthly, 2,000,000 hard limit
- `enterprise`: 100,000 daily, 3,000,000 monthly, 10,000,000 hard limit

**Response:**
```json
{
  "quota": {
    "user_id": "user_123456",
    "daily_limit": 20000,
    "daily_used": 5000,
    "daily_remaining": 15000,
    "monthly_limit": 600000,
    "monthly_used": 150000,
    "monthly_remaining": 450000,
    "hard_limit": 2000000,
    "warning_threshold": 0.85,
    "critical_threshold": 0.95,
    "last_updated": "2024-01-01T12:00:00Z"
  }
}
```

#### Check Quota Availability

Check if user has sufficient quota for a token request.

**Endpoint:** `POST /quotas/{user_id}/check`

**Request Body:**
```json
{
  "required_tokens": 1000,
  "model": "gpt-4"
}
```

**Response:**
```json
{
  "has_quota": true,
  "quota_info": {
    "user_id": "user_123456",
    "daily_limit": 10000,
    "daily_used": 5000,
    "daily_remaining": 5000,
    "monthly_limit": 300000,
    "monthly_used": 150000,
    "monthly_remaining": 150000,
    "hard_limit": 1000000,
    "warning_threshold": 0.8,
    "critical_threshold": 0.95
  },
  "estimated_cost": 0.01
}
```

### Token Counting

#### Count Tokens

Count tokens in text for a specific model.

**Endpoint:** `POST /token-count`

**Request Body:**
```json
{
  "text": "Hello, world! This is a test sentence.",
  "model": "gpt-4"
}
```

**Response:**
```json
{
  "tokens": 8,
  "model": "gpt-4",
  "cost_estimate": 0.00008
}
```

**Example:**
```python
import requests

url = "https://api.tokenmanagement.com/v1/token-count"
headers = {
    'Authorization': 'Bearer your-api-key',
    'Content-Type': 'application/json'
}

data = {
    "text": "Hello, world! This is a test sentence.",
    "model": "gpt-4"
}

response = requests.post(url, headers=headers, json=data)
result = response.json()
print(f"Token count: {result['tokens']}")
```

#### Batch Token Counting

Count tokens for multiple texts in a single request.

**Endpoint:** `POST /token-count/batch`

**Request Body:**
```json
{
  "texts": [
    "Hello, world!",
    "This is a longer text that will use more tokens.",
    "A very short text."
  ],
  "model": "gpt-4"
}
```

**Response:**
```json
{
  "results": [
    {
      "text": "Hello, world!",
      "tokens": 3,
      "cost_estimate": 0.00003
    },
    {
      "text": "This is a longer text that will use more tokens.",
      "tokens": 10,
      "cost_estimate": 0.0001
    },
    {
      "text": "A very short text.",
      "tokens": 4,
      "cost_estimate": 0.00004
    }
  ],
  "total_tokens": 17,
  "total_cost_estimate": 0.00017
}
```

### Usage Tracking

#### Record Usage

Record token usage for a user.

**Endpoint:** `POST /usage`

**Request Body:**
```json
{
  "user_id": "user_123456",
  "application": "chat-assistant",
  "tokens_used": 150,
  "model": "gpt-4",
  "metadata": {
    "request_id": "req_123456",
    "endpoint": "/chat/completions"
  }
}
```

**Response:**
```json
{
  "usage_record": {
    "id": "usage_123456",
    "user_id": "user_123456",
    "application": "chat-assistant",
    "tokens_used": 150,
    "model": "gpt-4",
    "cost": 0.0015,
    "timestamp": "2024-01-01T12:00:00Z",
    "metadata": {
      "request_id": "req_123456",
      "endpoint": "/chat/completions"
    }
  }
}
```

**Example:**
```python
import requests

url = "https://api.tokenmanagement.com/v1/usage"
headers = {
    'Authorization': 'Bearer your-api-key',
    'Content-Type': 'application/json'
}

data = {
    "user_id": "user_123456",
    "application": "chat-assistant",
    "tokens_used": 150,
    "model": "gpt-4",
    "metadata": {
        "request_id": "req_123456",
        "endpoint": "/chat/completions"
    }
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

#### Get Usage History

Retrieve usage history for a user.

**Endpoint:** `GET /usage/{user_id}`

**Query Parameters:**
- `start_date` (optional): Start date (ISO 8601 format)
- `end_date` (optional): End date (ISO 8601 format)
- `application` (optional): Filter by application
- `model` (optional): Filter by model
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20, max: 100)

**Response:**
```json
{
  "usage_history": [
    {
      "id": "usage_123456",
      "user_id": "user_123456",
      "application": "chat-assistant",
      "tokens_used": 150,
      "model": "gpt-4",
      "cost": 0.0015,
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ],
  "summary": {
    "total_tokens": 150,
    "total_cost": 0.0015,
    "average_tokens_per_request": 150,
    "request_count": 1
  },
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_items": 1,
    "total_pages": 1
  }
}
```

### Analytics

#### Get Usage Analytics

Get comprehensive usage analytics for a user.

**Endpoint:** `GET /analytics/{user_id}`

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 7, max: 365)
- `granularity` (optional): Time granularity (hourly, daily, weekly, monthly)

**Response:**
```json
{
  "analytics": {
    "user_id": "user_123456",
    "period": {
      "start": "2024-01-01T00:00:00Z",
      "end": "2024-01-08T00:00:00Z"
    },
    "summary": {
      "total_tokens": 10500,
      "total_cost": 10.50,
      "average_tokens_per_request": 150,
      "request_count": 70,
      "unique_applications": 3
    },
    "daily_breakdown": [
      {
        "date": "2024-01-01",
        "tokens": 1500,
        "cost": 1.50,
        "requests": 10
      }
    ],
    "application_breakdown": [
      {
        "application": "chat-assistant",
        "tokens": 7500,
        "cost": 7.50,
        "percentage": 71.4
      }
    ],
    "model_breakdown": [
      {
        "model": "gpt-4",
        "tokens": 10500,
        "cost": 10.50,
        "percentage": 100.0
      }
    ],
    "trends": {
      "daily_growth_rate": 5.2,
      "cost_trend": "increasing",
      "usage_prediction": {
        "next_week_tokens": 12000,
        "confidence": 0.85
      }
    }
  }
}
```

#### Get System Analytics

Get system-wide analytics and metrics.

**Endpoint:** `GET /analytics/system`

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 7, max: 365)

**Response:**
```json
{
  "system_analytics": {
    "period": {
      "start": "2024-01-01T00:00:00Z",
      "end": "2024-01-08T00:00:00Z"
    },
    "summary": {
      "total_users": 100,
      "active_users": 75,
      "total_tokens": 1050000,
      "total_cost": 1050.00,
      "average_tokens_per_user": 10500,
      "average_tokens_per_request": 150
    },
    "user_distribution": [
      {
        "usage_range": "0-1000",
        "user_count": 20,
        "percentage": 20.0
      }
    ],
    "top_applications": [
      {
        "application": "chat-assistant",
        "tokens": 750000,
        "cost": 750.00,
        "percentage": 71.4
      }
    ],
    "cost_breakdown": {
      "by_model": {
        "gpt-4": 1050.00,
        "claude-3": 0.00,
        "llama-2": 0.00
      },
      "by_department": {
        "Engineering": 630.00,
        "Product": 420.00
      }
    }
  }
}
```

### Monitoring

#### Get System Health

Get current system health metrics.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "health": {
    "status": "healthy",
    "timestamp": "2024-01-01T12:00:00Z",
    "database": {
      "status": "healthy",
      "connection_pool": {
        "total_connections": 10,
        "active_connections": 5,
        "idle_connections": 5
      }
    },
    "redis": {
      "status": "healthy",
      "memory_usage": "256MB",
      "connected_clients": 3
    },
    "api": {
      "status": "healthy",
      "requests_per_minute": 45,
      "average_response_time": 0.045
    },
    "system": {
      "cpu_usage": 45.2,
      "memory_usage": 62.8,
      "disk_usage": 78.5
    }
  }
}
```

#### Get Performance Metrics

Get system performance metrics.

**Endpoint:** `GET /metrics`

**Response:**
```json
{
  "metrics": {
    "timestamp": "2024-01-01T12:00:00Z",
    "performance": {
      "requests_per_second": 1.2,
      "average_response_time": 0.045,
      "p95_response_time": 0.120,
      "p99_response_time": 0.250
    },
    "database": {
      "queries_per_second": 15.3,
      "average_query_time": 0.008,
      "slow_queries": 2
    },
    "token_counting": {
      "tokens_per_second": 5000,
      "average_counting_time": 0.001
    },
    "errors": {
      "total_errors": 5,
      "error_rate": 0.05,
      "error_breakdown": {
        "429": 2,
        "500": 3
      }
    }
  }
}
```

#### Get Alerts

Get current system alerts.

**Endpoint:** `GET /alerts`

**Query Parameters:**
- `severity` (optional): Filter by severity (info, warning, critical)
- `status` (optional): Filter by status (active, resolved)

**Response:**
```json
{
  "alerts": [
    {
      "id": "alert_123456",
      "severity": "warning",
      "message": "High memory usage detected",
      "details": {
        "memory_usage": 85.2,
        "threshold": 80.0
      },
      "timestamp": "2024-01-01T12:00:00Z",
      "status": "active"
    }
  ]
}
```

### Webhooks

#### Register Webhook

Register a webhook to receive notifications.

**Endpoint:** `POST /webhooks`

**Request Body:**
```json
{
  "url": "https://your-app.com/webhooks/token-usage",
  "events": ["usage_recorded", "quota_warning", "quota_critical"],
  "secret": "your-webhook-secret"
}
```

**Response:**
```json
{
  "webhook": {
    "id": "webhook_123456",
    "url": "https://your-app.com/webhooks/token-usage",
    "events": ["usage_recorded", "quota_warning", "quota_critical"],
    "secret": "your-webhook-secret",
    "created_at": "2024-01-01T12:00:00Z",
    "status": "active"
  }
}
```

#### List Webhooks

List all registered webhooks.

**Endpoint:** `GET /webhooks`

**Response:**
```json
{
  "webhooks": [
    {
      "id": "webhook_123456",
      "url": "https://your-app.com/webhooks/token-usage",
      "events": ["usage_recorded", "quota_warning", "quota_critical"],
      "secret": "your-webhook-secret",
      "created_at": "2024-01-01T12:00:00Z",
      "status": "active"
    }
  ]
}
```

#### Delete Webhook

Delete a registered webhook.

**Endpoint:** `DELETE /webhooks/{webhook_id}`

**Response:**
```json
{
  "message": "Webhook deleted successfully"
}
```

## SDK Reference

### Python SDK

#### Installation

```bash
pip install token-management-sdk
```

#### Basic Usage

```python
from token_management_sdk import TokenManagementClient

# Initialize client
client = TokenManagementClient(
    api_key="your-api-key",
    base_url="https://api.tokenmanagement.com/v1"
)

# Create user
user = client.users.create({
    "username": "john.doe",
    "email": "john.doe@example.com",
    "full_name": "John Doe",
    "department": "Engineering",
    "role": "user"
})

# Get user quota
quota = client.quotas.get("user_123456")
print(f"Daily remaining: {quota['daily_remaining']}")

# Count tokens
token_count = client.tokens.count("Hello, world!", model="gpt-4")
print(f"Token count: {token_count}")

# Record usage
client.usage.record({
    "user_id": "user_123456",
    "application": "chat-assistant",
    "tokens_used": 150,
    "model": "gpt-4"
})

# Get analytics
analytics = client.analytics.get_user("user_123456", days=7)
print(f"Total tokens: {analytics['summary']['total_tokens']}")
```

#### Advanced Usage

```python
# Batch operations
users = [
    {"username": "user1", "email": "user1@example.com"},
    {"username": "user2", "email": "user2@example.com"},
    {"username": "user3", "email": "user3@example.com"}
]

created_users = client.users.create_batch(users)

# Webhook management
webhook = client.webhooks.register({
    "url": "https://your-app.com/webhooks",
    "events": ["usage_recorded"],
    "secret": "your-secret"
})

# Async operations
import asyncio

async def async_example():
    # Async token counting
    tokens = await client.tokens.count_async("Hello, world!")
    print(f"Token count: {tokens}")
    
    # Async usage recording
    await client.usage.record_async({
        "user_id": "user_123456",
        "application": "chat-assistant",
        "tokens_used": 150
    })

# Run async example
asyncio.run(async_example())
```

### JavaScript SDK

#### Installation

```bash
npm install token-management-sdk
```

#### Basic Usage

```javascript
const { TokenManagementClient } = require('token-management-sdk');

// Initialize client
const client = new TokenManagementClient({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.tokenmanagement.com/v1'
});

// Create user
async function createUser() {
  const user = await client.users.create({
    username: 'john.doe',
    email: 'john.doe@example.com',
    fullName: 'John Doe',
    department: 'Engineering',
    role: 'user'
  });
  console.log('User created:', user);
}

// Get user quota
async function getQuota() {
  const quota = await client.quotas.get('user_123456');
  console.log('Daily remaining:', quota.dailyRemaining);
}

// Count tokens
async function countTokens() {
  const tokenCount = await client.tokens.count('Hello, world!', 'gpt-4');
  console.log('Token count:', tokenCount);
}

// Record usage
async function recordUsage() {
  await client.usage.record({
    userId: 'user_123456',
    application: 'chat-assistant',
    tokensUsed: 150,
    model: 'gpt-4'
  });
  console.log('Usage recorded');
}

// Run examples
async function main() {
  await createUser();
  await getQuota();
  await countTokens();
  await recordUsage();
}

main();
```

## Examples

### Complete Integration Example

```python
import requests
from datetime import datetime, timedelta

class TokenManagementIntegration:
    def __init__(self, api_key, base_url="https://api.tokenmanagement.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def process_user_request(self, user_id, text, model="gpt-4"):
        """Process a user request with token counting and quota management."""
        
        # Step 1: Count tokens
        token_count = self.count_tokens(text, model)
        
        # Step 2: Check quota
        quota_check = self.check_quota(user_id, token_count)
        
        if not quota_check['has_quota']:
            return {
                'success': False,
                'error': quota_check['error'],
                'quota_info': quota_check['quota_info']
            }
        
        # Step 3: Process the request (simulate)
        try:
            # Here you would actually call your AI model
            response = self.call_ai_model(text, model)
            
            # Step 4: Record usage
            self.record_usage(user_id, token_count, model)
            
            return {
                'success': True,
                'response': response,
                'tokens_used': token_count,
                'cost': self.calculate_cost(token_count, model)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Request processing failed: {str(e)}"
            }
    
    def count_tokens(self, text, model="gpt-4"):
        """Count tokens in text."""
        url = f"{self.base_url}/token-count"
        data = {"text": text, "model": model}
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        return response.json()['tokens']
    
    def check_quota(self, user_id, required_tokens):
        """Check if user has sufficient quota."""
        url = f"{self.base_url}/quotas/{user_id}/check"
        data = {"required_tokens": required_tokens, "model": "gpt-4"}
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def record_usage(self, user_id, tokens_used, model):
        """Record token usage."""
        url = f"{self.base_url}/usage"
        data = {
            "user_id": user_id,
            "application": "chat-assistant",
            "tokens_used": tokens_used,
            "model": model,
            "metadata": {
                "timestamp": datetime.now().isoformat()
            }
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def call_ai_model(self, text, model):
        """Simulate calling an AI model."""
        # This is a placeholder - replace with actual AI model integration
        return {
            "text": f"Response to: {text}",
            "model": model,
            "timestamp": datetime.now().isoformat()
        }
    
    def calculate_cost(self, tokens, model):
        """Calculate cost of token usage."""
        cost_per_token = {
            "gpt-4": 0.00001,
            "claude-3": 0.000015,
            "llama-2": 0.000008
        }
        
        return tokens * cost_per_token.get(model, 0.00001)

# Usage example
if __name__ == "__main__":
    # Initialize integration
    integration = TokenManagementIntegration("your-api-key")
    
    # Process user request
    result = integration.process_user_request(
        user_id="user_123456",
        text="Hello, can you help me with my project?",
        model="gpt-4"
    )
    
    print("Request result:")
    print(result)
```

### Webhook Handler Example

```python
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

# Webhook secret (should match what you registered)
WEBHOOK_SECRET = "your-webhook-secret"

@app.route('/webhooks/token-usage', methods=['POST'])
def handle_webhook():
    """Handle webhook notifications from token management system."""
    
    # Verify webhook signature
    signature = request.headers.get('X-Webhook-Signature')
    if not verify_webhook_signature(request.data, signature):
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Parse webhook data
    webhook_data = request.get_json()
    
    # Handle different event types
    event_type = webhook_data.get('event')
    
    if event_type == 'usage_recorded':
        handle_usage_recorded(webhook_data)
    elif event_type == 'quota_warning':
        handle_quota_warning(webhook_data)
    elif event_type == 'quota_critical':
        handle_quota_critical(webhook_data)
    else:
        print(f"Unknown event type: {event_type}")
    
    return jsonify({'status': 'success'}), 200

def verify_webhook_signature(data, signature):
    """Verify webhook signature."""
    if not signature:
        return False
    
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        data,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

def handle_usage_recorded(data):
    """Handle usage recorded event."""
    user_id = data['user_id']
    tokens_used = data['tokens_used']
    application = data['application']
    
    print(f"User {user_id} used {tokens_used} tokens in {application}")
    
    # Update your application's usage tracking
    # Send notifications if needed
    # etc.

def handle_quota_warning(data):
    """Handle quota warning event."""
    user_id = data['user_id']
    usage_percentage = data['usage_percentage']
    
    print(f"WARNING: User {user_id} has used {usage_percentage}% of quota")
    
    # Send warning notification to user
    # Log the warning
    # etc.

def handle_quota_critical(data):
    """Handle quota critical event."""
    user_id = data['user_id']
    usage_percentage = data['usage_percentage']
    
    print(f"CRITICAL: User {user_id} has used {usage_percentage}% of quota")
    
    # Send critical notification
    # Potentially block further requests
    # Escalate to admin
    # etc.

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

---

*This API Reference provides comprehensive documentation for the Token Management System API. For additional information, please refer to the other documentation guides or contact the development team.*