/**
 * Unit Tests for Validation Engine
 * 
 * These tests validate the core functionality of the validation engine
 * including rule validation, compliance checking, and result handling.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ValidationEngine } from '../../src/validation/validators';
import { ValidationResult, ComplianceReport, ServerConfig } from '../../src/types';
import { createMockValidationContext } from '../setup';

describe('ValidationEngine', () => {
    let validationEngine: ValidationEngine;
    let mockContext = createMockValidationContext();

    beforeEach(() => {
        validationEngine = new ValidationEngine(mockContext);
    });

    describe('Basic Validation', () => {
        it('should validate server configuration successfully', async () => {
            const result = await validationEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThan(0);
            expect(result.passedRules).toBeGreaterThanOrEqual(0);
            expect(result.failedRules).toBeGreaterThanOrEqual(0);
            expect(result.rules).toBeDefined();
            expect(result.timestamp).toBeDefined();
        });

        it('should handle validation with warnings', async () => {
            const result = await validationEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(Array.isArray(result.warnings)).toBe(true);
            expect(Array.isArray(result.recommendations)).toBe(true);
        });
    });

    describe('Specific Rule Validation', () => {
        it('should validate specific rules', async () => {
            const result = await validationEngine.validateSpecificRules(['config-name', 'config-structure']);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.passedRules).toBeGreaterThanOrEqual(0);
            expect(result.failedRules).toBeGreaterThanOrEqual(0);
        });

        it('should handle non-existent rule', async () => {
            const result = await validationEngine.validateSpecificRules(['non-existent-rule']);

            expect(result.overallScore).toBe(0);
            expect(result.passedRules).toBe(0);
            expect(result.failedRules).toBe(0);
        });

        it('should validate multiple specific rules', async () => {
            const result = await validationEngine.validateSpecificRules([
                'config-name',
                'config-structure',
                'env-variables',
                'security-config'
            ]);

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.rules.length).toBeGreaterThan(0);
        });
    });

    describe('Auto-Fix Functionality', () => {
        it('should execute auto-fix for rules that support it', async () => {
            const result = await validationEngine.autoFixAllIssues();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.passedRules).toBeGreaterThanOrEqual(0);
            expect(result.failedRules).toBeGreaterThanOrEqual(0);
            expect(result.recommendations).toContain('Review manually fixed issues');
        });

        it('should handle rules without auto-fix capability', async () => {
            const result = await validationEngine.autoFixAllIssues();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
        });
    });

    describe('Rule Validation Results', () => {
        it('should provide detailed rule results', async () => {
            const result = await validationEngine.validateAllRules();

            expect(Array.isArray(result.rules)).toBe(true);

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

        it('should categorize rules by severity', async () => {
            const result = await validationEngine.validateAllRules();

            const criticalRules = result.rules.filter(rule => rule.severity === 'critical');
            const highRules = result.rules.filter(rule => rule.severity === 'high');
            const mediumRules = result.rules.filter(rule => rule.severity === 'medium');
            const lowRules = result.rules.filter(rule => rule.severity === 'low');

            expect(criticalRules.length + highRules.length + mediumRules.length + lowRules.length)
                .toBe(result.rules.length);
        });

        it('should track rule execution correctly', async () => {
            const result = await validationEngine.validateAllRules();

            const totalRules = result.passedRules + result.failedRules;
            expect(totalRules).toBe(result.rules.length);
        });
    });

    describe('Error Handling', () => {
        it('should handle rule execution errors gracefully', async () => {
            const result = await validationEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(Array.isArray(result.warnings)).toBe(true);
        });

        it('should handle empty rule list', async () => {
            const result = await validationEngine.validateSpecificRules([]);

            expect(result.overallScore).toBe(0);
            expect(result.passedRules).toBe(0);
            expect(result.failedRules).toBe(0);
            expect(result.rules).toHaveLength(0);
        });
    });

    describe('Validation Context', () => {
        it('should use validation context correctly', async () => {
            const customContext = {
                ...mockContext,
                serverName: 'custom-server',
                environment: 'production' as const
            };

            const customEngine = new ValidationEngine(customContext);
            const result = await customEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
        });

        it('should handle different environments', async () => {
            const developmentContext = {
                ...mockContext,
                environment: 'development' as const
            };

            const developmentEngine = new ValidationEngine(developmentContext);
            const result = await developmentEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
        });
    });

    describe('Performance and Efficiency', () => {
        it('should execute validation in reasonable time', async () => {
            const startTime = Date.now();

            const result = await validationEngine.validateAllRules();

            const duration = Date.now() - startTime;
            expect(duration).toBeLessThan(10000); // Should complete in under 10 seconds
        });

        it('should handle concurrent validation requests', async () => {
            const startTime = Date.now();

            const [result1, result2] = await Promise.all([
                validationEngine.validateAllRules(),
                validationEngine.validateSpecificRules(['config-name', 'config-structure'])
            ]);

            const duration = Date.now() - startTime;
            expect(duration).toBeLessThan(15000); // Should complete in under 15 seconds
            expect(result1.overallScore).toBeGreaterThanOrEqual(0);
            expect(result2.overallScore).toBeGreaterThanOrEqual(0);
        });
    });

    describe('Logging and Monitoring', () => {
        it('should log validation activities', async () => {
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
    });

    describe('Validation Report Generation', () => {
        it('should generate comprehensive validation report', async () => {
            const result = await validationEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
            expect(result.passedRules).toBeGreaterThanOrEqual(0);
            expect(result.failedRules).toBeGreaterThanOrEqual(0);
            expect(Array.isArray(result.rules)).toBe(true);
            expect(Array.isArray(result.warnings)).toBe(true);
            expect(Array.isArray(result.recommendations)).toBe(true);
            expect(result.timestamp).toBeDefined();
        });

        it('should provide rule-level details', async () => {
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
    });

    describe('Edge Cases', () => {
        it('should handle null or undefined context', () => {
            expect(() => {
                new ValidationEngine(null as any);
            }).toThrow();
        });

        it('should handle missing required fields in context', () => {
            const incompleteContext = {
                serverName: 'test',
                // Missing other required fields
            };

            expect(() => {
                new ValidationEngine(incompleteContext as any);
            }).toThrow();
        });

        it('should handle very long server names', async () => {
            const longNameContext = {
                ...mockContext,
                serverName: 'a'.repeat(100) // Very long name
            };

            const longNameEngine = new ValidationEngine(longNameContext);
            const result = await longNameEngine.validateAllRules();

            expect(result.overallScore).toBeGreaterThanOrEqual(0);
            expect(result.overallScore).toBeLessThanOrEqual(100);
        });
    });

    describe('Validation Consistency', () => {
        it('should produce consistent results', async () => {
            const result1 = await validationEngine.validateAllRules();
            const result2 = await validationEngine.validateAllRules();

            expect(result1.overallScore).toBe(result2.overallScore);
            expect(result1.passedRules).toBe(result2.passedRules);
            expect(result1.failedRules).toBe(result2.failedRules);
        });

        it('should maintain rule order consistency', async () => {
            const result1 = await validationEngine.validateAllRules();
            const result2 = await validationEngine.validateAllRules();

            const ruleIds1 = result1.rules.map(rule => rule.ruleId);
            const ruleIds2 = result2.rules.map(rule => rule.ruleId);

            expect(ruleIds1).toEqual(ruleIds2);
        });
    });
});