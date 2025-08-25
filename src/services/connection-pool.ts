/**
 * MCP Integration Coordinator - Connection Pool
 * 
 * Provides connection pooling for PostgreSQL database connections.
 * Optimizes performance by reusing connections and managing connection lifecycle.
 */

import { Pool, PoolConfig, PoolClient, QueryResult } from 'pg';
import { Logger } from '../logger';
import { DatabaseService } from './database-service';

export interface ConnectionPoolConfig {
    min: number;
    max: number;
    idleTimeoutMillis: number;
    acquireTimeoutMillis: number;
    createTimeoutMillis: number;
    destroyTimeoutMillis: number;
    reapIntervalMillis: number;
    createRetryIntervalMillis: number;
    log: boolean;
}

export interface PoolStats {
    totalCount: number;
    idleCount: number;
    activeCount: number;
    waitingCount: number;
    totalCreated: number;
    totalAcquired: number;
    totalReleased: number;
    totalErrored: number;
    averageWaitTime: number;
}

export class ConnectionPool {
    private pool: Pool;
    private logger: Logger;
    private config: ConnectionPoolConfig;
    private stats: PoolStats;
    private isInitialized: boolean = false;

    constructor(databaseService: DatabaseService, logger: Logger, config?: Partial<ConnectionPoolConfig>) {
        this.logger = logger;

        // Default configuration
        this.config = {
            min: 2,
            max: 20,
            idleTimeoutMillis: 30000,
            acquireTimeoutMillis: 10000,
            createTimeoutMillis: 30000,
            destroyTimeoutMillis: 5000,
            reapIntervalMillis: 1000,
            createRetryIntervalMillis: 200,
            log: false,
            ...config
        };

        // Initialize stats
        this.stats = {
            totalCount: 0,
            idleCount: 0,
            activeCount: 0,
            waitingCount: 0,
            totalCreated: 0,
            totalAcquired: 0,
            totalReleased: 0,
            totalErrored: 0,
            averageWaitTime: 0
        };

        // Create pool with PostgreSQL configuration
        this.pool = new Pool({
            min: this.config.min,
            max: this.config.max,
            idleTimeoutMillis: this.config.idleTimeoutMillis,
            acquireTimeoutMillis: this.config.acquireTimeoutMillis,
            createTimeoutMillis: this.config.createTimeoutMillis,
            destroyTimeoutMillis: this.config.destroyTimeoutMillis,
            reapIntervalMillis: this.config.reapIntervalMillis,
            createRetryIntervalMillis: this.config.createRetryIntervalMillis,
            log: this.config.log
        });

        // Set up event handlers
        this.setupEventHandlers();
    }

