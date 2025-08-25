/**
 * Test Utilities and Helpers
 * 
 * This file provides common utilities and helper functions for testing the AssessmentStore,
 * AssessmentProcessor, and AssessmentController components.
 */

import { vi } from 'vitest';

// Mock interfaces and types
export interface MockAssessmentData {
    id?: string;
    assessment_id: string;
    state: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
    request_data: Record<string, any>;
    result_data?: Record<string, any>;
    error_message?: string;
    progress: number;
    priority: number;
    retry_count: number;
    timeout_seconds: number;
    max_retries: number;
    created_at: Date;
    updated_at: Date;
    completed_at?: Date;
}

export interface MockProcessingResult {
    assessment_id: string;
    success: boolean;
    result_data?: Record<string, any>;
    error_message?: string;
    processing_time: number;
    retry_attempts: number;
}

export interface MockApiResponse<T = any> {
    success: boolean;
    data?: T;
    error?: string;
    timestamp: Date;
    request_id: string;
}

/**
 * Creates mock assessment data for testing
 */
export function createMockAssessmentData(
    overrides: Partial<MockAssessmentData> = {}
): MockAssessmentData {
    const baseData: MockAssessmentData = {
        assessment_id: `test-assessment-${Date.now()}`,
        state: 'pending',
        request_data: {
            serverName: 'test-server',
            assessmentType: 'compliance',
            options: { depth: 'full', includeDetails: true },
            timestamp: new Date().toISOString(),
            source: 'test'
        },
        progress: 0,
        priority: 5,
        retry_count: 0,
        timeout_seconds: 300,
        max_retries: 3,
        created_at: new Date(),
        updated_at: new Date()
    };

    return { ...baseData, ...overrides };
}

/**
 * Creates mock processing result
 */
export function createMockProcessingResult(
    overrides: Partial<MockProcessingResult> = {}
): MockProcessingResult {
    const baseResult: MockProcessingResult = {
        assessment_id: `test-assessment-${Date.now()}`,
        success: true,
        processing_time: 1000,
        retry_attempts: 0
    };

    return { ...baseResult, ...overrides };
}

/**
 * Creates mock API response
 */
export function createMockApiResponse<T>(
    data: T,
    overrides: Partial<MockApiResponse<T>> = {}
): MockApiResponse<T> {
    const baseResponse: MockApiResponse<T> = {
        success: true,
        data,
        timestamp: new Date(),
        request_id: `req-${Date.now()}`
    };

    return { ...baseResponse, ...overrides };
}

/**
 * Mock database service for testing
 */
export class MockDatabaseService {
    private assessments: Map<string, MockAssessmentData> = new Map();
    private isConnected = true;
    private connectionError: Error | null = null;

    constructor() {
        // Initialize with some test data
        this.initializeTestData();
    }

    private initializeTestData() {
        const testAssessments = [
            createMockAssessmentData({
                assessment_id: 'test-1',
                state: 'completed',
                progress: 100,
                completed_at: new Date()
            }),
            createMockAssessmentData({
                assessment_id: 'test-2',
                state: 'processing',
                progress: 50
            }),
            createMockAssessmentData({
                assessment_id: 'test-3',
                state: 'pending',
                progress: 0
            })
        ];

        testAssessments.forEach(assessment => {
            this.assessments.set(assessment.assessment_id, assessment);
        });
    }

    async connect(): Promise<void> {
        if (this.connectionError) {
            throw this.connectionError;
        }
        this.isConnected = true;
    }

    async disconnect(): Promise<void> {
        this.isConnected = false;
    }

    async simulateConnectionError(error: Error): Promise<void> {
        this.connectionError = error;
        this.isConnected = false;
    }

    async createAssessment(assessmentData: Omit<MockAssessmentData, 'id' | 'created_at' | 'updated_at'>): Promise<MockAssessmentData> {
        if (!this.isConnected) {
            throw new Error('Database not connected');
        }

        const assessment: MockAssessmentData = {
            ...assessmentData,
            id: `uuid-${Date.now()}`,
            created_at: new Date(),
            updated_at: new Date()
        };

        this.assessments.set(assessment.assessment_id, assessment);
        return assessment;
    }

    async getAssessment(assessmentId: string): Promise<MockAssessmentData | null> {
        if (!this.isConnected) {
            throw new Error('Database not connected');
        }

        return this.assessments.get(assessmentId) || null;
    }

    async updateAssessment(
        assessmentId: string,
        updates: Partial<MockAssessmentData>
    ): Promise<MockAssessmentData | null> {
        if (!this.isConnected) {
            throw new Error('Database not connected');
        }

        const assessment = this.assessments.get(assessmentId);
        if (!assessment) {
            return null;
        }

        const updatedAssessment = {
            ...assessment,
            ...updates,
            updated_at: new Date()
        };

        this.assessments.set(assessmentId, updatedAssessment);
        return updatedAssessment;
    }

