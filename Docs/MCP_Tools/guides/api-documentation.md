# API Documentation for MCP Server Communication

## Overview

This document provides comprehensive API documentation for MCP (Model Context Protocol) server communication within the KiloCode ecosystem. The API documentation follows the **Simple, Robust, Secure** approach and ensures proper integration between MCP servers.

## API Philosophy

### Key Principles
1. **Simplicity**: Use simple, intuitive API endpoints
2. **Robustness**: Implement proper error handling and validation
3. **Security**: Secure API by default with authentication and authorization
4. **Consistency**: Maintain consistent API patterns across all servers
5. **Documentation**: Provide comprehensive API documentation

### API Design Standards
- **RESTful Design**: Follow REST principles for API design
- **JSON Format**: Use JSON for request and response bodies
- **HTTP Status Codes**: Use appropriate HTTP status codes
- **Error Handling**: Implement consistent error handling
- **Authentication**: Use JWT tokens for authentication
- **Rate Limiting**: Implement rate limiting to prevent abuse

## API Authentication

### 1. JWT Authentication

#### JWT Token Structure
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user123",
    "iat": 1516239022,
    "exp": 1516242622,
    "roles": ["admin", "user"],
    "permissions": ["read", "write"]
  },
  "signature": "signature"
}
```

#### Authentication Flow
```bash
# 1. Login to get JWT token
curl -X POST http://localhost:3003/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Response
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "token_type": "Bearer"
}

# 2. Use JWT token for authenticated requests
curl -X GET http://localhost:3003/api/v1/files \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### JWT Validation
```javascript
// JWT validation function
function validateJWT(token) {
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    return { valid: true, payload: decoded };
  } catch (error) {
    return { valid: false, error: error.message };
  }
}
```

### 2. API Key Authentication

#### API Key Structure
```
kcp_abcdefghijklmnopqrstuvwxyz123456
```

#### API Key Usage
```bash
# Use API key in header
curl -X GET http://localhost:3003/api/v1/files \
  -H "X-API-Key: kcp_abcdefghijklmnopqrstuvwxyz123456"

# Use API key in query parameter
curl -X GET "http://localhost:3003/api/v1/files?api_key=kcp_abcdefghijklmnopqrstuvwxyz123456"
```

## API Endpoints

### 1. Filesystem Server API

#### Base URL: `http://localhost:3000`

#### 1.1 File Operations

##### `GET /api/v1/files`
**Description**: List files in directory
**Authentication**: Required
**Authorization**: Read permission
**Parameters**:
- `path` (string, required): Directory path
- `recursive` (boolean, optional): Include subdirectories (default: false)
- `include_hidden` (boolean, optional): Include hidden files (default: false)

**Request**:
```bash
curl -X GET "http://localhost:3000/api/v1/files?path=/opt/kilocode/mcp-servers" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response**:
```json
{
  "path": "/opt/kilocode/mcp-servers",
  "files": [
    {
      "name": "mcp-compliance-server",
      "type": "directory",
      "size": 4096,
      "modified": "2024-01-01T12:00:00Z",
      "permissions": "755"
    },
    {
      "name": "config.json",
      "type": "file",
      "size": 1024,
      "modified": "2024-01-01T12:00:00Z",
      "permissions": "644"
    }
  ]
}
```

##### `GET /api/v1/files/{filename}`
**Description**: Get file content
**Authentication**: Required
**Authorization**: Read permission
**Parameters**:
- `filename` (string, required): File name

**Request**:
```bash
curl -X GET "http://localhost:3000/api/v1/files/config.json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response**:
```json
{
  "filename": "config.json",
  "content": "{\n  \"mcpServers\": {\n    \"filesystem\": {\n      \"command\": \"npx\",\n      \"args\": [\"-y\", \"@modelcontextprotocol/server-filesystem\"]\n    }\n  }\n}",
  "size": 1024,
  "modified": "2024-01-01T12:00:00Z"
}
```

