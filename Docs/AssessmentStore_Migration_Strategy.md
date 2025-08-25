# AssessmentStore Migration Strategy

## Overview

This document outlines a comprehensive migration strategy for transitioning from the current EventEmitter-based system to the new AssessmentStore service. The strategy ensures zero-downtime migration, minimal risk, and maintains full compatibility with existing systems.

## Migration Principles

### 1. Zero-Downtime Migration
- **Gradual Rollout**: Feature flags allow gradual enablement
- **Dual-Mode Operation**: Both systems run in parallel during transition
- **Rollback Capability**: Immediate rollback to legacy system if issues arise

### 2. Data Consistency
- **Atomic Migration**: Data migration in atomic transactions
- **Validation**: Comprehensive validation of migrated data
- **Audit Trail**: Complete audit trail of all migration operations

### 3. Risk Mitigation
- **Phased Approach**: Migration in manageable phases
- **Testing**: Extensive testing at each phase
- **Monitoring**: Enhanced monitoring during migration

## Migration Architecture

### 1. Dual-Mode Service Architecture

```typescript
class AssessmentStoreMigrationService implements AssessmentStore {
  private useAssessmentStore: boolean;
  private assessmentStore: AssessmentStore;
  private legacyEventService: EventService;
  private migrationConfig: MigrationConfig;
  
  constructor(config: MigrationConfig) {
    this.migrationConfig = config;
    this.useAssessmentStore = config.enableAssessmentStore;
    
    // Initialize both services
    this.assessmentStore = new AssessmentStore(config.assessmentStoreConfig);
    this.legacyEventService = new EventService(config.legacyEventConfig);
  }
  
  async createAssessment(request: AssessmentRequest): Promise<string> {
    if (this.useAssessmentStore) {
      return this.assessmentStore.createAssessment(request);
    } else {
      return this.createAssessmentLegacy(request);
    }
  }
  
  async waitForCompletion(assessmentId: string, timeout?: number): Promise<AssessmentState> {
    if (this.useAssessmentStore) {
      return this.assessmentStore.waitForCompletion(assessmentId, timeout);
    } else {
      return this.waitForCompletionLegacy(assessmentId, timeout);
    }
  }
  
  // Bridge legacy system to new system
  private async waitForCompletionLegacy(assessmentId: string, timeout?: number): Promise<AssessmentState> {
    return new Promise((resolve, reject) => {
      const handler = (data: any) => {
        if (data.assessmentId === assessmentId) {
          this.legacyEventService.off('assessment.completed', handler);
          
          // Convert legacy event to AssessmentStore format
          const state: AssessmentState = {
            assessmentId: data.assessmentId,
            state: this.convertLegacyState(data.status),
            version: 1,
            progress: data.progress || 0,
            message: data.message,
            createdAt: data.timestamp,
            updatedAt: new Date().toISOString(),
            requestData: data.request,
            resultData: data.result,
            errorMessage: data.error,
            retryCount: 0,
            duration: data.duration
          };
          
          resolve(state);
        }
      };
      
      this.legacyEventService.on('assessment.completed', handler);
      
      // Timeout handling
      const timeoutId = setTimeout(() => {
        this.legacyEventService.off('assessment.completed', handler);
        reject(new AssessmentTimeoutError(assessmentId, timeout || 30000));
      }, timeout || 30000);
      
      // Check if assessment already completed
      this.checkLegacyAssessmentStatus(assessmentId).then((status) => {
        if (status.completed) {
          clearTimeout(timeoutId);
          this.legacyEventService.off('assessment.completed', handler);
          resolve(status.state);
        }
      });
    });
  }
  
  private convertLegacyState(legacyState: string): AssessmentState {
    const stateMap: Record<string, AssessmentState> = {
      'pending': AssessmentState.PENDING,
      'processing': AssessmentState.PROCESSING,
      'completed': AssessmentState.COMPLETED,
      'failed': AssessmentState.FAILED,
      'cancelled': AssessmentState.CANCELLED
    };
    
    return stateMap[legacyState] || AssessmentState.FAILED;
  }
}
```

### 2. Feature Flag System

