-- Add performance indexes for token usage logging system
-- This script creates additional indexes to optimize query performance for analytics and reporting

-- Create composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_token_usage_user_date ON token_usage(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_token_usage_session_date ON token_usage(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_token_usage_endpoint_date ON token_usage(api_endpoint, timestamp);
CREATE INDEX IF NOT EXISTS idx_token_usage_priority_date ON token_usage(priority_level, timestamp);

-- Create indexes for analytics queries
CREATE INDEX IF NOT EXISTS idx_token_usage_user_endpoint ON token_usage(user_id, api_endpoint);
CREATE INDEX IF NOT EXISTS idx_token_usage_user_priority ON token_usage(user_id, priority_level);
CREATE INDEX IF NOT EXISTS idx_token_usage_endpoint_priority ON token_usage(api_endpoint, priority_level);

-- Create indexes for time-based aggregations
CREATE INDEX IF NOT EXISTS idx_token_usage_date_hour ON token_usage(timestamp);
CREATE INDEX IF NOT EXISTS idx_token_usage_date_day ON token_usage(timestamp::date);
CREATE INDEX IF NOT EXISTS idx_token_usage_date_month ON token_usage(timestamp::date);

-- Create indexes for range queries
CREATE INDEX IF NOT EXISTS idx_token_usage_tokens_range ON token_usage(tokens_used);
CREATE INDEX IF NOT EXISTS idx_token_usage_user_tokens_range ON token_usage(user_id, tokens_used);

-- Create indexes for sorting operations
CREATE INDEX IF NOT EXISTS idx_token_usage_timestamp_desc ON token_usage(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_token_usage_tokens_used_desc ON token_usage(tokens_used DESC);

-- Create indexes for token limits table optimization
CREATE INDEX IF NOT EXISTS idx_token_limits_user_period_active ON token_limits(user_id, period_start) 
WHERE period_start >= NOW() - INTERVAL '30 days';

-- Create indexes for token revocations table optimization
CREATE INDEX IF NOT EXISTS idx_token_revocations_recent ON token_revocations(revoked_at DESC);

-- Create partial indexes for common filtering scenarios
CREATE INDEX IF NOT EXISTS idx_token_usage_high_priority ON token_usage(priority_level) 
WHERE priority_level = 'High';

CREATE INDEX IF NOT EXISTS idx_token_usage_medium_priority ON token_usage(priority_level) 
WHERE priority_level = 'Medium';

CREATE INDEX IF NOT EXISTS idx_token_usage_low_priority ON token_usage(priority_level) 
WHERE priority_level = 'Low';

-- Create indexes for specific API endpoints that are frequently used
CREATE INDEX IF NOT EXISTS idx_token_usage_chat_completions ON token_usage(api_endpoint) 
WHERE api_endpoint = '/chat/completions';

CREATE INDEX IF NOT EXISTS idx_token_usage_embeddings ON token_usage(api_endpoint) 
WHERE api_endpoint = '/embeddings';

-- Create indexes for user session tracking
CREATE INDEX IF NOT EXISTS idx_token_usage_active_sessions ON token_usage(session_id, timestamp) 
WHERE timestamp >= NOW() - INTERVAL '7 days';

-- Create indexes for token usage summary queries
CREATE INDEX IF NOT EXISTS idx_token_usage_summary_user_date ON token_usage(user_id, timestamp::date);
CREATE INDEX IF NOT EXISTS idx_token_usage_summary_endpoint_date ON token_usage(api_endpoint, timestamp::date);

-- Create indexes for trend analysis
CREATE INDEX IF NOT EXISTS idx_token_usage_trend_user ON token_usage(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_token_usage_trend_endpoint ON token_usage(api_endpoint, timestamp);

-- Create indexes for export operations
CREATE INDEX IF NOT EXISTS idx_token_usage_export_date ON token_usage(timestamp::date);
CREATE INDEX IF NOT EXISTS idx_token_usage_export_user ON token_usage(user_id);

-- Create indexes for cleanup operations
CREATE INDEX IF NOT EXISTS idx_token_usage_cleanup_old ON token_usage(timestamp) 
WHERE timestamp < NOW() - INTERVAL '30 days';

-- Verify indexes were created successfully
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename IN ('token_usage', 'token_limits', 'token_revocations')
ORDER BY tablename, indexname;

-- Display index statistics
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
FROM pg_stat_user_indexes 
WHERE tablename IN ('token_usage', 'token_limits', 'token_revocations')
ORDER BY tablename, indexname;

-- Grant necessary permissions for the new indexes (adjust as needed for your database setup)
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO your_application_user;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO your_application_user;

-- Analyze tables to update statistics
ANALYZE token_usage;
ANALYZE token_limits;
ANALYZE token_revocations;

-- Test the indexes with sample queries
-- Test user-specific queries
EXPLAIN (ANALYZE, BUFFERS) 
SELECT COUNT(*) FROM token_usage 
WHERE user_id = 'test-user' 
AND timestamp >= NOW() - INTERVAL '7 days';

-- Test endpoint-specific queries
EXPLAIN (ANALYZE, BUFFERS) 
SELECT COUNT(*) FROM token_usage 
WHERE api_endpoint = '/chat/completions' 
AND timestamp >= NOW() - INTERVAL '1 day';

-- Test summary queries
EXPLAIN (ANALYZE, BUFFERS) 
SELECT 
    user_id,
    COUNT(*) as request_count,
    SUM(tokens_used) as total_tokens,
    AVG(tokens_used) as avg_tokens
FROM token_usage 
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY user_id
ORDER BY total_tokens DESC
LIMIT 10;

-- Test trend analysis queries
EXPLAIN (ANALYZE, BUFFERS) 
SELECT 
    DATE(timestamp) as usage_date,
    COUNT(*) as request_count,
    SUM(tokens_used) as total_tokens
FROM token_usage 
WHERE user_id = 'test-user'
AND timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY usage_date;

-- Test export queries
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM token_usage 
WHERE timestamp >= NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC
LIMIT 1000;

-- Test cleanup queries
EXPLAIN (ANALYZE, BUFFERS) 
DELETE FROM token_usage 
WHERE timestamp < NOW() - INTERVAL '30 days'
RETURNING COUNT(*);

-- Display completion message
SELECT 'Token usage performance indexes created successfully' as message;