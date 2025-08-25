/**
 * KiloCode MCP Server Validation Scripts
 * 
 * This module provides comprehensive validation scripts for MCP servers
 * to ensure compliance with KiloCode standards, security requirements,
 * and performance benchmarks.
 */

import { Logger } from '../logger';
import { ValidationResult, ComplianceReport, ServerConfig, MCPServerConfig } from '../types';

// Extended ValidationResult type for validation rules
export interface ExtendedValidationResult extends ValidationResult {
    ruleId?: string;
    ruleName?: string;
    severity?: string;
    message?: string;
    details?: Record<string, any>;
    autoFixApplied?: boolean;
    recommendations?: string[];
}
import fs from 'fs/promises';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export interface ValidationContext {
    serverName: string;
    serverConfig: ServerConfig;
    environment: 'development' | 'staging' | 'production';
    projectRoot: string;
    kilocodeDir: string;
    logger: Logger;
}

export interface ValidationRule {
    id: string;
    name: string;
    description: string;
    severity: 'critical' | 'high' | 'medium' | 'low';
    category: 'security' | 'performance' | 'configuration' | 'compatibility' | 'reliability';
    validate: (context: ValidationContext) => Promise<ValidationResult>;
    autoFix?: (context: ValidationContext) => Promise<ValidationResult>;
}

export class ValidationEngine {
    private logger: Logger;
    private rules: Map<string, ValidationRule> = new Map();
    private context: ValidationContext;

    constructor(context: ValidationContext) {
        this.logger = context.logger;
        this.context = context;
        this.initializeRules();
    }

    private initializeRules(): void {
        // Configuration Validation Rules
        this.addRule(new ConfigurationNameRule());
        this.addRule(new ConfigurationStructureRule());
        this.addRule(new EnvironmentVariablesRule());
        this.addRule(new SecurityConfigurationRule());

        // Security Validation Rules
        this.addRule(new TokenManagementRule());
        this.addRule(new AccessControlRule());
        this.addRule(new NetworkSecurityRule());
        this.addRule(new DataEncryptionRule());

        // Performance Validation Rules
        this.addRule(new ResponseTimeRule());
        this.addRule(new ResourceUsageRule());
        this.addRule(new ThroughputRule());
        this.addRule(new ScalabilityRule());

        // Compatibility Validation Rules
        this.addRule(new VersionCompatibilityRule());
        this.addRule(new ProtocolAdherenceRule());
        this.addRule(new DependencyCompatibilityRule());

        // Reliability Validation Rules
        this.addRule(new UptimeRequirementRule());
        this.addRule(new ErrorHandlingRule());
        this.addRule(new RecoveryProcedureRule());

        // Server Type Specific Rules
        this.addRule(new FilesystemServerRule());
        this.addRule(new DatabaseServerRule());
        this.addRule(new MemoryServerRule());
        this.addRule(new APIServerRule());
    }

    private addRule(rule: ValidationRule): void {
        this.rules.set(rule.id, rule);
        this.logger.debug(`Added validation rule: ${rule.id}`);
    }

    async validateAllRules(): Promise<ComplianceReport> {
        const startTime = Date.now();
        const results: ValidationResult[] = [];
        const passedRules: string[] = [];
        const failedRules: string[] = [];
        const warnings: string[] = [];
        const recommendations: string[] = [];

        this.logger.info(`Starting validation for server: ${this.context.serverName}`);

        for (const [ruleId, rule] of this.rules) {
            try {
                const result = await rule.validate(this.context);
                const extendedResult = result as ExtendedValidationResult;
                results.push(extendedResult);

                if (extendedResult.valid) {
                    passedRules.push(ruleId);
                } else {
                    failedRules.push(ruleId);
                    warnings.push(...extendedResult.warnings);
                    recommendations.push(...(extendedResult.recommendations || []));
                }

                // Log rule execution
                this.logger.debug(`Rule ${ruleId} execution: ${result.valid ? 'PASSED' : 'FAILED'}`, {
                    ruleId,
                    duration: Date.now() - startTime,
                    errors: result.errors.length,
                    warnings: result.warnings.length
                });

            } catch (error) {
                this.logger.error(`Error executing validation rule ${ruleId}`, error as Error);
                failedRules.push(ruleId);
                warnings.push(`Rule ${ruleId} failed with error: ${error instanceof Error ? error.message : String(error)}`);
            }
        }

        // Calculate overall compliance score
        const totalRules = this.rules.size;
        const complianceScore = Math.round((passedRules.length / totalRules) * 100);

        const report: ComplianceReport = {
            overallScore: complianceScore,
            passedRules: passedRules.length,
            failedRules: failedRules.length,
            rules: results.map(result => ({
                ruleId: result.ruleId || 'unknown',
                ruleName: result.ruleName || 'Unknown Rule',
                passed: result.valid,
                severity: (result.severity as 'low' | 'medium' | 'high' | 'critical') || 'medium',
                message: result.message || 'Validation completed',
                details: result.details || {},
                autoFixApplied: result.autoFixApplied || false
            })),
            warnings,
            recommendations,
            timestamp: new Date().toISOString()
        };

        this.logger.info(`Validation completed for server: ${this.context.serverName}`, {
            totalRules,
            passedRules: passedRules.length,
            failedRules: failedRules.length,
            complianceScore,
            duration: Date.now() - startTime
        });

        return report;
    }

