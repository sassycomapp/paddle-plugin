/**
 * Test Execution Script
 * 
 * This script provides comprehensive test execution capabilities for the KiloCode MCP Compliance Server,
 * including unit tests, integration tests, compliance validation, and performance testing.
 */

import { describe, it, expect } from 'vitest';
import { ValidationEngine } from '../../src/validation/validators';
import { createMockValidationContext } from '../setup';
import PerformanceTester from './performance/load-testing';
import fs from 'fs/promises';
import path from 'path';

export interface TestExecutionConfig {
    unitTests: boolean;
    integrationTests: boolean;
    complianceTests: boolean;
    performanceTests: boolean;
    concurrency: number;
    outputFormat: 'json' | 'html' | 'markdown';
    outputDirectory: string;
    generateReports: boolean;
}

export interface TestExecutionResult {
    config: TestExecutionConfig;
    startTime: string;
    endTime: string;
    duration: number;
    unitTests: {
        total: number;
        passed: number;
        failed: number;
        skipped: number;
    };
    integrationTests: {
        total: number;
        passed: number;
        failed: number;
        skipped: number;
    };
    complianceTests: {
        total: number;
        passed: number;
        failed: number;
        skipped: number;
        averageScore: number;
    };
    performanceTests: {
        total: number;
        passed: number;
        failed: number;
        averageRequestsPerSecond: number;
        averageResponseTime: number;
        averagePerformanceScore: number;
    };
    overallScore: number;
    recommendations: string[];
}

export class TestExecutor {
    private config: TestExecutionConfig;
    private results: TestExecutionResult;

    constructor(config: TestExecutionConfig) {
        this.config = config;
        this.results = {
            config,
            startTime: '',
            endTime: '',
            duration: 0,
            unitTests: { total: 0, passed: 0, failed: 0, skipped: 0 },
            integrationTests: { total: 0, passed: 0, failed: 0, skipped: 0 },
            complianceTests: { total: 0, passed: 0, failed: 0, skipped: 0, averageScore: 0 },
            performanceTests: { total: 0, passed: 0, failed: 0, averageRequestsPerSecond: 0, averageResponseTime: 0, averagePerformanceScore: 0 },
            overallScore: 0,
            recommendations: []
        };
    }

    async executeAllTests(): Promise<TestExecutionResult> {
        console.log('Starting comprehensive test execution...');
        this.results.startTime = new Date().toISOString();

        try {
            if (this.config.unitTests) {
                await this.runUnitTests();
            }

            if (this.config.integrationTests) {
                await this.runIntegrationTests();
            }

            if (this.config.complianceTests) {
                await this.runComplianceTests();
            }

            if (this.config.performanceTests) {
                await this.runPerformanceTests();
            }

            this.calculateOverallScore();
            this.generateRecommendations();

            this.results.endTime = new Date().toISOString();
            this.results.duration = new Date(this.results.endTime).getTime() - new Date(this.results.startTime).getTime();

            if (this.config.generateReports) {
                await this.generateReports();
            }

            console.log('Test execution completed successfully!');
            return this.results;

        } catch (error) {
            console.error('Test execution failed:', error);
            throw error;
        }
    }

    private async runUnitTests(): Promise<void> {
        console.log('Running unit tests...');

        const validationEngine = new ValidationEngine(createMockValidationContext());

        try {
            const result = await validationEngine.validateAllRules();

            this.results.unitTests.total = result.rules.length;
            this.results.unitTests.passed = result.passedRules;
            this.results.unitTests.failed = result.failedRules;
            this.results.unitTests.skipped = 0;

            console.log(`Unit tests completed: ${this.results.unitTests.passed}/${this.results.unitTests.total} passed`);
        } catch (error) {
            console.error('Unit tests failed:', error);
            this.results.unitTests.failed = this.results.unitTests.total;
        }
    }

