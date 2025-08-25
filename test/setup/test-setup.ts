/**
 * Test Setup Configuration
 * 
 * This file provides the main test setup and configuration for the AssessmentStore
 * testing suite. It includes global test configuration, environment setup, and
 * common test utilities.
 */

import { vi, beforeEach, afterEach, beforeAll, afterAll } from 'vitest';
import { mockDatabaseService } from '../mocks/database-mock';
import { mockComplianceServer } from '../mocks/compliance-server-mock';

// Global test configuration
export const testConfig = {
    // Test environment settings
    environment: 'test',
    database: {
        host: 'localhost',
        port: 5432,
        database: 'assessment_store_test',
        username: 'test_user',
        password: 'test_password'
    },
    complianceServer: {
        url: 'http://localhost:3001',
        timeout: 5000,
        retries: 3
    },
    // Test timeouts
    timeouts: {
        connect: 5000,
        query: 3000,
        operation: 10000,
        assertion: 1000
    },
    // Test data settings
    testData: {
        assessmentCount: 100,
        maxConcurrentRequests: 50,
        retryAttempts: 3
    }
};

// Global test state
export const testState = {
    isSetupComplete: false,
    testStartTime: 0,
    cleanupFunctions: [] as Array<() => Promise<void> | void>,
    mockData: new Map<string, any>()
};

// Mock global implementations
export function setupGlobalMocks(): void {
    // Mock console methods for cleaner test output
    global.console = {
        ...console,
        log: vi.fn(),
        debug: vi.fn(),
        info: vi.fn(),
        warn: vi.fn(),
        error: vi.fn()
    };

    // Mock process.exit to prevent test termination
    vi.spyOn(process, 'exit').mockImplementation((code?: number) => {
        throw new Error(`Process exit called with code: ${code}`);
    });

    // Mock setTimeout and clearTimeout for predictable timing
    vi.useFakeTimers();
}

// Cleanup global mocks
export function cleanupGlobalMocks(): void {
    vi.restoreAllMocks();
    vi.useRealTimers();
}

// Setup test environment
export async function setupTestEnvironment(): Promise<void> {
    if (testState.isSetupComplete) {
        return;
    }

    testState.testStartTime = Date.now();
    testState.cleanupFunctions = [];

    try {
        // Setup database mock
        await mockDatabaseService.connect();
        testState.cleanupFunctions.push(() => mockDatabaseService.disconnect());

        // Setup compliance server mock
        mockComplianceServer.setHealthy(true);
        testState.cleanupFunctions.push(() => mockComplianceServer.reset());

        // Setup global mocks
        setupGlobalMocks();

        // Mark setup as complete
        testState.isSetupComplete = true;

        console.log('Test environment setup completed successfully');
    } catch (error) {
        console.error('Test environment setup failed:', error);
        throw error;
    }
}

// Cleanup test environment
export async function cleanupTestEnvironment(): Promise<void> {
    if (!testState.isSetupComplete) {
        return;
    }

    try {
        // Execute cleanup functions in reverse order
        for (let i = testState.cleanupFunctions.length - 1; i >= 0; i--) {
            const cleanupFn = testState.cleanupFunctions[i];
            try {
                if (typeof cleanupFn === 'function') {
                    await cleanupFn();
                }
            } catch (error) {
                console.error('Cleanup function failed:', error);
            }
        }

        // Reset test state
        testState.cleanupFunctions = [];
        testState.mockData.clear();
        testState.isSetupComplete = false;

        // Cleanup global mocks
        cleanupGlobalMocks();

        console.log('Test environment cleanup completed successfully');
    } catch (error) {
        console.error('Test environment cleanup failed:', error);
        throw error;
    }
}

