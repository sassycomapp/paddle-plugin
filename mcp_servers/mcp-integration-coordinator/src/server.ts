/**
 * MCP Integration Coordinator - Main Server
 * 
 * Coordinates communication between MCP servers with human oversight.
 */

import express from 'express';
import { ServerConfig, AssessmentProcessorConfig } from './types';
import { DefaultLogger } from './logger';
import { DatabaseService } from './services/database-service';
import { AuditService } from './services/audit-service';
import { AssessmentProcessor } from './services/assessment-processor';
import { AssessmentStore } from './services/assessment-store';
import { AssessmentController } from './controllers/assessment-controller';
import { RemediationController } from './controllers/remediation-controller';

export class IntegrationCoordinator {
    private app: express.Application;
    private logger: DefaultLogger;
    private databaseService: DatabaseService;
    private auditService: AuditService;
    private assessmentStore: AssessmentStore;
    private assessmentProcessor: AssessmentProcessor;
    private assessmentController: AssessmentController;
    private remediationController: RemediationController;
    private config: ServerConfig;
    private server: any;

    constructor(config: ServerConfig) {
        this.config = config;
        this.app = express();
        this.logger = new DefaultLogger({ name: 'IntegrationCoordinator' });

        // Initialize services
        this.databaseService = new DatabaseService(config.database, this.logger);
        this.auditService = new AuditService(this.databaseService, this.logger);

        // Initialize AssessmentStore
        this.assessmentStore = new AssessmentStore(
            {
                database: config.database,
                processing: {
                    timeout: 30000,
                    maxRetries: 3,
                    retryDelay: 5000,
                    queueSize: 100
                },
                complianceServer: {
                    baseUrl: 'http://localhost:3000',
                    apiKey: 'your-api-key',
                    timeout: 30000,
                    maxConcurrent: 5
                }
            },
            this.logger,
            this.databaseService,
            this.auditService
        );

        // Initialize AssessmentProcessor
        const assessmentProcessorConfig: AssessmentProcessorConfig = {
            assessmentStore: {
                database: config.database,
                complianceServer: {
                    baseUrl: 'http://localhost:3000',
                    apiKey: 'your-api-key',
                    timeout: 30000,
                    maxConcurrent: 5
                },
                processing: {
                    timeout: 30000,
                    maxRetries: 3,
                    retryDelay: 5000,
                    queueSize: 100
                }
            },
            processing: {
                timeout: 30000,
                maxRetries: 3,
                retryDelay: 5000,
                retryBackoff: 2,
                queueSize: 100,
                batchSize: 5,
                processingInterval: 1000
            },
            circuitBreaker: {
                failureThreshold: 5,
                resetTimeout: 60000,
                monitoringInterval: 30000
            },
            logging: {
                level: 'info',
                enableMetrics: true
            }
        };

        this.assessmentProcessor = new AssessmentProcessor(
            assessmentProcessorConfig,
            this.logger,
            this.databaseService,
            this.auditService,
            this.assessmentStore
        );

        // Initialize controllers
        this.assessmentController = new AssessmentController(this.assessmentStore, this.assessmentProcessor, this.auditService);
        this.remediationController = new RemediationController(this.assessmentStore, this.auditService); // Use AssessmentStore instead of EventService

        this.setupMiddleware();
        this.setupRoutes();
        this.setupEventHandlers();
    }

    /**
     * Setup Express middleware
     */
    private setupMiddleware(): void {
        this.app.use(express.json());
        this.app.use(express.urlencoded({ extended: true }));

        // Request logging middleware
        this.app.use((_req, _res, next) => {
            this.logger.info(`Request received`, {
                timestamp: new Date().toISOString()
            });
            next();
        });

        // Error handling middleware
        this.app.use((err: any, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
            this.logger.error('Unhandled error', err);
            res.status(500).json({
                error: {
                    code: 'INTERNAL_ERROR',
                    message: 'Internal server error',
                    retryable: false
                },
                timestamp: new Date().toISOString()
            });
        });
    }

