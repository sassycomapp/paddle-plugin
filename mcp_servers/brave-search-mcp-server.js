#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
// Assuming braveSearchManager.js will be accessible relative to this file
// This path might need adjustment if braveSearchManager.js is moved or packaged differently.
import braveSearch from '../brave-search-integration/braveSearchManager.js'; 

class BraveSearchMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'brave-search-mcp-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );
    this.setupTools();
    // The braveSearchManager handles its own initialization (cache, etc.)
    // We just need to ensure the API key is accessible to it.
    // The policy file in brave-search-integration/braveSearchPolicy.json needs to be updated
    // or the braveSearchManager modified to read the API key from an environment variable.
    // For now, we assume braveSearchManager.js is configured correctly.
  }

  setupTools() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'brave_search',
          description: 'Search the web using the Brave Search API',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'The search query',
              },
            },
            required: ['query'],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'brave_search':
            return await this.performBraveSearch(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  async performBraveSearch({ query }) {
    if (!query) {
      throw new Error('Query is required for brave_search.');
    }
    console.error(`[BraveSearchMCPServer] Performing search for: "${query}"`);
    try {
      const results = await braveSearch(query);
      console.error(`[BraveSearchMCPServer] Search successful for: "${query}"`);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(results, null, 2),
          },
        ],
      };
    } catch (error) {
      console.error(`[BraveSearchMCPServer] Search failed for: "${query}" - ${error.message}`);
      throw new Error(`Brave search failed: ${error.message}`);
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Brave Search MCP server running on stdio');
  }
}

// Handle graceful shutdown
process.on('SIGINT', async () => {
  console.error('Shutting down Brave Search MCP server...');
  process.exit(0);
});

// Run the server if this script is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const server = new BraveSearchMCPServer();
  server.run().catch(console.error);
}

export default BraveSearchMCPServer;