```typescript
interface MigrationConfig {
  enableAssessmentStore: boolean;
  enableLegacyFallback: boolean;
  migrationPercentage: number; // 0-100
  enableMetrics: boolean;
  enableAuditLogging: boolean;
  enableDualMode: boolean;
}

class FeatureFlagManager {
  private config: MigrationConfig;
  private random: () => number;
  
  constructor(config: MigrationConfig) {
    this.config = config;
    this.random = Math.random;
  }
  
  shouldUseAssessmentStore(): boolean {
    if (!this.config.enableAssessmentStore) {
      return false;
    }
    
    if (!this.config.enableDualMode) {
      return true;
    }
    
    // Use percentage-based routing
    return this.random() * 100 < this.config.migrationPercentage;
  }
  
  getMigrationStatus(): MigrationStatus {
    return {
      legacyMode: !this.shouldUseAssessmentStore(),
      migrationPercentage: this.config.migrationPercentage,
      assessmentsMigrated: this.getAssessmentsMigratedCount(),
      totalAssessments: this.getTotalAssessmentsCount(),
      lastUpdated: new Date().toISOString()
    };
  }
  
  updateConfig(newConfig: Partial<MigrationConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }
}
```

## Migration Phases

### Phase 1: Preparation (Weeks 1-2)

#### 1.1 Environment Setup
```bash
# Set up migration environment
kubectl create namespace assessment-store-migration
kubectl apply -f migration-config.yaml

# Initialize database schema
psql -f schema/migration-setup.sql

# Set up monitoring
kubectl apply -f monitoring/migration-alerts.yaml
```

#### 1.2 Data Export
```typescript
class DataExporter {
  async exportLegacyAssessments(): Promise<LegacyAssessment[]> {
    const assessments: LegacyAssessment[] = [];
    
    // Export from legacy event system
    const legacyAssessments = await this.queryLegacyAssessments();
    
    for (const legacy of legacyAssessments) {
      assessments.push({
        id: legacy.assessmentId,
        state: this.convertLegacyState(legacy.status),
        requestData: legacy.request,
        resultData: legacy.result,
        createdAt: legacy.timestamp,
        updatedAt: legacy.updatedAt,
        errorMessage: legacy.error,
        progress: legacy.progress || 0
      });
    }
    
    return assessments;
  }
  
  async exportLegacyAuditLogs(): Promise<AuditLog[]> {
    // Export audit logs from legacy system
    return this.queryLegacyAuditLogs();
  }
}
```

#### 1.3 Validation Scripts
```typescript
class MigrationValidator {
  async validateDataIntegrity(): Promise<ValidationResult> {
    const results: ValidationResult = {
      passed: true,
      errors: [],
      warnings: [],
      stats: {}
    };
    
    // Check data completeness
    const legacyCount = await this.getLegacyAssessmentCount();
    const exportCount = await this.getExportedAssessmentCount();
    
    if (legacyCount !== exportCount) {
      results.passed = false;
      results.errors.push(`Data count mismatch: legacy=${legacyCount}, exported=${exportCount}`);
    }
    
    // Check data consistency
    const consistencyResults = await this.checkDataConsistency();
    results.errors.push(...consistencyResults.errors);
    results.warnings.push(...consistencyResults.warnings);
    
    // Check referential integrity
    const referentialResults = await this.checkReferentialIntegrity();
    results.errors.push(...referentialResults.errors);
    
    return results;
  }
  
  private async checkDataConsistency(): Promise<ValidationResult> {
    const results: ValidationResult = { passed: true, errors: [], warnings: [], stats: {} };
    
    // Check for duplicate assessment IDs
    const duplicates = await this.findDuplicateAssessmentIds();
    if (duplicates.length > 0) {
      results.errors.push(`Duplicate assessment IDs found: ${duplicates.join(', ')}`);
    }
    
    // Check for invalid state transitions
    const invalidTransitions = await this.findInvalidStateTransitions();
    if (invalidTransitions.length > 0) {
      results.warnings.push(`Invalid state transitions found: ${invalidTransitions.length}`);
    }
    
    return results;
  }
}
```

### Phase 2: Dual-Mode Operation (Weeks 3-6)

