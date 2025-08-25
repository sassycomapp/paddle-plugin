cp_servers/mcp-integration-coordinator/INTEGRATION_DOCUMENTATION.md</path>
# MCP Integration Coordinator - Integration Documentation

## Overview

This document provides comprehensive documentation for the MCP Integration Coordinator, which serves as the central coordination point between the Generic MCP Installer and the Compliance Server. The integration maintains server independence while providing secure communication, human oversight, and comprehensive audit logging.

## Architecture Overview

### Core Components

1. **Integration Coordinator** - Central hub for server communication
2. **Authentication Service** - Manages user authentication and authorization
3. **Audit Service** - Provides comprehensive audit logging and compliance tracking
4. **Database Service** - Handles data persistence and retrieval
5. **Monitoring Service** - Provides system metrics and health monitoring
6. **Web Interface** - Human oversight dashboard for approval workflows

### Integration Flow

```
Generic MCP Installer → Integration Coordinator ← Compliance Server
       ↑                       ↓                      ↓
   User Actions         Human Oversight        Assessment Data
       ↓                       ↓                      ↓
   Configuration ←─────── Approval Workflow ←─── Remediation Plans
```

## Installation and Setup

### Prerequisites

- Node.js 18+
- PostgreSQL 12+
- npm 8+

### Database Setup

1. Create PostgreSQL database:
```sql
CREATE DATABASE mcp_integration;
CREATE USER mcp_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE mcp_integration TO mcp_user;
```

2. Run database migrations:
```bash
npm run migrate
```

### Installation

1. Navigate to the integration coordinator directory:
```bash
cd mcp_servers/mcp-integration-coordinator
```

2. Install dependencies:
```bash
npm install
```

3. Build the project:
```bash
npm run build
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Configuration

#### Environment Variables

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_DATABASE=mcp_integration
DB_USER=mcp_user
DB_PASSWORD=secure_password

# Server Configuration
PORT=3000
HOST=localhost

# Security
JWT_SECRET=your_jwt_secret_key
SESSION_SECRET=your_session_secret

# Logging
LOG_LEVEL=info
LOG_FILE_PATH=./logs/integration.log

# Monitoring
METRICS_RETENTION_DAYS=30
AUDIT_RETENTION_DAYS=90
```

#### Database Schema

The integration coordinator uses the following main tables:

- `users` - User authentication and authorization
- `audit_logs` - Comprehensive audit trail
- `system_metrics` - System performance metrics
- `approvals` - Approval workflow management
- `assessments` - Assessment tracking
- `remediations` - Remediation action tracking

## Integration Procedures

### 1. Server Registration

#### Generic MCP Installer Registration

The Generic MCP Installer registers with the integration coordinator using the following process:

1. **Authentication**: Installer authenticates using API key or JWT token
2. **Capability Discovery**: Installer reports available tools and capabilities
3. **Configuration Sync**: Installer syncs configuration with coordinator
4. **Status Reporting**: Installer reports operational status

```typescript
// Example registration request
const registration = {
    installerId: 'generic-mcp-installer',
    version: '1.0.0',
    capabilities: ['install_server', 'remove_server', 'generate_config'],
    contact: {
        email: 'admin@example.com',
        phone: '+1234567890'
    }
};
```

#### Compliance Server Registration

The Compliance Server registers using a similar process:

1. **Authentication**: Server authenticates using secure token
2. **Tool Registration**: Server reports available MCP tools
3. **Configuration Validation**: Server validates configuration compatibility
4. **Health Check**: Server reports health status

```typescript
// Example compliance server registration
const registration = {
    serverId: 'compliance-server',
    version: '1.0.0',
    tools: [
        'compliance_assessment',
        'generate_remediation_proposal',
        'execute_remediation'
    ],
    health: {
        status: 'healthy',
        uptime: 3600,
        lastCheck: '2025-08-24T10:00:00Z'
    }
};
```

### 2. Communication Protocols

#### HTTP/HTTPS API

All server communication uses RESTful API endpoints over HTTPS:

```bash
# Base URL
https://integration-coordinator:3000/api/v1

# Endpoints
POST   /servers/register        # Register new server
GET    /servers/{id}            # Get server status
POST   /servers/{id}/ping       # Health check
POST   /assessments             # Request assessment
POST   /remediations/propose    # Propose remediation
POST   /approvals               # Submit approval
GET    /audit/logs              # Get audit logs
GET    /metrics/system          # Get system metrics
```

#### WebSocket (Real-time Updates)

For real-time status updates, WebSocket connections are supported:

