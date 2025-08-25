# AssessmentStore TypeScript Interface Definitions

## Overview

This document provides comprehensive TypeScript interface definitions for the AssessmentStore service, designed to replace the EventEmitter-based system with centralized state management.

## Core Interfaces

### 1. Assessment State Enums

```typescript
/**
 * Assessment lifecycle states
 */
export enum AssessmentState {
  PENDING = 'pending',           // Assessment requested, not started
  PROCESSING = 'processing',     // Assessment in progress
  COMPLETED = 'completed',       // Assessment finished successfully
  FAILED = 'failed',            // Assessment failed
  CANCELLED = 'cancelled'       // Assessment cancelled by user
}

/**
 * Assessment types
 */
export enum AssessmentType {
  COMPLIANCE = 'compliance',
  HEALTH = 'health',
  SECURITY = 'security'
}

/**
 * Assessment severities
 */
export enum AssessmentSeverity {
  CRITICAL = 'critical',
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low'
}

/**
 * Server status types
 */
export enum ServerStatus {
  ONLINE = 'online',
  OFFLINE = 'offline',
  ERROR = 'error',
  UNKNOWN = 'unknown'
}

/**
 * Issue types
 */
export enum IssueType {
  MISSING_CONFIG = 'missing_config',
  INCOMPLETE_CONFIG = 'incomplete_config',
  INVALID_CONFIG = 'invalid_config',
  SECURITY_ISSUE = 'security_issue',
  PERFORMANCE_ISSUE = 'performance_issue'
}

/**
 * Remediation action types
 */
export enum RemediationActionType {
  INSTALL_SERVER = 'install_server',
  UPDATE_CONFIG = 'update_config',
  REMOVE_SERVER = 'remove_server',
  FIX_SECURITY = 'fix_security',
  OPTIMIZE_PERFORMANCE = 'optimize_performance'
}
```

### 2. Core Assessment Interfaces

```typescript
/**
 * Assessment request interface
 */
export interface AssessmentRequest {
  /** Unique assessment identifier */
  id: string;
  
  /** Name of the server being assessed */
  serverName?: string;
  
  /** Type of assessment */
  assessmentType: AssessmentType;
  
  /** Assessment options and configuration */
  options: AssessmentOptions;
  
  /** Request timestamp */
  timestamp: string;
  
  /** Source of the request */
  source: 'installer' | 'compliance';
  
  /** Priority level (1-10, higher is more important) */
  priority?: number;
  
  /** Timeout in seconds */
  timeout?: number;
  
  /** Request metadata */
  metadata?: Record<string, any>;
}

/**
 * Assessment options interface
 */
export interface AssessmentOptions {
  /** Include detailed assessment results */
  includeDetails: boolean;
  
  /** Generate assessment report */
  generateReport: boolean;
  
  /** Save results to database */
  saveResults: boolean;
  
  /** Check server status during assessment */
  checkServerStatus: boolean;
  
  /** Validate configuration */
  validateConfig: boolean;
  
  /** Check compliance */
  checkCompliance: boolean;
  
  /** Filter servers by name pattern */
  serverFilter?: string[];
  
  /** Perform deep scan */
  deepScan: boolean;
  
  /** Custom timeout override */
  timeout?: number;
  
  /** Additional custom options */
  customOptions?: Record<string, any>;
}

/**
 * Assessment state interface
 */
export interface AssessmentState {
  /** Assessment identifier */
  assessmentId: string;
  
  /** Current state of the assessment */
  state: AssessmentState;
  
  /** Version number for optimistic locking */
  version: number;
  
  /** Progress percentage (0-100) */
  progress: number;
  
  /** Status message */
  message?: string;
  
  /** Request creation timestamp */
  createdAt: string;
  
  /** Last update timestamp */
  updatedAt: string;
  
  /** Completion timestamp (if applicable) */
  completedAt?: string;
  
  /** Original request data */
  requestData: AssessmentRequest;
  
  /** Assessment results (if completed) */
  resultData?: AssessmentResult;
  
  /** Error message (if failed) */
  errorMessage?: string;
  
  /** Number of retry attempts */
  retryCount: number;
  
  /** Next retry timestamp (if applicable) */
  nextRetryAt?: string;
  
  /** Processing duration in milliseconds */
  duration?: number;
}

/**
 * Assessment result interface
 */
export interface AssessmentResult {
  /** Assessment completion timestamp */
  timestamp: string;
  
  /** Total number of servers assessed */
  totalServers: number;
  
  /** Number of compliant servers */
  compliantServers: number;
  
  /** Number of non-compliant servers */
  nonCompliantServers: number;
  
  /** List of missing servers */
  missingServers: string[];
  
  /** Configuration issues found */
  configurationIssues: ConfigurationIssue[];
  
  /** Server status information */
  serverStatuses: ServerStatusInfo[];
  
  /** Overall compliance score (0-100) */
  overallScore: number;
  
  /** Summary of issues by severity */
  summary: AssessmentSummary;
  
  /** Generated report (if requested) */
  report?: AssessmentReport;
  
  /** Additional metadata */
  metadata?: Record<string, any>;
}

/**
 * Configuration issue interface
 */
export interface ConfigurationIssue {
  /** Unique issue identifier */
  id: string;
  
  /** Server name where issue was found */
  serverName: string;
  
  /** Type of issue */
  issueType: IssueType;
  
  /** Severity level */
  severity: AssessmentSeverity;
  
  /** Issue description */
  description: string;
  
  /** Detailed issue information */
  details: Record<string, any>;
  
  /** Recommended action */
  recommendation: string;
  
  /** Remediation priority */
  priority?: number;
  
  /** Issue category */
  category?: string;
}

/**
 * Server status information interface
 */
export interface ServerStatusInfo {
  /** Server name */
  name: string;
  
  /** Server status */
  status: ServerStatus;
  
  /** Command used to check server */
  command: string;
  
  /** Command arguments */
  args: string[];
  
  /** Environment variables */
  env?: Record<string, string>;
  
  /** Last check timestamp */
  lastCheck: string;
  
  /** Response time in milliseconds */
  responseTime?: number;
  
  /** Error message (if applicable) */
  error?: string;
  
  /** Additional server metadata */
  metadata?: Record<string, any>;
}

/**
 * Assessment summary interface
 */
export interface AssessmentSummary {
  /** Number of critical issues */
  criticalIssues: number;
  
  /** Number of high severity issues */
  highIssues: number;
  
  /** Number of medium severity issues */
  mediumIssues: number;
  
  /** Number of low severity issues */
  lowIssues: number;
  
  /** Total issues found */
  get totalIssues(): number;
  
  /** Compliance percentage */
  get compliancePercentage(): number;
}

/**
 * Assessment report interface
 */
export interface AssessmentReport {
  /** Report generation timestamp */
  generatedAt: string;
  
  /** Report format (html, pdf, json) */
  format: 'html' | 'pdf' | 'json';
  
  /** Report content */
  content: string;
  
  /** Report size in bytes */
  size: number;
  
  /** Report download URL (if applicable) */
  downloadUrl?: string;
}
```