    async deleteAssessment(assessmentId: string): Promise<boolean> {
        if (!this.isConnected) {
            throw new Error('Database not connected');
        }

        return this.assessments.delete(assessmentId);
    }

    async getAllAssessments(): Promise<MockAssessmentData[]> {
        if (!this.isConnected) {
            throw new Error('Database not connected');
        }

        return Array.from(this.assessments.values());
    }

    async getAssessmentsByState(state: string): Promise<MockAssessmentData[]> {
        if (!this.isConnected) {
            throw new Error('Database not connected');
        }

        return Array.from(this.assessments.values()).filter(
            assessment => assessment.state === state
        );
    }

    async getAssessmentsByPriority(minPriority: number = 1): Promise<MockAssessmentData[]> {
        if (!this.isConnected) {
            throw new Error('Database not connected');
        }

        return Array.from(this.assessments.values()).filter(
            assessment => assessment.priority >= minPriority
        );
    }

    async getPendingAssessments(): Promise<MockAssessmentData[]> {
        return this.getAssessmentsByState('pending');
    }

    async getProcessingAssessments(): Promise<MockAssessmentData[]> {
        return this.getAssessmentsByState('processing');
    }

    async getCompletedAssessments(): Promise<MockAssessmentData[]> {
        return this.getAssessmentsByState('completed');
    }

    async cleanupOldAssessments(retentionDays: number = 30): Promise<number> {
        if (!this.isConnected) {
            throw new Error('Database not connected');
        }

        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - retentionDays);

        let deletedCount = 0;
        for (const [assessmentId, assessment] of this.assessments.entries()) {
            if (assessment.completed_at && assessment.completed_at < cutoffDate) {
                this.assessments.delete(assessmentId);
                deletedCount++;
            }
        }

        return deletedCount;
    }

    getAssessmentCount(): number {
        return this.assessments.size;
    }

    clear(): void {
        this.assessments.clear();
    }

    reset(): void {
        this.clear();
        this.initializeTestData();
    }
}

/**
 * Mock compliance server for testing
 */
export class MockComplianceServer {
    private isHealthy = true;
    private responseDelay = 100;
    private failureRate = 0;
    private timeoutRate = 0;

    constructor() {
        // Start mock server
        this.startMockServer();
    }

    private startMockServer(): void {
        // This would normally start an actual server, but for testing we'll simulate
        console.log('Mock compliance server started');
    }

    setHealthy(healthy: boolean): void {
        this.isHealthy = healthy;
    }

    setResponseDelay(delay: number): void {
        this.responseDelay = delay;
    }

    setFailureRate(rate: number): void {
        this.failureRate = Math.max(0, Math.min(1, rate));
    }

    setTimeoutRate(rate: number): void {
        this.timeoutRate = Math.max(0, Math.min(1, rate));
    }

    async processAssessment(assessmentData: Record<string, any>): Promise<MockProcessingResult> {
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, this.responseDelay));

        // Simulate timeout
        if (Math.random() < this.timeoutRate) {
            throw new Error('Compliance server timeout');
        }

        // Simulate failure
        if (Math.random() < this.failureRate) {
            return createMockProcessingResult({
                success: false,
                error_message: 'Compliance server processing failed',
                processing_time: this.responseDelay,
                retry_attempts: 0
            });
        }

        // Simulate successful processing
        const resultData = {
            compliance_score: Math.floor(Math.random() * 100),
            violations: Math.floor(Math.random() * 10),
            recommendations: ['Recommendation 1', 'Recommendation 2'],
            details: {
                server_name: assessmentData.serverName,
                assessment_type: assessmentData.assessmentType,
                timestamp: new Date().toISOString()
            }
        };

        return createMockProcessingResult({
            success: true,
            result_data: resultData,
            processing_time: this.responseDelay,
            retry_attempts: 0
        });
    }

    async healthCheck(): Promise<boolean> {
        await new Promise(resolve => setTimeout(resolve, this.responseDelay));
        return this.isHealthy;
    }

    async getServerStatus(): Promise<{
        healthy: boolean;
        response_time: number;
        uptime: number;
        version: string;
    }> {
        await new Promise(resolve => setTimeout(resolve, this.responseDelay));
        return {
            healthy: this.isHealthy,
            response_time: this.responseDelay,
            uptime: Date.now() - (this.startTime || Date.now()),
            version: '1.0.0-test'
        };
    }

    private startTime = Date.now();
}

/**
 * Mock logger for testing
 */
export function createMockLogger() {
    return {
        debug: vi.fn(),
        info: vi.fn(),
        warn: vi.fn(),
        error: vi.fn(),
        child: vi.fn(() => createMockLogger())
    };
}

