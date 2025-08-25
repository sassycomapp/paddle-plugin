/**
 * MCP Configuration and Compliance Server - Remediation Proposal Engine
 *
 * This module analyzes assessment results and generates remediation proposals
 * with prioritization and risk assessment.
 */

import { Logger } from '../logger';
import path from 'path';
import {
    AssessmentResult,
    ConfigurationIssue,
    RemediationProposal,
    RemediationAction,
    RiskAssessment,
    ServerTemplate,
    DiscoveredServer,
    ServerDiscoveryResult,
    MCPServerConfig,
    KiloCodeServerConfig,
    ServerNotFoundError,
    ComplianceError
} from '../types';

export class RemediationProposalEngine {
    private logger: Logger;
    private serverTemplates: Map<string, ServerTemplate>;
    private riskThresholds: Map<string, number>;

    constructor(logger: Logger) {
        this.logger = logger;
        this.serverTemplates = new Map();
        this.riskThresholds = new Map();
        this.initializeServerTemplates();
        this.initializeRiskThresholds();
    }

    /**
     * Generate remediation proposals based on assessment results
     */
    async generateProposals(
        assessment: AssessmentResult,
        discoveryResult?: ServerDiscoveryResult
    ): Promise<RemediationProposal[]> {
        this.logger.info('Generating remediation proposals', {
            totalIssues: assessment.configurationIssues.length
        });

        const proposals: RemediationProposal[] = [];

        try {
            // Process each configuration issue
            for (const issue of assessment.configurationIssues) {
                const proposal = await this.generateProposalForIssue(issue, discoveryResult);
                if (proposal) {
                    proposals.push(proposal);
                }
            }

            // Sort proposals by priority
            proposals.sort((a, b) => this.compareProposals(a, b));

            this.logger.info('Remediation proposals generated', {
                totalProposals: proposals.length,
                criticalProposals: proposals.filter(p => p.priority === 'critical').length,
                highProposals: proposals.filter(p => p.priority === 'high').length
            });

            return proposals;

        } catch (error) {
            this.logger.error('Failed to generate remediation proposals', error as Error);
            throw new ComplianceError('Failed to generate remediation proposals');
        }
    }

    /**
     * Generate a remediation proposal for a specific issue
     */
    private async generateProposalForIssue(
        issue: ConfigurationIssue,
        discoveryResult?: ServerDiscoveryResult
    ): Promise<RemediationProposal | null> {
        try {
            switch (issue.issueType) {
                case 'missing_config':
                    return this.generateMissingConfigProposal(issue, discoveryResult);

                case 'incomplete_config':
                    return this.generateIncompleteConfigProposal(issue);

                case 'invalid_config':
                    return this.generateInvalidConfigProposal(issue);

                case 'security_issue':
                    return this.generateSecurityIssueProposal(issue);

                case 'performance_issue':
                    return this.generatePerformanceIssueProposal(issue);

                default:
                    this.logger.warn(`Unknown issue type: ${issue.issueType}`, { issueId: issue.id });
                    return null;
            }
        } catch (error) {
            this.logger.error(`Failed to generate proposal for issue: ${issue.id}`, error as Error);
            return null;
        }
    }

    /**
     * Generate proposal for missing configuration
     */
    private generateMissingConfigProposal(
        issue: ConfigurationIssue,
        discoveryResult?: ServerDiscoveryResult
    ): RemediationProposal | null {
        const serverName = issue.serverName;

        // Check if server exists in discovery results
        const discoveredServer = discoveryResult?.servers.find(s => s.name === serverName);

        if (!discoveredServer) {
            // Server doesn't exist, can't remediate
            this.logger.warn(`Cannot remediate missing config for non-existent server: ${serverName}`);
            return null;
        }

        // Generate action based on server type
        const action = this.generateInstallAction(discoveredServer);

        return {
            id: `install-${serverName}-${Date.now()}`,
            priority: this.calculatePriority(issue.severity, 'install'),
            issue,
            solution: action,
            risk: this.assessInstallRisk(discoveredServer),
            estimatedTime: this.estimateInstallTime(discoveredServer),
            dependencies: this.getInstallDependencies(discoveredServer),
            prerequisites: this.getInstallPrerequisites(discoveredServer)
        };
    }

