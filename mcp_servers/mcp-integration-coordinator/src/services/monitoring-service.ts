/**
 * MCP Integration Coordinator - Monitoring Service
 *
 * Provides comprehensive monitoring and metrics collection.
 */

import { Logger } from '../logger';
import { DatabaseService } from './database-service';

export interface SystemMetrics {
    timestamp: string;
    cpu: {
        usage: number;
        cores: number;
    };
    memory: {
        total: number;
        used: number;
        free: number;
        usage: number;
    };
    disk: {
        total: number;
        used: number;
        free: number;
        usage: number;
    };
    network: {
        incoming: number;
        outgoing: number;
    };
    processes: {
        total: number;
        active: number;
    };
}

export interface ServiceMetrics {
    serviceName: string;
    status: 'healthy' | 'degraded' | 'unhealthy';
    uptime: number;
    responseTime: {
        average: number;
        min: number;
        max: number;
        p95: number;
    };
    errorRate: number;
    requestCount: number;
    lastHealthCheck: string;
}

export class MonitoringService {
    private logger: Logger;
    private databaseService: DatabaseService;
    private metricsInterval: NodeJS.Timeout | null = null;
    private systemMetrics: SystemMetrics[] = [];
    private serviceMetrics: Map<string, ServiceMetrics> = new Map();
    private maxMetricsRetention = 1000; // Keep last 1000 metrics entries

    constructor(databaseService: DatabaseService, logger: Logger) {
        this.databaseService = databaseService;
        this.logger = logger;
        this.initializeMetricsCollection();
    }

    /**
     * Initialize metrics collection
     */
    private initializeMetricsCollection(): void {
        // Collect system metrics every 30 seconds
        this.metricsInterval = setInterval(() => {
            this.collectSystemMetrics();
        }, 30000);

        this.logger.info('Monitoring service initialized');
    }

    /**
     * Collect system metrics
     */
    private async collectSystemMetrics(): Promise<void> {
        try {
            const metrics: SystemMetrics = {
                timestamp: new Date().toISOString(),
                cpu: {
                    usage: this.getCPUUsage(),
                    cores: this.getCPUCount()
                },
                memory: {
                    total: this.getTotalMemory(),
                    used: this.getUsedMemory(),
                    free: this.getFreeMemory(),
                    usage: this.getMemoryUsage()
                },
                disk: {
                    total: this.getTotalDiskSpace(),
                    used: this.getUsedDiskSpace(),
                    free: this.getFreeDiskSpace(),
                    usage: this.getDiskUsage()
                },
                network: {
                    incoming: this.getNetworkIncoming(),
                    outgoing: this.getNetworkOutgoing()
                },
                processes: {
                    total: this.getTotalProcesses(),
                    active: this.getActiveProcesses()
                }
            };

            this.systemMetrics.push(metrics);

            // Keep only recent metrics
            if (this.systemMetrics.length > this.maxMetricsRetention) {
                this.systemMetrics = this.systemMetrics.slice(-this.maxMetricsRetention);
            }

            // Store metrics in database
            await this.storeMetrics(metrics);

        } catch (error) {
            this.logger.error('Failed to collect system metrics', error as Error);
        }
    }

    /**
     * Store metrics in database
     */
    private async storeMetrics(metrics: SystemMetrics): Promise<void> {
        try {
            await this.databaseService.query(
                `INSERT INTO system_metrics 
                (timestamp, cpu_usage, cpu_cores, memory_total, memory_used, memory_free, memory_usage,
                 disk_total, disk_used, disk_free, disk_usage, network_incoming, network_outgoing,
                 processes_total, processes_active) 
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)`,
                [
                    metrics.timestamp,
                    metrics.cpu.usage,
                    metrics.cpu.cores,
                    metrics.memory.total,
                    metrics.memory.used,
                    metrics.memory.free,
                    metrics.memory.usage,
                    metrics.disk.total,
                    metrics.disk.used,
                    metrics.disk.free,
                    metrics.disk.usage,
                    metrics.network.incoming,
                    metrics.network.outgoing,
                    metrics.processes.total,
                    metrics.processes.active
                ]
            );
        } catch (error) {
            this.logger.error('Failed to store metrics', error as Error);
        }
    }

