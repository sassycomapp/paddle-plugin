/**
 * MCP Configuration and Compliance Server
 * 
 * Main server implementation that provides MCP protocol compliance checking,
 * configuration management, and remediation capabilities.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
    Tool
} from '@modelcontextprotocol/sdk/types.js';
import { DefaultLogger as Logger } from './logger';
import { ComplianceEngine } from './compliance/compliance-engine';
import { ExecutionEngine } from './execution/execution-engine';
import { AssessmentEngine } from './assessment/assessment-engine';
import {
    ComplianceReport,
    RemediationProposal,
    RemediationAction,
    RemediationOptions,
    AssessmentOptions,
    ServerConfig,
    TestResult
} from './types';

export class MCPComplianceServer {
    private server: Server;
    private logger: Logger;
    private complianceEngine: ComplianceEngine;
    private executionEngine: ExecutionEngine;
    private assessmentEngine: AssessmentEngine;
    private remediationEngine: any;
    private projectRoot: string;

    constructor(projectRoot: string = process.cwd()) {
        this.projectRoot = projectRoot;
        this.logger = new Logger({ name: 'MCPComplianceServer' });

        // Initialize engines
        this.complianceEngine = new ComplianceEngine(this.logger, projectRoot);
        this.executionEngine = new ExecutionEngine(this.logger, projectRoot);
        this.assessmentEngine = new AssessmentEngine(this.logger, projectRoot);
        // this.remediationEngine = new RemediationEngine(this.logger, projectRoot);

        // Initialize MCP server
        this.server = new Server(
            {
                name: 'mcp-compliance-server',
                version: '1.0.0',
                description: 'MCP Configuration and Compliance Server for KiloCode ecosystem'
            },
            {
                capabilities: {
                    tools: {}
                }
            }
        );

        // Set up request handlers
        this.setupRequestHandlers();
    }

    /**
     * Set up MCP request handlers
     */
    private setupRequestHandlers(): void {
        // List available tools
        this.server.setRequestHandler(ListToolsRequestSchema, async () => {
            return {
                tools: [
                    {
                        name: 'compliance_assessment',
                        description: 'Perform compliance assessment of MCP servers and configurations',
                        inputSchema: {
                            type: 'object',
                            properties: {
                                servers: {
                                    type: 'array',
                                    items: { type: 'string' },
                                    description: 'Specific servers to assess (empty for all)'
                                },
                                standards: {
                                    type: 'array',
                                    items: { type: 'string' },
                                    description: 'Compliance standards to check against'
                                },
                                options: {
                                    type: 'object',
                                    properties: {
                                        includeDetails: { type: 'boolean', default: true },
                                        generateReport: { type: 'boolean', default: true },
                                        saveResults: { type: 'boolean', default: false }
                                    }
                                }
                            }
                        }
                    },
                    {
                        name: 'generate_remediation_proposal',
                        description: 'Generate remediation proposals for compliance issues',
                        inputSchema: {
                            type: 'object',
                            properties: {
                                assessmentId: {
                                    type: 'string',
                                    description: 'Assessment ID to generate proposals for'
                                },
                                issues: {
                                    type: 'array',
                                    items: { type: 'string' },
                                    description: 'Specific issues to address (empty for all)'
                                },
                                priority: {
                                    type: 'string',
                                    enum: ['low', 'medium', 'high', 'critical'],
                                    default: 'medium'
                                },
                                autoApprove: {
                                    type: 'boolean',
                                    default: false
                                }
                            }
                        }
                    },
                    {
                        name: 'execute_remediation',
                        description: 'Execute approved remediation actions with testing',
                        inputSchema: {
                            type: 'object',
                            properties: {
                                actions: {
                                    type: 'array',
                                    items: {
                                        type: 'object',
                                        properties: {
                                            id: { type: 'string' },
                                            type: { type: 'string' },
                                            serverName: { type: 'string' },
                                            command: { type: 'string' },
                                            args: { type: 'array', items: { type: 'string' } },
                                            env: { type: 'object' },
                                            estimatedTime: { type: 'number' }
                                        }
                                    },
                                    description: 'Remediation actions to execute'
                                },
                                options: {
                                    type: 'object',
                                    properties: {
                                        autoApprove: { type: 'boolean', default: false },
                                        dryRun: { type: 'boolean', default: false },
                                        rollbackOnFailure: { type: 'boolean', default: true },
                                        parallelExecution: { type: 'boolean', default: false },
                                        maxConcurrent: { type: 'number', default: 1 },
                                        timeout: { type: 'number', default: 300000 }
                                    }
                                }
                            }
                        }
                    },
                    {
                        name: 'get_server_status',
                        description: 'Get status of MCP servers and configurations',
                        inputSchema: {
                            type: 'object',
                            properties: {
                                servers: {
                                    type: 'array',
                                    items: { type: 'string' },
                                    description: 'Specific servers to check (empty for all)'
                                },
                                includeConfig: {
                                    type: 'boolean',
                                    default: true
                                },
                                includeHealth: {
                                    type: 'boolean',
                                    default: true
                                }
                            }
                        }
                    },
                    {
                        name: 'validate_configuration',
                        description: 'Validate MCP server configurations',
                        inputSchema: {
                            type: 'object',
                            properties: {
                                configPath: {
                                    type: 'string',
                                    description: 'Path to configuration file (empty for default)'
                                },
                                servers: {
                                    type: 'array',
                                    items: { type: 'string' },
                                    description: 'Specific servers to validate (empty for all)'
                                },
                                strict: {
                                    type: 'boolean',
                                    default: false
                                }
                            }
                        }
                    },
                    {
                        name: 'get_execution_status',
                        description: 'Get status of ongoing remediation executions',
                        inputSchema: {
                            type: 'object',
                            properties: {
                                actionId: {
                                    type: 'string',
                                    description: 'Specific action ID to check (empty for all)'
                                }
                            }
                        }
                    },
                    {
                        name: 'cancel_execution',
                        description: 'Cancel ongoing remediation execution',
                        inputSchema: {
                            type: 'object',
                            properties: {
                                actionId: {
                                    type: 'string',
                                    required: true,
                                    description: 'Action ID to cancel'
                                }
                            }
                        }
                    }
                ]
            };
        });

        // Handle tool calls
        this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
            const { name, arguments: args } = request.params;

            try {
                switch (name) {
                    case 'compliance_assessment':
                        return await this.handleComplianceAssessment(args);

                    case 'generate_remediation_proposal':
                        return await this.handleGenerateRemediationProposal(args);

                    case 'execute_remediation':
                        return await this.handleExecuteRemediation(args);

                    case 'get_server_status':
                        return await this.handleGetServerStatus(args);

                    case 'validate_configuration':
                        return await this.handleValidateConfiguration(args);

                    case 'get_execution_status':
                        return await this.handleGetExecutionStatus(args);

                    case 'cancel_execution':
                        return await this.handleCancelExecution(args);

                    default:
                        throw new Error(`Unknown tool: ${name}`);
                }
            } catch (error) {
                this.logger.error(`Tool execution failed: ${name}`, error as Error);
                return {
                    content: [
                        {
                            type: 'text',
                            text: `Error: ${error instanceof Error ? error.message : String(error)}`
                        }
                    ]
                };
            }
        });
    }

    /**
     * Handle compliance assessment tool call
     */
    private async handleComplianceAssessment(args: any): Promise<any> {
        const options: AssessmentOptions = {
            includeDetails: args.options?.includeDetails ?? true,
            generateReport: args.options?.generateReport ?? true,
            saveResults: args.options?.saveResults ?? false,
            checkServerStatus: true,
            validateConfig: true,
            checkCompliance: true,
            deepScan: false
        };

        const assessment = await this.assessmentEngine.assessCompliance(
            args.servers || [],
            args.standards || [],
            options
        );

        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify(assessment, null, 2)
                }
            ]
        };
    }

    /**
     * Handle generate remediation proposal tool call
     */
    private async handleGenerateRemediationProposal(args: any): Promise<any> {
        // Placeholder for remediation proposal generation
        const proposal = {
            id: `proposal-${Date.now()}`,
            assessmentId: args.assessmentId,
            issues: args.issues || [],
            priority: args.priority || 'medium',
            autoApprove: args.autoApprove || false,
            actions: [],
            estimatedTime: 0,
            confidence: 0.8,
            recommendations: ['Manual review required for remediation proposals']
        };

        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify(proposal, null, 2)
                }
            ]
        };
    }

    /**
     * Handle execute remediation tool call
     */
    private async handleExecuteRemediation(args: any): Promise<any> {
        const options: RemediationOptions = {
            autoApprove: args.options?.autoApprove ?? false,
            dryRun: args.options?.dryRun ?? false,
            rollbackOnFailure: args.options?.rollbackOnFailure ?? true,
            parallelExecution: args.options?.parallelExecution ?? false,
            maxConcurrent: args.options?.maxConcurrent ?? 1,
            timeout: args.options?.timeout ?? 300000
        };

        const results = await this.executionEngine.executeActions(
            args.actions,
            options
        );

        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify(results, null, 2)
                }
            ]
        };
    }

    /**
     * Handle get server status tool call
     */
    private async handleGetServerStatus(args: any): Promise<any> {
        const status = await this.complianceEngine.getServerStatus(
            args.servers || [],
            args.includeConfig ?? true,
            args.includeHealth ?? true
        );

        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify(status, null, 2)
                }
            ]
        };
    }

    /**
     * Handle validate configuration tool call
     */
    private async handleValidateConfiguration(args: any): Promise<any> {
        const validation = await this.complianceEngine.validateConfiguration(
            args.configPath,
            args.servers || [],
            args.strict ?? false
        );

        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify(validation, null, 2)
                }
            ]
        };
    }

    /**
     * Handle get execution status tool call
     */
    private async handleGetExecutionStatus(args: any): Promise<any> {
        if (args.actionId) {
            const status = this.executionEngine.getExecutionStatus(args.actionId);
            return {
                content: [
                    {
                        type: 'text',
                        text: JSON.stringify(status, null, 2)
                    }
                ]
            };
        } else {
            const allStatus = this.executionEngine.getActiveExecutions();
            return {
                content: [
                    {
                        type: 'text',
                        text: JSON.stringify(allStatus, null, 2)
                    }
                ]
            };
        }
    }

    /**
     * Handle cancel execution tool call
     */
    private async handleCancelExecution(args: any): Promise<any> {
        const success = await this.executionEngine.cancelExecution(args.actionId);

        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify({
                        success,
                        actionId: args.actionId,
                        message: success ? 'Execution cancelled successfully' : 'Failed to cancel execution'
                    }, null, 2)
                }
            ]
        };
    }

    /**
     * Start the server
     */
    async run(): Promise<void> {
        const transport = new StdioServerTransport();
        await this.server.connect(transport);

        this.logger.info('MCP Compliance Server started successfully');
        this.logger.info(`Project root: ${this.projectRoot}`);
        this.logger.info('Available tools: compliance_assessment, generate_remediation_proposal, execute_remediation, get_server_status, validate_configuration, get_execution_status, cancel_execution');
    }

    /**
     * Get server statistics
     */
    getStats(): {
        uptime: number;
        totalAssessments: number;
        totalRemediations: number;
        activeExecutions: number;
        successRate: number;
    } {
        return {
            uptime: process.uptime(),
            totalAssessments: this.assessmentEngine.getAssessmentCount(),
            totalRemediations: this.executionEngine.getExecutionStats().total,
            activeExecutions: this.executionEngine.getExecutionStats().active,
            successRate: this.executionEngine.getExecutionStats().completed > 0
                ? parseFloat((this.executionEngine.getExecutionStats().successful / this.executionEngine.getExecutionStats().completed * 100).toFixed(1))
                : 0
        };
    }
}

// Main execution
if (require.main === module) {
    const server = new MCPComplianceServer();
    server.run().catch(console.error);
}