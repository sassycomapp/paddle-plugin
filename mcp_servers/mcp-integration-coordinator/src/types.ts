/**
 * MCP Integration Coordinator Types
 * 
 * This file defines the TypeScript interfaces and types used throughout
 * the MCP Integration Coordinator implementation.
 */

export interface AssessmentRequest {
    requestId: string;
    serverName?: string;
    assessmentType: 'compliance' | 'health' | 'security';
    options: AssessmentOptions;
    timestamp: string;
    source: 'installer' | 'compliance';
}

export interface AssessmentResponse {
    requestId: string;
    status: 'success' | 'pending' | 'failed';
    assessment?: AssessmentResult;
    requiresApproval: boolean;
    approvalRequestId?: string;
    timestamp: string;
}

export interface RemediationProposal {
    proposalId: string;
    assessmentId: string;
    actions: RemediationAction[];
    riskAssessment: RiskAssessment;
    estimatedTime: number;
    requiresApproval: true;
    timestamp: string;
}

export interface ApprovalRequest {
    approvalId: string;
    type: 'assessment' | 'remediation';
    data: AssessmentRequest | RemediationProposal;
    requestedBy: string;
    timestamp: string;
    expiresAt: string;
    decision?: string;
}

export interface ApprovalResponse {
    approvalId: string;
    status: 'approved' | 'rejected' | 'pending';
    decision?: string;
    approvedBy: string;
    timestamp: string;
}

export interface AssessmentStatus {
    requestId: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    progress: number;
    message?: string;
    lastUpdated: string;
}

export interface RemediationStatus {
    proposalId: string;
    status: 'pending' | 'approved' | 'rejected' | 'in_progress' | 'completed' | 'failed';
    progress: number;
    currentAction?: string;
    message?: string;
    lastUpdated: string;
}

export interface AuditLog {
    id: string;
    timestamp: string;
    action: string;
    actor: string;
    target: string;
    result: 'success' | 'failed' | 'pending';
    details: Record<string, any>;
    ipAddress?: string;
    userAgent?: string;
}

export interface AssessmentResult {
    timestamp: string;
    totalServers: number;
    compliantServers: number;
    nonCompliantServers: number;
    missingServers: string[];
    configurationIssues: ConfigurationIssue[];
    serverStatuses: ServerStatus[];
    overallScore: number;
    summary: {
        criticalIssues: number;
        highIssues: number;
        mediumIssues: number;
        lowIssues: number;
    };
}

export interface ConfigurationIssue {
    id: string;
    serverName: string;
    issueType: 'missing_config' | 'incomplete_config' | 'invalid_config' | 'security_issue' | 'performance_issue';
    severity: 'critical' | 'high' | 'medium' | 'low';
    description: string;
    details: Record<string, any>;
    recommendation: string;
}

export interface ServerStatus {
    name: string;
    status: 'online' | 'offline' | 'error' | 'unknown';
    command: string;
    args: string[];
    env?: Record<string, string>;
    lastCheck: string;
    responseTime?: number;
    error?: string;
}

export interface RemediationAction {
    id: string;
    type: 'install_server' | 'update_config' | 'remove_server' | 'fix_security' | 'optimize_performance';
    serverName: string;
    description: string;
    command?: string;
    args?: string[];
    env?: Record<string, string>;
    rollbackCommand?: string;
    rollbackArgs?: string[];
    rollbackEnv?: Record<string, string>;
    estimatedTime: number;
    requiresRestart: boolean;
    dependencies: string[];
}

export interface RiskAssessment {
    level: 'low' | 'medium' | 'high' | 'critical';
    impact: string;
    likelihood: number;
    mitigation: string;
}

export interface AssessmentOptions {
    includeDetails: boolean;
    generateReport: boolean;
    saveResults: boolean;
    checkServerStatus: boolean;
    validateConfig: boolean;
    checkCompliance: boolean;
    serverFilter?: string[];
    deepScan: boolean;
}

export interface ErrorResponse {
    error: {
        code: string;
        message: string;
        details?: Record<string, any>;
        retryable: boolean;
    };
    timestamp: string;
    requestId: string;
}