    /**
     * Generate proposal for incomplete configuration
     */
    private generateIncompleteConfigProposal(issue: ConfigurationIssue): RemediationProposal {
        const serverName = issue.serverName;

        // Generate action based on issue details
        let action: RemediationAction;

        if (issue.details.missingVars) {
            // Missing environment variables
            action = {
                id: `fix-env-${serverName}-${Date.now()}`,
                type: 'update_config',
                serverName,
                description: `Add missing environment variables to ${serverName}`,
                env: this.generateMissingEnvironmentVariables(issue.details.missingVars),
                estimatedTime: 30,
                requiresRestart: true,
                dependencies: []
            };
        } else if (issue.details.location === 'kilocode') {
            // Missing in KiloCode config
            action = {
                id: `add-to-kilocode-${serverName}-${Date.now()}`,
                type: 'update_config',
                serverName,
                description: `Add server configuration to .kilocode/mcp.json`,
                estimatedTime: 60,
                requiresRestart: true,
                dependencies: []
            };
        } else if (issue.details.location === 'vscode') {
            // Missing in VSCode config
            action = {
                id: `add-to-vscode-${serverName}-${Date.now()}`,
                type: 'update_config',
                serverName,
                description: `Add server configuration to .vscode/mcp.json`,
                estimatedTime: 60,
                requiresRestart: true,
                dependencies: []
            };
        } else {
            // Generic incomplete config
            action = {
                id: `fix-config-${serverName}-${Date.now()}`,
                type: 'update_config',
                serverName,
                description: `Fix incomplete configuration for ${serverName}`,
                estimatedTime: 45,
                requiresRestart: true,
                dependencies: []
            };
        }

        return {
            id: action.id,
            priority: this.calculatePriority(issue.severity, 'config'),
            issue,
            solution: action,
            risk: this.assessConfigRisk(issue),
            estimatedTime: action.estimatedTime,
            dependencies: action.dependencies,
            prerequisites: []
        };
    }

    /**
     * Generate proposal for invalid configuration
     */
    private generateInvalidConfigProposal(issue: ConfigurationIssue): RemediationProposal {
        const serverName = issue.serverName;

        const action: RemediationAction = {
            id: `fix-invalid-${serverName}-${Date.now()}`,
            type: 'update_config',
            serverName,
            description: `Fix invalid configuration for ${serverName}`,
            estimatedTime: 60,
            requiresRestart: true,
            dependencies: []
        };

        return {
            id: action.id,
            priority: this.calculatePriority(issue.severity, 'config'),
            issue,
            solution: action,
            risk: this.assessConfigRisk(issue),
            estimatedTime: action.estimatedTime,
            dependencies: action.dependencies,
            prerequisites: []
        };
    }

    /**
     * Generate proposal for security issue
     */
    private generateSecurityIssueProposal(issue: ConfigurationIssue): RemediationProposal {
        const serverName = issue.serverName;

        const action: RemediationAction = {
            id: `fix-security-${serverName}-${Date.now()}`,
            type: 'fix_security',
            serverName,
            description: `Fix security issue in ${serverName}: ${issue.description}`,
            estimatedTime: 90,
            requiresRestart: true,
            dependencies: []
        };

        return {
            id: action.id,
            priority: this.calculatePriority('critical', 'security'), // Security issues are always critical
            issue,
            solution: action,
            risk: {
                level: 'critical',
                impact: 'Security vulnerability could lead to unauthorized access',
                likelihood: 0.8,
                mitigation: 'Apply security patches and configuration fixes'
            },
            estimatedTime: action.estimatedTime,
            dependencies: action.dependencies,
            prerequisites: []
        };
    }

    /**
     * Generate proposal for performance issue
     */
    private generatePerformanceIssueProposal(issue: ConfigurationIssue): RemediationProposal {
        const serverName = issue.serverName;

        const action: RemediationAction = {
            id: `optimize-performance-${serverName}-${Date.now()}`,
            type: 'optimize_performance',
            serverName,
            description: `Optimize performance for ${serverName}: ${issue.description}`,
            estimatedTime: 120,
            requiresRestart: true,
            dependencies: []
        };

        return {
            id: action.id,
            priority: this.calculatePriority(issue.severity, 'performance'),
            issue,
            solution: action,
            risk: {
                level: 'medium',
                impact: 'Performance issues may affect system responsiveness',
                likelihood: 0.6,
                mitigation: 'Apply performance optimizations and configuration tuning'
            },
            estimatedTime: action.estimatedTime,
            dependencies: action.dependencies,
            prerequisites: []
        };
    }

