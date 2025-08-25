# MCP Server Database Schema and Configuration File Specifications

## Overview

This document provides comprehensive database schema and configuration file specifications for MCP (Model Context Protocol) servers within the KiloCode ecosystem. The specifications cover database design, configuration file formats, and data models, following the **Simple, Robust, Secure** approach.

## Database Philosophy

### Key Principles
1. **Simplicity**: Provide clear, intuitive database design
2. **Robustness**: Ensure reliable data storage with proper relationships
3. **Security**: Implement secure data handling with encryption and access control
4. **Consistency**: Maintain consistent data models across all servers
5. **Scalability**: Design for future growth and performance optimization

### Database Types
- **PostgreSQL**: Primary relational database for structured data
- **SQLite**: Lightweight database for development and testing
- **Redis**: In-memory database for caching and session management
- **ChromaDB**: Vector database for memory storage and retrieval

---

## PostgreSQL Database Schema

### 1. Compliance Server Schema

#### 1.1 Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    permissions TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created_at ON users(created_at);
```

#### 1.2 Servers Table
```sql
CREATE TABLE servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'stopped',
    health VARCHAR(20) NOT NULL DEFAULT 'unknown',
    version VARCHAR(20) NOT NULL,
    description TEXT,
    configuration JSONB,
    last_check TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_servers_name ON servers(name);
CREATE INDEX idx_servers_type ON servers(type);
CREATE INDEX idx_servers_status ON servers(status);
CREATE INDEX idx_servers_health ON servers(health);
CREATE INDEX idx_servers_created_at ON servers(created_at);
```

#### 1.3 Compliance Checks Table
```sql
CREATE TABLE compliance_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    check_id VARCHAR(100) UNIQUE NOT NULL,
    server_name VARCHAR(100) NOT NULL,
    check_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    overall_score DECIMAL(5,2),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (server_name) REFERENCES servers(name) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_compliance_checks_server_name ON compliance_checks(server_name);
