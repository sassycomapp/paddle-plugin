# MCP Server Communication API Documentation

## Overview

This document provides comprehensive API documentation for MCP (Model Context Protocol) server communication within the KiloCode ecosystem. The documentation covers API endpoints, request/response formats, authentication, and integration patterns, following the **Simple, Robust, Secure** approach.

## API Philosophy

### Key Principles
1. **Simplicity**: Provide clear, intuitive API design
2. **Robustness**: Ensure reliable API communication with proper error handling
3. **Security**: Implement secure API communication with authentication and authorization
4. **Consistency**: Maintain consistent API patterns across all servers
5. **Flexibility**: Support different communication patterns and protocols

### API Types
- **REST API**: HTTP-based RESTful API for server communication
- **WebSocket API**: Real-time communication for live updates
- **gRPC API**: High-performance RPC for internal server communication
- **Event API**: Event-driven communication for asynchronous operations

---

## REST API Documentation

### 1. Authentication API

#### 1.1 Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password123",
  "rememberMe": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 86400,
    "user": {
      "id": "user123",
      "username": "admin",
      "role": "admin",
      "permissions": ["read", "write", "admin"]
    }
  }
}
```

#### 1.2 Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 86400
  }
}
```

#### 1.3 Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

#### 1.4 Get User Profile
```http
GET /api/v1/auth/profile
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "user123",
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "permissions": ["read", "write", "admin"],
    "lastLogin": "2024-01-01T00:00:00.000Z",
    "createdAt": "2024-01-01T00:00:00.000Z"
  }
}
```

### 2. Compliance Server API

#### 2.1 Get Compliance Status
```http
GET /api/v1/compliance/status
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "overallStatus": "compliant",
    "lastCheck": "2024-01-01T00:00:00.000Z",
    "totalChecks": 150,
    "passedChecks": 145,
    "failedChecks": 5,
    "complianceScore": 96.7,
    "servers": [
      {
        "name": "filesystem",
        "status": "compliant",
        "lastCheck": "2024-01-01T00:00:00.000Z",
        "score": 98.5
      },
      {
        "name": "postgres",
        "status": "non-compliant",
        "lastCheck": "2024-01-01T00:00:00.000Z",
        "score": 85.2,
        "issues": [
          {
            "severity": "high",
            "category": "security",
            "description": "SSL certificate expired",
            "recommendation": "Renew SSL certificate"
          }
        ]
      }
    ]
  }
}
```

#### 2.2 Run Compliance Check
```http
POST /api/v1/compliance/check
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "serverName": "filesystem",
  "checkType": "full",
  "options": {
    "includeSecurity": true,
    "includePerformance": true,
    "includeConfiguration": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "checkId": "check123",
    "status": "running",
    "serverName": "filesystem",
    "checkType": "full",
    "startedAt": "2024-01-01T00:00:00.000Z",
    "estimatedDuration": 30000
  }
}
```

#### 2.3 Get Compliance Results
```http
GET /api/v1/compliance/results/{checkId}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "checkId": "check123",
    "status": "completed",
    "serverName": "filesystem",
    "checkType": "full",
    "startedAt": "2024-01-01T00:00:00.000Z",
    "completedAt": "2024-01-01T00:00:30.000Z",
    "duration": 30000,
    "results": {
      "overallScore": 98.5,
      "categories": {
        "security": {
          "score": 100,
          "checks": 20,
          "passed": 20,
          "failed": 0
        },
        "performance": {
          "score": 95,
          "checks": 15,
          "passed": 14,
          "failed": 1
        },
        "configuration": {
          "score": 100,
          "checks": 10,
          "passed": 10,
          "failed": 0
        }
      },
      "issues": [
        {
          "id": "issue123",
          "severity": "medium",
          "category": "performance",
          "title": "High memory usage",
          "description": "Memory usage exceeds 80% threshold",
          "recommendation": "Optimize memory usage or increase resources",
          "affectedComponents": ["filesystem-server"],
          "createdAt": "2024-01-01T00:00:00.000Z"
        }
      ]
    }
  }
}
```

