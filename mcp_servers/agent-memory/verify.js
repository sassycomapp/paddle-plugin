#!/usr/bin/env node

import pkg from 'pg';
const { Pool } = pkg;
import dotenv from 'dotenv';
dotenv.config({ path: './.env' });

// Debug: Log environment variables
console.log("PGUSER from env:", process.env.PGUSER);
console.log("PGHOST from env:", process.env.PGHOST);
console.log("PGDATABASE from env:", process.env.PGDATABASE);
console.log("PGPASSWORD from env:", process.env.PGPASSWORD);
console.log("PGPORT from env:", process.env.PGPORT);

// Test database connection
const pool = new Pool({
  user: process.env.PGUSER,
  host: process.env.PGHOST,
  database: process.env.PGDATABASE,
  password: String(process.env.PGPASSWORD),
  port: process.env.PGPORT,
});

async function verifyDatabase() {
  try {
    console.log('Testing database connection...');
    const client = await pool.connect();
    
    // Test episodic memory
    const agentId = `test-agent-${Date.now()}`;
    const sessionId = `test-session-${Math.random().toString(36).substring(2, 15)}`;
    
    // Test episodic memory
    console.log('Testing episodic memory...');
    const episodicResult = await client.query(
      'INSERT INTO episodic_memory (agent_id, session_id, context, tags) VALUES ($1, $2, $3, $4) RETURNING *',
      [agentId, sessionId, JSON.stringify({ test: 'data' }), ['test', 'memory']]
    );
    console.log('✓ Episodic memory stored:', episodicResult.rows[0].id);
    
    // Test semantic memory
    console.log('Testing semantic memory...');
    const semanticResult = await client.query(
      'INSERT INTO semantic_memory (entity, data, category, agent_id, tags) VALUES ($1, $2, $3, $4, $5) RETURNING *',
      [`test-entity-${Date.now()}`, JSON.stringify({ fact: 'test knowledge' }), 'test-category', agentId, ['test', 'semantic']]
    );
    console.log('✓ Semantic memory stored:', semanticResult.rows[0].entity);
    
    // Test working memory
    console.log('Testing working memory...');
    const workingResult = await client.query(
      'INSERT INTO working_memory (agent_id, session_id, key, value) VALUES ($1, $2, $3, $4) RETURNING *',
      [agentId, sessionId, 'test-key', JSON.stringify({ temp: 'data' })]
    );
    console.log('✓ Working memory stored:', workingResult.rows[0].key);
    
    // Test retrieval
    console.log('Testing memory retrieval...');
    const retrieved = await client.query(
      'SELECT * FROM episodic_memory WHERE agent_id = $1 ORDER BY timestamp DESC LIMIT 1',
      [agentId]
    );
    console.log('✓ Retrieved memory:', retrieved.rows[0].context);
    
    client.release();
    console.log('✓ All database tests passed!');
    
  } catch (error) {
    console.error('✗ Database test failed:', error.message);
  } finally {
    await pool.end();
  }
}

verifyDatabase();
