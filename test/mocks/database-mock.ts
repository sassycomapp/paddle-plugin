/**
 * Mock Database Service for Testing
 * 
 * This file provides a mock implementation of the database service for testing
 * the AssessmentStore component.
 */

import { vi } from 'vitest';

export interface MockDatabaseConfig {
    connection_delay: number;
    failure_rate: number;
    timeout_rate: number;
    max_connections: number;
    query_delay: number;
}

export interface MockAssessmentRecord {
    id: string;
    assessment_id: string;
    state: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
    version: number;
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

export interface MockQueryResult {
    success: boolean;
    data?: any;
    error?: string;
    duration: number;
}

export class MockDatabaseService {
    private config: MockDatabaseConfig;
    private isConnected: boolean = false;
    private connectionError: Error | null = null;
    private activeConnections: number = 0;
    private totalConnections: number = 0;
    private successfulConnections: number = 0;
    private failedConnections: number = 0;
    private assessments: Map<string, MockAssessmentRecord> = new Map();
    private queryHistory: Array<{
        id: string;
        timestamp: Date;
        query: string;
        duration: number;
        success: boolean;
        error?: string;
    }> = [];
    private connectionHistory: Array<{
        id: string;
        timestamp: Date;
        duration: number;
        success: boolean;
        error?: string;
    }> = [];

    constructor(config: Partial<MockDatabaseConfig> = {}) {
        this.config = {
            connection_delay: 50,
            failure_rate: 0,
            timeout_rate: 0,
            max_connections: 10,
            query_delay: 10,
            ...config
        };

        // Initialize with some test data
        this.initializeTestData();
    }

    /**
     * Initialize test data
     */
    private initializeTestData(): void {
        const testAssessments: MockAssessmentRecord[] = [
            {
                id: 'uuid-1',
                assessment_id: 'test-assessment-1',
                state: 'completed',
                version: 1,
                request_data: {
                    serverName: 'test-server-1',
                    assessmentType: 'compliance',
                    options: { depth: 'full', includeDetails: true },
                    timestamp: new Date().toISOString(),
                    source: 'test'
                },
                result_data: {
                    compliance_score: 85,
                    violations: 2,
                    recommendations: ['Update security policies']
                },
                progress: 100,
                priority: 5,
                retry_count: 0,
                timeout_seconds: 300,
                max_retries: 3,
                created_at: new Date(Date.now() - 3600000),
                updated_at: new Date(Date.now() - 1800000),
                completed_at: new Date(Date.now() - 1800000)
            },
            {
                id: 'uuid-2',
                assessment_id: 'test-assessment-2',
                state: 'processing',
                version: 2,
                request_data: {
                    serverName: 'test-server-2',
                    assessmentType: 'health',
                    options: { depth: 'basic', includeDetails: false },
                    timestamp: new Date().toISOString(),
                    source: 'test'
                },
                progress: 65,
                priority: 8,
                retry_count: 1,
                timeout_seconds: 600,
                max_retries: 3,
                created_at: new Date(Date.now() - 300000),
                updated_at: new Date(Date.now() - 60000)
            },
            {
                id: 'uuid-3',
                assessment_id: 'test-assessment-3',
                state: 'pending',
                version: 1,
                request_data: {
                    serverName: 'test-server-3',
                    assessmentType: 'security',
                    options: { depth: 'full', includeDetails: true },
                    timestamp: new Date().toISOString(),
                    source: 'test'
                },
                progress: 0,
                priority: 3,
                retry_count: 0,
                timeout_seconds: 900,
                max_retries: 5,
                created_at: new Date(Date.now() - 60000),
                updated_at: new Date(Date.now() - 60000)
            }
        ];

        testAssessments.forEach(assessment => {
            this.assessments.set(assessment.assessment_id, assessment);
        });
    }