/**
 * Mock timer utilities for testing async operations
 */
export class MockTimer {
    private timers: Map<NodeJS.Timeout, number> = new Map();

    setTimeout(callback: () => void, delay: number): NodeJS.Timeout {
        const timer = setTimeout(() => {
            callback();
            this.timers.delete(timer);
        }, delay);
        this.timers.set(timer, delay);
        return timer;
    }

    clearTimeout(timer: NodeJS.Timeout): void {
        clearTimeout(timer);
        this.timers.delete(timer);
    }

    setInterval(callback: () => void, interval: number): NodeJS.Timeout {
        const timer = setInterval(callback, interval);
        this.timers.set(timer, interval);
        return timer;
    }

    clearInterval(timer: NodeJS.Timeout): void {
        clearInterval(timer);
        this.timers.delete(timer);
    }

    getActiveTimers(): NodeJS.Timeout[] {
        return Array.from(this.timers.keys());
    }

    getTimerCount(): number {
        return this.timers.size;
    }

    clearAllTimers(): void {
        this.timers.forEach((_, timer) => {
            clearTimeout(timer);
            clearInterval(timer);
        });
        this.timers.clear();
    }
}

/**
 * Performance testing utilities
 */
export class PerformanceTester {
    private results: Array<{
        name: string;
        duration: number;
        memoryUsage: number;
        success: boolean;
        error?: string;
    }> = [];

    async measurePerformance<T>(
        name: string,
        operation: () => Promise<T> | T,
        iterations: number = 10
    ): Promise<{
        averageDuration: number;
        minDuration: number;
        maxDuration: number;
        averageMemory: number;
        successRate: number;
        results: Array<{
            duration: number;
            memoryUsage: number;
            success: boolean;
            error?: string;
        }>;
    }> {
        const testResults: Array<{
            duration: number;
            memoryUsage: number;
            success: boolean;
            error?: string;
        }> = [];

        let totalDuration = 0;
        let totalMemory = 0;
        let successCount = 0;

        for (let i = 0; i < iterations; i++) {
            const startMemory = process.memoryUsage().heapUsed;
            const startTime = Date.now();

            try {
                const result = await operation();
                const duration = Date.now() - startTime;
                const memoryUsage = process.memoryUsage().heapUsed - startMemory;

                testResults.push({
                    duration,
                    memoryUsage,
                    success: true
                });

                totalDuration += duration;
                totalMemory += memoryUsage;
                successCount++;
            } catch (error) {
                const duration = Date.now() - startTime;
                const memoryUsage = process.memoryUsage().heapUsed - startMemory;

                testResults.push({
                    duration,
                    memoryUsage,
                    success: false,
                    error: error instanceof Error ? error.message : String(error)
                });

                totalDuration += duration;
                totalMemory += memoryUsage;
            }
        }

        const averageDuration = totalDuration / iterations;
        const averageMemory = totalMemory / iterations;
        const successRate = successCount / iterations;

        // Store results
        this.results.push({
            name,
            duration: averageDuration,
            memoryUsage: averageMemory,
            success: successRate === 1
        });

        return {
            averageDuration,
            minDuration: Math.min(...testResults.map(r => r.duration)),
            maxDuration: Math.max(...testResults.map(r => r.duration)),
            averageMemory,
            successRate,
            results: testResults
        };
    }

    getResults(): Array<{
        name: string;
        duration: number;
        memoryUsage: number;
        success: boolean;
    }> {
        return [...this.results];
    }

    clearResults(): void {
        this.results = [];
    }

    generateReport(): string {
        let report = '# Performance Test Report\n\n';
        report += `Generated: ${new Date().toISOString()}\n\n`;

        if (this.results.length === 0) {
            report += 'No performance tests have been run yet.\n';
            return report;
        }

        report += '## Summary\n\n';
        report += `Total Tests: ${this.results.length}\n`;
        report += `Successful Tests: ${this.results.filter(r => r.success).length}\n`;
        report += `Failed Tests: ${this.results.filter(r => !r.success).length}\n\n`;

        report += '## Detailed Results\n\n';
        this.results.forEach(result => {
            report += `### ${result.name}\n`;
            report += `- Duration: ${result.duration.toFixed(2)}ms\n`;
            report += `- Memory Usage: ${(result.memoryUsage / 1024 / 1024).toFixed(2)}MB\n`;
            report += `- Status: ${result.success ? '✅ Passed' : '❌ Failed'}\n\n`;
        });

        return report;
    }
}

// Export instances for use in tests
export const mockDatabaseService = new MockDatabaseService();
export const mockComplianceServer = new MockComplianceServer();
export const mockTimer = new MockTimer();
export const performanceTester = new PerformanceTester();