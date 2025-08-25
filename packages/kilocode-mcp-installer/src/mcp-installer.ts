import fs from 'fs-extra';
import path from 'path';
import { spawn } from 'child_process';
import { Logger } from './logger';
import { ConfigGenerator } from './config-generator';
import { MCPServerConfig, KiloCodeServerConfig } from './types';

export class MCPInstaller {
    private logger: Logger;
    private configGenerator: ConfigGenerator;
    private vscodeConfigPath: string;
    private kilocodeConfigPath: string;

    constructor() {
        this.logger = new Logger();
        this.configGenerator = new ConfigGenerator();
        this.vscodeConfigPath = path.join(process.cwd(), '.vscode', 'mcp.json');
        this.kilocodeConfigPath = path.join(process.cwd(), '.kilocode', 'mcp.json');
    }

    async installServer(serverName: string, force: boolean = false, global: boolean = false): Promise<void> {
        this.logger.info(`Installing MCP server: ${serverName}`);

        // Check if server already exists
        if (!force && await this.serverExists(serverName)) {
            throw new Error(`Server ${serverName} is already installed`);
        }

        // Get server configuration template
        const serverConfig = this.getServerConfig(serverName);
        if (!serverConfig) {
            throw new Error(`No configuration template found for server: ${serverName}`);
        }

        // Install the server package
        await this.installPackage(serverConfig.package, global);

        // Update both configuration files
        await this.updateVSCodeConfig(serverName, serverConfig.vscode);
        await this.updateKiloCodeConfig(serverName, serverConfig.kilocode);

        this.logger.success(`Server ${serverName} installed successfully`);
    }

    async removeServer(serverName: string, global: boolean = false): Promise<void> {
        this.logger.info(`Removing MCP server: ${serverName}`);

        // Remove from both configuration files
        await this.removeVSCodeConfig(serverName);
        await this.removeKiloCodeConfig(serverName);

        // Uninstall the package if not global
        if (!global) {
            await this.uninstallPackage(serverName);
        }

        this.logger.success(`Server ${serverName} removed successfully`);
    }

    async listServers(): Promise<Array<{ name: string; description?: string; command: string; args: string[]; env?: Record<string, string> }>> {
        const servers: Array<{ name: string; description?: string; command: string; args: string[]; env?: Record<string, string> }> = [];

        try {
            // Load VSCode configuration
            const vscodeConfig = await this.loadConfig(this.vscodeConfigPath);
            if (vscodeConfig.mcpServers) {
                for (const [name, config] of Object.entries(vscodeConfig.mcpServers)) {
                    const serverConfig = config as MCPServerConfig;
                    servers.push({
                        name,
                        command: serverConfig.command,
                        args: serverConfig.args || [],
                        env: serverConfig.env
                    });
                }
            }

            // Load KiloCode configuration for additional info
            const kilocodeConfig = await this.loadConfig(this.kilocodeConfigPath);
            if (kilocodeConfig.mcpServers) {
                for (const [name, config] of Object.entries(kilocodeConfig.mcpServers)) {
                    const existingServer = servers.find(s => s.name === name);
                    if (existingServer && config && typeof config === 'object' && 'description' in config) {
                        existingServer.description = (config as any).description;
                    }
                }
            }
        } catch (error) {
            this.logger.error('Failed to load server configurations');
            throw error;
        }

        return servers;
    }

    private async serverExists(serverName: string): Promise<boolean> {
        try {
            const vscodeConfig = await this.loadConfig(this.vscodeConfigPath);
            return !!(vscodeConfig.mcpServers && serverName in vscodeConfig.mcpServers);
        } catch {
            return false;
        }
    }

