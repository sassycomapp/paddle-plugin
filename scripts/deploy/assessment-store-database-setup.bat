@echo off
REM AssessmentStore Database Setup Script for Windows
REM This script sets up the PostgreSQL database for AssessmentStore persistence

setlocal enabledelayedexpansion

REM Configuration
set "DB_HOST=localhost"
set "DB_PORT=5432"
set "DB_NAME=assessment_store"
set "DB_USER=assessment_user"
set "DB_PASSWORD=assessment_password"
set "DB_SSL=false"

REM Colors for output
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "NC=[0m"

REM Logging function
:log
echo %GREEN%[%date% %time%]%NC% %~1
goto :eof

:warn
echo %YELLOW%[%date% %time%]%NC% WARNING: %~1
goto :eof

:error
echo %RED%[%date% %time%]%NC% ERROR: %~1
exit /b 1

REM Check if PostgreSQL is installed
:check_postgres
call :log "Checking if PostgreSQL is installed..."

where psql >nul 2>&1
if %errorlevel% neq 0 (
    call :error "PostgreSQL is not installed. Please install PostgreSQL first."
)

call :log "PostgreSQL is installed"
goto :eof

REM Check if database exists
:check_database
call :log "Checking if database '%DB_NAME%' exists..."

psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -tc "SELECT 1 FROM pg_database WHERE datname = '%DB_NAME%'" | findstr "1" >nul
if %errorlevel% neq 0 (
    call :log "Database '%DB_NAME%' does not exist, creating it..."
    createdb -h %DB_HOST% -p %DB_PORT% -U %DB_USER% %DB_NAME%
    if %errorlevel% neq 0 (
        call :error "Failed to create database"
    )
    call :log "Database '%DB_NAME%' created successfully"
) else (
    call :log "Database '%DB_NAME%' already exists"
)
goto :eof

REM Create database user
:create_user
call :log "Creating database user '%DB_USER%'..."

REM Check if user exists
psql -h %DB_HOST% -p %DB_PORT% -U postgres -tc "SELECT 1 FROM pg_roles WHERE rolname = '%DB_USER%'" | findstr "1" >nul
if %errorlevel% neq 0 (
    call :log "User '%DB_USER%' does not exist, creating it..."
    createuser -h %DB_HOST% -p %DB_PORT% -U postgres -s %DB_USER%
    if %errorlevel% neq 0 (
        call :error "Failed to create user"
    )
    call :log "User '%DB_USER%' created successfully"
) else (
    call :log "User '%DB_USER%' already exists"
)

REM Set password
call :log "Setting password for user '%DB_USER%'..."
psql -h %DB_HOST% -p %DB_PORT% -U postgres -c "ALTER USER %DB_USER% WITH PASSWORD '%DB_PASSWORD%';"
if %errorlevel% neq 0 (
    call :error "Failed to set password"
)
goto :eof

REM Grant permissions
:grant_permissions
call :log "Granting permissions to user '%DB_USER%'..."

psql -h %DB_HOST% -p %DB_PORT% -U postgres -d %DB_NAME% -c "
    GRANT ALL PRIVILEGES ON DATABASE %DB_NAME% TO %DB_USER%;
    GRANT ALL PRIVILEGES ON SCHEMA public TO %DB_USER%;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO %DB_USER%;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO %DB_USER%;
    GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO %DB_USER%;
"
if %errorlevel% neq 0 (
    call :error "Failed to grant permissions"
)

call :log "Permissions granted successfully"
goto :eof

REM Run database migrations
:run_migrations
call :log "Running database migrations..."

REM Find migration files
set "MIGRATION_DIR=src\database\migrations"
if not exist "%MIGRATION_DIR%" (
    call :error "Migration directory not found: %MIGRATION_DIR%"
)

REM Run each migration file
for %%f in ("%MIGRATION_DIR%\*.sql") do (
    call :log "Running migration: %%~nxf"
    psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -f "%%f"
    if %errorlevel% neq 0 (
        call :error "Failed to run migration: %%~nxf"
    )
    call :log "Migration completed: %%~nxf"
)

call :log "All migrations completed successfully"
goto :eof

REM Create schema_migrations table
:create_schema_migrations_table
call :log "Creating schema_migrations table..."

psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -c "
    CREATE TABLE IF NOT EXISTS schema_migrations (
        id SERIAL PRIMARY KEY,
        version VARCHAR(255) NOT NULL,
        applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE (version)
    );
"
if %errorlevel% neq 0 (
    call :error "Failed to create schema_migrations table"
)

call :log "schema_migrations table created successfully"
goto :eof

REM Record migration versions
:record_migrations
call :log "Recording migration versions..."

set "MIGRATION_DIR=src\database\migrations"
for %%f in ("%MIGRATION_DIR%\*.sql") do (
    set "version=%%~nf"
    set "version=!version:*_=!"
    if not "!version!"=="" (
        call :log "Recording migration version: !version!"
        psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -c "
            INSERT INTO schema_migrations (version) VALUES ('!version!')
            ON CONFLICT (version) DO NOTHING;
        "
        if %errorlevel% neq 0 (
            call :warn "Failed to record migration version: !version!"
        )
    )
)

call :log "Migration versions recorded successfully"
goto :eof

