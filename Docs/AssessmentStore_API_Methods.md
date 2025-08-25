# AssessmentStore API Method Specifications

## Overview

This document provides detailed specifications for the Promise-based API methods of the AssessmentStore service, designed to replace the EventEmitter-based system with centralized state management.

## Core API Methods

### 1. Assessment Creation Methods

#### `createAssessment(request: AssessmentRequest): Promise<string>`

**Purpose**: Creates a new assessment and returns its ID immediately for tracking.

**Parameters**:
- `request`: [`AssessmentRequest`](AssessmentStore_TypeScript_Interfaces.md#assessment-request-interface) - Assessment request details

**Returns**: `Promise<string>` - Assessment ID

**Behavior**:
1. Validates the assessment request
2. Generates a unique assessment ID if not provided
3. Stores initial state as `PENDING`
4. Returns assessment ID immediately
5. Triggers background processing

**Error Handling**:
- `ValidationError`: Invalid request parameters
- `DatabaseError`: Database connection or storage failure
- `RateLimitError`: Too many concurrent assessments

**Example**:
```typescript
const request: AssessmentRequest = {
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
  priority: 8
};

try {
  const assessmentId = await assessmentStore.createAssessment(request);
  console.log('Assessment created:', assessmentId);
  // Client can now use assessmentId for tracking
} catch (error) {
  console.error('Failed to create assessment:', error);
}
```

#### `batchCreateAssessments(requests: AssessmentRequest[]): Promise<string[]>`

**Purpose**: Creates multiple assessments in a single batch operation for efficiency.

**Parameters**:
- `requests`: [`AssessmentRequest[]`](AssessmentStore_TypeScript_Interfaces.md#assessment-request-interface) - Array of assessment requests

**Returns**: `Promise<string[]>` - Array of assessment IDs

**Behavior**:
1. Validates all requests
2. Uses batch database insert for efficiency
3. Returns all assessment IDs
4. Handles partial failures gracefully

**Error Handling**:
- `ValidationError`: One or more invalid requests
- `DatabaseError`: Batch insert failure
- `RateLimitError`: System capacity exceeded

### 2. Assessment State Management Methods

#### `getState(assessmentId: string): Promise<AssessmentState>`

**Purpose**: Retrieves the current state of an assessment.

**Parameters**:
- `assessmentId`: `string` - Unique assessment identifier

**Returns**: `Promise<AssessmentState>` - Current assessment state

**Behavior**:
1. Checks cache first for performance
2. Falls back to database query
3. Handles concurrent access safely
4. Returns complete state information

**Error Handling**:
- `AssessmentNotFoundError`: Assessment ID not found
- `DatabaseError`: Database query failure

**Example**:
```typescript
try {
  const state = await assessmentStore.getState('assessment_123');
  console.log('Current state:', state.state);
  console.log('Progress:', state.progress);
} catch (error) {
  if (error instanceof AssessmentNotFoundError) {
    console.error('Assessment not found');
  }
}
```

#### `waitForCompletion(assessmentId: string, timeout?: number): Promise<AssessmentState>`

**Purpose**: Waits for an assessment to complete and returns its final state.

**Parameters**:
- `assessmentId`: `string` - Unique assessment identifier
- `timeout`: `number` (optional) - Timeout in milliseconds (default: 30000)

**Returns**: `Promise<AssessmentState>` - Final assessment state

**Behavior**:
1. Uses efficient polling strategy
2. Implements proper timeout handling
3. Returns immediately if already completed
4. Emits progress updates during waiting

**Error Handling**:
- `AssessmentNotFoundError`: Assessment ID not found
- `AssessmentTimeoutError`: Assessment did not complete within timeout
- `DatabaseError`: Database query failure

**Example**:
```typescript
try {
  const finalState = await assessmentStore.waitForCompletion('assessment_123', 60000);
  if (finalState.state === AssessmentState.COMPLETED) {
    console.log('Assessment completed successfully');
    console.log('Result:', finalState.resultData);
  } else if (finalState.state === AssessmentState.FAILED) {
    console.error('Assessment failed:', finalState.errorMessage);
  }
} catch (error) {
  if (error instanceof AssessmentTimeoutError) {
    console.error('Assessment timed out after 60 seconds');
  }
}
```

#### `updateProgress(assessmentId: string, progress: number, message?: string): Promise<void>`

**Purpose**: Updates the progress of an assessment during processing.

**Parameters**:
- `assessmentId`: `string` - Unique assessment identifier
- `progress`: `number` - Progress percentage (0-100)
- `message`: `string` (optional) - Status message

**Returns**: `Promise<void>`

**Behavior**:
1. Validates progress range (0-100)
2. Uses optimistic locking for concurrent updates
3. Updates both cache and database
4. Emits progress update events
5. Logs audit trail

**Error Handling**:
- `AssessmentNotFoundError`: Assessment ID not found
- `AssessmentStateTransitionError`: Assessment not in PROCESSING state
- `AssessmentLockError`: Concurrent modification detected
- `ValidationError`: Invalid progress value

**Example**:
```typescript
try {
  await assessmentStore.updateProgress('assessment_123', 45, 'Checking server configurations');
  await assessmentStore.updateProgress('assessment_123', 75, 'Validating compliance rules');
  await assessmentStore.updateProgress('assessment_123', 100, 'Assessment completed');
} catch (error) {
  console.error('Failed to update progress:', error);
}
```

#### `completeAssessment(assessmentId: string, result: AssessmentResult): Promise<void>`

**Purpose**: Marks an assessment as completed with results.

**Parameters**:
- `assessmentId`: `string` - Unique assessment identifier
- `result`: [`AssessmentResult`](AssessmentStore_TypeScript_Interfaces.md#assessment-result-interface) - Assessment results

**Returns**: `Promise<void>`

**Behavior**:
1. Validates assessment is in PROCESSING state
2. Stores assessment results
3. Updates state to COMPLETED
4. Sets completion timestamp
5. Emits completion event
6. Logs audit trail

**Error Handling**:
- `AssessmentNotFoundError`: Assessment ID not found
- `AssessmentStateTransitionError`: Invalid state transition
- `AssessmentLockError`: Concurrent modification detected
- `ValidationError`: Invalid result data

**Example**:
```typescript
const result: AssessmentResult = {
  timestamp: new Date().toISOString(),
  totalServers: 10,
  compliantServers: 8,
  nonCompliantServers: 2,
  missingServers: [],
  configurationIssues: [],
  serverStatuses: [],
  overallScore: 80,
  summary: {
    criticalIssues: 0,
    highIssues: 1,
    mediumIssues: 2,
    lowIssues: 3
  }
};

try {
  await assessmentStore.completeAssessment('assessment_123', result);
  console.log('Assessment completed successfully');
} catch (error) {
  console.error('Failed to complete assessment:', error);
}
```

#### `failAssessment(assessmentId: string, error: string): Promise<void>`

**Purpose**: Marks an assessment as failed with error information.

**Parameters**:
- `assessmentId`: `string` - Unique assessment identifier
- `error`: `string` - Error message

**Returns**: `Promise<void>`

**Behavior**:
1. Validates assessment is in PROCESSING state
2. Stores error information
3. Updates state to FAILED
4. Sets completion timestamp
5. Emits failure event
6. Logs audit trail
7. May trigger retry logic

**Error Handling**:
- `AssessmentNotFoundError`: Assessment ID not found
- `AssessmentStateTransitionError`: Invalid state transition
- `AssessmentLockError`: Concurrent modification detected

**Example**:
```typescript
try {
  await assessmentStore.failAssessment('assessment_123', 'Connection timeout to compliance server');
  console.log('Assessment marked as failed');
} catch (error) {
  console.error('Failed to mark assessment as failed:', error);
}
```

#### `cancelAssessment(assessmentId: string, reason?: string): Promise<void>`

**Purpose**: Cancels an assessment in progress.

**Parameters**:
- `assessmentId`: `string` - Unique assessment identifier
- `reason`: `string` (optional) - Cancellation reason

**Returns**: `Promise<void>`

**Behavior**:
1. Validates assessment is in PENDING or PROCESSING state
2. Updates state to CANCELLED
3. Sets completion timestamp
4. Emits cancellation event
5. Logs audit trail
6. Cleans up resources

**Error Handling**:
- `AssessmentNotFoundError`: Assessment ID not found
- `AssessmentStateTransitionError`: Assessment cannot be cancelled
- `AssessmentLockError`: Concurrent modification detected

**Example**:
```typescript
try {
  await assessmentStore.cancelAssessment('assessment_123', 'User requested cancellation');
  console.log('Assessment cancelled successfully');
} catch (error) {
  console.error('Failed to cancel assessment:', error);
}
```

### 3. Query Methods

#### `listAssessments(filters: AssessmentFilters): Promise<AssessmentState[]>`

**Purpose**: Lists assessments with optional filtering and pagination.

**Parameters**:
- `filters`: [`AssessmentFilters`](AssessmentStore_TypeScript_Interfaces.md#assessment-filters-interface) - Filtering and pagination options

**Returns**: `Promise<AssessmentState[]>` - Array of assessment states

**Behavior**:
1. Applies filters to database query
2. Supports pagination
3. Uses optimized indexes
4. Returns sorted results
5. Handles large datasets efficiently

**Error Handling**:
- `ValidationError`: Invalid filter parameters
- `DatabaseError`: Database query failure

**Example**:
```typescript
const filters: AssessmentFilters = {
  state: [AssessmentState.COMPLETED, AssessmentState.FAILED],
  createdAfter: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
  limit: 50,
  sortBy: 'createdAt',
  sortOrder: 'desc'
};

try {
  const assessments = await assessmentStore.listAssessments(filters);
  console.log(`Found ${assessments.length} assessments`);
  assessments.forEach(assessment => {
    console.log(`${assessment.assessmentId}: ${assessment.state} (${assessment.progress}%)`);
  });
} catch (error) {
  console.error('Failed to list assessments:', error);
}
```

#### `searchAssessments(query: string): Promise<AssessmentState[]>`

**Purpose**: Searches assessments by various criteria.

**Parameters**:
- `query`: `string` - Search query

**Returns**: `Promise<AssessmentState[]>` - Matching assessment states

**Behavior**:
1. Searches across multiple fields (assessmentId, serverName, etc.)
2. Uses full-text search for efficiency
3. Returns ranked results
4. Supports fuzzy matching

**Error Handling**:
- `ValidationError`: Invalid search query
- `DatabaseError`: Search query failure

#### `getAssessmentStats(filters?: AssessmentFilters): Promise<AssessmentStats>`

**Purpose**: Gets statistics about assessments.

**Parameters**:
- `filters`: [`AssessmentFilters`](AssessmentStore_TypeScript_Interfaces.md#assessment-filters-interface) (optional) - Optional filtering

**Returns**: `Promise<AssessmentStats>` - Assessment statistics

**Behavior**:
1. Aggregates data from assessment states
2. Calculates various metrics
3. Returns comprehensive statistics
4. Uses optimized queries for performance

**Error Handling**:
- `DatabaseError`: Statistics query failure

**Example**:
```typescript
try {
  const stats = await assessmentStore.getAssessmentStats();
  console.log('Total assessments:', stats.totalAssessments);
  console.log('Completed:', stats.byState[AssessmentState.COMPLETED]);
  console.log('Failed:', stats.byState[AssessmentState.FAILED]);
  console.log('Success rate:', stats.successRate);
} catch (error) {
  console.error('Failed to get assessment stats:', error);
}
```

### 4. Batch Operations

#### `batchUpdateProgress(updates: Array<{assessmentId: string, progress: number, message?: string}>): Promise<void>`

**Purpose**: Updates progress for multiple assessments in a single operation.

**Parameters**:
- `updates`: `Array<{assessmentId: string, progress: number, message?: string}>` - Array of progress updates

**Returns**: `Promise<void>`

**Behavior**:
1. Validates all updates
2. Uses batch database update
3. Handles partial failures
4. Emits individual events
5. Logs audit trail

**Error Handling**:
- `ValidationError`: Invalid update parameters
- `DatabaseError`: Batch update failure

#### `batchRetryFailedAssessments(maxRetries: number): Promise<string[]>`

**Purpose**: Retries failed assessments that haven't exceeded retry limits.

**Parameters**:
- `maxRetries`: `number` - Maximum number of retry attempts

**Returns**: `Promise<string[]>` - Array of assessment IDs that were queued for retry

**Behavior**:
1. Identifies failed assessments eligible for retry
2. Resets state to PENDING
3. Increments retry count
4. Schedules retry execution
5. Returns list of retried assessments

**Error Handling**:
- `DatabaseError`: Database operation failure

### 5. Maintenance Methods

#### `cleanupOldAssessments(retentionDays: number): Promise<number>`

**Purpose**: Cleans up old assessments based on retention policy.

**Parameters**:
- `retentionDays`: `number` - Number of days to retain assessments

**Returns**: `Promise<number>` - Number of assessments cleaned up

**Behavior**:
1. Identifies assessments older than retention period
2. Deletes from database
3. Cleans up related data (audit logs, metrics)
4. Returns cleanup count
5. Logs cleanup operation

**Error Handling**:
- `DatabaseError`: Database cleanup failure

#### `getHealthStatus(): Promise<HealthStatus>`

**Purpose**: Gets the health status of the AssessmentStore service.

**Returns**: `Promise<HealthStatus>` - Service health status

**Behavior**:
1. Checks database connectivity
2. Validates cache functionality
3. Checks queue status
4. Assesses overall health
5. Returns detailed health information

**Error Handling**:
- `HealthCheckError`: Health check failure

**Example**:
```typescript
try {
  const health = await assessmentStore.getHealthStatus();
  console.log('Overall health:', health.overall);
  console.log('Database:', health.services.database);
  console.log('Cache:', health.services.cache);
  console.log('Queue:', health.services.queue);
} catch (error) {
  console.error('Health check failed:', error);
}
```

#### `getMetrics(): Promise<AssessmentMetrics>`

**Purpose**: Gets performance metrics for the AssessmentStore service.

**Returns**: `Promise<AssessmentMetrics>` - Service metrics

**Behavior**:
1. Collects various performance metrics
2. Calculates derived metrics
3. Returns comprehensive metrics data
4. Includes timestamp for metrics

**Error Handling**:
- `MetricsError`: Metrics collection failure

**Example**:
```typescript
try {
  const metrics = await assessmentStore.getMetrics();
  console.log('Total assessments:', metrics.totalAssessments);
  console.log('Active assessments:', metrics.activeAssessments);
  console.log('Average processing time:', metrics.averageProcessingTime, 'ms');
  console.log('Throughput:', metrics.throughputPerMinute, 'assessments/minute');
  console.log('Error rate:', metrics.errorRate, '%');
} catch (error) {
  console.error('Failed to get metrics:', error);
}
```

### 6. Migration Methods

#### `isMigrationComplete(): Promise<boolean>`

**Purpose**: Checks if the migration from legacy system is complete.

**Returns**: `Promise<boolean>` - True if migration is complete

**Behavior**:
1. Checks migration status
2. Validates data consistency
3. Returns completion status

**Error Handling**:
- `MigrationError`: Migration status check failure

#### `enableLegacyMode(enabled: boolean): Promise<void>`

**Purpose**: Enables or disables legacy event system fallback.

**Parameters**:
- `enabled`: `boolean` - Whether to enable legacy mode

**Returns**: `Promise<void>`

**Behavior**:
1. Updates configuration
2. Enables/disables legacy event handling
3. Triggers mode switch

**Error Handling**:
- `ConfigurationError`: Configuration update failure

#### `getMigrationStatus(): Promise<MigrationStatus>`

**Purpose**: Gets detailed migration status information.

**Returns**: `Promise<MigrationStatus>` - Migration status details

**Behavior**:
1. Collects migration metrics
2. Calculates migration percentage
3. Returns comprehensive status

**Error Handling**:
- `MigrationError`: Migration status retrieval failure

## Advanced Usage Patterns

### 1. Progress Tracking with Callbacks

```typescript
// Track assessment progress with real-time updates
const assessmentId = await assessmentStore.createAssessment(request);

const subscription = assessmentStore.on(['assessment.progress'], (event) => {
  console.log(`Progress: ${event.progress}% - ${event.message}`);
});

try {
  const finalState = await assessmentStore.waitForCompletion(assessmentId);
  console.log('Assessment completed:', finalState.state);
} finally {
  assessmentStore.off(subscription.id);
}
```

### 2. Error Recovery with Retry Logic

```typescript
async function createAssessmentWithRetry(request: AssessmentRequest, maxRetries = 3): Promise<string> {
  let lastError: Error;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await assessmentStore.createAssessment(request);
    } catch (error) {
      lastError = error;
      if (attempt === maxRetries) break;
      
      // Exponential backoff
      const delay = Math.pow(2, attempt) * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError!;
}
```

### 3. Batch Processing with Error Handling

```typescript
async function processBatchAssessments(requests: AssessmentRequest[]): Promise<void> {
  const assessmentIds = await assessmentStore.batchCreateAssessments(requests);
  const results: Array<{assessmentId: string, success: boolean, error?: string}> = [];
  
  for (const assessmentId of assessmentIds) {
    try {
      const state = await assessmentStore.waitForCompletion(assessmentId, 60000);
      results.push({
        assessmentId,
        success: state.state === AssessmentState.COMPLETED
      });
    } catch (error) {
      results.push({
        assessmentId,
        success: false,
        error: error.message
      });
    }
  }
  
  // Process results
  const successful = results.filter(r => r.success).length;
  const failed = results.filter(r => !r.success).length;
  
  console.log(`Batch processed: ${successful} successful, ${failed} failed`);
  
  // Handle failed assessments
  if (failed > 0) {
    const failedIds = results.filter(r => !r.success).map(r => r.assessmentId);
    await assessmentStore.batchRetryFailedAssessments(3);
  }
}
```

### 4. Monitoring and Alerting

```typescript
// Set up monitoring for critical metrics
const metrics = await assessmentStore.getMetrics();
const health = await assessmentStore.getHealthStatus();

// Alert on high error rate
if (metrics.errorRate > 10) {
  console.warn(`High error rate detected: ${metrics.errorRate}%`);
  // Trigger alert system
}

// Alert on unhealthy services
if (health.overall !== 'healthy') {
  console.warn(`Service health degraded: ${health.overall}`);
  // Trigger alert system
}

// Monitor long-running assessments
const longRunning = await assessmentStore.listAssessments({
  state: AssessmentState.PROCESSING,
  createdBefore: new Date(Date.now() - 30 * 60 * 1000).toISOString()
});

if (longRunning.length > 0) {
  console.warn(`${longRunning.length} assessments running for more than 30 minutes`);
}
```

## Performance Considerations

### 1. Caching Strategy
- Use `getState()` with caching for frequently accessed assessments
- Implement client-side caching for read-heavy workloads
- Cache results for completed assessments

### 2. Batch Operations
- Use `batchCreateAssessments()` for bulk assessment creation
- Use `batchUpdateProgress()` for bulk progress updates
- Minimize database round trips

### 3. Timeout Handling
- Always use appropriate timeouts for `waitForCompletion()`
- Implement retry logic for transient failures
- Monitor for stuck assessments

### 4. Error Handling
- Handle specific error types appropriately
- Implement retry logic for retryable errors
- Log errors for debugging and monitoring

These API method specifications provide a comprehensive foundation for the AssessmentStore service, ensuring reliable, efficient, and maintainable assessment state management while addressing all the requirements identified in the current system analysis.