### 3. Remediation Interfaces

```typescript
/**
 * Remediation action interface
 */
export interface RemediationAction {
  /** Unique action identifier */
  id: string;
  
  /** Type of remediation action */
  type: RemediationActionType;
  
  /** Target server name */
  serverName: string;
  
  /** Action description */
  description: string;
  
  /** Command to execute */
  command?: string;
  
  /** Command arguments */
  args?: string[];
  
  /** Environment variables */
  env?: Record<string, string>;
  
  /** Rollback command */
  rollbackCommand?: string;
  
  /** Rollback arguments */
  rollbackArgs?: string[];
  
  /** Rollback environment variables */
  rollbackEnv?: Record<string, string>;
  
  /** Estimated execution time in seconds */
  estimatedTime: number;
  
  /** Whether server restart is required */
  requiresRestart: boolean;
  
  /** Action dependencies */
  dependencies: string[];
  
  /** Action priority */
  priority?: number;
  
  /** Risk assessment */
  riskAssessment?: RiskAssessment;
}

/**
 * Risk assessment interface
 */
export interface RiskAssessment {
  /** Risk level */
  level: 'low' | 'medium' | 'high' | 'critical';
  
  ** Potential impact */
  impact: string;
  
  ** Likelihood of occurrence (0-1) */
  likelihood: number;
  
  ** Mitigation strategies */
  mitigation: string;
  
  ** Risk score (0-100) */
  get riskScore(): number;
}

/**
 * Remediation proposal interface
 */
export interface RemediationProposal {
  /** Unique proposal identifier */
  proposalId: string;
  
  /** Associated assessment ID */
  assessmentId: string;
  
  /** List of remediation actions */
  actions: RemediationAction[];
  
  ** Overall risk assessment */
  riskAssessment: RiskAssessment;
  
  /** Total estimated time */
  estimatedTime: number;
  
  /** Whether proposal requires approval */
  requiresApproval: boolean;
  
  ** Proposal timestamp */
  timestamp: string;
  
  ** Expiration timestamp */
  expiresAt?: string;
}
```

