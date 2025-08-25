#!/usr/bin/env node

import { Command } from 'commander';
import { MCPInstaller } from './mcp-installer';
import { ConfigGenerator } from './config-generator';
import { Logger } from './logger';
import chalk from 'chalk';

const program = new Command();
const logger = new Logger();

program
    .name('kilocode-mcp-install')
    .description('KiloCode-customized MCP server installer')
    .version('1.0.0');

program
    .command('install <server>')
    .description('Install an MCP server')
    .option('-f, --force', 'Force installation even if server already exists')
    .option('-g, --global', 'Install globally')
    .action(async (server: string, options: { force?: boolean; global?: boolean }) => {
        try {
            const installer = new MCPInstaller();
            await installer.installServer(server, options.force || false, options.global || false);
            logger.success(`Successfully installed server: ${server}`);
        } catch (error) {
            logger.error(`Failed to install server: ${server}`);
            logger.error(error instanceof Error ? error.message : String(error));
            process.exit(1);
        }
    });

program
    .command('remove <server>')
    .description('Remove an MCP server')
    .option('-g, --global', 'Remove from global configuration')
    .action(async (server: string, options: { global?: boolean }) => {
        try {
            const installer = new MCPInstaller();
            await installer.removeServer(server, options.global || false);
            logger.success(`Successfully removed server: ${server}`);
        } catch (error) {
            logger.error(`Failed to remove server: ${server}`);
            logger.error(error instanceof Error ? error.message : String(error));
            process.exit(1);
        }
    });

program
    .command('list')
    .description('List installed MCP servers')
    .option('-v, --verbose', 'Show detailed information')
    .action(async (options: { verbose?: boolean }) => {
        try {
            const installer = new MCPInstaller();
            const servers = await installer.listServers();

            if (servers.length === 0) {
                logger.info('No MCP servers installed');
                return;
            }

            logger.info('Installed MCP servers:');
            servers.forEach(server => {
                if (options.verbose) {
                    console.log(`  ${server.name}: ${server.description || 'No description'}`);
                    console.log(`    Command: ${server.command} ${server.args.join(' ')}`);
                    console.log(`    Environment: ${Object.keys(server.env || {}).length} variables`);
                } else {
                    console.log(`  ${server.name}`);
                }
            });
        } catch (error) {
            logger.error('Failed to list servers');
            logger.error(error instanceof Error ? error.message : String(error));
            process.exit(1);
        }
    });

program
    .command('generate-config')
    .description('Generate .kilocode/mcp.json configuration from existing .vscode/mcp.json')
    .action(async () => {
        try {
            const generator = new ConfigGenerator();
            await generator.generateKiloCodeConfig();
            logger.success('Successfully generated .kilocode/mcp.json configuration');
        } catch (error) {
            logger.error('Failed to generate configuration');
            logger.error(error instanceof Error ? error.message : String(error));
            process.exit(1);
        }
    });

program
    .command('sync')
    .description('Synchronize .vscode/mcp.json and .kilocode/mcp.json configurations')
    .action(async () => {
        try {
            const generator = new ConfigGenerator();
            await generator.syncConfigurations();
            logger.success('Successfully synchronized configurations');
        } catch (error) {
            logger.error('Failed to synchronize configurations');
            logger.error(error instanceof Error ? error.message : String(error));
            process.exit(1);
        }
    });

program.parse();