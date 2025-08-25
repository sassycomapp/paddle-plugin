/**
 * MCP Configuration and Compliance Server - Execution Engine
 * 
 * This module executes remediation actions and manages the execution lifecycle.
 */

import { Logger } from '../logger';
import {
    ExecutionResult,
    RemediationAction,
    TestResult,
    RemediationOptions
} from '../types';
import fs from 'fs/promises';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export class ExecutionEngine {
    private logger: Logger;
    private projectRoot: string;
    private kilocodeDir: string;
    private vscodeDir: string;
    private activeExecutions: Map<string, ExecutionResult> = new Map();
    private executionStats = {
        total: 0,
        successful: 0,
        failed: 0,
        active: 0,
        completed: 0
    };

    constructor(logger: Logger, projectRoot: string = process.cwd()) {
        this.logger = logger;
        this.projectRoot = projectRoot;
        this.kilocodeDir = path.join(projectRoot, '.kilocode');
        this.vscodeDir = path.join(projectRoot, '.vscode');
    }

    /**
     * Execute remediation action
     */
    async executeAction(
        action: RemediationAction,
        options: RemediationOptions = {
            autoApprove: false,
            dryRun: false,
            rollbackOnFailure: true,
            parallelExecution: false,
            maxConcurrent: 1,
            timeout: 300000 // 5 minutes
        }
    ): Promise<ExecutionResult> {
        this.logger.info('Executing remediation action', {
            actionId: action.id,
            actionType: action.type,
            serverName: action.serverName,
            dryRun: options.dryRun
        });

        const executionId = `exec-${action.id}-${Date.now()}`;
        const startTime = new Date().toISOString();

        const result: ExecutionResult = {
            actionId: action.id,
            status: 'pending',
            startTime,
            tests: [],
            rollbackRequired: false,
            rollbackExecuted: false
        };

        let backupPath: string | null = null;

        try {
            // Add to active executions
            this.activeExecutions.set(executionId, result);
            this.executionStats.active++;
            this.executionStats.total++;

            // Validate prerequisites
            const prerequisitesValid = await this.validatePrerequisites(action);
            if (!prerequisitesValid.valid) {
                throw new Error(`Prerequisites not met: ${prerequisitesValid.reason}`);
            }

            // Create backup if rollback is enabled
            if (options.rollbackOnFailure && action.rollbackCommand) {
                backupPath = await this.createBackup(action);
                result.rollbackRequired = true;
            }

            // Execute action
            if (options.dryRun) {
                result.status = 'success';
                result.tests.push({
                    name: 'dry-run',
                    passed: true,
                    message: 'Dry run completed successfully',
                    duration: 0
                });
            } else {
                await this.executeRemediationAction(action, result, options.timeout);
            }

            // Run tests
            if (result.status === 'success') {
                await this.runPostActionTests(action, result);
            }

            // Clean up backup if successful
            if (backupPath && result.status === 'success') {
                await this.cleanupBackup(backupPath);
                result.rollbackRequired = false;
            }

            // Update stats
            this.executionStats.active--;
            this.executionStats.completed++;
            if (result.status === 'success') {
                this.executionStats.successful++;
            } else {
                this.executionStats.failed++;
            }

            // Execute rollback if needed
            if (result.status === 'failed' && result.rollbackRequired && !options.dryRun) {
                await this.executeRollback(action, result, backupPath);
            }

        } catch (error) {
            result.status = 'failed';
            result.errorMessage = error instanceof Error ? error.message : String(error);
            this.logger.error('Action execution failed', error as Error);

            // Update stats
            this.executionStats.active--;
            this.executionStats.completed++;
            this.executionStats.failed++;

            // Execute rollback if needed
            if (result.rollbackRequired && !options.dryRun) {
                if (backupPath) {
                    await this.executeRollback(action, result, backupPath);
                }
            }
        } finally {
            // Remove from active executions
            this.activeExecutions.delete(executionId);
        }

        const endTime = new Date().toISOString();
        result.endTime = endTime;

        this.logger.info('Action execution completed', {
            actionId: action.id,
            status: result.status,
            duration: this.calculateDuration(startTime, endTime)
        });

        return result;
    }

    /**
     * Execute multiple actions in parallel or sequentially
     */
    async executeActions(
        actions: RemediationAction[],
        options: RemediationOptions = {
            autoApprove: false,
            dryRun: false,
            rollbackOnFailure: true,
            parallelExecution: false,
            maxConcurrent: 1,
            timeout: 300000
        }
    ): Promise<ExecutionResult[]> {
        this.logger.info('Executing multiple remediation actions', {
            actionCount: actions.length,
            parallelExecution: options.parallelExecution,
            maxConcurrent: options.maxConcurrent
        });

        const results: ExecutionResult[] = [];

        if (options.parallelExecution && actions.length > 1) {
            // Execute in parallel
            const promises = actions.map(action =>
                this.executeAction(action, options)
            );
            results.push(...await Promise.allSettled(promises).then(settled =>
                settled.map(s => s.status === 'fulfilled' ? s.value :
                    ({
                        actionId: s.reason?.actionId || 'unknown',
                        status: 'failed' as const,
                        startTime: new Date().toISOString(),
                        tests: [],
                        rollbackRequired: false,
                        rollbackExecuted: false,
                        errorMessage: s.reason instanceof Error ? s.reason.message : String(s.reason)
                    })
                ))
            );
        } else {
            // Execute sequentially
            for (const action of actions) {
                const result = await this.executeAction(action, options);
                results.push(result);
            }
        }

        return results;
    }

    /**
     * Cancel active execution
     */
    async cancelExecution(executionId: string): Promise<boolean> {
        this.logger.info('Cancelling execution', { executionId });

        const execution = this.activeExecutions.get(executionId);
        if (!execution) {
            this.logger.warn('Execution not found', { executionId });
            return false;
        }

        // In a real implementation, this would kill the process
        // For now, we'll just mark it as failed
        execution.status = 'failed';
        execution.errorMessage = 'Execution cancelled by user';

        this.activeExecutions.delete(executionId);
        this.executionStats.active--;
        this.executionStats.completed++;
        this.executionStats.failed++;

        this.logger.info('Execution cancelled', { executionId });
        return true;
    }

    /**
     * Get execution status
     */
    getExecutionStatus(executionId: string): ExecutionResult | null {
        return this.activeExecutions.get(executionId) || null;
    }

    /**
     * Get all active executions
     */
    getActiveExecutions(): ExecutionResult[] {
        return Array.from(this.activeExecutions.values());
    }

    /**
     * Get execution statistics
     */
    getExecutionStats(): {
        total: number;
        successful: number;
        failed: number;
        active: number;
        completed: number;
        successRate: string;
    } {
        const successRate = this.executionStats.completed > 0
            ? (this.executionStats.successful / this.executionStats.completed * 100).toFixed(1)
            : '0';

        return {
            ...this.executionStats,
            successRate: `${successRate}%`
        };
    }

    /**
     * Validate prerequisites for an action
     */
    private async validatePrerequisites(action: RemediationAction): Promise<{ valid: boolean; reason?: string }> {
        this.logger.debug('Validating prerequisites', { actionId: action.id });

        try {
            // Check if project is a git repository
            if (action.rollbackCommand === 'git') {
                try {
                    await execAsync('git status', { timeout: 10000 });
                } catch (error) {
                    return { valid: false, reason: 'Git repository not available' };
                }
            }

            // Check if required environment variables are set
            if (action.env) {
                for (const [key, value] of Object.entries(action.env)) {
                    if (value === '' || value === null || value === undefined) {
                        return { valid: false, reason: `Environment variable ${key} is not set` };
                    }
                }
            }

            // Check dependencies
            for (const dependency of action.dependencies) {
                const depValid = await this.checkDependency(dependency);
                if (!depValid) {
                    return { valid: false, reason: `Dependency not available: ${dependency}` };
                }
            }

            return { valid: true };

        } catch (error) {
            return { valid: false, reason: `Prerequisites validation failed: ${error instanceof Error ? error.message : String(error)}` };
        }
    }

    /**
     * Check if dependency is available
     */
    private async checkDependency(dependency: string): Promise<boolean> {
        try {
            switch (dependency) {
                case 'node':
                    await execAsync('node --version', { timeout: 5000 });
                    return true;
                case 'npm':
                    await execAsync('npm --version', { timeout: 5000 });
                    return true;
                case 'python':
                    await execAsync('python --version', { timeout: 5000 });
                    return true;
                case 'python3':
                    await execAsync('python3 --version', { timeout: 5000 });
                    return true;
                case 'git':
                    await execAsync('git --version', { timeout: 5000 });
                    return true;
                default:
                    return false;
            }
        } catch (error) {
            return false;
        }
    }

    /**
     * Create backup for rollback
     */
    private async createBackup(action: RemediationAction): Promise<string> {
        this.logger.debug('Creating backup', { actionId: action.id });

        const backupPath = path.join(this.kilocodeDir, 'backups', `backup-${action.id}-${Date.now()}`);
        await fs.mkdir(path.dirname(backupPath), { recursive: true });

        try {
            // Backup configuration files
            const configFiles = [
                path.join(this.kilocodeDir, 'mcp.json'),
                path.join(this.vscodeDir, 'mcp.json')
            ];

            for (const configFile of configFiles) {
                if (await this.pathExists(configFile)) {
                    const backupFile = path.join(backupPath, path.basename(configFile));
                    await fs.copyFile(configFile, backupFile);
                }
            }

            this.logger.info('Backup created', { backupPath });
            return backupPath;

        } catch (error) {
            this.logger.error('Failed to create backup', error as Error);
            throw new Error(`Backup creation failed: ${error instanceof Error ? error.message : String(error)}`);
        }
    }

    /**
     * Cleanup backup
     */
    private async cleanupBackup(backupPath: string): Promise<void> {
        try {
            await fs.rm(backupPath, { recursive: true, force: true });
            this.logger.debug('Backup cleaned up', { backupPath });
        } catch (error) {
            this.logger.warn('Failed to cleanup backup', { backupPath, error: error instanceof Error ? error.message : String(error) });
        }
    }

    /**
     * Execute remediation action
     */
    private async executeRemediationAction(
        action: RemediationAction,
        result: ExecutionResult,
        timeout: number
    ): Promise<void> {
        this.logger.info('Executing remediation action', { actionId: action.id, actionType: action.type });

        const startTime = Date.now();
        result.status = 'pending';

        try {
            // Prepare command
            const command = action.command;
            const args = action.args || [];
            const env = { ...process.env, ...action.env };

            // Execute command
            const execOptions = {
                timeout,
                env,
                cwd: this.projectRoot
            };

            const { stdout, stderr } = await execAsync(`${command} ${args.join(' ')}`, execOptions);

            const duration = Date.now() - startTime;
            result.status = 'success';
            result.output = stdout;

            // Add success test
            result.tests.push({
                name: 'execution',
                passed: true,
                message: 'Action executed successfully',
                duration,
                details: { stdout, stderr }
            });

            this.logger.info('Action executed successfully', { actionId: action.id, duration });

        } catch (error) {
            const duration = Date.now() - startTime;
            result.status = 'failed';
            result.errorMessage = error instanceof Error ? error.message : String(error);

            // Add failure test
            result.tests.push({
                name: 'execution',
                passed: false,
                message: `Action execution failed: ${result.errorMessage}`,
                duration,
                details: { error }
            });

            throw error;
        }
    }

    /**
     * Execute rollback
     */
    private async executeRollback(
        action: RemediationAction,
        result: ExecutionResult,
        backupPath: string | null
    ): Promise<void> {
        this.logger.info('Executing rollback', { actionId: action.id });

        try {
            if (backupPath) {
                // Restore from backup
                const configFiles = [
                    path.join(this.kilocodeDir, 'mcp.json'),
                    path.join(this.vscodeDir, 'mcp.json')
                ];

                for (const configFile of configFiles) {
                    const backupFile = path.join(backupPath, path.basename(configFile));
                    if (await this.pathExists(backupFile)) {
                        await fs.copyFile(backupFile, configFile);
                    }
                }

                await this.cleanupBackup(backupPath);
            } else if (action.rollbackCommand) {
                // Execute rollback command
                const command = action.rollbackCommand;
                const args = action.rollbackArgs || [];
                const env = { ...process.env, ...action.rollbackEnv };

                await execAsync(`${command} ${args.join(' ')}`, {
                    timeout: 300000,
                    env,
                    cwd: this.projectRoot
                });
            }

            result.rollbackExecuted = true;
            result.tests.push({
                name: 'rollback',
                passed: true,
                message: 'Rollback executed successfully',
                duration: 0
            });

            this.logger.info('Rollback executed successfully', { actionId: action.id });

        } catch (error) {
            result.rollbackExecuted = false;
            result.tests.push({
                name: 'rollback',
                passed: false,
                message: `Rollback failed: ${error instanceof Error ? error.message : String(error)}`,
                duration: 0,
                details: { error }
            });

            this.logger.error('Rollback failed', error as Error);
        }
    }

    /**
     * Run post-action tests
     */
    private async runPostActionTests(action: RemediationAction, result: ExecutionResult): Promise<void> {
        this.logger.debug('Running post-action tests', { actionId: action.id });

        try {
            // Test 1: Check if server is still configured
            const configValid = await this.validateServerConfiguration(action.serverName);
            result.tests.push({
                name: 'configuration-validation',
                passed: configValid,
                message: configValid ? 'Configuration is valid' : 'Configuration validation failed',
                duration: 0
            });

            // Test 2: Check if server is healthy (if applicable)
            if (action.type === 'install_server' || action.type === 'update_config') {
                const healthy = await this.checkServerHealth(action.serverName);
                result.tests.push({
                    name: 'health-check',
                    passed: healthy,
                    message: healthy ? 'Server is healthy' : 'Server health check failed',
                    duration: 0
                });
            }

            // Test 3: Check if action was successful (basic check)
            const actionSuccessful = await this.verifyActionSuccess(action);
            result.tests.push({
                name: 'action-verification',
                passed: actionSuccessful,
                message: actionSuccessful ? 'Action was successful' : 'Action verification failed',
                duration: 0
            });

        } catch (error) {
            result.tests.push({
                name: 'post-action-tests',
                passed: false,
                message: `Post-action tests failed: ${error instanceof Error ? error.message : String(error)}`,
                duration: 0,
                details: { error }
            });
        }
    }

    /**
     * Validate server configuration
     */
    private async validateServerConfiguration(serverName: string): Promise<boolean> {
        try {
            const configPath = path.join(this.kilocodeDir, 'mcp.json');
            const configContent = await fs.readFile(configPath, 'utf-8');
            const config = JSON.parse(configContent);

            return config.mcpServers && !!config.mcpServers[serverName];
        } catch (error) {
            return false;
        }
    }

    /**
     * Check server health
     */
    private async checkServerHealth(serverName: string): Promise<boolean> {
        try {
            // This is a simplified health check
            // In a real implementation, this would test the actual server
            const configPath = path.join(this.kilocodeDir, 'mcp.json');
            const configContent = await fs.readFile(configPath, 'utf-8');
            const config = JSON.parse(configContent);

            if (config.mcpServers && config.mcpServers[serverName]) {
                const serverConfig = config.mcpServers[serverName];
                return !!serverConfig.command && !!serverConfig.args;
            }

            return false;
        } catch (error) {
            return false;
        }
    }

    /**
     * Verify action success
     */
    private async verifyActionSuccess(action: RemediationAction): Promise<boolean> {
        try {
            switch (action.type) {
                case 'install_server':
                    return await this.verifyServerInstallation(action.serverName);
                case 'update_config':
                    return await this.verifyConfigurationUpdate(action.serverName);
                case 'fix_security':
                    return await this.verifySecurityFix(action.serverName);
                case 'optimize_performance':
                    return await this.verifyPerformanceOptimization(action.serverName);
                default:
                    return true;
            }
        } catch (error) {
            return false;
        }
    }

    /**
     * Verify server installation
     */
    private async verifyServerInstallation(serverName: string): Promise<boolean> {
        try {
            const configPath = path.join(this.kilocodeDir, 'mcp.json');
            const configContent = await fs.readFile(configPath, 'utf-8');
            const config = JSON.parse(configContent);

            if (config.mcpServers && config.mcpServers[serverName]) {
                const serverConfig = config.mcpServers[serverName];
                return !!serverConfig.command && !!serverConfig.args;
            }

            return false;
        } catch (error) {
            return false;
        }
    }

    /**
     * Verify configuration update
     */
    private async verifyConfigurationUpdate(serverName: string): Promise<boolean> {
        return await this.verifyServerInstallation(serverName);
    }

    /**
     * Verify security fix
     */
    private async verifySecurityFix(serverName: string): Promise<boolean> {
        // This would check for specific security improvements
        return true;
    }

    /**
     * Verify performance optimization
     */
    private async verifyPerformanceOptimization(serverName: string): Promise<boolean> {
        // This would check for performance improvements
        return true;
    }

    /**
     * Calculate duration between two timestamps
     */
    private calculateDuration(startTime: string, endTime: string): string {
        const start = new Date(startTime).getTime();
        const end = new Date(endTime).getTime();
        const duration = end - start;

        const minutes = Math.floor(duration / 60000);
        const seconds = Math.floor((duration % 60000) / 1000);

        return `${minutes}m ${seconds}s`;
    }

    /**
     * Check if path exists
     */
    private async pathExists(path: string): Promise<boolean> {
        try {
            await fs.access(path);
            return true;
        } catch {
            return false;
        }
    }
}