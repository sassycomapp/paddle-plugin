#!/usr/bin/env node

/**
 * KiloCode MCP Server Manager
 * This script manages the lifecycle of MCP servers in the KiloCode environment
 */

const fs = require('fs-extra');
const path = require('path');
const { spawn } = require('child_process');
const yaml = require('js-yaml');
const { Logger } = require('./logger');

class MCPManager {
    constructor() {
        this.logger = new Logger();
        this.configPath = path.join(process.cwd(), '.kilocode', 'mcp.json');
        this.servicesConfigPath = path.join(process.cwd(), '.kilocode', 'config', 'services.yaml');
        this.environmentConfigPath = path.join(process.cwd(), '.kilocode', 'config', 'environment.yaml');
        this.runningServers = new Map();
        this.serverConfigs = new Map();
    }

    /**
     * Initialize the MCP server manager
     */
    async initialize() {
        try {
            this.logger.info('Initializing KiloCode MCP Server Manager');

            // Load configurations
            await this.loadConfigurations();

            // Validate environment
            await this.validateEnvironment();

            this.logger.success('MCP Server Manager initialized successfully');
        } catch (error) {
            this.logger.error(`Failed to initialize MCP Server Manager: ${error.message}`);
            throw error;
        }
    }

    /**
     * Load all configuration files
     */
    async loadConfigurations() {
        try {
            // Load MCP server configurations
            if (await fs.pathExists(this.configPath)) {
                const mcpConfig = await fs.readJson(this.configPath);
                this.loadMCPConfigurations(mcpConfig);
            }

            // Load services configuration
            if (await fs.pathExists(this.servicesConfigPath)) {
                const servicesConfig = yaml.load(await fs.readFile(this.servicesConfigPath, 'utf8'));
                this.loadServicesConfigurations(servicesConfig);
            }

            // Load environment configuration
            if (await fs.pathExists(this.environmentConfigPath)) {
                const envConfig = yaml.load(await fs.readFile(this.environmentConfigPath, 'utf8'));
                this.loadEnvironmentConfigurations(envConfig);
            }

            this.logger.info('Configurations loaded successfully');
        } catch (error) {
            this.logger.error(`Failed to load configurations: ${error.message}`);
            throw error;
        }
    }

    /**
     * Load MCP server configurations
     */
    loadMCPConfigurations(config) {
        if (config.mcpServers) {
            for (const [serverName, serverConfig] of Object.entries(config.mcpServers)) {
                if (this.isServerConfig(serverConfig)) {
                    this.serverConfigs.set(serverName, {
                        ...serverConfig,
                        name: serverName,
                        type: 'mcp',
                        status: 'stopped'
                    });
                }
            }
        }
    }

    /**
     * Load services configurations
     */
    loadServicesConfigurations(config) {
        if (config.services && config.services.custom_services && config.services.custom_services.services) {
            for (const [serviceName, serviceConfig] of Object.entries(config.services.custom_services.services)) {
                this.serverConfigs.set(serviceName, {
                    ...serviceConfig,
                    name: serviceName,
                    type: 'custom',
                    status: 'stopped'
                });
            }
        }

        if (config.services && config.services.core_services && config.services.core_services.services) {
            for (const [serviceName, serviceConfig] of Object.entries(config.services.core_services.services)) {
                this.serverConfigs.set(serviceName, {
                    ...serviceConfig,
                    name: serviceName,
                    type: 'core',
                    status: 'stopped'
                });
            }
        }
    }

    /**
     * Load environment configurations
     */
    loadEnvironmentConfigurations(config) {
        this.environmentConfig = config;
    }

    /**
     * Validate the environment
     */
    async validateEnvironment() {
        try {
            // Check if required directories exist
            const requiredDirs = [
                '.kilocode',
                '.kilocode/config',
                '.kilocode/integration',
                'logs',
                'temp',
                'data'
            ];

            for (const dir of requiredDirs) {
                const dirPath = path.join(process.cwd(), dir);
                if (!(await fs.pathExists(dirPath))) {
                    await fs.ensureDir(dirPath);
                    this.logger.info(`Created directory: ${dir}`);
                }
            }

            // Check Node.js version
            const nodeVersion = process.version;
            const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
            if (majorVersion < 18) {
                throw new Error(`Node.js version 18 or higher required. Current version: ${nodeVersion}`);
            }

            this.logger.info('Environment validation completed successfully');
        } catch (error) {
            this.logger.error(`Environment validation failed: ${error.message}`);
            throw error;
        }
    }

