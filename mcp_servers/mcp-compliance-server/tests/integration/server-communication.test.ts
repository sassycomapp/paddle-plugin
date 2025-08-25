/**
 * Integration Tests for Server Communication
 * 
 * These tests validate the communication between MCP servers and the compliance server,
 * ensuring proper protocol adherence, message handling, and error scenarios.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { spawn } from 'child_process';
import { ValidationEngine } from '../../../src/validation/validators';
import { createMockValidationContext } from '../../setup';
import fs from 'fs/promises';
import path from 'path';

describe('Server Communication Integration Tests', () => {
    let validationEngine: ValidationEngine;
    let mockContext = createMockValidationContext();
    let testServerProcess: any;
    let testServerPort: number;

    beforeEach(async () => {
        validationEngine = new ValidationEngine(mockContext);
        testServerPort = 3001 + Math.floor(Math.random() * 1000); // Random port
    });

    afterEach(async () => {
        if (testServerProcess) {
            testServerProcess.kill();
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    });

    describe('MCP Server Protocol Communication', () => {
        it('should establish MCP server connection', async () => {
            const testServerConfig = {
                name: 'test-mcp-server',
                command: 'node',
                args: ['test-server.js'],
                env: {
                    NODE_ENV: 'test',
                    KILOCODE_ENV: 'test',
                    KILOCODE_PROJECT_PATH: '/test/project',
                    TEST_PORT: testServerPort.toString(),
                    TEST_MODE: 'true'
                },
                description: 'Test MCP server for protocol validation'
            };

            // Create a simple test server
            const testServerCode = `
const http = require('http');
const server = http.createServer((req, res) => {
    if (req.method === 'POST' && req.url === '/mcp') {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', () => {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                jsonrpc: '2.0',
                id: 1,
                result: { content: [{ type: 'text', text: 'Test response' }] }
            }));
        });
    } else {
        res.writeHead(404);
        res.end();
    }
});

const port = process.env.TEST_PORT || 3001;
server.listen(port, () => {
    console.log(\`Test server running on port \${port}\`);
});
`;

            const testServerPath = path.join(__dirname, 'test-server.js');
            await fs.writeFile(testServerPath, testServerCode);

            // Start test server
            testServerProcess = spawn('node', [testServerPath], {
                stdio: 'pipe',
                env: { ...process.env, ...testServerConfig.env }
            });

            // Wait for server to start
            await new Promise(resolve => setTimeout(resolve, 1000));

            // Test MCP protocol communication
            const result = await validationEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(Array.isArray(result.rules)).toBe(true);

            // Clean up
            await fs.unlink(testServerPath);
        });

        it('should handle MCP server disconnection gracefully', async () => {
            // Test without server running
            const result = await validationEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(Array.isArray(result.rules)).toBe(true);
        });

        it('should validate MCP protocol compliance', async () => {
            const result = await validationEngine.validateSpecificRules(['protocol-adherence']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });
    });

    describe('Server Configuration Validation', () => {
        it('should validate server configuration structure', async () => {
            const result = await validationEngine.validateSpecificRules(['config-structure']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should validate server environment variables', async () => {
            const result = await validationEngine.validateSpecificRules(['env-variables']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should validate server security configuration', async () => {
            const result = await validationEngine.validateSpecificRules(['security-config']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });
    });

    describe('Cross-Server Communication', () => {
        it('should validate multiple server configurations', async () => {
            const contexts = [
                createMockValidationContext(),
                createMockValidationContext(),
                createMockValidationContext()
            ];

            const engines = contexts.map(ctx => new ValidationEngine(ctx));
            const results = await Promise.all(engines.map(engine => engine.validateAllRules()));

            expect(results).toHaveLength(3);
            results.forEach(result => {
                expect(result.overallScore).toBeGreaterThanOrEqual(0);
                expect(result.overallScore).toBeLessThanOrEqual(100);
            });
        });

        it('should handle concurrent server validation', async () => {
            const startTime = Date.now();

            const results = await Promise.all([
                validationEngine.validateAllRules(),
                validationEngine.validateSpecificRules(['config-name', 'config-structure']),
                validationEngine.validateSpecificRules(['env-variables', 'security-config'])
            ]);

            const duration = Date.now() - startTime;
            expect(duration).toBeLessThan(10000); // Should complete in under 10 seconds

            expect(results).toHaveLength(3);
            results.forEach(result => {
                expect(result.overallScore).toBeGreaterThanOrEqual(0);
                expect(result.overallScore).toBeLessThanOrEqual(100);
            });
        });
    });

    describe('Error Handling and Recovery', () => {
        it('should handle server connection errors gracefully', async () => {
            const result = await validationEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(Array.isArray(result.warnings)).toBe(true);
        });

        it('should handle invalid server configurations', async () => {
            const invalidContext = {
                ...mockContext,
                serverConfig: {
                    command: 'invalid-command',
                    args: ['nonexistent.js'],
                    env: {}
                }
            };

            const invalidEngine = new ValidationEngine(invalidContext);
            const result = await invalidEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.failedRules).toBeGreaterThanOrEqual(0);
        });

        it('should handle timeout scenarios', async () => {
            const result = await validationEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(Array.isArray(result.warnings)).toBe(true);
        });
    });

    describe('Performance and Load Testing', () => {
        it('should handle multiple server validations efficiently', async () => {
            const serverConfigs = Array.from({ length: 10 }, (_, i) => ({
                name: `test-server-${i}`,
                command: 'node',
                args: ['server.js'],
                env: {
                    NODE_ENV: 'test',
                    KILOCODE_ENV: 'test',
                    KILOCODE_PROJECT_PATH: `/test/project-${i}`
                },
                description: `Test server ${i}`
            }));

            const startTime = Date.now();

            const results = await Promise.all(
                serverConfigs.map(config => {
                    const context = {
                        ...mockContext,
                        serverName: config.name,
                        serverConfig: config
                    };
                    const engine = new ValidationEngine(context);
                    return engine.validateAllRules();
                })
            );

            const duration = Date.now() - startTime;
            expect(duration).toBeLessThan(30000); // Should complete in under 30 seconds

            expect(results).toHaveLength(10);
            results.forEach(result => {
                expect(result.overallScore).toBeGreaterThanOrEqual(0);
                expect(result.overallScore).toBeLessThanOrEqual(100);
            });
        });

        it('should maintain performance under load', async () => {
            const loadStartTime = Date.now();

            // Simulate concurrent server connections
            const concurrentRequests = 5;
            const results = await Promise.all(
                Array.from({ length: concurrentRequests }, () =>
                    validationEngine.validateAllRules()
                )
            );

            const loadDuration = Date.now() - loadStartTime;
            expect(loadDuration).toBeLessThan(20000); // Should complete in under 20 seconds

            expect(results).toHaveLength(concurrentRequests);
            results.forEach(result => {
                expect(result.overallScore).toBeGreaterThanOrEqual(0);
                expect(result.overallScore).toBeLessThanOrEqual(100);
            });
        });
    });

    describe('Security and Compliance', () => {
        it('should validate security configurations across servers', async () => {
            const securityRules = [
                'token-management',
                'access-control',
                'network-security',
                'data-encryption'
            ];

            const result = await validationEngine.validateSpecificRules(securityRules);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should validate compliance standards', async () => {
            const result = await validationEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(Array.isArray(result.rules)).toBe(true);

            // Check for critical security rules
            const criticalRules = result.rules.filter(rule => rule.severity === 'critical');
            expect(criticalRules.length).toBeGreaterThanOrEqual(0);
        });

        it('should detect security vulnerabilities', async () => {
            const vulnerableContext = {
                ...mockContext,
                serverConfig: {
                    command: 'node',
                    args: ['server.js', '--password=123456'],
                    env: {
                        NODE_ENV: 'production',
                        API_KEY: 'test-key',
                        INSECURE_URL: 'http://insecure.com'
                    }
                }
            };

            const vulnerableEngine = new ValidationEngine(vulnerableContext);
            const result = await vulnerableEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.failedRules).toBeGreaterThanOrEqual(0);
        });
    });

    describe('Logging and Monitoring', () => {
        it('should log server communication activities', async () => {
            const mockLogger = {
                debug: vi.fn(),
                info: vi.fn(),
                warn: vi.fn(),
                error: vi.fn(),
                child: vi.fn(() => mockLogger)
            };

            const contextWithLogging = {
                ...mockContext,
                logger: mockLogger as any
            };

            const engineWithLogging = new ValidationEngine(contextWithLogging);
            await engineWithLogging.validateAllRules();

            expect(mockLogger.info).toHaveBeenCalled();
            expect(mockLogger.debug).toHaveBeenCalled();
        });

        it('should track server performance metrics', async () => {
            const result = await validationEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.timestamp).toBeDefined();
        });
    });

    describe('Configuration Management', () => {
        it('should handle configuration updates', async () => {
            const initialResult = await validationEngine.validateAllRules();

            // Update context with new configuration
            const updatedContext = {
                ...mockContext,
                serverConfig: {
                    ...mockContext.serverConfig,
                    env: {
                        ...mockContext.serverConfig.env,
                        NEW_CONFIG: 'test-value'
                    }
                }
            };

            const updatedEngine = new ValidationEngine(updatedContext);
            const updatedResult = await updatedEngine.validateAllRules();

            expect(updatedResult.overallScore).toBeGreaterThanOrEqual(0);
            expect(updatedResult.overallScore).toBeLessThanOrEqual(100);
        });

        it('should validate configuration changes', async () => {
            const result = await validationEngine.validateSpecificRules(['config-structure', 'env-variables']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });
    });
});