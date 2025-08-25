#!/usr/bin/env node

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');
const fs = require('fs').promises;
const path = require('path');

class MockAgentMemoryServer {
  constructor() {
    this.server = new Server(
      {
        name: 'mock-agent-memory-server',
        version: '0.1.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.memoryDir = process.env.MEMORY_DIR || './mock_memory';
    this.setupTools();
  }

  async ensureMemoryDir() {
    try {
      await fs.mkdir(this.memoryDir, { recursive: true });
    } catch (error) {
      console.error('Error creating memory directory:', error);
    }
  }

  setupTools() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'store_memory',
          description: 'Store a memory for an agent',
          inputSchema: {
            type: 'object',
            properties: {
              agent_id: { type: 'string', description: 'Agent identifier' },
              key: { type: 'string', description: 'Memory key' },
              value: { type: 'any', description: 'Memory value' },
              metadata: { type: 'object', description: 'Optional metadata' }
            },
            required: ['agent_id', 'key', 'value']
          }
        },
        {
          name: 'get_memory',
          description: 'Get a specific memory for an agent',
          inputSchema: {
            type: 'object',
            properties: {
              agent_id: { type: 'string', description: 'Agent identifier' },
              key: { type: 'string', description: 'Memory key' }
            },
            required: ['agent_id', 'key']
          }
        },
        {
          name: 'get_agent_memories',
          description: 'Get all memories for an agent',
          inputSchema: {
            type: 'object',
            properties: {
              agent_id: { type: 'string', description: 'Agent identifier' }
            },
            required: ['agent_id']
          }
        },
        {
          name: 'search_memories',
          description: 'Search memories across all agents',
          inputSchema: {
            type: 'object',
            properties: {
              query: { type: 'string', description: 'Search query' },
              limit: { type: 'number', description: 'Maximum results', default: 10 }
            },
            required: ['query']
          }
        }
      ]
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'store_memory':
            return await this.storeMemory(args);
          case 'get_memory':
            return await this.getMemory(args);
          case 'get_agent_memories':
            return await this.getAgentMemories(args);
          case 'search_memories':
            return await this.searchMemories(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [{
            type: 'text',
            text: `Error: ${error.message}`
          }],
          isError: true
        };
      }
    });
  }

  async storeMemory(args) {
    await this.ensureMemoryDir();
    
    const agentDir = path.join(this.memoryDir, args.agent_id);
    await fs.mkdir(agentDir, { recursive: true });

    const memory = {
      agent_id: args.agent_id,
      key: args.key,
      value: args.value,
      metadata: args.metadata || {},
      timestamp: new Date().toISOString()
    };

    const filePath = path.join(agentDir, `${args.key}.json`);
    await fs.writeFile(filePath, JSON.stringify(memory, null, 2));

    return {
      content: [{
        type: 'text',
        text: `Memory stored successfully for agent ${args.agent_id}: ${args.key}`
      }]
    };
  }

  async getMemory(args) {
    await this.ensureMemoryDir();
    
    const filePath = path.join(this.memoryDir, args.agent_id, `${args.key}.json`);
    
    try {
      const content = await fs.readFile(filePath, 'utf8');
      const memory = JSON.parse(content);
      
      return {
        content: [{
          type: 'text',
          text: `Memory for ${args.agent_id}.${args.key}:\n\nValue: ${JSON.stringify(memory.value, null, 2)}\nMetadata: ${JSON.stringify(memory.metadata)}\nTimestamp: ${memory.timestamp}`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Memory ${args.key} not found for agent ${args.agent_id}`
        }],
        isError: true
      };
    }
  }

  async getAgentMemories(args) {
    await this.ensureMemoryDir();
    
    const agentDir = path.join(this.memoryDir, args.agent_id);
    
    try {
      const files = await fs.readdir(agentDir);
      const memories = [];

      for (const file of files) {
        if (file.endsWith('.json')) {
          const filePath = path.join(agentDir, file);
          const content = await fs.readFile(filePath, 'utf8');
          const memory = JSON.parse(content);
          memories.push(memory);
        }
      }

      return {
        content: [{
          type: 'text',
          text: `Memories for agent ${args.agent_id}:\n\n${memories.map(mem => 
            `${mem.key}: ${JSON.stringify(mem.value)}`
          ).join('\n')}`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `No memories found for agent ${args.agent_id}`
        }]
      };
    }
  }

  async searchMemories(args) {
    await this.ensureMemoryDir();
    
    const agents = await fs.readdir(this.memoryDir);
    const results = [];

    for (const agentId of agents) {
      const agentDir = path.join(this.memoryDir, agentId);
      const stat = await fs.stat(agentDir);
      
      if (stat.isDirectory()) {
        const files = await fs.readdir(agentDir);
        
        for (const file of files) {
          if (file.endsWith('.json')) {
            const filePath = path.join(agentDir, file);
            const content = await fs.readFile(filePath, 'utf8');
            const memory = JSON.parse(content);
            
            const searchStr = JSON.stringify(memory).toLowerCase();
            if (searchStr.includes(args.query.toLowerCase())) {
              results.push(memory);
            }
          }
        }
      }
    }

    const limit = args.limit || 10;
    const limitedResults = results.slice(0, limit);

    return {
      content: [{
        type: 'text',
        text: `Found ${limitedResults.length} memories:\n\n${limitedResults.map(mem => 
          `${mem.agent_id}.${mem.key}: ${JSON.stringify(mem.value)}`
        ).join('\n')}`
      }]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Mock agent memory server running on stdio');
  }
}

const server = new MockAgentMemoryServer();
server.run().catch(console.error);
