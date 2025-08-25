/**
 * MCP Integration Coordinator - Assessment Controller
 *
 * Handles assessment requests from MCP servers using Promise-based API
 * from AssessmentStore and AssessmentProcessor services.
 */

import { Router, Request, Response } from 'express';
import { AssessmentStore } from '../services/assessment-store';
import { AssessmentProcessor } from '../services/assessment-processor';
import { AuditService } from '../services/audit-service';
import { AssessmentRequest, AssessmentState, AssessmentResult } from '../types';
import { logger } from '../logger';

export class AssessmentController {
    private router: Router;
    private assessmentStore: AssessmentStore;
    private assessmentProcessor: AssessmentProcessor;
    private auditService: AuditService;

    constructor(
        assessmentStore: AssessmentStore,
        assessmentProcessor: AssessmentProcessor,
        auditService: AuditService
    ) {
        this.router = Router();
        this.assessmentStore = assessmentStore;
        this.assessmentProcessor = assessmentProcessor;
        this.auditService = auditService;
        this.setupRoutes();
    }

    /**
     * Setup assessment routes
     */
    private setupRoutes(): void {
        // Request assessment
        this.router.post('/request', this.requestAssessment);

        // Get assessment results
        this.router.get('/results/:assessmentId', this.getAssessmentResults);

        // Get assessment status
        this.router.get('/status/:assessmentId', this.getAssessmentStatus);

        // List all assessments
        this.router.get('/list', this.listAssessments);

        // Cancel assessment
        this.router.delete('/:assessmentId', this.cancelAssessment);

        // Get assessment statistics
        this.router.get('/statistics', this.getAssessmentStatistics);
    }

    /**
     * Request assessment
     */
    private async requestAssessment(req: Request, res: Response): Promise<void> {
        try {
            const assessmentRequest: AssessmentRequest = req.body;

            // Validate input
            if (!assessmentRequest.assessmentType || !assessmentRequest.options) {
                res.status(400).json({
                    error: {
                        code: 'INVALID_REQUEST',
                        message: 'Missing required fields: assessmentType and options',
                        retryable: false
                    }
                });
                return;
            }

            // Create assessment using AssessmentStore
            const createOptions = {
                assessmentType: assessmentRequest.assessmentType,
                options: assessmentRequest.options,
                serverName: assessmentRequest.serverName,
                source: assessmentRequest.source || 'installer'
            };

            console.log('AssessmentController: Creating assessment with options:', createOptions);

            const assessmentId = await this.assessmentStore.createAssessment(createOptions);

            console.log('AssessmentController: Assessment created with ID:', assessmentId);

            // Start processing using AssessmentProcessor
            console.log('AssessmentController: Starting processing for assessment:', assessmentId);
            this.assessmentProcessor.processAssessment(assessmentId).catch(error => {
                logger.error('Failed to start assessment processing', error as Error, { assessmentId });
            });

            // Log the assessment request
            console.log('AssessmentController: Logging assessment request');
            await this.auditService.log({
                action: 'assessment_requested',
                actor: (req as any).user?.username || 'unknown',
                target: 'assessment',
                result: 'success',
                details: {
                    assessmentId,
                    assessmentType: assessmentRequest.assessmentType,
                    options: assessmentRequest.options
                },
                ipAddress: (req as any).ip,
                userAgent: (req as any).get('User-Agent')
            });

            console.log('AssessmentController: Sending response');
            res.json({
                assessmentId,
                status: 'requested',
                message: 'Assessment request received and processing',
                estimatedTime: assessmentRequest.options?.includeDetails ? 30000 : 15000
            });
        } catch (error) {
            logger.error('Assessment request failed', error as Error);
            res.status(500).json({
                error: {
                    code: 'ASSESSMENT_REQUEST_FAILED',
                    message: 'Failed to request assessment',
                    retryable: false
                }
            });
        }
    }

