# MCP Integration Coordinator

A secure integration coordinator that manages communication between MCP servers with human oversight and approval workflows.

## Overview

The MCP Integration Coordinator serves as a central hub for coordinating communication between the Generic MCP Installer and the Compliance Server, ensuring all actions require proper human oversight and approval.

## Architecture

### Core Components

1. **Integration Coordinator** (`src/server.ts`)
   - Main HTTP server
   - API endpoint management
   - Event coordination

2. **Authentication Service** (`src/services/auth-service.ts`)
   - User authentication and authorization
   - JWT token management
   - Password hashing and verification

3. **Audit Service** (`src/services/audit-service.ts`)
   - Comprehensive audit logging
   - Activity tracking
   - Compliance monitoring

4. **AssessmentStore** (`src/services/assessment-store.ts`)
   - Promise-based state management system
   - Server communication coordination
   - Real-time updates

5. **Controllers**
   - Assessment Controller: Handles compliance assessment requests
   - Remediation Controller: Manages remediation proposals and approvals

## Key Features

### 🔐 Security & Authentication
- JWT-based authentication
- Role-based access control
- Secure password hashing
- Token refresh mechanism

### 👥 Human Oversight
- All remediation actions require human approval
- Comprehensive approval workflows
- Audit trail for all decisions
- Real-time status tracking

### 🔄 Server Integration
- Coordinates between Generic MCP Installer and Compliance Server
- Event-driven communication
- Secure API endpoints
- Status monitoring

### 📊 Monitoring & Logging
- Comprehensive audit logging
- Real-time dashboard
- Activity tracking
- Performance metrics

## Installation

### Prerequisites
- Node.js 18+
- PostgreSQL 12+
- npm 8+

### Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Initialize database:
```bash
npm run db:init
```

4. Start the server:
```bash
npm start
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/register` - Register new user

### Assessment
- `POST /api/assessment/request` - Request compliance assessment
- `GET /api/assessment/results/:id` - Get assessment results
- `GET /api/assessment/list` - List all assessments
- `DELETE /api/assessment/:id` - Cancel assessment

### Remediation
- `POST /api/remediation/propose` - Propose remediation
- `GET /api/remediation/proposals/:id` - Get remediation proposal
- `POST /api/remediation/approve` - Approve remediation
- `POST /api/remediation/reject` - Reject remediation
- `GET /api/remediation/list` - List all remediation proposals

### Monitoring
- `GET /health` - Health check
- `GET /api/dashboard` - Dashboard data
- `GET /api/audit/logs` - Audit logs

## Configuration

### Environment Variables

```bash
# Server Configuration
PORT=3001
HOST=localhost

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kilocode_integration
DB_USER=postgres
DB_PASSWORD=password

# Security Configuration
JWT_SECRET=your-secret-key
JWT_EXPIRATION=1h
BCRYPT_ROUNDS=12

# Redis Configuration (Optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Logging Configuration
LOG_LEVEL=info
LOG_FILE=logs/integration-coordinator.log
```

### Database Schema

The coordinator uses PostgreSQL for data storage with the following main tables:

- `users` - User accounts and authentication
- `audit_logs` - Comprehensive audit trail
- `assessments` - Assessment records and results
- `remediation_proposals` - Remediation proposals and approvals
- `approvals` - Approval workflow records

## Usage Examples

### Requesting an Assessment

```bash
curl -X POST http://localhost:3001/api/assessment/request \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "requestId": "assessment-123",
    "assessmentType": "compliance",
    "options": {
      "includeDetails": true,
      "generateReport": true
    },
    "timestamp": "2025-08-24T09:25:00Z",
    "source": "installer"
  }'
```

### Approving Remediation

```bash
curl -X POST http://localhost:3001/api/remediation/approve \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "approvalId": "approval-123",
    "decision": "approved",
    "reason": "Security vulnerability requires immediate attention"
  }'
```

### Getting Dashboard Data

```bash
curl -X GET http://localhost:3001/api/dashboard \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Integration with MCP Servers

### Generic MCP Installer Integration

The coordinator integrates with the Generic MCP Installer to:

1. **Request Assessments**: Installer can request compliance assessments for installed servers
2. **Submit Remediation Proposals**: Propose actions to fix compliance issues
3. **Execute Approved Actions**: Execute remediation actions after human approval
4. **Track Status**: Monitor the status of all operations

### Compliance Server Integration

The coordinator works with the Compliance Server to:

1. **Coordinate Assessments**: Forward assessment requests to the Compliance Server
2. **Manage Approvals**: Handle approval workflows for remediation actions
3. **Track Results**: Monitor and track remediation execution results
4. **Maintain Audit Trail**: Keep comprehensive records of all activities

## Human Oversight Workflow

### 1. Assessment Request
- Generic MCP Installer requests assessment
- Coordinator validates and forwards request
- Compliance Server performs assessment
- Results returned to coordinator

### 2. Remediation Proposal
- Compliance Server identifies issues
- Generates remediation proposals
- Coordinator logs proposals for review
- Human oversight interface displays proposals

### 3. Approval Process
- Human reviews remediation proposals
- Approves or rejects actions
- Coordinator logs approval decisions
- Approved actions queued for execution

### 4. Action Execution
- Coordinator executes approved actions
- Generic MCP Installer performs operations
- Results tracked and logged
- Human notified of completion

## Security Considerations

### Authentication
- JWT-based authentication with expiration
- Secure password hashing with bcrypt
- Token refresh mechanism
- Role-based access control

### Authorization
- Granular permission system
- Role-based access control
- Resource-level permissions
- Audit logging for all access

### Data Protection
- Secure storage of sensitive data
- Encryption in transit and at rest
- Regular security audits
- Compliance with security standards

## Monitoring & Observability

### Health Checks
- Endpoint health monitoring
- Database connection checks
- Service availability monitoring
- Performance metrics tracking

### Logging
- Comprehensive audit logging
- Structured log format
- Log rotation and retention
- Real-time log monitoring

### Metrics
- Request rate tracking
- Error rate monitoring
- Performance metrics
- Resource utilization

## Testing

### Running Tests
```bash
npm test
```

### Test Coverage
- Unit tests for core services
- Integration tests for API endpoints
- Security tests for authentication
- Performance tests for scalability

### Test Files
- `test/auth.test.js` - Authentication tests
- `test/api.test.js` - API endpoint tests
- `test/security.test.js` - Security tests
- `test/integration.test.js` - Integration tests

## Deployment

### Development
```bash
npm run dev
```

### Production
```bash
npm start
```

### Docker Deployment
```bash
docker build -t kilocode-integration-coordinator .
docker run -p 3001:3001 kilocode-integration-coordinator
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Check database credentials
   - Verify database is running
   - Check network connectivity

2. **Authentication Problems**
   - Verify JWT token validity
   - Check token expiration
   - Validate user credentials

3. **API Endpoint Issues**
   - Check server logs
   - Verify endpoint paths
   - Check request formatting

### Debug Mode
Enable debug logging:
```bash
LOG_LEVEL=debug npm start
```

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Standards
- Follow TypeScript best practices
- Write comprehensive tests
- Update documentation
- Follow security guidelines

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting guide
- Contact the development team

---

**Built with ❤️ by the KiloCode Team**