# Configuration Procedures for MCP Servers

## Overview

This guide provides comprehensive configuration procedures for MCP (Model Context Protocol) servers within the KiloCode ecosystem. The configuration process follows the **Simple, Robust, Secure** approach and ensures proper setup and operation of all components.

## Configuration Philosophy

### Key Principles
1. **Simplicity**: Use simple, clear configuration formats
2. **Robustness**: Implement proper validation and error handling
3. **Security**: Secure configuration by default
4. **Consistency**: Maintain consistent configuration across all servers
5. **Maintainability**: Ensure configurations are easy to maintain and update

### Configuration Structure
```
/etc/kilocode/mcp/
├── mcp.json                 # Main MCP configuration
├── .env                     # Environment variables
├── servers/
│   ├── filesystem.json      # Fileserver configuration
│   ├── postgres.json        # PostgreSQL server configuration
│   ├── memory.json          # Memory service configuration
│   └── compliance.json      # Compliance server configuration
├── security/
│   ├── ssl.json            # SSL/TLS configuration
│   ├── encryption.json     # Encryption configuration
│   └── access.json         # Access control configuration
└── monitoring/
    ├── metrics.json        # Metrics configuration
    └── logging.json        # Logging configuration
```

## Configuration Files

### 1. Main MCP Configuration

#### File: `/etc/kilocode/mcp/mcp.json`
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/opt/kilocode/mcp-servers", "/tmp"],
      "env": {
        "NODE_ENV": "production",
        "KILOCODE_ENV": "production",
        "KILOCODE_PROJECT_PATH": "/opt/kilocode/mcp-servers"
      },
      "description": "Filesystem access for MCP servers",
      "alwaysAllow": ["read_file", "write_file", "list_directory"]
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "NODE_ENV": "production",
        "KILOCODE_ENV": "production",
        "DATABASE_URL": "postgresql://mcp_user:mcp_password@localhost:5432/mcp_db"
      },
      "description": "PostgreSQL database connection",
      "alwaysAllow": ["execute_query", "get_schema", "get_tables"]
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
      "description": "Memory service for MCP servers"
    },
    "compliance": {
      "command": "node",
      "args": ["/opt/kilocode/mcp-servers/mcp-compliance-server/src/index.js"],
      "env": {
        "COMPLIANCE_LOG_LEVEL": "INFO",
        "COMPLIANCE_REPORT_PATH": "/opt/kilocode/mcp-servers/reports"
      },
      "description": "Compliance server for MCP servers"
    }
  },
  "globalSettings": {
    "logLevel": "INFO",
    "enableMetrics": true,
    "metricsPort": 9090,
    "enableSSL": true,
    "sslCertPath": "/etc/ssl/kilocode/mcp.crt",
    "sslKeyPath": "/etc/ssl/kilocode/mcp.key"
  }
}
```

### 2. Environment Configuration

#### File: `/etc/kilocode/mcp/.env`
```bash
# Environment Configuration
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
MCP_MEMORY_MAX_SIZE=100000
MCP_MEMORY_CLEANUP_INTERVAL=3600
MCP_MEMORY_LOG_LEVEL=INFO

# Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=/var/log/kilocode/mcp
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=7
LOG_COMPRESS=false

# Security Configuration
ENABLE_SSL=true
SSL_CERT_PATH=/etc/ssl/kilocode/mcp.crt
SSL_KEY_PATH=/etc/ssl/kilocode/mcp.key
JWT_SECRET=your_jwt_secret_here
API_KEY=your_api_key_here

# Performance Configuration
ENABLE_METRICS=true
METRICS_PORT=9090
METRICS_RETENTION_DAYS=30

