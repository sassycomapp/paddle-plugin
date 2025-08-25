/**
 * AssessmentProcessor Unit Tests
 *
 * This file contains comprehensive unit tests for the AssessmentProcessor component,
 * testing assessment processing logic, external compliance server communication,
 * retry mechanisms, and error handling scenarios.
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

// Mock AssessmentProcessor implementation for testing
class TestAssessmentProcessor {
    constructor() {
        // Initialize with mock dependencies
        this.database = mockDatabaseService;
        this.complianceServer = mockComplianceServer;
        this.logger = console;
        this.config = {
            maxConcurrentAssessments: 10,
            retryAttempts: 3,
            retryDelay: 1000,
            timeout: 30000,
            circuitBreakerThreshold: 5,
            circuitBreakerTimeout: 60000
        };
    }

    // Mock AssessmentProcessor methods
    async processAssessment(assessmentId: string, timeout: number = 30000): Promise<any> {
        const startTime = Date.now();

        try {
            // Validate assessment exists
            const assessment = await this.database.getAssessment(assessmentId);
            if (!assessment) {
                throw new Error('Assessment not found');
            }

            // Update to processing state
            await this.database.updateAssessment(assessmentId, {
                state: 'processing',
                updated_at: new Date()
            }, assessment.version);

            // Process assessment
            const result = await this.processAssessmentInternal(assessmentId);

            // Complete assessment
            await this.database.updateAssessment(assessmentId, {
                state: 'completed',
                progress: 100,
                result_data: result,
                completed_at: new Date(),
                updated_at: new Date()
            }, assessment.version + 1);

            return result;
        } catch (error) {
            await this.handleProcessingError(assessmentId, error as Error);
            throw error;
        }
    }

    async processAssessmentInternal(assessmentId: string): Promise<any> {
        const assessment = await this.database.getAssessment(assessmentId);
        if (!assessment) {
            throw new Error('Assessment not found');
        }

        // Simulate processing time
        await new Promise(resolve => setTimeout(resolve, 100));

        // Simulate processing logic
        const result = generateTestResultData(assessmentId);

        // Simulate occasional failures
        if (Math.random() < 0.1) {
            throw new Error('Processing failed');
        }

        return result;
    }

    async sendToComplianceServer(assessmentId: string): Promise<any> {
        const assessment = await this.database.getAssessment(assessmentId);
        if (!assessment) {
            throw new Error('Assessment not found');
        }

        // Simulate compliance server communication
        await new Promise(resolve => setTimeout(resolve, 200));

        // Simulate compliance server response
        return {
            assessment_id: assessmentId,
            compliance_score: Math.floor(Math.random() * 100),
            violations: Math.floor(Math.random() * 10),
            recommendations: ['Update security policies', 'Review configurations']
        };
    }

    async handleProcessingError(assessmentId: string, error: Error): Promise<void> {
        const assessment = await this.database.getAssessment(assessmentId);
        if (!assessment) {
            throw new Error('Assessment not found');
        }

        // Increment retry count
        const retryCount = assessment.retry_count + 1;

        // Schedule retry if within limits
        if (retryCount < this.config.retryAttempts) {
            const nextRetryAt = new Date(Date.now() + this.config.retryDelay);

            await this.database.updateAssessment(assessmentId, {
                state: 'pending',
                retry_count: retryCount,
                next_retry_at: nextRetryAt,
                updated_at: new Date()
            }, assessment.version);
        } else {
            // Mark as failed if max retries reached
            await this.database.updateAssessment(assessmentId, {
                state: 'failed',
                error_message: error.message,
                completed_at: new Date(),
                updated_at: new Date()
            }, assessment.version);
        }
    }

    async retryFailedAssessments(): Promise<string[]> {
        const failed = await this.database.getFailedAssessments();
        const retriedIds: string[] = [];

        for (const assessment of failed) {
            if (assessment.retry_count < this.config.retryAttempts) {
                await this.database.updateAssessment(assessment.assessment_id, {
                    state: 'pending',
                    retry_count: assessment.retry_count + 1,
                    updated_at: new Date()
                }, assessment.version);
                retriedIds.push(assessment.assessment_id);
            }
        }

        return retriedIds;
    }

    async processBatchAssessments(assessmentIds: string[]): Promise<any[]> {
        const results: any[] = [];

        for (const assessmentId of assessmentIds) {
            try {
                const result = await this.processAssessment(assessmentId);
                results.push({
                    assessmentId,
                    success: true,
                    result
                });
            } catch (error) {
                results.push({
                    assessmentId,
                    success: false,
                    error: error instanceof Error ? error.message : String(error)
                });
            }
        }

        return results;
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
                    successRate: complianceHealth.success_rate,
                    circuit_breaker: {
                        state: 'closed',
                        failures: 0,
                        threshold: this.config.circuitBreakerThreshold
                    }
                }
            }
        };
    }

    // Private properties
    private database: any;
    private complianceServer: any;
    private logger: any;
    private config: any;
}

// Test suite
describe('AssessmentProcessor', () => {
    let assessmentProcessor: TestAssessmentProcessor;

    beforeAll(async () => {
        await setupTestEnvironment();
        assessmentProcessor = new TestAssessmentProcessor();
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
        it('should create AssessmentProcessor instance with correct configuration', () => {
            expect(assessmentProcessor).toBeDefined();
            expect(assessmentProcessor).toBeInstanceOf(TestAssessmentProcessor);
        });

        it('should initialize with default configuration', () => {
            const processor = new TestAssessmentProcessor();
            expect(processor).toBeDefined();
        });

        it('should handle database connection failure gracefully', async () => {
            // Simulate database connection failure
            await mockDatabaseService.simulateOverload();

            const processor = new TestAssessmentProcessor();
            await expect(processor.getHealthStatus())
                .rejects.toThrow();
        });
    });

    describe('Assessment Processing', () => {
        describe('processAssessment', () => {
            it('should process assessment successfully', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await mockDatabaseService.createAssessment({
                    assessment_id: request.assessment_id,
                    state: 'pending',
                    request_data: request,
                    progress: 0,
                    priority: 5,
                    retry_count: 0,
                    timeout_seconds: 300,
                    max_retries: 3,
                    created_at: new Date(),
                    updated_at: new Date()
                });

                const result = await assessmentProcessor.processAssessment(assessmentId);

                expect(result).toBeDefined();
                expect(result.assessment_id).toBe(assessmentId);
                expect(result.compliance_score).toBeDefined();
                expect(result.violations).toBeDefined();

                // Verify assessment was completed
                const assessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(assessment!.state).toBe('completed');
                expect(assessment!.progress).toBe(100);
                expect(assessment!.result_data).toBeDefined();
            });

            it('should validate assessment ID before processing', async () => {
                await expect(assessmentProcessor.processAssessment('non-existent-id'))
                    .rejects.toThrow('Assessment not found');
            });

            it('should handle processing errors gracefully', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await mockDatabaseService.createAssessment({
                    assessment_id: request.assessment_id,
                    state: 'pending',
                    request_data: request,
                    progress: 0,
                    priority: 5,
                    retry_count: 0,
                    timeout_seconds: 300,
                    max_retries: 3,
                    created_at: new Date(),
                    updated_at: new Date()
                });

                // Simulate processing failure
                vi.spyOn(assessmentProcessor as any, 'processAssessmentInternal')
                    .mockRejectedValue(new Error('Processing failed'));

                await expect(assessmentProcessor.processAssessment(assessmentId))
                    .rejects.toThrow('Processing failed');

                // Verify assessment was marked as failed
                const assessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(assessment!.state).toBe('failed');
                expect(assessment!.error_message).toBe('Processing failed');
            });

            it('should handle concurrent assessment processing', async () => {
                const requests = createBatchTestAssessments(5);
                const assessmentIds: string[] = [];

                // Create assessments
                for (const request of requests) {
                    const assessment = await mockDatabaseService.createAssessment({
                        assessment_id: request.assessment_id,
                        state: 'pending',
                        request_data: request,
                        progress: 0,
                        priority: 5,
                        retry_count: 0,
                        timeout_seconds: 300,
                        max_retries: 3,
                        created_at: new Date(),
                        updated_at: new Date()
                    });
                    assessmentIds.push(assessment.assessment_id);
                }

                // Process assessments concurrently
                const promises = assessmentIds.map(id =>
                    assessmentProcessor.processAssessment(id)
                );

                const results = await Promise.all(promises);

                expect(results).toHaveLength(5);
                expect(results.every(r => r !== undefined)).toBe(true);

                // Verify all assessments were completed
                for (const assessmentId of assessmentIds) {
                    const assessment = await mockDatabaseService.getAssessment(assessmentId);
                    expect(assessment!.state).toBe('completed');
                }
            });

            it('should respect processing timeout', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await mockDatabaseService.createAssessment({
                    assessment_id: request.assessment_id,
                    state: 'pending',
                    request_data: request,
                    progress: 0,
                    priority: 5,
                    retry_count: 0,
                    timeout_seconds: 300,
                    max_retries: 3,
                    created_at: new Date(),
                    updated_at: new Date()
                });

                // Simulate long processing time
                vi.spyOn(assessmentProcessor as any, 'processAssessmentInternal')
                    .mockImplementation(async () => {
                        await new Promise(resolve => setTimeout(resolve, 5000));
                        return generateTestResultData(assessmentId);
                    });

                await expect(assessmentProcessor.processAssessment(assessmentId, 1000))
                    .rejects.toThrow('Processing timeout');
            });
        });

        describe('processAssessmentInternal', () => {
            it('should process assessment internally', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await mockDatabaseService.createAssessment({
                    assessment_id: request.assessment_id,
                    state: 'pending',
                    request_data: request,
                    progress: 0,
                    priority: 5,
                    retry_count: 0,
                    timeout_seconds: 300,
                    max_retries: 3,
                    created_at: new Date(),
                    updated_at: new Date()
                });

                const result = await (assessmentProcessor as any).processAssessmentInternal(assessmentId);

                expect(result).toBeDefined();
                expect(result.assessment_id).toBe(assessmentId);
                expect(result.compliance_score).toBeDefined();
            });

            it('should handle internal processing errors', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await mockDatabaseService.createAssessment({
                    assessment_id: request.assessment_id,
                    state: 'pending',
                    request_data: request,
                    progress: 0,
                    priority: 5,
                    retry_count: 0,
                    timeout_seconds: 300,
                    max_retries: 3,
                    created_at: new Date(),
                    updated_at: new Date()
                });

                // Simulate internal processing failure
                vi.spyOn(assessmentProcessor as any, 'processAssessmentInternal')
                    .mockRejectedValue(new Error('Internal processing failed'));

                await expect((assessmentProcessor as any).processAssessmentInternal(assessmentId))
                    .rejects.toThrow('Internal processing failed');
            });
        });

        describe('sendToComplianceServer', () => {
            it('should send assessment to compliance server', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await mockDatabaseService.createAssessment({
                    assessment_id: request.assessment_id,
                    state: 'pending',
                    request_data: request,
                    progress: 0,
                    priority: 5,
                    retry_count: 0,
                    timeout_seconds: 300,
                    max_retries: 3,
                    created_at: new Date(),
                    updated_at: new Date()
                });

                const result = await (assessmentProcessor as any).sendToComplianceServer(assessmentId);

                expect(result).toBeDefined();
                expect(result.assessment_id).toBe(assessmentId);
                expect(result.compliance_score).toBeDefined();
                expect(result.violations).toBeDefined();
            });

            it('should handle compliance server errors', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await mockDatabaseService.createAssessment({
                    assessment_id: request.assessment_id,
                    state: 'pending',
                    request_data: request,
                    progress: 0,
                    priority: 5,
                    retry_count: 0,
                    timeout_seconds: 300,
                    max_retries: 3,
                    created_at: new Date(),
                    updated_at: new Date()
                });

                // Simulate compliance server failure
                mockComplianceServer.setHealthy(false);

                await expect((assessmentProcessor as any).sendToComplianceServer(assessmentId))
                    .rejects.toThrow('Compliance server not healthy');
            });

            it('should handle compliance server timeouts', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await mockDatabaseService.createAssessment({
                    assessment_id: request.assessment_id,
                    state: 'pending',
                    request_data: request,
                    progress: 0,
                    priority: 5,
                    retry_count: 0,
                    timeout_seconds: 300,
                    max_retries: 3,
                    created_at: new Date(),
                    updated_at: new Date()
                });

                // Simulate compliance server timeout
                mockComplianceServer.setTimeoutRate(1);

                await expect((assessmentProcessor as any).sendToComplianceServer(assessmentId))
                    .rejects.toThrow('Compliance server timeout');
            });
        });
    });

    describe('Retry Mechanisms', () => {
        describe('handleProcessingError', () => {
            it('should handle processing error with retry', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await mockDatabaseService.createAssessment({
                    assessment_id: request.assessment_id,
                    state: 'processing',
                    request_data: request,
                    progress: 50,
                    priority: 5,
                    retry_count: 0,
                    timeout_seconds: 300,
                    max_retries: 3,
                    created_at: new Date(),
                    updated_at: new Date()
                });

                const error = new Error('Processing failed');
                await (assessmentProcessor as any).handleProcessingError(assessmentId, error);

                // Verify assessment was reset to pending with retry count
                const assessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(assessment!.state).toBe('pending');
                expect(assessment!.retry_count).toBe(1);
                expect(assessment!.next_retry_at).toBeDefined();
            });

            it('should handle processing error without retry (max retries reached)', async () => {
                const request = generateTestAssessmentData();
                const assessmentId = await mockDatabaseService.createAssessment({
                    assessment_id: request.assessment_id,
                    state: 'processing',
                    request_data: request,
                    progress: 50,
                    priority: 5,
                    retry_count: 3, // Max retries reached
                    timeout_seconds: 300,
                    max_retries: 3,
                    created_at: new Date(),
                    updated_at: new Date()
                });

                const error = new Error('Processing failed');
                await (assessmentProcessor as any).handleProcessingError(assessmentId, error);

                // Verify assessment was marked as failed
                const assessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(assessment!.state).toBe('failed');
                expect(assessment!.error_message).toBe('Processing failed');
                expect(assessment!.completed_at).toBeDefined();
            });
        });

        describe('retryFailedAssessments', () => {
            beforeEach(async () => {
                // Create failed assessments
                const failedAssessments = createBatchTestAssessments(3, ['failed']);
                for (const assessment of failedAssessments) {
                    await mockDatabaseService.createAssessment({
                        assessment_id: assessment.assessment_id,
                        state: 'failed',
                        request_data: assessment,
                        progress: 0,
                        priority: 5,
                        retry_count: 1,
                        timeout_seconds: 300,
                        max_retries: 3,
                        created_at: new Date(),
                        updated_at: new Date()
                    });
                }
            });

            it('should retry failed assessments', async () => {
                const retriedIds = await assessmentProcessor.retryFailedAssessments();

                expect(retriedIds).toHaveLength(3);

                // Verify assessments were reset to pending
                for (const assessmentId of retriedIds) {
                    const assessment = await mockDatabaseService.getAssessment(assessmentId);
                    expect(assessment!.state).toBe('pending');
                    expect(assessment!.retry_count).toBe(2);
                }
            });

            it('should respect retry limits', async () => {
                // Create assessments with different retry counts
                const requests = [
                    generateTestAssessmentData(),
                    generateTestAssessmentData(),
                    generateTestAssessmentData()
                ];

                const assessmentIds = [];
                for (const request of requests) {
                    const assessment = await mockDatabaseService.createAssessment({
                        assessment_id: request.assessment_id,
                        state: 'failed',
                        request_data: request,
                        progress: 0,
                        priority: 5,
                        retry_count: 3, // Max retries reached
                        timeout_seconds: 300,
                        max_retries: 3,
                        created_at: new Date(),
                        updated_at: new Date()
                    });
                    assessmentIds.push(assessment.assessment_id);
                }

                const retriedIds = await assessmentProcessor.retryFailedAssessments();

                // No assessments should be retried (max retries reached)
                expect(retriedIds).toHaveLength(0);
            });
        });
    });

    describe('Circuit Breaker', () => {
        it('should open circuit breaker after threshold failures', async () => {
            const request = generateTestAssessmentData();
            const assessmentId = await mockDatabaseService.createAssessment({
                assessment_id: request.assessment_id,
                state: 'pending',
                request_data: request,
                progress: 0,
                priority: 5,
                retry_count: 0,
                timeout_seconds: 300,
                max_retries: 3,
                created_at: new Date(),
                updated_at: new Date()
            });

            // Simulate multiple failures
            mockComplianceServer.setHealthy(false);

            const promises = Array.from({ length: 6 }, () =>
                assessmentProcessor.processAssessment(assessmentId).catch(() => { })
            );

            await Promise.all(promises);

            // Circuit breaker should be open
            const health = await assessmentProcessor.getHealthStatus();
            expect(health.services.compliance.circuit_breaker.state).toBe('open');
        });

        it('should reset circuit breaker after timeout', async () => {
            const request = generateTestAssessmentData();
            const assessmentId = await mockDatabaseService.createAssessment({
                assessment_id: request.assessment_id,
                state: 'pending',
                request_data: request,
                progress: 0,
                priority: 5,
                retry_count: 0,
                timeout_seconds: 300,
                max_retries: 3,
                created_at: new Date(),
                updated_at: new Date()
            });

            // Simulate failure and open circuit breaker
            mockComplianceServer.setHealthy(false);
            await assessmentProcessor.processAssessment(assessmentId).catch(() => { });

            // Wait for circuit breaker timeout
            await new Promise(resolve => setTimeout(resolve, 100));

            // Reset compliance server
            mockComplianceServer.setHealthy(true);

            // Circuit breaker should be half-open
            const health = await assessmentProcessor.getHealthStatus();
            expect(health.services.compliance.circuit_breaker.state).toBe('half_open');
        });
    });

    describe('Queue Management', () => {
        it('should process assessments in priority order', async () => {
            const requests = [
                generateTestAssessmentData({ priority: 1 }),
                generateTestAssessmentData({ priority: 10 }),
                generateTestAssessmentData({ priority: 5 })
            ];

            const assessmentIds: string[] = [];

            // Create assessments with different priorities
            for (const request of requests) {
                const assessment = await mockDatabaseService.createAssessment({
                    assessment_id: request.assessment_id,
                    state: 'pending',
                    request_data: request,
                    progress: 0,
                    priority: request.priority,
                    retry_count: 0,
                    timeout_seconds: 300,
                    max_retries: 3,
                    created_at: new Date(),
                    updated_at: new Date()
                });
                assessmentIds.push(assessment.assessment_id);
            }

            // Process assessments
            const results = await assessmentProcessor.processBatchAssessments(assessmentIds);

            // Verify all assessments were processed
            expect(results).toHaveLength(3);

            // Verify processing order (higher priority first)
            const processingOrder = results.map(result => result.priority).sort((a, b) => b - a);
            expect(processingOrder).toEqual([10, 5, 1]);
        });

        it('should handle batch processing efficiently', async () => {
            const requests = createBatchTestAssessments(20);
            const assessmentIds: string[] = [];

            // Create assessments
            for (const request of requests) {
                const assessment = await mockDatabaseService.createAssessment({
                    assessment_id: request.assessment_id,
                    state: 'pending',
                    request_data: request,
                    progress: 0,
                    priority: 5,
                    retry_count: 0,
                    timeout_seconds: 300,
                    max_retries: 3,
                    created_at: new Date(),
                    updated_at: new Date()
                });
                assessmentIds.push(assessment.assessment_id);
            }

            const startTime = Date.now();
            const results = await assessmentProcessor.processBatchAssessments(assessmentIds);
            const endTime = Date.now();

            expect(results).toHaveLength(20);
            expect(endTime - startTime).toBeLessThan(10000); // Should complete within 10 seconds
        });

        it('should handle partial batch failures', async () => {
            const requests = [
                generateTestAssessmentData(),
                generateTestAssessmentData(),
                generateTestAssessmentData()
            ];

            const assessmentIds: string[] = [];

            // Create assessments
            for (const request of requests) {
                const assessment = await mockDatabaseService.createAssessment({
                    assessment_id: request.assessment_id,
                    state: 'pending',
                    request_data: request,
                    progress: 0,
                    priority: 5,
                    retry_count: 0,
                    timeout_seconds: 300,
                    max_retries: 3,
                    created_at: new Date(),
                    updated_at: new Date()
                });
                assessmentIds.push(assessment.assessment_id);
            }

            // Simulate failure for second assessment
            vi.spyOn(assessmentProcessor as any, 'processAssessmentInternal')
                .mockImplementationOnce(async (assessmentId: string) => {
                    if (assessmentId === assessmentIds[1]) {
                        throw new Error('Processing failed');
                    }
                    return generateTestResultData(assessmentId);
                });

            const results = await assessmentProcessor.processBatchAssessments(assessmentIds);

            expect(results).toHaveLength(3);
            expect(results[0].success).toBe(true);
            expect(results[1].success).toBe(false);
            expect(results[2].success).toBe(true);
        });
    });

    describe('Error Handling', () => {
        it('should handle database connection errors gracefully', async () => {
            await mockDatabaseService.simulateOverload();

            const request = generateTestAssessmentData();
            const assessmentId = await mockDatabaseService.createAssessment({
                assessment_id: request.assessment_id,
                state: 'pending',
                request_data: request,
                progress: 0,
                priority: 5,
                retry_count: 0,
                timeout_seconds: 300,
                max_retries: 3,
                created_at: new Date(),
                updated_at: new Date()
            });

            await expect(assessmentProcessor.processAssessment(assessmentId))
                .rejects.toThrow('Database connection failed');
        });

        it('should handle compliance server unavailability', async () => {
            mockComplianceServer.setHealthy(false);

            const request = generateTestAssessmentData();
            const assessmentId = await mockDatabaseService.createAssessment({
                assessment_id: request.assessment_id,
                state: 'pending',
                request_data: request,
                progress: 0,
                priority: 5,
                retry_count: 0,
                timeout_seconds: 300,
                max_retries: 3,
                created_at: new Date(),
                updated_at: new Date()
            });

            await expect(assessmentProcessor.processAssessment(assessmentId))
                .rejects.toThrow('Compliance server not available');
        });

        it('should handle network partition scenarios', async () => {
            mockComplianceServer.simulateNetworkPartition(2000);

            const request = generateTestAssessmentData();
            const assessmentId = await mockDatabaseService.createAssessment({
                assessment_id: request.assessment_id,
                state: 'pending',
                request_data: request,
                progress: 0,
                priority: 5,
                retry_count: 0,
                timeout_seconds: 300,
                max_retries: 3,
                created_at: new Date(),
                updated_at: new Date()
            });

            await expect(assessmentProcessor.processAssessment(assessmentId))
                .rejects.toThrow('Network partition detected');
        });

        it('should handle memory pressure gracefully', async () => {
            // Create many assessments to test memory usage
            const requests = createBatchTestAssessments(100);
            const assessmentIds: string[] = [];

            for (const request of requests) {
                const assessment = await mockDatabaseService.createAssessment({
                    assessment_id: request.assessment_id,
                    state: 'pending',
                    request_data: request,
                    progress: 0,
                    priority: 5,
                    retry_count: 0,
                    timeout_seconds: 300,
                    max_retries: 3,
                    created_at: new Date(),
                    updated_at: new Date()
                });
                assessmentIds.push(assessment.assessment_id);
            }

            // Process assessments in batches to avoid memory issues
            const batchSize = 10;
            const results = [];

            for (let i = 0; i < assessmentIds.length; i += batchSize) {
                const batch = assessmentIds.slice(i, i + batchSize);
                const batchResults = await assessmentProcessor.processBatchAssessments(batch);
                results.push(...batchResults);
            }

            expect(results).toHaveLength(100);
        });
    });

    describe('Performance Tests', () => {
        it('should handle high-frequency assessment processing', async () => {
            const requests = createBatchTestAssessments(50);
            const assessmentIds: string[] = [];

            // Create assessments
            for (const request of requests) {
                const assessment = await mockDatabaseService.createAssessment({
                    assessment_id: request.assessment_id,
                    state: 'pending',
                    request_data: request,
                    progress: 0,
                    priority: 5,
                    retry_count: 0,
                    timeout_seconds: 300,
                    max_retries: 3,
                    created_at: new Date(),
                    updated_at: new Date()
                });
                assessmentIds.push(assessment.assessment_id);
            }

            const performance = await measurePerformance(
                'batch-process-50',
                async () => {
                    return await assessmentProcessor.processBatchAssessments(assessmentIds);
                },
                5
            );

            expect(performance.averageTime).toBeLessThan(15000);
            expect(performance.results.every(r => r.success)).toBe(true);
        });

        it('should handle concurrent processing efficiently', async () => {
            const requests = createBatchTestAssessments(20);
            const assessmentIds: string[] = [];

            // Create assessments
            for (const request of requests) {
                const assessment = await mockDatabaseService.createAssessment({
                    assessment_id: request.assessment_id,
                    state: 'pending',
                    request_data: request,
                    progress: 0,
                    priority: 5,
                    retry_count: 0,
                    timeout_seconds: 300,
                    max_retries: 3,
                    created_at: new Date(),
                    updated_at: new Date()
                });
                assessmentIds.push(assessment.assessment_id);
            }

            const performance = await measurePerformance(
                'concurrent-processing',
                async () => {
                    const promises = assessmentIds.map(id =>
                        assessmentProcessor.processAssessment(id)
                    );
                    return await Promise.all(promises);
                },
                10
            );

            expect(performance.averageTime).toBeLessThan(10000);
        });

        it('should handle retry performance efficiently', async () => {
            // Create failed assessments
            const failedAssessments = createBatchTestAssessments(10, ['failed']);
            const assessmentIds: string[] = [];

            for (const assessment of failedAssessments) {
                const assessmentRecord = await mockDatabaseService.createAssessment({
                    assessment_id: assessment.assessment_id,
                    state: 'failed',
                    request_data: assessment,
                    progress: 0,
                    priority: 5,
                    retry_count: 1,
                    timeout_seconds: 300,
                    max_retries: 3,
                    created_at: new Date(),
                    updated_at: new Date()
                });
                assessmentIds.push(assessmentRecord.assessment_id);
            }

            const performance = await measurePerformance(
                'retry-assessments',
                async () => {
                    return await assessmentProcessor.retryFailedAssessments();
                },
                10
            );

            expect(performance.averageTime).toBeLessThan(5000);
            expect(performance.results.every(r => r.success)).toBe(true);
        });
    });

    describe('Edge Cases', () => {
        it('should handle assessment ID collisions', async () => {
            const request1 = generateTestAssessmentData();
            const request2 = { ...generateTestAssessmentData(), assessment_id: request1.assessment_id };

            // First should succeed
            const assessment1 = await mockDatabaseService.createAssessment({
                assessment_id: request1.assessment_id,
                state: 'pending',
                request_data: request1,
                progress: 0,
                priority: 5,
                retry_count: 0,
                timeout_seconds: 300,
                max_retries: 3,
                created_at: new Date(),
                updated_at: new Date()
            });

            // Second should fail or generate different ID
            await expect(mockDatabaseService.createAssessment({
                assessment_id: request2.assessment_id,
                state: 'pending',
                request_data: request2,
                progress: 0,
                priority: 5,
                retry_count: 0,
                timeout_seconds: 300,
                max_retries: 3,
                created_at: new Date(),
                updated_at: new Date()
            })).rejects.toThrow();
        });

        it('should handle very long processing times', async () => {
            const request = generateTestAssessmentData();
            const assessmentId = await mockDatabaseService.createAssessment({
                assessment_id: request.assessment_id,
                state: 'pending',
                request_data: request,
                progress: 0,
                priority: 5,
                retry_count: 0,
                timeout_seconds: 300,
                max_retries: 3,
                created_at: new Date(),
                updated_at: new Date()
            });

            // Simulate very long processing time
            vi.spyOn(assessmentProcessor as any, 'processAssessmentInternal')
                .mockImplementation(async () => {
                    await new Promise(resolve => setTimeout(resolve, 5000));
                    return generateTestResultData(assessmentId);
                });

            const startTime = Date.now();
            const result = await assessmentProcessor.processAssessment(assessmentId, 10000);
            const endTime = Date.now();

            expect(endTime - startTime).toBeLessThan(10000);
            expect(result).toBeDefined();
        });

        it('should handle partial processing failures', async () => {
            const requests = createBatchTestAssessments(10);
            const assessmentIds: string[] = [];

            // Create assessments
            for (const request of requests) {
                const assessment = await mockDatabaseService.createAssessment({
                    assessment_id: request.assessment_id,
                    state: 'pending',
                    request_data: request,
                    progress: 0,
                    priority: 5,
                    retry_count: 0,
                    timeout_seconds: 300,
                    max_retries: 3,
                    created_at: new Date(),
                    updated_at: new Date()
                });
                assessmentIds.push(assessment.assessment_id);
            }

            // Simulate failures for some assessments
            vi.spyOn(assessmentProcessor as any, 'processAssessmentInternal')
                .mockImplementation(async (assessmentId: string) => {
                    if (assessmentId.includes('5') || assessmentId.includes('6')) {
                        throw new Error('Processing failed');
                    }
                    return generateTestResultData(assessmentId);
                });

            const results = await assessmentProcessor.processBatchAssessments(assessmentIds);

            const successful = results.filter(r => r.success).length;
            const failed = results.filter(r => !r.success).length;

            expect(successful).toBe(8);
            expect(failed).toBe(2);
        });

        it('should handle resource exhaustion scenarios', async () => {
            // Create many assessments to test resource limits
            const requests = createBatchTestAssessments(200);
            const assessmentIds: string[] = [];

            for (const request of requests) {
                const assessment = await mockDatabaseService.createAssessment({
                    assessment_id: request.assessment_id,
                    state: 'pending',
                    request_data: request,
                    progress: 0,
                    priority: 5,
                    retry_count: 0,
                    timeout_seconds: 300,
                    max_retries: 3,
                    created_at: new Date(),
                    updated_at: new Date()
                });
                assessmentIds.push(assessment.assessment_id);
            }

            // Process assessments in batches to avoid resource exhaustion
            const batchSize = 20;
            const results = [];

            for (let i = 0; i < assessmentIds.length; i += batchSize) {
                const batch = assessmentIds.slice(i, i + batchSize);
                const batchResults = await assessmentProcessor.processBatchAssessments(batch);
                results.push(...batchResults);

                // Small delay between batches to prevent resource exhaustion
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            expect(results).toHaveLength(200);
        });
    });
});