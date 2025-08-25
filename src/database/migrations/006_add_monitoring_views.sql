-- Add monitoring views for comprehensive token usage analytics
-- This script creates views that support monitoring, reporting, and alerting functionality

-- Create view for real-time token usage status
CREATE OR REPLACE VIEW token_usage_status AS
SELECT 
    tu.user_id,
    tu.session_id,
    tu.tokens_used,
    tu.api_endpoint,
    tu.priority_level,
    tu.timestamp,
    tl.max_tokens_per_period,
    tl.tokens_used_in_period,
    tl.period_start,
    tl.period_interval,
    -- Calculate remaining tokens
    (tl.max_tokens_per_period - tl.tokens_used_in_period) AS remaining_tokens,
    -- Calculate usage percentage
    ROUND((tl.tokens_used_in_period::float / tl.max_tokens_per_period) * 100, 2) AS usage_percentage,
    -- Calculate days until period reset
    EXTRACT(EPOCH FROM (tl.period_start + 
        CASE 
            WHEN tl.period_interval = '1 day' THEN INTERVAL '1 day'
            WHEN tl.period_interval = '7 days' THEN INTERVAL '7 days'
            WHEN tl.period_interval = '30 days' THEN INTERVAL '30 days'
            ELSE INTERVAL '1 day'
        END - NOW())) / 86400 AS days_until_reset,
    -- Flag for users approaching limits
    CASE 
        WHEN (tl.tokens_used_in_period::float / tl.max_tokens_per_period) > 0.8 THEN 'warning'
        WHEN (tl.tokens_used_in_period::float / tl.max_tokens_per_period) > 0.95 THEN 'critical'
        ELSE 'normal'
    END AS status_flag,
    -- Count requests in current period
    COUNT(*) OVER (PARTITION BY tu.user_id, DATE_TRUNC('day', tl.period_start)) AS requests_in_period
FROM token_usage tu
JOIN token_limits tl ON tu.user_id = tl.user_id
WHERE tl.period_start >= NOW() - INTERVAL '30 days'
ORDER BY tu.timestamp DESC;

-- Create view for hourly token usage trends
CREATE OR REPLACE VIEW token_usage_hourly_trends AS
SELECT 
    DATE_TRUNC('hour', timestamp) AS hour_timestamp,
    user_id,
    COUNT(*) AS request_count,
    SUM(tokens_used) AS total_tokens_used,
    AVG(tokens_used) AS avg_tokens_per_request,
    MAX(tokens_used) AS max_tokens_in_request,
    MIN(tokens_used) AS min_tokens_in_request,
    COUNT(DISTINCT user_id) AS unique_users,
    COUNT(DISTINCT api_endpoint) AS unique_endpoints,
    -- Calculate tokens per user
    SUM(tokens_used) / COUNT(DISTINCT user_id) AS tokens_per_user
FROM token_usage
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('hour', timestamp), user_id
ORDER BY hour_timestamp DESC, user_id;

