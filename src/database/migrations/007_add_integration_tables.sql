-- Migration: Add Integration Tables
-- Description: Creates database tables for MCP and KiloCode integration functionality

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- INTEGRATION SESSIONS TABLE
-- =============================================================================

CREATE TABLE integration_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    integration_type VARCHAR(50) NOT NULL CHECK (integration_type IN ('mcp', 'kilocode', 'memory', 'external_api')),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'failed', 'expired')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Token budget information
    token_budget INTEGER NOT NULL DEFAULT 10000,
    tokens_used INTEGER NOT NULL DEFAULT 0,
    tokens_available INTEGER NOT NULL DEFAULT 10000,
    
    -- Additional session metadata
    metadata JSONB DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT unique_user_session_integration UNIQUE (user_id, session_id, integration_type),
    CONSTRAINT check_token_budget CHECK (token_budget >= 0),
    CONSTRAINT check_tokens_used CHECK (tokens_used >= 0),
    CONSTRAINT check_tokens_available CHECK (tokens_available >= 0),
    CONSTRAINT check_tokens_balance CHECK (tokens_used + tokens_available = token_budget)
);

-- Create index for faster queries
CREATE INDEX idx_integration_sessions_user_id ON integration_sessions(user_id);
CREATE INDEX idx_integration_sessions_session_id ON integration_sessions(session_id);
CREATE INDEX idx_integration_sessions_integration_type ON integration_sessions(integration_type);
CREATE INDEX idx_integration_sessions_status ON integration_sessions(status);
CREATE INDEX idx_integration_sessions_created_at ON integration_sessions(created_at);
CREATE INDEX idx_integration_sessions_expires_at ON integration_sessions(expires_at);

-- =============================================================================
-- INTEGRATION OPERATIONS TABLE
-- =============================================================================

CREATE TABLE integration_operations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES integration_sessions(id) ON DELETE CASCADE,
    operation_type VARCHAR(50) NOT NULL,
    operation_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    
    -- Token usage tracking
    tokens_used INTEGER NOT NULL DEFAULT 0,
    tokens_estimated INTEGER NOT NULL DEFAULT 0,
    token_count_status VARCHAR(20) NOT NULL DEFAULT 'estimated' CHECK (token_count_status IN ('estimated', 'actual', 'adjusted')),
    
    -- Performance metrics
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    -- Request and response data
    request_data JSONB,
    response_data JSONB,
    error_message TEXT,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT check_tokens_used CHECK (tokens_used >= 0),
    CONSTRAINT check_tokens_estimated CHECK (tokens_estimated >= 0),
    CONSTRAINT check_duration_ms CHECK (duration_ms >= 0),
    CONSTRAINT check_operation_status_timeline CHECK (
        (status = 'completed' OR status = 'failed' OR status = 'cancelled') AND completed_at IS NOT NULL OR
        (status = 'running' AND started_at IS NOT NULL AND completed_at IS NULL) OR
        (status = 'pending' AND started_at IS NULL AND completed_at IS NULL)
    )
);

-- Create indexes for faster queries
CREATE INDEX idx_integration_operations_session_id ON integration_operations(session_id);
CREATE INDEX idx_integration_operations_operation_type ON integration_operations(operation_type);
CREATE INDEX idx_integration_operations_operation_name ON integration_operations(operation_name);
CREATE INDEX idx_integration_operations_status ON integration_operations(status);
CREATE INDEX idx_integration_operations_started_at ON integration_operations(started_at);
CREATE INDEX idx_integration_operations_completed_at ON integration_operations(completed_at);
CREATE INDEX idx_integration_operations_tokens_used ON integration_operations(tokens_used);

-- =============================================================================
-- INTEGRATION CONNECTIONS TABLE
-- =============================================================================

