/**
 * MCP Integration Coordinator - Types (JavaScript Version)
 * 
 * This file defines the JavaScript objects and interfaces used throughout
 * the MCP Integration Coordinator implementation.
 */

// Server Configuration
const ServerConfig = {
    port: 3001,
    host: 'localhost',
    database: {
        host: 'localhost',
        port: 5432,
        database: 'kilocode_integration',
        username: 'postgres',
        password: 'password',
        ssl: false,
        maxConnections: 10
    },
    logging: {
        level: 'info',
        enableConsole: true
    },
    security: {
        jwtSecret: 'your-secret-key',
        jwtExpiration: '1h',
        bcryptRounds: 12,
        rateLimit: {
            windowMs: 900000, // 15 minutes
            max: 100
        },
        cors: {
            origin: ['http://localhost:3000'],
            credentials: true
        }
    },
    compliance: {
        requireApproval: true,
        backupBeforeChanges: true,
        auditRetentionDays: 90
    }
};

// Assessment Types
const AssessmentRequest = {
    requestId: '',
    serverName: '',
    assessmentType: 'compliance', // 'compliance' | 'health' | 'security'
    options: {
        includeDetails: true,
        generateReport: true,
        saveResults: true,
        checkServerStatus: true,
        validateConfig: true,
        checkCompliance: true,
        deepScan: false
    },
    timestamp: '',
    source: 'installer' // 'installer' | 'compliance'
};

const AssessmentResponse = {
    requestId: '',
    status: 'success', // 'success' | 'pending' | 'failed'
    assessment: null,
    requiresApproval: true,
    approvalRequestId: '',
    timestamp: ''
};

const AssessmentResult = {
    timestamp: '',
    totalServers: 0,
    compliantServers: 0,
    nonCompliantServers: 0,
    missingServers: [],
    configurationIssues: [],
    serverStatuses: [],
    overallScore: 0,
    summary: {
        criticalIssues: 0,
        highIssues: 0,
        mediumIssues: 0,
        lowIssues: 0
    }
};

const ConfigurationIssue = {
    id: '',
    serverName: '',
    issueType: 'missing_config', // 'missing_config' | 'incomplete_config' | 'invalid_config' | 'security_issue' | 'performance_issue'
    severity: 'medium', // 'critical' | 'high' | 'medium' | 'low'
    description: '',
    details: {},
    recommendation: ''
};

const ServerStatus = {
    name: '',
    status: 'online', // 'online' | 'offline' | 'error' | 'unknown'
    command: '',
    args: [],
    env: {},
    lastCheck: '',
    responseTime: 0,
    error: ''
};

// Remediation Types
const RemediationProposal = {
    proposalId: '',
    assessmentId: '',
    actions: [],
    riskAssessment: {
        level: 'medium', // 'low' | 'medium' | 'high' | 'critical'
        impact: '',
        likelihood: 0,
        mitigation: ''
    },
    estimatedTime: 0,
    requiresApproval: true,
    timestamp: ''
};

const RemediationAction = {
    id: '',
    type: 'install_server', // 'install_server' | 'update_config' | 'remove_server' | 'fix_security' | 'optimize_performance'
    serverName: '',
    description: '',
    command: '',
    args: [],
    env: {},
    rollbackCommand: '',
    rollbackArgs: [],
    rollbackEnv: {},
    estimatedTime: 0,
    requiresRestart: false,
    dependencies: []
};

const ApprovalRequest = {
    approvalId: '',
    type: 'assessment', // 'assessment' | 'remediation'
    data: {},
    requestedBy: '',
    timestamp: '',
    expiresAt: ''
};

const ApprovalResponse = {
    approvalId: '',
    status: 'pending', // 'approved' | 'rejected' | 'pending'
    decision: '',
    approvedBy: '',
    timestamp: ''
};

// Audit Types
const AuditLog = {
    id: '',
    timestamp: '',
    action: '',
    actor: '',
    target: '',
    result: 'success', // 'success' | 'failed' | 'pending'
    details: {},
    ipAddress: '',
    userAgent: ''
};

// Error Types
const ErrorResponse = {
    error: {
        code: '',
        message: '',
        details: {},
        retryable: false
    },
    timestamp: '',
    requestId: ''
};

// Export all types
module.exports = {
    ServerConfig,
    AssessmentRequest,
    AssessmentResponse,
    AssessmentResult,
    ConfigurationIssue,
    ServerStatus,
    RemediationProposal,
    RemediationAction,
    ApprovalRequest,
    ApprovalResponse,
    AuditLog,
    ErrorResponse
};