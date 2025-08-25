-- Create token management tables for PostgreSQL database
-- This script creates the tables for tracking token usage, enforcing quotas, and managing revocations

-- Enable pg_tiktoken extension if not already enabled (should be done in previous migration)
-- CREATE EXTENSION IF NOT EXISTS pg_tiktoken;

-- Log tokens consumed per request with user and session context
CREATE TABLE IF NOT EXISTS token_usage (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    tokens_used INT NOT NULL,
    api_endpoint TEXT NOT NULL,
    priority_level TEXT NOT NULL CHECK (priority_level IN ('Low', 'Medium', 'High')),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Store per-user or per-API token quota and limits
CREATE TABLE IF NOT EXISTS token_limits (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    max_tokens_per_period INT NOT NULL,
    period_interval INTERVAL NOT NULL DEFAULT '1 day',
    tokens_used_in_period INT NOT NULL DEFAULT 0,
    period_start TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Optional table for revoked tokens if applicable
CREATE TABLE IF NOT EXISTS token_revocations (
    token TEXT PRIMARY KEY,
    revoked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reason TEXT
);

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_token_usage_user_id ON token_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_session_id ON token_usage(session_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_timestamp ON token_usage(timestamp);
CREATE INDEX IF NOT EXISTS idx_token_usage_user_session ON token_usage(user_id, session_id);

CREATE INDEX IF NOT EXISTS idx_token_limits_user_id ON token_limits(user_id);
CREATE INDEX IF NOT EXISTS idx_token_limits_period_start ON token_limits(period_start);
CREATE INDEX IF NOT EXISTS idx_token_limits_user_period ON token_limits(user_id, period_start);

CREATE INDEX IF NOT EXISTS idx_token_revocations_token ON token_revocations(token);
CREATE INDEX IF NOT EXISTS idx_token_revocations_revoked_at ON token_revocations(revoked_at);

-- Create unique constraint to ensure only one active token limit per user per period
CREATE UNIQUE INDEX IF NOT EXISTS idx_token_limits_user_period_unique 
ON token_limits(user_id, period_start);

-- Verify tables were created successfully
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('token_usage', 'token_limits', 'token_revocations');

-- Insert sample data for testing (optional)
-- INSERT INTO token_limits (user_id, max_tokens_per_period, period_interval) 
-- VALUES ('test-user', 10000, '1 day');

-- Test the tables with sample data
-- INSERT INTO token_usage (user_id, session_id, tokens_used, api_endpoint, priority_level)
-- VALUES ('test-user', 'test-session', 150, 'chat/completions', 'Medium');

-- SELECT * FROM token_usage LIMIT 5;
-- SELECT * FROM token_limits LIMIT 5;
-- SELECT * FROM token_revocations LIMIT 5;

-- Grant necessary permissions (adjust as needed for your database setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON token_usage TO your_application_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON token_limits TO your_application_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON token_revocations TO your_application_user;