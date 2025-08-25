# MCP Server Installation Guides

## Overview

This document provides comprehensive installation guides for MCP (Model Context Protocol) servers within the KiloCode ecosystem. The guides cover installation procedures for different MCP servers, including the MCP Compliance Server and MCP Memory Service, following the **Simple, Robust, Secure** approach.

## Installation Philosophy

### Key Principles
1. **Simplicity**: Provide clear, step-by-step installation procedures
2. **Robustness**: Ensure reliable installation with proper validation
3. **Security**: Emphasize secure installation practices
4. **Consistency**: Maintain consistent installation procedures across servers
5. **Flexibility**: Support different installation environments and scenarios

### Installation Types
- **Development Installation**: For development and testing environments
- **Production Installation**: For production deployment
- **Container Installation**: Using Docker containers
- **Package Installation**: Using package managers
- **Source Installation**: From source code

---

## MCP Compliance Server Installation Guide

### Overview

The MCP Compliance Server is responsible for validating MCP servers against KiloCode standards and requirements. This guide covers installation procedures for different environments.

### Prerequisites

#### System Requirements
```bash
# Minimum Requirements
- Operating System: Ubuntu 20.04+ / CentOS 8+ / Windows 10+
- CPU: 2 cores
- RAM: 4 GB
- Disk Space: 2 GB
- Network: Internet connection

# Recommended Requirements
- Operating System: Ubuntu 22.04+ / CentOS 9+ / Windows 11+
- CPU: 4 cores
- RAM: 8 GB
- Disk Space: 10 GB
- Network: High-speed internet connection
```

#### Software Requirements
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y nodejs npm git

# CentOS/RHEL
sudo yum install -y nodejs npm git

# Windows
# Download and install Node.js from https://nodejs.org
# Install Git from https://git-scm.com
```

### Installation Methods

#### 1. Development Installation

##### 1.1 Clone Repository
```bash
# Clone the repository
git clone https://github.com/kilocode/mcp-compliance-server.git
cd mcp-compliance-server

# Switch to development branch
git checkout develop
```

##### 1.2 Install Dependencies
```bash
# Install Node.js dependencies
npm install

# Install development dependencies
npm install --dev

# Install global dependencies
npm install -g nodemon typescript ts-node
```

##### 1.3 Environment Configuration
```bash
# Create environment file
cp .env.example .env

# Edit environment file
nano .env
```

```bash
# .env file content
NODE_ENV=development
KILOCODE_ENV=development
KILOCODE_PROJECT_PATH=/workspace
PORT=3000
LOG_LEVEL=debug
DATABASE_URL=sqlite:./data/compliance.db
REDIS_URL=redis://localhost:6379
```

##### 1.4 Database Setup
```bash
# Create data directory
mkdir -p data

# Initialize database
npm run db:init

# Run database migrations
npm run db:migrate
```

##### 1.5 Start Development Server
```bash
# Start development server
npm run dev

# Or use nodemon for auto-reload
npx nodemon src/index.ts
```

##### 1.6 Verify Installation
```bash
# Check server status
curl http://localhost:3000/health

# View server logs
npm run logs

# Run tests
npm test
```

#### 2. Production Installation

##### 2.1 System Preparation
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y nodejs npm git nginx supervisor

# Create application user
sudo useradd -m -s /bin/bash mcp-compliance
sudo usermod -aG sudo mcp-compliance
```

##### 2.2 Application Setup
```bash
# Switch to application user
sudo su - mcp-compliance

# Clone repository
git clone https://github.com/kilocode/mcp-compliance-server.git
cd mcp-compliance-server

# Switch to production branch
git checkout main
```

##### 2.3 Install Dependencies
```bash
# Install Node.js dependencies
npm install --production

# Install PM2 for process management
npm install -g pm2
```

##### 2.4 Environment Configuration
```bash
# Create environment file
cp .env.example .env

# Edit environment file
nano .env
```