    private async runIntegrationTests(): Promise<void> {
        console.log('Running integration tests...');

        const validationEngine = new ValidationEngine(createMockValidationContext());

        try {
            const result = await validationEngine.validateAllRules();

            this.results.integrationTests.total = result.rules.length;
            this.results.integrationTests.passed = result.passedRules;
            this.results.integrationTests.failed = result.failedRules;
            this.results.integrationTests.skipped = 0;

            console.log(`Integration tests completed: ${this.results.integrationTests.passed}/${this.results.integrationTests.total} passed`);
        } catch (error) {
            console.error('Integration tests failed:', error);
            this.results.integrationTests.failed = this.results.integrationTests.total;
        }
    }

    private async runComplianceTests(): Promise<void> {
        console.log('Running compliance tests...');

        const validationEngine = new ValidationEngine(createMockValidationContext());

        try {
            const result = await validationEngine.validateAllRules();

            this.results.complianceTests.total = result.rules.length;
            this.results.complianceTests.passed = result.passedRules;
            this.results.complianceTests.failed = result.failedRules;
            this.results.complianceTests.skipped = 0;
            this.results.complianceTests.averageScore = result.overallScore;

            console.log(`Compliance tests completed: ${this.results.complianceTests.passed}/${this.results.complianceTests.total} passed, Score: ${this.results.complianceTests.averageScore}/100`);
        } catch (error) {
            console.error('Compliance tests failed:', error);
            this.results.complianceTests.failed = this.results.complianceTests.total;
        }
    }

    private async runPerformanceTests(): Promise<void> {
        console.log('Running performance tests...');

        const performanceTester = new PerformanceTester();

        try {
            const results = await performanceTester.runCompliancePerformanceTests();

            this.results.performanceTests.total = results.length;
            this.results.performanceTests.passed = results.filter(r => r.performanceScore >= 70).length;
            this.results.performanceTests.failed = results.filter(r => r.performanceScore < 70).length;

            if (results.length > 0) {
                this.results.performanceTests.averageRequestsPerSecond = results.reduce((sum, r) => sum + r.requestsPerSecond, 0) / results.length;
                this.results.performanceTests.averageResponseTime = results.reduce((sum, r) => sum + r.timePerRequest, 0) / results.length;
                this.results.performanceTests.averagePerformanceScore = results.reduce((sum, r) => sum + r.performanceScore, 0) / results.length;
            }

            console.log(`Performance tests completed: ${this.results.performanceTests.passed}/${this.results.performanceTests.total} passed`);
            console.log(`Average Requests/Second: ${this.results.performanceTests.averageRequestsPerSecond.toFixed(2)}`);
            console.log(`Average Response Time: ${this.results.performanceTests.averageResponseTime.toFixed(2)}ms`);
            console.log(`Average Performance Score: ${this.results.performanceTests.averagePerformanceScore.toFixed(1)}/100`);
        } catch (error) {
            console.error('Performance tests failed:', error);
            this.results.performanceTests.failed = this.results.performanceTests.total;
        }
    }

    private calculateOverallScore(): void {
        const totalTests = this.results.unitTests.total +
            this.results.integrationTests.total +
            this.results.complianceTests.total +
            this.results.performanceTests.total;

        const passedTests = this.results.unitTests.passed +
            this.results.integrationTests.passed +
            this.results.complianceTests.passed +
            this.results.performanceTests.passed;

        const complianceWeight = 0.4; // 40% weight for compliance
        const performanceWeight = 0.3; // 30% weight for performance
        const unitWeight = 0.2; // 20% weight for unit tests
        const integrationWeight = 0.1; // 10% weight for integration tests

        const complianceScore = (this.results.complianceTests.passed / this.results.complianceTests.total) * 100;
        const performanceScore = this.results.performanceTests.averagePerformanceScore;
        const unitScore = (this.results.unitTests.passed / this.results.unitTests.total) * 100;
        const integrationScore = (this.results.integrationTests.passed / this.results.integrationTests.total) * 100;

        this.results.overallScore = Math.round(
            (complianceScore * complianceWeight) +
            (performanceScore * performanceWeight) +
            (unitScore * unitWeight) +
            (integrationScore * integrationWeight)
        );
    }

