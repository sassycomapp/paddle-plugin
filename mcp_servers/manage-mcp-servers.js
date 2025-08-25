#!/usr/bin/env node

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

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

function showHelp() {
  log('\n🤖 MCP Server Management Tool', 'cyan');
  log('================================', 'cyan');
  log('\nUsage: node manage-mcp-servers.js [command] [options]');
  log('\nCommands:');
  log('  start [server]     - Start all or specific MCP servers');
  log('  stop [server]      - Stop all or specific MCP servers');
  log('  restart [server]   - Restart all or specific MCP servers');
  log('  status             - Show status of all MCP servers');
  log('  logs [server]      - Show logs for all or specific servers');
  log('  install            - Install new MCP servers via "..."');
  log('  list               - List available MCP servers');
  log('  config             - Show "..." configuration');
  log('\nExamples:');
  log('  node manage-mcp-servers.js start');
  log('  node manage-mcp-servers.js start filesystem');
  log('  node manage-mcp-servers.js stop github');
  log('  node manage-mcp-servers.js logs llm-router-mcp');
  log('');
}

function listServers() {
  log('\n📋 Available MCP Servers:', 'cyan');
  log('=========================', 'cyan');
  
  const config = JSON.parse(fs.readFileSync(path.join(__dirname, 'mcp-servers-config.json'), 'utf8'));
  config.apps.forEach(app => {
    const status = getServerStatus(app.name);
    log(`  ${app.name.padEnd(20)} - ${status}`, status === 'online' ? 'green' : 'red');
  });
}

function getServerStatus(serverName) {
  try {
    const result = execSync(`ag2 jlist`, { encoding: 'utf8' });
    const processes = JSON.parse(result);
    const server = processes.find(p => p.name === serverName);
    return server ? server.pm2_env.status : 'stopped';
  } catch {
    return 'unknown';
  }
}

function showStatus() {
  log('\n📊 MCP Server Status:', 'cyan');
  log('=====================', 'cyan');
  exec('ag2 list');
}

function startServers(serverName = null) {
  if (serverName) {
    log(`🚀 Starting ${serverName}...`, 'green');
    exec(`ag2 start ${"./mcp-servers-config.json"} --only ${serverName}`);
  } else {
    log('🚀 Starting all MCP servers...', 'green');
    exec(`ag2 start ${"./mcp-servers-config.json"}`);
  }
}

function stopServers(serverName = null) {
  if (serverName) {
    log(`🛑 Stopping ${serverName}...`, 'red');
    exec(`ag2 stop ${serverName}`);
  } else {
    log('🛑 Stopping all MCP servers...', 'red');
    exec(`ag2 stop ${"./mcp-servers-config.json"}`);
  }
}

function restartServers(serverName = null) {
  if (serverName) {
    log(`🔄 Restarting ${serverName}...`, 'yellow');
    exec(`ag2 restart ${serverName}`);
  } else {
    log('🔄 Restarting all MCP servers...', 'yellow');
    exec(`ag2 restart ${"./mcp-servers-config.json"}`);
  }
}

function showLogs(serverName = null) {
  if (serverName) {
    log(`📋 Showing logs for ${serverName}...`, 'blue');
    exec(`ag2 logs ${serverName} --lines 50`);
  } else {
    log('📋 Showing logs for all MCP servers...', 'blue');
    exec(`"..." logs --lines 50`);
  }
}

function installMcpServers() {
  log('📦 Installing MCP servers via "..."...', 'cyan');
  exec(`ag2 start ${"./mcp-servers-config.json"}`);
}

function showConfig() {
  log('\n⚙️ "..." Configuration:', 'cyan');
  log('====================', 'cyan');
  const config = JSON.parse(fs.readFileSync(path.join(__dirname, 'mcp-servers-config.json'), 'utf8'));
  console.log(JSON.stringify(config, null, 2));
}

// Main execution
const [,, command, ...args] = process.argv;

if (!command || command === 'help') {
  showHelp();
  process.exit(0);
}

switch (command.toLowerCase()) {
  case 'start':
    startServers(args[0]);
    break;
  case 'stop':
    stopServers(args[0]);
    break;
  case 'restart':
    restartServers(args[0]);
    break;
  case 'status':
    showStatus();
    break;
  case 'logs':
    showLogs(args[0]);
    break;
  case 'install':
    installMcpServers();
    break;
  case 'list':
    listServers();
    break;
  case 'config':
    showConfig();
    break;
  default:
    log(`Unknown command: ${command}`, 'red');
    showHelp();
    process.exit(1);
}
