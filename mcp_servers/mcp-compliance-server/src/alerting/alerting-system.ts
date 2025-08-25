/**
 * KiloCode MCP Server Alerting System
 * 
 * This module provides comprehensive alerting capabilities for MCP servers
 * to notify administrators of compliance violations, security issues,
 * performance problems, and reliability concerns.
 */

import { Logger } from '../logger';
import { MonitoringAlert, MonitoringConfig } from '../monitoring/continuous-monitoring';
import { ValidationResult, ComplianceReport } from '../types';

export interface AlertRule {
    id: string;
    name: string;
    description: string;
    enabled: boolean;
    condition: (data: any) => boolean;
    severity: 'critical' | 'high' | 'medium' | 'low';
    category: 'compliance' | 'security' | 'performance' | 'reliability';
    channels: ('email' | 'slack' | 'webhook' | 'sms')[];
    throttle: {
        enabled: boolean;
        window: number; // milliseconds
        maxAlerts: number;
    };
    escalation: {
        enabled: boolean;
        levels: {
            level: number;
            delay: number; // milliseconds
            recipients: string[];
        }[];
    };
}

export interface AlertNotification {
    id: string;
    alertId: string;
    timestamp: string;
    channel: string;
    recipient: string;
    subject: string;
    message: string;
    status: 'pending' | 'sent' | 'failed' | 'delivered';
    error?: string;
    retryCount: number;
}

export interface AlertEscalation {
    id: string;
    alertId: string;
    level: number;
    timestamp: string;
    recipients: string[];
    status: 'pending' | 'sent' | 'failed';
    error?: string;
}

export class AlertingSystem {
    private logger: Logger;
    private rules: Map<string, AlertRule> = new Map();
    private notifications: AlertNotification[] = [];
    private escalations: AlertEscalation[] = [];
    private alertCounts: Map<string, { count: number; lastAlert: number }> = new Map();
    private escalationTimers: Map<string, NodeJS.Timeout> = new Map();

    constructor(logger: Logger) {
        this.logger = logger;
        this.initializeRules();
    }

    private initializeRules(): void {
        // Compliance Alert Rules
        this.addRule(new ComplianceScoreRule());
        this.addRule(new ConfigurationValidationRule());

        // Security Alert Rules
        this.addRule(new SecurityTokenRule());
        this.addRule(new AccessControlRule());
        this.addRule(new NetworkSecurityRule());

        // Performance Alert Rules
        this.addRule(new ResponseTimeRule());
        this.addRule(new ResourceUsageRule());
        this.addRule(new ThroughputRule());

        // Reliability Alert Rules
        this.addRule(new UptimeRule());
        this.addRule(new ErrorRateRule());
        this.addRule(new HealthCheckRule());
    }

    private addRule(rule: AlertRule): void {
        this.rules.set(rule.id, rule);
        this.logger.debug(`Added alert rule: ${rule.id}`);
    }

    async processAlert(alert: MonitoringAlert): Promise<void> {
        this.logger.info(`Processing alert: ${alert.id}`, {
            serverName: alert.serverName,
            type: alert.type,
            severity: alert.severity
        });

        // Check if alert should be throttled
        if (this.shouldThrottleAlert(alert)) {
            this.logger.debug(`Alert throttled: ${alert.id}`);
            return;
        }

        // Find matching rules
        const matchingRules = Array.from(this.rules.values()).filter(rule =>
            rule.enabled &&
            rule.category === alert.type &&
            rule.condition(alert)
        );

        if (matchingRules.length === 0) {
            this.logger.debug(`No matching rules found for alert: ${alert.id}`);
            return;
        }

        // Process each matching rule
        for (const rule of matchingRules) {
            try {
                await this.processRule(rule, alert);
            } catch (error) {
                this.logger.error(`Error processing rule ${rule.id} for alert ${alert.id}`, error as Error);
            }
        }

        // Update alert count for throttling
        this.updateAlertCount(alert);
    }

