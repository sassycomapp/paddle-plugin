# Installation Guide for System Administrators

## Overview

This guide provides comprehensive installation instructions for System Administrators deploying MCP (Model Context Protocol) servers within the KiloCode ecosystem. The installation process follows the **Simple, Robust, Secure** approach and ensures proper integration with existing infrastructure.

## Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows
- **Node.js**: 18.x LTS (minimum), 20.x LTS (recommended)
- **Python**: 3.8+ (minimum), 3.11+ (recommended)
- **npm**: 8.x+ (minimum), 9.x+ (recommended)
- **PostgreSQL**: 12+ (if using PostgreSQL-based servers)
- **Memory**: Minimum 4GB RAM, 8GB recommended
- **Storage**: Minimum 10GB free disk space

### Network Requirements
- **Internet Connection**: Required for package installation
- **Port Access**: Various ports depending on MCP servers (typically 3000-9000)
- **Firewall**: Allow outbound connections to package repositories
- **DNS**: Access to package registries (npm, PyPI)

### Security Requirements
- **User Account**: Dedicated service account with minimal privileges
- **Directory Permissions**: Appropriate read/write permissions for installation directories
- **Environment Variables**: Secure storage for sensitive configuration
- **SSL/TLS**: HTTPS for external connections

## Installation Process

### Step 1: Environment Preparation

#### 1.1 Create Service Account
```bash
# Create dedicated service account
sudo useradd -m -s /bin/bash mcp-service
sudo passwd mcp-service

# Add to necessary groups
sudo usermod -aG mcp-service mcp-service
```

#### 1.2 Prepare Installation Directory
```bash
# Create installation directory
sudo mkdir -p /opt/kilocode/mcp-servers
sudo chown mcp-service:mcp-service /opt/kilocode/mcp-servers

# Set appropriate permissions
sudo chmod 750 /opt/kilocode/mcp-servers
```

#### 1.3 Install System Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm postgresql

# CentOS/RHEL
sudo yum install -y python3 python3-pip nodejs npm postgresql-server

# macOS (using Homebrew)
brew install nodejs python postgresql

# Windows (using Chocolatey)
choco install nodejs python postgresql
```

### Step 2: Install Node.js MCP Servers

#### 2.1 Install KiloCode MCP Server Installer
```bash
# Navigate to installation directory
cd /opt/kilocode/mcp-servers

# Clone the repository
sudo -u mcp-service git clone https://github.com/kilocode/kilocode-mcp-installer.git

# Install dependencies
cd kilocode-mcp-installer
sudo -u mcp-service npm install
sudo -u mcp-service npm run build
```

#### 2.2 Install Core MCP Servers
```bash
# Install Filesystem Server
sudo -u mcp-service node dist/index.js install filesystem

# Install PostgreSQL Server
sudo -u mcp-service node dist/index.js install postgres

# Install Compliance Server
sudo -u mcp-service node dist/index.js install compliance

# Install Integration Coordinator
sudo -u mcp-service node dist/index.js install integration-coordinator
```

#### 2.3 Verify Node.js Server Installation
```bash
# Test filesystem server
sudo -u mcp-service npx -y @modelcontextprotocol/server-filesystem .

# Test postgres server
sudo -u mcp-service npx -y @modelcontextprotocol/server-postgres

# Test compliance server
cd mcp-compliance-server
sudo -u mcp-service node test-server.js
```

### Step 3: Install Python MCP Servers

#### 3.1 Install Python Environment
```bash
# Create Python virtual environment
sudo -u mcp-service python3 -m venv /opt/kilocode/mcp-servers/venv

# Activate virtual environment
sudo -u mcp-service source /opt/kilocode/mcp-servers/venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

#### 3.2 Install Memory Service
```bash
# Clone memory service repository
sudo -u mcp-service git clone https://github.com/doobidoo/mcp-memory-service.git

# Navigate to memory service
cd mcp-memory-service

# Run hardware-aware installation
python install.py

# Test installation
python memory_wrapper.py
```