    async validateSpecificRules(ruleIds: string[]): Promise<ComplianceReport> {
        const results: ValidationResult[] = [];
        const passedRules: string[] = [];
        const failedRules: string[] = [];
        const warnings: string[] = [];
        const recommendations: string[] = [];

        this.logger.info(`Starting specific validation for server: ${this.context.serverName}`, { ruleIds });

        for (const ruleId of ruleIds) {
            const rule = this.rules.get(ruleId);
            if (!rule) {
                this.logger.warn(`Validation rule not found: ${ruleId}`);
                warnings.push(`Rule ${ruleId} not found`);
                continue;
            }

            try {
                const result = await rule.validate(this.context);
                const extendedResult = result as ExtendedValidationResult;
                results.push(extendedResult);

                if (extendedResult.valid) {
                    passedRules.push(ruleId);
                } else {
                    failedRules.push(ruleId);
                    warnings.push(...extendedResult.warnings);
                    recommendations.push(...(extendedResult.recommendations || []));
                }

            } catch (error) {
                this.logger.error(`Error executing validation rule ${ruleId}`, error as Error);
                failedRules.push(ruleId);
                warnings.push(`Rule ${ruleId} failed with error: ${error instanceof Error ? error.message : String(error)}`);
            }
        }

        const totalRules = ruleIds.length;
        const complianceScore = Math.round((passedRules.length / totalRules) * 100);

        const report: ComplianceReport = {
            overallScore: complianceScore,
            passedRules: passedRules.length,
            failedRules: failedRules.length,
            rules: results.map(result => ({
                ruleId: result.ruleId || 'unknown',
                ruleName: result.ruleName || 'Unknown Rule',
                passed: result.valid,
                severity: (result.severity as 'low' | 'medium' | 'high' | 'critical') || 'medium',
                message: result.message || 'Validation completed',
                details: result.details || {},
                autoFixApplied: result.autoFixApplied || false
            })),
            warnings,
            recommendations,
            timestamp: new Date().toISOString()
        };

        return report;
    }

    async autoFixAllIssues(): Promise<ComplianceReport> {
        const startTime = Date.now();
        const results: ValidationResult[] = [];
        const fixedRules: string[] = [];
        const failedRules: string[] = [];
        const warnings: string[] = [];

        this.logger.info(`Starting auto-fix for server: ${this.context.serverName}`);

        for (const [ruleId, rule] of this.rules) {
            if (!rule.autoFix) {
                continue; // Skip rules without auto-fix capability
            }

            try {
                const result = await rule.autoFix(this.context);
                const extendedResult = result as ExtendedValidationResult;
                results.push(extendedResult);

                if (extendedResult.valid) {
                    fixedRules.push(ruleId);
                } else {
                    failedRules.push(ruleId);
                    warnings.push(...extendedResult.warnings);
                }

                this.logger.debug(`Auto-fix for rule ${ruleId}: ${result.valid ? 'SUCCESS' : 'FAILED'}`);

            } catch (error) {
                this.logger.error(`Error during auto-fix for rule ${ruleId}`, error as Error);
                failedRules.push(ruleId);
                warnings.push(`Auto-fix for rule ${ruleId} failed: ${error instanceof Error ? error.message : String(error)}`);
            }
        }

        const totalRules = fixedRules.length + failedRules.length;
        const fixSuccessRate = Math.round((fixedRules.length / totalRules) * 100);

        const report: ComplianceReport = {
            overallScore: fixSuccessRate,
            passedRules: fixedRules.length,
            failedRules: failedRules.length,
            rules: results.map(result => ({
                ruleId: result.ruleId || 'unknown',
                ruleName: result.ruleName || 'Unknown Rule',
                passed: result.valid,
                severity: (result.severity as 'low' | 'medium' | 'high' | 'critical') || 'medium',
                message: result.message || 'Auto-fix completed',
                details: result.details || {},
                autoFixApplied: result.autoFixApplied || false
            })),
            warnings,
            recommendations: ['Review manually fixed issues', 'Run validation again to confirm fixes'],
            timestamp: new Date().toISOString()
        };

        this.logger.info(`Auto-fix completed for server: ${this.context.serverName}`, {
            totalRules,
            fixedRules: fixedRules.length,
            failedRules: failedRules.length,
            successRate: fixSuccessRate,
            duration: Date.now() - startTime
        });

        return report;
    }
}

// Configuration Validation Rules
class ConfigurationNameRule implements ValidationRule {
    id = 'config-name';
    name = 'Configuration Name Validation';
    description = 'Validates server name follows KiloCode naming conventions';
    severity = 'high' as const;
    category = 'configuration' as const;

    async validate(context: ValidationContext): Promise<ExtendedValidationResult> {
        const { serverName } = context;
        const result: ExtendedValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Configuration name validation passed'
        };

        // Check length
        if (serverName.length > 30) {
            result.valid = false;
            result.errors.push(`Server name exceeds maximum length of 30 characters: ${serverName}`);
        }