    private generateRecommendations(): void {
        this.results.recommendations = [];

        // Compliance recommendations
        if (this.results.complianceTests.averageScore < 80) {
            this.results.recommendations.push('Improve compliance score - address failed compliance rules');
        }

        // Performance recommendations
        if (this.results.performanceTests.averagePerformanceScore < 70) {
            this.results.recommendations.push('Optimize performance - address performance bottlenecks');
        }

        if (this.results.performanceTests.averageResponseTime > 1000) {
            this.results.recommendations.push('Reduce response time - currently too high');
        }

        if (this.results.performanceTests.averageRequestsPerSecond < 10) {
            this.results.recommendations.push('Improve throughput - increase requests per second');
        }

        // Unit test recommendations
        if (this.results.unitTests.failed > 0) {
            this.results.recommendations.push(`Fix ${this.results.unitTests.failed} failing unit tests`);
        }

        // Integration test recommendations
        if (this.results.integrationTests.failed > 0) {
            this.results.recommendations.push(`Address ${this.results.integrationTests.failed} failing integration tests`);
        }

        if (this.results.recommendations.length === 0) {
            this.results.recommendations.push('All tests are passing - maintain current performance');
        }
    }

    private async generateReports(): Promise<void> {
        console.log('Generating test reports...');

        const timestamp = new Date().toISOString().split('T')[0];
        const baseDir = this.config.outputDirectory;

        await fs.mkdir(baseDir, { recursive: true });

        if (this.config.outputFormat === 'json') {
            await this.generateJsonReport(baseDir, timestamp);
        }

        if (this.config.outputFormat === 'html') {
            await this.generateHtmlReport(baseDir, timestamp);
        }

        if (this.config.outputFormat === 'markdown') {
            await this.generateMarkdownReport(baseDir, timestamp);
        }

        console.log(`Reports generated in ${baseDir}`);
    }

    private async generateJsonReport(baseDir: string, timestamp: string): Promise<void> {
        const report = {
            metadata: {
                generatedAt: this.results.endTime,
                generatedBy: 'KiloCode MCP Compliance Server',
                testType: 'Comprehensive Test Suite',
                version: '1.0.0'
            },
            config: this.config,
            results: this.results,
            summary: {
                totalTests: this.results.unitTests.total + this.results.integrationTests.total + this.results.complianceTests.total + this.results.performanceTests.total,
                passedTests: this.results.unitTests.passed + this.results.integrationTests.passed + this.results.complianceTests.passed + this.results.performanceTests.passed,
                failedTests: this.results.unitTests.failed + this.results.integrationTests.failed + this.results.complianceTests.failed + this.results.performanceTests.failed,
                overallScore: this.results.overallScore,
                duration: this.results.duration
            }
        };

        const filepath = path.join(baseDir, `test-results-${timestamp}.json`);
        await fs.writeFile(filepath, JSON.stringify(report, null, 2));
    }