    /**
     * Connect to the database
     */
    async connect(): Promise<void> {
        const connectionId = `conn-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const startTime = Date.now();

        this.totalConnections++;

        try {
            // Simulate connection delay
            await new Promise(resolve => setTimeout(resolve, this.config.connection_delay));

            // Simulate connection failure
            if (Math.random() < this.config.failure_rate) {
                this.failedConnections++;
                this.recordConnection(connectionId, startTime, false, 'Connection failed');
                throw new Error('Database connection failed');
            }

            // Simulate connection timeout
            if (Math.random() < this.config.timeout_rate) {
                this.failedConnections++;
                this.recordConnection(connectionId, startTime, false, 'Connection timeout');
                throw new Error('Database connection timeout');
            }

            // Check connection limit
            if (this.activeConnections >= this.config.max_connections) {
                this.failedConnections++;
                this.recordConnection(connectionId, startTime, false, 'Connection limit reached');
                throw new Error('Database connection limit reached');
            }

            this.activeConnections++;
            this.successfulConnections++;
            this.isConnected = true;
            this.connectionError = null;

            this.recordConnection(connectionId, startTime, true);

        } catch (error) {
            this.isConnected = false;
            this.connectionError = error instanceof Error ? error : new Error(String(error));
            throw error;
        }
    }

    /**
     * Disconnect from the database
     */
    async disconnect(): Promise<void> {
        if (this.isConnected) {
            this.activeConnections--;
            this.isConnected = false;
        }
    }

    /**
     * Create a new assessment
     */
    async createAssessment(assessmentData: Omit<MockAssessmentRecord, 'id' | 'version' | 'created_at' | 'updated_at'>): Promise<MockAssessmentRecord> {
        await this.executeQuery('create_assessment');

        const assessment: MockAssessmentRecord = {
            ...assessmentData,
            id: `uuid-${Date.now()}`,
            version: 1,
            created_at: new Date(),
            updated_at: new Date()
        };

        this.assessments.set(assessment.assessment_id, assessment);
        return assessment;
    }

    /**
     * Get an assessment by ID
     */
    async getAssessment(assessmentId: string): Promise<MockAssessmentRecord | null> {
        await this.executeQuery('get_assessment');
        return this.assessments.get(assessmentId) || null;
    }

    /**
     * Update an assessment
     */
    async updateAssessment(
        assessmentId: string,
        updates: Partial<MockAssessmentRecord>,
        expectedVersion?: number
    ): Promise<MockAssessmentRecord | null> {
        await this.executeQuery('update_assessment');

        const assessment = this.assessments.get(assessmentId);
        if (!assessment) {
            return null;
        }

        // Check optimistic locking
        if (expectedVersion && assessment.version !== expectedVersion) {
            throw new Error(`Optimistic lock failed. Expected version ${expectedVersion}, got ${assessment.version}`);
        }

        const updatedAssessment = {
            ...assessment,
            ...updates,
            version: assessment.version + 1,
            updated_at: new Date()
        };

        this.assessments.set(assessmentId, updatedAssessment);
        return updatedAssessment;
    }

    /**
     * Delete an assessment
     */
    async deleteAssessment(assessmentId: string): Promise<boolean> {
        await this.executeQuery('delete_assessment');
        return this.assessments.delete(assessmentId);
    }

    /**
     * List all assessments
     */
    async listAssessments(filters?: {
        state?: string[];
        limit?: number;
        offset?: number;
        sortBy?: string;
        sortOrder?: 'asc' | 'desc';
    }): Promise<{ assessments: MockAssessmentRecord[]; total: number }> {
        await this.executeQuery('list_assessments');

        let assessments = Array.from(this.assessments.values());

        // Apply filters
        if (filters?.state && filters.state.length > 0) {
            assessments = assessments.filter(a => filters!.state!.includes(a.state));
        }

        // Apply sorting
        if (filters?.sortBy) {
            assessments.sort((a, b) => {
                const aValue = a[filters.sortBy as keyof MockAssessmentRecord];
                const bValue = b[filters.sortBy as keyof MockAssessmentRecord];

                if (aValue < bValue) return filters!.sortOrder === 'asc' ? -1 : 1;
                if (aValue > bValue) return filters!.sortOrder === 'asc' ? 1 : -1;
                return 0;
            });
        }

        // Apply pagination
        const total = assessments.length;
        if (filters?.limit !== undefined) {
            const offset = filters.offset || 0;
            assessments = assessments.slice(offset, offset + filters.limit);
        }

        return { assessments, total };
    }

    /**
     * Get assessments by state
     */
    async getAssessmentsByState(state: string): Promise<MockAssessmentRecord[]> {
        await this.executeQuery('get_assessments_by_state');
        return Array.from(this.assessments.values()).filter(a => a.state === state);
    }

    /**
     * Get pending assessments
     */
    async getPendingAssessments(): Promise<MockAssessmentRecord[]> {
        return this.getAssessmentsByState('pending');
    }

    /**
     * Get processing assessments
     */
    async getProcessingAssessments(): Promise<MockAssessmentRecord[]> {
        return this.getAssessmentsByState('processing');
    }

    /**
     * Get completed assessments
     */
    async getCompletedAssessments(): Promise<MockAssessmentRecord[]> {
        return this.getAssessmentsByState('completed');
    }

    /**
     * Get failed assessments
     */
    async getFailedAssessments(): Promise<MockAssessmentRecord[]> {
        return this.getAssessmentsByState('failed');
    }

    /**
     * Get assessments by priority
     */
    async getAssessmentsByPriority(minPriority: number = 1): Promise<MockAssessmentRecord[]> {
        await this.executeQuery('get_assessments_by_priority');
        return Array.from(this.assessments.values()).filter(a => a.priority >= minPriority);
    }

    /**
     * Get high priority assessments
     */
    async getHighPriorityAssessments(): Promise<MockAssessmentRecord[]> {
        return this.getAssessmentsByPriority(8);
    }

    /**
     * Cleanup old assessments
     */
    async cleanupOldAssessments(retentionDays: number = 30): Promise<{ deleted: number; remaining: number }> {
        await this.executeQuery('cleanup_old_assessments');

        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - retentionDays);

        let deletedCount = 0;
        for (const [assessmentId, assessment] of this.assessments.entries()) {
            if (assessment.completed_at && assessment.completed_at < cutoffDate) {
                this.assessments.delete(assessmentId);
                deletedCount++;
            }
        }

        return {
            deleted: deletedCount,
            remaining: this.assessments.size
        };
    }

    /**
     * Get assessment statistics
     */
    async getAssessmentStats(): Promise<{
        total: number;
        by_state: Record<string, number>;
        by_priority: Record<string, number>;
        average_processing_time: number;
        success_rate: number;
    }> {
        await this.executeQuery('get_assessment_stats');

        const assessments = Array.from(this.assessments.values());
        const byState: Record<string, number> = {};
        const byPriority: Record<string, number> = {};

        assessments.forEach(assessment => {
            byState[assessment.state] = (byState[assessment.state] || 0) + 1;
            byPriority[`priority_${assessment.priority}`] = (byPriority[`priority_${assessment.priority}`] || 0) + 1;
        });

        const completed = assessments.filter(a => a.state === 'completed');
        const successRate = assessments.length > 0 ? completed.length / assessments.length : 0;

        return {
            total: assessments.length,
            by_state: byState,
            by_priority: byPriority,
            average_processing_time: 0, // Mock implementation
            success_rate: successRate
        };
    }

    /**
     * Check database health
     */
    async healthCheck(): Promise<{
        connected: boolean;
        active_connections: number;
        total_connections: number;
        success_rate: number;
        response_time: number;
        last_check: Date;
    }> {
        const responseTime = this.config.query_delay;
        const successRate = this.totalConnections > 0
            ? this.successfulConnections / this.totalConnections
            : 1;

        return {
            connected: this.isConnected,
            active_connections: this.activeConnections,
            total_connections: this.totalConnections,
            success_rate: successRate,
            response_time: responseTime,
            last_check: new Date()
        };
    }

    /**
     * Execute a query (simulated)
     */
    private async executeQuery(queryType: string): Promise<MockQueryResult> {
        const queryId = `query-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const startTime = Date.now();

        try {
            // Simulate query delay
            await new Promise(resolve => setTimeout(resolve, this.config.query_delay));

            // Simulate query failure
            if (Math.random() < this.config.failure_rate) {
                this.recordQuery(queryId, queryType, startTime, false, 'Query failed');
                throw new Error('Database query failed');
            }

            this.recordQuery(queryId, queryType, startTime, true);

            return {
                success: true,
                data: {},
                duration: Date.now() - startTime
            };

        } catch (error) {
            this.recordQuery(
                queryId,
                queryType,
                startTime,
                false,
                error instanceof Error ? error.message : String(error)
            );
            throw error;
        }
    }

