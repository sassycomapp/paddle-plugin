import fs from 'fs-extra';
import path from 'path';
import { Logger } from './logger';
import { MCPServerConfig, KiloCodeServerConfig, MCPConfig, KiloCodeConfig, ServerMetadata } from './types';

export class ConfigGenerator {
    private logger: Logger;

    constructor() {
        this.logger = new Logger();
    }

    async generateKiloCodeConfig(): Promise<void> {
        this.logger.info('Generating .kilocode/mcp.json configuration');

        const vscodeConfigPath = path.join(process.cwd(), '.vscode', 'mcp.json');
        const kilocodeConfigPath = path.join(process.cwd(), '.kilocode', 'mcp.json');

        try {
            // Load existing VSCode configuration
            const vscodeConfig = await this.loadConfig<MCPConfig>(vscodeConfigPath);

            // Load existing KiloCode configuration to preserve metadata
            const kilocodeConfig = await this.loadConfig<KiloCodeConfig>(kilocodeConfigPath);

            // Generate KiloCode configuration from VSCode config
            const newKiloCodeConfig: KiloCodeConfig = {
                mcpServers: {}
            };

            // Convert VSCode server configs to KiloCode format
            if (vscodeConfig.mcpServers) {
                for (const [serverName, config] of Object.entries(vscodeConfig.mcpServers)) {
                    if (this.isMCPServerConfig(config)) {
                        // Convert to KiloCode format with enhanced environment variables
                        const kilocodeConfig: KiloCodeServerConfig = {
                            command: config.command,
                            args: config.args,
                            env: {
                                ...config.env,
                                NODE_ENV: 'production',
                                KILOCODE_ENV: 'development',
                                KILOCODE_PROJECT_PATH: process.cwd()
                            }
                        };

                        // Add KiloCode-specific environment variables based on server type
                        this.addKiloCodeSpecificEnv(serverName, kilocodeConfig);

                        newKiloCodeConfig.mcpServers[serverName] = kilocodeConfig;
                    } else if (this.isServerMetadata(config)) {
                        // Preserve existing metadata
                        newKiloCodeConfig.mcpServers[serverName] = config;
                    }
                }
            }

            // Merge with existing KiloCode configuration (preserve metadata for servers not in VSCode)
            if (kilocodeConfig.mcpServers) {
                for (const [serverName, config] of Object.entries(kilocodeConfig.mcpServers)) {
                    if (!newKiloCodeConfig.mcpServers[serverName] && this.isServerMetadata(config)) {
                        newKiloCodeConfig.mcpServers[serverName] = config;
                    }
                }
            }

            // Ensure .kilocode directory exists
            await fs.ensureDir(path.dirname(kilocodeConfigPath));

            // Write the new KiloCode configuration
            await fs.writeJson(kilocodeConfigPath, newKiloCodeConfig, { spaces: 2 });

            this.logger.success('Successfully generated .kilocode/mcp.json configuration');
        } catch (error) {
            this.logger.error('Failed to generate KiloCode configuration');
            throw error;
        }
    }

    async syncConfigurations(): Promise<void> {
        this.logger.info('Synchronizing .vscode/mcp.json and .kilocode/mcp.json');

        const vscodeConfigPath = path.join(process.cwd(), '.vscode', 'mcp.json');
        const kilocodeConfigPath = path.join(process.cwd(), '.kilocode', 'mcp.json');

        try {
            // Load both configurations
            const vscodeConfig = await this.loadConfig<MCPConfig>(vscodeConfigPath);
            const kilocodeConfig = await this.loadConfig<KiloCodeConfig>(kilocodeConfigPath);

            // Sync VSCode to KiloCode (generate missing KiloCode configs)
            if (vscodeConfig.mcpServers) {
                for (const [serverName, config] of Object.entries(vscodeConfig.mcpServers)) {
                    if (this.isMCPServerConfig(config) && !this.isKiloCodeServerConfig(kilocodeConfig.mcpServers[serverName])) {
                        const kilocodeServerConfig: KiloCodeServerConfig = {
                            command: config.command,
                            args: config.args,
                            env: {
                                ...config.env,
                                NODE_ENV: 'production',
                                KILOCODE_ENV: 'development',
                                KILOCODE_PROJECT_PATH: process.cwd()
                            }
                        };
                        this.addKiloCodeSpecificEnv(serverName, kilocodeServerConfig);
                        kilocodeConfig.mcpServers[serverName] = kilocodeServerConfig;
                    }
                }
            }

            // Sync KiloCode to VSCode (add missing servers from KiloCode metadata)
            if (kilocodeConfig.mcpServers) {
                for (const [serverName, config] of Object.entries(kilocodeConfig.mcpServers)) {
                    if (this.isServerMetadata(config) && !vscodeConfig.mcpServers[serverName]) {
                        // Convert metadata to basic VSCode config
                        const vscodeServerConfig: MCPServerConfig = {
                            command: 'npx',
                            args: ['-y', 'placeholder-package'],
                            env: {}
                        };
                        vscodeConfig.mcpServers[serverName] = vscodeServerConfig;
                    }
                }
            }

            // Write updated configurations
            await fs.writeJson(vscodeConfigPath, vscodeConfig, { spaces: 2 });
            await fs.writeJson(kilocodeConfigPath, kilocodeConfig, { spaces: 2 });

            this.logger.success('Successfully synchronized configurations');
        } catch (error) {
            this.logger.error('Failed to synchronize configurations');
            throw error;
        }
    }