```bash
# Production .env file content
NODE_ENV=production
KILOCODE_ENV=production
KILOCODE_PROJECT_PATH=/var/www/mcp-compliance
PORT=3000
LOG_LEVEL=info
DATABASE_URL=postgresql://user:pass@localhost:5432/mcp_compliance
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
```

##### 2.5 Database Setup
```bash
# Create data directory
mkdir -p /var/www/mcp-compliance/data

# Initialize database
npm run db:init

# Run database migrations
npm run db:migrate

# Create database backup
npm run db:backup
```

##### 2.6 Process Management
```bash
# Create PM2 configuration
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'mcp-compliance',
    script: 'dist/index.js',
    instances: 'max',
    exec_mode: 'cluster',
    env: {
      NODE_ENV: 'production',
      PORT: 3000,
    },
    error_file: '/var/log/mcp-compliance/error.log',
    out_file: '/var/log/mcp-compliance/out.log',
    log_file: '/var/log/mcp-compliance/combined.log',
    time: true,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    node_args: '--max-old-space-size=1024',
  }]
};
EOF

# Start application with PM2
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
```

##### 2.7 Nginx Configuration
```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/mcp-compliance
```

```nginx
server {
    listen 80;
    server_name compliance.yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/mcp-compliance /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

##### 2.8 SSL Certificate
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d compliance.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

##### 2.9 Verify Installation
```bash
# Check server status
curl https://compliance.yourdomain.com/health

# View PM2 status
pm2 status

# View logs
pm2 logs mcp-compliance

# Run tests
npm test
```

#### 3. Container Installation

##### 3.1 Docker Installation
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

##### 3.2 Docker Setup
```bash
# Clone repository
git clone https://github.com/kilocode/mcp-compliance-server.git
cd mcp-compliance-server

# Create docker-compose file
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  mcp-compliance:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - KILOCODE_ENV=production
      - KILOCODE_PROJECT_PATH=/app
      - PORT=3000
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/mcp_compliance
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=mcp_compliance
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
EOF
```

##### 3.3 Build and Run
```bash
# Build Docker image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

##### 3.4 Verify Installation
```bash
# Check container status
docker-compose ps

# Check server health
curl http://localhost:3000/health

# Run tests in container
docker-compose exec mcp-compliance npm test
```

#### 4. Package Installation

##### 4.1 Download Package
```bash
# Download latest release
wget https://github.com/kilocode/mcp-compliance-server/releases/latest/download/mcp-compliance-server.tar.gz

# Extract package
tar -xzf mcp-compliance-server.tar.gz

# Move to application directory
sudo mv mcp-compliance-server /opt/
sudo chown -R mcp-compliance:mcp-compliance /opt/mcp-compliance-server
```

##### 4.2 Configuration
```bash
# Create configuration directory
sudo mkdir -p /etc/mcp-compliance

# Copy configuration files
sudo cp /opt/mcp-compliance-server/config/* /etc/mcp-compliance/

# Edit configuration
sudo nano /etc/mcp-compliance/config.json
```

```json
{
  "environment": "production",
  "port": 3000,
  "database": {
    "url": "postgresql://user:pass@localhost:5432/mcp_compliance"
  },
  "redis": {
    "url": "redis://localhost:6379"
  },
  "logging": {
    "level": "info",
    "file": "/var/log/mcp-compliance/app.log"
  }
}
```

##### 4.3 Service Setup
```bash
# Create service file
sudo nano /etc/systemd/system/mcp-compliance.service
```

```ini
[Unit]
Description=MCP Compliance Server
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=mcp-compliance
WorkingDirectory=/opt/mcp-compliance-server
ExecStart=/usr/bin/node dist/index.js
Restart=always
RestartSec=10
Environment=NODE_ENV=production
Environment=CONFIG_PATH=/etc/mcp-compliance/config.json

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable mcp-compliance
sudo systemctl start mcp-compliance

# Check service status
sudo systemctl status mcp-compliance
```

##### 4.4 Verify Installation
```bash
# Check server health
curl http://localhost:3000/health

# View logs
sudo journalctl -u mcp-compliance -f

# Run tests
sudo -u mcp-compliance npm test
```

