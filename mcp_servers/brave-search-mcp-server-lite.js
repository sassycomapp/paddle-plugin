#!/usr/bin/env node

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');

class MockBraveSearchServer {
  constructor() {
    this.server = new Server(
      {
        name: 'mock-brave-search-server',
        version: '0.1.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.mockData = [
      {
        title: "Understanding AG2 Orchestration System",
        url: "https://example.com/ag2-guide",
        description: "A comprehensive guide to the AG2 orchestration system and its capabilities.",
        age: "2024-08-12"
      },
      {
        title: "MCP Server Development Best Practices",
        url: "https://example.com/mcp-best-practices",
        description: "Learn how to build effective MCP servers with proper error handling and testing.",
        age: "2024-08-11"
      },
      {
        title: "Python AG2 Integration Tutorial",
        url: "https://example.com/python-ag2-tutorial",
        description: "Step-by-step guide to integrating AG2 orchestration with Python applications.",
        age: "2024-08-10"
      },
      {
        title: "Multi-Agent Systems Architecture",
        url: "https://example.com/multi-agent-architecture",
        description: "Design patterns and architectural considerations for building multi-agent systems.",
        age: "2024-08-09"
      }
    ];

    this.setupTools();
  }

  setupTools() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'brave_web_search',
          description: 'Search the web using Brave Search API (mock version)',
          inputSchema: {
            type: 'object',
            properties: {
              query: { type: 'string', description: 'Search query' },
              count: { type: 'number', description: 'Number of results to return', default: 5 }
            },
            required: ['query']
          }
        },
        {
          name: 'brave_news_search',
          description: 'Search for news using Brave Search API (mock version)',
          inputSchema: {
            type: 'object',
            properties: {
              query: { type: 'string', description: 'News search query' },
              count: { type: 'number', description: 'Number of results to return', default: 5 }
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
          case 'brave_web_search':
            return await this.webSearch(args);
          case 'brave_news_search':
            return await this.newsSearch(args);
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

  async webSearch(args) {
    const query = args.query.toLowerCase();
    const count = args.count || 5;

    // Simple mock search - filter mock data based on query
    const results = this.mockData.filter(item => 
      item.title.toLowerCase().includes(query) || 
      item.description.toLowerCase().includes(query)
    ).slice(0, count);

    return {
      content: [{
        type: 'text',
        text: `Web search results for "${args.query}":\n\n${results.map((result, index) => 
          `${index + 1}. ${result.title}\n   ${result.url}\n   ${result.description}\n   Published: ${result.age}`
        ).join('\n\n')}`
      }]
    };
  }

  async newsSearch(args) {
    const query = args.query.toLowerCase();
    const count = args.count || 5;

    // Mock news results
    const newsResults = [
      {
        title: `Latest News: ${args.query}`,
        url: `https://example.com/news/${args.query.replace(/\s+/g, '-')}`,
        description: `Breaking news about ${args.query} and its impact on the industry.`,
        age: "2024-08-12"
      },
      {
        title: `Analysis: ${args.query} Trends`,
        url: `https://example.com/analysis/${args.query.replace(/\s+/g, '-')}`,
        description: `In-depth analysis of current ${args.query} trends and future implications.`,
        age: "2024-08-11"
      }
    ].slice(0, count);

    return {
      content: [{
        type: 'text',
        text: `News search results for "${args.query}":\n\n${newsResults.map((result, index) => 
          `${index + 1}. ${result.title}\n   ${result.url}\n   ${result.description}\n   Published: ${result.age}`
        ).join('\n\n')}`
      }]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Mock Brave search server running on stdio');
  }
}

const server = new MockBraveSearchServer();
server.run().catch(console.error);
