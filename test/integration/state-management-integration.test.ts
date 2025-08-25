/**
 * State Management Integration Tests
 * 
 * This file contains comprehensive integration tests for the AssessmentStore,
 * AssessmentProcessor, and AssessmentController components, testing their
 * interactions and complete assessment workflows.
 */

import { describe, it, expect, beforeEach, afterEach, vi, test } from 'vitest';
import { mockDatabaseService } from '../mocks/database-mock';
import { mockComplianceServer } from '../mocks/compliance-server-mock';
import { TestAssessmentStore } from '../unit/assessment-store.test';
import { TestAssessmentProcessor } from '../unit/assessment-processor.test';
import { TestAssessmentController } from '../unit/assessment-controller.test';
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
describe('State Management Integration Tests', () => {
    let assessmentStore: TestAssessmentStore;
    let assessmentProcessor: TestAssessmentProcessor;
    let assessmentController: TestAssessmentController;

    beforeAll(async () => {
        await setupTestEnvironment();

        // Initialize all components
        assessmentStore = new TestAssessmentStore();
        assessmentProcessor = new TestAssessmentProcessor();
        assessmentController = new TestAssessmentController();
    });

    afterAll(async () => {
        await cleanupTestEnvironment();
    });

    beforeEach(() => {
        // Reset mock services before each test
        mockDatabaseService.reset();
        mockComplianceServer.reset();
        vi.clearAllMocks();
    });

    describe('Complete Assessment Workflow', () => {
        it('should handle complete assessment workflow from request to completion', async () => {
            // Step 1: Create assessment via controller
            const request = generateTestAssessmentData();
            const createResponse = await assessmentController.createAssessment(request);

            expect(createResponse.status).toBe(201);
            const assessmentId = createResponse.data.assessment_id;

            // Step 2: Verify assessment exists in store
            const storedAssessment = await assessmentStore.getState(assessmentId);
            expect(storedAssessment).toBeDefined();
            expect(storedAssessment.assessmentId).toBe(assessmentId);
            expect(storedAssessment.state).toBe('pending');

            // Step 3: Start processing via processor
            const processResponse = await assessmentProcessor.processAssessment(assessmentId);
            expect(processResponse).toBeDefined();
            expect(processResponse.assessment_id).toBe(assessmentId);

            // Step 4: Verify assessment is completed in store
            const completedAssessment = await assessmentStore.waitForCompletion(assessmentId, 10000);
            expect(completedAssessment).toBeDefined();
            expect(completedAssessment.state).toBe('completed');
            expect(completedAssessment.resultData).toBeDefined();

            // Step 5: Verify assessment is completed via controller
            const controllerResponse = await assessmentController.getAssessment(assessmentId);
            expect(controllerResponse.status).toBe(200);
            expect(controllerResponse.data.state).toBe('completed');
        });

        it('should handle assessment failure and retry workflow', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);
            const assessmentId = request.assessment_id;

            // Step 2: Simulate processing failure
            vi.spyOn(assessmentProcessor as any, 'processAssessmentInternal')
                .mockRejectedValue(new Error('Processing failed'));

            // Step 3: Process assessment (should fail)
            await expect(assessmentProcessor.processAssessment(assessmentId))
                .rejects.toThrow('Processing failed');

            // Step 4: Verify assessment is marked as failed
            const failedAssessment = await assessmentStore.getState(assessmentId);
            expect(failedAssessment.state).toBe('failed');
            expect(failedAssessment.errorMessage).toBe('Processing failed');

            // Step 5: Retry failed assessment
            const retriedIds = await assessmentProcessor.retryFailedAssessments();
            expect(retriedIds).toContain(assessmentId);

            // Step 6: Verify assessment is back to pending
            const retriedAssessment = await assessmentStore.getState(assessmentId);
            expect(retriedAssessment.state).toBe('pending');

            // Step 7: Process successfully
            const processResponse = await assessmentProcessor.processAssessment(assessmentId);
            expect(processResponse).toBeDefined();

            // Step 8: Verify completion
            const completedAssessment = await assessmentStore.waitForCompletion(assessmentId, 10000);
            expect(completedAssessment.state).toBe('completed');
        });

        it('should handle assessment cancellation workflow', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);
            const assessmentId = request.assessment_id;

            // Step 2: Start processing
            const processPromise = assessmentProcessor.processAssessment(assessmentId);

            // Step 3: Cancel assessment after short delay
            setTimeout(async () => {
                await assessmentController.cancelAssessment(assessmentId, 'User requested cancellation');
            }, 100);

            // Step 4: Verify cancellation
            const cancelledAssessment = await assessmentStore.getState(assessmentId);
            expect(cancelledAssessment.state).toBe('cancelled');
            expect(cancelledAssessment.errorMessage).toBe('User requested cancellation');

            // Step 5: Verify processing promise is rejected
            await expect(processPromise)
                .rejects.toThrow('Assessment cancelled');
        });

        it('should handle batch assessment workflow', async () => {
            // Step 1: Create multiple assessments
            const requests = createBatchTestAssessments(5);
            const createPromises = requests.map(request =>
                assessmentController.createAssessment(request)
            );

            const createResponses = await Promise.all(createPromises);
            expect(createResponses.every(r => r.status === 201)).toBe(true);

            const assessmentIds = createResponses.map(r => r.data.assessment_id);

            // Step 2: Process assessments in batch
            const processPromises = assessmentIds.map(id =>
                assessmentProcessor.processAssessment(id)
            );

            const processResults = await Promise.all(processPromises);
            expect(processResults).toHaveLength(5);
            expect(processResults.every(r => r !== undefined)).toBe(true);

            // Step 3: Verify all assessments are completed
            for (const assessmentId of assessmentIds) {
                const completedAssessment = await assessmentStore.waitForCompletion(assessmentId, 10000);
                expect(completedAssessment.state).toBe('completed');
            }

            // Step 4: Verify via controller
            const listResponse = await assessmentController.listAssessments();
            expect(listResponse.status).toBe(200);
            expect(listResponse.data.assessments).toHaveLength(5);
            expect(listResponse.data.assessments.every(a => a.state === 'completed')).toBe(true);
        });
    });

    describe('Service-to-Service Communication', () => {
        it('should handle database persistence and state management', async () => {
            // Step 1: Create assessment via controller
            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);
            const assessmentId = request.assessment_id;

            // Step 2: Verify database persistence
            const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
            expect(dbAssessment).toBeDefined();
            expect(dbAssessment.state).toBe('pending');

            // Step 3: Update state via processor
            await assessmentProcessor.processAssessment(assessmentId);

            // Step 4: Verify database persistence after processing
            const updatedDbAssessment = await mockDatabaseService.getAssessment(assessmentId);
            expect(updatedDbAssessment.state).toBe('completed');
            expect(updatedDbAssessment.result_data).toBeDefined();

            // Step 5: Verify store consistency
            const storeAssessment = await assessmentStore.getState(assessmentId);
            expect(storeAssessment.state).toBe('completed');
            expect(storeAssessment.resultData).toBeDefined();

            // Step 6: Verify controller consistency
            const controllerAssessment = await assessmentController.getAssessment(assessmentId);
            expect(controllerAssessment.data.state).toBe('completed');
        });

        it('should handle external compliance server integration', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);
            const assessmentId = request.assessment_id;

            // Step 2: Mock compliance server response
            mockComplianceServer.setMockResponse({
                assessment_id: assessmentId,
                compliance_score: 85,
                violations: 3,
                recommendations: ['Update security policies', 'Review configurations']
            });

            // Step 3: Process assessment
            const processResponse = await assessmentProcessor.processAssessment(assessmentId);

            // Step 4: Verify compliance server communication
            expect(processResponse.compliance_score).toBe(85);
            expect(processResponse.violations).toBe(3);
            expect(processResponse.recommendations).toContain('Update security policies');

            // Step 5: Verify result data includes compliance information
            const completedAssessment = await assessmentStore.waitForCompletion(assessmentId, 10000);
            expect(completedAssessment.resultData).toBeDefined();
            expect(completedAssessment.resultData.compliance_score).toBe(85);
        });

        it('should handle audit logging and compliance tracking', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);
            const assessmentId = request.assessment_id;

            // Step 2: Process assessment
            await assessmentProcessor.processAssessment(assessmentId);

            // Step 3: Verify audit trail
            const auditLogs = await mockDatabaseService.getAuditLogs(assessmentId);
            expect(auditLogs.length).toBeGreaterThan(0);

            // Verify key audit events
            const createEvent = auditLogs.find(log => log.event_type === 'assessment_created');
            expect(createEvent).toBeDefined();
            expect(createEvent.assessment_id).toBe(assessmentId);

            const processEvent = auditLogs.find(log => log.event_type === 'assessment_processing');
            expect(processEvent).toBeDefined();
            expect(processEvent.assessment_id).toBe(assessmentId);

            const completeEvent = auditLogs.find(log => log.event_type === 'assessment_completed');
            expect(completeEvent).toBeDefined();
            expect(completeEvent.assessment_id).toBe(assessmentId);
        });

        it('should handle rollback and recovery procedures', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);
            const assessmentId = request.assessment_id;

            // Step 2: Simulate database failure during processing
            mockDatabaseService.simulateOverload();

            // Step 3: Attempt to process (should fail)
            await expect(assessmentProcessor.processAssessment(assessmentId))
                .rejects.toThrow('Database connection failed');

            // Step 4: Verify assessment state is unchanged
            const assessment = await assessmentStore.getState(assessmentId);
            expect(assessment.state).toBe('pending');

            // Step 5: Restore database connection
            mockDatabaseService.restoreConnection();

            // Step 6: Retry processing
            const processResponse = await assessmentProcessor.processAssessment(assessmentId);
            expect(processResponse).toBeDefined();

            // Step 7: Verify successful completion
            const completedAssessment = await assessmentStore.waitForCompletion(assessmentId, 10000);
            expect(completedAssessment.state).toBe('completed');
        });
    });

    describe('Concurrent Operations', () => {
        it('should handle concurrent assessment creation and processing', async () => {
            // Step 1: Create multiple assessments concurrently
            const requests = createBatchTestAssessments(10);
            const createPromises = requests.map(request =>
                assessmentController.createAssessment(request)
            );

            const createResponses = await Promise.all(createPromises);
            expect(createResponses.every(r => r.status === 201)).toBe(true);

            const assessmentIds = createResponses.map(r => r.data.assessment_id);

            // Step 2: Process assessments concurrently
            const processPromises = assessmentIds.map(id =>
                assessmentProcessor.processAssessment(id)
            );

            const processResults = await Promise.all(processPromises);
            expect(processResults).toHaveLength(10);
            expect(processResults.every(r => r !== undefined)).toBe(true);

            // Step 3: Verify all assessments are completed
            const completionPromises = assessmentIds.map(id =>
                assessmentStore.waitForCompletion(id, 10000)
            );

            const completedAssessments = await Promise.all(completionPromises);
            expect(completedAssessments.every(a => a.state === 'completed')).toBe(true);

            // Step 4: Verify no data corruption
            for (const assessmentId of assessmentIds) {
                const assessment = await assessmentStore.getState(assessmentId);
                expect(assessment).toBeDefined();
                expect(assessment.assessmentId).toBe(assessmentId);
                expect(assessment.state).toBe('completed');
            }
        });

        it('should handle concurrent state updates', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);
            const assessmentId = request.assessment_id;

            // Step 2: Start processing
            const processPromise = assessmentProcessor.processAssessment(assessmentId);

            // Step 3: Concurrent progress updates
            const progressUpdates = [
                assessmentController.updateAssessmentProgress(assessmentId, 25, '25% complete'),
                assessmentController.updateAssessmentProgress(assessmentId, 50, '50% complete'),
                assessmentController.updateAssessmentProgress(assessmentId, 75, '75% complete'),
                assessmentController.updateAssessmentProgress(assessmentId, 100, '100% complete')
            ];

            await Promise.all(progressUpdates);

            // Step 4: Verify final state
            const completedAssessment = await assessmentStore.waitForCompletion(assessmentId, 10000);
            expect(completedAssessment.state).toBe('completed');
            expect(completedAssessment.progress).toBe(100);
        });

        it('should handle concurrent read operations', async () => {
            // Step 1: Create and complete assessment
            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);
            const assessmentId = request.assessment_id;

            await assessmentProcessor.processAssessment(assessmentId);
            await assessmentStore.waitForCompletion(assessmentId, 10000);

            // Step 2: Concurrent read operations
            const readPromises = [
                assessmentController.getAssessment(assessmentId),
                assessmentStore.getState(assessmentId),
                assessmentController.getAssessmentStats(),
                assessmentController.listAssessments()
            ];

            const readResults = await Promise.all(readPromises);
            expect(readResults).toHaveLength(4);

            // Verify all reads return consistent data
            const controllerAssessment = readResults[0].data;
            const storeAssessment = readResults[1];
            const stats = readResults[2].data;
            const list = readResults[3].data;

            expect(controllerAssessment.assessment_id).toBe(assessmentId);
            expect(storeAssessment.assessmentId).toBe(assessmentId);
            expect(stats.total).toBeGreaterThan(0);
            expect(list.assessments.length).toBeGreaterThan(0);
        });
    });

    describe('Error Recovery and Resilience', () => {
        it('should handle database connection failures gracefully', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);
            const assessmentId = request.assessment_id;

            // Step 2: Simulate database failure
            mockDatabaseService.simulateOverload();

            // Step 3: Attempt operations (should fail gracefully)
            await expect(assessmentController.getAssessment(assessmentId))
                .rejects.toThrow('Database connection failed');

            await expect(assessmentProcessor.processAssessment(assessmentId))
                .rejects.toThrow('Database connection failed');

            // Step 4: Restore database connection
            mockDatabaseService.restoreConnection();

            // Step 5: Verify operations work again
            const assessment = await assessmentController.getAssessment(assessmentId);
            expect(assessment.status).toBe(200);
        });

        it('should handle external service timeouts', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);
            const assessmentId = request.assessment_id;

            // Step 2: Simulate compliance server timeout
            mockComplianceServer.setTimeoutRate(1);

            // Step 3: Process assessment (should handle timeout)
            const processResponse = await assessmentProcessor.processAssessment(assessmentId);
            expect(processResponse).toBeDefined();

            // Step 4: Verify assessment completes despite timeout
            const completedAssessment = await assessmentStore.waitForCompletion(assessmentId, 10000);
            expect(completedAssessment.state).toBe('completed');
        });

        it('should handle network failures and retries', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);
            const assessmentId = request.assessment_id;

            // Step 2: Simulate network failures
            mockComplianceServer.setFailureRate(0.5);

            // Step 3: Process assessment (should retry and succeed)
            const processResponse = await assessmentProcessor.processAssessment(assessmentId);
            expect(processResponse).toBeDefined();

            // Step 4: Verify successful completion
            const completedAssessment = await assessmentStore.waitForCompletion(assessmentId, 10000);
            expect(completedAssessment.state).toBe('completed');
        });

        it('should handle data corruption scenarios', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);
            const assessmentId = request.assessment_id;

            // Step 2: Simulate data corruption
            await mockDatabaseService.corruptData(assessmentId);

            // Step 3: Attempt to process (should detect and handle corruption)
            await expect(assessmentProcessor.processAssessment(assessmentId))
                .rejects.toThrow('Data corruption detected');

            // Step 4: Verify assessment is marked as failed
            const failedAssessment = await assessmentStore.getState(assessmentId);
            expect(failedAssessment.state).toBe('failed');
            expect(failedAssessment.errorMessage).toContain('Data corruption');

            // Step 5: Verify recovery through retry
            const retriedIds = await assessmentProcessor.retryFailedAssessments();
            expect(retriedIds).toContain(assessmentId);

            // Step 6: Process successfully after recovery
            const processResponse = await assessmentProcessor.processAssessment(assessmentId);
            expect(processResponse).toBeDefined();
        });

        it('should handle system resource exhaustion', async () => {
            // Step 1: Create many assessments to test resource limits
            const requests = createBatchTestAssessments(100);
            const createPromises = requests.map(request =>
                assessmentController.createAssessment(request)
            );

            const createResponses = await Promise.all(createPromises);
            expect(createResponses.every(r => r.status === 201)).toBe(true);

            const assessmentIds = createResponses.map(r => r.data.assessment_id);

            // Step 2: Process assessments in batches to avoid resource exhaustion
            const batchSize = 10;
            const results = [];

            for (let i = 0; i < assessmentIds.length; i += batchSize) {
                const batch = assessmentIds.slice(i, i + batchSize);
                const batchPromises = batch.map(id =>
                    assessmentProcessor.processAssessment(id).catch(error => ({ error: error.message }))
                );

                const batchResults = await Promise.all(batchPromises);
                results.push(...batchResults);

                // Small delay between batches
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            // Step 3: Verify most assessments completed successfully
            const successful = results.filter(r => !r.error).length;
            const failed = results.filter(r => r.error).length;

            expect(successful).toBeGreaterThan(80); // At least 80% success rate
            expect(failed).toBeLessThan(20); // Less than 20% failures

            // Step 4: Verify system health
            const health = await assessmentController.getHealthStatus();
            expect(health.overall).toBe('healthy');
        });
    });

    describe('Performance and Load Testing', () => {
        it('should handle high load assessment processing', async () => {
            // Step 1: Create many assessments
            const requests = createBatchTestAssessments(50);
            const createPromises = requests.map(request =>
                assessmentController.createAssessment(request)
            );

            const createResponses = await Promise.all(createPromises);
            expect(createResponses.every(r => r.status === 201)).toBe(true);

            const assessmentIds = createResponses.map(r => r.data.assessment_id);

            // Step 2: Process assessments under load
            const performance = await measurePerformance(
                'high-load-processing',
                async () => {
                    const processPromises = assessmentIds.map(id =>
                        assessmentProcessor.processAssessment(id)
                    );
                    return await Promise.all(processPromises);
                },
                5
            );

            // Step 3: Verify performance metrics
            expect(performance.averageTime).toBeLessThan(30000); // Less than 30 seconds average
            expect(performance.results.every(r => r !== undefined)).toBe(true);

            // Step 4: Verify all assessments completed
            for (const assessmentId of assessmentIds) {
                const completedAssessment = await assessmentStore.waitForCompletion(assessmentId, 10000);
                expect(completedAssessment.state).toBe('completed');
            }
        });

        it('should handle database query performance under load', async () => {
            // Step 1: Create and complete many assessments
            const requests = createBatchTestAssessments(100);
            for (const request of requests) {
                await assessmentController.createAssessment(request);
                await assessmentProcessor.processAssessment(request.assessment_id);
                await assessmentStore.waitForCompletion(request.assessment_id, 10000);
            }

            // Step 2: Test query performance under load
            const performance = await measurePerformance(
                'query-performance',
                async () => {
                    const queryPromises = [
                        assessmentController.listAssessments(),
                        assessmentController.getAssessmentStats(),
                        assessmentController.listAssessments({ state: ['completed'] }),
                        assessmentController.listAssessments({ limit: 10, offset: 0 })
                    ];

                    return await Promise.all(queryPromises);
                },
                10
            );

            // Step 3: Verify query performance
            expect(performance.averageTime).toBeLessThan(5000); // Less than 5 seconds average

            // Step 4: Verify query results
            const listResponse = performance.results[0];
            expect(listResponse.status).toBe(200);
            expect(listResponse.data.assessments.length).toBe(100);

            const statsResponse = performance.results[1];
            expect(statsResponse.status).toBe(200);
            expect(statsResponse.data.total).toBe(100);
        });

        it('should handle memory usage and garbage collection', async () => {
            // Step 1: Create and process many assessments
            const requests = createBatchTestAssessments(200);
            const assessmentIds: string[] = [];

            for (const request of requests) {
                const response = await assessmentController.createAssessment(request);
                assessmentIds.push(response.data.assessment_id);

                await assessmentProcessor.processAssessment(response.data.assessment_id);
                await assessmentStore.waitForCompletion(response.data.assessment_id, 10000);
            }

            // Step 2: Force garbage collection (if available)
            if (global.gc) {
                global.gc();
            }

            // Step 3: Verify system stability after memory pressure
            const health = await assessmentController.getHealthStatus();
            expect(health.overall).toBe('healthy');

            // Step 4: Verify continued functionality
            const listResponse = await assessmentController.listAssessments();
            expect(listResponse.status).toBe(200);
            expect(listResponse.data.assessments.length).toBe(200);
        });

        it('should handle connection pooling efficiency', async () => {
            // Step 1: Create many assessments
            const requests = createBatchTestAssessments(100);
            const createPromises = requests.map(request =>
                assessmentController.createAssessment(request)
            );

            const createResponses = await Promise.all(createPromises);
            expect(createResponses.every(r => r.status === 201)).toBe(true);

            const assessmentIds = createResponses.map(r => r.data.assessment_id);

            // Step 2: Process assessments to test connection pooling
            const performance = await measurePerformance(
                'connection-pooling',
                async () => {
                    const processPromises = assessmentIds.map(id =>
                        assessmentProcessor.processAssessment(id)
                    );
                    return await Promise.all(processPromises);
                },
                5
            );

            // Step 3: Verify connection efficiency
            expect(performance.averageTime).toBeLessThan(20000); // Less than 20 seconds average

            // Step 4: Verify connection pool health
            const dbHealth = await mockDatabaseService.healthCheck();
            expect(dbHealth.active_connections).toBeLessThan(dbHealth.total_connections);
            expect(dbHealth.success_rate).toBeGreaterThan(0.95); // 95%+ success rate
        });

        it('should handle caching effectiveness', async () => {
            // Step 1: Create and complete assessment
            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);
            const assessmentId = request.assessment_id;

            await assessmentProcessor.processAssessment(assessmentId);
            await assessmentStore.waitForCompletion(assessmentId, 10000);

            // Step 2: Test caching effectiveness with repeated reads
            const performance = await measurePerformance(
                'caching-effectiveness',
                async () => {
                    const readPromises = Array(100).fill(null).map(() =>
                        assessmentController.getAssessment(assessmentId)
                    );
                    return await Promise.all(readPromises);
                },
                5
            );

            // Step 3: Verify caching improves performance
            expect(performance.averageTime).toBeLessThan(1000); // Less than 1 second average for 100 reads

            // Step 4: Verify all reads return consistent data
            const firstRead = performance.results[0];
            expect(firstRead.status).toBe(200);
            expect(firstRead.data.assessment_id).toBe(assessmentId);
        });
    });

    describe('Data Consistency and Integrity', () => {
        it('should maintain data consistency across services', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);
            const assessmentId = request.assessment_id;

            // Step 2: Read from all services
            const controllerAssessment = await assessmentController.getAssessment(assessmentId);
            const storeAssessment = await assessmentStore.getState(assessmentId);
            const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);

            // Step 3: Verify consistency
            expect(controllerAssessment.data.assessment_id).toBe(assessmentId);
            expect(storeAssessment.assessmentId).toBe(assessmentId);
            expect(dbAssessment.assessment_id).toBe(assessmentId);

            expect(controllerAssessment.data.state).toBe(storeAssessment.state);
            expect(storeAssessment.state).toBe(dbAssessment.state);

            expect(controllerAssessment.data.created_at).toBe(storeAssessment.createdAt);
            expect(storeAssessment.createdAt).toBe(dbAssessment.created_at);
        });

        it('should handle concurrent modification conflicts', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);
            const assessmentId = request.assessment_id;

            // Step 2: Concurrent updates from different services
            const updatePromises = [
                assessmentController.updateAssessmentProgress(assessmentId, 25, '25%'),
                assessmentController.updateAssessmentProgress(assessmentId, 50, '50%'),
                assessmentController.updateAssessmentProgress(assessmentId, 75, '75%')
            ];

            const updateResults = await Promise.all(updatePromises);

            // Step 3: Verify only one update succeeded (optimistic locking)
            const successfulUpdates = updateResults.filter(r => r.status === 200);
            expect(successfulUpdates.length).toBe(1);

            // Step 4: Verify final state
            const finalAssessment = await assessmentStore.getState(assessmentId);
            expect(finalAssessment.progress).toBeGreaterThan(0);
            expect(finalAssessment.progress).toBeLessThanOrEqual(100);
        });

        it('should handle transaction integrity', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);
            const assessmentId = request.assessment_id;

            // Step 2: Simulate transaction failure during processing
            mockDatabaseService.simulateTransactionFailure();

            // Step 3: Attempt to process (should fail)
            await expect(assessmentProcessor.processAssessment(assessmentId))
                .rejects.toThrow('Transaction failed');

            // Step 4: Verify assessment state is unchanged (transaction rollback)
            const assessment = await assessmentStore.getState(assessmentId);
            expect(assessment.state).toBe('pending');

            // Step 5: Restore transaction functionality
            mockDatabaseService.restoreTransaction();

            // Step 6: Process successfully
            const processResponse = await assessmentProcessor.processAssessment(assessmentId);
            expect(processResponse).toBeDefined();

            // Step 7: Verify successful completion
            const completedAssessment = await assessmentStore.waitForCompletion(assessmentId, 10000);
            expect(completedAssessment.state).toBe('completed');
        });

        it('should handle data validation across services', async () => {
            // Step 1: Create assessment with valid data
            const validRequest = generateTestAssessmentData();
            await assessmentController.createAssessment(validRequest);
            const assessmentId = validRequest.assessment_id;

            // Step 2: Verify data validation in all services
            const controllerAssessment = await assessmentController.getAssessment(assessmentId);
            const storeAssessment = await assessmentStore.getState(assessmentId);
            const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);

            // Step 3: Verify data integrity
            expect(controllerAssessment.data.assessment_id).toBe(assessmentId);
            expect(storeAssessment.assessmentId).toBe(assessmentId);
            expect(dbAssessment.assessment_id).toBe(assessmentId);

            expect(controllerAssessment.data.state).toBe('pending');
            expect(storeAssessment.state).toBe('pending');
            expect(dbAssessment.state).toBe('pending');

            // Step 4: Process assessment
            await assessmentProcessor.processAssessment(assessmentId);

            // Step 5: Verify data integrity after processing
            const finalControllerAssessment = await assessmentController.getAssessment(assessmentId);
            const finalStoreAssessment = await assessmentStore.getState(assessmentId);
            const finalDbAssessment = await mockDatabaseService.getAssessment(assessmentId);

            expect(finalControllerAssessment.data.state).toBe('completed');
            expect(finalStoreAssessment.state).toBe('completed');
            expect(finalDbAssessment.state).toBe('completed');
        });
    });

    describe('Monitoring and Observability', () => {
        it('should provide comprehensive monitoring data', async () => {
            // Step 1: Create and process multiple assessments
            const requests = createBatchTestAssessments(10);
            for (const request of requests) {
                await assessmentController.createAssessment(request);
                await assessmentProcessor.processAssessment(request.assessment_id);
                await assessmentStore.waitForCompletion(request.assessment_id, 10000);
            }

            // Step 2: Get monitoring data from all services
            const storeHealth = await assessmentStore.getHealthStatus();
            const processorHealth = await assessmentProcessor.getHealthStatus();
            const controllerHealth = await assessmentController.getHealthStatus();

            // Step 3: Verify monitoring data
            expect(storeHealth.overall).toBeDefined();
            expect(processorHealth.overall).toBeDefined();
            expect(controllerHealth.overall).toBeDefined();

            expect(storeHealth.services.database).toBeDefined();
            expect(processorHealth.services.database).toBeDefined();
            expect(controllerHealth.services.database).toBeDefined();

            expect(storeHealth.services.cache).toBeDefined();
            expect(processorHealth.services.compliance).toBeDefined();
            expect(controllerHealth.services.compliance).toBeDefined();
        });

        it('should track performance metrics accurately', async () => {
            // Step 1: Create and process assessments
            const requests = createBatchTestAssessments(5);
            const startTime = Date.now();

            for (const request of requests) {
                const createStart = Date.now();
                await assessmentController.createAssessment(request);
                const createEnd = Date.now();

                const processStart = Date.now();
                await assessmentProcessor.processAssessment(request.assessment_id);
                const processEnd = Date.now();

                const waitStart = Date.now();
                await assessmentStore.waitForCompletion(request.assessment_id, 10000);
                const waitEnd = Date.now();

                // Verify performance tracking
                expect(createEnd - createStart).toBeLessThan(1000);
                expect(processEnd - processStart).toBeLessThan(5000);
                expect(waitEnd - waitStart).toBeLessThan(10000);
            }

            const endTime = Date.now();
            const totalTime = endTime - startTime;

            // Step 2: Get metrics
            const storeMetrics = await assessmentStore.getMetrics();
            const processorMetrics = await assessmentProcessor.getMetrics();
            const controllerMetrics = await assessmentController.getMetrics();

            // Step 3: Verify metrics
            expect(storeMetrics.totalAssessments).toBe(5);
            expect(processorMetrics.totalAssessments).toBe(5);
            expect(controllerMetrics.totalAssessments).toBe(5);

            expect(storeMetrics.averageProcessingTime).toBeGreaterThan(0);
            expect(processorMetrics.averageProcessingTime).toBeGreaterThan(0);
            expect(controllerMetrics.averageProcessingTime).toBeGreaterThan(0);
        });

        it('should provide error tracking and alerting', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);
            const assessmentId = request.assessment_id;

            // Step 2: Simulate processing error
            vi.spyOn(assessmentProcessor as any, 'processAssessmentInternal')
                .mockRejectedValue(new Error('Processing error'));

            // Step 3: Process assessment (should fail)
            await expect(assessmentProcessor.processAssessment(assessmentId))
                .rejects.toThrow('Processing error');

            // Step 4: Verify error tracking
            const failedAssessment = await assessmentStore.getState(assessmentId);
            expect(failedAssessment.state).toBe('failed');
            expect(failedAssessment.errorMessage).toBe('Processing error');

            // Step 5: Get health status (should reflect error)
            const health = await assessmentController.getHealthStatus();
            expect(health.overall).toBe('degraded');

            // Step 6: Verify error logging
            const errorLogs = await mockDatabaseService.getErrorLogs();
            expect(errorLogs.length).toBeGreaterThan(0);
            expect(errorLogs.some(log => log.message.includes('Processing error'))).toBe(true);
        });

        it('should provide audit trail for compliance', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);
            const assessmentId = request.assessment_id;

            // Step 2: Process assessment
            await assessmentProcessor.processAssessment(assessmentId);
            await assessmentStore.waitForCompletion(assessmentId, 10000);

            // Step 3: Get audit trail
            const auditTrail = await mockDatabaseService.getAuditTrail(assessmentId);

            // Step 4: Verify audit trail
            expect(auditTrail.length).toBeGreaterThan(0);

            const createEvent = auditTrail.find(event => event.event_type === 'assessment_created');
            expect(createEvent).toBeDefined();
            expect(createEvent.assessment_id).toBe(assessmentId);

            const processEvent = auditTrail.find(event => event.event_type === 'assessment_processing');
            expect(processEvent).toBeDefined;