    /**
     * Get assessment results
     */
    private async getAssessmentResults(req: Request, res: Response): Promise<void> {
        const { assessmentId } = req.params;

        try {
            // Use AssessmentStore.waitForCompletion with timeout
            const timeout = parseInt(req.query.timeout as string) || 30000;
            const results = await this.assessmentStore.waitForCompletion(assessmentId, timeout);

            res.json({
                assessmentId,
                results
            });
        } catch (error) {
            logger.error('Failed to get assessment results', error as Error, { assessmentId });

            if (error.message.includes('timeout')) {
                res.status(408).json({
                    error: {
                        code: 'ASSESSMENT_TIMEOUT',
                        message: 'Assessment processing timed out',
                        retryable: true
                    }
                });
            } else if (error.message.includes('failed')) {
                res.status(400).json({
                    error: {
                        code: 'ASSESSMENT_FAILED',
                        message: error.message,
                        retryable: false
                    }
                });
            } else {
                res.status(500).json({
                    error: {
                        code: 'ASSESSMENT_RESULTS_FAILED',
                        message: 'Failed to get assessment results',
                        retryable: false
                    }
                });
            }
        }
    }

    /**
     * Get assessment status
     */
    private async getAssessmentStatus(req: Request, res: Response): Promise<void> {
        const { assessmentId } = req.params;

        try {
            const status = await this.assessmentStore.getState(assessmentId);

            res.json({
                assessmentId,
                status: status.state,
                progress: status.progress,
                message: status.message,
                lastUpdated: status.lastUpdated,
                completedAt: status.completedAt
            });
        } catch (error) {
            logger.error('Failed to get assessment status', error as Error, { assessmentId });

            if (error.message.includes('not found')) {
                res.status(404).json({
                    error: {
                        code: 'ASSESSMENT_NOT_FOUND',
                        message: 'Assessment not found',
                        retryable: false
                    }
                });
            } else {
                res.status(500).json({
                    error: {
                        code: 'ASSESSMENT_STATUS_FAILED',
                        message: 'Failed to get assessment status',
                        retryable: false
                    }
                });
            }
        }
    }

    /**
     * List all assessments
     */
    private async listAssessments(req: Request, res: Response): Promise<void> {
        try {
            const state = req.query.state as AssessmentState;
            const limit = parseInt(req.query.limit as string) || 100;
            const offset = parseInt(req.query.offset as string) || 0;

            const assessments = await this.assessmentStore.listAssessments(state, limit, offset);

            res.json({
                assessments,
                pagination: {
                    limit,
                    offset,
                    total: assessments.length
                }
            });
        } catch (error) {
            logger.error('Failed to list assessments', error as Error);
            res.status(500).json({
                error: {
                    code: 'ASSESSMENTS_LIST_FAILED',
                    message: 'Failed to list assessments',
                    retryable: false
                }
            });
        }
    }

    /**
     * Get assessment statistics
     */
    private async getAssessmentStatistics(_req: Request, res: Response): Promise<void> {
        try {
            const statistics = await this.assessmentStore.getStatistics();

            res.json({
                statistics
            });
        } catch (error) {
            logger.error('Failed to get assessment statistics', error as Error);
            res.status(500).json({
                error: {
                    code: 'ASSESSMENT_STATISTICS_FAILED',
                    message: 'Failed to get assessment statistics',
                    retryable: false
                }
            });
        }
    }

    /**
     * Cancel assessment
     */
    private async cancelAssessment(req: Request, res: Response): Promise<void> {
        const { assessmentId } = req.params;
        const reason = req.body.reason || 'User requested cancellation';

        try {
            // Cancel using AssessmentStore
            await this.assessmentStore.cancelAssessment(assessmentId, reason);

            // Log the cancellation
            await this.auditService.log({
                action: 'assessment_cancelled',
                actor: (req as any).user?.username || 'unknown',
                target: 'assessment',
                result: 'success',
                details: { assessmentId, reason },
                ipAddress: (req as any).ip,
                userAgent: (req as any).get('User-Agent')
            });

            res.json({
                assessmentId,
                status: 'cancelled',
                message: 'Assessment cancelled successfully'
            });
        } catch (error) {
            logger.error('Failed to cancel assessment', error as Error, { assessmentId });

            if (error.message.includes('not found')) {
                res.status(404).json({
                    error: {
                        code: 'ASSESSMENT_NOT_FOUND',
                        message: 'Assessment not found',
                        retryable: false
                    }
                });
            } else {
                res.status(500).json({
                    error: {
                        code: 'ASSESSMENT_CANCEL_FAILED',
                        message: 'Failed to cancel assessment',
                        retryable: false
                    }
                });
            }
        }
    }

    /**
     * Get router instance
     */
    public getRouter(): Router {
        return this.router;
    }
}