CREATE INDEX idx_compliance_checks_status ON compliance_checks(status);
CREATE INDEX idx_compliance_checks_started_at ON compliance_checks(started_at);
CREATE INDEX idx_compliance_checks_check_id ON compliance_checks(check_id);
```

#### 1.4 Compliance Results Table
```sql
CREATE TABLE compliance_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    check_id UUID NOT NULL,
    category VARCHAR(50) NOT NULL,
    score DECIMAL(5,2) NOT NULL,
    total_checks INTEGER NOT NULL,
    passed_checks INTEGER NOT NULL,
    failed_checks INTEGER NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (check_id) REFERENCES compliance_checks(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_compliance_results_check_id ON compliance_results(check_id);
CREATE INDEX idx_compliance_results_category ON compliance_results(category);
CREATE INDEX idx_compliance_results_score ON compliance_results(score);
```

#### 1.5 Compliance Issues Table
```sql
CREATE TABLE compliance_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    check_id UUID NOT NULL,
    issue_id VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    category VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    recommendation TEXT,
    affected_components TEXT[],
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    
    FOREIGN KEY (check_id) REFERENCES compliance_checks(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_compliance_issues_check_id ON compliance_issues(check_id);
CREATE INDEX idx_compliance_issues_severity ON compliance_issues(severity);
CREATE INDEX idx_compliance_issues_category ON compliance_issues(category);
CREATE INDEX idx_compliance_issues_status ON compliance_issues(status);
CREATE INDEX idx_compliance_issues_created_at ON compliance_issues(created_at);
```

#### 1.6 Audit Logs Table
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_resource_id ON audit_logs(resource_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
```

### 2. Memory Service Schema

#### 2.1 Memories Table
```sql
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id VARCHAR(100) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL,
    vector_embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_consolidated BOOLEAN DEFAULT false,
    consolidation_id UUID,
    
    FOREIGN KEY (consolidation_id) REFERENCES consolidations(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_memories_memory_id ON memories(memory_id);
CREATE INDEX idx_memories_created_at ON memories(created_at);
CREATE INDEX idx_memories_expires_at ON memories(expires_at);
CREATE INDEX idx_memories_is_consolidated ON memories(is_consolidated);
CREATE INDEX idx_memories_consolidation_id ON memories(consolidation_id);
```

#### 2.2 Consolidations Table
```sql
CREATE TABLE consolidations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consolidation_id VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    criteria JSONB NOT NULL,
    options JSONB NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_consolidations_consolidation_id ON consolidations(consolidation_id);
CREATE INDEX idx_consolidations_status ON consolidations(status);
CREATE INDEX idx_consolidations_started_at ON consolidations(started_at);
```

#### 2.3 Memory Tags Table
```sql
CREATE TABLE memory_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID NOT NULL,
    tag VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_memory_tags_memory_id ON memory_tags(memory_id);
CREATE INDEX idx_memory_tags_tag ON memory_tags(tag);
```

#### 2.4 Search History Table
```sql
CREATE TABLE search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    filters JSONB,
    results_count INTEGER NOT NULL,
    execution_time INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_search_history_created_at ON search_history(created_at);
CREATE INDEX idx_search_history_query ON search_history(query);
```

### 3. Integration Coordinator Schema

#### 3.1 Integration Sessions Table
```sql
CREATE TABLE integration_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(100) UNIQUE NOT NULL,
    initiator VARCHAR(50) NOT NULL,
    target VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    request_data JSONB,
    response_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_integration_sessions_session_id ON integration_sessions(session_id);
CREATE INDEX idx_integration_sessions_initiator ON integration_sessions(initiator);
CREATE INDEX idx_integration_sessions_target ON integration_sessions(target);
CREATE INDEX idx_integration_sessions_status ON integration_sessions(status);
CREATE INDEX idx_integration_sessions_created_at ON integration_sessions(created_at);
```

#### 3.2 Approval Requests Table
```sql
CREATE TABLE approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    approval_id VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,
    request_data JSONB NOT NULL,
    requested_by VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    approved_by VARCHAR(50),
    decision TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    rejected_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_approval_requests_approval_id ON approval_requests(approval_id);
CREATE INDEX idx_approval_requests_type ON approval_requests(type);
CREATE INDEX idx_approval_requests_status ON approval_requests(status);
CREATE INDEX idx_approval_requests_requested_by ON approval_requests(requested_by);
CREATE INDEX idx_approval_requests_expires_at ON approval_requests(expires_at);
```

#### 3.3 Audit Trails Table
```sql
CREATE TABLE audit_trails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    action VARCHAR(100) NOT NULL,
    actor VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id VARCHAR(100),
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES integration_sessions(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_audit_trails_session_id ON audit_trails(session_id);
CREATE INDEX idx_audit_trails_action ON audit_trails(action);
CREATE INDEX idx_audit_trails_actor ON audit_trails(actor);
CREATE INDEX idx_audit_trails_target_type ON audit_trails(target_type);
CREATE INDEX idx_audit_trails_timestamp ON audit_trails(timestamp);
```

---

## SQLite Database Schema (Development)

### 1. Compliance Server Schema
```sql
-- Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(6)))),
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    permissions TEXT DEFAULT '[]',
    is_active INTEGER DEFAULT 1,
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Servers table
CREATE TABLE servers (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(6)))),
    name TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'stopped',
    health TEXT NOT NULL DEFAULT 'unknown',
    version TEXT NOT NULL,
    description TEXT,
    configuration TEXT,
    last_check DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Compliance checks table
CREATE TABLE compliance_checks (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(6)))),
    check_id TEXT UNIQUE NOT NULL,
    server_name TEXT NOT NULL,
    check_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    overall_score REAL,
    started_at DATETIME,
    completed_at DATETIME,
    duration INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_name) REFERENCES servers(name) ON DELETE CASCADE
);

-- Compliance results table
CREATE TABLE compliance_results (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(6)))),
    check_id TEXT NOT NULL,
    category TEXT NOT NULL,
    score REAL NOT NULL,
    total_checks INTEGER NOT NULL,
    passed_checks INTEGER NOT NULL,
    failed_checks INTEGER NOT NULL,
    details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (check_id) REFERENCES compliance_checks(id) ON DELETE CASCADE
);

-- Compliance issues table
CREATE TABLE compliance_issues (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(6)))),
    check_id TEXT NOT NULL,
    issue_id TEXT NOT NULL,
    severity TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    recommendation TEXT,
    affected_components TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME,
    FOREIGN KEY (check_id) REFERENCES compliance_checks(id) ON DELETE CASCADE
);
```

### 2. Memory Service Schema
```sql
-- Memories table
CREATE TABLE memories (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(6)))),
    memory_id TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT NOT NULL,
    vector_embedding BLOB,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    is_consolidated INTEGER DEFAULT 0,
    consolidation_id TEXT,
    FOREIGN KEY (consolidation_id) REFERENCES consolidations(id) ON DELETE SET NULL
);

-- Consolidations table
CREATE TABLE consolidations (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(6)))),
    consolidation_id TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    criteria TEXT NOT NULL,
    options TEXT NOT NULL,
    started_at DATETIME,
    completed_at DATETIME,
    duration INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Memory tags table
CREATE TABLE memory_tags (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(6)))),
    memory_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

-- Search history table
CREATE TABLE search_history (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(6)))),
    query TEXT NOT NULL,
    filters TEXT,
    results_count INTEGER NOT NULL,
    execution_time INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## Redis Schema

### 1. Session Management
```redis
# User sessions
SET user:session:{session_id} "{user_data}" EX 86400
HSET user:session:{session_id} user_id "{user_id}" username "{username}" role "{role}" last_access "{timestamp}"

# Rate limiting
INCR rate_limit:user:{user_id}:{window}
EXPIRE rate_limit:user:{user_id}:{window} 3600

# Cache
SET cache:compliance:status "{status_data}" EX 300
SET cache:server:health "{health_data}" EX 60
```

### 2. Queue Management
```redis
# Task queue
LPUSH compliance:queue "{task_data}"
RPUSH memory:consolidation:queue "{consolidation_data}"

# Processing status
SET task:status:{task_id} "processing" EX 3600
SET task:result:{task_id} "{result_data}" EX 86400
```

### 3. Real-time Updates
```redis
# WebSocket connections
HSET websocket:connections:{user_id} connection_id "{connection_id}" last_ping "{timestamp}"

# Real-time data
PUBSUB compliance:updates "{update_data}"
PUBSUB server:status "{status_data}"
```

---

## Configuration File Specifications

### 1. MCP Configuration File (mcp.json)

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "env": {
        "NODE_ENV": "production",
        "KILOCODE_ENV": "production",
        "KILOCODE_PROJECT_PATH": "/workspace",
        "KILOCODE_PROJECT_NAME": "my-project",
        "FILESYSTEM_ROOT": "/data",
        "FILESYSTEM_ALLOWED_PATHS": ["/data", "/tmp"],
        "FILESYSTEM_MAX_FILE_SIZE": "100MB",
        "FILESYSTEM_TIMEOUT": "30000"
      },
      "description": "Filesystem access for project files",
      "docsPath": "docs/mcp/filesystem/configuration.md"
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "NODE_ENV": "production",
        "KILOCODE_ENV": "production",
        "KILOCODE_PROJECT_PATH": "/workspace",
        "KILOCODE_PROJECT_NAME": "my-project",
        "POSTGRES_CONNECTION_STRING": "postgresql://user:password@localhost:5432/kilocode",
        "POSTGRES_MAX_CONNECTIONS": "20",
        "POSTGRES_POOL_MIN": "2",
        "POSTGRES_POOL_MAX": "10"
      },
      "description": "PostgreSQL database connection",
      "docsPath": "docs/mcp/postgres/configuration.md"
    },
    "compliance": {
      "command": "node",
      "args": ["dist/server.js"],
      "env": {
        "NODE_ENV": "production",
        "KILOCODE_ENV": "production",
        "KILOCODE_PROJECT_PATH": "/workspace",
        "KILOCODE_PROJECT_NAME": "my-project",
        "PORT": "3000",
        "DATABASE_URL": "postgresql://user:password@localhost:5432/kilocode_compliance",
        "REDIS_URL": "redis://localhost:6379",
        "JWT_SECRET": "your-secret-key-here",
        "LOG_LEVEL": "info"
      },
      "description": "Compliance validation server",
      "docsPath": "docs/mcp/compliance/configuration.md"
    },
    "memory": {
      "command": "node",
      "args": ["dist/server.js"],
      "env": {
        "NODE_ENV": "production",
        "KILOCODE_ENV": "production",
        "KILOCODE_PROJECT_PATH": "/workspace",
        "KILOCODE_PROJECT_NAME": "my-project",
        "PORT": "8080",
        "DATABASE_URL": "postgresql://user:password@localhost:5432/kilocode_memory",
        "REDIS_URL": "redis://localhost:6379",
        "CHROMA_DB_PATH": "/var/lib/mcp-memory/chroma_db",
        "VECTOR_DIMENSION": "1536",
        "MEMORY_RETENTION_DAYS": "30"
      },
      "description": "Memory service for vector storage",
      "docsPath": "docs/mcp/memory/configuration.md"
    }
  }
}
```

### 2. Environment Configuration (.env)

```bash
# Application Configuration
NODE_ENV=production
KILOCODE_ENV=production
KILOCODE_PROJECT_PATH=/workspace
KILOCODE_PROJECT_NAME=my-project

# Server Configuration
PORT=3000
HOST=0.0.0.0
WORKERS=4

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/kilocode
DATABASE_POOL_MIN=2
DATABASE_POOL_MAX=10
DATABASE_POOL_ACQUIRE=30000
DATABASE_POOL_IDLE=10000

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your-redis-password
REDIS_DB=0

# Security Configuration
JWT_SECRET=your-secret-key-here
JWT_EXPIRES=24h
JWT_REFRESH=7d
BCRYPT_ROUNDS=12

# Logging Configuration
LOG_LEVEL=info
LOG_FORMAT=json
LOG_FILE=/var/log/mcp-compliance/app.log
LOG_ROTATION=daily
LOG_MAX_SIZE=10MB
LOG_MAX_FILES=5

# Performance Configuration
PERFORMANCE_ENABLED=true
PERFORMANCE_METRICS=true
PERFORMANCE_LOGGING=true
REQUEST_TIMEOUT=30000
REQUEST_MAX_SIZE=10485760

# Caching Configuration
CACHE_ENABLED=true
CACHE_TTL=3600
CACHE_MAX_SIZE=1000
CACHE_REDIS_URL=redis://localhost:6379
CACHE_REDIS_PREFIX=mcp:

# SSL/TLS Configuration
SSL_ENABLED=true
SSL_CERT_PATH=/etc/ssl/certs/mcp-compliance.crt
SSL_KEY_PATH=/etc/ssl/private/mcp-compliance.key
SSL_MIN_VERSION=tls1.2

# Monitoring Configuration
MONITORING_ENABLED=true
MONITORING_INTERVAL=30
MONITORING_RETENTION_DAYS=30

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_INTERVAL=daily
BACKUP_RETENTION_DAYS=30
BACKUP_PATH=/var/backups/mcp-compliance

# Email Configuration
EMAIL_ENABLED=false
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-email-password
EMAIL_FROM=noreply@kilocode.com

# Notification Configuration
NOTIFICATION_ENABLED=true
NOTIFICATION_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
NOTIFICATION_EMAIL=admin@example.com

# Compliance Configuration
COMPLIANCE_ENABLED=true
COMPLIANCE_INTERVAL=daily
COMPLIANCE_RETENTION_DAYS=90

# Memory Configuration
MEMORY_ENABLED=true
MEMORY_RETENTION_DAYS=30
MEMORY_CONSOLIDATION_INTERVAL=weekly
MEMORY_VECTOR_DIMENSION=1536
MEMORY_SIMILARITY_THRESHOLD=0.8
```

### 3. Docker Configuration (docker-compose.yml)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: kilocode
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - kilocode-network

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass your-redis-password
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - kilocode-network

  compliance-server:
    build: ./mcp_servers/mcp-compliance-server
    environment:
      NODE_ENV: production
      KILOCODE_ENV: production
      KILOCODE_PROJECT_PATH: /workspace
      KILOCODE_PROJECT_NAME: my-project
      PORT: 3000
      DATABASE_URL: postgresql://user:password@postgres:5432/kilocode_compliance
      REDIS_URL: redis://:your-redis-password@redis:6379
      JWT_SECRET: your-secret-key-here
      LOG_LEVEL: info
    ports:
      - "3000:3000"
    volumes:
      - ./mcp_servers/mcp-compliance-server:/app
      - /var/log/mcp-compliance:/var/log/mcp-compliance
    depends_on:
      - postgres
      - redis
    networks:
      - kilocode-network

  memory-service:
    build: ./mcp_servers/mcp-memory-service
    environment:
      NODE_ENV: production
      KILOCODE_ENV: production
      KILOCODE_PROJECT_PATH: /workspace
      KILOCODE_PROJECT_NAME: my-project
      PORT: 8080
      DATABASE_URL: postgresql://user:password@postgres:5432/kilocode_memory
      REDIS_URL: redis://:your-redis-password@redis:6379
      CHROMA_DB_PATH: /var/lib/mcp-memory/chroma_db
      VECTOR_DIMENSION: 1536
      MEMORY_RETENTION_DAYS: 30
    ports:
      - "8080:8080"
    volumes:
      - ./mcp_servers/mcp-memory-service:/app
      - chroma_db_data:/var/lib/mcp-memory/chroma_db
    depends_on:
      - postgres
      - redis
    networks:
      - kilocode-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - compliance-server
      - memory-service
    networks:
      - kilocode-network

volumes:
  postgres_data:
  redis_data:
  chroma_db_data:

networks:
  kilocode-network:
    driver: bridge
```

### 4. Kubernetes Configuration (kubernetes.yaml)

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: kilocode

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: kilocode
data:
  NODE_ENV: "production"
  KILOCODE_ENV: "production"
  LOG_LEVEL: "info"
  PORT: "3000"
  DATABASE_URL: "postgresql://user:password@postgres-service:5432/kilocode"
  REDIS_URL: "redis://redis-service:6379"
  JWT_SECRET: "your-secret-key-here"

---
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: kilocode
type: Opaque
data:
  database-password: cGFzc3dvcmQ=
  redis-password: eW91ci1yZWRpcy1wYXNzd29yZA==
  jwt-secret: eW91ci1zZWNyZXQta2V5LWhlcmU=

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: compliance-server
  namespace: kilocode
spec:
  replicas: 3
  selector:
    matchLabels:
      app: compliance-server
  template:
    metadata:
      labels:
        app: compliance-server
    spec:
      containers:
      - name: compliance-server
        image: kilocode/mcp-compliance-server:latest
        ports:
        - containerPort: 3000
        envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: compliance-service
  namespace: kilocode
spec:
  selector:
    app: compliance-server
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: compliance-ingress
  namespace: kilocode
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - compliance.kilocode.com
    secretName: compliance-tls
  rules:
  - host: compliance.kilocode.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: compliance-service
            port:
              number: 80
```

---

## Data Models

### 1. Compliance Server Data Models

#### 1.1 User Model
```typescript
interface User {
  id: string;
  username: string;
  email: string;
  passwordHash: string;
  role: 'admin' | 'user' | 'viewer' | 'guest';
  permissions: string[];
  isActive: boolean;
  lastLogin?: Date;
  createdAt: Date;
  updatedAt: Date;
}
```

#### 1.2 Server Model
```typescript
interface Server {
  id: string;
  name: string;
  type: string;
  status: 'running' | 'stopped' | 'error' | 'starting' | 'stopping';
  health: 'healthy' | 'warning' | 'critical' | 'unknown';
  version: string;
  description?: string;
  configuration: Record<string, any>;
  lastCheck?: Date;
  createdAt: Date;
  updatedAt: Date;
}
```

#### 1.3 Compliance Check Model
```typescript
interface ComplianceCheck {
  id: string;
  checkId: string;
  serverName: string;
  checkType: 'full' | 'security' | 'performance' | 'configuration';
  status: 'pending' | 'running' | 'completed' | 'failed';
  overallScore?: number;
  startedAt?: Date;
  completedAt?: Date;
  duration?: number;
  createdAt: Date;
  updatedAt: Date;
}
```

#### 1.4 Compliance Issue Model
```typescript
interface ComplianceIssue {
  id: string;
  checkId: string;
  issueId: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  category: 'security' | 'performance' | 'configuration' | 'operational';
  title: string;
  description: string;
  recommendation?: string;
  affectedComponents: string[];
  status: 'open' | 'in-progress' | 'resolved' | 'closed';
  createdAt: Date;
  updatedAt: Date;
  resolvedAt?: Date;
}
```

### 2. Memory Service Data Models

#### 2.1 Memory Model
```typescript
interface Memory {
  id: string;
  memoryId: string;
  content: string;
  metadata: MemoryMetadata;
  vectorEmbedding?: number[];
  createdAt: Date;
  updatedAt: Date;
  expiresAt?: Date;
  isConsolidated: boolean;
  consolidationId?: string;
}

interface MemoryMetadata {
  type: 'text' | 'image' | 'document' | 'code' | 'other';
  source: 'user-input' | 'system' | 'api' | 'integration';
  tags: string[];
  timestamp: Date;
  [key: string]: any;
}
```

#### 2.2 Consolidation Model
```typescript
interface Consolidation {
  id: string;
  consolidationId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  criteria: ConsolidationCriteria;
  options: ConsolidationOptions;
  startedAt?: Date;
  completedAt?: Date;
  duration?: number;
  createdAt: Date;
  updatedAt: Date;
}

interface ConsolidationCriteria {
  timeRange: {
    start: Date;
    end: Date;
  };
  tags: string[];
  similarityThreshold: number;
}

interface ConsolidationOptions {
  mergeStrategy: 'weighted' | 'average' | 'latest' | 'oldest';
  retention: 'keep_original' | 'keep_consolidated' | 'keep_both';
}
```

### 3. Integration Coordinator Data Models

#### 3.1 Integration Session Model
```typescript
interface IntegrationSession {
  id: string;
  sessionId: string;
  initiator: string;
  target: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  requestData: Record<string, any>;
  responseData?: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
  completedAt?: Date;
}
```

#### 3.2 Approval Request Model
```typescript
interface ApprovalRequest {
  id: string;
  approvalId: string;
  type: 'assessment' | 'remediation' | 'configuration' | 'deployment';
  requestData: Record<string, any>;
  requestedBy: string;
  status: 'pending' | 'approved' | 'rejected' | 'expired';
  approvedBy?: string;
  decision?: string;
  expiresAt: Date;
  createdAt: Date;
  updatedAt: Date;
  approvedAt?: Date;
  rejectedAt?: Date;
}
```

---

## Database Migration Scripts

### 1. Initial Migration
```sql
-- Create initial schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables
CREATE TABLE users (...);
CREATE TABLE servers (...);
CREATE TABLE compliance_checks (...);
CREATE TABLE compliance_results (...);
CREATE TABLE compliance_issues (...);
CREATE TABLE audit_logs (...);

-- Create indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_servers_name ON servers(name);
-- ... other indexes

-- Create initial data
INSERT INTO users (username, email, password_hash, role, permissions) VALUES
('admin', 'admin@example.com', '$2b$12$hashedpassword', 'admin', ARRAY['read', 'write', 'admin']),
('user', 'user@example.com', '$2b$12$hashedpassword', 'user', ARRAY['read', 'write']);

INSERT INTO servers (name, type, status, health, version, description) VALUES
('filesystem', 'filesystem', 'running', 'healthy', '1.0.0', 'Filesystem access server'),
('postgres', 'database', 'running', 'healthy', '2.0.0', 'PostgreSQL database server');
```

### 2. Migration Script Example
```sql
-- Migration: Add vector embedding support
ALTER TABLE memories ADD COLUMN IF NOT EXISTS vector_embedding VECTOR(1536);

-- Migration: Add consolidation support
CREATE TABLE IF NOT EXISTS consolidations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consolidation_id VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    criteria JSONB NOT NULL,
    options JSONB NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Migration: Add search history
CREATE TABLE IF NOT EXISTS search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    filters JSONB,
    results_count INTEGER NOT NULL,
    execution_time INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Migration: Add performance metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10,2) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for new tables
CREATE INDEX IF NOT EXISTS idx_consolidations_status ON consolidations(status);
CREATE INDEX IF NOT EXISTS idx_search_history_created_at ON search_history(created_at);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_server_name ON performance_metrics(server_name);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);
```

---

## Support and Contact Information

### Technical Support
- **Email**: support@kilocode.com
- **Phone**: +1 (555) 123-4567
- **Hours**: 24/7 for production support

### Database Support
- **Database Documentation**: [KiloCode Database Documentation](https://kilocode.com/docs/database)
- **Schema Designer**: [KiloCode Schema Designer](https://kilocode.com/tools/schema-designer)
- **Community Forum**: [KiloCode Community](https://community.kilocode.com)

### Documentation Resources
- **PostgreSQL Guide**: [KiloCode PostgreSQL Guide](https://kilocode.com/docs/postgresql)
- **Redis Guide**: [KiloCode Redis Guide](https://kilocode.com/docs/redis)
- **Configuration Guide**: [KiloCode Configuration Guide](https://kilocode.com/docs/configuration)

---

*These database schema and configuration file specifications are part of the KiloCode MCP Setup and Configuration Architecture Plan and should be reviewed and updated regularly to reflect changes in database design and best practices.*