#!/usr/bin/env node

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Test the snap-mcp-server tools
console.log('Testing snap-mcp-server tools...');

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

// Test ListTools
const listToolsRequest = {
  jsonrpc: '2.0',
  id: 1,
  method: 'tools/list',
  params: {}
};

// Test CallTool - arrange_windows
const arrangeWindowsRequest = {
  jsonrpc: '2.0',
  id: 2,
  method: 'tools/call',
  params: {
    name: 'arrange_windows',
    arguments: {
      layout: '2x2'
    }
  }
};

// Send requests
server.stdin.write(JSON.stringify(listToolsRequest) + '\n');
setTimeout(() => {
  server.stdin.write(JSON.stringify(arrangeWindowsRequest) + '\n');
}, 100);

// Wait for responses
setTimeout(() => {
  server.kill();
  
  console.log('=== List Tools Response ===');
  const responses = output.split('\n').filter(line => line.trim());
  responses.forEach((response, index) => {
    try {
      const parsed = JSON.parse(response);
      console.log(`Response ${index + 1}:`, JSON.stringify(parsed, null, 2));
    } catch (e) {
      console.log(`Raw ${index + 1}:`, response);
    }
  });
  
  if (error) {
    console.error('Errors:', error);
  }
}, 3000);

server.on('exit', (code) => {
  console.log(`Server exited with code ${code}`);
});