### 4. Audit and Monitoring Interfaces

```typescript
/**
 * Audit log entry interface
 */
export interface AuditLog {
  /** Unique audit log identifier */
  id: string;
  
  /** Assessment ID */
  assessmentId: string;
  
  /** Previous state (if applicable) */
  oldState?: AssessmentState;
  
  ** New state */
  newState: AssessmentState;
  
  ** Version before change */
  versionFrom?: number;
  
  ** Version after change */
  versionTo: number;
  
  ** User or service making the change */
  changedBy: string;
  
  ** Reason for the change */
  changeReason?: string;
  
  ** Action that triggered the change */
  changeAction: string;
  
  ** Change timestamp */
  createdAt: string;
  
  ** Additional context */
  context?: Record<string, any>;
  
  ** IP address of requester */
  ipAddress?: string;
  
  ** User agent of requester */
  userAgent?: string;
}

/**
 * Assessment metrics interface
 */
export interface AssessmentMetrics {
  /** Total number of assessments */
  totalAssessments: number;
  
  ** Number of active assessments */
  activeAssessments: number;
  
  ** Number of completed assessments */
  completedAssessments: number;
  
  ** Number of failed assessments */
  failedAssessments: number;
  
  ** Number of cancelled assessments */
  cancelledAssessments: number;
  
  ** Average processing time in milliseconds */
  averageProcessingTime: number;
  
  ** Throughput (assessments per minute) */
  throughputPerMinute: number;
  
  ** Error rate (percentage) */
  errorRate: number;
  
  ** Retry rate (percentage) */
  retryRate: number;
  
  ** Success rate (percentage) */
  successRate: number;
  
  ** Metrics timestamp */
  timestamp: string;
}

/**
 * Health status interface
 */
export interface HealthStatus {
  ** Overall health status */
  overall: 'healthy' | 'degraded' | 'unhealthy';
  
  ** Service health details */
  services: {
    database: 'healthy' | 'degraded' | 'unhealthy';
    cache: 'healthy' | 'degraded' | 'unhealthy';
    queue: 'healthy' | 'degraded' | 'unhealthy';
  };
  
  ** Last health check timestamp */
  lastUpdated: string;
  
  ** Health check details */
  details?: Record<string, any>;
}
```

### 5. Filter and Query Interfaces

```typescript
/**
 * Assessment filters interface
 */
export interface AssessmentFilters {
  /** Filter by assessment state */
  state?: AssessmentState | AssessmentState[];
  
  /** Filter by assessment type */
  assessmentType?: AssessmentType | AssessmentType[];
  
  ** Filter by server name pattern */
  serverName?: string;
  
  ** Filter by date range */
  createdAfter?: string;
  createdBefore?: string;
  
  ** Filter by completion date range */
  completedAfter?: string;
  completedBefore?: string;
  
  ** Filter by priority range */
  minPriority?: number;
  maxPriority?: number;
  
  ** Filter by progress range */
  minProgress?: number;
  maxProgress?: number;
  
  ** Filter by source */
  source?: 'installer' | 'compliance';
  
  ** Pagination */
  limit?: number;
  offset?: number;
  
  ** Sorting */
  sortBy?: 'createdAt' | 'updatedAt' | 'priority' | 'progress';
  sortOrder?: 'asc' | 'desc';
}

/**
 * Assessment statistics interface
 */
export interface AssessmentStats {
  ** Total assessments by state */
  byState: Record<AssessmentState, number>;
  
  ** Total assessments by type */
  byType: Record<AssessmentType, number>;
  
  ** Average processing time by state */
  avgProcessingTimeByState: Record<AssessmentState, number>;
  
  ** Success rate by type */
  successRateByType: Record<AssessmentType, number>;
  
  ** Daily assessment counts */
  dailyCounts: Array<{
    date: string;
    count: number;
    completed: number;
    failed: number;
  }>;
  
  ** Top servers by assessment count */
  topServers: Array<{
    serverName: string;
    assessmentCount: number;
    lastAssessment: string;
  }>;
}
```

### 6. Service Interfaces

