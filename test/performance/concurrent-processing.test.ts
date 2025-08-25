/**
 * Concurrent Processing Performance Tests
 * 
 * This file contains comprehensive performance tests for concurrent assessment processing,
 * testing the system's ability to handle high loads, concurrent operations, and resource utilization
 * under various stress scenarios.
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
describe('Concurrent Processing Performance Tests', () => {
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

    describe('Basic Concurrent Processing', () => {
        it('should handle concurrent assessment creation', async () => {
            // Step 1: Prepare many assessment requests
            const requestCount = 100;
            const requests = createBatchTestAssessments(requestCount);

            // Step 2: Measure performance of concurrent creation
            const performance = await measurePerformance(
                'concurrent-creation',
                async () => {
                    const createPromises = requests.map(request =>
                        assessmentController.createAssessment(request)
                    );
                    return await Promise.all(createPromises);
                },
                5
            );

            // Step 3: Verify performance metrics
            expect(performance.averageTime).toBeLessThan(30000); // Less than 30 seconds average
            expect(performance.minTime).toBeGreaterThan(0);
            expect(performance.maxTime).toBeGreaterThan(0);

            // Step 4: Verify all assessments were created
            const assessmentIds = performance.results.map(r => r.data.assessment_id);
            expect(assessmentIds).toHaveLength(requestCount);
            expect(new Set(assessmentIds).size).toBe(requestCount); // All unique

            // Step 5: Verify database consistency
            for (const assessmentId of assessmentIds) {
                const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(dbAssessment).toBeDefined();
                expect(dbAssessment.state).toBe('pending');
            }
        });

        it('should handle concurrent assessment processing', async () => {
            // Step 1: Create assessments first
            const requestCount = 50;
            const requests = createBatchTestAssessments(requestCount);
            const assessmentIds: string[] = [];

            for (const request of requests) {
                const response = await assessmentController.createAssessment(request);
                assessmentIds.push(response.data.assessment_id);
            }

            // Step 2: Measure performance of concurrent processing
            const performance = await measurePerformance(
                'concurrent-processing',
                async () => {
                    const processPromises = assessmentIds.map(assessmentId =>
                        assessmentController.processAssessment(assessmentId)
                    );
                    return await Promise.all(processPromises);
                },
                5
            );

            // Step 3: Verify performance metrics
            expect(performance.averageTime).toBeLessThan(60000); // Less than 60 seconds average
            expect(performance.minTime).toBeGreaterThan(0);
            expect(performance.maxTime).toBeGreaterThan(0);

            // Step 4: Verify all assessments were processed
            expect(performance.results.every(r => r.status === 200)).toBe(true);

            // Step 5: Verify database consistency
            for (const assessmentId of assessmentIds) {
                const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
                expect(dbAssessment).toBeDefined();
                expect(dbAssessment.state).toBe('completed');
            }
        });

        it('should handle concurrent state updates', async () => {
            // Step 1: Create assessment
            const request = generateTestAssessmentData();
            const createResponse = await assessmentController.createAssessment(request);
            const assessmentId = createResponse.data.assessment_id;

            // Step 2: Measure performance of concurrent state updates
            const updateCount = 20;
            const performance = await measurePerformance(
                'concurrent-updates',
                async () => {
                    const updatePromises = Array(updateCount).fill(null).map((_, index) =>
                        assessmentController.updateAssessmentProgress(assessmentId, index * 5, `${index * 5}% complete`)
                    );
                    return await Promise.all(updatePromises);
                },
                5
            );

            // Step 3: Verify performance metrics
            expect(performance.averageTime).toBeLessThan(5000); // Less than 5 seconds average
            expect(performance.minTime).toBeGreaterThan(0);
            expect(performance.maxTime).toBeGreaterThan(0);

            // Step 4: Verify updates were applied (last update should win)
            const dbAssessment = await mockDatabaseService.getAssessment(assessmentId);
            expect(dbAssessment.progress).toBe(95); // Last update (19 * 5)
            expect(dbAssessment.message).toBe('95% complete');
        });

        it('should handle concurrent database queries', async () => {
            // Step 1: Create many assessments
            const requestCount = 200;
            const requests = createBatchTestAssessments(requestCount);
            for (const request of requests) {
                await assessmentController.createAssessment(request);
            }

            // Step 2: Process some assessments
            for (let i = 0; i < 100; i++) {
                await assessmentController.processAssessment(requests[i].assessment_id);
            }

            // Step 3: Measure performance of concurrent queries
            const performance = await measurePerformance(
                'concurrent-queries',
                async () => {
                    const queryPromises = Array(50).fill(null).map(() => {
                        const randomType = Math.random() > 0.5 ? 'pending' : 'completed';
                        return assessmentController.listAssessments({ state: [randomType], limit: 10 });
                    });
                    return await Promise.all(queryPromises);
                },
                10
            );

            // Step 3: Verify performance metrics
            expect(performance.averageTime).toBeLessThan(5000); // Less than 5 seconds average
            expect(performance.minTime).toBeGreaterThan(0);
            expect(performance.maxTime).toBeGreaterThan(0);

            // Step 4: Verify all queries returned valid results
            expect(performance.results.every(r => r.status === 200)).toBe(true);
            expect(performance.results.every(r => r.data.assessments.length <= 10)).toBe(true);
        });
    });

    describe('Load Testing Scenarios', () => {
        it('should handle high load assessment creation', async () => {
            // Step 1: Prepare high volume of requests
            const requestCount = 500;
            const requests = createBatchTestAssessments(requestCount);

            // Step 2: Measure performance under high load
            const performance = await measurePerformance(
                'high-load-creation',
                async () => {
                    const createPromises = requests.map(request =>
                        assessmentController.createAssessment(request)
                    );
                    return await Promise.all(createPromises);
                },
                3
            );

            // Step 3: Verify performance metrics
            expect(performance.averageTime).toBeLessThan(120000); // Less than 2 minutes average
            expect(performance.successRate).toBeGreaterThan(0.95); // 95% success rate

            // Step 4: Verify system stability
            const health = await assessmentController.getHealthStatus();
            expect(health.overall).toBe('healthy');

            // Step 5: Verify database integrity
            const stats = await assessmentController.getAssessmentStats();
            expect(stats.total).toBe(requestCount);
        });

        it('should handle sustained load processing', async () => {
            // Step 1: Create assessments
            const requestCount = 300;
            const requests = createBatchTestAssessments(requestCount);
            const assessmentIds: string[] = [];

            for (const request of requests) {
                const response = await assessmentController.createAssessment(request);
                assessmentIds.push(response.data.assessment_id);
            }

            // Step 2: Measure sustained processing performance
            const performance = await measurePerformance(
                'sustained-load-processing',
                async () => {
                    const processPromises = assessmentIds.map(assessmentId =>
                        assessmentController.processAssessment(assessmentId)
                    );
                    return await Promise.all(processPromises);
                },
                3
            );

            // Step 3: Verify performance metrics
            expect(performance.averageTime).toBeLessThan(180000); // Less than 3 minutes average
            expect(performance.successRate).toBeGreaterThan(0.90); // 90% success rate

            // Step 4: Verify system remains stable
            const health = await assessmentController.getHealthStatus();
            expect(health.overall).toBe('healthy');

            // Step 5: Verify all assessments processed
            const processedCount = performance.results.filter(r => r.status === 200).length;
            expect(processedCount).toBeGreaterThan(requestCount * 0.9);
        });

        it('should handle mixed workload scenarios', async () => {
            // Step 1: Create assessments
            const requestCount = 200;
            const requests = createBatchTestAssessments(requestCount);
            const assessmentIds: string[] = [];

            for (const request of requests) {
                const response = await assessmentController.createAssessment(request);
                assessmentIds.push(response.data.assessment_id);
            }

            // Step 2: Simulate mixed workload (creation, processing, querying)
            const performance = await measurePerformance(
                'mixed-workload',
                async () => {
                    const mixedPromises = [];

                    // 40% creation
                    for (let i = 0; i < 80; i++) {
                        const newRequest = generateTestAssessmentData();
                        mixedPromises.push(assessmentController.createAssessment(newRequest));
                    }

                    // 40% processing
                    for (let i = 0; i < 80; i++) {
                        const randomId = assessmentIds[Math.floor(Math.random() * assessmentIds.length)];
                        mixedPromises.push(assessmentController.processAssessment(randomId));
                    }

                    // 20% querying
                    for (let i = 0; i < 40; i++) {
                        mixedPromises.push(assessmentController.listAssessments({ limit: 10 }));
                    }

                    return await Promise.all(mixedPromises);
                },
                5
            );

            // Step 3: Verify performance metrics
            expect(performance.averageTime).toBeLessThan(60000); // Less than 1 minute average
            expect(performance.successRate).toBeGreaterThan(0.85); // 85% success rate

            // Step 4: Verify system stability
            const health = await assessmentController.getHealthStatus();
            expect(health.overall).toBe('healthy');
        });

        it('should handle burst load scenarios', async () => {
            // Step 1: Simulate burst load with varying concurrency levels
            const burstScenarios = [
                { concurrency: 10, duration: 5000 },
                { concurrency: 50, duration: 3000 },
                { concurrency: 100, duration: 2000 },
                { concurrency: 200, duration: 1000 }
            ];

            const results = [];

            for (const scenario of burstScenarios) {
                // Step 2: Prepare burst load
                const requests = createBatchTestAssessments(scenario.concurrency);

                // Step 3: Measure burst performance
                const performance = await measurePerformance(
                    `burst-load-${scenario.concurrency}`,
                    async () => {
                        const burstPromises = requests.map(request =>
                            assessmentController.createAssessment(request)
                        );
                        return await Promise.all(burstPromises);
                    },
                    3
                );

                // Step 4: Record results
                results.push({
                    concurrency: scenario.concurrency,
                    averageTime: performance.averageTime,
                    successRate: performance.successRate,
                    throughput: scenario.concurrency / (performance.averageTime / 1000)
                });

                // Step 5: Verify system recovers
                await new Promise(resolve => setTimeout(resolve, 2000));
                const health = await assessmentController.getHealthStatus();
                expect(health.overall).toBe('healthy');
            }

            // Step 6: Analyze burst performance
            console.log('Burst Load Results:', results);
            expect(results.length).toBe(4);
            expect(results.every(r => r.successRate > 0.90)).toBe(true);
        });
    });

    describe('Resource Utilization Testing', () => {
        it('should monitor memory usage under load', async () => {
            // Step 1: Track initial memory usage
            const initialMemory = process.memoryUsage();

            // Step 2: Create many assessments
            const requestCount = 1000;
            const requests = createBatchTestAssessments(requestCount);
            const assessmentIds: string[] = [];

            for (const request of requests) {
                const response = await assessmentController.createAssessment(request);
                assessmentIds.push(response.data.assessment_id);
            }

            // Step 3: Process assessments
            for (const assessmentId of assessmentIds) {
                await assessmentController.processAssessment(assessmentId);
            }

            // Step 4: Track peak memory usage
            const peakMemory = process.memoryUsage();

            // Step 5: Calculate memory growth
            const memoryGrowth = {
                heapUsed: peakMemory.heapUsed - initialMemory.heapUsed,
                heapTotal: peakMemory.heapTotal - initialMemory.heapTotal,
                external: peakMemory.external - initialMemory.external,
                rss: peakMemory.rss - initialMemory.rss
            };

            // Step 6: Verify memory usage is reasonable
            expect(memoryGrowth.heapUsed).toBeLessThan(500 * 1024 * 1024); // Less than 500MB
            expect(memoryGrowth.heapTotal).toBeLessThan(1000 * 1024 * 1024); // Less than 1GB
            expect(memoryGrowth.rss).toBeLessThan(1500 * 1024 * 1024); // Less than 1.5GB

            // Step 7: Verify memory cleanup
            await new Promise(resolve => setTimeout(resolve, 5000));
            const finalMemory = process.memoryUsage();
            expect(finalMemory.heapUsed).toBeLessThan(peakMemory.heapUsed * 1.1); // Less than 10% growth
        });

        it('should monitor CPU usage under load', async () => {
            // Step 1: Track initial CPU usage
            const initialCpu = process.cpuUsage();

            // Step 2: Create and process many assessments
            const requestCount = 500;
            const requests = createBatchTestAssessments(requestCount);
            const assessmentIds: string[] = [];

            for (const request of requests) {
                const response = await assessmentController.createAssessment(request);
                assessmentIds.push(response.data.assessment_id);
            }

            // Step 3: Process assessments with CPU-intensive operations
            for (const assessmentId of assessmentIds) {
                await assessmentController.processAssessment(assessmentId);
            }

            // Step 4: Track CPU usage
            const finalCpu = process.cpuUsage(initialCpu);

            // Step 5: Calculate CPU usage
            const cpuUsageMs = finalCpu.user + finalCpu.system;
            const cpuUsagePercent = (cpuUsageMs / (requestCount * 1000)) * 100; // Percentage per assessment

            // Step 6: Verify CPU usage is reasonable
            expect(cpuUsagePercent).toBeLessThan(10); // Less than 10% CPU per assessment
        });

        it('should monitor database connection usage', async () => {
            // Step 1: Get initial connection pool status
            const initialPool = await mockDatabaseService.getConnectionPoolHealth();

            // Step 2: Perform many concurrent operations
            const requestCount = 200;
            const requests = createBatchTestAssessments(requestCount);
            const assessmentIds: string[] = [];

            for (const request of requests) {
                const response = await assessmentController.createAssessment(request);
                assessmentIds.push(response.data.assessment_id);
            }

            // Step 3: Process assessments
            for (const assessmentId of assessmentIds) {
                await assessmentController.processAssessment(assessmentId);
            }

            // Step 4: Monitor connection pool during operations
            const poolSamples = [];
            for (let i = 0; i < 10; i++) {
                poolSamples.push(await mockDatabaseService.getConnectionPoolHealth());
                await new Promise(resolve => setTimeout(resolve, 1000));
            }

            // Step 5: Analyze connection pool usage
            const maxConnections = Math.max(...poolSamples.map(p => p.active_connections));
            const avgWaitTime = poolSamples.reduce((sum, p) => sum + p.wait_time, 0) / poolSamples.length;

            // Step 6: Verify connection pool usage is reasonable
            expect(maxConnections).toBeLessThan(initialPool.max_connections * 0.8); // Less than 80% of max
            expect(avgWaitTime).toBeLessThan(100); // Less than 100ms average wait time

            // Step 7: Verify connections are properly released
            const finalPool = await mockDatabaseService.getConnectionPoolHealth();
            expect(finalPool.active_connections).toBeLessThan(initialPool.max_connections * 0.2); // Less than 20% of max
        });

        it('should monitor file descriptor usage', async () => {
            // Step 1: Track initial file descriptor usage
            const initialFdCount = await getFileDescriptorCount();

            // Step 2: Perform many file operations
            const requestCount = 100;
            const requests = createBatchTestAssessments(requestCount);
            const assessmentIds: string[] = [];

            for (const request of requests) {
                const response = await assessmentController.createAssessment(request);
                assessmentIds.push(response.data.assessment_id);
            }

            // Step 3: Process assessments with file operations
            for (const assessmentId of assessmentIds) {
                await assessmentController.processAssessment(assessmentId);
            }

            // Step 4: Track peak file descriptor usage
            const peakFdCount = await getFileDescriptorCount();

            // Step 5: Calculate file descriptor growth
            const fdGrowth = peakFdCount - initialFdCount;

            // Step 6: Verify file descriptor usage is reasonable
            expect(fdGrowth).toBeLessThan(100); // Less than 100 file descriptors

            // Step 7: Verify file descriptors are properly closed
            await new Promise(resolve => setTimeout(resolve, 5000));
            const finalFdCount = await getFileDescriptorCount();
            expect(finalFdCount).toBeLessThan(initialFdCount + 50); // Less than 50 growth
        });
    });

    describe('Performance Regression Testing', () {
        it('should detect performance regressions in assessment creation', async () => {
            // Step 1: Establish baseline performance
            const baselineRequests = createBatchTestAssessments(100);
            const baselinePerformance = await measurePerformance(
                'baseline-creation',
                async () => {
                    const createPromises = baselineRequests.map(request =>
                        assessmentController.createAssessment(request)
                    );
                    return await Promise.all(createPromises);
                },
                5
            );

            // Step 2: Simulate potential performance degradation
            await simulatePerformanceDegradation();

            // Step 3: Measure current performance
            const currentRequests = createBatchTestAssessments(100);
            const currentPerformance = await measurePerformance(
                'current-creation',
                async () => {
                    const createPromises = currentRequests.map(request =>
                        assessmentController.createAssessment(request)
                    );
                    return await Promise.all(createPromises);
                },
                5
            );

            // Step 4: Compare performance
            const performanceDegradation = (currentPerformance.averageTime - baselinePerformance.averageTime) / baselinePerformance.averageTime;

            // Step 5: Verify performance regression is detected
            expect(performanceDegradation).toBeLessThan(0.5); // Less than 50% degradation
        });

        it('should detect performance regressions in assessment processing', async () => {
            // Step 1: Establish baseline performance
            const baselineRequests = createBatchTestAssessments(50);
            const baselineAssessmentIds: string[] = [];

            for (const request of baselineRequests) {
                const response = await assessmentController.createAssessment(request);
                baselineAssessmentIds.push(response.data.assessment_id);
            }

            const baselinePerformance = await measurePerformance(
                'baseline-processing',
                async () => {
                    const processPromises = baselineAssessmentIds.map(assessmentId =>
                        assessmentController.processAssessment(assessmentId)
                    );
                    return await Promise.all(processPromises);
                },
                5
            );

            // Step 2: Simulate potential performance degradation
            await simulatePerformanceDegradation();

            // Step 3: Measure current performance
            const currentRequests = createBatchTestAssessments(50);
            const currentAssessmentIds: string[] = [];

            for (const request of currentRequests) {
                const response = await assessmentController.createAssessment(request);
                currentAssessmentIds.push(response.data.assessment_id);
            }

            const currentPerformance = await measurePerformance(
                'current-processing',
                async () => {
                    const processPromises = currentAssessmentIds.map(assessmentId =>
                        assessmentController.processAssessment(assessmentId)
                    );
                    return await Promise.all(processPromises);
                },
                5
            );

            // Step 4: Compare performance
            const performanceDegradation = (currentPerformance.averageTime - baselinePerformance.averageTime) / baselinePerformance.averageTime;

            // Step 5: Verify performance regression is detected
            expect(performanceDegradation).toBeLessThan(0.5); // Less than 50% degradation
        });

        it('should detect performance regressions in database queries', async () => {
            // Step 1: Establish baseline performance
            const baselineRequests = createBatchTestAssessments(200);
            for (const request of baselineRequests) {
                await assessmentController.createAssessment(request);
            }

            const baselinePerformance = await measurePerformance(
                'baseline-queries',
                async () => {
                    const queryPromises = Array(20).fill(null).map(() =>
                        assessmentController.listAssessments({ limit: 10 })
                    );
                    return await Promise.all(queryPromises);
                },
                10
            );

            // Step 2: Simulate potential performance degradation
            await simulatePerformanceDegradation();

            // Step 3: Measure current performance
            const currentPerformance = await measurePerformance(
                'current-queries',
                async () => {
                    const queryPromises = Array(20).fill(null).map(() =>
                        assessmentController.listAssessments({ limit: 10 })
                    );
                    return await Promise.all(queryPromises);
                },
                10
            );

            // Step 4: Compare performance
            const performanceDegradation = (currentPerformance.averageTime - baselinePerformance.averageTime) / baselinePerformance.averageTime;

            // Step 5: Verify performance regression is detected
            expect(performanceDegradation).toBeLessThan(0.5); // Less than 50% degradation
        });
    });

    describe('Stress Testing', () => {
        it('should handle extreme stress conditions', async () => {
            // Step 1: Prepare extreme load
            const extremeLoad = 1000;
            const requests = createBatchTestAssessments(extremeLoad);

// Step 2: Measure performance under extreme stress
