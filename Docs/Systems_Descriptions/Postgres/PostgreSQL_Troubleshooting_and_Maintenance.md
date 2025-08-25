# PostgreSQL Troubleshooting and Maintenance Guide

## Table of Contents
1. [Common Issues and Solutions](#common-issues-and-solutions)
2. [Service Management](#service-management)
3. [Connection Troubleshooting](#connection-troubleshooting)
4. [Performance Optimization](#performance-optimization)
5. [Backup and Recovery](#backup-and-recovery)
6. [Security Maintenance](#security-maintenance)
7. [pgvector Extension Issues](#pgvector-extension-issues)
8. [MCP Server Troubleshooting](#mcp-server-troubleshooting)
9. [Monitoring and Health Checks](#monitoring-and-health-checks)
10. [Emergency Procedures](#emergency-procedures)

## Common Issues and Solutions

### 1. PostgreSQL Service Issues

#### Problem: Service won't start
```powershell
# Check service status
Get-Service -Name postgresql-x64-17

# Check Windows Event Viewer for errors
# Look in: Applications and Services Logs → PostgreSQL
```

**Solutions:**
1. **Check data directory permissions**
   ```powershell
   # Ensure PostgreSQL service account has access to data directory
   icacls "C:\Program Files\PostgreSQL\17\data" /grant "NT AUTHORITY\NetworkService":F
   ```

2. **Check port conflicts**
   ```powershell
   # Check if port 5432 is in use
   netstat -ano | findstr :5432
   ```

3. **Manual service recovery**
   ```powershell
   # Stop any running processes
   taskkill /F /IM postgres.exe
   
   # Try starting manually
   & "C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe" start -D "C:\Program Files\PostgreSQL\17\data"
   ```

#### Problem: Service shows as "Stopped" but processes are running
**Solution:** This is a common Windows service issue. Force restart:
```powershell
# Stop the service
Stop-Service -Name postgresql-x64-17 -Force

# Wait a few seconds
Start-Sleep -Seconds 5

# Start the service
Start-Service -Name postgresql-x64-17
```

### 2. Connection Issues

#### Problem: Connection refused (10061)
**Solutions:**
1. **Verify PostgreSQL is running**
   ```powershell
   Get-Service -Name postgresql-x64-17
   ```

2. **Check firewall settings**
   ```powershell
   # Check Windows Firewall rules
   Get-NetFirewallRule -DisplayName "*PostgreSQL*" | Format-Table
   ```

3. **Test basic connectivity**
   ```powershell
   # Test with telnet
   telnet localhost 5432
   
   # Or with PowerShell
   Test-NetConnection -ComputerName localhost -Port 5432
   ```

#### Problem: Authentication failed (FATAL: password authentication failed)
**Solutions:**
1. **Verify password**
   ```powershell
   # Test connection with explicit password
   psql -h localhost -p 5432 -U postgres -d postgres -W
   ```

2. **Check pg_hba.conf**
   ```powershell
   # Verify authentication method
   Get-Content "C:\Program Files\PostgreSQL\17\data\pg_hba.conf"
   ```

3. **Reset password if needed**
   ```powershell
   # Reset postgres password
   & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -c "ALTER USER postgres PASSWORD 'new_password';"
   ```

### 3. pgvector Extension Issues

#### Problem: Vector extension not found
```sql
-- Check if extension exists
SELECT * FROM pg_extension WHERE extname = 'vector';
```

**Solutions:**
1. **Install pgvector extension**
   ```sql
   -- Connect to database and enable extension
   \c postgres
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **Verify installation files**
   ```powershell
   # Check if vector extension files exist
   Get-ChildItem "C:\Program Files\PostgreSQL\17\share\extension\" | Where-Object {$_.Name -like "vector*"}
   ```

3. **Rebuild if necessary**
   ```powershell
   # Rebuild pgvector (if installed from source)
   cd $env:TEMP\pgvector
   nmake /F Makefile.win clean
   nmake /F Makefile.win
   nmake /F Makefile.win install
   ```

#### Problem: Vector operations failing
**Solutions:**
1. **Check vector dimensions**
   ```sql
   -- Verify your vector column matches embedding model dimensions
   \d documents
   ```

2. **Test vector operations**
   ```sql
   -- Basic vector test
   SELECT '[1,2,3]'::vector <=> '[1,2,3]'::vector;
   ```

3. **Rebuild indexes**
   ```sql
   -- Rebuild vector index
   REINDEX INDEX idx_documents_embedding;
   ```

## Service Management

### Starting and Stopping Services

#### Graceful Shutdown
```powershell
# Stop PostgreSQL service gracefully
Stop-Service -Name postgresql-x64-17

# Or using pg_ctl
& "C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe" stop -D "C:\Program Files\PostgreSQL\17\data" -m fast
```

#### Emergency Stop
```powershell
# Force stop if graceful fails
Stop-Service -Name postgresql-x64-17 -Force

# Kill remaining processes
taskkill /F /IM postgres.exe /T
```

#### Starting Services
```powershell
# Start PostgreSQL service
Start-Service -Name postgresql-x64-17

# Verify it's running
Get-Service -Name postgresql-x64-17
```

### Service Configuration

#### Update Service Configuration
```powershell
# Open service properties
sc.exe config postgresql-x64-17 binPath= "\"C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe\" runservice -N \"postgresql-x64-17\" -D \"C:\Program Files\PostgreSQL\17\data\""
```

#### Check Service Dependencies
```powershell
# Check service dependencies
sc.exe queryex type= service state= all | findstr "postgresql"
```

## Connection Troubleshooting

### Connection Testing

#### Basic Connectivity Test
```powershell
# Test basic connectivity
Test-NetConnection -ComputerName localhost -Port 5432

# Test with PostgreSQL tools
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5432 -U postgres -d postgres -c "SELECT version();"
```

#### Advanced Connection Testing
```sql
-- Test database connectivity
SELECT 
  version(),
  current_timestamp,
  inet_server_addr() as server_ip,
  inet_server_port() as server_port;

-- Check active connections
SELECT 
  pid,
  usename,
  application_name,
  client_addr,
  state,
  query
FROM pg_stat_activity
WHERE state != 'idle';
```

### Connection Pooling Issues

#### Check Connection Limits
```sql
-- Check current connections
SELECT count(*) FROM pg_stat_activity;

-- Check max connections setting
SHOW max_connections;

-- Check connection usage
SELECT 
  count(*) as current_connections,
  setting as max_connections,
  round(count(*)::float / setting * 100, 2) as usage_percent
FROM pg_stat_activity, pg_settings 
WHERE pg_settings.name = 'max_connections';
```

#### Reset Connections
```sql
-- Ter problematic connections
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active' 
  AND query NOT LIKE '%pg_terminate_backend%'
  AND pid <> pg_backend_pid();
```

## Performance Optimization

### Query Performance

#### Identify Slow Queries
```sql
-- Enable query logging (requires restart)
ALTER SYSTEM SET log_min_duration_statement = '1000';
SELECT pg_reload_conf();

-- Check slow queries
SELECT 
  query,
  calls,
  total_time,
  mean_time,
  rows,
  100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

#### Index Optimization
```sql
-- Rebuild indexes
REINDEX DATABASE postgres;
REINDEX INDEX idx_documents_embedding;

-- Analyze tables for better query planning
ANALYZE documents;

-- Check index usage
SELECT 
  schemaname,
  relname,
  indexrelname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### Configuration Tuning

#### Memory Configuration
```sql
-- Check current memory settings
SHOW shared_buffers;
SHOW work_mem;
SHOW maintenance_work_mem;

-- Recommended settings for development
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
```

#### Checkpoint Tuning
```sql
-- Check checkpoint performance
SELECT 
  checkpoints_timed,
  checkpoints_req,
  checkpoint_write_time,
  checkpoint_sync_time,
  buffers_checkpoint
FROM pg_stat_bgwriter;

-- Adjust checkpoint settings if needed
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET max_wal_size = '1GB';
ALTER SYSTEM SET min_wal_size = '80MB';
SELECT pg_reload_conf();
```

## Backup and Recovery

### Backup Procedures

#### Full Database Backup
```powershell
# Create full backup
& "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" -U postgres -Fc -f "C:\backups\postgres_full_$(Get-Date -Format 'yyyyMMdd').dump" postgres

# Verify backup
& "C:\Program Files\PostgreSQL\17\bin\pg_restore.exe" -l "C:\backups\postgres_full_$(Get-Date -Format 'yyyyMMdd').dump"
```

#### Automated Backup Script
```powershell
# Create backup script (backup-postgres.ps1)
$backupPath = "C:\backups"
$backupFile = "postgres_full_$(Get-Date -Format 'yyyyMMdd').dump"
$pgDump = "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe"
$pgUser = "postgres"

# Create backup directory
if (-not (Test-Path $backupPath)) {
    New-Item -ItemType Directory -Path $backupPath | Out-Null
}

# Perform backup
& $pgDump -U $pgUser -Fc -f "$backupPath\$backupFile" postgres

# Keep only last 7 days of backups
Get-ChildItem $backupPath | Where-Object {$_.Name -like "postgres_full_*.dump"} | 
    Sort-Object LastWriteTime | Select-Object -First (@(Get-ChildItem $backupPath).Count - 7) | 
    Remove-Item -Force
```

### Recovery Procedures

#### Point-in-Time Recovery
```powershell
# Restore from backup
& "C:\Program Files\PostgreSQL\17\bin\pg_restore.exe" -d postgres "C:\backups\postgres_full_20250820.dump"

# If PITR needed, ensure wal archiving is enabled
# Check recovery.conf settings
```

#### Emergency Recovery
```powershell
# If database is corrupted, try recovery
& "C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe" recover -D "C:\Program Files\PostgreSQL\17\data"

# If that fails, restore from last known good backup
```

## Security Maintenance

### User and Role Management

#### Review User Privileges
```sql
-- Check all users and their roles
SELECT usename, usecreatedb, usesuper, usecatupd, valuntil 
FROM pg_user;

-- Check user privileges
SELECT 
  grantee,
  table_name,
  privilege_type
FROM information_schema.role_table_grants
WHERE grantee = 'postgres';
```

#### Create Application Users
```sql
-- Create dedicated user for applications
CREATE USER app_user WITH PASSWORD 'secure_password';

-- Grant necessary privileges
GRANT CONNECT ON DATABASE postgres TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE ON documents TO app_user;
```

### Security Auditing

#### Enable Logging
```sql
-- Enable connection logging
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
SELECT pg_reload_conf();

-- Check security events
SELECT 
  timestamp,
  user_name,
  database_name,
  application_name,
  action
FROM pg_stat_activity
WHERE state = 'active';
```

#### Monitor Failed Logins
```sql
-- Check authentication failures
SELECT 
  log_time,
  user_name,
  database_name,
  application_name,
  error_message
FROM pg_log
WHERE log_level = 'ERROR' 
  AND message LIKE '%authentication%';
```

## pgvector Extension Issues

### Extension Maintenance

#### Update Extension
```sql
-- Update vector extension if available
ALTER EXTENSION vector UPDATE;

-- Check extension version
SELECT extversion FROM pg_extension WHERE extname = 'vector';
```

#### Vector Index Maintenance
```sql
-- Rebuild vector indexes
REINDEX INDEX idx_documents_embedding;

-- Analyze vector tables
ANALYZE documents;

-- Check index statistics
SELECT 
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
WHERE indexname LIKE '%vector%';
```

### Vector Performance Issues

#### Optimize Vector Operations
```sql
-- Adjust index parameters if needed
DROP INDEX IF EXISTS idx_documents_embedding;
CREATE INDEX idx_documents_embedding ON documents 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 200);

-- Test different distance metrics
SELECT 
  embedding <=> '[0.1,0.2,0.3]'::vector as l2_distance,
  embedding <=> '[0.1,0.2,0.3]'::vector as cosine_distance
FROM documents
LIMIT 10;
```

## MCP Server Troubleshooting

### Connection Issues

#### Test MCP Server Connections
```powershell
# Test PostgreSQL MCP server
npx -y @modelcontextprotocol/server-postgres postgresql://postgres:2001@localhost:5432/postgres

# Test agent-memory server
cd mcp_servers/agent-memory
node index.js

# Test validation server
cd testing-validation-system
node src/mcp/test-mcp-server.js
```

#### Environment Variable Issues
```powershell
# Check environment variables
Get-ChildItem Env: | Where-Object {$_.Name -like "PG*"}
Get-ChildItem Env: | Where-Object {$_.Name -like "DATABASE*"}

# Set environment variables for testing
$env:DATABASE_URL = "postgresql://postgres:2001@localhost:5432/postgres"
$env:PGPASSWORD = "2001"
```

### Dependency Issues

#### Check Node.js Dependencies
```powershell
# Check MCP server dependencies
cd mcp_servers
npm list

# Reinstall dependencies if needed
npm install

# Check specific packages
npm list pg
npm list @xenova/transformers
```

## Monitoring and Health Checks

### Health Check Script
```powershell
# health-check.ps1
$healthStatus = @{
    Database = $false
    Service = $false
    Extension = $false
    Connections = $false
}

# Check PostgreSQL service
$service = Get-Service -Name postgresql-x64-17 -ErrorAction SilentlyContinue
if ($service -and $service.Status -eq 'Running') {
    $healthStatus.Service = $true
}

# Check database connectivity
try {
    & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5432 -U postgres -d postgres -c "SELECT 1;" -t | Out-Null
    $healthStatus.Database = $true
} catch {
    Write-Host "Database connection failed: $($_.Exception.Message)"
}

# Check pgvector extension
try {
    $vectorCheck = & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5432 -U postgres -d postgres -c "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector';" -t
    if ($vectorCheck -gt 0) {
        $healthStatus.Extension = $true
    }
} catch {
    Write-Host "Extension check failed: $($_.Exception.Message)"
}

# Check active connections
try {
    $connCount = & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5432 -U postgres -d postgres -c "SELECT COUNT(*) FROM pg_stat_activity;" -t
    if ($connCount -lt 50) { # Reasonable threshold
        $healthStatus.Connections = $true
    }
} catch {
    Write-Host "Connection check failed: $($_.Exception.Message)"
}

# Report health status
$overallHealth = $healthStatus.Values -contains $false
if ($overallHealth) {
    Write-Host "❌ Health Check Failed" -ForegroundColor Red
    $healthStatus | Format-Table
} else {
    Write-Host "✅ Health Check Passed" -ForegroundColor Green
}
```

### Performance Monitoring
```sql
-- Monitor database performance
SELECT 
  pg_stat_get_dbid() as dbid,
  pg_stat_get_dbname() as dbname,
  pg_stat_get_numbackends() as numbackends,
  pg_stat_get_xact_commit() as xact_commit,
  pg_stat_get_xact_rollback() as xact_rollback,
  pg_stat_get_blocks_fetched() as blocks_fetched,
  pg_stat_get_blocks_hit() as blocks_hit
FROM pg_stat_get_dbstat();

-- Monitor memory usage
SELECT 
  datname,
  pg_size_pretty(pg_database_size(datname)) as size,
  numbackends,
  xact_commit,
  xact_rollback
FROM pg_stat_database;
```

## Emergency Procedures

### Database Corruption Recovery

#### Emergency Recovery Steps
1. **Stop PostgreSQL service**
   ```powershell
   Stop-Service -Name postgresql-x64-17 -Force
   ```

2. **Check database files**
   ```powershell
   # Check data directory integrity
   chkdsk "C:\Program Files\PostgreSQL\17\data"
   ```

3. **Attempt recovery**
   ```powershell
   & "C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe" recover -D "C:\Program Files\PostgreSQL\17\data"
   ```

4. **If recovery fails, restore from backup**
   ```powershell
   & "C:\Program Files\PostgreSQL\17\bin\pg_restore.exe" -d postgres "C:\backups\postgres_full_20250820.dump"
   ```

### Service Failure Recovery

#### Emergency Service Restart
```powershell
# Emergency restart script
$service = "postgresql-x64-17"

# Stop service
Stop-Service -Name $service -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 5

# Kill remaining processes
Get-Process postgres -ErrorAction SilentlyContinue | Stop-Process -Force

# Start service
Start-Service -Name $service

# Verify status
Get-Service -Name $service
```

## Contact Information

- **Database Administrator**: [Contact Info]
- **System Administrator**: [Contact Info]
- **Support Team**: [Contact Info]

## Documentation Updates

This troubleshooting guide should be updated regularly as the system evolves. Please document any new issues and solutions discovered during maintenance operations.

**Last Updated**: 2025-08-20  
**Next Review**: [Date]