    /**
     * Initialize the connection pool
     */
    public async initialize(): Promise<void> {
        try {
            this.logger.info('Initializing connection pool', {
                config: this.config
            });

            // Test the pool
            const client = await this.pool.connect();
            await client.query('SELECT 1');
            client.release();

            this.isInitialized = true;
            this.logger.info('Connection pool initialized successfully');
        } catch (error) {
            this.logger.error('Failed to initialize connection pool', error as Error);
            throw new Error(`Failed to initialize connection pool: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    /**
     * Get a connection from the pool
     */
    public async getConnection(): Promise<PoolClient> {
        if (!this.isInitialized) {
            await this.initialize();
        }

        const startTime = Date.now();

        try {
            const client = await this.pool.connect();

            // Update stats
            this.stats.totalAcquired++;
            this.stats.activeCount++;
            this.stats.idleCount--;

            const waitTime = Date.now() - startTime;
            this.updateAverageWaitTime(waitTime);

            this.logger.debug('Connection acquired from pool', {
                waitTime,
                activeCount: this.stats.activeCount,
                idleCount: this.stats.idleCount,
                waitingCount: this.stats.waitingCount
            });

            return client;
        } catch (error) {
            this.stats.totalErrored++;
            this.logger.error('Failed to acquire connection from pool', error as Error);
            throw new Error(`Failed to acquire connection: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    /**
     * Execute a query with connection management
     */
    public async query(text: string, params?: any[]): Promise<QueryResult> {
        const client = await this.getConnection();

        try {
            const result = await client.query(text, params);
            return result;
        } finally {
            client.release();
        }
    }

    /**
     * Execute a query with a callback function
     */
    public async withConnection<T>(callback: (client: PoolClient) => Promise<T>): Promise<T> {
        const client = await this.getConnection();

        try {
            return await callback(client);
        } finally {
            client.release();
        }
    }

    /**
     * Execute multiple queries in a transaction
     */
    public async withTransaction<T>(callback: (client: PoolClient) => Promise<T>): Promise<T> {
        const client = await this.getConnection();

        try {
            await client.query('BEGIN');
            const result = await callback(client);
            await client.query('COMMIT');
            return result;
        } catch (error) {
            await client.query('ROLLBACK');
            throw error;
        } finally {
            client.release();
        }
    }

    /**
     * Get pool statistics
     */
    public getStats(): PoolStats {
        // Update current pool stats
        this.updatePoolStats();

        return { ...this.stats };
    }

    /**
     * Check if pool is healthy
     */
    public async isHealthy(): Promise<boolean> {
        try {
            const client = await this.getConnection();
            await client.query('SELECT 1');
            client.release();
            return true;
        } catch (error) {
            this.logger.error('Connection pool health check failed', error as Error);
            return false;
        }
    }

    /**
     * Close the connection pool
     */
    public async close(): Promise<void> {
        try {
            this.logger.info('Closing connection pool');

            await this.pool.end();
            this.isInitialized = false;

            this.logger.info('Connection pool closed successfully');
        } catch (error) {
            this.logger.error('Failed to close connection pool', error as Error);
            throw new Error(`Failed to close connection pool: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    /**
     * Reset the connection pool
     */
    public async reset(): Promise<void> {
        try {
            this.logger.info('Resetting connection pool');

            await this.close();
            await this.initialize();

            this.logger.info('Connection pool reset successfully');
        } catch (error) {
            this.logger.error('Failed to reset connection pool', error as Error);
            throw new Error(`Failed to reset connection pool: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    /**
     * Set up event handlers for the pool
     */
    private setupEventHandlers(): void {
        this.pool.on('connect', (client) => {
            this.stats.totalCreated++;
            this.stats.activeCount++;

            if (this.config.log) {
                this.logger.debug('New database connection created', {
                    totalCreated: this.stats.totalCreated,
                    activeCount: this.stats.activeCount
                });
            }
        });

        this.pool.on('acquire', (client) => {
            this.stats.activeCount++;
            this.stats.idleCount--;

            if (this.config.log) {
                this.logger.debug('Connection acquired', {
                    activeCount: this.stats.activeCount,
                    idleCount: this.stats.idleCount
                });
            }
        });

        this.pool.on('release', (client) => {
            this.stats.activeCount--;
            this.stats.idleCount++;
            this.stats.totalReleased++;

            if (this.config.log) {
                this.logger.debug('Connection released', {
                    activeCount: this.stats.activeCount,
                    idleCount: this.stats.idleCount,
                    totalReleased: this.stats.totalReleased
                });
            }
        });

        this.pool.on('error', (error) => {
            this.stats.totalErrored++;

            this.logger.error('Connection pool error', error as Error, {
                totalErrored: this.stats.totalErrored
            });
        });

        this.pool.on('remove', (client) => {
            this.stats.idleCount--;

            if (this.config.log) {
                this.logger.debug('Connection removed from pool', {
                    idleCount: this.stats.idleCount
                });
            }
        });
    }

    /**
     * Update pool statistics
     */
    private updatePoolStats(): void {
        this.stats.totalCount = this.pool.totalCount;
        this.stats.idleCount = this.pool.idleCount;
        this.stats.activeCount = this.pool.totalCount - this.pool.idleCount;
        this.stats.waitingCount = this.pool.waitingCount;
    }

    /**
     * Update average wait time
     */
    private updateAverageWaitTime(waitTime: number): void {
        // Simple moving average
        const alpha = 0.1; // Smoothing factor
        this.stats.averageWaitTime = alpha * waitTime + (1 - alpha) * this.stats.averageWaitTime;
    }

    /**
     * Get pool configuration
     */
    public getConfig(): ConnectionPoolConfig {
        return { ...this.config };
    }

    /**
     * Update pool configuration
     */
    public updateConfig(newConfig: Partial<ConnectionPoolConfig>): void {
        this.config = { ...this.config, ...newConfig };

        // Update pool configuration if it exists
        if (this.pool) {
            this.pool.options = { ...this.pool.options, ...newConfig };
        }

        this.logger.info('Connection pool configuration updated', { config: this.config });
    }

    /**
     * Get pool size information
     */
    public getPoolSize(): {
        total: number;
        active: number;
        idle: number;
        waiting: number;
    } {
        this.updatePoolStats();

        return {
            total: this.stats.totalCount,
            active: this.stats.activeCount,
            idle: this.stats.idleCount,
            waiting: this.stats.waitingCount
        };
    }

    /**
     * Check if pool is under pressure
     */
    public isUnderPressure(): boolean {
        const size = this.getPoolSize();
        const pressureThreshold = 0.8; // 80% utilization

        return (size.active / size.total) > pressureThreshold;
    }

    /**
     * Get connection pool recommendations
     */
    public getRecommendations(): {
        currentConfig: ConnectionPoolConfig;
        recommendedConfig: ConnectionPoolConfig;
        recommendations: string[];
    } {
        const size = this.getPoolSize();
        const recommendations: string[] = [];
        let recommendedConfig = { ...this.config };

        // Analyze usage patterns
        if (size.waitingCount > 0) {
            recommendations.push('Consider increasing max connections to reduce waiting time');
            recommendedConfig.max = Math.min(this.config.max * 1.5, 100);
        }

        if (size.activeCount / size.total > 0.8) {
            recommendations.push('High connection utilization detected');
            recommendedConfig.max = Math.min(this.config.max * 1.2, 100);
        }

        if (size.idleCount > this.config.max * 0.5) {
            recommendations.push('Consider reducing min connections to save resources');
            recommendedConfig.min = Math.max(this.config.min - 1, 1);
        }

        return {
            currentConfig: this.config,
            recommendedConfig,
            recommendations
        };
    }
}