#### 2.4 Get Compliance History
```http
GET /api/v1/compliance/history?serverName=filesystem&limit=10&offset=0
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 50,
    "limit": 10,
    "offset": 0,
    "history": [
      {
        "checkId": "check123",
        "serverName": "filesystem",
        "status": "completed",
        "score": 98.5,
        "startedAt": "2024-01-01T00:00:00.000Z",
        "completedAt": "2024-01-01T00:00:30.000Z"
      },
      {
        "checkId": "check122",
        "serverName": "filesystem",
        "status": "completed",
        "score": 97.2,
        "startedAt": "2024-01-01T23:00:00.000Z",
        "completedAt": "2024-01-01T23:00:25.000Z"
      }
    ]
  }
}
```

### 3. Memory Service API

#### 3.1 Store Memory
```http
POST /api/v1/memory/store
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "content": "Sample memory content",
  "metadata": {
    "type": "text",
    "source": "user-input",
    "tags": ["important", "project"],
    "timestamp": "2024-01-01T00:00:00.000Z"
  },
  "vector": [0.1, 0.2, 0.3, 0.4, 0.5]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "memoryId": "mem123",
    "content": "Sample memory content",
    "metadata": {
      "type": "text",
      "source": "user-input",
      "tags": ["important", "project"],
      "timestamp": "2024-01-01T00:00:00.000Z"
    },
    "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
    "createdAt": "2024-01-01T00:00:00.000Z",
    "updatedAt": "2024-01-01T00:00:00.000Z"
  }
}
```

#### 3.2 Retrieve Memory
```http
GET /api/v1/memory/retrieve/{memoryId}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "memoryId": "mem123",
    "content": "Sample memory content",
    "metadata": {
      "type": "text",
      "source": "user-input",
      "tags": ["important", "project"],
      "timestamp": "2024-01-01T00:00:00.000Z"
    },
    "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
    "createdAt": "2024-01-01T00:00:00.000Z",
    "updatedAt": "2024-01-01T00:00:00.000Z"
  }
}
```

#### 3.3 Search Memory
```http
POST /api/v1/memory/search
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "query": "sample content",
  "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
  "filters": {
    "tags": ["important"],
    "type": "text"
  },
  "limit": 10,
  "threshold": 0.8
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "sample content",
    "results": [
      {
        "memoryId": "mem123",
        "content": "Sample memory content",
        "metadata": {
          "type": "text",
          "source": "user-input",
          "tags": ["important", "project"],
          "timestamp": "2024-01-01T00:00:00.000Z"
        },
        "score": 0.95,
        "distance": 0.05
      },
      {
        "memoryId": "mem124",
        "content": "Another sample content",
        "metadata": {
          "type": "text",
          "source": "system",
          "tags": ["important"],
          "timestamp": "2024-01-01T01:00:00.000Z"
        },
        "score": 0.87,
        "distance": 0.13
      }
    ],
    "total": 2,
    "limit": 10,
    "threshold": 0.8
  }
}
```

#### 3.4 Consolidate Memory
```http
POST /api/v1/memory/consolidate
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "criteria": {
    "timeRange": {
      "start": "2024-01-01T00:00:00.000Z",
      "end": "2024-01-02T00:00:00.000Z"
    },
    "tags": ["important"],
    "similarityThreshold": 0.9
  },
  "options": {
    "mergeStrategy": "weighted",
    "retention": "keep_original"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "consolidationId": "cons123",
    "status": "running",
    "criteria": {
      "timeRange": {
        "start": "2024-01-01T00:00:00.000Z",
        "end": "2024-01-02T00:00:00.000Z"
      },
      "tags": ["important"],
      "similarityThreshold": 0.9
    },
    "estimatedDuration": 60000,
    "startedAt": "2024-01-01T00:00:00.000Z"
  }
}
```

### 4. Server Management API

#### 4.1 Get Server List
```http
GET /api/v1/servers
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "servers": [
      {
        "name": "filesystem",
        "type": "filesystem",
        "status": "running",
        "health": "healthy",
        "lastCheck": "2024-01-01T00:00:00.000Z",
        "version": "1.0.0",
        "description": "Filesystem access server"
      },
      {
        "name": "postgres",
        "type": "database",
        "status": "running",
        "health": "warning",
        "lastCheck": "2024-01-01T00:00:00.000Z",
        "version": "2.0.0",
        "description": "PostgreSQL database server"
      }
    ]
  }
}
```