#### 3.3 Install Additional Python Servers
```bash
# Install EasyOCR MCP server
sudo -u mcp-service git clone https://github.com/kilocode/easyocr-mcp.git
cd easyocr-mcp
sudo -u mcp-service pip install -r requirements.txt

# Install Everything Search MCP server
sudo -u mcp-service git clone https://github.com/kilocode/everything-search-mcp.git
cd everything-search-mcp
sudo -u mcp-service pip install -r requirements.txt
```

### Step 4: Configure MCP Servers

#### 4.1 Create Base Configuration
```bash
# Create configuration directory
sudo mkdir -p /etc/kilocode/mcp
sudo chown mcp-service:mcp-service /etc/kilocode/mcp

# Create base configuration file
cat << 'EOF' | sudo tee /etc/kilocode/mcp/mcp.json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", ".", "/tmp"],
      "env": {
        "NODE_ENV": "production",
        "KILOCODE_ENV": "production"
      },
      "description": "Filesystem access for project files"
    },
    "postgres": {
      "command": "node",
      "args": ["/opt/kilocode/mcp-servers/kilocode-mcp-installer/dist/index.js", "postgres"],
      "env": {
        "DATABASE_URL": "postgresql://mcp_user:mcp_password@localhost:5432/mcp_db",
        "NODE_ENV": "production",
        "KILOCODE_ENV": "production"
      },
      "description": "PostgreSQL database connection"
    },
    "memory": {
      "command": "python",
      "args": ["/opt/kilocode/mcp-servers/mcp-memory-service/memory_wrapper.py"],
      "env": {
        "MCP_MEMORY_VECTOR_DB_PATH": "/opt/kilocode/mcp-servers/memory_db",
        "MCP_MEMORY_BACKUPS_PATH": "/opt/kilocode/mcp-servers/memory_backups",
        "MCP_MEMORY_LOG_LEVEL": "INFO"
      },
      "alwaysAllow": [
        "store_memory",
        "retrieve_memory",
        "recall_memory",
        "search_by_tag",
        "delete_memory",
        "get_stats"
      ],
      "description": "Persistent semantic memory service"
    }
  }
}
EOF
```

#### 4.2 Create Environment Configuration
```bash
# Create environment file
cat << 'EOF' | sudo tee /etc/kilocode/mcp/.env
# KiloCode Environment Configuration
KILOCODE_ENV=production
KILOCODE_PROJECT_PATH=/opt/kilocode/mcp-servers
KILOCODE_PROJECT_NAME=KiloCode MCP Servers

# Database Configuration
DATABASE_URL=postgresql://mcp_user:mcp_password@localhost:5432/mcp_db
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=mcp_db
DATABASE_USER=mcp_user
DATABASE_PASSWORD=mcp_password

# Memory Service Configuration
MCP_MEMORY_VECTOR_DB_PATH=/opt/kilocode/mcp-servers/memory_db
MCP_MEMORY_BACKUPS_PATH=/opt/kilocode/mcp-servers/memory_backups
MCP_MEMORY_MAX_SIZE=1000000
MCP_MEMORY_CLEANUP_INTERVAL=3600
MCP_MEMORY_LOG_LEVEL=INFO

# Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=/var/log/kilocode/mcp
EOF
```

#### 4.3 Set Up Directory Structure
```bash
# Create necessary directories
sudo mkdir -p /var/log/kilocode/mcp
sudo mkdir -p /opt/kilocode/mcp-servers/memory_db
sudo mkdir -p /opt/kilocode/mcp-servers/memory_backups
sudo mkdir -p /opt/kilocode/mcp-servers/reports

# Set permissions
sudo chown -R mcp-service:mcp-service /var/log/kilocode/mcp
sudo chown -R mcp-service:mcp-service /opt/kilocode/mcp-servers/memory_db
sudo chown -R mcp-service:mcp-service /opt/kilocode/mcp-servers/memory_backups
sudo chown -R mcp-service:mcp-service /opt/kilocode/mcp-servers/reports

# Set appropriate permissions
sudo chmod 750 /var/log/kilocode/mcp
sudo chmod 750 /opt/kilocode/mcp-servers/memory_db
sudo chmod 750 /opt/kilocode/mcp-servers/memory_backups
sudo chmod 755 /opt/kilocode/mcp-servers/reports
```

