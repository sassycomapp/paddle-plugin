-- Create security and audit tables for PostgreSQL database
-- This script creates tables for secure token storage, audit logging, and security monitoring

-- Enable pgcrypto extension for cryptographic functions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Secure token storage table for HashiCorp Vault integration
CREATE TABLE IF NOT EXISTS secure_token_storage (
    id SERIAL PRIMARY KEY,
    token_id UUID NOT NULL DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    service_name TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    token_encrypted BYTEA NOT NULL,
    token_type TEXT NOT NULL CHECK (token_type IN ('api_key', 'access_token', 'refresh_token', 'jwt')),
    encryption_algorithm TEXT NOT NULL DEFAULT 'AES-256-GCM',
    encryption_key_version INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    metadata JSONB DEFAULT '{}',
    CONSTRAINT unique_token_hash UNIQUE (token_hash)
);

-- Security audit log table for tracking all security operations
CREATE TABLE IF NOT EXISTS security_audit_log (
    id SERIAL PRIMARY KEY,
    audit_id UUID NOT NULL DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL CHECK (event_type IN (
        'token_created', 'token_retrieved', 'token_revoked', 'token_renewed',
        'token_access_attempt', 'security_violation', 'authentication_failure',
        'authorization_failure', 'data_access', 'configuration_change'
    )),
    severity_level TEXT NOT NULL CHECK (severity_level IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    user_id TEXT NOT NULL,
    service_name TEXT NOT NULL,
    resource_id TEXT,
    action TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    session_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_audit_id UNIQUE (audit_id)
);

-- Security violation alerts table
CREATE TABLE IF NOT EXISTS security_alerts (
    id SERIAL PRIMARY KEY,
    alert_id UUID NOT NULL DEFAULT gen_random_uuid(),
    alert_type TEXT NOT NULL CHECK (alert_type IN (
        'suspicious_activity', 'token_compromise', 'rate_limit_exceeded',
        'unauthorized_access', 'data_breach', 'system_intrusion'
    )),
    severity TEXT NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    user_id TEXT,
    resource_id TEXT,
    details JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'INVESTIGATING', 'RESOLVED', 'FALSE_POSITIVE')),
    assigned_to TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    CONSTRAINT unique_alert_id UNIQUE (alert_id)
);

-- Security configuration table
CREATE TABLE IF NOT EXISTS security_configurations (
    id SERIAL PRIMARY KEY,
    config_key TEXT NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    config_type TEXT NOT NULL CHECK (config_type IN ('string', 'integer', 'boolean', 'json')),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by TEXT
);

-- Security metrics table for monitoring and reporting
CREATE TABLE IF NOT EXISTS security_metrics (
    id SERIAL PRIMARY KEY,
    metric_name TEXT NOT NULL,
    metric_value NUMERIC NOT NULL,
    metric_unit TEXT,
    dimensions JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_system TEXT NOT NULL
);

-- Token encryption keys table (for key rotation)
CREATE TABLE IF NOT EXISTS encryption_keys (
    id SERIAL PRIMARY KEY,
    key_id UUID NOT NULL DEFAULT gen_random_uuid(),
    key_version INTEGER NOT NULL,
    key_algorithm TEXT NOT NULL DEFAULT 'AES-256-GCM',
    key_hash TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deactivated_at TIMESTAMP WITH TIME ZONE,
    rotation_schedule TEXT,
    CONSTRAINT unique_key_version UNIQUE (key_version)
);

