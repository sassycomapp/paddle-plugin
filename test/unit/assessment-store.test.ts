/**
 * AssessmentStore Unit Tests
 *
 * This file contains comprehensive unit tests for the AssessmentStore component,
 * testing all CRUD operations, state transitions, error handling, and edge cases.
 */

import { describe, it, expect, beforeEach, afterEach, vi, test } from 'vitest';
import { mockDatabaseService } from '../mocks/database-mock';
import { mockComplianceServer } from '../mocks/compliance-server-mock';
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

// Mock AssessmentStore implementation for testing
class TestAssessmentStore {
    constructor() {
        // Initialize with mock dependencies
        this.database = mockDatabaseService;
        this.complianceServer = mockComplianceServer;
        this.logger = console;
    }

    // Mock AssessmentStore methods
    async createAssessment(request: any): Promise<string> {
        // Validate request
        if (!request.assessment_id || !request.serverName || !request.assessmentType) {
            throw new Error('Invalid assessment request');
        }

        // Create assessment in database
        const assessment = await this.database.createAssessment({
            assessment_id: request.assessment_id,
            state: 'pending',
            request_data: request,
            progress: 0,
            priority: request.priority || 5,
            retry_count: 0,
            timeout_seconds: request.timeout || 300,
            max_retries: 3
        });

        return assessment.assessment_id;
    }

    async getState(assessmentId: string): Promise<any> {
        const assessment = await this.database.getAssessment(assessmentId);
        if (!assessment) {
            throw new Error('Assessment not found');
        }

        return {
            assessmentId: assessment.assessment_id,
            state: assessment.state,
            version: assessment.version,
            progress: assessment.progress,
            message: assessment.error_message,
            createdAt: assessment.created_at.toISOString(),
            updatedAt: assessment.updated_at.toISOString(),
            completedAt: assessment.completed_at?.toISOString(),
            requestData: assessment.request_data,
            resultData: assessment.result_data,
            errorMessage: assessment.error_message,
            retryCount: assessment.retry_count,
            nextRetryAt: assessment.next_retry_at
        };
    }

    async waitForCompletion(assessmentId: string, timeout: number = 30000): Promise<any> {
        const startTime = Date.now();
        const checkInterval = 100;

        while (Date.now() - startTime < timeout) {
            const state = await this.getState(assessmentId);

            if (state.state === 'completed' || state.state === 'failed' || state.state === 'cancelled') {
                return state;
            }

            await new Promise(resolve => setTimeout(resolve, checkInterval));
        }

        throw new Error('Assessment timeout');
    }

    async updateProgress(assessmentId: string, progress: number, message?: string): Promise<void> {
        if (progress < 0 || progress > 100) {
            throw new Error('Progress must be between 0 and 100');
        }

        const current = await this.getState(assessmentId);
        await this.database.updateAssessment(assessmentId, {
            progress,
            error_message: message,
            updated_at: new Date()
        }, current.version);
    }

    async completeAssessment(assessmentId: string, result: any): Promise<void> {
        const current = await this.getState(assessmentId);

        if (current.state !== 'processing') {
            throw new Error(`Cannot complete assessment in ${current.state} state`);
        }

        await this.database.updateAssessment(assessmentId, {
            state: 'completed',
            progress: 100,
            result_data: result,
            completed_at: new Date(),
            updated_at: new Date()
        }, current.version);
    }

    async failAssessment(assessmentId: string, error: string): Promise<void> {
        const current = await this.getState(assessmentId);

        if (current.state !== 'processing') {
            throw new Error(`Cannot fail assessment in ${current.state} state`);
        }

        await this.database.updateAssessment(assessmentId, {
            state: 'failed',
            error_message: error,
            completed_at: new Date(),
            updated_at: new Date()
        }, current.version);
    }

    async cancelAssessment(assessmentId: string, reason?: string): Promise<void> {
        const current = await this.getState(assessmentId);

        if (current.state === 'completed' || current.state === 'failed') {
            throw new Error(`Cannot cancel ${current.state} assessment`);
        }

        await this.database.updateAssessment(assessmentId, {
            state: 'cancelled',
            error_message: reason,
            completed_at: new Date(),
            updated_at: new Date()
        }, current.version);
    }

