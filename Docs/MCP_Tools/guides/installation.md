# Installation Guide for MCP Servers

## Overview

This guide provides comprehensive installation instructions for MCP (Model Context Protocol) servers within the KiloCode ecosystem. The installation process follows the **Simple, Robust, Secure** approach and ensures proper setup and configuration of all components.

## Prerequisites

### System Requirements
- **Operating System**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: Minimum 20GB free space (50GB recommended)
- **CPU**: Minimum 2 cores (4 cores recommended)
- **Network**: Internet connection for package downloads

### Software Requirements
- **Node.js**: 18.x LTS (minimum), 20.x LTS (recommended)
- **Python**: 3.8+ (minimum), 3.11+ (recommended)
- **PostgreSQL**: 12+ (minimum), 14+ (recommended)
- **Git**: 2.x+ (minimum), 2.30+ (recommended)
- **Docker**: 20.10+ (optional, for containerized deployment)

### Network Requirements
- **Ports**: 3000-3005 (for MCP servers), 5432 (PostgreSQL)
- **Firewall**: Allow traffic on required ports
- **DNS**: Proper DNS resolution for server names

## Installation Methods

### Method 1: Manual Installation
Recommended for development and testing environments.

### Method 2: Automated Installation
Recommended for production environments using the KiloCode MCP Installer.

### Method 3: Docker Installation
Recommended for containerized deployments.

## Method 1: Manual Installation

### Step 1: System Preparation

#### 1.1 Update System
```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl wget gnupg software-properties-common apt-transport-https

# Add Node.js repository
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -

# Add PostgreSQL repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'

# Import PostgreSQL signing key
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# Update package lists again
sudo apt update
```

#### 1.2 Install Base Software
```bash
# Install Node.js and npm
sudo apt install -y nodejs npm

# Install Python and pip
sudo apt install -y python3 python3-pip python3-venv

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install Git
sudo apt install -y git

# Install Docker (optional)
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER
```

#### 1.3 Create Directories
```bash
# Create main installation directory
sudo mkdir -p /opt/kilocode/mcp-servers
sudo chown -R $USER:$USER /opt/kilocode/mcp-servers

# Create configuration directory
sudo mkdir -p /etc/kilocode/mcp
sudo chown -R $USER:$USER /etc/kilocode/mcp

# Create log directory
sudo mkdir -p /var/log/kilocode/mcp
sudo chown -R $USER:$USER /var/log/kilocode/mcp

# Create backup directory
sudo mkdir -p /opt/kilocode/mcp-servers/backups
sudo chown -R $USER:$USER /opt/kilocode/mcp-servers/backups
```

### Step 2: Install MCP Servers

#### 2.1 Install MCP Compliance Server
```bash
# Navigate to installation directory
cd /opt/kilocode/mcp-servers

# Clone compliance server repository
git clone https://github.com/kilocode/mcp-compliance-server.git

# Navigate to compliance server
cd mcp-compliance-server

# Install dependencies
npm install

# Build the application
npm run build

# Create configuration
cat << 'EOF' > config.json
{
  "server": {
    "port": 3003,
    "host": "localhost",
    "logLevel": "info"
  },
  "database": {
    "url": "postgresql://mcp_user:mcp_password@localhost:5432/mcp_db",
    "pool": {
      "min": 2,
      "max": 10
    }
  },
  "compliance": {
    "rulesPath": "./rules",
    "reportsPath": "./reports",
    "autoFix": false,
    "requireApproval": true
  }
}
EOF

# Create systemd service
cat << 'EOF' | sudo tee /etc/systemd/system/mcp-compliance.service
[Unit]
Description=MCP Compliance Server
After=network.target postgresql.service

[Service]
Type=simple
User=mcp-service
WorkingDirectory=/opt/kilocode/mcp-servers/mcp-compliance-server
ExecStart=/usr/bin/node src/index.js
Restart=always
RestartSec=10
Environment=NODE_ENV=production
Environment=KILOCODE_ENV=production
Environment=CONFIG_PATH=/etc/kilocode/mcp/compliance.json

[Install]
WantedBy=multi-user.target
EOF

# Create user for service
sudo useradd -m -s /bin/bash mcp-service
sudo usermod -aG $USER mcp-service
```