        // Check for invalid characters
        if (!/^[a-z0-9-]+$/.test(serverName)) {
            result.valid = false;
            result.errors.push(`Server name contains invalid characters. Only lowercase letters, numbers, and hyphens allowed: ${serverName}`);
        }

        // Check for consecutive hyphens
        if (serverName.includes('--')) {
            result.warnings.push('Server name contains consecutive hyphens');
        }

        // Check for leading/trailing hyphens
        if (serverName.startsWith('-') || serverName.endsWith('-')) {
            result.warnings.push('Server name starts or ends with hyphen');
        }

        // Check for common patterns
        const commonPatterns = ['server', 'service', 'api', 'tool'];
        if (commonPatterns.some(pattern => serverName.includes(pattern))) {
            result.warnings.push('Server name contains generic terms');
        }

        return result;
    }
}

class ConfigurationStructureRule implements ValidationRule {
    id = 'config-structure';
    name = 'Configuration Structure Validation';
    description = 'Validates server configuration follows required structure';
    severity = 'critical' as const;
    category = 'configuration' as const;

    async validate(context: ValidationContext): Promise<ExtendedValidationResult> {
        const { serverConfig } = context;
        const result: ExtendedValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Configuration structure validation passed'
        };

        // Check required fields
        const requiredFields = ['command', 'args'];
        for (const field of requiredFields) {
            if (!(serverConfig as any)[field]) {
                result.valid = false;
                result.errors.push(`Missing required field: ${field}`);
            }
        }

        // Check command validity
        if ((serverConfig as any).command) {
            const validCommands = ['npx', 'node', 'python', 'python3'];
            if (!validCommands.includes((serverConfig as any).command)) {
                result.warnings.push(`Unknown command: ${(serverConfig as any).command}`);
            }
        }

        // Check args array
        if ((serverConfig as any).args && !Array.isArray((serverConfig as any).args)) {
            result.valid = false;
            result.errors.push('Args must be an array');
        }

        // Check environment variables
        if ((serverConfig as any).env && typeof (serverConfig as any).env !== 'object') {
            result.valid = false;
            result.errors.push('Env must be an object');
        }

        return result;
    }
}

class EnvironmentVariablesRule implements ValidationRule {
    id = 'env-variables';
    name = 'Environment Variables Validation';
    description = 'Validates environment variables follow KiloCode conventions';
    severity = 'high' as const;
    category = 'configuration' as const;

    async validate(context: ValidationContext): Promise<ExtendedValidationResult> {
        const { serverConfig, environment } = context;
        const result: ExtendedValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Environment variables validation passed'
        };

        if (!(serverConfig as any).env) {
            result.warnings.push('No environment variables configured');
            return result;
        }

        // Check for required environment variables
        const requiredVars = ['NODE_ENV', 'KILOCODE_ENV'];
        for (const varName of requiredVars) {
            if (!(serverConfig as any).env![varName]) {
                result.warnings.push(`Missing required environment variable: ${varName}`);
            }
        }

        // Check for sensitive data in environment variables
        const sensitiveVars = ['PASSWORD', 'TOKEN', 'SECRET', 'KEY', 'API_KEY'];
        for (const [varName, value] of Object.entries((serverConfig as any).env!)) {
            if (sensitiveVars.some(sensitive => varName.toUpperCase().includes(sensitive))) {
                if (typeof value === 'string' && value.length > 0) {
                    // Check for weak values
                    const weakPatterns = ['password', '123', 'admin', 'test', 'default'];
                    if (weakPatterns.some(pattern => value.toLowerCase().includes(pattern))) {
                        result.errors.push(`Weak ${varName}: contains common patterns`);
                        result.valid = false;
                    }
                }
            }
        }

        // Check for insecure protocols
        for (const [varName, value] of Object.entries((serverConfig as any).env!)) {
            if (varName.toUpperCase().includes('URL') && typeof value === 'string') {
                if (value.startsWith('http://') && !value.includes('localhost')) {
                    result.warnings.push(`Insecure protocol detected in ${varName}: ${value}`);
                }
            }
        }

        return result;
    }
}

class SecurityConfigurationRule implements ValidationRule {
    id = 'security-config';
    name = 'Security Configuration Validation';
    description = 'Validates security-related configuration settings';
    severity = 'critical' as const;
    category = 'security' as const;

    async validate(context: ValidationContext): Promise<ExtendedValidationResult> {
        const { serverConfig, environment } = context;
        const result: ExtendedValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Security configuration validation passed'
        };

        // Check for hardcoded credentials
        if ((serverConfig as any).args) {
            for (const arg of (serverConfig as any).args) {
                if (arg.includes('password=') || arg.includes('token=') || arg.includes('secret=')) {
                    result.errors.push('Hardcoded credentials found in server arguments');
                    result.valid = false;
                }
            }
        }

        // Check for insecure protocols in production
        if (environment === 'production') {
            if ((serverConfig as any).args?.some((arg: string) => arg.includes('http://') && !arg.includes('localhost'))) {
                result.errors.push('Insecure protocol detected in production environment');
                result.valid = false;
            }
        }