### Post-Installation Steps

#### 1. Initial Configuration
```bash
# Run initial setup
npm run setup

# Create admin user
npm run create-admin

# Configure initial compliance rules
npm run configure-rules
```

#### 2. Security Hardening
```bash
# Set up firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 3000

# Configure fail2ban
sudo apt install -y fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local
```

#### 3. Monitoring Setup
```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Set up log rotation
sudo nano /etc/logrotate.d/mcp-compliance
```

```
/var/log/mcp-compliance/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 mcp-compliance mcp-compliance
}
```

#### 4. Backup Configuration
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/mcp-compliance"
mkdir -p $BACKUP_DIR

# Backup database
pg_dump mcp_compliance > $BACKUP_DIR/database_$DATE.sql

# Backup configuration
cp -r /etc/mcp-compliance $BACKUP_DIR/config_$DATE

# Backup logs
cp -r /var/log/mcp-compliance $BACKUP_DIR/logs_$DATE

# Compress backup
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz -C $BACKUP_DIR database_$DATE.sql config_$DATE logs_$DATE

# Clean old backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

# Make backup script executable
chmod +x backup.sh

# Add to crontab
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

---

## MCP Memory Service Installation Guide

### Overview

The MCP Memory Service provides memory management and consolidation capabilities for the KiloCode ecosystem. This guide covers installation procedures for different environments.

### Prerequisites

#### System Requirements
```bash
# Minimum Requirements
- Operating System: Ubuntu 20.04+ / CentOS 8+ / Windows 10+
- CPU: 4 cores
- RAM: 8 GB
- Disk Space: 10 GB
- Network: Internet connection

# Recommended Requirements
- Operating System: Ubuntu 22.04+ / CentOS 9+ / Windows 11+
- CPU: 8 cores
- RAM: 16 GB
- Disk Space: 50 GB
- Network: High-speed internet connection
```

#### Software Requirements
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y nodejs npm git python3 python3-pip postgresql redis-server

# CentOS/RHEL
sudo yum install -y nodejs npm git python3 python3-pip postgresql-server redis

# Windows
# Download and install Node.js from https://nodejs.org
# Install Python 3 from https://python.org
# Install PostgreSQL from https://www.postgresql.org
# Install Redis from https://redis.io
```

### Installation Methods

#### 1. Development Installation

##### 1.1 Clone Repository
```bash
# Clone the repository
git clone https://github.com/kilocode/mcp-memory-service.git
cd mcp-memory-service

# Switch to development branch
git checkout develop
```

##### 1.2 Install Dependencies
```bash
# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies
npm install --dev

# Install global dependencies
npm install -g nodemon typescript ts-node
```

##### 1.3 Environment Configuration
```bash
# Create environment file
cp .env.example .env

# Edit environment file
nano .env
```

```bash
# .env file content
NODE_ENV=development
KILOCODE_ENV=development
KILOCODE_PROJECT_PATH=/workspace
PORT=8080
LOG_LEVEL=debug
DATABASE_URL=postgresql://localhost:5432/mcp_memory
REDIS_URL=redis://localhost:6379
VECTOR_DB_URL=http://localhost:8080
MEMORY_CONSOLIDATION_ENABLED=true
MEMORY_RETENTION_DAYS=30
```

##### 1.4 Database Setup
```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE mcp_memory;"
sudo -u postgres psql -c "CREATE USER mcp_user WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE mcp_memory TO mcp_user;"

# Run database migrations
npm run db:migrate

# Seed database with initial data
npm run db:seed
```

##### 1.5 Start Development Services
```bash
# Start Redis
sudo systemctl start redis
sudo systemctl enable redis

# Start development server
npm run dev

# Or use nodemon for auto-reload
npx nodemon src/index.ts

# Start vector database (if using)
python -m chromadb run --path ./chroma_db
```

##### 1.6 Verify Installation
```bash
# Check server status
curl http://localhost:8080/health

