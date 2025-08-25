/**
 * MCP Integration Coordinator - Assessment Controller (JavaScript Version)
 *
 * Handles assessment requests from MCP servers using Promise-based API
 * from AssessmentStore and AssessmentProcessor services.
 */

const express = require('express');
const { AssessmentStore } = require('../services/assessment-store');
const { AssessmentProcessor } = require('../services/assessment-processor');
const { AuditService } = require('../services/audit-service');
const { logger } = require('../logger');

class AssessmentController {
    constructor(assessmentStore, assessmentProcessor, auditService) {
        this.router = express.Router();
        this.assessmentStore = assessmentStore;
        this.assessmentProcessor = assessmentProcessor;
        this.auditService = auditService;
        this.setupRoutes();
    }

    /**
     * Setup assessment routes
     */
    setupRoutes() {
        // Request assessment
        this.router.post('/request', this.requestAssessment.bind(this));

        // Get assessment results
        this.router.get('/results/:assessmentId', this.getAssessmentResults.bind(this));

        // Get assessment status
        this.router.get('/status/:assessmentId', this.getAssessmentStatus.bind(this));

        // List all assessments
        this.router.get('/list', this.listAssessments.bind(this));

        // Cancel assessment
        this.router.delete('/:assessmentId', this.cancelAssessment.bind(this));

        // Get assessment statistics
        this.router.get('/statistics', this.getAssessmentStatistics.bind(this));
    }

    /**
     * Request assessment
     */
    async requestAssessment(req, res) {
        try {
            const assessmentRequest = req.body;

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
            console.log('AssessmentController (JS): Creating assessment');
            const createOptions = {
                assessmentType: assessmentRequest.assessmentType,
                options: assessmentRequest.options,
                serverName: assessmentRequest.serverName,
                source: assessmentRequest.source || 'installer'
            };
            console.log('AssessmentController (JS): Create options:', createOptions);

            const assessmentId = await this.assessmentStore.createAssessment(createOptions);
            console.log('AssessmentController (JS): Assessment created with ID:', assessmentId);

            // Start processing using AssessmentProcessor
            console.log('AssessmentController (JS): Starting processing');
            this.assessmentProcessor.processAssessment(assessmentId).catch(error => {
                logger.error('Failed to start assessment processing', error, { assessmentId });
            });

            // Log the assessment request
            console.log('AssessmentController (JS): Logging assessment request');
            await this.auditService.log({
                action: 'assessment_requested',
                actor: req.user?.username || 'unknown',
                target: 'assessment',
                result: 'success',
                details: {
                    assessmentId,
                    assessmentType: assessmentRequest.assessmentType,
                    options: assessmentRequest.options
                },
                ipAddress: req.ip,
                userAgent: req.get('User-Agent')
            });

            console.log('AssessmentController (JS): Sending response');
            res.json({
                assessmentId,
                status: 'requested',
                message: 'Assessment request received and processing',
                estimatedTime: assessmentRequest.options?.includeDetails ? 30000 : 15000
            });
        } catch (error) {
            logger.error('Assessment request failed', error);
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
    async getAssessmentResults(req, res) {
        const { assessmentId } = req.params;

        try {
            // Use AssessmentStore.waitForCompletion with timeout
            const timeout = parseInt(req.query.timeout) || 30000;
            const results = await this.assessmentStore.waitForCompletion(assessmentId, timeout);

            res.json({
                assessmentId,
                results
            });
        } catch (error) {
            logger.error('Failed to get assessment results', error, { assessmentId });

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
    async getAssessmentStatus(req, res) {
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
            logger.error('Failed to get assessment status', error, { assessmentId });

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
    async listAssessments(req, res) {
        try {
            const state = req.query.state;
            const limit = parseInt(req.query.limit) || 100;
            const offset = parseInt(req.query.offset) || 0;

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
            logger.error('Failed to list assessments', error);
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
    async getAssessmentStatistics(req, res) {
        try {
            const statistics = await this.assessmentStore.getStatistics();

            res.json({
                statistics
            });
        } catch (error) {
            logger.error('Failed to get assessment statistics', error);
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
    async cancelAssessment(req, res) {
        const { assessmentId } = req.params;
        const reason = req.body.reason || 'User requested cancellation';

        try {
            // Cancel using AssessmentStore
            await this.assessmentStore.cancelAssessment(assessmentId, reason);

            // Log the cancellation
            await this.auditService.log({
                action: 'assessment_cancelled',
                actor: req.user?.username || 'unknown',
                target: 'assessment',
                result: 'success',
                details: { assessmentId, reason },
                ipAddress: req.ip,
                userAgent: req.get('User-Agent')
            });

            res.json({
                assessmentId,
                status: 'cancelled',
                message: 'Assessment cancelled successfully'
            });
        } catch (error) {
            logger.error('Failed to cancel assessment', error, { assessmentId });

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
    getRouter() {
        return this.router;
    }
}

module.exports = { AssessmentController };