```typescript
/**
 * AssessmentStore configuration interface
 */
export interface AssessmentStoreConfig {
  ** Database configuration */
  database: {
    host: string;
    port: number;
    database: string;
    username: string;
    password: string;
    ssl?: boolean;
    maxConnections?: number;
    connectionTimeout?: number;
  };
  
  ** Cache configuration */
  cache?: {
    enabled: boolean;
    redis?: {
      host: string;
      port: number;
      password?: string;
      db?: number;
    };
    ttl?: number;
  };
  
  ** Queue configuration */
  queue?: {
    enabled: boolean;
    maxRetries?: number;
    retryDelay?: number;
  };
  
  ** Performance configuration */
  performance: {
    maxConcurrentAssessments?: number;
    defaultTimeout?: number;
    metricsInterval?: number;
    cleanupInterval?: number;
  };
  
  ** Migration configuration */
  migration?: {
    enableLegacyFallback: boolean;
    migrationPercentage?: number;
    enableMetrics: boolean;
  };
  
  ** Logging configuration */
  logging: {
    level: 'debug' | 'info' | 'warn' | 'error';
    enableAudit: boolean;
    enableMetrics: boolean;
  };
}

/**
 * AssessmentStore service interface
 */
export interface AssessmentStore {
  // Core assessment operations
  createAssessment(request: AssessmentRequest): Promise<string>;
  waitForCompletion(assessmentId: string, timeout?: number): Promise<AssessmentState>;
  getState(assessmentId: string): Promise<AssessmentState>;
  updateProgress(assessmentId: string, progress: number, message?: string): Promise<void>;
  completeAssessment(assessmentId: string, result: AssessmentResult): Promise<void>;
  failAssessment(assessmentId: string, error: string): Promise<void>;
  cancelAssessment(assessmentId: string, reason?: string): Promise<void>;
  
  // Query operations
  listAssessments(filters: AssessmentFilters): Promise<AssessmentState[]>;
  getAssessmentStats(filters?: AssessmentFilters): Promise<AssessmentStats>;
  searchAssessments(query: string): Promise<AssessmentState[]>;
  
  // Batch operations
  batchCreateAssessments(requests: AssessmentRequest[]): Promise<string[]>;
  batchUpdateProgress(updates: Array<{assessmentId: string, progress: number, message?: string}>): Promise<void>;
  batchRetryFailedAssessments(maxRetries: number): Promise<string[]>;
  
  // Maintenance operations
  cleanupOldAssessments(retentionDays: number): Promise<number>;
  getHealthStatus(): Promise<HealthStatus>;
  getMetrics(): Promise<AssessmentMetrics>;
  
  // Migration operations
  isMigrationComplete(): Promise<boolean>;
  enableLegacyMode(enabled: boolean): Promise<void>;
  getMigrationStatus(): Promise<{
    legacyMode: boolean;
    migrationPercentage: number;
    assessmentsMigrated: number;
    totalAssessments: number;
  }>;
}

/**
 * AssessmentStore factory interface
 */
export interface AssessmentStoreFactory {
  create(config: AssessmentStoreConfig): Promise<AssessmentStore>;
  createWithLegacyFallback(config: AssessmentStoreConfig, legacyEventService: any): Promise<AssessmentStore>;
}
```

### 7. Error Handling Interfaces

```typescript
/**
 * AssessmentStore error types
 */
export class AssessmentStoreError extends Error {
  constructor(
    message: string,
    public code: string,
    public assessmentId?: string,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = 'AssessmentStoreError';
  }
}

export class AssessmentNotFoundError extends AssessmentStoreError {
  constructor(assessmentId: string) {
    super(`Assessment not found: ${assessmentId}`, 'ASSESSMENT_NOT_FOUND', assessmentId);
    this.name = 'AssessmentNotFoundError';
  }
}

export class AssessmentStateTransitionError extends AssessmentStoreError {
  constructor(assessmentId: string, fromState: AssessmentState, toState: AssessmentState) {
    super(
      `Invalid state transition: ${assessmentId} from ${fromState} to ${toState}`,
      'INVALID_STATE_TRANSITION',
      assessmentId,
      { fromState, toState }
    );
    this.name = 'AssessmentStateTransitionError';
  }
}

export class AssessmentTimeoutError extends AssessmentStoreError {
  constructor(assessmentId: string, timeout: number) {
    super(
      `Assessment timeout: ${assessmentId} after ${timeout}ms`,
      'ASSESSMENT_TIMEOUT',
      assessmentId,
      { timeout }
    );
    this.name = 'AssessmentTimeoutError';
  }
}

export class AssessmentLockError extends AssessmentStoreError {
  constructor(assessmentId: string, expectedVersion: number, actualVersion: number) {
    super(
      `Optimistic lock failed: ${assessmentId}. Expected version ${expectedVersion}, got ${actualVersion}`,
      'OPTIMISTIC_LOCK_FAILED',
      assessmentId,
      { expectedVersion, actualVersion }
    );
    this.name = 'AssessmentLockError';
  }
}

/**
 * Error response interface
 */
export interface ErrorResponse {
  /** Error code */
  code: string;
  
  /** Error message */
  message: string;
  
  /** Error details */
  details?: Record<string, any>;
  
  /** Assessment ID (if applicable) */
  assessmentId?: string;
  
  ** Error timestamp */
  timestamp: string;
  
  ** Error severity */
  severity: 'low' | 'medium' | 'high' | 'critical';
}
```