# View server logs
npm run logs

# Run tests
npm test

# Check database connection
npm run db:check
```

#### 2. Production Installation

##### 2.1 System Preparation
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y nodejs npm git python3 python3-pip postgresql redis-server nginx supervisor

# Create application user
sudo useradd -m -s /bin/bash mcp-memory
sudo usermod -aG sudo mcp-memory
```

##### 2.2 Application Setup
```bash
# Switch to application user
sudo su - mcp-memory

# Clone repository
git clone https://github.com/kilocode/mcp-memory-service.git
cd mcp-memory-service

# Switch to production branch
git checkout main
```

##### 2.3 Install Dependencies
```bash
# Install Node.js dependencies
npm install --production

# Install Python dependencies
pip install -r requirements.txt

# Install PM2 for process management
npm install -g pm2

# Install system dependencies for Python packages
sudo apt install -y build-essential python3-dev
```

##### 2.4 Environment Configuration
```bash
# Create environment file
cp .env.example .env

# Edit environment file
nano .env
```

```bash
# Production .env file content
NODE_ENV=production
KILOCODE_ENV=production
KILOCODE_PROJECT_PATH=/var/www/mcp-memory
PORT=8080
LOG_LEVEL=info
DATABASE_URL=postgresql://mcp_user:password@localhost:5432/mcp_memory
REDIS_URL=redis://localhost:6379
VECTOR_DB_URL=http://localhost:8080
MEMORY_CONSOLIDATION_ENABLED=true
MEMORY_RETENTION_DAYS=90
MEMORY_STORAGE_PATH=/var/lib/mcp-memory
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
```

##### 2.5 Database Setup
```bash
# Create database directory
sudo mkdir -p /var/lib/postgresql/15/main
sudo chown -R postgres:postgres /var/lib/postgresql/15/main

# Initialize PostgreSQL
sudo postgresql-setup --initdb

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE mcp_memory;"
sudo -u postgres psql -c "CREATE USER mcp_user WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE mcp_memory TO mcp_user;"

# Run database migrations
npm run db:migrate

# Create database backup
npm run db:backup
```

##### 2.6 Redis Setup
```bash
# Start and enable Redis
sudo systemctl start redis
sudo systemctl enable redis

# Configure Redis for production
sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup
sudo nano /etc/redis/redis.conf
```

```redis
# Production Redis configuration
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

```bash
# Restart Redis
sudo systemctl restart redis

# Check Redis status
sudo systemctl status redis
```

##### 2.7 Process Management
```bash
# Create PM2 configuration
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'mcp-memory',
    script: 'dist/index.js',
    instances: 'max',
    exec_mode: 'cluster',
    env: {
      NODE_ENV: 'production',
      PORT: 8080,
    },
    error_file: '/var/log/mcp-memory/error.log',
    out_file: '/var/log/mcp-memory/out.log',
    log_file: '/var/log/mcp-memory/combined.log',
    time: true,
    autorestart: true,
    watch: false,
    max_memory_restart: '2G',
    node_args: '--max-old-space-size=2048',
  }]
};
EOF

