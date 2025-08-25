# API Documentation for Developers

## Overview

This document provides comprehensive API documentation for developers working with MCP (Model Context Protocol) servers within the KiloCode ecosystem. The API documentation follows the **Simple, Robust, Secure** approach and ensures proper integration with existing infrastructure.

## API Architecture

### API Design Principles
1. **RESTful Design**: Follow REST principles for API design
2. **Consistent Naming**: Use consistent naming conventions across all APIs
3. **Standard HTTP Methods**: Use standard HTTP methods (GET, POST, PUT, DELETE)
4. **Status Codes**: Use appropriate HTTP status codes
5. **Error Handling**: Provide clear and consistent error responses

### API Authentication
All MCP APIs require authentication using one of the following methods:

1. **JWT Tokens**: JSON Web Tokens for stateless authentication
2. **API Keys**: Simple API key authentication
3. **OAuth 2.0**: Integration with existing authentication systems

### API Versioning
APIs are versioned using URL versioning:
- `/api/v1/` - Current stable version
- `/api/v2/` - Next version (when available)

## MCP Server APIs

### 1. Filesystem Server API

#### Base URL
```
http://localhost:3000/api/v1
```

#### Authentication
```javascript
const headers = {
  'Authorization': 'Bearer YOUR_JWT_TOKEN',
  'Content-Type': 'application/json'
};
```

#### Endpoints

##### List Files
**GET** `/files`

List files in the specified directory.

**Request:**
```javascript
{
  "path": "/path/to/directory",
  "recursive": false,
  "includeHidden": false
}
```

**Response:**
```javascript
{
  "success": true,
  "data": {
    "path": "/path/to/directory",
    "files": [
      {
        "name": "example.txt",
        "path": "/path/to/directory/example.txt",
        "size": 1024,
        "modified": "2024-01-01T00:00:00Z",
        "type": "file"
      }
    ],
    "directories": [
      {
        "name": "subdir",
        "path": "/path/to/directory/subdir",
        "type": "directory"
      }
    ]
  }
}
```

##### Read File
**GET** `/files/read`

Read the contents of a file.

**Request:**
```javascript
{
  "path": "/path/to/file.txt"
}
```

**Response:**
```javascript
{
  "success": true,
  "data": {
    "path": "/path/to/file.txt",
    "content": "File contents here...",
    "size": 1024,
    "modified": "2024-01-01T00:00:00Z"
  }
}
```

##### Write File
**POST** `/files/write`

Write content to a file.

**Request:**
```javascript
{
  "path": "/path/to/file.txt",
  "content": "File content here...",
  "overwrite": true
}
```

**Response:**
```javascript
{
  "success": true,
  "data": {
    "path": "/path/to/file.txt",
    "size": 1024,
    "modified": "2024-01-01T00:00:00Z"
  }
}
```

##### Delete File
**DELETE** `/files/delete`

Delete a file or directory.

**Request:**
```javascript
{
  "path": "/path/to/file.txt"
}
```

**Response:**
```javascript
{
  "success": true,
  "data": {
    "path": "/path/to/file.txt",
    "deleted": true
  }
}
```

### 2. PostgreSQL Server API

#### Base URL
```
http://localhost:3001/api/v1
```

#### Authentication
```javascript
const headers = {
  'Authorization': 'Bearer YOUR_JWT_TOKEN',
  'Content-Type': 'application/json'
};
```

#### Endpoints

##### Execute Query
**POST** `/query`

Execute a SQL query.

**Request:**
```javascript
{
  "query": "SELECT * FROM users WHERE id = $1",
  "params": [1],
  "type": "select"
}
```

**Response:**
```javascript
{
  "success": true,
  "data": {
    "rows": [
      {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com"
      }
    ],
    "rowCount": 1,
    "fields": ["id", "name", "email"]
  }
}
```

##### Get Table Schema
**GET** `/schema/:table`

Get the schema of a table.

