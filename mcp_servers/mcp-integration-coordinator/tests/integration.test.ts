cp_servers / mcp - integration - coordinator / tests / integration.test.ts </path>
/**
 * MCP Integration Coordinator - Integration Tests
 * 
 * Tests the integration between Generic MCP Installer and Compliance Server.
 */

import { MCPIntegrationCoordinator } from '../src/server';
import { AuthService } from '../src/services/auth-service';
import { AuditService } from '../src/services/audit-service';
import { DatabaseService } from '../src/services/database-service';
import { Logger } from '../src/logger';
import { spawn } from 'child_process';
import { promisify } from 'util';
import { setTimeout } from 'timers/promises';

const exec = promisify(require('child_process').exec);

describe('MCP Integration Tests', () => {
    let coordinator: MCPIntegrationCoordinator;
    let authService: AuthService;
    let auditService: AuditService;
    let databaseService: DatabaseService;
    let logger: Logger;
    let testServer: any;

    beforeAll(async () => {
        // Initialize test services
        logger = new Logger({ name: 'IntegrationTest' });
        databaseService = new DatabaseService(logger);
        await databaseService.initialize();

        authService = new AuthService(databaseService, logger);
        auditService = new AuditService(databaseService, logger);

        coordinator = new MCPIntegrationCoordinator(
            databaseService,
            authService,
            auditService,
            logger
        );

        // Start test compliance server
        testServer = spawn('node', ['mcp_servers/mcp-compliance-server/test-server.js'], {
            cwd: process.cwd(),
            stdio: 'pipe'
        });

        await setTimeout(5000); // Wait for server to start
    });

    afterAll(async () => {
        // Cleanup
        if (testServer) {
            testServer.kill();
        }
        await databaseService.close();
    });

    describe('Server Communication', () => {
        it('should establish connection between servers', async () => {
            const result = await coordinator.testServerConnection('compliance-server');
            expect(result.success).toBe(true);
            expect(result.message).toContain('connected');
        });

        it('should handle connection failures gracefully', async () => {
            const result = await coordinator.testServerConnection('nonexistent-server');
            expect(result.success).toBe(false);
            expect(result.message).toContain('failed');
        });
    });

    describe('Assessment Integration', () => {
        it('should request assessment from compliance server', async () => {
            const assessmentRequest = {
                requestId: 'test-assessment-123',
                assessmentType: 'compliance',
                options: {
                    includeDetails: true,
                    generateReport: true
                },
                timestamp: new Date().toISOString(),
                source: 'installer'
            };

            const result = await coordinator.requestAssessment(assessmentRequest);
            expect(result.success).toBe(true);
            expect(result.assessmentId).toBeDefined();
            expect(result.status).toBe('pending');
        });

        it('should handle assessment request failures', async () => {
            const invalidRequest = {
                requestId: 'invalid-request',
                assessmentType: 'invalid-type',
                options: {}
            };

            const result = await coordinator.requestAssessment(invalidRequest);
            expect(result.success).toBe(false);
            expect(result.error).toBeDefined();
        });
    });

    describe('Remediation Integration', () => {
        it('should propose remediation actions', async () => {
            const proposalRequest = {
                assessmentId: 'test-assessment-123',
                issues: ['missing_config'],
                priority: 'high',
                autoApprove: false
            };

            const result = await coordinator.proposeRemediation(proposalRequest);
            expect(result.success).toBe(true);
            expect(result.proposalId).toBeDefined();
            expect(result.actions).toBeDefined();
        });

        it('should handle remediation proposal failures', async () => {
            const invalidProposal = {
                assessmentId: 'invalid-assessment',
                issues: [],
                priority: 'invalid-priority'
            };

            const result = await coordinator.proposeRemediation(invalidProposal);
            expect(result.success).toBe(false);
            expect(result.error).toBeDefined();
        });
    });

    describe('Approval Workflow', () => {
        it('should approve remediation actions', async () => {
            const approvalRequest = {
                approvalId: 'test-approval-123',
                decision: 'approved',
                reason: 'Test approval'
            };

            const result = await coordinator.approveRemediation(approvalRequest);
            expect(result.success).toBe(true);
            expect(result.executionId).toBeDefined();
        });

        it('should reject remediation actions', async () => {
            const rejectionRequest = {
                approvalId: 'test-rejection-123',
                decision: 'rejected',
                reason: 'Test rejection'
            };

            const result = await coordinator.rejectRemediation(rejectionRequest);
            expect(result.success).toBe(true);
            expect(result.message).toContain('rejected');
        });
    });

    describe('Audit Logging', () => {
        it('should log assessment events', async () => {
            await auditService.logAssessmentEvent(
                'created',
                'test-assessment-123',
                'test-user',
                'success'
            );

            const logs = await auditService.getLogs({
                actor: 'test-user',
                action: 'assessment_created'
            });

            expect(logs.length).toBeGreaterThan(0);
            expect(logs[0].actor).toBe('test-user');
        });

        it('should log remediation events', async () => {
            await auditService.logRemediationEvent(
                'approved',
                'test-remediation-123',
                'test-user',
                'success'
            );

            const logs = await auditService.getLogs({
                actor: 'test-user',
                action: 'remediation_approved'
            });

            expect(logs.length).toBeGreaterThan(0);
            expect(logs[0].actor).toBe('test-user');
        });
    });

    describe('Authentication', () => {
        it('should authenticate valid user', async () => {
            const loginResult = await authService.login('testuser', 'testpassword');
            expect(loginResult.success).toBe(true);
            expect(loginResult.token).toBeDefined();
        });

        it('should reject invalid credentials', async () => {
            const loginResult = await authService.login('invaliduser', 'invalidpassword');
            expect(loginResult.success).toBe(false);
            expect(loginResult.error).toBeDefined();
        });
    });

    describe('Error Handling', () => {
        it('should handle server timeouts', async () => {
            const result = await coordinator.requestAssessment({
                requestId: 'timeout-test',
                assessmentType: 'compliance',
                options: { timeout: 100 } // Very short timeout
            });

            expect(result.success).toBe(false);
            expect(result.error).toContain('timeout');
        });

        it('should handle invalid JSON responses', async () => {
            // Mock invalid response
            const result = await coordinator.processServerResponse('invalid-json-response');
            expect(result.success).toBe(false);
            expect(result.error).toContain('JSON');
        });
    });

    describe('Performance', () => {
        it('should handle concurrent requests', async () => {
            const requests = Array(10).fill(null).map((_, i) =>
                coordinator.requestAssessment({
                    requestId: `concurrent-test-${i}`,
                    assessmentType: 'compliance',
                    options: {}
                })
            );

            const results = await Promise.all(requests);
            const successful = results.filter(r => r.success).length;

            expect(successful).toBeGreaterThan(0);
            expect(successful).toBeLessThanOrEqual(10);
        });

        it('should maintain performance under load', async () => {
            const startTime = Date.now();
            const requests = Array(5).fill(null).map((_, i) =>
                coordinator.requestAssessment({
                    requestId: `performance-test-${i}`,
                    assessmentType: 'compliance',
                    options: {}
                })
            );

            await Promise.all(requests);
            const duration = Date.now() - startTime;

            expect(duration).toBeLessThan(10000); // Should complete in under 10 seconds
        });
    });

    describe('Security', () => {
        it('should validate input sanitization', async () => {
            const maliciousRequest = {
                requestId: '<script>alert("xss")</script>',
                assessmentType: 'compliance',
                options: {}
            };

            const result = await coordinator.requestAssessment(maliciousRequest);
            expect(result.success).toBe(true); // Should not fail but should sanitize
        });

        it('should prevent SQL injection', async () => {
            const maliciousInput = "'; DROP TABLE users; --";

            const result = await coordinator.requestAssessment({
                requestId: maliciousInput,
                assessmentType: 'compliance',
                options: {}
            });

            expect(result.success).toBe(true);
            // Verify no database errors occurred
        });
    });
});

