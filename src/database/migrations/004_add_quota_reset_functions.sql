-- Add quota reset functions for PostgreSQL database
-- This script creates functions for automated quota reset operations

-- Enable pg_cron extension if not already enabled
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Create table for tracking quota reset schedules
CREATE TABLE IF NOT EXISTS quota_reset_schedules (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    reset_type TEXT NOT NULL CHECK (reset_type IN ('daily', 'weekly', 'monthly', 'custom')),
    reset_interval INTERVAL NOT NULL DEFAULT '1 day',
    reset_time TIME NOT NULL DEFAULT '00:00:00',
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_reset TIMESTAMP WITH TIME ZONE,
    next_reset TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Create table for tracking quota reset history
CREATE TABLE IF NOT EXISTS quota_reset_history (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER NOT NULL REFERENCES quota_reset_schedules(id),
    user_id TEXT NOT NULL,
    reset_type TEXT NOT NULL,
    reset_start TIMESTAMP WITH TIME ZONE NOT NULL,
    reset_end TIMESTAMP WITH TIME ZONE NOT NULL,
    tokens_reset INTEGER NOT NULL,
    users_affected INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('completed', 'failed', 'partial', 'cancelled')),
    error_message TEXT,
    execution_time INTERVAL NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_quota_reset_schedules_user_id ON quota_reset_schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_quota_reset_schedules_reset_type ON quota_reset_schedules(reset_type);
CREATE INDEX IF NOT EXISTS idx_quota_reset_schedules_is_active ON quota_reset_schedules(is_active);
CREATE INDEX IF NOT EXISTS idx_quota_reset_schedules_next_reset ON quota_reset_schedules(next_reset);
CREATE INDEX IF NOT EXISTS idx_quota_reset_history_schedule_id ON quota_reset_history(schedule_id);
CREATE INDEX IF NOT EXISTS idx_quota_reset_history_user_id ON quota_reset_history(user_id);
CREATE INDEX IF NOT EXISTS idx_quota_reset_history_status ON quota_reset_history(status);
CREATE INDEX IF NOT EXISTS idx_quota_reset_history_created_at ON quota_reset_history(created_at);

-- Function to calculate next reset time
CREATE OR REPLACE FUNCTION calculate_next_reset_time(
    p_reset_type TEXT,
    p_reset_interval INTERVAL,
    p_reset_time TIME,
    p_current_time TIMESTAMP WITH TIME ZONE
) RETURNS TIMESTAMP WITH TIME ZONE AS $$
DECLARE
    next_reset TIMESTAMP WITH TIME ZONE;
    base_date DATE;
BEGIN
    CASE p_reset_type
        WHEN 'daily' THEN
            next_reset := p_current_time::DATE + p_reset_time::TIME + p_reset_interval;
        WHEN 'weekly' THEN
            base_date := p_current_time::DATE;
            -- Find next Monday (start of week)
            IF p_current_time::date < base_date + (1 - EXTRACT(DOW FROM base_date)::integer) * INTERVAL '1 day' THEN
                base_date := base_date + (1 - EXTRACT(DOW FROM base_date)::integer) * INTERVAL '1 day';
            ELSE
                base_date := base_date + (8 - EXTRACT(DOW FROM base_date)::integer) * INTERVAL '1 day';
            END IF;
            next_reset := base_date + p_reset_time::TIME;
        WHEN 'monthly' THEN
            base_date := p_current_time::DATE;
            -- Find first day of next month
            base_date := (base_date + INTERVAL '1 month') - (EXTRACT(DAY FROM base_date)::integer - 1) * INTERVAL '1 day';
            next_reset := base_date + p_reset_time::TIME;
        WHEN 'custom' THEN
            next_reset := p_current_time + p_reset_interval;
        ELSE
            next_reset := p_current_time + p_reset_interval;
    END CASE;
    
    RETURN next_reset;
END;
$$ LANGUAGE plpgsql;

-- Function to reset token usage for a specific user
CREATE OR REPLACE FUNCTION reset_user_token_usage(
    p_user_id TEXT,
    p_reset_start TIMESTAMP WITH TIME ZONE,
    p_reset_end TIMESTAMP WITH TIME ZONE
) RETURNS INTEGER AS $$
DECLARE
    tokens_reset INTEGER;
BEGIN
    -- Reset token usage for the user
    UPDATE token_limits 
    SET tokens_used_in_period = 0,
        period_start = p_reset_end,
        updated_at = NOW()
    WHERE user_id = p_user_id
    AND period_start >= p_reset_start
    AND period_start < p_reset_end;
    
    GET DIAGNOSTICS tokens_reset = ROW_COUNT;
    
    RETURN tokens_reset;
END;
$$ LANGUAGE plpgsql;

-- Function to reset token usage for all users
CREATE OR REPLACE FUNCTION reset_all_token_usage(
    p_reset_start TIMESTAMP WITH TIME ZONE,
    p_reset_end TIMESTAMP WITH TIME ZONE
) RETURNS TABLE(
    user_id TEXT,
    tokens_reset INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        user_id,
        0 as tokens_reset
    FROM token_limits
    WHERE period_start >= p_reset_start
    AND period_start < p_reset_end;
    
    -- Update all user token limits
    UPDATE token_limits
    SET tokens_used_in_period = 0,
        period_start = p_reset_end,
        updated_at = NOW()
    WHERE period_start >= p_reset_start
    AND period_start < p_reset_end;
END;
$$ LANGUAGE plpgsql;

-- Function to execute scheduled quota reset
CREATE OR REPLACE FUNCTION execute_scheduled_quota_reset(
    p_schedule_id INTEGER
) RETURNS TEXT AS $$
DECLARE
    schedule_record RECORD;
    reset_start TIMESTAMP WITH TIME ZONE;
    reset_end TIMESTAMP WITH TIME ZONE;
    execution_start TIMESTAMP WITH TIME ZONE;
    execution_end TIMESTAMP WITH TIME ZONE;
    status TEXT;
    error_message TEXT;
    tokens_reset INTEGER;
    users_affected INTEGER;
BEGIN
    -- Get schedule details
    SELECT * INTO schedule_record
    FROM quota_reset_schedules
    WHERE id = p_schedule_id;
    
    IF NOT FOUND THEN
        RETURN 'Schedule not found';
    END IF;
    
    -- Calculate reset window
    reset_start := schedule_record.last_reset;
    reset_end := schedule_record.next_reset;
    
    IF reset_start IS NULL THEN
        reset_start := schedule_record.created_at;
    END IF;
    
    execution_start := clock_timestamp();
    
    BEGIN
        -- Execute reset based on type
        IF schedule_record.user_id IS NOT NULL THEN
            -- Single user reset
            tokens_reset := reset_user_token_usage(schedule_record.user_id, reset_start, reset_end);
            users_affected := 1;
            status := 'completed';
        ELSE
            -- All users reset
            -- This would need to be implemented with a loop or batch processing
            -- For now, we'll just update the token_limits table directly
            UPDATE token_limits
            SET tokens_used_in_period = 0,
                period_start = reset_end,
                updated_at = NOW()
            WHERE period_start >= reset_start
            AND period_start < reset_end;
            
            tokens_reset := (SELECT COUNT(*) FROM token_limits WHERE period_start >= reset_start AND period_start < reset_end);
            users_affected := (SELECT COUNT(DISTINCT user_id) FROM token_limits WHERE period_start >= reset_start AND period_start < reset_end);
            status := 'completed';
        END IF;
        
        EXCEPTION
            WHEN OTHERS THEN
                status := 'failed';
                error_message := SQLERRM;
                tokens_reset := 0;
                users_affected := 0;
    END;
    
    execution_end := clock_timestamp();
    
    -- Record execution history
    INSERT INTO quota_reset_history (
        schedule_id,
        user_id,
        reset_type,
        reset_start,
        reset_end,
        tokens_reset,
        users_affected,
        status,
        error_message,
        execution_time
    ) VALUES (
        p_schedule_id,
        schedule_record.user_id,
        schedule_record.reset_type,
        reset_start,
        reset_end,
        tokens_reset,
        users_affected,
        status,
        error_message,
        execution_end - execution_start
    );
    
    -- Update schedule with next reset time
    UPDATE quota_reset_schedules
    SET 
        last_reset = reset_end,
        next_reset = calculate_next_reset_time(
            schedule_record.reset_type,
            schedule_record.reset_interval,
            schedule_record.reset_time,
            reset_end
        ),
        updated_at = NOW()
    WHERE id = p_schedule_id;
    
    RETURN status;
END;
$$ LANGUAGE plpgsql;

-- Function to get pending quota resets
CREATE OR REPLACE FUNCTION get_pending_resets(
    p_limit INTEGER DEFAULT 10
) RETURNS TABLE(
    id INTEGER,
    user_id TEXT,
    reset_type TEXT,
    reset_interval INTERVAL,
    reset_time TIME,
    is_active BOOLEAN,
    last_reset TIMESTAMP WITH TIME ZONE,
    next_reset TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        id,
        user_id,
        reset_type,
        reset_interval,
        reset_time,
        is_active,
        last_reset,
        next_reset,
        created_at
    FROM quota_reset_schedules
    WHERE is_active = true
    AND next_reset <= NOW() + INTERVAL '1 hour'
    ORDER BY next_reset ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to cancel a scheduled reset
CREATE OR REPLACE FUNCTION cancel_scheduled_reset(
    p_schedule_id INTEGER
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE quota_reset_schedules
    SET is_active = false,
        updated_at = NOW()
    WHERE id = p_schedule_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to validate reset configuration
CREATE OR REPLACE FUNCTION validate_reset_configuration(
    p_reset_type TEXT,
    p_reset_interval INTERVAL,
    p_reset_time TIME
) RETURNS BOOLEAN AS $$
BEGIN
    -- Validate reset type
    IF p_reset_type NOT IN ('daily', 'weekly', 'monthly', 'custom') THEN
        RETURN false;
    END IF;
    
    -- Validate reset interval for custom type
    IF p_reset_type = 'custom' AND p_reset_interval <= INTERVAL '0 seconds' THEN
        RETURN false;
    END IF;
    
    -- Validate reset time format
    IF p_reset_time IS NULL OR p_reset_time < '00:00:00' OR p_reset_time > '23:59:59' THEN
        RETURN false;
    END IF;
    
    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- Function to get reset history
CREATE OR REPLACE FUNCTION get_reset_history(
    p_user_id TEXT DEFAULT NULL,
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_limit INTEGER DEFAULT 100
) RETURNS TABLE(
    id INTEGER,
    schedule_id INTEGER,
    user_id TEXT,
    reset_type TEXT,
    reset_start TIMESTAMP WITH TIME ZONE,
    reset_end TIMESTAMP WITH TIME ZONE,
    tokens_reset INTEGER,
    users_affected INTEGER,
    status TEXT,
    error_message TEXT,
    execution_time INTERVAL,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        h.id,
        h.schedule_id,
        h.user_id,
        h.reset_type,
        h.reset_start,
        h.reset_end,
        h.tokens_reset,
        h.users_affected,
        h.status,
        h.error_message,
        h.execution_time,
        h.created_at
    FROM quota_reset_history h
    WHERE (p_user_id IS NULL OR h.user_id = p_user_id)
    AND (p_start_date IS NULL OR h.created_at >= p_start_date)
    AND (p_end_date IS NULL OR h.created_at <= p_end_date)
    ORDER BY h.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to schedule quota reset
CREATE OR REPLACE FUNCTION schedule_quota_reset(
    p_user_id TEXT DEFAULT NULL,
    p_reset_type TEXT DEFAULT 'daily',
    p_reset_interval INTERVAL DEFAULT '1 day',
    p_reset_time TIME DEFAULT '00:00:00'
) RETURNS INTEGER AS $$
DECLARE
    schedule_id INTEGER;
    is_valid BOOLEAN;
BEGIN
    -- Validate configuration
    is_valid := validate_reset_configuration(p_reset_type, p_reset_interval, p_reset_time);
    
    IF NOT is_valid THEN
        RAISE EXCEPTION 'Invalid reset configuration';
    END IF;
    
    -- Calculate next reset time
    DECLARE
        next_reset TIMESTAMP WITH TIME ZONE;
    BEGIN
        next_reset := calculate_next_reset_time(p_reset_type, p_reset_interval, p_reset_time, NOW());
        
        -- Insert schedule
        INSERT INTO quota_reset_schedules (
            user_id,
            reset_type,
            reset_interval,
            reset_time,
            next_reset
        ) VALUES (
            p_user_id,
            p_reset_type,
            p_reset_interval,
            p_reset_time,
            next_reset
        ) RETURNING id INTO schedule_id;
        
        RETURN schedule_id;
    END;
END;
$$ LANGUAGE plpgsql;

-- Function to get system health for quota reset
CREATE OR REPLACE FUNCTION get_quota_reset_health() RETURNS TABLE(
    total_schedules INTEGER,
    active_schedules INTEGER,
    pending_resets INTEGER,
    last_reset TIMESTAMP WITH TIME ZONE,
    next_reset TIMESTAMP WITH TIME ZONE,
    system_status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_schedules,
        COUNT(CASE WHEN is_active = true THEN 1 END) as active_schedules,
        COUNT(CASE WHEN is_active = true AND next_reset <= NOW() + INTERVAL '1 hour' THEN 1 END) as pending_resets,
        MAX(last_reset) as last_reset,
        MIN(next_reset) as next_reset,
        CASE 
            WHEN COUNT(CASE WHEN is_active = true AND next_reset <= NOW() + INTERVAL '1 hour' THEN 1 END) > 0 THEN 'pending'
            WHEN COUNT(CASE WHEN is_active = true THEN 1 END) > 0 THEN 'active'
            ELSE 'idle'
        END as system_status
    FROM quota_reset_schedules;
END;
$$ LANGUAGE plpgsql;

-- Create cron job for automatic quota reset execution
-- This will run every minute and execute any pending resets
SELECT cron.schedule('*/1 * * * *', $$SELECT execute_scheduled_quota_reset(id) FROM get_pending_resets(10)$$);

-- Grant necessary permissions
-- GRANT SELECT, INSERT, UPDATE, DELETE ON quota_reset_schedules TO your_application_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON quota_reset_history TO your_application_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_application_user;

-- Verify tables and functions were created successfully
DO $$
BEGIN
    -- Check if tables exist
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'quota_reset_schedules') THEN
        RAISE NOTICE 'quota_reset_schedules table created successfully';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'quota_reset_history') THEN
        RAISE NOTICE 'quota_reset_history table created successfully';
    END IF;
    
    -- Check if functions exist
    IF EXISTS (SELECT FROM information_schema.routines WHERE routine_schema = 'public' AND routine_name = 'calculate_next_reset_time') THEN
        RAISE NOTICE 'calculate_next_reset_time function created successfully';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.routines WHERE routine_schema = 'public' AND routine_name = 'execute_scheduled_quota_reset') THEN
        RAISE NOTICE 'execute_scheduled_quota_reset function created successfully';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.routines WHERE routine_schema = 'public' AND routine_name = 'schedule_quota_reset') THEN
        RAISE NOTICE 'schedule_quota_reset function created successfully';
    END IF;
END $$;