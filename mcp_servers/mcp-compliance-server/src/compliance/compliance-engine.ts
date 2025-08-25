/**
 * MCP Configuration and Compliance Server - Compliance Engine
 * 
 * This module handles compliance checking and validation of MCP servers and configurations.
 */

import { Logger } from '../logger';
import { ComplianceReport, ServerConfig, ValidationResult, ServerStatus } from '../types';
import fs from 'fs/promises';
import path from 'path';

export class ComplianceEngine {
    private logger: Logger;
    private projectRoot: string;
    private kilocodeDir: string;
    private vscodeDir: string;

    constructor(logger: Logger, projectRoot: string = process.cwd()) {
        this.logger = logger;
        this.projectRoot = projectRoot;
        this.kilocodeDir = path.join(projectRoot, '.kilocode');
        this.vscodeDir = path.join(projectRoot, '.vscode');
    }

    /**
     * Get status of MCP servers and configurations
     */
    async getServerStatus(
        servers: string[] = [],
        includeConfig: boolean = true,
        includeHealth: boolean = true
    ): Promise<ServerStatus[]> {
        this.logger.info('Getting server status', { servers, includeConfig, includeHealth });

        const configPaths = [
            path.join(this.kilocodeDir, 'mcp.json'),
            path.join(this.vscodeDir, 'mcp.json')
        ];

        const allStatus: ServerStatus[] = [];

        for (const configPath of configPaths) {
            try {
                const configContent = await fs.readFile(configPath, 'utf-8');
                const config = JSON.parse(configContent);

                if (config.mcpServers) {
                    for (const [serverName, serverConfig] of Object.entries(config.mcpServers)) {
                        // Filter servers if specific ones requested
                        if (servers.length > 0 && !servers.includes(serverName)) {
                            continue;
                        }

                        const status: ServerStatus = {
                            name: serverName,
                            configPath,
                            configExists: true,
                            healthy: false,
                            lastChecked: new Date().toISOString(),
                            issues: []
                        };

                        // Check configuration validity
                        if (includeConfig) {
                            const configValidation = this.validateServerConfig(serverName, serverConfig);
                            status.configValid = configValidation.valid;
                            if (!configValidation.valid) {
                                status.issues.push(...configValidation.errors);
                            }
                        }

                        // Check server health
                        if (includeHealth) {
                            try {
                                const health = await this.checkServerHealth(serverName, serverConfig);
                                status.healthy = health.healthy;
                                if (!health.healthy) {
                                    status.issues.push(...health.issues);
                                }
                            } catch (error) {
                                status.healthy = false;
                                status.issues.push(`Health check failed: ${error instanceof Error ? error.message : String(error)}`);
                            }
                        }

                        allStatus.push(status);
                    }
                }
            } catch (error) {
                this.logger.warn(`Failed to read config file: ${configPath}`, error as Error);
            }
        }

        return allStatus;
    }

    /**
     * Validate MCP server configurations
     */
    async validateConfiguration(
        configPath?: string,
        servers: string[] = [],
        strict: boolean = false
    ): Promise<ValidationResult> {
        this.logger.info('Validating configuration', { configPath, servers, strict });

        const result: ValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            configPath: configPath || 'default',
            servers: {}
        };

        const targetConfigPath = configPath ||
            (await fs.pathExists(path.join(this.kilocodeDir, 'mcp.json'))
                ? path.join(this.kilocodeDir, 'mcp.json')
                : path.join(this.vscodeDir, 'mcp.json'));

        try {
            const configContent = await fs.readFile(targetConfigPath, 'utf-8');
            const config = JSON.parse(configContent);

            if (!config.mcpServers) {
                result.valid = false;
                result.errors.push('No mcpServers section found in configuration');
                return result;
            }

            for (const [serverName, serverConfig] of Object.entries(config.mcpServers)) {
                // Filter servers if specific ones requested
                if (servers.length > 0 && !servers.includes(serverName)) {
                    continue;
                }

                const serverValidation = this.validateServerConfig(serverName, serverConfig, strict);
                result.servers[serverName] = serverValidation;

                if (!serverValidation.valid) {
                    result.valid = false;
                    result.errors.push(...serverValidation.errors);
                }

                if (serverValidation.warnings.length > 0) {
                    result.warnings.push(...serverValidation.warnings);
                }
            }

        } catch (error) {
            result.valid = false;
            result.errors.push(`Failed to read configuration: ${error instanceof Error ? error.message : String(error)}`);
        }

