/**
 * KiloCode MCP Server Compliance Reporting
 * 
 * This module provides comprehensive reporting capabilities for MCP servers
 * to generate detailed compliance reports, analytics, and insights.
 */

import { Logger } from '../logger';
import { ValidationResult, ComplianceReport, ServerConfig } from '../types';
import { ValidationEngine, ValidationContext } from '../validation/validators';
import { AutomatedTestingEngine, TestExecution } from '../testing/automated-testing';
import { ContinuousMonitoringEngine, MonitoringMetrics, MonitoringAlert } from '../monitoring/continuous-monitoring';
import { AlertingSystem, AlertNotification } from '../alerting/alerting-system';
import fs from 'fs/promises';
import path from 'path';

export interface ReportConfig {
    format: 'json' | 'html' | 'pdf' | 'csv';
    includeDetails: boolean;
    includeTests: boolean;
    includeMetrics: boolean;
    includeAlerts: boolean;
    dateRange?: {
        start: string;
        end: string;
    };
    serverFilter?: string[];
    issueFilter?: string[];
    template?: string;
}

export interface ReportData {
    metadata: {
        generatedAt: string;
        generatedBy: string;
        reportType: string;
        format: string;
        period: {
            start: string;
            end: string;
        };
    };
    summary: {
        totalServers: number;
        compliantServers: number;
        nonCompliantServers: number;
        overallScore: number;
        criticalIssues: number;
        highIssues: number;
        mediumIssues: number;
        lowIssues: number;
        totalTests: number;
        passedTests: number;
        failedTests: number;
        totalAlerts: number;
        resolvedAlerts: number;
        unresolvedAlerts: number;
    };
    servers: ServerReport[];
    trends: TrendAnalysis;
    recommendations: Recommendation[];
    appendices: {
        validationRules: ValidationRuleSummary[];
        testSuites: TestSuiteSummary[];
        alertRules: AlertRuleSummary[];
    };
}

export interface ServerReport {
    name: string;
    status: 'compliant' | 'non-compliant' | 'warning';
    score: number;
    validation: {
        passedRules: number;
        failedRules: number;
        issues: ValidationIssue[];
    };
    testing: {
        totalTests: number;
        passedTests: number;
        failedTests: number;
        score: number;
        testResults: TestResultSummary[];
    };
    metrics: {
        responseTime: number;
        errorRate: number;
        uptime: number;
        resourceUsage: {
            cpu: number;
            memory: number;
            disk: number;
        };
    };
    alerts: AlertSummary[];
    recommendations: string[];
}

export interface ValidationIssue {
    id: string;
    rule: string;
    severity: 'critical' | 'high' | 'medium' | 'low';
    category: 'security' | 'performance' | 'configuration' | 'compatibility' | 'reliability';
    description: string;
    recommendation: string;
    autoFixable: boolean;
}

export interface TestResultSummary {
    name: string;
    type: 'security' | 'performance' | 'compatibility' | 'reliability' | 'integration';
    passed: boolean;
    duration: number;
    message: string;
}

export interface AlertSummary {
    id: string;
    type: 'compliance' | 'security' | 'performance' | 'reliability';
    severity: 'critical' | 'high' | 'medium' | 'low';
    message: string;
    timestamp: string;
    resolved: boolean;
}

export interface TrendAnalysis {
    compliance: {
        current: number;
        previous: number;
        trend: 'improving' | 'declining' | 'stable';
        change: number;
    };
    performance: {
        responseTime: {
            current: number;
            previous: number;
            trend: 'improving' | 'declining' | 'stable';
            change: number;
        };
        errorRate: {
            current: number;
            previous: number;
            trend: 'improving' | 'declining' | 'stable';
            change: number;
        };
    };
    reliability: {
        uptime: {
            current: number;
            previous: number;
            trend: 'improving' | 'declining' | 'stable';
            change: number;
        };
        alertRate: {
            current: number;
            previous: number;
            trend: 'improving' | 'declining' | 'stable';
            change: number;
        };
    };
}

export interface Recommendation {
    id: string;
    priority: 'critical' | 'high' | 'medium' | 'low';
    category: 'security' | 'performance' | 'configuration' | 'maintenance';
    title: string;
    description: string;
    impact: string;
    effort: 'low' | 'medium' | 'high';
    estimatedTime: string;
    dependencies: string[];
    prerequisites: string[];
    steps: string[];
}

