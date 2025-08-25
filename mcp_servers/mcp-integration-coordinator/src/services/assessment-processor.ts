/**
 * MCP Integration Coordinator - Assessment Processor Service
 *
 * Handles background processing of assessments and coordinates with the AssessmentStore
 * for state management and external compliance server communication.
 */

import { EventEmitter } from 'events';
import {
    AssessmentProcessorConfig,
    AssessmentState,
    AssessmentStateData,
    ProcessingQueueItem,
    CircuitBreakerState,
    AssessmentProcessorMetrics,
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
import { AssessmentStore } from './assessment-store';

export class AssessmentProcessor extends EventEmitter {
    private config: AssessmentProcessorConfig;
    private logger: Logger;
    private databaseService: DatabaseService;
    private auditService: AuditService;
    private assessmentStore: AssessmentStore;
    private processingQueue: ProcessingQueueItem[] = [];
    private isProcessing: boolean = false;
    private circuitBreaker: CircuitBreakerState;
    private metrics: AssessmentProcessorMetrics;
    private processingInterval: NodeJS.Timeout | null = null;
    private activeAssessments: Set<string> = new Set();

    constructor(
        config: AssessmentProcessorConfig,
        logger: Logger,
        databaseService: DatabaseService,
        auditService: AuditService,
        assessmentStore: AssessmentStore
    ) {
        super();
        this.config = config;
        this.logger = logger;
        this.databaseService = databaseService;
        this.auditService = auditService;
        this.assessmentStore = assessmentStore;

        // Initialize circuit breaker
        this.circuitBreaker = {
            state: 'closed',
            failureCount: 0
        };

        // Initialize metrics
        this.metrics = {
            totalProcessed: 0,
            successful: 0,
            failed: 0,
            retryCount: 0,
            averageProcessingTime: 0,
            queueSize: 0,
            circuitBreakerState: this.circuitBreaker
        };

        this.logger.info('AssessmentProcessor initialized', {
            config: this.config.processing,
            circuitBreaker: this.config.circuitBreaker
        });
    }

    /**
     * Start the assessment processor
     */
    public async start(): Promise<void> {
        try {
            this.logger.info('Starting AssessmentProcessor');

            // Start processing queue
            this.startProcessingQueue();

            // Start circuit breaker monitoring
            this.startCircuitBreakerMonitoring();

            // Load pending assessments from AssessmentStore
            await this.loadPendingAssessments();

            this.logger.info('AssessmentProcessor started successfully');
        } catch (error) {
            this.logger.error('Failed to start AssessmentProcessor', error as Error);
            throw error;
        }
    }

    /**
     * Stop the assessment processor
     */
    public async stop(): Promise<void> {
        try {
            this.logger.info('Stopping AssessmentProcessor');

            // Stop processing queue
            if (this.processingInterval) {
                clearInterval(this.processingInterval);
                this.processingInterval = null;
            }

            // Wait for current processing to complete
            const maxWaitTime = 30000; // 30 seconds
            const startTime = Date.now();

            while (this.isProcessing && Date.now() - startTime < maxWaitTime) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            // Cancel any active assessments
            for (const assessmentId of this.activeAssessments) {
                await this.cancelAssessment(assessmentId, 'Processor shutdown');
            }

            this.logger.info('AssessmentProcessor stopped successfully');
        } catch (error) {
            this.logger.error('Failed to stop AssessmentProcessor', error as Error);
            throw error;
        }
    }

    /**
     * Process a specific assessment
     */
    public async processAssessment(assessmentId: string): Promise<void> {
        try {
            this.logger.info('Processing assessment', { assessmentId });

            // Check if assessment is already being processed
            if (this.activeAssessments.has(assessmentId)) {
                throw new AssessmentProcessingError(
                    `Assessment ${assessmentId} is already being processed`,
                    assessmentId,
                    'ALREADY_PROCESSING'
                );
            }

            // Get assessment state from AssessmentStore
            const assessmentState = await this.assessmentStore.getState(assessmentId);

            // Add to processing queue
            const queueItem: ProcessingQueueItem = {
                assessmentId,
                priority: 'normal',
                retryCount: 0,
                maxRetries: this.config.processing.maxRetries,
                timeout: this.config.processing.timeout,
                createdAt: new Date().toISOString()
            };

            this.processingQueue.push(queueItem);
            this.metrics.queueSize = this.processingQueue.length;

            this.logger.debug('Assessment added to processing queue', { assessmentId, queueSize: this.processingQueue.length });

            // Trigger processing if not already running
            if (!this.isProcessing) {
                await this.processQueue();
            }

        } catch (error) {
            this.logger.error('Failed to process assessment', error as Error, { assessmentId });
            throw error;
        }
    }

    /**
     * Call compliance server for assessment execution
     */
    private async callComplianceServer(assessmentData: AssessmentStateData): Promise<AssessmentResult> {
        try {
            const startTime = Date.now();

            // Check circuit breaker state
            if (this.circuitBreaker.state === 'open') {
                throw new AssessmentExecutionError(
                    'Compliance server is currently unavailable (circuit breaker open)',
                    assessmentData.assessmentId
                );
            }

            this.logger.debug('Calling compliance server', {
                assessmentId: assessmentData.assessmentId,
                assessmentType: assessmentData.requestData.assessmentType
            });

            // Simulate HTTP call to compliance server
            // In a real implementation, this would use axios or fetch
            const complianceServerUrl = this.config.assessmentStore.complianceServer.baseUrl;
            const apiKey = this.config.assessmentStore.complianceServer.apiKey;

            const response = await fetch(`${complianceServerUrl}/api/assessments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify({
                    assessmentId: assessmentData.assessmentId,
                    ...assessmentData.requestData
                })
            });

            if (!response.ok) {
                throw new AssessmentExecutionError(
                    `Compliance server returned ${response.status}: ${response.statusText}`,
                    assessmentData.assessmentId
                );
            }

            const result = await response.json() as any;

            // Ensure the result has the required AssessmentResult structure
            const assessmentResult: AssessmentResult = {
                timestamp: new Date().toISOString(),
                totalServers: result.totalServers || 0,
                compliantServers: result.compliantServers || 0,
                nonCompliantServers: result.nonCompliantServers || 0,
                missingServers: result.missingServers || [],
                configurationIssues: result.configurationIssues || [],
                serverStatuses: result.serverStatuses || [],
                overallScore: result.overallScore || 0,
                summary: result.summary || {
                    criticalIssues: 0,
                    highIssues: 0,
                    mediumIssues: 0,
                    lowIssues: 0
                }
            };

            // Update circuit breaker on success
            this.updateCircuitBreakerSuccess();

            const processingTime = Date.now() - startTime;
            this.logger.info('Compliance server call completed', {
                assessmentId: assessmentData.assessmentId,
                processingTime
            });

            return assessmentResult;

        } catch (error) {
            // Update circuit breaker on failure
            this.updateCircuitBreakerFailure();

            if (error instanceof AssessmentExecutionError) {
                throw error;
            }

            throw new AssessmentExecutionError(
                `Failed to call compliance server: ${error instanceof Error ? error.message : 'Unknown error'}`,
                assessmentData.assessmentId
            );
        }
    }

    /**
     * Update assessment state in AssessmentStore
     */
    private async updateAssessmentState(
        assessmentId: string,
        state: AssessmentState,
        result?: AssessmentResult,
        message?: string
    ): Promise<void> {
        try {
            this.logger.debug('Updating assessment state', { assessmentId, state });

            // Use AssessmentStore service to update state
            await this.assessmentStore.updateState(assessmentId, state, result, message);

            this.logger.debug('Assessment state updated successfully', { assessmentId, state });

        } catch (error) {
            this.logger.error('Failed to update assessment state', error as Error, { assessmentId, state });
            throw new AssessmentProcessingError(
                `Failed to update assessment state: ${error instanceof Error ? error.message : 'Unknown error'}`,
                assessmentId,
                'STATE_UPDATE_FAILED'
            );
        }
    }

    /**
     * Handle processing errors and retries
     */
    private async handleProcessingError(
        assessmentId: string,
        error: Error,
        retryCount: number
    ): Promise<boolean> {
        try {
            this.logger.warn('Processing error occurred', error instanceof Error ? error.message : 'Unknown error');
            this.logger.debug('Processing error details', { assessmentId, retryCount, error: error instanceof Error ? error.stack : undefined });

            // Log the error
            await this.auditService.log({
                action: 'assessment_processing_error',
                actor: 'assessment-processor',
                target: 'assessment',
                result: 'failed',
                details: {
                    assessmentId,
                    error: error.message,
                    retryCount,
                    errorType: error.name
                },
                ipAddress: 'system',
                userAgent: 'assessment-processor'
            });

            // Check if we should retry
            if (retryCount < this.config.processing.maxRetries) {
                const delay = this.calculateRetryDelay(retryCount);
                const nextRetryAt = new Date(Date.now() + delay).toISOString();

                // Update assessment state for retry using AssessmentStore
                await this.assessmentStore.updateState(assessmentId, AssessmentState.FAILED, undefined, error.message);

                this.logger.info('Assessment scheduled for retry', {
                    assessmentId,
                    retryCount,
                    nextRetryAt
                });

                return true; // Should retry
            } else {
                // Max retries exceeded, mark as permanently failed
                await this.updateAssessmentState(assessmentId, AssessmentState.FAILED, undefined, error.message);

                this.logger.error('Assessment failed permanently', error, {
                    assessmentId,
                    retryCount
                });

                return false; // No more retries
            }

        } catch (error) {
            this.logger.error('Failed to handle processing error', error as Error, { assessmentId });
            return false;
        }
    }

    /**
     * Start processing queue management
     */
    private startProcessingQueue(): void {
        this.processingInterval = setInterval(async () => {
            await this.processQueue();
        }, this.config.processing.processingInterval);

        this.logger.info('Processing queue started', {
            interval: this.config.processing.processingInterval
        });
    }

    /**
     * Process the assessment queue
     */
    private async processQueue(): Promise<void> {
        if (this.isProcessing || this.processingQueue.length === 0) {
            return;
        }

        this.isProcessing = true;

        try {
            // Process batch of assessments
            const batchSize = Math.min(this.config.processing.batchSize, this.processingQueue.length);
            const batch = this.processingQueue.splice(0, batchSize);

            this.metrics.queueSize = this.processingQueue.length;

            // Process each assessment in the batch
            const processingPromises = batch.map(item => this.processQueueItem(item));

            await Promise.allSettled(processingPromises);

        } catch (error) {
            this.logger.error('Error processing queue', error as Error);
        } finally {
            this.isProcessing = false;
        }
    }

    /**
     * Process a single queue item
     */
    private async processQueueItem(item: ProcessingQueueItem): Promise<void> {
        const startTime = Date.now();

        try {
            this.activeAssessments.add(item.assessmentId);

            // Check if assessment should be retried
            if (item.nextRetryAt && new Date(item.nextRetryAt) > new Date()) {
                this.logger.debug('Assessment scheduled for future retry', {
                    assessmentId: item.assessmentId,
                    nextRetryAt: item.nextRetryAt
                });
                return;
            }

            this.logger.info('Processing assessment from queue', {
                assessmentId: item.assessmentId,
                retryCount: item.retryCount
            });

            // Get assessment data
            const assessmentData = await this.getAssessmentData(item.assessmentId);

            // Update state to processing
            await this.updateAssessmentState(item.assessmentId, AssessmentState.PROCESSING);

            // Call compliance server
            const result = await this.callComplianceServer(assessmentData);

            // Update state to completed
            await this.updateAssessmentState(item.assessmentId, AssessmentState.COMPLETED, result);

            // Update metrics
            this.metrics.totalProcessed++;
            this.metrics.successful++;
            this.metrics.averageProcessingTime = this.calculateAverageProcessingTime(startTime);

            // Log completion
            await this.auditService.log({
                action: 'assessment_completed',
                actor: 'assessment-processor',
                target: 'assessment',
                result: 'success',
                details: {
                    assessmentId: item.assessmentId,
                    processingTime: Date.now() - startTime,
                    result: result
                },
                ipAddress: 'system',
                userAgent: 'assessment-processor'
            });

            this.logger.info('Assessment processed successfully', {
                assessmentId: item.assessmentId,
                processingTime: Date.now() - startTime
            });

            // Emit completion event
            this.emit('assessment.completed', {
                assessmentId: item.assessmentId,
                result,
                processingTime: Date.now() - startTime
            });

        } catch (error) {
            this.metrics.totalProcessed++;
            this.metrics.failed++;
            this.metrics.retryCount++;

            // Handle error and retry
            const shouldRetry = await this.handleProcessingError(
                item.assessmentId,
                error as Error,
                item.retryCount + 1
            );

            if (shouldRetry) {
                // Add back to queue with retry count
                this.processingQueue.push({
                    ...item,
                    retryCount: item.retryCount + 1,
                    lastAttemptAt: new Date().toISOString(),
                    nextRetryAt: new Date(Date.now() + this.calculateRetryDelay(item.retryCount + 1)).toISOString()
                });
                this.metrics.queueSize = this.processingQueue.length;
            }

            // Emit error event
            this.emit('assessment.failed', {
                assessmentId: item.assessmentId,
                error: error instanceof Error ? error.message : 'Unknown error',
                retryCount: item.retryCount + 1
            });

        } finally {
            this.activeAssessments.delete(item.assessmentId);
        }
    }

    /**
     * Load pending assessments from database
     */
    private async loadPendingAssessments(): Promise<void> {
        try {
            this.logger.info('Loading pending assessments');

            const query = `
                SELECT assessment_id 
                FROM assessment_states 
                WHERE state = $1 AND next_retry_at IS NOT NULL AND next_retry_at <= NOW()
                ORDER BY created_at ASC
                LIMIT ${this.config.processing.queueSize}
            `;

            const result = await this.databaseService.query(query, [AssessmentState.PENDING]);

            for (const row of result.rows) {
                const queueItem: ProcessingQueueItem = {
                    assessmentId: row.assessment_id,
                    priority: 'normal',
                    retryCount: 0,
                    maxRetries: this.config.processing.maxRetries,
                    timeout: this.config.processing.timeout,
                    createdAt: new Date().toISOString()
                };

                this.processingQueue.push(queueItem);
            }

            this.metrics.queueSize = this.processingQueue.length;

            this.logger.info('Pending assessments loaded', {
                count: result.rows.length,
                queueSize: this.processingQueue.length
            });

        } catch (error) {
            this.logger.error('Failed to load pending assessments', error as Error);
        }
    }

    /**
     * Start circuit breaker monitoring
     */
    private startCircuitBreakerMonitoring(): void {
        setInterval(() => {
            this.checkCircuitBreaker();
        }, this.config.circuitBreaker.monitoringInterval);

        this.logger.info('Circuit breaker monitoring started', {
            interval: this.config.circuitBreaker.monitoringInterval
        });
    }

    /**
     * Check circuit breaker state
     */
    private async checkCircuitBreaker(): Promise<void> {
        try {
            if (this.circuitBreaker.state === 'open') {
                const resetTime = this.circuitBreaker.nextAttemptTime;
                if (resetTime && new Date(resetTime) <= new Date()) {
                    this.logger.info('Resetting circuit breaker');
                    this.circuitBreaker.state = 'half-open';
                    this.circuitBreaker.failureCount = 0;
                    this.circuitBreaker.nextAttemptTime = undefined;
                }
            }
        } catch (error) {
            this.logger.error('Error checking circuit breaker', error as Error);
        }
    }

    /**
     * Update circuit breaker on success
     */
    private updateCircuitBreakerSuccess(): void {
        if (this.circuitBreaker.state === 'half-open') {
            this.circuitBreaker.state = 'closed';
            this.circuitBreaker.failureCount = 0;
            this.logger.debug('Circuit breaker closed after successful request');
        }
    }

    /**
     * Update circuit breaker on failure
     */
    private updateCircuitBreakerFailure(): void {
        this.circuitBreaker.failureCount++;

        if (this.circuitBreaker.failureCount >= this.config.circuitBreaker.failureThreshold) {
            this.circuitBreaker.state = 'open';
            this.circuitBreaker.lastFailureTime = new Date().toISOString();
            this.circuitBreaker.nextAttemptTime = new Date(
                Date.now() + this.config.circuitBreaker.resetTimeout
            ).toISOString();

            this.logger.warn('Circuit breaker opened', {
                failureCount: this.circuitBreaker.failureCount,
                resetTimeout: this.config.circuitBreaker.resetTimeout
            });
        }
    }

    /**
     * Calculate retry delay with exponential backoff
     */
    private calculateRetryDelay(retryCount: number): number {
        const baseDelay = this.config.processing.retryDelay;
        const backoffMultiplier = Math.pow(2, retryCount);
        const jitter = Math.random() * 1000; // Add random jitter

        return Math.min(baseDelay * backoffMultiplier + jitter, 300000); // Max 5 minutes
    }

    /**
     * Calculate average processing time
     */
    private calculateAverageProcessingTime(startTime: number): number {
        const processingTime = Date.now() - startTime;
        const totalProcessed = this.metrics.totalProcessed;

        if (totalProcessed === 1) {
            return processingTime;
        }

        return ((this.metrics.averageProcessingTime * (totalProcessed - 1)) + processingTime) / totalProcessed;
    }

    /**
     * Get assessment data from database
     */
    private async getAssessmentData(assessmentId: string): Promise<AssessmentStateData> {
        try {
            const query = `
                SELECT assessment_id, state, version, progress, message,
                       created_at, updated_at, completed_at, request_data,
                       result_data, error_message, retry_count, next_retry_at, metadata
                FROM assessment_states 
                WHERE assessment_id = $1
            `;

            const result = await this.databaseService.query(query, [assessmentId]);

            if (result.rows.length === 0) {
                throw new AssessmentNotFoundError(assessmentId);
            }

            const row = result.rows[0];
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
                nextRetryAt: row.next_retry_at,
                metadata: row.metadata ? JSON.parse(row.metadata) : undefined
            };

        } catch (error) {
            if (error instanceof AssessmentNotFoundError) {
                throw error;
            }
            throw new AssessmentProcessingError(
                `Failed to get assessment data: ${error instanceof Error ? error.message : 'Unknown error'}`,
                assessmentId,
                'DATA_RETRIEVAL_FAILED'
            );
        }
    }

    /**
     * Cancel an assessment
     */
    private async cancelAssessment(assessmentId: string, reason: string): Promise<void> {
        try {
            this.logger.info('Cancelling assessment', { assessmentId, reason });

            // Update state to cancelled
            await this.updateAssessmentState(assessmentId, AssessmentState.CANCELLED);

            // Remove from processing queue if present
            const index = this.processingQueue.findIndex(item => item.assessmentId === assessmentId);
            if (index > -1) {
                this.processingQueue.splice(index, 1);
                this.metrics.queueSize = this.processingQueue.length;
            }

            // Remove from active assessments
            this.activeAssessments.delete(assessmentId);

            // Log cancellation
            await this.auditService.log({
                action: 'assessment_cancelled',
                actor: 'assessment-processor',
                target: 'assessment',
                result: 'success',
                details: {
                    assessmentId,
                    reason
                },
                ipAddress: 'system',
                userAgent: 'assessment-processor'
            });

            this.logger.info('Assessment cancelled successfully', { assessmentId });

        } catch (error) {
            this.logger.error('Failed to cancel assessment', error as Error, { assessmentId });
            throw new AssessmentCancellationError(
                `Failed to cancel assessment: ${error instanceof Error ? error.message : 'Unknown error'}`,
                assessmentId
            );
        }
    }

    /**
     * Get current metrics
     */
    public getMetrics(): AssessmentProcessorMetrics {
        this.metrics.circuitBreakerState = { ...this.circuitBreaker };
        this.metrics.queueSize = this.processingQueue.length;
        this.metrics.lastProcessedAt = new Date().toISOString();

        return { ...this.metrics };
    }

    /**
     * Get processing queue status
     */
    public getQueueStatus(): {
        queueSize: number;
        activeAssessments: string[];
        isProcessing: boolean;
        circuitBreakerState: CircuitBreakerState;
    } {
        return {
            queueSize: this.processingQueue.length,
            activeAssessments: Array.from(this.activeAssessments),
            isProcessing: this.isProcessing,
            circuitBreakerState: { ...this.circuitBreaker }
        };
    }
}