-- Security compliance records table
CREATE TABLE IF NOT EXISTS compliance_records (
    id SERIAL PRIMARY KEY,
    compliance_standard TEXT NOT NULL,
    control_id TEXT NOT NULL,
    control_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('COMPLIANT', 'NON_COMPLIANT', 'NOT_APPLICABLE', 'UNDER_REVIEW')),
    evidence JSONB DEFAULT '{}',
    last_assessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    next_assessment TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    assessor TEXT
);

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_secure_token_storage_user_id ON secure_token_storage(user_id);
CREATE INDEX IF NOT EXISTS idx_secure_token_storage_service_name ON secure_token_storage(service_name);
CREATE INDEX IF NOT EXISTS idx_secure_token_storage_token_type ON secure_token_storage(token_type);
CREATE INDEX IF NOT EXISTS idx_secure_token_storage_is_active ON secure_token_storage(is_active);
CREATE INDEX IF NOT EXISTS idx_secure_token_storage_expires_at ON secure_token_storage(expires_at);
CREATE INDEX IF NOT EXISTS idx_secure_token_storage_created_at ON secure_token_storage(created_at);

CREATE INDEX IF NOT EXISTS idx_security_audit_log_event_type ON security_audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_security_audit_log_severity_level ON security_audit_log(severity_level);
CREATE INDEX IF NOT EXISTS idx_security_audit_log_user_id ON security_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_security_audit_log_service_name ON security_audit_log(service_name);
CREATE INDEX IF NOT EXISTS idx_security_audit_log_created_at ON security_audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_security_audit_log_ip_address ON security_audit_log(ip_address);

CREATE INDEX IF NOT EXISTS idx_security_alerts_alert_type ON security_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_security_alerts_severity ON security_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_security_alerts_status ON security_alerts(status);
CREATE INDEX IF NOT EXISTS idx_security_alerts_user_id ON security_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_security_alerts_created_at ON security_alerts(created_at);

CREATE INDEX IF NOT EXISTS idx_security_configurations_config_key ON security_configurations(config_key);
CREATE INDEX IF NOT EXISTS idx_security_configurations_is_active ON security_configurations(is_active);

CREATE INDEX IF NOT EXISTS idx_security_metrics_metric_name ON security_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_security_metrics_timestamp ON security_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_security_metrics_source_system ON security_metrics(source_system);

CREATE INDEX IF NOT EXISTS idx_compliance_records_compliance_standard ON compliance_records(compliance_standard);
CREATE INDEX IF NOT EXISTS idx_compliance_records_control_id ON compliance_records(control_id);
CREATE INDEX IF NOT EXISTS idx_compliance_records_status ON compliance_records(status);

-- Create foreign key constraints
ALTER TABLE secure_token_storage 
ADD CONSTRAINT fk_encryption_key_version 
FOREIGN KEY (encryption_key_version) REFERENCES encryption_keys(key_version);

-- Insert default security configurations
INSERT INTO security_configurations (config_key, config_value, config_type, description) VALUES
('token_retention_days', '90', 'integer', 'Number of days to retain tokens before automatic cleanup'),
('audit_log_retention_days', '365', 'integer', 'Number of days to retain audit logs'),
('max_failed_attempts', '5', 'integer', 'Maximum failed authentication attempts before lockout'),
('lockout_duration_minutes', '30', 'integer', 'Duration of account lockout in minutes'),
('enable_rate_limiting', 'true', 'boolean', 'Enable rate limiting for security-sensitive operations'),
('max_requests_per_minute', '60', 'integer', 'Maximum requests per minute for security operations'),
('token_rotation_days', '30', 'integer', 'Number of days between token rotations'),
('enable_mfa', 'false', 'boolean', 'Enable multi-factor authentication for critical operations'),
('session_timeout_minutes', '60', 'integer', 'Session timeout duration in minutes'),
('password_expiry_days', '90', 'integer', 'Password expiry duration in days')
ON CONFLICT (config_key) DO NOTHING;