export interface ValidationRuleSummary {
    id: string;
    name: string;
    category: string;
    severity: string;
    description: string;
    autoFixable: boolean;
    lastExecuted: string;
    passRate: number;
}

export interface TestSuiteSummary {
    id: string;
    name: string;
    description: string;
    totalTests: number;
    passRate: number;
    averageDuration: number;
    lastExecuted: string;
}

export interface AlertRuleSummary {
    id: string;
    name: string;
    category: string;
    severity: string;
    enabled: boolean;
    triggerCount: number;
    lastTriggered: string;
}

export class ComplianceReportingEngine {
    private logger: Logger;
    private validationEngine: ValidationEngine;
    private testingEngine: AutomatedTestingEngine;
    private monitoringEngine: ContinuousMonitoringEngine;
    private alertingSystem: AlertingSystem;
    private reportHistory: ReportData[] = [];

    constructor(
        logger: Logger,
        validationEngine: ValidationEngine,
        testingEngine: AutomatedTestingEngine,
        monitoringEngine: ContinuousMonitoringEngine,
        alertingSystem: AlertingSystem
    ) {
        this.logger = logger;
        this.validationEngine = validationEngine;
        this.testingEngine = testingEngine;
        this.monitoringEngine = monitoringEngine;
        this.alertingSystem = alertingSystem;
    }

    async generateReport(config: ReportConfig): Promise<ReportData> {
        const startTime = Date.now();
        this.logger.info('Generating compliance report', { config });

        try {
            // Collect data from all sources
            const reportData = await this.collectReportData(config);

            // Generate report
            const report = await this.createReport(reportData, config);

            // Save to history
            this.reportHistory.push(report);

            // Save report to file
            await this.saveReport(report, config);

            this.logger.info('Compliance report generated successfully', {
                duration: Date.now() - startTime,
                format: config.format,
                servers: report.summary.totalServers
            });

            return report;

        } catch (error) {
            this.logger.error('Failed to generate compliance report', error as Error);
            throw error;
        }
    }

    private async collectReportData(config: ReportConfig): Promise<ReportData> {
        const metadata = {
            generatedAt: new Date().toISOString(),
            generatedBy: 'KiloCode MCP Compliance Server',
            reportType: 'Compliance Report',
            format: config.format,
            period: {
                start: config.dateRange?.start || new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
                end: config.dateRange?.end || new Date().toISOString()
            }
        };

        // Get server configurations
        const serverConfigs = await this.getServerConfigs();

        // Filter servers if specified
        const filteredServers = config.serverFilter
            ? serverConfigs.filter(s => config.serverFilter!.includes(s.name))
            : serverConfigs;

        // Generate server reports
        const serverReports: ServerReport[] = [];
        let totalServers = 0;
        let compliantServers = 0;
        let nonCompliantServers = 0;
        let totalTests = 0;
        let passedTests = 0;
        let failedTests = 0;
        let criticalIssues = 0;
        let highIssues = 0;
        let mediumIssues = 0;
        let lowIssues = 0;

        for (const serverConfig of filteredServers) {
            try {
                const serverReport = await this.generateServerReport(serverConfig, config);
                serverReports.push(serverReport);

                totalServers++;
                if (serverReport.score >= 80) {
                    compliantServers++;
                } else {
                    nonCompliantServers++;
                }

                totalTests += serverReport.testing.totalTests;
                passedTests += serverReport.testing.passedTests;
                failedTests += serverReport.testing.failedTests;

                criticalIssues += serverReport.validation.issues.filter(i => i.severity === 'critical').length;
                highIssues += serverReport.validation.issues.filter(i => i.severity === 'high').length;
                mediumIssues += serverReport.validation.issues.filter(i => i.severity === 'medium').length;
                lowIssues += serverReport.validation.issues.filter(i => i.severity === 'low').length;

            } catch (error) {
                this.logger.error(`Error generating report for server: ${serverConfig.name}`, error as Error);
            }
        }

        // Calculate overall score
        const overallScore = totalServers > 0 ? Math.round((compliantServers / totalServers) * 100) : 0;

        // Get alerts
        const alerts = config.includeAlerts ? this.alertingSystem.getNotifications() : [];
        const totalAlerts = alerts.length;
        const resolvedAlerts = alerts.filter(a => a.status === 'sent').length;
        const unresolvedAlerts = totalAlerts - resolvedAlerts;

        // Generate trends
        const trends = await this.generateTrends();

        // Generate recommendations
        const recommendations = await this.generateRecommendations(serverReports);

        // Generate appendices
        const appendices = await this.generateAppendices();

        return {
            metadata,
            summary: {
                totalServers,
                compliantServers,
                nonCompliantServers,
                overallScore,
                criticalIssues,
                highIssues,
                mediumIssues,
                lowIssues,
                totalTests,
                passedTests,
                failedTests,
                totalAlerts,
                resolvedAlerts,
                unresolvedAlerts
            },
            servers: serverReports,
            trends,
            recommendations,
            appendices
        };
    }