... (还有17个字符未显示)
expect(processEvent).toBeDefined();
        expect(processEvent.assessment_id).toBe(assessmentId);

        const completeEvent = auditTrail.find(event => event.event_type === 'assessment_completed');
        expect(completeEvent).toBeDefined();
        expect(completeEvent.assessment_id).toBe(assessmentId);

        // Step 5: Verify audit trail includes timestamps and user information
        for (const event of auditTrail) {
            expect(event.timestamp).toBeDefined();
            expect(event.user_id).toBeDefined();
            expect(event.event_type).toBeDefined();
        }
    });

    it('should provide real-time metrics and alerts', async () => {
        // Step 1: Create and process assessments
        const requests = createBatchTestAssessments(10);
        for (const request of requests) {
            await assessmentController.createAssessment(request);
            await assessmentProcessor.processAssessment(request.assessment_id);
            await assessmentStore.waitForCompletion(request.assessment_id, 10000);
        }

        // Step 2: Get real-time metrics
        const storeMetrics = await assessmentStore.getMetrics();
        const processorMetrics = await assessmentProcessor.getMetrics();
        const controllerMetrics = await assessmentController.getMetrics();

        // Step 3: Verify metrics include real-time data
        expect(storeMetrics.totalAssessments).toBe(10);
        expect(processorMetrics.totalAssessments).toBe(10);
        expect(controllerMetrics.totalAssessments).toBe(10);

        expect(storeMetrics.activeAssessments).toBe(0);
        expect(processorMetrics.activeAssessments).toBe(0);
        expect(controllerMetrics.activeAssessments).toBe(0);

        expect(storeMetrics.completedAssessments).toBe(10);
        expect(processorMetrics.completedAssessments).toBe(10);
        expect(controllerMetrics.completedAssessments).toBe(10);

        // Step 4: Verify error rate
        expect(storeMetrics.errorRate).toBe(0);
        expect(processorMetrics.errorRate).toBe(0);
        expect(controllerMetrics.errorRate).toBe(0);

        // Step 5: Verify throughput
        expect(storeMetrics.throughputPerMinute).toBeGreaterThan(0);
        expect(processorMetrics.throughputPerMinute).toBeGreaterThan(0);
        expect(controllerMetrics.throughputPerMinute).toBeGreaterThan(0);
    });
});

