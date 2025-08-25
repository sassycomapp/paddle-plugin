# Database Schema and Configuration File Specifications

## Overview

This document provides comprehensive database schema and configuration file specifications for MCP (Model Context Protocol) servers within the KiloCode ecosystem. The specifications follow the **Simple, Robust, Secure** approach and ensure proper data management and configuration.

## Database Schema Specifications

### 1. PostgreSQL Database Schema

#### 1.1 Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created_at ON users(created_at);
```

#### 1.2 Compliance Logs Table
```sql
CREATE TABLE compliance_logs (
    id SERIAL PRIMARY KEY,
    check_id VARCHAR(100) NOT NULL,
    rule_id VARCHAR(50) NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    server_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('passed', 'failed', 'warning', 'error')),
    message TEXT,
    remediation_command TEXT,
    remediation_description TEXT,
    auto_fix BOOLEAN DEFAULT false,
    require_approval BOOLEAN DEFAULT true,
    approved_by VARCHAR(50),
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key to users table
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_compliance_logs_check_id ON compliance_logs(check_id);
CREATE INDEX idx_compliance_logs_rule_id ON compliance_logs(rule_id);
CREATE INDEX idx_compliance_logs_server_name ON compliance_logs(server_name);
CREATE INDEX idx_compliance_logs_status ON compliance_logs(status);
CREATE INDEX idx_compliance_logs_created_at ON compliance_logs(created_at);
CREATE INDEX idx_compliance_logs_user_id ON compliance_logs(user_id);
```

#### 1.3 Memory Items Table
```sql
CREATE TABLE memory_items (
    id SERIAL PRIMARY KEY,
    memory_id VARCHAR(100) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    tags TEXT[], -- Array of tags
    metadata JSONB, -- Additional metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE,
    
    -- Vector embedding for semantic search
    embedding VECTOR(1536), -- OpenAI embedding size
    similarity_score FLOAT DEFAULT 0.0
);

-- Indexes
CREATE INDEX idx_memory_items_memory_id ON memory_items(memory_id);
CREATE INDEX idx_memory_items_tags ON memory_items USING GIN(tags);
CREATE INDEX idx_memory_items_expires_at ON memory_items(expires_at);
CREATE INDEX idx_memory_items_created_at ON memory_items(created_at);
CREATE INDEX idx_memory_items_access_count ON memory_items(access_count);
CREATE INDEX idx_memory_items_embedding ON memory_items USING hnsw (embedding vector_cosine_ops);
```

#### 1.4 Configuration Files Table
```sql
CREATE TABLE configuration_files (
    id SERIAL PRIMARY KEY,
    file_path VARCHAR(500) UNIQUE NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    checksum VARCHAR(64) NOT NULL, -- SHA-256 hash
    version INTEGER DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_configuration_files_file_path ON configuration_files(file_path);
CREATE INDEX idx_configuration_files_file_name ON configuration_files(file_name);
CREATE INDEX idx_configuration_files_file_type ON configuration_files(file_type);
CREATE INDEX idx_configuration_files_checksum ON configuration_files(checksum);
CREATE INDEX idx_configuration_files_version ON configuration_files(version);
CREATE INDEX idx_configuration_files_is_active ON configuration_files(is_active);
CREATE INDEX idx_configuration_files_created_at ON configuration_files(created_at);
```

#### 1.5 Audit Logs Table
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100),
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    ip_address INET,
    user_agent TEXT,
    request_data JSONB,
    response_data JSONB,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_resource_id ON audit_logs(resource_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_ip_address ON audit_logs(ip_address);
CREATE INDEX idx_audit_logs_status ON audit_logs(status);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

#### 1.6 System Metrics Table
```sql
CREATE TABLE system_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(20),
    server_name VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    tags JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX idx_system_metrics_metric_name ON system_metrics(metric_name);
CREATE INDEX idx_system_metrics_server_name ON system_metrics(server_name);
CREATE INDEX idx_system_metrics_timestamp ON system_metrics(timestamp);
CREATE INDEX idx_system_metrics_tags ON system_metrics USING GIN(tags);
```

#### 1.7 API Keys Table
```sql
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    key_id VARCHAR(100) UNIQUE NOT NULL,
    key_prefix VARCHAR(10) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    permissions TEXT[], -- Array of permissions
    is_active BOOLEAN NOT NULL DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_api_keys_key_id ON api_keys(key_id);
CREATE INDEX idx_api_keys_key_prefix ON api_keys(key_prefix);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);
CREATE INDEX idx_api_keys_expires_at ON api_keys(expires_at);
CREATE INDEX idx_api_keys_created_by ON api_keys(created_by);
```

#### 1.8 Server Status Table
```sql
CREATE TABLE server_status (
    id SERIAL PRIMARY KEY,
    server_name VARCHAR(100) NOT NULL,
    server_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('running', 'stopped', 'error', 'maintenance')),
    health_score INTEGER CHECK (health_score >= 0 AND health_score <= 100),
    cpu_usage FLOAT,
    memory_usage FLOAT,
    disk_usage FLOAT,
    response_time FLOAT,
    last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_server_status_server_name ON server_status(server_name);