    private getServerConfig(serverName: string): { package: string; vscode: MCPServerConfig; kilocode: KiloCodeServerConfig } | null {
        const templates: Record<string, { package: string; vscode: MCPServerConfig; kilocode: KiloCodeServerConfig }> = {
            'filesystem': {
                package: '@modelcontextprotocol/server-filesystem',
                vscode: {
                    command: 'npx',
                    args: ['-y', '@modelcontextprotocol/server-filesystem', '.', '/tmp'],
                    env: {}
                },
                kilocode: {
                    command: 'npx',
                    args: ['-y', '@modelcontextprotocol/server-filesystem', '.'],
                    env: {
                        NODE_ENV: 'production',
                        KILOCODE_ENV: 'development',
                        KILOCODE_PROJECT_PATH: process.cwd()
                    }
                }
            },
            'github': {
                package: '@modelcontextprotocol/server-github',
                vscode: {
                    command: 'npx',
                    args: ['-y', '@modelcontextprotocol/server-github'],
                    env: { GITHUB_PERSONAL_ACCESS_TOKEN: '' }
                },
                kilocode: {
                    command: 'npx',
                    args: ['-y', '@modelcontextprotocol/server-github'],
                    env: {
                        NODE_ENV: 'production',
                        KILOCODE_ENV: 'development',
                        GITHUB_PERSONAL_ACCESS_TOKEN: '',
                        KILOCODE_PROJECT_PATH: process.cwd()
                    }
                }
            },
            'postgres': {
                package: '@modelcontextprotocol/server-postgres',
                vscode: {
                    command: 'npx',
                    args: ['-y', '@modelcontextprotocol/server-postgres', 'postgresql://postgres:DeeCee@2001@localhost:5432/postgres'],
                    env: {}
                },
                kilocode: {
                    command: 'npx',
                    args: ['-y', '@modelcontextprotocol/server-postgres', 'postgresql://postgres:DeeCee@2001@localhost:5432/postgres'],
                    env: {
                        NODE_ENV: 'production',
                        KILOCODE_ENV: 'development',
                        KILOCODE_PROJECT_PATH: process.cwd(),
                        KILOCODE_DB_CONFIG: 'postgresql://postgres:DeeCee@2001@localhost:5432/postgres'
                    }
                }
            },
            'agent-memory': {
                package: 'file:mcp_servers/agent-memory',
                vscode: {
                    command: 'node',
                    args: ['mcp_servers/agent-memory/index.js'],
                    env: {
                        DATABASE_URL: 'postgresql://postgres:DeeCee@2001@localhost:5432/postgres',
                        MEMORY_BANK_PATH: '../../memorybank'
                    }
                },
                kilocode: {
                    command: 'node',
                    args: ['mcp_servers/agent-memory/index.js'],
                    env: {
                        NODE_ENV: 'production',
                        KILOCODE_ENV: 'development',
                        KILOCODE_PROJECT_PATH: process.cwd(),
                        DATABASE_URL: 'postgresql://postgres:DeeCee@2001@localhost:5432/postgres',
                        MEMORY_BANK_PATH: '../../memorybank'
                    }
                }
            },
            'rag-mcp-server': {
                package: 'file:mcp_servers/rag-mcp-server',
                vscode: {
                    command: 'node',
                    args: ['mcp_servers/rag-mcp-server.js'],
                    env: { CHROMA_URL: 'http://localhost:8000' }
                },
                kilocode: {
                    command: 'node',
                    args: ['mcp_servers/rag-mcp-server.js'],
                    env: {
                        NODE_ENV: 'production',
                        KILOCODE_ENV: 'development',
                        KILOCODE_PROJECT_PATH: process.cwd(),
                        CHROMA_URL: 'http://localhost:8000'
                    }
                }
            },
            'fetch': {
                package: 'mcp-server-fetch',
                vscode: {
                    command: 'python',
                    args: ['-m', 'mcp_server_fetch'],
                    env: {}
                },
                kilocode: {
                    command: 'python',
                    args: ['-m', 'mcp_server_fetch'],
                    env: {
                        NODE_ENV: 'production',
                        KILOCODE_ENV: 'development',
                        KILOCODE_PROJECT_PATH: process.cwd()
                    }
                }
            }
        };

        return templates[serverName] || null;
    }

    private async installPackage(packageName: string, global: boolean = false): Promise<void> {
        return new Promise((resolve, reject) => {
            const npmPath = process.platform === 'win32' ? 'npm.cmd' : 'npm';
            const args = global ? ['install', '-g', packageName] : ['install', packageName];
            const child = spawn(npmPath, args, { stdio: 'pipe' });

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
                    this.logger.info(`Package installed: ${packageName}`);
                    resolve();
                } else {
                    reject(new Error(`Failed to install package ${packageName}: ${stderr}`));
                }
            });

            child.on('error', (error) => {
                reject(error);
            });
        });
    }

    private async uninstallPackage(packageName: string): Promise<void> {
        return new Promise((resolve, reject) => {
            const npmPath = process.platform === 'win32' ? 'npm.cmd' : 'npm';
            const child = spawn(npmPath, ['uninstall', packageName], { stdio: 'pipe' });

            let stderr = '';

            child.stderr?.on('data', (data) => {
                stderr += data.toString();
            });

            child.on('close', (code) => {
                if (code === 0) {
                    this.logger.info(`Package uninstalled: ${packageName}`);
                    resolve();
                } else {
                    reject(new Error(`Failed to uninstall package ${packageName}: ${stderr}`));
                }
            });

            child.on('error', (error) => {
                reject(error);
            });
        });
    }

    private async updateVSCodeConfig(serverName: string, config: MCPServerConfig): Promise<void> {
        await this.configGenerator.updateConfigFile(this.vscodeConfigPath, serverName, config);
    }

    private async updateKiloCodeConfig(serverName: string, config: KiloCodeServerConfig): Promise<void> {
        await this.configGenerator.updateConfigFile(this.kilocodeConfigPath, serverName, config);
    }

    private async removeVSCodeConfig(serverName: string): Promise<void> {
        await this.configGenerator.removeServerFromConfig(this.vscodeConfigPath, serverName);
    }

    private async removeKiloCodeConfig(serverName: string): Promise<void> {
        await this.configGenerator.removeServerFromConfig(this.kilocodeConfigPath, serverName);
    }

    private async loadConfig(configPath: string): Promise<any> {
        try {
            if (await fs.pathExists(configPath)) {
                const configContent = await fs.readJson(configPath);
                return configContent;
            }
            return { mcpServers: {} };
        } catch (error) {
            this.logger.warn(`Failed to load config ${configPath}, creating new one`);
            return { mcpServers: {} };
        }
    }
}