describe('End-to-End Integration Flow', () => {
    let coordinator: MCPIntegrationCoordinator;
    let authService: AuthService;
    let auditService: AuditService;
    let databaseService: DatabaseService;
    let logger: Logger;

    beforeAll(async () => {
        logger = new Logger({ name: 'E2ETest' });
        databaseService = new DatabaseService(logger);
        await databaseService.initialize();

        authService = new AuthService(databaseService, logger);
        auditService = new AuditService(databaseService, logger);

        coordinator = new MCPIntegrationCoordinator(
            databaseService,
            authService,
            auditService,
            logger
        );
    });

    afterAll(async () => {
        await databaseService.close();
    });

    it('should complete full integration workflow', async () => {
        // Step 1: Authenticate
        const authResult = await authService.login('testuser', 'testpassword');
        expect(authResult.success).toBe(true);

        // Step 2: Request assessment
        const assessmentRequest = {
            requestId: 'e2e-assessment-123',
            assessmentType: 'compliance',
            options: {
                includeDetails: true,
                generateReport: true
            },
            timestamp: new Date().toISOString(),
            source: 'installer'
        };

        const assessmentResult = await coordinator.requestAssessment(assessmentRequest);
        expect(assessmentResult.success).toBe(true);
        const assessmentId = assessmentResult.assessmentId;

        // Step 3: Propose remediation
        const remediationRequest = {
            assessmentId,
            issues: ['missing_config'],
            priority: 'high',
            autoApprove: false
        };

        const remediationResult = await coordinator.proposeRemediation(remediationRequest);
        expect(remediationResult.success).toBe(true);
        const proposalId = remediationResult.proposalId;

        // Step 4: Approve remediation
        const approvalRequest = {
            approvalId: proposalId,
            decision: 'approved',
            reason: 'E2E test approval'
        };

        const approvalResult = await coordinator.approveRemediation(approvalRequest);
        expect(approvalResult.success).toBe(true);

        // Step 5: Verify audit logs
        const auditLogs = await auditService.getLogs({
            actor: 'testuser'
        });

        expect(auditLogs.length).toBeGreaterThan(0);

        // Verify all steps were logged
        const assessmentLogged = auditLogs.some(log =>
            log.action.includes('assessment') && log.result === 'success'
        );
        const remediationLogged = auditLogs.some(log =>
            log.action.includes('remediation') && log.result === 'success'
        );
        const approvalLogged = auditLogs.some(log =>
            log.action.includes('approval') && log.result === 'success'
        );

        expect(assessmentLogged).toBe(true);
        expect(remediationLogged).toBe(true);
        expect(approvalLogged).toBe(true);
    });

    it('should handle workflow failures gracefully', async () => {
        // Step 1: Authenticate
        const authResult = await authService.login('testuser', 'testpassword');
        expect(authResult.success).toBe(true);

        // Step 2: Request invalid assessment
        const invalidAssessment = {
            requestId: 'invalid-e2e-123',
            assessmentType: 'invalid-type',
            options: {}
        };

        const assessmentResult = await coordinator.requestAssessment(invalidAssessment);
        expect(assessmentResult.success).toBe(false);

        // Step 3: Verify error was logged
        const auditLogs = await auditService.getLogs({
            actor: 'testuser',
            result: 'failure'
        });

        expect(auditLogs.length).toBeGreaterThan(0);
    });
});