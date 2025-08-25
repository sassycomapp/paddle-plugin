#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');

// Test configuration
const mcpConfig = {
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
    "env": {}
  },
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": process.env.GITHUB_PERSONAL_ACCESS_TOKEN || ""
    }
  },
  "postgres": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-postgres"],
    "env": {
      "DATABASE_URL": process.env.DATABASE_URL || ""
    }
  },
  "braveSearch": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
    "env": {
      "BRAVE_API_KEY": process.env.BRAVE_API_KEY || ""
    }
  },
  "fetch": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-fetch"],
    "env": {}
  }
};

function testMcpServer(serverName, config) {
  return new Promise((resolve) => {
    console.log(`\n🧪 Testing ${serverName}...`);
    
    const child = spawn(config.command, config.args, {
      env: { ...process.env, ...config.env },
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 10000
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    child.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    child.on('error', (error) => {
      console.log(`❌ ${serverName}: Failed to start - ${error.message}`);
      resolve({ name: serverName, status: 'error', error: error.message });
    });

    child.on('exit', (code) => {
      if (code === 0) {
        console.log(`✅ ${serverName}: Started successfully`);
        resolve({ name: serverName, status: 'success', stdout, stderr });
      } else {
        console.log(`⚠️  ${serverName}: Exited with code ${code}`);
        resolve({ name: serverName, status: 'exit', code, stdout, stderr });
      }
    });

    // Send initialize request
    setTimeout(() => {
      const initRequest = {
        jsonrpc: '2.0',
        id: 1,
        method: 'initialize',
        params: {
          protocolVersion: '2024-11-05',
          capabilities: {},
          clientInfo: { name: 'test-client', version: '1.0.0' }
        }
      };
      
      try {
        child.stdin.write(JSON.stringify(initRequest) + '\n');
      } catch (e) {
        // Ignore write errors
      }
    }, 1000);

    // Kill after timeout
    setTimeout(() => {
      child.kill();
    }, 8000);
  });
}

async function runTests() {
  console.log('🔍 Starting MCP Server Tests...\n');
  
  const results = [];
  
  for (const [serverName, config] of Object.entries(mcpConfig)) {
    const result = await testMcpServer(serverName, config);
    results.push(result);
  }
  
  console.log('\n📊 Test Results Summary:');
  console.log('========================');
  
  results.forEach(result => {
    const icon = result.status === 'success' ? '✅' : 
                 result.status === 'error' ? '❌' : '⚠️';
    console.log(`${icon} ${result.name}: ${result.status}`);
    if (result.error) {
      console.log(`   Error: ${result.error}`);
    }
  });
  
  // Check missing environment variables
  console.log('\n🔐 Environment Variables Check:');
  console.log('================================');
  
  const requiredEnvVars = {
    'GITHUB_PERSONAL_ACCESS_TOKEN': 'github',
    'DATABASE_URL': 'postgres',
    'BRAVE_API_KEY': 'braveSearch'
  };
  
  for (const [envVar, server] of Object.entries(requiredEnvVars)) {
    const value = process.env[envVar];
    console.log(`${value ? '✅' : '❌'} ${envVar}: ${value ? 'Set' : 'Missing'} (${server})`);
  }
}

// Load environment variables
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

runTests().catch(console.error);