CREATE TABLE integration_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_type VARCHAR(50) NOT NULL,
    connection_name VARCHAR(255) NOT NULL,
    endpoint_url TEXT,
    api_key VARCHAR(512),
    auth_token TEXT,
    auth_type VARCHAR(50) DEFAULT 'none' CHECK (auth_type IN ('none', 'api_key', 'bearer_token', 'oauth', 'basic')),
    
    -- Connection status
    status VARCHAR(20) NOT NULL DEFAULT 'disconnected' CHECK (status IN ('disconnected', 'connected', 'error', 'expired')),
    last_connected_at TIMESTAMP WITH TIME ZONE,
    last_error_message TEXT,
    
    -- Rate limiting information
    rate_limit_remaining INTEGER,
    rate_limit_limit INTEGER,
    rate_limit_reset TIMESTAMP WITH TIME ZONE,
    
    -- Configuration
    config JSONB DEFAULT '{}',
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT unique_connection_name UNIQUE (integration_type, connection_name),
    CONSTRAINT check_rate_limit CHECK (rate_limit_limit IS NULL OR rate_limit_limit >= 0),
    CONSTRAINT check_rate_limit_remaining CHECK (rate_limit_remaining IS NULL OR rate_limit_remaining >= 0)
);

-- Create indexes for faster queries
CREATE INDEX idx_integration_connections_integration_type ON integration_connections(integration_type);
CREATE INDEX idx_integration_connections_connection_name ON integration_connections(connection_name);
CREATE INDEX idx_integration_connections_status ON integration_connections(status);
CREATE INDEX idx_integration_connections_last_connected_at ON integration_connections(last_connected_at);

-- =============================================================================
-- INTEGRATION LOGS TABLE
-- =============================================================================

CREATE TABLE integration_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES integration_sessions(id) ON DELETE CASCADE,
    operation_id UUID REFERENCES integration_operations(id) ON DELETE SET NULL,
    
    -- Log level and message
    log_level VARCHAR(10) NOT NULL CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    message TEXT NOT NULL,
    
    -- Context information
    component VARCHAR(100) NOT NULL,
    operation_type VARCHAR(50),
    user_id VARCHAR(255),
    
    -- Additional data
    data JSONB,
    stack_trace TEXT,
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT check_log_level CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
);

-- Create indexes for faster queries
CREATE INDEX idx_integration_logs_session_id ON integration_logs(session_id);
CREATE INDEX idx_integration_logs_operation_id ON integration_logs(operation_id);
CREATE INDEX idx_integration_logs_log_level ON integration_logs(log_level);
CREATE INDEX idx_integration_logs_component ON integration_logs(component);
CREATE INDEX idx_integration_logs_operation_type ON integration_logs(operation_type);
CREATE INDEX idx_integration_logs_user_id ON integration_logs(user_id);
CREATE INDEX idx_integration_logs_created_at ON integration_logs(created_at);

-- =============================================================================
-- INTEGRATION METRICS TABLE
-- =============================================================================

CREATE TABLE integration_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(20, 6) NOT NULL,
    metric_unit VARCHAR(20),
    
    -- Dimensions
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    operation_type VARCHAR(50),
    
    -- Timestamp
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT unique_metric_unique UNIQUE (integration_type, metric_name, user_id, session_id, operation_type, recorded_at)
);

-- Create indexes for faster queries
CREATE INDEX idx_integration_metrics_integration_type ON integration_metrics(integration_type);
CREATE INDEX idx_integration_metrics_metric_name ON integration_metrics(metric_name);
CREATE INDEX idx_integration_metrics_user_id ON integration_metrics(user_id);
CREATE INDEX idx_integration_metrics_session_id ON integration_metrics(session_id);
CREATE INDEX idx_integration_metrics_operation_type ON integration_metrics(operation_type);
CREATE INDEX idx_integration_metrics_recorded_at ON integration_metrics(recorded_at);

-- =============================================================================
-- INTEGRATION QUOTAS TABLE
-- =============================================================================