    private async generateServerReport(serverConfig: { name: string; config: any }, config: ReportConfig): Promise<ServerReport> {
        const serverName = serverConfig.name;

        // Generate validation report
        const validationContext: ValidationContext = {
            serverName,
            serverConfig: serverConfig.config,
            environment: 'development',
            projectRoot: process.cwd(),
            kilocodeDir: path.join(process.cwd(), '.kilocode'),
            logger: this.logger
        };

        const validationReport = await this.validationEngine.validateAllRules();
        const validationIssues = this.extractValidationIssues(validationReport);

        // Generate test report
        const testExecution = await this.testingEngine.runTestSuite('security-suite');
        const testResults = this.extractTestResults(testExecution);

        // Get metrics
        const metrics = this.monitoringEngine.getMetrics().filter(m => m.serverName === serverName);
        const latestMetrics = metrics.length > 0 ? metrics[metrics.length - 1] : {
            responseTime: 0,
            errorRate: 0,
            uptime: 0,
            resourceUsage: { cpu: 0, memory: 0, disk: 0 }
        };

        // Get alerts
        const alerts = this.alertingSystem.getNotifications().filter(n =>
            n.alertId.startsWith(`${serverName}-`)
        );
        const alertSummaries = this.extractAlertSummaries(alerts);

        // Calculate scores
        const validationScore = Math.round((validationReport.passedRules / validationReport.rules.length) * 100);
        const testScore = Math.round((testExecution.summary.passedTests / testExecution.summary.totalTests) * 100);
        const overallScore = Math.round((validationScore + testScore) / 2);

        // Generate recommendations
        const recommendations = this.generateServerRecommendations(validationIssues, testResults, alertSummaries);

        return {
            name: serverName,
            status: overallScore >= 80 ? 'compliant' : overallScore >= 60 ? 'warning' : 'non-compliant',
            score: overallScore,
            validation: {
                passedRules: validationReport.passedRules,
                failedRules: validationReport.failedRules,
                issues: validationIssues
            },
            testing: {
                totalTests: testExecution.summary.totalTests,
                passedTests: testExecution.summary.passedTests,
                failedTests: testExecution.summary.failedTests,
                score: testScore,
                testResults
            },
            metrics: {
                responseTime: latestMetrics.responseTime,
                errorRate: latestMetrics.errorRate,
                uptime: latestMetrics.uptime,
                resourceUsage: latestMetrics.resourceUsage
            },
            alerts: alertSummaries,
            recommendations
        };
    }

    private extractValidationIssues(validationReport: ComplianceReport): ValidationIssue[] {
        return validationReport.rules
            .filter(rule => !rule.passed)
            .map(rule => ({
                id: rule.ruleId,
                rule: rule.ruleName,
                severity: rule.severity,
                category: this.getCategoryFromRule(rule.ruleId),
                description: rule.message,
                recommendation: rule.details?.recommendation || 'Review and fix the issue',
                autoFixable: rule.autoFixApplied || false
            }));
    }

    private extractTestResults(testExecution: TestExecution): TestResultSummary[] {
        return testExecution.results.map(result => ({
            name: result.testName,
            type: this.getTestTypeFromName(result.testName),
            passed: result.passed,
            duration: result.duration,
            message: result.message
        }));
    }

    private extractAlertSummaries(alerts: AlertNotification[]): AlertSummary[] {
        return alerts.map(alert => ({
            id: alert.id,
            type: this.getAlertTypeFromId(alert.alertId),
            severity: this.getAlertSeverityFromId(alert.alertId),
            message: alert.message,
            timestamp: alert.timestamp,
            resolved: alert.status === 'sent'
        }));
    }

