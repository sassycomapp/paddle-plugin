#!/usr/bin/env node

/**
 * MCP Server Installer Script
 * This script helps install and configure MCP servers
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const MCP_SERVERS = {
  'filesystem': {
    package: '@modelcontextprotocol/server-filesystem',
    description: 'File system access server',
    args: ['.', '/tmp']
  },
  'github': {
    package: '@modelcontextprotocol/server-github',
    description: 'GitHub integration server',
    env: ['GITHUB_PERSONAL_ACCESS_TOKEN']
  },
  'postgres': {
    package: '@modelcontextprotocol/server-postgres',
    description: 'PostgreSQL database server',
    env: ['DATABASE_URL']
  },
  'sqlite': {
    package: '@modelcontextprotocol/server-sqlite',
    description: 'SQLite database server',
    args: ['~/database.db']
  },
  'fetch': {
    package: '@modelcontextprotocol/server-fetch',
    description: 'HTTP fetch server'
  },
  'brave-search': {
    package: '@modelcontextprotocol/server-brave-search',
    description: 'Brave search integration',
    env: ['BRAVE_API_KEY']
  }
};

function installMcpServer(serverName) {
  const server = MCP_SERVERS[serverName];
  if (!server) {
    console.error(`Unknown MCP server: ${serverName}`);
    console.log('Available servers:', Object.keys(MCP_SERVERS).join(', '));
    process.exit(1);
  }

  console.log(`Installing ${serverName}: ${server.description}`);
  
  try {
    // Install the package globally
    execSync(`npm install -g ${server.package}`, { stdio: 'inherit' });
    
    // Update MCP configuration
    updateMcpConfig(serverName, server);
    
    console.log(`✅ Successfully installed ${serverName}`);
  } catch (error) {
    console.error(`❌ Failed to install ${serverName}:`, error.message);
    process.exit(1);
  }
}

function updateMcpConfig(serverName, server) {
  const configPath = path.join('.vscode', 'mcp.json');
  let config = { mcpServers: {} };
  
  if (fs.existsSync(configPath)) {
    config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  }

  config.mcpServers[serverName] = {
    command: 'npx',
    args: ['-y', server.package, ...(server.args || [])],
    env: {}
  };

  if (server.env) {
    server.env.forEach(envVar => {
      config.mcpServers[serverName].env[envVar] = process.env[envVar] || '';
    });
  }

  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  console.log(`Updated ${configPath} with ${serverName} configuration`);
}

function listAvailableServers() {
  console.log('\n📋 Available MCP Servers:');
  Object.entries(MCP_SERVERS).forEach(([name, server]) => {
    console.log(`  ${name}: ${server.description}`);
  });
  console.log('\nUsage: node install-mcp-server.js <server-name>');
}

// CLI handling
const serverName = process.argv[2];
if (!serverName) {
  listAvailableServers();
  process.exit(0);
}

installMcpServer(serverName);
