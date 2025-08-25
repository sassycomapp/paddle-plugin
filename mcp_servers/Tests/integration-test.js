#!/usr/bin/env node

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Integration test with actual MCP protocol
console.log('🔧 Running integration test with MCP protocol...\n');

const server = spawn('node', [join(__dirname, '../snap-mcp-server.js')], {
  stdio: ['pipe', 'pipe', 'pipe']
});

let responses = [];
let errors = [];

server.stdout.on('data', (data) => {
  const lines = data.toString().split('\n').filter(line => line.trim());
  lines.forEach(line => {
    try {
      const parsed = JSON.parse(line);
      responses.push(parsed);
    } catch (e) {
      console.log('Raw:', line);
    }
  });
});

server.stderr.on('data', (data) => {
  errors.push(data.toString());
});

// Test sequence
const testSequence = [
  {
    name: 'Initialize',
    request: {
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: { name: 'integration-test', version: '1.0.0' }
      }
    },
    validate: (response) => response?.result?.serverInfo?.name === 'snap-windows'
  },
  {
    name: 'List Tools',
    request: {
      jsonrpc: '2.0',
      id: 2,
      method: 'tools/list',
      params: {}
    },
    validate: (response) => response?.result?.tools?.length >= 3
  },
  {
    name: 'Test arrange_windows',
    request: {
      jsonrpc: '2.0',
      id: 3,
      method: 'tools/call',
      params: {
        name: 'arrange_windows',
        arguments: { layout: 'left-right' }
      }
    },
    validate: (response) => !response?.error
  },
  {
    name: 'Test snap_to_position',
    request: {
      jsonrpc: '2.0',
      id: 4,
      method: 'tools/call',
      params: {
        name: 'snap_to_position',
        arguments: { windowTitle: 'Notepad', position: 'right' }
      }
    },
    validate: (response) => !response?.error
  },
  {
    name: 'Test manage_layouts',
    request: {
      jsonrpc: '2.0',
      id: 5,
      method: 'tools/call',
      params: {
        name: 'manage_layouts',
        arguments: { action: 'save', name: 'integration-test' }
      }
    },
    validate: (response) => !response?.error
  }
];

async function runTests() {
  let passed = 0;
  let total = testSequence.length;

  for (let i = 0; i < testSequence.length; i++) {
    const test = testSequence[i];
    console.log(`🧪 ${i + 1}/${total}: ${test.name}`);
    
    server.stdin.write(JSON.stringify(test.request) + '\n');
    
    // Wait for response
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const response = responses.find(r => r.id === test.request.id);
    if (response && test.validate(response)) {
      console.log(`   ✅ ${test.name} passed`);
      passed++;
    } else {
      console.log(`   ❌ ${test.name} failed`);
      if (response?.error) {
        console.log(`      Error: ${JSON.stringify(response.error)}`);
      }
    }
  }

  console.log('\n📊 Integration Test Results:');
  console.log(`   Passed: ${passed}/${total}`);
  console.log(`   Success Rate: ${(passed/total*100).toFixed(1)}%`);

  if (errors.length > 0) {
    console.log('\n❌ Errors:');
    errors.forEach(error => console.log(`   ${error}`));
  }

  server.kill();
  
  if (passed === total) {
    console.log('\n🎉 All integration tests passed! The snap-mcp-server is fully functional.');
  }
  
  return passed === total;
}

// Run the integration test
setTimeout(() => {
  runTests().catch(console.error);
}, 1000);