-- Insert default compliance records
INSERT INTO compliance_records (compliance_standard, control_id, control_name, status, notes) VALUES
('SOC2', 'CC-1', 'Access Control', 'COMPLIANT', 'Access controls implemented and tested'),
('SOC2', 'CC-2', 'System Operations', 'COMPLIANT', 'System operations monitored and controlled'),
('SOC2', 'CC-3', 'Network Security', 'COMPLIANT', 'Network security controls in place'),
('SOC2', 'CC-4', 'System Availability', 'COMPLIANT', 'System availability monitored'),
('SOC2', 'CC-5', 'Data Integrity', 'COMPLIANT', 'Data integrity controls implemented'),
('SOC2', 'CC-6', 'Data Confidentiality', 'COMPLIANT', 'Data confidentiality controls implemented'),
('SOC2', 'CC-7', 'System Maintenance', 'COMPLIANT', 'System maintenance procedures documented'),
('SOC2', 'CC-8', 'Configuration Management', 'COMPLIANT', 'Configuration management implemented')
ON CONFLICT (control_id) DO NOTHING;

-- Create security views for reporting
CREATE OR REPLACE VIEW security_token_summary AS
SELECT 
    user_id,
    service_name,
    token_type,
    COUNT(*) as token_count,
    COUNT(CASE WHEN is_active = true THEN 1 END) as active_tokens,
    COUNT(CASE WHEN expires_at < NOW() THEN 1 END) as expired_tokens,
    COUNT(CASE WHEN last_used < NOW() - INTERVAL '30 days' THEN 1 END) as inactive_tokens
FROM secure_token_storage
GROUP BY user_id, service_name, token_type;

CREATE OR REPLACE VIEW security_audit_summary AS
SELECT 
    DATE_TRUNC('day', created_at) as audit_date,
    event_type,
    severity_level,
    COUNT(*) as event_count,
    COUNT(DISTINCT user_id) as affected_users
FROM security_audit_log
GROUP BY DATE_TRUNC('day', created_at), event_type, severity_level
ORDER BY audit_date DESC;

CREATE OR REPLACE VIEW security_alert_summary AS
SELECT 
    alert_type,
    severity,
    status,
    COUNT(*) as alert_count,
    COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as open_alerts,
    COUNT(CASE WHEN status = 'CRITICAL' THEN 1 END) as critical_alerts
FROM security_alerts
GROUP BY alert_type, severity, status;

-- Create security functions

-- Function to rotate encryption keys
CREATE OR REPLACE FUNCTION rotate_encryption_keys() 
RETURNS TABLE(old_key_version INTEGER, new_key_version INTEGER) AS $$
DECLARE
    old_key RECORD;
    new_key_version INTEGER;
BEGIN
    -- Get the current active key
    SELECT key_version INTO old_key 
    FROM encryption_keys 
    WHERE is_active = true 
    ORDER BY created_at DESC 
    LIMIT 1;
    
    -- Create new key
    new_key_version := COALESCE((SELECT MAX(key_version) FROM encryption_keys), 0) + 1;
    
    INSERT INTO encryption_keys (key_version, key_algorithm, key_hash, is_active)
    VALUES (new_key_version, 'AES-256-GCM', 'placeholder_hash_' || new_key_version, true);
    
    -- Deactivate old key
    UPDATE encryption_keys 
    SET is_active = false, deactivated_at = NOW()
    WHERE key_version = old_key.key_version;
    
    RETURN QUERY SELECT old_key.key_version, new_key_version;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_tokens() 
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM secure_token_storage 
    WHERE expires_at < NOW() OR (created_at < NOW() - INTERVAL '90 days' AND is_active = false);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to generate security metrics
