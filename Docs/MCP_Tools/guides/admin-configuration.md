# Configuration Management for System Administrators

## Overview

This guide provides comprehensive configuration management instructions for System Administrators managing MCP (Model Context Protocol) servers within the KiloCode ecosystem. The configuration process follows the **Simple, Robust, Secure** approach and ensures proper integration with existing infrastructure.

## Configuration Overview

### Configuration Hierarchy
The MCP server configuration follows a hierarchical structure:

1. **System-wide Configuration**: `/etc/kilocode/mcp/`
2. **Project Configuration**: `/opt/kilocode/mcp-servers/`
3. **Service-specific Configuration**: Individual service directories
4. **Environment Variables**: Runtime configuration
5. **Runtime Configuration**: Dynamic configuration changes

### Configuration Files Structure
```
/etc/kilocode/mcp/
├── mcp.json                    # Main MCP configuration
├── .env                        # Environment variables
├── servers/
│   ├── filesystem.json         # Filesystem server config
│   ├── postgres.json           # PostgreSQL server config
│   ├── memory.json             # Memory service config
│   └── compliance.json         # Compliance server config
├── security/
│   ├── ssl.crt                 # SSL certificate
│   ├── ssl.key                 # SSL private key
│   └── access-control.json     # Access control rules
└── logging/
    ├── logrotate.conf          # Log rotation configuration
    └── logging.conf            # Logging configuration
```

## Core Configuration Management

### Step 1: Base Configuration Setup

#### 1.1 Main MCP Configuration
```bash
# Create main MCP configuration file
cat << 'EOF' | sudo tee /etc/kilocode/mcp/mcp.json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", ".", "/tmp"],
      "env": {
        "NODE_ENV": "production",
        "KILOCODE_ENV": "production",
        "KILOCODE_PROJECT_PATH": "/opt/kilocode/mcp-servers"
      },
      "description": "Filesystem access for project files",
      "enabled": true,
      "restartPolicy": "always"
    },
    "postgres": {
      "command": "node",
      "args": ["/opt/kilocode/mcp-servers/kilocode-mcp-installer/dist/index.js", "postgres"],
      "env": {
        "DATABASE_URL": "postgresql://mcp_user:mcp_password@localhost:5432/mcp_db",
        "NODE_ENV": "production",
        "KILOCODE_ENV": "production"
      },
      "description": "PostgreSQL database connection",
      "enabled": true,
      "restartPolicy": "always"
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
      "description": "Persistent semantic memory service",
      "enabled": true,
      "restartPolicy": "always"
    },
    "compliance": {
      "command": "node",
      "args": ["/opt/kilocode/mcp-servers/mcp-compliance-server/src/index.js"],
      "env": {
        "COMPLIANCE_LOG_LEVEL": "INFO",
        "COMPLIANCE_REPORT_PATH": "/opt/kilocode/mcp-servers/reports"
      },
      "description": "Compliance validation server",
      "enabled": true,
      "restartPolicy": "always"
    }
  },
  "globalSettings": {
    "logLevel": "INFO",
    "maxConcurrentConnections": 100,
    "timeout": 30000,
    "enableMetrics": true,
    "metricsPort": 9090
  }
}
EOF
```