    /**
     * Generate install action for discovered server
     */
    private generateInstallAction(server: DiscoveredServer): RemediationAction {
        const action: RemediationAction = {
            id: `install-${server.name}-${Date.now()}`,
            type: 'install_server',
            serverName: server.name,
            description: `Install MCP server: ${server.name}`,
            command: server.command,
            args: server.args,
            estimatedTime: this.estimateInstallTime(server),
            requiresRestart: true,
            dependencies: this.getInstallDependencies(server)
        };

        // Add rollback command
        action.rollbackCommand = 'npx';
        action.rollbackArgs = ['-y', '@kilocode/mcp-installer', 'remove', server.name];
        action.rollbackEnv = {};

        return action;
    }

    /**
     * Generate missing environment variables
     */
    private generateMissingEnvironmentVariables(missingVars: string[]): Record<string, string> {
        const env: Record<string, string> = {};

        for (const varName of missingVars) {
            switch (varName) {
                case 'NODE_ENV':
                    env[varName] = 'production';
                    break;
                case 'KILOCODE_ENV':
                    env[varName] = 'development';
                    break;
                case 'KILOCODE_PROJECT_PATH':
                    env[varName] = process.cwd();
                    break;
                case 'KILOCODE_PROJECT_NAME':
                    env[varName] = require(path.join(process.cwd(), 'package.json')).name || 'unknown';
                    break;
                default:
                    env[varName] = '';
            }
        }

        return env;
    }

    /**
     * Calculate priority based on severity and action type
     */
    private calculatePriority(severity: string, actionType: string): 'critical' | 'high' | 'medium' | 'low' {
        const priorityMatrix: Record<string, Record<string, 'critical' | 'high' | 'medium' | 'low'>> = {
            critical: {
                install: 'critical',
                update_config: 'critical',
                fix_security: 'critical',
                optimize_performance: 'high'
            },
            high: {
                install: 'high',
                update_config: 'high',
                fix_security: 'critical',
                optimize_performance: 'medium'
            },
            medium: {
                install: 'medium',
                update_config: 'medium',
                fix_security: 'high',
                optimize_performance: 'medium'
            },
            low: {
                install: 'low',
                update_config: 'low',
                fix_security: 'medium',
                optimize_performance: 'low'
            }
        };

        return priorityMatrix[severity]?.[actionType] || 'medium';
    }

    /**
     * Assess installation risk
     */
    private assessInstallRisk(server: DiscoveredServer): RiskAssessment {
        let level: 'low' | 'medium' | 'high' | 'critical' = 'low';
        let impact = 'Standard installation with minimal risk';
        let likelihood = 0.2;
        let mitigation = 'Standard installation procedure';

        // Higher risk for complex servers
        if (server.type === 'docker') {
            level = 'medium';
            impact = 'Docker installation may have dependency conflicts';
            likelihood = 0.4;
            mitigation = 'Check Docker compatibility and dependencies';
        } else if (server.type === 'python') {
            level = 'medium';
            impact = 'Python server may require specific Python version';
            likelihood = 0.3;
            mitigation = 'Verify Python version and package dependencies';
        } else if (server.args.some(arg => arg.includes('latest'))) {
            level = 'high';
            impact = 'Latest version may have breaking changes';
            likelihood = 0.5;
            mitigation = 'Test in development environment first';
        }

        return { level, impact, likelihood, mitigation };
    }

    /**
     * Assess configuration risk
     */
    private assessConfigRisk(issue: ConfigurationIssue): RiskAssessment {
        let level: 'low' | 'medium' | 'high' | 'critical' = 'low';
        let impact = 'Configuration change with minimal impact';
        let likelihood = 0.1;
        let mitigation = 'Standard configuration update';

        switch (issue.severity) {
            case 'critical':
                level = 'critical';
                impact = 'Critical configuration issue may cause system failure';
                likelihood = 0.7;
                mitigation = 'Apply fix with careful testing and rollback plan';
                break;
            case 'high':
                level = 'high';
                impact = 'High severity configuration issue may affect functionality';
                likelihood = 0.5;
                mitigation = 'Apply fix with testing and monitoring';
                break;
            case 'medium':
                level = 'medium';
                impact = 'Medium severity configuration issue may cause minor problems';
                likelihood = 0.3;
                mitigation = 'Apply fix with basic testing';
                break;
            case 'low':
                level = 'low';
                impact = 'Low severity configuration issue has minimal impact';
                likelihood = 0.1;
                mitigation = 'Apply fix as convenient';
                break;
        }

        return { level, impact, likelihood, mitigation };
    }