#### 2.1 Gradual Enablement
```typescript
class GradualMigrationManager {
  private config: MigrationConfig;
  private metrics: MigrationMetrics;
  
  async startGradualMigration(): Promise<void> {
    // Start with 1% traffic to AssessmentStore
    this.config.migrationPercentage = 1;
    this.config.enableAssessmentStore = true;
    this.config.enableDualMode = true;
    
    // Monitor for issues
    await this.monitorMigration(24 * 60 * 60 * 1000); // 24 hours
    
    // Gradually increase percentage
    const percentages = [1, 5, 10, 25, 50, 75, 90, 95, 99, 100];
    
    for (const percentage of percentages) {
      if (percentage > this.config.migrationPercentage) {
        this.config.migrationPercentage = percentage;
        
        // Monitor for issues
        await this.monitorMigration(12 * 60 * 60 * 1000); // 12 hours
        
        // Check for rollback conditions
        if (this.shouldRollback()) {
          await this.rollback();
          throw new Error('Migration rollback triggered');
        }
      }
    }
  }
  
  private async monitorMigration(duration: number): Promise<void> {
    const startTime = Date.now();
    const checkInterval = 60 * 1000; // 1 minute
    
    while (Date.now() - startTime < duration) {
      const metrics = await this.getMigrationMetrics();
      
      // Check for rollback conditions
      if (metrics.errorRate > 0.05 || metrics.responseTime > 5000) {
        console.warn('Migration metrics exceeded thresholds:', metrics);
        break;
      }
      
      await new Promise(resolve => setTimeout(resolve, checkInterval));
    }
  }
  
  private shouldRollback(): boolean {
    const metrics = this.metrics.getCurrentMetrics();
    
    // Rollback conditions
    return (
      metrics.errorRate > 0.1 ||
      metrics.responseTime > 10000 ||
      metrics.failureRate > 0.05 ||
      metrics.systemHealth !== 'healthy'
    );
  }
}
```

#### 2.2 Data Synchronization
```typescript
class DataSynchronizer {
  private legacyStore: LegacyEventService;
  private assessmentStore: AssessmentStore;
  
  async syncData(): Promise<void> {
    // Sync active assessments
    await this.syncActiveAssessments();
    
    // Sync completed assessments
    await this.syncCompletedAssessments();
    
    // Sync audit logs
    await this.syncAuditLogs();
  }
  
  private async syncActiveAssessments(): Promise<void> {
    const activeAssessments = await this.legacyStore.getActiveAssessments();
    
    for (const assessment of activeAssessments) {
      try {
        // Check if assessment exists in AssessmentStore
        const existing = await this.assessmentStore.getState(assessment.id);
        
        if (!existing) {
          // Create assessment in AssessmentStore
          await this.assessmentStore.createAssessment(assessment.request);
        } else {
          // Update progress if needed
          if (existing.progress !== assessment.progress) {
            await this.assessmentStore.updateProgress(
              assessment.id,
              assessment.progress,
              assessment.message
            );
          }
        }
      } catch (error) {
        console.error('Failed to sync assessment:', assessment.id, error);
      }
    }
  }
  
  private async syncCompletedAssessments(): Promise<void> {
    const completedAssessments = await this.legacyStore.getCompletedAssessments();
    
    for (const assessment of completedAssessments) {
      try {
        const existing = await this.assessmentStore.getState(assessment.id);
        
        if (existing && existing.state !== AssessmentState.COMPLETED) {
          // Mark as completed in AssessmentStore
          await this.assessmentStore.completeAssessment(assessment.id, assessment.result);
        }
      } catch (error) {
        console.error('Failed to sync completed assessment:', assessment.id, error);
      }
    }
  }
}
```