### 8. Event and Callback Interfaces

```typescript
/**
 * Assessment event types
 */
export type AssessmentEvent = 
  | { type: 'assessment.created'; assessmentId: string; data: AssessmentRequest }
  | { type: 'assessment.started'; assessmentId: string; timestamp: string }
  | { type: 'assessment.progress'; assessmentId: string; progress: number; message?: string }
  | { type: 'assessment.completed'; assessmentId: string; result: AssessmentResult; duration: number }
  | { type: 'assessment.failed'; assessmentId: string; error: string; duration: number }
  | { type: 'assessment.cancelled'; assessmentId: string; reason?: string; duration: number };

/**
 * Event handler interface
 */
export type AssessmentEventHandler = (event: AssessmentEvent) => void | Promise<void>;

/**
 * Event subscription interface
 */
export interface EventSubscription {
  /** Subscription ID */
  id: string;
  
  /** Event types to subscribe to */
  eventTypes: string[];
  
  /** Event handler */
  handler: AssessmentEventHandler;
  
  /** Whether subscription is active */
  active: boolean;
  
  ** Subscription timestamp */
  createdAt: string;
}

/**
 * Event emitter interface for AssessmentStore
 */
export interface AssessmentEventEmitter {
  /** Subscribe to assessment events */
  on(eventTypes: string[], handler: AssessmentEventHandler): EventSubscription;
  
  /** Unsubscribe from assessment events */
  off(subscriptionId: string): boolean;
  
  /** Emit assessment event */
  emit(event: AssessmentEvent): Promise<void>;
  
  /** Get active subscriptions */
  getSubscriptions(): EventSubscription[];
  
  /** Clear all subscriptions */
  clear(): void;
}
```

## Usage Examples

### 1. Basic Assessment Creation

```typescript
const assessmentRequest: AssessmentRequest = {
  id: 'assessment_123',
  serverName: 'web-server-01',
  assessmentType: AssessmentType.COMPLIANCE,
  options: {
    includeDetails: true,
    generateReport: true,
    saveResults: true,
    checkServerStatus: true,
    validateConfig: true,
    checkCompliance: true,
    deepScan: false
  },
  timestamp: new Date().toISOString(),
  source: 'installer',
  priority: 8,
  timeout: 600
};

const assessmentId = await assessmentStore.createAssessment(assessmentRequest);
console.log('Assessment created:', assessmentId);
```

### 2. Waiting for Assessment Completion

```typescript
try {
  const assessmentState = await assessmentStore.waitForCompletion(assessmentId, 30000);
  console.log('Assessment completed:', assessmentState.state);
  
  if (assessmentState.state === AssessmentState.COMPLETED) {
    console.log('Result:', assessmentState.resultData);
  } else if (assessmentState.state === AssessmentState.FAILED) {
    console.error('Assessment failed:', assessmentState.errorMessage);
  }
} catch (error) {
  if (error instanceof AssessmentTimeoutError) {
    console.error('Assessment timed out');
  } else {
    console.error('Error waiting for assessment:', error);
  }
}
```

### 3. Querying Assessments

```typescript
const filters: AssessmentFilters = {
  state: [AssessmentState.COMPLETED, AssessmentState.FAILED],
  createdAfter: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
  limit: 50,
  sortBy: 'createdAt',
  sortOrder: 'desc'
};

const assessments = await assessmentStore.listAssessments(filters);
console.log(`Found ${assessments.length} assessments`);
```

### 4. Error Handling

```typescript
try {
  await assessmentStore.completeAssessment(assessmentId, result);
} catch (error) {
  if (error instanceof AssessmentNotFoundError) {
    console.error('Assessment not found:', error.assessmentId);
  } else if (error instanceof AssessmentLockError) {
    console.error('Concurrent modification detected');
    // Retry logic here
  } else {
    console.error('Unexpected error:', error);
  }
}
```

These interface definitions provide a comprehensive foundation for the AssessmentStore service, ensuring type safety, clear contracts, and maintainable code while addressing all the requirements identified in the current system analysis.