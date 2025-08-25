#!/usr/bin/env node

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class MCPTester {
  constructor() {
    this.server = null;
    this.requestId = 1;
  }

  async startServer() {
    console.log('Starting Agent Memory MCP server...');
    this.server = spawn('node', ['index.js'], {
      cwd: __dirname,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: {
        ...process.env,
        PGUSER: 'postgres',
        PGPASSWORD: '2001',
        PGHOST: 'localhost',
        PGDATABASE: 'postgres',
        PGPORT: '5432'
      }
    });

    this.server.stdout.on('data', (data) => {
      const output = data.toString();
      if (!output.includes('Agent Memory MCP server running')) {
        console.log('Server:', output.trim());
      }
    });

    this.server.stderr.on('data', (data) => {
      console.error('Server error:', data.toString());
    });

    // Wait for server to initialize
    await new Promise(resolve => setTimeout(resolve, 5000));
    console.log('Server started successfully');
  }

  async sendRequest(method, params = {}) {
    const request = {
      jsonrpc: '2.0',
      id: this.requestId++,
      method,
      params
    };

    return new Promise((resolve, reject) => {
      let response = '';
      
      const onData = (data) => {
        response += data.toString();
        try {
          const lines = response.split('\n');
          for (const line of lines) {
            if (line.trim()) {
              const parsed = JSON.parse(line.trim());
              if (parsed.id === request.id) {
                this.server.stdout.off('data', onData);
                resolve(parsed);
                return;
              }
            }
          }
        } catch (e) {
          // Continue waiting for complete JSON
        }
      };

      this.server.stdout.on('data', onData);
      this.server.stdin.write(JSON.stringify(request) + '\n');

      setTimeout(() => {
        this.server.stdout.off('data', onData);
        console.error('Request timed out after 60 seconds');
        reject(new Error('Request timeout'));
      }, 60000);
    });
  }

  async testMemorySystem() {
    try {
      console.log('\n=== Testing Agent Memory System ===\n');

      // First, list available tools
      console.log('1. Listing available tools...');
      const toolsList = await this.sendRequest('tools/list');
      console.log('✓ Available tools:', JSON.stringify(toolsList, null, 2));

      // Test 2: Store episodic memory
      console.log('\n2. Testing store_episodic_memory...');
      const episodicResult = await this.sendRequest('tools/call', {
        name: 'store_episodic_memory',
        arguments: {
          agent_id: 'test-agent-' + Date.now(),
          session_id: 'test-session-' + Math.random().toString(36).substring(2, 15),
          context: { event: 'user_login', details: { username: 'john_doe', timestamp: new Date().toISOString() } },
          tags: ['authentication', 'user_action']
        }
      });
      console.log('✓ Episodic memory stored:', JSON.stringify(episodicResult, null, 2));

      // Test 3: Store semantic memory
      console.log('\n3. Testing store_semantic_memory...');
      const semanticResult = await this.sendRequest('tools/call', {
        name: 'store_semantic_memory',
        arguments: {
          entity: 'user_preferences_john_doe',
          data: { theme: 'dark', language: 'en', notifications: true, auto_save: true },
          category: 'user_profile',
          agent_id: 'test-agent-' + Date.now(),
          tags: ['preferences', 'settings', 'user_john_doe']
        }
      });
      console.log('✓ Semantic memory stored:', JSON.stringify(semanticResult, null, 2));

      // Test 4: Store working memory
      console.log('\n4. Testing store_working_memory...');
      const workingResult = await this.sendRequest('tools/call', {
        name: 'store_working_memory',
        arguments: {
          agent_id: 'test-agent-' + Date.now(),
          session_id: 'test-session-' + Math.random().toString(36).substring(2, 15),
          key: 'current_task',
          value: { task: 'process_payment', status: 'in_progress', amount: 99.99, currency: 'USD' }
        }
      });
      console.log('✓ Working memory stored:', JSON.stringify(workingResult, null, 2));

      // Test 5: Retrieve episodic memories
      console.log('\n5. Testing retrieve_episodic_memory...');
      const episodicMemories = await this.sendRequest('tools/call', {
        name: 'retrieve_episodic_memory',
        arguments: {
          agent_id: 'test-agent-' + Date.now(),
          limit: 5
        }
      });
      console.log('✓ Retrieved episodic memories:', JSON.stringify(episodicMemories, null, 2));

      // Test 6: Retrieve semantic memories
      console.log('\n6. Testing retrieve_semantic_memory...');
      const semanticMemories = await this.sendRequest('tools/call', {
        name: 'retrieve_semantic_memory',
        arguments: {
          agent_id: 'test-agent-' + Date.now(),
          category: 'user_profile'
        }
      });
      console.log('✓ Retrieved semantic memories:', JSON.stringify(semanticMemories, null, 2));

      // Test 7: Retrieve working memory
      console.log('\n7. Testing retrieve_working_memory...');
      const workingMemories = await this.sendRequest('tools/call', {
        name: 'retrieve_working_memory',
        arguments: {
          agent_id: 'test-agent-' + Date.now(),
          session_id: 'test-session-' + Math.random().toString(36).substring(2, 15)
        }
      });
      console.log('✓ Retrieved working memories:', JSON.stringify(workingMemories, null, 2));

      // Test 8: Search memories
      console.log('\n8. Testing search_memories...');
      const searchResults = await this.sendRequest('tools/call', {
        name: 'search_memories',
        arguments: {
          query: 'user',
          agent_id: 'test-agent-' + Date.now(),
          limit: 10
        }
      });
      console.log('✓ Search results:', JSON.stringify(searchResults, null, 2));

      // Test 9: Clear working memory
      console.log('\n9. Testing clear_working_memory...');
      const clearResult = await this.sendRequest('tools/call', {
        name: 'clear_working_memory',
        arguments: {
          agent_id: 'test-agent-' + Date.now(),
          session_id: 'test-session-' + Math.random().toString(36).substring(2, 15)
        }
      });
      console.log('✓ Working memory cleared:', JSON.stringify(clearResult, null, 2));

      // Test 10: Verify working memory is cleared
      console.log('\n10. Verifying working memory is cleared...');
      const verifyCleared = await this.sendRequest('tools/call', {
        name: 'retrieve_working_memory',
        arguments: {
          agent_id: 'test-agent-' + Date.now(),
          session_id: 'test-session-' + Math.random().toString(36).substring(2, 15)
        }
      });
      console.log('✓ Working memory after clear:', JSON.stringify(verifyCleared, null, 2));

      console.log('\n=== All tests completed successfully! ===');

    } catch (error) {
      console.error('Test failed:', error);
    }
  }

  async stopServer() {
    if (this.server) {
      this.server.kill();
      console.log('Server stopped');
    }
  }

  async run() {
    try {
      await this.startServer();
      await this.testMemorySystem();
    } finally {
      await this.stopServer();
    }
  }
}

// Run the tests
const tester = new MCPTester();
tester.run().catch(console.error);
