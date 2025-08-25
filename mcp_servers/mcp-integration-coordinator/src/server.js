/**
 * MCP Integration Coordinator - Main Server (JavaScript Version)
 * 
 * Coordinates communication between MCP servers with human oversight.
 */

const express = require('express');
const { ServerConfig } = require('./types');
const { Logger } = require('./logger');
const { DatabaseService } = require('./services/database-service');
const { AuditService } = require('./services/audit-service');
const { AssessmentController } = require('./controllers/assessment-controller');
const { RemediationController } = require('./controllers/remediation-controller');
const { AssessmentStore } = require('./services/assessment-store');

class IntegrationCoordinator {
    constructor(config) {
        this.config = config;
        this.app = express();
        this.logger = new Logger({ name: 'IntegrationCoordinator' });

        // Initialize services
        this.databaseService = new DatabaseService(config.database, this.logger);
        this.auditService = new AuditService(this.databaseService, this.logger);

        // Initialize AssessmentStore
        this.assessmentStore = new AssessmentStore({
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
        }, this.logger);

        // Initialize controllers
        this.assessmentController = new AssessmentController(this.assessmentStore, this.auditService);
        this.remediationController = new RemediationController(this.assessmentStore, this.auditService);

        this.setupMiddleware();
        this.setupRoutes();
        this.setupEventHandlers();
    }

    /**
     * Setup Express middleware
     */
    setupMiddleware() {
        this.app.use(express.json());
        this.app.use(express.urlencoded({ extended: true }));

        // Request logging middleware
        this.app.use((req, res, next) => {
            this.logger.info(`${req.method} ${req.path}`, {
                ip: req.ip,
                userAgent: req.get('User-Agent'),
                timestamp: new Date().toISOString()
            });
            next();
        });

        // Error handling middleware
        this.app.use((err, req, res, next) => {
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
    setupRoutes() {
        // Health check
        this.app.get('/health', (req, res) => {
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
        this.app.get('/api/audit/logs', async (req, res) => {
            try {
                const logs = await this.auditService.getLogs({
                    limit: parseInt(req.query.limit) || 100,
                    offset: parseInt(req.query.offset) || 0
                });
                res.json({ logs });
            } catch (error) {
                this.logger.error('Failed to get audit logs', error);
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
        this.app.get('/api/dashboard', async (req, res) => {
            try {
                const stats = await this.auditService.getStats();
                res.json({
                    stats,
                    services: {
                        database: this.databaseService.isConnectionActive(),
                        assessmentStore: true
                    }
                });
            } catch (error) {
                this.logger.error('Failed to get dashboard data', error);
                res.status(500).json({
                    error: {
                        code: 'DASHBOARD_FAILED',
                        message: 'Failed to get dashboard data',
                        retryable: false
                    }
                });
            }
        });

        // Root endpoint
        this.app.get('/', (req, res) => {
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
    setupEventHandlers() {
        // Note: Event handlers have been replaced with Promise-based API calls
        // in AssessmentController and AssessmentProcessor services
    }

    /**
     * Fetch data from compliance server
     */
    async fetchFromComplianceServer(endpoint, options = {}) {
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

        return new Promise((resolve, reject) => {
            const httpModule = url.startsWith('https') ? require('https') : require('http');

            const req = httpModule.request(url, fetchOptions, (res) => {
                let data = '';
                res.on('data', (chunk) => data += chunk);
                res.on('end', () => {
                    try {
                        const parsedData = JSON.parse(data);
                        resolve({
                            statusCode: res.statusCode,
                            headers: res.headers,
                            data: parsedData
                        });
                    } catch (error) {
                        reject(new Error(`Failed to parse response: ${error.message}`));
                    }
                });
            });

            req.on('error', (error) => {
                reject(error);
            });

            req.setTimeout(10000, () => {
                req.destroy();
                reject(new Error('Request timeout'));
            });

            if (fetchOptions.body) {
                req.write(fetchOptions.body);
            }

            req.end();
        });
    }

    /**
     * Start the server
     */
    async start() {
        try {
            // Initialize database
            await this.databaseService.initialize();


            // Start HTTP server
            this.server = this.app.listen(this.config.port, this.config.host, () => {
                this.logger.info(`Integration Coordinator started on ${this.config.host}:${this.config.port}`);
            });

            // Setup graceful shutdown
            this.setupGracefulShutdown();

        } catch (error) {
            this.logger.error('Failed to start Integration Coordinator', error);
            throw error;
        }
    }

    /**
     * Stop the server
     */
    async stop() {
        try {

            if (this.server) {
                await new Promise((resolve) => {
                    this.server.close(() => {
                        this.logger.info('HTTP server stopped');
                        resolve(true);
                    });
                });
            }

            await this.databaseService.close();
            this.logger.info('Integration Coordinator stopped');
        } catch (error) {
            this.logger.error('Failed to stop Integration Coordinator', error);
            throw error;
        }
    }

    /**
     * Setup graceful shutdown
     */
    setupGracefulShutdown() {
        const shutdown = async (signal) => {
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
    getStats() {
        return {
            uptime: process.uptime(),
            memory: process.memoryUsage(),
            eventCount: 0, // EventService removed, so event count is 0
            databaseStatus: this.databaseService.isConnectionActive()
        };
    }
}

// Main execution
if (require.main === module) {
    const config = {
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

module.exports = { IntegrationCoordinator };