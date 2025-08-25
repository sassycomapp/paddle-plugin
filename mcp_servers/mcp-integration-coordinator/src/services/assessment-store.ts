/**
 * MCP Integration Coordinator - Assessment Store Service
 *
 * Provides Promise-based state management for assessments, replacing
 * the event-driven approach with direct state queries and coordination.
 */

import { EventEmitter } from 'events';
import {
    AssessmentStoreConfig,
    AssessmentState,
    AssessmentStateData,
    AssessmentStoreCreateOptions,
    AssessmentStoreStatistics,
    AssessmentStoreRetryInfo,
    AssessmentRequest,
    AssessmentResult,
    AssessmentProcessingError,
    AssessmentStateTransitionError,
    AssessmentNotFoundError,
    AssessmentTimeoutError,
    AssessmentExecutionError,
    AssessmentStatusError,
    AssessmentCancellationError
} from '../types';
import { Logger } from '../logger';
import { DatabaseService } from './database-service';
import { AuditService } from './audit-service';
import { AssessmentStoreDAO, AssessmentFilters, AssessmentUpdateOptions } from './assessment-store-dao';

export class AssessmentStore extends EventEmitter {
    private config: AssessmentStoreConfig;
    private logger: Logger;
    private databaseService: DatabaseService;
    private auditService: AuditService;
    private dao: AssessmentStoreDAO;
    private activeAssessments: Map<string, AssessmentStateData> = new Map();
    private assessmentTimeouts: Map<string, NodeJS.Timeout> = new Map();
    private isInitialized: boolean = false;

    constructor(
        config: AssessmentStoreConfig,
        logger: Logger,
        databaseService: DatabaseService,
        auditService: AuditService
    ) {
        super();
        this.config = config;
        this.logger = logger;
        this.databaseService = databaseService;
        this.auditService = auditService;
        this.dao = new AssessmentStoreDAO(databaseService, logger);

        this.logger.info('AssessmentStore initialized', {
            config: this.config.processing,
            complianceServer: this.config.complianceServer
        });
    }

    /**
     * Initialize the AssessmentStore with database connection
     */
    public async initialize(): Promise<void> {
        try {
            this.logger.info('Initializing AssessmentStore with database persistence');

            // Initialize DAO
            await this.dao.initialize();

            // Load pending assessments from database
            await this.loadPendingAssessments();

            this.isInitialized = true;
            this.logger.info('AssessmentStore initialized successfully with database persistence');
        } catch (error) {
            this.logger.error('Failed to initialize AssessmentStore', error as Error);
            throw new AssessmentProcessingError(
                `Failed to initialize AssessmentStore: ${error instanceof Error ? error.message : 'Unknown error'}`,
                undefined,
                'INIT_FAILED'
            );
        }
    }

    /**
     * Create a new assessment
     */
    public async createAssessment(options: AssessmentStoreCreateOptions): Promise<string> {
        try {
            if (!this.isInitialized) {
                await this.initialize();
            }

            const assessmentId = await this.dao.createAssessment(options);

            // Store in memory for quick access
            const assessmentData = await this.dao.getAssessment(assessmentId);
            this.activeAssessments.set(assessmentId, assessmentData);

            this.logger.info('Assessment created', { assessmentId, assessmentType: options.assessmentType });

            return assessmentId;
        } catch (error) {
            this.logger.error('Failed to create assessment', error as Error);
            throw new AssessmentProcessingError(
                `Failed to create assessment: ${error instanceof Error ? error.message : 'Unknown error'}`,
                undefined,
                'CREATE_FAILED'
            );
        }
    }