CREATE TABLE integration_quotas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    integration_type VARCHAR(50) NOT NULL,
    quota_type VARCHAR(50) NOT NULL,
    
    -- Quota limits
    daily_limit INTEGER NOT NULL DEFAULT 10000,
    monthly_limit INTEGER NOT NULL DEFAULT 300000,
    hard_limit INTEGER NOT NULL DEFAULT 1000000,
    
    -- Usage tracking
    daily_tokens_used INTEGER NOT NULL DEFAULT 0,
    monthly_tokens_used INTEGER NOT NULL DEFAULT 0,
    total_tokens_used INTEGER NOT NULL DEFAULT 0,
    
    -- Reset times
    daily_reset_at TIMESTAMP WITH TIME ZONE,
    monthly_reset_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'disabled')),
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT unique_user_quota UNIQUE (user_id, integration_type, quota_type),
    CONSTRAINT check_quota_limits CHECK (daily_limit >= 0 AND monthly_limit >= 0 AND hard_limit >= 0),
    CONSTRAINT check_usage CHECK (daily_tokens_used >= 0 AND monthly_tokens_used >= 0 AND total_tokens_used >= 0),
    CONSTRAINT check_usage_limits CHECK (
        daily_tokens_used <= daily_limit AND
        monthly_tokens_used <= monthly_limit AND
        total_tokens_used <= hard_limit
    )
);

-- Create indexes for faster queries
CREATE INDEX idx_integration_quotas_user_id ON integration_quotas(user_id);
CREATE INDEX idx_integration_quotas_integration_type ON integration_quotas(integration_type);
CREATE INDEX idx_integration_quotas_quota_type ON integration_quotas(quota_type);
CREATE INDEX idx_integration_quotas_status ON integration_quotas(status);
CREATE INDEX idx_integration_quotas_daily_reset_at ON integration_quotas(daily_reset_at);
CREATE INDEX idx_integration_quotas_monthly_reset_at ON integration_quotas(monthly_reset_at);

-- =============================================================================
-- INTEGRATION AUDIT LOGS TABLE
-- =============================================================================

CREATE TABLE integration_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    integration_type VARCHAR(50),
    
    -- Action information
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    
    -- Changes made
    old_values JSONB,
    new_values JSONB,
    
    -- Additional information
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(255),
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT check_action CHECK (action IN ('create', 'read', 'update', 'delete', 'execute', 'auth', 'error'))
);

-- Create indexes for faster queries
CREATE INDEX idx_integration_audit_logs_user_id ON integration_audit_logs(user_id);
CREATE INDEX idx_integration_audit_logs_session_id ON integration_audit_logs(session_id);
CREATE INDEX idx_integration_audit_logs_integration_type ON integration_audit_logs(integration_type);
CREATE INDEX idx_integration_audit_logs_action ON integration_audit_logs(action);
CREATE INDEX idx_integration_audit_logs_resource_type ON integration_audit_logs(resource_type);
CREATE INDEX idx_integration_audit_logs_resource_id ON integration_audit_logs(resource_id);
CREATE INDEX idx_integration_audit_logs_created_at ON integration_audit_logs(created_at);
CREATE INDEX idx_integration_audit_logs_request_id ON integration_audit_logs(request_id);

-- =============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =============================================================================

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_integration_sessions_updated_at 
    BEFORE UPDATE ON integration_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update token usage in sessions
CREATE OR REPLACE FUNCTION update_session_token_usage()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_TABLE_NAME = 'integration_operations' AND TG_OP = 'INSERT' THEN
        IF NEW.tokens_used > 0 THEN
            UPDATE integration_sessions 
            SET tokens_used = tokens_used + NEW.tokens_used,
                tokens_available = token_budget - (tokens_used + NEW.tokens_used),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.session_id;
        END IF;
    ELSIF TG_TABLE_NAME = 'integration_operations' AND TG_OP = 'UPDATE' THEN
        IF OLD.tokens_used != NEW.tokens_used THEN
            UPDATE integration_sessions 
            SET tokens_used = tokens_used - OLD.tokens_used + NEW.tokens_used,
                tokens_available = token_budget - (tokens_used - OLD.tokens_used + NEW.tokens_used),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.session_id;
        END IF;
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_update_session_token_usage
    AFTER INSERT OR UPDATE ON integration_operations
    FOR EACH ROW EXECUTE FUNCTION update_session_token_usage();