    /**
     * Update service metrics
     */
    updateServiceMetrics(serviceName: string, metrics: Partial<ServiceMetrics>): void {
        const existingMetrics = this.serviceMetrics.get(serviceName) || {
            serviceName,
            status: 'healthy',
            uptime: 0,
            responseTime: { average: 0, min: 0, max: 0, p95: 0 },
            errorRate: 0,
            requestCount: 0,
            lastHealthCheck: new Date().toISOString()
        };

        const updatedMetrics = { ...existingMetrics, ...metrics };
        this.serviceMetrics.set(serviceName, updatedMetrics);
    }

    /**
     * Get current system metrics
     */
    getCurrentSystemMetrics(): SystemMetrics | null {
        return this.systemMetrics.length > 0 ? this.systemMetrics[this.systemMetrics.length - 1] : null;
    }

    /**
     * Get system metrics history
     */
    getSystemMetricsHistory(hours: number = 24): SystemMetrics[] {
        const cutoff = new Date(Date.now() - hours * 60 * 60 * 1000);
        return this.systemMetrics.filter(metric => new Date(metric.timestamp) > cutoff);
    }

    /**
     * Get service metrics
     */
    getServiceMetrics(serviceName?: string): ServiceMetrics[] {
        if (serviceName) {
            const metrics = this.serviceMetrics.get(serviceName);
            return metrics ? [metrics] : [];
        }
        return Array.from(this.serviceMetrics.values());
    }

    /**
     * Get system health status
     */
    getSystemHealth(): {
        overall: 'healthy' | 'degraded' | 'unhealthy';
        services: { [key: string]: 'healthy' | 'degraded' | 'unhealthy' };
        lastUpdated: string;
    } {
        const services: { [key: string]: 'healthy' | 'degraded' | 'unhealthy' } = {};

        for (const [serviceName, metrics] of this.serviceMetrics) {
            services[serviceName] = metrics.status;
        }

        // Determine overall health
        const unhealthyServices = Object.values(services).filter(status => status === 'unhealthy').length;
        const degradedServices = Object.values(services).filter(status => status === 'degraded').length;

        let overall: 'healthy' | 'degraded' | 'unhealthy' = 'healthy';
        if (unhealthyServices > 0) {
            overall = 'unhealthy';
        } else if (degradedServices > 0) {
            overall = 'degraded';
        }

        return {
            overall,
            services,
            lastUpdated: new Date().toISOString()
        };
    }

    /**
     * Get performance metrics
     */
    getPerformanceMetrics(): {
        uptime: number;
        memoryUsage: number;
        cpuUsage: number;
        diskUsage: number;
        requestRate: number;
        errorRate: number;
    } {
        const currentMetrics = this.getCurrentSystemMetrics();
        const totalRequests = Array.from(this.serviceMetrics.values())
            .reduce((sum, metrics) => sum + metrics.requestCount, 0);

        const totalErrors = Array.from(this.serviceMetrics.values())
            .reduce((sum, metrics) => sum + (metrics.requestCount * metrics.errorRate / 100), 0);

        return {
            uptime: process.uptime(),
            memoryUsage: currentMetrics ? currentMetrics.memory.usage : 0,
            cpuUsage: currentMetrics ? currentMetrics.cpu.usage : 0,
            diskUsage: currentMetrics ? currentMetrics.disk.usage : 0,
            requestRate: totalRequests / (process.uptime() || 1), // requests per second
            errorRate: totalRequests > 0 ? (totalErrors / totalRequests) * 100 : 0
        };
    }