CREATE INDEX idx_server_status_server_type ON server_status(server_type);
CREATE INDEX idx_server_status_status ON server_status(status);
CREATE INDEX idx_server_status_last_heartbeat ON server_status(last_heartbeat);
CREATE INDEX idx_server_status_created_at ON server_status(created_at);
```

### 2. Database Views

#### 2.1 Compliance Summary View
```sql
CREATE VIEW compliance_summary AS
SELECT 
    server_name,
    COUNT(*) as total_checks,
    COUNT(CASE WHEN status = 'passed' THEN 1 END) as passed_checks,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_checks,
    COUNT(CASE WHEN status = 'warning' THEN 1 END) as warning_checks,
    COUNT(CASE WHEN status = 'error' THEN 1 END) as error_checks,
    ROUND(
        (COUNT(CASE WHEN status = 'passed' THEN 1 END) * 100.0) / 
        NULLIF(COUNT(*), 0), 2
    ) as compliance_score,
    MAX(created_at) as last_check
FROM compliance_logs
GROUP BY server_name;
```

#### 2.2 User Activity View
```sql
CREATE VIEW user_activity AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.role,
    COUNT(a.id) as total_actions,
    COUNT(CASE WHEN a.status = 'success' THEN 1 END) as successful_actions,
    COUNT(CASE WHEN a.status = 'failed' THEN 1 END) as failed_actions,
    MAX(a.created_at) as last_activity
FROM users u
LEFT JOIN audit_logs a ON u.id = a.user_id
GROUP BY u.id, u.username, u.email, u.role;
```

#### 2.3 Memory Statistics View
```sql
CREATE VIEW memory_statistics AS
SELECT 
    COUNT(*) as total_items,
    COUNT(CASE WHEN expires_at > CURRENT_TIMESTAMP THEN 1 END) as active_items,
    COUNT(CASE WHEN expires_at <= CURRENT_TIMESTAMP THEN 1 END) as expired_items,
    AVG(LENGTH(content)) as avg_content_size,
    MAX(access_count) as max_access_count,
    SUM(access_count) as total_accesses
FROM memory_items;
```

### 3. Database Functions

#### 3.1 Update Timestamp Function
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';
```

#### 3.2 Create Triggers
```sql
-- Trigger for updating updated_at timestamp
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_configuration_files_updated_at BEFORE UPDATE ON configuration_files
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger for soft deletion
CREATE OR REPLACE FUNCTION soft_delete_configuration_files()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.is_active = true THEN
        NEW.is_active = false;
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END IF;
    RETURN OLD;
END;
$$ language 'plpgsql';

CREATE TRIGGER soft_delete_config_files BEFORE UPDATE ON configuration_files
    FOR EACH ROW EXECUTE FUNCTION soft_delete_configuration_files();
```

