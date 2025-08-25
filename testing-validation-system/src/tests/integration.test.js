const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

describe('Integration Tests - Testing and Validation System', () => {
  const projectRoot = path.join(__dirname, '..', '..');
  
  describe('Podman Integration Tests', () => {
    test('should validate podman-compose.yml structure', () => {
      const composePath = path.join(projectRoot, 'podman-compose.yml');
      const composeContent = fs.readFileSync(composePath, 'utf8');
      const compose = yaml.load(composeContent);
      
      expect(compose.version).toBe('3.8');
      expect(compose.services.postgres).toBeDefined();
      expect(compose.services.test).toBeDefined();
    });

    test('should validate service dependencies', () => {
      const composePath = path.join(projectRoot, 'podman-compose.yml');
      const composeContent = fs.readFileSync(composePath, 'utf8');
      const compose = yaml.load(composeContent);
      
      const testService = compose.services.test;
      expect(testService.depends_on).toHaveProperty('postgres');
      expect(testService.environment.DATABASE_URL).toBeDefined();
    });

    test('should validate volume mounts', () => {
      const composePath = path.join(projectRoot, 'podman-compose.yml');
      const composeContent = fs.readFileSync(composePath, 'utf8');
      const compose = yaml.load(composeContent);
      
      const testService = compose.services.test;
      expect(testService.volumes).toContain('./src:/app/src:ro');
      expect(testService.volumes).toContain('./reports:/app/reports');
    });
  });

  describe('Database Integration Tests', () => {
    test('should validate SQL schema structure', () => {
      const sqlPath = path.join(projectRoot, 'sql/init-test-db.sql');
      const sqlContent = fs.readFileSync(sqlPath, 'utf8');
      
      expect(sqlContent).toContain('CREATE TABLE IF NOT EXISTS test_suites');
      expect(sqlContent).toContain('CREATE TABLE IF NOT EXISTS test_cases');
      expect(sqlContent).toContain('CREATE TABLE IF NOT EXISTS test_executions');
      expect(sqlContent).toContain('CREATE TABLE IF NOT EXISTS test_results');
      expect(sqlContent).toContain('CREATE TABLE IF NOT EXISTS static_analysis_results');
      expect(sqlContent).toContain('CREATE TABLE IF NOT EXISTS performance_metrics');
      
      // Check for proper column definitions
      expect(sqlContent).toMatch(/name\s+VARCHAR/);
      expect(sqlContent).toMatch(/status\s+VARCHAR/);
      expect(sqlContent).toMatch(/created_at\s+TIMESTAMPTZ/);
    });

    test('should validate indexes are created', () => {
      const sqlPath = path.join(projectRoot, 'sql/init-test-db.sql');
      const sqlContent = fs.readFileSync(sqlPath, 'utf8');
      
      expect(sqlContent).toContain('CREATE INDEX IF NOT EXISTS idx_test_cases_suite_id ON test_cases(suite_id)');
      expect(sqlContent).toContain('CREATE INDEX IF NOT EXISTS idx_test_results_execution_id ON test_results(execution_id)');
    });
  });

  describe('Dockerfile Tests', () => {
    test('should validate Dockerfile.test structure', () => {
      const dockerfilePath = path.join(projectRoot, 'Dockerfile.test');
      const dockerfileContent = fs.readFileSync(dockerfilePath, 'utf8');
      
      expect(dockerfileContent).toContain('FROM node:18-alpine');
      expect(dockerfileContent).toContain('WORKDIR /app');
      expect(dockerfileContent).toContain('COPY package*.json ./');
      expect(dockerfileContent).toContain('RUN npm ci');
    });

    test('should validate health check configuration', () => {
      const dockerfilePath = path.join(projectRoot, 'Dockerfile.test');
      const dockerfileContent = fs.readFileSync(dockerfilePath, 'utf8');
      
    });
  });

  describe('GitHub Actions Integration Tests', () => {
    test('should validate workflow triggers', () => {
      const workflowPath = path.join(projectRoot, '.github/workflows/test.yml');
      const workflowContent = fs.readFileSync(workflowPath, 'utf8');
      
      expect(workflowContent).toContain('on: [push, pull_request]');
    });

    test('should validate job dependencies', () => {
      const workflowPath = path.join(projectRoot, '.github/workflows/test.yml');
      const workflowContent = fs.readFileSync(workflowPath, 'utf8');
      
      expect(workflowContent).toContain('needs: [lint, security]');
    });

    test('should validate matrix strategy', () => {
      const workflowPath = path.join(projectRoot, '.github/workflows/test.yml');
      const workflowContent = fs.readFileSync(workflowPath, 'utf8');
      
      expect(workflowContent).toContain('matrix');
      expect(workflowContent).toContain('node-version');
      expect(workflowContent).toContain('os: [ubuntu-latest, windows-latest]');
    });
  });

  describe('Cross-platform Script Tests', () => {
    test('should validate Windows batch script', () => {
      const batPath = path.join(projectRoot, 'scripts/setup-podman.bat');
      const batContent = fs.readFileSync(batPath, 'utf8');
      
      expect(batContent).toContain('@echo off');
      expect(batContent).toContain('podman-compose up -d');
      expect(batContent).toContain('podman-compose logs -f');
    });

    test('should validate Unix shell script', () => {
      const shPath = path.join(projectRoot, 'scripts/setup-podman.sh');
      const shContent = fs.readFileSync(shPath, 'utf8');
      
      expect(shContent).toContain('#!/bin/bash');
      expect(shContent).toContain('podman-compose up -d');
      expect(shContent).toContain('chmod +x');
    });
  });

  describe('Environment Configuration Tests', () => {
    test('should validate environment variables', () => {
      const composePath = path.join(projectRoot, 'podman-compose.yml');
      const composeContent = fs.readFileSync(composePath, 'utf8');
      const compose = yaml.load(composeContent);
      
      const postgres = compose.services.postgres;
      expect(postgres.environment.POSTGRES_DB).toBe('test_db');
      expect(postgres.environment.POSTGRES_USER).toBe('test_user');
      expect(postgres.environment.POSTGRES_PASSWORD).toBe('test_password');
    });

    test('should validate port mappings', () => {
      const composePath = path.join(projectRoot, 'podman-compose.yml');
      const composeContent = fs.readFileSync(composePath, 'utf8');
      const compose = yaml.load(composeContent);
      
      const postgres = compose.services.postgres;
      expect(postgres.ports).toContain('5432:5432');
    });
  });

  describe('Report Generation Tests', () => {
    test('should validate report script exists', () => {
      const reportScriptPath = path.join(projectRoot, 'scripts/generate-report.js');
      expect(fs.existsSync(reportScriptPath)).toBe(true);
    });

    test('should validate report script functionality', () => {
      const reportScriptPath = path.join(projectRoot, 'scripts/generate-report.js');
      const reportContent = fs.readFileSync(reportScriptPath, 'utf8');
      
      expect(reportContent).toContain('generateReport');
      expect(reportContent).toContain('summaryResult.rows');
      expect(reportContent).toContain('securityResult.rows');
      expect(reportContent).toContain('test-report.json');
      expect(reportContent).toContain('test-report.html');
    });
  });

  describe('Health Check Tests', () => {
    test('should validate health check endpoints', () => {
      const composePath = path.join(projectRoot, 'podman-compose.yml');
      const composeContent = fs.readFileSync(composePath, 'utf8');
      const compose = yaml.load(composeContent);
      
      const postgres = compose.services.postgres;
      expect(postgres.healthcheck.test).toContain('pg_isready -U test_user -d test_db');
      expect(postgres.healthcheck.interval).toBe('10s');
      expect(postgres.healthcheck.timeout).toBe('5s');
      expect(postgres.healthcheck.retries).toBe(5);
    });
  });
});