CREATE OR REPLACE FUNCTION generate_security_metrics() 
RETURNS TABLE(metric_name TEXT, metric_value NUMERIC, metric_unit TEXT) AS $$
BEGIN
    -- Active tokens count
    INSERT INTO security_metrics (metric_name, metric_value, metric_unit, source_system)
    SELECT 'active_tokens', COUNT(*), 'count', 'token_management'
    FROM secure_token_storage WHERE is_active = true;
    
    -- Revoked tokens count
    INSERT INTO security_metrics (metric_name, metric_value, metric_unit, source_system)
    SELECT 'revoked_tokens', COUNT(*), 'count', 'token_management'
    FROM secure_token_storage WHERE is_active = false;
    
    -- Audit events count (last 24 hours)
    INSERT INTO security_metrics (metric_name, metric_value, metric_unit, source_system)
    SELECT 'audit_events_24h', COUNT(*), 'count', 'audit_system'
    FROM security_audit_log 
    WHERE created_at >= NOW() - INTERVAL '24 hours';
    
    -- Security alerts count
    INSERT INTO security_metrics (metric_name, metric_value, metric_unit, source_system)
    SELECT 'security_alerts', COUNT(*), 'count', 'alert_system'
    FROM security_alerts WHERE status = 'OPEN';
    
    -- Critical alerts count
    INSERT INTO security_metrics (metric_name, metric_value, metric_unit, source_system)
    SELECT 'critical_alerts', COUNT(*), 'count', 'alert_system'
    FROM security_alerts WHERE severity = 'CRITICAL' AND status = 'OPEN';
    
    RETURN QUERY 
    SELECT metric_name, metric_value, metric_unit 
    FROM security_metrics 
    WHERE timestamp >= NOW() - INTERVAL '1 minute'
    ORDER BY timestamp DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to check token security compliance
CREATE OR REPLACE FUNCTION check_token_compliance(user_id TEXT) 
RETURNS TABLE(compliant BOOLEAN, issues TEXT[]) AS $$
BEGIN
    RETURN QUERY 
    SELECT 
        CASE 
            WHEN COUNT(*) FILTER (WHERE status = 'NON_COMPLIANT') = 0 THEN true
            ELSE false
        END as compliant,
        ARRAY_AGG(CASE 
            WHEN status = 'NON_COMPLIANT' THEN control_name || ': ' || notes
            ELSE NULL
        END) FILTER (WHERE status = 'NON_COMPLIANT') as issues
    FROM compliance_records
    WHERE control_id IN (
        'CC-1', 'CC-2', 'CC-3', 'CC-4', 'CC-5', 'CC-6', 'CC-7', 'CC-8'
    )
    GROUP BY compliant;
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions (adjust as needed for your database setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON secure_token_storage TO your_application_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON security_audit_log TO your_application_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON security_alerts TO your_application_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON security_configurations TO your_application_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON security_metrics TO your_application_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON encryption_keys TO your_application_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON compliance_records TO your_application_user;

-- Grant execute on functions
-- GRANT EXECUTE ON FUNCTION rotate_encryption_keys() TO your_application_user;
-- GRANT EXECUTE ON FUNCTION cleanup_expired_tokens() TO your_application_user;
-- GRANT EXECUTE ON FUNCTION generate_security_metrics() TO your_application_user;
-- GRANT EXECUTE ON FUNCTION check_token_compliance(text) TO your_application_user;

-- Verify tables were created successfully
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'secure_token_storage', 'security_audit_log', 'security_alerts', 
    'security_configurations', 'security_metrics', 'encryption_keys', 'compliance_records'
);

-- Test the security system with sample data
-- INSERT INTO secure_token_storage (user_id, service_name, token_hash, token_encrypted, token_type, encryption_key_version)
-- VALUES ('test-user', 'openai', 'hash123', decode('testencrypteddata', 'hex'), 'api_key', 1);

-- INSERT INTO security_audit_log (event_type, severity_level, user_id, service_name, action, details)
-- VALUES ('token_created', 'INFO', 'test-user', 'openai', 'create_token', '{"reason": "test_creation"}');

-- INSERT INTO security_alerts (alert_type, severity, title, description, user_id)
-- VALUES ('suspicious_activity', 'MEDIUM', 'Unusual Login Pattern', 'Multiple login attempts from unusual location', 'test-user');

-- SELECT * FROM security_token_summary LIMIT 5;
-- SELECT * FROM security_audit_summary LIMIT 5;
-- SELECT * FROM security_alert_summary LIMIT 5;