        // Check for proper environment variable usage
        if ((serverConfig as any).env) {
            const securityVars = ['TOKEN', 'API_KEY', 'SECRET', 'PASSWORD'];
            for (const varName of Object.keys((serverConfig as any).env)) {
                if (securityVars.some(security => varName.includes(security))) {
                    const value = (serverConfig as any).env[varName];
                    if (typeof value === 'string' && value.length < 8) {
                        result.warnings.push(`Short ${varName}: consider using longer values`);
                    }
                }
            }
        }

        return result;
    }
}

// Security Validation Rules
class TokenManagementRule implements ValidationRule {
    id = 'token-management';
    name = 'Token Management Validation';
    description = 'Validates token management and security practices';
    severity = 'critical' as const;
    category = 'security' as const;

    async validate(context: ValidationContext): Promise<ExtendedValidationResult> {
        const { serverConfig, environment } = context;
        const result: ExtendedValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Token management validation passed'
        };

        if (!(serverConfig as any).env) {
            result.warnings.push('No environment variables configured for token management');
            return result;
        }

        // Check for token-related environment variables
        const tokenVars = Object.keys((serverConfig as any).env).filter(key =>
            key.toUpperCase().includes('TOKEN') ||
            key.toUpperCase().includes('API_KEY') ||
            key.toUpperCase().includes('SECRET')
        );

        if (tokenVars.length === 0) {
            result.warnings.push('No token-related environment variables found');
            return result;
        }

        // Validate token values
        for (const varName of tokenVars) {
            const value = (serverConfig as any).env[varName];
            if (typeof value === 'string') {
                // Check for common weak tokens
                const weakTokens = ['default', 'example', 'test', 'demo', 'sample'];
                if (weakTokens.some(weak => value.toLowerCase().includes(weak))) {
                    result.errors.push(`Weak token value in ${varName}: contains common patterns`);
                    result.valid = false;
                }

                // Check token length
                if (value.length < 16) {
                    result.warnings.push(`Short token in ${varName}: consider using longer values`);
                }

                // Check for predictable patterns
                if (value.match(/^[a-zA-Z0-9]{8,}$/) && !value.match(/[A-Z]/) && !value.match(/[a-z]/) && !value.match(/[0-9]/)) {
                    result.warnings.push(`Token in ${varName} lacks complexity: consider adding special characters`);
                }
            }
        }

        // Check for token rotation in production
        if (environment === 'production') {
            const hasRotation = (serverConfig as any).env.TOKEN_ROTATION_INTERVAL ||
                (serverConfig as any).env.API_KEY_ROTATION_INTERVAL;
            if (!hasRotation) {
                result.warnings.push('Consider implementing token rotation for production environment');
            }
        }

        return result;
    }
}

class AccessControlRule implements ValidationRule {
    id = 'access-control';
    name = 'Access Control Validation';
    description = 'Validates access control and authentication configuration';
    severity = 'high' as const;
    category = 'security' as const;

    async validate(context: ValidationContext): Promise<ExtendedValidationResult> {
        const { serverConfig, environment } = context;
        const result: ExtendedValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Access control validation passed'
        };

        // Check for authentication configuration
        const authVars = ['AUTH_TOKEN', 'API_KEY', 'SECRET_KEY', 'ACCESS_TOKEN'];
        const hasAuth = authVars.some(varName => (serverConfig as any).env?.[varName]);

        if (!hasAuth) {
            result.warnings.push('No authentication configuration found');
        }

        // Check for rate limiting configuration
        if (environment === 'production') {
            const hasRateLimit = (serverConfig as any).env?.RATE_LIMIT ||
                (serverConfig as any).env?.REQUEST_LIMIT ||
                (serverConfig as any).env?.THROTTLE;
            if (!hasRateLimit) {
                result.warnings.push('Consider implementing rate limiting for production environment');
            }
        }

        // Check for IP whitelisting
        if (environment === 'production') {
            const hasWhitelist = (serverConfig as any).env?.ALLOWED_IPS ||
                (serverConfig as any).env?.WHITELIST_IPS;
            if (!hasWhitelist) {
                result.warnings.push('Consider implementing IP whitelisting for production environment');
            }
        }

        return result;
    }
}

class NetworkSecurityRule implements ValidationRule {
    id = 'network-security';
    name = 'Network Security Validation';
    description = 'Validates network security configuration';
    severity = 'high' as const;
    category = 'security' as const;

    async validate(context: ValidationContext): Promise<ExtendedValidationResult> {
        const { serverConfig, environment } = context;
        const result: ExtendedValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Network security validation passed'
        };

        // Check for secure protocols
        if ((serverConfig as any).args) {
            for (const arg of (serverConfig as any).args) {
                // Check for HTTP in production
                if (environment === 'production' && arg.includes('http://') && !arg.includes('localhost')) {
                    result.errors.push('Insecure HTTP protocol detected in production');
                    result.valid = false;
                }

                // Check for unencrypted connections
                if (arg.includes('://') && !arg.includes('https://') && !arg.includes('localhost')) {
                    result.warnings.push('Consider using HTTPS for external connections');
                }
            }
        }