### Step 5: Set Up System Services

#### 5.1 Create Systemd Services
```bash
# Create filesystem service
cat << 'EOF' | sudo tee /etc/systemd/system/mcp-filesystem.service
[Unit]
Description=MCP Filesystem Server
After=network.target

[Service]
Type=simple
User=mcp-service
WorkingDirectory=/opt/kilocode/mcp-servers
ExecStart=/usr/bin/npx -y @modelcontextprotocol/server-filesystem . /tmp
Restart=always
RestartSec=10
Environment=NODE_ENV=production
Environment=KILOCODE_ENV=production
Environment=KILOCODE_PROJECT_PATH=/opt/kilocode/mcp-servers

[Install]
WantedBy=multi-user.target
EOF

# Create postgres service
cat << 'EOF' | sudo tee /etc/systemd/system/mcp-postgres.service
[Unit]
Description=MCP PostgreSQL Server
After=network.target postgresql.service

[Service]
Type=simple
User=mcp-service
WorkingDirectory=/opt/kilocode/mcp-servers
ExecStart=/usr/bin/node /opt/kilocode/mcp-servers/kilocode-mcp-installer/dist/index.js postgres
Restart=always
RestartSec=10
Environment=NODE_ENV=production
Environment=KILOCODE_ENV=production
Environment=DATABASE_URL=postgresql://mcp_user:mcp_password@localhost:5432/mcp_db

[Install]
WantedBy=multi-user.target
EOF

# Create memory service
cat << 'EOF' | sudo tee /etc/systemd/system/mcp-memory.service
[Unit]
Description=MCP Memory Service
After=network.target

[Service]
Type=simple
User=mcp-service
WorkingDirectory=/opt/kilocode/mcp-servers/mcp-memory-service
ExecStart=/opt/kilocode/mcp-servers/venv/bin/python memory_wrapper.py
Restart=always
RestartSec=10
Environment=MCP_MEMORY_VECTOR_DB_PATH=/opt/kilocode/mcp-servers/memory_db
Environment=MCP_MEMORY_BACKUPS_PATH=/opt/kilocode/mcp-servers/memory_backups
Environment=MCP_MEMORY_LOG_LEVEL=INFO

[Install]
WantedBy=multi-user.target
EOF
```

#### 5.2 Enable and Start Services
```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable mcp-filesystem
sudo systemctl enable mcp-postgres
sudo systemctl enable mcp-memory

# Start services
sudo systemctl start mcp-filesystem
sudo systemctl start mcp-postgres
sudo systemctl start mcp-memory

# Check service status
sudo systemctl status mcp-filesystem
sudo systemctl status mcp-postgres
sudo systemctl status mcp-memory
```

### Step 6: Configure Monitoring and Logging

#### 6.1 Set Up Log Rotation
```bash
# Create log rotation configuration
cat << 'EOF' | sudo tee /etc/logrotate.d/kilocode-mcp
/var/log/kilocode/mcp/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 mcp-service mcp-service
    postrotate
        systemctl reload mcp-filesystem mcp-postgres mcp-memory
    endscript
}
EOF
```