#### 2.3 Monitoring and Alerting
```typescript
class MigrationMonitor {
  private metrics: MigrationMetrics;
  private alerts: AlertManager;
  
  async startMonitoring(): Promise<void> {
    // Set up real-time monitoring
    setInterval(() => this.collectMetrics(), 30 * 1000); // 30 seconds
    setInterval(() => this.checkAlerts(), 60 * 1000); // 1 minute
  }
  
  private async collectMetrics(): Promise<void> {
    const metrics = await this.getMigrationMetrics();
    this.metrics.recordMetrics(metrics);
    
    // Check for anomalies
    this.detectAnomalies(metrics);
  }
  
  private async checkAlerts(): Promise<void> {
    const metrics = this.metrics.getCurrentMetrics();
    
    // Alert on high error rate
    if (metrics.errorRate > 0.05) {
      this.alerts.send('High error rate during migration', {
        errorRate: metrics.errorRate,
        timestamp: new Date().toISOString()
      });
    }
    
    // Alert on performance degradation
    if (metrics.responseTime > 5000) {
      this.alerts.send('Performance degradation during migration', {
        responseTime: metrics.responseTime,
        timestamp: new Date().toISOString()
      });
    }
    
    // Alert on data inconsistency
    if (metrics.dataInconsistency > 0.01) {
      this.alerts.send('Data inconsistency detected', {
        inconsistencyRate: metrics.dataInconsistency,
        timestamp: new Date().toISOString()
      });
    }
  }
  
  private detectAnomalies(metrics: MigrationMetrics): void {
    // Check for sudden changes in metrics
    const baseline = this.metrics.getBaseline();
    
    if (baseline) {
      const errorRateChange = Math.abs(metrics.errorRate - baseline.errorRate);
      const responseTimeChange = Math.abs(metrics.responseTime - baseline.responseTime);
      
      if (errorRateChange > 0.02 || responseTimeChange > 2000) {
        console.warn('Anomaly detected in migration metrics:', {
          errorRateChange,
          responseTimeChange,
          current: metrics,
          baseline
        });
      }
    }
  }
}
```

### Phase 3: Full Migration (Weeks 7-8)

#### 3.1 Complete Data Migration
```typescript
class CompleteDataMigration {
  private assessmentStore: AssessmentStore;
  private legacyStore: LegacyEventService;
  
  async migrateAllData(): Promise<MigrationResult> {
    const result: MigrationResult = {
      totalAssessments: 0,
      migratedAssessments: 0,
      failedAssessments: 0,
      errors: [],
      warnings: [],
      startTime: new Date().toISOString(),
      endTime: null
    };
    
    try {
      // Export all legacy data
      const legacyAssessments = await this.legacyStore.getAllAssessments();
      result.totalAssessments = legacyAssessments.length;
      
      // Migrate assessments in batches
      const batchSize = 1000;
      for (let i = 0; i < legacyAssessments.length; i += batchSize) {
        const batch = legacyAssessments.slice(i, i + batchSize);
        const batchResult = await this.migrateBatch(batch);
        
        result.migratedAssessments += batchResult.migrated;
        result.failedAssessments += batchResult.failed;
        result.errors.push(...batchResult.errors);
        result.warnings.push(...batchResult.warnings);
        
        // Progress reporting
        console.log(`Migration progress: ${i + batch.length}/${legacyAssessments.length}`);
      }
      
      // Validate migration
      const validation = await this.validateMigration();
      result.errors.push(...validation.errors);
      result.warnings.push(...validation.warnings);
      
    } catch (error) {
      result.errors.push(`Migration failed: ${error.message}`);
    } finally {
      result.endTime = new Date().toISOString();
    }
    
    return result;
  }
  
  private async migrateBatch(batch: LegacyAssessment[]): Promise<BatchMigrationResult> {
    const result: BatchMigrationResult = {
      migrated: 0,
      failed: 0,
      errors: [],
      warnings: []
    };
    
    for (const assessment of batch) {
      try {
        // Check if assessment already exists
        const existing = await this.assessmentStore.getState(assessment.id);
        
        if (!existing) {
          // Create assessment
          await this.assessmentStore.createAssessment(assessment.request);
          
          // Set appropriate state
          if (assessment.state === AssessmentState.COMPLETED) {
            await this.assessmentStore.completeAssessment(assessment.id, assessment.result);
          } else if (assessment.state === AssessmentState.FAILED) {
            await this.assessmentStore.failAssessment(assessment.id, assessment.errorMessage);
          }
          
          result.migrated++;
        } else {
          result.warnings.push(`Assessment already exists: ${assessment.id}`);
        }
      } catch (error) {
        result.failed++;
        result.errors.push(`Failed to migrate assessment ${assessment.id}: ${error.message}`);
      }
    }
    
    return result;
  }
}
```