    /**
     * Start all configured MCP servers
     */
    async startAllServers() {
        try {
            this.logger.info('Starting all MCP servers');

            const servers = Array.from(this.serverConfigs.values());
            const startPromises = servers.map(server => this.startServer(server.name));

            await Promise.allSettled(startPromises);

            this.logger.info('All MCP servers startup process completed');
        } catch (error) {
            this.logger.error(`Failed to start all servers: ${error.message}`);
            throw error;
        }
    }

    /**
     * Start a specific MCP server
     */
    async startServer(serverName) {
        try {
            const serverConfig = this.serverConfigs.get(serverName);
            if (!serverConfig) {
                throw new Error(`Server ${serverName} not found`);
            }

            if (this.runningServers.has(serverName)) {
                this.logger.warn(`Server ${serverName} is already running`);
                return;
            }

            this.logger.info(`Starting server: ${serverName}`);

            // Prepare environment variables
            const env = {
                ...process.env,
                ...serverConfig.environment,
                NODE_ENV: 'production',
                KILOCODE_ENV: 'development',
                KILOCODE_PROJECT_PATH: process.cwd(),
                KILOCODE_PROJECT_NAME: require(path.join(process.cwd(), 'package.json')).name || 'unknown'
            };

            // Spawn the server process
            const child = spawn(serverConfig.command, serverConfig.args, {
                stdio: 'pipe',
                env: env,
                cwd: process.cwd()
            });

            // Store the process reference
            this.runningServers.set(serverName, {
                process: child,
                config: serverConfig,
                startTime: new Date()
            });

            // Set up process handlers
            child.stdout?.on('data', (data) => {
                const message = data.toString().trim();
                if (message) {
                    this.logger.info(`[${serverName}] ${message}`);
                }
            });

            child.stderr?.on('data', (data) => {
                const message = data.toString().trim();
                if (message) {
                    this.logger.error(`[${serverName}] ${message}`);
                }
            });

            child.on('close', (code) => {
                this.logger.info(`Server ${serverName} exited with code: ${code}`);
                this.runningServers.delete(serverName);
                serverConfig.status = 'stopped';
            });

            child.on('error', (error) => {
                this.logger.error(`Server ${serverName} error: ${error.message}`);
                this.runningServers.delete(serverName);
                serverConfig.status = 'error';
            });

            // Wait a moment for the server to start
            await new Promise(resolve => setTimeout(resolve, 2000));

            serverConfig.status = 'running';
            this.logger.success(`Server ${serverName} started successfully`);

        } catch (error) {
            this.logger.error(`Failed to start server ${serverName}: ${error.message}`);
            serverConfig.status = 'error';
            throw error;
        }
    }

    /**
     * Stop all running MCP servers
     */
    async stopAllServers() {
        try {
            this.logger.info('Stopping all MCP servers');

            const stopPromises = Array.from(this.runningServers.keys()).map(serverName =>
                this.stopServer(serverName)
            );

            await Promise.allSettled(stopPromises);

            this.logger.info('All MCP servers stopped successfully');
        } catch (error) {
            this.logger.error(`Failed to stop all servers: ${error.message}`);
            throw error;
        }
    }

    /**
     * Stop a specific MCP server
     */
    async stopServer(serverName) {
        try {
            const serverProcess = this.runningServers.get(serverName);
            if (!serverProcess) {
                this.logger.warn(`Server ${serverName} is not running`);
                return;
            }

            this.logger.info(`Stopping server: ${serverName}`);

            // Graceful shutdown
            serverProcess.process.kill('SIGTERM');

            // Wait for graceful shutdown
            await new Promise((resolve, reject) => {
                serverProcess.process.on('close', (code) => {
                    this.logger.info(`Server ${serverName} stopped with code: ${code}`);
                    this.runningServers.delete(serverName);
                    const serverConfig = this.serverConfigs.get(serverName);
                    if (serverConfig) {
                        serverConfig.status = 'stopped';
                    }
                    resolve();
                });

                // Force kill after timeout
                setTimeout(() => {
                    if (!serverProcess.process.killed) {
                        serverProcess.process.kill('SIGKILL');
                    }
                }, 10000);
            });

        } catch (error) {
            this.logger.error(`Failed to stop server ${serverName}: ${error.message}`);
            throw error;
        }
    }

