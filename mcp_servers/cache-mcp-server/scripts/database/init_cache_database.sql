-- Cache Management System Database Initialization Script
-- This script creates the PostgreSQL database and required tables for the cache system

-- Create database (run this as a superuser)
-- CREATE DATABASE paddle_plugin_cache;
-- CREATE USER cache_user WITH PASSWORD '2001';
-- GRANT ALL PRIVILEGES ON DATABASE paddle_plugin_cache TO cache_user;

-- Connect to the target database and run the rest of the script

-- Create extensions
CREATE EXTENSION IF NOT EXISTS pgvector;
CREATE EXTENSION IF NOT EXISTS uuid-ossp;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Create predictive cache table
CREATE TABLE IF NOT EXISTS predictive_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE
);

-- Create semantic cache table
CREATE TABLE IF NOT EXISTS semantic_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    embedding VECTOR(384),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE
);

-- Create vector cache table
CREATE TABLE IF NOT EXISTS vector_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE
);

-- Create vector diary table
CREATE TABLE IF NOT EXISTS vector_diary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    context_type VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    importance_score FLOAT DEFAULT 0.0,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE
);

-- Create indexes for performance
-- Predictive Cache Indexes
CREATE INDEX IF NOT EXISTS idx_predictive_cache_key ON predictive_cache (key);
CREATE INDEX IF NOT EXISTS idx_predictive_cache_expires_at ON predictive_cache (expires_at);
CREATE INDEX IF NOT EXISTS idx_predictive_cache_created_at ON predictive_cache (created_at);

-- Semantic Cache Indexes
CREATE INDEX IF NOT EXISTS idx_semantic_cache_key ON semantic_cache (key);
CREATE INDEX IF NOT EXISTS idx_semantic_cache_expires_at ON semantic_cache (expires_at);
CREATE INDEX IF NOT EXISTS idx_semantic_cache_created_at ON semantic_cache (created_at);
CREATE INDEX IF NOT EXISTS idx_semantic_cache_embedding ON semantic_cache USING hnsw (embedding vector_cosine_ops);

-- Vector Cache Indexes
CREATE INDEX IF NOT EXISTS idx_vector_cache_key ON vector_cache (key);
CREATE INDEX IF NOT EXISTS idx_vector_cache_expires_at ON vector_cache (expires_at);
CREATE INDEX IF NOT EXISTS idx_vector_cache_created_at ON vector_cache (created_at);
CREATE INDEX IF NOT EXISTS idx_vector_cache_embedding ON vector_cache USING hnsw (embedding vector_cosine_ops);

-- Vector Diary Indexes
CREATE INDEX IF NOT EXISTS idx_vector_diary_session_id ON vector_diary (session_id);
CREATE INDEX IF NOT EXISTS idx_vector_diary_expires_at ON vector_diary (expires_at);
CREATE INDEX IF NOT EXISTS idx_vector_diary_created_at ON vector_diary (created_at);
CREATE INDEX IF NOT EXISTS idx_vector_diary_context_type ON vector_diary (context_type);
CREATE INDEX IF NOT EXISTS idx_vector_diary_embedding ON vector_diary USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_vector_diary_importance_score ON vector_diary (importance_score DESC);

-- Create constraints
ALTER TABLE predictive_cache 
ADD CONSTRAINT chk_access_count_non_negative 
CHECK (access_count >= 0);

ALTER TABLE semantic_cache 
ADD CONSTRAINT chk_access_count_non_negative 
CHECK (access_count >= 0);

ALTER TABLE vector_cache 
ADD CONSTRAINT chk_access_count_non_negative 
CHECK (access_count >= 0);

ALTER TABLE vector_diary 
ADD CONSTRAINT chk_access_count_non_negative 
CHECK (access_count >= 0);

ALTER TABLE vector_diary 
ADD CONSTRAINT chk_importance_score_range 
CHECK (importance_score >= 0.0 AND importance_score <= 1.0);

-- Create function to update last_accessed timestamp
CREATE OR REPLACE FUNCTION update_last_accessed()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_accessed = NOW();
    NEW.access_count = COALESCE(NEW.access_count, 0) + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for cache tables
CREATE TRIGGER trg_update_predictive_cache_accessed
AFTER UPDATE ON predictive_cache
FOR EACH ROW
EXECUTE FUNCTION update_last_accessed();

CREATE TRIGGER trg_update_semantic_cache_accessed
AFTER UPDATE ON semantic_cache
FOR EACH ROW
EXECUTE FUNCTION update_last_accessed();

CREATE TRIGGER trg_update_vector_cache_accessed
AFTER UPDATE ON vector_cache
FOR EACH ROW
EXECUTE FUNCTION update_last_accessed();