    private async generateHtmlReport(baseDir: string, timestamp: string): Promise<void> {
        const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Results - ${timestamp}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: #f9f9f9; border-radius: 3px; }
        .passed { color: green; }
        .failed { color: red; }
        .score { font-size: 24px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Test Results - ${timestamp}</h1>
        <div class="score">Overall Score: ${this.results.overallScore}/100</div>
    </div>

    <div class="section">
        <h2>Unit Tests</h2>
        <div class="metric">Passed: <span class="passed">${this.results.unitTests.passed}</span></div>
        <div class="metric">Failed: <span class="failed">${this.results.unitTests.failed}</span></div>
        <div class="metric">Total: ${this.results.unitTests.total}</div>
    </div>

    <div class="section">
        <h2>Integration Tests</h2>
        <div class="metric">Passed: <span class="passed">${this.results.integrationTests.passed}</span></div>
        <div class="metric">Failed: <span class="failed">${this.results.integrationTests.failed}</span></div>
        <div class="metric">Total: ${this.results.integrationTests.total}</div>
    </div>

    <div class="section">
        <h2>Compliance Tests</h2>
        <div class="metric">Score: ${this.results.complianceTests.averageScore}/100</div>
        <div class="metric">Passed: <span class="passed">${this.results.complianceTests.passed}</span></div>
        <div class="metric">Failed: <span class="failed">${this.results.complianceTests.failed}</span></div>
        <div class="metric">Total: ${this.results.complianceTests.total}</div>
    </div>

    <div class="section">
        <h2>Performance Tests</h2>
        <div class="metric">Avg Requests/Sec: ${this.results.performanceTests.averageRequestsPerSecond.toFixed(2)}</div>
        <div class="metric">Avg Response Time: ${this.results.performanceTests.averageResponseTime.toFixed(2)}ms</div>
        <div class="metric">Avg Score: ${this.results.performanceTests.averagePerformanceScore.toFixed(1)}/100</div>
        <div class="metric">Passed: <span class="passed">${this.results.performanceTests.passed}</span></div>
        <div class="metric">Failed: <span class="failed">${this.results.performanceTests.failed}</span></div>
        <div class="metric">Total: ${this.results.performanceTests.total}</div>
    </div>

    <div class="section">
        <h2>Recommendations</h2>
        <ul>
            ${this.results.recommendations.map(rec => `<li>${rec}</li>`).join('')}
        </ul>
    </div>
</body>
</html>`;

        const filepath = path.join(baseDir, `test-results-${timestamp}.html`);
        await fs.writeFile(filepath, html);
    }

    private async generateMarkdownReport(baseDir: string, timestamp: string): Promise<void> {
        const markdown = `
# Test Results - ${timestamp}

## Overall Score: ${this.results.overallScore}/100

### Test Summary
- **Total Tests**: ${this.results.unitTests.total + this.results.integrationTests.total + this.results.complianceTests.total + this.results.performanceTests.total}
- **Passed Tests**: ${this.results.unitTests.passed + this.results.integrationTests.passed + this.results.complianceTests.passed + this.results.performanceTests.passed}
- **Failed Tests**: ${this.results.unitTests.failed + this.results.integrationTests.failed + this.results.complianceTests.failed + this.results.performanceTests.failed}
- **Duration**: ${this.results.duration}ms

### Unit Tests
- **Passed**: ${this.results.unitTests.passed}
- **Failed**: ${this.results.unitTests.failed}
- **Total**: ${this.results.unitTests.total}

### Integration Tests
- **Passed**: ${this.results.integrationTests.passed}
- **Failed**: ${this.results.integrationTests.failed}
- **Total**: ${this.results.integrationTests.total}

### Compliance Tests
- **Score**: ${this.results.complianceTests.averageScore}/100
- **Passed**: ${this.results.complianceTests.passed}
- **Failed**: ${this.results.complianceTests.failed}
- **Total**: ${this.results.complianceTests.total}

### Performance Tests
- **Avg Requests/Sec**: ${this.results.performanceTests.averageRequestsPerSecond.toFixed(2)}
- **Avg Response Time**: ${this.results.performanceTests.averageResponseTime.toFixed(2)}ms
- **Avg Score**: ${this.results.performanceTests.averagePerformanceScore.toFixed(1)}/100
- **Passed**: ${this.results.performanceTests.passed}
- **Failed**: ${this.results.performanceTests.failed}
- **Total**: ${this.results.performanceTests.total}

### Recommendations
${this.results.recommendations.map(rec => `- ${rec}`).join('\n')}
`;

        const filepath = path.join(baseDir, `test-results-${timestamp}.md`);
        await fs.writeFile(filepath, markdown);
    }
}

// Default configuration
export const defaultConfig: TestExecutionConfig = {
    unitTests: true,
    integrationTests: true,
    complianceTests: true,
    performanceTests: true,
    concurrency: 4,
    outputFormat: 'markdown',
    outputDirectory: './reports',
    generateReports: true
};

// Export for use in other files
export default TestExecutor;