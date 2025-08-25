#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { Pool } from 'pg';
import { parse } from 'pg-connection-string';
import { pipeline } from '@xenova/transformers';
import { v4 as uuidv4 } from 'uuid';

class PGVectorMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'pgvector-mcp-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.pool = null;
    this.embeddingPipeline = null;
    this.collectionName = 'documents';
    
    this.setupTools();
    this.initializeServices();
  }

  async initializeServices() {
    try {
      // Initialize PostgreSQL connection
      const connectionString = process.env.DATABASE_URL || 'postgresql://postgres:2001@localhost:5432/postgres';
      const config = parse(connectionString);
      
      this.pool = new Pool({
        user: config.user,
        password: config.password,
        host: config.host,
        port: config.port,
        database: config.database,
        ssl: config.ssl ? { rejectUnauthorized: false } : false
      });

      // Verify pgvector extension exists
      const client = await this.pool.connect();
      try {
        const res = await client.query(
          "SELECT extname FROM pg_extension WHERE extname = 'vector'"
        );
        if (res.rows.length === 0) {
          throw new Error('pgvector extension not installed');
        }
      } finally {
        client.release();
      }

      // Initialize embedding pipeline
      this.embeddingPipeline = await pipeline(
        'feature-extraction',
        'Xenova/all-MiniLM-L6-v2'
      );

      console.error('PGVector MCP Server initialized successfully');
    } catch (error) {
      console.error('Failed to initialize services:', error);
      throw error;
    }
  }

  setupTools() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'add_document',
          description: 'Add a document to the RAG knowledge base',
          inputSchema: {
            type: 'object',
            properties: {
              content: {
                type: 'string',
                description: 'The document content to add',
              },
              metadata: {
                type: 'object',
                description: 'Optional metadata for the document',
              },
              documentId: {
                type: 'string',
                description: 'Unique identifier for the document',
              },
            },
            required: ['content', 'documentId'],
          },
        },
        {
          name: 'search_documents',
          description: 'Search for relevant documents based on a query',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'The search query',
              },
              nResults: {
                type: 'number',
                description: 'Number of results to return (default: 5)',
                default: 5,
              },
            },
            required: ['query'],
          },
        },
        {
          name: 'delete_document',
          description: 'Delete a document from the knowledge base',
          inputSchema: {
            type: 'object',
            properties: {
              documentId: {
                type: 'string',
                description: 'The document ID to delete',
              },
            },
            required: ['documentId'],
          },
        },
        {
          name: 'get_document',
          description: 'Retrieve a specific document by ID',
          inputSchema: {
            type: 'object',
            properties: {
              documentId: {
                type: 'string',
                description: 'The document ID to retrieve',
              },
            },
            required: ['documentId'],
          },
        },
        {
          name: 'list_documents',
          description: 'List all documents in the knowledge base',
          inputSchema: {
            type: 'object',
            properties: {
              limit: {
                type: 'number',
                description: 'Maximum number of documents to return',
                default: 100,
              },
            },
          },
        },
        {
          name: 'update_document',
          description: 'Update an existing document',
          inputSchema: {
            type: 'object',
            properties: {
              documentId: {
                type: 'string',
                description: 'The document ID to update',
              },
              content: {
                type: 'string',
                description: 'The new document content',
              },
              metadata: {
                type: 'object',
                description: 'Updated metadata for the document',
              },
            },
            required: ['documentId', 'content'],
          },
        },
        {
          name: 'batch_add_documents',
          description: 'Add multiple documents at once',
          inputSchema: {
            type: 'object',
            properties: {
              documents: {
                type: 'array',
                items: {
                  type: 'object',
                  properties: {
                    content: { type: 'string' },
                    documentId: { type: 'string' },
                    metadata: { type: 'object' },
                  },
                  required: ['content', 'documentId'],
                },
                description: 'Array of documents to add',
              },
            },
            required: ['documents'],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'add_document':
            return await this.addDocument(args);
          case 'search_documents':
            return await this.searchDocuments(args);
          case 'delete_document':
            return await this.deleteDocument(args);
          case 'get_document':
            return await this.getDocument(args);
          case 'list_documents':
            return await this.listDocuments(args);
          case 'update_document':
            return await this.updateDocument(args);
          case 'batch_add_documents':
            return await this.batchAddDocuments(args);
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

  async generateEmbedding(text) {
    try {
      const output = await this.embeddingPipeline(text, {
        pooling: 'mean',
        normalize: true,
      });
      
      // Convert tensor to array
      const embedding = Array.from(output.data);
      return embedding;
    } catch (error) {
      throw new Error(`Failed to generate embedding: ${error.message}`);
    }
  }

  async addDocument({ content, documentId, metadata = {} }) {
    if (!this.pool) {
      throw new Error('Database connection not initialized');
    }

    try {
      const embedding = await this.generateEmbedding(content);
      const client = await this.pool.connect();
      
      try {
        await client.query('BEGIN');
        
        // Insert document
        await client.query(
          `INSERT INTO documents (id, content, embedding, metadata)
           VALUES ($1, $2, $3::vector, $4)
           ON CONFLICT (id) DO UPDATE
           SET content = EXCLUDED.content,
               embedding = EXCLUDED.embedding,
               metadata = EXCLUDED.metadata`,
          [
            documentId,
            content,
            embedding,
            { ...metadata, documentId }
          ]
        );
        
        await client.query('COMMIT');
        
        return {
          content: [
            {
              type: 'text',
              text: `Document '${documentId}' added successfully`,
            },
          ],
        };
      } catch (error) {
        await client.query('ROLLBACK');
        throw error;
      } finally {
        client.release();
      }
    } catch (error) {
      throw new Error(`Failed to add document: ${error.message}`);
    }
  }

  async searchDocuments({ query, nResults = 5 }) {
    if (!this.pool) {
      throw new Error('Database connection not initialized');
    }

    try {
      const queryEmbedding = await this.generateEmbedding(query);
      const client = await this.pool.connect();
      
      try {
        const result = await client.query(
          `SELECT id, content, metadata, 1 - (embedding <=> $1::vector) AS similarity
           FROM documents
           ORDER BY embedding <=> $1::vector
           LIMIT $2`,
          [queryEmbedding, nResults]
        );

        const formattedResults = result.rows.map(row => ({
          content: row.content,
          metadata: row.metadata,
          distance: 1 - row.similarity
        }));

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(formattedResults, null, 2),
            },
          ],
        };
      } finally {
        client.release();
      }
    } catch (error) {
      throw new Error(`Failed to search documents: ${error.message}`);
    }
  }

  async deleteDocument({ documentId }) {
    if (!this.pool) {
      throw new Error('Database connection not initialized');
    }

    try {
      const client = await this.pool.connect();
      
      try {
        await client.query('BEGIN');
        
        // Delete document
        const result = await client.query(
          'DELETE FROM documents WHERE id = $1 RETURNING id',
          [documentId]
        );
        
        await client.query('COMMIT');
        
        if (result.rowCount === 0) {
          return {
            content: [
              {
                type: 'text',
                text: `Document '${documentId}' not found`,
              },
            ],
          };
        }
        
        return {
          content: [
            {
              type: 'text',
              text: `Document '${documentId}' deleted successfully`,
            },
          ],
        };
      } catch (error) {
        await client.query('ROLLBACK');
        throw error;
      } finally {
        client.release();
      }
    } catch (error) {
      throw new Error(`Failed to delete document: ${error.message}`);
    }
  }

  async getDocument({ documentId }) {
    if (!this.pool) {
      throw new Error('Database connection not initialized');
    }

    try {
      const client = await this.pool.connect();
      
      try {
        const result = await client.query(
          'SELECT id, content, metadata FROM documents WHERE id = $1',
          [documentId]
        );
        
        if (result.rows.length === 0) {
          return {
            content: [
              {
                type: 'text',
                text: `Document '${documentId}' not found`,
              },
            ],
          };
        }
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                content: result.rows[0].content,
                metadata: result.rows[0].metadata
              }, null, 2),
            },
          ],
        };
      } finally {
        client.release();
      }
    } catch (error) {
      throw new Error(`Failed to get document: ${error.message}`);
    }
  }

  async listDocuments({ limit = 100 }) {
    if (!this.pool) {
      throw new Error('Database connection not initialized');
    }

    try {
      const client = await this.pool.connect();
      
      try {
        const result = await client.query(
          'SELECT id, content, metadata FROM documents LIMIT $1',
          [limit]
        );
        
        const documents = result.rows.map(row => ({
          content: row.content.substring(0, 200) + (row.content.length > 200 ? '...' : ''),
          metadata: row.metadata,
          documentId: row.id
        }));

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(documents, null, 2),
            },
          ],
        };
      } finally {
        client.release();
      }
    } catch (error) {
      throw new Error(`Failed to list documents: ${error.message}`);
    }
  }

  async updateDocument({ documentId, content, metadata = {} }) {
    return this.addDocument({ content, documentId, metadata });
  }

  async batchAddDocuments({ documents }) {
    if (!this.pool) {
      throw new Error('Database connection not initialized');
    }

    try {
      const client = await this.pool.connect();
      
      try {
        await client.query('BEGIN');
        
        for (const doc of documents) {
          const embedding = await this.generateEmbedding(doc.content);
          
          await client.query(
            `INSERT INTO documents (id, content, embedding, metadata)
             VALUES ($1, $2, $3::vector, $4)
             ON CONFLICT (id) DO UPDATE
             SET content = EXCLUDED.content,
                 embedding = EXCLUDED.embedding,
                 metadata = EXCLUDED.metadata`,
            [
              doc.documentId,
              doc.content,
              embedding,
              { ...doc.metadata, documentId: doc.documentId }
            ]
          );
        }
        
        await client.query('COMMIT');
        
        return {
          content: [
            {
              type: 'text',
              text: `Successfully added ${documents.length} documents`,
            },
          ],
        };
      } catch (error) {
        await client.query('ROLLBACK');
        throw error;
      } finally {
        client.release();
      }
    } catch (error) {
      throw new Error(`Failed to batch add documents: ${error.message}`);
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('PGVector MCP server running on stdio');
  }
}

// Handle graceful shutdown
process.on('SIGINT', async () => {
  console.error('Shutting down PGVector MCP server...');
  if (this.pool) {
    await this.pool.end();
  }
  process.exit(0);
});

// Run the server if this script is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const server = new PGVectorMCPServer();
  server.run().catch(console.error);
}

export default PGVectorMCPServer;
