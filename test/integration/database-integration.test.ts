/**
 * Database Integration Tests
 * 
 * This file contains comprehensive integration tests for database operations,
 * testing database persistence, transactions, and data integrity for the
 * AssessmentStore service.
 */

import { describe, it, expect, beforeEach, afterEach, vi, test } from 'vitest';
import { mockDatabaseService } from '../mocks/database-mock';
import { TestAssessmentStore } from '../unit/assessment-store.test';
import {
    setupTestEnvironment,
    cleanupTestEnvironment,
    generateTestAssessmentData,
    generateTestResultData,
    createTestAssessment,
    createBatchTestAssessments,
    assertAssessmentState,
    assertAssessmentResult,
    assertAssessmentError,
    measurePerformance
} from '../setup/test-setup';

// Test suite
describe('Database Integration Tests', () => {
    let assessmentStore: TestAssessmentStore;

    beforeAll(async () => {
        await setupTestEnvironment();
        assessmentStore = new TestAssessmentStore();
    });

    afterAll(async () => {
        await cleanupTestEnvironment();
    });

    beforeEach(() => {
        // Reset mock database before each test
        mockDatabaseService.reset();
        vi.clearAllMocks();
    });

    describe('Database Connection and Health', () => {
        it('should establish database connection successfully', async () => {
            // Step 1: Test database connection
            const connection = await mockDatabaseService.getConnection();
            expect(connection).toBeDefined();
            expect(connection.status).toBe('connected');

            // Step 2: Test health check
            const health = await mockDatabaseService.healthCheck();
            expect(health.status).toBe('healthy');
            expect(health.connection_pool.active_connections).toBeGreaterThanOrEqual(0);
            expect(health.connection_pool.total_connections).toBeGreaterThan(0);
        });

        it('should handle database connection failures gracefully', async () => {
            // Step 1: Simulate database failure
            mockDatabaseService.simulateConnectionFailure();

            // Step 2: Test connection failure handling
            await expect(mockDatabaseService.getConnection())
                .rejects.toThrow('Database connection failed');

            // Step 3: Test health check during failure
            const health = await mockDatabaseService.healthCheck();
            expect(health.status).toBe('unhealthy');
            expect(health.error).toBeDefined();

            // Step 4: Restore connection
            mockDatabaseService.restoreConnection();

            // Step 5: Verify connection is restored
            const restoredConnection = await mockDatabaseService.getConnection();
            expect(restoredConnection.status).toBe('connected');
        });

        it('should handle connection pool exhaustion', async () => {
            // Step 1: Create many concurrent connections
            const connectionPromises = Array(50).fill(null).map(() =>
                mockDatabaseService.getConnection()
            );

            const connections = await Promise.all(connectionPromises);
            expect(connections.length).toBe(50);

            // Step 2: Test connection pool health
            const health = await mockDatabaseService.healthCheck();
            expect(health.connection_pool.active_connections).toBeGreaterThan(0);
            expect(health.connection_pool.active_connections).toBeLessThanOrEqual(health.connection_pool.total_connections);
        });

        it('should handle connection timeouts', async () => {
            // Step 1: Simulate slow connection
            mockDatabaseService.setConnectionTimeout(5000);

            // Step 2: Test timeout handling
            const startTime = Date.now();
            await expect(mockDatabaseService.getConnection())
                .rejects.toThrow('Connection timeout');
            const endTime = Date.now();

            // Step 3: Verify timeout was respected
            expect(endTime - startTime).toBeGreaterThanOrEqual(5000);

            // Step 4: Restore normal timeout
            mockDatabaseService.setConnectionTimeout(1000);
        });
    });

    describe('Assessment CRUD Operations', () => {
        it('should create assessment in database', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);

            // Step 2: Verify database persistence
            const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
            expect(dbAssessment).toBeDefined();
            expect(dbAssessment.assessment_id).toBe(assessmentId);
            expect(dbAssessment.state).toBe('pending');
            expect(dbAssessment.request_data).toEqual(request);

            // Step 3: Verify timestamps
            expect(dbAssessment.created_at).toBeDefined();
            expect(dbAssessment.updated_at).toBeDefined();
            expect(new Date(dbAssessment.created_at)).toEqual(new Date(dbAssessment.updated_at));
        });

        it('should read assessment from database', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);

            // Step 2: Read assessment from database
            const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
            expect(dbAssessment).toBeDefined();
            expect(dbAssessment.assessment_id).toBe(assessmentId);

            // Step 3: Verify all fields
            expect(dbAssessment.state).toBe('pending');
            expect(dbAssessment.version).toBe(1);
            expect(dbAssessment.progress).toBe(0);
            expect(dbAssessment.retry_count).toBe(0);
            expect(dbAssessment.request_data).toEqual(request);
        });

        it('should update assessment in database', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);

            // Step 2: Update assessment state
            await assessmentStore.updateProgress(assessmentId, 50, '50% complete');

            // Step 3: Verify database update
            const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
            expect(dbAssessment.progress).toBe(50);
            expect(dbAssessment.message).toBe('50% complete');
            expect(dbAssessment.version).toBe(2);
            expect(dbAssessment.updated_at).not.toEqual(dbAssessment.created_at);
        });

        it('should delete assessment from database', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);

            // Step 2: Delete assessment
            await assessmentStore.cancelAssessment(assessmentId, 'Test deletion');

            // Step 3: Verify database deletion
            const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
            expect(dbAssessment).toBeDefined();
            expect(dbAssessment.state).toBe('cancelled');
            expect(dbAssessment.completed_at).toBeDefined();

            // Step 4: Verify soft delete
            const deletedAssessment = await mockDatabaseService.getDeletedAssessment(assessmentId);
            expect(deletedAssessment).toBeDefined();
        });

        it('should handle batch database operations', async () => {
            // Step 1: Create multiple assessments
            const requests = createBatchTestAssessments(10);
            const assessmentIds = await assessmentStore.batchCreateAssessments(requests);

            // Step 2: Verify batch creation
            expect(assessmentIds).toHaveLength(10);

            // Step 3: Verify all assessments exist in database
            for (const assessmentId of assessmentIds) {
                const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(dbAssessment).toBeDefined();
                expect(dbAssessment.state).toBe('pending');
            }

            // Step 4: Batch update progress
            const updatePromises = assessmentIds.map(id =>
                assessmentStore.updateProgress(id, 25, '25% complete')
            );

            await Promise.all(updatePromises);

            // Step 5: Verify batch updates
            for (const assessmentId of assessmentIds) {
                const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(dbAssessment.progress).toBe(25);
            }
        });
    });

    describe('Database Transactions', () => {
        it('should handle atomic transactions', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);

            // Step 2: Start transaction
            const transaction = await mockDatabaseService.beginTransaction();

            // Step 3: Perform multiple operations in transaction
            await mockDatabaseService.updateAssessmentState(transaction, assessmentId, 'processing');
            await mockDatabaseService.updateAssessmentProgress(transaction, assessmentId, 50);
            await mockDatabaseService.updateAssessmentVersion(transaction, assessmentId, 2);

            // Step 4: Commit transaction
            await mockDatabaseService.commitTransaction(transaction);

            // Step 5: Verify transaction committed
            const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
            expect(dbAssessment.state).toBe('processing');
            expect(dbAssessment.progress).toBe(50);
            expect(dbAssessment.version).toBe(2);
        });

        it('should handle transaction rollback', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);
            // Step 2: Start transaction
            const transaction = await mockDatabaseService.beginTransaction();

            // Step 3: Perform operations that will fail
            await mockDatabaseService.updateAssessmentState(transaction, assessmentId, 'processing');
            await mockDatabaseService.updateAssessmentProgress(transaction, assessmentId, 50);

            // Step 4: Simulate failure and rollback
            await mockDatabaseService.simulateTransactionFailure(transaction);
            await mockDatabaseService.rollbackTransaction(transaction);

            // Step 5: Verify rollback
            const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
            expect(dbAssessment.state).toBe('pending');
            expect(dbAssessment.progress).toBe(0);
            expect(dbAssessment.version).toBe(1);
        });

        it('should handle concurrent transactions', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);

            // Step 2: Start concurrent transactions
            const transaction1 = await mockDatabaseService.beginTransaction();
            const transaction2 = await mockDatabaseService.beginTransaction();

            // Step 3: Perform operations in both transactions
            await mockDatabaseService.updateAssessmentState(transaction1, assessmentId, 'processing');
            await mockDatabaseService.updateAssessmentProgress(transaction2, assessmentId, 25);

            // Step 4: Commit both transactions
            await mockDatabaseService.commitTransaction(transaction1);
            await mockDatabaseService.commitTransaction(transaction2);

            // Step 5: Verify final state
            const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
            expect(dbAssessment.state).toBe('processing');
            expect(dbAssessment.progress).toBe(25);
            expect(dbAssessment.version).toBe(3); // 1 initial + 2 updates
        });

        it('should handle transaction isolation', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);

            // Step 2: Start transaction with isolation level
            const transaction = await mockDatabaseService.beginTransaction('SERIALIZABLE');

            // Step 3: Read assessment in transaction
            const assessmentInTransaction = await mockDatabaseService.getAssessmentInTransaction(transaction, assessmentId);
            expect(assessmentInTransaction.state).toBe('pending');

            // Step 4: Update assessment in transaction
            await mockDatabaseService.updateAssessmentState(transaction, assessmentId, 'processing');

            // Step 5: Verify isolation - external read should see old state
            const externalAssessment = await mockDatabaseService.getAssessment(assessmentId);
            expect(externalAssessment.state).toBe('pending');

            // Step 6: Commit transaction
            await mockDatabaseService.commitTransaction(transaction);

            // Step 7: Verify external read now sees new state
            const finalAssessment = await mockDatabaseService.getAssessment(assessmentId);
            expect(finalAssessment.state).toBe('processing');
        });
    });

    describe('Database Indexing and Performance', () => {
        it('should use indexes for efficient queries', async () => {
            // Step 1: Create many assessments
            const requests = createBatchTestAssessments(100);
            const assessmentIds = await assessmentStore.batchCreateAssessments(requests);

            // Step 2: Test query performance with indexes
            const performance = await measurePerformance(
                'indexed-query',
                async () => {
                    const queryPromises = [
                        mockDatabaseService.getAssessmentsByState('pending'),
                        mockDatabaseService.getAssessmentsByDateRange(new Date(Date.now() - 24 * 60 * 60 * 1000), new Date()),
                        mockDatabaseService.getAssessmentsByServerName('test-server')
                    ];
                    return await Promise.all(queryPromises);
                },
                10
            );

            // Step 3: Verify performance
            expect(performance.averageTime).toBeLessThan(1000); // Less than 1 second average

            // Step 4: Verify query results
            const pendingAssessments = performance.results[0];
            expect(pendingAssessments.length).toBeGreaterThan(0);

            const recentAssessments = performance.results[1];
            expect(recentAssessments.length).toBeGreaterThan(0);
        });

        it('should handle complex queries with joins', async () => {
            // Step 1: Create assessments with related data
            const requests = createBatchTestAssessments(10);
            const assessmentIds = await assessmentStore.batchCreateAssessments(requests);

            // Step 2: Process assessments to create results
            for (const assessmentId of assessmentIds) {
                await assessmentStore.updateProgress(assessmentId, 100, 'Complete');
                const result = generateTestResultData();
                await assessmentStore.completeAssessment(assessmentId, result);
            }

            // Step 2: Test complex query with joins
            const complexQuery = await mockDatabaseService.getComplexAssessmentData();
            expect(complexQuery).toBeDefined();
            expect(complexQuery.length).toBeGreaterThan(0);

            // Step 3: Verify query structure
            const firstResult = complexQuery[0];
            expect(firstResult.assessment_id).toBeDefined();
            expect(firstResult.state).toBeDefined();
            expect(firstResult.result_data).toBeDefined();
            expect(firstResult.created_at).toBeDefined();
        });

        it('should handle pagination efficiently', async () => {
            // Step 1: Create many assessments
            const requests = createBatchTestAssessments(1000);
            const assessmentIds = await assessmentStore.batchCreateAssessments(requests);

            // Step 2: Test pagination performance
            const performance = await measurePerformance(
                'pagination-query',
                async () => {
                    const pages = [];
                    for (let offset = 0; offset < 1000; offset += 100) {
                        const page = await mockDatabaseService.getAssessmentsPaginated(100, offset);
                        pages.push(page);
                    }
                    return pages;
                },
                5
            );

            // Step 3: Verify performance
            expect(performance.averageTime).toBeLessThan(5000); // Less than 5 seconds average

            // Step 4: Verify pagination results
            const totalPages = performance.results.length;
            expect(totalPages).toBe(10); // 1000 assessments / 100 per page

            // Step 5: Verify no duplicates across pages
            const allAssessments = performance.results.flat();
            const uniqueAssessments = new Set(allAssessments.map(a => a.assessment_id));
            expect(uniqueAssessments.size).toBe(1000);
        });

        it('should handle full-text search efficiently', async () => {
            // Step 1: Create assessments with searchable content
            const requests = createBatchTestAssessments(50);
            const assessmentIds = await assessmentStore.batchCreateAssessments(requests);

            // Step 2: Test full-text search performance
            const performance = await measurePerformance(
                'fulltext-search',
                async () => {
                    const searchPromises = [
                        mockDatabaseService.searchAssessments('test-server'),
                        mockDatabaseService.searchAssessments('compliance'),
                        mockDatabaseService.searchAssessments('assessment')
                    ];
                    return await Promise.all(searchPromises);
                },
                10
            );

            // Step 3: Verify performance
            expect(performance.averageTime).toBeLessThan(2000); // Less than 2 seconds average

            // Step 4: Verify search results
            const serverSearch = performance.results[0];
            expect(serverSearch.length).toBeGreaterThan(0);

            const complianceSearch = performance.results[1];
            expect(complianceSearch.length).toBeGreaterThan(0);
        });
    });

    describe('Database Constraints and Validation', () => {
        it('should enforce unique constraint on assessment_id', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);

            // Step 2: Attempt to create duplicate assessment
            const duplicateRequest = { ...request, assessment_id: assessmentId };
            await expect(assessmentStore.createAssessment(duplicateRequest))
                .rejects.toThrow('Duplicate assessment ID');
        });

        it('should enforce state transition constraints', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);

            // Step 2: Attempt invalid state transition
            await expect(assessmentStore.completeAssessment(assessmentId, generateTestResultData()))
                .rejects.toThrow('Invalid state transition');

            // Step 3: Verify state is unchanged
            const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
            expect(dbAssessment.state).toBe('pending');
        });

        it('should enforce data validation constraints', async () => {
            // Step 1: Create assessment with invalid data
            const invalidRequest = {
                assessment_id: '',
                serverName: 'test-server',
                assessmentType: 'compliance',
                options: { includeDetails: true },
                timestamp: new Date().toISOString(),
                source: 'installer'
            };

            await expect(assessmentStore.createAssessment(invalidRequest))
                .rejects.toThrow('Invalid assessment data');
        });

        it('should enforce foreign key constraints', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);

            // Step 2: Attempt to create result with invalid assessment ID
            const invalidResult = {
                assessment_id: 'invalid-assessment-id',
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

            await expect(assessmentStore.completeAssessment('invalid-assessment-id', invalidResult))
                .rejects.toThrow('Foreign key constraint violation');
        });

        it('should enforce check constraints', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);

            // Step 2: Attempt to set invalid progress value
            await expect(assessmentStore.updateProgress(assessmentId, 150, 'Invalid progress'))
                .rejects.toThrow('Check constraint violation');

            // Step 3: Attempt to set invalid priority value
            await expect(assessmentStore.updateProgress(assessmentId, -1, 'Invalid progress'))
                .rejects.toThrow('Check constraint violation');
        });
    });

    describe('Database Backup and Recovery', () => {
        it('should create database backup', async () => {
            // Step 1: Create assessments
            const requests = createBatchTestAssessments(10);
            const assessmentIds = await assessmentStore.batchCreateAssessments(requests);

            // Step 2: Process assessments
            for (const assessmentId of assessmentIds) {
                await assessmentStore.updateProgress(assessmentId, 100, 'Complete');
                const result = generateTestResultData();
                await assessmentStore.completeAssessment(assessmentId, result);
            }

            // Step 3: Create backup
            const backup = await mockDatabaseService.createBackup();
            expect(backup).toBeDefined();
            expect(backup.timestamp).toBeDefined();
            expect(backup.assessment_count).toBe(10);
            expect(backup.size_bytes).toBeGreaterThan(0);
        });

        it('should restore database from backup', async () => {
            // Step 1: Create assessments
            const requests = createBatchTestAssessments(5);
            const assessmentIds = await assessmentStore.batchCreateAssessments(requests);

            // Step 2: Create backup
            const backup = await mockDatabaseService.createBackup();

            // Step 3: Delete assessments
            for (const assessmentId of assessmentIds) {
                await assessmentStore.cancelAssessment(assessmentId, 'Test deletion');
            }

            // Step 4: Restore from backup
            const restoreResult = await mockDatabaseService.restoreBackup(backup);
            expect(restoreResult).toBeDefined();
            expect(restoreResult.restored_count).toBe(5);

            // Step 5: Verify restoration
            for (const assessmentId of assessmentIds) {
                const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(dbAssessment).toBeDefined();
                expect(dbAssessment.state).toBe('pending');
            }
        });

        it('should handle backup compression', async () => {
            // Step 1: Create many assessments
            const requests = createBatchTestAssessments(100);
            const assessmentIds = await assessmentStore.batchCreateAssessments(requests);

            // Step 2: Create compressed backup
            const backup = await mockDatabaseService.createBackup(true); // compressed

            // Step 3: Verify compression worked
            expect(backup.compressed).toBe(true);
            expect(backup.size_bytes).toBeLessThan(10000); // Should be compressed

            // Step 4: Restore from compressed backup
            const restoreResult = await mockDatabaseService.restoreBackup(backup);
            expect(restoreResult.restored_count).toBe(100);
        });

        it('should handle incremental backups', async () => {
            // Step 1: Create initial assessments
            const initialRequests = createBatchTestAssessments(10);
            const initialAssessmentIds = await assessmentStore.batchCreateAssessments(initialRequests);

            // Step 2: Create full backup
            const fullBackup = await mockDatabaseService.createBackup();

            // Step 3: Create additional assessments
            const additionalRequests = createBatchTestAssessments(5);
            const additionalAssessmentIds = await assessmentStore.batchCreateAssessments(additionalRequests);

            // Step 4: Create incremental backup
            const incrementalBackup = await mockDatabaseService.createIncrementalBackup(fullBackup.timestamp);
            expect(incrementalBackup).toBeDefined();
            expect(incrementalBackup.incremental).toBe(true);
            expect(incrementalBackup.assessment_count).toBe(5);

            // Step 5: Restore from full backup
            await mockDatabaseService.restoreBackup(fullBackup);

            // Step 6: Apply incremental backup
            const restoreResult = await mockDatabaseService.applyIncrementalBackup(incrementalBackup);
            expect(restoreResult.applied_count).toBe(5);

            // Step 7: Verify total assessments
            const totalAssessments = await mockDatabaseService.getAssessmentCount();
            expect(totalAssessments).toBe(15);
        });
    });

    describe('Database Schema Evolution', () => {
        it('should handle schema migrations', async () => {
            // Step 1: Create assessments with current schema
            const requests = createBatchTestAssessments(5);
            const assessmentIds = await assessmentStore.batchCreateAssessments(requests);

            // Step 2: Simulate schema change
            await mockDatabaseService.simulateSchemaChange();

            // Step 3: Verify schema migration
            const migratedAssessments = await mockDatabaseService.getAssessments();
            expect(migratedAssessments).toBeDefined();
            expect(migratedAssessments.length).toBe(5);

            // Step 4: Verify new schema fields
            const firstAssessment = migratedAssessments[0];
            expect(firstAssessment.new_field).toBeDefined();
        });

        it('should handle backward compatibility with old schema', async () => {
            // Step 1: Create assessments with old schema
            const oldAssessments = await mockDatabaseService.createOldSchemaAssessments(5);

            // Step 2: Verify old schema assessments work with new code
            for (const assessment of oldAssessments) {
                const result = await assessmentStore.getState(assessment.assessment_id);
                expect(result).toBeDefined();
                expect(result.assessmentId).toBe(assessment.assessment_id);
            }
        });

        it('should handle forward compatibility with new schema', async () => {
            // Step 1: Create assessments with new schema
            const requests = createBatchTestAssessments(5);
            const assessmentIds = await assessmentStore.batchCreateAssessments(requests);

            // Step 2: Simulate old code accessing new schema
            const oldAssessments = await mockDatabaseService.getAssessmentsWithOldSchema();
            expect(oldAssessments).toBeDefined();
            expect(oldAssessments.length).toBe(5);

            // Step 3: Verify old code can handle new fields
            for (const assessment of oldAssessments) {
                expect(assessment.assessment_id).toBeDefined();
                expect(assessment.state).toBeDefined();
                // New fields should be ignored or have default values
            }
        });

        it('should handle data type migrations', async () => {
            // Step 1: Create assessments with old data types
            const oldAssessments = await mockDatabaseService.createOldDataTypeAssessments(3);

            // Step 2: Migrate data types
            const migrationResult = await mockDatabaseService.migrateDataTypes();
            expect(migrationResult).toBeDefined();
            expect(migrationResult.migrated_count).toBe(3);

            // Step 3: Verify data type migration
            for (const assessment of oldAssessments) {
                const migratedAssessment = await mockDatabaseService.getAssessment(assessment.assessment_id);
                expect(migratedAssessment).toBeDefined();
                expect(typeof migratedAssessment.progress).toBe('number');
                expect(typeof migratedAssessment.version).toBe('number');
            }
        });
    });

    describe('Database Security and Auditing', () => {
        it('should track all database changes', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);

            // Step 2: Perform various operations
            await assessmentStore.updateProgress(assessmentId, 25, '25% complete');
            await assessmentStore.updateProgress(assessmentId, 50, '50% complete');
            await assessmentStore.updateProgress(assessmentId, 75, '75% complete');
            await assessmentStore.updateProgress(assessmentId, 100, '100% complete');

            // Step 3: Get audit trail
            const auditTrail = await mockDatabaseService.getAuditTrail(assessmentId);
            expect(auditTrail.length).toBeGreaterThan(0);

            // Step 4: Verify audit trail includes all changes
            const createEvent = auditTrail.find(event => event.event_type === 'assessment_created');
            expect(createEvent).toBeDefined();

            const updateEvents = auditTrail.filter(event => event.event_type === 'assessment_updated');
            expect(updateEvents.length).toBe(4);

            // Step 5: Verify audit trail includes user information
            for (const event of auditTrail) {
                expect(event.user_id).toBeDefined();
                expect(event.timestamp).toBeDefined();
                expect(event.event_type).toBeDefined();
            }
        });

        it('should handle database access logging', async () => {
            // Step 1: Perform various database operations
            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);

            await assessmentStore.getState(assessmentId);
            await assessmentStore.updateProgress(assessmentId, 50, '50% complete');
            await assessmentStore.listAssessments();

            // Step 2: Get access logs
            const accessLogs = await mockDatabaseService.getAccessLogs();
            expect(accessLogs.length).toBeGreaterThan(0);

            // Step 3: Verify access logs include all operations
            const createLog = accessLogs.find(log => log.operation === 'INSERT');
            expect(createLog).toBeDefined();

            const readLog = accessLogs.find(log => log.operation === 'SELECT');
            expect(readLog).toBeDefined();

            const updateLog = accessLogs.find(log => log.operation === 'UPDATE');
            expect(updateLog).toBeDefined();
        });

        it('should handle database security breaches', async () => {
            // Step 1: Simulate SQL injection attempt
            const maliciousInput = "'; DROP TABLE assessments; --";
            await expect(mockDatabaseService.getAssessment(maliciousInput))
                .rejects.toThrow('Security violation');

            // Step 2: Verify table still exists
            const assessments = await mockDatabaseService.getAssessments();
            expect(assessments).toBeDefined();

            // Step 3: Simulate unauthorized access
            await expect(mockDatabaseService.getAssessmentsByUser('unauthorized-user'))
                .rejects.toThrow('Access denied');
        });

        it('should handle data encryption', async () => {
            // Step 1: Create assessment with sensitive data
            const sensitiveRequest = {
                assessment_id: 'sensitive-assessment',
                serverName: 'test-server',
                assessmentType: 'compliance',
                options: {
                    includeDetails: true,
                    sensitiveData: 'confidential information'
                },
                timestamp: new Date().toISOString(),
                source: 'installer'
            };

            const assessmentId = await assessmentStore.createAssessment(sensitiveRequest);

            // Step 2: Verify data is encrypted in database
            const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
            expect(dbAssessment.request_data.sensitiveData).not.toBe('confidential information');
            expect(dbAssessment.request_data.sensitiveData).toContain('encrypted:');

            // Step 3: Verify data can be decrypted
            const decryptedData = await mockDatabaseService.decryptSensitiveData(dbAssessment.request_data.sensitiveData);
            expect(decryptedData).toBe('confidential information');
        });
    });

    describe('Database Performance Optimization', () => {
        it('should handle connection pooling efficiently', async () => {
            // Step 1: Create many concurrent connections
            const connectionPromises = Array(100).fill(null).map(() =>
                mockDatabaseService.getConnection()
            );

            const connections = await Promise.all(connectionPromises);
            expect(connections.length).toBe(100);

            // Step 2: Test connection pool performance
            const performance = await measurePerformance(
                'connection-pool',
                async () => {
                    const queryPromises = connections.map(connection =>
                        mockDatabaseService.executeQuery(connection, 'SELECT COUNT(*) FROM assessments')
                    );
                    return await Promise.all(queryPromises);
                },
                10
            );

            // Step 3: Verify performance
            expect(performance.averageTime).toBeLessThan(2000); // Less than 2 seconds average

            // Step 4: Verify connection pool health
            const poolHealth = await mockDatabaseService.getConnectionPoolHealth();
            expect(poolHealth.active_connections).toBeLessThan(poolHealth.max_connections);
            expect(poolHealth.wait_time).toBeLessThan(100); // Less than 100ms wait time
        });

        it('should handle query optimization', async () => {
            // Step 1: Create many assessments
            const requests = createBatchTestAssessments(1000);
            const assessmentIds = await assessmentStore.batchCreateAssessments(requests);

            // Step 2: Test query optimization
            const performance = await measurePerformance(
                'query-optimization',
                async () => {
                    const queryPromises = [
                        mockDatabaseService.getOptimizedAssessmentCount(),
                        mockDatabaseService.getOptimizedAssessmentsByState('pending'),
                        mockDatabaseService.getOptimizedAssessmentsByDateRange(new Date(Date.now() - 24 * 60 * 60 * 1000), new Date())
                    ];
                    return await Promise.all(queryPromises);
                },
                10
            );

            // Step 3: Verify performance
            expect(performance.averageTime).toBeLessThan(1000); // Less than 1 second average

            // Step 4: Verify query results
            const countResult = performance.results[0];
            expect(countResult).toBe(1000);

            const pendingResult = performance.results[1];
            expect(pendingResult.length).toBe(1000);

            const dateResult = performance.results[2];
            expect(dateResult.length).toBe(1000);
        });

        it('should handle index optimization', async () => {
            // Step 1: Create many assessments
            const requests = createBatchTestAssessments(5000);
            const assessmentIds = await assessmentStore.batchCreateAssessments(requests);

            // Step 2: Test index performance
            const performance = await measurePerformance(
                'index-optimization',
                async () => {
                    const queryPromises = [
                        mockDatabaseService.getAssessmentsByState('pending'),
                        mockDatabaseService.getAssessmentsByServerName('test-server'),
                        mockDatabaseService.getAssessmentsByDateRange(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), new Date())
                    ];
                    return await Promise.all(queryPromises);
                },
                5
            );

            // Step 3: Verify performance
            expect(performance.averageTime).toBeLessThan(3000); // Less than 3 seconds average

            // Step 4: Verify query results
            const pendingResult = performance.results[0];
            expect(pendingResult.length).toBe(5000);

            const serverResult = performance.results[1];
            expect(serverResult.length).toBeGreaterThan(0);

            const dateResult = performance.results[2];
            expect(dateResult.length).toBeGreaterThan(0);
        });

        it('should handle memory optimization', async () => {
            // Step 1: Create many assessments
            const requests = createBatchTestAssessments(10000);
            const assessmentIds = await assessmentStore.batchCreateAssessments(requests);

            // Step 2: Test memory usage
            const memoryUsage = process.memoryUsage();
            expect(memoryUsage.heapUsed).toBeGreaterThan(0);
            expect(memoryUsage.heapTotal).toBeGreaterThan(0);

            // Step 3: Test memory optimization
            const performance = await measurePerformance(
                'memory-optimization',
                async () => {
                    const queryPromises = Array(100).fill(null).map(() =>
                        mockDatabaseService.getAssessmentsLimited(100)
                    );
                    return await Promise.all(queryPromises);
                },
                5
            );

            // Step 4: Verify memory usage is controlled
            const finalMemoryUsage = process.memoryUsage();
            expect(finalMemoryUsage.heapUsed).toBeLessThan(memoryUsage.heapUsed * 2); // Less than 2x increase

            // Step 5: Verify performance
            expect(performance.averageTime).toBeLessThan(5000); // Less than 5 seconds average
        });
    });
});