#### 2.2 Install MCP Memory Service
```bash
# Navigate back to main directory
cd /opt/kilocode/mcp-servers

# Clone memory service repository
git clone https://github.com/kilocode/mcp-memory-service.git

# Navigate to memory service
cd mcp-memory-service

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install the memory service
python install.py

# Create configuration
cat << 'EOF' > config.json
{
  "server": {
    "port": 3002,
    "host": "localhost",
    "logLevel": "info"
  },
  "database": {
    "vector_db_path": "/opt/kilocode/mcp-servers/memory_db",
    "backups_path": "/opt/kilocode/mcp-servers/memory_backups",
    "max_size": 100000,
    "cleanup_interval": 3600
  },
  "memory": {
    "max_items": 10000,
    "max_size_per_item": 1024000,
    "default_tags": ["default"],
    "auto_consolidate": true
  }
}
EOF

# Create systemd service
cat << 'EOF' | sudo tee /etc/systemd/system/mcp-memory.service
[Unit]
Description=MCP Memory Service
After=network.target

[Service]
Type=simple
User=mcp-service
WorkingDirectory=/opt/kilocode/mcp-servers/mcp-memory-service
ExecStart=/opt/kilocode/mcp-servers/mcp-memory-service/venv/bin/python memory_wrapper.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/kilocode/mcp-servers/mcp-memory-service
Environment=CONFIG_PATH=/etc/kilocode/mcp/memory.json

[Install]
WantedBy=multi-user.target
EOF
```

#### 2.3 Install MCP Filesystem Server
```bash
# Navigate back to main directory
cd /opt/kilocode/mcp-servers

# Install filesystem server using npm
npm install -g @modelcontextprotocol/server-filesystem

# Create configuration
cat << 'EOF' > /etc/kilocode/mcp/filesystem.json
{
  "server": {
    "port": 3000,
    "host": "localhost",
    "logLevel": "info"
  },
  "filesystem": {
    "root": "/opt/kilocode/mcp-servers",
    "allowed_paths": ["/opt/kilocode/mcp-servers", "/tmp"],
    "max_file_size": 10485760,
    "timeout": 30000
  }
}
EOF

# Create systemd service
cat << 'EOF' | sudo tee /etc/systemd/system/mcp-filesystem.service
[Unit]
Description=MCP Filesystem Server
After=network.target

[Service]
Type=simple
User=mcp-service
ExecStart=/usr/bin/npx -y @modelcontextprotocol/server-filesystem /opt/kilocode/mcp-servers /tmp
Restart=always
RestartSec=10
Environment=NODE_ENV=production
Environment=KILOCODE_ENV=production
Environment=CONFIG_PATH=/etc/kilocode/mcp/filesystem.json

[Install]
WantedBy=multi-user.target
EOF
```

#### 2.4 Install MCP PostgreSQL Server
```bash
# Install PostgreSQL MCP server
npm install -g @modelcontextprotocol/server-postgres

# Create PostgreSQL configuration
cat << 'EOF' > /etc/kilocode/mcp/postgres.json
{
  "server": {
    "port": 3001,
    "host": "localhost",
    "logLevel": "info"
  },
  "database": {
    "connection_string": "postgresql://mcp_user:mcp_password@localhost:5432/mcp_db",
    "pool": {
      "min": 2,
      "max": 20
    },
    "query_timeout": 30000,
    "idle_timeout": 60000
  }
}
EOF

# Create systemd service
cat << 'EOF' | sudo tee /etc/systemd/system/mcp-postgres.service
[Unit]
Description=MCP PostgreSQL Server
After=network.target postgresql.service

[Service]
Type=simple
User=mcp-service
ExecStart=/usr/bin/npx -y @modelcontextprotocol/server-postgres
Restart=always
RestartSec=10
Environment=NODE_ENV=production
Environment=KILOCODE_ENV=production
Environment=CONFIG_PATH=/etc/kilocode/mcp/postgres.json

[Install]
WantedBy=multi-user.target
EOF
```

### Step 3: Configure Database

#### 3.1 Configure PostgreSQL
```bash
# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres createdb mcp_db
sudo -u postgres createuser mcp_user
sudo -u postgres psql -c "ALTER USER mcp_user PASSWORD 'mcp_password';"

# Grant permissions
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE mcp_db TO mcp_user;"

# Create schema
sudo -u postgres psql -d mcp_db -f /opt/kilocode/mcp-servers/mcp-compliance-server/database/schema.sql
```