    private shouldThrottleAlert(alert: MonitoringAlert): boolean {
        const alertKey = `${alert.serverName}-${alert.type}-${alert.severity}`;
        const alertCount = this.alertCounts.get(alertKey);

        if (!alertCount) return false;

        const now = Date.now();
        const timeWindow = 5 * 60 * 1000; // 5 minutes

        // Check if within time window
        if (now - alertCount.lastAlert > timeWindow) {
            return false;
        }

        // Check if exceeded max alerts
        const rule = Array.from(this.rules.values()).find(r =>
            r.category === alert.type && r.throttle.maxAlerts > 0
        );

        if (!rule) return false;

        return alertCount.count >= rule.throttle.maxAlerts;
    }

    private updateAlertCount(alert: MonitoringAlert): void {
        const alertKey = `${alert.serverName}-${alert.type}-${alert.severity}`;
        const existing = this.alertCounts.get(alertKey);

        if (existing) {
            existing.count++;
            existing.lastAlert = Date.now();
        } else {
            this.alertCounts.set(alertKey, {
                count: 1,
                lastAlert: Date.now()
            });
        }
    }

    private async processRule(rule: AlertRule, alert: MonitoringAlert): Promise<void> {
        this.logger.info(`Processing rule: ${rule.name} for alert: ${alert.id}`);

        // Send notifications through configured channels
        for (const channel of rule.channels) {
            try {
                await this.sendNotification(rule, alert, channel);
            } catch (error) {
                this.logger.error(`Failed to send ${channel} notification for rule ${rule.id}`, error as Error);
            }
        }

        // Handle escalation if enabled
        if (rule.escalation.enabled) {
            await this.handleEscalation(rule, alert);
        }
    }