#### 4.2 Get Server Details
```http
GET /api/v1/servers/{serverName}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "name": "filesystem",
    "type": "filesystem",
    "status": "running",
    "health": "healthy",
    "lastCheck": "2024-01-01T00:00:00.000Z",
    "version": "1.0.0",
    "description": "Filesystem access server",
    "configuration": {
      "rootPath": "/data",
      "allowedPaths": ["/data", "/tmp"],
      "maxFileSize": "100MB",
      "timeout": 30000
    },
    "metrics": {
      "uptime": 86400,
      "requests": 1500,
      "errors": 5,
      "avgResponseTime": 150
    },
    "logs": {
      "info": 1000,
      "warn": 100,
      "error": 5
    }
  }
}
```

#### 4.3 Start Server
```http
POST /api/v1/servers/{serverName}/start
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "serverName": "filesystem",
    "action": "start",
    "status": "initiated",
    "message": "Server start initiated",
    "timestamp": "2024-01-01T00:00:00.000Z"
  }
}
```

#### 4.4 Stop Server
```http
POST /api/v1/servers/{serverName}/stop
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "serverName": "filesystem",
    "action": "stop",
    "status": "initiated",
    "message": "Server stop initiated",
    "timestamp": "2024-01-01T00:00:00.000Z"
  }
}
```

#### 4.5 Restart Server
```http
POST /api/v1/servers/{serverName}/restart
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "serverName": "filesystem",
    "action": "restart",
    "status": "initiated",
    "message": "Server restart initiated",
    "timestamp": "2024-01-01T00:00:00.000Z"
  }
}
```

### 5. Monitoring API

#### 5.1 Get Metrics
```http
GET /api/v1/metrics?serverName=filesystem&timeRange=1h
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "serverName": "filesystem",
    "timeRange": "1h",
    "metrics": {
      "cpu": {
        "current": 45.2,
        "average": 42.1,
        "max": 67.8,
        "min": 23.4
      },
      "memory": {
        "current": 2.1,
        "average": 1.9,
        "max": 2.5,
        "min": 1.2
      },
      "disk": {
        "current": 65.4,
        "average": 64.2,
        "max": 67.1,
        "min": 62.3
      },
      "network": {
        "in": 1024000,
        "out": 512000,
        "total": 1536000
      },
      "requests": {
        "total": 1500,
        "successful": 1480,
        "failed": 20,
        "averageResponseTime": 150
      }
    },
    "timestamp": "2024-01-01T00:00:00.000Z"
  }
}
```

#### 5.2 Get Logs
```http
GET /api/v1/logs?serverName=filesystem&level=error&limit=100
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "serverName": "filesystem",
    "level": "error",
    "limit": 100,
    "logs": [
      {
        "id": "log123",
        "timestamp": "2024-01-01T00:00:00.000Z",
        "level": "error",
        "message": "Failed to read file: /data/test.txt",
        "details": {
          "error": "ENOENT: no such file or directory",
          "stack": "Error: ENOENT: no such file or directory..."
        },
        "metadata": {
          "server": "filesystem",
          "requestId": "req123"
        }
      }
    ],
    "total": 5
  }
}
```

#### 5.3 Get Health Status
```http
GET /api/v1/health
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "overall": "healthy",
    "timestamp": "2024-01-01T00:00:00.000Z",
    "components": {
      "database": {
        "status": "healthy",
        "responseTime": 15,
        "lastCheck": "2024-01-01T00:00:00.000Z"
      },
      "redis": {
        "status": "healthy",
        "responseTime": 5,
        "lastCheck": "2024-01-01T00:00:00.000Z"
      },
      "filesystem": {
        "status": "healthy",
        "responseTime": 25,
        "lastCheck": "2024-01-01T00:00:00.000Z"
      },
      "compliance": {
        "status": "warning",
        "responseTime": 100,
        "lastCheck": "2024-01-01T00:00:00.000Z",
        "issues": ["High memory usage"]
      }
    }
  }
}
```

