#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const chalk = require('chalk');

console.log(chalk.blue('🧪 Testing and Validation System - Final Verification\n'));

const projectRoot = __dirname;
const results = [];

function checkFile(filePath, description) {
  const fullPath = path.join(projectRoot, filePath);
  const exists = fs.existsSync(fullPath);
  results.push({
    description,
    status: exists ? '✅' : '❌',
    path: filePath
  });
  return exists;
}

function checkContent(filePath, content, description) {
  const fullPath = path.join(projectRoot, filePath);
  if (!fs.existsSync(fullPath)) {
    results.push({ description, status: '❌', path: filePath });
    return false;
  }
  
  const fileContent = fs.readFileSync(fullPath, 'utf8');
  const contains = fileContent.includes(content);
  results.push({
    description,
    status: contains ? '✅' : '❌',
    path: filePath
  });
  return contains;
}

// Test 1: Core Structure
console.log(chalk.yellow('📁 Checking core structure...'));
checkFile('package.json', 'Package configuration');
checkFile('podman-compose.yml', 'Podman compose configuration');
checkFile('Dockerfile.test', 'Test Dockerfile');
checkFile('README.md', 'Documentation');
checkFile('sql/init-test-db.sql', 'Database initialization');

// Test 2: Scripts and Tools
console.log(chalk.yellow('\n🔧 Checking scripts and tools...'));
checkFile('scripts/setup-podman.sh', 'Unix setup script');
checkFile('scripts/setup-podman.bat', 'Windows setup script');
checkFile('scripts/generate-report.js', 'Report generator');
checkFile('verify-installation.js', 'Installation verifier');

// Test 3: Testing Infrastructure
console.log(chalk.yellow('\n🧪 Checking testing infrastructure...'));
checkFile('src/tests/system.test.js', 'System tests');
checkFile('src/tests/integration.test.js', 'Integration tests');
checkFile('src/tests/test-runner.js', 'Test runner');
checkFile('.github/workflows/test.yml', 'GitHub Actions workflow');

// Test 4: MCP Server
console.log(chalk.yellow('\n🤖 Checking MCP server...'));
checkFile('src/mcp/test-mcp-server.js', 'MCP test server');

// Test 5: Configuration Content
console.log(chalk.yellow('\n⚙️ Checking configuration content...'));
checkContent('package.json', '"test:coverage"', 'Coverage script');
checkContent('package.json', '"podman:test"', 'Podman test script');
checkContent('package.json', '"report:generate"', 'Report generation script');
checkContent('.github/workflows/test.yml', 'semgrep', 'Security scanning');
checkContent('podman-compose.yml', 'postgres:15-alpine', 'PostgreSQL image');

// Test 6: Database Schema
console.log(chalk.yellow('\n🗄️ Checking database schema...'));
checkContent('sql/init-test-db.sql', 'CREATE TABLE IF NOT EXISTS test_suites', 'Test suites table');
checkContent('sql/init-test-db.sql', 'CREATE TABLE IF NOT EXISTS test_cases', 'Test cases table');
checkContent('sql/init-test-db.sql', 'CREATE TABLE IF NOT EXISTS test_executions', 'Test executions table');

// Display results
console.log(chalk.cyan('\n📊 Verification Results:'));
console.log('='.repeat(50));

let passed = 0;
let total = 0;

results.forEach(result => {
  console.log(`${result.status} ${result.description} (${result.path})`);
  if (result.status === '✅') passed++;
  total++;
});

console.log('='.repeat(50));
console.log(chalk.green(`✅ ${passed}/${total} checks passed`));

if (passed === total) {
  console.log(chalk.green.bold('\n🎉 All tests passed! The Testing and Validation System is ready to use.'));
  console.log(chalk.blue('\nNext steps:'));
  console.log('1. Run: npm install');
  console.log('2. Run: npm run podman:up');
  console.log('3. Run: npm test');
  console.log('4. Run: npm run test:integration');
} else {
  console.log(chalk.red.bold('\n❌ Some tests failed. Please check the missing components.'));
  process.exit(1);
}
