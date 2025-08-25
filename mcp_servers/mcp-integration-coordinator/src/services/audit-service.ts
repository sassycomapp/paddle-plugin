/**
 * MCP Integration Coordinator - Audit Service
 * 
 * Handles audit logging and compliance tracking.
 */

import { DatabaseService } from './database-service';
import { Logger } from '../logger';
import { AuditLog } from '../types';

export class AuditService {
    private logger: Logger;
    private databaseService: DatabaseService;

    constructor(databaseService: DatabaseService, logger: Logger) {
        this.databaseService = databaseService;
        this.logger = logger;
    }

    /**
     * Log an audit event
     */
    async log(auditData: Omit<AuditLog, 'id' | 'timestamp'>): Promise<void> {
        try {
            const auditLog: AuditLog = {
                id: this.generateId(),
                timestamp: new Date().toISOString(),
                ...auditData
            };

            // Log to database
            await this.databaseService.query(
                `INSERT INTO audit_logs 
                (id, timestamp, action, actor, target, result, details, ip_address, user_agent) 
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
                [
                    auditLog.id,
                    auditLog.timestamp,
                    auditLog.action,
                    auditLog.actor,
                    auditLog.target,
                    auditLog.result,
                    JSON.stringify(auditLog.details),
                    auditLog.ipAddress,
                    auditLog.userAgent
                ]
            );

            // Also log to console for development
            this.logger.info('Audit log entry created', auditLog);
        } catch (error) {
            this.logger.error('Failed to create audit log', error as Error, auditData);
            // Don't throw - audit failures shouldn't break the main application
        }
    }

    /**
     * Get audit logs with filtering
     */
    async getLogs(filters: {
        actor?: string;
        action?: string;
        target?: string;
        result?: string;
        startDate?: string;
        endDate?: string;
        limit?: number;
        offset?: number;
    } = {}): Promise<AuditLog[]> {
        try {
            let query = 'SELECT * FROM audit_logs WHERE 1=1';
            const params: any[] = [];
            let paramIndex = 1;

            if (filters.actor) {
                query += ` AND actor = $${paramIndex}`;
                params.push(filters.actor);
                paramIndex++;
            }

            if (filters.action) {
                query += ` AND action = $${paramIndex}`;
                params.push(filters.action);
                paramIndex++;
            }

            if (filters.target) {
                query += ` AND target = $${paramIndex}`;
                params.push(filters.target);
                paramIndex++;
            }

            if (filters.result) {
                query += ` AND result = $${paramIndex}`;
                params.push(filters.result);
                paramIndex++;
            }

            if (filters.startDate) {
                query += ` AND timestamp >= $${paramIndex}`;
                params.push(filters.startDate);
                paramIndex++;
            }

            if (filters.endDate) {
                query += ` AND timestamp <= $${paramIndex}`;
                params.push(filters.endDate);
                paramIndex++;
            }

            query += ' ORDER BY timestamp DESC';

            if (filters.limit) {
                query += ` LIMIT $${paramIndex}`;
                params.push(filters.limit);
                paramIndex++;
            }

            if (filters.offset) {
                query += ` OFFSET $${paramIndex}`;
                params.push(filters.offset);
            }

            const result = await this.databaseService.query(query, params);
            return result.rows.map((row: any) => ({
                id: row.id,
                timestamp: row.timestamp,
                action: row.action,
                actor: row.actor,
                target: row.target,
                result: row.result,
                details: JSON.parse(row.details || '{}'),
                ipAddress: row.ip_address,
                userAgent: row.user_agent
            }));
        } catch (error) {
            this.logger.error('Failed to get audit logs', error as Error, filters);
            throw error;
        }
    }

    /**
     * Get audit statistics
     */
    async getStats(filters: {
        startDate?: string;
        endDate?: string;
    } = {}): Promise<{
        totalLogs: number;
        successLogs: number;
        failedLogs: number;
        actionCounts: Record<string, number>;
        actorCounts: Record<string, number>;
    }> {
        try {
            let whereClause = '1=1';
            const params: any[] = [];
            let paramIndex = 1;

            if (filters.startDate) {
                whereClause += ` AND timestamp >= $${paramIndex}`;
                params.push(filters.startDate);
                paramIndex++;
            }

            if (filters.endDate) {
                whereClause += ` AND timestamp <= $${paramIndex}`;
                params.push(filters.endDate);
                paramIndex++;
            }

            const totalResult = await this.databaseService.query(
                `SELECT COUNT(*) as total FROM audit_logs WHERE ${whereClause}`,
                params
            );

            const successResult = await this.databaseService.query(
                `SELECT COUNT(*) as total FROM audit_logs WHERE ${whereClause} AND result = 'success'`,
                params
            );

            const failedResult = await this.databaseService.query(
                `SELECT COUNT(*) as total FROM audit_logs WHERE ${whereClause} AND result = 'failed'`,
                params
            );

            const actionResult = await this.databaseService.query(
                `SELECT action, COUNT(*) as count FROM audit_logs WHERE ${whereClause} GROUP BY action`,
                params
            );

            const actorResult = await this.databaseService.query(
                `SELECT actor, COUNT(*) as count FROM audit_logs WHERE ${whereClause} GROUP BY actor`,
                params
            );

            return {
                totalLogs: parseInt(totalResult.rows[0].total),
                successLogs: parseInt(successResult.rows[0].total),
                failedLogs: parseInt(failedResult.rows[0].total),
                actionCounts: actionResult.rows.reduce((acc: any, row: any) => {
                    acc[row.action] = parseInt(row.count);
                    return acc;
                }, {} as Record<string, number>),
                actorCounts: actorResult.rows.reduce((acc: any, row: any) => {
                    acc[row.actor] = parseInt(row.count);
                    return acc;
                }, {} as Record<string, number>)
            };
        } catch (error) {
            this.logger.error('Failed to get audit stats', error as Error, filters);
            throw error;
        }
    }

    /**
     * Clean up old audit logs
     */
    async cleanup(retentionDays: number = 90): Promise<number> {
        try {
            const cutoffDate = new Date();
            cutoffDate.setDate(cutoffDate.getDate() - retentionDays);

            const result = await this.databaseService.query(
                'DELETE FROM audit_logs WHERE timestamp < $1 RETURNING COUNT(*) as deleted',
                [cutoffDate.toISOString()]
            );

            const deletedCount = parseInt(result.rows[0].deleted);
            this.logger.info(`Cleaned up ${deletedCount} old audit logs`);
            return deletedCount;
        } catch (error) {
            this.logger.error('Failed to cleanup audit logs', error as Error);
            throw error;
        }
    }

    /**
     * Generate unique ID for audit log
     */
    private generateId(): string {
        return `audit_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
}