---

## WebSocket API Documentation

### 1. Connection Setup

#### 1.1 WebSocket Connection
```javascript
const socket = new WebSocket('wss://api.kilocode.com/ws');

socket.onopen = function(event) {
  console.log('WebSocket connection established');
  
  // Authenticate
  socket.send(JSON.stringify({
    type: 'auth',
    token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
  }));
};

socket.onmessage = function(event) {
  const message = JSON.parse(event.data);
  console.log('Received message:', message);
  
  switch(message.type) {
    case 'auth_success':
      console.log('Authentication successful');
      break;
    case 'compliance_update':
      handleComplianceUpdate(message.data);
      break;
    case 'memory_update':
      handleMemoryUpdate(message.data);
      break;
    case 'server_status':
      handleServerStatus(message.data);
      break;
  }
};

socket.onclose = function(event) {
  console.log('WebSocket connection closed');
};

socket.onerror = function(error) {
  console.error('WebSocket error:', error);
};
```

#### 1..2 Authentication
```javascript
// Send authentication message
socket.send(JSON.stringify({
  type: 'auth',
  token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
}));

// Listen for authentication response
socket.onmessage = function(event) {
  const message = JSON.parse(event.data);
  if (message.type === 'auth_success') {
    console.log('Authentication successful');
  } else if (message.type === 'auth_error') {
    console.error('Authentication failed:', message.error);
  }
};
```

### 2. Real-time Updates

#### 2.1 Compliance Updates
```javascript
// Subscribe to compliance updates
socket.send(JSON.stringify({
  type: 'subscribe',
  channel: 'compliance'
}));

// Handle compliance updates
socket.onmessage = function(event) {
  const message = JSON.parse(event.data);
  if (message.type === 'compliance_update') {
    const update = message.data;
    console.log('Compliance update:', update);
    
    // Update UI
    updateComplianceStatus(update.serverName, update.status, update.score);
  }
};
```

#### 2.2 Memory Updates
```javascript
// Subscribe to memory updates
socket.send(JSON.stringify({
  type: 'subscribe',
  channel: 'memory'
}));

// Handle memory updates
socket.onmessage = function(event) {
  const message = JSON.parse(event.data);
  if (message.type === 'memory_update') {
    const update = message.data;
    console.log('Memory update:', update);
    
    // Update memory list
    addMemoryToList(update.memory);
  }
};
```

#### 2.3 Server Status Updates
```javascript
// Subscribe to server status updates
socket.send(JSON.stringify({
  type: 'subscribe',
  channel: 'server_status'
}));

// Handle server status updates
socket.onmessage = function(event) {
  const message = JSON.parse(event.data);
  if (message.type === 'server_status') {
    const update = message.data;
    console.log('Server status update:', update);
    
    // Update server status in UI
    updateServerStatus(update.serverName, update.status, update.health);
  }
};
```

### 3. Commands

#### 3.1 Send Command
```javascript
// Send command to server
socket.send(JSON.stringify({
  type: 'command',
  command: 'start_server',
  serverName: 'filesystem',
  parameters: {
    timeout: 30000
  }
}));

// Handle command response
socket.onmessage = function(event) {
  const message = JSON.parse(event.data);
  if (message.type === 'command_response') {
    const response = message.data;
    console.log('Command response:', response);
    
    if (response.success) {
      console.log('Command executed successfully');
    } else {
      console.error('Command failed:', response.error);
    }
  }
};
```

#### 3.2 Request Real-time Data
```javascript
// Request real-time metrics
socket.send(JSON.stringify({
  type: 'request',
  request: 'metrics',
  serverName: 'filesystem',
  interval: 5000
}));

// Handle real-time metrics
socket.onmessage = function(event) {
  const message = JSON.parse(event.data);
  if (message.type === 'metrics') {
    const metrics = message.data;
    console.log('Real-time metrics:', metrics);
    
    // Update metrics display
    updateMetricsDisplay(metrics);
  }
};
```

---

## gRPC API Documentation

### 1. Service Definitions

