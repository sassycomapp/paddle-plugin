/**
 * Mock Compliance Server for Testing
 * 
 * This file provides a mock implementation of the compliance server for testing
 * the AssessmentProcessor and AssessmentController components.
 */

import { vi } from 'vitest';

export interface MockComplianceResponse {
    success: boolean;
    data?: any;
    error?: string;
    processing_time: number;
    timestamp: string;
}

export interface MockComplianceConfig {
    healthy: boolean;
    response_delay: number;
    failure_rate: number;
    timeout_rate: number;
    max_concurrent_requests: number;
}

export class MockComplianceServer {
    private config: MockComplianceConfig;
    private activeRequests: number = 0;
    private totalRequests: number = 0;
    private successfulRequests: number = 0;
    private failedRequests: number = 0;
    private timeoutRequests: number = 0;
    private requestHistory: Array<{
        id: string;
        timestamp: Date;
        duration: number;
        success: boolean;
        error?: string;
    }> = [];

    constructor(config: Partial<MockComplianceConfig> = {}) {
        this.config = {
            healthy: true,
            response_delay: 100,
            failure_rate: 0,
            timeout_rate: 0,
            max_concurrent_requests: 10,
            ...config
        };
    }

    /**
     * Set the health status of the mock server
     */
    setHealthy(healthy: boolean): void {
        this.config.healthy = healthy;
    }

    /**
     * Set the response delay for the mock server
     */
    setResponseDelay(delay: number): void {
        this.config.response_delay = delay;
    }

    /**
     * Set the failure rate for the mock server
     */
    setFailureRate(rate: number): void {
        this.config.failure_rate = Math.max(0, Math.min(1, rate));
    }

    /**
     * Set the timeout rate for the mock server
     */
    setTimeoutRate(rate: number): void {
        this.config.timeout_rate = Math.max(0, Math.min(1, rate));
    }

    /**
     * Set the maximum concurrent requests
     */
    setMaxConcurrentRequests(max: number): void {
        this.config.max_concurrent_requests = max;
    }

