#!/usr/bin/env node

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Test the snap-mcp-server
console.log('Testing snap-mcp-server...');

const server = spawn('node', [join(__dirname, '../snap-mcp-server.js')], {
  stdio: ['pipe', 'pipe', 'pipe']
});

let output = '';
let error = '';

server.stdout.on('data', (data) => {
  output += data.toString();
});

server.stderr.on('data', (data) => {
  error += data.toString();
});

// Send initialize request
const initializeRequest = {
  jsonrpc: '2.0',
  id: 1,
  method: 'initialize',
  params: {
    protocolVersion: '2024-11-05',
    capabilities: {},
    clientInfo: {
      name: 'test-client',
      version: '1.0.0'
    }
  }
};

// Send the request
server.stdin.write(JSON.stringify(initializeRequest) + '\n');

// Wait for response
setTimeout(() => {
  server.kill();
  
  if (output) {
    console.log('✅ Server responded successfully');
    console.log('Response:', output);
  } else if (error) {
    console.error('❌ Server error:', error);
  } else {
    console.log('⚠️  No response received');
  }
}, 2000);

// Handle server exit
server.on('exit', (code) => {
  console.log(`Server exited with code ${code}`);
});
