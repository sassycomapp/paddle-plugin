# Troubleshooting Guide

## Overview

This guide provides comprehensive troubleshooting instructions for MCP (Model Context Protocol) servers within the KiloCode ecosystem. The troubleshooting process follows the **Simple, Robust, Secure** approach and helps resolve common issues efficiently.

## Troubleshooting Philosophy

### Key Principles
1. **Systematic Approach**: Follow a structured troubleshooting methodology
2. **Root Cause Analysis**: Identify and address the root cause of issues
3. **Preventive Measures**: Implement preventive measures to avoid recurrence
4. **Documentation**: Document troubleshooting steps and solutions
5. **Continuous Improvement**: Learn from troubleshooting experiences

### Troubleshooting Methodology
1. **Identify the Problem**: Clearly define the issue
2. **Gather Information**: Collect relevant data and logs
3. **Analyze the Cause**: Determine the root cause
4. **Implement Solution**: Apply appropriate fix
5. **Verify Resolution**: Confirm the issue is resolved
6. **Document Solution**: Record the troubleshooting process

## Common Issues and Solutions

### 1. MCP Server Startup Issues

#### Issue 1.1: Server Fails to Start
**Symptom**: MCP server fails to start with error messages
**Solution**: Check configuration, dependencies, and logs

```bash
# Check server logs
tail -f /var/log/kilocode/mcp/server.log

# Check configuration files
cat /etc/kilocode/mcp/server.json

# Check dependencies
npm list --depth=0
pip list

# Check system resources
free -h
df -h
```

**Resolution Steps**:
1. Verify configuration file syntax
2. Check required dependencies are installed
3. Ensure sufficient system resources
4. Check port availability
5. Review error logs for specific issues

#### Issue 1.2: Port Already in Use
**Symptom**: Server fails to start due to port conflict
**Solution**: Identify and resolve port conflicts

```bash
# Check port usage
netstat -tulpn | grep :3000

# Find process using port
lsof -i :3000

# Kill conflicting process
sudo kill -9 <PID>

# Or change port in configuration
sed -i 's/"port": 3000/"port": 3001/' /etc/kilocode/mcp/server.json
```

**Resolution Steps**:
1. Identify process using the port
2. Terminate the conflicting process or change the port
3. Restart the server
4. Verify server starts successfully

### 2. Configuration Issues

#### Issue 2.1: Configuration Validation Errors
**Symptom**: Configuration validation fails with error messages
**Solution**: Validate and fix configuration issues

```bash
# Run configuration validation
sudo /opt/kilocode/mcp-servers/scripts/validate-config.sh

# Check configuration syntax
cat /etc/kilocode/mcp/server.json | jq .

# Validate environment variables
env | grep KILOCODE

# Check file permissions
ls -la /etc/kilocode/mcp/
```

**Resolution Steps**:
1. Run configuration validation script
2. Fix syntax errors in configuration files
3. Ensure required environment variables are set
4. Verify file permissions are correct
5. Test configuration changes

#### Issue 2.2: Environment Variable Issues
**Symptom**: Services fail due to missing or incorrect environment variables
**Solution**: Check and fix environment variable configuration

```bash
# Check environment file
cat /etc/kilocode/mcp/.env

# Test environment variable access
echo $KILOCODE_ENV
echo $KILOCODE_PROJECT_PATH

# Validate environment variables in services
systemctl show mcp-filesystem --property=Environment
```

**Resolution Steps**:
1. Check environment file syntax and content
2. Verify all required variables are set
3. Test variable access in services
4. Update environment files as needed
5. Restart services after changes

### 3. Database Issues

#### Issue 3.1: Database Connection Failed
**Symptom**: Services cannot connect to database
**Solution**: Check database configuration and connectivity

```bash
# Check database service status
sudo systemctl status postgresql

# Test database connection
psql -U mcp_user -d mcp_db -c "SELECT 1;"

# Check database logs
tail -f /var/log/postgresql/postgresql-14-main.log

# Check connection parameters
cat /etc/kilocode/mcp/database.json
```

**Resolution Steps**:
1. Verify database service is running
2. Check database connection parameters
3. Test database connectivity manually
4. Check database logs for errors
5. Verify user permissions and database existence

#### Issue 3.2: Database Performance Issues
**Symptom**: Database queries are slow or timeout
**Solution**: Optimize database performance