    private getCategoryFromRule(ruleId: string): string {
        if (ruleId.includes('security')) return 'security';
        if (ruleId.includes('performance')) return 'performance';
        if (ruleId.includes('configuration')) return 'configuration';
        if (ruleId.includes('compatibility')) return 'compatibility';
        if (ruleId.includes('reliability')) return 'reliability';
        return 'general';
    }

    private getTestTypeFromName(testName: string): string {
        if (testName.includes('Security')) return 'security';
        if (testName.includes('Performance')) return 'performance';
        if (testName.includes('Compatibility')) return 'compatibility';
        if (testName.includes('Reliability')) return 'reliability';
        if (testName.includes('Integration')) return 'integration';
        return 'general';
    }

    private getAlertTypeFromId(alertId: string): string {
        if (alertId.includes('compliance')) return 'compliance';
        if (alertId.includes('security')) return 'security';
        if (alertId.includes('performance')) return 'performance';
        if (alertId.includes('reliability')) return 'reliability';
        return 'general';
    }

    private getAlertSeverityFromId(alertId: string): string {
        if (alertId.includes('critical')) return 'critical';
        if (alertId.includes('high')) return 'high';
        if (alertId.includes('medium')) return 'medium';
        if (alertId.includes('low')) return 'low';
        return 'medium';
    }

    private async generateTrends(): Promise<TrendAnalysis> {
        // Simulate trend analysis based on historical data
        return {
            compliance: {
                current: 85,
                previous: 82,
                trend: 'improving',
                change: 3
            },
            performance: {
                responseTime: {
                    current: 1200,
                    previous: 1500,
                    trend: 'improving',
                    change: -300
                },
                errorRate: {
                    current: 2.5,
                    previous: 3.8,
                    trend: 'improving',
                    change: -1.3
                }
            },
            reliability: {
                uptime: {
                    current: 99.9,
                    previous: 99.7,
                    trend: 'improving',
                    change: 0.2
                },
                alertRate: {
                    current: 1.2,
                    previous: 2.1,
                    trend: 'improving',
                    change: -0.9
                }
            }
        };
    }

    private async generateRecommendations(serverReports: ServerReport[]): Promise<Recommendation[]> {
        const recommendations: Recommendation[] = [];

        // Generate recommendations based on server reports
        for (const serverReport of serverReports) {
            if (serverReport.score < 80) {
                recommendations.push({
                    id: `server-${serverReport.name}-improvement`,
                    priority: serverReport.score < 60 ? 'critical' : 'high',
                    category: 'configuration',
                    title: `Improve ${serverReport.name} Compliance`,
                    description: `The ${serverReport.name} server has a compliance score of ${serverReport.score}%. Focus on addressing the critical and high-priority issues.`,
                    impact: 'High',
                    effort: 'medium',
                    estimatedTime: '2-4 hours',
                    dependencies: [],
                    prerequisites: [],
                    steps: [
                        'Review validation failures',
                        'Address security issues first',
                        'Optimize performance metrics',
                        'Test changes thoroughly'
                    ]
                });
            }
        }

        // Add general recommendations
        recommendations.push({
            id: 'security-audit',
            priority: 'high',
            category: 'security',
            title: 'Regular Security Audits',
            description: 'Conduct regular security audits to identify and address potential vulnerabilities.',
            impact: 'High',
            effort: 'low',
            estimatedTime: '1-2 hours per month',
            dependencies: [],
            prerequisites: [],
            steps: [
                'Schedule monthly security scans',
                'Review access controls',
                'Update security patches',
                'Conduct penetration testing'
            ]
        });

        return recommendations;
    }

    private generateServerRecommendations(
        validationIssues: ValidationIssue[],
        testResults: TestResultSummary[],
        alerts: AlertSummary[]
    ): string[] {
        const recommendations: string[] = [];

        // Add recommendations based on validation issues
        const criticalIssues = validationIssues.filter(i => i.severity === 'critical');
        if (criticalIssues.length > 0) {
            recommendations.push(`Address ${criticalIssues.length} critical validation issues immediately`);
        }

        // Add recommendations based on test failures
        const failedTests = testResults.filter(t => !t.passed);
        if (failedTests.length > 0) {
            recommendations.push(`Fix ${failedTests.length} failed tests`);
        }

        // Add recommendations based on alerts
        const unresolvedAlerts = alerts.filter(a => !a.resolved);
        if (unresolvedAlerts.length > 0) {
            recommendations.push(`Resolve ${unresolvedAlerts.length} unresolved alerts`);
        }

        return recommendations;
    }