    async updateConfigFile(configPath: string, serverName: string, config: MCPServerConfig | KiloCodeServerConfig): Promise<void> {
        try {
            const currentConfig = await this.loadConfig<any>(configPath);

            if (!currentConfig.mcpServers) {
                currentConfig.mcpServers = {};
            }

            currentConfig.mcpServers[serverName] = config;

            await fs.ensureDir(path.dirname(configPath));
            await fs.writeJson(configPath, currentConfig, { spaces: 2 });

            this.logger.info(`Updated ${path.basename(configPath)} with server: ${serverName}`);
        } catch (error) {
            this.logger.error(`Failed to update config file: ${configPath}`);
            throw error;
        }
    }

    async removeServerFromConfig(configPath: string, serverName: string): Promise<void> {
        try {
            const currentConfig = await this.loadConfig<any>(configPath);

            if (currentConfig.mcpServers && serverName in currentConfig.mcpServers) {
                delete currentConfig.mcpServers[serverName];
                await fs.writeJson(configPath, currentConfig, { spaces: 2 });
                this.logger.info(`Removed server ${serverName} from ${path.basename(configPath)}`);
            }
        } catch (error) {
            this.logger.error(`Failed to remove server from config: ${configPath}`);
            throw error;
        }
    }

    private async loadConfig<T>(configPath: string): Promise<T> {
        try {
            if (await fs.pathExists(configPath)) {
                return await fs.readJson(configPath);
            }
            return { mcpServers: {} } as T;
        } catch (error) {
            this.logger.warn(`Failed to load config ${configPath}, creating new one`);
            return { mcpServers: {} } as T;
        }
    }

    private isMCPServerConfig(config: any): config is MCPServerConfig {
        return config && typeof config === 'object' &&
            'command' in config && 'args' in config;
    }

    private isKiloCodeServerConfig(config: any): config is KiloCodeServerConfig {
        return config && typeof config === 'object' &&
            'command' in config && 'args' in config && 'env' in config &&
            'NODE_ENV' in config.env && 'KILOCODE_ENV' in config.env;
    }

    private isServerMetadata(config: any): config is ServerMetadata {
        return config && typeof config === 'object' &&
            ('description' in config || 'docsPath' in config);
    }

    private addKiloCodeSpecificEnv(serverName: string, config: KiloCodeServerConfig): void {
        // Add KiloCode-specific environment variables based on server type
        switch (serverName) {
            case 'postgres':
            case 'agent-memory':
            case 'testing-validation':
                config.env.KILOCODE_DB_CONFIG = config.env.DATABASE_URL || 'postgresql://localhost:5432/postgres';
                break;
            case 'rag-mcp-server':
                config.env.KILOCODE_RAG_CONFIG = config.env.CHROMA_URL || 'http://localhost:8000';
                break;
            case 'filesystem':
                config.env.KILOCODE_FS_PATH = process.cwd();
                break;
            case 'github':
                config.env.KILOCODE_GITHUB_CONFIG = config.env.GITHUB_PERSONAL_ACCESS_TOKEN || '';
                break;
        }

        // Add project-specific environment variables
        config.env.KILOCODE_PROJECT_NAME = require(path.join(process.cwd(), 'package.json')).name || 'unknown';
    }
}