/**
 * MCP Integration Coordinator - Remediation Controller
 * 
 * Handles remediation requests and approvals.
 */

import { Router, Request, Response } from 'express';
import { AssessmentStore } from '../services/assessment-store';
import { AuditService } from '../services/audit-service';
import { RemediationProposal, ApprovalRequest, AssessmentState } from '../types';
import { logger } from '../logger';

export class RemediationController {
    private router: Router;
    private assessmentStore: AssessmentStore;
    private auditService: AuditService;

    constructor(assessmentStore: AssessmentStore, auditService: AuditService) {
        this.router = Router();
        this.assessmentStore = assessmentStore;
        this.auditService = auditService;
        this.setupRoutes();
    }

    /**
     * Setup remediation routes
     */
    private setupRoutes(): void {
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
    private async proposeRemediation(req: Request, res: Response): Promise<void> {
        try {
            const proposal: RemediationProposal = req.body;

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
            await this.assessmentStore.createAssessment({
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
            });

            // Log the remediation proposal
            await this.auditService.log({
                action: 'remediation_proposed',
                actor: (req as any).user?.username || 'unknown',
                target: 'remediation',
                result: 'success',
                details: {
                    proposalId,
                    assessmentId: proposal.assessmentId,
                    actionsCount: proposal.actions.length
                },
                ipAddress: (req as any).ip,
                userAgent: (req as any).get('User-Agent')
            });

            res.json({
                proposalId,
                status: 'proposed',
                message: 'Remediation proposal submitted and pending approval',
                requiresApproval: true
            });
        } catch (error) {
            logger.error('Remediation proposal failed', error as Error);
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
    private async getRemediationProposal(req: any, res: any): Promise<void> {
        try {
            const { proposalId } = req.params;

            // Get proposal using AssessmentStore
            const proposal = await this.assessmentStore.getState(proposalId);

            res.json({
                proposalId,
                proposal
            });
        } catch (error) {
            logger.error('Failed to get remediation proposal', error as Error);
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
    private async approveRemediation(req: Request, res: Response): Promise<void> {
        try {
            const approvalRequest: ApprovalRequest = req.body;

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
            await this.assessmentStore.updateState(approvalRequest.approvalId, AssessmentState.COMPLETED, undefined, 'Remediation approved');

            // Log the approval
            await this.auditService.log({
                action: 'remediation_approved',
                actor: (req as any).user?.username || 'unknown',
                target: 'remediation',
                result: 'success',
                details: {
                    approvalId: approvalRequest.approvalId,
                    decision: approvalRequest.decision
                },
                ipAddress: (req as any).ip,
                userAgent: (req as any).get('User-Agent')
            });

            res.json({
                approvalId: approvalRequest.approvalId,
                status: 'approved',
                message: 'Remediation approved successfully'
            });
        } catch (error) {
            logger.error('Remediation approval failed', error as Error);
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
    private async rejectRemediation(req: Request, res: Response): Promise<void> {
        try {
            const approvalRequest: ApprovalRequest = req.body;

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
            await this.assessmentStore.updateState(approvalRequest.approvalId, AssessmentState.FAILED, undefined, 'Remediation rejected');

            // Log the rejection
            await this.auditService.log({
                action: 'remediation_rejected',
                actor: (req as any).user?.username || 'unknown',
                target: 'remediation',
                result: 'success',
                details: {
                    approvalId: approvalRequest.approvalId,
                    decision: approvalRequest.decision
                },
                ipAddress: (req as any).ip,
                userAgent: (req as any).get('User-Agent')
            });

            res.json({
                approvalId: approvalRequest.approvalId,
                status: 'rejected',
                message: 'Remediation rejected successfully'
            });
        } catch (error) {
            logger.error('Remediation rejection failed', error as Error);
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
    private async listRemediationProposals(_req: Request, res: Response): Promise<void> {
        try {
            // List proposals using AssessmentStore
            const proposals = await this.assessmentStore.getAssessmentsForRetry();

            res.json({
                proposals
            });
        } catch (error) {
            logger.error('Failed to list remediation proposals', error as Error);
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
    public getRouter(): Router {
        return this.router;
    }
}