        // Check for proper port configuration
        if ((serverConfig as any).env?.PORT) {
            const port = parseInt((serverConfig as any).env.PORT);
            if (port < 1024 && port !== 80 && port !== 443) {
                result.warnings.push('Using privileged port (< 1024) requires proper permissions');
            }
        }

        // Check for firewall configuration
        if (environment === 'production') {
            const hasFirewall = (serverConfig as any).env?.FIREWALL_RULES ||
                (serverConfig as any).env?.SECURITY_GROUPS;
            if (!hasFirewall) {
                result.warnings.push('Consider implementing firewall rules for production environment');
            }
        }

        return result;
    }
}

class DataEncryptionRule implements ValidationRule {
    id = 'data-encryption';
    name = 'Data Encryption Validation';
    description = 'Validates data encryption configuration';
    severity = 'critical' as const;
    category = 'security' as const;

    async validate(context: ValidationContext): Promise<ValidationResult> {
        const { serverConfig, environment } = context;
        const result: ValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Data encryption validation passed'
        };

        // Check for encryption configuration
        const encryptionVars = ['ENCRYPTION_KEY', 'ENCRYPTION_ALGORITHM', 'SSL_CERT'];
        const hasEncryption = encryptionVars.some(varName => serverConfig.env?.[varName]);

        if (!hasEncryption && environment === 'production') {
            result.warnings.push('Consider implementing data encryption for production environment');
        }

        // Check for SSL/TLS configuration
        if (serverConfig.args?.some(arg => arg.includes('--ssl') || arg.includes('--tls'))) {
            const hasCert = serverConfig.env?.SSL_CERT || serverConfig.env?.TLS_CERT;
            if (!hasCert) {
                result.errors.push('SSL/TLS enabled but certificate not configured');
                result.valid = false;
            }
        }

        // Check for secure cipher suites
        if (serverConfig.env?.CIPHER_SUITES) {
            const weakCiphers = ['RC4', 'DES', '3DES', 'MD5', 'SHA1'];
            if (weakCiphers.some(cipher => (serverConfig.env!.CIPHER_SUITES || '').includes(cipher))) {
                result.errors.push('Weak cipher suites detected');
                result.valid = false;
            }
        }

        return result;
    }
}

// Performance Validation Rules
class ResponseTimeRule implements ValidationRule {
    id = 'response-time';
    name = 'Response Time Validation';
    description = 'Validates response time performance benchmarks';
    severity = 'medium' as const;
    category = 'performance' as const;

    async validate(context: ValidationContext): Promise<ValidationResult> {
        const { serverConfig, environment } = context;
        const result: ValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Response time validation passed'
        };

        // Define response time benchmarks by environment
        const benchmarks = {
            development: 500, // 500ms
            staging: 200,     // 200ms
            production: 100   // 100ms
        };

        const benchmark = benchmarks[environment];

        // Check for timeout configuration
        if (serverConfig.env?.TIMEOUT) {
            const timeout = parseInt(serverConfig.env.TIMEOUT);
            if (timeout > benchmark * 2) {
                result.warnings.push(`Timeout (${timeout}ms) exceeds recommended benchmark (${benchmark}ms)`);
            }
        }

        // Check for response optimization
        if (serverConfig.args?.some(arg => arg.includes('--cache') || arg.includes('--compress'))) {
            result.message = 'Response optimization features detected';
        } else {
            result.warnings.push('Consider enabling response optimization features');
        }

        return result;
    }
}

class ResourceUsageRule implements ValidationRule {
    id = 'resource-usage';
    name = 'Resource Usage Validation';
    description = 'Validates resource usage and performance optimization';
    severity = 'medium' as const;
    category = 'performance' as const;

    async validate(context: ValidationContext): Promise<ValidationResult> {
        const { serverConfig, environment } = context;
        const result: ValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Resource usage validation passed'
        };

        // Check for memory limits
        if (serverConfig.env?.MEMORY_LIMIT) {
            const memoryLimit = parseInt(serverConfig.env.MEMORY_LIMIT);
            if (memoryLimit > 8192 && environment === 'production') {
                result.warnings.push('High memory limit configured, consider monitoring and optimization');
            }
        }

        // Check for CPU limits
        if (serverConfig.env?.CPU_LIMIT) {
            const cpuLimit = parseInt(serverConfig.env.CPU_LIMIT);
            if (cpuLimit > 80 && environment === 'production') {
                result.warnings.push('High CPU limit configured, consider optimization');
            }
        }

        // Check for connection pooling
        if (serverConfig.env?.MAX_CONNECTIONS) {
            const maxConnections = parseInt(serverConfig.env.MAX_CONNECTIONS);
            if (maxConnections > 100 && environment === 'production') {
                result.warnings.push('High connection limit configured, consider connection pooling');
            }
        }

        // Check for caching configuration
        if (!serverConfig.env?.CACHE_SIZE && environment === 'production') {
            result.warnings.push('Consider implementing caching for better performance');
        }

        return result;
    }
}

class ThroughputRule implements ValidationRule {
    id = 'throughput';
    name = 'Throughput Validation';
    description = 'Validates throughput and capacity planning';
    severity = 'medium' as const;
    category = 'performance' as const;

    async validate(context: ValidationContext): Promise<ValidationResult> {
        const { serverConfig, environment } = context;
        const result: ValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Throughput validation passed'
        };