```bash
# Check database performance
psql -U mcp_user -d mcp_db -c "SELECT * FROM pg_stat_activity;"

# Check slow queries
psql -U mcp_user -d mcp_db -c "SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Check table sizes
psql -U mcp_user -d mcp_db -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size FROM pg_tables WHERE schemaname = 'public';"

# Optimize database
psql -U mcp_user -d mcp_db -c "VACUUM ANALYZE;"
```

**Resolution Steps**:
1. Identify slow queries
2. Optimize query performance
3. Index frequently queried tables
4. Run database maintenance tasks
5. Monitor performance after changes

### 4. Memory Service Issues

#### Issue 4.1: Memory Service Not Responding
**Symptom**: Memory service is not responding to requests
**Solution**: Check service status and logs

```bash
# Check service status
sudo systemctl status mcp-memory

# Check service logs
tail -f /var/log/kilocode/mcp/memory.log

# Test service connectivity
curl -s http://localhost:3002/get_stats

# Check memory usage
free -h
```

**Resolution Steps**:
1. Verify service is running
2. Check service logs for errors
3. Test service connectivity
4. Check system memory usage
5. Restart service if necessary

#### Issue 4.2: Memory Service Performance Issues
**Symptom**: Memory service is slow or unresponsive
**Solution**: Optimize memory service performance

```bash
# Check memory service stats
curl -s http://localhost:3002/get_stats

# Check memory database size
du -sh /opt/kilocode/mcp-servers/memory_db/

# Check memory service logs
tail -f /var/log/kilocode/mcp/memory.log

# Optimize memory service
curl -s http://localhost:3002/consolidate
```

**Resolution Steps**:
1. Check memory service statistics
2. Analyze memory database size
3. Review service logs for performance issues
4. Run memory consolidation
5. Monitor performance after optimization

### 5. Compliance Server Issues

#### Issue 5.1: Compliance Checks Failing
**Symptom**: Compliance checks are failing or producing errors
**Solution**: Check compliance configuration and logs

```bash
# Check compliance server status
sudo systemctl status mcp-compliance

# Check compliance logs
tail -f /var/log/kilocode/mcp/compliance.log

# Run compliance check manually
sudo /opt/kilocode/mcp-servers/scripts/compliance-check.sh

# Check configuration
cat /etc/kilocode/mcp/compliance.json
```

**Resolution Steps**:
1. Verify compliance server is running
2. Check compliance logs for errors
3. Run compliance checks manually
4. Verify configuration files
5. Check rule definitions and targets

#### Issue 5.2: Compliance Reports Not Generated
**Symptom**: Compliance reports are not being generated
**Solution**: Check report generation process

```bash
# Check report directory
ls -la /opt/kilocode/mcp-servers/reports/

# Check report generation logs
tail -f /var/log/kilocode/mcp/report-generation.log

# Test report generation manually
sudo /opt/kilocode/mcp-servers/scripts/generate-report.sh

# Check report permissions
ls -la /opt/kilocode/mcp-servers/reports/
```

**Resolution Steps**:
1. Check report directory existence and permissions
2. Review report generation logs
3. Test report generation manually
4. Check report templates and configuration
5. Verify output directory permissions

### 6. Network Issues

#### Issue 6.1: Network Connectivity Problems
**Symptom**: Services cannot communicate over the network
**Solution**: Check network configuration and connectivity

```bash
# Check network connectivity
ping localhost
ping 192.168.1.100

# Check port availability
netstat -tulpn | grep :3000

# Check firewall status
sudo ufw status

# Check network interfaces
ip addr show
```

**Resolution Steps**:
1. Test basic network connectivity
2. Check port availability and usage
3. Verify firewall configuration
4. Check network interface status
5. Test service communication

#### Issue 6.2: SSL/TLS Certificate Issues
**Symptom**: SSL/TLS connections are failing
**Solution**: Check certificate configuration and validity

```bash
# Check certificate validity
openssl x509 -in /etc/ssl/kilocode/mcp.crt -text -noout

# Check certificate expiration
openssl x509 -in /etc/ssl/kilocode/mcp.crt -noout -dates

# Test SSL connection
openssl s_client -connect localhost:3000

# Check certificate configuration
cat /etc/kilocode/mcp/ssl.json
```

**Resolution Steps**:
1. Verify certificate validity and expiration
2. Check certificate configuration
3. Test SSL connection
4. Renew or regenerate certificates if needed
5. Update certificate references in configuration

### 7. Performance Issues

#### Issue 7.1: High CPU Usage
**Symptom**: System CPU usage is consistently high
**Solution**: Identify and address CPU-intensive processes

