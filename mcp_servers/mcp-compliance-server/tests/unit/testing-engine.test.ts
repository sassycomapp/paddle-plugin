/**
 * Unit Tests for Automated Testing Engine
 *
 * These tests validate the core functionality of the automated testing engine
 * including test suite execution, result handling, and reporting.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { AutomatedTestingEngine, TestSuite, Test, TestResult, TestExecution } from '../../src/testing/automated-testing';
import { ValidationContext } from '../../src/validation/validators';
import { Logger } from '../../src/logger';
import { ServerConfig } from '../../src/types';

// Mock logger
const mockLogger = {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn()
} as unknown as Logger;

describe('AutomatedTestingEngine', () => {
    let testingEngine: AutomatedTestingEngine;
    let mockContext: ValidationContext;

    beforeEach(() => {
        vi.clearAllMocks();

        mockContext = {
            serverName: 'test-server',
            serverConfig: {
                port: 3000,
                host: 'localhost',
                database: {
                    host: 'localhost',
                    port: 5432,
                    database: 'test',
                    username: 'test',
                    password: 'test'
                },
                logging: {
                    level: 'info' as const
                },
                security: {
                    enableCors: true,
                    allowedOrigins: ['*'],
                    rateLimit: {
                        windowMs: 60000,
                        max: 100
                    }
                },
                compliance: {
                    autoRemediate: false,
                    requireApproval: true,
                    backupBeforeChanges: true
                },
                command: 'node',
                args: ['test']
            } as ServerConfig,
            environment: 'development' as const,
            projectRoot: '/test',
            kilocodeDir: '/test/.kilocode',
            logger: mockLogger
        };

        testingEngine = new AutomatedTestingEngine(mockContext);
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    describe('Test Suite Management', () => {
        it('should initialize with default test suites', () => {
            const suites = testingEngine.getTestSuites();
            expect(suites.length).toBeGreaterThan(0);

            const suiteIds = suites.map(suite => suite.id);
            expect(suiteIds).toContain('security-suite');
            expect(suiteIds).toContain('performance-suite');
            expect(suiteIds).toContain('compatibility-suite');
            expect(suiteIds).toContain('reliability-suite');
            expect(suiteIds).toContain('integration-suite');
        });

        it('should add custom test suite', () => {
            const customSuite: TestSuite = {
                id: 'custom-suite',
                name: 'Custom Test Suite',
                description: 'A custom test suite for testing',
                tests: [],
                environment: 'development',
                serverName: 'test-server',
                serverConfig: mockContext.serverConfig
            };

            testingEngine['addTestSuite'](customSuite);
            const suites = testingEngine.getTestSuites();
            expect(suites.find(s => s.id === 'custom-suite')).toBeDefined();
        });
    });

    describe('Test Execution', () => {
        it('should execute a single test successfully', async () => {
            const mockTest: Test = {
                id: 'test-1',
                name: 'Mock Test',
                description: 'A mock test for testing',
                type: 'security',
                severity: 'medium',
                execute: async () => ({
                    testId: 'test-1',
                    testName: 'Mock Test',
                    passed: true,
                    duration: 100,
                    message: 'Test passed'
                })
            };

            const result = await testingEngine['executeTest'](mockTest);

            expect(result.testId).toBe('test-1');
            expect(result.passed).toBe(true);
            expect(result.duration).toBeGreaterThan(0);
        });

        it('should handle test execution failure', async () => {
            const mockTest: Test = {
                id: 'test-2',
                name: 'Failing Test',
                description: 'A test that always fails',
                type: 'security',
                severity: 'medium',
                execute: async () => {
                    throw new Error('Test failed');
                }
            };

            const result = await testingEngine['executeTest'](mockTest);

            expect(result.testId).toBe('test-2');
            expect(result.passed).toBe(false);
            expect(result.error).toContain('Test failed');
        });

        it('should handle test timeout', async () => {
            const mockTest: Test = {
                id: 'test-3',
                name: 'Timeout Test',
                description: 'A test that times out',
                type: 'security',
                severity: 'medium',
                timeout: 100, // 100ms timeout
                execute: async () => {
                    await new Promise(resolve => setTimeout(resolve, 200)); // 200ms delay
                    return {
                        testId: 'test-3',
                        testName: 'Timeout Test',
                        passed: true,
                        duration: 200,
                        message: 'Test passed'
                    };
                }
            };

            const result = await testingEngine['executeTest'](mockTest);

            expect(result.testId).toBe('test-3');
            expect(result.passed).toBe(false);
            expect(result.error).toContain('timeout');
        });

        it('should retry failed tests', async () => {
            let attemptCount = 0;
            const mockTest: Test = {
                id: 'test-4',
                name: 'Retry Test',
                description: 'A test that fails twice then passes',
                type: 'security',
                severity: 'medium',
                retryCount: 2,
                execute: async () => {
                    attemptCount++;
                    if (attemptCount < 3) {
                        throw new Error(`Attempt ${attemptCount} failed`);
                    }
                    return {
                        testId: 'test-4',
                        testName: 'Retry Test',
                        passed: true,
                        duration: 100,
                        message: 'Test passed after retries'
                    };
                }
            };

            const result = await testingEngine['executeTest'](mockTest);

            expect(result.testId).toBe('test-4');
            expect(result.passed).toBe(true);
            expect(attemptCount).toBe(3);
        });
    });

    describe('Test Suite Execution', () => {
        it('should execute a complete test suite', async () => {
            const suite = testingEngine.getTestSuites()[0]; // Get first suite
            const execution = await testingEngine.runTestSuite(suite.id);

            expect(execution.suiteId).toBe(suite.id);
            expect(execution.suiteName).toBe(suite.name);
            expect(execution.serverName).toBe(suite.serverName);
            expect(execution.status).toBe('completed');
            expect(execution.results.length).toBeGreaterThan(0);
            expect(execution.summary.totalTests).toBe(suite.tests.length);
            expect(execution.summary.passedTests + execution.summary.failedTests).toBe(suite.tests.length);
        });

        it('should handle suite execution failure', async () => {
            // Create a suite with a failing test
            const failingSuite: TestSuite = {
                id: 'failing-suite',
                name: 'Failing Test Suite',
                description: 'A suite with failing tests',
                tests: [{
                    id: 'failing-test',
                    name: 'Failing Test',
                    description: 'A test that always fails',
                    type: 'security',
                    severity: 'critical',
                    execute: async () => {
                        throw new Error('Suite execution failed');
                    }
                }],
                environment: 'development',
                serverName: 'test-server',
                serverConfig: mockContext.serverConfig
            };

            testingEngine['addTestSuite'](failingSuite);
            const execution = await testingEngine.runTestSuite('failing-suite');

            expect(execution.status).toBe('failed');
            expect(execution.summary.failedTests).toBe(1);
            expect(execution.summary.score).toBe(0);
        });

        it('should calculate test scores correctly', async () => {
            const mixedSuite: TestSuite = {
                id: 'mixed-suite',
                name: 'Mixed Test Suite',
                description: 'A suite with mixed results',
                tests: [
                    {
                        id: 'pass-1',
                        name: 'Passing Test 1',
                        description: 'A test that passes',
                        type: 'security',
                        severity: 'medium',
                        execute: async () => ({
                            testId: 'pass-1',
                            testName: 'Passing Test 1',
                            passed: true,
                            duration: 100,
                            message: 'Test passed'
                        })
                    },
                    {
                        id: 'pass-2',
                        name: 'Passing Test 2',
                        description: 'Another test that passes',
                        type: 'security',
                        severity: 'medium',
                        execute: async () => ({
                            testId: 'pass-2',
                            testName: 'Passing Test 2',
                            passed: true,
                            duration: 100,
                            message: 'Test passed'
                        })
                    },
                    {
                        id: 'fail-1',
                        name: 'Failing Test',
                        description: 'A test that fails',
                        type: 'security',
                        severity: 'medium',
                        execute: async () => ({
                            testId: 'fail-1',
                            testName: 'Failing Test',
                            passed: false,
                            duration: 100,
                            message: 'Test failed',
                            error: 'Test error'
                        })
                    }
                ],
                environment: 'development',
                serverName: 'test-server',
                serverConfig: mockContext.serverConfig
            };

            testingEngine['addTestSuite'](mixedSuite);
            const execution = await testingEngine.runTestSuite('mixed-suite');

            expect(execution.summary.totalTests).toBe(3);
            expect(execution.summary.passedTests).toBe(2);
            expect(execution.summary.failedTests).toBe(1);
            expect(execution.summary.score).toBe(67); // 2/3 = 67%
        });
    });

    describe('Test Reporting', () => {
        it('should generate test report', async () => {
            // Execute a test suite first
            const suite = testingEngine.getTestSuites()[0];
            await testingEngine.runTestSuite(suite.id);

            const executions = testingEngine.getExecutionHistory();
            const report = testingEngine.generateTestReport(executions);

            expect(report).toContain('# Automated Testing Report');
            expect(report).toContain('Generated:');
            expect(report).toContain('## Summary');
            expect(report).toContain('## Test Suite Results');
            expect(report).toContain(suite.name);
        });

        it('should handle empty execution history', () => {
            const executions = testingEngine.getExecutionHistory();
            const report = testingEngine.generateTestReport(executions);

            expect(report).toContain('# Automated Testing Report');
            expect(report).toContain('Total Test Suites: 0');
            expect(report).toContain('Total Tests: 0');
        });
    });

    describe('Execution History', () => {
        it('should maintain execution history', async () => {
            const initialHistory = testingEngine.getExecutionHistory();
            expect(initialHistory.length).toBe(0);

            // Execute a test suite
            const suite = testingEngine.getTestSuites()[0];
            await testingEngine.runTestSuite(suite.id);

            const updatedHistory = testingEngine.getExecutionHistory();
            expect(updatedHistory.length).toBe(1);
            expect(updatedHistory[0].suiteId).toBe(suite.id);
        });

        it('should execute all test suites', async () => {
            const suites = testingEngine.getTestSuites();
            const executions = await testingEngine.runAllTestSuites();

            expect(executions.length).toBe(suites.length);

            // All suites should have been executed
            for (const suite of suites) {
                const execution = executions.find(e => e.suiteId === suite.id);
                expect(execution).toBeDefined();
                expect(execution?.suiteName).toBe(suite.name);
            }
        });
    });

    describe('Error Handling', () => {
        it('should handle unknown test suite', async () => {
            await expect(testingEngine.runTestSuite('unknown-suite'))
                .rejects.toThrow('Test suite not found: unknown-suite');
        });

        it('should handle test suite with no tests', async () => {
            const emptySuite: TestSuite = {
                id: 'empty-suite',
                name: 'Empty Test Suite',
                description: 'A suite with no tests',
                tests: [],
                environment: 'development',
                serverName: 'test-server',
                serverConfig: mockContext.serverConfig
            };

            testingEngine['addTestSuite'](emptySuite);
            const execution = await testingEngine.runTestSuite('empty-suite');

            expect(execution.suiteId).toBe('empty-suite');
            expect(execution.results.length).toBe(0);
            expect(execution.summary.totalTests).toBe(0);
            expect(execution.summary.score).toBe(0);
        });
    });
});