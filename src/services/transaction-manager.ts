/**
 * MCP Integration Coordinator - Transaction Manager
 * 
 * Provides transaction management and error handling for database operations.
 * Ensures data consistency and provides retry logic for transient failures.
 */

import { Logger } from '../logger';
import { DatabaseService } from './database-service';
import { AssessmentProcessingError, AssessmentNotFoundError } from '../types';

export interface TransactionOptions {
    isolationLevel?: 'READ COMMITTED' | 'REPEATABLE READ' | 'SERIALIZABLE';
    timeout?: number;
    retryCount?: number;
    retryDelay?: number;
    backoffMultiplier?: number;
}

export interface TransactionResult<T> {
    success: boolean;
    data?: T;
    error?: Error;
    retryCount: number;
    duration: number;
}

export class TransactionManager {
    private databaseService: DatabaseService;
    private logger: Logger;
    private defaultOptions: TransactionOptions;

    constructor(databaseService: DatabaseService, logger: Logger) {
        this.databaseService = databaseService;
        this.logger = logger;
        this.defaultOptions = {
            isolationLevel: 'READ COMMITTED',
            timeout: 30000,
            retryCount: 3,
            retryDelay: 1000,
            backoffMultiplier: 2
        };
    }

    /**
     * Execute a transaction with automatic retry logic
     */
    public async executeTransaction<T>(
        operation: (client: any) => Promise<T>,
        options: TransactionOptions = {}
    ): Promise<TransactionResult<T>> {
        const startTime = Date.now();
        const mergedOptions = { ...this.defaultOptions, ...options };
        let retryCount = 0;
        let lastError: Error | null = null;

        while (retryCount <= mergedOptions.retryCount!) {
            try {
                const result = await this.executeWithRetry(operation, mergedOptions);
                const duration = Date.now() - startTime;

                this.logger.debug('Transaction completed successfully', {
                    duration,
                    retryCount,
                    operation: operation.name || 'anonymous'
                });

                return {
                    success: true,
                    data: result,
                    retryCount,
                    duration
                };
            } catch (error) {
                lastError = error as Error;
                retryCount++;

                this.logger.warn('Transaction attempt failed', {
                    error: error instanceof Error ? error.message : 'Unknown error',
                    attempt: retryCount,
                    maxAttempts: mergedOptions.retryCount! + 1,
                    operation: operation.name || 'anonymous'
                });

                if (retryCount <= mergedOptions.retryCount!) {
                    const delay = this.calculateDelay(mergedOptions.retryDelay!, retryCount, mergedOptions.backoffMultiplier!);
                    await this.sleep(delay);
                }
            }
        }

        const duration = Date.now() - startTime;
        this.logger.error('Transaction failed after all retries', {
            error: lastError instanceof Error ? lastError.message : 'Unknown error',
            totalAttempts: retryCount,
            duration,
            operation: operation.name || 'anonymous'
        });

        return {
            success: false,
            error: lastError || new Error('Unknown transaction error'),
            retryCount,
            duration
        };
    }

