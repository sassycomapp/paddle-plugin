/**
 * MCP Integration Coordinator - Audit Service (JavaScript Version)
 * 
 * Handles audit logging and compliance tracking.
 */

class AuditService {
    constructor(databaseService, logger) {
        this.databaseService = databaseService;
        this.logger = logger;
        this.logs = [];
    }

    /**
     * Log an action
     */
    async log(actionData) {
        try {
            const logEntry = {
                id: `audit_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                timestamp: new Date().toISOString(),
                ...actionData
            };

            this.logs.push(logEntry);
            this.logger.info('Audit log entry created', logEntry);

            // In a real implementation, this would save to the database
            // For now, we'll just keep it in memory
            return logEntry;
        } catch (error) {
            this.logger.error('Failed to create audit log', error);
            throw error;
        }
    }

    /**
     * Get audit logs
     */
    async getLogs(options = {}) {
        try {
            const { limit = 100, offset = 0 } = options;
            const filteredLogs = this.logs.slice(offset, offset + limit);
            return filteredLogs;
        } catch (error) {
            this.logger.error('Failed to get audit logs', error);
            throw error;
        }
    }

    /**
     * Get audit statistics
     */
    async getStats() {
        try {
            const totalLogs = this.logs.length;
            const successLogs = this.logs.filter(log => log.result === 'success').length;
            const failedLogs = this.logs.filter(log => log.result === 'failed').length;
            const pendingLogs = this.logs.filter(log => log.result === 'pending').length;

            const actions = {};
            this.logs.forEach(log => {
                actions[log.action] = (actions[log.action] || 0) + 1;
            });

            return {
                totalLogs,
                successLogs,
                failedLogs,
                pendingLogs,
                actions,
                lastLog: this.logs[this.logs.length - 1] || null
            };
        } catch (error) {
            this.logger.error('Failed to get audit stats', error);
            throw error;
        }
    }

    /**
     * Clear old logs
     */
    async clearOldLogs(retentionDays = 90) {
        try {
            const cutoffDate = new Date();
            cutoffDate.setDate(cutoffDate.getDate() - retentionDays);

            this.logs = this.logs.filter(log => new Date(log.timestamp) > cutoffDate);
            this.logger.info(`Cleared logs older than ${retentionDays} days`);
        } catch (error) {
            this.logger.error('Failed to clear old logs', error);
            throw error;
        }
    }
}

module.exports = { AuditService };