#### 3.2 Final Validation
```typescript
class FinalMigrationValidator {
  private assessmentStore: AssessmentStore;
  private legacyStore: LegacyEventService;
  
  async validateCompleteMigration(): Promise<FinalValidationResult> {
    const result: FinalValidationResult = {
      passed: true,
      errors: [],
      warnings: [],
      stats: {},
      recommendations: []
    };
    
    // Count comparison
    const legacyCount = await this.legacyStore.getAssessmentCount();
    const newCount = await this.assessmentStore.getAssessmentCount();
    
    if (legacyCount !== newCount) {
      result.passed = false;
      result.errors.push(`Assessment count mismatch: legacy=${legacyCount}, new=${newCount}`);
    }
    
    // Data consistency check
    const consistency = await this.checkDataConsistency();
    result.errors.push(...consistency.errors);
    result.warnings.push(...consistency.warnings);
    
    // State validation
    const stateValidation = await this.validateStateTransitions();
    result.errors.push(...stateValidation.errors);
    
    // Performance validation
    const performance = await this.validatePerformance();
    result.warnings.push(...performance.warnings);
    
    // Generate recommendations
    result.recommendations = this.generateRecommendations(result);
    
    return result;
  }
  
  private async checkDataConsistency(): Promise<ValidationResult> {
    const result: ValidationResult = { passed: true, errors: [], warnings: [], stats: {} };
    
    // Check for data loss
    const lostData = await this.findLostData();
    if (lostData.length > 0) {
      result.errors.push(`Data loss detected: ${lostData.length} records`);
    }
    
    // Check for data corruption
    const corruptedData = await this.findCorruptedData();
    if (corruptedData.length > 0) {
      result.errors.push(`Data corruption detected: ${corruptedData.length} records`);
    }
    
    // Check for duplicates
    const duplicates = await this.findDuplicates();
    if (duplicates.length > 0) {
      result.warnings.push(`Duplicates detected: ${duplicates.length} records`);
    }
    
    return result;
  }
  
  private generateRecommendations(validation: FinalValidationResult): string[] {
    const recommendations: string[] = [];
    
    if (validation.errors.length > 0) {
      recommendations.push('Address all validation errors before proceeding');
    }
    
    if (validation.warnings.length > 0) {
      recommendations.push('Review and address validation warnings');
    }
    
    if (validation.stats.errorRate > 0.01) {
      recommendations.push('Monitor error rates closely post-migration');
    }
    
    if (validation.stats.responseTime > 1000) {
      recommendations.push('Optimize performance post-migration');
    }
    
    return recommendations;
  }
}
```

### Phase 4: Cleanup and Optimization (Weeks 9-10)

#### 4.1 Legacy System Cleanup
```typescript
class LegacyCleanupManager {
  private legacyStore: LegacyEventService;
  private assessmentStore: AssessmentStore;
  
  async cleanupLegacySystem(): Promise<CleanupResult> {
    const result: CleanupResult = {
      cleanedAssessments: 0,
      cleanedAuditLogs: 0,
      errors: [],
      startTime: new Date().toISOString(),
      endTime: null
    };
    
    try {
      // Archive legacy data
      await this.archiveLegacyData();
      
      // Clean up legacy assessments
      const cleanedAssessments = await this.cleanupLegacyAssessments();
      result.cleanedAssessments = cleanedAssessments;
      
      // Clean up legacy audit logs
      const cleanedAuditLogs = await this.cleanupLegacyAuditLogs();
      result.cleanedAuditLogs = cleanedAuditLogs;
      
      // Remove legacy services
      await this.removeLegacyServices();
      
    } catch (error) {
      result.errors.push(`Cleanup failed: ${error.message}`);
    } finally {
      result.endTime = new Date().toISOString();
    }
    
    return result;
  }
  
  private async archiveLegacyData(): Promise<void> {
    // Create backup of legacy data
    const backup = await this.legacyStore.exportAllData();
    
    // Store in archive
    await this.assessmentStore.archiveData(backup);
    
    console.log('Legacy data archived successfully');
  }
  
  private async cleanupLegacyAssessments(): Promise<number> {
    // Remove legacy assessments that have been migrated
    const migratedAssessments = await this.assessmentStore.getAllAssessmentIds();
    
    let cleanedCount = 0;
    for (const assessmentId of migratedAssessments) {
      try {
        await this.legacyStore.removeAssessment(assessmentId);
        cleanedCount++;
      } catch (error) {
        console.error(`Failed to cleanup legacy assessment ${assessmentId}:`, error);
      }
    }
    
    return cleanedCount;
  }
  
  private async removeLegacyServices(): Promise<void> {
    // Stop legacy services
    await this.legacyStore.stop();
    
    // Remove legacy service deployment
    await this.removeLegacyDeployment();
    
    console.log('Legacy services removed successfully');
  }
}
```