#### 3.3 Data Cleanup Function
```sql
CREATE OR REPLACE FUNCTION cleanup_expired_data()
RETURNS void AS $$
BEGIN
    -- Delete expired memory items
    DELETE FROM memory_items 
    WHERE expires_at <= CURRENT_TIMESTAMP;
    
    -- Delete expired API keys
    DELETE FROM api_keys 
    WHERE expires_at <= CURRENT_TIMESTAMP AND is_active = false;
    
    -- Delete old audit logs (keep last 90 days)
    DELETE FROM audit_logs 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days';
    
    -- Delete old compliance logs (keep last 180 days)
    DELETE FROM compliance_logs 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '180 days';
    
    -- Delete old system metrics (keep last 30 days)
    DELETE FROM system_metrics 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '30 days';
END;
$$ language 'plpgsql';
```

### 4. Database Configuration

#### 4.1 PostgreSQL Configuration
```ini
# postgresql.conf
# Connection Settings
listen_addresses = 'localhost'
port = 5432
max_connections = 200

# Memory Settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Checkpoint Settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# Logging Settings
log_statement = 'all'
log_duration = on
log_line_prefix = '%m [%p] %q%u@%d '
log_timezone = 'UTC'

# Security Settings
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
password_encryption = scram-sha-256

# Performance Settings
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 8MB
maintenance_work_mem = 128MB
```

#### 4.2 Database Connection Pool
```sql
-- Create connection pool
CREATE ROLE app_user LOGIN PASSWORD 'secure_password';
CREATE DATABASE mcp_db WITH OWNER app_user;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE mcp_db TO app_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO app_user;
```

## Configuration File Specifications

### 1. Main Configuration File

#### 1.1 MCP Configuration File (`mcp.json`)
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
      "alwaysAllow": ["read_file", "write_file", "list_directory"],
      "timeout": 30000,
      "maxConnections": 100
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "NODE_ENV": "production",
        "KILOCODE_ENV": "production",
        "DATABASE_URL": "postgresql://app_user:secure_password@localhost:5432/mcp_db"
      },
      "description": "PostgreSQL database connection",
      "alwaysAllow": ["execute_query", "get_schema", "get_tables"],
      "timeout": 30000,
      "maxConnections": 50
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
      "description": "Memory service for MCP servers",
      "timeout": 30000,
      "maxConnections": 100
    },
    "compliance": {
      "command": "node",
      "args": ["/opt/kilocode/mcp-servers/mcp-compliance-server/src/index.js"],
      "env": {
        "COMPLIANCE_LOG_LEVEL": "INFO",
        "COMPLIANCE_REPORT_PATH": "/opt/kilocode/mcp-servers/reports"
      },
      "description": "Compliance server for MCP servers",
      "timeout": 30000,
      "maxConnections": 50
    }
  },
  "globalSettings": {
    "logLevel": "INFO",
    "enableMetrics": true,
    "metricsPort": 9090,
    "enableSSL": true,
    "sslCertPath": "/etc/ssl/kilocode/mcp.crt",
    "sslKeyPath": "/etc/ssl/kilocode/mcp.key",
    "enableCompression": true,
    "maxRequestSize": "10MB",
    "requestTimeout": 30000
  }
}
```

#### 1.2 Environment Configuration File (`.env`)
```bash
# Environment Configuration
KILOCODE_ENV=production
KILOCODE_PROJECT_PATH=/opt/kilocode/mcp-servers
KILOCODE_PROJECT_NAME=KiloCode MCP Servers

# Database Configuration
DATABASE_URL=postgresql://app_user:secure_password@localhost:5432/mcp_db
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=mcp_db
DATABASE_USER=app_user
DATABASE_PASSWORD=secure_password
DATABASE_POOL_SIZE=20
DATABASE_POOL_TIMEOUT=30
DATABASE_SSL_MODE=require

