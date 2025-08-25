#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const COLORS = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
};

function log(message, color = 'white') {
  console.log(`${COLORS[color]}${message}${COLORS.reset}`);
}

function exec(command, options = {}) {
  try {
    return execSync(command, { 
      stdio: 'inherit',
      cwd: path.join(__dirname, '..'),
      ...options 
    });
  } catch (error) {
    log(`Error executing: ${command}`, 'red');
    throw error;
  }
}

function checkNodeVersion() {
  const version = process.version;
  const major = parseInt(version.slice(1).split('.')[0]);
  if (major < 18) {
    log(`❌ Node.js 18+ required. Current: ${version}`, 'red');
    process.exit(1);
  }
  log(`✅ Node.js ${version} detected`, 'green');
}

function checkNpm() {
  try {
    const version = execSync('npm --version', { encoding: 'utf8' }).trim();
    log(`✅ npm ${version} detected`, 'green');
    return true;
  } catch {
    log('❌ npm not found', 'red');
    return false;
  }
}

function checkDependencies() {
  try {
    const version = execSync('ag2 --version', { encoding: 'utf8' }).trim();
    log(`✅ ag2 ${version} detected`, 'green');
    return true;
  } catch {
    log('❌ ag2 not found', 'yellow');
    return false;
  }
}

function installAg2() {
  log('📦 Installing ag2', 'cyan');
  exec('npm install -g @modelcontextprotocol/ag2');
}

function installMcpInspector() {
  log('📦 Installing MCP Inspector...', 'cyan');
  exec('npm install -g @modelcontextprotocol/inspector');
}

function installMcpServers() {
  const servers = [
    '@modelcontextprotocol/server-filesystem',
    '@modelcontextprotocol/server-github',
    '@modelcontextprotocol/server-postgres',
    '@modelcontextprotocol/server-brave-search'
  ];

  log('📦 Installing MCP servers...', 'cyan');
  servers.forEach(server => {
    log(`  Installing ${server}...`, 'blue');
    exec(`npm install -g ${server}`);
  });
}

function createVscodeConfig() {
  const configPath = '.vscode/mcp.json';
  const config = {
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "."],
        env: {}
      },
      github: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-github"],
        env: {
          GITHUB_PERSONAL_ACCESS_TOKEN: process.env.GITHUB_PERSONAL_ACCESS_TOKEN || ""
        }
      },
      postgres: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-postgres"],
        env: {
          DATABASE_URL: process.env.DATABASE_URL || ""
        }
      },
      braveSearch: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-brave-search"],
        env: {
          BRAVE_API_KEY: process.env.BRAVE_API_KEY || ""
        }
      }
    }
  };

  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  log(`✅ Created VS Code MCP configuration at ${configPath}`, 'green');
}

function showSummary() {
  log('\n🎉 MCP Installer Setup Complete!', 'green');
  log('=================================', 'green');
  log('\n📋 Available commands:', 'cyan');
  log('  node mcp_servers/manage-mcp-servers.js list     - List all MCP servers');
  log('  node mcp_servers/manage-mcp-servers.js status   - Show server status');
  log('  node mcp_servers/manage-mcp-servers.js start    - Start all servers');
  log('  node mcp_servers/manage-mcp-servers.js stop     - Stop all servers');
  log('  node mcp_servers/manage-mcp-servers.js restart  - Restart all servers');
  log('  node mcp_servers/manage-mcp-servers.js logs     - View all logs');
  log('\n🌐 MCP Inspector:', 'cyan');
  log('  npx @modelcontextprotocol/inspector');
  log('  Open http://localhost:6274 in your browser');
  log('\n📁 Configuration files:', 'cyan');
  log('  .vscode/mcp.json - VS Code MCP configuration');
  log('\n🔧 Environment variables to set:', 'cyan');
  log('  GITHUB_PERSONAL_ACCESS_TOKEN - For GitHub integration');
  log('  DATABASE_URL - For PostgreSQL server');
  log('  BRAVE_API_KEY - For Brave search server');
  log('');
}

function main() {
  log('🚀 MCP Installer - Complete Setup', 'cyan');
  log('=================================', 'cyan');
  log('');

  checkNodeVersion();
  checkNpm();
  
  if (!checkDependencies()) {
    installAg2();
  }
  
  installMcpInspector();
  installMcpServers();
  createVscodeConfig();
  
  showSummary();
}

// Handle command line arguments
const args = process.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) {
  log('Usage: node install-mcp-complete.js [options]', 'cyan');
  log('Options:', 'white');
  log('  --help, -h     Show this help message');
  log('  --skip-"..."     Skip "..." installation');
  log('  --skip-servers Skip MCP server installation');
  process.exit(0);
}

main();
