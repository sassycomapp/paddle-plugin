/**
 * Test Setup Utilities
 * 
 * This file provides common setup utilities for testing the KiloCode MCP Compliance Server.
 */

import { Logger } from '../../src/logger';
import { ValidationContext } from '../../src/validation/validators';
import { ServerConfig } from '../../src/types';

export function createMockLogger(): Logger {
    return {
        debug: vi.fn(),
        info: vi.fn(),
        warn: vi.fn(),
        error: vi.fn(),
        child: vi.fn(() => createMockLogger())
    } as unknown as Logger;
}

export function createMockValidationContext(): ValidationContext {
    return {
        serverName: 'test-server',
        serverConfig: {
            command: 'node',
            args: ['server.js'],
            env: {
                NODE_ENV: 'development',
                KILOCODE_ENV: 'development',
                KILOCODE_PROJECT_PATH: '/test/project'
            },
            description: 'Test server for validation'
        } as ServerConfig,
        environment: 'development',
        projectRoot: '/test/project',
        kilocodeDir: '/test/project/.kilocode',
        logger: createMockLogger()
    };
}

export function createMockServerConfig(overrides: Partial<ServerConfig> = {}): ServerConfig {
    return {
        command: 'node',
        args: ['server.js'],
        env: {
            NODE_ENV: 'development',
            KILOCODE_ENV: 'development',
            KILOCODE_PROJECT_PATH: '/test/project',
            ...overrides.env
        },
        description: 'Test server',
        ...overrides
    };
}

export function createMockValidationResult(overrides: Partial<ValidationResult> = {}): ValidationResult {
    return {
        valid: true,
        errors: [],
        warnings: [],
        suggestions: [],
        recommendations: [],
        ...overrides
    };
}

export function waitFor(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}

export function createTestServerConfig() {
    return {
        name: 'test-server',
        command: 'node',
        args: ['test-server.js'],
        env: {
            NODE_ENV: 'test',
            KILOCODE_ENV: 'test',
            KILOCODE_PROJECT_PATH: '/test/project',
            TEST_MODE: 'true'
        },
        description: 'Test server for integration testing'
    };
}

export function createTestMCPConfig() {
    return {
        mcpServers: {
            'test-server': {
                command: 'node',
                args: ['test-server.js'],
                env: {
                    NODE_ENV: 'test',
                    KILOCODE_ENV: 'test',
                    KILOCODE_PROJECT_PATH: '/test/project'
                },
                description: 'Test MCP server'
            }
        }
    };
}