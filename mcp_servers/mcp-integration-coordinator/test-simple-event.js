/**
 * Simple test to verify event handling is working
 */

const http = require('http');

// Test the event handling directly
async function testEventHandling() {
    console.log('🧪 Testing Event Handling...');

    try {
        // Step 1: Send assessment request
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

        const assessmentResponse = await new Promise((resolve, reject) => {
            const postData = JSON.stringify(assessmentRequest);
            const options = {
                hostname: 'localhost',
                port: 3001,
                path: '/api/assessment/request',
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(postData)
                }
            };

            const req = http.request(options, (res) => {
                let data = '';
                res.on('data', (chunk) => data += chunk);
                res.on('end', () => {
                    try {
                        const parsedData = JSON.parse(data);
                        resolve({
                            statusCode: res.statusCode,
                            data: parsedData
                        });
                    } catch (error) {
                        reject(error);
                    }
                });
            });

            req.on('error', (error) => {
                reject(error);
            });

            req.setTimeout(10000, () => {
                req.destroy();
                reject(new Error('Request timeout'));
            });

            req.write(postData);
            req.end();
        });

        if (assessmentResponse.statusCode !== 200) {
            throw new Error(`Assessment request failed with status ${assessmentResponse.statusCode}`);
        }

        console.log('✅ Assessment request successful:', assessmentResponse.data);
        const assessmentId = assessmentResponse.data.assessmentId;

        // Step 2: Wait for assessment to complete
        console.log('⏳ Waiting for assessment to complete...');
        await new Promise(resolve => setTimeout(resolve, 3000));

        // Step 3: Get assessment results
        console.log('📥 Getting assessment results...');

        const resultsResponse = await new Promise((resolve, reject) => {
            const options = {
                hostname: 'localhost',
                port: 3001,
                path: `/api/assessment/results/${assessmentId}`,
                method: 'GET'
            };

            const req = http.request(options, (res) => {
                let data = '';
                res.on('data', (chunk) => data += chunk);
                res.on('end', () => {
                    try {
                        const parsedData = JSON.parse(data);
                        resolve({
                            statusCode: res.statusCode,
                            data: parsedData
                        });
                    } catch (error) {
                        resolve({
                            statusCode: res.statusCode,
                            data: data
                        });
                    }
                });
            });

            req.on('error', (error) => {
                reject(error);
            });

            req.setTimeout(15000, () => {
                req.destroy();
                reject(new Error('Request timeout'));
            });

            req.end();
        });

        console.log('📊 Results response status:', resultsResponse.statusCode);
        console.log('📊 Results response data:', resultsResponse.data);

        // Check if we got actual results or a timeout error
        if (resultsResponse.statusCode === 200) {
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
                    assessmentId: assessmentId,
                    results: resultsResponse.data.results
                };
            }
        } else {
            console.log('❌ Get results failed with status', resultsResponse.statusCode);
            return { success: false, error: `Get results failed with status ${resultsResponse.statusCode}` };
        }

    } catch (error) {
        console.error('❌ Test failed:', error.message);
        return { success: false, error: error.message };
    }
}

// Run the test
testEventHandling()
    .then(result => {
        console.log('=====================================');
        if (result.success) {
            console.log('🎉 Event Handling Test PASSED!');
            console.log(`📋 Assessment ID: ${result.assessmentId}`);
            console.log(`📊 Results: ${JSON.stringify(result.results, null, 2)}`);
        } else {
            console.log('💥 Event Handling Test FAILED!');
            console.log(`❌ Error: ${result.error}`);
        }
        process.exit(result.success ? 0 : 1);
    })
    .catch(error => {
        console.error('Test execution failed:', error);
        process.exit(1);
    });