    /**
     * Process an assessment request
     */
    async processAssessment(assessmentData: any): Promise<MockComplianceResponse> {
        const requestId = `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const startTime = Date.now();

        // Check if server is healthy
        if (!this.config.healthy) {
            return this.createErrorResponse(
                requestId,
                'Compliance server is not healthy',
                503
            );
        }

        // Check concurrent request limit
        if (this.activeRequests >= this.config.max_concurrent_requests) {
            return this.createErrorResponse(
                requestId,
                'Compliance server is at maximum capacity',
                429
            );
        }

        this.activeRequests++;
        this.totalRequests++;

        try {
            // Simulate network delay
            await new Promise(resolve => setTimeout(resolve, this.config.response_delay));

            // Simulate timeout
            if (Math.random() < this.config.timeout_rate) {
                this.timeoutRequests++;
                this.recordRequest(requestId, startTime, false, 'Request timeout');
                throw new Error('Compliance server timeout');
            }

            // Simulate failure
            if (Math.random() < this.config.failure_rate) {
                this.failedRequests++;
                this.recordRequest(requestId, startTime, false, 'Processing failed');
                return this.createErrorResponse(
                    requestId,
                    'Compliance server processing failed',
                    500
                );
            }

            // Simulate successful processing
            const resultData = this.generateMockResult(assessmentData);
            this.successfulRequests++;
            this.recordRequest(requestId, startTime, true);

            return {
                success: true,
                data: resultData,
                processing_time: Date.now() - startTime,
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            this.failedRequests++;
            this.recordRequest(
                requestId,
                startTime,
                false,
                error instanceof Error ? error.message : String(error)
            );
            throw error;
        } finally {
            this.activeRequests--;
        }
    }

    /**
     * Perform health check
     */
    async healthCheck(): Promise<{
        healthy: boolean;
        active_requests: number;
        total_requests: number;
        success_rate: number;
        response_time: number;
        uptime: number;
    }> {
        const responseTime = this.config.response_delay;
        const successRate = this.totalRequests > 0
            ? this.successfulRequests / this.totalRequests
            : 1;

        return {
            healthy: this.config.healthy,
            active_requests: this.activeRequests,
            total_requests: this.totalRequests,
            success_rate: successRate,
            response_time: responseTime,
            uptime: Date.now() - (this.startTime || Date.now())
        };
    }

    /**
     * Get server statistics
     */
    getStats(): {
        total_requests: number;
        successful_requests: number;
        failed_requests: number;
        timeout_requests: number;
        active_requests: number;
        success_rate: number;
        average_response_time: number;
    } {
        const totalResponseTime = this.requestHistory.reduce((sum, req) => sum + req.duration, 0);
        const averageResponseTime = this.requestHistory.length > 0
            ? totalResponseTime / this.requestHistory.length
            : 0;

        return {
            total_requests: this.totalRequests,
            successful_requests: this.successfulRequests,
            failed_requests: this.failedRequests,
            timeout_requests: this.timeoutRequests,
            active_requests: this.activeRequests,
            success_rate: this.totalRequests > 0 ? this.successfulRequests / this.totalRequests : 0,
            average_response_time: averageResponseTime
        };
    }

    /**
     * Get request history
     */
    getRequestHistory(): Array<{
        id: string;
        timestamp: Date;
        duration: number;
        success: boolean;
        error?: string;
    }> {
        return [...this.requestHistory];
    }

    /**
     * Clear request history
     */
    clearHistory(): void {
        this.requestHistory = [];
    }

    /**
     * Reset all statistics
     */
    reset(): void {
        this.activeRequests = 0;
        this.totalRequests = 0;
        this.successfulRequests = 0;
        this.failedRequests = 0;
        this.timeoutRequests = 0;
        this.requestHistory = [];
    }

    /**
     * Simulate server overload
     */
    simulateOverload(duration: number = 5000): void {
        this.config.healthy = false;
        setTimeout(() => {
            this.config.healthy = true;
        }, duration);
    }

    /**
     * Simulate network partition
     */
    simulateNetworkPartition(duration: number = 3000): void {
        this.config.failure_rate = 1;
        setTimeout(() => {
            this.config.failure_rate = 0;
        }, duration);
    }

    /**
     * Generate mock compliance result
     */
    private generateMockResult(assessmentData: any): any {
        const complianceScore = Math.floor(Math.random() * 100);
        const violations = Math.floor(Math.random() * 10);
        const recommendations = [
            'Review security configurations',
            'Update compliance policies',
            'Monitor system performance',
            'Implement backup procedures'
        ];

        return {
            assessment_id: assessmentData.assessment_id || `assessment-${Date.now()}`,
            server_name: assessmentData.serverName || 'unknown-server',
            assessment_type: assessmentData.assessmentType || 'compliance',
            compliance_score: complianceScore,
            violations: violations,
            recommendations: recommendations.slice(0, Math.floor(Math.random() * 3) + 1),
            details: {
                timestamp: new Date().toISOString(),
                processing_time: this.config.response_delay,
                server_status: 'online',
                checks_performed: Math.floor(Math.random() * 50) + 10,
                issues_found: violations,
                warnings: Math.floor(Math.random() * 5)
            },
            metadata: {
                generated_by: 'mock-compliance-server',
                version: '1.0.0-test',
                test_mode: true
            }
        };
    }

    /**
     * Create error response
     */
    private createErrorResponse(requestId: string, error: string, statusCode: number): MockComplianceResponse {
        return {
            success: false,
            error: error,
            processing_time: 0,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Record request in history
     */
    private recordRequest(
        requestId: string,
        startTime: number,
        success: boolean,
        error?: string
    ): void {
        const duration = Date.now() - startTime;
        this.requestHistory.push({
            id: requestId,
            timestamp: new Date(),
            duration,
            success,
            error
        });

        // Keep only last 1000 requests
        if (this.requestHistory.length > 1000) {
            this.requestHistory = this.requestHistory.slice(-1000);
        }
    }

    private startTime = Date.now();
}

// Export default instance
export const mockComplianceServer = new MockComplianceServer();