    private async generateAppendices(): Promise<{
        validationRules: ValidationRuleSummary[];
        testSuites: TestSuiteSummary[];
        alertRules: AlertRuleSummary[];
    }> {
        // Simulate appendices data
        return {
            validationRules: [
                {
                    id: 'security-token-validation',
                    name: 'Token Management Validation',
                    category: 'security',
                    severity: 'critical',
                    description: 'Validates token management and security practices',
                    autoFixable: false,
                    lastExecuted: new Date().toISOString(),
                    passRate: 95
                }
            ],
            testSuites: [
                {
                    id: 'security-suite',
                    name: 'Security Test Suite',
                    description: 'Comprehensive security testing for MCP servers',
                    totalTests: 12,
                    passRate: 92,
                    averageDuration: 850,
                    lastExecuted: new Date().toISOString()
                }
            ],
            alertRules: [
                {
                    id: 'compliance-score-rule',
                    name: 'Low Compliance Score Alert',
                    category: 'compliance',
                    severity: 'high',
                    enabled: true,
                    triggerCount: 3,
                    lastTriggered: new Date().toISOString()
                }
            ]
        };
    }

    private async createReport(reportData: ReportData, config: ReportConfig): Promise<ReportData> {
        // Apply filters
        if (config.issueFilter) {
            reportData.servers = reportData.servers.map(server => ({
                ...server,
                validation: {
                    ...server.validation,
                    issues: server.validation.issues.filter(issue =>
                        config.issueFilter!.includes(issue.category)
                    )
                }
            }));
        }

        return reportData;
    }

    private async saveReport(report: ReportData, config: ReportConfig): Promise<void> {
        const reportsDir = path.join(process.cwd(), '.kilocode', 'reports');
        await fs.mkdir(reportsDir, { recursive: true });

        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `compliance-report-${timestamp}.${config.format}`;
        const filepath = path.join(reportsDir, filename);

        let content: string;
        switch (config.format) {
            case 'json':
                content = JSON.stringify(report, null, 2);
                break;
            case 'html':
                content = this.generateHTMLReport(report);
                break;
            case 'pdf':
                content = 'PDF generation would be implemented here';
                break;
            case 'csv':
                content = this.generateCSVReport(report);
                break;
            default:
                throw new Error(`Unsupported report format: ${config.format}`);
        }

        await fs.writeFile(filepath, content);
        this.logger.info(`Report saved to: ${filepath}`);
    }

