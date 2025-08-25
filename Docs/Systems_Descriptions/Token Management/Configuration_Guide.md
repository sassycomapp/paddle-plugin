# Token Management System - Configuration Guide

## Table of Contents
- [Overview](#overview)
- [Configuration Files](#configuration-files)
- [Environment Variables](#environment-variables)
- [Database Configuration](#database-configuration)
- [API Configuration](#api-configuration)
- [Security Configuration](#security-configuration)
- [Monitoring Configuration](#monitoring-configuration)
- [Caching Configuration](#caching-configuration)
- [Integration Configuration](#integration-configuration)
- [Performance Configuration](#performance-configuration)
- [Logging Configuration](#logging-configuration)
- [Advanced Configuration](#advanced-configuration)

## Overview

The Token Management System provides flexible configuration options through multiple sources including configuration files, environment variables, and database settings. This guide covers all available configuration options and best practices for system configuration.

### Configuration Hierarchy

Configuration is loaded in the following order (later sources override earlier ones):

1. **Default Configuration** (built-in defaults)
2. **Configuration File** (`config.json`)
3. **Environment Variables** (system environment)
4. **Database Settings** (runtime overrides)
5. **Command Line Arguments** (highest priority)

## Configuration Files

### Main Configuration File

The main configuration file is `config.json` located in the application root directory:

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "token_management",
    "user": "token_user",
    "password": "secure_password",
    "pool_size": 20,
    "max_overflow": 30,
    "timeout": 30
  },
  "api": {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": false,
    "cors_enabled": true,
    "cors_origins": ["*"]
  },
  "security": {
    "secret_key": "your-secret-key-here",
    "jwt_algorithm": "HS256",
    "token_expiry": 3600,
    "api_key_expiry": 86400
  },
  "monitoring": {
    "enabled": true,
    "check_interval": 60,
    "alert_thresholds": {
      "cpu_usage": 80,
      "memory_usage": 85,
      "error_rate": 5.0,
      "response_time": 2.0,
      "quota_usage": 90
    }
  },
  "caching": {
    "enabled": true,
    "redis_host": "localhost",
    "redis_port": 6379,
    "cache_ttl": 300,
    "max_cache_size": 10000
  },
  "integrations": {
    "mcp": {
      "enabled": true,
      "host": "localhost",
      "port": 8000,
      "timeout": 30
    },
    "kilocode": {
      "enabled": true,
      "host": "localhost",
      "port": 8080,
      "timeout": 60
    }
  }
}
```

### Environment Configuration

Environment-specific configurations can be stored in separate files:

```json
// config.development.json
{
  "database": {
    "host": "localhost",
    "debug": true
  },
  "api": {
    "host": "127.0.0.1",
    "debug": true
  }
}

// config.production.json
{
  "database": {
    "host": "prod-db.example.com",
    "pool_size": 50
  },
  "api": {
    "host": "0.0.0.0",
    "debug": false
  }
}
```

### Configuration Validation

```python
import json
from pathlib import Path
from typing import Dict, Any

class ConfigValidator:
    """Validate configuration files."""
    
    def __init__(self):
        self.required_sections = ['database', 'api', 'security']
        self.required_database_fields = ['host', 'port', 'name', 'user', 'password']
        self.required_api_fields = ['host', 'port']
        self.required_security_fields = ['secret_key']
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration structure."""
        try:
            # Check required sections
            for section in self.required_sections:
                if section not in config:
                    raise ValueError(f"Missing required section: {section}")
            
            # Validate database configuration
            if 'database' in config:
                self._validate_database_config(config['database'])
            
            # Validate API configuration
            if 'api' in config:
                self._validate_api_config(config['api'])
            
            # Validate security configuration
            if 'security' in config:
                self._validate_security_config(config['security'])
            
            return True
            
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False
    
    def _validate_database_config(self, db_config: Dict[str, Any]):
        """Validate database configuration."""
        for field in self.required_database_fields:
            if field not in db_config:
                raise ValueError(f"Missing database field: {field}")
        
        # Validate port range
        if not (1 <= db_config['port'] <= 65535):
            raise ValueError("Database port must be between 1 and 65535")
    
    def _validate_api_config(self, api_config: Dict[str, Any]):
        """Validate API configuration."""
        for field in self.required_api_fields:
            if field not in api_config:
                raise ValueError(f"Missing API field: {field}")
        
        # Validate port range
        if not (1 <= api_config['port'] <= 65535):
            raise ValueError("API port must be between 1 and 65535")
    
    def _validate_security_config(self, security_config: Dict[str, Any]):
        """Validate security configuration."""
        if 'secret_key' not in security_config or not security_config['secret_key']:
            raise ValueError("Security secret key is required")
        
        if 'token_expiry' in security_config and security_config['token_expiry'] <= 0:
            raise ValueError("Token expiry must be positive")

# Usage
validator = ConfigValidator()
with open('config.json', 'r') as f:
    config = json.load(f)

if validator.validate_config(config):
    print("Configuration is valid")
else:
    print("Configuration validation failed")
```

## Environment Variables

### Database Configuration

```bash
# Database Connection
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
export DATABASE_NAME=token_management
export DATABASE_USER=token_user
export DATABASE_PASSWORD=secure_password

# Database Pool Settings
export DATABASE_POOL_SIZE=20
export DATABASE_MAX_OVERFLOW=30
export DATABASE_TIMEOUT=30
export DATABASE_POOL_RECYCLE=3600
```

### API Configuration

```bash
# Server Settings
export API_HOST=0.0.0.0
export API_PORT=8000
export API_DEBUG=false
export API_WORKERS=4

# CORS Settings
export API_CORS_ENABLED=true
export API_CORS_ORIGINS="https://yourapp.com,https://app.yourcompany.com"
export API_CORS_METHODS="GET,POST,PUT,DELETE,OPTIONS"
export API_CORS_HEADERS="Content-Type,Authorization"
```

### Security Configuration

```bash
# Security Settings
export SECURITY_SECRET_KEY=your-secret-key-here
export SECURITY_JWT_ALGORITHM=HS256
export SECURITY_TOKEN_EXPIRY=3600
export SECURITY_API_KEY_EXPIRY=86400
export SECURITY_RATE_LIMIT=100
export SECURITY_RATE_LIMIT_WINDOW=3600
```

### Monitoring Configuration

```bash
# Monitoring Settings
export MONITORING_ENABLED=true
export MONITORING_CHECK_INTERVAL=60
export MONITORING_LOG_LEVEL=INFO
export MONITORING_METRICS_ENABLED=true

# Alert Thresholds
export MONITORING_CPU_THRESHOLD=80
export MONITORING_MEMORY_THRESHOLD=85
export MONITORING_ERROR_RATE_THRESHOLD=5.0
export MONITORING_RESPONSE_TIME_THRESHOLD=2.0
export MONITORING_QUOTA_THRESHOLD=90
```

### Caching Configuration

```bash
# Redis Settings
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PASSWORD=

# Cache Settings
export CACHING_ENABLED=true
export CACHING_TTL=300
export CACHING_MAX_SIZE=10000
export CACHING_ENABLE_COMPRESSION=true
```

### Integration Configuration

```bash
# MCP Integration
export MCP_ENABLED=true
export MCP_HOST=localhost
export MCP_PORT=8000
export MCP_TIMEOUT=30
export MCP_MAX_RETRIES=3

# KiloCode Integration
export KILOCODE_ENABLED=true
export KILOCODE_HOST=localhost
export KILOCODE_PORT=8080
export KILOCODE_TIMEOUT=60
export KILOCODE_MAX_CONCURRENT_TASKS=10
```

### Logging Configuration

```bash
# Logging Settings
export LOG_LEVEL=INFO
export LOG_FILE=/var/log/token_management/app.log
export LOG_MAX_SIZE=10485760
export LOG_BACKUP_COUNT=5
export LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

## Database Configuration

### PostgreSQL Configuration

```sql
-- PostgreSQL Configuration
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Reload configuration
SELECT pg_reload_conf();
```

### Database Connection Pool

```python
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager

class DatabaseConnectionPool:
    """Database connection pool for token management system."""
    
    def __init__(self, config):
        self.config = config
        self.pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool."""
        try:
            self.pool = pool.ThreadedConnectionPool(
                minconn=self.config.get('pool_size', 5),
                maxconn=self.config.get('max_connections', 20),
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['name'],
                user=self.config['user'],
                password=self.config['password'],
                connect_timeout=self.config.get('timeout', 30)
            )
            print("Database connection pool initialized successfully")
        except Exception as e:
            print(f"Failed to initialize database pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection from pool."""
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        except Exception as e:
            print(f"Database error: {e}")
            raise
        finally:
            if conn:
                self.pool.putconn(conn)
    
    def execute_query(self, query, params=None):
        """Execute SQL query with connection pool."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchall()
    
    def close_all(self):
        """Close all connections in pool."""
        if self.pool:
            self.pool.closeall()
```

### Database Schema Configuration

```sql
-- Token Management Schema Configuration
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    department VARCHAR(100),
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quotas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    daily_limit INTEGER NOT NULL DEFAULT 10000,
    monthly_limit INTEGER NOT NULL DEFAULT 300000,
    hard_limit INTEGER NOT NULL DEFAULT 1000000,
    warning_threshold DECIMAL(3,2) NOT NULL DEFAULT 0.80,
    critical_threshold DECIMAL(3,2) NOT NULL DEFAULT 0.95,
    daily_used INTEGER NOT NULL DEFAULT 0,
    monthly_used INTEGER NOT NULL DEFAULT 0,
    last_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    application VARCHAR(100) NOT NULL,
    tokens_used INTEGER NOT NULL,
    model VARCHAR(50) NOT NULL,
    cost DECIMAL(10,6) NOT NULL DEFAULT 0.0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_usage_records_user_id ON usage_records(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_records_timestamp ON usage_records(timestamp);
CREATE INDEX IF NOT EXISTS idx_usage_records_application ON usage_records(application);
```

## API Configuration

### Server Configuration

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
import uvicorn

app = FastAPI(
    title="Token Management System",
    description="API for managing AI token usage and quotas",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourapp.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# API Key Authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        reload=False,
        log_level="info"
    )
```

### Rate Limiting Configuration

```python
from fastapi import FastAPI, Request
from fastapi.middleware import Middleware
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time
from collections import defaultdict

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app, limit=100, window=3600):
        super().__init__(app)
        self.limit = limit
        self.window = window
        self.requests = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < self.window
        ]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.limit:
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded"},
                headers={"Retry-After": str(self.window)}
            )
        
        # Record request
        self.requests[client_ip].append(current_time)
        
        response = await call_next(request)
        return response

# Apply rate limiting
app.add_middleware(RateLimitMiddleware, limit=100, window=3600)
```

## Security Configuration

### Authentication Configuration

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional

app = FastAPI()

# Security Configuration
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Generate password hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username
```

### API Key Authentication

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Annotated

router = APIRouter()
api_key_header = APIKeyHeader(name="X-API-Key")

API_KEYS = {
    "user1": "key1",
    "user2": "key2",
    "admin": "admin-key"
}

async def get_api_key(api_key: Annotated[str, Depends(api_key_header)]):
    """Validate API key."""
    if api_key not in API_KEYS.values():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    return api_key

@router.get("/protected")
async def protected_route(api_key: Annotated[str, Depends(get_api_key)]):
    """Protected route requiring API key."""
    return {"message": "Access granted", "api_key": api_key}
```

## Monitoring Configuration

### Health Check Configuration

```python
from src.monitoring import HealthChecker, HealthStatus

class SystemHealthChecker:
    """Comprehensive system health checker."""
    
    def __init__(self, config):
        self.config = config
        self.health_checker = HealthChecker()
    
    def check_system_health(self):
        """Perform comprehensive system health check."""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }
        
        # Check database
        db_health = self.health_checker.check_database()
        health_status['components']['database'] = db_health
        
        # Check Redis
        redis_health = self.health_checker.check_redis()
        health_status['components']['redis'] = redis_health
        
        # Check API
        api_health = self.health_checker.check_api()
        health_status['components']['api'] = api_health
        
        # Check system resources
        system_health = self.health_checker.check_system_resources()
        health_status['components']['system'] = system_health
        
        # Determine overall status
        for component, status in health_status['components'].items():
            if status['status'] == 'unhealthy':
                health_status['overall_status'] = 'degraded'
            elif status['status'] == 'critical':
                health_status['overall_status'] = 'critical'
        
        return health_status
```

### Alert Configuration

```python
from src.alerting import AlertManager, AlertSeverity

class AlertConfiguration:
    """Alert configuration manager."""
    
    def __init__(self, config):
        self.config = config
        self.alert_manager = AlertManager()
        self._setup_alerts()
    
    def _setup_alerts(self):
        """Setup alert configurations."""
        # Database alerts
        self.alert_manager.add_alert_rule(
            name='database_connection',
            condition='database.status == "unhealthy"',
            severity=AlertSeverity.CRITICAL,
            message='Database connection lost'
        )
        
        # Memory alerts
        self.alert_manager.add_alert_rule(
            name='high_memory_usage',
            condition='memory_usage > 90',
            severity=AlertSeverity.CRITICAL,
            message='Memory usage critical'
        )
        
        # CPU alerts
        self.alert_manager.add_alert_rule(
            name='high_cpu_usage',
            condition='cpu_usage > 85',
            severity=AlertSeverity.WARNING,
            message='High CPU usage detected'
        )
        
        # Quota alerts
        self.alert_manager.add_alert_rule(
            name='quota_warning',
            condition='quota_usage > 80',
            severity=AlertSeverity.WARNING,
            message='Quota usage warning'
        )
        
        self.alert_manager.add_alert_rule(
            name='quota_critical',
            condition='quota_usage > 95',
            severity=AlertSeverity.CRITICAL,
            message='Quota usage critical'
        )
    
    def check_alerts(self, metrics):
        """Check for alerts based on metrics."""
        return self.alert_manager.check_alerts(metrics)
```

## Caching Configuration

### Redis Configuration

```python
import redis
from redis.exceptions import RedisError

class RedisCache:
    """Redis caching implementation."""
    
    def __init__(self, config):
        self.config = config
        self.redis_client = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.Redis(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 6379),
                db=self.config.get('db', 0),
                password=self.config.get('password'),
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            self.redis_client.ping()
            print("Redis connection established")
            
        except RedisError as e:
            print(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def get(self, key):
        """Get value from cache."""
        if not self.redis_client:
            return None
        
        try:
            return self.redis_client.get(key)
        except RedisError as e:
            print(f"Redis get error: {e}")
            return None
    
    def set(self, key, value, ttl=None):
        """Set value in cache."""
        if not self.redis_client:
            return False
        
        try:
            if ttl:
                return self.redis_client.setex(key, ttl, value)
            else:
                return self.redis_client.set(key, value)
        except RedisError as e:
            print(f"Redis set error: {e}")
            return False
    
    def delete(self, key):
        """Delete key from cache."""
        if not self.redis_client:
            return False
        
        try:
            return self.redis_client.delete(key)
        except RedisError as e:
            print(f"Redis delete error: {e}")
            return False
    
    def clear_pattern(self, pattern):
        """Clear keys matching pattern."""
        if not self.redis_client:
            return
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except RedisError as e:
            print(f"Redis clear pattern error: {e}")
```

### Cache Configuration Examples

```python
# User session cache
def cache_user_session(user_id, session_data, ttl=3600):
    """Cache user session data."""
    cache_key = f"user_session:{user_id}"
    redis_cache.set(cache_key, json.dumps(session_data), ttl)

# Quota cache
def cache_user_quota(user_id, quota_data, ttl=60):
    """Cache user quota data."""
    cache_key = f"user_quota:{user_id}"
    redis_cache.set(cache_key, json.dumps(quota_data), ttl)

# Token count cache
def cache_token_count(text, model, token_count, ttl=300):
    """Cache token count results."""
    cache_key = f"token_count:{hash(text)}:{model}"
    redis_cache.set(cache_key, token_count, ttl)
```

## Integration Configuration

### MCP Integration Configuration

```python
from src.mcp_integration import MCPIntegration

class MCPConfiguration:
    """MCP integration configuration."""
    
    def __init__(self, config):
        self.config = config
        self.mcp_integration = None
        self._setup_mcp()
    
    def _setup_mcp(self):
        """Setup MCP integration."""
        if not self.config.get('enabled', True):
            return
        
        try:
            self.mcp_integration = MCPIntegration(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 8000),
                timeout=self.config.get('timeout', 30),
                max_retries=self.config.get('max_retries', 3)
            )
            
            # Test connection
            self.mcp_integration.test_connection()
            print("MCP integration initialized")
            
        except Exception as e:
            print(f"MCP integration failed: {e}")
            self.mcp_integration = None
    
    def get_mcp_client(self):
        """Get MCP client instance."""
        return self.mcp_integration
```

### KiloCode Integration Configuration

```python
from src.kilocode_integration import KiloCodeIntegration

class KiloCodeConfiguration:
    """KiloCode integration configuration."""
    
    def __init__(self, config):
        self.config = config
        self.kilocode_integration = None
        self._setup_kilocode()
    
    def _setup_kilocode(self):
        """Setup KiloCode integration."""
        if not self.config.get('enabled', True):
            return
        
        try:
            self.kilocode_integration = KiloCodeIntegration(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 8080),
                timeout=self.config.get('timeout', 60),
                max_concurrent_tasks=self.config.get('max_concurrent_tasks', 10)
            )
            
            # Test connection
            self.kilocode_integration.test_connection()
            print("KiloCode integration initialized")
            
        except Exception as e:
            print(f"KiloCode integration failed: {e}")
            self.kilocode_integration = None
    
    def get_kilocode_client(self):
        """Get KiloCode client instance."""
        return self.kilocode_integration
```

## Performance Configuration

### Performance Optimization

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

class PerformanceOptimizer:
    """Performance optimization utilities."""
    
    def __init__(self, config):
        self.config = config
        self.executor = ThreadPoolExecutor(
            max_workers=config.get('max_workers', 4)
        )
    
    async def async_batch_processing(self, items, process_func, batch_size=10):
        """Process items in batches asynchronously."""
        results = []
        
        # Create batches
        batches = [
            items[i:i + batch_size]
            for i in range(0, len(items), batch_size)
        ]
        
        # Process batches concurrently
        tasks = []
        for batch in batches:
            task = asyncio.create_task(
                self._process_batch(batch, process_func)
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        batch_results = await asyncio.gather(*tasks)
        
        # Flatten results
        for result in batch_results:
            results.extend(result)
        
        return results
    
    async def _process_batch(self, batch, process_func):
        """Process a single batch."""
        results = []
        
        for item in batch:
            try:
                result = await process_func(item)
                results.append(result)
            except Exception as e:
                print(f"Error processing item {item}: {e}")
                results.append(None)
        
        return results
    
    @lru_cache(maxsize=1000)
    def cached_token_count(self, text, model):
        """Cached token counting with LRU cache."""
        # This would call the actual token counting service
        return self._count_tokens(text, model)
    
    def _count_tokens(self, text, model):
        """Actual token counting implementation."""
        # Placeholder for actual token counting
        return len(text.split())
```

### Database Performance Configuration

```python
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

class DatabasePerformance:
    """Database performance optimization."""
    
    def __init__(self, config):
        self.config = config
    
    def create_optimized_indexes(self):
        """Create optimized database indexes."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_usage_records_user_timestamp ON usage_records(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_usage_records_application_timestamp ON usage_records(application, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_quotas_user_daily ON quotas(user_id, daily_limit)",
            "CREATE INDEX IF NOT EXISTS idx_users_department ON users(department)",
            "CREATE INDEX IF NOT EXISTS idx_usage_records_cost ON usage_records(cost)"
        ]
        
        for index in indexes:
            try:
                self.execute_query(index)
                print(f"Created index: {index}")
            except Exception as e:
                print(f"Failed to create index {index}: {e}")
    
    def analyze_tables(self):
        """Analyze database tables for better query planning."""
        tables = ['users', 'quotas', 'usage_records']
        
        for table in tables:
            try:
                self.execute_query(f"ANALYZE {table}")
                print(f"Analyzed table: {table}")
            except Exception as e:
                print(f"Failed to analyze table {table}: {e}")
    
    def vacuum_tables(self):
        """Perform VACUUM on database tables."""
        tables = ['users', 'quotas', 'usage_records']
        
        for table in tables:
            try:
                self.execute_query(f"VACUUM ANALYZE {table}")
                print(f"Vacuumed table: {table}")
            except Exception as e:
                print(f"Failed to vacuum table {table}: {e}")
```

## Logging Configuration

### Logging Setup

```python
import logging
import logging.handlers
from pathlib import Path

class LoggingConfiguration:
    """Logging configuration manager."""
    
    def __init__(self, config):
        self.config = config
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration."""
        # Create logs directory
        log_dir = Path(self.config.get('log_dir', '/var/log/token_management'))
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, self.config.get('log_level', 'INFO')),
            format=self.config.get('log_format', 
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            handlers=[
                # Console handler
                logging.StreamHandler(),
                
                # File handler with rotation
                logging.handlers.RotatingFileHandler(
                    log_dir / 'app.log',
                    maxBytes=self.config.get('max_size', 10485760),  # 10MB
                    backupCount=self.config.get('backup_count', 5)
                ),
                
                # Error file handler
                logging.handlers.RotatingFileHandler(
                    log_dir / 'error.log',
                    maxBytes=self.config.get('max_size', 10485760),
                    backupCount=self.config.get('backup_count', 5),
                    level=logging.ERROR
                )
            ]
        )
        
        # Set up specific loggers
        self._setup_loggers()
    
    def _setup_loggers(self):
        """Setup specific loggers."""
        # Token counting logger
        token_logger = logging.getLogger('token_counting')
        token_logger.setLevel(logging.INFO)
        
        # Quota management logger
        quota_logger = logging.getLogger('quota_management')
        quota_logger.setLevel(logging.INFO)
        
        # API logger
        api_logger = logging.getLogger('api')
        api_logger.setLevel(logging.INFO)
        
        # Database logger
        db_logger = logging.getLogger('database')
        db_logger.setLevel(logging.INFO)
```

### Structured Logging

```python
import json
import logging
from datetime import datetime

class StructuredLogger:
    """Structured logging implementation."""
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def log_event(self, event_type, user_id=None, details=None, severity='info'):
        """Log structured event."""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'severity': severity,
            'user_id': user_id,
            'details': details or {}
        }
        
        log_message = json.dumps(log_data)
        
        if severity == 'error':
            self.logger.error(log_message)
        elif severity == 'warning':
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def log_token_usage(self, user_id, tokens_used, application, model):
        """Log token usage event."""
        self.log_event(
            event_type='token_usage',
            user_id=user_id,
            details={
                'tokens_used': tokens_used,
                'application': application,
                'model': model
            },
            severity='info'
        )
    
    def log_quota_warning(self, user_id, usage_percentage):
        """Log quota warning event."""
        self.log_event(
            event_type='quota_warning',
            user_id=user_id,
            details={
                'usage_percentage': usage_percentage,
                'threshold': 80
            },
            severity='warning'
        )
    
    def log_quota_critical(self, user_id, usage_percentage):
        """Log quota critical event."""
        self.log_event(
            event_type='quota_critical',
            user_id=user_id,
            details={
                'usage_percentage': usage_percentage,
                'threshold': 95
            },
            severity='error'
        )
```

## Advanced Configuration

### Dynamic Configuration

```python
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

class DynamicConfiguration:
    """Dynamic configuration management."""
    
    def __init__(self, config_path):
        self.config_path = Path(config_path)
        self.config = {}
        self.last_modified = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                self.last_modified = datetime.fromtimestamp(
                    self.config_path.stat().st_mtime
                )
                print(f"Configuration loaded from {self.config_path}")
            else:
                print(f"Configuration file not found: {self.config_path}")
                self.config = {}
        except Exception as e:
            print(f"Failed to load configuration: {e}")
            self.config = {}
    
    def reload_config(self):
        """Reload configuration if file has changed."""
        try:
            current_modified = datetime.fromtimestamp(
                self.config_path.stat().st_mtime
            )
            
            if current_modified != self.last_modified:
                print("Configuration file changed, reloading...")
                self._load_config()
                return True
        except Exception as e:
            print(f"Failed to check configuration changes: {e}")
        
        return False
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        
        # Save to file
        self._save_config()
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"Configuration saved to {self.config_path}")
        except Exception as e:
            print(f"Failed to save configuration: {e}")
```

### Configuration Management

```python
class ConfigurationManager:
    """Centralized configuration management."""
    
    def __init__(self):
        self.config_sources = []
        self.config = {}
        self._initialize_sources()
    
    def _initialize_sources(self):
        """Initialize configuration sources."""
        # Add default configuration
        self.config_sources.append(DefaultConfiguration())
        
        # Add file configuration
        self.config_sources.append(FileConfiguration('config.json'))
        
        # Add environment configuration
        self.config_sources.append(EnvironmentConfiguration())
        
        # Add database configuration
        self.config_sources.append(DatabaseConfiguration())
    
    def load_config(self):
        """Load configuration from all sources."""
        self.config = {}
        
        for source in self.config_sources:
            source_config = source.load()
            self._merge_config(self.config, source_config)
        
        return self.config
    
    def _merge_config(self, base_config, new_config):
        """Merge configuration dictionaries."""
        for key, value in new_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._merge_config(base_config[key], value)
            else:
                base_config[key] = value
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value
    
    def reload(self):
        """Reload configuration from all sources."""
        return self.load_config()

# Configuration source interfaces
class ConfigurationSource:
    """Base configuration source interface."""
    
    def load(self):
        """Load configuration from source."""
        raise NotImplementedError

class DefaultConfiguration(ConfigurationSource):
    """Default configuration source."""
    
    def load(self):
        return {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'token_management',
                'user': 'token_user',
                'password': 'password'
            },
            'api': {
                'host': '0.0.0.0',
                'port': 8000,
                'debug': False
            },
            'security': {
                'secret_key': 'default-secret-key',
                'token_expiry': 3600
            }
        }

class FileConfiguration(ConfigurationSource):
    """File-based configuration source."""
    
    def __init__(self, file_path):
        self.file_path = file_path
    
    def load(self):
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load file configuration: {e}")
            return {}

class EnvironmentConfiguration(ConfigurationSource):
    """Environment-based configuration source."""
    
    def load(self):
        config = {}
        
        # Database configuration from environment
        if 'DATABASE_HOST' in os.environ:
            config.setdefault('database', {})['host'] = os.environ['DATABASE_HOST']
        if 'DATABASE_PORT' in os.environ:
            config.setdefault('database', {})['port'] = int(os.environ['DATABASE_PORT'])
        if 'DATABASE_NAME' in os.environ:
            config.setdefault('database', {})['name'] = os.environ['DATABASE_NAME']
        if 'DATABASE_USER' in os.environ:
            config.setdefault('database', {})['user'] = os.environ['DATABASE_USER']
        if 'DATABASE_PASSWORD' in os.environ:
            config.setdefault('database', {})['password'] = os.environ['DATABASE_PASSWORD']
        
        # API configuration from environment
        if 'API_HOST' in os.environ:
            config.setdefault('api', {})['host'] = os.environ['API_HOST']
        if 'API_PORT' in os.environ:
            config.setdefault('api', {})['port'] = int(os.environ['API_PORT'])
        if 'API_DEBUG' in os.environ:
            config.setdefault('api', {})['debug'] = os.environ['API_DEBUG'].lower() == 'true'
        
        return config

class DatabaseConfiguration(ConfigurationSource):
    """Database-based configuration source."""
    
    def load(self):
        # This would load configuration from database
        # For now, return empty dict
        return {}
```

---

*This Configuration Guide provides comprehensive documentation for configuring the Token Management System. For additional information, please refer to the other documentation guides or contact the development team.*