        // Check for batch processing configuration
        if (serverConfig.args?.some(arg => arg.includes('--batch') || arg.includes('--bulk'))) {
            result.message = 'Batch processing features detected';
        } else {
            result.warnings.push('Consider implementing batch processing for better throughput');
        }

        // Check for parallel processing
        if (serverConfig.env?.MAX_WORKERS) {
            const maxWorkers = parseInt(serverConfig.env.MAX_WORKERS);
            if (maxWorkers > 1) {
                result.message = 'Parallel processing configured';
            }
        }

        // Check for load balancing
        if (environment === 'production' && !serverConfig.env?.LOAD_BALANCER) {
            result.warnings.push('Consider implementing load balancing for production environment');
        }

        return result;
    }
}

class ScalabilityRule implements ValidationRule {
    id = 'scalability';
    name = 'Scalability Validation';
    description = 'Validates scalability and auto-scaling configuration';
    severity = 'medium' as const;
    category = 'performance' as const;

    async validate(context: ValidationContext): Promise<ValidationResult> {
        const { serverConfig, environment } = context;
        const result: ValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Scalability validation passed'
        };

        // Check for auto-scaling configuration
        if (environment === 'production') {
            const hasAutoScaling = serverConfig.env?.AUTO_SCALE ||
                serverConfig.env?.SCALE_THRESHOLD ||
                serverConfig.env?.MIN_INSTANCES ||
                serverConfig.env?.MAX_INSTANCES;

            if (!hasAutoScaling) {
                result.warnings.push('Consider implementing auto-scaling for production environment');
            }
        }

        // Check for stateless configuration
        if (serverConfig.args?.some(arg => arg.includes('--stateless') || arg.includes('--sessionless'))) {
            result.message = 'Stateless configuration detected';
        } else {
            result.warnings.push('Consider implementing stateless design for better scalability');
        }

        // Check for database connection pooling
        if (serverConfig.env?.DB_POOL_SIZE) {
            const poolSize = parseInt(serverConfig.env.DB_POOL_SIZE);
            if (poolSize > 10) {
                result.message = 'Database connection pooling configured';
            }
        }

        return result;
    }
}

// Compatibility Validation Rules
class VersionCompatibilityRule implements ValidationRule {
    id = 'version-compatibility';
    name = 'Version Compatibility Validation';
    description = 'Validates version compatibility requirements';
    severity = 'high' as const;
    category = 'compatibility' as const;

    async validate(context: ValidationContext): Promise<ValidationResult> {
        const { serverConfig, environment } = context;
        const result: ValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Version compatibility validation passed'
        };

        // Check for Node.js version compatibility
        if (serverConfig.command === 'node') {
            const nodeVersion = serverConfig.env?.NODE_VERSION;
            if (nodeVersion) {
                const versionParts = nodeVersion.split('.').map(Number);
                if (versionParts[0] && versionParts[0] < 18) {
                    result.errors.push('Node.js version must be 18.x or higher');
                    result.valid = false;
                }
            }
        }

        // Check for Python version compatibility
        if (serverConfig.command === 'python' || serverConfig.command === 'python3') {
            const pythonVersion = serverConfig.env?.PYTHON_VERSION;
            if (pythonVersion) {
                const versionParts = pythonVersion.split('.').map(Number);
                if (versionParts[0] === 3 && versionParts[1] && versionParts[1] < 8) {
                    result.errors.push('Python version must be 3.8 or higher');
                    result.valid = false;
                }
            }
        }

        // Check for MCP protocol version
        if (serverConfig.env?.MCP_VERSION) {
            const mcpVersion = serverConfig.env.MCP_VERSION;
            if (!mcpVersion.startsWith('1.')) {
                result.warnings.push('MCP protocol version should be 1.x for compatibility');
            }
        }

        return result;
    }
}

class ProtocolAdherenceRule implements ValidationRule {
    id = 'protocol-adherence';
    name = 'Protocol Adherence Validation';
    description = 'Validates MCP protocol adherence';
    severity = 'critical' as const;
    category = 'compatibility' as const;

    async validate(context: ValidationContext): Promise<ValidationResult> {
        const { serverConfig } = context;
        const result: ValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Protocol adherence validation passed'
        };

        // Check for MCP protocol compliance flags
        const protocolFlags = ['--mcp', '--protocol', '--stdio'];
        const hasProtocolFlag = serverConfig.args?.some(arg =>
            protocolFlags.some(flag => arg.includes(flag))
        );

        if (!hasProtocolFlag) {
            result.warnings.push('Consider adding MCP protocol compliance flags');
        }

        // Check for required MCP arguments
        if (serverConfig.command === 'npx') {
            const mcpServers = [
                '@modelcontextprotocol/server-filesystem',
                '@modelcontextprotocol/server-postgres',
                '@modelcontextprotocol/server-sqlite'
            ];

            const isMCPServer = mcpServers.some(server =>
                serverConfig.args?.some(arg => arg.includes(server))
            );

            if (isMCPServer && !serverConfig.args?.some(arg => arg.includes('--stdio'))) {
                result.errors.push('MCP servers must use --stdio flag for protocol compliance');
                result.valid = false;
            }
        }