```typescript
// WebSocket connection
const ws = new WebSocket('wss://integration-coordinator:3000/ws');

// Subscribe to updates
ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['assessments', 'remediations', 'approvals']
}));
```

### 3. Authentication and Authorization

#### JWT Token Authentication

All API requests require JWT authentication:

```typescript
// Generate JWT token
const loginResponse = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        username: 'admin',
        password: 'secure_password'
    })
});

const { token } = await loginResponse.json();

// Use token in subsequent requests
const response = await fetch('/api/v1/assessments', {
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
});
```

#### Role-Based Access Control

Users are assigned roles with specific permissions:

- **Admin**: Full access to all functions
- **User**: Can request assessments and view results
- **Approver**: Can approve remediation actions
- **Viewer**: Read-only access to logs and metrics

```typescript
// Example permission check
const hasPermission = await authService.checkPermission(
    token,
    'approve_remediation'
);

if (!hasPermission) {
    throw new Error('Insufficient permissions');
}
```

### 4. Assessment Workflow

#### Requesting Assessments

The Generic MCP Installer requests assessments from the Compliance Server:

```typescript
// Request assessment
const assessmentRequest = {
    requestId: 'assessment-123',
    assessmentType: 'compliance',
    options: {
        includeDetails: true,
        generateReport: true,
        autoApprove: false // Always requires human approval
    },
    targetServers: ['filesystem', 'postgres'],
    timestamp: new Date().toISOString()
};

const response = await fetch('/api/v1/assessments', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(assessmentRequest)
});
```

#### Assessment Processing

1. **Validation**: Integration coordinator validates request
2. **Routing**: Request forwarded to Compliance Server
3. **Execution**: Compliance Server performs assessment
4. **Results**: Results returned to coordinator
5. **Logging**: Assessment logged for audit purposes

```typescript
// Assessment response structure
const assessmentResponse = {
    success: true,
    assessmentId: 'assessment-123',
    status: 'pending',
    requiresApproval: true,
    autoExecuted: false,
    results: {
        summary: {
            totalIssues: 5,
            criticalIssues: 2,
            warningIssues: 3
        },
        servers: {
            filesystem: {
                status: 'compliant',
                issues: []
            },
            postgres: {
                status: 'non_compliant',
                issues: ['missing_config', 'security_issue']
            }
        }
    }
};
```

### 5. Remediation Workflow

#### Proposing Remediation

Based on assessment results, remediation actions are proposed:

```typescript
// Propose remediation
const remediationRequest = {
    assessmentId: 'assessment-123',
    issues: ['missing_config', 'security_issue'],
    priority: 'high',
    autoApprove: false, // Always requires human approval
    proposedActions: [
        {
            id: 'action-1',
            type: 'install_server',
            serverName: 'postgres',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-postgres'],
            env: {
                DATABASE_URL: 'postgresql://user:pass@localhost:5432/db'
            }
        }
    ]
};

const response = await fetch('/api/v1/remediations/propose', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(remediationRequest)
});
```

#### Approval Workflow

All remediation actions require human approval:

```typescript
// Submit approval request
const approvalRequest = {
    approvalId: 'approval-123',
    proposalId: 'remediation-123',
    decision: 'approved', // or 'rejected'
    reason: 'Security compliance required',
    approvalToken: 'secure_approval_token'
};

const response = await fetch('/api/v1/approvals', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(approvalRequest)
});
```

#### Approval Token Generation

Approval tokens are generated for authorized users:

```typescript
// Generate approval token
const tokenResponse = await fetch('/api/v1/auth/approval-token', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${userToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        reason: 'Approving security remediation',
        expiresAt: '2025-08-24T12:00:00Z'
    })
});

const { approvalToken } = await tokenResponse.json();
```

### 6. Execution Workflow

#### Executing Approved Remediation

Once approved, remediation actions are executed:

```typescript
// Execute remediation
const executionRequest = {
    proposalId: 'remediation-123',
    approvalToken: 'secure_approval_token',
    dryRun: false,
    rollbackOnFailure: true,
    parallelExecution: false
};

const response = await fetch('/api/v1/remediations/execute', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(executionRequest)
});
```

#### Execution Monitoring

Real-time monitoring of execution progress:

```typescript
// Get execution status
const statusResponse = await fetch('/api/v1/remediations/execution/123', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});

const executionStatus = await statusResponse.json();
/*
{
    executionId: 'exec-123',
    status: 'running',
    progress: 50,
    currentAction: 'installing_postgres',
    startTime: '2025-08-24T10:00:00Z',
    estimatedCompletion: '2025-08-24T10:05:00Z',
    results: {
        completed: 1,
        total: 2,
        successful: 1,
        failed: 0
    }
}
*/
```