#### 1.2 Environment Configuration
```bash
# Create environment configuration file
cat << 'EOF' | sudo tee /etc/kilocode/mcp/.env
# KiloCode Environment Configuration
KILOCODE_ENV=production
KILOCODE_PROJECT_PATH=/opt/kilocode/mcp-servers
KILOCODE_PROJECT_NAME=KiloCode MCP Servers
KILOCODE_VERSION=1.0.0

# Database Configuration
DATABASE_URL=postgresql://mcp_user:mcp_password@localhost:5432/mcp_db
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=mcp_db
DATABASE_USER=mcp_user
DATABASE_PASSWORD=mcp_password
DATABASE_SSL_MODE=require
DATABASE_POOL_SIZE=20
DATABASE_CONNECTION_TIMEOUT=30

# Memory Service Configuration
MCP_MEMORY_VECTOR_DB_PATH=/opt/kilocode/mcp-servers/memory_db
MCP_MEMORY_BACKUPS_PATH=/opt/kilocode/mcp-servers/memory_backups
MCP_MEMORY_MAX_SIZE=1000000
MCP_MEMORY_CLEANUP_INTERVAL=3600
MCP_MEMORY_LOG_LEVEL=INFO
MCP_MEMORY_VECTOR_DIMENSION=1536
MCP_MEMORY_SIMILARITY_THRESHOLD=0.7

# Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=/var/log/kilocode/mcp
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=30
LOG_COMPRESS=true

# Security Configuration
SSL_CERT_PATH=/etc/kilocode/mcp/security/ssl.crt
SSL_KEY_PATH=/etc/kilocode/mcp/security/ssl.key
JWT_SECRET=your_jwt_secret_here
API_KEY=your_api_key_here

# Performance Configuration
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=30000
ENABLE_METRICS=true
METRICS_PORT=9090
METRICS_PATH=/metrics

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_INTERVAL=86400
BACKUP_RETENTION_DAYS=30
BACKUP_COMPRESSION=true

# Monitoring Configuration
HEALTH_CHECK_INTERVAL=300
HEALTH_CHECK_TIMEOUT=10
ENABLE_ALERTS=true
ALERT_EMAIL=admin@kilocode.com
EOF
```

### Step 2: Service-Specific Configuration

#### 2.1 Filesystem Server Configuration
```bash
# Create filesystem server configuration
cat << 'EOF' | sudo tee /etc/kilocode/mcp/servers/filesystem.json
{
  "filesystem": {
    "allowedPaths": [
      "/opt/kilocode/mcp-servers",
      "/tmp",
      "/var/log/kilocode/mcp"
    ],
    "blockedPaths": [
      "/etc",
      "/var/log",
      "/usr",
      "/bin",
      "/sbin",
      "/lib"
    ],
    "maxFileSize": "100MB",
    "maxDirectoryDepth": 10,
    "enableFileMonitoring": true,
    "fileWatchPatterns": [
      "**/*.log",
      "**/*.json",
      "**/*.js"
    ],
    "security": {
      "enablePathValidation": true,
      "enableFileAccessLogging": true,
      "maxConcurrentOperations": 50
    }
  }
}
EOF
```

#### 2.2 PostgreSQL Server Configuration
```bash
# Create PostgreSQL server configuration
cat << 'EOF' | sudo tee /etc/kilocode/mcp/servers/postgres.json
{
  "postgres": {
    "connection": {
      "host": "localhost",
      "port": 5432,
      "database": "mcp_db",
      "username": "mcp_user",
      "password": "${DATABASE_PASSWORD}",
      "sslMode": "require",
      "poolSize": 20,
      "connectionTimeout": 30,
      "idleTimeout": 300,
      "maxLifetime": 1800
    },
    "query": {
      "timeout": 30000,
      "fetchSize": 1000,
      "maxRows": 10000,
      "enableQueryLogging": true,
      "slowQueryThreshold": 5000
    },
    "security": {
      "enablePreparedStatement": true,
      "enableQueryValidation": true,
      "maxQueryLength": 10000
    },
    "backup": {
      "enabled": true,
      "interval": 86400,
      "retentionDays": 30,
      "compression": true,
      "path": "/opt/kilocode/mcp-servers/backups"
    }
  }
}
EOF
```

#### 2.3 Memory Service Configuration
```bash
# Create memory service configuration
cat << 'EOF' | sudo tee /etc/kilocode/mcp/servers/memory.json
{
  "memory": {
    "database": {
      "type": "sqlite",
      "path": "/opt/kilocode/mcp-servers/memory_db/memory.db",
      "backupPath": "/opt/kilocode/mcp-servers/memory_backups",
      "maxSize": 1000000,
      "cleanupInterval": 3600,
      "compression": true
    },
    "vector": {
      "dimension": 1536,
      "similarityThreshold": 0.7,
      "maxResults": 100,
      "enableIndexing": true,
      "indexType": "HNSW"
    },
    "operations": {
      "maxConcurrentOperations": 50,
      "operationTimeout": 30000,
      "enableBatchProcessing": true,
      "batchSize": 100
    },
    "security": {
      "enableEncryption": true,
      "enableAccessLogging": true,
      "maxMemorySize": "1GB"
    }
  }
}
EOF
```