-- Trigger to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_TABLE_NAME = 'integration_sessions' AND TG_OP = 'UPDATE' THEN
        IF NEW.expires_at IS NOT NULL AND NEW.expires_at <= CURRENT_TIMESTAMP THEN
            NEW.status = 'expired';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_cleanup_expired_sessions
    BEFORE UPDATE ON integration_sessions
    FOR EACH ROW EXECUTE FUNCTION cleanup_expired_sessions();

-- Trigger to reset daily quotas
CREATE OR REPLACE FUNCTION reset_daily_quotas()
RETURNS EVENT TRIGGER AS $$
DECLARE
    current_time TIMESTAMP WITH TIME ZONE;
    reset_time TIMESTAMP WITH TIME ZONE;
BEGIN
    current_time := CURRENT_TIMESTAMP;
    reset_time := date_trunc('day', current_time) + interval '1 day';
    
    -- Reset daily quotas if it's a new day
    IF date_trunc('day', current_time) != date_trunc('day', pg_last_got_heap_access('integration_quotas')) THEN
        UPDATE integration_quotas
        SET daily_tokens_used = 0,
            daily_reset_at = reset_time,
            last_updated_at = current_time
        WHERE daily_reset_at IS NULL OR daily_reset_at < current_time;
    END IF;
END;
$$ language 'plpgsql';

CREATE EVENT TRIGGER trigger_reset_daily_quotas
    ON ddl_command_end
    WHEN TAG IN ('CREATE TABLE', 'ALTER TABLE', 'DROP TABLE')
    EXECUTE FUNCTION reset_daily_quotas();

-- =============================================================================
-- SAMPLE DATA INSERTIONS
-- =============================================================================

-- Insert sample integration connections
INSERT INTO integration_connections (integration_type, connection_name, endpoint_url, status, config) VALUES
('mcp', 'memory_service', 'http://localhost:8000', 'connected', 
     '{"timeout": 30, "retry_count": 3, "max_retries": 5}'),
('kilocode', 'orchestrator', 'http://localhost:8080', 'connected',
     '{"timeout": 60, "max_concurrent_tasks": 10, "task_timeout": 300}'),
('external_api', 'openai', 'https://api.openai.com/v1', 'connected',
     '{"timeout": 30, "rate_limit": 60, "max_tokens": 4000}'),
('external_api', 'anthropic', 'https://api.anthropic.com', 'connected',
     '{"timeout": 30, "rate_limit": 60, "max_tokens": 4000}');

-- Insert sample integration quotas for demo users
INSERT INTO integration_quotas (user_id, integration_type, quota_type, daily_limit, monthly_limit, hard_limit) VALUES
('demo_user', 'mcp', 'standard', 50000, 1500000, 10000000),
('demo_user', 'kilocode', 'standard', 100000, 3000000, 20000000),
('demo_user', 'memory', 'standard', 25000, 750000, 5000000),
('demo_user', 'external_api', 'standard', 75000, 2250000, 15000000),
('api_user', 'mcp', 'api', 100000, 3000000, 20000000),
('api_user', 'kilocode', 'api', 200000, 6000000, 40000000),
('api_user', 'memory', 'api', 50000, 1500000, 10000000),
('api_user', 'external_api', 'api', 150000, 4500000, 30000000);