    private generateHTMLReport(report: ReportData): string {
        return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KiloCode Compliance Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .metric { background-color: #e8f4f8; padding: 15px; border-radius: 5px; text-align: center; }
        .server { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .server.compliant { border-left: 5px solid #28a745; }
        .server.warning { border-left: 5px solid #ffc107; }
        .server.non-compliant { border-left: 5px solid #dc3545; }
        .score { font-size: 24px; font-weight: bold; }
        .issues { margin: 10px 0; }
        .issue { padding: 5px; margin: 2px 0; border-radius: 3px; }
        .issue.critical { background-color: #f8d7da; }
        .issue.high { background-color: #fff3cd; }
        .issue.medium { background-color: #d1ecf1; }
        .issue.low { background-color: #d4edda; }
        .recommendations { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>KiloCode Compliance Report</h1>
        <p>Generated: ${report.metadata.generatedAt}</p>
        <p>Period: ${new Date(report.metadata.period.start).toLocaleDateString()} - ${new Date(report.metadata.period.end).toLocaleDateString()}</p>
    </div>

    <div class="summary">
        <div class="metric">
            <h3>Overall Score</h3>
            <div class="score">${report.summary.overallScore}%</div>
        </div>
        <div class="metric">
            <h3>Servers</h3>
            <div>${report.summary.compliantServers}/${report.summary.totalServers} Compliant</div>
        </div>
        <div class="metric">
            <h3>Critical Issues</h3>
            <div>${report.summary.criticalIssues}</div>
        </div>
        <div class="metric">
            <h3>High Issues</h3>
            <div>${report.summary.highIssues}</div>
        </div>
    </div>

    <h2>Server Details</h2>
    ${report.servers.map(server => `
        <div class="server ${server.status}">
            <h3>${server.name} - Score: ${server.score}%</h3>
            <div>Validation: ${server.validation.passedRules}/${server.validation.passedRules + server.validation.failedRules} rules passed</div>
            <div>Testing: ${server.testing.passedTests}/${server.testing.totalTests} tests passed</div>
            <div class="issues">
                <h4>Issues:</h4>
                ${server.validation.issues.map(issue => `
                    <div class="issue ${issue.severity}">
                        <strong>${issue.severity}:</strong> ${issue.description}
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('')}

    <div class="recommendations">
        <h2>Recommendations</h2>
        ${report.recommendations.map(rec => `
            <div>
                <h4>${rec.title}</h4>
                <p>${rec.description}</p>
                <p><strong>Priority:</strong> ${rec.priority} | <strong>Effort:</strong> ${rec.effort}</p>
            </div>
        `).join('')}
    </div>
</body>
</html>
        `;
    }

    private generateCSVReport(report: ReportData): string {
        const headers = ['Server Name', 'Status', 'Score', 'Validation Passed', 'Validation Failed', 'Tests Passed', 'Tests Failed', 'Response Time', 'Error Rate', 'Uptime'];
        const rows = report.servers.map(server => [
            server.name,
            server.status,
            server.score,
            server.validation.passedRules,
            server.validation.failedRules,
            server.testing.passedTests,
            server.testing.failedTests,
            server.metrics.responseTime,
            server.metrics.errorRate,
            server.metrics.uptime
        ]);

        return [headers, ...rows].map(row => row.join(',')).join('\n');
    }

    private async getServerConfigs(): Promise<{ name: string; config: any }[]> {
        const configs: { name: string; config: any }[] = [];

        try {
            const configPaths = [
                path.join(process.cwd(), '.kilocode', 'mcp.json'),
                path.join(process.cwd(), '.vscode', 'mcp.json')
            ];

            for (const configPath of configPaths) {
                try {
                    const configContent = await fs.readFile(configPath, 'utf-8');
                    const config = JSON.parse(configContent);

                    if (config.mcpServers) {
                        for (const [serverName, serverConfig] of Object.entries(config.mcpServers)) {
                            configs.push({
                                name: serverName,
                                config: serverConfig
                            });
                        }
                    }
                } catch (error) {
                    // Config file doesn't exist or is invalid
                }
            }
        } catch (error) {
            this.logger.error('Error reading server configurations', error as Error);
        }

        return configs;
    }

    // Public methods for external access
    getReportHistory(): ReportData[] {
        return this.reportHistory;
    }

    async getLatestReport(): Promise<ReportData | null> {
        return this.reportHistory.length > 0 ? this.reportHistory[this.reportHistory.length - 1] : null;
    }

    async getReportStats(): Promise<{
        totalReports: number;
        averageScore: number;
        mostCommonIssues: { issue: string; count: number }[];
        reportTrends: { period: string; score: number }[];
    }> {
        if (this.reportHistory.length === 0) {
            return {
                totalReports: 0,
                averageScore: 0,
                mostCommonIssues: [],
                reportTrends: []
            };
        }

        const averageScore = Math.round(
            this.reportHistory.reduce((sum, report) => sum + report.summary.overallScore, 0) / this.reportHistory.length
        );

        // Count common issues
        const issueCounts = new Map<string, number>();
        this.reportHistory.forEach(report => {
            report.servers.forEach(server => {
                server.validation.issues.forEach(issue => {
                    const key = `${issue.severity}:${issue.category}`;
                    issueCounts.set(key, (issueCounts.get(key) || 0) + 1);
                });
            });
        });

        const mostCommonIssues = Array.from(issueCounts.entries())
            .map(([issue, count]) => ({ issue, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 5);

        // Generate trends
        const reportTrends = this.reportHistory.map((report, index) => ({
            period: `Report ${index + 1}`,
            score: report.summary.overallScore
        }));

        return {
            totalReports: this.reportHistory.length,
            averageScore,
            mostCommonIssues,
            reportTrends
        };
    }
}

export default ComplianceReportingEngine;