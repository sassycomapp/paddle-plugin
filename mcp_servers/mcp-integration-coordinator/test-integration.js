/**
 * MCP Integration Coordinator - Integration Test Script
 * 
 * Tests the integration between MCP compliance server and integration coordinator.
 */

const http = require('http');
const https = require('https');

class IntegrationTester {
    constructor() {
        this.integrationCoordinatorUrl = 'http://localhost:3001';
        this.complianceServerUrl = 'http://localhost:3000';
        this.testResults = [];
        this.passedTests = 0;
        this.failedTests = 0;
    }

    /**
     * Make HTTP request
     */
    makeRequest(url, options = {}) {
        return new Promise((resolve, reject) => {
            const urlObj = new URL(url);
            const isHttps = urlObj.protocol === 'https:';
            const lib = isHttps ? https : http;

            const requestOptions = {
                hostname: urlObj.hostname,
                port: urlObj.port || (isHttps ? 443 : 80),
                path: urlObj.pathname + urlObj.search,
                method: options.method || 'GET',
                headers: options.headers || {},
                timeout: 5000
            };

            const req = lib.request(requestOptions, (res) => {
                let data = '';
                res.on('data', (chunk) => data += chunk);
                res.on('end', () => {
                    try {
                        const parsedData = data ? JSON.parse(data) : {};
                        resolve({
                            statusCode: res.statusCode,
                            headers: res.headers,
                            data: parsedData
                        });
                    } catch (error) {
                        resolve({
                            statusCode: res.statusCode,
                            headers: res.headers,
                            data: data
                        });
                    }
                });
            });

            req.on('error', (error) => {
                reject(error);
            });

            req.on('timeout', () => {
                req.destroy();
                reject(new Error('Request timeout'));
            });

            if (options.body) {
                req.write(JSON.stringify(options.body));
            }

            req.end();
        });
    }

    /**
     * Run a test and record results
     */
    async runTest(testName, testFunction) {
        try {
            console.log(`\n🧪 Running test: ${testName}`);
            const result = await testFunction();
            console.log(`✅ ${testName}: PASSED`);
            this.passedTests++;
            this.testResults.push({ name: testName, status: 'PASSED', result });
            return result;
        } catch (error) {
            console.log(`❌ ${testName}: FAILED - ${error.message}`);
            this.failedTests++;
            this.testResults.push({ name: testName, status: 'FAILED', error: error.message });
            throw error;
        }
    }

    /**
     * Test integration coordinator health
     */
    async testIntegrationCoordinatorHealth() {
        await this.runTest('Integration Coordinator Health Check', async () => {
            const response = await this.makeRequest(`${this.integrationCoordinatorUrl}/health`);

            if (response.statusCode !== 200) {
                throw new Error(`Expected status 200, got ${response.statusCode}`);
            }

            if (!response.data.status) {
                throw new Error('Missing status field in response');
            }

            if (response.data.status !== 'healthy') {
                throw new Error(`Expected status 'healthy', got '${response.data.status}'`);
            }

            return response.data;
        });
    }

    /**
     * Test compliance server health
     */
    async testComplianceServerHealth() {
        await this.runTest('Compliance Server Health Check', async () => {
            const response = await this.makeRequest(`${this.complianceServerUrl}/health`);

            if (response.statusCode !== 200) {
                throw new Error(`Expected status 200, got ${response.statusCode}`);
            }

            return response.data;
        });
    }

