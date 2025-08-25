/**
 * MCP Integration Coordinator - Remediation Controller (JavaScript Version)
 * 
 * Handles remediation requests and approvals.
 */

const express = require('express');
const { AssessmentStore } = require('../services/assessment-store');
const { AuditService } = require('../services/audit-service');
const { logger } = require('../logger');

class RemediationController {
    constructor(assessmentStore, auditService) {
        this.router = express.Router();
        this.assessmentStore = assessmentStore;
        this.auditService = auditService;
        this.setupRoutes();
    }

    /**
     * Setup remediation routes
     */
    setupRoutes() {
        // Request remediation proposal
        this.router.post('/propose', this.proposeRemediation.bind(this));

        // Get remediation proposal
        this.router.get('/proposals/:proposalId', this.getRemediationProposal.bind(this));

        // Approve remediation
        this.router.post('/approve', this.approveRemediation.bind(this));

        // Reject remediation
        this.router.post('/reject', this.rejectRemediation.bind(this));

        // List all remediation proposals
        this.router.get('/list', this.listRemediationProposals.bind(this));
    }

    /**
     * Propose remediation
     */
    async proposeRemediation(req, res) {
        try {
            const proposal = req.body;

            // Validate input
            if (!proposal.assessmentId || !Array.isArray(proposal.actions)) {
                res.status(400).json({
                    error: {
                        code: 'INVALID_INPUT',
                        message: 'Assessment ID and actions array are required',
                        retryable: false
                    }
                });
                return;
            }

            // Generate proposal ID
            const proposalId = `proposal_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

            // Log remediation proposal using AssessmentStore
            this.assessmentStore.createAssessment({
                assessmentType: 'compliance',
                options: {
                    includeDetails: true,
                    generateReport: true,
                    saveResults: true,
                    checkServerStatus: true,
                    validateConfig: true,
                    checkCompliance: true,
                    deepScan: false
                },
                serverName: proposal.assessmentId,
                source: 'compliance'
            }).catch(error => {
                logger.error('Failed to create assessment for remediation proposal', error);
            });

            // Log the remediation proposal
            await this.auditService.log({
                action: 'remediation_proposed',
                actor: req.user?.username || 'unknown',
                target: 'remediation',
                result: 'success',
                details: {
                    proposalId,
                    assessmentId: proposal.assessmentId,
                    actionsCount: proposal.actions.length
                },
                ipAddress: req.ip,
                userAgent: req.get('User-Agent')
            });

            res.json({
                proposalId,
                status: 'proposed',
                message: 'Remediation proposal submitted and pending approval',
                requiresApproval: true
            });
        } catch (error) {
            logger.error('Remediation proposal failed', error);
            res.status(500).json({
                error: {
                    code: 'REMEDIATION_PROPOSAL_FAILED',
                    message: 'Failed to propose remediation',
                    retryable: false
                }
            });
        }
    }

    /**
     * Get remediation proposal
     */
    async getRemediationProposal(req, res) {
        try {
            const { proposalId } = req.params;

            // Get proposal using AssessmentStore
            const proposal = await this.assessmentStore.getState(proposalId).catch(() => ({
                error: 'Proposal retrieval failed'
            }));

            res.json({
                proposalId,
                proposal
            });
        } catch (error) {
            logger.error('Failed to get remediation proposal', error);
            res.status(500).json({
                error: {
                    code: 'REMEDIATION_PROPOSAL_RETRIEVAL_FAILED',
                    message: 'Failed to get remediation proposal',
                    retryable: false
                }
            });
        }
    }

    /**
     * Approve remediation
     */
    async approveRemediation(req, res) {
        try {
            const approvalRequest = req.body;

            // Validate input
            if (!approvalRequest.approvalId || !approvalRequest.decision) {
                res.status(400).json({
                    error: {
                        code: 'INVALID_INPUT',
                        message: 'Approval ID and decision are required',
                        retryable: false
                    }
                });
                return;
            }

            // Log approval using AssessmentStore
            this.assessmentStore.updateState(approvalRequest.approvalId, 'completed', undefined, 'Remediation approved')
                .catch(error => {
                    logger.error('Failed to update assessment state for approval', error);
                });

            // Log the approval
            await this.auditService.log({
                action: 'remediation_approved',
                actor: req.user?.username || 'unknown',
                target: 'remediation',
                result: 'success',
                details: {
                    approvalId: approvalRequest.approvalId,
                    decision: approvalRequest.decision
                },
                ipAddress: req.ip,
                userAgent: req.get('User-Agent')
            });

            res.json({
                approvalId: approvalRequest.approvalId,
                status: 'approved',
                message: 'Remediation approved successfully'
            });
        } catch (error) {
            logger.error('Remediation approval failed', error);
            res.status(500).json({
                error: {
                    code: 'REMEDIATION_APPROVAL_FAILED',
                    message: 'Failed to approve remediation',
                    retryable: false
                }
            });
        }
    }

    /**
     * Reject remediation
     */
    async rejectRemediation(req, res) {
        try {
            const approvalRequest = req.body;

            // Validate input
            if (!approvalRequest.approvalId || !approvalRequest.decision) {
                res.status(400).json({
                    error: {
                        code: 'INVALID_INPUT',
                        message: 'Approval ID and decision are required',
                        retryable: false
                    }
                });
                return;
            }

            // Log rejection using AssessmentStore
            this.assessmentStore.updateState(approvalRequest.approvalId, 'failed', undefined, 'Remediation rejected')
                .catch(error => {
                    logger.error('Failed to update assessment state for rejection', error);
                });

            // Log the rejection
            await this.auditService.log({
                action: 'remediation_rejected',
                actor: req.user?.username || 'unknown',
                target: 'remediation',
                result: 'success',
                details: {
                    approvalId: approvalRequest.approvalId,
                    decision: approvalRequest.decision
                },
                ipAddress: req.ip,
                userAgent: req.get('User-Agent')
            });

            res.json({
                approvalId: approvalRequest.approvalId,
                status: 'rejected',
                message: 'Remediation rejected successfully'
            });
        } catch (error) {
            logger.error('Remediation rejection failed', error);
            res.status(500).json({
                error: {
                    code: 'REMEDIATION_REJECTION_FAILED',
                    message: 'Failed to reject remediation',
                    retryable: false
                }
            });
        }
    }

    /**
     * List all remediation proposals
     */
    async listRemediationProposals(req, res) {
        try {
            // List proposals using AssessmentStore
            const proposals = await this.assessmentStore.getAssessmentsForRetry().catch(() => []);

            res.json({
                proposals
            });
        } catch (error) {
            logger.error('Failed to list remediation proposals', error);
            res.status(500).json({
                error: {
                    code: 'REMEDIATION_PROPOSALS_LIST_FAILED',
                    message: 'Failed to list remediation proposals',
                    retryable: false
                }
            });
        }
    }

    /**
     * Get router instance
     */
    getRouter() {
        return this.router;
    }
}

module.exports = { RemediationController };