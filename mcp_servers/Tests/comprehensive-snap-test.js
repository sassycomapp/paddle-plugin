#!/usr/bin/env node

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { promises as fs } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class SnapMCPTester {
  constructor() {
    this.serverPath = join(__dirname, '../snap-mcp-server.js');
    this.server = null;
    this.responses = [];
    this.errors = [];
  }

  async startServer() {
    console.log('🚀 Starting snap-mcp-server...');
    return new Promise((resolve, reject) => {
      this.server = spawn('node', [this.serverPath], {
        stdio: ['pipe', 'pipe', 'pipe']
      });

      this.server.stdout.on('data', (data) => {
        const lines = data.toString().split('\n').filter(line => line.trim());
        lines.forEach(line => {
          try {
            const parsed = JSON.parse(line);
            this.responses.push(parsed);
            console.log('📥 Response:', JSON.stringify(parsed, null, 2));
          } catch (e) {
            console.log('📄 Raw output:', line);
          }
        });
      });

      this.server.stderr.on('data', (data) => {
        const error = data.toString();
        this.errors.push(error);
        console.error('❌ Error:', error);
      });

      // Give server time to start
      setTimeout(resolve, 1000);
    });
  }

  async sendRequest(request) {
    return new Promise((resolve) => {
      this.server.stdin.write(JSON.stringify(request) + '\n');
      setTimeout(resolve, 500);
    });
  }

  async testInitialize() {
    console.log('\n🔍 Test 1: Initialize Server');
    const request = {
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: { name: 'test-client', version: '1.0.0' }
      }
    };
    
    await this.sendRequest(request);
    const initResponse = this.responses.find(r => r.id === 1);
    
    if (initResponse?.result?.serverInfo?.name === 'snap-windows') {
      console.log('✅ Initialize test passed');
      return true;
    } else {
      console.log('❌ Initialize test failed');
      return false;
    }
  }

  async testListTools() {
    console.log('\n🔍 Test 2: List Available Tools');
    const request = {
      jsonrpc: '2.0',
      id: 2,
      method: 'tools/list',
      params: {}
    };
    
    await this.sendRequest(request);
    const toolsResponse = this.responses.find(r => r.id === 2);
    
    if (toolsResponse?.result?.tools?.length >= 3) {
      const toolNames = toolsResponse.result.tools.map(t => t.name);
      const expectedTools = ['arrange_windows', 'snap_to_position', 'manage_layouts'];
      const hasAllTools = expectedTools.every(tool => toolNames.includes(tool));
      
      if (hasAllTools) {
        console.log('✅ List tools test passed');
        console.log('   Available tools:', toolNames);
        return true;
      }
    }
    
    console.log('❌ List tools test failed');
    return false;
  }

  async testToolSchemas() {
    console.log('\n🔍 Test 3: Validate Tool Schemas');
    const toolsResponse = this.responses.find(r => r.id === 2);
    
    if (!toolsResponse?.result?.tools) {
      console.log('❌ No tools found for schema validation');
      return false;
    }

    const arrangeTool = toolsResponse.result.tools.find(t => t.name === 'arrange_windows');
    const snapTool = toolsResponse.result.tools.find(t => t.name === 'snap_to_position');
    const manageTool = toolsResponse.result.tools.find(t => t.name === 'manage_layouts');

    let allValid = true;

    // Test arrange_windows schema
    if (arrangeTool?.inputSchema?.properties?.layout?.enum?.includes('2x2')) {
      console.log('✅ arrange_windows schema valid');
    } else {
      console.log('❌ arrange_windows schema invalid');
      allValid = false;
    }

    // Test snap_to_position schema
    if (snapTool?.inputSchema?.properties?.windowTitle?.type === 'string' && 
        snapTool?.inputSchema?.properties?.position?.enum?.includes('left')) {
      console.log('✅ snap_to_position schema valid');
    } else {
      console.log('❌ snap_to_position schema invalid');
      allValid = false;
    }

    // Test manage_layouts schema
    if (manageTool?.inputSchema?.properties?.action?.enum?.includes('save')) {
      console.log('✅ manage_layouts schema valid');
    } else {
      console.log('❌ manage_layouts schema invalid');
      allValid = false;
    }

    return allValid;
  }

  async testToolCalls() {
    console.log('\n🔍 Test 4: Test Tool Functionality');
    
    // Test arrange_windows
    const arrangeRequest = {
      jsonrpc: '2.0',
      id: 3,
      method: 'tools/call',
      params: {
        name: 'arrange_windows',
        arguments: { layout: '2x2' }
      }
    };
    
    await this.sendRequest(arrangeRequest);
    
    // Test snap_to_position
    const snapRequest = {
      jsonrpc: '2.0',
      id: 4,
      method: 'tools/call',
      params: {
        name: 'snap_to_position',
        arguments: { windowTitle: 'Test Window', position: 'left' }
      }
    };
    
    await this.sendRequest(snapRequest);
    
    // Test manage_layouts
    const manageRequest = {
      jsonrpc: '2.0',
      id: 5,
      method: 'tools/call',
      params: {
        name: 'manage_layouts',
        arguments: { action: 'save', name: 'test-layout' }
      }
    };
    
    await this.sendRequest(manageRequest);
    
    // Check for any error responses
    const errorResponses = this.responses.filter(r => r.error);
    if (errorResponses.length === 0) {
      console.log('✅ All tool calls executed without errors');
      return true;
    } else {
      console.log('❌ Some tool calls failed:', errorResponses);
      return false;
    }
  }

  async testConfiguration() {
    console.log('\n🔍 Test 5: Configuration Validation');
    
    try {
      // Check if server file exists
      await fs.access(this.serverPath);
      console.log('✅ Server file exists');
      
      // Check VS Code configuration
      const vscodeConfigPath = join(__dirname, '../../.vscode/mcp.json');
      const configContent = await fs.readFile(vscodeConfigPath, 'utf8');
      const config = JSON.parse(configContent);
      
      if (config.mcpServers?.['snap-windows']) {
        const snapConfig = config.mcpServers['snap-windows'];
        if (snapConfig.command === 'node' && 
            snapConfig.args?.includes('mcp_servers/snap-mcp-server.js')) {
          console.log('✅ VS Code configuration correct');
          return true;
        }
      }
      
      console.log('❌ VS Code configuration invalid');
      return false;
    } catch (error) {
      console.log('❌ Configuration test failed:', error.message);
      return false;
    }
  }

  async stopServer() {
    if (this.server) {
      this.server.kill();
      console.log('\n🛑 Server stopped');
    }
  }

  async runAllTests() {
    console.log('🧪 Starting comprehensive snap-mcp-server tests...\n');
    
    const results = [];
    
    try {
      await this.startServer();
      
      results.push(await this.testInitialize());
      results.push(await this.testListTools());
      results.push(await this.testToolSchemas());
      results.push(await this.testToolCalls());
      results.push(await this.testConfiguration());
      
    } catch (error) {
      console.error('💥 Test suite failed:', error);
    } finally {
      await this.stopServer();
    }
    
    const passed = results.filter(r => r).length;
    const total = results.length;
    
    console.log('\n📊 Test Results Summary:');
    console.log(`   Passed: ${passed}/${total}`);
    console.log(`   Success Rate: ${(passed/total*100).toFixed(1)}%`);
    
    if (passed === total) {
      console.log('🎉 All tests passed! Snap-mcp-server is correctly configured and integrated.');
    } else {
      console.log('⚠️  Some tests failed. Check the output above for details.');
    }
    
    return passed === total;
  }
}

// Run the comprehensive test
const tester = new SnapMCPTester();
tester.runAllTests().catch(console.error);
