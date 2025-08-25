-- =============================================
-- Assessment State Management Schema Migration
-- =============================================

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create extension for JSONB operations
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create ENUM type for assessment states
CREATE TYPE AssessmentState AS ENUM (
    'pending',        -- Assessment requested, not started
    'processing',     -- Assessment in progress
    'completed',      -- Assessment finished successfully
    'failed',         -- Assessment failed
    'cancelled'       -- Assessment cancelled by user
);

-- Create main assessment states table
CREATE TABLE assessment_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id VARCHAR(255) UNIQUE NOT NULL,
    state AssessmentState NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    
    -- Request and result data
    request_data JSONB NOT NULL,
    result_data JSONB,
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Progress tracking
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    
    -- Priority and retry handling
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    retry_count INTEGER DEFAULT 0,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    timeout_seconds INTEGER DEFAULT 300,
    max_retries INTEGER DEFAULT 3,
    
    -- Constraints
    CONSTRAINT valid_state_transition CHECK (
        -- Ensure completed_at is set only for terminal states
        (state IN ('completed', 'failed', 'cancelled') AND completed_at IS NOT NULL) OR
        (state NOT IN ('completed', 'failed', 'cancelled') AND completed_at IS NULL)
    ),
    
    CONSTRAINT valid_progress CHECK (
        (state = 'processing' AND progress > 0) OR
        (state IN ('completed', 'failed', 'cancelled') AND progress = 100) OR
        (state = 'pending' AND progress = 0)
    )
);

-- Create indexes for performance
CREATE INDEX idx_assessment_states_assessment_id ON assessment_states(assessment_id);
CREATE INDEX idx_assessment_states_state_created ON assessment_states(state, created_at);
CREATE INDEX idx_assessment_states_priority_created ON assessment_states(priority, created_at);
CREATE INDEX idx_assessment_states_next_retry ON assessment_states(next_retry_at) 
    WHERE next_retry_at IS NOT NULL;
CREATE INDEX idx_assessment_states_created_completed ON assessment_states(created_at, completed_at)
    WHERE state IN ('completed', 'failed');

-- Create trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_assessment_states_updated_at 
    BEFORE UPDATE ON assessment_states 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create stored procedure for creating assessments
CREATE OR REPLACE FUNCTION create_assessment(
    p_assessment_id VARCHAR(255),
    p_request_data JSONB,
    p_priority INTEGER DEFAULT 5,
    p_timeout_seconds INTEGER DEFAULT 300
) RETURNS UUID AS $$
DECLARE
    v_new_id UUID;
BEGIN
    INSERT INTO assessment_states (
        assessment_id,
        state,
        request_data,
        priority,
        timeout_seconds
    ) VALUES (
        p_assessment_id,
        'pending',
        p_request_data,
        p_priority,
        p_timeout_seconds
    ) RETURNING id INTO v_new_id;
    
    RETURN v_new_id;
END;
$$ LANGUAGE plpgsql;

-- Create stored procedure for updating assessment state
CREATE OR REPLACE FUNCTION update_assessment_state(
    p_assessment_id VARCHAR(255),
    p_new_state AssessmentState,
    p_version INTEGER,
    p_result_data JSONB DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL,
    p_progress INTEGER DEFAULT NULL,
    p_changed_by VARCHAR(255) DEFAULT NULL,
    p_change_reason TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    v_old_version INTEGER;
    v_old_state AssessmentState;
BEGIN
    -- Get current version and state for optimistic locking
    SELECT version, state INTO v_old_version, v_old_state
    FROM assessment_states
    WHERE assessment_id = p_assessment_id
    FOR UPDATE;
    
    -- Check optimistic lock
    IF v_old_version != p_version THEN
        RAISE EXCEPTION 'Optimistic lock failed. Expected version %, got %', p_version, v_old_version;
    END IF;
    
    -- Update the assessment state
    UPDATE assessment_states 
    SET 
        state = p_new_state,
        version = version + 1,
        result_data = p_result_data,
        error_message = p_error_message,
        progress = COALESCE(p_progress, progress),
        completed_at = CASE 
            WHEN p_new_state IN ('completed', 'failed', 'cancelled') THEN NOW()
            ELSE completed_at 
        END,
        request_data = jsonb_set(
            request_data, 
            '{changed_by}', 
            to_jsonb(p_changed_by), 
            true
        )
    WHERE assessment_id = p_assessment_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Create stored procedure for cleanup old assessments
CREATE OR REPLACE FUNCTION cleanup_old_assessments(
    p_retention_days INTEGER DEFAULT 30,
    p_batch_size INTEGER DEFAULT 1000
) RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER := 0;
    v_cutoff_date TIMESTAMP WITH TIME ZONE;
BEGIN
    v_cutoff_date := NOW() - (p_retention_days || ' days')::INTERVAL;
    
    -- Delete old completed assessments
    DELETE FROM assessment_states 
    WHERE state IN ('completed', 'failed', 'cancelled') 
    AND completed_at < v_cutoff_date
    LIMIT p_batch_size;
    
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    
    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create view for active assessments
CREATE VIEW active_assessments AS
SELECT 
    assessment_id,
    state,
    progress,
    created_at,
    updated_at,
    priority,
    timeout_seconds,
    EXTRACT(EPOCH FROM (NOW() - created_at)) AS duration_seconds
FROM assessment_states
WHERE state IN ('pending', 'processing')
ORDER BY priority ASC, created_at ASC;

-- Create view for completed assessments summary
CREATE VIEW completed_assessments_summary AS
SELECT 
    state,
    COUNT(*) AS count,
    AVG(progress) AS avg_progress,
    MIN(created_at) AS earliest_completed,
    MAX(created_at) AS latest_completed,
    EXTRACT(EPOCH FROM AVG(completed_at - created_at)) AS avg_duration_seconds
FROM assessment_states
WHERE state IN ('completed', 'failed', 'cancelled')
GROUP BY state;

-- Create view for assessment statistics by hour
CREATE VIEW assessment_stats_by_hour AS
SELECT 
    DATE_TRUNC('hour', created_at) AS hour,
    state,
    COUNT(*) AS count
FROM assessment_states
GROUP BY DATE_TRUNC('hour', created_at), state
ORDER BY hour DESC, state;

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO assessment_store_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO assessment_store_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO assessment_store_user;