/**
 * MCP Integration Coordinator - Redis Service
 * 
 * Handles Redis caching and session management.
 */

import { createClient, RedisClientType } from 'redis';
import { Logger } from '../logger';
import { RedisConfig } from '../types';

export class RedisService {
    private client: RedisClientType | null = null;
    private logger: Logger;
    private isConnected: boolean = false;

    constructor(config: RedisConfig, logger: Logger) {
        this.logger = logger;
        this.client = createClient({
            url: `redis://${config.host}:${config.port}`,
            password: config.password,
            database: config.db || 0
        });

        this.setupEventHandlers();
    }

    /**
     * Setup Redis event handlers
     */
    private setupEventHandlers(): void {
        if (!this.client) return;

        this.client.on('connect', () => {
            this.isConnected = true;
            this.logger.info('Redis connected');
        });

        this.client.on('error', (error) => {
            this.logger.error('Redis error', error as Error);
            this.isConnected = false;
        });

        this.client.on('end', () => {
            this.isConnected = false;
            this.logger.info('Redis disconnected');
        });
    }

    /**
     * Connect to Redis
     */
    async connect(): Promise<void> {
        if (!this.client) {
            throw new Error('Redis client not initialized');
        }

        try {
            await this.client.connect();
            this.isConnected = true;
            this.logger.info('Redis connected successfully');
        } catch (error) {
            this.logger.error('Failed to connect to Redis', error as Error);
            throw error;
        }
    }

    /**
     * Disconnect from Redis
     */
    async disconnect(): Promise<void> {
        if (!this.client) {
            return;
        }

        try {
            await this.client.disconnect();
            this.isConnected = false;
            this.logger.info('Redis disconnected');
        } catch (error) {
            this.logger.error('Failed to disconnect from Redis', error as Error);
            throw error;
        }
    }

    /**
     * Set a value in Redis
     */
    async set(key: string, value: any, ttl?: number): Promise<void> {
        if (!this.client || !this.isConnected) {
            throw new Error('Redis not connected');
        }

        try {
            const serializedValue = JSON.stringify(value);
            if (ttl) {
                await this.client.setEx(key, ttl, serializedValue);
            } else {
                await this.client.set(key, serializedValue);
            }
        } catch (error) {
            this.logger.error('Failed to set Redis value', error as Error, { key, ttl });
            throw error;
        }
    }

    /**
     * Get a value from Redis
     */
    async get(key: string): Promise<any | null> {
        if (!this.client || !this.isConnected) {
            throw new Error('Redis not connected');
        }

        try {
            const value = await this.client.get(key);
            return value ? JSON.parse(value) : null;
        } catch (error) {
            this.logger.error('Failed to get Redis value', error as Error, { key });
            throw error;
        }
    }

    /**
     * Delete a key from Redis
     */
    async del(key: string): Promise<number> {
        if (!this.client || !this.isConnected) {
            throw new Error('Redis not connected');
        }

        try {
            return await this.client.del(key);
        } catch (error) {
            this.logger.error('Failed to delete Redis key', error as Error, { key });
            throw error;
        }
    }

    /**
     * Check if a key exists in Redis
     */
    async exists(key: string): Promise<boolean> {
        if (!this.client || !this.isConnected) {
            throw new Error('Redis not connected');
        }

        try {
            const result = await this.client.exists(key);
            return result === 1;
        } catch (error) {
            this.logger.error('Failed to check Redis key existence', error as Error, { key });
            throw error;
        }
    }

    /**
     * Set expiration for a key
     */
    async expire(key: string, ttl: number): Promise<boolean> {
        if (!this.client || !this.isConnected) {
            throw new Error('Redis not connected');
        }

        try {
            const result = await this.client.expire(key, ttl);
            return result === true;
        } catch (error) {
            this.logger.error('Failed to set Redis key expiration', error as Error, { key, ttl });
            throw error;
        }
    }

    /**
     * Get Redis connection status
     */
    isConnectionActive(): boolean {
        return this.isConnected;
    }
}