    /**
     * Wait for assessment completion with timeout
     */
    public async waitForCompletion(assessmentId: string, timeout: number = 30000): Promise<AssessmentResult | null> {
        try {
            if (!this.isInitialized) {
                await this.initialize();
            }

            const startTime = Date.now();

            // Check memory first for performance
            let assessmentData = this.activeAssessments.get(assessmentId);
            if (!assessmentData) {
                assessmentData = await this.dao.getAssessment(assessmentId);
                this.activeAssessments.set(assessmentId, assessmentData);
            }

            // Check if already completed
            if (assessmentData.state === AssessmentState.COMPLETED) {
                return assessmentData.resultData || null;
            }

            if (assessmentData.state === AssessmentState.FAILED) {
                throw new AssessmentExecutionError(
                    `Assessment failed: ${assessmentData.errorMessage || 'Unknown error'}`,
                    assessmentId
                );
            }

            return new Promise((resolve, reject) => {
                const timeoutId = setTimeout(() => {
                    this.assessmentTimeouts.delete(assessmentId);
                    reject(new AssessmentTimeoutError(assessmentId, timeout));
                }, timeout);

                const checkCompletion = async () => {
                    try {
                        // Refresh assessment data from database
                        assessmentData = await this.dao.getAssessment(assessmentId);
                        this.activeAssessments.set(assessmentId, assessmentData);

                        if (assessmentData.state === AssessmentState.COMPLETED) {
                            clearTimeout(timeoutId);
                            this.assessmentTimeouts.delete(assessmentId);
                            resolve(assessmentData.resultData || null);
                        } else if (assessmentData.state === AssessmentState.FAILED) {
                            clearTimeout(timeoutId);
                            this.assessmentTimeouts.delete(assessmentId);
                            reject(new AssessmentExecutionError(
                                `Assessment failed: ${assessmentData.errorMessage || 'Unknown error'}`,
                                assessmentId
                            ));
                        } else if (Date.now() - startTime >= timeout) {
                            clearTimeout(timeoutId);
                            this.assessmentTimeouts.delete(assessmentId);
                            reject(new AssessmentTimeoutError(assessmentId, timeout));
                        } else {
                            // Check again in 500ms
                            setTimeout(checkCompletion, 500);
                        }
                    } catch (error) {
                        clearTimeout(timeoutId);
                        this.assessmentTimeouts.delete(assessmentId);
                        reject(error);
                    }
                };

                this.assessmentTimeouts.set(assessmentId, timeoutId);
                checkCompletion();
            });
        } catch (error) {
            this.logger.error('Failed to wait for assessment completion', error as Error, { assessmentId });
            throw error;
        }
    }

    /**
     * Get assessment state
     */
    public async getState(assessmentId: string): Promise<{
        assessmentId: string;
        state: AssessmentState;
        progress: number;
        message?: string;
        lastUpdated: string;
        completedAt?: string;
    }> {
        try {
            if (!this.isInitialized) {
                await this.initialize();
            }

            // Check memory first for performance
            let assessmentData = this.activeAssessments.get(assessmentId);
            if (!assessmentData) {
                assessmentData = await this.dao.getAssessment(assessmentId);
                this.activeAssessments.set(assessmentId, assessmentData);
            }

            return {
                assessmentId: assessmentData.assessmentId,
                state: assessmentData.state,
                progress: assessmentData.progress,
                message: assessmentData.message,
                lastUpdated: assessmentData.updatedAt,
                completedAt: assessmentData.completedAt
            };
        } catch (error) {
            this.logger.error('Failed to get assessment state', error as Error, { assessmentId });
            throw error;
        }
    }

    /**
     * List assessments with optional filtering
     */
    public async listAssessments(
        state?: AssessmentState,
        limit: number = 100,
        offset: number = 0
    ): Promise<AssessmentStateData[]> {
        try {
            if (!this.isInitialized) {
                await this.initialize();
            }

            const filters: AssessmentFilters = {
                state,
                limit,
                offset,
                orderBy: 'created_at',
                orderDirection: 'DESC'
            };

            return await this.dao.listAssessments(filters);
        } catch (error) {
            this.logger.error('Failed to list assessments', error as Error);
            throw new AssessmentProcessingError(
                `Failed to list assessments: ${error instanceof Error ? error.message : 'Unknown error'}`,
                undefined,
                'LIST_FAILED'
            );
        }
    }

    /**
     * Cancel an assessment
     */
    public async cancelAssessment(assessmentId: string, reason: string = 'User requested cancellation'): Promise<void> {
        try {
            if (!this.isInitialized) {
                await this.initialize();
            }

            const assessmentData = this.activeAssessments.get(assessmentId);
            let currentVersion: number | undefined;

            if (assessmentData) {
                currentVersion = assessmentData.version;
            }

            // Check if assessment can be cancelled
            const currentState = assessmentData?.state || (await this.dao.getAssessment(assessmentId)).state;
            if (currentState === AssessmentState.COMPLETED ||
                currentState === AssessmentState.FAILED ||
                currentState === AssessmentState.CANCELLED) {
                this.logger.warn('Cannot cancel assessment in current state', {
                    assessmentId,
                    currentState
                });
                return;
            }

            // Update assessment state in database
            const updateOptions: AssessmentUpdateOptions = {
                state: AssessmentState.CANCELLED,
                message: `Assessment cancelled: ${reason}`,
                changedBy: 'system',
                changeReason: reason,
                changeAction: 'cancel'
            };

            await this.dao.updateAssessment(assessmentId, updateOptions, currentVersion);

            // Update memory cache
            const updatedData = await this.dao.getAssessment(assessmentId);
            this.activeAssessments.set(assessmentId, updatedData);

            // Clear any pending timeout
            const timeoutId = this.assessmentTimeouts.get(assessmentId);
            if (timeoutId) {
                clearTimeout(timeoutId);
                this.assessmentTimeouts.delete(assessmentId);
            }

            this.logger.info('Assessment cancelled', { assessmentId, reason });

            // Emit cancellation event for backward compatibility
            this.emit('assessment.cancelled', { assessmentId, reason });
        } catch (error) {
            this.logger.error('Failed to cancel assessment', error as Error, { assessmentId });
            throw error;
        }
    }

