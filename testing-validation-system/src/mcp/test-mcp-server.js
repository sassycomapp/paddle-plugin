#!/usr/bin/env node

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');
const { Pool } = require('pg');
const { spawn } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

class TestMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'test-mcp-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // PostgreSQL connection
    this.pool = new Pool({
      connectionString: process.env.DATABASE_URL || 'postgresql://postgres:2001@localhost:5432/postgres',
    });

    this.setupTools();
  }

  setupTools() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'create_test_suite',
          description: 'Create a new test suite',
          inputSchema: {
            type: 'object',
            properties: {
              name: { type: 'string', description: 'Name of the test suite' },
              description: { type: 'string', description: 'Description of the test suite' },
              type: { 
                type: 'string', 
                enum: ['unit', 'integration', 'e2e', 'security', 'performance'],
                description: 'Type of test suite'
              }
            },
            required: ['name', 'type']
          }
        },
        {
          name: 'create_test_case',
          description: 'Create a new test case',
          inputSchema: {
            type: 'object',
            properties: {
              suite_name: { type: 'string', description: 'Name of the test suite' },
              name: { type: 'string', description: 'Name of the test case' },
              description: { type: 'string', description: 'Description of the test case' },
              file_path: { type: 'string', description: 'Path to the test file' },
              test_function: { type: 'string', description: 'Name of the test function' },
              tags: { type: 'array', items: { type: 'string' }, description: 'Tags for categorization' },
              priority: { 
                type: 'string', 
                enum: ['low', 'medium', 'high', 'critical'],
                description: 'Priority level'
              }
            },
            required: ['suite_name', 'name']
          }
        },
        {
          name: 'run_test_suite',
          description: 'Execute a test suite',
          inputSchema: {
            type: 'object',
            properties: {
              suite_name: { type: 'string', description: 'Name of the test suite to run' },
              environment: { 
                type: 'string', 
                enum: ['local', 'podman', 'ci'],
                default: 'local',
                description: 'Environment to run tests in'
              },
              branch: { type: 'string', description: 'Git branch being tested' },
              commit_hash: { type: 'string', description: 'Git commit hash' }
            },
            required: ['suite_name']
          }
        },
        {
          name: 'get_test_results',
          description: 'Get test results for a specific execution',
          inputSchema: {
            type: 'object',
            properties: {
              execution_id: { type: 'number', description: 'ID of the test execution' },
              suite_name: { type: 'string', description: 'Name of the test suite' },
              limit: { type: 'number', default: 50, description: 'Maximum number of results' }
            }
          }
        },
        {
          name: 'get_test_summary',
          description: 'Get summary of test results across all suites',
          inputSchema: {
            type: 'object',
            properties: {
              days: { type: 'number', default: 7, description: 'Number of days to look back' }
            }
          }
        },
        {
          name: 'run_security_scan',
          description: 'Run Semgrep security scan on codebase',
          inputSchema: {
            type: 'object',
            properties: {
              path: { type: 'string', default: '.', description: 'Path to scan' },
              rules: { type: 'string', default: 'auto', description: 'Semgrep rules to use' }
            }
          }
        },
        {
          name: 'generate_test_report',
          description: 'Generate comprehensive test report',
          inputSchema: {
            type: 'object',
            properties: {
              execution_id: { type: 'number', description: 'Specific execution ID' },
              format: { 
                type: 'string', 
                enum: ['json', 'html', 'markdown'],
                default: 'json',
                description: 'Report format'
              }
            }
          }
        }
      ]
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'create_test_suite':
            return await this.createTestSuite(args);
          case 'create_test_case':
            return await this.createTestCase(args);
          case 'run_test_suite':
            return await this.runTestSuite(args);
          case 'get_test_results':
            return await this.getTestResults(args);
          case 'get_test_summary':
            return await this.getTestSummary(args);
          case 'run_security_scan':
            return await this.runSecurityScan(args);
          case 'generate_test_report':
            return await this.generateTestReport(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [{
            type: 'text',
            text: `Error: ${error.message}`
          }],
          isError: true
        };
      }
    });
  }

  async createTestSuite(args) {
    const { name, description, type } = args;
    
    const query = `
      INSERT INTO test_suites (name, description, type)
      VALUES ($1, $2, $3)
      RETURNING *
    `;
    
    const result = await this.pool.query(query, [name, description, type]);
    
    return {
      content: [{
        type: 'text',
        text: `Created test suite: ${JSON.stringify(result.rows[0], null, 2)}`
      }]
    };
  }

  async createTestCase(args) {
    const { suite_name, name, description, file_path, test_function, tags, priority } = args;
    
    // Get suite ID
    const suiteQuery = 'SELECT id FROM test_suites WHERE name = $1';
    const suiteResult = await this.pool.query(suiteQuery, [suite_name]);
    
    if (suiteResult.rows.length === 0) {
      throw new Error(`Test suite '${suite_name}' not found`);
    }
    
    const suiteId = suiteResult.rows[0].id;
    
    const query = `
      INSERT INTO test_cases (suite_id, name, description, file_path, test_function, tags, priority)
      VALUES ($1, $2, $3, $4, $5, $6, $7)
      RETURNING *
    `;
    
    const result = await this.pool.query(query, [
      suiteId, name, description, file_path, test_function, tags || [], priority || 'medium'
    ]);
    
    return {
      content: [{
        type: 'text',
        text: `Created test case: ${JSON.stringify(result.rows[0], null, 2)}`
      }]
    };
  }

  async runTestSuite(args) {
    const { suite_name, environment = 'local', branch, commit_hash } = args;
    
    // Get suite details
    const suiteQuery = 'SELECT * FROM test_suites WHERE name = $1';
    const suiteResult = await this.pool.query(suiteQuery, [suite_name]);
    
    if (suiteResult.rows.length === 0) {
      throw new Error(`Test suite '${suite_name}' not found`);
    }
    
    const suite = suiteResult.rows[0];
    
    // Create test execution record
    const executionQuery = `
      INSERT INTO test_executions (suite_id, execution_name, status, environment, branch, commit_hash)
      VALUES ($1, $2, 'running', $3, $4, $5)
      RETURNING *
    `;
    
    const executionName = `${suite_name}_${new Date().toISOString()}`;
    const executionResult = await this.pool.query(executionQuery, [
      suite.id, executionName, environment, branch, commit_hash
    ]);
    
    const executionId = executionResult.rows[0].id;
    
    // Run tests based on type
    let testResults = [];
    
    try {
      switch (suite.type) {
        case 'unit':
          testResults = await this.runUnitTests(suite, executionId);
          break;
        case 'integration':
          testResults = await this.runIntegrationTests(suite, executionId);
          break;
        case 'e2e':
          testResults = await this.runE2ETests(suite, executionId);
          break;
        case 'security':
          testResults = await this.runSecurityTests(suite, executionId);
          break;
        case 'performance':
          testResults = await this.runPerformanceTests(suite, executionId);
          break;
      }
      
      // Update execution status
      await this.pool.query(
        'UPDATE test_executions SET status = $1, completed_at = NOW() WHERE id = $2',
        ['completed', executionId]
      );
      
    } catch (error) {
      await this.pool.query(
        'UPDATE test_executions SET status = $1, completed_at = NOW() WHERE id = $2',
        ['failed', executionId]
      );
      throw error;
    }
    
    return {
      content: [{
        type: 'text',
        text: `Test execution completed: ${executionName}\nResults: ${JSON.stringify(testResults, null, 2)}`
      }]
    };
  }

  async runUnitTests(suite, executionId) {
    // Run Jest unit tests
    return new Promise((resolve, reject) => {
      const jest = spawn('npx', ['jest', '--json', '--outputFile=jest-results.json'], {
        stdio: 'inherit'
      });
      
      jest.on('close', async (code) => {
        try {
          const results = JSON.parse(await fs.readFile('jest-results.json', 'utf8'));
          
          // Store results in database
          for (const testResult of results.testResults) {
            for (const test of testResult.assertionResults) {
              await this.pool.query(
                `INSERT INTO test_results (execution_id, case_id, status, duration_ms, error_message)
                 VALUES ($1, $2, $3, $4, $5)`,
                [executionId, null, test.status, test.duration, test.failureMessages?.[0]]
              );
            }
          }
          
          resolve(results);
        } catch (error) {
          reject(error);
        }
      });
    });
  }

  async runIntegrationTests(suite, executionId) {
    // Run integration tests with Docker/Podman
    const composeFile = environment === 'podman' ? 'docker-compose.podman.yml' : 'docker-compose.yml';
    
    return new Promise((resolve, reject) => {
      const docker = spawn('docker-compose', ['-f', composeFile, 'up', '--abort-on-container-exit'], {
        stdio: 'inherit'
      });
      
      docker.on('close', async (code) => {
        // Parse and store results
        resolve({ status: code === 0 ? 'passed' : 'failed' });
      });
    });
  }

  async runSecurityTests(suite, executionId) {
    // Run Semgrep security scan
    return new Promise((resolve, reject) => {
      const semgrep = spawn('semgrep', ['--config=auto', '--json', '.'], {
        stdio: 'pipe'
      });
      
      let output = '';
      semgrep.stdout.on('data', (data) => {
        output += data.toString();
      });
      
      semgrep.on('close', async (code) => {
        try {
          const results = JSON.parse(output);
          
          // Store security findings
          for (const finding of results.results || []) {
            await this.pool.query(
              `INSERT INTO static_analysis_results 
               (execution_id, rule_id, severity, file_path, line_number, message)
               VALUES ($1, $2, $3, $4, $5, $6)`,
              [
                executionId,
                finding.check_id,
                finding.extra.severity,
                finding.path,
                finding.start.line,
                finding.extra.message
              ]
            );
          }
          
          resolve(results);
        } catch (error) {
          reject(error);
        }
      });
    });
  }

  async getTestResults(args) {
    const { execution_id, suite_name, limit = 50 } = args;
    
    let query = `
      SELECT r.*, c.name as case_name, s.name as suite_name
      FROM test_results r
      JOIN test_executions e ON r.execution_id = e.id
      JOIN test_suites s ON e.suite_id = s.id
      LEFT JOIN test_cases c ON r.case_id = c.id
    `;
    
    const params = [];
    let whereClause = '';
    
    if (execution_id) {
      whereClause = ' WHERE e.id = $1';
      params.push(execution_id);
    } else if (suite_name) {
      whereClause = ' WHERE s.name = $1';
      params.push(suite_name);
    }
    
    query += whereClause + ` ORDER BY r.created_at DESC LIMIT $${params.length + 1}`;
    params.push(limit);
    
    const result = await this.pool.query(query, params);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(result.rows, null, 2)
      }]
    };
  }

  async getTestSummary(args) {
    const { days = 7 } = args;
    
    const query = `
      SELECT * FROM test_summary 
      WHERE started_at >= NOW() - INTERVAL '${days} days'
      ORDER BY started_at DESC
    `;
    
    const result = await this.pool.query(query);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(result.rows, null, 2)
      }]
    };
  }

  async runSecurityScan(args) {
    const { path = '.', rules = 'auto' } = args;
    
    return new Promise((resolve, reject) => {
      const semgrep = spawn('semgrep', ['--config', rules, '--json', path], {
        stdio: 'pipe'
      });
      
      let output = '';
      semgrep.stdout.on('data', (data) => {
        output += data.toString();
      });
      
      semgrep.on('close', async (code) => {
        try {
          const results = JSON.parse(output);
          resolve({
            content: [{
              type: 'text',
              text: JSON.stringify(results, null, 2)
            }]
          });
        } catch (error) {
          reject(error);
        }
      });
    });
  }

  async generateTestReport(args) {
    const { execution_id, format = 'json' } = args;
    
    let query = `
      SELECT 
        s.name as suite_name,
        s.type,
        e.execution_name,
        e.status,
        e.started_at,
        e.completed_at,
        COUNT(r.id) as total_tests,
        COUNT(CASE WHEN r.status = 'passed' THEN 1 END) as passed,
        COUNT(CASE WHEN r.status = 'failed' THEN 1 END) as failed,
        COUNT(CASE WHEN r.status = 'skipped' THEN 1 END) as skipped,
        AVG(r.duration_ms) as avg_duration
      FROM test_executions e
      JOIN test_suites s ON e.suite_id = s.id
      LEFT JOIN test_results r ON e.id = r.execution_id
    `;
    
    if (execution_id) {
      query += ` WHERE e.id = $1`;
    }
    
    query += ` GROUP BY s.id, s.name, s.type, e.id, e.execution_name, e.status, e.started_at, e.completed_at`;
    
    const result = await this.pool.query(query, execution_id ? [execution_id] : []);
    
    const report = {
      summary: result.rows,
      generated_at: new Date().toISOString(),
      format: format
    };
    
    if (format === 'html') {
      const html = this.generateHTMLReport(report);
      return {
        content: [{
          type: 'text',
          text: html
        }]
      };
    }
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(report, null, 2)
      }]
    };
  }

  generateHTMLReport(report) {
    return `
<!DOCTYPE html>
<html>
<head>
  <title>Test Report</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; }
    .passed { color: green; }
    .failed { color: red; }
    .warning { color: orange; }
  </style>
</head>
<body>
  <h1>Test Report</h1>
  <p>Generated: ${report.generated_at}</p>
  
  <table>
    <thead>
      <tr>
        <th>Suite</th>
        <th>Type</th>
        <th>Status</th>
        <th>Total</th>
        <th>Passed</th>
        <th>Failed</th>
        <th>Skipped</th>
        <th>Avg Duration (ms)</th>
      </tr>
    </thead>
    <tbody>
      ${report.summary.map(row => `
        <tr>
          <td>${row.suite_name}</td>
          <td>${row.type}</td>
          <td class="${row.status}">${row.status}</td>
          <td>${row.total_tests}</td>
          <td class="passed">${row.passed}</td>
          <td class="failed">${row.failed}</td>
          <td>${row.skipped}</td>
          <td>${Math.round(row.avg_duration || 0)}</td>
        </tr>
      `).join('')}
    </tbody>
  </table>
</body>
</html>`;
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Test MCP server running on stdio');
  }
}

const server = new TestMCPServer();
server.run().catch(console.error);