        return result;
    }

    /**
     * Validate individual server configuration
     */
    private validateServerConfig(
        serverName: string,
        serverConfig: any,
        strict: boolean = false
    ): ValidationResult {
        const result: ValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            configPath: 'server-config'
        };

        // Check required fields
        if (!serverConfig.command) {
            result.valid = false;
            result.errors.push(`Missing required field: command`);
        }

        if (!serverConfig.args || !Array.isArray(serverConfig.args)) {
            result.valid = false;
            result.errors.push(`Missing or invalid field: args (must be array)`);
        }

        // Check command validity
        if (serverConfig.command) {
            const validCommands = ['npx', 'node', 'python', 'python3'];
            if (!validCommands.includes(serverConfig.command)) {
                result.warnings.push(`Unknown command: ${serverConfig.command}`);
            }
        }

        // Check environment variables
        if (serverConfig.env && typeof serverConfig.env !== 'object') {
            result.valid = false;
            result.errors.push(`Invalid env field: must be object`);
        }

        // Check for security issues
        if (serverConfig.env) {
            const securityIssues = this.checkSecurityIssues(serverConfig.env);
            result.errors.push(...securityIssues.errors);
            if (securityIssues.warnings.length > 0) {
                result.warnings.push(...securityIssues.warnings);
            }
        }

        // Check for KiloCode-specific requirements
        if (serverName.includes('kilocode')) {
            const kilocodeValidation = this.validateKiloCodeConfig(serverConfig);
            result.errors.push(...kilocodeValidation.errors);
            result.warnings.push(...kilocodeValidation.warnings);
        }

        return result;
    }

    /**
     * Check server health
     */
    private async checkServerHealth(serverName: string, serverConfig: any): Promise<{ healthy: boolean; issues: string[] }> {
        const issues: string[] = [];
        let healthy = true;

        try {
            // Test if command is available
            if (serverConfig.command === 'npx') {
                // Check if package is available
                const packageName = serverConfig.args?.[1] || serverName;
                try {
                    await this.executeCommand(`npm list -g ${packageName}`, { timeout: 10000 });
                } catch (error) {
                    issues.push(`Package not available: ${packageName}`);
                    healthy = false;
                }
            } else if (serverConfig.command === 'node') {
                // Check if script exists
                const scriptPath = serverConfig.args?.[0];
                if (scriptPath && !await fs.pathExists(path.join(this.projectRoot, scriptPath))) {
                    issues.push(`Script not found: ${scriptPath}`);
                    healthy = false;
                }
            }

            // Test environment variables
            if (serverConfig.env) {
                for (const [key, value] of Object.entries(serverConfig.env)) {
                    if (value === '' || value === null || value === undefined) {
                        issues.push(`Environment variable not set: ${key}`);
                        healthy = false;
                    }
                }
            }

            // Test basic connectivity
            try {
                await this.executeCommand(`${serverConfig.command} ${serverConfig.args.slice(0, 2).join(' ')} --version`, { timeout: 5000 });
            } catch (error) {
                issues.push(`Command execution failed: ${error instanceof Error ? error.message : String(error)}`);
                healthy = false;
            }

        } catch (error) {
            issues.push(`Health check failed: ${error instanceof Error ? error.message : String(error)}`);
            healthy = false;
        }

        return { healthy, issues };
    }

    /**
     * Check for security issues in configuration
     */
    private checkSecurityIssues(env: Record<string, any>): { errors: string[]; warnings: string[] } {
        const errors: string[] = [];
        const warnings: string[] = [];

        const sensitiveVars = ['PASSWORD', 'TOKEN', 'SECRET', 'KEY', 'API_KEY', 'PRIVATE_KEY'];
        const weakPatterns = ['password', '123', 'admin', 'test'];

        for (const [key, value] of Object.entries(env)) {
            // Check for hardcoded sensitive information
            if (sensitiveVars.some(sensitive => key.toUpperCase().includes(sensitive))) {
                if (typeof value === 'string' && value.length > 0) {
                    // Check for weak values
                    if (weakPatterns.some(pattern => value.toLowerCase().includes(pattern))) {
                        errors.push(`Weak ${key}: contains common patterns`);
                    }

                    // Check for default values
                    if (value.toLowerCase().includes('default') || value.toLowerCase().includes('example')) {
                        warnings.push(`Default value detected for ${key}`);
                    }
                }
            }

            // Check for insecure protocols
            if (key.toUpperCase().includes('URL') && typeof value === 'string') {
                if (value.startsWith('http://') && !value.includes('localhost')) {
                    warnings.push(`Insecure protocol detected in ${key}: ${value}`);
                }
            }
        }

        return { errors, warnings };
    }

    /**
     * Validate KiloCode-specific configuration requirements
     */
    private validateKiloCodeConfig(serverConfig: any): { errors: string[]; warnings: string[] } {
        const errors: string[] = [];
        const warnings: string[] = [];

        // Check for required KiloCode environment variables
        const requiredKilocodeVars = ['KILOCODE_ENV', 'KILOCODE_PROJECT_PATH'];
        for (const varName of requiredKilocodeVars) {
            if (!serverConfig.env || !serverConfig.env[varName]) {
                warnings.push(`Missing KiloCode environment variable: ${varName}`);
            }
        }

        // Check for proper project path
        if (serverConfig.env && serverConfig.env.KILOCODE_PROJECT_PATH) {
            const projectPath = serverConfig.env.KILOCODE_PROJECT_PATH;
            if (!path.isAbsolute(projectPath)) {
                warnings.push(`Relative project path: ${projectPath}`);
            }
        }

        return { errors, warnings };
    }

    /**
     * Execute command with timeout
     */
    private async executeCommand(command: string, options: { timeout?: number } = {}): Promise<string> {
        const { exec } = require('child_process');
        const { promisify } = require('util');
        const execAsync = promisify(exec);

        return await execAsync(command, {
            timeout: options.timeout || 30000,
            cwd: this.projectRoot
        });
    }

    /**
     * Generate compliance report
     */
    async generateComplianceReport(servers: string[] = []): Promise<ComplianceReport> {
        this.logger.info('Generating compliance report', { servers });

        const report: ComplianceReport = {
            generatedAt: new Date().toISOString(),
            totalServers: 0,
            compliantServers: 0,
            nonCompliantServers: 0,
            issues: [],
            recommendations: [],
            servers: {}
        };

        try {
            const status = await this.getServerStatus(servers, true, true);
            report.totalServers = status.length;

            for (const serverStatus of status) {
                report.servers[serverStatus.name] = serverStatus;

                if (serverStatus.healthy && serverStatus.configValid) {
                    report.compliantServers++;
                } else {
                    report.nonCompliantServers++;
                    report.issues.push({
                        server: serverStatus.name,
                        type: serverStatus.configValid ? 'health' : 'configuration',
                        severity: serverStatus.configValid ? 'medium' : 'high',
                        message: serverStatus.issues.join(', ')
                    });
                }
            }

            // Generate recommendations
            if (report.nonCompliantServers > 0) {
                report.recommendations.push({
                    type: 'remediation',
                    priority: 'high',
                    message: `Address ${report.nonCompliantServers} non-compliant servers`
                });
            }

            if (report.issues.length > 5) {
                report.recommendations.push({
                    type: 'review',
                    priority: 'medium',
                    message: 'Review configuration standards and update server configurations'
                });
            }

        } catch (error) {
            report.issues.push({
                server: 'system',
                type: 'error',
                severity: 'critical',
                message: `Report generation failed: ${error instanceof Error ? error.message : String(error)}`
            });
        }

        return report;
    }
}