export interface HealthStatus {
    status: 'healthy' | 'degraded' | 'unhealthy';
    components: {
        [component: string]: {
            status: 'healthy' | 'warning' | 'error';
            message?: string;
            lastCheck: string;
        };
    };
    timestamp: string;
}

export interface SystemMetrics {
    timestamp: string;
    cpu: number;
    memory: number;
    disk: number;
    network: {
        incoming: number;
        outgoing: number;
    };
    activeConnections: number;
    requestRate: number;
    errorRate: number;
}

export interface DashboardData {
    totalServers: number;
    onlineServers: number;
    offlineServers: number;
    criticalIssues: number;
    highIssues: number;
    mediumIssues: number;
    lowIssues: number;
    lastAssessment: string;
    overallCompliance: number;
    recentChanges: ChangeLog[];
    pendingApprovals: number;
    activeExecutions: number;
}

export interface ChangeLog {
    timestamp: string;
    action: 'install' | 'remove' | 'update' | 'remediate';
    serverName: string;
    user: string;
    result: 'success' | 'failed';
    details: string;
}

// Authentication and Authorization Types
export interface AuthToken {
    accessToken: string;
    refreshToken: string;
    expiresAt: string;
    role: Role;
    permissions: Permission[];
}

export interface LoginRequest {
    username: string;
    password: string;
    rememberMe?: boolean;
}

export interface LoginResponse {
    token: AuthToken;
    user: User;
}

export interface User {
    id: string;
    username: string;
    email: string;
    role: Role;
    permissions: Permission[];
    active: boolean;
    lastLogin: string;
    password?: string; // Only included in database operations, not in API responses
}

export enum Role {
    INSTALLER = 'installer',
    COMPLIANCE = 'compliance',
    HUMAN_OVERSIGHT = 'human_oversight',
    ADMIN = 'admin'
}

export enum Permission {
    REQUEST_ASSESSMENT = 'request:assessment',
    APPROVE_ASSESSMENT = 'approve:assessment',
    PROPOSE_REMEDIATION = 'propose:remediation',
    APPROVE_REMEDIATION = 'approve:remediation',
    VIEW_AUDIT_LOGS = 'view:audit_logs',
    MANAGE_SYSTEM = 'manage:system'
}

// Server Configuration Types
export interface ServerConfig {
    port: number;
    host: string;
    database: DatabaseConfig;
    redis?: RedisConfig;
    logging: LoggingConfig;
    security: SecurityConfig;
    compliance: ComplianceConfig;
}

export interface DatabaseConfig {
    host: string;
    port: number;
    database: string;
    username: string;
    password: string;
    ssl?: boolean;
    maxConnections?: number;
}

export interface RedisConfig {
    host: string;
    port: number;
    password?: string;
    db?: number;
}

export interface LoggingConfig {
    level: 'debug' | 'info' | 'warn' | 'error';
    file?: string;
    maxSize?: string;
    maxFiles?: number;
    enableConsole: boolean;
}

export interface SecurityConfig {
    jwtSecret: string;
    jwtExpiration: string;
    bcryptRounds: number;
    rateLimit: {
        windowMs: number;
        max: number;
    };
    cors: {
        origin: string[];
        credentials: boolean;
    };
}

export interface ComplianceConfig {
    requireApproval: boolean;
    backupBeforeChanges: boolean;
    auditRetentionDays: number;
}