#### 4.2 Performance Optimization
```typescript
class PostMigrationOptimizer {
  private assessmentStore: AssessmentStore;
  
  async optimizePostMigration(): Promise<OptimizationResult> {
    const result: OptimizationResult = {
      optimizations: [],
      performanceImprovements: {},
      startTime: new Date().toISOString(),
      endTime: null
    };
    
    try {
      // Database optimization
      const dbOptimizations = await this.optimizeDatabase();
      result.optimizations.push(...dbOptimizations);
      
      // Cache optimization
      const cacheOptimizations = await this.optimizeCache();
      result.optimizations.push(...cacheOptimizations);
      
      // Index optimization
      const indexOptimizations = await this.optimizeIndexes();
      result.optimizations.push(...indexOptimizations);
      
      // Performance baseline establishment
      const baseline = await this.establishPerformanceBaseline();
      result.performanceImprovements = baseline;
      
    } finally {
      result.endTime = new Date().toISOString();
    }
    
    return result;
  }
  
  private async optimizeDatabase(): Promise<string[]> {
    const optimizations: string[] = [];
    
    // Update database statistics
    await this.updateDatabaseStatistics();
    optimizations.push('Database statistics updated');
    
    // Optimize query plans
    await this.optimizeQueryPlans();
    optimizations.push('Query plans optimized');
    
    // Reorganize tables
    await this.reorganizeTables();
    optimizations.push('Tables reorganized');
    
    return optimizations;
  }
  
  private async establishPerformanceBaseline(): Promise<PerformanceBaseline> {
    const baseline: PerformanceBaseline = {
      responseTime: {},
      throughput: {},
      errorRate: {},
      timestamp: new Date().toISOString()
    };
    
    // Measure response time
    baseline.responseTime.average = await this.measureAverageResponseTime();
    baseline.responseTime.p95 = await this.measureP95ResponseTime();
    baseline.responseTime.p99 = await this.measureP99ResponseTime();
    
    // Measure throughput
    baseline.throughput.perSecond = await this.measureThroughput();
    baseline.throughput.perMinute = await this.measureThroughputPerMinute();
    
    // Measure error rate
    baseline.errorRate.current = await this.measureErrorRate();
    
    return baseline;
  }
}
```

## Rollback Strategy

### 1. Immediate Rollback
```typescript
class RollbackManager {
  private config: MigrationConfig;
  private legacyStore: LegacyEventService;
  private assessmentStore: AssessmentStore;
  
  async immediateRollback(): Promise<RollbackResult> {
    const result: RollbackResult = {
      success: false,
      errors: [],
      warnings: [],
      rollbackTime: new Date().toISOString(),
      details: {}
    };
    
    try {
      // Step 1: Disable AssessmentStore
      this.config.enableAssessmentStore = false;
      this.config.enableDualMode = false;
      
      // Step 2: Restore legacy services
      await this.restoreLegacyServices();
      
      // Step 3: Restore legacy data
      await this.restoreLegacyData();
      
      // Step 4: Restart services
      await this.restartServices();
      
      result.success = true;
      console.log('Immediate rollback completed successfully');
      
    } catch (error) {
      result.errors.push(`Rollback failed: ${error.message}`);
      console.error('Rollback failed:', error);
    }
    
    return result;
  }
  
  private async restoreLegacyServices(): Promise<void> {
    // Start legacy services
    await this.legacyStore.start();
    
    // Verify legacy services are running
    const health = await this.legacyStore.getHealth();
    if (health.status !== 'healthy') {
      throw new Error(`Legacy services not healthy after restore: ${health.status}`);
    }
  }
  
  private async restoreLegacyData(): Promise<void> {
    // Restore from backup
    const backup = await this.assessmentStore.getLatestBackup();
    
    if (backup) {
      await this.legacyStore.restoreData(backup);
    } else {
      throw new Error('No backup available for data restoration');
    }
  }
  
  private async restartServices(): Promise<void> {
    // Restart all services
    await this.restartIntegrationCoordinator();
    await this.restartComplianceServer();
    
    // Verify services are running
    await this.verifyServiceHealth();
  }
}
```

