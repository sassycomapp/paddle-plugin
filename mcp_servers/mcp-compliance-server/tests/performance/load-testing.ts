/**
 * Performance Testing with Apache Bench
 * 
 * This script provides performance testing capabilities using Apache Bench (ab)
 * to validate the performance benchmarks of the KiloCode MCP Compliance Server.
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs/promises';
import path from 'path';

const execAsync = promisify(exec);

export interface LoadTestConfig {
    url: string;
    concurrency: number;
    requests: number;
    duration?: number;
    headers?: Record<string, string>;
    postData?: string;
    keepAlive?: boolean;
}

export interface LoadTestResult {
    config: LoadTestConfig;
    startTime: string;
    endTime: string;
    duration: number;
    totalRequests: number;
    completedRequests: number;
    failedRequests: number;
    totalBytes: number;
    requestsPerSecond: number;
    timePerRequest: number;
    timePerRequestAcrossAllConcurrent: number;
    transferRate: number;
    responseTime: {
        min: number;
        max: number;
        mean: number;
        stddev: number;
        median: number;
        percentage: {
            '50%': number;
            '66%': number;
            '75%': number;
            '80%': number;
            '90%': number;
            '95%': number;
            '98%': number;
            '99%': number;
            '100%': number;
        };
    };
    connectionTimes: {
        min: number;
        max: number;
        mean: number;
        stddev: number;
        median: number;
    };
    performanceScore: number;
    recommendations: string[];
}

export class PerformanceTester {
    private results: LoadTestResult[] = [];

    async runLoadTest(config: LoadTestConfig): Promise<LoadTestResult> {
        console.log(`Starting load test: ${config.url}`);
        console.log(`Concurrency: ${config.concurrency}, Requests: ${config.requests}`);

        const startTime = new Date().toISOString();
        const abCommand = this.buildAbCommand(config);

        try {
            const { stdout, stderr } = await execAsync(abCommand, {
                timeout: config.duration ? config.duration * 1000 : 30000
            });

            const endTime = new Date().toISOString();
            const duration = new Date(endTime).getTime() - new Date(startTime).getTime();

            const result = this.parseAbOutput(stdout, config, startTime, endTime, duration);

            this.results.push(result);

            console.log(`Load test completed in ${duration}ms`);
            console.log(`Requests per second: ${result.requestsPerSecond.toFixed(2)}`);
            console.log(`Performance score: ${result.performanceScore}/100`);

            return result;
        } catch (error) {
            console.error('Load test failed:', error);
            throw error;
        }
    }

    private buildAbCommand(config: LoadTestConfig): string {
        let command = `ab -n ${config.requests} -c ${config.concurrency}`;

        if (config.duration) {
            command += ` -t ${config.duration}`;
        }

        if (config.headers) {
            for (const [key, value] of Object.entries(config.headers)) {
                command += ` -H "${key}: ${value}"`;
            }
        }

        if (config.postData) {
            command += ` -p "${config.postData}"`;
        }

        if (config.keepAlive) {
            command += ' -k';
        }

        command += ` "${config.url}"`;

        return command;
    }

    private parseAbOutput(output: string, config: LoadTestConfig, startTime: string, endTime: string, duration: number): LoadTestResult {
        const lines = output.split('\n');
        const result: Partial<LoadTestResult> = {
            config,
            startTime,
            endTime,
            duration,
            recommendations: []
        };

        // Parse key metrics
        for (const line of lines) {
            if (line.includes('Complete requests:')) {
                result.completedRequests = parseInt(line.split(':')[1].trim());
            } else if (line.includes('Failed requests:')) {
                result.failedRequests = parseInt(line.split(':')[1].trim());
            } else if (line.includes('Total transferred:')) {
                result.totalBytes = parseInt(line.split(':')[1].trim().split(' ')[0]);
            } else if (line.includes('Requests per second:')) {
                result.requestsPerSecond = parseFloat(line.split(':')[1].trim().split(' ')[0]);
            } else if (line.includes('Time per request:')) {
                const timePerRequest = parseFloat(line.split(':')[1].trim().split(' ')[0]);
                result.timePerRequest = timePerRequest;
            } else if (line.includes('Time per request across all concurrent requests:')) {
                const timeAcrossConcurrent = parseFloat(line.split(':')[1].trim().split(' ')[0]);
                result.timePerRequestAcrossAllConcurrent = timeAcrossConcurrent;
            } else if (line.includes('Transfer rate:')) {
                const transferRate = parseFloat(line.split(':')[1].trim().split(' ')[0]);
                result.transferRate = transferRate;
            } else if (line.includes('Document Length:')) {
                // This helps calculate total bytes
                const docLength = parseInt(line.split(':')[1].trim());
                if (!result.totalBytes) {
                    result.totalBytes = docLength * result.completedRequests!;
                }
            }
        }

        // Parse response time distribution
        const responseTimeSection = lines.find(line => line.includes('Percentage of the requests'));
        if (responseTimeSection) {
            const percentages = responseTimeSection.split(':')[1].trim().split(',');
            result.responseTime = {
                min: 0,
                max: 0,
                mean: 0,
                stddev: 0,
                median: 0,
                percentage: {
                    '50%': parseFloat(percentages[0].trim().split('ms')[0]),
                    '66%': parseFloat(percentages[1].trim().split('ms')[0]),
                    '75%': parseFloat(percentages[2].trim().split('ms')[0]),
                    '80%': parseFloat(percentages[3].trim().split('ms')[0]),
                    '90%': parseFloat(percentages[4].trim().split('ms')[0]),
                    '95%': parseFloat(percentages[5].trim().split('ms')[0]),
                    '98%': parseFloat(percentages[6].trim().split('ms')[0]),
                    '99%': parseFloat(percentages[7].trim().split('ms')[0]),
                    '100%': parseFloat(percentages[8].trim().split('ms')[0])
                }
            };
        }

        // Parse connection times
        const connectionTimeSection = lines.find(line => line.includes('Connection Times (ms)'));
        if (connectionTimeSection) {
            const connectionTimes = lines[lines.indexOf(connectionTimeSection) + 1].split('|')[1].trim().split(/\s+/);
            result.connectionTimes = {
                min: parseFloat(connectionTimes[0]),
                max: parseFloat(connectionTimes[1]),
                mean: parseFloat(connectionTimes[2]),
                stddev: parseFloat(connectionTimes[3]),
                median: parseFloat(connectionTimes[4])
            };
        }

        // Calculate performance score
        result.performanceScore = this.calculatePerformanceScore(result as LoadTestResult);

        // Generate recommendations
        result.recommendations = this.generateRecommendations(result as LoadTestResult);

        return result as LoadTestResult;
    }

    private calculatePerformanceScore(result: LoadTestResult): number {
        let score = 100;

        // Deduct points for failed requests
        if (result.failedRequests > 0) {
            score -= (result.failedRequests / result.totalRequests) * 50;
        }

        // Deduct points for slow response times
        if (result.timePerRequest > 1000) {
            score -= Math.min(30, (result.timePerRequest - 1000) / 100);
        }

        // Deduct points for low throughput
        if (result.requestsPerSecond < 10) {
            score -= Math.min(20, (10 - result.requestsPerSecond) * 2);
        }

        return Math.max(0, Math.round(score));
    }

    private generateRecommendations(result: LoadTestResult): string[] {
        const recommendations: string[] = [];

        if (result.failedRequests > 0) {
            recommendations.push(`Address ${result.failedRequests} failed requests`);
        }

        if (result.timePerRequest > 1000) {
            recommendations.push(`Optimize response time (currently ${result.timePerRequest.toFixed(2)}ms)`);
        }

        if (result.requestsPerSecond < 10) {
            recommendations.push(`Improve throughput (currently ${result.requestsPerSecond.toFixed(2)} req/s)`);
        }

        if (result.responseTime && result.responseTime['95%'] > 2000) {
            recommendations.push(`Address 95th percentile response time (currently ${result.responseTime['95%']}ms)`);
        }

        if (result.connectionTimes && result.connectionTimes.mean > 500) {
            recommendations.push(`Optimize connection times (currently ${result.connectionTimes.mean.toFixed(2)}ms)`);
        }

        if (recommendations.length === 0) {
            recommendations.push('Performance is within acceptable limits');
        }

        return recommendations;
    }

    async runCompliancePerformanceTests(): Promise<LoadTestResult[]> {
        const baseUrl = 'http://localhost:3000';
        const tests = [
            {
                name: 'Basic Compliance Check',
                config: {
                    url: `${baseUrl}/api/compliance`,
                    concurrency: 10,
                    requests: 100,
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer test-token'
                    },
                    postData: JSON.stringify({
                        servers: ['test-server'],
                        standards: ['kilocode-v1']
                    })
                }
            },
            {
                name: 'Server Validation',
                config: {
                    url: `${baseUrl}/api/validate`,
                    concurrency: 5,
                    requests: 50,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    postData: JSON.stringify({
                        serverName: 'test-server',
                        serverConfig: {
                            command: 'node',
                            args: ['server.js'],
                            env: {
                                NODE_ENV: 'development'
                            }
                        }
                    })
                }
            },
            {
                name: 'Report Generation',
                config: {
                    url: `${baseUrl}/api/reports`,
                    concurrency: 3,
                    requests: 20,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    postData: JSON.stringify({
                        format: 'html',
                        includeDetails: true
                    })
                }
            }
        ];

        const results: LoadTestResult[] = [];

        for (const test of tests) {
            console.log(`\n=== Running ${test.name} ===`);
            try {
                const result = await this.runLoadTest(test.config);
                results.push(result);
            } catch (error) {
                console.error(`Test ${test.name} failed:`, error);
            }
        }

        return results;
    }

    async generatePerformanceReport(results: LoadTestResult[]): Promise<string> {
        let report = '# Performance Testing Report\n\n';
        report += `Generated: ${new Date().toISOString()}\n\n`;

        const totalTests = results.length;
        const avgRequestsPerSecond = results.reduce((sum, r) => sum + r.requestsPerSecond, 0) / totalTests;
        const avgResponseTime = results.reduce((sum, r) => sum + r.timePerRequest, 0) / totalTests;
        const avgPerformanceScore = results.reduce((sum, r) => sum + r.performanceScore, 0) / totalTests;

        report += `## Summary\n`;
        report += `- Total Tests: ${totalTests}\n`;
        report += `- Average Requests/Second: ${avgRequestsPerSecond.toFixed(2)}\n`;
        report += `- Average Response Time: ${avgResponseTime.toFixed(2)}ms\n`;
        report += `- Average Performance Score: ${avgPerformanceScore.toFixed(1)}/100\n\n`;

        report += `## Test Results\n\n`;

        for (const result of results) {
            report += `### ${result.config.url}\n`;
            report += `- Requests/Second: ${result.requestsPerSecond.toFixed(2)}\n`;
            report += `- Response Time: ${result.timePerRequest.toFixed(2)}ms\n`;
            report += `- Performance Score: ${result.performanceScore}/100\n`;
            report += `- Completed Requests: ${result.completedRequests}/${result.config.requests}\n`;
            report += `- Failed Requests: ${result.failedRequests}\n`;
            report += `- Duration: ${result.duration}ms\n\n`;

            if (result.recommendations.length > 0) {
                report += `#### Recommendations\n`;
                for (const recommendation of result.recommendations) {
                    report += `- ${recommendation}\n`;
                }
                report += '\n';
            }
        }

        return report;
    }

    async savePerformanceReport(results: LoadTestResult[], filename?: string): Promise<void> {
        const report = await this.generatePerformanceReport(results);
        const defaultFilename = `performance-report-${new Date().toISOString().split('T')[0]}.md`;
        const filepath = filename || path.join(__dirname, '..', '..', 'reports', defaultFilename);

        await fs.mkdir(path.dirname(filepath), { recursive: true });
        await fs.writeFile(filepath, report);

        console.log(`Performance report saved to: ${filepath}`);
    }

    getResults(): LoadTestResult[] {
        return this.results;
    }

    clearResults(): void {
        this.results = [];
    }
}

// Export for use in other files
export default PerformanceTester;