// Generate test data
export function generateTestAssessmentData(overrides: any = {}): any {
    const baseData = {
        assessment_id: `test-assessment-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        serverName: `test-server-${Math.random().toString(36).substr(2, 6)}`,
        assessmentType: ['compliance', 'health', 'security'][Math.floor(Math.random() * 3)],
        options: {
            includeDetails: Math.random() > 0.5,
            generateReport: Math.random() > 0.3,
            saveResults: Math.random() > 0.2,
            checkServerStatus: Math.random() > 0.4,
            validateConfig: Math.random() > 0.3,
            checkCompliance: Math.random() > 0.2,
            deepScan: Math.random() > 0.6,
            timeout: Math.floor(Math.random() * 600) + 60
        },
        timestamp: new Date().toISOString(),
        source: ['installer', 'compliance'][Math.floor(Math.random() * 2)],
        priority: Math.floor(Math.random() * 10) + 1,
        metadata: {
            testRun: true,
            generatedBy: 'test-setup',
            version: '1.0.0-test'
        }
    };

    return { ...baseData, ...overrides };
}

// Generate test results
export function generateTestResultData(assessmentId: string): any {
    return {
        assessment_id: assessmentId,
        timestamp: new Date().toISOString(),
        totalServers: Math.floor(Math.random() * 20) + 5,
        compliantServers: Math.floor(Math.random() * 15) + 3,
        nonCompliantServers: Math.floor(Math.random() * 5) + 1,
        missingServers: [],
        configurationIssues: [],
        serverStatuses: [],
        overallScore: Math.floor(Math.random() * 100),
        summary: {
            criticalIssues: Math.floor(Math.random() * 3),
            highIssues: Math.floor(Math.random() * 5),
            mediumIssues: Math.floor(Math.random() * 10),
            lowIssues: Math.floor(Math.random() * 15)
        },
        report: {
            format: 'html',
            generatedAt: new Date().toISOString(),
            size: Math.floor(Math.random() * 1000000) + 100000
        },
        metadata: {
            testRun: true,
            generatedBy: 'test-setup',
            version: '1.0.0-test'
        }
    };
}

// Create test assessment with specific state
export function createTestAssessment(state: string, overrides: any = {}): any {
    const assessmentData = generateTestAssessmentData({
        state,
        progress: state === 'completed' ? 100 : state === 'processing' ? Math.floor(Math.random() * 90) + 10 : 0,
        ...overrides
    });

    if (state === 'completed') {
        assessmentData.resultData = generateTestResultData(assessmentData.assessment_id);
        assessmentData.completedAt = new Date().toISOString();
    }

    return assessmentData;
}

// Batch create test assessments
export function createBatchTestAssessments(count: number, states?: string[]): any[] {
    const assessments: any[] = [];
    const possibleStates = states || ['pending', 'processing', 'completed', 'failed', 'cancelled'];

    for (let i = 0; i < count; i++) {
        const state = possibleStates[Math.floor(Math.random() * possibleStates.length)];
        assessments.push(createTestAssessment(state));
    }

    return assessments;
}

// Performance test helper
export async function measurePerformance<T>(
    name: string,
    operation: () => Promise<T> | T,
    iterations: number = 10
): Promise<{
    averageTime: number;
    minTime: number;
    maxTime: number;
    results: Array<{ time: number; success: boolean; error?: string }>;
    result: T;
}> {
    const results: Array<{ time: number; success: boolean; error?: string }> = [];
    let totalTime = 0;
    let minTime = Infinity;
    let maxTime = 0;
    let finalResult: T;

    for (let i = 0; i < iterations; i++) {
        const startTime = Date.now();
        try {
            const result = await operation();
            const time = Date.now() - startTime;

            results.push({ time, success: true });
            totalTime += time;
            minTime = Math.min(minTime, time);
            maxTime = Math.max(maxTime, time);
            finalResult = result;
        } catch (error) {
            const time = Date.now() - startTime;
            results.push({ time, success: false, error: error instanceof Error ? error.message : String(error) });
            totalTime += time;
            minTime = Math.min(minTime, time);
            maxTime = Math.max(maxTime, time);
        }
    }

    return {
        averageTime: totalTime / iterations,
        minTime,
        maxTime,
        results,
        result: finalResult!
    };
}

// Error testing helper
export function createTestError(message: string, code?: string): Error {
    const error = new Error(message);
    if (code) {
        (error as any).code = code;
    }
    return error;
}

// Assertion helpers
export function assertAssessmentState(assessment: any, expectedState: string): void {
    expect(assessment).toBeDefined();
    expect(assessment.assessment_id).toBeDefined();
    expect(assessment.state).toBe(expectedState);
    expect(assessment.progress).toBeGreaterThanOrEqual(0);
    expect(assessment.progress).toBeLessThanOrEqual(100);
    expect(assessment.created_at).toBeDefined();
    expect(assessment.updated_at).toBeDefined();
}

export function assertAssessmentResult(result: any): void {
    expect(result).toBeDefined();
    expect(result.assessment_id).toBeDefined();
    expect(result.timestamp).toBeDefined();
    expect(result.totalServers).toBeGreaterThan(0);
    expect(result.overallScore).toBeGreaterThanOrEqual(0);
    expect(result.overallScore).toBeLessThanOrEqual(100);
}

export function assertAssessmentError(error: any, expectedMessage?: string): void {
    expect(error).toBeDefined();
    expect(error).toBeInstanceOf(Error);
    if (expectedMessage) {
        expect(error.message).toContain(expectedMessage);
    }
}

// Test lifecycle hooks
beforeAll(async () => {
    await setupTestEnvironment();
});

afterAll(async () => {
    await cleanupTestEnvironment();
});

beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks();

    // Reset mock services
    mockDatabaseService.reset();
    mockComplianceServer.reset();

    // Clear test state
    testState.mockData.clear();
});

afterEach(() => {
    // Clean up any pending timers
    vi.clearAllTimers();
});

// Export test utilities
export {
    setupTestEnvironment,
    cleanupTestEnvironment,
    generateTestAssessmentData,
    generateTestResultData,
    createTestAssessment,
    createBatchTestAssessments,
    measurePerformance,
    createTestError,
    assertAssessmentState,
    assertAssessmentResult,
    assertAssessmentError
};