    /**
     * Test assessment request flow
     */
    async testAssessmentRequestFlow() {
        await this.runTest('Assessment Request Flow', async () => {
            const assessmentRequest = {
                requestId: `test_${Date.now()}`,
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
                timestamp: new Date().toISOString(),
                source: 'compliance'
            };

            const response = await this.makeRequest(
                `${this.integrationCoordinatorUrl}/api/assessment/request`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: assessmentRequest
                }
            );

            if (response.statusCode !== 200) {
                throw new Error(`Expected status 200, got ${response.statusCode}`);
            }

            if (!response.data.assessmentId) {
                throw new Error('Missing assessmentId in response');
            }

            if (response.data.status !== 'requested') {
                throw new Error(`Expected status 'requested', got '${response.data.status}'`);
            }

            // Wait for assessment to complete
            await new Promise(resolve => setTimeout(resolve, 6000));

            // Get assessment results
            const resultsResponse = await this.makeRequest(
                `${this.integrationCoordinatorUrl}/api/assessment/results/${response.data.assessmentId}`
            );

            if (resultsResponse.statusCode !== 200) {
                throw new Error(`Expected status 200, got ${resultsResponse.statusCode}`);
            }

            return {
                assessmentId: response.data.assessmentId,
                status: response.data.status,
                results: resultsResponse.data
            };
        });
    }

    /**
     * Test remediation proposal flow
     */
    async testRemediationProposalFlow() {
        await this.runTest('Remediation Proposal Flow', async () => {
            const remediationProposal = {
                assessmentId: `test_${Date.now()}`,
                actions: [
                    {
                        id: 'action_1',
                        type: 'fix_security',
                        serverName: 'test-server',
                        description: 'Fix security vulnerability',
                        estimatedTime: 300,
                        requiresRestart: false,
                        dependencies: []
                    }
                ],
                riskAssessment: {
                    level: 'medium',
                    impact: 'Medium impact on system security',
                    likelihood: 0.5,
                    mitigation: 'Apply security patches'
                },
                estimatedTime: 300,
                requiresApproval: true,
                timestamp: new Date().toISOString()
            };

            const response = await this.makeRequest(
                `${this.integrationCoordinatorUrl}/api/remediation/propose`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: remediationProposal
                }
            );

            if (response.statusCode !== 200) {
                throw new Error(`Expected status 200, got ${response.statusCode}`);
            }

            if (!response.data.proposalId) {
                throw new Error('Missing proposalId in response');
            }

            if (response.data.status !== 'proposed') {
                throw new Error(`Expected status 'proposed', got '${response.data.status}'`);
            }

            // Test remediation approval
            const approvalRequest = {
                approvalId: response.data.proposalId,
                type: 'remediation',
                data: remediationProposal,
                requestedBy: 'test-user',
                timestamp: new Date().toISOString(),
                expiresAt: new Date(Date.now() + 3600000).toISOString()
            };

            const approvalResponse = await this.makeRequest(
                `${this.integrationCoordinatorUrl}/api/remediation/approve`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: approvalRequest
                }
            );

            if (approvalResponse.statusCode !== 200) {
                throw new Error(`Expected status 200, got ${approvalResponse.statusCode}`);
            }

            return {
                proposalId: response.data.proposalId,
                status: response.data.status,
                approval: approvalResponse.data
            };
        });
    }

    /**
     * Test audit logging
     */
    async testAuditLogging() {
        await this.runTest('Audit Logging', async () => {
            const response = await this.makeRequest(`${this.integrationCoordinatorUrl}/api/audit/logs`);

            if (response.statusCode !== 200) {
                throw new Error(`Expected status 200, got ${response.statusCode}`);
            }

            if (!Array.isArray(response.data.logs)) {
                throw new Error('Expected logs to be an array');
            }

            // Should have logs from our previous tests
            const assessmentLogs = response.data.logs.filter(log =>
                log.action.includes('assessment') || log.action.includes('remediation')
            );

            if (assessmentLogs.length === 0) {
                throw new Error('Expected to find assessment or remediation logs');
            }

            return {
                totalLogs: response.data.logs.length,
                assessmentLogs: assessmentLogs.length
            };
        });
    }

    /**
     * Test dashboard data
     */
    async testDashboardData() {
        await this.runTest('Dashboard Data', async () => {
            const response = await this.makeRequest(`${this.integrationCoordinatorUrl}/api/dashboard`);

            if (response.statusCode !== 200) {
                throw new Error(`Expected status 200, got ${response.statusCode}`);
            }

            if (!response.data.stats) {
                throw new Error('Missing stats in response');
            }

            if (!response.data.services) {
                throw new Error('Missing services in response');
            }

            return response.data;
        });
    }

    /**
     * Test server communication
     */
    async testServerCommunication() {
        await this.runTest('Server Communication', async () => {
            // Test integration coordinator can communicate with compliance server
            const response = await this.makeRequest(`${this.complianceServerUrl}/health`);

            if (response.statusCode !== 200) {
                throw new Error(`Integration coordinator cannot communicate with compliance server. Status: ${response.statusCode}`);
            }

            // Test compliance server can communicate with integration coordinator
            const coordinatorResponse = await this.makeRequest(`${this.integrationCoordinatorUrl}/health`);

            if (coordinatorResponse.statusCode !== 200) {
                throw new Error(`Compliance server cannot communicate with integration coordinator. Status: ${coordinatorResponse.statusCode}`);
            }

            return {
                complianceServerStatus: response.statusCode,
                integrationCoordinatorStatus: coordinatorResponse.statusCode
            };
        });
    }

    /**
     * Test human oversight workflow
     */
    async testHumanOversightWorkflow() {
        await this.runTest('Human Oversight Workflow', async () => {
            // Create a remediation proposal that requires approval
            const remediationProposal = {
                assessmentId: `human_oversight_test_${Date.now()}`,
                actions: [
                    {
                        id: 'human_action_1',
                        type: 'fix_security',
                        serverName: 'critical-server',
                        description: 'Fix critical security vulnerability',
                        estimatedTime: 600,
                        requiresRestart: true,
                        dependencies: ['backup-service']
                    }
                ],
                riskAssessment: {
                    level: 'high',
                    impact: 'High impact on system security',
                    likelihood: 0.8,
                    mitigation: 'Apply critical security patches immediately'
                },
                estimatedTime: 600,
                requiresApproval: true,
                timestamp: new Date().toISOString()
            };

            const response = await this.makeRequest(
                `${this.integrationCoordinatorUrl}/api/remediation/propose`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: remediationProposal
                }
            );

            if (response.statusCode !== 200) {
                throw new Error(`Expected status 200, got ${response.statusCode}`);
            }

            // Check that the proposal is logged for human oversight
            const auditResponse = await this.makeRequest(`${this.integrationCoordinatorUrl}/api/audit/logs`);
            const oversightLogs = auditResponse.data.logs.filter(log =>
                log.action === 'remediation_proposal_for_review'
            );

            if (oversightLogs.length === 0) {
                throw new Error('Expected to find human oversight logs');
            }

            // Test that the proposal requires approval
            if (!response.data.requiresApproval) {
                throw new Error('Expected remediation proposal to require approval');
            }

            return {
                proposalId: response.data.proposalId,
                requiresApproval: response.data.requiresApproval,
                oversightLogs: oversightLogs.length
            };
        });
    }

    /**
     * Run all tests
     */
    async runAllTests() {
        console.log('🚀 Starting Integration Tests...');
        console.log(`Integration Coordinator URL: ${this.integrationCoordinatorUrl}`);
        console.log(`Compliance Server URL: ${this.complianceServerUrl}`);
        console.log('=====================================');

        try {
            await this.testIntegrationCoordinatorHealth();
            await this.testComplianceServerHealth();
            await this.testServerCommunication();
            await this.testAssessmentRequestFlow();
            await this.testRemediationProposalFlow();
            await this.testAuditLogging();
            await this.testDashboardData();
            await this.testHumanOversightWorkflow();

            console.log('\n🎉 All tests completed successfully!');
            console.log('=====================================');
            console.log(`✅ Passed: ${this.passedTests}`);
            console.log(`❌ Failed: ${this.failedTests}`);
            console.log(`📊 Success Rate: ${((this.passedTests / (this.passedTests + this.failedTests)) * 100).toFixed(1)}%`);

            return {
                passed: this.passedTests,
                failed: this.failedTests,
                successRate: (this.passedTests / (this.passedTests + this.failedTests)) * 100,
                results: this.testResults
            };
        } catch (error) {
            console.error('\n💥 Test suite failed:', error.message);
            throw error;
        }
    }
}

// Run tests if this file is executed directly
if (require.main === module) {
    const tester = new IntegrationTester();
    tester.runAllTests()
        .then(results => {
            console.log('\n📋 Test Results Summary:');
            results.results.forEach(result => {
                console.log(`${result.status}: ${result.name}`);
            });
            process.exit(results.failed > 0 ? 1 : 0);
        })
        .catch(error => {
            console.error('Test execution failed:', error);
            process.exit(1);
        });
}

module.exports = IntegrationTester;