    /**
     * Estimate installation time
     */
    private estimateInstallTime(server: DiscoveredServer): number {
        const baseTimes: Record<string, number> = {
            npm: 60,
            python: 90,
            node: 45,
            docker: 120,
            other: 60
        };

        let time = baseTimes[server.type] || 60;

        // Add time for complex configurations
        if (server.args.length > 3) {
            time += 30;
        }

        // Add time for version-specific installations
        if (server.version && server.version !== 'latest') {
            time += 15;
        }

        return time;
    }

    /**
     * Get installation dependencies
     */
    private getInstallDependencies(server: DiscoveredServer): string[] {
        const dependencies: string[] = [];

        switch (server.type) {
            case 'npm':
                dependencies.push('node', 'npm');
                break;
            case 'python':
                dependencies.push('python', 'pip');
                break;
            case 'docker':
                dependencies.push('docker');
                break;
            case 'node':
                dependencies.push('node');
                break;
        }

        return dependencies;
    }

    /**
     * Get installation prerequisites
     */
    private getInstallPrerequisites(server: DiscoveredServer): string[] {
        const prerequisites: string[] = [];

        switch (server.type) {
            case 'npm':
                prerequisites.push('Node.js 18+ installed');
                break;
            case 'python':
                prerequisites.push('Python 3.8+ installed');
                break;
            case 'docker':
                prerequisites.push('Docker installed and running');
                break;
            case 'node':
                prerequisites.push('Node.js installed');
                break;
        }

        return prerequisites;
    }

    /**
     * Compare proposals for sorting
     */
    private compareProposals(a: RemediationProposal, b: RemediationProposal): number {
        const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
        const aPriority = priorityOrder[a.priority];
        const bPriority = priorityOrder[b.priority];

        if (aPriority !== bPriority) {
            return bPriority - aPriority; // Higher priority first
        }

        // Same priority, sort by risk level
        const riskOrder = { critical: 4, high: 3, medium: 2, low: 1 };
        const aRisk = riskOrder[a.risk.level];
        const bRisk = riskOrder[b.risk.level];

        if (aRisk !== bRisk) {
            return bRisk - aRisk; // Higher risk first
        }

        // Same risk, sort by estimated time (shorter first)
        return a.estimatedTime - b.estimatedTime;
    }

    /**
     * Initialize server templates
     */
    private initializeServerTemplates(): void {
        const templates: ServerTemplate[] = [
            {
                name: 'filesystem',
                description: 'Filesystem access MCP server',
                config: {
                    command: 'npx',
                    args: ['-y', '@modelcontextprotocol/server-filesystem', '.', '/tmp'],
                    env: {}
                },
                defaultEnv: {
                    NODE_ENV: 'production',
                    KILOCODE_ENV: 'development',
                    KILOCODE_PROJECT_PATH: process.cwd(),
                    KILOCODE_FS_PATH: process.cwd(),
                    KILOCODE_PROJECT_NAME: require(path.join(process.cwd(), 'package.json')).name || 'unknown'
                },
                requiredEnv: ['NODE_ENV', 'KILOCODE_ENV', 'KILOCODE_PROJECT_PATH', 'KILOCODE_PROJECT_NAME'],
                optionalEnv: ['KILOCODE_FS_PATH'],
                complianceRules: ['filesystem-security', 'filesystem-performance'],
                dependencies: ['@modelcontextprotocol/server-filesystem']
            },
            {
                name: 'postgres',
                description: 'PostgreSQL database MCP server',
                config: {
                    command: 'npx',
                    args: ['-y', '@modelcontextprotocol/server-postgres'],
                    env: {}
                },
                defaultEnv: {
                    NODE_ENV: 'production',
                    KILOCODE_ENV: 'development',
                    KILOCODE_PROJECT_PATH: process.cwd(),
                    KILOCODE_DB_CONFIG: 'postgresql://localhost:5432/postgres',
                    KILOCODE_PROJECT_NAME: require(path.join(process.cwd(), 'package.json')).name || 'unknown'
                },
                requiredEnv: ['NODE_ENV', 'KILOCODE_ENV', 'KILOCODE_PROJECT_PATH', 'KILOCODE_PROJECT_NAME'],
                optionalEnv: ['KILOCODE_DB_CONFIG'],
                complianceRules: ['database-security', 'database-performance'],
                dependencies: ['@modelcontextprotocol/server-postgres']
            },
            {
                name: 'github',
                description: 'GitHub integration MCP server',
                config: {
                    command: 'npx',
                    args: ['-y', '@modelcontextprotocol/server-github'],
                    env: {}
                },
                defaultEnv: {
                    NODE_ENV: 'production',
                    KILOCODE_ENV: 'development',
                    KILOCODE_PROJECT_PATH: process.cwd(),
                    KILOCODE_GITHUB_CONFIG: '',
                    KILOCODE_PROJECT_NAME: require(path.join(process.cwd(), 'package.json')).name || 'unknown'
                },
                requiredEnv: ['NODE_ENV', 'KILOCODE_ENV', 'KILOCODE_PROJECT_PATH', 'KILOCODE_PROJECT_NAME'],
                optionalEnv: ['GITHUB_PERSONAL_ACCESS_TOKEN', 'KILOCODE_GITHUB_CONFIG'],
                complianceRules: ['github-security', 'github-performance'],
                dependencies: ['@modelcontextprotocol/server-github']
            }
        ];

        for (const template of templates) {
            this.serverTemplates.set(template.name, template);
        }
    }