#### 1.1 Compliance Service
```protobuf
syntax = "proto3";

package compliance;

service ComplianceService {
  rpc GetComplianceStatus (GetComplianceStatusRequest) returns (ComplianceStatusResponse);
  rpc RunComplianceCheck (RunComplianceCheckRequest) returns (ComplianceCheckResponse);
  rpc GetComplianceResults (GetComplianceResultsRequest) returns (ComplianceResultsResponse);
  rpc GetComplianceHistory (GetComplianceHistoryRequest) returns (ComplianceHistoryResponse);
}

message GetComplianceStatusRequest {
  string server_name = 1;
}

message ComplianceStatusResponse {
  bool success = 1;
  ComplianceStatus status = 2;
}

message ComplianceStatus {
  string overall_status = 1;
  string last_check = 2;
  int32 total_checks = 3;
  int32 passed_checks = 4;
  int32 failed_checks = 5;
  double compliance_score = 6;
  repeated ServerStatus servers = 7;
}

message ServerStatus {
  string name = 1;
  string status = 2;
  string last_check = 3;
  double score = 4;
  repeated Issue issues = 5;
}

message Issue {
  string id = 1;
  string severity = 2;
  string category = 3;
  string description = 4;
  string recommendation = 5;
}

message RunComplianceCheckRequest {
  string server_name = 1;
  string check_type = 2;
  CheckOptions options = 3;
}

message CheckOptions {
  bool include_security = 1;
  bool include_performance = 2;
  bool include_configuration = 3;
}

message ComplianceCheckResponse {
  bool success = 1;
  ComplianceCheck check = 2;
}

message ComplianceCheck {
  string check_id = 1;
  string status = 2;
  string server_name = 3;
  string check_type = 4;
  string started_at = 5;
  int32 estimated_duration = 6;
}

message GetComplianceResultsRequest {
  string check_id = 1;
}

message ComplianceResultsResponse {
  bool success = 1;
  ComplianceResults results = 2;
}

message ComplianceResults {
  string check_id = 1;
  string status = 2;
  string server_name = 3;
  string check_type = 4;
  string started_at = 5;
  string completed_at = 6;
  int32 duration = 7;
  double overall_score = 8;
  CategoryResults categories = 9;
  repeated Issue issues = 10;
}

message CategoryResults {
  SecurityResults security = 1;
  PerformanceResults performance = 2;
  ConfigurationResults configuration = 3;
}

message SecurityResults {
  double score = 1;
  int32 checks = 2;
  int32 passed = 3;
  int32 failed = 4;
}

message PerformanceResults {
  double score = 1;
  int32 checks = 2;
  int32 passed = 3;
  int32 failed = 4;
}

message ConfigurationResults {
  double score = 1;
  int32 checks = 2;
  int32 passed = 3;
  int32 failed = 4;
}

message GetComplianceHistoryRequest {
  string server_name = 1;
  int32 limit = 2;
  int32 offset = 3;
}

message ComplianceHistoryResponse {
  bool success = 1;
  ComplianceHistory history = 2;
}

message ComplianceHistory {
  int32 total = 1;
  int32 limit = 2;
  int32 offset = 3;
  repeated ComplianceCheckItem history = 4;
}

message ComplianceCheckItem {
  string check_id = 1;
  string server_name = 2;
  string status = 3;
  double score = 4;
  string started_at = 5;
  string completed_at = 6;
}
```