# Compliance Configuration
COMPLIANCE_RULES_PATH=/opt/kilocode/mcp-servers/rules
COMPLIANCE_REPORTS_PATH=/opt/kilocode/mcp-servers/reports
COMPLIANCE_AUTO_FIX=false
COMPLIANCE_REQUIRE_APPROVAL=true
```

### 3. Server-Specific Configurations

#### File: `/etc/kilocode/mcp/servers/filesystem.json`
```json
{
  "server": {
    "port": 3000,
    "host": "localhost",
    "logLevel": "INFO",
    "timeout": 30000,
    "maxConnections": 100
  },
  "filesystem": {
    "root": "/opt/kilocode/mcp-servers",
    "allowedPaths": ["/opt/kilocode/mcp-servers", "/tmp", "/home"],
    "maxFileSize": 10485760,
    "maxDepth": 10,
    "followSymlinks": false,
    "includeHidden": false
  },
  "security": {
    "enableAuthentication": true,
    "enableAuthorization": true,
    "allowedUsers": ["mcp-service"],
    "rateLimit": {
      "enabled": true,
      "requestsPerMinute": 100
    }
  }
}
```

#### File: `/etc/kilocode/mcp/servers/postgres.json`
```json
{
  "server": {
    "port": 3001,
    "host": "localhost",
    "logLevel": "INFO",
    "timeout": 30000,
    "maxConnections": 50
  },
  "database": {
    "connectionString": "postgresql://mcp_user:mcp_password@localhost:5432/mcp_db",
    "pool": {
      "min": 2,
      "max": 20,
      "idleTimeoutMillis": 30000,
      "connectionTimeoutMillis": 10000
    },
    "queryTimeout": 30000,
    "idleTimeout": 60000,
    "maxRetries": 3,
    "retryDelay": 1000
  },
  "security": {
    "enableSSL": true,
    "sslCertPath": "/etc/ssl/kilocode/mcp.crt",
    "sslKeyPath": "/etc/ssl/kilocode/mcp.key",
    "allowedUsers": ["mcp-service"],
    "rateLimit": {
      "enabled": true,
      "requestsPerMinute": 60
    }
  }
}
```

#### File: `/etc/kilocode/mcp/servers/memory.json`
```json
{
  "server": {
    "port": 3002,
    "host": "localhost",
    "logLevel": "INFO",
    "timeout": 30000,
    "maxConnections": 100
  },
  "database": {
    "vectorDbPath": "/opt/kilocode/mcp-servers/memory_db",
    "backupsPath": "/opt/kilocode/mcp-servers/memory_backups",
    "maxSize": 100000,
    "cleanupInterval": 3600,
    "compression": true,
    "encryption": true
  },
  "memory": {
    "maxItems": 10000,
    "maxSizePerItem": 1024000,
    "defaultTags": ["default"],
    "autoConsolidate": true,
    "consolidationInterval": 86400,
    "retentionDays": 30
  },
  "security": {
    "enableAuthentication": true,
    "enableAuthorization": true,
    "allowedUsers": ["mcp-service"],
    "rateLimit": {
      "enabled": true,
      "requestsPerMinute": 200
    }
  }
}
```

#### File: `/etc/kilocode/mcp/servers/compliance.json`
```json
{
  "server": {
    "port": 3003,
    "host": "localhost",
    "logLevel": "INFO",
    "timeout": 30000,
    "maxConnections": 50
  },
  "compliance": {
    "rulesPath": "/opt/kilocode/mcp-servers/rules",
    "reportsPath": "/opt/kilocode/mcp-servers/reports",
    "autoFix": false,
    "requireApproval": true,
    "maxConcurrentChecks": 5,
    "checkTimeout": 300000
  },
  "security": {
    "enableAuthentication": true,
    "enableAuthorization": true,
    "allowedUsers": ["mcp-service"],
    "rateLimit": {
      "enabled": true,
      "requestsPerMinute": 30
    }
  }
}
```

### 4. Security Configuration

#### File: `/etc/kilocode/mcp/security/ssl.json`
```json
{
  "ssl": {
    "enabled": true,
    "certPath": "/etc/ssl/kilocode/mcp.crt",
    "keyPath": "/etc/ssl/kilocode/mcp.key",
    "protocol": "TLSv1.2",
    "cipherSuites": [
      "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
      "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
      "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA",
      "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA"
    ],
    "sessionTimeout": 3600,
    "enableOCSPStapling": true,
    "enableHSTS": true,
    "hstsMaxAge": 31536000,
    "hstsIncludeSubDomains": true,
    "hstsPreload": false
  }
}
```

#### File: `/etc/kilocode/mcp/security/encryption.json`
```json
{
  "encryption": {
    "enabled": true,
    "algorithm": "AES-256-GCM",
    "keyRotationInterval": 86400,
    "dataEncryption": {
      "enabled": true,
      "algorithm": "AES-256-GCM",
      "keySize": 256,
      "ivSize": 128
    },
    "transportEncryption": {
      "enabled": true,
      "algorithm": "TLSv1.2",
      "certificatePath": "/etc/ssl/kilocode/mcp.crt",
      "privateKeyPath": "/etc/ssl/kilocode/mcp.key"
    },
    "databaseEncryption": {
      "enabled": true,
      "algorithm": "AES-256-GCM",
      "keyPath": "/etc/kilocode/mcp/security/db.key"
    }
  }
}
```

#### File: `/etc/kilocode/mcp/security/access.json`
```json
{
  "access": {
    "authentication": {
      "enabled": true,
      "method": "jwt",
      "jwt": {
        "secret": "your_jwt_secret_here",
        "algorithm": "HS256",
        "expiresIn": 3600,
        "refreshTokenExpiresIn": 86400
      },
      "apiKey": {
        "enabled": true,
        "header": "X-API-Key",
        "prefix": "kcp_"
      }
    },
    "authorization": {
      "enabled": true,
      "method": "role",
      "roles": {
        "admin": {
          "permissions": ["*"]
        },
        "user": {
          "permissions": ["read", "write", "execute"]
        },
        "readonly": {
          "permissions": ["read"]
        }
      }
    },
    "rateLimit": {
      "enabled": true,
      "windowMs": 60000,
      "maxRequests": 100,
      "skipSuccessfulRequests": false,
      "skipFailedRequests": false
    }
  }
}
```

### 5. Monitoring Configuration

#### File: `/etc/kilocode/mcp/monitoring/metrics.json`
```json
{
  "metrics": {
    "enabled": true,
    "port": 9090,
    "path": "/metrics",
    "retentionDays": 30,
    "collectors": {
      "system": {
        "enabled": true,
        "interval": 10
      },
      "application": {
        "enabled": true,
        "interval": 30
      },
      "database": {
        "enabled": true,
        "interval": 60
      }
    },
    "endpoints": {
      "prometheus": {
        "enabled": true,
        "path": "/metrics"
      },
      "health": {
        "enabled": true,
        "path": "/health"
      },
      "info": {
        "enabled": true,
        "path": "/info"
      }
    }
  }
}
```

#### File: `/etc/kilocode/mcp/monitoring/logging.json`
```json
{
  "logging": {
    "enabled": true,
    "level": "INFO",
    "format": "json",
    "directory": "/var/log/kilocode/mcp",
    "maxSize": "10MB",
    "maxFiles": 7,
    "compress": true,
    "console": false,
    "file": {
      "enabled": true,
      "filename": "mcp.log"
    },
    "syslog": {
      "enabled": false,
      "host": "localhost",
      "port": 514,
      "facility": "local0"
    },
    "logstash": {
      "enabled": false,
      "host": "localhost",
      "port": 5000,
      "index": "mcp"
    }
  }
}
```

## Configuration Procedures

### Procedure 1: Initial Configuration Setup

#### Step 1: Create Configuration Directory Structure
```bash
# Create main configuration directory
sudo mkdir -p /etc/kilocode/mcp
sudo mkdir -p /etc/kilocode/mcp/servers
sudo mkdir -p /etc/kilocode/mcp/security
sudo mkdir -p /etc/kilocode/mcp/monitoring