# Memory Service Configuration
MCP_MEMORY_VECTOR_DB_PATH=/opt/kilocode/mcp-servers/memory_db
MCP_MEMORY_BACKUPS_PATH=/opt/kilocode/mcp-servers/memory_backups
MCP_MEMORY_MAX_SIZE=100000
MCP_MEMORY_CLEANUP_INTERVAL=3600
MCP_MEMORY_LOG_LEVEL=INFO
MCP_MEMORY_EMBEDDING_MODEL=text-embedding-ada-002

# Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=/var/log/kilocode/mcp
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=7
LOG_COMPRESS=true
LOG_FORMAT=json

# Security Configuration
ENABLE_SSL=true
SSL_CERT_PATH=/etc/ssl/kilocode/mcp.crt
SSL_KEY_PATH=/etc/ssl/kilocode/mcp.key
JWT_SECRET=your_jwt_secret_here_change_in_production
API_KEY=your_api_key_here_change_in_production
ENCRYPTION_KEY=your_encryption_key_here_change_in_production

# Performance Configuration
ENABLE_METRICS=true
METRICS_PORT=9090
METRICS_RETENTION_DAYS=30
METRICS_ENABLED=true
METRICS_ENDPOINT=/metrics

# Compliance Configuration
COMPLIANCE_RULES_PATH=/opt/kilocode/mcp-servers/rules
COMPLIANCE_REPORTS_PATH=/opt/kilocode/mcp-servers/reports
COMPLIANCE_AUTO_FIX=false
COMPLIANCE_REQUIRE_APPROVAL=true
COMPLIANCE_CHECK_INTERVAL=3600
COMPLIANCE_ALERT_THRESHOLD=5

# Monitoring Configuration
MONITORING_ENABLED=true
MONITORING_PORT=8080
MONITORING_HEALTH_CHECK_INTERVAL=30
MONITORING_METRICS_INTERVAL=60

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_PATH=/opt/kilocode/mcp-servers/backups
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE=0 2 * * *
BACKUP_COMPRESSION=true