    /**
     * Record query in history
     */
    private recordQuery(
        queryId: string,
        queryType: string,
        startTime: number,
        success: boolean,
        error?: string
    ): void {
        const duration = Date.now() - startTime;
        this.queryHistory.push({
            id: queryId,
            timestamp: new Date(),
            query: queryType,
            duration,
            success,
            error
        });

        // Keep only last 1000 queries
        if (this.queryHistory.length > 1000) {
            this.queryHistory = this.queryHistory.slice(-1000);
        }
    }

    /**
     * Record connection in history
     */
    private recordConnection(
        connectionId: string,
        startTime: number,
        success: boolean,
        error?: string
    ): void {
        const duration = Date.now() - startTime;
        this.connectionHistory.push({
            id: connectionId,
            timestamp: new Date(),
            duration,
            success,
            error
        });

        // Keep only last 100 connections
        if (this.connectionHistory.length > 100) {
            this.connectionHistory = this.connectionHistory.slice(-100);
        }
    }

    /**
     * Get connection statistics
     */
    getConnectionStats(): {
        total_connections: number;
        successful_connections: number;
        failed_connections: number;
        active_connections: number;
        success_rate: number;
        average_connection_time: number;
    } {
        const totalConnectionTime = this.connectionHistory.reduce((sum, conn) => sum + conn.duration, 0);
        const averageConnectionTime = this.connectionHistory.length > 0
            ? totalConnectionTime / this.connectionHistory.length
            : 0;

        return {
            total_connections: this.totalConnections,
            successful_connections: this.successfulConnections,
            failed_connections: this.failedConnections,
            active_connections: this.activeConnections,
            success_rate: this.totalConnections > 0 ? this.successfulConnections / this.totalConnections : 0,
            average_connection_time: averageConnectionTime
        };
    }

