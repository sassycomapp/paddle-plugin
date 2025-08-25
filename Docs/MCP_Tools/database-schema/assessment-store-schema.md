# AssessmentStore Database Schema

## Overview

This document provides the complete database schema for the AssessmentStore service, designed to replace the EventEmitter-based system with centralized state management.

## Schema Files

### 1. Main Assessment State Table

```sql
-- =============================================
-- Assessment State Management Schema
-- =============================================

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
```

### 2. Audit Trail Table

```sql
-- =============================================
-- Assessment State Audit Trail
-- =============================================

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
```

### 3. Performance Optimization Tables

```sql
-- =============================================
-- Performance Optimization Tables
-- =============================================

-- Cache table for frequently accessed assessment states
CREATE TABLE assessment_state_cache (
    assessment_id VARCHAR(255) PRIMARY KEY,
    state_data JSONB NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    access_count INTEGER DEFAULT 0
);

-- Index for cache expiration
CREATE INDEX idx_assessment_state_cache_expires ON assessment_state_cache(expires_at);

-- Metrics table for performance monitoring
CREATE TABLE assessment_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id VARCHAR(255) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,  -- 'processing_time', 'error_count', 'retry_count'
    metric_value INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for metrics queries
    INDEX idx_assessment_metrics_assessment_id (assessment_id),
    INDEX idx_assessment_metrics_type_timestamp (metric_type, timestamp)
);

-- Queue table for batch processing
CREATE TABLE assessment_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id VARCHAR(255) NOT NULL,
    queue_type VARCHAR(50) NOT NULL,  -- 'processing', 'retry', 'cleanup'
    priority INTEGER DEFAULT 5,
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    processing_attempts INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- Indexes for queue management
    INDEX idx_assessment_queue_type_scheduled (queue_type, scheduled_at),
    INDEX idx_assessment_queue_priority_scheduled (priority, scheduled_at),
    UNIQUE UNIQUE_assessment_queue_assessment_id (assessment_id, queue_type)
);
```

### 4. Foreign Key Constraints and Relationships

```sql
-- =============================================
-- Foreign Key Constraints
-- =============================================

-- Add foreign key constraint for audit trail (if using assessment_states.id as reference)
-- ALTER TABLE assessment_state_audit 
-- ADD CONSTRAINT fk_assessment_state_audit_assessment 
-- FOREIGN KEY (assessment_id) REFERENCES assessment_states(assessment_id);

-- Add foreign key constraint for metrics
-- ALTER TABLE assessment_metrics 
-- ADD CONSTRAINT fk_assessment_metrics_assessment 
-- FOREIGN KEY (assessment_id) REFERENCES assessment_states(assessment_id);

-- Add foreign key constraint for queue
-- ALTER TABLE assessment_queue 
-- ADD CONSTRAINT fk_assessment_queue_assessment 
-- FOREIGN KEY (assessment_id) REFERENCES assessment_states(assessment_id);
```

### 5. Database Views

```sql
-- =============================================
-- Database Views for Reporting
-- =============================================

-- View for active assessments
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

-- View for completed assessments summary
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

-- View for assessment statistics by hour
CREATE VIEW assessment_stats_by_hour AS
SELECT 
    DATE_TRUNC('hour', created_at) AS hour,
    state,
    COUNT(*) AS count
FROM assessment_states
GROUP BY DATE_TRUNC('hour', created_at), state
ORDER BY hour DESC, state;
```

### 6. Stored Procedures for Common Operations

```sql
-- =============================================
-- Stored Procedures
-- =============================================

-- Procedure to create a new assessment
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

-- Procedure to update assessment state
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

-- Procedure to cleanup old assessments
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
```

### 7. Database Initialization Script

```sql
-- =============================================
-- Database Initialization Script
-- =============================================

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create extension for JSONB operations
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Run all schema creation in a transaction
BEGIN;

-- Execute all the CREATE TABLE, TYPE, and FUNCTION statements above
-- Add any additional setup needed here

-- Commit the transaction
COMMIT;

-- Create database user for AssessmentStore
-- CREATE USER assessment_store_user WITH PASSWORD 'secure_password';
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO assessment_store_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO assessment_store_user;
```

## Schema Design Principles

### 1. Normalization
- **Third Normal Form**: All tables are properly normalized to reduce redundancy
- **JSONB for Semi-Structured Data**: Use JSONB for flexible request/result data
- **Separation of Concerns**: Audit data separated from main state data

### 2. Performance Optimization
- **Strategic Indexing**: Indexes on frequently queried columns
- **Partial Indexes**: Specialized indexes for common query patterns
- **Covering Indexes**: Indexes that cover common query requirements

### 3. Data Integrity
- **Constraints**: CHECK constraints for data validation
- **Foreign Keys**: Referential integrity between related tables
- **Triggers**: Automated audit logging and timestamp updates

### 4. Scalability
- **Partitioning Ready**: Schema designed for future partitioning by date
- **Connection Pooling**: Optimized for connection pool usage
- **Read Optimization**: Views and indexes optimized for reporting queries

## Migration Considerations

### 1. Data Migration from Event System
```sql
-- Example migration query to import existing assessments
INSERT INTO assessment_states (
    assessment_id,
    state,
    request_data,
    created_at,
    updated_at
)
SELECT 
    assessment_id,
    'completed' as state,
    jsonb_build_object(
        'serverName', server_name,
        'assessmentType', assessment_type,
        'options', options,
        'timestamp', timestamp,
        'source', source
    ) as request_data,
    created_at,
    updated_at
FROM existing_assessments
WHERE status = 'completed';
```

### 2. Index Strategy for Migration
- **Disable Indexes**: Temporarily disable non-critical indexes during bulk import
- **Batch Processing**: Process data in batches to avoid memory issues
- **Validation**: Post-migration validation checks

### 3. Performance Monitoring
- **Query Analysis**: Monitor slow queries during and after migration
- **Index Usage**: Track index usage and optimize as needed
- **Resource Monitoring**: Monitor CPU, memory, and I/O during migration

## Backup and Recovery Strategy

### 1. Regular Backups
- **Full Backups**: Daily full database backups
- **Point-in-Time Recovery**: WAL archiving for point-in-time recovery
- **Logical Backups**: pg_dump for schema and data portability

### 2. Recovery Procedures
- **AssessmentStore Recovery**: Specific procedures for AssessmentStore data recovery
- **Point-in-Time Recovery**: Procedures for recovering to specific timestamps
- **Validation Scripts**: Scripts to validate recovered data integrity

This schema provides a solid foundation for the AssessmentStore service, ensuring data integrity, performance, and scalability while supporting the migration from the existing event-based system.