#### 6.2 Configure Monitoring
```bash
# Create monitoring script
cat << 'EOF' | sudo tee /opt/kilocode/mcp-servers/monitoring/health-check.sh
#!/bin/bash

# Health check script for MCP servers
HEALTH_LOG="/var/log/kilocode/mcp/health-check.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Check filesystem server
if systemctl is-active --quiet mcp-filesystem; then
    echo "[$DATE] Filesystem server: OK" >> $HEALTH_LOG
else
    echo "[$DATE] Filesystem server: FAILED" >> $HEALTH_LOG
    systemctl restart mcp-filesystem
fi

# Check postgres server
if systemctl is-active --quiet mcp-postgres; then
    echo "[$DATE] PostgreSQL server: OK" >> $HEALTH_LOG
else
    echo "[$DATE] PostgreSQL server: FAILED" >> $HEALTH_LOG
    systemctl restart mcp-postgres
fi

# Check memory service
if systemctl is-active --quiet mcp-memory; then
    echo "[$DATE] Memory service: OK" >> $HEALTH_LOG
else
    echo "[$DATE] Memory service: FAILED" >> $HEALTH_LOG
    systemctl restart mcp-memory
fi

# Check disk space
DISK_USAGE=$(df /opt/kilocode/mcp-servers | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "[$DATE] WARNING: Disk usage at ${DISK_USAGE}%" >> $HEALTH_LOG
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ $MEMORY_USAGE -gt 80 ]; then
    echo "[$DATE] WARNING: Memory usage at ${MEMORY_USAGE}%" >> $HEALTH_LOG
fi
EOF

# Make health check script executable
sudo chmod +x /opt/kilocode/mcp-servers/monitoring/health-check.sh

# Set up cron job for health checks
echo "*/5 * * * * /opt/kilocode/mcp-servers/monitoring/health-check.sh" | sudo crontab -
```

### Step 7: Configure Backup and Recovery

#### 7.1 Create Backup Script
```bash
# Create backup script
cat << 'EOF' | sudo tee /opt/kilocode/mcp-servers/backup/backup-mcp.sh
#!/bin/bash

# Backup script for MCP servers
BACKUP_DIR="/opt/kilocode/mcp-servers/backups"
DATE=$(date '+%Y%m%d_%H%M%S')
BACKUP_FILE="mcp_backup_$DATE.tar.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup configuration files
tar -czf $BACKUP_DIR/$BACKUP_FILE \
    /etc/kilocode/mcp \
    /opt/kilocode/mcp-servers/kilocode-mcp-installer \
    /opt/kilocode/mcp-servers/mcp-memory-service \
    /opt/kilocode/mcp-servers/memory_db \
    /var/log/kilocode/mcp

# Keep only last 7 days of backups
find $BACKUP_DIR -name "mcp_backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/$BACKUP_FILE"
EOF

# Make backup script executable
sudo chmod +x /opt/kilocode/mcp-servers/backup/backup-mcp.sh

# Set up daily backup
echo "0 2 * * * /opt/kilocode/mcp-servers/backup/backup-mcp.sh" | sudo crontab -
```

#### 7.2 Create Recovery Script
```bash
# Create recovery script
cat << 'EOF' | sudo tee /opt/kilocode/mcp-servers/backup/recover-mcp.sh
#!/bin/bash

# Recovery script for MCP servers
BACKUP_FILE=$1
BACKUP_DIR="/opt/kilocode/mcp-servers/backups"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file>"
    exit 1
fi

if [ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_DIR/$BACKUP_FILE"
    exit 1
fi

# Stop services
sudo systemctl stop mcp-filesystem
sudo systemctl stop mcp-postgres
sudo systemctl stop mcp-memory

# Extract backup
cd /
sudo tar -xzf $BACKUP_DIR/$BACKUP_FILE

# Start services
sudo systemctl start mcp-filesystem
sudo systemctl start mcp-postgres
sudo systemctl start mcp-memory

echo "Recovery completed from backup: $BACKUP_FILE"
EOF

# Make recovery script executable
sudo chmod +x /opt/kilocode/mcp-servers/backup/recover-mcp.sh
```

### Step 8: Security Configuration

#### 8.1 Configure Firewall Rules
```bash
# Ubuntu/Debian (ufw)
sudo ufw allow ssh
sudo ufw allow from 192.168.1.0/24 to any port 22
sudo ufw allow from 192.168.1.0/24 to any port 5432
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --reload
```

#### 8.2 Set Up SSL/TLS Certificates
```bash
# Create SSL certificate directory
sudo mkdir -p /etc/ssl/kilocode
sudo chown root:root /etc/ssl/kilocode
sudo chmod 700 /etc/ssl/kilocode

# Generate self-signed certificate (for testing)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/kilocode/mcp.key \
    -out /etc/ssl/kilocode/mcp.crt \
    -subj "/C=US/ST=State/L=City/O=KiloCode/OU=MCP/CN=localhost"

# Set appropriate permissions
sudo chmod 600 /etc/ssl/kilocode/mcp.key
sudo chmod 644 /etc/ssl/kilocode/mcp.crt
```