##### `POST /api/v1/files`
**Description**: Create or update file
**Authentication**: Required
**Authorization**: Write permission
**Parameters**:
- `path` (string, required): File path
- `content` (string, required): File content
- `create_dirs` (boolean, optional): Create directories if they don't exist (default: false)

**Request**:
```bash
curl -X POST "http://localhost:3000/api/v1/files" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/opt/kilocode/mcp-servers/new-file.txt",
    "content": "Hello, World!",
    "create_dirs": true
  }'
```

**Response**:
```json
{
  "success": true,
  "message": "File created successfully",
  "path": "/opt/kilocode/mcp-servers/new-file.txt",
  "size": 13
}
```

##### `DELETE /api/v1/files/{filename}`
**Description**: Delete file
**Authentication**: Required
**Authorization**: Write permission
**Parameters**:
- `filename` (string, required): File name

**Request**:
```bash
curl -X DELETE "http://localhost:3000/api/v1/files/new-file.txt" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response**:
```json
{
  "success": true,
  "message": "File deleted successfully"
}
```

#### 1.2 Directory Operations

##### `GET /api/v1/directories`
**Description**: List directories
**Authentication**: Required
**Authorization**: Read permission
**Parameters**:
- `path` (string, required): Base path
- `recursive` (boolean, optional): Include subdirectories (default: false)

**Request**:
```bash
curl -X GET "http://localhost:3000/api/v1/directories?path=/opt/kilocode/mcp-servers" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response**:
```json
{
  "path": "/opt/kilocode/mcp-servers",
  "directories": [
    {
      "name": "mcp-compliance-server",
      "path": "/opt/kilocode/mcp-servers/mcp-compliance-server",
      "size": 4096,
      "modified": "2024-01-01T12:00:00Z",
      "files_count": 10
    }
  ]
}
```

##### `POST /api/v1/directories`
**Description**: Create directory
**Authentication**: Required
**Authorization**: Write permission
**Parameters**:
- `path` (string, required): Directory path
- `recursive` (boolean, optional): Create parent directories (default: false)

**Request**:
```bash
curl -X POST "http://localhost:3000/api/v1/directories" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/opt/kilocode/mcp-servers/new-directory",
    "recursive": true
  }'
```

**Response**:
```json
{
  "success": true,
  "message": "Directory created successfully",
  "path": "/opt/kilocode/mcp-servers/new-directory"
}
```

##### `DELETE /api/v1/directories/{dirname}`
**Description**: Delete directory
**Authentication**: Required
**Authorization**: Write permission
**Parameters**:
- `dirname` (string, required): Directory name
- `recursive` (boolean, optional): Delete recursively (default: false)

**Request**:
```bash
curl -X DELETE "http://localhost:3000/api/v1/directories/new-directory?recursive=true" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response**:
```json
{
  "success": true,
  "message": "Directory deleted successfully"
}
```

### 2. PostgreSQL Server API

#### Base URL: `http://localhost:3001`

#### 2.1 Database Operations

##### `GET /api/v1/tables`
**Description**: List database tables
**Authentication**: Required
**Authorization**: Read permission
**Parameters**:
- `schema` (string, optional): Schema name (default: public)

**Request**:
```bash
curl -X GET "http://localhost:3001/api/v1/tables" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response**:
```json
{
  "schema": "public",
  "tables": [
    {
      "name": "users",
      "type": "BASE TABLE",
      "owner": "mcp_user",
      "size": 8192
    },
    {
      "name": "compliance_logs",
      "type": "BASE TABLE",
      "owner": "mcp_user",
      "size": 16384
    }
  ]
}
```

##### `GET /api/v1/tables/{table_name}/schema`
**Description**: Get table schema
**Authentication**: Required
**Authorization**: Read permission
**Parameters**:
- `table_name` (string, required): Table name

**Request**:
```bash
curl -X GET "http://localhost:3001/api/v1/tables/users/schema" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response**:
```json
{
  "table_name": "users",
  "columns": [
    {
      "name": "id",
      "type": "integer",
      "nullable": false,
      "default": null
    },
    {
      "name": "username",
      "type": "character varying(50)",
      "nullable": false,
      "default": null
    },
    {
      "name": "email",
      "type": "character varying(100)",
      "nullable": true,
      "default": null
    }
  ],
  "indexes": [
    {
      "name": "users_pkey",
      "columns": ["id"],
      "unique": true
    }
  ]
}
```