    /**
     * Get alerts
     */
    getAlerts(): {
        type: 'warning' | 'critical';
        message: string;
        timestamp: string;
        metric: string;
        value: number;
        threshold: number;
    }[] {
        const alerts: any[] = [];
        const currentMetrics = this.getCurrentSystemMetrics();

        if (!currentMetrics) return alerts;

        // Memory usage alert
        if (currentMetrics.memory.usage > 90) {
            alerts.push({
                type: 'critical',
                message: 'High memory usage detected',
                timestamp: currentMetrics.timestamp,
                metric: 'memory_usage',
                value: currentMetrics.memory.usage,
                threshold: 90
            });
        } else if (currentMetrics.memory.usage > 75) {
            alerts.push({
                type: 'warning',
                message: 'Elevated memory usage',
                timestamp: currentMetrics.timestamp,
                metric: 'memory_usage',
                value: currentMetrics.memory.usage,
                threshold: 75
            });
        }

        // CPU usage alert
        if (currentMetrics.cpu.usage > 95) {
            alerts.push({
                type: 'critical',
                message: 'High CPU usage detected',
                timestamp: currentMetrics.timestamp,
                metric: 'cpu_usage',
                value: currentMetrics.cpu.usage,
                threshold: 95
            });
        } else if (currentMetrics.cpu.usage > 80) {
            alerts.push({
                type: 'warning',
                message: 'Elevated CPU usage',
                timestamp: currentMetrics.timestamp,
                metric: 'cpu_usage',
                value: currentMetrics.cpu.usage,
                threshold: 80
            });
        }

        // Disk usage alert
        if (currentMetrics.disk.usage > 95) {
            alerts.push({
                type: 'critical',
                message: 'High disk usage detected',
                timestamp: currentMetrics.timestamp,
                metric: 'disk_usage',
                value: currentMetrics.disk.usage,
                threshold: 95
            });
        } else if (currentMetrics.disk.usage > 85) {
            alerts.push({
                type: 'warning',
                message: 'Elevated disk usage',
                timestamp: currentMetrics.timestamp,
                metric: 'disk_usage',
                value: currentMetrics.disk.usage,
                threshold: 85
            });
        }

        return alerts;
    }

    /**
     * Cleanup old metrics
     */
    async cleanupOldMetrics(retentionDays: number = 30): Promise<void> {
        try {
            const cutoffDate = new Date(Date.now() - retentionDays * 24 * 60 * 60 * 1000);

            await this.databaseService.query(
                'DELETE FROM system_metrics WHERE timestamp < $1',
                [cutoffDate.toISOString()]
            );

            this.logger.info(`Cleaned up metrics older than ${retentionDays} days`);
        } catch (error) {
            this.logger.error('Failed to cleanup old metrics', error as Error);
        }
    }

    /**
     * Stop monitoring
     */
    stop(): void {
        if (this.metricsInterval) {
            clearInterval(this.metricsInterval);
            this.metricsInterval = null;
        }
        this.logger.info('Monitoring service stopped');
    }

    // Helper methods for system metrics (simplified implementations)
    private getCPUUsage(): number {
        // In a real implementation, you would use system libraries or commands
        return Math.random() * 100; // Mock data
    }

    private getCPUCount(): number {
        return require('os').cpus().length;
    }

    private getTotalMemory(): number {
        return require('os').totalmem();
    }

    private getUsedMemory(): number {
        return require('os').totalmem() - require('os').freemem();
    }

    private getFreeMemory(): number {
        return require('os').freemem();
    }

    private getMemoryUsage(): number {
        const total = this.getTotalMemory();
        const used = this.getUsedMemory();
        return Math.round((used / total) * 100);
    }

    private getTotalDiskSpace(): number {
        // Mock implementation
        return 1000000000; // 1GB
    }

    private getUsedDiskSpace(): number {
        // Mock implementation
        return Math.random() * 800000000; // Random usage up to 800MB
    }

    private getFreeDiskSpace(): number {
        return this.getTotalDiskSpace() - this.getUsedDiskSpace();
    }

    private getDiskUsage(): number {
        const total = this.getTotalDiskSpace();
        const used = this.getUsedDiskSpace();
        return Math.round((used / total) * 100);
    }

    private getNetworkIncoming(): number {
        // Mock implementation
        return Math.random() * 1000000; // Random bytes
    }

    private getNetworkOutgoing(): number {
        // Mock implementation
        return Math.random() * 1000000; // Random bytes
    }

    private getTotalProcesses(): number {
        return require('os').loadavg().length;
    }

    private getActiveProcesses(): number {
        return Math.floor(Math.random() * 10) + 1; // Mock data
    }
}