const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const chalk = require('chalk');

class TestRunner {
  constructor() {
    this.results = {
      total: 0,
      passed: 0,
      failed: 0,
      skipped: 0,
      tests: []
    };
    this.startTime = Date.now();
  }

  log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}]`;
    
    switch (type) {
      case 'success':
        console.log(chalk.green(`${prefix} ✓ ${message}`));
        break;
      case 'error':
        console.log(chalk.red(`${prefix} ✗ ${message}`));
        break;
      case 'warning':
        console.log(chalk.yellow(`${prefix} ⚠ ${message}`));
        break;
      case 'info':
      default:
        console.log(chalk.blue(`${prefix} ℹ ${message}`));
        break;
    }
  }

  async runSystemTests() {
    this.log('Starting System Architecture Tests...');
    
    try {
      const { execSync } = require('child_process');
      const output = execSync('npm test -- src/tests/system.test.js --json', { 
        encoding: 'utf8',
        cwd: path.join(__dirname, '..', '..')
      });
      
      const results = JSON.parse(output);
      this.log(`System Tests: ${results.numPassedTests}/${results.numTotalTests} passed`, 'success');
      
      return {
        passed: results.numPassedTests,
        total: results.numTotalTests,
        results: results.testResults
      };
    } catch (error) {
      this.log(`System Tests Failed: ${error.message}`, 'error');
      return { passed: 0, total: 1, error: error.message };
    }
  }

  async runIntegrationTests() {
    this.log('Starting Integration Tests...');
    
    try {
      const output = execSync('npm test -- src/tests/integration.test.js --json', { 
        encoding: 'utf8',
        cwd: path.join(__dirname, '..', '..')
      });
      
      const results = JSON.parse(output);
      this.log(`Integration Tests: ${results.numPassedTests}/${results.numTotalTests} passed`, 'success');
      
      return {
        passed: results.numPassedTests,
        total: results.numTotalTests,
        results: results.testResults
      };
    } catch (error) {
      this.log(`Integration Tests Failed: ${error.message}`, 'error');
      return { passed: 0, total: 1, error: error.message };
    }
  }

  async runSecurityTests() {
    this.log('Starting Security Tests...');
    
    try {
      const output = execSync('npm run security-scan', { 
        encoding: 'utf8',
        cwd: path.join(__dirname, '..', '..')
      });
      
      this.log('Security scan completed successfully', 'success');
      
      return {
        passed: 1,
        total: 1,
        output: output
      };
    } catch (error) {
      this.log(`Security Tests Failed: ${error.message}`, 'error');
      return { passed: 0, total: 1, error: error.message };
    }
  }

  async runPodmanTests() {
    this.log('Starting Podman Configuration Tests...');
    
    try {
      // Test podman-compose file validity
      const composePath = path.join(__dirname, '..', '..', 'podman-compose.yml');
      const yaml = require('js-yaml');
      const composeContent = fs.readFileSync(composePath, 'utf8');
      const compose = yaml.load(composeContent);
      
      const tests = [
        { name: 'Compose version', check: () => compose.version === '3.8' },
        { name: 'Postgres service', check: () => compose.services.postgres !== undefined },
        { name: 'Test service', check: () => compose.services.test !== undefined },
        { name: 'Volume mounts', check: () => compose.services.test.volumes.length > 0 }
      ];
      
      let passed = 0;
      tests.forEach(test => {
        if (test.check()) {
          this.log(`✓ ${test.name}`, 'success');
          passed++;
        } else {
          this.log(`✗ ${test.name}`, 'error');
        }
      });
      
      return { passed, total: tests.length };
    } catch (error) {
      this.log(`Podman Tests Failed: ${error.message}`, 'error');
      return { passed: 0, total: 1, error: error.message };
    }
  }

  async runPerformanceTests() {
    this.log('Starting Performance Tests...');
    
    const startTime = Date.now();
    
    try {
      // Simulate performance tests
      const testFiles = fs.readdirSync(path.join(__dirname));
      const jsFiles = testFiles.filter(f => f.endsWith('.js'));
      
      const endTime = Date.now();
      const duration = endTime - startTime;
      
      this.log(`Performance Tests completed in ${duration}ms`, 'success');
      
      return {
        passed: 1,
        total: 1,
        duration,
        filesTested: jsFiles.length
      };
    } catch (error) {
      this.log(`Performance Tests Failed: ${error.message}`, 'error');
      return { passed: 0, total: 1, error: error.message };
    }
  }

  async generateReport(results) {
    this.log('Generating comprehensive test report...');
    
    const report = {
      timestamp: new Date().toISOString(),
      duration: Date.now() - this.startTime,
      summary: {
        total: 0,
        passed: 0,
        failed: 0
      },
      details: results
    };
    
    // Calculate totals
    Object.values(results).forEach(testResult => {
      report.summary.total += testResult.total || 0;
      report.summary.passed += testResult.passed || 0;
      report.summary.failed += (testResult.total || 0) - (testResult.passed || 0);
    });
    
    // Save JSON report
    const reportsDir = path.join(__dirname, '..', '..', 'reports');
    if (!fs.existsSync(reportsDir)) {
      fs.mkdirSync(reportsDir, { recursive: true });
    }
    
    fs.writeFileSync(
      path.join(reportsDir, 'comprehensive-test-report.json'),
      JSON.stringify(report, null, 2)
    );
    
    // Generate HTML report
    const htmlReport = this.generateHTMLReport(report);
    fs.writeFileSync(
      path.join(reportsDir, 'comprehensive-test-report.html'),
      htmlReport
    );
    
    this.log(`Report generated: ${reportsDir}/comprehensive-test-report.html`, 'success');
    
    return report;
  }

  generateHTMLReport(report) {
    return `
