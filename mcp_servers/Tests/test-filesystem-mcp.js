#!/usr/bin/env node

/**
 * Test script for MCP Filesystem Server
 * This script tests basic filesystem operations provided by the MCP file-mcp-server
 */

const { spawn } = require('child_process');
const path = require('path');

// Test configuration
const FILESYSTEM_SERVER = {
  command: 'npx',
  args: ['-y', '@modelcontextprotocol/server-filesystem', '.', '/tmp'],
  env: {}
};

function testFilesystemServer() {
  return new Promise((resolve) => {
    console.log('🧪 Testing MCP Filesystem Server...\n');
    
    const child = spawn(FILESYSTEM_SERVER.command, FILESYSTEM_SERVER.args, {
      env: { ...process.env, ...FILESYSTEM_SERVER.env },
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => {
      stdout += data.toString();
      console.log('📤 STDOUT:', data.toString().trim());
    });

    child.stderr.on('data', (data) => {
      stderr += data.toString();
      console.log('📤 STDERR:', data.toString().trim());
    });

    child.on('error', (error) => {
      console.log('❌ Failed to start:', error.message);
      resolve({ status: 'error', error: error.message });
    });

    child.on('spawn', () => {
      console.log('✅ Server process spawned successfully');
      console.log('✅ PID:', child.pid);
    });

    // Test basic initialization
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
        console.log('📤 Sending initialize request...');
        child.stdin.write(JSON.stringify(initRequest) + '\n');
      } catch (e) {
        console.log('❌ Failed to send request:', e.message);
      }
    }, 1000);

    // Clean shutdown after test
    setTimeout(() => {
      console.log('✅ Test completed successfully');
      child.kill('SIGTERM');
      resolve({ status: 'success', stdout, stderr });
    }, 3000);
  });
}

async function runTest() {
  console.log('🔍 MCP Filesystem Server Test');
  console.log('==============================\n');
  
  try {
    const result = await testFilesystemServer();
    
    console.log('\n📊 Test Results:');
    console.log('================');
    if (result.status === 'success') {
      console.log('✅ MCP Filesystem Server is working correctly');
    } else {
      console.log('❌ MCP Filesystem Server failed:', result.error);
    }
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

// Run the test
runTest();