# Security Configuration
SECURITY_RATE_LIMIT=100
SECURITY_RATE_LIMIT_WINDOW=3600
SECURITY_MAX_LOGIN_ATTEMPTS=5
SECURITY_SESSION_TIMEOUT=3600
SECURITY_PASSWORD_EXPIRY_DAYS=90
```

### 2. Server-Specific Configuration Files

#### 2.1 Fileserver Configuration (`filesystem.json`)
```json
{
  "server": {
    "port": 3000,
    "host": "localhost",
    "logLevel": "INFO",
    "timeout": 30000,
    "maxConnections": 100,
    "enableCompression": true,
    "maxRequestSize": "10MB"
  },
  "filesystem": {
    "root": "/opt/kilocode/mcp-servers",
    "allowedPaths": ["/opt/kilocode/mcp-servers", "/tmp", "/home"],
    "maxFileSize": 10485760,
    "maxDepth": 10,
    "followSymlinks": false,
    "includeHidden": false,
    "enableWatch": true,
    "watchInterval": 1000
  },
  "security": {
    "enableAuthentication": true,
    "enableAuthorization": true,
    "allowedUsers": ["mcp-service"],
    "rateLimit": {
      "enabled": true,
      "requestsPerMinute": 100,
      "burst": 200
    },
    "cors": {
      "enabled": true,
      "origins": ["http://localhost:3000", "http://localhost:3001"],
      "methods": ["GET", "POST", "PUT", "DELETE"],
      "headers": ["Content-Type", "Authorization"]
    }
  },
  "logging": {
    "enabled": true,
    "level": "INFO",
    "format": "json",
    "file": "/var/log/kilocode/mcp/filesystem.log",
    "maxSize": "10MB",
    "maxFiles": 7,
    "compress": true
  }
}
```

#### 2.2 PostgreSQL Configuration (`postgres.json`)
```json
{
  "server": {
    "port": 3001,
    "host": "localhost",
    "logLevel": "INFO",
    "timeout": 30000,
    "maxConnections": 50,
    "enableSSL": true
  },
  "database": {
    "connectionString": "postgresql://app_user:secure_password@localhost:5432/mcp_db",
    "pool": {
      "min": 2,
      "max": 20,
      "idleTimeoutMillis": 30000,
      "connectionTimeoutMillis": 10000,
      "maxUses": 7500
    },
    "queryTimeout": 30000,
    "idleTimeout": 60000,
    "maxRetries": 3,
    "retryDelay": 1000,
    "ssl": {
      "rejectUnauthorized": true,
      "ca": "/etc/ssl/kilocode/ca.crt"
    }
  },
  "security": {
    "enableAuthentication": true,
    "enableAuthorization": true,
    "allowedUsers": ["mcp-service"],
    "rateLimit": {
      "enabled": true,
      "requestsPerMinute": 60,
      "burst": 120
    },
    "queryLogging": true,
    "slowQueryThreshold": 5000
  },
  "logging": {
    "enabled": true,
    "level": "INFO",
    "format": "json",
    "file": "/var/log/kilocode/mcp/postgres.log",
    "maxSize": "10MB",
    "maxFiles": 7,
    "compress": true
  }
}
```

#### 2.3 Memory Service Configuration (`memory.json`)
```json
{
  "server": {
    "port": 3002,
    "host": "localhost",
    "logLevel": "INFO",
    "timeout": 30000,
    "maxConnections": 100,
    "enableCompression": true
  },
  "database": {
    "vectorDbPath": "/opt/kilocode/mcp-servers/memory_db",
    "backupsPath": "/opt/kilocode/mcp-servers/memory_backups",
    "maxSize": 100000,
    "cleanupInterval": 3600,
    "compression": true,
    "encryption": true,
    "backupInterval": 86400,
    "backupRetention": 30
  },
  "memory": {
    "maxItems": 10000,
    "maxSizePerItem": 1024000,
    "defaultTags": ["default"],
    "autoConsolidate": true,
    "consolidationInterval": 86400,
    "retentionDays": 30,
    "embeddingModel": "text-embedding-ada-002",
    "similarityThreshold": 0.7
  },
  "security": {
    "enableAuthentication": true,
    "enableAuthorization": true,
    "allowedUsers": ["mcp-service"],
    "rateLimit": {
      "enabled": true,
      "requestsPerMinute": 200,
      "burst": 400
    },
    "dataEncryption": {
      "enabled": true,
      "algorithm": "AES-256-GCM",
      "keyRotationInterval": 86400
    }
  },
  "logging": {
    "enabled": true,
    "level": "INFO",
    "format": "json",
    "file": "/var/log/kilocode/mcp/memory.log",
    "maxSize": "10MB",
    "maxFiles": 7,
    "compress": true
  }
}
```

#### 2.4 Compliance Server Configuration (`compliance.json`)
```json
{
  "server": {
    "port": 3003,
    "host": "localhost",
    "logLevel": "INFO",
    "timeout": 30000,
    "maxConnections": 50,
    "enableSSL": true
  },
  "compliance": {
    "rulesPath": "/opt/kilocode/mcp-servers/rules",
    "reportsPath": "/opt/kilocode/mcp-servers/reports",
    "autoFix": false,
    "requireApproval": true,
    "maxConcurrentChecks": 5,
    "checkTimeout": 300000,
    "alertThreshold": 5,
    "notificationChannels": ["email", "slack"]
  },
  "security": {
    "enableAuthentication": true,
    "enableAuthorization": true,
    "allowedUsers": ["mcp-service"],
    "rateLimit": {
      "enabled": true,
      "requestsPerMinute": 30,
      "burst": 60
    },
    "auditLogging": true,
    "auditRetention": 365
  },
  "logging": {
    "enabled": true,
    "level": "INFO",
    "format": "json",
    "file": "/var/log/kilocode/mcp/compliance.log",
    "maxSize": "10MB",
    "maxFiles": 7,
    "compress": true
  }
}
```

### 3. Security Configuration Files

#### 3.1 SSL Configuration (`ssl.json`)
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
    "hstsPreload": false,
    "certRenewalDays": 30,
    "certValidation": true
  }
}
```

