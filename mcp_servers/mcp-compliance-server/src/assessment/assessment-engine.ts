/**
 * MCP Configuration and Compliance Server - Assessment Engine
 * 
 * This module performs comprehensive assessments of MCP servers and configurations.
 */

import { Logger } from '../logger';
import {
    AssessmentResult,
    ServerStatus,
    ConfigurationIssue,
    DiscoveredServer,
    AssessmentOptions,
    ComplianceIssue
} from '../types';
import fs from 'fs/promises';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export class AssessmentEngine {
    private logger: Logger;
    private projectRoot: string;
    private kilocodeDir: string;
    private vscodeDir: string;
    private assessmentCount: number = 0;

    constructor(logger: Logger, projectRoot: string = process.cwd()) {
        this.logger = logger;
        this.projectRoot = projectRoot;
        this.kilocodeDir = path.join(projectRoot, '.kilocode');
        this.vscodeDir = path.join(projectRoot, '.vscode');
    }

    /**
     * Perform comprehensive compliance assessment
     */
    async assessCompliance(
        servers: string[] = [],
        standards: string[] = [],
        options: AssessmentOptions = {
            includeDetails: true,
            generateReport: true,
            saveResults: false,
            checkServerStatus: true,
            validateConfig: true,
            checkCompliance: true,
            deepScan: false
        }
    ): Promise<AssessmentResult> {
        this.logger.info('Starting compliance assessment', {
            servers,
            standards,
            options
        });

        this.assessmentCount++;
        const assessmentId = `assessment-${this.assessmentCount}`;
        const startTime = Date.now();

        const result: AssessmentResult = {
            timestamp: new Date().toISOString(),
            totalServers: 0,
            compliantServers: 0,
            nonCompliantServers: 0,
            missingServers: [],
            configurationIssues: [],
            serverStatuses: [],
            overallScore: 0,
            summary: {
                criticalIssues: 0,
                highIssues: 0,
                mediumIssues: 0,
                lowIssues: 0
            }
        };

        try {
            // Step 1: Discover servers
            const discovery = await this.discoverServers();
            this.logger.info('Server discovery completed', {
                discovered: discovery.servers.length,
                errors: discovery.errors.length,
                warnings: discovery.warnings.length
            });

            // Step 2: Filter servers if specific ones requested
            const targetServers = servers.length > 0
                ? discovery.servers.filter(server => servers.includes(server.name))
                : discovery.servers;

            result.totalServers = targetServers.length;

            // Step 3: Assess each server
            for (const server of targetServers) {
                const serverAssessment = await this.assessServer(server, options);
                result.serverStatuses.push(serverAssessment.status);

                if (serverAssessment.compliant) {
                    result.compliantServers++;
                } else {
                    result.nonCompliantServers++;
                    result.configurationIssues.push(...serverAssessment.issues);

                    // Update summary
                    for (const issue of serverAssessment.issues) {
                        switch (issue.severity) {
                            case 'critical':
                                result.summary.criticalIssues++;
                                break;
                            case 'high':
                                result.summary.highIssues++;
                                break;
                            case 'medium':
                                result.summary.mediumIssues++;
                                break;
                            case 'low':
                                result.summary.lowIssues++;
                                break;
                        }
                    }
                }
            }

            // Step 4: Check for missing servers
            const expectedServers = await this.getExpectedServers();
            const missingServers = expectedServers.filter(expected =>
                !targetServers.some(discovered => discovered.name === expected)
            );
            result.missingServers = missingServers;

            // Step 5: Calculate overall score
            result.overallScore = this.calculateOverallScore(result);

            // Step 6: Generate report if requested
            if (options.generateReport) {
                await this.generateAssessmentReport(result, assessmentId);
            }

            // Step 7: Save results if requested
            if (options.saveResults) {
                await this.saveAssessmentResults(result, assessmentId);
            }

            const duration = Date.now() - startTime;
            this.logger.info('Assessment completed', {
                duration: `${duration}ms`,
                totalServers: result.totalServers,
                compliantServers: result.compliantServers,
                nonCompliantServers: result.nonCompliantServers,
                overallScore: result.overallScore,
                missingServers: result.missingServers.length
            });

        } catch (error) {
            this.logger.error('Assessment failed', error as Error);
            throw new Error(`Assessment failed: ${error instanceof Error ? error.message : String(error)}`);
        }

        return result;
    }

    /**
     * Discover servers in the project
     */
    private async discoverServers(): Promise<ServerDiscoveryResult> {
        const servers: DiscoveredServer[] = [];
        const errors: string[] = [];
        const warnings: string[] = [];

        try {
            // Check configuration files
            const configPaths = [
                path.join(this.kilocodeDir, 'mcp.json'),
                path.join(this.vscodeDir, 'mcp.json')
            ];

            for (const configPath of configPaths) {
                try {
                    const configContent = await fs.readFile(configPath, 'utf-8');
                    const config = JSON.parse(configContent);

                    if (config.mcpServers) {
                        for (const [serverName, serverConfig] of Object.entries(config.mcpServers)) {
                            // Skip if already discovered
                            if (servers.some(s => s.name === serverName)) {
                                continue;
                            }

                            const discovered: DiscoveredServer = {
                                name: serverName,
                                type: this.determineServerType(serverName),
                                command: (serverConfig as any).command || '',
                                args: (serverConfig as any).args || [],
                                path: undefined as string | undefined,
                                version: undefined as string | undefined,
                                installed: false,
                                configured: true,
                                compliant: false,
                                issues: []
                            } as DiscoveredServer;

                            // Check if server is installed
                            try {
                                discovered.installed = await this.checkServerInstallation(discovered);
                            } catch (error) {
                                errors.push(`Failed to check installation for ${serverName}: ${error instanceof Error ? error.message : String(error)}`);
                            }

                            // Check version
                            try {
                                discovered.version = await this.getServerVersion(discovered);
                            } catch (error) {
                                warnings.push(`Failed to get version for ${serverName}: ${error instanceof Error ? error.message : String(error)}`);
                            }

                            servers.push(discovered);
                        }
                    }
                } catch (error) {
                    if (!configPath.includes('mcp.json')) {
                        warnings.push(`Failed to read config file: ${configPath}`);
                    }
                }
            }

            // Discover additional servers in mcp_servers directory
            try {
                const mcpServersDir = path.join(this.projectRoot, 'mcp_servers');
                if (await this.pathExists(mcpServersDir)) {
                    const serverFiles = await fs.readdir(mcpServersDir);

                    for (const file of serverFiles) {
                        if (file.endsWith('-server.js') || file.endsWith('.js')) {
                            const serverName = file.replace('-server.js', '').replace('.js', '');

                            // Skip if already discovered
                            if (servers.some(s => s.name === serverName)) {
                                continue;
                            }

                            const discovered: DiscoveredServer = {
                                name: serverName,
                                type: 'node',
                                command: 'node',
                                args: [path.join(mcpServersDir, file)],
                                path: path.join(mcpServersDir, file),
                                version: undefined as string | undefined,
                                installed: true,
                                configured: false,
                                compliant: false,
                                issues: []
                            } as DiscoveredServer;

                            servers.push(discovered);
                        }
                    }
                }
            } catch (error) {
                warnings.push(`Failed to scan mcp_servers directory: ${error instanceof Error ? error.message : String(error)}`);
            }

        } catch (error) {
            errors.push(`Server discovery failed: ${error instanceof Error ? error.message : String(error)}`);
        }

        return { servers, errors, warnings };
    }

    /**
     * Assess individual server
     */
    private async assessServer(server: DiscoveredServer, options: AssessmentOptions): Promise<{
        status: ServerStatus;
        compliant: boolean;
        issues: ConfigurationIssue[];
    }> {
        const issues: ConfigurationIssue[] = [];
        let compliant = true;

        const status: ServerStatus = {
            name: server.name,
            status: 'unknown',
            command: server.command,
            args: server.args,
            env: {},
            lastCheck: new Date().toISOString(),
            responseTime: 0,
            configExists: false,
            healthy: false,
            lastChecked: new Date().toISOString(),
            issues: []
        };

        try {
            // Check configuration
            if (!server.configured) {
                const issue: ConfigurationIssue = {
                    id: `config-missing-${server.name}`,
                    serverName: server.name,
                    issueType: 'missing_config',
                    severity: 'high',
                    description: `Server ${server.name} is not configured`,
                    details: { server },
                    recommendation: 'Configure the server in mcp.json'
                };
                issues.push(issue);
                compliant = false;
            }

            // Check installation
            if (!server.installed) {
                const issue: ConfigurationIssue = {
                    id: `install-missing-${server.name}`,
                    serverName: server.name,
                    issueType: 'missing_config',
                    severity: 'critical',
                    description: `Server ${server.name} is not installed`,
                    details: { server },
                    recommendation: 'Install the server using MCP installer'
                };
                issues.push(issue);
                compliant = false;
            }

            // Check server health
            if (server.installed && server.configured) {
                try {
                    const health = await this.checkServerHealth(server);
                    status.status = health.healthy ? 'online' : 'error';
                    status.responseTime = health.responseTime;
                    status.error = health.error || '';

                    if (!health.healthy) {
                        const issue: ConfigurationIssue = {
                            id: `health-${server.name}`,
                            serverName: server.name,
                            issueType: 'incomplete_config',
                            severity: 'medium',
                            description: `Server ${server.name} is unhealthy`,
                            details: { health },
                            recommendation: 'Check server logs and configuration'
                        };
                        issues.push(issue);
                        compliant = false;
                    }
                } catch (error) {
                    status.status = 'error';
                    status.error = error instanceof Error ? error.message : String(error);

                    const issue: ConfigurationIssue = {
                        id: `health-error-${server.name}`,
                        serverName: server.name,
                        issueType: 'invalid_config',
                        severity: 'high',
                        description: `Server ${server.name} health check failed`,
                        details: { error },
                        recommendation: 'Check server configuration and dependencies'
                    };
                    issues.push(issue);
                    compliant = false;
                }
            } else {
                status.status = 'offline';
            }

            // Check for specific issues based on server type
            if (options.includeDetails) {
                const typeIssues = await this.checkServerTypeSpecificIssues(server);
                issues.push(...typeIssues);

                if (typeIssues.length > 0) {
                    compliant = false;
                }
            }

        } catch (error) {
            status.status = 'error';
            status.error = error instanceof Error ? error.message : String(error);

            const issue: ConfigurationIssue = {
                id: `assessment-error-${server.name}`,
                serverName: server.name,
                issueType: 'invalid_config',
                severity: 'critical',
                description: `Server ${server.name} assessment failed`,
                details: { error },
                recommendation: 'Check server configuration and try again'
            };
            issues.push(issue);
            compliant = false;
        }

        return { status, compliant, issues };
    }

    /**
     * Check server installation
     */
    private async checkServerInstallation(server: DiscoveredServer): Promise<boolean> {
        try {
            switch (server.type) {
                case 'npm':
                    const packageName = `@modelcontextprotocol/server-${server.name}`;
                    await execAsync(`npm list -g ${packageName}`, { timeout: 10000 });
                    return true;

                case 'node':
                    if (server.path && await this.pathExists(server.path)) {
                        return true;
                    }
                    return false;

                case 'python':
                    if (server.command === 'python' || server.command === 'python3') {
                        await execAsync(`${server.command} --version`, { timeout: 5000 });
                        return true;
                    }
                    return false;

                default:
                    return false;
            }
        } catch (error) {
            return false;
        }
    }

    /**
     * Get server version
     */
    private async getServerVersion(server: DiscoveredServer): Promise<string | undefined> {
        try {
            switch (server.type) {
                case 'npm':
                    const result = await execAsync(`npm list -g @modelcontextprotocol/server-${server.name} --json`, { timeout: 10000 });
                    const packageInfo = JSON.parse(result.stdout);
                    return packageInfo.version;

                case 'node':
                case 'python':
                    const versionResult = await execAsync(`${server.command} --version`, { timeout: 5000 });
                    return versionResult.stdout.trim();

                default:
                    return undefined;
            }
        } catch (error) {
            return undefined;
        }
    }

    /**
     * Check server health
     */
    private async checkServerHealth(server: DiscoveredServer): Promise<{
        healthy: boolean;
        responseTime: number;
        error?: string;
    }> {
        const startTime = Date.now();

        try {
            // Simple health check - try to get help or version
            if (server.type === 'npm') {
                await execAsync(`npx -y @modelcontextprotocol/server-${server.name} --help`, { timeout: 5000 });
            } else if (server.type === 'node' && server.path) {
                await execAsync(`node ${server.path} --help`, { timeout: 5000 });
            } else if (server.type === 'python') {
                await execAsync(`${server.command} --version`, { timeout: 5000 });
            }

            const responseTime = Date.now() - startTime;
            return { healthy: true, responseTime };
        } catch (error) {
            const responseTime = Date.now() - startTime;
            return {
                healthy: false,
                responseTime,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }

    /**
     * Check server type specific issues
     */
    private async checkServerTypeSpecificIssues(server: DiscoveredServer): Promise<ConfigurationIssue[]> {
        const issues: ConfigurationIssue[] = [];

        try {
            // Check for common issues based on server type
            switch (server.type) {
                case 'npm':
                    // Check if package is outdated
                    try {
                        const result = await execAsync(`npm outdated -g @modelcontextprotocol/server-${server.name}`, { timeout: 10000 });
                        if (result.stdout.trim()) {
                            issues.push({
                                id: `outdated-${server.name}`,
                                serverName: server.name,
                                issueType: 'performance_issue',
                                severity: 'medium',
                                description: `Server ${server.name} package is outdated`,
                                details: { outdated: true },
                                recommendation: 'Update the server package'
                            });
                        }
                    } catch (error) {
                        // Not outdated or check failed
                    }
                    break;

                case 'node':
                    // Check if script file exists and is executable
                    if (server.path) {
                        const stats = await fs.stat(server.path);
                        if (!stats.isFile()) {
                            issues.push({
                                id: `invalid-script-${server.name}`,
                                serverName: server.name,
                                issueType: 'invalid_config',
                                severity: 'high',
                                description: `Server script ${server.path} is not a valid file`,
                                details: { path: server.path },
                                recommendation: 'Check server script file'
                            });
                        }
                    }
                    break;
            }

            // Check for security issues
            const securityIssues = await this.checkSecurityIssues(server);
            issues.push(...securityIssues);

        } catch (error) {
            issues.push({
                id: `type-check-${server.name}`,
                serverName: server.name,
                issueType: 'invalid_config',
                severity: 'medium',
                description: `Failed to check type-specific issues for ${server.name}`,
                details: { error },
                recommendation: 'Check server configuration'
            });
        }

        return issues;
    }

    /**
     * Check for security issues
     */
    private async checkSecurityIssues(server: DiscoveredServer): Promise<ConfigurationIssue[]> {
        const issues: ConfigurationIssue[] = [];

        try {
            // Check for common security patterns in configuration
            if (server.args) {
                for (const arg of server.args) {
                    // Check for hardcoded credentials
                    if (arg.includes('password=') || arg.includes('token=') || arg.includes('secret=')) {
                        issues.push({
                            id: `security-hardcoded-${server.name}`,
                            serverName: server.name,
                            issueType: 'security_issue',
                            severity: 'critical',
                            description: `Hardcoded credentials found in server arguments`,
                            details: { argument: arg },
                            recommendation: 'Use environment variables for sensitive data'
                        });
                    }
                }
            }

            // Check for insecure protocols
            if (server.args.some(arg => arg.includes('http://') && !arg.includes('localhost'))) {
                issues.push({
                    id: `security-insecure-${server.name}`,
                    serverName: server.name,
                    issueType: 'security_issue',
                    severity: 'high',
                    description: `Insecure protocol detected in server configuration`,
                    details: { hasInsecureProtocol: true },
                    recommendation: 'Use HTTPS for external connections'
                });
            }

        } catch (error) {
            issues.push({
                id: `security-check-${server.name}`,
                serverName: server.name,
                issueType: 'security_issue',
                severity: 'medium',
                description: `Failed to check security issues for ${server.name}`,
                details: { error },
                recommendation: 'Review server configuration for security issues'
            });
        }

        return issues;
    }

    /**
     * Determine server type based on name
     */
    private determineServerType(serverName: string): 'npm' | 'node' | 'python' | 'docker' | 'other' {
        const npmServers = [
            'filesystem', 'github', 'postgres', 'sqlite', 'fetch', 'brave-search',
            'rag', 'memory', 'scheduler', 'playwright', 'snap-windows'
        ];

        if (npmServers.includes(serverName)) {
            return 'npm';
        }

        if (serverName.includes('-server') || serverName.includes('mcp-')) {
            return 'node';
        }

        if (serverName.includes('python') || serverName.includes('py')) {
            return 'python';
        }

        if (serverName.includes('docker')) {
            return 'docker';
        }

        return 'other';
    }

    /**
     * Get expected servers from configuration
     */
    private async getExpectedServers(): Promise<string[]> {
        const expectedServers: string[] = [];

        try {
            const configPaths = [
                path.join(this.kilocodeDir, 'mcp.json'),
                path.join(this.vscodeDir, 'mcp.json')
            ];

            for (const configPath of configPaths) {
                try {
                    const configContent = await fs.readFile(configPath, 'utf-8');
                    const config = JSON.parse(configContent);

                    if (config.mcpServers) {
                        expectedServers.push(...Object.keys(config.mcpServers));
                    }
                } catch (error) {
                    // Config file doesn't exist or is invalid
                }
            }
        } catch (error) {
            // Failed to read expected servers
        }

        return expectedServers;
    }

    /**
     * Calculate overall score
     */
    private calculateOverallScore(result: AssessmentResult): number {
        if (result.totalServers === 0) {
            return 0;
        }

        const complianceScore = (result.compliantServers / result.totalServers) * 100;
        const missingPenalty = (result.missingServers.length / result.totalServers) * 20;
        const issuePenalty = (result.configurationIssues.length / result.totalServers) * 10;

        return Math.max(0, Math.round(complianceScore - missingPenalty - issuePenalty));
    }

    /**
     * Generate assessment report
     */
    private async generateAssessmentReport(result: AssessmentResult, assessmentId: string): Promise<void> {
        try {
            const reportPath = path.join(this.kilocodeDir, 'reports', `assessment-${assessmentId}.json`);
            await fs.mkdir(path.dirname(reportPath), { recursive: true });
            await fs.writeFile(reportPath, JSON.stringify(result, null, 2));

            this.logger.info('Assessment report generated', { reportPath });
        } catch (error) {
            this.logger.warn('Failed to generate assessment report', error as Error);
        }
    }

    /**
     * Save assessment results
     */
    private async saveAssessmentResults(result: AssessmentResult, assessmentId: string): Promise<void> {
        try {
            const resultsPath = path.join(this.kilocodeDir, 'assessments', `${assessmentId}.json`);
            await fs.mkdir(path.dirname(resultsPath), { recursive: true });
            await fs.writeFile(resultsPath, JSON.stringify(result, null, 2));

            this.logger.info('Assessment results saved', { resultsPath });
        } catch (error) {
            this.logger.warn('Failed to save assessment results', error as Error);
        }
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

    /**
     * Get assessment count
     */
    getAssessmentCount(): number {
        return this.assessmentCount;
    }
}

interface ServerDiscoveryResult {
    servers: DiscoveredServer[];
    errors: string[];
    warnings: string[];
}