        return result;
    }
}

class DependencyCompatibilityRule implements ValidationRule {
    id = 'dependency-compatibility';
    name = 'Dependency Compatibility Validation';
    description = 'Validates dependency compatibility and versions';
    severity = 'medium' as const;
    category = 'compatibility' as const;

    async validate(context: ValidationContext): Promise<ValidationResult> {
        const { serverConfig, projectRoot } = context;
        const result: ValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Dependency compatibility validation passed'
        };

        try {
            // Check package.json for dependencies
            const packageJsonPath = path.join(projectRoot, 'package.json');
            const packageJson = JSON.parse(await fs.readFile(packageJsonPath, 'utf-8'));

            if (packageJson.dependencies) {
                // Check for outdated dependencies
                for (const [dep, version] of Object.entries(packageJson.dependencies)) {
                    if (typeof version === 'string' && (version.startsWith('^') || version.startsWith('~'))) {
                        result.warnings.push(`Dependency ${dep} uses loose version constraint: ${version}`);
                    }
                }
            }

            // Check for conflicting dependencies
            if (packageJson.devDependencies) {
                const devDeps = Object.keys(packageJson.devDependencies);
                const prodDeps = Object.keys(packageJson.dependencies || {});

                const conflicts = devDeps.filter(dep => prodDeps.includes(dep));
                if (conflicts.length > 0) {
                    result.warnings.push(`Dependencies exist in both dev and prod: ${conflicts.join(', ')}`);
                }
            }

        } catch (error) {
            result.warnings.push('Could not validate package.json dependencies');
        }

        return result;
    }
}

// Reliability Validation Rules
class UptimeRequirementRule implements ValidationRule {
    id = 'uptime-requirement';
    name = 'Uptime Requirement Validation';
    description = 'Validates uptime and availability requirements';
    severity = 'high' as const;
    category = 'reliability' as const;

    async validate(context: ValidationContext): Promise<ValidationResult> {
        const { serverConfig, environment } = context;
        const result: ValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Uptime requirement validation passed'
        };

        // Define uptime requirements by environment
        const uptimeRequirements = {
            development: 95,   // 95% uptime
            staging: 99,      // 99% uptime
            production: 99.9  // 99.9% uptime
        };

        const requiredUptime = uptimeRequirements[environment];

        // Check for health check configuration
        if (!serverConfig.env?.HEALTH_CHECK_INTERVAL) {
            result.warnings.push('Consider implementing health checks for monitoring uptime');
        }

        // Check for monitoring configuration
        if (environment === 'production' && !serverConfig.env?.MONITORING_ENABLED) {
            result.warnings.push('Consider enabling monitoring for production environment');
        }

        // Check for alerting configuration
        if (environment === 'production' && !serverConfig.env?.ALERTING_ENABLED) {
            result.warnings.push('Consider implementing alerting for production environment');
        }

        return result;
    }
}

class ErrorHandlingRule implements ValidationRule {
    id = 'error-handling';
    name = 'Error Handling Validation';
    description = 'Validates error handling and logging configuration';
    severity = 'medium' as const;
    category = 'reliability' as const;

    async validate(context: ValidationContext): Promise<ValidationResult> {
        const { serverConfig, environment } = context;
        const result: ValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Error handling validation passed'
        };

        // Check for error logging configuration
        if (!serverConfig.env?.LOG_LEVEL) {
            result.warnings.push('Consider configuring log level for error handling');
        }

        // Check for error handling flags
        if (serverConfig.args?.some(arg => arg.includes('--error-handling') || arg.includes('--strict'))) {
            result.message = 'Error handling features detected';
        } else {
            result.warnings.push('Consider enabling strict error handling');
        }

        // Check for retry configuration
        if (serverConfig.env?.RETRY_COUNT) {
            const retryCount = parseInt(serverConfig.env.RETRY_COUNT);
            if (retryCount > 3 && environment === 'production') {
                result.warnings.push('High retry count configured, consider exponential backoff');
            }
        }

        // Check for circuit breaker configuration
        if (!serverConfig.env?.CIRCUIT_BREAKER_ENABLED && environment === 'production') {
            result.warnings.push('Consider implementing circuit breaker pattern for resilience');
        }

        return result;
    }
}

class RecoveryProcedureRule implements ValidationRule {
    id = 'recovery-procedure';
    name = 'Recovery Procedure Validation';
    description = 'Validates recovery and backup procedures';
    severity = 'high' as const;
    category = 'reliability' as const;

    async validate(context: ValidationContext): Promise<ValidationResult> {
        const { serverConfig, environment } = context;
        const result: ValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Recovery procedure validation passed'
        };

        // Check for backup configuration
        if (environment === 'production') {
            const hasBackup = serverConfig.env?.BACKUP_ENABLED ||
                serverConfig.env?.BACKUP_SCHEDULE ||
                serverConfig.env?.BACKUP_RETENTION;

            if (!hasBackup) {
                result.errors.push('Backup configuration required for production environment');
                result.valid = false;
            }
        }

        // Check for recovery procedures
        if (!serverConfig.env?.RECOVERY_PROCEDURE && environment === 'production') {
            result.warnings.push('Consider documenting recovery procedures');
        }