## Human Oversight Interface

### Web Dashboard

The integration coordinator provides a web-based dashboard for human oversight:

```bash
# Start the web interface
npm run start:web

# Access at
http://localhost:3000
```

### Dashboard Features

1. **Assessment Dashboard**
   - View all pending assessments
   - Review assessment results
   - Export assessment reports

2. **Remediation Dashboard**
   - View proposed remediation actions
   - Approve or reject remediation
   - Monitor execution progress

3. **Audit Dashboard**
   - View comprehensive audit logs
   - Filter logs by various criteria
   - Export audit reports

4. **System Dashboard**
   - Monitor system health
   - View performance metrics
   - Set up alerts

### Approval Workflow Interface

#### Assessment Approval

```html
<!-- Assessment Approval Interface -->
<div class="assessment-approval">
    <h3>Assessment Results</h3>
    <div class="assessment-summary">
        <p>Total Issues: <span class="critical">2</span> Critical, <span class="warning">3</span> Warning</p>
    </div>
    <div class="server-issues">
        <h4>PostgreSQL Server</h4>
        <ul>
            <li class="critical">Missing configuration file</li>
            <li class="warning">Outdated version</li>
        </ul>
    </div>
    <div class="approval-actions">
        <button class="btn-approve" onclick="approveAssessment('assessment-123')">
            Approve Assessment
        </button>
        <button class="btn-reject" onclick="rejectAssessment('assessment-123', 'Manual review needed')">
            Reject Assessment
        </button>
    </div>
</div>
```

#### Remediation Approval

```html
<!-- Remediation Approval Interface -->
<div class="remediation-approval">
    <h3>Remediation Proposal</h3>
    <div class="proposal-details">
        <h4>Proposed Actions:</h4>
        <ul>
            <li>Install PostgreSQL server with latest version</li>
            <li>Generate configuration file</li>
            <li>Test connectivity</li>
        </ul>
    </div>
    <div class="risk-assessment">
        <h4>Risk Assessment:</h4>
        <p>Impact: <span class="medium">Medium</span></p>
        <p>Effort: <span class="low">Low</span></p>
        <p>Success Rate: <span class="high">High</span></p>
    </div>
    <div class="approval-actions">
        <button class="btn-approve" onclick="approveRemediation('remediation-123')">
            Approve Remediation
        </button>
        <button class="btn-reject" onclick="rejectRemediation('remediation-123', 'Alternative solution preferred')">
            Reject Remediation
        </button>
    </div>
</div>
```

## Security Considerations

### Authentication Security

1. **JWT Tokens**: Use strong JWT secrets with appropriate expiration
2. **Password Hashing**: Implement bcrypt for password storage
3. **Session Management**: Secure session handling with proper timeouts
4. **Multi-factor Authentication**: Optional MFA for critical operations

### Data Protection

1. **Encryption**: Encrypt sensitive data at rest and in transit
2. **Data Masking**: Mask sensitive information in logs and displays
3. **Access Control**: Implement strict role-based access control
4. **Audit Trail**: Maintain comprehensive audit logs

### Network Security

1. **HTTPS**: Use HTTPS for all API communications
2. **Firewall**: Configure firewall rules appropriately
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Input Validation**: Validate all inputs to prevent injection attacks

## Monitoring and Alerting

### System Metrics

The integration coordinator collects comprehensive system metrics:

```typescript
// Available metrics
const metrics = {
    system: {
        cpu: { usage: 45.2, cores: 8 },
        memory: { total: 16, used: 8, free: 8, usage: 50 },
        disk: { total: 500, used: 200, free: 300, usage: 40 },
        network: { incoming: 1024, outgoing: 2048 }
    },
    services: {
        'integration-coordinator': {
            status: 'healthy',
            uptime: 86400,
            responseTime: { average: 150, p95: 300 },
            errorRate: 0.1
        },
        'compliance-server': {
            status: 'healthy',
            uptime: 86400,
            responseTime: { average: 200, p95: 500 },
            errorRate: 0.2
        }
    }
};
```

### Alert Configuration

Configure alerts for critical events:

```typescript
// Alert configuration
const alerts = {
    critical: [
        { condition: 'cpu_usage > 90', action: 'notify_admin' },
        { condition: 'memory_usage > 85', action: 'notify_team' },
        { condition: 'disk_usage > 95', action: 'emergency_alert' }
    ],
    warning: [
        { condition: 'error_rate > 5', action: 'log_warning' },
        { condition: 'response_time > 1000', action: 'log_warning' }
    ]
};
```