#### 2.4 Compliance Server Configuration
```bash
# Create compliance server configuration
cat << 'EOF' | sudo tee /etc/kilocode/mcp/servers/compliance.json
{
  "compliance": {
    "validation": {
      "enabled": true,
      "interval": 3600,
      "autoRemediate": false,
      "requireApproval": true
    },
    "reporting": {
      "enabled": true,
      "path": "/opt/kilocode/mcp-servers/reports",
      "format": "json",
      "retentionDays": 90,
      "includeMetrics": true
    },
    "security": {
      "enableAuditLogging": true,
      "enableAlerting": true,
      "alertEmail": "admin@kilocode.com",
      "alertThreshold": "WARNING"
    },
    "rules": {
      "security": {
        "enabled": true,
        "severity": "HIGH"
      },
      "performance": {
        "enabled": true,
        "severity": "MEDIUM"
      },
      "compliance": {
        "enabled": true,
        "severity": "HIGH"
      }
    }
  }
}
EOF
```

### Step 3: Security Configuration

#### 3.1 Access Control Configuration
```bash
# Create access control configuration
cat << 'EOF' | sudo tee /etc/kilocode/mcp/security/access-control.json
{
  "accessControl": {
    "users": {
      "admin": {
        "role": "administrator",
        "permissions": ["read", "write", "execute", "configure", "monitor"],
        "allowedServers": ["*"],
        "allowedIPs": ["127.0.0.1", "192.168.1.0/24"]
      },
      "developer": {
        "role": "developer",
        "permissions": ["read", "write", "execute"],
        "allowedServers": ["filesystem", "postgres", "memory"],
        "allowedIPs": ["127.0.0.1", "192.168.1.0/24"]
      },
      "readonly": {
        "role": "readonly",
        "permissions": ["read"],
        "allowedServers": ["filesystem", "postgres"],
        "allowedIPs": ["127.0.0.1"]
      }
    },
    "servers": {
      "filesystem": {
        "allowedUsers": ["admin", "developer", "readonly"],
        "maxConnections": 10,
        "timeout": 30000
      },
      "postgres": {
        "allowedUsers": ["admin", "developer"],
        "maxConnections": 20,
        "timeout": 60000
      },
      "memory": {
        "allowedUsers": ["admin", "developer"],
        "maxConnections": 15,
        "timeout": 45000
      },
      "compliance": {
        "allowedUsers": ["admin"],
        "maxConnections": 5,
        "timeout": 30000
      }
    }
  }
}
EOF
```

#### 3.2 SSL/TLS Configuration
```bash
# Create SSL configuration
cat << 'EOF' | sudo tee /etc/kilocode/mcp/security/ssl.json
{
  "ssl": {
    "enabled": true,
    "certPath": "/etc/kilocode/mcp/security/ssl.crt",
    "keyPath": "/etc/kilocode/mcp/security/ssl.key",
    "caPath": "/etc/kilocode/mcp/security/ca.crt",
    "protocol": "TLSv1.2",
    "cipherSuites": [
      "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
      "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
      "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA",
      "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA"
    ],
    "dhParamPath": "/etc/kilocode/mcp/security/dhparam.pem",
    "sessionTimeout": 3600,
    "enableOCSPStapling": true,
    "enableHSTS": true,
    "hstsMaxAge": 31536000
  }
}
EOF
```