    /**
     * Get query statistics
     */
    getQueryStats(): {
        total_queries: number;
        successful_queries: number;
        failed_queries: number;
        average_query_time: number;
        slowest_query: number;
    } {
        const successfulQueries = this.queryHistory.filter(q => q.success).length;
        const failedQueries = this.queryHistory.filter(q => !q.success).length;
        const totalQueryTime = this.queryHistory.reduce((sum, q) => sum + q.duration, 0);
        const averageQueryTime = this.queryHistory.length > 0
            ? totalQueryTime / this.queryHistory.length
            : 0;
        const slowestQuery = this.queryHistory.length > 0
            ? Math.max(...this.queryHistory.map(q => q.duration))
            : 0;

        return {
            total_queries: this.queryHistory.length,
            successful_queries: successfulQueries,
            failed_queries: failedQueries,
            average_query_time: averageQueryTime,
            slowest_query: slowestQuery
        };
    }

    /**
     * Get query history
     */
    getQueryHistory(): Array<{
        id: string;
        timestamp: Date;
        query: string;
        duration: number;
        success: boolean;
        error?: string;
    }> {
        return [...this.queryHistory];
    }

    /**
     * Clear query history
     */
    clearHistory(): void {
        this.queryHistory = [];
        this.connectionHistory = [];
    }

    /**
     * Reset all data and statistics
     */
    reset(): void {
        this.assessments.clear();
        this.activeConnections = 0;
        this.totalConnections = 0;
        this.successfulConnections = 0;
        this.failedConnections = 0;
        this.isConnected = false;
        this.connectionError = null;
        this.queryHistory = [];
        this.connectionHistory = [];
        this.initializeTestData();
    }

    /**
     * Simulate database overload
     */
    simulateOverload(duration: number = 5000): void {
        this.config.failure_rate = 0.5;
        setTimeout(() => {
            this.config.failure_rate = 0;
        }, duration);
    }

    /**
     * Simulate database timeout
     */
    simulateTimeout(duration: number = 3000): void {
        this.config.timeout_rate = 1;
        setTimeout(() => {
            this.config.timeout_rate = 0;
        }, duration);
    }

    /**
     * Get current connection status
     */
    isConnectionHealthy(): boolean {
        return this.isConnected && this.connectionError === null;
    }

    /**
     * Get current connection error
     */
    getConnectionError(): Error | null {
        return this.connectionError;
    }

    /**
     * Get assessment count
     */
    getAssessmentCount(): number {
        return this.assessments.size;
    }

    /**
     * Get all assessments
     */
    async getAllAssessments(): Promise<MockAssessmentRecord[]> {
        return Array.from(this.assessments.values());
    }
}

// Export default instance
export const mockDatabaseService = new MockDatabaseService();