# Start application with PM2
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
```

##### 2.8 Nginx Configuration
```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/mcp-memory
```

```nginx
server {
    listen 80;
    server_name memory.yourdomain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/mcp-memory /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

##### 2.9 SSL Certificate
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d memory.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

##### 2.10 Verify Installation
```bash
# Check server status
curl https://memory.yourdomain.com/health

# View PM2 status
pm2 status

# View logs
pm2 logs mcp-memory

# Run tests
npm test

# Check database connection
npm run db:check
```

#### 3. Container Installation

##### 3.1 Docker Installation
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

##### 3.2 Docker Setup
```bash
# Clone repository
git clone https://github.com/kilocode/mcp-memory-service.git
cd mcp-memory-service

# Create docker-compose file
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  mcp-memory:
    build: .
    ports:
      - "8080:8080"
    environment:
      - NODE_ENV=production
      - KILOCODE_ENV=production
      - KILOCODE_PROJECT_PATH=/app
      - PORT=8080
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/mcp_memory
      - REDIS_URL=redis://redis:6379
      - VECTOR_DB_URL=http://vector-db:8000
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./chroma_db:/app/chroma_db
    depends_on:
      - postgres
      - redis
      - vector-db
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=mcp_memory
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  vector-db:
    build: 
      context: .
      dockerfile: Dockerfile.vector
    ports:
      - "8000:8000"
    volumes:
      - ./chroma_db:/chroma_db
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
EOF
```

##### 3.3 Build and Run
```bash
# Build Docker images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

##### 3.4 Verify Installation
```bash
# Check container status
docker-compose ps

# Check server health
curl http://localhost:8080/health

# Run tests in container
docker-compose exec mcp-memory npm test

# Check database connection
docker-compose exec mcp-memory npm run db:check
```

#### 4. Package Installation

##### 4.1 Download Package
```bash
# Download latest release
wget https://github.com/kilocode/mcp-memory-service/releases/latest/download/mcp-memory-service.tar.gz

# Extract package
tar -xzf mcp-memory-service.tar.gz

# Move to application directory
sudo mv mcp-memory-service /opt/
sudo chown -R mcp-memory:mcp-memory /opt/mcp-memory-service
```

##### 4.2 Configuration
```bash
# Create configuration directory
sudo mkdir -p /etc/mcp-memory

# Copy configuration files
sudo cp /opt/mcp-memory-service/config/* /etc/mcp-memory/

# Edit configuration
sudo nano /etc/mcp-memory/config.json
```

```json
{
  "environment": "production",
  "port": 8080,
  "database": {
    "url": "postgresql://mcp_user:password@localhost:5432/mcp_memory"
  },
  "redis": {
    "url": "redis://localhost:6379"
  },
  "vector_db": {
    "url": "http://localhost:8000"
  },
  "memory": {
    "consolidation_enabled": true,
    "retention_days": 90,
    "storage_path": "/var/lib/mcp-memory"
  },
  "logging": {
    "level": "info",
    "file": "/var/log/mcp-memory/app.log"
  }
}
```

##### 4.3 Service Setup
```bash
# Create service file
sudo nano /etc/systemd/system/mcp-memory.service
```

```ini
[Unit]
Description=MCP Memory Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=mcp-memory
WorkingDirectory=/opt/mcp-memory-service
ExecStart=/usr/bin/node dist/index.js
Restart=always
RestartSec=10
Environment=NODE_ENV=production
Environment=CONFIG_PATH=/etc/mcp-memory/config.json

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable mcp-memory
sudo systemctl start mcp-memory

# Check service status
sudo systemctl status mcp-memory
```

##### 4.4 Verify Installation
```bash
# Check server health
curl http://localhost:8080/health

# View logs
sudo journalctl -u mcp-memory -f

# Run tests
sudo -u mcp-memory npm test

# Check database connection
sudo -u mcp-memory npm run db:check
```

### Post-Installation Steps

#### 1. Initial Configuration
```bash
# Run initial setup
npm run setup

# Configure memory settings
npm run configure-memory

# Set up consolidation rules
npm run configure-consolidation
```

#### 2. Security Hardening
```bash
# Set up firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 8080

# Configure fail2ban
sudo apt install -y fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local
```

#### 3. Monitoring Setup
```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Set up log rotation
sudo nano /etc/logrotate.d/mcp-memory
```

```
/var/log/mcp-memory/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 mcp-memory mcp-memory
}
```

#### 4. Backup Configuration
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/mcp-memory"
mkdir -p $BACKUP_DIR

# Backup database
pg_dump mcp_memory > $BACKUP_DIR/database_$DATE.sql

# Backup vector database
cp -r /var/lib/mcp-memory/chroma_db $BACKUP_DIR/vector_db_$DATE

# Backup configuration
cp -r /etc/mcp-memory $BACKUP_DIR/config_$DATE

# Backup logs
cp -r /var/log/mcp-memory $BACKUP_DIR/logs_$DATE

# Compress backup
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz -C $BACKUP_DIR database_$DATE.sql vector_db_$DATE config_$DATE logs_$DATE

# Clean old backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

# Make backup script executable
chmod +x backup.sh

# Add to crontab
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

#### 5. Performance Optimization
```bash
# Configure system settings
echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf
echo "vm.vfs_cache_pressure=50" | sudo tee -a /etc/sysctl.conf

# Apply settings
sudo sysctl -p

# Configure PostgreSQL for performance
sudo nano /etc/postgresql/15/main/postgresql.conf
```

```ini
# PostgreSQL performance settings
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
```

```bash
# Restart PostgreSQL
sudo systemctl restart postgresql
```

---

## Common Installation Issues and Solutions

### 1. Node.js Issues

#### 1.1 Node.js Version Compatibility
```bash
# Check Node.js version
node --version

# Install Node.js version manager (nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Install specific Node.js version
nvm install 18.17.0

# Use specific Node.js version
nvm use 18.17.0
```

#### 1.2 Permission Issues
```bash
# Fix npm permissions
sudo chown -R $(whoami) ~/.npm

# Use npm without sudo
npm config set prefix ~/.npm

# Add to PATH
echo 'export PATH=~/.npm/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### 2. Database Issues

#### 2.1 PostgreSQL Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# Test database connection
psql -h localhost -U mcp_user -d mcp_memory
```

#### 2.2 Redis Connection Issues
```bash
# Check Redis status
sudo systemctl status redis

# Start Redis
sudo systemctl start redis

# Check Redis logs
sudo tail -f /var/log/redis/redis-server.log

# Test Redis connection
redis-cli ping
```

### 3. Port Conflicts

#### 3.1 Find and Kill Process Using Port
```bash
# Find process using port
sudo lsof -i :8080

# Kill process
sudo kill -9 <PID>
```

#### 3.2 Change Port Configuration
```bash
# Edit environment file
nano .env

# Change port
PORT=3001

# Restart service
sudo systemctl restart mcp-compliance
```

### 4. Memory Issues

#### 4.1 Increase Memory Limit
```bash
# Edit PM2 configuration
nano ecosystem.config.js

# Increase memory limit
max_memory_restart: '4G'

# Restart service
pm2 restart mcp-compliance
```

#### 4.2 Optimize Node.js Memory
```bash
# Set Node.js memory limits
export NODE_OPTIONS="--max-old-space-size=4096"

# Add to startup
echo 'export NODE_OPTIONS="--max-old-space-size=4096"' >> ~/.bashrc
```

### 5. SSL Certificate Issues

#### 5.1 Certificate Renewal
```bash
# Renew certificate
sudo certbot renew

# Test certificate
sudo certbot certificates

# Check certificate expiration
sudo openssl x509 -enddate -noout -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem
```

#### 5.2 Certificate Configuration
```bash
# Check Nginx configuration
sudo nginx -t

# Test SSL configuration
sudo openssl s_client -connect yourdomain.com:443
```

---

## Support and Contact Information

### Technical Support
- **Email**: support@kilocode.com
- **Phone**: +1 (555) 123-4567
- **Hours**: 24/7 for production support

### Installation Support
- **Installation Guide**: [KiloCode Installation Documentation](https://kilocode.com/docs/installation)
- **Video Tutorials**: [KiloCode YouTube Channel](https://youtube.com/kilocode)
- **Community Forum**: [KiloCode Community](https://community.kilocode.com)

### Documentation Resources
- **API Documentation**: [KiloCode API Reference](https://kilocode.com/api)
- **Configuration Guide**: [KiloCode Configuration Guide](https://kilocode.com/docs/configuration)
- **Troubleshooting Guide**: [KiloCode Troubleshooting Guide](https://kilocode.com/docs/troubleshooting)

---

*These installation guides are part of the KiloCode MCP Setup and Configuration Architecture Plan and should be reviewed and updated regularly to reflect changes in installation procedures and best practices.*