#### 3.2 Access Control Configuration (`access.json`)
```json
{
  "access": {
    "authentication": {
      "enabled": true,
      "method": "jwt",
      "jwt": {
        "secret": "your_jwt_secret_here_change_in_production",
        "algorithm": "HS256",
        "expiresIn": 3600,
        "refreshTokenExpiresIn": 86400,
        "issuer": "kilocode-mcp",
        "audience": "mcp-clients"
      },
      "apiKey": {
        "enabled": true,
        "header": "X-API-Key",
        "prefix": "kcp_",
        "length": 32
      },
      "session": {
        "enabled": true,
        "timeout": 3600,
        "refreshInterval": 1800
      }
    },
    "authorization": {
      "enabled": true,
      "method": "role",
      "roles": {
        "admin": {
          "permissions": ["*"],
          "description": "System administrator with full access"
        },
        "user": {
          "permissions": ["read", "write", "execute"],
          "description": "Regular user with standard permissions"
        },
        "readonly": {
          "permissions": ["read"],
          "description": "Read-only user with limited access"
        },
        "service": {
          "permissions": ["read", "write"],
          "description": "Service account with service-specific permissions"
        }
      },
      "resourceBased": {
        "enabled": true,
        "rules": [
          {
            "resource": "filesystem",
            "actions": ["read", "write"],
            "conditions": {
              "ip": ["192.168.1.0/24"],
              "time": ["09:00-17:00"]
            }
          }
        ]
      }
    },
    "rateLimit": {
      "enabled": true,
      "windowMs": 60000,
      "maxRequests": 100,
      "skipSuccessfulRequests": false,
      "skipFailedRequests": false,
      "skip": ["/health", "/metrics"]
    }
  }
}
```

### 4. Monitoring Configuration Files

#### 4.1 Metrics Configuration (`metrics.json`)
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
        "interval": 10,
        "metrics": ["cpu", "memory", "disk", "network"]
      },
      "application": {
        "enabled": true,
        "interval": 30,
        "metrics": ["requests", "responses", "errors", "latency"]
      },
      "database": {
        "enabled": true,
        "interval": 60,
        "metrics": ["connections", "queries", "slow_queries", "transactions"]
      },
      "business": {
        "enabled": true,
        "interval": 300,
        "metrics": ["compliance_score", "active_users", "memory_usage"]
      }
    },
    "endpoints": {
      "prometheus": {
        "enabled": true,
        "path": "/metrics",
        "format": "prometheus"
      },
      "health": {
        "enabled": true,
        "path": "/health",
        "format": "json"
      },
      "info": {
        "enabled": true,
        "path": "/info",
        "format": "json"
      },
      "metrics": {
        "enabled": true,
        "path": "/api/v1/metrics",
        "format": "json"
      }
    },
    "alerting": {
      "enabled": true,
      "rules": [
        {
          "name": "high_cpu_usage",
          "condition": "cpu_usage > 80",
          "threshold": 5,
          "action": "alert"
        },
        {
          "name": "high_memory_usage",
          "condition": "memory_usage > 85",
          "threshold": 3,
          "action": "alert"
        },
        {
          "name": "high_error_rate",
          "condition": "error_rate > 5",
          "threshold": 10,
          "action": "alert"
        }
      ]
    }
  }
}
```

#### 4.2 Logging Configuration (`logging.json`)
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
      "filename": "mcp.log",
      "path": "/var/log/kilocode/mcp"
    },
    "syslog": {
      "enabled": false,
      "host": "localhost",
      "port": 514,
      "facility": "local0",
      "protocol": "udp"
    },
    "logstash": {
      "enabled": false,
      "host": "localhost",
      "port": 5000,
      "index": "mcp",
      "ssl": {
        "enabled": false,
        "caCert": "/etc/ssl/kilocode/ca.crt"
      }
    },
    "elasticsearch": {
      "enabled": false,
      "hosts": ["localhost:9200"],
      "index": "mcp-logs",
      "auth": {
        "username": "elastic",
        "password": "password"
      }
    },
    "fields": {
      "service": "mcp",
      "environment": "production",
      "version": "1.0.0"
    }
  }
}
```