### 2. Rollback Triggers
```typescript
class RollbackTriggerManager {
  private rollbackManager: RollbackManager;
  private metrics: MigrationMetrics;
  
  shouldRollback(): boolean {
    const metrics = this.metrics.getCurrentMetrics();
    
    // Rollback triggers
    const triggers = [
      this.checkErrorRate(metrics),
      this.checkResponseTime(metrics),
      this.checkFailureRate(metrics),
      this.checkDataConsistency(metrics),
      this.checkSystemHealth(metrics)
    ];
    
    return triggers.some(trigger => trigger.shouldRollback);
  }
  
  private checkErrorRate(metrics: MigrationMetrics): RollbackTrigger {
    const shouldRollback = metrics.errorRate > 0.1;
    
    return {
      shouldRollback,
      reason: `Error rate too high: ${metrics.errorRate}`,
      severity: 'critical',
      timestamp: new Date().toISOString()
    };
  }
  
  private checkResponseTime(metrics: MigrationMetrics): RollbackTrigger {
    const shouldRollback = metrics.responseTime > 10000;
    
    return {
      shouldRollback,
      reason: `Response time too high: ${metrics.responseTime}ms`,
      severity: 'high',
      timestamp: new Date().toISOString()
    };
  }
  
  private checkFailureRate(metrics: MigrationMetrics): RollbackTrigger {
    const shouldRollback = metrics.failureRate > 0.05;
    
    return {
      shouldRollback,
      reason: `Failure rate too high: ${metrics.failureRate}`,
      severity: 'critical',
      timestamp: new Date().toISOString()
    };
  }
  
  private checkDataConsistency(metrics: MigrationMetrics): RollbackTrigger {
    const shouldRollback = metrics.dataInconsistency > 0.01;
    
    return {
      shouldRollback,
      reason: `Data inconsistency detected: ${metrics.dataInconsistency}`,
      severity: 'high',
      timestamp: new Date().toISOString()
    };
  }
  
  private checkSystemHealth(metrics: MigrationMetrics): RollbackTrigger {
    const shouldRollback = metrics.systemHealth !== 'healthy';
    
    return {
      shouldRollback,
      reason: `System health degraded: ${metrics.systemHealth}`,
      severity: 'critical',
      timestamp: new Date().toISOString()
    };
  }
}
```

## Implementation Roadmap

### Phase 1: Preparation (Weeks 1-2)
- [ ] Set up migration environment
- [ ] Export legacy data
- [ ] Create validation scripts
- [ ] Set up monitoring and alerting

### Phase 2: Dual-Mode Operation (Weeks 3-6)
- [ ] Enable dual-mode operation
- [ ] Gradual traffic migration
- [ ] Data synchronization
- [ ] Enhanced monitoring

### Phase 3: Full Migration (Weeks 7-8)
- [ ] Complete data migration
- [ ] Final validation
- [ ] Performance testing
- [ ] User acceptance testing

### Phase 4: Cleanup and Optimization (Weeks 9-10)
- [ ] Legacy system cleanup
- [ ] Performance optimization
- [ ] Documentation update
- [ ] Training and knowledge transfer

## Success Criteria

### Migration Success Metrics
- **Zero Downtime**: No service interruption during migration
- **Data Integrity**: 100% data consistency between systems
- **Performance**: No performance degradation post-migration
- **Rollback Capability**: < 5 minutes rollback time if needed

### Quality Metrics
- **Error Rate**: < 0.1% during migration
- **Response Time**: < 100ms for 95% of requests
- **Data Loss**: 0 records lost during migration
- **Validation**: 100% validation pass rate

### Business Metrics
- **User Experience**: No negative user feedback
- **System Stability**: 99.99% uptime during migration
- **Business Continuity**: No impact on business operations
- **Cost**: Migration completed within budget

This comprehensive migration strategy ensures a smooth, risk-free transition from the current EventEmitter-based system to the new AssessmentStore service while maintaining full compatibility and system reliability.