CREATE TRIGGER trg_update_vector_diary_accessed
AFTER UPDATE ON vector_diary
FOR EACH ROW
EXECUTE FUNCTION update_last_accessed();

-- Create function to clean up expired entries
CREATE OR REPLACE FUNCTION cleanup_expired_entries()
RETURNS VOID AS $$
BEGIN
    DELETE FROM predictive_cache WHERE expires_at IS NOT NULL AND expires_at < NOW();
    DELETE FROM semantic_cache WHERE expires_at IS NOT NULL AND expires_at < NOW();
    DELETE FROM vector_cache WHERE expires_at IS NOT NULL AND expires_at < NOW();
    DELETE FROM vector_diary WHERE expires_at IS NOT NULL AND expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Create function to get cache statistics
CREATE OR REPLACE FUNCTION get_cache_stats()
RETURNS TABLE(
    cache_name TEXT,
    total_entries BIGINT,
    expired_entries BIGINT,
    active_entries BIGINT,
    avg_access_count FLOAT,
    last_accessed TIMESTAMP
) AS $$
BEGIN
    -- Predictive Cache Stats
    RETURN QUERY SELECT 
        'predictive_cache'::TEXT,
        COUNT(*)::BIGINT,
        COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at < NOW() THEN 1 END)::BIGINT,
        COUNT(CASE WHEN expires_at IS NULL OR expires_at >= NOW() THEN 1 END)::BIGINT,
        AVG(access_count)::FLOAT,
        MAX(last_accessed)::TIMESTAMP
    FROM predictive_cache;
    
    -- Semantic Cache Stats
    RETURN QUERY SELECT 
        'semantic_cache'::TEXT,
        COUNT(*)::BIGINT,
        COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at < NOW() THEN 1 END)::BIGINT,
        COUNT(CASE WHEN expires_at IS NULL OR expires_at >= NOW() THEN 1 END)::BIGINT,
        AVG(access_count)::FLOAT,
        MAX(last_accessed)::TIMESTAMP
    FROM semantic_cache;
    
    -- Vector Cache Stats
    RETURN QUERY SELECT 
        'vector_cache'::TEXT,
        COUNT(*)::BIGINT,
        COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at < NOW() THEN 1 END)::BIGINT,
        COUNT(CASE WHEN expires_at IS NULL OR expires_at >= NOW() THEN 1 END)::BIGINT,
        AVG(access_count)::FLOAT,
        MAX(last_accessed)::TIMESTAMP
    FROM vector_cache;
    
    -- Vector Diary Stats
    RETURN QUERY SELECT 
        'vector_diary'::TEXT,
        COUNT(*)::BIGINT,
        COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at < NOW() THEN 1 END)::BIGINT,
        COUNT(CASE WHEN expires_at IS NULL OR expires_at >= NOW() THEN 1 END)::BIGINT,
        AVG(access_count)::FLOAT,
        MAX(last_accessed)::TIMESTAMP
    FROM vector_diary;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cache_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cache_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO cache_user;

-- Create views for easier access
CREATE OR REPLACE VIEW cache_overview AS
SELECT 
    'predictive_cache' as cache_name,
    COUNT(*) as total_entries,
    COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at < NOW() THEN 1 END) as expired_entries,
    COUNT(CASE WHEN expires_at IS NULL OR expires_at >= NOW() THEN 1 END) as active_entries,
    AVG(access_count) as avg_access_count,
    MAX(last_accessed) as last_accessed
FROM predictive_cache

UNION ALL

SELECT 
    'semantic_cache' as cache_name,
    COUNT(*) as total_entries,
    COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at < NOW() THEN 1 END) as expired_entries,
    COUNT(CASE WHEN expires_at IS NULL OR expires_at >= NOW() THEN 1 END) as active_entries,
    AVG(access_count) as avg_access_count,
    MAX(last_accessed) as last_accessed
FROM semantic_cache

UNION ALL

SELECT 
    'vector_cache' as cache_name,
    COUNT(*) as total_entries,
    COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at < NOW() THEN 1 END) as expired_entries,
    COUNT(CASE WHEN expires_at IS NULL OR expires_at >= NOW() THEN 1 END) as active_entries,
    AVG(access_count) as avg_access_count,
    MAX(last_accessed) as last_accessed
FROM vector_cache

UNION ALL

SELECT 
    'vector_diary' as cache_name,
    COUNT(*) as total_entries,
    COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at < NOW() THEN 1 END) as expired_entries,
    COUNT(CASE WHEN expires_at IS NULL OR expires_at >= NOW() THEN 1 END) as active_entries,
    AVG(access_count) as avg_access_count,
    MAX(last_accessed) as last_accessed