    private async sendNotification(rule: AlertRule, alert: MonitoringAlert, channel: string): Promise<void> {
        const notification: AlertNotification = {
            id: `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            alertId: alert.id,
            timestamp: new Date().toISOString(),
            channel,
            recipient: this.getRecipientForChannel(channel, rule),
            subject: this.formatSubject(rule, alert),
            message: this.formatMessage(rule, alert),
            status: 'pending',
            retryCount: 0
        };

        this.notifications.push(notification);

        try {
            switch (channel) {
                case 'email':
                    await this.sendEmailNotification(notification);
                    break;
                case 'slack':
                    await this.sendSlackNotification(notification);
                    break;
                case 'webhook':
                    await this.sendWebhookNotification(notification);
                    break;
                case 'sms':
                    await this.sendSMSNotification(notification);
                    break;
                default:
                    throw new Error(`Unsupported notification channel: ${channel}`);
            }

            notification.status = 'sent';
            this.logger.info(`Notification sent via ${channel}: ${notification.id}`);

        } catch (error) {
            notification.status = 'failed';
            notification.error = error instanceof Error ? error.message : String(error);
            this.logger.error(`Notification failed via ${channel}: ${notification.id}`, error as Error);

            // Retry logic
            await this.retryNotification(notification);
        }
    }

    private async retryNotification(notification: AlertNotification): Promise<void> {
        const maxRetries = 3;
        const retryDelay = 5000; // 5 seconds

        if (notification.retryCount >= maxRetries) {
            this.logger.error(`Max retries reached for notification: ${notification.id}`);
            return;
        }

        // Wait before retry
        await new Promise(resolve => setTimeout(resolve, retryDelay));

        notification.retryCount++;
        notification.status = 'pending';

        try {
            switch (notification.channel) {
                case 'email':
                    await this.sendEmailNotification(notification);
                    break;
                case 'slack':
                    await this.sendSlackNotification(notification);
                    break;
                case 'webhook':
                    await this.sendWebhookNotification(notification);
                    break;
                case 'sms':
                    await this.sendSMSNotification(notification);
                    break;
            }

            notification.status = 'sent';
            this.logger.info(`Notification retry successful: ${notification.id}`);

        } catch (error) {
            notification.status = 'failed';
            notification.error = error instanceof Error ? error.message : String(error);
            this.logger.error(`Notification retry failed: ${notification.id}`, error as Error);

            // Continue retrying
            await this.retryNotification(notification);
        }
    }

    private async handleEscalation(rule: AlertRule, alert: MonitoringAlert): Promise<void> {
        for (const level of rule.escalation.levels) {
            const escalation: AlertEscalation = {
                id: `escalation-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                alertId: alert.id,
                level: level.level,
                timestamp: new Date().toISOString(),
                recipients: level.recipients,
                status: 'pending'
            };

            this.escalations.push(escalation);

            // Set up escalation timer
            const timer = setTimeout(async () => {
                try {
                    await this.sendEscalationNotification(escalation);
                } catch (error) {
                    this.logger.error(`Escalation notification failed: ${escalation.id}`, error as Error);
                }
            }, level.delay);

            this.escalationTimers.set(escalation.id, timer);
        }
    }

    private async sendEscalationNotification(escalation: AlertEscalation): Promise<void> {
        // In a real implementation, this would send notifications to escalation recipients
        this.logger.info(`Escalation notification sent: ${escalation.id}`, {
            level: escalation.level,
            recipients: escalation.recipients
        });

        escalation.status = 'sent';
    }

    private getRecipientForChannel(channel: string, rule: AlertRule): string {
        // In a real implementation, this would get the actual recipient based on channel and rule
        switch (channel) {
            case 'email':
                return 'admin@example.com';
            case 'slack':
                return '#alerts';
            case 'webhook':
                return rule.id;
            case 'sms':
                return '+1234567890';
            default:
                return 'unknown';
        }
    }

    private formatSubject(rule: AlertRule, alert: MonitoringAlert): string {
        const severity = alert.severity.toUpperCase();
        const serverName = alert.serverName;
        const type = alert.type;

        return `[${severity}] ${serverName} - ${type} Alert: ${rule.name}`;
    }

    private formatMessage(rule: AlertRule, alert: MonitoringAlert): string {
        const timestamp = new Date(alert.timestamp).toLocaleString();
        const severity = alert.severity.toUpperCase();
        const serverName = alert.serverName;
        const type = alert.type;
        const message = alert.message;
        const details = JSON.stringify(alert.details, null, 2);

        return `🚨 *${severity} Alert* 🚨

*Server:* ${serverName}
*Type:* ${type}
*Rule:* ${rule.name}
*Time:* ${timestamp}
*Message:* ${message}

*Details:*
\`\`\`json
${details}
\`\`\`

*Rule Description:* ${rule.description}

Please take immediate action to resolve this issue.

---
*This alert was generated by the KiloCode MCP Compliance Server*
`;
    }

    private async sendEmailNotification(notification: AlertNotification): Promise<void> {
        // In a real implementation, this would use an email service
        this.logger.info(`Email notification sent: ${notification.id}`);
    }

    private async sendSlackNotification(notification: AlertNotification): Promise<void> {
        // In a real implementation, this would use the Slack API
        this.logger.info(`Slack notification sent: ${notification.id}`);
    }

    private async sendWebhookNotification(notification: AlertNotification): Promise<void> {
        // In a real implementation, this would make an HTTP request
        this.logger.info(`Webhook notification sent: ${notification.id}`);
    }

    private async sendSMSNotification(notification: AlertNotification): Promise<void> {
        // In a real implementation, this would use an SMS service
        this.logger.info(`SMS notification sent: ${notification.id}`);
    }

    // Public methods for external access
    getNotifications(): AlertNotification[] {
        return this.notifications;
    }

    getEscalations(): AlertEscalation[] {
        return this.escalations;
    }

    getAlertCounts(): Map<string, { count: number; lastAlert: number }> {
        return this.alertCounts;
    }

    async cancelEscalation(escalationId: string): Promise<void> {
        const timer = this.escalationTimers.get(escalationId);
        if (timer) {
            clearTimeout(timer);
            this.escalationTimers.delete(escalationId);

            const escalation = this.escalations.find(e => e.id === escalationId);
            if (escalation) {
                escalation.status = 'failed';
                this.logger.info(`Escalation cancelled: ${escalationId}`);
            }
        }
    }

    async getAlertStats(): Promise<{
        totalAlerts: number;
        totalNotifications: number;
        totalEscalations: number;
        notificationsByStatus: Record<string, number>;
        escalationsByStatus: Record<string, number>;
        alertsBySeverity: Record<string, number>;
        alertsByType: Record<string, number>;
    }> {
        const notificationsByStatus = this.notifications.reduce((acc, n) => {
            acc[n.status] = (acc[n.status] || 0) + 1;
            return acc;
        }, {} as Record<string, number>);

        const escalationsByStatus = this.escalations.reduce((acc, e) => {
            acc[e.status] = (acc[e.status] || 0) + 1;
            return acc;
        }, {} as Record<string, number>);

        const alertsBySeverity = Array.from(this.alertCounts.entries()).reduce((acc, [key, count]) => {
            const severity = key.split('-')[2]; // Extract severity from key
            acc[severity] = (acc[severity] || 0) + count.count;
            return acc;
        }, {} as Record<string, number>);

        const alertsByType = Array.from(this.alertCounts.entries()).reduce((acc, [key, count]) => {
            const type = key.split('-')[1]; // Extract type from key
            acc[type] = (acc[type] || 0) + count.count;
            return acc;
        }, {} as Record<string, number>);

        return {
            totalAlerts: this.alertCounts.size,
            totalNotifications: this.notifications.length,
            totalEscalations: this.escalations.length,
            notificationsByStatus,
            escalationsByStatus,
            alertsBySeverity,
            alertsByType
        };
    }

    async cleanup(): Promise<void> {
        // Clear all escalation timers
        for (const timer of this.escalationTimers.values()) {
            clearTimeout(timer);
        }
        this.escalationTimers.clear();

        // Clean up old notifications (older than 30 days)
        const cutoffTime = Date.now() - (30 * 24 * 60 * 60 * 1000);
        this.notifications = this.notifications.filter(n =>
            new Date(n.timestamp).getTime() > cutoffTime
        );

        // Clean up old escalations (older than 30 days)
        this.escalations = this.escalations.filter(e =>
            new Date(e.timestamp).getTime() > cutoffTime
        );

        this.logger.info('Alerting system cleanup completed');
    }
}