REM Create indexes for performance
:create_indexes
call :log "Creating performance indexes..."

psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -c "
    -- Create indexes for assessment_states table
    CREATE INDEX IF NOT EXISTS idx_assessment_states_assessment_id ON assessment_states(assessment_id);
    CREATE INDEX IF NOT EXISTS idx_assessment_states_state_created ON assessment_states(state, created_at);
    CREATE INDEX IF NOT EXISTS idx_assessment_states_priority_created ON assessment_states(priority, created_at);
    CREATE INDEX IF NOT EXISTS idx_assessment_states_next_retry ON assessment_states(next_retry_at) WHERE next_retry_at IS NOT NULL;
    CREATE INDEX IF NOT EXISTS idx_assessment_states_created_completed ON assessment_states(created_at, completed_at) WHERE state IN ('completed', 'failed');
    
    -- Create indexes for assessment_state_audit table
    CREATE INDEX IF NOT EXISTS idx_assessment_state_audit_assessment_id ON assessment_state_audit(assessment_id);
    CREATE INDEX IF NOT EXISTS idx_assessment_state_audit_created_at ON assessment_state_audit(created_at);
    CREATE INDEX IF NOT EXISTS idx_assessment_state_audit_state_transition ON assessment_state_audit(old_state, new_state);
    CREATE INDEX IF NOT EXISTS idx_assessment_state_audit_changed_by ON assessment_state_audit(changed_by);
    
    -- Create indexes for assessment_metrics table
    CREATE INDEX IF NOT EXISTS idx_assessment_metrics_assessment_id ON assessment_metrics(assessment_id);
    CREATE INDEX IF NOT EXISTS idx_assessment_metrics_type_timestamp ON assessment_metrics(metric_type, timestamp);
    
    -- Create indexes for assessment_queue table
    CREATE INDEX IF NOT EXISTS idx_assessment_queue_type_scheduled ON assessment_queue(queue_type, scheduled_at);
    CREATE INDEX IF NOT EXISTS idx_assessment_queue_priority_scheduled ON assessment_queue(priority, scheduled_at);
"
if %errorlevel% neq 0 (
    call :error "Failed to create indexes"
)

call :log "Performance indexes created successfully"
goto :eof

REM Create database views
:create_views
call :log "Creating database views..."

psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -c "
    -- Create view for active assessments
    CREATE OR REPLACE VIEW active_assessments AS
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
    CREATE OR REPLACE VIEW completed_assessments_summary AS
    SELECT 
        state,
        COUNT(*) AS count,
        AVG(progress) AS avg_progress,
        MIN(created_at) AS earliest_completed,
        MAX(created_at) AS latest_completed,
        EXTRACT(EPOCH FROM AVG(NOW() - completed_at)) AS avg_completion_time
    FROM assessment_states
    WHERE state IN ('completed', 'failed')
    GROUP BY state;
    
    -- Create view for assessment statistics
    CREATE OR REPLACE VIEW assessment_statistics AS
    SELECT 
        COUNT(*) AS total_assessments,
        COUNT(CASE WHEN state = 'pending' THEN 1 END) AS pending_count,
        COUNT(CASE WHEN state = 'processing' THEN 1 END) AS processing_count,
        COUNT(CASE WHEN state = 'completed' THEN 1 END) AS completed_count,
        COUNT(CASE WHEN state = 'failed' THEN 1 END) AS failed_count,
        COUNT(CASE WHEN state = 'cancelled' THEN 1 END) AS cancelled_count,
        AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) AS avg_processing_time,
        COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) AS recent_assessments
    FROM assessment_states;
"
if %errorlevel% neq 0 (
    call :error "Failed to create views"
)

call :log "Database views created successfully"
goto :eof

REM Test database connection
:test_connection
call :log "Testing database connection..."

psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -c "SELECT 1;" >nul 2>&1
if %errorlevel% neq 0 (
    call :error "Database connection test failed"
)

call :log "Database connection test passed"
goto :eof

REM Show setup summary
:show_summary
call :log "Database setup completed successfully!"
echo.
echo Database Configuration:
echo   Host: %DB_HOST%
echo   Port: %DB_PORT%
echo   Database: %DB_NAME%
echo   User: %DB_USER%
echo   SSL: %DB_SSL%
echo.
echo Tables Created:
echo   - assessment_states
echo   - assessment_state_audit
echo   - assessment_metrics
echo   - assessment_queue
echo   - schema_migrations
echo.
echo Views Created:
echo   - active_assessments
echo   - completed_assessments_summary
echo   - assessment_statistics
echo.
echo Indexes Created:
echo   - Performance indexes for all tables
echo.
echo Next Steps:
echo   1. Update your application configuration with the database connection details
echo   2. Run your application to test the database integration
echo   3. Monitor database performance and adjust as needed
goto :eof

REM Main setup function
:main
call :log "Starting AssessmentStore database setup..."

REM Check prerequisites
call :check_postgres

REM Setup database
call :check_database
call :create_user
call :grant_permissions

REM Run migrations
call :create_schema_migrations_table
call :run_migrations
call :record_migrations

REM Optimize performance
call :create_indexes
call :create_views

REM Test connection
call :test_connection

REM Show summary
call :show_summary

endlocal
exit /b 0