FROM vector_diary;

-- Create materialized view for performance monitoring
CREATE MATERIALIZED VIEW cache_performance_stats AS
SELECT 
    NOW() as timestamp,
    'predictive_cache' as cache_name,
    COUNT(*) as total_entries,
    COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at < NOW() THEN 1 END) as expired_entries,
    COUNT(CASE WHEN expires_at IS NULL OR expires_at >= NOW() THEN 1 END) as active_entries,
    AVG(access_count) as avg_access_count,
    MAX(last_accessed) as last_accessed
FROM predictive_cache

UNION ALL

SELECT 
    NOW() as timestamp,
    'semantic_cache' as cache_name,
    COUNT(*) as total_entries,
    COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at < NOW() THEN 1 END) as expired_entries,
    COUNT(CASE WHEN expires_at IS NULL OR expires_at >= NOW() THEN 1 END) as active_entries,
    AVG(access_count) as avg_access_count,
    MAX(last_accessed) as last_accessed
FROM semantic_cache

UNION ALL

SELECT 
    NOW() as timestamp,
    'vector_cache' as cache_name,
    COUNT(*) as total_entries,
    COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at < NOW() THEN 1 END) as expired_entries,
    COUNT(CASE WHEN expires_at IS NULL OR expires_at >= NOW() THEN 1 END) as active_entries,
    AVG(access_count) as avg_access_count,
    MAX(last_accessed) as last_accessed
FROM vector_cache

UNION ALL

SELECT 
    NOW() as timestamp,
    'vector_diary' as cache_name,
    COUNT(*) as total_entries,
    COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at < NOW() THEN 1 END) as expired_entries,
    COUNT(CASE WHEN expires_at IS NULL OR expires_at >= NOW() THEN 1 END) as active_entries,
    AVG(access_count) as avg_access_count,
    MAX(last_accessed) as last_accessed
FROM vector_diary;

-- Create index for the materialized view
CREATE INDEX idx_cache_performance_stats_timestamp ON cache_performance_stats (timestamp, cache_name);

-- Grant permissions on views
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cache_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cache_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO cache_user;
GRANT ALL PRIVILEGES ON ALL MATERIALIZED VIEWS IN SCHEMA public TO cache_user;

-- Create stored procedures for cache management
CREATE OR REPLACE PROCEDURE cleanup_expired_cache_entries()
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM predictive_cache WHERE expires_at IS NOT NULL AND expires_at < NOW();
    DELETE FROM semantic_cache WHERE expires_at IS NOT NULL AND expires_at < NOW();
    DELETE FROM vector_cache WHERE expires_at IS NOT NULL AND expires_at < NOW();
    DELETE FROM vector_diary WHERE expires_at IS NOT NULL AND expires_at < NOW();
    
    RAISE NOTICE 'Expired cache entries cleaned up';
END;
$$;

CREATE OR REPLACE PROCEDURE clear_cache_table(cache_table_name TEXT)
LANGUAGE plpgsql
AS $$
BEGIN
    CASE cache_table_name
        WHEN 'predictive_cache' THEN
            DELETE FROM predictive_cache;
        WHEN 'semantic_cache' THEN
            DELETE FROM semantic_cache;
        WHEN 'vector_cache' THEN
            DELETE FROM vector_cache;
        WHEN 'vector_diary' THEN
            DELETE FROM vector_diary;
        ELSE
            RAISE EXCEPTION 'Unknown cache table: %', cache_table_name;
    END CASE;
    
    RAISE NOTICE 'Cache table % cleared', cache_table_name;
END;
$$;

-- Grant execute permissions on procedures
GRANT EXECUTE ON PROCEDURE cleanup_expired_cache_entries() TO cache_user;
GRANT EXECUTE ON PROCEDURE clear_cache_table(TEXT) TO cache_user;

-- Create a job scheduler for automatic cleanup (requires pg_cron extension)
-- CREATE EXTENSION IF NOT EXISTS pg_cron;
-- SELECT cron.schedule('0 * * * *', $$CALL cleanup_expired_cache_entries()$$);

-- Display completion message
DO $$
BEGIN
    RAISE NOTICE 'Cache Management System database initialized successfully!';
    RAISE NOTICE 'Tables created: predictive_cache, semantic_cache, vector_cache, vector_diary';
    RAISE NOTICE 'Indexes and constraints created for performance and data integrity';
    RAISE NOTICE 'Functions and procedures created for cache management';
    RAISE NOTICE 'Views created for monitoring and reporting';
END $$;