// Alert Rule Implementations
class ComplianceScoreRule implements AlertRule {
    id = 'compliance-score-rule';
    name = 'Low Compliance Score Alert';
    description = 'Alert when compliance score drops below threshold';
    enabled = true;
    severity = 'high' as const;
    category = 'compliance' as const;
    channels = ['email', 'slack'];
    throttle = { enabled: true, window: 300000, maxAlerts: 5 };
    escalation = {
        enabled: true,
        levels: [
            { level: 1, delay: 300000, recipients: ['admin@example.com'] },
            { level: 2, delay: 600000, recipients: ['manager@example.com'] }
        ]
    };

    condition = (alert: MonitoringAlert) => {
        return alert.type === 'compliance' && alert.severity === 'high';
    };
}

class ConfigurationValidationRule implements AlertRule {
    id = 'configuration-validation-rule';
    name = 'Configuration Validation Alert';
    description = 'Alert when configuration validation fails';
    enabled = true;
    severity = 'critical' as const;
    category = 'compliance' as const;
    channels = ['email', 'slack', 'sms'];
    throttle = { enabled: true, window: 300000, maxAlerts: 3 };
    escalation = {
        enabled: true,
        levels: [
            { level: 1, delay: 180000, recipients: ['admin@example.com'] },
            { level: 2, delay: 360000, recipients: ['manager@example.com', 'security@example.com'] }
        ]
    };

    condition = (alert: MonitoringAlert) => {
        return alert.type === 'compliance' && alert.severity === 'critical';
    };
}

class SecurityTokenRule implements AlertRule {
    id = 'security-token-rule';
    name = 'Security Token Alert';
    description = 'Alert when security token issues are detected';
    enabled = true;
    severity = 'critical' as const;
    category = 'security' as const;
    channels = ['email', 'slack', 'sms'];
    throttle = { enabled: true, window: 300000, maxAlerts: 2 };
    escalation = {
        enabled: true,
        levels: [
            { level: 1, delay: 120000, recipients: ['security@example.com'] },
            { level: 2, delay: 240000, recipients: ['security@example.com', 'manager@example.com'] }
        ]
    };

    condition = (alert: MonitoringAlert) => {
        return alert.type === 'security' && alert.severity === 'critical';
    };
}

class AccessControlRule implements AlertRule {
    id = 'access-control-rule';
    name = 'Access Control Alert';
    description = 'Alert when access control issues are detected';
    enabled = true;
    severity = 'high' as const;
    category = 'security' as const;
    channels = ['email', 'slack'];
    throttle = { enabled: true, window: 300000, maxAlerts: 4 };
    escalation = {
        enabled: true,
        levels: [
            { level: 1, delay: 300000, recipients: ['admin@example.com'] }
        ]
    };

    condition = (alert: MonitoringAlert) => {
        return alert.type === 'security' && alert.severity === 'high';
    };
}

