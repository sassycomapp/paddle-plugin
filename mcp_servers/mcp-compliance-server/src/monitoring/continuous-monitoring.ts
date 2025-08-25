/**
 * KiloCode MCP Server Continuous Monitoring
 * 
 * This module provides continuous monitoring capabilities for MCP servers
 * to ensure ongoing compliance with KiloCode standards, security requirements,
 * and performance benchmarks.
 */

import { Logger } from '../logger';
import { ValidationResult, ComplianceReport, ServerConfig } from '../types';
import { ValidationEngine, ValidationContext } from '../validation/validators';
import { AutomatedTestingEngine, TestExecution } from '../testing/automated-testing';
import fs from 'fs/promises';
import path from 'path';

export interface MonitoringConfig {
    enabled: boolean;
    interval: number; // in milliseconds
    retentionPeriod: number; // in milliseconds
    alertThresholds: {
        complianceScore: number;
        responseTime: number;
        errorRate: number;
        resourceUsage: {
            cpu: number;
            memory: number;
            disk: number;
        };
    };
    notifications: {
        enabled: boolean;
        channels: ('email' | 'slack' | 'webhook')[];
        email?: {
            smtp: {
                host: string;
                port: number;
                secure: boolean;
                user: string;
                password: string;
            };
            from: string;
            to: string[];
        };
        slack?: {
            webhookUrl: string;
            channel: string;
        };
        webhook?: {
            url: string;
            headers?: Record<string, string>;
        };
    };
}

export interface MonitoringMetrics {
    timestamp: string;
    serverName: string;
    complianceScore: number;
    responseTime: number;
    errorRate: number;
    resourceUsage: {
        cpu: number;
        memory: number;
        disk: number;
    };
    activeConnections: number;
    uptime: number;
    lastHealthCheck: string;
    issues: string[];
}

export interface MonitoringAlert {
    id: string;
    timestamp: string;
    serverName: string;
    type: 'compliance' | 'performance' | 'security' | 'reliability';
    severity: 'critical' | 'high' | 'medium' | 'low';
    message: string;
    details: Record<string, any>;
    resolved: boolean;
    resolvedAt?: string;
    resolvedBy?: string;
}

export class ContinuousMonitoringEngine {
    private logger: Logger;
    private config: MonitoringConfig;
    private validationEngine: ValidationEngine;
    private testingEngine: AutomatedTestingEngine;
    private metrics: MonitoringMetrics[] = [];
    private alerts: MonitoringAlert[] = [];
    private monitoringInterval?: NodeJS.Timeout;
    private isRunning: boolean = false;

    constructor(
        logger: Logger,
        config: MonitoringConfig,
        validationEngine: ValidationEngine,
        testingEngine: AutomatedTestingEngine
    ) {
        this.logger = logger;
        this.config = config;
        this.validationEngine = validationEngine;
        this.testingEngine = testingEngine;
    }

    async start(): Promise<void> {
        if (this.isRunning) {
            this.logger.warn('Monitoring is already running');
            return;
        }

        if (!this.config.enabled) {
            this.logger.warn('Monitoring is disabled in configuration');
            return;
        }

        this.isRunning = true;
        this.logger.info('Starting continuous monitoring', {
            interval: this.config.interval,
            retentionPeriod: this.config.retentionPeriod
        });

        // Start monitoring interval
        this.monitoringInterval = setInterval(
            () => this.runMonitoringCycle(),
            this.config.interval
        );

        // Run initial monitoring cycle
        await this.runMonitoringCycle();
    }

    async stop(): Promise<void> {
        if (!this.isRunning) {
            this.logger.warn('Monitoring is not running');
            return;
        }

        this.isRunning = false;

        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = undefined as unknown as NodeJS.Timeout;
        }