#### 3.3 Authentication Configuration
```bash
# Create authentication configuration
cat << 'EOF' | sudo tee /etc/kilocode/mcp/security/auth.json
{
  "authentication": {
    "jwt": {
      "enabled": true,
      "secret": "${JWT_SECRET}",
      "algorithm": "HS256",
      "expiresIn": 3600,
      "refreshTokenExpiresIn": 86400
    },
    "apiKeys": {
      "enabled": true,
      "apiKey": "${API_KEY}",
      "apiKeyHeader": "X-API-Key"
    },
    "basicAuth": {
      "enabled": false,
      "users": {
        "admin": "${ADMIN_PASSWORD}",
        "developer": "${DEVELOPER_PASSWORD}",
        "readonly": "${READONLY_PASSWORD}"
      }
    },
    "oauth2": {
      "enabled": false,
      "providers": {
        "github": {
          "clientId": "${GITHUB_CLIENT_ID}",
          "clientSecret": "${GITHUB_CLIENT_SECRET}",
          "callbackUrl": "https://your-domain.com/auth/callback"
        }
      }
    }
  }
}
EOF
```

### Step 4: Logging Configuration

#### 4.1 Logging Configuration
```bash
# Create logging configuration
cat << 'EOF' | sudo tee /etc/kilocode/mcp/logging/logging.conf
{
  "logging": {
    "level": "${LOG_LEVEL}",
    "dir": "${LOG_DIR}",
    "maxSize": "${LOG_MAX_SIZE}",
    "backupCount": "${LOG_BACKUP_COUNT}",
    "compress": "${LOG_COMPRESS}",
    "format": "json",
    "outputs": [
      {
        "type": "file",
        "path": "${LOG_DIR}/mcp.log",
        "maxSize": "${LOG_MAX_SIZE}",
        "backupCount": "${LOG_BACKUP_COUNT}",
        "compress": "${LOG_COMPRESS}"
      },
      {
        "type": "console",
        "colorize": true
      }
    ],
    "categories": {
      "default": {
        "level": "INFO",
        "outputs": ["*"]
      },
      "filesystem": {
        "level": "INFO",
        "outputs": ["file"]
      },
      "postgres": {
        "level": "INFO",
        "outputs": ["file"]
      },
      "memory": {
        "level": "INFO",
        "outputs": ["file"]
      },
      "compliance": {
        "level": "INFO",
        "outputs": ["file"]
      },
      "security": {
        "level": "WARNING",
        "outputs": ["file", "console"]
      },
      "performance": {
        "level": "INFO",
        "outputs": ["file"]
      }
    }
  }
}
EOF
```

#### 4.2 Log Rotation Configuration
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
        systemctl reload mcp-filesystem mcp-postgres mcp-memory mcp-compliance
    endscript
}
EOF
```

### Step 5: Monitoring and Metrics Configuration

#### 5.1 Metrics Configuration
```bash
# Create metrics configuration
cat << 'EOF' | sudo tee /etc/kilocode/mcp/monitoring/metrics.json
{
  "metrics": {
    "enabled": "${ENABLE_METRICS}",
    "port": "${METRICS_PORT}",
    "path": "${METRICS_PATH}",
    "collectors": [
      "system",
      "process",
      "memory",
      "disk",
      "network"
    ],
    "retention": {
      "duration": "7d",
      "cleanupInterval": "24h"
    },
    "alerting": {
      "enabled": true,
      "rules": [
        {
          "name": "high_cpu_usage",
          "condition": "cpu_usage > 80",
          "severity": "WARNING",
          "action": "alert"
        },
        {
          "name": "high_memory_usage",
          "condition": "memory_usage > 85",
          "severity": "WARNING",
          "action": "alert"
        },
        {
          "name": "disk_space_low",
          "condition": "disk_usage > 90",
          "severity": "CRITICAL",
          "action": "alert"
        }
      ]
    }
  }
}
EOF
```

#### 5.2 Health Check Configuration
```bash
# Create health check configuration
cat << 'EOF' | sudo tee /etc/kilocode/mcp/monitoring/health.json
{
  "health": {
    "enabled": true,
    "interval": "${HEALTH_CHECK_INTERVAL}",
    "timeout": "${HEALTH_CHECK_TIMEOUT}",
    "checks": {
      "filesystem": {
        "enabled": true,
        "path": "/opt/kilocode/mcp-servers",
        "writable": true
      },
      "postgres": {
        "enabled": true,
        "query": "SELECT 1",
        "timeout": 5000
      },
      "memory": {
        "enabled": true,
        "operation": "get_stats",
        "timeout": 10000
      },
      "compliance": {
        "enabled": true,
        "operation": "get_status",
        "timeout": 5000
      }
    },
    "notifications": {
      "enabled": "${ENABLE_ALERTS}",
      "email": "${ALERT_EMAIL}",
      "webhook": null,
      "slack": null
    }
  }
}
EOF
```

## Configuration Management Procedures

### Step 6: Configuration Deployment

#### 6.1 Configuration Validation
```bash
# Create configuration validation script
cat << 'EOF' | sudo tee /opt/kilocode/mcp-servers/scripts/validate-config.sh
#!/bin/bash