##### `POST /api/v1/query`
**Description**: Execute SQL query
**Authentication**: Required
**Authorization**: Execute permission
**Parameters**:
- `query` (string, required): SQL query
- `params` (array, optional): Query parameters
- `limit` (integer, optional): Result limit (default: 1000)

**Request**:
```bash
curl -X POST "http://localhost:3001/api/v1/query" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT * FROM users WHERE username = $1",
    "params": ["admin"],
    "limit": 10
  }'
```

**Response**:
```json
{
  "query": "SELECT * FROM users WHERE username = $1",
  "params": ["admin"],
  "result": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@kilocode.com"
    }
  ],
  "row_count": 1,
  "execution_time": 0.023
}
```

##### `POST /api/v1/transaction`
**Description**: Execute transaction
**Authentication**: Required
**Authorization**: Execute permission
**Parameters**:
- `queries` (array, required): Array of queries
- `params` (array, optional): Parameters for each query

**Request**:
```bash
curl -X POST "http://localhost:3001/api/v1/transaction" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "queries": [
      "INSERT INTO users (username, email) VALUES ($1, $2)",
      "UPDATE compliance_logs SET status = $1 WHERE user_id = $2"
    ],
    "params": [
      ["newuser", "newuser@kilocode.com"],
      ["completed", 1]
    ]
  }'
```

**Response**:
```json
{
  "success": true,
  "message": "Transaction completed successfully",
  "affected_rows": 2,
  "execution_time": 0.045
}
```

### 3. Memory Service API

#### Base URL: `http://localhost:3002`

#### 3.1 Memory Operations

##### `POST /api/v1/memory/store`
**Description**: Store memory item
**Authentication**: Required
**Authorization**: Write permission
**Parameters**:
- `content` (string, required): Memory content
- `tags` (array, optional): Memory tags
- `metadata` (object, optional): Additional metadata
- `ttl` (integer, optional): Time to live in seconds

**Request**:
```bash
curl -X POST "http://localhost:3002/api/v1/memory/store" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This is a memory item",
    "tags": ["important", "configuration"],
    "metadata": {
      "source": "filesystem",
      "priority": "high"
    },
    "ttl": 3600
  }'
```

**Response**:
```json
{
  "success": true,
  "memory_id": "mem_1234567890",
  "content": "This is a memory item",
  "tags": ["important", "configuration"],
  "metadata": {
    "source": "filesystem",
    "priority": "high"
  },
  "created_at": "2024-01-01T12:00:00Z",
  "expires_at": "2024-01-01T13:00:00Z"
}
```

##### `GET /api/v1/memory/retrieve/{memory_id}`
**Description**: Retrieve memory item
**Authentication**: Required
**Authorization**: Read permission
**Parameters**:
- `memory_id` (string, required): Memory ID

**Request**:
```bash
curl -X GET "http://localhost:3002/api/v1/memory/retrieve/mem_1234567890" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response**:
```json
{
  "memory_id": "mem_1234567890",
  "content": "This is a memory item",
  "tags": ["important", "configuration"],
  "metadata": {
    "source": "filesystem",
    "priority": "high"
  },
  "created_at": "2024-01-01T12:00:00Z",
  "expires_at": "2024-01-01T13:00:00Z"
}
```

##### `POST /api/v1/memory/search`
**Description**: Search memory items
**Authentication**: Required
**Authorization**: Read permission
**Parameters**:
- `query` (string, required): Search query
- `tags` (array, optional): Filter by tags
- `limit` (integer, optional): Result limit (default: 100)
- `offset` (integer, optional): Result offset (default: 0)

**Request**:
```bash
curl -X POST "http://localhost:3002/api/v1/memory/search" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "query": "configuration",
    "tags": ["important"],
    "limit": 10,
    "offset": 0
  }'