#### 3.2 Configure Database Connection
```bash
# Update PostgreSQL configuration for MCP servers
cat << 'EOF' | sudo tee -a /etc/postgresql/14/main/postgresql.conf
# MCP Server Configuration
listen_addresses = '*'
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
EOF

# Update pg_hba.conf for MCP servers
cat << 'EOF' | sudo tee -a /etc/postgresql/14/main/pg_hba.conf
# MCP Server Access
host    mcp_db        mcp_user        127.0.0.1/32            md5
host    mcp_db        mcp_user        ::1/128                 md5
EOF

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Step 4: Configure Services

#### 4.1 Create Main Configuration
```bash
# Create main MCP configuration
cat << 'EOF' > /etc/kilocode/mcp/mcp.json
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
  }
}
EOF
```

#### 4.2 Create Environment Configuration
```bash
# Create environment file
cat << 'EOF' > /etc/kilocode/mcp/.env
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
EOF
```

### Step 5: Start Services

#### 5.1 Enable and Start Services
```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable mcp-filesystem
sudo systemctl enable mcp-postgres
sudo systemctl enable mcp-memory
sudo systemctl enable mcp-compliance

# Start services
sudo systemctl start mcp-filesystem
sudo systemctl start mcp-postgres
sudo systemctl start mcp-memory
sudo systemctl start mcp-compliance

# Check service status
sudo systemctl status mcp-filesystem
sudo systemctl status mcp-postgres
sudo systemctl status mcp-memory
sudo systemctl status mcp-compliance
```

#### 5.2 Verify Services
```bash
# Test filesystem server
curl -s http://localhost:3000/api/v1/files | jq .

# Test PostgreSQL server
curl -s http://localhost:3001/api/v1/tables | jq .

# Test memory server
curl -s http://localhost:3002/api/v1/memory/stats | jq .

# Test compliance server
curl -s http://localhost:3003/api/v1/compliance/check \
  -H "Content-Type: application/json" \
  -d '{"targets": ["filesystem"], "rules": ["security"]}' | jq .
```

## Method 2: Automated Installation

### Step 1: Install KiloCode MCP Installer
```bash
# Navigate to installation directory
cd /opt/kilocode/mcp-servers

# Clone MCP installer repository
git clone https://github.com/kilocode/kilocode-mcp-installer.git

# Navigate to installer
cd kilocode-mcp-installer

# Install dependencies
npm install

# Build the installer
npm run build

# Make installer executable
chmod +x dist/index.js
```

### Step 2: Run Automated Installation
```bash
# Run automated installation
sudo node dist/index.js install --mode production

# Or with custom configuration
sudo node dist/index.js install \
  --mode production \
  --config /path/to/custom-config.json \
  --skip-backup
```

### Step 3: Verify Installation
```bash
# Check installation status
sudo node dist/index.js status

# Run validation tests
sudo node dist/index.js validate

# Generate installation report
sudo node dist/index.js report --output /tmp/installation-report.json
```

## Method 3: Docker Installation

### Step 1: Install Docker
```bash
# Install Docker
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER

# Log out and log back in to apply group changes
```

### Step 2: Create Docker Compose File
```bash
# Create docker-compose.yml
cat << 'EOF' > docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: mcp_db
      POSTGRES_USER: mcp_user
      POSTGRES_PASSWORD: mcp_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql
    ports:
      - "5432:5432"
    restart: unless-stopped

  filesystem:
    image: kilocode/mcp-filesystem:latest
    environment:
      NODE_ENV: production
      KILOCODE_ENV: production
      KILOCODE_PROJECT_PATH: /opt/kilocode/mcp-servers
    volumes:
      - ./servers:/opt/kilocode/mcp-servers
    ports:
      - "3000:3000"
    restart: unless-stopped

  postgres-server:
    image: kilocode/mcp-postgres:latest
    environment:
      NODE_ENV: production
      KILOCODE_ENV: production
      DATABASE_URL: postgresql://mcp_user:mcp_password@postgres:5432/mcp_db
    depends_on:
      - postgres
    ports:
      - "3001:3001"
    restart: unless-stopped

  memory:
    image: kilocode/mcp-memory:latest
    environment:
      MCP_MEMORY_VECTOR_DB_PATH: /opt/kilocode/mcp-servers/memory_db
      MCP_MEMORY_BACKUPS_PATH: /opt/kilocode/mcp-servers/memory_backups
      MCP_MEMORY_LOG_LEVEL: INFO
    volumes:
      - memory_data:/opt/kilocode/mcp-servers/memory_db
      - memory_backups:/opt/kilocode/mcp-servers/memory_backups
    ports:
      - "3002:3002"
    restart: unless-stopped

  compliance:
    image: kilocode/mcp-compliance:latest
    environment:
      COMPLIANCE_LOG_LEVEL: INFO
      COMPLIANCE_REPORT_PATH: /opt/kilocode/mcp-servers/reports
    volumes:
      - ./reports:/opt/kilocode/mcp-servers/reports
      - ./rules:/opt/kilocode/mcp-servers/rules
    ports:
      - "3003:3003"
    depends_on:
      - postgres
    restart: unless-stopped

