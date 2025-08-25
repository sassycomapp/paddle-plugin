/**
 * MCP Integration Coordinator - Assessment Store DAO
 * 
 * Database Access Layer for AssessmentStore operations.
 * Handles all database interactions for assessment state management.
 */

import { Logger } from '../logger';
import { DatabaseService } from './database-service';
import {
    AssessmentState,
    AssessmentStateData,
    AssessmentRequest,
    AssessmentResult,
    AssessmentStoreCreateOptions,
    AssessmentStoreStatistics,
    AssessmentStoreRetryInfo,
    AssessmentProcessingError,
    AssessmentNotFoundError,
    AssessmentStateTransitionError
} from '../types';

export interface AssessmentFilters {
    state?: AssessmentState;
    assessmentId?: string;
    serverName?: string;
    assessmentType?: 'compliance' | 'health' | 'security';
    createdAfter?: string;
    createdBefore?: string;
    limit?: number;
    offset?: number;
    orderBy?: 'created_at' | 'updated_at' | 'priority';
    orderDirection?: 'ASC' | 'DESC';
}

export interface AssessmentUpdateOptions {
    state?: AssessmentState;
    progress?: number;
    message?: string;
    resultData?: AssessmentResult;
    errorMessage?: string;
    retryCount?: number;
    nextRetryAt?: string;
    changedBy?: string;
    changeReason?: string;
    changeAction?: string;
}

export class AssessmentStoreDAO {
    private databaseService: DatabaseService;
    private logger: Logger;
    private connectionPool: any;

    constructor(databaseService: DatabaseService, logger: Logger) {
        this.databaseService = databaseService;
        this.logger = logger;
    }

    /**
     * Initialize connection pool and database schema
     */
    public async initialize(): Promise<void> {
        try {
            this.logger.info('Initializing AssessmentStore DAO');

            // Initialize connection pool
            await this.initializeConnectionPool();

            // Verify database schema
            await this.verifySchema();

            this.logger.info('AssessmentStore DAO initialized successfully');
        } catch (error) {
            this.logger.error('Failed to initialize AssessmentStore DAO', error as Error);
            throw new AssessmentProcessingError(
                `Failed to initialize DAO: ${error instanceof Error ? error.message : 'Unknown error'}`,
                undefined,
                'DAO_INIT_FAILED'
            );
        }
    }