    async listAssessments(filters?: any): Promise<any> {
        const result = await this.database.listAssessments(filters);
        return {
            assessments: result.assessments.map((assessment: any) => ({
                assessmentId: assessment.assessment_id,
                state: assessment.state,
                version: assessment.version,
                progress: assessment.progress,
                createdAt: assessment.created_at.toISOString(),
                updatedAt: assessment.updated_at.toISOString(),
                completedAt: assessment.completed_at?.toISOString(),
                requestData: assessment.request_data,
                resultData: assessment.result_data,
                errorMessage: assessment.error_message,
                retryCount: assessment.retry_count
            })),
            total: result.total
        };
    }

    async getAssessmentStats(): Promise<any> {
        const stats = await this.database.getAssessmentStats();
        return {
            total: stats.total,
            byState: stats.by_state,
            byPriority: stats.by_priority,
            successRate: stats.success_rate,
            averageProcessingTime: stats.average_processing_time
        };
    }

    async batchCreateAssessments(requests: any[]): Promise<string[]> {
        const assessmentIds: string[] = [];

        for (const request of requests) {
            try {
                const id = await this.createAssessment(request);
                assessmentIds.push(id);
            } catch (error) {
                // Skip invalid requests
                console.warn('Skipping invalid assessment request:', error);
            }
        }

        return assessmentIds;
    }

    async batchRetryFailedAssessments(maxRetries: number): Promise<string[]> {
        const failed = await this.database.getFailedAssessments();
        const retriedIds: string[] = [];

        for (const assessment of failed) {
            if (assessment.retry_count < maxRetries) {
                await this.database.updateAssessment(assessment.assessment_id, {
                    state: 'pending',
                    retry_count: assessment.retry_count + 1,
                    updated_at: new Date()
                });
                retriedIds.push(assessment.assessment_id);
            }
        }

        return retriedIds;
    }

    async cleanupOldAssessments(retentionDays: number): Promise<any> {
        const result = await this.database.cleanupOldAssessments(retentionDays);
        return {
            deleted: result.deleted,
            remaining: result.remaining
        };
    }

    async getHealthStatus(): Promise<any> {
        const dbHealth = await this.database.healthCheck();
        const complianceHealth = await this.complianceServer.healthCheck();

        return {
            overall: dbHealth.connected && complianceHealth.healthy ? 'healthy' : 'degraded',
            services: {
                database: {
                    status: dbHealth.connected ? 'healthy' : 'unhealthy',
                    activeConnections: dbHealth.active_connections,
                    totalConnections: dbHealth.total_connections,
                    successRate: dbHealth.success_rate
                },
                compliance: {
                    status: complianceHealth.healthy ? 'healthy' : 'unhealthy',
                    activeRequests: complianceHealth.active_requests,
                    totalRequests: complianceHealth.total_requests,
                    successRate: complianceHealth.success_rate
                }
            }
        };
    }

    // Private properties
    private database: any;
    private complianceServer: any;
    private logger: any;
}