## Troubleshooting

### Common Issues

#### Server Connection Problems

**Issue**: Integration coordinator cannot connect to MCP servers

**Solution**:
1. Verify server is running and accessible
2. Check network connectivity and firewall settings
3. Validate authentication credentials
4. Review server logs for connection errors

```bash
# Test server connectivity
curl -X GET https://integration-coordinator:3000/api/v1/servers/compliance-server/ping
```

#### Authentication Failures

**Issue**: Users cannot authenticate or tokens are invalid

**Solution**:
1. Verify user credentials in database
2. Check JWT token expiration
3. Validate session configuration
4. Review authentication service logs

```bash
# Test authentication
curl -X POST https://integration-coordinator:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

#### Approval Workflow Issues

**Issue**: Approval tokens are not working or approvals are failing

**Solution**:
1. Verify user has appropriate permissions
2. Check approval token expiration
3. Validate token integrity
4. Review approval service logs

```bash
# Check user permissions
curl -X GET https://integration-coordinator:3000/api/v1/auth/permissions \
  -H "Authorization: Bearer <user_token>"
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Set debug environment variable
export LOG_LEVEL=debug

# Start with debug mode
npm run start:debug
```

### Log Analysis

Review logs for troubleshooting:

```bash
# View application logs
tail -f logs/integration.log

# Filter for specific errors
grep "ERROR" logs/integration.log