    /**
     * Create a new assessment
     */
    public async createAssessment(
        options: AssessmentStoreCreateOptions,
        assessmentId?: string
    ): Promise<string> {
        try {
            const id = assessmentId || `assessment_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            const timestamp = new Date().toISOString();

            const requestData: AssessmentRequest = {
                requestId: options.requestId || id,
                serverName: options.serverName,
                assessmentType: options.assessmentType,
                options: options.options,
                timestamp,
                source: options.source
            };

            const query = `
                INSERT INTO assessment_states (
                    assessment_id, state, version, progress, message, 
                    created_at, updated_at, request_data, priority, timeout_seconds
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (assessment_id) DO UPDATE SET
                    state = $2,
                    version = $3,
                    progress = $4,
                    message = $5,
                    updated_at = $7,
                    request_data = $8
                RETURNING id
            `;

            const values = [
                id,
                AssessmentState.PENDING,
                1,
                0,
                'Assessment created and pending processing',
                timestamp,
                timestamp,
                JSON.stringify(requestData),
                options.options.priority || 5,
                options.options.timeout || 300
            ];

            const result = await this.databaseService.query(query, values);

            if (result.rows.length === 0) {
                throw new AssessmentProcessingError(
                    `Failed to create assessment: ${id}`,
                    id,
                    'CREATE_FAILED'
                );
            }

            this.logger.info('Assessment created in database', { assessmentId: id });
            return id;
        } catch (error) {
            this.logger.error('Failed to create assessment in database', error as Error, {
                assessmentId: assessmentId
            });
            throw new AssessmentProcessingError(
                `Failed to create assessment: ${error instanceof Error ? error.message : 'Unknown error'}`,
                assessmentId,
                'CREATE_FAILED'
            );
        }
    }

    /**
     * Get assessment by ID
     */
    public async getAssessment(assessmentId: string): Promise<AssessmentStateData> {
        try {
            const query = `
                SELECT assessment_id, state, version, progress, message, 
                       created_at, updated_at, completed_at, request_data, 
                       result_data, error_message, retry_count, next_retry_at
                FROM assessment_states 
                WHERE assessment_id = $1
            `;

            const result = await this.databaseService.query(query, [assessmentId]);

            if (result.rows.length === 0) {
                throw new AssessmentNotFoundError(assessmentId);
            }

            const row = result.rows[0];
            return this.mapRowToAssessmentStateData(row);
        } catch (error) {
            this.logger.error('Failed to get assessment from database', error as Error, { assessmentId });
            if (error instanceof AssessmentNotFoundError) {
                throw error;
            }
            throw new AssessmentProcessingError(
                `Failed to get assessment: ${error instanceof Error ? error.message : 'Unknown error'}`,
                assessmentId,
                'GET_FAILED'
            );
        }
    }

    /**
     * Update assessment state
     */
    public async updateAssessment(
        assessmentId: string,
        options: AssessmentUpdateOptions,
        currentVersion?: number
    ): Promise<number> {
        try {
            const timestamp = new Date().toISOString();
            let version = currentVersion;

            // Build update query dynamically
            const updates: string[] = [];
            const values: any[] = [];
            let paramIndex = 1;

            // Always update updated_at
            updates.push(`updated_at = $${paramIndex++}`);
            values.push(timestamp);

            // Add optional updates
            if (options.state !== undefined) {
                updates.push(`state = $${paramIndex++}`);
                values.push(options.state);
            }

            if (options.progress !== undefined) {
                updates.push(`progress = $${paramIndex++}`);
                values.push(options.progress);
            }

            if (options.message !== undefined) {
                updates.push(`message = $${paramIndex++}`);
                values.push(options.message);
            }

            if (options.resultData !== undefined) {
                updates.push(`result_data = $${paramIndex++}`);
                values.push(JSON.stringify(options.resultData));
            }

            if (options.errorMessage !== undefined) {
                updates.push(`error_message = $${paramIndex++}`);
                values.push(options.errorMessage);
            }

            if (options.retryCount !== undefined) {
                updates.push(`retry_count = $${paramIndex++}`);
                values.push(options.retryCount);
            }

            if (options.nextRetryAt !== undefined) {
                updates.push(`next_retry_at = $${paramIndex++}`);
                values.push(options.nextRetryAt);
            }

            // Handle completed timestamp
            if (options.state && ['completed', 'failed', 'cancelled'].includes(options.state)) {
                updates.push(`completed_at = $${paramIndex++}`);
                values.push(timestamp);
            }

            // Handle version increment
            if (currentVersion !== undefined) {
                updates.push(`version = $${paramIndex++}`);
                values.push(currentVersion + 1);
                version = currentVersion + 1;
            }

            // Add audit context if provided
            if (options.changedBy || options.changeReason || options.changeAction) {
                const context: any = {};
                if (options.changedBy) context.changed_by = options.changedBy;
                if (options.changeReason) context.change_reason = options.changeReason;
                if (options.changeAction) context.change_action = options.changeAction;

                updates.push(`request_data = jsonb_set(request_data, '{audit}', $${paramIndex++}, true)`);
                values.push(JSON.stringify(context));
            }

            const query = `
                UPDATE assessment_states 
                SET ${updates.join(', ')}
                WHERE assessment_id = $${paramIndex++}
                ${currentVersion !== undefined ? `AND version = $${paramIndex++}` : ''}
                RETURNING version
            `;

            values.push(assessmentId);
            if (currentVersion !== undefined) {
                values.push(currentVersion);
            }

            const result = await this.databaseService.query(query, values);

            if (result.rows.length === 0) {
                throw new AssessmentProcessingError(
                    `Assessment not found or version mismatch: ${assessmentId}`,
                    assessmentId,
                    'UPDATE_FAILED'
                );
            }

            this.logger.debug('Assessment updated in database', {
                assessmentId,
                version: result.rows[0].version
            });

            return result.rows[0].version;
        } catch (error) {
            this.logger.error('Failed to update assessment in database', error as Error, { assessmentId });
            if (error instanceof AssessmentProcessingError && error.code === 'UPDATE_FAILED') {
                throw error;
            }
            throw new AssessmentProcessingError(
                `Failed to update assessment: ${error instanceof Error ? error.message : 'Unknown error'}`,
                assessmentId,
                'UPDATE_FAILED'
            );
        }
    }

    /**
     * List assessments with filtering and pagination
     */
    public async listAssessments(filters: AssessmentFilters = {}): Promise<AssessmentStateData[]> {
        try {
            let query = `
                SELECT assessment_id, state, version, progress, message, 
                       created_at, updated_at, completed_at, request_data, 
                       result_data, error_message, retry_count, next_retry_at
                FROM assessment_states
            `;

            const values: any[] = [];
            const conditions: string[] = [];

            // Add filters
            if (filters.state) {
                conditions.push(`state = $${values.length + 1}`);
                values.push(filters.state);
            }

            if (filters.assessmentId) {
                conditions.push(`assessment_id = $${values.length + 1}`);
                values.push(filters.assessmentId);
            }

            if (filters.serverName) {
                conditions.push(`request_data->>'serverName' = $${values.length + 1}`);
                values.push(filters.serverName);
            }

            if (filters.assessmentType) {
                conditions.push(`request_data->>'assessmentType' = $${values.length + 1}`);
                values.push(filters.assessmentType);
            }

            if (filters.createdAfter) {
                conditions.push(`created_at >= $${values.length + 1}`);
                values.push(filters.createdAfter);
            }

            if (filters.createdBefore) {
                conditions.push(`created_at <= $${values.length + 1}`);
                values.push(filters.createdBefore);
            }

            // Add WHERE clause if there are conditions
            if (conditions.length > 0) {
                query += ` WHERE ${conditions.join(' AND ')}`;
            }

            // Add ORDER BY
            const orderBy = filters.orderBy || 'created_at';
            const orderDirection = filters.orderDirection || 'DESC';
            query += ` ORDER BY ${orderBy} ${orderDirection}`;

            // Add LIMIT and OFFSET
            if (filters.limit !== undefined) {
                query += ` LIMIT $${values.length + 1}`;
                values.push(filters.limit);
            }

            if (filters.offset !== undefined) {
                query += ` OFFSET $${values.length + 1}`;
                values.push(filters.offset);
            }

            const result = await this.databaseService.query(query, values);
            return result.rows.map(row => this.mapRowToAssessmentStateData(row));
        } catch (error) {
            this.logger.error('Failed to list assessments from database', error as Error);
            throw new AssessmentProcessingError(
                `Failed to list assessments: ${error instanceof Error ? error.message : 'Unknown error'}`,
                undefined,
                'LIST_FAILED'
            );
        }
    }

    /**
     * Delete assessment (soft delete)
     */
    public async deleteAssessment(assessmentId: string): Promise<boolean> {
        try {
            const query = `
                UPDATE assessment_states 
                SET state = 'cancelled', 
                    message = 'Soft deleted',
                    completed_at = NOW(),
                    updated_at = NOW()
                WHERE assessment_id = $1
                RETURNING id
            `;

            const result = await this.databaseService.query(query, [assessmentId]);
            const deleted = result.rows.length > 0;

            if (deleted) {
                this.logger.info('Assessment soft deleted', { assessmentId });
            } else {
                this.logger.warn('Assessment not found for deletion', { assessmentId });
            }

            return deleted;
        } catch (error) {
            this.logger.error('Failed to delete assessment from database', error as Error, { assessmentId });
            throw new AssessmentProcessingError(
                `Failed to delete assessment: ${error instanceof Error ? error.message : 'Unknown error'}`,
                assessmentId,
                'DELETE_FAILED'
            );
        }
    }

    /**
     * Get assessments for retry
     */
    public async getAssessmentsForRetry(maxRetries: number = 3): Promise<AssessmentStoreRetryInfo[]> {
        try {
            const query = `
                SELECT assessment_id, retry_count, next_retry_at, error_message
                FROM assessment_states 
                WHERE state = 'failed' 
                AND retry_count < $1
                AND (next_retry_at IS NULL OR next_retry_at <= NOW())
                ORDER BY retry_count ASC, created_at ASC
            `;

            const result = await this.databaseService.query(query, [maxRetries]);

            return result.rows.map(row => ({
                assessmentId: row.assessment_id,
                retryCount: row.retry_count,
                nextRetryAt: row.next_retry_at,
                errorMessage: row.error_message
            }));
        } catch (error) {
            this.logger.error('Failed to get assessments for retry from database', error as Error);
            throw new AssessmentProcessingError(
                `Failed to get retry assessments: ${error instanceof Error ? error.message : 'Unknown error'}`,
                undefined,
                'RETRY_LIST_FAILED'
            );
        }
    }

    /**
     * Get assessment statistics
     */
    public async getAssessmentStatistics(): Promise<AssessmentStoreStatistics> {
        try {
            const query = `
                SELECT 
                    COUNT(*) as total_assessments,
                    COUNT(CASE WHEN state = 'pending' THEN 1 END) as pending_count,
                    COUNT(CASE WHEN state = 'processing' THEN 1 END) as processing_count,
                    COUNT(CASE WHEN state = 'completed' THEN 1 END) as completed_count,
                    COUNT(CASE WHEN state = 'failed' THEN 1 END) as failed_count,
                    COUNT(CASE WHEN state = 'cancelled' THEN 1 END) as cancelled_count,
                    AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) as avg_processing_time,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '1 hour' THEN 1 END) as recent_assessments
                FROM assessment_states
            `;

            const result = await this.databaseService.query(query);
            const row = result.rows[0];

            return {
                totalAssessments: parseInt(row.total_assessments),
                assessmentsByState: {
                    [AssessmentState.PENDING]: parseInt(row.pending_count),
                    [AssessmentState.PROCESSING]: parseInt(row.processing_count),
                    [AssessmentState.COMPLETED]: parseInt(row.completed_count),
                    [AssessmentState.FAILED]: parseInt(row.failed_count),
                    [AssessmentState.CANCELLED]: parseInt(row.cancelled_count)
                },
                averageProcessingTime: parseFloat(row.avg_processing_time) || 0,
                recentAssessments: parseInt(row.recent_assessments)
            };
        } catch (error) {
            this.logger.error('Failed to get assessment statistics from database', error as Error);
            throw new AssessmentProcessingError(
                `Failed to get statistics: ${error instanceof Error ? error.message : 'Unknown error'}`,
                undefined,
                'STATISTICS_FAILED'
            );
        }
    }

    /**
     * Cleanup old assessments
     */
    public async cleanupOldAssessments(retentionDays: number = 30): Promise<number> {
        try {
            const query = `
                DELETE FROM assessment_states 
                WHERE state IN ('completed', 'failed', 'cancelled') 
                AND completed_at < NOW() - INTERVAL '${retentionDays} days'
                RETURNING id
            `;

            const result = await this.databaseService.query(query);
            const deletedCount = result.rows.length;

            this.logger.info('Cleaned up old assessments', {
                retentionDays,
                deletedCount
            });

            return deletedCount;
        } catch (error) {
            this.logger.error('Failed to cleanup old assessments from database', error as Error);
            throw new AssessmentProcessingError(
                `Failed to cleanup old assessments: ${error instanceof Error ? error.message : 'Unknown error'}`,
                undefined,
                'CLEANUP_FAILED'
            );
        }
    }

    /**
     * Load pending assessments from database
     */
    public async loadPendingAssessments(): Promise<AssessmentStateData[]> {
        try {
            const query = `
                SELECT assessment_id, state, version, progress, message, 
                       created_at, updated_at, completed_at, request_data, 
                       result_data, error_message, retry_count, next_retry_at
                FROM assessment_states 
                WHERE state IN ('pending', 'failed')
                ORDER BY created_at ASC
            `;

            const result = await this.databaseService.query(query);
            return result.rows.map(row => this.mapRowToAssessmentStateData(row));
        } catch (error) {
            this.logger.error('Failed to load pending assessments from database', error as Error);
            throw new AssessmentProcessingError(
                `Failed to load pending assessments: ${error instanceof Error ? error.message : 'Unknown error'}`,
                undefined,
                'LOAD_FAILED'
            );
        }
    }

    /**
     * Get audit trail for assessment
     */
    public async getAssessmentAuditTrail(assessmentId: string): Promise<any[]> {
        try {
            const query = `
                SELECT id, old_state, new_state, version_from, version_to,
                       changed_by, change_reason, change_action, created_at, context
                FROM assessment_state_audit 
                WHERE assessment_id = $1
                ORDER BY created_at ASC
            `;

            const result = await this.databaseService.query(query, [assessmentId]);
            return result.rows;
        } catch (error) {
            this.logger.error('Failed to get assessment audit trail from database', error as Error, { assessmentId });
            throw new AssessmentProcessingError(
                `Failed to get audit trail: ${error instanceof Error ? error.message : 'Unknown error'}`,
                assessmentId,
                'AUDIT_FAILED'
            );
        }
    }

    /**
     * Initialize connection pool
     */
    private async initializeConnectionPool(): Promise<void> {
        // This would typically use a connection pool library like pg-pool
        // For now, we'll rely on the existing DatabaseService
        this.logger.debug('Connection pool initialized');
    }

    /**
     * Verify database schema
     */
    private async verifySchema(): Promise<void> {
        try {
            const query = `
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('assessment_states', 'assessment_state_audit')
            `;

            const result = await this.databaseService.query(query);
            const tables = result.rows.map(row => row.table_name);

            if (tables.length < 2) {
                throw new AssessmentProcessingError(
                    'Database schema verification failed. Required tables are missing.',
                    undefined,
                    'SCHEMA_VERIFICATION_FAILED'
                );
            }

            this.logger.info('Database schema verified successfully');
        } catch (error) {
            this.logger.error('Database schema verification failed', error as Error);
            throw error;
        }
    }

    /**
     * Map database row to AssessmentStateData
     */
    private mapRowToAssessmentStateData(row: any): AssessmentStateData {
        return {
            assessmentId: row.assessment_id,
            state: row.state,
            version: row.version,
            progress: row.progress,
            message: row.message,
            createdAt: row.created_at,
            updatedAt: row.updated_at,
            completedAt: row.completed_at,
            requestData: JSON.parse(row.request_data),
            resultData: row.result_data ? JSON.parse(row.result_data) : undefined,
            errorMessage: row.error_message,
            retryCount: row.retry_count,
            nextRetryAt: row.next_retry_at
        };
    }

    /**
     * Close database connections
     */
    public async close(): Promise<void> {
        try {
            // Close connection pool if implemented
            this.logger.info('AssessmentStore DAO closed successfully');
        } catch (error) {
            this.logger.error('Failed to close AssessmentStore DAO', error as Error);
            throw new AssessmentProcessingError(
                `Failed to close DAO: ${error instanceof Error ? error.message : 'Unknown error'}`,
                undefined,
                'DAO_CLOSE_FAILED'
            );
        }
    }
}