**Request:**
```javascript
{
  "table": "users"
}
```

**Response:**
```javascript
{
  "success": true,
  "data": {
    "table": "users",
    "columns": [
      {
        "name": "id",
        "type": "integer",
        "nullable": false,
        "primary": true
      },
      {
        "name": "name",
        "type": "varchar(255)",
        "nullable": false,
        "primary": false
      }
    ]
  }
}
```

##### Get Tables
**GET** `/tables`

Get all tables in the database.

**Response:**
```javascript
{
  "success": true,
  "data": {
    "tables": [
      {
        "name": "users",
        "schema": "public",
        "size": 1024
      }
    ]
  }
}
```

### 3. Memory Service API

#### Base URL
```
http://localhost:3002/api/v1
```

#### Authentication
```javascript
const headers = {
  'Authorization': 'Bearer YOUR_JWT_TOKEN',
  'Content-Type': 'application/json'
};
```

#### Endpoints

##### Store Memory
**POST** `/memory/store`

Store a memory item.

**Request:**
```javascript
{
  "content": "This is a memory item",
  "tags": ["important", "work"],
  "metadata": {
    "category": "personal",
    "priority": "high"
  },
  "expire_at": "2024-12-31T23:59:59Z"
}
```

**Response:**
```javascript
{
  "success": true,
  "data": {
    "id": "mem_123456789",
    "content": "This is a memory item",
    "tags": ["important", "work"],
    "metadata": {
      "category": "personal",
      "priority": "high"
    },
    "created_at": "2024-01-01T00:00:00Z",
    "expire_at": "2024-12-31T23:59:59Z"
  }
}
```

##### Retrieve Memory
**GET** `/memory/retrieve`

Retrieve a memory item by ID.

**Request:**
```javascript
{
  "id": "mem_123456789"
}
```

**Response:**
```javascript
{
  "success": true,
  "data": {
    "id": "mem_123456789",
    "content": "This is a memory item",
    "tags": ["important", "work"],
    "metadata": {
      "category": "personal",
      "priority": "high"
    },
    "created_at": "2024-01-01T00:00:00Z",
    "expire_at": "2024-12-31T23:59:59Z"
  }
}
```

##### Search Memory
**POST** `/memory/search`

Search for memory items by content or tags.

**Request:**
```javascript
{
  "query": "important work",
  "tags": ["important"],
  "limit": 10,
  "offset": 0
}
```

**Response:**
```javascript
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "mem_123456789",
        "content": "This is a memory item",
        "tags": ["important", "work"],
        "score": 0.95,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 1,
    "limit": 10,
    "offset": 0
  }
}
```

##### Delete Memory
**DELETE** `/memory/delete`

Delete a memory item.

**Request:**
```javascript
{
  "id": "mem_123456789"
}
```

**Response:**
```javascript
{
  "success": true,
  "data": {
    "id": "mem_123456789",
    "deleted": true
  }
}
```

##### Get Memory Stats
**GET** `/memory/stats`

Get memory service statistics.

**Response:**
```javascript
{
  "success": true,
  "data": {
    "total_items": 1000,
    "total_size": 1024000,
    "tags": {
      "important": 500,
      "work": 300,
      "personal": 200
    },
    "categories": {
      "personal": 400,
      "work": 600
    }
  }
}
```

### 4. Compliance Server API

#### Base URL
```
http://localhost:3003/api/v1
```

#### Authentication
```javascript
const headers = {
  'Authorization': 'Bearer YOUR_JWT_TOKEN',
  'Content-Type': 'application/json'
};
```

#### Endpoints

##### Run Compliance Check
**POST** `/compliance/check`

Run a compliance check on specified targets.

**Request:**
```javascript
{
  "targets": ["filesystem", "postgres", "memory"],
  "rules": ["security", "performance", "compliance"],
  "options": {
    "auto_fix": false,
    "require_approval": true
  }
}
```