## Configuration Validation

### 1. Configuration Validation Scripts

#### 1.1 JSON Configuration Validation
```bash
#!/bin/bash

# Validate JSON configuration files
CONFIG_DIR="/etc/kilocode/mcp"
ERROR_COUNT=0

for config_file in "$CONFIG_DIR"/*.json; do
    echo "Validating $config_file..."
    if [ -f "$config_file" ]; then
        if jq empty "$config_file" 2>/dev/null; then
            echo "✓ $config_file is valid JSON"
        else
            echo "✗ $config_file is invalid JSON"
            ERROR_COUNT=$((ERROR_COUNT + 1))
        fi
    else
        echo "⚠ $config_file does not exist"
    fi
done

if [ $ERROR_COUNT -eq 0 ]; then
    echo "All configuration files are valid"
    exit 0
else
    echo "Found $ERROR_COUNT invalid configuration files"
    exit 1
fi
```

#### 1.2 Environment Variable Validation
```bash
#!/bin/bash

# Validate environment variables
ENV_FILE="/etc/kilocode/mcp/.env"
REQUIRED_VARS=(
    "KILOCODE_ENV"
    "KILOCODE_PROJECT_PATH"
    "DATABASE_URL"
    "MCP_MEMORY_VECTOR_DB_PATH"
    "JWT_SECRET"
    "API_KEY"
)

echo "Validating environment variables..."
source "$ENV_FILE"

ERROR_COUNT=0
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "✗ Required variable $var is not set"
        ERROR_COUNT=$((ERROR_COUNT + 1))
    else
        echo "✓ $var is set"
    fi
done

if [ $ERROR_COUNT -eq 0 ]; then
    echo "All required environment variables are set"
    exit 0
else
    echo "Found $ERROR_COUNT missing environment variables"
    exit 1
fi
```

#### 1.3 Database Connection Validation
```bash
#!/bin/bash

# Validate database connection
DB_CONNECTION_STRING=$(grep "DATABASE_URL" /etc/kilocode/mcp/.env | cut -d'=' -f2)

echo "Validating database connection..."
if psql "$DB_CONNECTION_STRING" -c "SELECT 1;" >/dev/null 2>&1; then
    echo "✓ Database connection successful"
    exit 0
else
    echo "✗ Database connection failed"
    exit 1
fi
```

### 2. Configuration Management Best Practices

#### 2.1 Configuration Security
1. **Never hardcode credentials** in configuration files
2. **Use environment variables** for sensitive data
3. **Restrict file permissions** on configuration files
4. **Encrypt sensitive configuration data**
5. **Regularly rotate secrets and keys**
6. **Audit configuration changes**
7. **Use configuration management tools**

#### 2.2 Configuration Validation
1. **Validate configuration syntax** before deployment
2. **Check for required environment variables**
3. **Verify database connectivity**
4. **Test configuration in staging first**
5. **Use automated validation scripts**
6. **Implement configuration drift detection**
7. **Regular configuration audits**

#### 2.3 Configuration Backup and Recovery
1. **Regular backups** of configuration files
2. **Version control** for configuration changes
3. **Disaster recovery procedures**
4. **Configuration rollback capabilities**
5. **Documentation of configuration changes**
6. **Testing backup and recovery procedures**

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
- **Database Support**: database@kilocode.com
- **Configuration Support**: config@kilocode.com
- **Security Configuration**: security@kilocode.com

---

*This database schema and configuration file specifications guide is part of the KiloCode MCP Setup and Configuration Architecture Plan and should be reviewed and updated regularly to reflect changes in database schema and configuration requirements.*