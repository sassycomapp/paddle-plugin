/**
 * MCP Integration Coordinator - Database Service
 * 
 * Handles database connections and operations.
 */

import { Pool } from 'pg';
import { Logger } from '../logger';
import { DatabaseConfig } from '../types';

export class DatabaseService {
    private pool: any;
    private logger: Logger;
    private isConnected: boolean = false;

    constructor(config: DatabaseConfig, logger: Logger) {
        this.logger = logger;
        this.pool = new Pool({
            host: config.host,
            port: config.port,
            database: config.database,
            user: config.username,
            password: config.password,
            ssl: config.ssl || false,
            max: config.maxConnections || 10,
            idleTimeoutMillis: 30000,
            connectionTimeoutMillis: 2000,
        });
    }

    /**
     * Initialize database connection
     */
    async initialize(): Promise<void> {
        try {
            // Test connection
            await this.pool.query('SELECT NOW()');
            this.isConnected = true;
            this.logger.info('Database connection established');
        } catch (error) {
            this.logger.error('Failed to connect to database', error as Error);
            throw error;
        }
    }

    /**
     * Get database client from pool
     */
    async getClient(): Promise<any> {
        if (!this.isConnected) {
            await this.initialize();
        }
        return this.pool.connect();
    }

    /**
     * Execute query with client
     */
    async query(text: string, params?: any[]): Promise<any> {
        const client = await this.getClient();
        try {
            const result = await client.query(text, params);
            return result;
        } finally {
            client.release();
        }
    }

    /**
     * Execute query with transaction
     */
    async withTransaction<T>(callback: (client: any) => Promise<T>): Promise<T> {
        const client = await this.getClient();
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
     * Close database connection
     */
    async close(): Promise<void> {
        try {
            await this.pool.end();
            this.isConnected = false;
            this.logger.info('Database connection closed');
        } catch (error) {
            this.logger.error('Failed to close database connection', error as Error);
            throw error;
        }
    }

    /**
     * Check if database is connected
     */
    isConnectionActive(): boolean {
        return this.isConnected;
    }

    /**
     * Get database pool statistics
     */
    getPoolStats(): {
        totalCount: number;
        idleCount: number;
        activeCount: number;
    } {
        return {
            totalCount: this.pool.totalCount,
            idleCount: this.pool.idleCount,
            activeCount: this.pool.totalCount - this.pool.idleCount
        };
    }
}