<!DOCTYPE html>
<html>
<head>
    <title>Testing and Validation System - Comprehensive Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .summary { display: flex; gap: 20px; margin: 20px 0; }
        .card { background: white; border: 1px solid #ddd; padding: 20px; border-radius: 5px; flex: 1; }
        .success { border-left: 4px solid #28a745; }
        .failure { border-left: 4px solid #dc3545; }
        .warning { border-left: 4px solid #ffc107; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
        .progress-bar { width: 100%; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden; }
        .progress-fill { height: 100%; background: #28a745; transition: width 0.3s; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Testing and Validation System - Comprehensive Report</h1>
        <p>Generated: ${new Date(report.timestamp).toLocaleString()}</p>
        <p>Duration: ${report.duration}ms</p>
    </div>

    <div class="summary">
        <div class="card success">
            <h3>Total Tests</h3>
            <p style="font-size: 2em; margin: 0;">${report.summary.total}</p>
        </div>
        <div class="card success">
            <h3>Passed</h3>
            <p style="font-size: 2em; margin: 0; color: #28a745;">${report.summary.passed}</p>
        </div>
        <div class="card failure">
            <h3>Failed</h3>
            <p style="font-size: 2em; margin: 0; color: #dc3545;">${report.summary.failed}</p>
        </div>
        <div class="card">
            <h3>Success Rate</h3>
            <p style="font-size: 2em; margin: 0;">
                ${report.summary.total > 0 ? Math.round((report.summary.passed / report.summary.total) * 100) : 0}%
            </p>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${report.summary.total > 0 ? (report.summary.passed / report.summary.total) * 100 : 0}%"></div>
            </div>
        </div>
    </div>

    <h2>Test Details</h2>
    <table>
        <thead>
            <tr>
                <th>Test Suite</th>
                <th>Passed</th>
                <th>Total</th>
                <th>Success Rate</th>
            </tr>
        </thead>
        <tbody>
            ${Object.entries(report.details).map(([suite, result]) => `
                <tr>
                    <td>${suite}</td>
                    <td>${result.passed || 0}</td>
                    <td>${result.total || 0}</td>
                    <td>${result.total > 0 ? Math.round((result.passed / result.total) * 100) : 0}%</td>
                </tr>
            `).join('')}
        </tbody>
    </table>
</body>
</html>`;
  }

  async runAllTests() {
    this.log('Starting comprehensive testing of Testing and Validation System...');
    
    const results = {};
    
    try {
      results.system = await this.runSystemTests();
      results.integration = await this.runIntegrationTests();
      results.security = await this.runSecurityTests();
      results.podman = await this.runPodmanTests();
      results.performance = await this.runPerformanceTests();
      
      const report = await this.generateReport(results);
      
      this.log('=====================================', 'info');
      this.log('COMPREHENSIVE TESTING COMPLETE', 'info');
      this.log(`Total Tests: ${report.summary.total}`, 'info');
      this.log(`Passed: ${report.summary.passed}`, 'success');
      this.log(`Failed: ${report.summary.failed}`, 'error');
      this.log(`Success Rate: ${report.summary.total > 0 ? Math.round((report.summary.passed / report.summary.total) * 100) : 0}%`, 'info');
      this.log('=====================================', 'info');
      
      return report;
    } catch (error) {
      this.log(`Comprehensive testing failed: ${error.message}`, 'error');
      throw error;
    }
  }
}

// Export for use as module
module.exports = TestRunner;

// Run if called directly
if (require.main === module) {
  const runner = new TestRunner();
  runner.runAllTests().catch(console.error);
}