#### 1.2 Memory Service
```protobuf
syntax = "proto3";

package memory;

service MemoryService {
  rpc StoreMemory (StoreMemoryRequest) returns (StoreMemoryResponse);
  rpc RetrieveMemory (RetrieveMemoryRequest) returns (RetrieveMemoryResponse);
  rpc SearchMemory (SearchMemoryRequest) returns (SearchMemoryResponse);
  rpc ConsolidateMemory (ConsolidateMemoryRequest) returns (ConsolidateMemoryResponse);
}

message StoreMemoryRequest {
  string content = 1;
  MemoryMetadata metadata = 2;
  repeated float vector = 3;
}

message MemoryMetadata {
  string type = 1;
  string source = 2;
  repeated string tags = 3;
  string timestamp = 4;
}

message StoreMemoryResponse {
  bool success = 1;
  Memory memory = 2;
}

message Memory {
  string memory_id = 1;
  string content = 2;
  MemoryMetadata metadata = 3;
  repeated float vector = 4;
  string created_at = 5;
  string updated_at = 6;
}

message RetrieveMemoryRequest {
  string memory_id = 1;
}

message RetrieveMemoryResponse {
  bool success = 1;
  Memory memory = 2;
}

message SearchMemoryRequest {
  string query = 1;
  repeated float vector = 2;
  MemoryFilters filters = 3;
  int32 limit = 4;
  double threshold = 5;
}

message MemoryFilters {
  repeated string tags = 1;
  string type = 2;
}

message SearchMemoryResponse {
  bool success = 1;
  SearchResults results = 2;
}

message SearchResults {
  string query = 1;
  repeated SearchResult results = 2;
  int32 total = 3;
  int32 limit = 4;
  double threshold = 5;
}

message SearchResult {
  string memory_id = 1;
  string content = 2;
  MemoryMetadata metadata = 3;
  double score = 4;
  double distance = 5;
}

message ConsolidateMemoryRequest {
  ConsolidationCriteria criteria = 1;
  ConsolidationOptions options = 2;
}

message ConsolidationCriteria {
  TimeRange time_range = 1;
  repeated string tags = 2;
  double similarity_threshold = 3;
}

message TimeRange {
  string start = 1;
  string end = 2;
}

message ConsolidationOptions {
  string merge_strategy = 1;
  string retention = 2;
}

message ConsolidateMemoryResponse {
  bool success = 1;
  Consolidation consolidation = 2;
}

message Consolidation {
  string consolidation_id = 1;
  string status = 2;
  ConsolidationCriteria criteria = 3;
  int32 estimated_duration = 4;
  string started_at = 5;
}
```

### 2. Client Implementation

#### 2.1 Node.js Client
```javascript
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');

// Load proto file
const packageDefinition = protoLoader.loadSync('./compliance.proto', {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
});

const complianceProto = grpc.loadPackageDefinition(packageDefinition).compliance;

// Create client
const client = new complianceProto.ComplianceService(
  'localhost:50051',
  grpc.credentials.createInsecure()
);

// Get compliance status
client.getComplianceStatus({ server_name: 'filesystem' }, (error, response) => {
  if (error) {
    console.error('Error:', error);
    return;
  }
  
  console.log('Compliance Status:', response.status);
});

// Run compliance check
client.runComplianceCheck({
  server_name: 'filesystem',
  check_type: 'full',
  options: {
    include_security: true,
    include_performance: true,
    include_configuration: true
  }
}, (error, response) => {
  if (error) {
    console.error('Error:', error);
    return;
  }
  
  console.log('Compliance Check:', response.check);
});
```

#### 2.2 Python Client
```python
import grpc
import compliance_pb2
import compliance_pb2_grpc

# Create channel
channel = grpc.insecure_channel('localhost:50051')

# Create client
stub = compliance_pb2_grpc.ComplianceServiceStub(channel)

# Get compliance status
request = compliance_pb2.GetComplianceStatusRequest(server_name='filesystem')
response = stub.GetComplianceStatus(request)
print(f'Compliance Status: {response.status}')

# Run compliance check
request = compliance_pb2.RunComplianceCheckRequest(
    server_name='filesystem',
    check_type='full',
    options=compliance_pb2.CheckOptions(
        include_security=True,
        include_performance=True,
        include_configuration=True
    )
)
response = stub.RunComplianceCheck(request)
print(f'Compliance Check: {response.check}')
```

---

## Error Handling

