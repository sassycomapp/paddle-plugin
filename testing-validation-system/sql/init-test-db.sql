-- Test Management Database Schema
-- This schema supports comprehensive testing and validation tracking

-- Test Suites table
CREATE TABLE IF NOT EXISTS test_suites (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL CHECK (type IN ('unit', 'integration', 'e2e', 'security', 'performance')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Test Cases table
CREATE TABLE IF NOT EXISTS test_cases (
    id SERIAL PRIMARY KEY,
    suite_id INTEGER REFERENCES test_suites(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    file_path VARCHAR(500),
    test_function VARCHAR(255),
    tags TEXT[], -- Array of tags for categorization
    priority VARCHAR(20) CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Test Executions table (tracks each test run)
CREATE TABLE IF NOT EXISTS test_executions (
    id SERIAL PRIMARY KEY,
    suite_id INTEGER REFERENCES test_suites(id) ON DELETE CASCADE,
    execution_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    environment VARCHAR(100), -- e.g., 'local', 'podman', 'ci'
    branch VARCHAR(100),
    commit_hash VARCHAR(40),
    metadata JSONB
);

-- Test Results table (individual test outcomes)
CREATE TABLE IF NOT EXISTS test_results (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER REFERENCES test_executions(id) ON DELETE CASCADE,
    case_id INTEGER REFERENCES test_cases(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL CHECK (status IN ('passed', 'failed', 'skipped', 'error')),
    duration_ms INTEGER,
    error_message TEXT,
    stack_trace TEXT,
    logs TEXT,
    screenshots TEXT[], -- Array of screenshot paths for UI tests
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Static Analysis Results (Semgrep findings)
CREATE TABLE IF NOT EXISTS static_analysis_results (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER REFERENCES test_executions(id) ON DELETE CASCADE,
    rule_id VARCHAR(255),
    severity VARCHAR(20) CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    file_path VARCHAR(500),
    line_number INTEGER,
    column_start INTEGER,
    column_end INTEGER,
    message TEXT,
    fix_suggestions TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance Metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER REFERENCES test_executions(id) ON DELETE CASCADE,
    metric_name VARCHAR(255) NOT NULL,
    metric_value NUMERIC,
    unit VARCHAR(50),
    threshold NUMERIC,
    status VARCHAR(20) CHECK (status IN ('pass', 'fail', 'warning')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Remediation Actions table
CREATE TABLE IF NOT EXISTS remediation_actions (
    id SERIAL PRIMARY KEY,
    result_id INTEGER REFERENCES test_results(id) ON DELETE CASCADE,
    action_type VARCHAR(100), -- e.g., 'code_fix', 'config_change', 'dependency_update'
    description TEXT,
    ai_suggestion TEXT,
    implemented_by VARCHAR(255),
    implemented_at TIMESTAMPTZ,
    status VARCHAR(50) CHECK (status IN ('pending', 'in_progress', 'completed', 'rejected')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Test Coverage table
CREATE TABLE IF NOT EXISTS test_coverage (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER REFERENCES test_executions(id) ON DELETE CASCADE,
    file_path VARCHAR(500),
    lines_total INTEGER,
    lines_covered INTEGER,
    coverage_percentage NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_test_cases_suite_id ON test_cases(suite_id);
CREATE INDEX IF NOT EXISTS idx_test_results_execution_id ON test_results(execution_id);
CREATE INDEX IF NOT EXISTS idx_test_results_case_id ON test_results(case_id);
CREATE INDEX IF NOT EXISTS idx_test_executions_suite_id ON test_executions(suite_id);
CREATE INDEX IF NOT EXISTS idx_static_analysis_execution_id ON static_analysis_results(execution_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_execution_id ON performance_metrics(execution_id);

-- Views for reporting
CREATE OR REPLACE VIEW test_summary AS
SELECT 
    s.name as suite_name,
    s.type,
    e.execution_name,
    e.status as execution_status,
    e.started_at,
    e.completed_at,
    COUNT(r.id) as total_tests,
    COUNT(CASE WHEN r.status = 'passed' THEN 1 END) as passed_tests,
    COUNT(CASE WHEN r.status = 'failed' THEN 1 END) as failed_tests,
    COUNT(CASE WHEN r.status = 'skipped' THEN 1 END) as skipped_tests,
    AVG(r.duration_ms) as avg_duration_ms
FROM test_suites s
JOIN test_executions e ON s.id = e.suite_id
LEFT JOIN test_results r ON e.id = r.execution_id
GROUP BY s.id, s.name, s.type, e.id, e.execution_name, e.status, e.started_at, e.completed_at;

CREATE OR REPLACE VIEW security_summary AS
SELECT 
    e.execution_name,
    COUNT(s.id) as total_findings,
    COUNT(CASE WHEN s.severity = 'critical' THEN 1 END) as critical_findings,
    COUNT(CASE WHEN s.severity = 'error' THEN 1 END) as error_findings,
    COUNT(CASE WHEN s.severity = 'warning' THEN 1 END) as warning_findings,
    COUNT(CASE WHEN s.severity = 'info' THEN 1 END) as info_findings
FROM test_executions e
LEFT JOIN static_analysis_results s ON e.id = s.execution_id
WHERE s.id IS NOT NULL
GROUP BY e.id, e.execution_name;
