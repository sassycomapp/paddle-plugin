#!/usr/bin/env node

import { spawn } from 'child_process';
import path from 'path';

// Test the MCP server
console.log('Testing Agent Memory MCP Server...');

const server = spawn('node', ['index.js'], {
  cwd: path.dirname(new URL(import.meta.url).pathname),
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

// Test initialization
setTimeout(() => {
  const initRequest = {
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
  
  server.stdin.write(JSON.stringify(initRequest) + '\n');
}, 100);

// Test list tools
setTimeout(() => {
  const listToolsRequest = {
    jsonrpc: '2.0',
    id: 2,
    method: 'tools/list',
    params: {}
  };
  
  server.stdin.write(JSON.stringify(listToolsRequest) + '\n');
}, 200);

// Test store episodic memory
setTimeout(() => {
  const storeMemoryRequest = {
    jsonrpc: '2.0',
    id: 3,
    method: 'tools/call',
    params: {
      name: 'store_episodic_memory',
      arguments: {
        agent_id: 'test-agent',
        session_id: 'test-session-1',
        context: {
          event: 'test_memory',
          description: 'This is a test memory',
          data: { key: 'value' }
        },
        tags: ['test', 'memory']
      }
    }
  };
  
  server.stdin.write(JSON.stringify(storeMemoryRequest) + '\n');
}, 300);

// Test retrieve memories
setTimeout(() => {
  const retrieveMemoryRequest = {
    jsonrpc: '2.0',
    id: 4,
    method: 'tools/call',
    params: {
      name: 'retrieve_episodic_memory',
      arguments: {
        agent_id: 'test-agent',
        limit: 5
      }
    }
  };
  
  server.stdin.write(JSON.stringify(retrieveMemoryRequest) + '\n');
}, 400);

// Close server after tests
setTimeout(() => {
  server.kill();
  console.log('Test completed!');
  console.log('Output:', output);
  if (error) console.log('Error:', error);
}, 1000);

server.on('close', (code) => {
  console.log(`Server exited with code ${code}`);
});