    /**
     * Initialize risk thresholds
     */
    private initializeRiskThresholds(): void {
        this.riskThresholds.set('install', 0.7);
        this.riskThresholds.set('update_config', 0.5);
        this.riskThresholds.set('fix_security', 0.9);
        this.riskThresholds.set('optimize_performance', 0.3);
    }

    /**
     * Get server template by name
     */
    getServerTemplate(serverName: string): ServerTemplate | undefined {
        return this.serverTemplates.get(serverName);
    }

    /**
     * Get all available server templates
     */
    getAllServerTemplates(): ServerTemplate[] {
        return Array.from(this.serverTemplates.values());
    }

    /**
     * Validate remediation proposal
     */
    validateProposal(proposal: RemediationProposal): { valid: boolean; errors: string[] } {
        const errors: string[] = [];

        // Validate basic structure
        if (!proposal.id || proposal.id.length === 0) {
            errors.push('Proposal ID is required');
        }

        if (!proposal.priority || !['critical', 'high', 'medium', 'low'].includes(proposal.priority)) {
            errors.push('Valid priority is required');
        }

        if (!proposal.issue || !proposal.issue.id) {
            errors.push('Valid issue is required');
        }

        if (!proposal.solution || !proposal.solution.id) {
            errors.push('Valid solution is required');
        }

        if (!proposal.risk || !proposal.risk.level) {
            errors.push('Valid risk assessment is required');
        }

        if (proposal.estimatedTime <= 0) {
            errors.push('Estimated time must be positive');
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    /**
     * Filter proposals by priority
     */
    filterProposalsByPriority(proposals: RemediationProposal[], priority: string): RemediationProposal[] {
        return proposals.filter(p => p.priority === priority);
    }

    /**
     * Filter proposals by server name
     */
    filterProposalsByServer(proposals: RemediationProposal[], serverName: string): RemediationProposal[] {
        return proposals.filter(p => p.issue.serverName === serverName);
    }

    /**
     * Get proposals that require approval
     */
    getProposalsRequiringApproval(proposals: RemediationProposal[]): RemediationProposal[] {
        return proposals.filter(p =>
            p.priority === 'critical' ||
            p.risk.level === 'critical' ||
            p.solution.requiresRestart
        );
    }

    /**
     * Estimate total remediation time
     */
    estimateTotalTime(proposals: RemediationProposal[]): number {
        return proposals.reduce((total, proposal) => total + proposal.estimatedTime, 0);
    }

    /**
     * Get critical path for remediation
     */
    getCriticalPath(proposals: RemediationProposal[]): RemediationProposal[] {
        const criticalProposals = proposals.filter(p =>
            p.priority === 'critical' ||
            p.risk.level === 'critical'
        );

        // Sort by dependencies (simplified - assumes linear dependencies)
        return criticalProposals.sort((a, b) => a.estimatedTime - b.estimatedTime);
    }
}