### 1. Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "details": {
      "field": "Additional error details"
    },
    "retryable": true
  },
  "timestamp": "2024-01-01T00:00:00.000Z",
  "requestId": "req123"
}
```

### 2. Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `AUTH_REQUIRED` | Authentication required | 401 |
| `AUTH_FAILED` | Authentication failed | 401 |
| `FORBIDDEN` | Insufficient permissions | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `VALIDATION_ERROR` | Input validation failed | 400 |
| `INTERNAL_ERROR` | Internal server error | 500 |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable | 503 |
| `TIMEOUT` | Request timeout | 408 |
| `RATE_LIMITED` | Rate limit exceeded | 429 |

### 3. Error Handling Examples

#### 3.1 Authentication Error
```javascript
// Handle authentication error
fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'admin',
    password: 'wrongpassword'
  })
})
.then(response => {
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
})
.then(data => {
  if (!data.success) {
    console.error('Authentication failed:', data.error);
    // Show error message to user
    showError(data.error.message);
  } else {
    // Handle successful authentication
    handleLoginSuccess(data.data);
  }
})
.catch(error => {
  console.error('Error:', error);
  showError('An error occurred during authentication');
});
```

#### 3.2 Validation Error
```javascript
// Handle validation error
fetch('/api/v1/memory/store', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
  },
  body: JSON.stringify({
    content: '', // Empty content
    metadata: {
      type: 'text',
      source: 'user-input'
    }
  })
})
.then(response => {
  if (!response.ok) {
    return response.json().then(errorData => {
      throw new Error(errorData.error.message);
    });
  }
  return response.json();
})
.then(data => {
  if (data.success) {
    // Handle successful storage
    handleMemoryStored(data.data);
  }
})
.catch(error => {
  console.error('Validation error:', error);
  showError(error.message);
});
```

---

## Authentication and Authorization

### 1. Authentication Methods

#### 1.1 JWT Token Authentication
```javascript
// Get JWT token
const loginResponse = await fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'admin',
    password: 'password123'
  })
});

const loginData = await loginResponse.json();
const token = loginData.data.token;

// Use token in requests
const response = await fetch('/api/v1/compliance/status', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

#### 1.2 API Key Authentication
```javascript
// Use API key in headers
const response = await fetch('/api/v1/compliance/status', {
  headers: {
    'X-API-Key': 'your-api-key-here',
    'Content-Type': 'application/json'
  }
});
```

### 2. Authorization Levels

| Role | Permissions | Description |
|------|-------------|-------------|
| `admin` | All permissions | Full system access |
| `user` | Read, Write | Standard user access |
| `viewer` | Read | Read-only access |
| `guest` | Limited read | Restricted access |

### 3. Permission Checks

```javascript
// Check user permissions
function checkPermission(requiredPermission) {
  const user = getCurrentUser();
  return user.permissions.includes(requiredPermission);
}

// Example usage
if (checkPermission('admin')) {
  // Show admin controls
  showAdminControls();
} else {
  // Hide admin controls
  hideAdminControls();
}
```

---

## Rate Limiting

### 1. Rate Limit Headers

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

### 2. Rate Limit Handling

```javascript
// Handle rate limiting
async function makeApiRequest(url, options) {
  try {
    const response = await fetch(url, options);
    
    // Check rate limit headers
    const remaining = response.headers.get('X-RateLimit-Remaining');
    const reset = response.headers.get('X-RateLimit-Reset');
    
    if (remaining === '0') {
      const resetTime = new Date(reset * 1000);
      const waitTime = resetTime - Date.now();
      
      console.log(`Rate limit exceeded. Waiting ${waitTime}ms...`);
      await new Promise(resolve => setTimeout(resolve, waitTime));
      
      // Retry request
      return makeApiRequest(url, options);
    }
    
    return response;
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}
```

---

## Support and Contact Information

### Technical Support
- **Email**: support@kilocode.com
- **Phone**: +1 (555) 123-4567
- **Hours**: 24/7 for production support

### API Support
- **API Documentation**: [KiloCode API Documentation](https://kilocode.com/api)
- **API Explorer**: [KiloCode API Explorer](https://api.kilocode.com/explorer)
- **Community Forum**: [KiloCode Community](https://community.kilocode.com)

### Documentation Resources
- **REST API Guide**: [KiloCode REST API Guide](https://kilocode.com/docs/rest-api)
- **WebSocket API Guide**: [KiloCode WebSocket API Guide](https://kilocode.com/docs/websocket-api)
- **gRPC API Guide**: [KiloCode gRPC API Guide](https://kilocode.com/docs/grpc-api)

---

*This API documentation is part of the KiloCode MCP Setup and Configuration Architecture Plan and should be reviewed and updated regularly to reflect changes in API design and best practices.*