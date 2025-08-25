/**
 * API Endpoint Integration Tests
 * 
 * This file contains comprehensive integration tests for API endpoints,
 * testing HTTP request/response handling, validation, and error scenarios
 * for the AssessmentController and related API components.
 */

import { describe, it, expect, beforeEach, afterEach, vi, test } from 'vitest';
import { mockDatabaseService } from '../mocks/database-mock';
import { mockComplianceServer } from '../mocks/compliance-server-mock';
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
describe('API Endpoint Integration Tests', () => {
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

    describe('Assessment Creation Endpoints', () => {
        it('should create assessment via POST /assessments', async () => {
            // Step 1: Prepare assessment request
            const request = generateTestAssessmentData();

            // Step 2: Send POST request
            const response = await assessmentController.createAssessment(request);

            // Step 3: Verify response
            expect(response.status).toBe(201);
            expect(response.data.assessment_id).toBeDefined();
            expect(response.data.created_at).toBeDefined();

            // Step 4: Verify database persistence
            const dbAssessment = await mockDatabaseService.getAssessment(response.data.assessment_id);
            expect(dbAssessment).toBeDefined();
            expect(dbAssessment.assessment_id).toBe(response.data.assessment_id);
            expect(dbAssessment.state).toBe('pending');
        });

        it('should validate assessment creation request', async () => {
            // Step 1: Prepare invalid request
            const invalidRequest = {
                assessment_id: '',
                serverName: 'test-server',
                assessmentType: 'invalid-type',
                options: { includeDetails: 'invalid' },
                timestamp: 'invalid-timestamp',
                source: 'invalid-source'
            };

            // Step 2: Send POST request with invalid data
            const response = await assessmentController.createAssessment(invalidRequest);

            // Step 3: Verify error response
            expect(response.status).toBe(400);
            expect(response.error).toBeDefined();
            expect(response.error.message).toContain('Invalid assessment data');
        });

        it('should handle duplicate assessment ID', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const firstResponse = await assessmentController.createAssessment(request);

            // Step 2: Create assessment with same ID
            const duplicateRequest = { ...request, assessment_id: request.assessment_id };
            const secondResponse = await assessmentController.createAssessment(duplicateRequest);

            // Step 3: Verify error response
            expect(secondResponse.status).toBe(409);
            expect(secondResponse.error).toBeDefined();
            expect(secondResponse.error.message).toContain('Duplicate assessment ID');
        });

        it('should handle assessment creation with high priority', async () => {
            // Step 1: Prepare high-priority request
            const highPriorityRequest = {
                ...generateTestAssessmentData(),
                priority: 10
            };

            // Step 2: Send POST request
            const response = await assessmentController.createAssessment(highPriorityRequest);

            // Step 3: Verify response
            expect(response.status).toBe(201);

            // Step 4: Verify priority in database
            const dbAssessment = await mockDatabaseService.getAssessment(response.data.assessment_id);
            expect(dbAssessment.priority).toBe(10);
        });

        it('should handle batch assessment creation', async () => {
            // Step 1: Prepare batch requests
            const requests = createBatchTestAssessments(5);

            // Step 2: Send batch POST request
            const responses = await assessmentController.batchCreateAssessments(requests);

            // Step 3: Verify responses
            expect(responses).toHaveLength(5);
            expect(responses.every(r => r.status === 201)).toBe(true);

            // Step 4: Verify database persistence
            for (const response of responses) {
                const dbAssessment = await mockDatabaseService.getAssessment(response.data.assessment_id);
                expect(dbAssessment).toBeDefined();
                expect(dbAssessment.state).toBe('pending');
            }
        });
    });

    describe('Assessment Retrieval Endpoints', () => {
        it('should get assessment by ID via GET /assessments/:id', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const createResponse = await assessmentController.createAssessment(request);
            const assessmentId = createResponse.data.assessment_id;

            // Step 2: Send GET request
            const response = await assessmentController.getAssessment(assessmentId);

            // Step 3: Verify response
            expect(response.status).toBe(200);
            expect(response.data.assessment_id).toBe(assessmentId);
            expect(response.data.state).toBe('pending');
            expect(response.data.created_at).toBeDefined();
        });

        it('should handle assessment not found', async () => {
            // Step 1: Send GET request for non-existent assessment
            const response = await assessmentController.getAssessment('non-existent-id');

            // Step 3: Verify error response
            expect(response.status).toBe(404);
            expect(response.error).toBeDefined();
            expect(response.error.message).toContain('Assessment not found');
        });

        it('should list assessments via GET /assessments', async () => {
            // Step 1: Create multiple assessments
            const requests = createBatchTestAssessments(10);
            for (const request of requests) {
                await assessmentController.createAssessment(request);
            }

            // Step 2: Send GET request
            const response = await assessmentController.listAssessments();

            // Step 3: Verify response
            expect(response.status).toBe(200);
            expect(response.data.assessments).toHaveLength(10);
            expect(response.data.pagination).toBeDefined();
            expect(response.data.pagination.total).toBe(10);
        });

        it('should handle pagination in list assessments', async () => {
            // Step 1: Create many assessments
            const requests = createBatchTestAssessments(25);
            for (const request of requests) {
                await assessmentController.createAssessment(request);
            }

            // Step 2: Send GET request with pagination
            const response = await assessmentController.listAssessments({ limit: 10, offset: 0 });

            // Step 3: Verify response
            expect(response.status).toBe(200);
            expect(response.data.assessments).toHaveLength(10);
            expect(response.data.pagination.limit).toBe(10);
            expect(response.data.pagination.offset).toBe(0);
            expect(response.data.pagination.total).toBe(25);
        });

        it('should filter assessments by state', async () => {
            // Step 1: Create assessments with different states
            const requests = createBatchTestAssessments(5);
            for (const request of requests) {
                await assessmentController.createAssessment(request);
            }

            // Step 2: Process some assessments
            for (let i = 0; i < 3; i++) {
                const assessmentId = requests[i].assessment_id;
                await assessmentController.processAssessment(assessmentId);
            }

            // Step 3: Send GET request with state filter
            const response = await assessmentController.listAssessments({ state: ['pending'] });

            // Step 4: Verify response
            expect(response.status).toBe(200);
            expect(response.data.assessments.every(a => a.state === 'pending')).toBe(true);
            expect(response.data.assessments.length).toBe(2);
        });

        it('should search assessments by server name', async () => {
            // Step 1: Create assessments with different server names
            const requests = [
                { ...generateTestAssessmentData(), serverName: 'server-1' },
                { ...generateTestAssessmentData(), serverName: 'server-2' },
                { ...generateTestAssessmentData(), serverName: 'server-3' }
            ];

            for (const request of requests) {
                await assessmentController.createAssessment(request);
            }

            // Step 2: Send GET request with search
            const response = await assessmentController.listAssessments({ search: 'server-1' });

            // Step 3: Verify response
            expect(response.status).toBe(200);
            expect(response.data.assessments.length).toBe(1);
            expect(response.data.assessments[0].serverName).toBe('server-1');
        });
    });

    describe('Assessment Update Endpoints', () => {
        it('should update assessment progress via PUT /assessments/:id/progress', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const createResponse = await assessmentController.createAssessment(request);
            const assessmentId = createResponse.data.assessment_id;

            // Step 2: Send PUT request
            const response = await assessmentController.updateAssessmentProgress(assessmentId, 50, '50% complete');

            // Step 3: Verify response
            expect(response.status).toBe(200);

            // Step 4: Verify database update
            const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
            expect(dbAssessment.progress).toBe(50);
            expect(dbAssessment.message).toBe('50% complete');
        });

        it('should validate progress update values', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const createResponse = await assessmentController.createAssessment(request);
            const assessmentId = createResponse.data.assessment_id;

            // Step 2: Send PUT request with invalid progress
            const response = await assessmentController.updateAssessmentProgress(assessmentId, 150, 'Invalid progress');

            // Step 3: Verify error response
            expect(response.status).toBe(400);
            expect(response.error).toBeDefined();
            expect(response.error.message).toContain('Invalid progress value');
        });

        it('should handle progress update for non-existent assessment', async () => {
            // Step 1: Send PUT request for non-existent assessment
            const response = await assessmentController.updateAssessmentProgress('non-existent-id', 50, '50% complete');

            // Step 3: Verify error response
            expect(response.status).toBe(404);
            expect(response.error).toBeDefined();
            expect(response.error.message).toContain('Assessment not found');
        });

        it('should complete assessment via PUT /assessments/:id/complete', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const createResponse = await assessmentController.createAssessment(request);
            const assessmentId = createResponse.data.assessment_id;

            // Step 2: Send PUT request
            const result = generateTestResultData();
            const response = await assessmentController.completeAssessment(assessmentId, result);

            // Step 3: Verify response
            expect(response.status).toBe(200);

            // Step 4: Verify database update
            const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
            expect(dbAssessment.state).toBe('completed');
            expect(dbAssessment.result_data).toEqual(result);
            expect(dbAssessment.completed_at).toBeDefined();
        });

        it('should fail assessment via PUT /assessments/:id/fail', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const createResponse = await assessmentController.createAssessment(request);
            const assessmentId = createResponse.data.assessment_id;

            // Step 2: Send PUT request
            const response = await assessmentController.failAssessment(assessmentId, 'Processing failed');

            // Step 3: Verify response
            expect(response.status).toBe(200);

            // Step 4: Verify database update
            const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
            expect(dbAssessment.state).toBe('failed');
            expect(dbAssessment.error_message).toBe('Processing failed');
            expect(dbAssessment.completed_at).toBeDefined();
        });

        it('should cancel assessment via PUT /assessments/:id/cancel', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const createResponse = await assessmentController.createAssessment(request);
            const assessmentId = createResponse.data.assessment_id;

            // Step 2: Send PUT request
            const response = await assessmentController.cancelAssessment(assessmentId, 'User requested cancellation');

            // Step 3: Verify response
            expect(response.status).toBe(200);

            // Step 4: Verify database update
            const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
            expect(dbAssessment.state).toBe('cancelled');
            expect(dbAssessment.error_message).toBe('User requested cancellation');
            expect(dbAssessment.completed_at).toBeDefined();
        });
    });

    describe('Assessment Processing Endpoints', () => {
        it('should process assessment via POST /assessments/:id/process', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const createResponse = await assessmentController.createAssessment(request);
            const assessmentId = createResponse.data.assessment_id;

            // Step 2: Send POST request
            const response = await assessmentController.processAssessment(assessmentId);

            // Step 3: Verify response
            expect(response.status).toBe(200);
            expect(response.data.assessment_id).toBe(assessmentId);
            expect(response.data.processing_time).toBeDefined();

            // Step 4: Verify database update
            const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
            expect(dbAssessment.state).toBe('completed');
        });

        it('should handle processing for non-existent assessment', async () => {
            // Step 1: Send POST request for non-existent assessment
            const response = await assessmentController.processAssessment('non-existent-id');

            // Step 3: Verify error response
            expect(response.status).toBe(404);
            expect(response.error).toBeDefined();
            expect(response.error.message).toContain('Assessment not found');
        });

        it('should handle processing for already completed assessment', async () => {
            // Step 1: Create and complete assessment
            const request = generateTestAssessmentData();
            const createResponse = await assessmentController.createAssessment(request);
            const assessmentId = createResponse.data.assessment_id;

            await assessmentController.completeAssessment(assessmentId, generateTestResultData());

            // Step 2: Send POST request to process completed assessment
            const response = await assessmentController.processAssessment(assessmentId);

            // Step 3: Verify error response
            expect(response.status).toBe(400);
            expect(response.error).toBeDefined();
            expect(response.error.message).toContain('Assessment already completed');
        });

        it('should batch process assessments via POST /assessments/batch/process', async () => {
            // Step 1: Create multiple assessments
            const requests = createBatchTestAssessments(5);
            const assessmentIds = requests.map(r => r.assessment_id);

            // Step 2: Send batch POST request
            const response = await assessmentController.batchProcessAssessments(assessmentIds);

            // Step 3: Verify response
            expect(response.status).toBe(200);
            expect(response.data.processed_count).toBe(5);
            expect(response.data.failed_count).toBe(0);

            // Step 4: Verify database updates
            for (const assessmentId of assessmentIds) {
                const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(dbAssessment.state).toBe('completed');
            }
        });

        it('should handle batch processing with partial failures', async () => {
            // Step 1: Create multiple assessments
            const requests = createBatchTestAssessments(3);
            const assessmentIds = requests.map(r => r.assessment_id);

            // Step 2: Simulate failure for one assessment
            mockComplianceServer.setFailureRate(0.33);

            // Step 3: Send batch POST request
            const response = await assessmentController.batchProcessAssessments(assessmentIds);

            // Step 4: Verify response
            expect(response.status).toBe(207); // Multi-status
            expect(response.data.processed_count).toBeGreaterThan(0);
            expect(response.data.failed_count).toBeGreaterThan(0);

            // Step 5: Verify database updates
            const successCount = assessmentIds.filter(id => {
                const dbAssessment = mockDatabaseService.getAssessmentSync(id);
                return dbAssessment && dbAssessment.state === 'completed';
            }).length;

            const failCount = assessmentIds.filter(id => {
                const dbAssessment = mockDatabaseService.getAssessmentSync(id);
                return dbAssessment && dbAssessment.state === 'failed';
            }).length;

            expect(successCount + failCount).toBe(3);
        });
    });

    describe('Assessment Statistics Endpoints', () => {
        it('should get assessment stats via GET /assessments/stats', async () => {
            // Step 1: Create multiple assessments
            const requests = createBatchTestAssessments(10);
            for (const request of requests) {
                await assessmentController.createAssessment(request);
            }

            // Step 2: Process some assessments
            for (let i = 0; i < 7; i++) {
                await assessmentController.processAssessment(requests[i].assessment_id);
            }

            // Step 3: Send GET request
            const response = await assessmentController.getAssessmentStats();

            // Step 4: Verify response
            expect(response.status).toBe(200);
            expect(response.data.total).toBe(10);
            expect(response.data.by_state).toBeDefined();
            expect(response.data.by_state.pending).toBe(3);
            expect(response.data.by_state.completed).toBe(7);
            expect(response.data.success_rate).toBe(0.7);
        });

        it('should get assessment health via GET /health', async () => {
            // Step 1: Send GET request
            const response = await assessmentController.getHealthStatus();

            // Step 2: Verify response
            expect(response.status).toBe(200);
            expect(response.data.overall).toBeDefined();
            expect(response.data.services).toBeDefined();
            expect(response.data.services.database).toBeDefined();
            expect(response.data.services.compliance).toBeDefined();
            expect(response.data.services.cache).toBeDefined();
        });

        it('should get assessment metrics via GET /metrics', async () => {
            // Step 1: Create and process assessments
            const requests = createBatchTestAssessments(5);
            for (const request of requests) {
                await assessmentController.createAssessment(request);
                await assessmentController.processAssessment(request.assessment_id);
            }

            // Step 2: Send GET request
            const response = await assessmentController.getMetrics();

            // Step 3: Verify response
            expect(response.status).toBe(200);
            expect(response.data.totalAssessments).toBe(5);
            expect(response.data.activeAssessments).toBe(0);
            expect(response.data.completedAssessments).toBe(5);
            expect(response.data.averageProcessingTime).toBeGreaterThan(0);
            expect(response.data.throughputPerMinute).toBeGreaterThan(0);
        });
    });

    describe('Error Handling and Validation', () => {
        it('should handle invalid HTTP methods', async () => {
            // Step 1: Try to use invalid HTTP method
            const response = await assessmentController.invalidMethod('/assessments', 'PATCH');

            // Step 2: Verify error response
            expect(response.status).toBe(405);
            expect(response.error).toBeDefined();
            expect(response.error.message).toContain('Method not allowed');
        });

        it('should handle invalid content types', async () => {
            // Step 1: Try to send invalid content type
            const response = await assessmentController.invalidContentType('/assessments', 'text/plain');

            // Step 2: Verify error response
            expect(response.status).toBe(415);
            expect(response.error).toBeDefined();
            expect(response.error.message).toContain('Unsupported media type');
        });

        it('should handle request size limits', async () => {
            // Step 1: Try to send oversized request
            const largeRequest = {
                ...generateTestAssessmentData(),
                largeData: 'x'.repeat(1000000) // 1MB of data
            };

            const response = await assessmentController.createAssessment(largeRequest);

            // Step 2: Verify error response
            expect(response.status).toBe(413);
            expect(response.error).toBeDefined();
            expect(response.error.message).toContain('Request entity too large');
        });

        it('should handle rate limiting', async () => {
            // Step 1: Send many requests quickly
            const requests = createBatchTestAssessments(100);
            const responses = await Promise.all(
                requests.map(request => assessmentController.createAssessment(request))
            );

            // Step 2: Check for rate limiting responses
            const rateLimitedResponses = responses.filter(r => r.status === 429);
            expect(rateLimitedResponses.length).toBeGreaterThan(0);

            // Step 3: Verify rate limiting headers
            const rateLimitedResponse = rateLimitedResponses[0];
            expect(rateLimitedResponse.headers).toBeDefined();
            expect(rateLimitedResponse.headers['x-ratelimit-limit']).toBeDefined();
            expect(rateLimitedResponse.headers['x-ratelimit-remaining']).toBeDefined();
            expect(rateLimitedResponse.headers['x-ratelimit-reset']).toBeDefined();
        });

        it('should handle authentication failures', async () => {
            // Step 1: Try to access protected endpoint without authentication
            const response = await assessmentController.unauthorizedRequest('/assessments');

            // Step 2: Verify error response
            expect(response.status).toBe(401);
            expect(response.error).toBeDefined();
            expect(response.error.message).toContain('Unauthorized');
        });

        it('should handle authorization failures', async () => {
            // Step 1: Try to access protected endpoint with insufficient permissions
            const response = await assessmentController.forbiddenRequest('/assessments');

            // Step 2: Verify error response
            expect(response.status).toBe(403);
            expect(response.error).toBeDefined();
            expect(response.error.message).toContain('Forbidden');
        });
    });

    describe('Performance and Load Testing', () => {
        it('should handle high request load', async () => {
            // Step 1: Prepare many requests
            const requests = createBatchTestAssessments(100);

            // Step 2: Send requests concurrently
            const performance = await measurePerformance(
                'high-load-creation',
                async () => {
                    const createPromises = requests.map(request =>
                        assessmentController.createAssessment(request)
                    );
                    return await Promise.all(createPromises);
                },
                5
            );

            // Step 3: Verify performance
            expect(performance.averageTime).toBeLessThan(30000); // Less than 30 seconds average
            expect(performance.results.every(r => r.status === 201)).toBe(true);

            // Step 4: Verify all assessments created
            const assessmentIds = performance.results.map(r => r.data.assessment_id);
            expect(assessmentIds).toHaveLength(100);

            // Step 5: Verify database consistency
            for (const assessmentId of assessmentIds) {
                const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(dbAssessment).toBeDefined();
            }
        });

        it('should handle concurrent processing requests', async () => {
            // Step 1: Create many assessments
            const requests = createBatchTestAssessments(50);
            for (const request of requests) {
                await assessmentController.createAssessment(request);
            }

            // Step 2: Send processing requests concurrently
            const performance = await measurePerformance(
                'concurrent-processing',
                async () => {
                    const processPromises = requests.map(request =>
                        assessmentController.processAssessment(request.assessment_id)
                    );
                    return await Promise.all(processPromises);
                },
                5
            );

            // Step 3: Verify performance
            expect(performance.averageTime).toBeLessThan(60000); // Less than 60 seconds average
            expect(performance.results.every(r => r.status === 200)).toBe(true);

            // Step 4: Verify all assessments processed
            for (const request of requests) {
                const dbAssessment = await mockDatabaseService.getAssessment(request.assessment_id);
                expect(dbAssessment.state).toBe('completed');
            }
        });

        it('should handle database query performance under load', async () => {
            // Step 1: Create and process many assessments
            const requests = createBatchTestAssessments(200);
            for (const request of requests) {
                await assessmentController.createAssessment(request);
                await assessmentController.processAssessment(request.assessment_id);
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

            // Step 3: Verify performance
            expect(performance.averageTime).toBeLessThan(5000); // Less than 5 seconds average

            // Step 4: Verify query results
            const listResponse = performance.results[0];
            expect(listResponse.status).toBe(200);
            expect(listResponse.data.assessments.length).toBe(200);

            const statsResponse = performance.results[1];
            expect(statsResponse.status).toBe(200);
            expect(statsResponse.data.total).toBe(200);
        });

        it('should handle memory usage under load', async () => {
            // Step 1: Create many assessments
            const requests = createBatchTestAssessments(1000);
            const assessmentIds: string[] = [];

            for (const request of requests) {
                const response = await assessmentController.createAssessment(request);
                assessmentIds.push(response.data.assessment_id);
            }

            // Step 2: Process assessments
            for (const assessmentId of assessmentIds) {
                await assessmentController.processAssessment(assessmentId);
            }

            // Step 3: Check memory usage
            const memoryUsage = process.memoryUsage();
            expect(memoryUsage.heapUsed).toBeGreaterThan(0);
            expect(memoryUsage.heapTotal).toBeGreaterThan(0);

            // Step 4: Verify system stability
            const health = await assessmentController.getHealthStatus();
            expect(health.overall).toBe('healthy');

            // Step 5: Verify continued functionality
            const listResponse = await assessmentController.listAssessments();
            expect(listResponse.status).toBe(200);
            expect(listResponse.data.assessments.length).toBe(1000);
        });
    });

    describe('Caching and Response Optimization', () => {
        it('should handle caching for frequently accessed data', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const createResponse = await assessmentController.createAssessment(request);
            const assessmentId = createResponse.data.assessment_id;

            // Step 2: Process assessment
            await assessmentController.processAssessment(assessmentId);

            // Step 3: Send multiple GET requests to test caching
            const performance = await measurePerformance(
                'caching-test',
                async () => {
                    const readPromises = Array(100).fill(null).map(() =>
                        assessmentController.getAssessment(assessmentId)
                    );
                    return await Promise.all(readPromises);
                },
                5
            );

            // Step 4: Verify caching improves performance
            expect(performance.averageTime).toBeLessThan(1000); // Less than 1 second average for 100 reads

            // Step 5: Verify all reads return consistent data
            const firstRead = performance.results[0];
            expect(firstRead.status).toBe(200);
            expect(firstRead.data.assessment_id).toBe(assessmentId);
        });

        it('should handle cache invalidation', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const createResponse = await assessmentController.createAssessment(request);
            const assessmentId = createResponse.data.assessment_id;

            // Step 2: Read assessment to cache it
            await assessmentController.getAssessment(assessmentId);

            // Step 3: Update assessment
            await assessmentController.updateAssessmentProgress(assessmentId, 50, '50% complete');

            // Step 4: Read assessment again to verify cache invalidation
            const response = await assessmentController.getAssessment(assessmentId);

            // Step 5: Verify updated data
            expect(response.status).toBe(200);
            expect(response.data.progress).toBe(50);
            expect(response.data.message).toBe('50% complete');
        });

        it('should handle compression for large responses', async () => {
            // Step 1: Create many assessments
            const requests = createBatchTestAssessments(100);
            for (const request of requests) {
                await assessmentController.createAssessment(request);
                await assessmentController.processAssessment(request.assessment_id);
            }

            // Step 2: Send GET request for large list
            const response = await assessmentController.listAssessments();

            // Step 3: Verify response is compressed
            expect(response.headers).toBeDefined();
            expect(response.headers['content-encoding']).toBe('gzip');

            // Step 4: Verify response content
            expect(response.status).toBe(200);
            expect(response.data.assessments.length).toBe(100);
        });

        it('should handle ETag for conditional requests', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const createResponse = await assessmentController.createAssessment(request);
            const assessmentId = createResponse.data.assessment_id;

            // Step 2: Get assessment to get ETag
            const firstResponse = await assessmentController.getAssessment(assessmentId);
            const etag = firstResponse.headers['etag'];

            // Step 3: Send conditional GET request
            const conditionalResponse = await assessmentController.conditionalGet(assessmentId, etag);

            // Step 4: Verify response
            expect(conditionalResponse.status).toBe(304); // Not Modified
            expect(conditionalResponse.data).toBeUndefined();
        });
    });

    describe('API Documentation and OpenAPI', () => {
        it('should provide OpenAPI documentation', async () => {
            // Step 1: Send GET request for OpenAPI documentation
            const response = await assessmentController.getOpenApiDocs();

            // Step 2: Verify response
            expect(response.status).toBe(200);
            expect(response.data.openapi).toBeDefined();
            expect(response.data.info).toBeDefined();
            expect(response.data.paths).toBeDefined();
            expect(response.data.components).toBeDefined();

            // Step 3: Verify assessment endpoints are documented
            expect(response.data.paths['/assessments']).toBeDefined();
            expect(response.data.paths['/assessments/{id}']).toBeDefined();
            expect(response.data.paths['/assessments/stats']).toBeDefined();
            expect(response.data.paths['/health']).toBeDefined();
        });

        it('should provide API examples', async () => {
            // Step 1: Send GET request for API examples
            const response = await assessmentController.getApiExamples();

            // Step 2: Verify response
            expect(response.status).toBe(200);
            expect(response.data.examples).toBeDefined();
            expect(response.data.examples.create_assessment).toBeDefined();
            expect(response.data.examples.update_progress).toBeDefined();
            expect(response.data.examples.complete_assessment).toBeDefined();
        });

        it('should provide API validation rules', async () => {
            // Step 1: Send GET request for validation rules
            const response = await assessmentController.getValidationRules();

            // Step 2: Verify response
            expect(response.status).toBe(200);
            expect(response.data.rules).toBeDefined();
            expect(response.data.rules.assessment_request).toBeDefined();
            expect(response.data.rules.assessment_result).toBeDefined();
            expect(response.data.rules.progress_update).toBeDefined();
        });
    });

    describe('API Versioning and Compatibility', () => {
        it('should handle API versioning', async () => {
            // Step 1: Send request to different API versions
            const v1Response = await assessmentController.getApiVersion('v1');
            const v2Response = await assessmentController.getApiVersion('v2');

            // Step 2: Verify responses
            expect(v1Response.status).toBe(200);
            expect(v2Response.status).toBe(200);
            expect(v1Response.data.version).toBe('1.0.0');
            expect(v2Response.data.version).toBe('2.0.0');
        });

        it('should handle backward compatibility', async () => {
            // Step 1: Create assessment using old API version
            const oldRequest = {
                assessment_id: 'backward-compatible-assessment',
                serverName: 'test-server',
                assessmentType: 'compliance',
                options: { includeDetails: true },
                timestamp: new Date().toISOString(),
                source: 'installer'
            };

            const response = await assessmentController.createAssessmentV1(oldRequest);

            // Step 2: Verify response
            expect(response.status).toBe(201);

            // Step 3: Verify assessment works with new API
            const getResponse = await assessmentController.getAssessment('backward-compatible-assessment');
            expect(getResponse.status).toBe(200);
            expect(getResponse.data.assessment_id).toBe('backward-compatible-assessment');
        });

        it('should handle deprecated endpoints', async () => {
            // Step 1: Send request to deprecated endpoint
            const response = await assessmentController.useDeprecatedEndpoint();

            // Step 2: Verify response includes deprecation warning
            expect(response.status).toBe(200);
            expect(response.headers).toBeDefined();
            expect(response.headers['warning']).toBeDefined();
            expect(response.headers['warning']).toContain('deprecated');
        });

        it('should handle API migration', async () => {
            // Step 1: Send request to migration endpoint
            const response = await assessmentController.migrateApi();

            // Step 2: Verify response
            expect(response.status).toBe(200);
            expect(response.data.migration_status).toBeDefined();
            expect(response.data.new_api_endpoints).toBeDefined();
            expect(response.data.old_api_endpoints).toBeDefined();
        });
    });

    describe('API Security and Compliance', () => {
        it('should handle input sanitization', async () => {
            // Step 1: Create request with malicious content
            const maliciousRequest = {
                ...generateTestAssessmentData(),
                serverName: '<script>alert("xss")</script>',
                options: {
                    includeDetails: true,
                    customOptions: {
                        malicious: 'DROP TABLE assessments; --'
                    }
                }
            };

            const response = await assessmentController.createAssessment(maliciousRequest);

            // Step 2: Verify response
            expect(response.status).toBe(201);

            // Step 3: Verify data is sanitized in database
            const dbAssessment = await mockDatabaseService.getAssessment(response.data.assessment_id);
            expect(dbAssessment.request_data.serverName).not.toContain('<script>');
            expect(dbAssessment.request_data.options.customOptions.malicious).not.toContain('DROP TABLE');
        });

        it('should handle audit logging for API calls', async () => {
            // Step 1: Perform various API operations
            const request = generateTestAssessmentData();
            await assessmentController.createAssessment(request);
            const assessmentId = request.assessment_id;

            await assessmentController.updateAssessmentProgress(assessmentId, 50, '50% complete');
            await assessmentController.processAssessment(assessmentId);
            await assessmentController.getAssessment(assessmentId);

            // Step 2: Get audit logs
            const auditLogs = await mockDatabaseService.getApiAuditLogs();

            // Step 3: Verify audit logs
            expect(auditLogs.length).toBeGreaterThan(0);

            const createLog = auditLogs.find(log => log.operation === 'POST /assessments');
            expect(createLog).toBeDefined();

            const updateLog = auditLogs.find(log => log.operation === 'PUT /assessments/{id}/progress');
            expect(updateLog).toBeDefined();

            const processLog = auditLogs.find(log => log.operation === 'POST /assessments/{id}/process');
            expect(processLog).toBeDefined();

            const readLog = auditLogs.find(log => log.operation === 'GET /assessments/{id}');
            expect(readLog).toBeDefined();
        });

        it('should handle API rate limiting and throttling', async () => {
            // Step 1: Send many requests quickly
            const requests = createBatchTestAssessments(200);
            const responses = await Promise.all(
                requests.map(request => assessmentController.createAssessment(request))
            );

            // Step 2: Analyze rate limiting
            const successCount = responses.filter(r => r.status === 201).length;
            const rateLimitedCount = responses.filter(r => r.status === 429).length;

            expect(successCount).toBeGreaterThan(0);
            expect(rateLimitedCount).toBeGreaterThan(0);

            // Step 3: Verify rate limiting headers
            const rateLimitedResponse = responses.find(r => r.status === 429);
            expect(rateLimitedResponse.headers).toBeDefined();
            expect(rateLimitedResponse.headers['x-ratelimit-limit']).toBeDefined();
            expect(rateLimitedResponse.headers['x-ratelimit-remaining']).toBeDefined();
            expect(rateLimitedResponse.headers['x-ratelimit-reset']).toBeDefined();
        });

        it('should handle API key authentication', async () => {
            // Step 1: Send request with valid API key
            const response = await assessmentController.authenticateWithApiKey('valid-api-key');

            // Step 2: Verify response
            expect(response.status).toBe(200);

            // Step 3: Send request with invalid API key
            const invalidResponse = await assessmentController.authenticateWithApiKey('invalid-api-key');

            // Step 4: Verify error response
            expect(invalidResponse.status).toBe(401);
            expect(invalidResponse.error).toBeDefined();
            expect(invalidResponse.error.message).toContain('Invalid API key');
        });

        it('should handle JWT token authentication', async () => {
            // Step 1: Get JWT token
            const tokenResponse = await assessmentController.getJwtToken();
            expect(tokenResponse.status).toBe(200);
            expect(tokenResponse.data.token).toBeDefined();

            // Step 2: Send request with valid JWT token
            const response = await assessmentController.authenticateWithJwt(tokenResponse.data.token);