## Verification and Testing

### Step 9: Installation Verification

#### 9.1 Check Service Status
```bash
# Check all services
sudo systemctl status mcp-filesystem
sudo systemctl status mcp-postgres
sudo systemctl status mcp-memory

# Check service logs
sudo journalctl -u mcp-filesystem -f
sudo journalctl -u mcp-postgres -f
sudo journalctl -u mcp-memory -f
```

#### 9.2 Test MCP Server Functionality
```bash
# Test filesystem server
curl -X POST http://localhost:3000/read_file \
    -H "Content-Type: application/json" \
    -d '{"path": "/etc/kilocode/mcp/mcp.json"}'

# Test postgres server
curl -X POST http://localhost:3001/execute_query \
    -H "Content-Type: application/json" \
    -d '{"query": "SELECT version();"}'

# Test memory service
curl -X POST http://localhost:3002/store_memory \
    -H "Content-Type: application/json" \
    -d '{"content": "Test memory", "tags": ["test"]}'
```

#### 9.3 Run Compliance Validation
```bash
# Run compliance validation
cd /opt/kilocode/mcp-servers/mcp-compliance-server
sudo -u mcp-service node test-server.js --compliance
```

### Step 10: Performance Testing

#### 10.1 Load Testing
```bash
# Install Apache Bench for load testing
sudo apt install apache2-utils

# Run load test on filesystem server
ab -n 1000 -c 10 http://localhost:3000/health

# Run load test on postgres server
ab -n 1000 -c 10 http://localhost:3001/health

# Run load test on memory service
ab -n 1000 -c 10 http://localhost:3002/health
```

#### 10.2 Resource Monitoring
```bash
# Monitor resource usage
htop

# Monitor disk usage
df -h

# Monitor memory usage
free -h

# Monitor network usage
iftop
```

## Troubleshooting Common Issues

### Issue 1: Service Fails to Start
**Symptom**: Systemd service fails to start
**Solution**: Check service logs with `journalctl -u <service-name> -f`

### Issue 2: Port Already in Use
**Symptom**: Error indicating port is already in use
**Solution**: Check what's using the port with `netstat -tulpn | grep :<port>`

### Issue 3: Permission Denied
**Symptom**: Permission errors when accessing files or directories
**Solution**: Check file permissions and ownership with `ls -la /path/to/file`

### Issue 4: Database Connection Issues
**Symptom**: Unable to connect to PostgreSQL database
**Solution**: Check database logs with `sudo journalctl -u postgresql -f`

### Issue 5: Memory Service Issues
**Symptom**: Memory service fails to start or function
**Solution**: Check Python environment and dependencies with `python memory_wrapper.py --help`

## Maintenance Schedule

### Daily Tasks
- Check service status
- Review health check logs
- Monitor disk space usage
- Check for error logs

### Weekly Tasks
- Review performance metrics
- Check backup integrity
- Update system packages
- Review security logs

### Monthly Tasks
- Test backup recovery
- Review compliance validation
- Update documentation
- Plan capacity upgrades

### Quarterly Tasks
- Security audit
- Performance optimization
- Disaster recovery testing
- Documentation review

## Support and Contact Information

### Technical Support
- **Email**: support@kilocode.com
- **Phone**: +1 (555) 123-4567
- **Hours**: 24/7 for production systems

### Documentation
- **Main Documentation**: [KiloCode MCP Documentation](https://docs.kilocode.com/mcp)
- **GitHub Issues**: [KiloCode GitHub](https://github.com/kilocode/kilocode/issues)
- **Community Forum**: [KiloCode Community](https://community.kilocode.com)

### Emergency Contacts
- **System Administrator**: admin@kilocode.com
- **Security Officer**: security@kilocode.com
- **Compliance Officer**: compliance@kilocode.com

---

*This installation guide is part of the KiloCode MCP Setup and Configuration Architecture Plan and should be reviewed and updated regularly to reflect changes in installation procedures and best practices.*