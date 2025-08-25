-- =============================================
-- Assessment State Audit Trail Migration
-- =============================================

-- Create assessment state audit table
CREATE TABLE assessment_state_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id VARCHAR(255) NOT NULL,
    
    -- State transition details
    old_state AssessmentState,
    new_state AssessmentState NOT NULL,
    version_from INTEGER,
    version_to INTEGER,
    
    -- Change metadata
    changed_by VARCHAR(255),  -- User or service making the change
    change_reason TEXT,       -- Optional reason for state change
    change_action VARCHAR(100), -- Action that triggered the change
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Additional context
    context JSONB,            -- Additional context about the change
    ip_address INET,          -- IP address of the requester
    user_agent TEXT           -- User agent of the requester
);

-- Create indexes for audit queries
CREATE INDEX idx_assessment_state_audit_assessment_id ON assessment_state_audit(assessment_id);
CREATE INDEX idx_assessment_state_audit_created_at ON assessment_state_audit(created_at);
CREATE INDEX idx_assessment_state_audit_state_transition ON assessment_state_audit(old_state, new_state);
CREATE INDEX idx_assessment_state_audit_changed_by ON assessment_state_audit(changed_by);

-- Create trigger for automatic audit logging
CREATE OR REPLACE FUNCTION log_assessment_state_audit()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO assessment_state_audit (
        assessment_id,
        old_state,
        new_state,
        version_from,
        version_to,
        changed_by,
        change_reason,
        change_action,
        context,
        ip_address,
        user_agent
    ) VALUES (
        NEW.assessment_id,
        OLD.state,
        NEW.state,
        OLD.version,
        NEW.version,
        NEW.request_data->>'changed_by',
        NEW.request_data->>'change_reason',
        NEW.request_data->>'change_action',
        NEW.request_data->>'context',
        (NEW.request_data->>'ip_address')::INET,
        NEW.request_data->>'user_agent'
    );
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_assessment_state_audit
    AFTER UPDATE ON assessment_states
    FOR EACH ROW EXECUTE FUNCTION log_assessment_state_audit();

-- Create view for audit trail by assessment
CREATE VIEW assessment_audit_summary AS
SELECT 
    assessment_id,
    COUNT(*) AS total_changes,
    MIN(created_at) AS first_change,
    MAX(created_at) AS last_change,
    STRING_AGG(DISTINCT new_state::text, ', ' ORDER BY created_at) AS state_history
FROM assessment_state_audit
GROUP BY assessment_id
ORDER BY last_change DESC;

-- Create view for recent audit changes
CREATE VIEW recent_audit_changes AS
SELECT 
    a.assessment_id,
    a.old_state,
    a.new_state,
    a.changed_by,
    a.change_reason,
    a.change_action,
    a.created_at,
    s.server_name,
    s.assessment_type
FROM assessment_state_audit a
LEFT JOIN LATERAL (
    SELECT request_data->>'serverName' AS server_name,
           request_data->>'assessmentType' AS assessment_type
    FROM assessment_states s
    WHERE s.assessment_id = a.assessment_id
) s ON true
WHERE a.created_at > NOW() - INTERVAL '7 days'
ORDER BY a.created_at DESC;

-- Create function to get audit trail for a specific assessment
CREATE OR REPLACE FUNCTION get_assessment_audit_trail(
    p_assessment_id VARCHAR(255)
) RETURNS TABLE (
    id UUID,
    old_state AssessmentState,
    new_state AssessmentState,
    version_from INTEGER,
    version_to INTEGER,
    changed_by VARCHAR(255),
    change_reason TEXT,
    change_action VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE,
    context JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.id,
        a.old_state,
        a.new_state,
        a.version_from,
        a.version_to,
        a.changed_by,
        a.change_reason,
        a.change_action,
        a.created_at,
        a.context
    FROM assessment_state_audit a
    WHERE a.assessment_id = p_assessment_id
    ORDER BY a.created_at ASC;
END;
$$ LANGUAGE plpgsql;

-- Create function to get audit statistics
CREATE OR REPLACE FUNCTION get_audit_statistics(
    p_days INTEGER DEFAULT 30
) RETURNS TABLE (
    total_changes BIGINT,
    changes_by_state JSONB,
    changes_by_user JSONB,
    top_changed_assessments JSONB,
    audit_period_start TIMESTAMP WITH TIME ZONE,
    audit_period_end TIMESTAMP WITH TIME ZONE
) AS $$
DECLARE
    v_start_date TIMESTAMP WITH TIME ZONE;
BEGIN
    v_start_date := NOW() - (p_days || ' days')::INTERVAL;
    
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT AS total_changes,
        COALESCE(jsonb_object_agg(sa.new_state, COUNT(*)), '{}'::jsonb) AS changes_by_state,
        COALESCE(jsonb_object_agg(sa.changed_by, COUNT(*)), '{}'::jsonb) AS changes_by_user,
        COALESCE(jsonb_agg_jsonb(
            jsonb_build_object(
                'assessment_id', sa.assessment_id,
                'change_count', COUNT(*),
                'last_change', MAX(sa.created_at)
            ) ORDER BY COUNT(*) DESC LIMIT 10
        ), '[]'::jsonb) AS top_changed_assessments,
        v_start_date AS audit_period_start,
        NOW() AS audit_period_end
    FROM assessment_state_audit sa
    WHERE sa.created_at >= v_start_date
    GROUP BY ROLLUP(sa.new_state, sa.changed_by)
    HAVING COUNT(*) > 0;
END;
$$ LANGUAGE plpgsql;

-- Create function to cleanup old audit logs
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(
    p_retention_days INTEGER DEFAULT 90,
    p_batch_size INTEGER DEFAULT 1000
) RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER := 0;
    v_cutoff_date TIMESTAMP WITH TIME ZONE;
BEGIN
    v_cutoff_date := NOW() - (p_retention_days || ' days')::INTERVAL;
    
    -- Delete old audit logs
    DELETE FROM assessment_state_audit 
    WHERE created_at < v_cutoff_date
    LIMIT p_batch_size;
    
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    
    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON assessment_state_audit TO assessment_store_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO assessment_store_user;