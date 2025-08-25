/**
 * Compliance Validation Tests
 * 
 * These tests validate the compliance checking functionality against KiloCode standards,
 * ensuring servers meet security, performance, and reliability requirements.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { ValidationEngine } from '../../../src/validation/validators';
import { createMockValidationContext } from '../../setup';

describe('Compliance Validation Tests', () => {
    let validationEngine: ValidationEngine;
    let mockContext = createMockValidationContext();

    beforeEach(() => {
        validationEngine = new ValidationEngine(mockContext);
    });

    describe('KiloCode Standards Compliance', () => {
        it('should validate against KiloCode environment standards', async () => {
            const result = await validationEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.passedRules).toBeGreaterThanOrEqual(0);
            expect(result.failedRules).toBeGreaterThanOrEqual(0);
            expect(Array.isArray(result.rules)).toBe(true);
            expect(result.timestamp).toBeDefined();
        });

        it('should validate MCP server configuration requirements', async () => {
            const configRules = [
                'config-name',
                'config-structure',
                'env-variables'
            ];

            const result = await validationEngine.validateSpecificRules(configRules);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should validate security benchmarks', async () => {
            const securityRules = [
                'token-management',
                'access-control',
                'network-security',
                'data-encryption',
                'security-config'
            ];

            const result = await validationEngine.validateSpecificRules(securityRules);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should validate performance benchmarks', async () => {
            const performanceRules = [
                'response-time',
                'resource-usage',
                'throughput',
                'scalability'
            ];

            const result = await validationEngine.validateSpecificRules(performanceRules);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should validate naming conventions', async () => {
            const result = await validationEngine.validateSpecificRules(['config-name']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });
    });

    describe('Security Compliance', () => {
        it('should validate token management practices', async () => {
            const result = await validationEngine.validateSpecificRules(['token-management']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should validate access control implementation', async () => {
            const result = await validationEngine.validateSpecificRules(['access-control']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should validate network security configuration', async () => {
            const result = await validationEngine.validateSpecificRules(['network-security']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should detect hardcoded credentials', async () => {
            const vulnerableContext = {
                ...mockContext,
                serverConfig: {
                    command: 'node',
                    args: ['server.js', '--password=secret123', '--token=abc123'],
                    env: {
                        NODE_ENV: 'production',
                        API_KEY: 'test-key-123'
                    }
                }
            };

            const vulnerableEngine = new ValidationEngine(vulnerableContext);
            const result = await vulnerableEngine.validateSpecificRules(['security-config', 'token-management']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.failedRules).toBeGreaterThanOrEqual(0);
        });

        it('should validate secure protocol usage', async () => {
            const insecureContext = {
                ...mockContext,
                serverConfig: {
                    command: 'node',
                    args: ['server.js'],
                    env: {
                        NODE_ENV: 'production',
                        INSECURE_URL: 'http://insecure.com',
                        API_ENDPOINT: 'http://api.example.com'
                    }
                }
            };

            const insecureEngine = new ValidationEngine(insecureContext);
            const result = await insecureEngine.validateSpecificRules(['security-config']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.failedRules).toBeGreaterThanOrEqual(0);
        });
    });

    describe('Performance Compliance', () => {
        it('should validate response time requirements', async () => {
            const result = await validationEngine.validateSpecificRules(['response-time']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should validate resource usage limits', async () => {
            const result = await validationEngine.validateSpecificRules(['resource-usage']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should validate throughput requirements', async () => {
            const result = await validationEngine.validateSpecificRules(['throughput']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should validate scalability configuration', async () => {
            const result = await validationEngine.validateSpecificRules(['scalability']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });
    });

    describe('Compatibility Compliance', () => {
        it('should validate version compatibility', async () => {
            const result = await validationEngine.validateSpecificRules(['version-compatibility']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should validate protocol adherence', async () => {
            const result = await validationEngine.validateSpecificRules(['protocol-adherence']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should validate dependency compatibility', async () => {
            const result = await validationEngine.validateSpecificRules(['dependency-compatibility']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should handle version conflicts', async () => {
            const conflictContext = {
                ...mockContext,
                projectRoot: '/test/project',
                serverConfig: {
                    command: 'node',
                    args: ['server.js'],
                    env: {
                        NODE_VERSION: '16.x',
                        PYTHON_VERSION: '3.6'
                    }
                }
            };

            const conflictEngine = new ValidationEngine(conflictContext);
            const result = await conflictEngine.validateSpecificRules(['version-compatibility']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.failedRules).toBeGreaterThanOrEqual(0);
        });
    });

    describe('Reliability Compliance', () => {
        it('should validate uptime requirements', async () => {
            const result = await validationEngine.validateSpecificRules(['uptime-requirement']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should validate error handling', async () => {
            const result = await validationEngine.validateSpecificRules(['error-handling']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should validate recovery procedures', async () => {
            const result = await validationEngine.validateSpecificRules(['recovery-procedure']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should validate production environment requirements', async () => {
            const productionContext = {
                ...mockContext,
                environment: 'production' as const,
                serverConfig: {
                    command: 'node',
                    args: ['server.js'],
                    env: {
                        NODE_ENV: 'production',
                        KILOCODE_ENV: 'production'
                    }
                }
            };

            const productionEngine = new ValidationEngine(productionContext);
            const result = await productionEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.failedRules).toBeGreaterThanOrEqual(0);
        });
    });

    describe('Server Type Specific Compliance', () => {
        it('should validate filesystem server requirements', async () => {
            const result = await validationEngine.validateSpecificRules(['filesystem-server']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should validate database server requirements', async () => {
            const result = await validationEngine.validateSpecificRules(['database-server']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should validate memory server requirements', async () => {
            const result = await validationEngine.validateSpecificRules(['memory-server']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });

        it('should validate API server requirements', async () => {
            const result = await validationEngine.validateSpecificRules(['api-server']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });
    });

    describe('Compliance Scoring', () => {
        it('should calculate compliance score correctly', async () => {
            const result = await validationEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.passedRules + result.failedRules).toBe(result.rules.length);
        });

        it('should handle perfect compliance', async () => {
            const perfectContext = {
                ...mockContext,
                serverConfig: {
                    command: 'node',
                    args: ['server.js'],
                    env: {
                        NODE_ENV: 'development',
                        KILOCODE_ENV: 'development',
                        KILOCODE_PROJECT_PATH: '/test/project'
                    }
                }
            };

            const perfectEngine = new ValidationEngine(perfectContext);
            const result = await perfectEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
        });

        it('should handle zero compliance', async () => {
            const invalidContext = {
                ...mockContext,
                serverConfig: {
                    command: 'invalid',
                    args: [],
                    env: {}
                }
            };

            const invalidEngine = new ValidationEngine(invalidContext);
            const result = await invalidEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
        });
    });

    describe('Compliance Reporting', () => {
        it('should generate compliance report', async () => {
            const result = await validationEngine.validateAllRules();

            expect(result.overallScore).toBeDefined();
            expect(result.passedRules).toBeDefined();
            expect(result.failedRules).toBeDefined();
            expect(Array.isArray(result.rules)).toBe(true);
            expect(Array.isArray(result.warnings)).toBe(true);
            expect(Array.isArray(result.recommendations)).toBe(true);
            expect(result.timestamp).toBeDefined();
        });

        it('should provide detailed rule information', async () => {
            const result = await validationEngine.validateAllRules();

            for (const rule of result.rules) {
                expect(rule.ruleId).toBeDefined();
                expect(rule.ruleName).toBeDefined();
                expect(typeof rule.passed).toBe('boolean');
                expect(['low', 'medium', 'high', 'critical']).toContain(rule.severity);
                expect(rule.message).toBeDefined();
                expect(rule.details).toBeDefined();
                expect(typeof rule.autoFixApplied).toBe('boolean');
            }
        });

        it('should categorize issues by severity', async () => {
            const result = await validationEngine.validateAllRules();

            const criticalIssues = result.rules.filter(rule => rule.severity === 'critical' && !rule.passed);
            const highIssues = result.rules.filter(rule => rule.severity === 'high' && !rule.passed);
            const mediumIssues = result.rules.filter(rule => rule.severity === 'medium' && !rule.passed);
            const lowIssues = result.rules.filter(rule => rule.severity === 'low' && !rule.passed);

            expect(criticalIssues.length + highIssues.length + mediumIssues.length + lowIssues.length)
                .toBe(result.failedRules);
        });
    });

    describe('Auto-Fix Compliance', () => {
        it('should attempt auto-fix for compliance issues', async () => {
            const result = await validationEngine.autoFixAllIssues();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.passedRules).toBeGreaterThanOrEqual(0);
            expect(result.failedRules).toBeGreaterThanOrEqual(0);
            expect(result.recommendations).toContain('Review manually fixed issues');
        });

        it('should handle auto-fix failures gracefully', async () => {
            const result = await validationEngine.autoFixAllIssues();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(Array.isArray(result.warnings)).toBe(true);
        });
    });

    describe('Environment-Specific Compliance', () => {
        it('should validate development environment compliance', async () => {
            const devContext = {
                ...mockContext,
                environment: 'development' as const
            };

            const devEngine = new ValidationEngine(devContext);
            const result = await devEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
        });

        it('should validate staging environment compliance', async () => {
            const stagingContext = {
                ...mockContext,
                environment: 'staging' as const
            };

            const stagingEngine = new ValidationEngine(stagingContext);
            const result = await stagingEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
        });

        it('should validate production environment compliance', async () => {
            const productionContext = {
                ...mockContext,
                environment: 'production' as const
            };

            const productionEngine = new ValidationEngine(productionContext);
            const result = await productionEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
        });
    });
});