```bash
# Check CPU usage
top -b -n 1 | head -20

# Check process CPU usage
ps aux --sort=-%cpu | head -10

# Check system load
uptime

# Monitor CPU over time
mpstat 1 5
```

**Resolution Steps**:
1. Identify CPU-intensive processes
2. Check system load averages
3. Monitor CPU usage over time
4. Optimize or restart high-CPU processes
5. Consider scaling resources if needed

#### Issue 7.2: High Memory Usage
**Symptom**: System memory usage is consistently high
**Solution**: Identify and address memory-intensive processes

```bash
# Check memory usage
free -h

# Check process memory usage
ps aux --sort=-%mem | head -10

# Check memory allocation
cat /proc/meminfo

# Monitor memory over time
vmstat 1 5
```

**Resolution Steps**:
1. Identify memory-intensive processes
2. Check system memory allocation
3. Monitor memory usage over time
4. Restart or optimize high-memory processes
5. Consider increasing memory if needed

### 8. Security Issues

#### Issue 8.1: Authentication Failures
**Symptom**: Users cannot authenticate to the system
**Solution**: Check authentication configuration and logs

```bash
# Check authentication logs
tail -f /var/log/auth.log

# Check user accounts
getent passwd | grep mcp

# Check SSH configuration
cat /etc/ssh/sshd_config

# Test authentication
sudo -u mcp-service whoami
```

**Resolution Steps**:
1. Review authentication logs for errors
2. Check user account configuration
3. Verify authentication service settings
4. Test authentication manually
5. Reset passwords if necessary

#### Issue 8.2: Security Alert Notifications
**Symptom**: Receiving security alert notifications
**Solution**: Investigate and address security concerns

```bash
# Check security logs
tail -f /var/log/kilocode/mcp/security.log

# Check system security
sudo auditctl -l

# Check for unauthorized access
last | grep "$(date '+%b %d')"

# Run security scan
sudo /opt/kilocode/mcp-servers/security/audit.sh
```

**Resolution Steps**:
1. Review security logs for suspicious activity
2. Check system security settings
3. Look for unauthorized access attempts
4. Run security scans to identify issues
5. Implement security fixes as needed

## Advanced Troubleshooting

### 9. Debug Mode Configuration

#### Enable Debug Logging
```bash
# Enable debug logging for all services
sudo sed -i 's/LOG_LEVEL=INFO/LOG_LEVEL=DEBUG/' /etc/kilocode/mcp/.env

# Restart services
sudo systemctl restart mcp-filesystem mcp-postgres mcp-memory mcp-compliance

# Check debug logs
tail -f /var/log/kilocode/mcp/*.log
```

#### Debug Mode for Specific Services
```bash
# Enable debug for specific service
sudo systemctl set-property mcp-filesystem Environment="LOG_LEVEL=DEBUG"

# Restart service
sudo systemctl restart mcp-filesystem

# Monitor debug output
journalctl -u mcp-filesystem -f
```

### 10. Performance Analysis

#### System Performance Analysis
```bash
# Install performance analysis tools
sudo apt install -y sysstat iotop htop

# Monitor system performance
iostat -x 1 5
vmstat 1 5
mpstat 1 5

# Monitor disk I/O
iotop -o -b -n 5

# Monitor network I/O
nethogs
```

#### Application Performance Analysis
```bash
# Monitor application performance
sudo /opt/kilocode/mcp-servers/scripts/performance-monitor.sh

# Generate performance report
sudo /opt/kilocode/mcp-servers/scripts/generate-performance-report.sh

# Analyze performance data
cat /opt/kilocode/mcp-servers/reports/performance-report-$(date +%Y%m%d).txt
```

### 11. Database Troubleshooting

#### Database Connection Issues
```bash
# Check database connectivity
psql -U mcp_user -d mcp_db -c "SELECT version();"

# Check database connections
psql -U mcp_user -d mcp_db -c "SELECT count(*) FROM pg_stat_activity;"

# Check database locks
psql -U mcp_user -d mcp_db -c "SELECT * FROM pg_locks;"

# Check database performance
psql -U mcp_user -d mcp_db -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

#### Database Recovery
```bash
# Create database backup
pg_dump -U mcp_user -d mcp_db > /tmp/database_backup.sql

# Restore database
psql -U mcp_user -d mcp_db < /tmp/database_backup.sql

# Check database integrity
psql -U mcp_user -d mcp_db -c "VACUUM FULL;"
```

## Troubleshooting Tools

### 12. System Monitoring Tools

#### System Monitoring
```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Monitor system resources
htop
iotop
nethogs

