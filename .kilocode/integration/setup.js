#!/usr/bin/env node

/**
 * KiloCode Setup Script
 * This script sets up the KiloCode environment and validates the installation
 */

const fs = require('fs-extra');
const path = require('path');
const { spawn } = require('child_process');
const { Logger } = require('./logger');

class SetupManager {
    constructor() {
        this.logger = new Logger();
        this.projectRoot = process.cwd();
        this.kilocodeDir = path.join(this.projectRoot, '.kilocode');
        this.configDir = path.join(this.kilocodeDir, 'config');
        this.integrationDir = path.join(this.kilocodeDir, 'integration');
        this.logsDir = path.join(this.projectRoot, 'logs');
        this.tempDir = path.join(this.projectRoot, 'temp');
        this.dataDir = path.join(this.projectRoot, 'data');
        this.backupsDir = path.join(this.projectRoot, 'backups');
    }

    /**
     * Main setup process
     */
    async setup() {
        try {
            this.logger.info('Starting KiloCode setup process');

            // Step 1: Create directory structure
            await this.createDirectoryStructure();

            // Step 2: Validate dependencies
            await this.validateDependencies();

            // Step 3: Install MCP servers
            await this.installMCPServers();

            // Step 4: Generate configurations
            await this.generateConfigurations();

            // Step 5: Validate installation
            await this.validateInstallation();

            this.logger.success('KiloCode setup completed successfully');
        } catch (error) {
            this.logger.error(`Setup failed: ${error.message}`);
            throw error;
        }
    }

    /**
     * Create required directory structure
     */
    async createDirectoryStructure() {
        this.logger.info('Creating directory structure');

        const directories = [
            this.kilocodeDir,
            this.configDir,
            this.integrationDir,
            this.logsDir,
            this.tempDir,
            this.dataDir,
            this.backupsDir,
            path.join(this.dataDir, 'mock'),
            path.join(this.dataDir, 'dev'),
            path.join(this.dataDir, 'uploads'),
            path.join(this.dataDir, 'exports'),
            path.join(this.logsDir, 'services'),
            path.join(this.logsDir, 'integration'),
            path.join(this.logsDir, 'errors'),
            path.join(this.backupsDir, 'daily'),
            path.join(this.backupsDir, 'weekly'),
            path.join(this.backupsDir, 'monthly')
        ];

        for (const dir of directories) {
            await fs.ensureDir(dir);
            this.logger.debug(`Created directory: ${dir}`);
        }

        this.logger.success('Directory structure created successfully');
    }

    /**
     * Validate system dependencies
     */
    async validateDependencies() {
        this.logger.info('Validating system dependencies');

        // Check Node.js version
        const nodeVersion = process.version;
        const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
        if (majorVersion < 18) {
            throw new Error(`Node.js version 18 or higher required. Current version: ${nodeVersion}`);
        }

        // Check npm version
        const npmVersion = await this.getNpmVersion();
        if (npmVersion > 0 && npmVersion < 8) {
            this.logger.warn(`npm version 8 or higher recommended. Current version: ${npmVersion}`);
        } else if (npmVersion === 0) {
            this.logger.warn('npm version check failed. Continuing with setup...');
        } else {
            this.logger.debug(`npm version ${npmVersion} is acceptable`);
        }

        // Check Python availability
        const pythonVersion = await this.getPythonVersion();
        if (!pythonVersion) {
            this.logger.warn('Python not found. Some MCP servers may not work properly.');
        }

        // Check required binaries
        const requiredBinaries = ['git', 'npx'];
        for (const binary of requiredBinaries) {
            try {
                await this.executeCommand(binary, ['--version']);
                this.logger.debug(`${binary} is available`);
            } catch (error) {
                this.logger.warn(`${binary} not found. Some functionality may be limited.`);
            }
        }

        this.logger.success('System dependencies validated successfully');
    }

    /**
     * Install MCP servers
     */
    async installMCPServers() {
        this.logger.info('Installing MCP servers');

        try {
            // Use the global MCP installer
            await this.executeCommand('kilocode-mcp-install', ['sync']);
            this.logger.success('MCP servers synchronized successfully');
        } catch (error) {
            this.logger.warn(`Failed to sync MCP servers: ${error.message}`);
            // Continue with setup even if MCP sync fails
        }

        this.logger.success('MCP servers installation process completed');
    }

    /**
     * Generate configuration files
     */
    async generateConfigurations() {
        this.logger.info('Generating configuration files');

        // Generate .kilocode/mcp.json if it doesn't exist
        const mcpConfigPath = path.join(this.kilocodeDir, 'mcp.json');
        if (!(await fs.pathExists(mcpConfigPath))) {
            const defaultConfig = {
                mcpServers: {
                    filesystem: {
                        command: "npx",
                        args: ["-y", "@modelcontextprotocol/server-filesystem", ".", "/tmp"],
                        env: {
                            NODE_ENV: "production",
                            KILOCODE_ENV: "development",
                            KILOCODE_PROJECT_PATH: this.projectRoot,
                            KILOCODE_FS_PATH: this.projectRoot,
                            KILOCODE_PROJECT_NAME: require(path.join(this.projectRoot, 'package.json')).name || 'unknown'
                        }
                    }
                }
            };

            await fs.writeJson(mcpConfigPath, defaultConfig, { spaces: 2 });
            this.logger.info('Created default MCP configuration');
        }

        // Generate environment configuration
        const envConfigPath = path.join(this.configDir, 'environment.yaml');
        if (!(await fs.pathExists(envConfigPath))) {
            const defaultEnvConfig = {
                environment: {
                    current: "development",
                    overrides: {
                        development: {
                            debug: true,
                            logging_level: "DEBUG",
                            cache_ttl: 300
                        }
                    }
                },
                database: {
                    primary: {
                        host: "localhost",
                        port: 5432,
                        name: "postgres",
                        user: "postgres",
                        password: "DeeCee@2001",
                        ssl_mode: "disable"
                    }
                },
                filesystem: {
                    base_path: this.projectRoot,
                    temp_path: path.join(this.projectRoot, 'temp'),
                    logs_path: path.join(this.projectRoot, 'logs'),
                    data_path: path.join(this.projectRoot, 'data'),
                    backups_path: path.join(this.projectRoot, 'backups')
                }
            };

            await fs.writeFile(envConfigPath, JSON.stringify(defaultEnvConfig, null, 2));
            this.logger.info('Created default environment configuration');
        }

        this.logger.success('Configuration files generated successfully');
    }