# Configuration validation script
CONFIG_DIR="/etc/kilocode/mcp"
LOG_FILE="/var/log/kilocode/mcp/config-validation.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] Starting configuration validation..." >> $LOG_FILE

# Validate JSON files
for config_file in $CONFIG_DIR/*.json; do
    if [ -f "$config_file" ]; then
        if ! jq empty "$config_file" 2>/dev/null; then
            echo "[$DATE] ERROR: Invalid JSON in $config_file" >> $LOG_FILE
            exit 1
        else
            echo "[$DATE] OK: Valid JSON in $config_file" >> $LOG_FILE
        fi
    fi
done

# Validate environment variables
if [ ! -f "$CONFIG_DIR/.env" ]; then
    echo "[$DATE] ERROR: Environment file not found" >> $LOG_FILE
    exit 1
else
    echo "[$DATE] OK: Environment file found" >> $LOG_FILE
fi

# Validate required directories
required_dirs=(
    "/opt/kilocode/mcp-servers"
    "/var/log/kilocode/mcp"
    "/opt/kilocode/mcp-servers/memory_db"
    "/opt/kilocode/mcp-servers/memory_backups"
    "/opt/kilocode/mcp-servers/reports"
)

for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "[$DATE] ERROR: Required directory not found: $dir" >> $LOG_FILE
        exit 1
    else
        echo "[$DATE] OK: Required directory found: $dir" >> $LOG_FILE
    fi
done

echo "[$DATE] Configuration validation completed successfully" >> $LOG_FILE
EOF

# Make validation script executable
sudo chmod +x /opt/kilocode/mcp-servers/scripts/validate-config.sh
```

#### 6.2 Configuration Deployment Script
```bash
# Create configuration deployment script
cat << 'EOF' | sudo tee /opt/kilocode/mcp-servers/scripts/deploy-config.sh
#!/bin/bash

# Configuration deployment script
CONFIG_DIR="/etc/kilocode/mcp"
BACKUP_DIR="/opt/kilocode/mcp-servers/config-backups"
DATE=$(date '+%Y%m%d_%H%M%S')
DEPLOY_LOG="/var/log/kilocode/mcp/deploy.log"

echo "[$DATE] Starting configuration deployment..." >> $DEPLOY_LOG

# Create backup of current configuration
mkdir -p $BACKUP_DIR
cp -r $CONFIG_DIR $BACKUP_DIR/config_backup_$DATE

# Validate configuration before deployment
/opt/kilocode/mcp-servers/scripts/validate-config.sh
if [ $? -ne 0 ]; then
    echo "[$DATE] ERROR: Configuration validation failed" >> $DEPLOY_LOG
    exit 1
fi

# Reload systemd configuration
systemctl daemon-reload

# Restart services in order
services=("mcp-filesystem" "mcp-postgres" "mcp-memory" "mcp-compliance")

for service in "${services[@]}"; do
    echo "[$DATE] Restarting $service..." >> $DEPLOY_LOG
    systemctl restart $service
    
    if [ $? -eq 0 ]; then
        echo "[$DATE] OK: $service restarted successfully" >> $DEPLOY_LOG
    else
        echo "[$DATE] ERROR: Failed to restart $service" >> $DEPLOY_LOG
        exit 1
    fi
    
    # Wait for service to start
    sleep 5
    
    # Check service status
    if systemctl is-active --quiet $service; then
        echo "[$DATE] OK: $service is running" >> $DEPLOY_LOG
    else
        echo "[$DATE] ERROR: $service is not running" >> $DEPLOY_LOG
        exit 1
    fi
done

echo "[$DATE] Configuration deployment completed successfully" >> $DEPLOY_LOG
EOF

# Make deployment script executable
sudo chmod +x /opt/kilocode/mcp-servers/scripts/deploy-config.sh
```

### Step 7: Configuration Backup and Recovery

#### 7.1 Configuration Backup Script
```bash
# Create configuration backup script
cat << 'EOF' | sudo tee /opt/kilocode/mcp-servers/scripts/backup-config.sh
#!/bin/bash

# Configuration backup script
CONFIG_DIR="/etc/kilocode/mcp"
BACKUP_DIR="/opt/kilocode/mcp-servers/config-backups"
DATE=$(date '+%Y%m%d_%H%M%S')
BACKUP_FILE="config_backup_$DATE.tar.gz"
BACKUP_LOG="/var/log/kilocode/mcp/backup.log"

echo "[$DATE] Starting configuration backup..." >> $BACKUP_LOG

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
tar -czf $BACKUP_DIR/$BACKUP_FILE \
    -C /etc/kilocode \
    mcp

# Verify backup
if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    echo "[$DATE] OK: Configuration backup created successfully" >> $BACKUP_LOG
else
    echo "[$DATE] ERROR: Failed to create configuration backup" >> $BACKUP_LOG
    exit 1
fi

# Keep only last 7 days of backups
find $BACKUP_DIR -name "config_backup_*.tar.gz" -mtime +7 -delete

echo "[$DATE] Configuration backup completed: $BACKUP_DIR/$BACKUP_FILE" >> $BACKUP_LOG
EOF

# Make backup script executable
sudo chmod +x /opt/kilocode/mcp-servers/scripts/backup-config.sh
```

#### 7.2 Configuration Recovery Script
```bash
# Create configuration recovery script
cat << 'EOF' | sudo tee /opt/kilocode/mcp-servers/scripts/recover-config.sh
#!/bin/bash

# Configuration recovery script
CONFIG_DIR="/etc/kilocode/mcp"
BACKUP_DIR="/opt/kilocode/mcp-servers/config-backups"
RECOVERY_LOG="/var/log/kilocode/mcp/recovery.log"

if [ -z "$1" ]; then
    echo "Usage: $0 <backup-file>"
    echo "Available backups:"
    ls -la $BACKUP_DIR/config_backup_*.tar.gz
    exit 1
fi

BACKUP_FILE="$1"
DATE=$(date '+%Y%m%d_%H%M%S')

echo "[$DATE] Starting configuration recovery from $BACKUP_FILE..." >> $RECOVERY_LOG

# Check if backup file exists
if [ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    echo "[$DATE] ERROR: Backup file not found: $BACKUP_DIR/$BACKUP_FILE" >> $RECOVERY_LOG
    exit 1
fi

# Stop services
echo "[$DATE] Stopping services..." >> $RECOVERY_LOG
systemctl stop mcp-filesystem mcp-postgres mcp-memory mcp-compliance

# Backup current configuration
echo "[$DATE] Creating backup of current configuration..." >> $RECOVERY_LOG
mkdir -p $BACKUP_DIR/current_backup_$DATE
cp -r $CONFIG_DIR $BACKUP_DIR/current_backup_$DATE

# Restore configuration
echo "[$DATE] Restoring configuration..." >> $RECOVERY_LOG
cd /
tar -xzf $BACKUP_DIR/$BACKUP_FILE

# Validate restored configuration
echo "[$DATE] Validating restored configuration..." >> $RECOVERY_LOG
/opt/kilocode/mcp-servers/scripts/validate-config.sh
if [ $? -ne 0 ]; then
    echo "[$DATE] ERROR: Restored configuration validation failed" >> $RECOVERY_LOG
    exit 1
fi

# Start services
echo "[$DATE] Starting services..." >> $RECOVERY_LOG
systemctl start mcp-filesystem mcp-postgres mcp-memory mcp-compliance

# Check service status
services=("mcp-filesystem" "mcp-postgres" "mcp-memory" "mcp-compliance")
for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        echo "[$DATE] OK: $service is running" >> $RECOVERY_LOG
    else
        echo "[$DATE] ERROR: $service is not running" >> $RECOVERY_LOG
        exit 1
    fi
done

echo "[$DATE] Configuration recovery completed successfully" >> $RECOVERY_LOG
EOF

# Make recovery script executable
sudo chmod +x /opt/kilocode/mcp-servers/scripts/recover-config.sh
```

## Configuration Management Best Practices

### Security Best Practices
1. **Environment Variables**: Store sensitive information in environment variables
2. **File Permissions**: Restrict access to configuration files
3. **SSL/TLS**: Always use SSL/TLS for external communications
4. **Access Control**: Implement role-based access control
5. **Audit Logging**: Enable audit logging for configuration changes

### Performance Best Practices
1. **Configuration Caching**: Cache frequently accessed configuration
2. **Lazy Loading**: Load configuration on demand
3. **Connection Pooling**: Use connection pooling for database connections
4. **Resource Limits**: Set appropriate resource limits
5. **Monitoring**: Monitor configuration performance

### Maintenance Best Practices
1. **Regular Backups**: Perform regular configuration backups
2. **Version Control**: Use version control for configuration files
3. **Testing**: Test configuration changes in a staging environment
4. **Documentation**: Document all configuration changes
5. **Automation**: Automate configuration deployment and validation

## Troubleshooting Configuration Issues

### Common Configuration Issues

#### Issue 1: Invalid JSON Configuration
**Symptom**: Services fail to start due to invalid JSON
**Solution**: Use `jq` to validate JSON files
```bash
# Validate JSON configuration
jq empty /etc/kilocode/mcp/mcp.json
```

#### Issue 2: Missing Environment Variables
**Symptom**: Services fail to start due to missing environment variables
**Solution**: Check environment file and variable references
```bash
# Check environment file
cat /etc/kilocode/mcp/.env

# Check variable references
grep -r "\${" /etc/kilocode/mcp/
```

#### Issue 3: Permission Issues
**Symptom**: Services fail to access configuration files
**Solution**: Check file permissions and ownership
```bash
# Check file permissions
ls -la /etc/kilocode/mcp/

# Fix permissions
sudo chown -R mcp-service:mcp-service /etc/kilocode/mcp/
sudo chmod 640 /etc/kilocode/mcp/*.json
sudo chmod 600 /etc/kilocode/mcp/.env
```

#### Issue 4: Service Configuration Mismatch
**Symptom**: Services start but don't behave as expected
**Solution**: Verify service configuration matches system configuration
```bash
# Check service configuration
systemctl show mcp-filesystem --property=Environment

# Check service logs
journalctl -u mcp-filesystem -f
```

### Configuration Debugging

#### Debug Mode Configuration
```bash
# Enable debug logging
sudo sed -i 's/LOG_LEVEL=INFO/LOG_LEVEL=DEBUG/' /etc/kilocode/mcp/.env

# Restart services
sudo systemctl restart mcp-filesystem mcp-postgres mcp-memory mcp-compliance

# Check debug logs
tail -f /var/log/kilocode/mcp/*.log
```

#### Configuration Validation
```bash
# Validate all configurations
sudo /opt/kilocode/mcp-servers/scripts/validate-config.sh

# Check configuration syntax
sudo /opt/kilocode/mcp-servers/scripts/deploy-config.sh --dry-run
```

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

*This configuration management guide is part of the KiloCode MCP Setup and Configuration Architecture Plan and should be reviewed and updated regularly to reflect changes in configuration procedures and best practices.*