// Test suite
describe('AssessmentStore', () => {
    let assessmentStore: TestAssessmentStore;

    beforeAll(async () => {
        await setupTestEnvironment();
        assessmentStore = new TestAssessmentStore();
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

    describe('Constructor and Initialization', () => {
        it('should create AssessmentStore instance with correct configuration', () => {
            expect(assessmentStore).toBeDefined();
            expect(assessmentStore).toBeInstanceOf(TestAssessmentStore);
        });

        it('should initialize with default configuration', () => {
            const store = new TestAssessmentStore();
            expect(store).toBeDefined();
        });

        it('should handle database connection failure gracefully', async () => {
            // Simulate database connection failure
            await mockDatabaseService.simulateOverload();

            const store = new TestAssessmentStore();
            await expect(store.getHealthStatus()).rejects.toThrow();
        });
    });

    describe('Core Assessment Operations', () => {
        describe('createAssessment', () => {
            it('should create a new assessment successfully', async () => {
                const request = generateTestAssessmentData();

                const assessmentId = await assessmentStore.createAssessment(request);

                expect(assessmentId).toBeDefined();
                expect(typeof assessmentId).toBe('string');

                // Verify assessment was created in database
                const assessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(assessment).toBeDefined();
                expect(assessment!.state).toBe('pending');
                expect(assessment!.request_data).toEqual(request);
            });

            it('should validate assessment request data', async () => {
                const invalidRequest = { ...generateTestAssessmentData() };
                delete invalidRequest.assessment_id;

                await expect(assessmentStore.createAssessment(invalidRequest))
                    .rejects.toThrow('Invalid assessment request');
            });

            it('should handle database connection errors', async () => {
                // Simulate database failure
                await mockDatabaseService.simulateOverload();

                const request = generateTestAssessmentData();
                await expect(assessmentStore.createAssessment(request))
                    .rejects.toThrow('Database connection failed');
            });

            it('should handle concurrent assessment creation', async () => {
                const requests = createBatchTestAssessments(10);

                const promises = requests.map(request =>
                    assessmentStore.createAssessment(request)
                );

                const assessmentIds = await Promise.all(promises);

                expect(assessmentIds).toHaveLength(10);
                expect(new Set(assessmentIds).size).toBe(10); // All IDs should be unique

                // Verify all assessments were created
                const assessments = await mockDatabaseService.getAllAssessments();
                expect(assessments).toHaveLength(13); // 3 initial + 10 new
            });

            it('should generate unique assessment IDs', async () => {
                const request1 = generateTestAssessmentData();
                const request2 = generateTestAssessmentData();

                const id1 = await assessmentStore.createAssessment(request1);
                const id2 = await assessmentStore.createAssessment(request2);

                expect(id1).not.toBe(id2);
            });

            it('should set default values for optional fields', async () => {
                const request = generateTestAssessmentData({
                    priority: undefined,
                    timeout: undefined
                });

                const assessmentId = await assessmentStore.createAssessment(request);
                const assessment = await mockDatabaseService.getAssessment(assessmentId);

                expect(assessment!.priority).toBe(5); // Default priority
                expect(assessment!.timeout_seconds).toBe(300); // Default timeout
            });
        });

        describe('getState', () => {
            it('should get existing assessment state', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await assessmentStore.createAssessment(request);

                const state = await assessmentStore.getState(assessmentId);

                expect(state).toBeDefined();
                expect(state.assessmentId).toBe(assessmentId);
                expect(state.state).toBe('pending');
                expect(state.progress).toBe(0);
            });

            it('should throw error for non-existent assessment', async () => {
                await expect(assessmentStore.getState('non-existent-id'))
                    .rejects.toThrow('Assessment not found');
            });

            it('should handle database query errors', async () => {
                // Simulate database failure
                await mockDatabaseService.simulateOverload();

                const request = generateTestAssessmentData();
                const assessmentId = await assessmentStore.createAssessment(request);

                await expect(assessmentStore.getState(assessmentId))
                    .rejects.toThrow('Database query failed');
            });

            it('should return complete assessment data', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await assessmentStore.createAssessment(request);

                // Update assessment to processing state
                await mockDatabaseService.updateAssessment(assessmentId, {
                    state: 'processing',
                    progress: 50
                });

                const state = await assessmentStore.getState(assessmentId);

                expect(state.assessmentId).toBe(assessmentId);
                expect(state.state).toBe('processing');
                expect(state.progress).toBe(50);
                expect(state.requestData).toEqual(request);
                expect(state.version).toBe(2);
            });
        });

        describe('waitForCompletion', () => {
            it('should wait for assessment completion', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await assessmentStore.createAssessment(request);

                // Start a promise to complete the assessment
                const completionPromise = (async () => {
                    await new Promise(resolve => setTimeout(resolve, 100));
                    await mockDatabaseService.updateAssessment(assessmentId, {
                        state: 'completed',
                        progress: 100,
                        result_data: generateTestResultData(assessmentId)
                    });
                })();

                const state = await assessmentStore.waitForCompletion(assessmentId, 5000);

                expect(state.state).toBe('completed');
                expect(state.progress).toBe(100);

                await completionPromise;
            });

            it('should timeout for assessments that never complete', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await assessmentStore.createAssessment(request);

                await expect(assessmentStore.waitForCompletion(assessmentId, 100))
                    .rejects.toThrow('Assessment timeout');
            });

            it('should return immediately if assessment is already completed', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await assessmentStore.createAssessment(request);

                // Complete assessment immediately
                await mockDatabaseService.updateAssessment(assessmentId, {
                    state: 'completed',
                    progress: 100,
                    result_data: generateTestResultData(assessmentId)
                });

                const startTime = Date.now();
                const state = await assessmentStore.waitForCompletion(assessmentId, 5000);
                const endTime = Date.now();

                expect(state.state).toBe('completed');
                expect(endTime - startTime).toBeLessThan(100); // Should return immediately
            });

            it('should handle assessment failures during wait', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await assessmentStore.createAssessment(request);

                // Start a promise to fail the assessment
                const failurePromise = (async () => {
                    await new Promise(resolve => setTimeout(resolve, 100));
                    await mockDatabaseService.updateAssessment(assessmentId, {
                        state: 'failed',
                        error_message: 'Processing failed'
                    });
                })();

                const state = await assessmentStore.waitForCompletion(assessmentId, 5000);

                expect(state.state).toBe('failed');
                expect(state.errorMessage).toBe('Processing failed');

                await failurePromise;
            });
        });

        describe('updateProgress', () => {
            it('should update assessment progress successfully', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await assessmentStore.createAssessment(request);

                await assessmentStore.updateProgress(assessmentId, 50, 'Halfway done');

                const assessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(assessment!.progress).toBe(50);
                expect(assessment!.updated_at.getTime()).toBeGreaterThan(
                    assessment!.created_at.getTime()
                );
            });

            it('should validate progress range', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await assessmentStore.createAssessment(request);

                await expect(assessmentStore.updateProgress(assessmentId, -1))
                    .rejects.toThrow('Progress must be between 0 and 100');

                await expect(assessmentStore.updateProgress(assessmentId, 101))
                    .rejects.toThrow('Progress must be between 0 and 100');
            });

            it('should handle concurrent progress updates', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await assessmentStore.createAssessment(request);

                // Update progress concurrently
                const promises = [
                    assessmentStore.updateProgress(assessmentId, 25, '25%'),
                    assessmentStore.updateProgress(assessmentId, 50, '50%'),
                    assessmentStore.updateProgress(assessmentId, 75, '75%'),
                    assessmentStore.updateProgress(assessmentId, 100, '100%')
                ];

                await Promise.all(promises);

                const assessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(assessment!.progress).toBe(100); // Should end at 100
                expect(assessment!.version).toBeGreaterThan(1);
            });

            it('should throw error for non-existent assessment', async () => {
                await expect(assessmentStore.updateProgress('non-existent-id', 50))
                    .rejects.toThrow('Assessment not found');
            });
        });

        describe('completeAssessment', () => {
            it('should complete assessment successfully', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await assessmentStore.createAssessment(request);

                // Set to processing first
                await mockDatabaseService.updateAssessment(assessmentId, {
                    state: 'processing'
                });

                const result = generateTestResultData(assessmentId);
                await assessmentStore.completeAssessment(assessmentId, result);

                const assessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(assessment!.state).toBe('completed');
                expect(assessment!.progress).toBe(100);
                expect(assessment!.result_data).toEqual(result);
                expect(assessment!.completed_at).toBeDefined();
            });

            it('should validate assessment state before completion', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await assessmentStore.createAssessment(request);

                // Try to complete assessment that is still pending
                const result = generateTestResultData(assessmentId);
                await expect(assessmentStore.completeAssessment(assessmentId, result))
                    .rejects.toThrow('Cannot complete assessment in pending state');
            });

            it('should handle concurrent completion attempts', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await assessmentStore.createAssessment(request);

                // Set to processing first
                await mockDatabaseService.updateAssessment(assessmentId, {
                    state: 'processing'
                });

                const result = generateTestResultData(assessmentId);

                // Try to complete concurrently
                const promises = [
                    assessmentStore.completeAssessment(assessmentId, result),
                    assessmentStore.completeAssessment(assessmentId, result)
                ];

                const results = await Promise.allSettled(promises);

                // One should succeed, one should fail
                const successCount = results.filter(r => r.status === 'fulfilled').length;
                const failureCount = results.filter(r => r.status === 'rejected').length;

                expect(successCount).toBe(1);
                expect(failureCount).toBe(1);

                // Verify assessment is completed
                const assessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(assessment!.state).toBe('completed');
            });
        });

        describe('failAssessment', () => {
            it('should fail assessment successfully', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await assessmentStore.createAssessment(request);

                // Set to processing first
                await mockDatabaseService.updateAssessment(assessmentId, {
                    state: 'processing'
                });

                const errorMessage = 'Processing failed due to timeout';
                await assessmentStore.failAssessment(assessmentId, errorMessage);

                const assessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(assessment!.state).toBe('failed');
                expect(assessment!.error_message).toBe(errorMessage);
                expect(assessment!.completed_at).toBeDefined();
            });

            it('should validate assessment state before failure', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await assessmentStore.createAssessment(request);

                // Try to fail assessment that is still pending
                await expect(assessmentStore.failAssessment(assessmentId, 'Test error'))
                    .rejects.toThrow('Cannot fail assessment in pending state');
            });

            it('should handle concurrent failure attempts', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await assessmentStore.createAssessment(request);

                // Set to processing first
                await mockDatabaseService.updateAssessment(assessmentId, {
                    state: 'processing'
                });

                const errorMessage = 'Processing failed';

                // Try to fail concurrently
                const promises = [
                    assessmentStore.failAssessment(assessmentId, errorMessage),
                    assessmentStore.failAssessment(assessmentId, errorMessage)
                ];

                const results = await Promise.allSettled(promises);

                // One should succeed, one should fail
                const successCount = results.filter(r => r.status === 'fulfilled').length;
                const failureCount = results.filter(r => r.status === 'rejected').length;

                expect(successCount).toBe(1);
                expect(failureCount).toBe(1);

                // Verify assessment is failed
                const assessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(assessment!.state).toBe('failed');
            });
        });

        describe('cancelAssessment', () => {
            it('should cancel assessment successfully', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await assessmentStore.createAssessment(request);

                const cancelReason = 'User requested cancellation';
                await assessmentStore.cancelAssessment(assessmentId, cancelReason);

                const assessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(assessment!.state).toBe('cancelled');
                expect(assessment!.completed_at).toBeDefined();
            });

            it('should cancel processing assessment', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await assessmentStore.createAssessment(request);

                // Set to processing first
                await mockDatabaseService.updateAssessment(assessmentId, {
                    state: 'processing'
                });

                await assessmentStore.cancelAssessment(assessmentId, 'User requested cancellation');

                const assessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(assessment!.state).toBe('cancelled');
            });

            it('should prevent cancellation of completed assessments', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await assessmentStore.createAssessment(request);

                // Complete assessment first
                await mockDatabaseService.updateAssessment(assessmentId, {
                    state: 'completed',
                    progress: 100
                });

                await expect(assessmentStore.cancelAssessment(assessmentId, 'Test cancellation'))
                    .rejects.toThrow('Cannot cancel completed assessment');
            });
        });
    });

    describe('Query Operations', () => {
        describe('listAssessments', () => {
            beforeEach(async () => {
                // Create test assessments
                const assessments = createBatchTestAssessments(20);
                for (const assessment of assessments) {
                    await assessmentStore.createAssessment(assessment);
                }
            });

            it('should list all assessments', async () => {
                const result = await assessmentStore.listAssessments();

                expect(result.assessments).toBeDefined();
                expect(result.total).toBeGreaterThan(0);
                expect(result.assessments.length).toBeLessThanOrEqual(result.total);
            });

            it('should filter assessments by state', async () => {
                const result = await assessmentStore.listAssessments({
                    state: ['completed']
                });

                expect(result.assessments.every(a => a.state === 'completed')).toBe(true);
            });

            it('should support pagination', async () => {
                const page1 = await assessmentStore.listAssessments({
                    limit: 5,
                    offset: 0
                });

                const page2 = await assessmentStore.listAssessments({
                    limit: 5,
                    offset: 5
                });

                expect(page1.assessments).toHaveLength(5);
                expect(page2.assessments).toHaveLength(5);
                expect(page1.assessments[0].assessment_id).not.toBe(page2.assessments[0].assessment_id);
            });

            it('should sort assessments by creation date', async () => {
                const result = await assessmentStore.listAssessments({
                    sortBy: 'created_at',
                    sortOrder: 'desc'
                });

                for (let i = 0; i < result.assessments.length - 1; i++) {
                    const current = new Date(result.assessments[i].created_at);
                    const next = new Date(result.assessments[i + 1].created_at);
                    expect(current.getTime()).toBeGreaterThanOrEqual(next.getTime());
                }
            });

            it('should handle empty results', async () => {
                const result = await assessmentStore.listAssessments({
                    state: ['non_existent_state']
                });

                expect(result.assessments).toHaveLength(0);
                expect(result.total).toBe(0);
            });
        });

        describe('getAssessmentStats', () => {
            beforeEach(async () => {
                // Create test assessments with different states
                const assessments = createBatchTestAssessments(10, ['pending', 'processing', 'completed', 'failed']);
                for (const assessment of assessments) {
                    await assessmentStore.createAssessment(assessment);
                }
            });

            it('should return assessment statistics', async () => {
                const stats = await assessmentStore.getAssessmentStats();

                expect(stats).toBeDefined();
                expect(stats.total).toBeGreaterThan(0);
                expect(stats.by_state).toBeDefined();
                expect(stats.by_priority).toBeDefined();
                expect(stats.success_rate).toBeGreaterThanOrEqual(0);
                expect(stats.success_rate).toBeLessThanOrEqual(1);
            });

            it('should calculate success rate correctly', async () => {
                const stats = await assessmentStore.getAssessmentStats();

                const completedCount = stats.by_state['completed'] || 0;
                const totalCount = stats.total;
                const expectedSuccessRate = totalCount > 0 ? completedCount / totalCount : 0;

                expect(stats.success_rate).toBeCloseTo(expectedSuccessRate, 2);
            });
        });
    });

    describe('Batch Operations', () => {
        describe('batchCreateAssessments', () => {
            it('should create multiple assessments', async () => {
                const requests = createBatchTestAssessments(5);

                const assessmentIds = await assessmentStore.batchCreateAssessments(requests);

                expect(assessmentIds).toHaveLength(5);
                expect(new Set(assessmentIds).size).toBe(5); // All IDs should be unique

                // Verify all assessments were created
                const assessments = await mockDatabaseService.getAllAssessments();
                expect(assessments.length).toBeGreaterThan(5);
            });

            it('should handle partial batch creation failures', async () => {
                const requests = [
                    generateTestAssessmentData(),
                    { ...generateTestAssessmentData(), assessment_id: '' }, // Invalid
                    generateTestAssessmentData()
                ];

                const assessmentIds = await assessmentStore.batchCreateAssessments(requests);

                expect(assessmentIds).toHaveLength(2); // Only valid ones should be created
            });

            it('should create assessments efficiently', async () => {
                const requests = createBatchTestAssessments(20);

                const startTime = Date.now();
                const assessmentIds = await assessmentStore.batchCreateAssessments(requests);
                const endTime = Date.now();

                expect(assessmentIds).toHaveLength(20);
                expect(endTime - startTime).toBeLessThan(5000); // Should complete quickly
            });
        });

        describe('batchRetryFailedAssessments', () => {
            beforeEach(async () => {
                // Create some failed assessments
                const failedAssessments = createBatchTestAssessments(3, ['failed']);
                for (const assessment of failedAssessments) {
                    await assessmentStore.createAssessment(assessment);
                }
            });

            it('should retry failed assessments', async () => {
                const retriedIds = await assessmentStore.batchRetryFailedAssessments(3);

                expect(retriedIds).toHaveLength(3);

                // Verify assessments were reset to pending
                for (const assessmentId of retriedIds) {
                    const assessment = await mockDatabaseService.getAssessment(assessmentId);
                    expect(assessment!.state).toBe('pending');
                    expect(assessment!.retry_count).toBeGreaterThan(0);
                }
            });

            it('should respect retry limits', async () => {
                // Create assessments with different retry counts
                const requests = [
                    generateTestAssessmentData(),
                    generateTestAssessmentData(),
                    generateTestAssessmentData()
                ];

                const assessmentIds = await assessmentStore.batchCreateAssessments(requests);

                // Set different retry counts
                await mockDatabaseService.updateAssessment(assessmentIds[0], {
                    state: 'failed',
                    retry_count: 5
                });

                await mockDatabaseService.updateAssessment(assessmentIds[1], {
                    state: 'failed',
                    retry_count: 2
                });

                await mockDatabaseService.updateAssessment(assessmentIds[2], {
                    state: 'failed',
                    retry_count: 1
                });

                const retriedIds = await assessmentStore.batchRetryFailedAssessments(3);

                // Only assessments with retry_count < 3 should be retried
                expect(retriedIds).toHaveLength(2);
                expect(retriedIds).not.toContain(assessmentIds[0]); // retry_count = 5 > 3
            });
        });
    });

    describe('Maintenance Operations', () => {
        describe('cleanupOldAssessments', () => {
            beforeEach(async () => {
                // Create old assessments
                const oldAssessments = createBatchTestAssessments(5, ['completed']);
                for (const assessment of oldAssessments) {
                    await assessmentStore.createAssessment(assessment);
                }

                // Update some to be old
                const allAssessments = await mockDatabaseService.getAllAssessments();
                for (const assessment of allAssessments) {
                    if (assessment.state === 'completed') {
                        assessment.completed_at = new Date(Date.now() - 35 * 24 * 60 * 60 * 1000); // 35 days ago
                    }
                }
            });

            it('should cleanup old assessments', async () => {
                const initialCount = await mockDatabaseService.getAssessmentCount();
                const result = await assessmentStore.cleanupOldAssessments(30);

                expect(result.deleted).toBeGreaterThan(0);
                expect(result.remaining).toBeLessThan(initialCount);
            });

            it('should respect retention period', async () => {
                const result = await assessmentStore.cleanupOldAssessments(10);

                // Should not delete recent assessments
                expect(result.deleted).toBe(0);
            });

            it('should handle cleanup errors gracefully', async () => {
                // Simulate database failure
                await mockDatabaseService.simulateOverload();

                await expect(assessmentStore.cleanupOldAssessments(30))
                    .rejects.toThrow('Database connection failed');
            });
        });

        describe('getHealthStatus', () => {
            it('should return health status', async () => {
                const health = await assessmentStore.getHealthStatus();

                expect(health).toBeDefined();
                expect(health.overall).toBeDefined();
                expect(health.services).toBeDefined();
                expect(health.services.database).toBeDefined();
                expect(health.services.cache).toBeDefined();
                expect(health.services.queue).toBeDefined();
            });

            it('should detect unhealthy services', async () => {
                // Simulate database failure
                await mockDatabaseService.simulateOverload();

                const health = await assessmentStore.getHealthStatus();

                expect(health.overall).not.toBe('healthy');
                expect(health.services.database.status).not.toBe('healthy');
            });
        });
    });

    describe('Error Handling', () => {
        it('should handle database connection errors gracefully', async () => {
            await mockDatabaseService.simulateOverload();

            const request = generateTestAssessmentData();
            await expect(assessmentStore.createAssessment(request))
                .rejects.toThrow();
        });

        it('should handle compliance server timeouts', async () => {
            mockComplianceServer.setTimeoutRate(1);

            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);

            await expect(assessmentStore.waitForCompletion(assessmentId, 1000))
                .rejects.toThrow('Compliance server timeout');
        });

        it('should handle concurrent modification conflicts', async () => {
            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);

            // Simulate concurrent modification
            await mockDatabaseService.updateAssessment(assessmentId, {
                state: 'processing',
                version: 2
            });

            // Try to update with old version
            await expect(assessmentStore.updateProgress(assessmentId, 50, 'Test'))
                .rejects.toThrow('Optimistic lock failed');
        });

        it('should handle invalid state transitions', async () => {
            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);

            // Try to transition from pending to completed (invalid)
            await expect(assessmentStore.completeAssessment(assessmentId, generateTestResultData(assessmentId)))
                .rejects.toThrow('Cannot complete assessment in pending state');
        });
    });

    describe('Performance Tests', () => {
        it('should handle high-frequency assessment creation', async () => {
            const requests = createBatchTestAssessments(100);

            const performance = await measurePerformance(
                'batch-create-100',
                async () => {
                    return await assessmentStore.batchCreateAssessments(requests);
                },
                5
            );

            expect(performance.averageTime).toBeLessThan(5000);
            expect(performance.results.every(r => r.success)).toBe(true);
        });

        it('should handle concurrent state updates', async () => {
            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);

            const performance = await measurePerformance(
                'concurrent-updates',
                async () => {
                    const promises = Array.from({ length: 10 }, (_, i) =>
                        assessmentStore.updateProgress(assessmentId, i * 10, `Update ${i}`)
                    );
                    return await Promise.all(promises);
                },
                10
            );

            expect(performance.averageTime).toBeLessThan(2000);
        });

        it('should handle query performance under load', async () => {
            // Create many assessments
            const requests = createBatchTestAssessments(500);
            await assessmentStore.batchCreateAssessments(requests);

            const performance = await measurePerformance(
                'list-assessments',
                async () => {
                    return await assessmentStore.listAssessments({
                        limit: 100,
                        offset: 0
                    });
                },
                20
            );

            expect(performance.averageTime).toBeLessThan(1000);
        });
    });

    describe('Edge Cases', () => {
        it('should handle assessment ID collisions', async () => {
            const request1 = generateTestAssessmentData();
            const request2 = { ...generateTestAssessmentData(), assessment_id: request1.assessment_id };

            // First should succeed
            const id1 = await assessmentStore.createAssessment(request1);
            expect(id1).toBeDefined();

            // Second should fail or generate different ID
            await expect(assessmentStore.createAssessment(request2))
                .rejects.toThrow();
        });

        it('should handle very long assessment processing times', async () => {
            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);

            // Set to processing
            await mockDatabaseService.updateAssessment(assessmentId, {
                state: 'processing'
            });

            // Wait with long timeout
            const startTime = Date.now();
            const state = await assessmentStore.waitForCompletion(assessmentId, 10000);
            const endTime = Date.now();

            expect(endTime - startTime).toBeLessThan(10000);
            expect(state.state).toBe('processing'); // Should still be processing
        });

        it('should handle memory pressure gracefully', async () => {
            // Create many assessments to test memory usage
            const requests = createBatchTestAssessments(1000);
            const assessmentIds = await assessmentStore.batchCreateAssessments(requests);

            // Verify all were created
            expect(assessmentIds).toHaveLength(1000);

            // Clean up
            await assessmentStore.cleanupOldAssessments(0);
        });

        it('should handle network partition scenarios', async () => {
            mockComplianceServer.simulateNetworkPartition(2000);

            const request = generateTestAssessmentData();
            const assessmentId = await assessmentStore.createAssessment(request);

            // Should still be able to query local state
            const state = await assessmentStore.getState(assessmentId);
            expect(state).toBeDefined();

            // But compliance operations should fail
            await expect(assessmentStore.waitForCompletion(assessmentId, 3000))
                .rejects.toThrow();
        });
    });
});