    /**
     * Validate the installation
     */
    async validateInstallation() {
        this.logger.info('Validating installation');

        // Check if MCP installer is available (but don't fail if not)
        try {
            await this.executeCommand('kilocode-mcp-install', ['--help']);
            this.logger.debug('MCP installer is available');
        } catch (error) {
            this.logger.warn('MCP installer is not available in PATH. You may need to run: npm install -g @kilocode/mcp-installer');
        }

        // Check if required files exist
        const requiredFiles = [
            path.join(this.integrationDir, 'mcp-server-manager.js'),
            path.join(this.integrationDir, 'logger.js'),
            'package.json'
        ];

        for (const file of requiredFiles) {
            if (!(await fs.pathExists(file))) {
                throw new Error(`Required file missing: ${file}`);
            }
        }

        // Check MCP config file (optional)
        const mcpConfigPath = path.join(this.kilocodeDir, 'mcp.json');
        if (!(await fs.pathExists(mcpConfigPath))) {
            this.logger.warn('MCP configuration file not found. Will be generated during setup.');
        }

        // Check if required directories exist
        const requiredDirs = [
            this.kilocodeDir,
            this.configDir,
            this.integrationDir,
            this.logsDir,
            this.dataDir
        ];

        for (const dir of requiredDirs) {
            if (!(await fs.pathExists(dir))) {
                throw new Error(`Required directory missing: ${dir}`);
            }
        }

        // Validate MCP server configurations
        try {
            const mcpConfig = await fs.readJson(path.join(this.kilocodeDir, 'mcp.json'));
            if (!mcpConfig.mcpServers || Object.keys(mcpConfig.mcpServers).length === 0) {
                this.logger.warn('No MCP servers configured');
            } else {
                this.logger.info(`Found ${Object.keys(mcpConfig.mcpServers).length} MCP servers configured`);
            }
        } catch (error) {
            this.logger.warn('Failed to validate MCP server configurations');
        }

        // Check if MCP installer is available (but don't fail if not)
        try {
            await this.executeCommand('kilocode-mcp-install', ['--help']);
            this.logger.debug('MCP installer is available');
        } catch (error) {
            this.logger.warn('MCP installer is not available in PATH. You may need to run: npm install -g @kilocode/mcp-installer');
        }

        this.logger.success('Installation validation completed successfully');
    }

    /**
     * Get npm version
     */
    async getNpmVersion() {
        try {
            const result = await this.executeCommand('npm', ['--version']);
            return parseFloat(result.trim());
        } catch (error) {
            return 0;
        }
    }

    /**
     * Get Python version
     */
    async getPythonVersion() {
        try {
            const result = await this.executeCommand('python', ['--version']);
            return result.trim();
        } catch (error) {
            try {
                const result = await this.executeCommand('python3', ['--version']);
                return result.trim();
            } catch (error) {
                return null;
            }
        }
    }

    /**
     * Execute a command and return the result
     */
    async executeCommand(command, args) {
        return new Promise((resolve, reject) => {
            const child = spawn(command, args, { stdio: 'pipe', cwd: this.projectRoot });

            let stdout = '';
            let stderr = '';

            child.stdout?.on('data', (data) => {
                stdout += data.toString();
            });

            child.stderr?.on('data', (data) => {
                stderr += data.toString();
            });

            child.on('close', (code) => {
                if (code === 0) {
                    resolve(stdout.trim());
                } else {
                    reject(new Error(`Command failed with code ${code}: ${stderr}`));
                }
            });

            child.on('error', (error) => {
                reject(error);
            });
        });
    }

    /**
     * Clean up temporary files
     */
    async cleanup() {
        this.logger.info('Cleaning up temporary files');

        try {
            const tempFiles = [
                path.join(this.tempDir, '*.tmp'),
                path.join(this.tempDir, '*.log'),
                path.join(this.logsDir, '*.tmp')
            ];

            for (const pattern of tempFiles) {
                const files = await fs.glob(pattern);
                for (const file of files) {
                    await fs.remove(file);
                }
            }

            this.logger.success('Cleanup completed successfully');
        } catch (error) {
            this.logger.warn(`Cleanup failed: ${error.message}`);
        }
    }
}

// Export the setup manager
module.exports = { SetupManager };

// If this script is run directly, perform the setup
if (require.main === module) {
    const setupManager = new SetupManager();

    async function main() {
        try {
            await setupManager.setup();
            console.log('KiloCode setup completed successfully!');
            process.exit(0);
        } catch (error) {
            console.error('Setup failed:', error.message);
            process.exit(1);
        }
    }

    // Handle process termination
    process.on('SIGINT', async () => {
        console.log('\nReceived SIGINT, cleaning up...');
        await setupManager.cleanup();
        process.exit(0);
    });

    process.on('SIGTERM', async () => {
        console.log('\nReceived SIGTERM, cleaning up...');
        await setupManager.cleanup();
        process.exit(0);
    });

    main().catch(console.error);
}