    /**
     * Get assessment statistics
     */
    public async getStatistics(): Promise<AssessmentStoreStatistics> {
        try {
            if (!this.isInitialized) {
                await this.initialize();
            }

            return await this.dao.getAssessmentStatistics();
        } catch (error) {
            this.logger.error('Failed to get assessment statistics', error as Error);
            throw new AssessmentProcessingError(
                `Failed to get statistics: ${error instanceof Error ? error.message : 'Unknown error'}`,
                undefined,
                'STATISTICS_FAILED'
            );
        }
    }

    /**
     * Update assessment state
     */
    public async updateState(
        assessmentId: string,
        state: AssessmentState,
        result?: AssessmentResult,
        message?: string
    ): Promise<void> {
        try {
            if (!this.isInitialized) {
                await this.initialize();
            }

            const assessmentData = this.activeAssessments.get(assessmentId);
            let currentVersion: number | undefined;

            if (assessmentData) {
                currentVersion = assessmentData.version;
            }

            // Validate state transition
            const currentState = assessmentData?.state || (await this.dao.getAssessment(assessmentId)).state;
            this.validateStateTransition(currentState, state);

            // Build update options
            const updateOptions: AssessmentUpdateOptions = {
                state,
                message,
                resultData: result,
                changedBy: 'system',
                changeAction: 'state_update'
            };

            // Set completed timestamp for terminal states
            if (state === AssessmentState.COMPLETED || state === AssessmentState.FAILED || state === AssessmentState.CANCELLED) {
                updateOptions.changedBy = 'system';
                updateOptions.changeReason = message || `State changed to ${state}`;
            }

            // Update assessment state in database
            await this.dao.updateAssessment(assessmentId, updateOptions, currentVersion);

            // Update memory cache
            const updatedData = await this.dao.getAssessment(assessmentId);
            this.activeAssessments.set(assessmentId, updatedData);

            // Clear timeout for completed/failed/cancelled assessments
            if (state === AssessmentState.COMPLETED || state === AssessmentState.FAILED || state === AssessmentState.CANCELLED) {
                const timeoutId = this.assessmentTimeouts.get(assessmentId);
                if (timeoutId) {
                    clearTimeout(timeoutId);
                    this.assessmentTimeouts.delete(assessmentId);
                }
            }

            this.logger.debug('Assessment state updated', { assessmentId, state, progress: updatedData.progress });

            // Emit state change event for backward compatibility
            this.emit('assessment.stateChanged', { assessmentId, state, progress: updatedData.progress });
        } catch (error) {
            this.logger.error('Failed to update assessment state', error as Error, { assessmentId, state });
            throw error;
        }
    }

    /**
     * Get assessment data for processing
     */
    public async getAssessmentData(assessmentId: string): Promise<AssessmentStateData> {
        try {
            if (!this.isInitialized) {
                await this.initialize();
            }

            // Check memory first for performance
            let assessmentData = this.activeAssessments.get(assessmentId);
            if (!assessmentData) {
                assessmentData = await this.dao.getAssessment(assessmentId);
                this.activeAssessments.set(assessmentId, assessmentData);
            }

            return assessmentData;
        } catch (error) {
            this.logger.error('Failed to get assessment data', error as Error, { assessmentId });
            throw error;
        }
    }

    /**
     * Get assessments that need retry
     */
    public async getAssessmentsForRetry(): Promise<AssessmentStoreRetryInfo[]> {
        try {
            if (!this.isInitialized) {
                await this.initialize();
            }

            return await this.dao.getAssessmentsForRetry(this.config.processing.maxRetries);
        } catch (error) {
            this.logger.error('Failed to get assessments for retry', error as Error);
            throw new AssessmentProcessingError(
                `Failed to get retry assessments: ${error instanceof Error ? error.message : 'Unknown error'}`,
                undefined,
                'RETRY_LIST_FAILED'
            );
        }
    }

