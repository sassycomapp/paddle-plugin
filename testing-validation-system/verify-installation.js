#!/usr/bin/env node

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');

async function verifyInstallation() {
  console.log('🔍 Verifying Testing and Validation System Installation...\n');

  const checks = [
    { name: 'Node.js', command: 'node --version', required: true },
    { name: 'npm', command: 'npm --version', required: true },
    { name: 'PostgreSQL', command: 'pg_isready --version', required: true },
    { name: 'Podman', command: 'podman --version', required: true },
    { name: 'podman-compose', command: 'podman-compose --version', required: true },
    { name: 'Python', command: 'python3 --version', required: false },
    { name: 'Semgrep', command: 'semgrep --version', required: false }
  ];

  const results = [];

  for (const check of checks) {
    try {
      const output = execSync(check.command, { encoding: 'utf8', stdio: 'pipe' });
      results.push({ ...check, status: '✅', output: output.trim() });
      console.log(`✅ ${check.name}: ${output.trim()}`);
    } catch (error) {
      if (check.required) {
        results.push({ ...check, status: '❌', error: error.message });
        console.log(`❌ ${check.name}: Required but not found`);
      } else {
        results.push({ ...check, status: '⚠️', error: error.message });
        console.log(`⚠️ ${check.name}: Optional - ${error.message}`);
      }
    }
  }

  console.log('\n📁 Checking file structure...');
  
  const requiredFiles = [
    'package.json',
    'podman-compose.yml',
    'sql/init-test-db.sql',
    'scripts/setup-podman.sh',
    'scripts/setup-podman.bat',
    'scripts/generate-report.js',
    'src/mcp/test-mcp-server.js',
    'README.md'
  ];

  for (const file of requiredFiles) {
    try {
      await fs.access(path.join(__dirname, file));
      console.log(`✅ ${file}`);
    } catch (error) {
      console.log(`❌ ${file}: Missing`);
    }
  }

  console.log('\n🧪 Running basic tests...');
  
  try {
    execSync('npm test -- --passWithNoTests', { stdio: 'pipe' });
    console.log('✅ Basic test execution successful');
  } catch (error) {
    console.log('⚠️ Basic test execution failed (expected if no tests written yet)');
  }

  console.log('\n📊 Installation Summary:');
  const failedRequired = results.filter(r => r.status === '❌' && r.required);
  
  if (failedRequired.length === 0) {
    console.log('✅ All required components are installed!');
    console.log('\n🚀 Next steps:');
    console.log('1. Run: npm install');
    console.log('2. Run: ./scripts/setup-podman.sh (Linux/macOS) or scripts\\setup-podman.bat (Windows)');
    console.log('3. Run: npm test');
  } else {
    console.log('❌ Missing required components:');
    failedRequired.forEach(r => console.log(`   - ${r.name}`));
    console.log('\nPlease install the missing components before proceeding.');
  }

  // Create verification report
  const report = {
    timestamp: new Date().toISOString(),
    checks: results,
    status: failedRequired.length === 0 ? 'SUCCESS' : 'INCOMPLETE'
  };

  await fs.writeFile(
    path.join(__dirname, 'reports/installation-verification.json'),
    JSON.stringify(report, null, 2)
  );

  console.log('\n📄 Verification report saved to: reports/installation-verification.json');
}

// Create reports directory if it doesn't exist
const reportsDir = path.join(__dirname, 'reports');
fs.mkdir(reportsDir, { recursive: true }).then(() => {
  verifyInstallation().catch(console.error);
});