volumes:
  postgres_data:
  memory_data:
  memory_backups:
EOF
```

### Step 3: Start Docker Services
```bash
# Pull images
docker-compose pull

# Start services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

## Post-Installation Configuration

### Step 6: Configure Firewall
```bash
# Install UFW if not installed
sudo apt install -y ufw

# Allow SSH
sudo ufw allow ssh

# Allow MCP server ports
sudo ufw allow 3000:3005/tcp

# Allow PostgreSQL
sudo ufw allow 5432/tcp

# Enable firewall
sudo ufw enable

# Check firewall status
sudo ufw status
```

### Step 7: Configure SSL/TLS
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

### Step 8: Configure Monitoring
```bash
# Install monitoring tools
sudo apt install -y prometheus grafana node-exporter

# Create Prometheus configuration
cat << 'EOF' | sudo tee /etc/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'mcp-servers'
    static_configs:
      - targets: ['localhost:3000', 'localhost:3001', 'localhost:3002', 'localhost:3003']
EOF

# Start Prometheus
sudo systemctl start prometheus
sudo systemctl enable prometheus

# Start Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

## Verification and Testing

### Step 9: Verify Installation
```bash
# Check all services are running
sudo systemctl is-active mcp-filesystem
sudo systemctl is-active mcp-postgres
sudo systemctl is-active mcp-memory
sudo systemctl is-active mcp-compliance

# Test all MCP servers
curl -s http://localhost:3000/api/v1/files | jq .
curl -s http://localhost:3001/api/v1/tables | jq .
curl -s http://localhost:3002/api/v1/memory/stats | jq .
curl -s http://localhost:3003/api/v1/compliance/check \
  -H "Content-Type: application/json" \
  -d '{"targets": ["filesystem"], "rules": ["security"]}' | jq .

# Test database connectivity
psql -U mcp_user -d mcp_db -c "SELECT version();"
```

### Step 10: Run Tests
```bash
# Run compliance tests
sudo /opt/kilocode/mcp-servers/mcp-compliance-server/scripts/test-executor.js

# Run integration tests
sudo /opt/kilocode/mcp-servers/scripts/integration-test.sh

# Run performance tests
sudo /opt/kilocode/mcp-servers/scripts/performance-test.sh
```

## Troubleshooting Installation Issues

### Common Installation Issues

#### Issue 1: Service Fails to Start
**Solution**: Check logs and dependencies
```bash
# Check service logs
sudo journalctl -u mcp-filesystem -f
sudo journalctl -u mcp-postgres -f
sudo journalctl -u mcp-memory -f
sudo journalctl -u mcp-compliance -f

# Check dependencies
which node
which npm
which python3
which psql
```

#### Issue 2: Database Connection Issues
**Solution**: Check database configuration and connectivity
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
psql -U mcp_user -d mcp_db -c "SELECT 1;"

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

#### Issue 3: Port Already in Use
**Solution**: Find and resolve port conflicts
```bash
# Check port usage
sudo netstat -tulpn | grep :3000

# Find process using port
sudo lsof -i :3000

# Kill conflicting process
sudo kill -9 <PID>
```

## Support and Contact Information

### Technical Support
- **Email**: support@kilocode.com
- **Phone**: +1 (555) 123-4567
- **Hours**: 24/7 for production support

### Documentation
- **Main Documentation**: [KiloCode Documentation](https://docs.kilocode.com/mcp)
- **GitHub Issues**: [KiloCode GitHub](https://github.com/kilocode/kilocode/issues)
- **Community Forum**: [KiloCode Community](https://community.kilocode.com)

### Installation Support
- **Installation Support**: install@kilocode.com
- **System Requirements**: requirements@kilocode.com
- **Docker Support**: docker@kilocode.com

---

*This installation guide is part of the KiloCode MCP Setup and Configuration Architecture Plan and should be reviewed and updated regularly to reflect changes in installation procedures and best practices.*