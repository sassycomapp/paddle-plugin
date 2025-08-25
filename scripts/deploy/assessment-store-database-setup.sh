#!/bin/bash

# AssessmentStore Database Setup Script
# This script sets up the PostgreSQL database for AssessmentStore persistence

set -e

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-assessment_store}"
DB_USER="${DB_USER:-assessment_user}"
DB_PASSWORD="${DB_PASSWORD:-assessment_password}"
DB_SSL="${DB_SSL:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if PostgreSQL is installed
check_postgres() {
    if ! command -v psql &> /dev/null; then
        error "PostgreSQL is not installed. Please install PostgreSQL first."
    fi
    
    log "PostgreSQL is installed"
}

# Check if database exists
check_database() {
    log "Checking if database '$DB_NAME' exists..."
    
    if ! PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1; then
        log "Database '$DB_NAME' does not exist, creating it..."
        createdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME || error "Failed to create database"
        log "Database '$DB_NAME' created successfully"
    else
        log "Database '$DB_NAME' already exists"
    fi
}

# Create database user
create_user() {
    log "Creating database user '$DB_USER'..."
    
    # Check if user exists
    if ! PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U postgres -tc "SELECT 1 FROM pg_roles WHERE rolname = '$DB_USER'" | grep -q 1; then
        log "User '$DB_USER' does not exist, creating it..."
        createuser -h $DB_HOST -p $DB_PORT -U postgres -s $DB_USER || error "Failed to create user"
        log "User '$DB_USER' created successfully"
    else
        log "User '$DB_USER' already exists"
    fi
    
    # Set password
    log "Setting password for user '$DB_USER'..."
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U postgres -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || error "Failed to set password"
}

# Grant permissions
grant_permissions() {
    log "Granting permissions to user '$DB_USER'..."
    
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U postgres -d $DB_NAME -c "
        GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
        GRANT ALL PRIVILEGES ON SCHEMA public TO $DB_USER;
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
        GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
        GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO $DB_USER;
    " || error "Failed to grant permissions"
    
    log "Permissions granted successfully"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Find migration files
    MIGRATION_DIR="./src/database/migrations"
    if [ ! -d "$MIGRATION_DIR" ]; then
        error "Migration directory not found: $MIGRATION_DIR"
    fi
    
    # Run each migration file
    for migration_file in "$MIGRATION_DIR"/*.sql; do
        if [ -f "$migration_file" ]; then
            log "Running migration: $migration_file"
            PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$migration_file" || error "Failed to run migration: $migration_file"
            log "Migration completed: $migration_file"
        fi
    done
    
    log "All migrations completed successfully"
}

# Create schema_migrations table
create_schema_migrations_table() {
    log "Creating schema_migrations table..."
    
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id SERIAL PRIMARY KEY,
            version VARCHAR(255) NOT NULL,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE (version)
        );
    " || error "Failed to create schema_migrations table"
    
    log "schema_migrations table created successfully"
}

# Record migration versions
record_migrations() {
    log "Recording migration versions..."
    
    MIGRATION_DIR="./src/database/migrations"
    for migration_file in "$MIGRATION_DIR"/*.sql; do
        if [ -f "$migration_file" ]; then
            version=$(basename "$migration_file" | sed 's/[^0-9]*//g')
            if [ -n "$version" ]; then
                log "Recording migration version: $version"
                PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
                    INSERT INTO schema_migrations (version) VALUES ('$version')
                    ON CONFLICT (version) DO NOTHING;
                " || warn "Failed to record migration version: $version"
            fi
        fi
    done
    
    log "Migration versions recorded successfully"
}

# Create indexes for performance
create_indexes() {
    log "Creating performance indexes..."
    
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
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
    " || error "Failed to create indexes"
    
    log "Performance indexes created successfully"
}

# Create database views
create_views() {
    log "Creating database views..."
    
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
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
    " || error "Failed to create views"
    
    log "Database views created successfully"
}

# Test database connection
test_connection() {
    log "Testing database connection..."
    
    if ! PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
        error "Database connection test failed"
    fi
    
    log "Database connection test passed"
}

# Show setup summary
show_summary() {
    log "Database setup completed successfully!"
    echo
    echo "Database Configuration:"
    echo "  Host: $DB_HOST"
    echo "  Port: $DB_PORT"
    echo "  Database: $DB_NAME"
    echo "  User: $DB_USER"
    echo "  SSL: $DB_SSL"
    echo
    echo "Tables Created:"
    echo "  - assessment_states"
    echo "  - assessment_state_audit"
    echo "  - assessment_metrics"
    echo "  - assessment_queue"
    echo "  - schema_migrations"
    echo
    echo "Views Created:"
    echo "  - active_assessments"
    echo "  - completed_assessments_summary"
    echo "  - assessment_statistics"
    echo
    echo "Indexes Created:"
    echo "  - Performance indexes for all tables"
    echo
    echo "Next Steps:"
    echo "  1. Update your application configuration with the database connection details"
    echo "  2. Run your application to test the database integration"
    echo "  3. Monitor database performance and adjust as needed"
}

# Main setup function
main() {
    log "Starting AssessmentStore database setup..."
    
    # Check prerequisites
    check_postgres
    
    # Setup database
    check_database
    create_user
    grant_permissions
    
    # Run migrations
    create_schema_migrations_table
    run_migrations
    record_migrations
    
    # Optimize performance
    create_indexes
    create_views
    
    # Test connection
    test_connection
    
    # Show summary
    show_summary
}

# Run main function
main "$@"