-- Create view for daily token usage analytics
CREATE OR REPLACE VIEW token_usage_daily_analytics AS
SELECT 
    DATE(timestamp) AS usage_date,
    user_id,
    COUNT(*) AS daily_requests,
    SUM(tokens_used) AS daily_tokens_used,
    AVG(tokens_used) AS avg_tokens_per_request,
    MAX(tokens_used) AS peak_tokens_request,
    MIN(tokens_used) AS min_tokens_request,
    -- Calculate rolling averages
    AVG(SUM(tokens_used)) OVER (
        PARTITION BY user_id 
        ORDER BY DATE(timestamp) 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_7day_avg,
    -- Calculate growth rate
    CASE 
        WHEN LAG(SUM(tokens_used), 1) OVER (
            PARTITION BY user_id 
            ORDER BY DATE(timestamp)
        ) IS NULL THEN 0
        ELSE (SUM(tokens_used) - LAG(SUM(tokens_used), 1) OVER (
            PARTITION BY user_id 
            ORDER BY DATE(timestamp)
        )) * 100.0 / LAG(SUM(tokens_used), 1) OVER (
            PARTITION BY user_id 
            ORDER BY DATE(timestamp)
        )
    END AS growth_rate_percentage,
    -- Identify anomalous usage
    CASE 
        WHEN SUM(tokens_used) > (
            SELECT AVG(daily_tokens) * 3 
            FROM (
                SELECT DATE(timestamp) AS date, SUM(tokens_used) AS daily_tokens
                FROM token_usage
                WHERE timestamp >= NOW() - INTERVAL '30 days'
                GROUP BY DATE(timestamp)
            ) subq
        ) THEN 'anomaly_high'
        WHEN SUM(tokens_used) < (
            SELECT AVG(daily_tokens) * 0.3 
            FROM (
                SELECT DATE(timestamp) AS date, SUM(tokens_used) AS daily_tokens
                FROM token_usage
                WHERE timestamp >= NOW() - INTERVAL '30 days'
                GROUP BY DATE(timestamp)
            ) subq
        ) THEN 'anomaly_low'
        ELSE 'normal'
    END AS anomaly_flag
FROM token_usage
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE(timestamp), user_id
ORDER BY usage_date DESC, user_id;

-- Create view for API endpoint usage analysis
CREATE OR REPLACE VIEW api_endpoint_usage AS
SELECT 
    api_endpoint,
    COUNT(*) AS total_requests,
    SUM(tokens_used) AS total_tokens_used,
    AVG(tokens_used) AS avg_tokens_per_request,
    MAX(tokens_used) AS max_tokens_used,
    MIN(tokens_used) AS min_tokens_used,
    COUNT(DISTINCT user_id) AS unique_users,
    -- Calculate usage trends
    SUM(tokens_used) FILTER (WHERE timestamp >= NOW() - INTERVAL '7 days') AS tokens_last_7days,
    SUM(tokens_used) FILTER (WHERE timestamp >= NOW() - INTERVAL '1 day') AS tokens_last_24hours,
    -- Calculate growth
    CASE 
        WHEN SUM(tokens_used) FILTER (WHERE timestamp >= NOW() - INTERVAL '7 days') = 0 THEN 0
        ELSE (SUM(tokens_used) FILTER (WHERE timestamp >= NOW() - INTERVAL '1 day') * 7.0) / 
             NULLIF(SUM(tokens_used) FILTER (WHERE timestamp >= NOW() - INTERVAL '7 days'), 0)
    END AS daily_growth_factor,
    -- Priority distribution
    COUNT(*) FILTER (WHERE priority_level = 'High') AS high_priority_requests,
    COUNT(*) FILTER (WHERE priority_level = 'Medium') AS medium_priority_requests,
    COUNT(*) FILTER (WHERE priority_level = 'Low') AS low_priority_requests,
    -- Time-based analysis
    EXTRACT(HOUR FROM MIN(timestamp)) AS first_hour_used,
    EXTRACT(HOUR FROM MAX(timestamp)) AS last_hour_used,
    EXTRACT(DOW FROM MIN(timestamp)) AS first_day_of_week_used
FROM token_usage
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY api_endpoint
ORDER BY total_tokens_used DESC;

-- Create view for user quota compliance monitoring
CREATE OR REPLACE VIEW user_quota_compliance AS
SELECT 
    tl.user_id,
    tl.max_tokens_per_period,
    tl.tokens_used_in_period,
    (tl.max_tokens_per_period - tl.tokens_used_in_period) AS remaining_tokens,
    ROUND((tl.tokens_used_in_period::float / tl.max_tokens_per_period) * 100, 2) AS usage_percentage,
    tl.period_start,
    tl.period_interval,
    -- Calculate compliance status
    CASE 
        WHEN (tl.tokens_used_in_period::float / tl.max_tokens_per_period) > 1.0 THEN 'violated'
        WHEN (tl.tokens_used_in_period::float / tl.max_tokens_per_period) > 0.9 THEN 'warning'
        WHEN (tl.tokens_used_in_period::float / tl.max_tokens_per_period) > 0.75 THEN 'caution'
        ELSE 'compliant'
    END AS compliance_status,
    -- Count recent violations
    COUNT(*) FILTER (WHERE tu.timestamp >= NOW() - INTERVAL '7 days' AND tu.tokens_used > 1000) AS recent_large_requests,
    -- Calculate average daily usage
    tl.tokens_used_in_period / GREATEST(
        EXTRACT(EPOCH FROM (NOW() - tl.period_start)) / 86400,
        1
    ) AS average_daily_usage,
    -- Projected usage at current rate
    tl.tokens_used_in_period + (
        tl.tokens_used_in_period / GREATEST(
            EXTRACT(EPOCH FROM (NOW() - tl.period_start)) / 86400,
            1
        ) * EXTRACT(EPOCH FROM (
            CASE 
                WHEN tl.period_interval = '1 day' THEN INTERVAL '1 day'
                WHEN tl.period_interval = '7 days' THEN INTERVAL '7 days'
                WHEN tl.period_interval = '30 days' THEN INTERVAL '30 days'
                ELSE INTERVAL '1 day'
            END - (NOW() - tl.period_start)
        )) / 86400
    ) AS projected_usage,
    -- Days until projected violation
    CASE 
        WHEN (tl.tokens_used_in_period::float / tl.max_tokens_per_period) >= 1.0 THEN 0
        ELSE (
            (tl.max_tokens_per_period - tl.tokens_used_in_period) / GREATEST(
                tl.tokens_used_in_period / GREATEST(
                    EXTRACT(EPOCH FROM (NOW() - tl.period_start)) / 86400,
                    1
                ),
                1
            )
        )
    END AS estimated_days_until_violation
FROM token_limits tl
LEFT JOIN token_usage tu ON tl.user_id = tu.user_id AND tu.timestamp >= NOW() - INTERVAL '7 days'
WHERE tl.period_start >= NOW() - INTERVAL '30 days'
GROUP BY tl.user_id, tl.max_tokens_per_period, tl.tokens_used_in_period, 
         tl.period_start, tl.period_interval
ORDER BY usage_percentage DESC;

-- Create view for system health metrics
CREATE OR REPLACE VIEW system_health_metrics AS
WITH request_stats AS (
    SELECT 
        COUNT(*) AS total_requests_24h,
        COUNT(*) FILTER (WHERE timestamp >= NOW() - INTERVAL '1 hour') AS requests_last_hour,
        AVG(tokens_used) AS avg_tokens_per_request,
        MAX(tokens_used) AS max_tokens_single_request,
        COUNT(DISTINCT user_id) AS active_users_24h,
        COUNT(DISTINCT api_endpoint) AS active_endpoints
    FROM token_usage
    WHERE timestamp >= NOW() - INTERVAL '24 hours'
),
user_stats AS (
    SELECT 
        COUNT(*) AS total_users_with_limits,
        COUNT(*) FILTER (WHERE usage_percentage > 80) AS users_high_usage,
        COUNT(*) FILTER (WHERE usage_percentage > 95) AS users_critical_usage,
        AVG(usage_percentage) AS avg_usage_percentage,
        MAX(usage_percentage) AS max_usage_percentage
    FROM user_quota_compliance
),
error_stats AS (
    SELECT 
        COUNT(*) AS total_requests,
        COUNT(*) FILTER (WHERE priority_level = 'High') AS high_priority_requests,
        COUNT(*) FILTER (WHERE timestamp >= NOW() - INTERVAL '1 hour') AS recent_requests
    FROM token_usage
    WHERE timestamp >= NOW() - INTERVAL '24 hours'
)
SELECT 
    NOW() AS metric_timestamp,
    rs.total_requests_24h,
    rs.requests_last_hour,
    rs.avg_tokens_per_request,
    rs.max_tokens_single_request,
    rs.active_users_24h,
    rs.active_endpoints,
    us.total_users_with_limits,
    us.users_high_usage,
    us.users_critical_usage,
    us.avg_usage_percentage,
    us.max_usage_percentage,
    es.total_requests,
    es.high_priority_requests,
    es.recent_requests,
    -- Calculate system load indicators
    CASE 
        WHEN rs.requests_last_hour > 1000 THEN 'high'
        WHEN rs.requests_last_hour > 500 THEN 'medium'
        ELSE 'low'
    END AS system_load,
    CASE 
        WHEN us.users_critical_usage > 5 THEN 'critical'
        WHEN us.users_critical_usage > 2 THEN 'warning'
        WHEN us.users_high_usage > 10 THEN 'caution'
        ELSE 'normal'
    END AS quota_status,
    -- Calculate error rates (simplified)
    CASE 
        WHEN es.high_priority_requests::float / NULLIF(es.total_requests, 0) > 0.1 THEN 'high_error_rate'
        WHEN es.high_priority_requests::float / NULLIF(es.total_requests, 0) > 0.05 THEN 'medium_error_rate'
        ELSE 'normal'
    END AS error_rate_status
FROM request_stats rs, user_stats us, error_stats es;

-- Create view for alerting triggers
CREATE OR REPLACE VIEW alerting_triggers AS
SELECT 
    user_id,
    'quota_violation' AS alert_type,
    usage_percentage AS trigger_value,
    'User has exceeded token quota' AS alert_message,
    NOW() AS trigger_timestamp,
    CASE 
        WHEN usage_percentage > 100 THEN 'critical'
        WHEN usage_percentage > 95 THEN 'high'
        WHEN usage_percentage > 90 THEN 'medium'
        ELSE 'low'
    END AS severity_level
FROM user_quota_compliance
WHERE usage_percentage > 90

UNION ALL

SELECT 
    user_id,
    'anomalous_usage' AS alert_type,
    AVG(tokens_used) AS trigger_value,
    'User showing anomalous token consumption pattern' AS alert_message,
    NOW() AS trigger_timestamp,
    'medium' AS severity_level
FROM token_usage
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY user_id
HAVING AVG(tokens_used) > (
    SELECT AVG(avg_tokens) * 3 
    FROM (
        SELECT AVG(tokens_used) AS avg_tokens
        FROM token_usage
        WHERE timestamp >= NOW() - INTERVAL '7 days'
        GROUP BY user_id
    ) subq
)

UNION ALL

SELECT 
    'system' AS user_id,
    'system_overload' AS alert_type,
    requests_last_hour AS trigger_value,
    'System experiencing high request volume' AS alert_message,
    NOW() AS trigger_timestamp,
    CASE 
        WHEN requests_last_hour > 2000 THEN 'critical'
        WHEN requests_last_hour > 1000 THEN 'high'
        ELSE 'medium'
    END AS severity_level
FROM system_health_metrics
WHERE requests_last_hour > 500

ORDER BY trigger_timestamp DESC, severity_level DESC;

-- Create indexes for optimal performance on monitoring views
CREATE INDEX IF NOT EXISTS idx_token_usage_status_user_timestamp ON token_usage_status(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_token_usage_status_usage_percentage ON token_usage_status(usage_percentage DESC);
CREATE INDEX IF NOT EXISTS idx_token_usage_hourly_trends_timestamp ON token_usage_hourly_trends(hour_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_token_usage_daily_analytics_date ON token_usage_daily_analytics(usage_date DESC);
CREATE INDEX IF NOT EXISTS idx_api_endpoint_usage_tokens ON api_endpoint_usage(total_tokens_used DESC);
CREATE INDEX IF NOT EXISTS idx_user_quota_compliance_usage ON user_quota_compliance(usage_percentage DESC);
CREATE INDEX IF NOT EXISTS idx_system_health_metrics_timestamp ON system_health_metrics(metric_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_alerting_triggers_severity ON alerting_triggers(severity_level DESC, trigger_timestamp DESC);

-- Create materialized view for frequently accessed analytics data
CREATE MATERIALIZED VIEW IF NOT EXISTS token_usage_analytics_materialized AS
SELECT 
    DATE_TRUNC('day', timestamp) AS day,
    user_id,
    api_endpoint,
    COUNT(*) AS request_count,
    SUM(tokens_used) AS total_tokens,
    AVG(tokens_used) AS avg_tokens_per_request
FROM token_usage
WHERE timestamp >= NOW() - INTERVAL '90 days'
GROUP BY DATE_TRUNC('day', timestamp), user_id, api_endpoint
WITH DATA;

-- Create refresh function for materialized view
CREATE OR REPLACE FUNCTION refresh_token_usage_analytics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY token_usage_analytics_materialized;
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions (adjust as needed for your database setup)
-- GRANT SELECT ON token_usage_status TO your_application_user;
-- GRANT SELECT ON token_usage_hourly_trends TO your_application_user;
-- GRANT SELECT ON token_usage_daily_analytics TO your_application_user;
-- GRANT SELECT ON api_endpoint_usage TO your_application_user;
-- GRANT SELECT ON user_quota_compliance TO your_application_user;
-- GRANT SELECT ON system_health_metrics TO your_application_user;
-- GRANT SELECT ON alerting_triggers TO your_application_user;
-- GRANT SELECT ON token_usage_analytics_materialized TO your_application_user;
-- GRANT EXECUTE ON FUNCTION refresh_token_usage_analytics() TO your_application_user;

-- Verify views were created successfully
SELECT table_name 
FROM information_schema.views 
WHERE table_schema = 'public' 
AND table_name LIKE 'token_usage_%'
ORDER BY table_name;

SELECT matviewname 
FROM pg_matviews 
WHERE schemaname = 'public' 
AND matviewname = 'token_usage_analytics_materialized';

-- Test the monitoring views with sample queries
-- SELECT * FROM token_usage_status LIMIT 10;
-- SELECT * FROM token_usage_hourly_trends LIMIT 10;
-- SELECT * FROM user_quota_compliance ORDER BY usage_percentage DESC LIMIT 10;
-- SELECT * FROM system_health_metrics;
-- SELECT * FROM alerting_triggers ORDER BY trigger_timestamp DESC LIMIT 10;