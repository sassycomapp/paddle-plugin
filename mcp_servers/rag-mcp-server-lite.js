#!/usr/bin/env node

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');
const fs = require('fs').promises;
const path = require('path');

class MockRAGServer {
  constructor() {
    this.server = new Server(
      {
        name: 'mock-rag-server',
        version: '0.1.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.dataDir = process.env.DATA_DIR || './mock_data';
    this.setupTools();
  }

  async ensureDataDir() {
    try {
      await fs.mkdir(this.dataDir, { recursive: true });
    } catch (error) {
      console.error('Error creating data directory:', error);
    }
  }

  setupTools() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'store_document',
          description: 'Store a document in the mock knowledge base',
          inputSchema: {
            type: 'object',
            properties: {
              content: { type: 'string', description: 'Document content to store' },
              metadata: { type: 'object', description: 'Optional metadata' }
            },
            required: ['content']
          }
        },
        {
          name: 'search_documents',
          description: 'Search documents in the mock knowledge base',
          inputSchema: {
            type: 'object',
            properties: {
              query: { type: 'string', description: 'Search query' },
              limit: { type: 'number', description: 'Maximum results to return', default: 5 }
            },
            required: ['query']
          }
        },
        {
          name: 'get_document',
          description: 'Get a specific document by ID',
          inputSchema: {
            type: 'object',
            properties: {
              id: { type: 'string', description: 'Document ID' }
            },
            required: ['id']
          }
        }
      ]
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'store_document':
            return await this.storeDocument(args);
          case 'search_documents':
            return await this.searchDocuments(args);
          case 'get_document':
            return await this.getDocument(args);
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

  async storeDocument(args) {
    await this.ensureDataDir();
    
    const id = `doc_${Date.now()}`;
    const document = {
      id,
      content: args.content,
      metadata: args.metadata || {},
      timestamp: new Date().toISOString()
    };

    const filePath = path.join(this.dataDir, `${id}.json`);
    await fs.writeFile(filePath, JSON.stringify(document, null, 2));

    return {
      content: [{
        type: 'text',
        text: `Document stored successfully with ID: ${id}`
      }]
    };
  }

  async searchDocuments(args) {
    await this.ensureDataDir();
    
    const files = await fs.readdir(this.dataDir);
    const documents = [];

    for (const file of files) {
      if (file.endsWith('.json')) {
        const filePath = path.join(this.dataDir, file);
        const content = await fs.readFile(filePath, 'utf8');
        const doc = JSON.parse(content);
        
        // Simple text search
        if (doc.content.toLowerCase().includes(args.query.toLowerCase())) {
          documents.push(doc);
        }
      }
    }

    const limit = args.limit || 5;
    const results = documents.slice(0, limit);

    return {
      content: [{
        type: 'text',
        text: `Found ${results.length} documents:\n\n${results.map(doc => 
          `ID: ${doc.id}\nContent: ${doc.content.substring(0, 200)}...\nMetadata: ${JSON.stringify(doc.metadata)}\n---`
        ).join('\n\n')}`
      }]
    };
  }

  async getDocument(args) {
    await this.ensureDataDir();
    
    const filePath = path.join(this.dataDir, `${args.id}.json`);
    
    try {
      const content = await fs.readFile(filePath, 'utf8');
      const doc = JSON.parse(content);
      
      return {
        content: [{
          type: 'text',
          text: `Document ${args.id}:\n\nContent: ${doc.content}\nMetadata: ${JSON.stringify(doc.metadata)}\nTimestamp: ${doc.timestamp}`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Document ${args.id} not found`
        }],
        isError: true
      };
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Mock RAG server running on stdio');
  }
}

const server = new MockRAGServer();
server.run().catch(console.error);