class NetworkSecurityRule implements AlertRule {
    id = 'network-security-rule';
    name = 'Network Security Alert';
    description = 'Alert when network security issues are detected';
    enabled = true;
    severity = 'high' as const;
    category = 'security' as const;
    channels = ['email', 'slack'];
    throttle = { enabled: true, window: 300000, maxAlerts: 3 };
    escalation = {
        enabled: true,
        levels: [
            { level: 1, delay: 240000, recipients: ['security@example.com'] }
        ]
    };

    condition = (alert: MonitoringAlert) => {
        return alert.type === 'security' && alert.severity === 'high';
    };
}

class ResponseTimeRule implements AlertRule {
    id = 'response-time-rule';
    name = 'Response Time Alert';
    description = 'Alert when response time exceeds threshold';
    enabled = true;
    severity = 'medium' as const;
    category = 'performance' as const;
    channels = ['email', 'slack'];
    throttle = { enabled: true, window: 300000, maxAlerts: 6 };
    escalation = {
        enabled: false,
        levels: []
    };

    condition = (alert: MonitoringAlert) => {
        return alert.type === 'performance' && alert.severity === 'medium';
    };
}

class ResourceUsageRule implements AlertRule {
    id = 'resource-usage-rule';
    name = 'Resource Usage Alert';
    description = 'Alert when resource usage exceeds threshold';
    enabled = true;
    severity = 'medium' as const;
    category = 'performance' as const;
    channels = ['email', 'slack'];
    throttle = { enabled: true, window: 300000, maxAlerts: 5 };
    escalation = {
        enabled: false,
        levels: []
    };

    condition = (alert: MonitoringAlert) => {
        return alert.type === 'performance' && alert.severity === 'medium';
    };
}

class ThroughputRule implements AlertRule {
    id = 'throughput-rule';
    name = 'Throughput Alert';
    description = 'Alert when throughput drops below threshold';
    enabled = true;
    severity = 'medium' as const;
    category = 'performance' as const;
    channels = ['email'];
    throttle = { enabled: true, window: 300000, maxAlerts: 4 };
    escalation = {
        enabled: false,
        levels: []
    };

    condition = (alert: MonitoringAlert) => {
        return alert.type === 'performance' && alert.severity === 'medium';
    };
}

class UptimeRule implements AlertRule {
    id = 'uptime-rule';
    name = 'Uptime Alert';
    description = 'Alert when uptime drops below threshold';
    enabled = true;
    severity = 'high' as const;
    category = 'reliability' as const;
    channels = ['email', 'slack'];
    throttle = { enabled: true, window: 300000, maxAlerts: 3 };
    escalation = {
        enabled: true,
        levels: [
            { level: 1, delay: 180000, recipients: ['admin@example.com'] }
        ]
    };

    condition = (alert: MonitoringAlert) => {
        return alert.type === 'reliability' && alert.severity === 'high';
    };
}

class ErrorRateRule implements AlertRule {
    id = 'error-rate-rule';
    name = 'Error Rate Alert';
    description = 'Alert when error rate exceeds threshold';
    enabled = true;
    severity = 'high' as const;
    category = 'reliability' as const;
    channels = ['email', 'slack'];
    throttle = { enabled: true, window: 300000, maxAlerts: 4 };
    escalation = {
        enabled: true,
        levels: [
            { level: 1, delay: 300000, recipients: ['admin@example.com'] }
        ]
    };

    condition = (alert: MonitoringAlert) => {
        return alert.type === 'reliability' && alert.severity === 'high';
    };
}

class HealthCheckRule implements AlertRule {
    id = 'health-check-rule';
    name = 'Health Check Alert';
    description = 'Alert when health check fails';
    enabled = true;
    severity = 'critical' as const;
    category = 'reliability' as const;
    channels = ['email', 'slack', 'sms'];
    throttle = { enabled: true, window: 300000, maxAlerts: 2 };
    escalation = {
        enabled: true,
        levels: [
            { level: 1, delay: 120000, recipients: ['admin@example.com'] },
            { level: 2, delay: 240000, recipients: ['manager@example.com'] }
        ]
    };

    condition = (alert: MonitoringAlert) => {
        return alert.type === 'reliability' && alert.severity === 'critical';
    };
}

export default AlertingSystem;