-- Grant necessary permissions (adjust as needed for your PostgreSQL setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON integration_sessions TO application_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON integration_operations TO application_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON integration_connections TO application_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON integration_logs TO application_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON integration_metrics TO application_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON integration_quotas TO application_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON integration_audit_logs TO application_user;

-- Grant usage on sequences
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO application_user;

-- Create views for common queries

-- View for active integration sessions
CREATE VIEW active_integration_sessions AS
SELECT 
    id,
    user_id,
    session_id,
    integration_type,
    status,
    token_budget,
    tokens_used,
    tokens_available,
    created_at,
    updated_at,
    expires_at,
    metadata
FROM integration_sessions
WHERE status = 'active' AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP);

-- View for recent integration operations
CREATE VIEW recent_integration_operations AS
SELECT 
    o.id,
    o.session_id,
    s.user_id,
    s.integration_type,
    o.operation_type,
    o.operation_name,
    o.status,
    o.tokens_used,
    o.tokens_estimated,
    o.started_at,
    o.completed_at,
    o.duration_ms,
    o.error_message,
    o.created_at as operation_created_at
FROM integration_operations o
JOIN integration_sessions s ON o.session_id = s.id
WHERE o.created_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY o.created_at DESC;

-- View for integration metrics summary
CREATE VIEW integration_metrics_summary AS
SELECT 
    integration_type,
    metric_name,
    metric_value,
    metric_unit,
    COUNT(*) as record_count,
    MIN(recorded_at) as first_recorded,
    MAX(recorded_at) as last_recorded
FROM integration_metrics
WHERE recorded_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY integration_type, metric_name, metric_value, metric_unit
ORDER BY integration_type, metric_name, last_recorded DESC;

-- View for quota usage summary
CREATE VIEW quota_usage_summary AS
SELECT 
    user_id,
    integration_type,
    quota_type,
    daily_limit,
    daily_tokens_used,
    daily_tokens_used::float / daily_limit * 100 as daily_usage_percent,
    monthly_limit,
    monthly_tokens_used,
    monthly_tokens_used::float / monthly_limit * 100 as monthly_usage_percent,
    hard_limit,
    total_tokens_used,
    total_tokens_used::float / hard_limit * 100 as total_usage_percent,
    status,
    last_updated_at
FROM integration_quotas
ORDER BY user_id, integration_type, quota_type;

-- Comments for documentation
COMMENT ON TABLE integration_sessions IS 'Stores integration session information including token budgets and usage';
COMMENT ON TABLE integration_operations IS 'Tracks individual integration operations with token usage and performance metrics';
COMMENT ON TABLE integration_connections IS 'Manages external API and service connections with authentication';
COMMENT ON TABLE integration_logs IS 'Stores detailed logs for integration operations and debugging';
COMMENT ON TABLE integration_metrics IS 'Collects and stores performance metrics for integration systems';
COMMENT ON TABLE integration_quotas IS 'Manages user quotas and usage limits for integration services';
COMMENT ON TABLE integration_audit_logs IS 'Audit trail for integration system actions and changes';

COMMENT ON COLUMN integration_sessions.token_budget IS 'Total token budget for the session';
COMMENT ON COLUMN integration_sessions.tokens_used IS 'Tokens consumed in this session';
COMMENT ON COLUMN integration_sessions.tokens_available IS 'Remaining tokens in this session';
COMMENT ON COLUMN integration_operations.tokens_used IS 'Actual tokens consumed by this operation';
COMMENT ON COLUMN integration_operations.tokens_estimated IS 'Estimated tokens before operation execution';
COMMENT ON COLUMN integration_operations.duration_ms IS 'Operation execution duration in milliseconds';
COMMENT ON COLUMN integration_quotas.daily_tokens_used IS 'Tokens used in the current day';
COMMENT ON COLUMN integration_quotas.monthly_tokens_used IS 'Tokens used in the current month';
COMMENT ON COLUMN integration_quotas.total_tokens_used IS 'Total tokens used all time';

-- Migration complete
-- Summary: Created comprehensive integration tables for MCP and KiloCode systems
-- Tables include: sessions, operations, connections, logs, metrics, quotas, and audit logs
-- Features: Token budget management, performance tracking, audit trails, and automatic cleanup