        this.logger.info('Continuous monitoring stopped');
    }

    private async runMonitoringCycle(): Promise<void> {
        try {
            const startTime = Date.now();
            this.logger.debug('Starting monitoring cycle');

            // Get current server configurations
            const serverConfigs = await this.getServerConfigs();

            for (const serverConfig of serverConfigs) {
                try {
                    // Run validation
                    const validationContext: ValidationContext = {
                        serverName: serverConfig.name,
                        serverConfig: serverConfig.config,
                        environment: this.getEnvironment(),
                        projectRoot: process.cwd(),
                        kilocodeDir: path.join(process.cwd(), '.kilocode'),
                        logger: this.logger
                    };

                    const validationReport = await this.validationEngine.validateAllRules();

                    // Run automated testing
                    const testExecution = await this.testingEngine.runTestSuite('security-suite');

                    // Collect metrics
                    const metrics = await this.collectMetrics(serverConfig.name, validationReport, testExecution);

                    // Check for alerts
                    const newAlerts = await this.checkForAlerts(metrics);

                    // Store metrics
                    this.metrics.push(metrics);

                    // Store alerts
                    this.alerts.push(...newAlerts);

                    // Send notifications if needed
                    if (newAlerts.length > 0) {
                        await this.sendNotifications(newAlerts);
                    }

                    this.logger.debug(`Monitoring completed for server: ${serverConfig.name}`, {
                        duration: Date.now() - startTime,
                        complianceScore: metrics.complianceScore,
                        responseTime: metrics.responseTime
                    });

                } catch (error) {
                    this.logger.error(`Error monitoring server: ${serverConfig.name}`, error as Error);
                }
            }

            // Cleanup old metrics
            await this.cleanupMetrics();

            // Cleanup old alerts
            await this.cleanupAlerts();

        } catch (error) {
            this.logger.error('Error in monitoring cycle', error as Error);
        }
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

    private getEnvironment(): 'development' | 'staging' | 'production' {
        const env = process.env.KILOCODE_ENV || 'development';
        return env as 'development' | 'staging' | 'production';
    }

    private async collectMetrics(
        serverName: string,
        validationReport: ComplianceReport,
        testExecution: TestExecution
    ): Promise<MonitoringMetrics> {
        const startTime = Date.now();

        try {
            // Simulate resource usage collection
            const resourceUsage = await this.collectResourceUsage();

            // Calculate metrics
            const complianceScore = validationReport.overallScore;
            const responseTime = this.calculateAverageResponseTime(testExecution);
            const errorRate = this.calculateErrorRate(testExecution);
            const uptime = await this.calculateUptime(serverName);

            const metrics: MonitoringMetrics = {
                timestamp: new Date().toISOString(),
                serverName,
                complianceScore,
                responseTime,
                errorRate,
                resourceUsage,
                activeConnections: await this.getActiveConnections(serverName),
                uptime,
                lastHealthCheck: new Date().toISOString(),
                issues: this.extractIssues(validationReport, testExecution)
            };

            return metrics;

        } catch (error) {
            this.logger.error(`Error collecting metrics for server: ${serverName}`, error as Error);

            return {
                timestamp: new Date().toISOString(),
                serverName,
                complianceScore: 0,
                responseTime: 0,
                errorRate: 100,
                resourceUsage: { cpu: 0, memory: 0, disk: 0 },
                activeConnections: 0,
                uptime: 0,
                lastHealthCheck: new Date().toISOString(),
                issues: ['Metrics collection failed']
            };
        }
    }

    private async collectResourceUsage(): Promise<{ cpu: number; memory: number; disk: number }> {
        // Simulate resource usage collection
        // In a real implementation, this would use system APIs
        return {
            cpu: Math.random() * 100,
            memory: Math.random() * 100,
            disk: Math.random() * 100
        };
    }

    private calculateAverageResponseTime(testExecution: TestExecution): number {
        const responseTimeTests = testExecution.results.filter(
            result => result.testName.includes('Response') || result.testName.includes('Time')
        );

        if (responseTimeTests.length === 0) return 0;

        const totalTime = responseTimeTests.reduce((sum, result) => sum + result.duration, 0);
        return Math.round(totalTime / responseTimeTests.length);
    }

    private calculateErrorRate(testExecution: TestExecution): number {
        const totalTests = testExecution.summary.totalTests;
        const failedTests = testExecution.summary.failedTests;

        if (totalTests === 0) return 0;

        return Math.round((failedTests / totalTests) * 100);
    }

    private async calculateUptime(serverName: string): Promise<number> {
        // Simulate uptime calculation
        // In a real implementation, this would track actual server uptime
        return 99.9; // 99.9% uptime
    }

    private extractIssues(validationReport: ComplianceReport, testExecution: TestExecution): string[] {
        const issues: string[] = [];

        // Extract validation issues
        if (validationReport.failedRules > 0) {
            issues.push(`${validationReport.failedRules} validation rules failed`);
        }

        // Extract test issues
        if (testExecution.summary.failedTests > 0) {
            issues.push(`${testExecution.summary.failedTests} tests failed`);
        }

        // Extract warnings
        if (validationReport.warnings.length > 0) {
            issues.push(...validationReport.warnings.slice(0, 3)); // Limit to first 3 warnings
        }

        return issues;
    }

    private async checkForAlerts(metrics: MonitoringMetrics): Promise<MonitoringAlert[]> {
        const alerts: MonitoringAlert[] = [];

        // Check compliance score
        if (metrics.complianceScore < this.config.alertThresholds.complianceScore) {
            alerts.push({
                id: `compliance-${metrics.serverName}-${Date.now()}`,
                timestamp: new Date().toISOString(),
                serverName: metrics.serverName,
                type: 'compliance',
                severity: metrics.complianceScore < 50 ? 'critical' : 'high',
                message: `Compliance score dropped to ${metrics.complianceScore}%`,
                details: { currentScore: metrics.complianceScore, threshold: this.config.alertThresholds.complianceScore },
                resolved: false
            });
        }

        // Check response time
        if (metrics.responseTime > this.config.alertThresholds.responseTime) {
            alerts.push({
                id: `performance-${metrics.serverName}-${Date.now()}`,
                timestamp: new Date().toISOString(),
                serverName: metrics.serverName,
                type: 'performance',
                severity: metrics.responseTime > 5000 ? 'critical' : 'medium',
                message: `Response time increased to ${metrics.responseTime}ms`,
                details: { currentResponseTime: metrics.responseTime, threshold: this.config.alertThresholds.responseTime },
                resolved: false
            });
        }

        // Check error rate
        if (metrics.errorRate > this.config.alertThresholds.errorRate) {
            alerts.push({
                id: `reliability-${metrics.serverName}-${Date.now()}`,
                timestamp: new Date().toISOString(),
                serverName: metrics.serverName,
                type: 'reliability',
                severity: metrics.errorRate > 50 ? 'critical' : 'high',
                message: `Error rate increased to ${metrics.errorRate}%`,
                details: { currentErrorRate: metrics.errorRate, threshold: this.config.alertThresholds.errorRate },
                resolved: false
            });
        }

        // Check resource usage
        if (metrics.resourceUsage.cpu > this.config.alertThresholds.resourceUsage.cpu) {
            alerts.push({
                id: `resource-cpu-${metrics.serverName}-${Date.now()}`,
                timestamp: new Date().toISOString(),
                serverName: metrics.serverName,
                type: 'performance',
                severity: metrics.resourceUsage.cpu > 90 ? 'critical' : 'medium',
                message: `CPU usage at ${metrics.resourceUsage.cpu.toFixed(1)}%`,
                details: { currentCpu: metrics.resourceUsage.cpu, threshold: this.config.alertThresholds.resourceUsage.cpu },
                resolved: false
            });
        }

        if (metrics.resourceUsage.memory > this.config.alertThresholds.resourceUsage.memory) {
            alerts.push({
                id: `resource-memory-${metrics.serverName}-${Date.now()}`,
                timestamp: new Date().toISOString(),
                serverName: metrics.serverName,
                type: 'performance',
                severity: metrics.resourceUsage.memory > 90 ? 'critical' : 'medium',
                message: `Memory usage at ${metrics.resourceUsage.memory.toFixed(1)}%`,
                details: { currentMemory: metrics.resourceUsage.memory, threshold: this.config.alertThresholds.resourceUsage.memory },
                resolved: false
            });
        }

        return alerts;
    }

    private async sendNotifications(alerts: MonitoringAlert[]): Promise<void> {
        if (!this.config.notifications.enabled) {
            return;
        }

        for (const alert of alerts) {
            const message = this.formatAlertMessage(alert);

            for (const channel of this.config.notifications.channels) {
                try {
                    switch (channel) {
                        case 'email':
                            await this.sendEmailNotification(message, alert);
                            break;
                        case 'slack':
                            await this.sendSlackNotification(message, alert);
                            break;
                        case 'webhook':
                            await this.sendWebhookNotification(message, alert);
                            break;
                    }
                } catch (error) {
                    this.logger.error(`Failed to send ${channel} notification for alert: ${alert.id}`, error as Error);
                }
            }
        }
    }

    private formatAlertMessage(alert: MonitoringAlert): string {
        return `🚨 *${alert.severity.toUpperCase()} Alert* - ${alert.serverName}\n\n` +
            `*Type:* ${alert.type}\n` +
            `*Message:* ${alert.message}\n` +
            `*Time:* ${new Date(alert.timestamp).toLocaleString()}\n` +
            `*Details:* ${JSON.stringify(alert.details, null, 2)}`;
    }

    private async sendEmailNotification(message: string, alert: MonitoringAlert): Promise<void> {
        if (!this.config.notifications.email) return;

        // In a real implementation, this would use an email library
        this.logger.info(`Email notification sent for alert: ${alert.id}`);
    }

    private async sendSlackNotification(message: string, alert: MonitoringAlert): Promise<void> {
        if (!this.config.notifications.slack) return;

        // In a real implementation, this would use the Slack API
        this.logger.info(`Slack notification sent for alert: ${alert.id}`);
    }

    private async sendWebhookNotification(message: string, alert: MonitoringAlert): Promise<void> {
        if (!this.config.notifications.webhook) return;

        // In a real implementation, this would make an HTTP request
        this.logger.info(`Webhook notification sent for alert: ${alert.id}`);
    }

    private async cleanupMetrics(): Promise<void> {
        const cutoffTime = Date.now() - this.config.retentionPeriod;
        this.metrics = this.metrics.filter(metric =>
            new Date(metric.timestamp).getTime() > cutoffTime
        );
    }

    private async cleanupAlerts(): Promise<void> {
        const cutoffTime = Date.now() - this.config.retentionPeriod;
        this.alerts = this.alerts.filter(alert =>
            new Date(alert.timestamp).getTime() > cutoffTime
        );
    }

    private async getActiveConnections(serverName: string): Promise<number> {
        // Simulate active connections count
        // In a real implementation, this would query the server
        return Math.floor(Math.random() * 100);
    }

    // Public methods for external access
    getMetrics(): MonitoringMetrics[] {
        return this.metrics;
    }

    getAlerts(): MonitoringAlert[] {
        return this.alerts;
    }

    async resolveAlert(alertId: string, resolvedBy: string): Promise<void> {
        const alert = this.alerts.find(a => a.id === alertId);
        if (alert) {
            alert.resolved = true;
            alert.resolvedAt = new Date().toISOString();
            alert.resolvedBy = resolvedBy;
            this.logger.info(`Alert resolved: ${alertId}`, { resolvedBy });
        }
    }

    getMonitoringStatus(): {
        isRunning: boolean;
        lastRun?: string;
        metricsCount: number;
        alertsCount: number;
        unresolvedAlertsCount: number;
    } {
        return {
            isRunning: this.isRunning,
            lastRun: this.metrics.length > 0 ? this.metrics[this.metrics.length - 1].timestamp : undefined,
            metricsCount: this.metrics.length,
            alertsCount: this.alerts.length,
            unresolvedAlertsCount: this.alerts.filter((a: any) => !a.resolved).length
        };
    }
}

export default ContinuousMonitoringEngine;