# Set appropriate permissions
sudo chown -R $USER:$USER /etc/kilocode/mcp
sudo chmod 755 /etc/kilocode/mcp
sudo chmod 644 /etc/kilocode/mcp/*.json
sudo chmod 600 /etc/kilocode/mcp/.env
```

#### Step 2: Generate SSL Certificates
```bash
# Create SSL certificate directory
sudo mkdir -p /etc/ssl/kilocode
sudo chown root:root /etc/ssl/kilocode
sudo chmod 700 /etc/ssl/kilocode

# Generate SSL certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/kilocode/mcp.key \
    -out /etc/ssl/kilocode/mcp.crt \
    -subj "/C=US/ST=State/L=City/O=KiloCode/OU=MCP/CN=localhost"

# Set appropriate permissions
sudo chmod 600 /etc/ssl/kilocode/mcp.key
sudo chmod 644 /etc/ssl/kilocode/mcp.crt
```

#### Step 3: Generate Encryption Keys
```bash
# Generate database encryption key
sudo openssl rand -base64 32 > /etc/kilocode/mcp/security/db.key
sudo chmod 600 /etc/kilocode/mcp/security/db.key

# Generate JWT secret
sudo openssl rand -base64 32 > /etc/kilocode/mcp/security/jwt.secret
sudo chmod 600 /etc/kilocode/mcp/security/jwt.secret

# Generate API key
sudo openssl rand -hex 32 > /etc/kilocode/mcp/security/api.key
sudo chmod 600 /etc/kilocode/mcp/security/api.key
```

#### Step 4: Create Configuration Files
```bash
# Create main MCP configuration
cat << 'EOF' | sudo tee /etc/kilocode/mcp/mcp.json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/opt/kilocode/mcp-servers", "/tmp"],
      "env": {
        "NODE_ENV": "production",
        "KILOCODE_ENV": "production",
        "KILOCODE_PROJECT_PATH": "/opt/kilocode/mcp-servers"
      },
      "description": "Filesystem access for MCP servers"
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "NODE_ENV": "production",
        "KILOCODE_ENV": "production",
        "DATABASE_URL": "postgresql://mcp_user:mcp_password@localhost:5432/mcp_db"
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
      "description": "Memory service for MCP servers"
    },
    "compliance": {
      "command": "node",
      "args": ["/opt/kilocode/mcp-servers/mcp-compliance-server/src/index.js"],
      "env": {
        "COMPLIANCE_LOG_LEVEL": "INFO",
        "COMPLIANCE_REPORT_PATH": "/opt/kilocode/mcp-servers/reports"
      },
      "description": "Compliance server for MCP servers"
    }
  },
  "globalSettings": {
    "logLevel": "INFO",
    "enableMetrics": true,
    "metricsPort": 9090,
    "enableSSL": true,
    "sslCertPath": "/etc/ssl/kilocode/mcp.crt",
    "sslKeyPath": "/etc/ssl/kilocode/mcp.key"
  }
}
EOF

# Create environment file
cat << 'EOF' | sudo tee /etc/kilocode/mcp/.env
KILOCODE_ENV=production
KILOCODE_PROJECT_PATH=/opt/kilocode/mcp-servers
KILOCODE_PROJECT_NAME=KiloCode MCP Servers

DATABASE_URL=postgresql://mcp_user:mcp_password@localhost:5432/mcp_db
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=mcp_db
DATABASE_USER=mcp_user
DATABASE_PASSWORD=mcp_password

MCP_MEMORY_VECTOR_DB_PATH=/opt/kilocode/mcp-servers/memory_db
MCP_MEMORY_BACKUPS_PATH=/opt/kilocode/mcp-servers/memory_backups
MCP_MEMORY_MAX_SIZE=100000
MCP_MEMORY_CLEANUP_INTERVAL=3600
MCP_MEMORY_LOG_LEVEL=INFO

LOG_LEVEL=INFO
LOG_DIR=/var/log/kilocode/mcp
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=7
LOG_COMPRESS=false

ENABLE_SSL=true
SSL_CERT_PATH=/etc/ssl/kilocode/mcp.crt
SSL_KEY_PATH=/etc/ssl/kilocode/mcp.key
JWT_SECRET=$(cat /etc/kilocode/mcp/security/jwt.secret)
API_KEY=$(cat /etc/kilocode/mcp/security/api.key)

ENABLE_METRICS=true
METRICS_PORT=9090
METRICS_RETENTION_DAYS=30

COMPLIANCE_RULES_PATH=/opt/kilocode/mcp-servers/rules
COMPLIANCE_REPORTS_PATH=/opt/kilocode/mcp-servers/reports
COMPLIANCE_AUTO_FIX=false
COMPLIANCE_REQUIRE_APPROVAL=true
EOF
```

### Procedure 2: Server Configuration Updates

#### Step 1: Update Server Configuration
```bash
# Update filesystem server configuration
cat << 'EOF' | sudo tee /etc/kilocode/mcp/servers/filesystem.json
{
  "server": {
    "port": 3000,
    "host": "localhost",
    "logLevel": "INFO",
    "timeout": 30000,
    "maxConnections": 100
  },
  "filesystem": {
    "root": "/opt/kilocode/mcp-servers",
    "allowedPaths": ["/opt/kilocode/mcp-servers", "/tmp", "/home"],
    "maxFileSize": 10485760,
    "maxDepth": 10,
    "followSymlinks": false,
    "includeHidden": false
  },
  "security": {
    "enableAuthentication": true,
    "enableAuthorization": true,
    "allowedUsers": ["mcp-service"],
    "rateLimit": {
      "enabled": true,
      "requestsPerMinute": 100
    }
  }
}
EOF

# Update PostgreSQL server configuration
cat << 'EOF' | sudo tee /etc/kilocode/mcp/servers/postgres.json
{
  "server": {
    "port": 3001,
    "host": "localhost",
    "logLevel": "INFO",
    "timeout": 30000,
    "maxConnections": 50
  },
  "database": {
    "connectionString": "postgresql://mcp_user:mcp_password@localhost:5432/mcp_db",
    "pool": {
      "min": 2,
      "max": 20,
      "idleTimeoutMillis": 30000,
      "connectionTimeoutMillis": 10000
    },
    "queryTimeout": 30000,
    "idleTimeout": 60000,
    "maxRetries": 3,
    "retryDelay": 1000
  },
  "security": {
    "enableSSL": true,
    "sslCertPath": "/etc/ssl/kilocode/mcp.crt",
    "sslKeyPath": "/etc/ssl/kilocode/mcp.key",
    "allowedUsers": ["mcp-service"],
    "rateLimit": {
      "enabled": true,
      "requestsPerMinute": 60
    }
  }
}
EOF
```

#### Step 2: Validate Configuration
```bash
# Validate configuration syntax
sudo /opt/kilocode/mcp-servers/scripts/validate-config.sh

# Check JSON syntax
cat /etc/kilocode/mcp/mcp.json | jq .

# Validate environment variables
source /etc/kilocode/mcp/.env
echo "KILOCODE_ENV: $KILOCODE_ENV"
echo "DATABASE_URL: $DATABASE_URL"
```

#### Step 3: Restart Services
```bash
# Restart all MCP services
sudo systemctl restart mcp-filesystem
sudo systemctl restart mcp-postgres
sudo systemctl restart mcp-memory
sudo systemctl restart mcp-compliance

# Check service status
sudo systemctl status mcp-filesystem
sudo systemctl status mcp-postgres
sudo systemctl status mcp-memory
sudo systemctl status mcp-compliance
```

### Procedure 3: Security Configuration Updates

#### Step 1: Update SSL Configuration
```bash
# Generate new SSL certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/kilocode/mcp.key \
    -out /etc/ssl/kilocode/mcp.crt \
    -subj "/C=US/ST=State/L=City/O=KiloCode/OU=MCP/CN=localhost"

# Update SSL configuration
cat << 'EOF' | sudo tee /etc/kilocode/mcp/security/ssl.json
{
  "ssl": {
    "enabled": true,
    "certPath": "/etc/ssl/kilocode/mcp.crt",
    "keyPath": "/etc/ssl/kilocode/mcp.key",
    "protocol": "TLSv1.2",
    "cipherSuites": [
      "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
      "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
      "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA",
      "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA"
    ],
    "sessionTimeout": 3600,
    "enableOCSPStapling": true,
    "enableHSTS": true,
    "hstsMaxAge": 31536000,
    "hstsIncludeSubDomains": true,
    "hstsPreload": false
  }
}
EOF
```

#### Step 2: Update Access Control
```bash
# Update access control configuration
cat << 'EOF' | sudo tee /etc/kilocode/mcp/security/access.json
{
  "access": {
    "authentication": {
      "enabled": true,
      "method": "jwt",
      "jwt": {
        "secret": $(cat /etc/kilocode/mcp/security/jwt.secret),
        "algorithm": "HS256",
        "expiresIn": 3600,
        "refreshTokenExpiresIn": 86400
      },
      "apiKey": {
        "enabled": true,
        "header": "X-API-Key",
        "prefix": "kcp_"
      }
    },
    "authorization": {
      "enabled": true,
      "method": "role",
      "roles": {
        "admin": {
          "permissions": ["*"]
        },
        "user": {
          "permissions": ["read", "write", "execute"]
        },
        "readonly": {
          "permissions": ["read"]
        }
      }
    },
    "rateLimit": {
      "enabled": true,
      "windowMs": 60000,
      "maxRequests": 100,
      "skipSuccessfulRequests": false,
      "skipFailedRequests": false
    }
  }
}
EOF
```

#### Step 3: Update Encryption Configuration
```bash
# Generate new encryption key
sudo openssl rand -base64 32 > /etc/kilocode/mcp/security/db.key
sudo chmod 600 /etc/kilocode/mcp/security/db.key

# Update encryption configuration
cat << 'EOF' | sudo tee /etc/kilocode/mcp/security/encryption.json
{
  "encryption": {
    "enabled": true,
    "algorithm": "AES-256-GCM",
    "keyRotationInterval": 86400,
    "dataEncryption": {
      "enabled": true,
      "algorithm": "AES-256-GCM",
      "keySize": 256,
      "ivSize": 128
    },
    "transportEncryption": {
      "enabled": true,
      "algorithm": "TLSv1.2",
      "certificatePath": "/etc/ssl/kilocode/mcp.crt",
      "privateKeyPath": "/etc/ssl/kilocode/mcp.key"
    },
    "databaseEncryption": {
      "enabled": true,
      "algorithm": "AES-256-GCM",
      "keyPath": "/etc/kilocode/mcp/security/db.key"
    }
  }
}
EOF
```

### Procedure 4: Monitoring Configuration Updates

#### Step 1: Update Metrics Configuration
```bash
# Update metrics configuration
cat << 'EOF' | sudo tee /etc/kilocode/mcp/monitoring/metrics.json
{
  "metrics": {
    "enabled": true,
    "port": 9090,
    "path": "/metrics",
    "retentionDays": 30,
    "collectors": {
      "system": {
        "enabled": true,
        "interval": 10
      },
      "application": {
        "enabled": true,
        "interval": 30
      },
      "database": {
        "enabled": true,
        "interval": 60
      }
    },
    "endpoints": {
      "prometheus": {
        "enabled": true,
        "path": "/metrics"
      },
      "health": {
        "enabled": true,
        "path": "/health"
      },
      "info": {
        "enabled": true,
        "path": "/info"
      }
    }
  }
}
EOF
```

#### Step 2: Update Logging Configuration
```bash
# Update logging configuration
cat << 'EOF' | sudo tee /etc/kilocode/mcp/monitoring/logging.json
{
  "logging": {
    "enabled": true,
    "level": "INFO",
    "format": "json",
    "directory": "/var/log/kilocode/mcp",
    "maxSize": "10MB",
    "maxFiles": 7,
    "compress": true,
    "console": false,
    "file": {
      "enabled": true,
      "filename": "mcp.log"
    },
    "syslog": {
      "enabled": false,
      "host": "localhost",
      "port": 514,
      "facility": "local0"
    },
    "logstash": {
      "enabled": false,
      "host": "localhost",
      "port": 5000,
      "index": "mcp"
    }
  }
}
EOF
```

#### Step 3: Restart Monitoring Services
```bash
# Restart monitoring services
sudo systemctl restart prometheus
sudo systemctl restart grafana-server

# Check monitoring service status
sudo systemctl status prometheus
sudo systemctl status grafana-server
```

## Configuration Validation

### Step 1: Validate Configuration Files
```bash
# Validate JSON syntax
for config_file in /etc/kilocode/mcp/*.json /etc/kilocode/mcp/servers/*.json /etc/kilocode/mcp/security/*.json /etc/kilocode/mcp/monitoring/*.json; do
    echo "Validating $config_file..."
    cat "$config_file" | jq . > /dev/null
    if [ $? -eq 0 ]; then
        echo "OK: $config_file is valid"
    else
        echo "ERROR: $config_file is invalid"
    fi
done
```

### Step 2: Validate Environment Variables
```bash
# Validate environment variables
source /etc/kilocode/mcp/.env

# Check required variables
required_vars=("KILOCODE_ENV" "KILOCODE_PROJECT_PATH" "DATABASE_URL" "MCP_MEMORY_VECTOR_DB_PATH")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "ERROR: $var is not set"
    else
        echo "OK: $var is set to ${!var}"
    fi
done
```

### Step 3: Validate Service Configuration
```bash
# Validate service configuration
services=("mcp-filesystem" "mcp-postgres" "mcp-memory" "mcp-compliance")
for service in "${services[@]}"; do
    echo "Validating $service configuration..."
    if systemctl is-active --quiet $service; then
        echo "OK: $service is running"
    else
        echo "ERROR: $service is not running"
    fi
done
```

## Configuration Backup and Recovery

### Step 1: Create Configuration Backup
```bash
# Create backup directory
sudo mkdir -p /opt/kilocode/mcp-servers/backups/config
sudo chown -R $USER:$USER /opt/kilocode/mcp-servers/backups

# Create backup
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
sudo tar -czf /opt/kilocode/mcp-servers/backups/config/config_backup_$BACKUP_DATE.tar.gz \
    -C /etc/kilocode \
    mcp

# Verify backup
if [ -f "/opt/kilocode/mcp-servers/backups/config/config_backup_$BACKUP_DATE.tar.gz" ]; then
    echo "Backup created successfully: /opt/kilocode/mcp-servers/backups/config/config_backup_$BACKUP_DATE.tar.gz"
else
    echo "ERROR: Failed to create backup"
fi
```

### Step 2: Restore Configuration from Backup
```bash
# List available backups
ls -la /opt/kilocode/mcp-servers/backups/config/

# Extract backup
BACKUP_FILE="config_backup_20240101_120000.tar.gz"
sudo tar -xzf /opt/kilocode/mcp-servers/backups/config/$BACKUP_FILE \
    -C /etc/kilocode

# Restore permissions
sudo chown -R $USER:$USER /etc/kilocode/mcp
sudo chmod 644 /etc/kilocode/mcp/*.json
sudo chmod 600 /etc/kilocode/mcp/.env

# Restart services
sudo systemctl restart mcp-filesystem mcp-postgres mcp-memory mcp-compliance
```

## Configuration Management Best Practices

### Best Practices
1. **Version Control**: Keep configuration files in version control
2. **Documentation**: Document all configuration changes
3. **Testing**: Test configuration changes in a development environment first
4. **Backup**: Regularly backup configuration files
5. **Security**: Secure sensitive configuration data
6. **Monitoring**: Monitor configuration changes
7. **Automation**: Automate configuration management where possible

### Configuration Change Management
1. **Plan**: Plan configuration changes carefully
2. **Test**: Test changes in a development environment
3. **Document**: Document all changes
4. **Review**: Review changes with stakeholders
5. **Deploy**: Deploy changes to production
6. **Monitor**: Monitor the impact of changes
7. **Rollback**: Prepare rollback procedures

### Security Considerations
1. **Sensitive Data**: Never store sensitive data in configuration files
2. **Access Control**: Restrict access to configuration files
3. **Encryption**: Encrypt sensitive configuration data
4. **Audit**: Audit configuration changes
5. **Compliance**: Ensure configuration meets compliance requirements

## Support and Contact Information

### Technical Support
- **Email**: support@kilocode.com
- **Phone**: +1 (555) 123-4567
- **Hours**: 24/7 for production support

### Documentation
- **Main Documentation**: [KiloCode Documentation](https://docs.kilocode.com/mcp)
- **GitHub Issues**: [KiloCode GitHub](https://github.com/kilocode/kilocode/issues)
- **Community Forum**: [KiloCode Community](https://community.kilocode.com)

### Configuration Support
- **Configuration Support**: config@kilocode.com
- **Security Configuration**: security@kilocode.com
- **Monitoring Configuration**: monitoring@kilocode.com

---

*This configuration procedures guide is part of the KiloCode MCP Setup and Configuration Architecture Plan and should be reviewed and updated regularly to reflect changes in configuration procedures and best practices.*