# View audit logs
psql -U mcp_user -d mcp_integration -c "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 100;"
```

## Performance Optimization

### Database Optimization

1. **Indexing**: Ensure proper indexing on frequently queried columns
2. **Connection Pooling**: Use connection pooling for database connections
3. **Query Optimization**: Optimize slow queries with proper indexing
4. **Partitioning**: Consider table partitioning for large datasets

### Caching Strategy

1. **Redis Integration**: Implement Redis for caching frequently accessed data
2. **Response Caching**: Cache API responses where appropriate
3. **Session Caching**: Cache user sessions for better performance

### Load Balancing

For high-availability deployments:

1. **Load Balancer**: Use load balancer for multiple coordinator instances
2. **Session Affinity**: Configure session affinity if needed
3. **Health Checks**: Implement health checks for load balancer

## Backup and Recovery

### Database Backup

```bash
# Daily backup
pg_dump -U mcp_user -d mcp_integration > backup_$(date +%Y%m%d).sql

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
pg_dump -U mcp_user -d mcp_integration | gzip > /backups/mcp_integration_$DATE.sql.gz
```

### Configuration Backup

```bash
# Backup configuration files
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env config/
```

### Disaster Recovery

1. **Recovery Procedures**: Document step-by-step recovery procedures
2. **Point-in-Time Recovery**: Configure point-in-time recovery for PostgreSQL
3. **Failover Plan**: Implement failover procedures for critical services
4. **Regular Testing**: Test recovery procedures regularly

## API Reference

### Authentication Endpoints

#### POST /api/v1/auth/login
Authenticate user and return JWT token

**Request**:
```json
{
    "username": "admin",
    "password": "password"
}
```

**Response**:
```json
{
    "success": true,
    "token": "jwt_token_here",
    "user": {
        "id": 1,
        "username": "admin",
        "role": "admin"
    }
}
```

#### POST /api/v1/auth/approval-token
Generate approval token for authorized users

**Request**:
```json
{
    "reason": "Approving security remediation",
    "expiresAt": "2025-08-24T12:00:00Z"
}
```

**Response**:
```json
{
    "success": true,
    "approvalToken": "approval_token_here",
    "expiresAt": "2025-08-24T12:00:00Z"
}
```

### Assessment Endpoints

#### POST /api/v1/assessments
Request compliance assessment

**Request**:
```json
{
    "requestId": "assessment-123",
    "assessmentType": "compliance",
    "options": {
        "includeDetails": true,
        "generateReport": true,
        "autoApprove": false
    },
    "targetServers": ["filesystem", "postgres"]
}
```

**Response**:
```json
{
    "success": true,
    "assessmentId": "assessment-123",
    "status": "pending",
    "requiresApproval": true,
    "autoExecuted": false
}
```

#### GET /api/v1/assessments/{id}
Get assessment results

**Response**:
```json
{
    "success": true,
    "assessmentId": "assessment-123",
    "status": "completed",
    "results": {
        "summary": {
            "totalIssues": 5,
            "criticalIssues": 2,
            "warningIssues": 3
        },
        "servers": {
            "filesystem": {
                "status": "compliant",
                "issues": []
            },
            "postgres": {
                "status": "non_compliant",
                "issues": ["missing_config", "security_issue"]
            }
        }
    }
}
```

### Remediation Endpoints

#### POST /api/v1/remediations/propose
Propose remediation actions

**Request**:
```json
{
    "assessmentId": "assessment-123",
    "issues": ["missing_config", "security_issue"],
    "priority": "high",
    "autoApprove": false,
    "proposedActions": [
        {
            "id": "action-1",
            "type": "install_server",
            "serverName": "postgres",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-postgres"],
            "env": {
                "DATABASE_URL": "postgresql://user:pass@localhost:5432/db"
            }
        }
    ]
}
```

**Response**:
```json
{
    "success": true,
    "proposalId": "remediation-123",
    "status": "pending",
    "requiresApproval": true,
    "autoExecuted": false
}
```

#### POST /api/v1/approvals
Submit approval for remediation

**Request**:
```json
{
    "approvalId": "approval-123",
    "proposalId": "remediation-123",
    "decision": "approved",
    "reason": "Security compliance required",
    "approvalToken": "approval_token_here"
}
```

**Response**:
```json
{
    "success": true,
    "approvalId": "approval-123",
    "decision": "approved",
    "executionId": "exec-123"
}
```

### Monitoring Endpoints

#### GET /api/v1/metrics/system
Get system metrics

**Response**:
```json
{
    "success": true,
    "metrics": {
        "timestamp": "2025-08-24T10:00:00Z",
        "system": {
            "cpu": { "usage": 45.2, "cores": 8 },
            "memory": { "total": 16, "used": 8, "free": 8, "usage": 50 },
            "disk": { "total": 500, "used": 200, "free": 300, "usage": 40 }
        },
        "services": {
            "integration-coordinator": {
                "status": "healthy",
                "uptime": 86400,
                "responseTime": { "average": 150, "p95": 300 },
                "errorRate": 0.1
            }
        }
    }
}
```

#### GET /api/v1/audit/logs
Get audit logs

**Parameters**:
- `actor`: Filter by actor
- `action`: Filter by action
- `startDate`: Filter by start date
- `endDate`: Filter by end date
- `limit`: Number of records to return
- `offset`: Offset for pagination

**Response**:
```json
{
    "success": true,
    "logs": [
        {
            "id": "audit-123",
            "timestamp": "2025-08-24T10:00:00Z",
            "action": "assessment_requested",
            "actor": "admin",
            "target": "assessment-123",
            "result": "success",
            "details": {
                "requestId": "assessment-123",
                "assessmentType": "compliance"
            }
        }
    ],
    "total": 1,
    "page": 1,
    "pageSize": 10
}
```

## Best Practices

### Security Best Practices

1. **Principle of Least Privilege**: Grant users minimum required permissions
2. **Regular Security Audits**: Conduct regular security assessments
3. **Input Validation**: Validate all user inputs
4. **Secure Coding**: Follow secure coding practices
5. **Regular Updates**: Keep dependencies updated

### Performance Best Practices

1. **Database Optimization**: Optimize database queries and indexing
2. **Caching**: Implement appropriate caching strategies
3. **Connection Pooling**: Use connection pooling for database connections
4. **Load Testing**: Perform regular load testing
5. **Monitoring**: Monitor performance metrics regularly

### Operational Best Practices

1. **Documentation**: Maintain comprehensive documentation
2. **Automation**: Automate routine tasks
3. **Monitoring**: Implement comprehensive monitoring
4. **Backup**: Regular backups and testing
5. **Incident Response**: Document and test incident response procedures

### Development Best Practices

1. **Code Reviews**: Implement code review processes
2. **Testing**: Comprehensive testing strategy
3. **Version Control**: Use version control for all configurations
4. **CI/CD**: Implement continuous integration and deployment
5. **Error Handling**: Implement proper error handling and logging

## Conclusion

The MCP Integration Coordinator provides a robust, secure, and scalable solution for coordinating between the Generic MCP Installer and Compliance Server. By maintaining server independence while providing comprehensive oversight capabilities, the integration ensures that all critical operations require human approval while maintaining system reliability and security.

The comprehensive audit trail, monitoring capabilities, and human oversight interface provide the necessary controls for managing MCP server configurations and remediation actions in the KiloCode ecosystem.

---

**Document Version**: 1.0  
**Created**: August 24, 2025  
**Last Updated**: August 24, 2025  
**Status**: Complete

For questions or support, please contact the KiloCode development team.