**Response:**
```javascript
{
  "success": true,
  "data": {
    "check_id": "comp_123456789",
    "status": "running",
    "targets": ["filesystem", "postgres", "memory"],
    "rules": ["security", "performance", "compliance"],
    "started_at": "2024-01-01T00:00:00Z",
    "estimated_duration": 300
  }
}
```

##### Get Compliance Status
**GET** `/compliance/status/:check_id`

Get the status of a compliance check.

**Request:**
```javascript
{
  "check_id": "comp_123456789"
}
```

**Response:**
```javascript
{
  "success": true,
  "data": {
    "check_id": "comp_123456789",
    "status": "completed",
    "progress": 100,
    "results": {
      "filesystem": {
        "passed": 15,
        "failed": 2,
        "warnings": 3
      },
      "postgres": {
        "passed": 20,
        "failed": 1,
        "warnings": 0
      },
      "memory": {
        "passed": 18,
        "failed": 0,
        "warnings": 2
      }
    },
    "completed_at": "2024-01-01T00:05:00Z"
  }
}
```

##### Get Compliance Report
**GET** `/compliance/report/:check_id`

Get a detailed compliance report.

**Request:**
```javascript
{
  "check_id": "comp_123456789",
  "format": "json"
}
```

**Response:**
```javascript
{
  "success": true,
  "data": {
    "check_id": "comp_123456789",
    "generated_at": "2024-01-01T00:05:00Z",
    "summary": {
      "total_checks": 100,
      "passed": 85,
      "failed": 10,
      "warnings": 5,
      "score": 85
    },
    "details": {
      "filesystem": [
        {
          "rule": "file_permissions",
          "status": "failed",
          "message": "File has incorrect permissions",
          "severity": "high",
          "recommendation": "Fix file permissions"
        }
      ],
      "postgres": [
        {
          "rule": "connection_pool",
          "status": "warning",
          "message": "Connection pool size is optimal",
          "severity": "medium",
          "recommendation": "Monitor connection usage"
        }
      ]
    }
  }
}
```

##### Approve Remediation
**POST** `/compliance/approve`

Approve remediation actions.

**Request:**
```javascript
{
  "check_id": "comp_123456789",
  "actions": ["fix_file_permissions", "optimize_queries"],
  "reason": "Approved for production deployment"
}
```

**Response:**
```javascript
{
  "success": true,
  "data": {
    "check_id": "comp_123456789",
    "approved_actions": ["fix_file_permissions", "optimize_queries"],
    "status": "approved",
    "approved_by": "admin",
    "approved_at": "2024-01-01T00:10:00Z"
  }
}
```

## Integration APIs

### 5. Integration Coordinator API

#### Base URL
```
http://localhost:3004/api/v1
```

#### Authentication
```javascript
const headers = {
  'Authorization': 'Bearer YOUR_JWT_TOKEN',
  'Content-Type': 'application/json'
};
```

#### Endpoints

##### Request Assessment
**POST** `/assessment/request`

Request a compliance assessment.

**Request:**
```javascript
{
  "server_name": "filesystem",
  "assessment_type": "compliance",
  "options": {
    "rules": ["security", "performance"],
    "auto_fix": false
  }
}
```