// Utility Types
export type DeepPartial<T> = {
    [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type AsyncFunction<T = any> = (...args: any[]) => Promise<T>;



// Error Types
export class IntegrationError extends Error {
    constructor(message: string, public code?: string) {
        super(message);
        this.name = 'IntegrationError';
    }
}

export class AuthenticationError extends Error {
    constructor(message: string) {
        super(message);
        this.name = 'AuthenticationError';
    }
}

export class AuthorizationError extends Error {
    constructor(message: string) {
        super(message);
        this.name = 'AuthorizationError';
    }
}

export class ValidationError extends Error {
    constructor(message: string, public field?: string) {
        super(message);
        this.name = 'ValidationError';
    }
}

export class TimeoutError extends Error {
    constructor(message: string, public timeout: number) {
        super(message);
        this.name = 'TimeoutError';
    }
}

// AssessmentStore and AssessmentProcessor Types
export enum AssessmentState {
    PENDING = 'pending',
    PROCESSING = 'processing',
    COMPLETED = 'completed',
    FAILED = 'failed',
    CANCELLED = 'cancelled'
}

export interface AssessmentStateData {
    assessmentId: string;
    state: AssessmentState;
    version: number;
    progress: number;
    message?: string;
    createdAt: string;
    updatedAt: string;
    completedAt?: string;
    requestData: AssessmentRequest;
    resultData?: AssessmentResult;
    errorMessage?: string;
    retryCount: number;
    nextRetryAt?: string;
    metadata?: Record<string, any>;
}


export interface ProcessingQueueItem {
    assessmentId: string;
    priority: 'high' | 'normal' | 'low';
    retryCount: number;
    maxRetries: number;
    timeout: number;
    createdAt: string;
    lastAttemptAt?: string;
    nextRetryAt?: string;
}

export interface CircuitBreakerState {
    state: 'closed' | 'open' | 'half-open';
    failureCount: number;
    lastFailureTime?: string;
    nextAttemptTime?: string;
}

export interface AssessmentProcessorConfig {
    assessmentStore: AssessmentStoreConfig;
    processing: {
        timeout: number;
        maxRetries: number;
        retryDelay: number;
        retryBackoff: number;
        queueSize: number;
        batchSize: number;
        processingInterval: number;
    };
    circuitBreaker: {
        failureThreshold: number;
        resetTimeout: number;
        monitoringInterval: number;
    };
    logging: {
        level: 'debug' | 'info' | 'warn' | 'error';
        enableMetrics: boolean;
    };
}

export interface AssessmentProcessorMetrics {
    totalProcessed: number;
    successful: number;
    failed: number;
    retryCount: number;
    averageProcessingTime: number;
    queueSize: number;
    circuitBreakerState: CircuitBreakerState;
    lastProcessedAt?: string;
}

export class AssessmentProcessingError extends Error {
    constructor(message: string, public assessmentId?: string, public code?: string) {
        super(message);
        this.name = 'AssessmentProcessingError';
    }
}

export class AssessmentStateTransitionError extends Error {
    constructor(public fromState: AssessmentState, public toState: AssessmentState) {
        super(`Invalid state transition from ${fromState} to ${toState}`);
        this.name = 'AssessmentStateTransitionError';
    }
}

export class AssessmentNotFoundError extends Error {
    constructor(public assessmentId: string) {
        super(`Assessment not found: ${assessmentId}`);
        this.name = 'AssessmentNotFoundError';
    }
}

export class AssessmentTimeoutError extends Error {
    constructor(public assessmentId: string, public timeout: number) {
        super(`Assessment timeout: ${assessmentId} after ${timeout}ms`);
        this.name = 'AssessmentTimeoutError';
    }
}

export class AssessmentExecutionError extends Error {
    constructor(message: string, public assessmentId?: string) {
        super(message);
        this.name = 'AssessmentExecutionError';
    }
}

export class AssessmentStatusError extends Error {
    constructor(message: string, public assessmentId?: string) {
        super(message);
        this.name = 'AssessmentStatusError';
    }
}

export class AssessmentCancellationError extends Error {
    constructor(message: string, public assessmentId?: string) {
        super(message);
        this.name = 'AssessmentCancellationError';
    }
}

// AssessmentStore Interfaces
export interface AssessmentStoreConfig {
    database: DatabaseConfig;
    cache?: RedisConfig;
    processing: {
        timeout: number;
        maxRetries: number;
        retryDelay: number;
        queueSize: number;
    };
    complianceServer: {
        baseUrl: string;
        apiKey: string;
        timeout: number;
        maxConcurrent: number;
    };
}

export interface AssessmentStoreCreateOptions {
    assessmentType: 'compliance' | 'health' | 'security';
    options: AssessmentOptions;
    serverName?: string;
    source: 'installer' | 'compliance';
    requestId?: string;
}

export interface AssessmentStoreStatistics {
    totalAssessments: number;
    assessmentsByState: Record<AssessmentState, number>;
    averageProcessingTime: number;
    recentAssessments: number;
}

export interface AssessmentStoreRetryInfo {
    assessmentId: string;
    retryCount: number;
    nextRetryAt?: string;
    errorMessage?: string;
}