    /**
     * Restart a specific MCP server
     */
    async restartServer(serverName) {
        try {
            await this.stopServer(serverName);
            await this.startServer(serverName);
            this.logger.success(`Server ${serverName} restarted successfully`);
        } catch (error) {
            this.logger.error(`Failed to restart server ${serverName}: ${error.message}`);
            throw error;
        }
    }

    /**
     * Get status of all servers
     */
    async getServerStatus() {
        const status = {};

        for (const [serverName, serverConfig] of this.serverConfigs) {
            const isRunning = this.runningServers.has(serverName);
            status[serverName] = {
                name: serverName,
                type: serverConfig.type,
                status: isRunning ? 'running' : serverConfig.status,
                pid: isRunning ? this.runningServers.get(serverName).process.pid : null,
                uptime: isRunning ? Date.now() - this.runningServers.get(serverName).startTime.getTime() : null,
                command: serverConfig.command,
                args: serverConfig.args,
                environment: serverConfig.environment
            };
        }

        return status;
    }

    /**
     * Get logs for a specific server
     */
    async getServerLogs(serverName, lines = 100) {
        // This would be implemented based on your logging strategy
        // For now, return recent process output
        const serverProcess = this.runningServers.get(serverName);
        if (!serverProcess) {
            throw new Error(`Server ${serverName} is not running`);
        }

        // In a real implementation, you would read from log files
        return {
            server: serverName,
            logs: [],
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Health check for all servers
     */
    async healthCheck() {
        const healthStatus = {};

        for (const [serverName, serverConfig] of this.serverConfigs) {
            try {
                const isRunning = this.runningServers.has(serverName);
                healthStatus[serverName] = {
                    healthy: isRunning,
                    status: isRunning ? 'running' : 'stopped',
                    last_check: new Date().toISOString(),
                    uptime: isRunning ? Date.now() - this.runningServers.get(serverName).startTime.getTime() : null
                };
            } catch (error) {
                healthStatus[serverName] = {
                    healthy: false,
                    status: 'error',
                    error: error.message,
                    last_check: new Date().toISOString()
                };
            }
        }

        return healthStatus;
    }

    /**
     * Check if a configuration object is a server configuration
     */
    isServerConfig(config) {
        return config &&
            typeof config === 'object' &&
            'command' in config &&
            'args' in config;
    }

    /**
     * Graceful shutdown
     */
    async shutdown() {
        try {
            this.logger.info('Performing graceful shutdown');
            await this.stopAllServers();
            this.logger.info('Graceful shutdown completed');
        } catch (error) {
            this.logger.error(`Error during graceful shutdown: ${error.message}`);
        }
    }
}

// Export the manager class
module.exports = { MCPManager };

// If this script is run directly, start the manager
if (require.main === module) {
    const manager = new MCPManager();

    async function main() {
        try {
            await manager.initialize();

            // Handle command line arguments
            const command = process.argv[2];

            switch (command) {
                case 'start':
                    await manager.startAllServers();
                    break;
                case 'stop':
                    await manager.stopAllServers();
                    break;
                case 'restart':
                    await manager.stopAllServers();
                    await manager.startAllServers();
                    break;
                case 'status':
                    const status = await manager.getServerStatus();
                    console.log(JSON.stringify(status, null, 2));
                    break;
                case 'health':
                    const health = await manager.healthCheck();
                    console.log(JSON.stringify(health, null, 2));
                    break;
                default:
                    console.log('Usage: node mcp-server-manager.js <start|stop|restart|status|health>');
                    process.exit(1);
            }
        } catch (error) {
            console.error('Error:', error.message);
            process.exit(1);
        }
    }

    // Handle process termination
    process.on('SIGINT', async () => {
        console.log('\nReceived SIGINT, shutting down gracefully...');
        await manager.shutdown();
        process.exit(0);
    });

    process.on('SIGTERM', async () => {
        console.log('\nReceived SIGTERM, shutting down gracefully...');
        await manager.shutdown();
        process.exit(0);
    });

    main().catch(console.error);
}