describe('Migration and Compatibility', () => {
    it('should handle migration from legacy system', async () => {
        // Step 1: Create assessment using legacy system
        const legacyRequest = {
            assessment_id: 'legacy-assessment',
            serverName: 'legacy-server',
            assessmentType: 'compliance',
            options: { includeDetails: true },
            timestamp: new Date().toISOString(),
            source: 'legacy'
        };

        // Step 2: Simulate legacy system creation
        await mockDatabaseService.createLegacyAssessment(legacyRequest);

        // Step 3: Verify assessment exists in legacy format
        const legacyAssessment = await mockDatabaseService.getLegacyAssessment('legacy-assessment');
        expect(legacyAssessment).toBeDefined();
        expect(legacyAssessment.assessment_id).toBe('legacy-assessment');

        // Step 4: Migrate to new system
        const migratedAssessment = await assessmentStore.migrateLegacyAssessment('legacy-assessment');
        expect(migratedAssessment).toBeDefined();
        expect(migratedAssessment.assessmentId).toBe('legacy-assessment');
        expect(migratedAssessment.state).toBe('pending');

        // Step 5: Verify migration consistency
        const newAssessment = await assessmentStore.getState('legacy-assessment');
        expect(newAssessment.assessmentId).toBe('legacy-assessment');
        expect(newAssessment.state).toBe('pending');

        // Step 6: Process migrated assessment
        await assessmentProcessor.processAssessment('legacy-assessment');
        const completedAssessment = await assessmentStore.waitForCompletion('legacy-assessment', 10000);
        expect(completedAssessment.state).toBe('completed');
    });

    it('should maintain backward compatibility', async () => {
        // Step 1: Create assessment using new system
        const request = generateTestAssessmentData();
        await assessmentController.createAssessment(request);
        const assessmentId = request.assessment_id;

        // Step 2: Verify backward compatibility with legacy API
        const legacyResponse = await mockDatabaseService.getLegacyAssessment(assessmentId);
        expect(legacyResponse).toBeDefined();
        expect(legacyResponse.assessment_id).toBe(assessmentId);

        // Step 3: Process assessment
        await assessmentProcessor.processAssessment(assessmentId);
        await assessmentStore.waitForCompletion(assessmentId, 10000);

        // Step 4: Verify legacy API still works after processing
        const legacyCompletedResponse = await mockDatabaseService.getLegacyAssessment(assessmentId);
        expect(legacyCompletedResponse).toBeDefined();
        expect(legacyCompletedResponse.state).toBe('completed');
    });

    it('should handle dual-mode operation', async () => {
        // Step 1: Create assessments in both modes
        const newRequest = generateTestAssessmentData();
        const legacyRequest = {
            assessment_id: 'legacy-dual-mode',
            serverName: 'legacy-server',
            assessmentType: 'compliance',
            options: { includeDetails: true },
            timestamp: new Date().toISOString(),
            source: 'legacy'
        };

        await assessmentController.createAssessment(newRequest);
        await mockDatabaseService.createLegacyAssessment(legacyRequest);

        // Step 2: Process both assessments
        await assessmentProcessor.processAssessment(newRequest.assessment_id);
        await assessmentProcessor.processAssessment('legacy-dual-mode');

        // Step 3: Verify both complete successfully
        const newCompleted = await assessmentStore.waitForCompletion(newRequest.assessment_id, 10000);
        const legacyCompleted = await assessmentStore.waitForCompletion('legacy-dual-mode', 10000);

        expect(newCompleted.state).toBe('completed');
        expect(legacyCompleted.state).toBe('completed');
    });

    it('should handle gradual cutover with feature flags', async () => {
        // Step 1: Configure gradual cutover
        await assessmentStore.enableLegacyMode(false);

        // Step 2: Create assessment using new system
        const request = generateTestAssessmentData();
        await assessmentController.createAssessment(request);
        const assessmentId = request.assessment_id;

        // Step 3: Process assessment
        await assessmentProcessor.processAssessment(assessmentId);
        const completedAssessment = await assessmentStore.waitForCompletion(assessmentId, 10000);

        // Step 4: Verify new system works
        expect(completedAssessment.state).toBe('completed');

        // Step 5: Enable legacy mode for fallback
        await assessmentStore.enableLegacyMode(true);

        // Step 6: Create another assessment
        const legacyRequest = {
            assessment_id: 'legacy-cutover',
            serverName: 'legacy-server',
            assessmentType: 'compliance',
            options: { includeDetails: true },
            timestamp: new Date().toISOString(),
            source: 'legacy'
        };

        await mockDatabaseService.createLegacyAssessment(legacyRequest);

        // Step 7: Verify fallback works
        const legacyAssessment = await assessmentStore.getState('legacy-cutover');
        expect(legacyAssessment).toBeDefined();
        expect(legacyAssessment.assessmentId).toBe('legacy-cutover');
    });

    it('should handle rollback procedures', async () => {
        // Step 1: Create assessment using new system
        const request = generateTestAssessmentData();
        await assessmentController.createAssessment(request);
        const assessmentId = request.assessment_id;

        // Step 2: Process assessment
        await assessmentProcessor.processAssessment(assessmentId);
        const completedAssessment = await assessmentStore.waitForCompletion(assessmentId, 10000);

        // Step 3: Verify new system works
        expect(completedAssessment.state).toBe('completed');

        // Step 4: Simulate rollback scenario
        await assessmentStore.rollbackToLegacy(assessmentId);

        // Step 5: Verify rollback worked
        const rollbackAssessment = await mockDatabaseService.getLegacyAssessment(assessmentId);
        expect(rollbackAssessment).toBeDefined();
        expect(rollbackAssessment.assessment_id).toBe(assessmentId);

        // Step 6: Verify system health after rollback
        const health = await assessmentController.getHealthStatus();
        expect(health.overall).toBe('healthy');
    });
});

