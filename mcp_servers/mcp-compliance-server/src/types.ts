/**
 * MCP Configuration and Compliance Server Types
 * 
 * This file defines the TypeScript interfaces and types used throughout
 * the MCP Configuration and Compliance Server implementation.
 */

export interface MCPServerConfig {
    command: string;
    args: string[];
    env?: Record<string, string>;
    description?: string;
    docsPath?: string;
}

export interface KiloCodeServerConfig extends MCPServerConfig {
    env: {
        NODE_ENV: string;
        KILOCODE_ENV: string;
        KILOCODE_PROJECT_PATH: string;
        KILOCODE_PROJECT_NAME: string;
        [key: string]: string;
    };
}

export interface ServerMetadata {
    name: string;
    description?: string;
    docsPath?: string;
    version?: string;
    status?: 'online' | 'offline' | 'error';
    lastChecked?: string;
}

export interface MCPConfig {
    mcpServers: Record<string, MCPServerConfig | ServerMetadata>;
}

export interface KiloCodeConfig {
    mcpServers: Record<string, KiloCodeServerConfig | ServerMetadata>;
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

export interface AssessmentResult {
    timestamp: string;
    totalServers: number;
    compliantServers: number;
    nonCompliantServers: number;
    missingServers: string[];
    configurationIssues: ConfigurationIssue[];
    serverStatuses: ServerStatus[];
    overallScore: number; // 0-100
    summary: {
        criticalIssues: number;
        highIssues: number;
        mediumIssues: number;
        lowIssues: number;
    };
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
    estimatedTime: number; // in seconds
    requiresRestart: boolean;
    dependencies: string[];
}

export interface RiskAssessment {
    level: 'low' | 'medium' | 'high' | 'critical';
    impact: string;
    likelihood: number; // 0-1
    mitigation: string;
}

export interface RemediationProposal {
    id: string;
    priority: 'critical' | 'high' | 'medium' | 'low';
    issue: ConfigurationIssue;
    solution: RemediationAction;
    risk: RiskAssessment;
    estimatedTime: number;
    dependencies: string[];
    prerequisites: string[];
}

export interface TestResult {
    name: string;
    passed: boolean;
    message: string;
    duration: number;
    details?: Record<string, any>;
}

export interface ExecutionResult {
    actionId: string;
    status: 'success' | 'failed' | 'partial' | 'pending';
    startTime: string;
    endTime?: string;
    tests: TestResult[];
    rollbackRequired: boolean;
    rollbackExecuted: boolean;
    errorMessage?: string;
    output?: string;
}

export interface ValidationResult {
    valid: boolean;
    errors: string[];
    warnings: string[];
    suggestions: string[];
    recommendations?: string[];
    validatedConfig?: Partial<MCPServerConfig>;
    ruleId?: string;
    ruleName?: string;
    severity?: string;
    message?: string;
    details?: Record<string, any>;
    autoFixApplied?: boolean;
}

export interface ComplianceRule {
    id: string;
    name: string;
    description: string;
    severity: 'critical' | 'high' | 'medium' | 'low';
    category: 'security' | 'performance' | 'configuration' | 'integration';
    validate: (config: MCPServerConfig) => ValidationResult;
    autoFix?: (config: MCPServerConfig) => Partial<MCPServerConfig>;
}

export interface ComplianceReport {
    overallScore: number; // 0-100
    passedRules: number;
    failedRules: number;
    rules: ComplianceRuleResult[];
    warnings: string[];
    recommendations: string[];
    timestamp: string;
}

export interface ComplianceRuleResult {
    ruleId: string;
    ruleName: string;
    passed: boolean;
    severity: 'critical' | 'high' | 'medium' | 'low';
    message: string;
    details: Record<string, any>;
    autoFixApplied?: boolean;
}

export interface ServerTemplate {
    name: string;
    description: string;
    config: MCPServerConfig;
    defaultEnv: Record<string, string>;
    requiredEnv: string[];
    optionalEnv: string[];
    complianceRules: string[];
    dependencies: string[];
}

export interface SyncResult {
    success: boolean;
    conflicts: string[];
    syncedServers: string[];
    errors: string[];
    warnings: string[];
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
}

export interface ChangeLog {
    timestamp: string;
    action: 'install' | 'remove' | 'update' | 'remediate';
    serverName: string;
    user: string;
    result: 'success' | 'failed';
    details: string;
}

export interface ReportOptions {
    format: 'json' | 'html' | 'pdf';
    includeDetails: boolean;
    includeTests: boolean;
    dateRange?: {
        start: string;
        end: string;
    };
    serverFilter?: string[];
    issueFilter?: string[];
}

export interface AssessmentOptions {
    checkServerStatus: boolean;
    validateConfig: boolean;
    checkCompliance: boolean;
    generateReport: boolean;
    serverFilter?: string[];
    deepScan: boolean;
}

export interface RemediationOptions {
    autoApprove: boolean;
    dryRun: boolean;
    rollbackOnFailure: boolean;
    parallelExecution: boolean;
    maxConcurrent: number;
    timeout: number;
}

export interface ServerDiscoveryResult {
    servers: DiscoveredServer[];
    errors: string[];
    warnings: string[];
}

export interface DiscoveredServer {
    name: string;
    type: 'npm' | 'python' | 'node' | 'docker' | 'other';
    command: string;
    args: string[];
    path?: string;
    version?: string;
    installed: boolean;
    configured: boolean;
    compliant: boolean;
    issues: ConfigurationIssue[];
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

export interface ServerConfig {
    port: number;
    host: string;
    database: DatabaseConfig;
    redis?: {
        host: string;
        port: number;
        password?: string;
    };
    logging: {
        level: 'debug' | 'info' | 'warn' | 'error';
        file?: string;
        maxSize?: string;
        maxFiles?: number;
    };
    security: {
        apiKey?: string;
        enableCors: boolean;
        allowedOrigins: string[];
        rateLimit: {
            windowMs: number;
            max: number;
        };
    };
    compliance: {
        autoRemediate: boolean;
        requireApproval: boolean;
        backupBeforeChanges: boolean;
    };
    // MCP Server configuration properties
    command?: string;
    args?: string[];
    env?: Record<string, string>;
}

// Utility types
export type DeepPartial<T> = {
    [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type AsyncFunction<T = any> = (...args: any[]) => Promise<T>;

export type EventHandler<T = any> = (data: T) => void;

export interface EventSystem {
    on: (event: string, handler: EventHandler) => void;
    off: (event: string, handler: EventHandler) => void;
    emit: (event: string, data?: any) => void;
    once: (event: string, handler: EventHandler) => void;
}

export interface ProgressTracker {
    start(task: string, total?: number): void;
    update(progress: number, message?: string): void;
    complete(message?: string): void;
    error(error: string): void;
    getProgress(): number;
    getStatus(): string;
}

export interface Logger {
    debug(message: string, meta?: any): void;
    info(message: string, meta?: any): void;
    warn(message: string, meta?: any): void;
    error(message: string, error?: Error, meta?: any): void;
    child(context: Record<string, any>): Logger;
}

// MCP Protocol Types
export interface MCPTool {
    name: string;
    description: string;
    inputSchema: Record<string, any>;
}

export interface MCPToolCall {
    name: string;
    arguments: Record<string, any>;
}

export interface MCPToolResult {
    content: Array<{
        type: 'text' | 'image' | 'file';
        text?: string;
        data?: any;
        mimeType?: string;
    }>;
    isError?: boolean;
    error?: string;
}

// Error Types
export class ConfigurationError extends Error {
    constructor(message: string, public serverName?: string) {
        super(message);
        this.name = 'ConfigurationError';
    }
}

export class ComplianceError extends Error {
    constructor(message: string, public ruleId?: string) {
        super(message);
        this.name = 'ComplianceError';
    }
}

export class RemediationError extends Error {
    constructor(message: string, public actionId?: string) {
        super(message);
        this.name = 'RemediationError';
    }
}

export class ServerNotFoundError extends Error {
    constructor(serverName: string) {
        super(`Server not found: ${serverName}`);
        this.name = 'ServerNotFoundError';
    }
}

export class ValidationError extends Error {
    constructor(message: string, public field?: string) {
        super(message);
        this.name = 'ValidationError';
    }
}

// Additional interfaces for MCP Compliance Server
export interface ServerStatus {
    name: string;
    configPath?: string;
    configExists: boolean;
    configValid?: boolean;
    healthy: boolean;
    lastChecked: string;
    issues: string[];
}

export interface ComplianceIssue {
    server: string;
    type: 'configuration' | 'health' | 'security' | 'performance';
    severity: 'low' | 'medium' | 'high' | 'critical';
    message: string;
    details?: any;
}

export interface Recommendation {
    type: 'remediation' | 'review' | 'optimization';
    priority: 'low' | 'medium' | 'high';
    message: string;
}

export interface AssessmentOptions {
    includeDetails: boolean;
    generateReport: boolean;
    saveResults: boolean;
}