    /**
     * Execute a transaction with specific isolation level
     */
    public async executeWithIsolation<T>(
        operation: (client: any) => Promise<T>,
        isolationLevel: TransactionOptions['isolationLevel'] = 'READ COMMITTED'
    ): Promise<T> {
        const client = await this.databaseService.getClient();

        try {
            await client.query('BEGIN');
            await client.query(`SET TRANSACTION ISOLATION LEVEL ${isolationLevel}`);

            const result = await operation(client);

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
     * Execute multiple operations in a single transaction
     */
    public async executeBatchTransaction<T>(
        operations: Array<{ operation: (client: any) => Promise<T>; description: string }>,
        options: TransactionOptions = {}
    ): Promise<TransactionResult<T[]>> {
        const startTime = Date.now();
        const mergedOptions = { ...this.defaultOptions, ...options };
        let retryCount = 0;
        let lastError: Error | null = null;

        while (retryCount <= mergedOptions.retryCount!) {
            try {
                const results: T[] = [];
                const client = await this.databaseService.getClient();

                try {
                    await client.query('BEGIN');
                    await client.query(`SET TRANSACTION ISOLATION LEVEL ${mergedOptions.isolationLevel}`);

                    for (const { operation: op, description } of operations) {
                        try {
                            const result = await op(client);
                            results.push(result);
                            this.logger.debug(`Batch operation completed: ${description}`);
                        } catch (error) {
                            this.logger.error(`Batch operation failed: ${description}`, error as Error);
                            throw error;
                        }
                    }

                    await client.query('COMMIT');
                    const duration = Date.now() - startTime;

                    this.logger.debug('Batch transaction completed successfully', {
                        duration,
                        retryCount,
                        operationCount: operations.length
                    });

                    return {
                        success: true,
                        data: results,
                        retryCount,
                        duration
                    };
                } catch (error) {
                    await client.query('ROLLBACK');
                    throw error;
                } finally {
                    client.release();
                }
            } catch (error) {
                lastError = error as Error;
                retryCount++;

                this.logger.warn('Batch transaction attempt failed', {
                    error: error instanceof Error ? error.message : 'Unknown error',
                    attempt: retryCount,
                    maxAttempts: mergedOptions.retryCount! + 1,
                    operationCount: operations.length
                });

                if (retryCount <= mergedOptions.retryCount!) {
                    const delay = this.calculateDelay(mergedOptions.retryDelay!, retryCount, mergedOptions.backoffMultiplier!);
                    await this.sleep(delay);
                }
            }
        }

        const duration = Date.now() - startTime;
        this.logger.error('Batch transaction failed after all retries', {
            error: lastError instanceof Error ? lastError.message : 'Unknown error',
            totalAttempts: retryCount,
            duration,
            operationCount: operations.length
        });

        return {
            success: false,
            error: lastError || new Error('Unknown batch transaction error'),
            retryCount,
            duration
        };
    }

    /**
     * Execute with retry logic for specific operations
     */
    private async executeWithRetry<T>(
        operation: (client: any) => Promise<T>,
        options: TransactionOptions
    ): Promise<T> {
        const client = await this.databaseService.getClient();

        try {
            await client.query('BEGIN');
            await client.query(`SET TRANSACTION ISOLATION LEVEL ${options.isolationLevel}`);

            const result = await operation(client);

            await client.query('COMMIT');
            return result;
        } catch (error) {
            await client.query('ROLLBACK');

            // Check if error is retryable
            if (this.isRetryableError(error)) {
                throw error; // Will be caught by retry loop
            }

            // For non-retryable errors, wrap in AssessmentProcessingError
            if (error instanceof Error) {
                throw new AssessmentProcessingError(
                    `Transaction failed: ${error.message}`,
                    undefined,
                    'TRANSACTION_FAILED'
                );
            }

            throw error;
        } finally {
            client.release();
        }
    }

    /**
     * Check if error is retryable
     */
    private isRetryableError(error: any): boolean {
        if (!error || typeof error !== 'object') {
            return false;
        }

        // PostgreSQL retryable errors
        const retryableCodes = [
            '40001', // Serialization failure
            '40P01', // Deadlock detected
            '53300', // Insufficient resources
            '53100', // Disk full
            '53200', // Out of memory
            '53400', // Configuration limit exceeded
            '57P01', // Admin shutdown
            '57P02', // Crash shutdown
            '57P03', // Cannot connect now
            '58P01', // WAL write error
            '08000', // Connection exception
            '08003', // Connection does not exist
            '08006', // Connection failure
            '08001', // SQL client unable to establish SQL connection
            '08004', // SQL server rejected establishment of SQL connection
            '08007', // Transaction resolution unknown
            '57P01', // Admin shutdown
            '57P02', // Crash shutdown
            '57P03', // Cannot connect now
            '58P01', // WAL write error
            '0F000', // Invalid catalog name
            '3D000', // Invalid catalog name
            '3F000', // Invalid schema name
            '42601', // Syntax error
            '42501', // Insufficient privilege
            '42846', // Cannot coerce
            '42803', // Grouping error
            '42P01', // Undefined table
            '42P02', // Undefined column
            '42703', // Undefined column
            '42704', // Undefined object
            '42830', // Invalid foreign key
            '42803', // Grouping error
            '42P01', // Undefined table
            '42703'  // Undefined column
        ];

        // Check if error has code property
        if (error.code && retryableCodes.includes(error.code)) {
            return true;
        }

        // Check if error message contains retryable patterns
        const retryableMessages = [
            'connection',
            'timeout',
            'deadlock',
            'serialization',
            'resource',
            'memory',
            'disk',
            'shutdown',
            'network',
            'temporary'
        ];

        if (error.message) {
            const message = error.message.toLowerCase();
            return retryableMessages.some(pattern => message.includes(pattern));
        }

        return false;
    }

    /**
     * Calculate delay with exponential backoff
     */
    private calculateDelay(baseDelay: number, attempt: number, multiplier: number): number {
        return baseDelay * Math.pow(multiplier, attempt - 1);
    }

    /**
     * Sleep for specified milliseconds
     */
    private sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Create a savepoint within a transaction
     */
    public async createSavepoint(client: any, name: string): Promise<void> {
        await client.query(`SAVEPOINT ${name}`);
    }

    /**
     * Rollback to a savepoint
     */
    public async rollbackToSavepoint(client: any, name: string): Promise<void> {
        await client.query(`ROLLBACK TO SAVEPOINT ${name}`);
    }

    /**
     * Release a savepoint
     */
    public async releaseSavepoint(client: any, name: string): Promise<void> {
        await client.query(`RELEASE SAVEPOINT ${name}`);
    }

    /**
     * Execute a read-only transaction
     */
    public async executeReadOnly<T>(
        operation: (client: any) => Promise<T>,
        options: TransactionOptions = {}
    ): Promise<T> {
        const mergedOptions = { ...this.defaultOptions, ...options };

        return this.executeWithIsolation(operation, 'READ COMMITTED');
    }

    /**
     * Execute a repeatable read transaction
     */
    public async executeRepeatableRead<T>(
        operation: (client: any) => Promise<T>,
        options: TransactionOptions = {}
    ): Promise<T> {
        const mergedOptions = { ...this.defaultOptions, ...options };

        return this.executeWithIsolation(operation, 'REPEATABLE READ');
    }

    /**
     * Execute a serializable transaction
     */
    public async executeSerializable<T>(
        operation: (client: any) => Promise<T>,
        options: TransactionOptions = {}
    ): Promise<T> {
        const mergedOptions = { ...this.defaultOptions, ...options };

        return this.executeWithIsolation(operation, 'SERIALIZABLE');
    }

    /**
     * Get transaction statistics
     */
    public getTransactionStats(): {
        totalTransactions: number;
        successfulTransactions: number;
        failedTransactions: number;
        averageDuration: number;
        retryRate: number;
    } {
        // This would track actual statistics in a real implementation
        return {
            totalTransactions: 0,
            successfulTransactions: 0,
            failedTransactions: 0,
            averageDuration: 0,
            retryRate: 0
        };
    }
}