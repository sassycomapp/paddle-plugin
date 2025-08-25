-- Agent Memory System Database Schema
-- Creates tables for episodic, semantic, and working memory

CREATE TABLE IF NOT EXISTS episodic_memory (
  id SERIAL PRIMARY KEY,
  agent_id VARCHAR(255) NOT NULL,
  session_id VARCHAR(255),
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  context JSONB,
  memory_type VARCHAR(50) DEFAULT 'episodic',
  relevance_score FLOAT DEFAULT 1.0,
  tags TEXT[],
  CONSTRAINT unique_agent_session_memory UNIQUE (agent_id, session_id, context)
);

CREATE TABLE IF NOT EXISTS semantic_memory (
  id SERIAL PRIMARY KEY,
  entity VARCHAR(255) NOT NULL,
  data JSONB,
  category VARCHAR(100),
  last_updated TIMESTAMPTZ DEFAULT NOW(),
  access_count INTEGER DEFAULT 0,
  tags TEXT[],
  agent_id VARCHAR(255),
  CONSTRAINT unique_entity_agent UNIQUE (entity, agent_id)
);

CREATE TABLE IF NOT EXISTS working_memory (
  id SERIAL PRIMARY KEY,
  agent_id VARCHAR(255) NOT NULL,
  session_id VARCHAR(255) NOT NULL,
  key VARCHAR(255) NOT NULL,
  value JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ,
  UNIQUE(agent_id, session_id, key)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_episodic_agent_time ON episodic_memory (agent_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_episodic_session ON episodic_memory (session_id);
CREATE INDEX IF NOT EXISTS idx_episodic_tags ON episodic_memory USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_episodic_context ON episodic_memory USING GIN (context);

CREATE INDEX IF NOT EXISTS idx_semantic_entity ON semantic_memory (entity);
CREATE INDEX IF NOT EXISTS idx_semantic_category ON semantic_memory (category);
CREATE INDEX IF NOT EXISTS idx_semantic_agent ON semantic_memory (agent_id);
CREATE INDEX IF NOT EXISTS idx_semantic_tags ON semantic_memory USING GIN (tags);

CREATE INDEX IF NOT EXISTS idx_working_agent_session ON working_memory (agent_id, session_id);
CREATE INDEX IF NOT EXISTS idx_working_expires ON working_memory (expires_at) WHERE expires_at IS NOT NULL;

-- Insert sample data for testing
INSERT INTO episodic_memory (agent_id, session_id, context, memory_type, tags) VALUES
('system', 'setup', '{"event": "memory_system_initialization", "description": "Agent memory system tables created"}', 'system', ARRAY['setup', 'initialization']);

INSERT INTO semantic_memory (entity, data, category, agent_id, tags) VALUES
('agent_memory_system', '{"description": "Unified agent memory system with PostgreSQL and Memory Bank integration", "version": "1.0.0", "components": ["PostgreSQL", "Memory Bank", "MCP Servers"]}', 'system', 'system', ARRAY['architecture', 'documentation']);

-- Verify table creation
SELECT 
  schemaname,
  tablename,
  tableowner
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN ('episodic_memory', 'semantic_memory', 'working_memory')
ORDER BY tablename;