    /**
     * Persist assessment to database (deprecated - use DAO directly)
     */
    private async persistAssessment(assessmentData: AssessmentStateData): Promise<void> {
        try {
            // Use DAO for persistence
            const updateOptions: AssessmentUpdateOptions = {
                state: assessmentData.state,
                progress: assessmentData.progress,
                message: assessmentData.message,
                resultData: assessmentData.resultData,
                errorMessage: assessmentData.errorMessage,
                retryCount: assessmentData.retryCount,
                nextRetryAt: assessmentData.nextRetryAt
            };

            await this.dao.updateAssessment(
                assessmentData.assessmentId,
                updateOptions,
                assessmentData.version - 1
            );
        } catch (error) {
            this.logger.error('Failed to persist assessment', error as Error, { assessmentId: assessmentData.assessmentId });
            // Don't throw here as this is an internal operation
        }
    }

    /**
     * Validate state transition
     */
    private validateStateTransition(fromState: AssessmentState, toState: AssessmentState): void {
        const validTransitions: Record<AssessmentState, AssessmentState[]> = {
            [AssessmentState.PENDING]: [AssessmentState.PROCESSING, AssessmentState.CANCELLED],
            [AssessmentState.PROCESSING]: [AssessmentState.COMPLETED, AssessmentState.FAILED, AssessmentState.CANCELLED],
            [AssessmentState.COMPLETED]: [],
            [AssessmentState.FAILED]: [AssessmentState.PROCESSING], // Retry
            [AssessmentState.CANCELLED]: []
        };

        const validNextStates = validTransitions[fromState];
        if (!validNextStates.includes(toState)) {
            throw new AssessmentStateTransitionError(fromState, toState);
        }
    }

    /**
     * Load pending assessments from database
     */
    public async loadPendingAssessments(): Promise<void> {
        try {
            const assessments = await this.dao.loadPendingAssessments();

            for (const assessmentData of assessments) {
                this.activeAssessments.set(assessmentData.assessmentId, assessmentData);
            }

            this.logger.info('Loaded pending assessments from database', {
                count: assessments.length
            });
        } catch (error) {
            this.logger.error('Failed to load pending assessments', error as Error);
            throw new AssessmentProcessingError(
                `Failed to load pending assessments: ${error instanceof Error ? error.message : 'Unknown error'}`,
                undefined,
                'LOAD_FAILED'
            );
        }
    }

    /**
     * Cleanup completed assessments older than specified time
     */
    public async cleanupOldAssessments(maxAge: number = 7 * 24 * 60 * 60 * 1000): Promise<void> {
        try {
            const retentionDays = Math.floor(maxAge / (24 * 60 * 60 * 1000));
            const deletedCount = await this.dao.cleanupOldAssessments(retentionDays);

            // Remove from memory
            for (const [assessmentId, assessmentData] of this.activeAssessments.entries()) {
                if (assessmentData.completedAt && new Date(assessmentData.completedAt).getTime() < Date.now() - maxAge) {
                    this.activeAssessments.delete(assessmentId);
                }
            }

            this.logger.info('Cleaned up old assessments', {
                maxAge,
                retentionDays,
                cleanedCount: deletedCount
            });
        } catch (error) {
            this.logger.error('Failed to cleanup old assessments', error as Error);
            throw new AssessmentProcessingError(
                `Failed to cleanup old assessments: ${error instanceof Error ? error.message : 'Unknown error'}`,
                undefined,
                'CLEANUP_FAILED'
            );
        }
    }

    /**
     * Get audit trail for assessment
     */
    public async getAssessmentAuditTrail(assessmentId: string): Promise<any[]> {
        try {
            if (!this.isInitialized) {
                await this.initialize();
            }

            return await this.dao.getAssessmentAuditTrail(assessmentId);
        } catch (error) {
            this.logger.error('Failed to get assessment audit trail', error as Error, { assessmentId });
            throw new AssessmentProcessingError(
                `Failed to get audit trail: ${error instanceof Error ? error.message : 'Unknown error'}`,
                assessmentId,
                'AUDIT_FAILED'
            );
        }
    }

    /**
     * Close database connections
     */
    public async close(): Promise<void> {
        try {
            await this.dao.close();
            this.logger.info('AssessmentStore closed successfully');
        } catch (error) {
            this.logger.error('Failed to close AssessmentStore', error as Error);
            throw new AssessmentProcessingError(
                `Failed to close AssessmentStore: ${error instanceof Error ? error.message : 'Unknown error'}`,
                undefined,
                'CLOSE_FAILED'
            );
        }
    }
}