**Response:**
```javascript
{
  "success": true,
  "data": {
    "request_id": "assess_123456789",
    "status": "pending",
    "server_name": "filesystem",
    "assessment_type": "compliance",
    "options": {
      "rules": ["security", "performance"],
      "auto_fix": false
    },
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

##### Get Assessment Status
**GET** `/assessment/status/:request_id`

Get the status of an assessment request.

**Request:**
```javascript
{
  "request_id": "assess_123456789"
}
```

**Response:**
```javascript
{
  "success": true,
  "data": {
    "request_id": "assess_123456789",
    "status": "completed",
    "assessment": {
      "server_name": "filesystem",
      "assessment_type": "compliance",
      "results": {
        "passed": 15,
        "failed": 2,
        "warnings": 3
      }
    },
    "requires_approval": true,
    "created_at": "2024-01-01T00:00:00Z",
    "completed_at": "2024-01-01T00:05:00Z"
  }
}
```

##### Request Remediation
**POST** `/remediation/propose`

Request a remediation proposal.

**Request:**
```javascript
{
  "assessment_id": "assess_123456789",
  "actions": ["fix_file_permissions", "optimize_queries"]
}
```

**Response:**
```javascript
{
  "success": true,
  "data": {
    "proposal_id": "remed_123456789",
    "assessment_id": "assess_123456789",
    "actions": [
      {
        "action": "fix_file_permissions",
        "description": "Fix file permissions",
        "risk": "low",
        "estimated_time": 60
      }
    ],
    "requires_approval": true,
    "created_at": "2024-01-01T00:10:00Z"
  }
}
```

## WebSocket APIs

### 6. Real-time Communication

#### WebSocket Connection
```javascript
const socket = new WebSocket('ws://localhost:3005');

socket.onopen = () => {
  console.log('WebSocket connected');
};

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received message:', data);
};

socket.onclose = () => {
  console.log('WebSocket disconnected');
};

socket.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

#### WebSocket Events

##### Memory Update
```javascript
// Server sends memory update
{
  "type": "memory_update",
  "data": {
    "id": "mem_123456789",
    "action": "created",
    "content": "New memory item"
  }
}
```

##### Compliance Update
```javascript
// Server sends compliance update
{
  "type": "compliance_update",
  "data": {
    "check_id": "comp_123456789",
    "status": "completed",
    "progress": 100
  }
}
```