```

**Response**:
```json
{
  "query": "configuration",
  "results": [
    {
      "memory_id": "mem_1234567890",
      "content": "This is a memory item",
      "tags": ["important", "configuration"],
      "score": 0.95,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total_count": 1,
  "limit": 10,
  "offset": 0
}
```

##### `DELETE /api/v1/memory/{memory_id}`
**Description**: Delete memory item
**Authentication**: Required
**Authorization**: Write permission
**Parameters**:
- `memory_id` (string, required): Memory ID

**Request**:
```bash
curl -X DELETE "http://localhost:3002/api/v1/memory/mem_1234567890" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response**:
```json
{
  "success": true,
  "message": "Memory item deleted successfully"
}
```

#### 3.2 Memory Statistics

##### `GET /api/v1/memory/stats`
**Description**: Get memory statistics
**Authentication**: Required
**Authorization**: Read permission
**Parameters**: None

**Request**:
```bash
curl -X GET "http://localhost:3002/api/v1/memory/stats" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response**:
```json
{
  "total_items": 1000,
  "total_size": 10485760,
  "average_size": 10485,
  "tags": {
    "important": 500,
    "configuration": 300,
    "system": 200
  },
  "created_today": 50,
  "expires_today": 25,
  "memory_usage": "75%"
}
```

### 4. Compliance Server API

#### Base URL: `http://localhost:3003`

#### 4.1 Compliance Operations

##### `POST /api/v1/compliance/check`
**Description**: Run compliance check
**Authentication**: Required
**Authorization**: Execute permission
**Parameters**:
- `targets` (array, required): Target servers to check
- `rules` (array, optional): Specific rules to check (default: all)
- `auto_fix` (boolean, optional): Auto-fix issues (default: false)
- `require_approval` (boolean, optional): Require approval for fixes (default: true)

**Request**:
```bash
curl -X POST "http://localhost:3003/api/v1/compliance/check" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "targets": ["filesystem", "postgres"],
    "rules": ["SEC-001", "SEC-002"],
    "auto_fix": false,
    "require_approval": true
  }'
```

**Response**:
```json
{
  "check_id": "check_1234567890",
  "targets": ["filesystem", "postgres"],
  "rules": ["SEC-001", "SEC-002"],
  "status": "completed",
  "results": [
    {
      "rule_id": "SEC-001",
      "rule_name": "Secure File Permissions",
      "status": "passed",
      "message": "All files have secure permissions"
    },
    {
      "rule_id": "SEC-002",
      "rule_name": "Secure Directory Permissions",
      "status": "failed",
      "message": "Some directories have insecure permissions",
      "remediation": {
        "command": "chmod 755 /opt/kilocode/mcp-servers/*",
        "description": "Set secure directory permissions"
      }
    }
  ],
  "summary": {
    "total_rules": 2,
    "passed": 1,
    "failed": 1,
    "compliance_score": 50
  },
  "started_at": "2024-01-01T12:00:00Z",
  "completed_at": "2024-01-01T12:00:30Z"
}
```

##### `GET /api/v1/compliance/check/{check_id}`
**Description**: Get compliance check status
**Authentication**: Required
**Authorization**: Read permission
**Parameters**:
- `check_id` (string, required): Check ID

**Request**:
```bash
curl -X GET "http://localhost:3003/api/v1/compliance/check/check_1234567890" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response**:
```json
{
  "check_id": "check_1234567890",
  "status": "completed",
  "progress": 100,
  "results": [
    {
      "rule_id": "SEC-001",
      "rule_name": "Secure File Permissions",
      "status": "passed",
      "message": "All files have secure permissions"
    }
  ],
  "summary": {
    "total_rules": 2,
    "passed": 1,
    "failed": 1,
    "compliance_score": 50
  }
}
```

##### `GET /api/v1/compliance/rules`
**Description**: List available compliance rules
**Authentication**: Required
**Authorization**: Read permission
**Parameters**:
- `category` (string, optional): Filter by category
- `severity` (string, optional): Filter by severity

**Request**:
```bash
curl -X GET "http://localhost:3003/api/v1/compliance/rules?category=security&severity=high" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response**:
```json
{
  "rules": [
    {
      "rule_id": "SEC-001",
      "rule_name": "Secure File Permissions",
      "category": "security",
      "severity": "high",
      "description": "Ensure files have secure permissions",
      "target": "filesystem",
      "auto_fix": true,
      "require_approval": false
    },
    {
      "rule_id": "SEC-002",
      "rule_name": "Secure Directory Permissions",
      "category": "security",
      "severity": "high",
      "description": "Ensure directories have secure permissions",
      "target": "filesystem",
      "auto_fix": true,
      "require_approval": false
    }
  ],
  "total_count": 2
}
```

##### `POST /api/v1/compliance/approve`
**Description**: Approve compliance remediation
**Authentication**: Required
**Authorization**: Approve permission
**Parameters**:
- `check_id` (string, required): Check ID
- `rule_id` (string, required): Rule ID
- `approved` (boolean, required): Approval decision
- `comment` (string, optional): Approval comment

**Request**:
```bash
curl -X POST "http://localhost:3003/api/v1/compliance/approve" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "check_id": "check_1234567890",
    "rule_id": "SEC-002",
    "approved": true,
    "comment": "Approved for remediation"
  }'
```

**Response**:
```json
{
  "success": true,
  "message": "Remediation approved",
  "approval_id": "approval_1234567890",
  "status": "approved"
}
```

#### 4.2 Compliance Dashboard

##### `GET /api/v1/compliance/dashboard`
**Description**: Get compliance dashboard
**Authentication**: Required
**Authorization**: Read permission
**Parameters**: None

**Request**:
```bash
curl -X GET "http://localhost:3003/api/v1/compliance/dashboard" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response**:
```json
{
  "overall_compliance": 85,
  "servers": {
    "filesystem": {
      "compliance": 90,
      "last_check": "2024-01-01T12:00:00Z",
      "status": "healthy"
    },
    "postgres": {
      "compliance": 80,
      "last_check": "2024-01-01T11:30:00Z",
      "status": "warning"
    }
  },
  "categories": {
    "security": 95,
    "performance": 75,
    "configuration": 85
  },
  "recent_checks": [
    {
      "check_id": "check_1234567890",
      "timestamp": "2024-01-01T12:00:00Z",
      "compliance_score": 85,
      "status": "completed"
    }
  ]
}
```

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "path",
      "issue": "Path is required"
    },
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_1234567890"
  }
}
```

### Common Error Codes
- `AUTHENTICATION_ERROR`: Authentication failed
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `VALIDATION_ERROR`: Invalid request parameters
- `NOT_FOUND_ERROR`: Resource not found
- `INTERNAL_ERROR`: Internal server error
- `RATE_LIMIT_ERROR`: Rate limit exceeded
- `COMPLIANCE_ERROR`: Compliance check failed

### Error Handling Examples
```bash
# Authentication error
curl -X GET "http://localhost:3000/api/v1/files" \
  -H "Authorization: Bearer invalid_token"

# Response
{
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Invalid or expired token",
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_1234567890"
  }
}

# Authorization error
curl -X GET "http://localhost:3000/api/v1/files" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Response
{
  "error": {
    "code": "AUTHORIZATION_ERROR",
    "message": "Insufficient permissions",
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_1234567890"
  }
}

# Validation error
curl -X GET "http://localhost:3000/api/v1/files"

# Response
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "path",
      "issue": "Path is required"
    },
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_1234567890"
  }
}
```

## Rate Limiting

### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

### Rate Limit Response
```json
{
  "error": {
    "code": "RATE_LIMIT_ERROR",
    "message": "Rate limit exceeded",
    "details": {
      "limit": 100,
      "remaining": 0,
      "reset": 1640995200
    },
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_1234567890"
  }
}
```

## Webhooks

### Webhook Configuration
```json
{
  "webhooks": {
    "compliance_check_completed": {
      "url": "https://your-webhook-url.com/compliance",
      "events": ["check_completed", "check_failed"],
      "secret": "your_webhook_secret"
    }
  }
}
```

### Webhook Payload
```json
{
  "event": "check_completed",
  "check_id": "check_1234567890",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "compliance_score": 85,
    "passed_rules": 17,
    "failed_rules": 3,
    "servers": ["filesystem", "postgres"]
  }
}
```

## SDK Examples

### JavaScript SDK
```javascript
const MCPClient = require('kilocode-mcp-client');

const client = new MCPClient({
  baseURL: 'http://localhost:3000',
  token: 'your_jwt_token'
});

// File operations
async function fileOperations() {
  try {
    const files = await client.files.list('/opt/kilocode/mcp-servers');
    console.log('Files:', files);
    
    const content = await client.files.read('/opt/kilocode/mcp-servers/config.json');
    console.log('Content:', content);
    
    await client.files.write('/opt/kilocode/mcp-servers/new-file.txt', 'Hello, World!');
    console.log('File written successfully');
  } catch (error) {
    console.error('Error:', error.message);
  }
}

// Compliance operations
async function complianceOperations() {
  try {
    const check = await client.compliance.check({
      targets: ['filesystem', 'postgres'],
      rules: ['SEC-001', 'SEC-002']
    });
    console.log('Compliance check:', check);
    
    const dashboard = await client.compliance.dashboard();
    console.log('Dashboard:', dashboard);
  } catch (error) {
    console.error('Error:', error.message);
  }
}
```

### Python SDK
```python
from kilocode_mcp_client import MCPClient

client = MCPClient(
    base_url='http://localhost:3000',
    token='your_jwt_token'
)

# File operations
async def file_operations():
    try:
        files = await client.files.list('/opt/kilocode/mcp-servers')
        print('Files:', files)
        
        content = await client.files.read('/opt/kilocode/mcp-servers/config.json')
        print('Content:', content)
        
        await client.files.write('/opt/kilocode/mcp-servers/new-file.txt', 'Hello, World!')
        print('File written successfully')
    except Exception as e:
        print('Error:', str(e))

# Compliance operations
async def compliance_operations():
    try:
        check = await client.compliance.check({
            'targets': ['filesystem', 'postgres'],
            'rules': ['SEC-001', 'SEC-002']
        })
        print('Compliance check:', check)
        
        dashboard = await client.compliance.dashboard()
        print('Dashboard:', dashboard)
    except Exception as e:
        print('Error:', str(e))
```

## Testing APIs

### API Testing with curl
```bash
# Test filesystem API
curl -X GET "http://localhost:3000/api/v1/files?path=/opt/kilocode/mcp-servers" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json"

# Test PostgreSQL API
curl -X POST "http://localhost:3001/api/v1/query" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM users", "limit": 10}'

# Test memory API
curl -X POST "http://localhost:3002/api/v1/memory/store" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test memory", "tags": ["test"]}'

# Test compliance API
curl -X POST "http://localhost:3003/api/v1/compliance/check" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"targets": ["filesystem"], "rules": ["SEC-001"]}'
```

### API Testing with Postman
1. Create a new collection
2. Add requests for each API endpoint
3. Set up authentication (Bearer token)
4. Configure environment variables
5. Add tests to validate responses
6. Run collection and generate reports

## Support and Contact Information

### Technical Support
- **Email**: support@kilocode.com
- **Phone**: +1 (555) 123-4567
- **Hours**: 24/7 for production support

### Documentation
- **Main Documentation**: [KiloCode Documentation](https://docs.kilocode.com/mcp)
- **GitHub Issues**: [KiloCode GitHub](https://github.com/kilocode/kilocode/issues)
- **Community Forum**: [KiloCode Community](https://community.kilocode.com)

### API Support
- **API Support**: api@kilocode.com
- **SDK Support**: sdk@kilocode.com
- **Integration Support**: integration@kilocode.com

---

*This API documentation is part of the KiloCode MCP Setup and Configuration Architecture Plan and should be reviewed and updated regularly to reflect changes in API endpoints and best practices.*