    /**
     * Setup API routes
     */
    private setupRoutes(): void {
        // Health check
        this.app.get('/health', (_req, res) => {
            res.json({
                status: 'healthy',
                timestamp: new Date().toISOString(),
                services: {
                    database: this.databaseService.isConnectionActive(),
                    assessmentStore: true
                }
            });
        });

        // API routes
        this.app.use('/api/assessment', this.assessmentController.getRouter());
        this.app.use('/api/remediation', this.remediationController.getRouter());

        // Audit logs
        this.app.get('/api/audit/logs', async (_req, res) => {
            try {
                const logs = await this.auditService.getLogs({
                    limit: parseInt((_req as any).query.limit as string) || 100,
                    offset: parseInt((_req as any).query.offset as string) || 0
                });
                res.json({ logs });
            } catch (error) {
                this.logger.error('Failed to get audit logs', error as Error);
                res.status(500).json({
                    error: {
                        code: 'AUDIT_LOGS_FAILED',
                        message: 'Failed to get audit logs',
                        retryable: false
                    }
                });
            }
        });

        // Dashboard data
        this.app.get('/api/dashboard', async (_req, res) => {
            try {
                const stats = await this.auditService.getStats();
                res.json({
                    stats,
                    services: {
                        database: this.databaseService.isConnectionActive(),
                        assessmentStore: true,
                        assessmentProcessor: this.assessmentProcessor.getMetrics()
                    }
                });
            } catch (error) {
                this.logger.error('Failed to get dashboard data', error as Error);
                res.status(500).json({
                    error: {
                        code: 'DASHBOARD_FAILED',
                        message: 'Failed to get dashboard data',
                        retryable: false
                    }
                });
            }
        });

        // AssessmentProcessor endpoints
        this.app.get('/api/assessment-processor/metrics', async (_req, res) => {
            try {
                const metrics = this.assessmentProcessor.getMetrics();
                const queueStatus = this.assessmentProcessor.getQueueStatus();
                res.json({
                    metrics,
                    queueStatus
                });
            } catch (error) {
                this.logger.error('Failed to get assessment processor metrics', error as Error);
                res.status(500).json({
                    error: {
                        code: 'ASSESSMENT_PROCESSOR_METRICS_FAILED',
                        message: 'Failed to get assessment processor metrics',
                        retryable: false
                    }
                });
            }
        });

        this.app.post('/api/assessment-processor/process/:assessmentId', async (req, res) => {
            try {
                const { assessmentId } = req.params;
                await this.assessmentProcessor.processAssessment(assessmentId);
                res.json({
                    assessmentId,
                    status: 'processing',
                    message: 'Assessment processing started'
                });
            } catch (error) {
                this.logger.error('Failed to start assessment processing', error as Error);
                res.status(500).json({
                    error: {
                        code: 'ASSESSMENT_PROCESSING_FAILED',
                        message: 'Failed to start assessment processing',
                        retryable: true
                    }
                });
            }
        });

        // Root endpoint
        this.app.get('/', (_req, res) => {
            res.json({
                name: 'MCP Integration Coordinator',
                version: '1.0.0',
                description: 'Coordinates communication between MCP servers with human oversight',
                endpoints: {
                    health: '/health',
                    assessment: '/api/assessment',
                    remediation: '/api/remediation',
                    audit: '/api/audit/logs',
                    dashboard: '/api/dashboard'
                }
            });
        });
    }

    /**
     * Setup event handlers
     */
    private setupEventHandlers(): void {
        // Note: Event handlers have been replaced with Promise-based API calls
        // in AssessmentController and AssessmentProcessor services
    }

    /**
     * Fetch data from compliance server
     */
    private async fetchFromComplianceServer(endpoint: string, options: any = {}) {
        const url = `http://localhost:3000${endpoint}`;
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const fetchOptions = { ...defaultOptions, ...options };

        if (fetchOptions.body) {
            fetchOptions.body = JSON.stringify(fetchOptions.body);
        }

        const response = await fetch(url, fetchOptions);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    /**
     * Start the server
     */
    async start(): Promise<void> {
        try {
            // Initialize database
            await this.databaseService.initialize();

            // Start AssessmentProcessor
            await this.assessmentProcessor.start();

            // Start HTTP server
            this.server = this.app.listen(this.config.port, this.config.host, () => {
                this.logger.info(`Integration Coordinator started on ${this.config.host}:${this.config.port}`);
            });

            // Setup graceful shutdown
            this.setupGracefulShutdown();

        } catch (error) {
            this.logger.error('Failed to start Integration Coordinator', error as Error);
            throw error;
        }
    }

    /**
     * Stop the server
     */
    async stop(): Promise<void> {
        try {
            if (this.server) {
                await new Promise((resolve) => {
                    this.server.close(() => {
                        this.logger.info('HTTP server stopped');
                        resolve(true);
                    });
                });
            }

            // Stop AssessmentProcessor
            await this.assessmentProcessor.stop();

            await this.databaseService.close();
            this.logger.info('Integration Coordinator stopped');
        } catch (error) {
            this.logger.error('Failed to stop Integration Coordinator', error as Error);
            throw error;
        }
    }

    /**
     * Setup graceful shutdown
     */
    private setupGracefulShutdown(): void {
        const shutdown = async (signal: string) => {
            this.logger.info(`Received ${signal}, shutting down gracefully...`);
            await this.stop();
            process.exit(0);
        };

        process.on('SIGTERM', () => shutdown('SIGTERM'));
        process.on('SIGINT', () => shutdown('SIGINT'));
    }

    /**
     * Get server statistics
     */
    getStats(): {
        uptime: number;
        memory: NodeJS.MemoryUsage;
        eventCount: number;
        databaseStatus: boolean;
        assessmentStore: boolean;
        assessmentProcessor: any;
    } {
        return {
            uptime: process.uptime(),
            memory: process.memoryUsage(),
            eventCount: 0, // EventService removed, so event count is 0
            databaseStatus: this.databaseService.isConnectionActive(),
            assessmentStore: true,
            assessmentProcessor: this.assessmentProcessor.getMetrics()
        };
    }
}

// Main execution
if (require.main === module) {
    const config: ServerConfig = {
        port: 3001,
        host: 'localhost',
        database: {
            host: 'localhost',
            port: 5432,
            database: 'kilocode_integration',
            username: 'postgres',
            password: 'password',
            ssl: false,
            maxConnections: 10
        },
        logging: {
            level: 'info',
            enableConsole: true
        },
        security: {
            jwtSecret: 'your-secret-key',
            jwtExpiration: '1h',
            bcryptRounds: 12,
            rateLimit: {
                windowMs: 900000, // 15 minutes
                max: 100
            },
            cors: {
                origin: ['http://localhost:3000'],
                credentials: true
            }
        },
        compliance: {
            requireApproval: true,
            backupBeforeChanges: true,
            auditRetentionDays: 90
        }
    };

    const coordinator = new IntegrationCoordinator(config);
    coordinator.start().catch(console.error);
}