describe('Edge Cases and Error Scenarios', () => {
    it('should handle assessment ID collisions during migration', async () => {
        // Step 1: Create assessment in both systems with same ID
        const assessmentId = 'collision-assessment';
        const newRequest = {
            assessment_id: assessmentId,
            serverName: 'new-server',
            assessmentType: 'compliance',
            options: { includeDetails: true },
            timestamp: new Date().toISOString(),
            source: 'new'
        };

        const legacyRequest = {
            assessment_id: assessmentId,
            serverName: 'legacy-server',
            assessmentType: 'compliance',
            options: { includeDetails: true },
            timestamp: new Date().toISOString(),
            source: 'legacy'
        };

        await assessmentController.createAssessment(newRequest);
        await mockDatabaseService.createLegacyAssessment(legacyRequest);

        // Step 2: Attempt migration (should detect collision)
        await expect(assessmentStore.migrateLegacyAssessment(assessmentId))
            .rejects.toThrow('Assessment ID collision detected');

        // Step 3: Verify both assessments still exist
        const newAssessment = await assessmentStore.getState(assessmentId);
        const legacyAssessment = await mockDatabaseService.getLegacyAssessment(assessmentId);

        expect(newAssessment).toBeDefined();
        expect(legacyAssessment).toBeDefined();
    });

    it('should handle incomplete migration data', async () => {
        // Step 1: Create legacy assessment with incomplete data
        const incompleteRequest = {
            assessment_id: 'incomplete-assessment',
            serverName: 'legacy-server',
            // Missing required fields
            timestamp: new Date().toISOString(),
            source: 'legacy'
        };

        await mockDatabaseService.createLegacyAssessment(incompleteRequest);

        // Step 2: Attempt migration (should handle gracefully)
        const migratedAssessment = await assessmentStore.migrateLegacyAssessment('incomplete-assessment');
        expect(migratedAssessment).toBeDefined();
        expect(migratedAssessment.assessmentId).toBe('incomplete-assessment');

        // Step 3: Verify migration completed with default values
        const assessment = await assessmentStore.getState('incomplete-assessment');
        expect(assessment).toBeDefined();
        expect(assessment.state).toBe('pending');
    });

    it('should handle migration timeout scenarios', async () => {
        // Step 1: Create large number of legacy assessments
        const legacyRequests = Array(100).fill(null).map((_, i) => ({
            assessment_id: `timeout-assessment-${i}`,
            serverName: `legacy-server-${i}`,
            assessmentType: 'compliance',
            options: { includeDetails: true },
            timestamp: new Date().toISOString(),
            source: 'legacy'
        }));

        for (const request of legacyRequests) {
            await mockDatabaseService.createLegacyAssessment(request);
        }

        // Step 2: Attempt batch migration with timeout
        await expect(assessmentStore.batchMigrateLegacyAssessments(50, 5000))
            .rejects.toThrow('Migration timeout');

        // Step 3: Verify partial migration occurred
        const migratedCount = await assessmentStore.getMigratedCount();
        expect(migratedCount).toBeGreaterThan(0);
        expect(migratedCount).toBeLessThan(50);
    });

    it('should handle concurrent migration attempts', async () => {
        // Step 1: Create legacy assessments
        const legacyRequests = [
            { assessment_id: 'concurrent-1', serverName: 'server-1', assessmentType: 'compliance', options: {}, timestamp: new Date().toISOString(), source: 'legacy' },
            { assessment_id: 'concurrent-2', serverName: 'server-2', assessmentType: 'compliance', options: {}, timestamp: new Date().toISOString(), source: 'legacy' }
        ];

        for (const request of legacyRequests) {
            await mockDatabaseService.createLegacyAssessment(request);
        }

        // Step 2: Attempt concurrent migration
        const migrationPromises = legacyRequests.map(request =>
            assessmentStore.migrateLegacyAssessment(request.assessment_id)
        );

        const migrationResults = await Promise.all(migrationPromises);

        // Step 3: Verify both migrations succeeded
        expect(migrationResults).toHaveLength(2);
        expect(migrationResults.every(r => r !== undefined)).toBe(true);

        // Step 4: Verify no duplicate migrations
        const migratedAssessments = await assessmentStore.listAssessments();
        expect(migratedAssessments.data.assessments.length).toBe(2);
    });

    it('should handle migration data validation', async () => {
        // Step 1: Create legacy assessment with invalid data
        const invalidRequest = {
            assessment_id: 'invalid-assessment',
            serverName: '', // Invalid server name
            assessmentType: 'invalid-type', // Invalid assessment type
            options: { includeDetails: 'invalid' }, // Invalid option type
            timestamp: 'invalid-timestamp', // Invalid timestamp
            source: 'legacy'
        };

        await mockDatabaseService.createLegacyAssessment(invalidRequest);

        // Step 2: Attempt migration (should validate and fix data)
        const migratedAssessment = await assessmentStore.migrateLegacyAssessment('invalid-assessment');
        expect(migratedAssessment).toBeDefined();
        expect(migratedAssessment.assessmentId).toBe('invalid-assessment');

        // Step 3: Verify data was sanitized
        const assessment = await assessmentStore.getState('invalid-assessment');
        expect(assessment).toBeDefined();
        expect(assessment.requestData.serverName).toBe(''); // Empty but valid
        expect(assessment.requestData.assessmentType).toBe('invalid-type'); // Invalid but preserved
    });
});
});