        // Check for rollback configuration
        if (!serverConfig.env?.ROLLBACK_ENABLED && environment === 'production') {
            result.warnings.push('Consider implementing rollback capabilities');
        }

        // Check for failover configuration
        if (environment === 'production' && !serverConfig.env?.FAILOVER_ENABLED) {
            result.warnings.push('Consider implementing failover for critical services');
        }

        return result;
    }
}

// Server Type Specific Rules
class FilesystemServerRule implements ValidationRule {
    id = 'filesystem-server';
    name = 'Filesystem Server Validation';
    description = 'Validates filesystem-specific configuration';
    severity = 'medium' as const;
    category = 'configuration' as const;

    async validate(context: ValidationContext): Promise<ValidationResult> {
        const { serverConfig } = context;
        const result: ValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Filesystem server validation passed'
        };

        // Check for filesystem-specific environment variables
        const fsVars = ['FILESYSTEM_ROOT', 'UPLOAD_DIR', 'TEMP_DIR', 'BACKUP_DIR'];
        const hasFsVars = fsVars.some(varName => serverConfig.env?.[varName]);

        if (!hasFsVars) {
            result.warnings.push('Consider configuring filesystem-specific directories');
        }

        // Check for file size limits
        if (!serverConfig.env?.MAX_FILE_SIZE) {
            result.warnings.push('Consider setting maximum file size limits');
        }

        // Check for file type restrictions
        if (!serverConfig.env?.ALLOWED_FILE_TYPES) {
            result.warnings.push('Consider setting allowed file type restrictions');
        }

        // Check for file permissions
        if (!serverConfig.env?.FILE_PERMISSIONS) {
            result.warnings.push('Consider setting secure file permissions');
        }

        return result;
    }
}

class DatabaseServerRule implements ValidationRule {
    id = 'database-server';
    name = 'Database Server Validation';
    description = 'Validates database-specific configuration';
    severity = 'high' as const;
    category = 'configuration' as const;

    async validate(context: ValidationContext): Promise<ValidationResult> {
        const { serverConfig } = context;
        const result: ValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Database server validation passed'
        };

        // Check for database connection configuration
        const dbVars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD'];
        const hasDbVars = dbVars.some(varName => serverConfig.env?.[varName]);

        if (!hasDbVars) {
            result.warnings.push('Database connection configuration required');
        }

        // Check for connection pooling
        if (!serverConfig.env?.DB_POOL_SIZE) {
            result.warnings.push('Consider configuring database connection pooling');
        }

        // Check for query timeout
        if (!serverConfig.env?.DB_QUERY_TIMEOUT) {
            result.warnings.push('Consider setting database query timeout');
        }

        // Check for connection encryption
        if (!serverConfig.env?.DB_SSL_ENABLED) {
            result.warnings.push('Consider enabling database connection encryption');
        }

        return result;
    }
}

class MemoryServerRule implements ValidationRule {
    id = 'memory-server';
    name = 'Memory Server Validation';
    description = 'Validates memory-specific configuration';
    severity = 'medium' as const;
    category = 'configuration' as const;

    async validate(context: ValidationContext): Promise<ValidationResult> {
        const { serverConfig } = context;
        const result: ValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'Memory server validation passed'
        };

        // Check for memory limits
        if (!serverConfig.env?.MEMORY_LIMIT) {
            result.warnings.push('Consider setting memory usage limits');
        }

        // Check for cache configuration
        if (!serverConfig.env?.CACHE_SIZE) {
            result.warnings.push('Consider configuring cache size limits');
        }

        // Check for cache expiration
        if (!serverConfig.env?.CACHE_TTL) {
            result.warnings.push('Consider setting cache expiration time');
        }

        // Check for memory optimization
        if (!serverConfig.args?.some(arg => arg.includes('--memory-optimization'))) {
            result.warnings.push('Consider enabling memory optimization features');
        }

        return result;
    }
}

class APIServerRule implements ValidationRule {
    id = 'api-server';
    name = 'API Server Validation';
    description = 'Validates API-specific configuration';
    severity = 'high' as const;
    category = 'configuration' as const;

    async validate(context: ValidationContext): Promise<ValidationResult> {
        const { serverConfig } = context;
        const result: ValidationResult = {
            valid: true,
            errors: [],
            warnings: [],
            suggestions: [],
            recommendations: [],
            ruleId: this.id,
            ruleName: this.name,
            severity: this.severity,
            message: 'API server validation passed'
        };

        // Check for API versioning
        if (!serverConfig.env?.API_VERSION) {
            result.warnings.push('Consider implementing API versioning');
        }

        // Check for rate limiting
        if (!serverConfig.env?.RATE_LIMIT) {
            result.warnings.push('Consider implementing rate limiting');
        }

        // Check for API documentation
        if (!serverConfig.env?.API_DOCS_URL) {
            result.warnings.push('Consider providing API documentation');
        }

        // Check for API key management
        if (!serverConfig.env?.API_KEY_HEADER) {
            result.warnings.push('Consider configuring API key authentication');
        }

        return result;
    }
}

export default ValidationEngine;