# Monitor network connections
netstat -tulpn
ss -tulpn

# Monitor processes
ps aux --forest
```

#### Log Analysis
```bash
# Install log analysis tools
sudo apt install -y multitail

# Monitor multiple logs
multitail /var/log/kilocode/mcp/*.log

# Search logs
grep -i "error" /var/log/kilocode/mcp/*.log
grep -i "warning" /var/log/kilocode/mcp/*.log

# Log rotation
logrotate -f /etc/logrotate.d/kilocode-mcp
```

### 13. Network Troubleshooting Tools

#### Network Diagnostics
```bash
# Test network connectivity
ping localhost
ping 8.8.8.8
traceroute 8.8.8.8

# Check network interfaces
ip addr show
ifconfig

# Check routing table
ip route show
netstat -rn

# Check DNS resolution
nslookup localhost
dig google.com
```

#### Port Analysis
```bash
# Check port usage
netstat -tulpn
ss -tulpn

# Check specific port
lsof -i :3000
nc -zv localhost 3000

# Port scanning
nmap -sT -p 1-1000 localhost
```

## Preventive Maintenance

### 14. Regular Maintenance Tasks

#### Daily Maintenance
```bash
# Create daily maintenance script
cat << 'EOF' | sudo tee /opt/kilocode/mcp-servers/maintenance/daily.sh
#!/bin/bash

# Daily maintenance script
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] Starting daily maintenance..."

# Check service status
services=("mcp-filesystem" "mcp-postgres" "mcp-memory" "mcp-compliance")
for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        echo "[$DATE] OK: $service is running"
    else
        echo "[$DATE] WARNING: $service is not starting"
        systemctl start $service
    fi
done

# Check disk space
DISK_USAGE=$(df /opt/kilocode/mcp-servers | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "[$DATE] WARNING: Disk usage at ${DISK_USAGE}%"
    # Clean up old logs
    find /var/log/kilocode/mcp -name "*.log" -mtime +7 -delete
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ $MEMORY_USAGE -gt 85 ]; then
    echo "[$DATE] WARNING: Memory usage at ${MEMORY_USAGE}%"
fi

# Rotate logs
logrotate -f /etc/logrotate.d/kilocode-mcp

echo "[$DATE] Daily maintenance completed"
EOF

# Make script executable
sudo chmod +x /opt/kilocode/mcp-servers/maintenance/daily.sh

# Set up cron job
echo "0 2 * * * /opt/kilocode/mcp-servers/maintenance/daily.sh" | sudo crontab -
```

#### Weekly Maintenance
```bash
# Create weekly maintenance script
cat << 'EOF' | sudo tee /opt/kilocode/mcp-servers/maintenance/weekly.sh
#!/bin/bash

# Weekly maintenance script
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] Starting weekly maintenance..."

# Update system packages
sudo apt update
sudo apt upgrade -y

# Check service logs for errors
services=("mcp-filesystem" "mcp-postgres" "mcp-memory" "mcp-compliance")
for service in "${services[@]}"; do
    LOG_ERRORS=$(journalctl -u $service --since "1 week ago" | grep -i "error\|failed" | wc -l)
    if [ $LOG_ERRORS -gt 0 ]; then
        echo "[$DATE] WARNING: Found $LOG_ERRORS errors in $service logs"
    fi
done

# Check database performance
if systemctl is-active --quiet mcp-postgres; then
    SLOW_QUERIES=$(psql -U mcp_user -d mcp_db -c "SELECT COUNT(*) FROM pg_stat_statements WHERE total_time > 1000;" -t -A)
    echo "[$DATE] INFO: Found $SLOW_QUERIES slow queries"
fi

# Clean up temporary files
find /tmp -name "mcp_*" -mtime +1 -delete

# Verify backups
BACKUP_DIR="/opt/kilocode/mcp-servers/backups"
if [ -d "$BACKUP_DIR" ]; then
    for backup_file in $BACKUP_DIR/*.tar.gz; do
        if [ -f "$backup_file" ]; then
            if tar -tzf "$backup_file" >/dev/null 2>&1; then
                echo "[$DATE] OK: Backup $backup_file is valid"
            else
                echo "[$DATE] ERROR: Backup $backup_file is corrupted"
            fi
        fi
    done
fi

echo "[$DATE] Weekly maintenance completed"
EOF

# Make script executable
sudo chmod +x /opt/kilocode/mcp-servers/maintenance/weekly.sh

# Set up cron job
echo "0 3 * * 0 /opt/kilocode/mcp-servers/maintenance/weekly.sh" | sudo crontab -
```

### 15. Backup and Recovery

#### Automated Backup
```bash
# Create automated backup script
cat << 'EOF' | sudo tee /opt/kilocode/mcp-servers/backup/backup.sh
#!/bin/bash

# Automated backup script
BACKUP_DIR="/opt/kilocode/mcp-servers/backups"
DATE=$(date '+%Y%m%d_%H%M%S')
BACKUP_FILE="mcp_backup_$DATE.tar.gz"

echo "Starting automated backup..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Stop services for consistent backup
systemctl stop mcp-filesystem mcp-postgres mcp-memory mcp-compliance

# Create backup
tar -czf $BACKUP_DIR/$BACKUP_FILE \
    -C /etc/kilocode \
    mcp \
    -C /opt/kilocode/mcp-servers \
    kilocode-mcp-installer \
    mcp-memory-service \
    memory_db \
    memory_backups \
    reports

# Start services
systemctl start mcp-filesystem mcp-postgres mcp-memory mcp-compliance

# Verify backup
if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    echo "Backup created successfully: $BACKUP_DIR/$BACKUP_FILE"
    if tar -tzf $BACKUP_DIR/$BACKUP_FILE >/dev/null 2>&1; then
        echo "Backup integrity verified"
    else
        echo "ERROR: Backup integrity check failed"
    fi
else
    echo "ERROR: Failed to create backup"
    exit 1
fi

# Clean up old backups
find $BACKUP_DIR -name "mcp_backup_*.tar.gz" -mtime +30 -delete

echo "Automated backup completed"
EOF

# Make backup script executable
sudo chmod +x /opt/kilocode/mcp-servers/backup/backup.sh

# Set up cron job
echo "0 2 * * * /opt/kilocode/mcp-servers/backup/backup.sh" | sudo crontab -
```

## Emergency Procedures

### 16. Emergency Shutdown

#### Graceful Shutdown
```bash
# Create emergency shutdown script
cat << 'EOF' | sudo tee /opt/kilocode/mcp-servers/emergency/shutdown.sh
#!/bin/bash

# Emergency shutdown script
echo "Starting emergency shutdown..."

# Stop all services
systemctl stop mcp-filesystem mcp-postgres mcp-memory mcp-compliance

# Create emergency backup
BACKUP_DIR="/opt/kilocode/mcp-servers/backups/emergency"
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/emergency_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    -C /etc/kilocode \
    mcp \
    -C /opt/kilocode/mcp-servers \
    kilocode-mcp-installer \
    mcp-memory-service

# Log shutdown
echo "Emergency shutdown completed at $(date)" >> /var/log/kilocode/mcp/emergency.log

echo "Emergency shutdown completed"
EOF

# Make emergency script executable
sudo chmod +x /opt/kilocode/mcp-servers/emergency/shutdown.sh
```

#### Emergency Restart
```bash
# Create emergency restart script
cat << 'EOF' | sudo tee /opt/kilocode/mcp-servers/emergency/restart.sh
#!/bin/bash

# Emergency restart script
echo "Starting emergency restart..."

# Stop all services
systemctl stop mcp-filesystem mcp-postgres mcp-memory mcp-compliance

# Wait for services to stop
sleep 5

# Start all services
systemctl start mcp-filesystem mcp-postgres mcp-memory mcp-compliance

# Check service status
services=("mcp-filesystem" "mcp-postgres" "mcp-memory" "mcp-compliance")
for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        echo "OK: $service is running"
    else
        echo "ERROR: $service failed to start"
    fi
done

echo "Emergency restart completed"
EOF

# Make emergency restart script executable
sudo chmod +x /opt/kilocode/mcp-servers/emergency/restart.sh
```

## Support and Contact Information

### Technical Support
- **Email**: support@kilocode.com
- **Phone**: +1 (555) 123-4567
- **Hours**: 24/7 for emergency support

### Documentation
- **Main Documentation**: [KiloCode Documentation](https://docs.kilocode.com/mcp)
- **GitHub Issues**: [KiloCode GitHub](https://github.com/kilocode/kilocode/issues)
- **Community Forum**: [KiloCode Community](https://community.kilocode.com)

### Emergency Contacts
- **System Administrator**: admin@kilocode.com
- **Security Officer**: security@kilocode.com
- **Compliance Officer**: compliance@kilocode.com

---

*This troubleshooting guide is part of the KiloCode MCP Setup and Configuration Architecture Plan and should be reviewed and updated regularly to reflect changes in troubleshooting procedures and best practices.*