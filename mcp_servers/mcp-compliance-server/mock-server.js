/**
 * Mock MCP Compliance Server for Integration Testing
 * 
 * This mock server simulates the behavior of a real compliance server
 * for testing integration with the MCP Integration Coordinator.
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');

class MockComplianceServer {
    constructor() {
        this.app = express();
        this.port = 3000;
        this.server = null;
        this.assessments = new Map();
        this.remediations = new Map();
        this.executions = new Map();

        this.setupMiddleware();
        this.setupRoutes();
    }

    /**
     * Setup Express middleware
     */
    setupMiddleware() {
        this.app.use(express.json());
        this.app.use(express.urlencoded({ extended: true }));
        this.app.use(cors());
        this.app.use(helmet());
    }

    /**
     * Setup API routes
     */
    setupRoutes() {
        // Health check
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'healthy',
                timestamp: new Date().toISOString(),
                server: 'MCP Compliance Server',
                version: '1.0.0'
            });
        });

        // Root endpoint
        this.app.get('/', (req, res) => {
            res.json({
                name: 'MCP Compliance Server',
                version: '1.0.0',
                description: 'Mock compliance server for testing',
                endpoints: {
                    health: '/health',
                    compliance: '/api/compliance',
                    assessment: '/api/assessment',
                    remediation: '/api/remediation',
                    execution: '/api/execution'
                }
            });
        });

        // Compliance assessment endpoint
        this.app.post('/api/compliance', (req, res) => {
            try {
                const { serverName, assessmentType } = req.body;

                const assessmentId = `compliance_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

                const assessment = {
                    id: assessmentId,
                    serverName: serverName || 'unknown',
                    assessmentType: assessmentType || 'compliance',
                    status: 'in_progress',
                    progress: 0,
                    startTime: new Date().toISOString(),
                    estimatedDuration: 30000,
                    issues: [
                        {
                            id: 'issue_1',
                            severity: 'high',
                            category: 'security',
                            description: 'Security vulnerability detected',
                            recommendation: 'Apply security patches'
                        },
                        {
                            id: 'issue_2',
                            severity: 'medium',
                            category: 'configuration',
                            description: 'Configuration optimization needed',
                            recommendation: 'Update configuration settings'
                        }
                    ]
                };

                this.assessments.set(assessmentId, assessment);

                // Simulate assessment progress
                this.simulateAssessmentProgress(assessmentId);

                res.json({
                    assessmentId,
                    status: 'started',
                    message: 'Compliance assessment started',
                    estimatedTime: 30000
                });
            } catch (error) {
                res.status(500).json({
                    error: {
                        code: 'COMPLIANCE_ASSESSMENT_FAILED',
                        message: 'Failed to start compliance assessment',
                        retryable: false
                    }
                });
            }
        });

        // Get assessment status
        this.app.get('/api/assessment/:assessmentId', (req, res) => {
            try {
                const { assessmentId } = req.params;
                const assessment = this.assessments.get(assessmentId);

                if (!assessment) {
                    return res.status(404).json({
                        error: {
                            code: 'ASSESSMENT_NOT_FOUND',
                            message: 'Assessment not found',
                            retryable: false
                        }
                    });
                }

                res.json(assessment);
            } catch (error) {
                res.status(500).json({
                    error: {
                        code: 'GET_ASSESSMENT_FAILED',
                        message: 'Failed to get assessment',
                        retryable: false
                    }
                });
            }
        });

        // Generate remediation proposal
        this.app.post('/api/remediation', (req, res) => {
            try {
                const { assessmentId, serverName } = req.body;

                const remediationId = `remediation_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

                const remediation = {
                    id: remediationId,
                    assessmentId: assessmentId || 'unknown',
                    serverName: serverName || 'unknown',
                    status: 'proposed',
                    actions: [
                        {
                            id: 'action_1',
                            type: 'security_patch',
                            description: 'Apply security patches',
                            estimatedTime: 600,
                            requiresRestart: true,
                            dependencies: ['backup-service']
                        },
                        {
                            id: 'action_2',
                            type: 'configuration_update',
                            description: 'Update configuration settings',
                            estimatedTime: 300,
                            requiresRestart: false,
                            dependencies: []
                        }
                    ],
                    riskAssessment: {
                        level: 'medium',
                        impact: 'Medium impact on system',
                        likelihood: 0.6,
                        mitigation: 'Execute during maintenance window'
                    },
                    estimatedTotalTime: 900,
                    requiresApproval: true,
                    proposedAt: new Date().toISOString()
                };

                this.remediations.set(remediationId, remediation);

                res.json({
                    remediationId,
                    status: 'proposed',
                    message: 'Remediation proposal generated',
                    requiresApproval: true
                });
            } catch (error) {
                res.status(500).json({
                    error: {
                        code: 'REMEDIATION_PROPOSAL_FAILED',
                        message: 'Failed to generate remediation proposal',
                        retryable: false
                    }
                });
            }
        });

        // Execute remediation
        this.app.post('/api/execution', (req, res) => {
            try {
                const { remediationId, approvedBy } = req.body;

                const executionId = `execution_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

                const execution = {
                    id: executionId,
                    remediationId: remediationId || 'unknown',
                    status: 'pending',
                    progress: 0,
                    startTime: null,
                    endTime: null,
                    approvedBy: approvedBy || 'unknown',
                    currentAction: null,
                    logs: []
                };

                this.executions.set(executionId, execution);

                // Simulate execution
                this.simulateExecution(executionId);

                res.json({
                    executionId,
                    status: 'started',
                    message: 'Remediation execution started'
                });
            } catch (error) {
                res.status(500).json({
                    error: {
                        code: 'EXECUTION_FAILED',
                        message: 'Failed to start remediation execution',
                        retryable: false
                    }
                });
            }
        });

        // Get execution status
        this.app.get('/api/execution/:executionId', (req, res) => {
            try {
                const { executionId } = req.params;
                const execution = this.executions.get(executionId);

                if (!execution) {
                    return res.status(404).json({
                        error: {
                            code: 'EXECUTION_NOT_FOUND',
                            message: 'Execution not found',
                            retryable: false
                        }
                    });
                }

                res.json(execution);
            } catch (error) {
                res.status(500).json({
                    error: {
                        code: 'GET_EXECUTION_FAILED',
                        message: 'Failed to get execution',
                        retryable: false
                    }
                });
            }
        });

        // Cancel execution
        this.app.post('/api/execution/:executionId/cancel', (req, res) => {
            try {
                const { executionId } = req.params;
                const execution = this.executions.get(executionId);

                if (!execution) {
                    return res.status(404).json({
                        error: {
                            code: 'EXECUTION_NOT_FOUND',
                            message: 'Execution not found',
                            retryable: false
                        }
                    });
                }

                execution.status = 'cancelled';
                execution.endTime = new Date().toISOString();
                execution.logs.push({
                    timestamp: new Date().toISOString(),
                    level: 'info',
                    message: 'Execution cancelled by user'
                });

                res.json({
                    executionId,
                    status: 'cancelled',
                    message: 'Execution cancelled successfully'
                });
            } catch (error) {
                res.status(500).json({
                    error: {
                        code: 'CANCEL_EXECUTION_FAILED',
                        message: 'Failed to cancel execution',
                        retryable: false
                    }
                });
            }
        });
    }

    /**
     * Simulate assessment progress
     */
    simulateAssessmentProgress(assessmentId) {
        const assessment = this.assessments.get(assessmentId);
        if (!assessment) return;

        const interval = setInterval(() => {
            assessment.progress += Math.random() * 20;

            if (assessment.progress >= 100) {
                assessment.progress = 100;
                assessment.status = 'completed';
                assessment.endTime = new Date().toISOString();
                clearInterval(interval);
            }
        }, 1000);
    }

    /**
     * Simulate execution progress
     */
    simulateExecution(executionId) {
        const execution = this.executions.get(executionId);
        if (!execution) return;

        execution.status = 'running';
        execution.startTime = new Date().toISOString();

        const actions = ['security_patch', 'configuration_update'];
        let currentActionIndex = 0;

        const interval = setInterval(() => {
            if (currentActionIndex < actions.length) {
                execution.currentAction = actions[currentActionIndex];
                execution.progress += (100 / actions.length);

                execution.logs.push({
                    timestamp: new Date().toISOString(),
                    level: 'info',
                    message: `Executing ${actions[currentActionIndex]}...`
                });

                currentActionIndex++;
            } else {
                execution.progress = 100;
                execution.status = 'completed';
                execution.endTime = new Date().toISOString();
                execution.currentAction = null;
                execution.logs.push({
                    timestamp: new Date().toISOString(),
                    level: 'info',
                    message: 'Execution completed successfully'
                });
                clearInterval(interval);
            }
        }, 2000);
    }

    /**
     * Start the server
     */
    start() {
        return new Promise((resolve, reject) => {
            this.server = this.app.listen(this.port, (error) => {
                if (error) {
                    reject(error);
                } else {
                    console.log(`🚀 Mock Compliance Server started on port ${this.port}`);
                    resolve();
                }
            });
        });
    }

    /**
     * Stop the server
     */
    stop() {
        return new Promise((resolve) => {
            if (this.server) {
                this.server.close(() => {
                    console.log('🛑 Mock Compliance Server stopped');
                    resolve();
                });
            } else {
                resolve();
            }
        });
    }

    /**
     * Get server statistics
     */
    getStats() {
        return {
            uptime: process.uptime(),
            memory: process.memoryUsage(),
            assessments: this.assessments.size,
            remediations: this.remediations.size,
            executions: this.executions.size
        };
    }
}

// Main execution
if (require.main === module) {
    const server = new MockComplianceServer();
    server.start().catch(console.error);

    // Handle graceful shutdown
    process.on('SIGTERM', () => {
        server.stop().then(() => process.exit(0));
    });

    process.on('SIGINT', () => {
        server.stop().then(() => process.exit(0));
    });
}

module.exports = MockComplianceServer;