##### System Alert
```javascript
// Server sends system alert
{
  "type": "system_alert",
  "data": {
    "level": "warning",
    "message": "High memory usage detected",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

## Error Handling

### Error Response Format
```javascript
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "details": {
      "field": "Additional error details"
    },
    "retryable": false
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "req_123456789"
}
```

### Common Error Codes

#### Authentication Errors
- `AUTH_REQUIRED`: Authentication required
- `INVALID_TOKEN`: Invalid or expired token
- `INSUFFICIENT_PERMISSIONS`: Insufficient permissions

#### Validation Errors
- `INVALID_REQUEST`: Invalid request format
- `MISSING_PARAMETER`: Required parameter missing
- `INVALID_PARAMETER`: Invalid parameter value

#### System Errors
- `INTERNAL_ERROR`: Internal server error
- `SERVICE_UNAVAILABLE`: Service temporarily unavailable
- `TIMEOUT`: Request timeout

#### Business Logic Errors
- `NOT_FOUND`: Resource not found
- `CONFLICT`: Resource conflict
- `FORBIDDEN`: Action forbidden

## Rate Limiting

### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

### Rate Limit Rules
- **Authentication endpoints**: 5 requests per minute
- **Read operations**: 100 requests per minute
- **Write operations**: 10 requests per minute
- **WebSocket connections**: 1 connection per client

## Webhooks

### Webhook Configuration
```javascript
// Configure webhook
const webhookConfig = {
  url: "https://your-webhook-url.com",
  events: ["memory_created", "compliance_completed", "system_alert"],
  secret: "your-webhook-secret"
};
```

### Webhook Events

#### Memory Created
```javascript
{
  "event": "memory_created",
  "data": {
    "id": "mem_123456789",
    "content": "New memory item",
    "tags": ["important"],
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### Compliance Completed
```javascript
{
  "event": "compliance_completed",
  "data": {
    "check_id": "comp_123456789",
    "status": "completed",
    "score": 85,
    "failed_checks": 10
  }
}
```

#### System Alert
```javascript
{
  "event": "system_alert",
  "data": {
    "level": "warning",
    "message": "High memory usage detected",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

## SDKs and Libraries

### JavaScript/Node.js SDK
```javascript
const KiloCodeMCP = require('@kilocode/mcp-sdk');

// Initialize client
const client = new KiloCodeMCP({
  baseURL: 'http://localhost:3000',
  apiKey: 'your-api-key',
  timeout: 30000
});

// Use filesystem API
async function listFiles() {
  try {
    const response = await client.files.list('/path/to/directory');
    console.log(response.data);
  } catch (error) {
    console.error('Error:', error);
  }
}

// Use memory API
async function storeMemory() {
  try {
    const response = await client.memory.store({
      content: 'Important memory item',
      tags: ['important', 'work']
    });
    console.log(response.data);
  } catch (error) {
    console.error('Error:', error);
  }
}
```

### Python SDK
```python
from kilocode_mcp import KiloCodeMCP

# Initialize client
client = KiloCodeMCP(
    base_url='http://localhost:3000',
    api_key='your-api-key',
    timeout=30
)

# Use filesystem API
def list_files():
    try:
        response = client.files.list('/path/to/directory')
        print(response.data)
    except Exception as e:
        print('Error:', e)

# Use memory API
def store_memory():
    try:
        response = client.memory.store({
            'content': 'Important memory item',
            'tags': ['important', 'work']
        })
        print(response.data)
    except Exception as e:
        print('Error:', e)
```

## Testing APIs

### API Testing with curl
```bash
# Test filesystem API
curl -X GET http://localhost:3000/api/v1/files \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"path": "/tmp"}'

# Test memory API
curl -X POST http://localhost:3002/api/v1/memory/store \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test memory", "tags": ["test"]}'

# Test compliance API
curl -X POST http://localhost:3003/api/v1/compliance/check \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"targets": ["filesystem"], "rules": ["security"]}'
```

### API Testing with Postman
1. Create a new collection
2. Add requests for each API endpoint
3. Set up authentication headers
4. Configure environment variables
5. Add tests to each request
6. Run collection tests

## API Best Practices

### Security Best Practices
1. **Always use HTTPS**: Never use HTTP for API communication
2. **Validate all inputs**: Validate all API inputs before processing
3. **Use rate limiting**: Implement rate limiting to prevent abuse
4. **Monitor API usage**: Monitor API usage for suspicious activity
5. **Keep dependencies updated**: Regularly update API dependencies

### Performance Best Practices
1. **Use caching**: Implement caching for frequently accessed data
2. **Optimize queries**: Optimize database queries for performance
3. **Use pagination**: Implement pagination for large datasets
4. **Compress responses**: Use compression for API responses
5. **Monitor performance**: Monitor API performance metrics

### Documentation Best Practices
1. **Document all endpoints**: Document all API endpoints
2. **Provide examples**: Provide code examples for each endpoint
3. **Keep documentation updated**: Keep documentation updated with API changes
4. **Use OpenAPI**: Use OpenAPI specification for API documentation
5. **Provide SDKs**: Provide SDKs for popular programming languages

## Support and Contact Information

### Technical Support
- **Email**: support@kilocode.com
- **Phone**: +1 (555) 123-4567
- **Hours**: 9 AM - 5 PM EST, Monday - Friday

### API Documentation
- **Main Documentation**: [KiloCode API Documentation](https://docs.kilocode.com/api)
- **GitHub Issues**: [KiloCode GitHub](https://github.com/kilocode/kilocode/issues)
- **Community Forum**: [KiloCode Community](https://community.kilocode.com)

### Development Resources
- **API Examples**: [KiloCode API Examples](https://github.com/kilocode/api-examples)
- **SDK Documentation**: [KiloCode SDK Documentation](https://docs.kilocode.com/sdk)
- **Best Practices**: [KiloCode API Best Practices](https://docs.kilocode.com/api-best-practices)

---

*This API documentation is part of the KiloCode MCP Setup and Configuration Architecture Plan and should be reviewed and updated regularly to reflect changes in API design and functionality.*