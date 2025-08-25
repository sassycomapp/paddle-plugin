#!/usr/bin/env node

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

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
      stdio: ['pipe', 'pipe', 'pipe']
    });

    this.server.stdout.on('data', (data) => {
      console.log('Server stdout:', data.toString());
    });

    this.server.stderr.on('data', (data) => {
      console.error('Server stderr:', data.toString());
    });

    // Wait for server to initialize
    await new Promise(resolve => setTimeout(resolve, 1000));
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
        reject(new Error('Request timeout'));
      }, 5000);
    });
  }

  async testMemorySystem() {
    try {
      console.log('\n=== Testing Agent Memory System ===\n');

      // Test 1: Store episodic memory
      console.log('1. Testing store_episodic_memory...');
      const episodicResult = await this.sendRequest('store_episodic_memory', {
        agentId: 'test-agent-1',
        sessionId: 'test-session-1',
        context: { event: 'user_login', details: { username: 'john_doe' } },
        tags: ['authentication', 'user_action']
      });
      console.log('✓ Episodic memory stored:', episodicResult);

      // Test 2: Store semantic memory
      console.log('\n2. Testing store_semantic_memory...');
      const semanticResult = await this.sendRequest('store_semantic_memory', {
        agentId: 'test-agent-1',
        entity: 'user_preferences',
        data: { theme: 'dark', language: 'en', notifications: true },
        category: 'user_profile',
        tags: ['preferences', 'settings']
      });
      console.log('✓ Semantic memory stored:', semanticResult);

      // Test 3: Store working memory
      console.log('\n3. Testing store_working_memory...');
      const workingResult = await this.sendRequest('store_working_memory', {
        agentId: 'test-agent-1',
        sessionId: 'test-session-1',
        key: 'current_task',
        value: { task: 'process_payment', status: 'in_progress' }
      });
      console.log('✓ Working memory stored:', workingResult);

      // Test 4: Retrieve episodic memories
      console.log('\n4. Testing get_episodic_memories...');
      const episodicMemories = await this.sendRequest('get_episodic_memories', {
        agentId: 'test-agent-1',
        limit: 10
      });
      console.log('✓ Retrieved episodic memories:', episodicMemories);

      // Test 5: Retrieve semantic memories
      console.log('\n5. Testing get_semantic_memories...');
      const semanticMemories = await this.sendRequest('get_semantic_memories', {
        agentId: 'test-agent-1',
        category: 'user_profile'
      });
      console.log('✓ Retrieved semantic memories:', semanticMemories);

      // Test 6: Retrieve working memory
      console.log('\n6. Testing get_working_memory...');
      const workingMemories = await this.sendRequest('get_working_memory', {
        agentId: 'test-agent-1',
        sessionId: 'test-session-1'
      });
      console.log('✓ Retrieved working memories:', workingMemories);

      // Test 7: Search memories
      console.log('\n7. Testing search_memories...');
      const searchResults = await this.sendRequest('search_memories', {
        agentId: 'test-agent-1',
        query: 'user',
        limit: 5
      });
      console.log('✓ Search results:', searchResults);

      // Test 8: Cleanup working memory
      console.log('\n8. Testing cleanup_working_memory...');
      const cleanupResult = await this.sendRequest('cleanup_working_memory', {
        agentId: 'test-agent-1',
        sessionId: 'test-session-1'
      });
      console.log('✓ Working memory cleaned:', cleanupResult);

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
