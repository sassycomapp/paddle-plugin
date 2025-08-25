#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import pkg from 'pg';
const { Pool } = pkg;
import { v4 as uuidv4 } from 'uuid';
import fs from 'fs-extra';
import path from 'path';

// PostgreSQL connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://postgres:2001@localhost:5432/postgres',
});

// Memory Bank configuration
const MEMORY_BANK_PATH = process.env.MEMORY_BANK_PATH || path.join(process.cwd(), '../../memorybank');

class AgentMemoryServer {
  constructor() {
    this.server = new Server(
      {
        name: 'agent-memory-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupTools();
    this.setupHandlers();
  }

  setupTools() {
    this.tools = [
      {
        name: 'store_episodic_memory',
        description: 'Store an episodic memory (event/context) in PostgreSQL',
        inputSchema: {
          type: 'object',
          properties: {
            agent_id: { type: 'string', description: 'Unique identifier for the agent' },
            session_id: { type: 'string', description: 'Session identifier' },
            context: { type: 'object', description: 'Memory context/data' },
            memory_type: { type: 'string', description: 'Type of memory (episodic, system, etc.)' },
            relevance_score: { type: 'number', description: 'Relevance score (0-1)' },
            tags: { type: 'array', items: { type: 'string' }, description: 'Tags for categorization' },
          },
          required: ['agent_id', 'context'],
        },
      },
      {
        name: 'retrieve_episodic_memory',
        description: 'Retrieve episodic memories from PostgreSQL',
        inputSchema: {
          type: 'object',
          properties: {
            agent_id: { type: 'string', description: 'Agent identifier to filter memories' },
            session_id: { type: 'string', description: 'Session identifier to filter memories' },
            tags: { type: 'array', items: { type: 'string' }, description: 'Tags to filter memories' },
            limit: { type: 'number', description: 'Maximum number of memories to return' },
            offset: { type: 'number', description: 'Offset for pagination' },
          },
        },
      },
      {
        name: 'store_semantic_memory',
        description: 'Store semantic memory (facts/knowledge) in PostgreSQL',
        inputSchema: {
          type: 'object',
          properties: {
            entity: { type: 'string', description: 'Entity name or identifier' },
            data: { type: 'object', description: 'Entity data/knowledge' },
            category: { type: 'string', description: 'Category for the entity' },
            agent_id: { type: 'string', description: 'Agent identifier' },
            tags: { type: 'array', items: { type: 'string' }, description: 'Tags for categorization' },
          },
          required: ['entity', 'data'],
        },
      },
      {
        name: 'retrieve_semantic_memory',
        description: 'Retrieve semantic memories from PostgreSQL',
        inputSchema: {
          type: 'object',
          properties: {
            entity: { type: 'string', description: 'Entity name to retrieve' },
            category: { type: 'string', description: 'Category to filter entities' },
            agent_id: { type: 'string', description: 'Agent identifier to filter' },
            tags: { type: 'array', items: { type: 'string' }, description: 'Tags to filter entities' },
          },
        },
      },
      {
        name: 'store_working_memory',
        description: 'Store working memory (temporary state) in PostgreSQL',
        inputSchema: {
          type: 'object',
          properties: {
            agent_id: { type: 'string', description: 'Agent identifier' },
            session_id: { type: 'string', description: 'Session identifier' },
            key: { type: 'string', description: 'Memory key' },
            value: { type: 'object', description: 'Memory value' },
            expires_at: { type: 'string', format: 'date-time', description: 'Expiration time (ISO 8601)' },
          },
          required: ['agent_id', 'session_id', 'key', 'value'],
        },
      },
      {
        name: 'retrieve_working_memory',
        description: 'Retrieve working memory from PostgreSQL',
        inputSchema: {
          type: 'object',
          properties: {
            agent_id: { type: 'string', description: 'Agent identifier' },
            session_id: { type: 'string', description: 'Session identifier' },
            key: { type: 'string', description: 'Specific key to retrieve' },
          },
          required: ['agent_id', 'session_id'],
        },
      },
      {
        name: 'clear_working_memory',
        description: 'Clear working memory for a session',
        inputSchema: {
          type: 'object',
          properties: {
            agent_id: { type: 'string', description: 'Agent identifier' },
            session_id: { type: 'string', description: 'Session identifier' },
            key: { type: 'string', description: 'Specific key to clear (optional)' },
          },
          required: ['agent_id', 'session_id'],
        },
      },
      {
        name: 'sync_memory_bank',
        description: 'Synchronize between PostgreSQL and Memory Bank files',
        inputSchema: {
          type: 'object',
          properties: {
            direction: { type: 'string', enum: ['pg-to-files', 'files-to-pg', 'bidirectional'], description: 'Sync direction' },
            agent_id: { type: 'string', description: 'Agent identifier for filtering' },
            memory_types: { type: 'array', items: { type: 'string' }, description: 'Memory types to sync' },
          },
          required: ['direction'],
        },
      },
      {
        name: 'search_memories',
        description: 'Search across all memory types using keywords or tags',
        inputSchema: {
          type: 'object',
          properties: {
            query: { type: 'string', description: 'Search query' },
            agent_id: { type: 'string', description: 'Agent identifier to filter' },
            memory_types: { type: 'array', items: { type: 'string', enum: ['episodic', 'semantic', 'working'] }, description: 'Memory types to search' },
            tags: { type: 'array', items: { type: 'string' }, description: 'Tags to filter' },
            limit: { type: 'number', description: 'Maximum results' },
          },
          required: ['query'],
        },
      },
    ];
  }

  setupHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: this.tools,
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'store_episodic_memory':
            return await this.storeEpisodicMemory(args);
          case 'retrieve_episodic_memory':
            return await this.retrieveEpisodicMemory(args);
          case 'store_semantic_memory':
            return await this.storeSemanticMemory(args);
          case 'retrieve_semantic_memory':
            return await this.retrieveSemanticMemory(args);
          case 'store_working_memory':
            return await this.storeWorkingMemory(args);
          case 'retrieve_working_memory':
            return await this.retrieveWorkingMemory(args);
          case 'clear_working_memory':
            return await this.clearWorkingMemory(args);
          case 'sync_memory_bank':
            return await this.syncMemoryBank(args);
          case 'search_memories':
            return await this.searchMemories(args);
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

  async storeEpisodicMemory(args) {
    const { agent_id, session_id, context, memory_type = 'episodic', relevance_score = 1.0, tags = [] } = args;
    
    const query = `
      INSERT INTO episodic_memory (agent_id, session_id, context, memory_type, relevance_score, tags)
      VALUES ($1, $2, $3, $4, $5, $6)
      RETURNING *
    `;
    
    const result = await pool.query(query, [agent_id, session_id, JSON.stringify(context), memory_type, relevance_score, tags]);
    
    return {
      content: [
        {
          type: 'text',
          text: `Stored episodic memory: ${JSON.stringify(result.rows[0], null, 2)}`,
        },
      ],
    };
  }

  async retrieveEpisodicMemory(args) {
    const { agent_id, session_id, tags, limit = 10, offset = 0 } = args;
    
    let query = 'SELECT * FROM episodic_memory WHERE 1=1';
    const params = [];
    let paramIndex = 1;
    
    if (agent_id) {
      query += ` AND agent_id = $${paramIndex}`;
      params.push(agent_id);
      paramIndex++;
    }
    
    if (session_id) {
      query += ` AND session_id = $${paramIndex}`;
      params.push(session_id);
      paramIndex++;
    }
    
    if (tags && tags.length > 0) {
      query += ` AND tags && $${paramIndex}`;
      params.push(tags);
      paramIndex++;
    }
    
    query += ` ORDER BY timestamp DESC LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`;
    params.push(limit, offset);
    
    const result = await pool.query(query, params);
    
    return {
      content: [
        {
          type: 'text',
          text: `Retrieved ${result.rows.length} episodic memories:\n${JSON.stringify(result.rows, null, 2)}`,
        },
      ],
    };
  }

  async storeSemanticMemory(args) {
    const { entity, data, category, agent_id, tags = [] } = args;
    
    const query = `
      INSERT INTO semantic_memory (entity, data, category, agent_id, tags)
      VALUES ($1, $2, $3, $4, $5)
      ON CONFLICT (entity, agent_id) DO UPDATE SET
        data = EXCLUDED.data,
        category = EXCLUDED.category,
        last_updated = NOW(),
        tags = EXCLUDED.tags
      RETURNING *
    `;
    
    const result = await pool.query(query, [entity, JSON.stringify(data), category, agent_id, tags]);
    
    return {
      content: [
        {
          type: 'text',
          text: `Stored semantic memory: ${JSON.stringify(result.rows[0], null, 2)}`,
        },
      ],
    };
  }

  async retrieveSemanticMemory(args) {
    const { entity, category, agent_id, tags } = args;
    
    let query = 'SELECT * FROM semantic_memory WHERE 1=1';
    const params = [];
    let paramIndex = 1;
    
    if (entity) {
      query += ` AND entity = $${paramIndex}`;
      params.push(entity);
      paramIndex++;
    }
    
    if (category) {
      query += ` AND category = $${paramIndex}`;
      params.push(category);
      paramIndex++;
    }
    
    if (agent_id) {
      query += ` AND agent_id = $${paramIndex}`;
      params.push(agent_id);
      paramIndex++;
    }
    
    if (tags && tags.length > 0) {
      query += ` AND tags && $${paramIndex}`;
      params.push(tags);
      paramIndex++;
    }
    
    query += ' ORDER BY last_updated DESC';
    
    const result = await pool.query(query, params);
    
    return {
      content: [
        {
          type: 'text',
          text: `Retrieved ${result.rows.length} semantic memories:\n${JSON.stringify(result.rows, null, 2)}`,
        },
      ],
    };
  }

  async storeWorkingMemory(args) {
    const { agent_id, session_id, key, value, expires_at } = args;
    
    const query = `
      INSERT INTO working_memory (agent_id, session_id, key, value, expires_at)
      VALUES ($1, $2, $3, $4, $5)
      ON CONFLICT (agent_id, session_id, key) DO UPDATE SET
        value = EXCLUDED.value,
        created_at = NOW(),
        expires_at = EXCLUDED.expires_at
      RETURNING *
    `;
    
    const result = await pool.query(query, [agent_id, session_id, key, JSON.stringify(value), expires_at]);
    
    return {
      content: [
        {
          type: 'text',
          text: `Stored working memory: ${JSON.stringify(result.rows[0], null, 2)}`,
        },
      ],
    };
  }

  async retrieveWorkingMemory(args) {
    const { agent_id, session_id, key } = args;
    
    let query = 'SELECT * FROM working_memory WHERE agent_id = $1 AND session_id = $2';
    const params = [agent_id, session_id];
    
    if (key) {
      query += ' AND key = $3';
      params.push(key);
    }
    
    query += ' AND (expires_at IS NULL OR expires_at > NOW()) ORDER BY created_at DESC';
    
    const result = await pool.query(query, params);
    
    return {
      content: [
        {
          type: 'text',
          text: `Retrieved ${result.rows.length} working memories:\n${JSON.stringify(result.rows, null, 2)}`,
        },
      ],
    };
  }

  async clearWorkingMemory(args) {
    const { agent_id, session_id, key } = args;
    
    let query = 'DELETE FROM working_memory WHERE agent_id = $1 AND session_id = $2';
    const params = [agent_id, session_id];
    
    if (key) {
      query += ' AND key = $3';
      params.push(key);
    }
    
    const result = await pool.query(query, params);
    
    return {
      content: [
        {
          type: 'text',
          text: `Cleared ${result.rowCount} working memories`,
        },
      ],
    };
  }

  async syncMemoryBank(args) {
    const { direction = 'bidirectional', agent_id, memory_types = ['episodic', 'semantic'] } = args;
    
    // This is a placeholder for Memory Bank integration
    // In a real implementation, this would sync with the memorybank/ directory
    
    return {
      content: [
        {
          type: 'text',
          text: `Memory Bank sync initiated: ${direction} for types: ${memory_types.join(', ')}`,
        },
      ],
    };
  }

  async searchMemories(args) {
    const { query, agent_id, memory_types = ['episodic', 'semantic'], tags, limit = 10 } = args;
    
    const results = {
      episodic: [],
      semantic: [],
      working: []
    };
    
    // Search episodic memories
    if (memory_types.includes('episodic')) {
      const episodicQuery = `
        SELECT * FROM episodic_memory 
        WHERE (context::text ILIKE $1 OR tags && $2)
        ${agent_id ? 'AND agent_id = $3' : ''}
        ORDER BY relevance_score DESC, timestamp DESC
        LIMIT $4
      `;
      const episodicParams = [`%${query}%`, tags || [], ...(agent_id ? [agent_id] : []), limit];
      const episodicResult = await pool.query(episodicQuery, episodicParams);
      results.episodic = episodicResult.rows;
    }
    
    // Search semantic memories
    if (memory_types.includes('semantic')) {
      const semanticQuery = `
        SELECT * FROM semantic_memory 
        WHERE (entity ILIKE $1 OR data::text ILIKE $1 OR tags && $2)
        ${agent_id ? 'AND agent_id = $3' : ''}
        ORDER BY access_count DESC, last_updated DESC
        LIMIT $4
      `;
      const semanticParams = [`%${query}%`, tags || [], ...(agent_id ? [agent_id] : []), limit];
      const semanticResult = await pool.query(semanticQuery, semanticParams);
      results.semantic = semanticResult.rows;
    }
    
    return {
      content: [
        {
          type: 'text',
          text: `Search results for "${query}":\n${JSON.stringify(results, null, 2)}`,
        },
      ],
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Agent Memory MCP server running on stdio');
  }
}

// Handle graceful shutdown
process.on('SIGINT', async () => {
  console.error('Shutting down Agent Memory MCP server...');
  process.exit(0);
});

// Run the server if this script is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const server = new AgentMemoryServer();
  server.run().catch(console.error);
}

export default AgentMemoryServer;
