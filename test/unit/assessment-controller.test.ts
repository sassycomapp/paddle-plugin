/**
 * AssessmentController Unit Tests
 *
 * This file contains comprehensive unit tests for the AssessmentController component,
 * testing API endpoint responses, Promise-based API integration, error handling,
 * input validation, and concurrent request handling.
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

// Mock AssessmentController implementation for testing
class TestAssessmentController {
    constructor() {
        // Initialize with mock dependencies
        this.database = mockDatabaseService;
        this.complianceServer = mockComplianceServer;
        this.logger = console;
        this.config = {
            requestTimeout: 30000,
            maxConcurrentRequests: 100,
            rateLimit: {
                windowMs: 60000,
                max: 1000
            },
            validation: {
                maxRequestSize: 1024 * 1024, // 1MB
                allowedAssessmentTypes: ['compliance', 'health', 'security'],
                requiredFields: ['assessment_id', 'serverName', 'assessmentType']
            }
        };
    }

    // Mock AssessmentController methods
    async createAssessment(request: any): Promise<any> {
        // Validate request
        if (!this.validateRequest(request)) {
            throw new Error('Validation failed');
        }

        // Sanitize request
        const sanitized = await this.sanitizeRequest(request);

        // Check for duplicate
        const existing = await this.database.getAssessment(sanitized.assessment_id);
        if (existing) {
            throw new Error('Assessment already exists');
        }

        // Create assessment
        const assessment = await this.database.createAssessment({
            assessment_id: sanitized.assessment_id,
            state: 'pending',
            request_data: sanitized,
            progress: 0,
            priority: 5,
            retry_count: 0,
            timeout_seconds: 300,
            max_retries: 3,
            created_at: new Date(),
            updated_at: new Date()
        });

        return {
            status: 201,
            data: assessment
        };
    }

    async getAssessment(assessmentId: string): Promise<any> {
        const assessment = await this.database.getAssessment(assessmentId);
        if (!assessment) {
            throw new Error('Assessment not found');
        }

        return {
            status: 200,
            data: assessment
        };
    }

    async updateAssessmentProgress(assessmentId: string, progress: number, message?: string, timeout?: number): Promise<any> {
        // Validate progress
        if (progress < 0 || progress > 100) {
            throw new Error('Progress must be between 0 and 100');
        }

        const assessment = await this.database.getAssessment(assessmentId);
        if (!assessment) {
            throw new Error('Assessment not found');
        }

        // Validate state
        if (assessment.state === 'completed' || assessment.state === 'failed' || assessment.state === 'cancelled') {
            throw new Error(`Cannot update ${assessment.state} assessment`);
        }

        // Update progress
        await this.database.updateAssessment(assessmentId, {
            state: 'processing',
            progress: progress,
            error_message: message,
            updated_at: new Date()
        }, assessment.version);

        return {
            status: 200,
            data: { assessmentId, progress, message }
        };
    }

    async completeAssessment(assessmentId: string, result: any): Promise<any> {
        const assessment = await this.database.getAssessment(assessmentId);
        if (!assessment) {
            throw new Error('Assessment not found');
        }

        // Validate state
        if (assessment.state !== 'processing') {
            throw new Error(`Cannot complete assessment in ${assessment.state} state`);
        }

        // Complete assessment
        await this.database.updateAssessment(assessmentId, {
            state: 'completed',
            progress: 100,
            result_data: result,
            completed_at: new Date(),
            updated_at: new Date()
        }, assessment.version + 1);

        return {
            status: 200,
            data: { assessmentId, result }
        };
    }

    async failAssessment(assessmentId: string, error: string): Promise<any> {
        const assessment = await this.database.getAssessment(assessmentId);
        if (!assessment) {
            throw new Error('Assessment not found');
        }

        // Validate state
        if (assessment.state !== 'processing') {
            throw new Error(`Cannot fail assessment in ${assessment.state} state`);
        }

        // Fail assessment
        await this.database.updateAssessment(assessmentId, {
            state: 'failed',
            error_message: error,
            completed_at: new Date(),
            updated_at: new Date()
        }, assessment.version + 1);

        return {
            status: 200,
            data: { assessmentId, error }
        };
    }

    async cancelAssessment(assessmentId: string, reason?: string): Promise<any> {
        const assessment = await this.database.getAssessment(assessmentId);
        if (!assessment) {
            throw new Error('Assessment not found');
        }

        // Validate state
        if (assessment.state === 'completed' || assessment.state === 'failed') {
            throw new Error(`Cannot cancel ${assessment.state} assessment`);
        }

        // Cancel assessment
        await this.database.updateAssessment(assessmentId, {
            state: 'cancelled',
            error_message: reason,
            completed_at: new Date(),
            updated_at: new Date()
        }, assessment.version + 1);

        return {
            status: 200,
            data: { assessmentId, reason }
        };
    }

    async listAssessments(filters?: any): Promise<any> {
        const assessments = await this.database.listAssessments(filters);
        return {
            status: 200,
            data: {
                assessments: assessments,
                total: assessments.length
            }
        };
    }

    async getAssessmentStats(): Promise<any> {
        const stats = await this.database.getAssessmentStats();
        return {
            status: 200,
            data: stats
        };
    }

    async batchCreateAssessments(requests: any[]): Promise<any> {
        const created: string[] = [];
        const failed: Array<{ request: any, error: string }> = [];

        for (const request of requests) {
            try {
                const response = await this.createAssessment(request);
                created.push(response.data.assessment_id);
            } catch (error) {
                failed.push({
                    request,
                    error: error instanceof Error ? error.message : String(error)
                });
            }
        }

        return {
            status: failed.length > 0 ? 207 : 201,
            data: {
                created,
                failed
            }
        };
    }

    async batchUpdateProgress(updates: Array<{ assessmentId: string, progress: number, message?: string }>): Promise<any> {
        const updated: string[] = [];
        const failed: Array<{ assessmentId: string, error: string }> = [];

        for (const update of updates) {
            try {
                const response = await this.updateAssessmentProgress(update.assessmentId, update.progress, update.message);
                updated.push(response.data.assessmentId);
            } catch (error) {
                failed.push({
                    assessmentId: update.assessmentId,
                    error: error instanceof Error ? error.message : String(error)
                });
            }
        }

        return {
            status: failed.length > 0 ? 207 : 200,
            data: {
                updated,
                failed
            }
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

    // Private methods
    private validateRequest(request: any): boolean {
        return request.assessment_id &&
            request.serverName &&
            request.assessmentType &&
            this.config.validation.allowedAssessmentTypes.includes(request.assessmentType);
    }

    private async sanitizeRequest(request: any): Promise<any> {
        return {
            ...request,
            serverName: request.serverName?.trim(),
            assessmentType: request.assessmentType.toLowerCase(),
            options: {
                ...request.options,
                includeDetails: Boolean(request.options?.includeDetails),
                generateReport: Boolean(request.options?.generateReport),
                deepScan: Boolean(request.options?.deepScan)
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
describe('AssessmentController', () => {
    let assessmentController: TestAssessmentController;

    beforeAll(async () => {
        await setupTestEnvironment();
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

    describe('Constructor and Initialization', () => {
        it('should create AssessmentController instance with correct configuration', () => {
            expect(assessmentController).toBeDefined();
            expect(assessmentController).toBeInstanceOf(TestAssessmentController);
        });

        it('should initialize with default configuration', () => {
            const controller = new TestAssessmentController();
            expect(controller).toBeDefined();
        });

        it('should handle database connection failure gracefully', async () => {
            // Simulate database connection failure
            await mockDatabaseService.simulateOverload();

            const controller = new TestAssessmentController();
            await expect(controller.getHealthStatus())
                .rejects.toThrow();
        });
    });

    describe('API Endpoint Tests', () => {
        describe('createAssessment', () => {
            it('should create assessment successfully', async () => {
                const request = generateTestAssessmentData();
                const response = await assessmentController.createAssessment(request);

                expect(response).toBeDefined();
                expect(response.status).toBe(201);
                expect(response.data.assessment_id).toBe(request.assessment_id);
                expect(response.data.state).toBe('pending');

                // Verify assessment was created in database
                const assessment = await mockDatabaseService.getAssessment(request.assessment_id);
                expect(assessment).toBeDefined();
                expect(assessment.state).toBe('pending');
            });

            it('should validate required fields', async () => {
                const invalidRequest = {
                    serverName: 'test-server',
                    // Missing assessment_id and assessmentType
                };

                await expect(assessmentController.createAssessment(invalidRequest))
                    .rejects.toThrow('Validation failed');
            });

            it('should validate assessment type', async () => {
                const invalidRequest = {
                    assessment_id: 'test-assessment',
                    serverName: 'test-server',
                    assessmentType: 'invalid_type',
                    options: { includeDetails: true }
                };

                await expect(assessmentController.createAssessment(invalidRequest))
                    .rejects.toThrow('Invalid assessment type');
            });

            it('should handle duplicate assessment IDs', async () => {
                const request = generateTestAssessmentData();

                // Create first assessment
                await assessmentController.createAssessment(request);

                // Try to create duplicate
                await expect(assessmentController.createAssessment(request))
                    .rejects.toThrow('Assessment already exists');
            });

            it('should sanitize input data', async () => {
                const request = {
                    assessment_id: 'test-assessment',
                    serverName: '  test-server  ',
                    assessmentType: 'COMPLIANCE',
                    options: {
                        includeDetails: 'true',
                        generateReport: 'false',
                        deepScan: 'true'
                    }
                };

                const response = await assessmentController.createAssessment(request);

                expect(response).toBeDefined();
                expect(response.data.serverName).toBe('test-server');
                expect(response.data.assessmentType).toBe('compliance');
                expect(response.data.options.includeDetails).toBe(true);
                expect(response.data.options.generateReport).toBe(false);
                expect(response.data.options.deepScan).toBe(true);
            });
        });

        describe('getAssessment', () => {
            beforeEach(async () => {
                const request = generateTestAssessmentData();
                await assessmentController.createAssessment(request);
            });

            it('should get assessment successfully', async () => {
                const request = generateTestAssessmentData();
                const createResponse = await assessmentController.createAssessment(request);

                const response = await assessmentController.getAssessment(request.assessment_id);

                expect(response).toBeDefined();
                expect(response.status).toBe(200);
                expect(response.data.assessment_id).toBe(request.assessment_id);
                expect(response.data.state).toBe('pending');
            });

            it('should handle non-existent assessment', async () => {
                await expect(assessmentController.getAssessment('non-existent-id'))
                    .rejects.toThrow('Assessment not found');
            });

            it('should handle database errors gracefully', async () => {
                await mockDatabaseService.simulateOverload();

                await expect(assessmentController.getAssessment('test-assessment'))
                    .rejects.toThrow('Database error');
            });
        });

        describe('updateAssessmentProgress', () => {
            beforeEach(async () => {
                const request = generateTestAssessmentData();
                await assessmentController.createAssessment(request);

                // Update to processing state
                await mockDatabaseService.updateAssessment(request.assessment_id, {
                    state: 'processing',
                    progress: 0,
                    updated_at: new Date()
                }, 1);
            });

            it('should update progress successfully', async () => {
                const response = await assessmentController.updateAssessmentProgress(
                    'test-assessment',
                    50,
                    'Processing server configurations'
                );

                expect(response).toBeDefined();
                expect(response.status).toBe(200);

                // Verify progress was updated
                const assessment = await mockDatabaseService.getAssessment('test-assessment');
                expect(assessment.progress).toBe(50);
                expect(assessment.error_message).toBe('Processing server configurations');
            });

            it('should validate progress range', async () => {
                await expect(assessmentController.updateAssessmentProgress('test-assessment', -1))
                    .rejects.toThrow('Progress must be between 0 and 100');

                await expect(assessmentController.updateAssessmentProgress('test-assessment', 101))
                    .rejects.toThrow('Progress must be between 0 and 100');
            });

            it('should handle non-existent assessment', async () => {
                await expect(assessmentController.updateAssessmentProgress('non-existent-id', 50))
                    .rejects.toThrow('Assessment not found');
            });

            it('should handle state validation', async () => {
                // Update to completed state
                await mockDatabaseService.updateAssessment('test-assessment', {
                    state: 'completed',
                    progress: 100,
                    updated_at: new Date()
                }, 2);

                await expect(assessmentController.updateAssessmentProgress('test-assessment', 75))
                    .rejects.toThrow('Cannot update completed assessment');
            });
        });

        describe('completeAssessment', () => {
            beforeEach(async () => {
                const request = generateTestAssessmentData();
                await assessmentController.createAssessment(request);

                // Update to processing state
                await mockDatabaseService.updateAssessment(request.assessment_id, {
                    state: 'processing',
                    progress: 50,
                    updated_at: new Date()
                }, 1);
            });

            it('should complete assessment successfully', async () => {
                const result = generateTestResultData('test-assessment');
                const response = await assessmentController.completeAssessment('test-assessment', result);

                expect(response).toBeDefined();
                expect(response.status).toBe(200);

                // Verify assessment was completed
                const assessment = await mockDatabaseService.getAssessment('test-assessment');
                expect(assessment.state).toBe('completed');
                expect(assessment.progress).toBe(100);
                expect(assessment.result_data).toEqual(result);
            });

            it('should validate assessment state', async () => {
                // Keep assessment in pending state
                await expect(assessmentController.completeAssessment('test-assessment', {}))
                    .rejects.toThrow('Cannot complete assessment in pending state');
            });

            it('should handle non-existent assessment', async () => {
                await expect(assessmentController.completeAssessment('non-existent-id', {}))
                    .rejects.toThrow('Assessment not found');
            });
        });

        describe('failAssessment', () => {
            beforeEach(async () => {
                const request = generateTestAssessmentData();
                await assessmentController.createAssessment(request);

                // Update to processing state
                await mockDatabaseService.updateAssessment(request.assessment_id, {
                    state: 'processing',
                    progress: 50,
                    updated_at: new Date()
                }, 1);
            });

            it('should fail assessment successfully', async () => {
                const response = await assessmentController.failAssessment(
                    'test-assessment',
                    'Processing failed'
                );

                expect(response).toBeDefined();
                expect(response.status).toBe(200);

                // Verify assessment was failed
                const assessment = await mockDatabaseService.getAssessment('test-assessment');
                expect(assessment.state).toBe('failed');
                expect(assessment.error_message).toBe('Processing failed');
            });

            it('should validate assessment state', async () => {
                // Keep assessment in pending state
                await expect(assessmentController.failAssessment('test-assessment', 'Error'))
                    .rejects.toThrow('Cannot fail assessment in pending state');
            });

            it('should handle non-existent assessment', async () => {
                await expect(assessmentController.failAssessment('non-existent-id', 'Error'))
                    .rejects.toThrow('Assessment not found');
            });
        });

        describe('cancelAssessment', () => {
            beforeEach(async () => {
                const request = generateTestAssessmentData();
                await assessmentController.createAssessment(request);
            });

            it('should cancel assessment successfully', async () => {
                const response = await assessmentController.cancelAssessment(
                    'test-assessment',
                    'User requested cancellation'
                );

                expect(response).toBeDefined();
                expect(response.status).toBe(200);

                // Verify assessment was cancelled
                const assessment = await mockDatabaseService.getAssessment('test-assessment');
                expect(assessment.state).toBe('cancelled');
                expect(assessment.error_message).toBe('User requested cancellation');
            });

            it('should validate assessment state', async () => {
                // Update to completed state
                await mockDatabaseService.updateAssessment('test-assessment', {
                    state: 'completed',
                    progress: 100,
                    updated_at: new Date()
                }, 1);

                await expect(assessmentController.cancelAssessment('test-assessment', 'Reason'))
                    .rejects.toThrow('Cannot cancel completed assessment');
            });

            it('should handle non-existent assessment', async () => {
                await expect(assessmentController.cancelAssessment('non-existent-id', 'Reason'))
                    .rejects.toThrow('Assessment not found');
            });
        });

        describe('listAssessments', () => {
            beforeEach(async () => {
                const requests = createBatchTestAssessments(5);
                for (const request of requests) {
                    await assessmentController.createAssessment(request);
                }
            });

            it('should list all assessments', async () => {
                const response = await assessmentController.listAssessments();

                expect(response).toBeDefined();
                expect(response.status).toBe(200);
                expect(response.data.assessments).toHaveLength(5);
                expect(response.data.total).toBe(5);
            });

            it('should filter by state', async () => {
                // Update one assessment to completed
                await mockDatabaseService.updateAssessment('test-assessment-1', {
                    state: 'completed',
                    progress: 100,
                    updated_at: new Date()
                }, 1);

                const response = await assessmentController.listAssessments({
                    state: ['completed']
                });

                expect(response).toBeDefined();
                expect(response.data.assessments).toHaveLength(1);
                expect(response.data.assessments[0].state).toBe('completed');
            });

            it('should handle pagination', async () => {
                const response = await assessmentController.listAssessments({
                    limit: 2,
                    offset: 0
                });

                expect(response).toBeDefined();
                expect(response.data.assessments).toHaveLength(2);
                expect(response.data.total).toBe(5);
            });

            it('should handle sorting', async () => {
                const response = await assessmentController.listAssessments({
                    sortBy: 'createdAt',
                    sortOrder: 'desc'
                });

                expect(response).toBeDefined();
                expect(response.data.assessments).toHaveLength(5);
                // Verify sorting order
                const dates = response.data.assessments.map(a => new Date(a.createdAt));
                for (let i = 1; i < dates.length; i++) {
                    expect(dates[i - 1].getTime()).toBeGreaterThanOrEqual(dates[i].getTime());
                }
            });
        });

        describe('getAssessmentStats', () => {
            beforeEach(async () => {
                const requests = createBatchTestAssessments(10);
                for (const request of requests) {
                    await assessmentController.createAssessment(request);
                }

                // Update some assessments to different states
                await mockDatabaseService.updateAssessment('test-assessment-1', {
                    state: 'completed',
                    progress: 100,
                    updated_at: new Date()
                }, 1);

                await mockDatabaseService.updateAssessment('test-assessment-2', {
                    state: 'failed',
                    error_message: 'Processing failed',
                    updated_at: new Date()
                }, 1);
            });

            it('should get assessment statistics', async () => {
                const response = await assessmentController.getAssessmentStats();

                expect(response).toBeDefined();
                expect(response.status).toBe(200);
                expect(response.data.total).toBe(10);
                expect(response.data.by_state).toBeDefined();
                expect(response.data.by_state.completed).toBe(1);
                expect(response.data.by_state.failed).toBe(1);
                expect(response.data.successRate).toBe(0.1); // 1 completed out of 10
            });
        });

        describe('batchCreateAssessments', () => {
            it('should create multiple assessments successfully', async () => {
                const requests = createBatchTestAssessments(3);
                const response = await assessmentController.batchCreateAssessments(requests);

                expect(response).toBeDefined();
                expect(response.status).toBe(201);
                expect(response.data.created).toHaveLength(3);
                expect(response.data.failed).toHaveLength(0);

                // Verify all assessments were created
                for (const assessmentId of response.data.created) {
                    const assessment = await mockDatabaseService.getAssessment(assessmentId);
                    expect(assessment).toBeDefined();
                }
            });

            it('should handle partial failures in batch', async () => {
                const requests = [
                    generateTestAssessmentData(),
                    generateTestAssessmentData(),
                    { ...generateTestAssessmentData(), assessmentType: 'invalid' }
                ];

                const response = await assessmentController.batchCreateAssessments(requests);

                expect(response).toBeDefined();
                expect(response.status).toBe(207); // Multi-status
                expect(response.data.created).toHaveLength(2);
                expect(response.data.failed).toHaveLength(1);
            });

            it('should handle empty batch', async () => {
                const response = await assessmentController.batchCreateAssessments([]);

                expect(response).toBeDefined();
                expect(response.status).toBe(200);
                expect(response.data.created).toHaveLength(0);
                expect(response.data.failed).toHaveLength(0);
            });
        });

        describe('batchUpdateProgress', () => {
            beforeEach(async () => {
                const requests = createBatchTestAssessments(3);
                for (const request of requests) {
                    await assessmentController.createAssessment(request);

                    // Update to processing state
                    await mockDatabaseService.updateAssessment(request.assessment_id, {
                        state: 'processing',
                        progress: 0,
                        updated_at: new Date()
                    }, 1);
                }
            });

            it('should update progress for multiple assessments', async () => {
                const updates = [
                    { assessmentId: 'test-assessment-1', progress: 25, message: '25% complete' },
                    { assessmentId: 'test-assessment-2', progress: 50, message: '50% complete' },
                    { assessmentId: 'test-assessment-3', progress: 75, message: '75% complete' }
                ];

                const response = await assessmentController.batchUpdateProgress(updates);

                expect(response).toBeDefined();
                expect(response.status).toBe(200);
                expect(response.data.updated).toHaveLength(3);
                expect(response.data.failed).toHaveLength(0);

                // Verify progress was updated
                for (const update of updates) {
                    const assessment = await mockDatabaseService.getAssessment(update.assessmentId);
                    expect(assessment.progress).toBe(update.progress);
                    expect(assessment.error_message).toBe(update.message);
                }
            });

            it('should handle partial failures in batch update', async () => {
                const updates = [
                    { assessmentId: 'test-assessment-1', progress: 25 },
                    { assessmentId: 'non-existent-id', progress: 50 },
                    { assessmentId: 'test-assessment-3', progress: 75 }
                ];

                const response = await assessmentController.batchUpdateProgress(updates);

                expect(response).toBeDefined();
                expect(response.status).toBe(207); // Multi-status
                expect(response.data.updated).toHaveLength(2);
                expect(response.data.failed).toHaveLength(1);
            });
        });
    });

    describe('Promise-Based API Integration', () => {
        it('should handle Promise-based operations correctly', async () => {
            const request = generateTestAssessmentData();

            // Create assessment
            const createPromise = assessmentController.createAssessment(request);
            const createResponse = await createPromise;

            expect(createResponse).toBeDefined();
            expect(createResponse.status).toBe(201);

            // Get assessment
            const getPromise = assessmentController.getAssessment(request.assessment_id);
            const getResponse = await getPromise;

            expect(getResponse).toBeDefined();
            expect(getResponse.status).toBe(200);

            // Update progress
            const updatePromise = assessmentController.updateAssessmentProgress(
                request.assessment_id,
                50,
                'Processing'
            );
            const updateResponse = await updatePromise;

            expect(updateResponse).toBeDefined();
            expect(updateResponse.status).toBe(200);
        });

        it('should handle Promise rejection properly', async () => {
            const invalidRequest = {
                serverName: 'test-server',
                // Missing required fields
            };

            await expect(assessmentController.createAssessment(invalidRequest))
                .rejects.toThrow('Validation failed');
        });

        it('should handle Promise chaining', async () => {
            const request = generateTestAssessmentData();

            // Chain operations
            const result = await assessmentController.createAssessment(request)
                .then(response => assessmentController.getAssessment(request.assessment_id))
                .then(response => assessmentController.updateAssessmentProgress(
                    request.assessment_id,
                    25,
                    'Starting'
                ))
                .then(response => assessmentController.getAssessment(request.assessment_id));

            expect(result).toBeDefined();
            expect(result.status).toBe(200);
            expect(result.data.progress).toBe(25);
        });

        it('should handle Promise.all for concurrent operations', async () => {
            const requests = createBatchTestAssessments(3);

            const createPromises = requests.map(request =>
                assessmentController.createAssessment(request)
            );

            const createResponses = await Promise.all(createPromises);

            expect(createResponses).toHaveLength(3);
            expect(createResponses.every(r => r.status === 201)).toBe(true);

            // Get all assessments concurrently
            const getPromises = requests.map(request =>
                assessmentController.getAssessment(request.assessment_id)
            );

            const getResponses = await Promise.all(getPromises);

            expect(getResponses).toHaveLength(3);
            expect(getResponses.every(r => r.status === 200)).toBe(true);
        });
    });

    describe('Error Handling', () => {
        it('should handle database connection errors', async () => {
            await mockDatabaseService.simulateOverload();

            await expect(assessmentController.createAssessment(generateTestAssessmentData()))
                .rejects.toThrow('Database connection failed');
        });

        it('should handle compliance server errors', async () => {
            mockComplianceServer.setHealthy(false);

            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);

            await expect(assessmentController.getAssessment(request.assessment_id))
                .resolves.toBeDefined(); // Should still work without compliance server
        });

        it('should handle network timeouts', async () => {
            mockComplianceServer.setTimeoutRate(1);

            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);

            // Should handle timeout gracefully
            const response = await assessmentController.getAssessment(request.assessment_id);
            expect(response).toBeDefined();
        });

        it('should handle rate limiting', async () => {
            // Mock rate limiting to fail
            vi.spyOn(assessmentController as any, 'handleRateLimit')
                .mockReturnValue(false);

            const request = generateTestAssessmentData();

            await expect(assessmentController.createAssessment(request))
                .rejects.toThrow('Rate limit exceeded');
        });

        it('should handle request size limits', async () => {
            const largeRequest = {
                assessment_id: 'test-assessment',
                serverName: 'test-server',
                assessmentType: 'compliance',
                options: {
                    // Large data that exceeds size limit
                    largeData: 'x'.repeat(2 * 1024 * 1024) // 2MB
                }
            };

            await expect(assessmentController.createAssessment(largeRequest))
                .rejects.toThrow('Request too large');
        });

        it('should handle malformed JSON', async () => {
            const malformedRequest = JSON.parse('{"assessment_id": "test", "serverName": "test", "assessmentType": "compliance", "options": {');

            await expect(assessmentController.createAssessment(malformedRequest))
                .rejects.toThrow('Invalid JSON');
        });
    });

    describe('Input Validation', () => {
        it('should validate assessment ID format', async () => {
            const invalidRequest = {
                assessment_id: 'invalid-id',
                serverName: 'test-server',
                assessmentType: 'compliance',
                options: { includeDetails: true }
            };

            await expect(assessmentController.createAssessment(invalidRequest))
                .rejects.toThrow('Invalid assessment ID format');
        });

        it('should validate server name format', async () => {
            const invalidRequest = {
                assessment_id: 'test-assessment',
                serverName: '', // Empty server name
                assessmentType: 'compliance',
                options: { includeDetails: true }
            };

            await expect(assessmentController.createAssessment(invalidRequest))
                .rejects.toThrow('Server name is required');
        });

        it('should validate options structure', async () => {
            const invalidRequest = {
                assessment_id: 'test-assessment',
                serverName: 'test-server',
                assessmentType: 'compliance',
                options: 'invalid-options' // Should be object
            };

            await expect(assessmentController.createAssessment(invalidRequest))
                .rejects.toThrow('Options must be an object');
        });

        it('should validate option values', async () => {
            const invalidRequest = {
                assessment_id: 'test-assessment',
                serverName: 'test-server',
                assessmentType: 'compliance',
                options: {
                    includeDetails: 'invalid', // Should be boolean
                    generateReport: 123, // Should be boolean
                    deepScan: 'yes' // Should be boolean
                }
            };

            await expect(assessmentController.createAssessment(invalidRequest))
                .rejects.toThrow('Invalid option values');
        });

        it('should validate timestamp format', async () => {
            const invalidRequest = {
                assessment_id: 'test-assessment',
                serverName: 'test-server',
                assessmentType: 'compliance',
                timestamp: 'invalid-timestamp',
                options: { includeDetails: true }
            };

            await expect(assessmentController.createAssessment(invalidRequest))
                .rejects.toThrow('Invalid timestamp format');
        });
    });

    describe('Concurrent Request Handling', () => {
        it('should handle concurrent create requests', async () => {
            const requests = createBatchTestAssessments(10);

            const promises = requests.map(request =>
                assessmentController.createAssessment(request)
            );

            const responses = await Promise.all(promises);

            expect(responses).toHaveLength(10);
            expect(responses.every(r => r.status === 201)).toBe(true);

            // Verify all assessments were created
            for (const request of requests) {
                const assessment = await mockDatabaseService.getAssessment(request.assessment_id);
                expect(assessment).toBeDefined();
            }
        });

        it('should handle concurrent get requests', async () => {
            // Create assessments first
            const requests = createBatchTestAssessments(5);
            for (const request of requests) {
                await assessmentController.createAssessment(request);
            }

            const promises = requests.map(request =>
                assessmentController.getAssessment(request.assessment_id)
            );

            const responses = await Promise.all(promises);

            expect(responses).toHaveLength(5);
            expect(responses.every(r => r.status === 200)).toBe(true);
        });

        it('should handle mixed concurrent operations', async () => {
            const requests = createBatchTestAssessments(5);

            // Create assessments
            const createPromises = requests.map(request =>
                assessmentController.createAssessment(request)
            );

            await Promise.all(createPromises);

            // Mixed operations: some get, some update
            const mixedPromises = [
                assessmentController.getAssessment(requests[0].assessment_id),
                assessmentController.updateAssessmentProgress(requests[1].assessment_id, 25),
                assessmentController.getAssessment(requests[2].assessment_id),
                assessmentController.updateAssessmentProgress(requests[3].assessment_id, 50),
                assessmentController.getAssessment(requests[4].assessment_id)
            ];

            const responses = await Promise.all(mixedPromises);

            expect(responses).toHaveLength(5);
            expect(responses.every(r => r.status === 200)).toBe(true);
        });

        it('should handle request timeout', async () => {
            const request = generateTestAssessmentData();

            // Simulate slow processing
            vi.spyOn(mockDatabaseService, 'updateAssessment')
                .mockImplementationOnce(async () => {
                    await new Promise(resolve => setTimeout(resolve, 5000));
                    return { assessment_id: request.assessment_id, state: 'processing' };
                });

            await assessmentController.createAssessment(request);

            // Should timeout after specified time
            await expect(assessmentController.updateAssessmentProgress(
                request.assessment_id,
                50,
                undefined,
                1000 // 1 second timeout
            )).rejects.toThrow('Request timeout');
        });

        it('should handle circuit breaker activation', async () => {
            // Simulate multiple failures
            mockDatabaseService.simulateOverload(5000);

            const requests = createBatchTestAssessments(5);
            const promises = requests.map(request =>
                assessmentController.createAssessment(request).catch(() => ({ error: 'failed' }))
            );

            const results = await Promise.all(promises);

            // Some should fail due to circuit breaker
            const failed = results.filter(r => (r as any).error);
            expect(failed.length).toBeGreaterThan(0);
        });
    });

    describe('Performance Tests', () => {
        it('should handle high-frequency create requests', async () => {
            const requests = createBatchTestAssessments(50);

            const performance = await measurePerformance(
                'high-frequency-create',
                async () => {
                    const promises = requests.map(request =>
                        assessmentController.createAssessment(request)
                    );
                    return await Promise.all(promises);
                },
                5
            );

            expect(performance.averageTime).toBeLessThan(10000);
            expect(performance.results.every(r => r.status === 201)).toBe(true);
        });

        it('should handle high-frequency get requests', async () => {
            // Create assessments first
            const requests = createBatchTestAssessments(20);
            for (const request of requests) {
                await assessmentController.createAssessment(request);
            }

            const performance = await measurePerformance(
                'high-frequency-get',
                async () => {
                    const promises = requests.map(request =>
                        assessmentController.getAssessment(request.assessment_id)
                    );
                    return await Promise.all(promises);
                },
                10
            );

            expect(performance.averageTime).toBeLessThan(5000);
            expect(performance.results.every(r => r.status === 200)).toBe(true);
        });

        it('should handle batch operations efficiently', async () => {
            const requests = createBatchTestAssessments(100);

            const performance = await measurePerformance(
                'batch-create',
                async () => {
                    return await assessmentController.batchCreateAssessments(requests);
                },
                5
            );

            expect(performance.averageTime).toBeLessThan(15000);
            expect(performance.data.created.length).toBe(100);
        });

        it('should handle memory pressure gracefully', async () => {
            // Create many assessments
            const requests = createBatchTestAssessments(200);
            for (const request of requests) {
                await assessmentController.createAssessment(request);
            }

            // Process in batches to avoid memory issues
            const batchSize = 20;
            const results = [];

            for (let i = 0; i < requests.length; i += batchSize) {
                const batch = requests.slice(i, i + batchSize);
                const batchResults = await assessmentController.batchCreateAssessments(batch);
                results.push(batchResults);

                // Small delay between batches
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            expect(results.length).toBeGreaterThan(0);
        });
    });

    describe('Edge Cases', () => {
        it('should handle assessment ID collisions', async () => {
            const request1 = generateTestAssessmentData();
            const request2 = { ...generateTestAssessmentData(), assessment_id: request1.assessment_id };

            // First should succeed
            const response1 = await assessmentController.createAssessment(request1);
            expect(response1.status).toBe(201);

            // Second should fail
            await expect(assessmentController.createAssessment(request2))
                .rejects.toThrow('Assessment already exists');
        });

        it('should handle very long assessment IDs', async () => {
            const longId = 'a'.repeat(255);
            const request = {
                assessment_id: longId,
                serverName: 'test-server',
                assessmentType: 'compliance',
                options: { includeDetails: true }
            };

            await expect(assessmentController.createAssessment(request))
                .rejects.toThrow('Assessment ID too long');
        });

        it('should handle special characters in server names', async () => {
            const request = {
                assessment_id: 'test-assessment',
                serverName: 'test-server-123!@#$%^&*()',
                assessmentType: 'compliance',
                options: { includeDetails: true }
            };

            const response = await assessmentController.createAssessment(request);
            expect(response.status).toBe(201);
        });

        it('should handle Unicode characters', async () => {
            const request = {
                assessment_id: 'test-assessment',
                serverName: '测试服务器',
                assessmentType: 'compliance',
                options: { includeDetails: true }
            };

            const response = await assessmentController.createAssessment(request);
            expect(response.status).toBe(201);
        });

        it('should handle nested option structures', async () => {
            const request = {
                assessment_id: 'test-assessment',
                serverName: 'test-server',
                assessmentType: 'compliance',
                options: {
                    includeDetails: true,
                    generateReport: true,
                    deepScan: true,
                    customOptions: {
                        nested: {
                            value: 'test',
                            array: [1, 2, 3],
                            object: { key: 'value' }
                        }
                    }
                }
            };

            const response = await assessmentController.createAssessment(request);
            expect(response.status).toBe(201);
        });

        it('should handle null and undefined values', async () => {
            const request = {
                assessment_id: 'test-assessment',
                serverName: 'test-server',
                assessmentType: 'compliance',
                options: {
                    includeDetails: null,
                    generateReport: undefined,
                    deepScan: true
                }
            };

            const response = await assessmentController.createAssessment(request);
            expect(response.status).toBe(201);
        });
    });

    describe('Logging and Monitoring', () => {
        it('should log requests and responses', async () => {
            const request = generateTestAssessmentData();

            const logSpy = vi.spyOn(assessmentController as any, 'logRequest');

            const response = await assessmentController.createAssessment(request);

            expect(logSpy).toHaveBeenCalledWith(
                expect.objectContaining(request),
                expect.objectContaining({ status: 201 }),
                expect.any(Number)
            );
        });

        it('should track request metrics', async () => {
            const requests = createBatchTestAssessments(5);

            // Create assessments
            for (const request of requests) {
                await assessmentController.createAssessment(request);
            }

            // Get metrics
            const stats = await assessmentController.getAssessmentStats();

            expect(stats).toBeDefined();
            expect(stats.data.total).toBe(5);
        });

        it('should handle error logging', async () => {
            const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => { });

            try {
                await assessmentController.createAssessment({
                    assessment_id: 'test',
                    serverName: 'test',
                    assessmentType: 'invalid'
                });
            } catch (error) {
                // Expected to throw
            }

            expect(errorSpy).toHaveBeenCalled();
        });
    });
});