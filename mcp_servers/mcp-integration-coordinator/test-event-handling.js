/**
 * Simple test script to verify event handling functionality
 */

const http = require('http');
const https = require('https');

class EventHandlingTester {
    constructor() {
        this.integrationCoordinatorUrl = 'http://localhost:3001';
        this.testResults = [];
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
                timeout: 10000
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
     * Test assessment request and results
     */
    async testAssessmentFlow() {
        console.log('🧪 Testing Assessment Flow...');

        try {
            // Step 1: Request assessment
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

            console.log('📤 Sending assessment request...');
            const response = await this.makeRequest(
                `${this.integrationCoordinatorUrl}/api/assessment/request`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: assessmentRequest
                }
            );

            if (response.statusCode !== 200) {
                throw new Error(`Assessment request failed with status ${response.statusCode}`);
            }

            console.log('✅ Assessment request successful:', response.data);

            // Step 2: Wait for assessment to complete and get results
            console.log('⏳ Waiting for assessment completion...');
            await new Promise(resolve => setTimeout(resolve, 5000));

            console.log('📥 Getting assessment results...');
            const resultsResponse = await this.makeRequest(
                `${this.integrationCoordinatorUrl}/api/assessment/results/${response.data.assessmentId}`
            );

            if (resultsResponse.statusCode !== 200) {
                throw new Error(`Get results failed with status ${resultsResponse.statusCode}`);
            }

            console.log('✅ Assessment results received:', resultsResponse.data);

            // Check if we got actual results or a timeout error
            if (resultsResponse.data.results && resultsResponse.data.results.error) {
                console.log('❌ Assessment failed with error:', resultsResponse.data.results.error);
                return { success: false, error: resultsResponse.data.results.error };
            } else if (resultsResponse.data.results && resultsResponse.data.results.status === 'timeout') {
                console.log('⏰ Assessment timed out');
                return { success: false, error: 'Assessment timeout' };
            } else {
                console.log('🎉 Assessment completed successfully!');
                return {
                    success: true,
                    assessmentId: response.data.assessmentId,
                    results: resultsResponse.data.results
                };
            }

        } catch (error) {
            console.error('❌ Assessment flow failed:', error.message);
            return { success: false, error: error.message };
        }
    }

    /**
     * Run the test
     */
    async runTest() {
        console.log('🚀 Starting Event Handling Test...');
        console.log('=====================================');

        const result = await this.testAssessmentFlow();

        console.log('=====================================');
        if (result.success) {
            console.log('🎉 Event Handling Test PASSED!');
            console.log(`📋 Assessment ID: ${result.assessmentId}`);
            console.log(`📊 Results: ${JSON.stringify(result.results, null, 2)}`);
        } else {
            console.log('💥 Event Handling Test FAILED!');
            console.log(`❌ Error: ${result.error}`);
        }

        return result;
    }
}

// Run the test if this file is executed directly
if (require.main === module) {
    const tester = new EventHandlingTester();
    tester.runTest()
        .then(result => {
            process.exit(result.success ? 0 : 1);
        })
        .catch(error => {
            console.error('Test execution failed:', error);
            process.exit(1);
        });
}

module.exports = EventHandlingTester;