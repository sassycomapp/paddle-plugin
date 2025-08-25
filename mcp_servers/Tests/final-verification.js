#!/usr/bin/env node

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

console.log('🔍 Final Verification: snap-mcp-server Installation\n');

// Test 1: Check if server file exists
import { existsSync } from 'fs';
const serverPath = join(__dirname, '../snap-mcp-server.js');
console.log('✅ Server file exists:', existsSync(serverPath));

// Test 2: Check VS Code configuration
import { readFileSync } from 'fs';
const configPath = join(__dirname, '../../.vscode/mcp.json');
if (existsSync(configPath)) {
  const config = JSON.parse(readFileSync(configPath, 'utf8'));
  const snapConfig = config.mcpServers?.['snap-windows'];
  console.log('✅ VS Code configuration exists:', !!snapConfig);
  console.log('   Command:', snapConfig?.command);
  console.log('   Args:', snapConfig?.args);
}

// Test 3: Test server startup and basic functionality
console.log('\n🚀 Testing server startup...');
const server = spawn('node', [serverPath], { stdio: ['pipe', 'pipe', 'pipe'] });

let responses = [];
let errors = [];

server.stdout.on('data', (data) => {
  const lines = data.toString().split('\n').filter(line => line.trim());
  lines.forEach(line => {
    try {
      const parsed = JSON.parse(line);
      responses.push(parsed);
    } catch (e) {
      // Ignore non-JSON lines
    }
  });
});

server.stderr.on('data', (data) => {
  errors.push(data.toString());
});

// Send initialize request
const initRequest = {
  jsonrpc: '2.0',
  id: 1,
  method: 'initialize',
  params: {
    protocolVersion: '2024-11-05',
    capabilities: {},
    clientInfo: { name: 'verification', version: '1.0.0' }
  }
};

server.stdin.write(JSON.stringify(initRequest) + '\n');

// Send list tools request
const listToolsRequest = {
  jsonrpc: '2.0',
  id: 2,
  method: 'tools/list',
  params: {}
};

setTimeout(() => {
  server.stdin.write(JSON.stringify(listToolsRequest) + '\n');
}, 500);

setTimeout(() => {
  server.kill();
  
  console.log('\n📊 Verification Results:');
  
  // Check initialize response
  const initResponse = responses.find(r => r.id === 1);
  console.log('✅ Initialize response:', !!initResponse);
  if (initResponse) {
    console.log('   Server name:', initResponse.result?.serverInfo?.name);
    console.log('   Version:', initResponse.result?.serverInfo?.version);
  }
  
  // Check tools list
  const toolsResponse = responses.find(r => r.id === 2);
  console.log('✅ Tools list response:', !!toolsResponse);
  if (toolsResponse) {
    const tools = toolsResponse.result?.tools || [];
    console.log('   Available tools:', tools.map(t => t.name).join(', '));
    console.log('   Tool count:', tools.length);
  }
  
  if (errors.length > 0) {
    console.log('\n❌ Errors:');
    errors.forEach(error => console.log('   ', error.trim()));
  }
  
  const allPassed = initResponse && toolsResponse && toolsResponse.result?.tools?.length >= 3;
  
  console.log('\n🎯 Final Status:', allPassed ? 'SUCCESS' : 'FAILED');
  
  if (allPassed) {
    console.log('\n🎉 snap-mcp-server is successfully installed and ready to use!');
    console.log('\n📋 Available tools:');
    console.log('   • arrange_windows - Arrange windows in predefined layouts');
    console.log('   • snap_to_position - Snap specific windows to positions');
    console.log('   • manage_layouts - Save and apply window layouts');
  }
  
}, 2000);
