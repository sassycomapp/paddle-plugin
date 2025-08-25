# Token Management System - Troubleshooting Guide

## Table of Contents
- [Overview](#overview)
- [Common Issues](#common-issues)
- [Diagnostic Tools](#diagnostic-tools)
- [Database Issues](#database-issues)
- [API Issues](#api-issues)
- [Token Counting Issues](#token-counting-issues)
- [Quota Management Issues](#quota-management-issues)
- [Performance Issues](#performance-issues)
- [Integration Issues](#integration-issues)
- [Security Issues](#security-issues)
- [Monitoring Issues](#monitoring-issues)
- [Error Codes](#error-codes)
- [Support](#support)

## Overview

This troubleshooting guide provides solutions for common issues encountered when using the Token Management System. The guide is organized by problem category and includes diagnostic steps, common causes, and resolution procedures.

### Troubleshooting Process

1. **Identify the Problem**: Determine the specific issue and error messages
2. **Check Logs**: Review system logs for relevant error information
3. **Diagnose**: Use diagnostic tools to gather system information
4. **Resolve**: Apply the appropriate solution
5. **Verify**: Confirm the issue has been resolved
6. **Document**: Record the issue and resolution for future reference

### Getting Help

If you cannot resolve your issue using this guide:

1. Check the [FAQ](FAQ.md) section
2. Review the [Best Practices](Best_Practices.md) guide
3. Contact support with detailed information about your issue
4. Provide system logs and diagnostic information

## Common Issues

### Issue 1: Database Connection Failed

**Symptoms:**
- Application fails to start
- Database operations timeout
- Error messages about database connectivity

**Diagnostic Steps:**

```bash
# Check database service status
sudo systemctl status postgresql

# Test database connection
psql -h localhost -U token_user -d token_management

# Check network connectivity
telnet localhost 5432

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log
```

**Common Causes:**
- Database service not running
- Incorrect connection parameters
- Network connectivity issues
- Authentication problems
- Database server overloaded

**Solutions:**

```bash
# Start database service
sudo systemctl start postgresql

# Check and update connection parameters
# Edit config.json or environment variables
# Ensure host, port, username, password are correct

# Check firewall settings
sudo ufw status
sudo ufw allow 5432

# Reset database password if needed
sudo -u postgres psql
ALTER USER token_user WITH PASSWORD 'new_password';
```

**Verification:**
```python
# Test database connection
from src.database import Database

db = Database()
try:
    connection = db.get_connection()
    print("Database connection successful")
except Exception as e:
    print(f"Database connection failed: {e}")
```

### Issue 2: API Server Won't Start

**Symptoms:**
- API server fails to start
- Port conflicts
- Missing dependencies

**Diagnostic Steps:**

```bash
# Check if port is in use
netstat -tulpn | grep :8000

# Check application logs
tail -f logs/app.log

# Check Python environment
python -c "import sys; print(sys.path)"

# Check dependencies
pip list
```

**Common Causes:**
- Port already in use
- Missing Python packages
- Configuration errors
- Permission issues

**Solutions:**

```bash
# Kill process using port
sudo fuser -k 8000/tcp

# Install missing dependencies
pip install -r requirements.txt

# Check configuration file syntax
python -m json.tool config.json

# Fix permissions
chmod +x scripts/setup_token_integration.py
```

**Verification:**
```bash
# Start API server
python -m uvicorn token_management.main:app --host 0.0.0.0 --port 8000

# Test API endpoint
curl http://localhost:8000/health
```

### Issue 3: Token Counting Inaccurate

**Symptoms:**
- Token counts don't match expected values
- Different models give different counts
- Performance issues with token counting

**Diagnostic Steps:**

```python
# Test token counting
from src.token_counter import TokenCounter

counter = TokenCounter()

# Test with known text
test_text = "Hello, world!"
print(f"GPT-4 tokens: {counter.count_tokens(test_text, 'gpt-4')}")
print(f"Claude tokens: {counter.count_tokens(test_text, 'claude-3')}")
print(f"Llama tokens: {counter.count_tokens(test_text, 'llama-2')}")

# Test with longer text
long_text = "This is a longer text that should give us more tokens to work with."
print(f"Long text tokens: {counter.count_tokens(long_text, 'gpt-4')}")
```

**Common Causes:**
- pg_tiktoken extension not installed
- Model-specific tokenization issues
- Caching problems
- Database connection issues

**Solutions:**

```bash
# Check pg_tiktoken installation
psql -d token_management -c "SELECT * FROM pg_extension WHERE extname = 'pg_tiktoken';"

# Install pg_tiktoken if needed
psql -d token_management -c "CREATE EXTENSION IF NOT EXISTS pg_tiktoken;"

# Clear token cache
redis-cli FLUSHDB

# Test token counting directly
python -c "
from src.token_counter import TokenCounter
counter = TokenCounter()
print('Testing token counting...')
print(f'Test tokens: {counter.count_tokens(\"Hello, world!\", \"gpt-4\")}')
"
```

**Verification:**
```python
# Verify token counting accuracy
def test_token_counting():
    counter = TokenCounter()
    
    # Test cases with known token counts
    test_cases = [
        ("Hello, world!", 3),  # Expected: 3 tokens
        ("This is a test.", 5),  # Expected: 5 tokens
        ("", 0),  # Expected: 0 tokens
    ]
    
    for text, expected in test_cases:
        actual = counter.count_tokens(text, 'gpt-4')
        if actual == expected:
            print(f"✓ {text}: {actual} tokens (expected {expected})")
        else:
            print(f"✗ {text}: {actual} tokens (expected {expected})")

test_token_counting()
```

### Issue 4: Quota Management Not Working

**Symptoms:**
- Users can exceed quota limits
- Quota checks not working
- Incorrect quota calculations

**Diagnostic Steps:**

```python
# Check user quota
from src.quota_manager import QuotaManager

quota_manager = QuotaManager()
user_quota = quota_manager.get_user_quota('user_123456')
print(f"User quota: {user_quota}")

# Check quota calculation
required_tokens = 1000
has_quota = quota_manager.has_sufficient_quota('user_123456', required_tokens)
print(f"Has sufficient quota: {has_quota}")

# Check quota reset logic
print(f"Last reset: {user_quota.last_reset}")
print(f"Daily used: {user_quota.daily_used}")
print(f"Daily limit: {user_quota.daily_limit}")
```

**Common Causes:**
- Incorrect quota configuration
- Database schema issues
- Reset logic problems
- Concurrent request issues

**Solutions:**

```bash
# Check database schema
psql -d token_management -c "\d quotas"

# Reset user quota
psql -d token_management -c "
UPDATE quotas 
SET daily_used = 0, monthly_used = 0, last_reset = CURRENT_TIMESTAMP 
WHERE user_id = 'user_123456';
"

# Check quota calculation logic
python -c "
from src.quota_manager import QuotaManager
qm = QuotaManager()
print('Testing quota calculation...')
print(f'Test quota: {qm.has_sufficient_quota(\"test_user\", 100)}')
"
```

**Verification:**
```python
# Verify quota management
def test_quota_management():
    quota_manager = QuotaManager()
    
    # Test user with sufficient quota
    result = quota_manager.has_sufficient_quota('user_123456', 100)
    print(f"Sufficient quota test: {result}")
    
    # Test user with insufficient quota
    # (This would require setting up a user with limited quota)
    result = quota_manager.has_sufficient_quota('limited_user', 10000)
    print(f"Insufficient quota test: {result}")

test_quota_management()
```

### Issue 5: Performance Issues

**Symptoms:**
- Slow API responses
- High CPU/memory usage
- Database timeouts
- Token counting delays

**Diagnostic Steps:**

```bash
# Check system resources
top
htop
free -h
df -h

# Check database performance
psql -d token_management -c "SELECT * FROM pg_stat_activity;"

# Check API performance
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health

# Check Redis performance
redis-cli info
```

**Common Causes:**
- Database connection pool issues
- Inefficient queries
- Memory leaks
- Resource contention
- Network latency

**Solutions:**

```bash
# Optimize database configuration
# Increase connection pool size
# Add indexes for frequently queried tables

# Optimize application performance
# Enable caching
# Implement connection pooling
# Optimize queries

# Monitor and manage resources
# Set up resource limits
# Implement load balancing
# Scale horizontally
```

**Verification:**
```python
# Performance testing
import time
import requests

def test_api_performance():
    url = "http://localhost:8000/health"
    
    # Test response time
    start_time = time.time()
    response = requests.get(url)
    end_time = time.time()
    
    response_time = end_time - start_time
    print(f"Response time: {response_time:.3f} seconds")
    
    # Test concurrent requests
    import concurrent.futures
    
    def make_request():
        return requests.get(url)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(100)]
        results = [future.result() for future in futures]
    
    success_rate = sum(1 for r in results if r.status_code == 200) / len(results)
    print(f"Success rate: {success_rate:.2%}")

test_api_performance()
```

## Diagnostic Tools

### System Health Checker

```python
import psutil
import requests
from datetime import datetime

class SystemHealthChecker:
    """Comprehensive system health checker."""
    
    def __init__(self):
        self.checks = []
    
    def add_check(self, name, check_func):
        """Add a health check function."""
        self.checks.append((name, check_func))
    
    def run_checks(self):
        """Run all health checks."""
        results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        for name, check_func in self.checks:
            try:
                result = check_func()
                results['checks'][name] = {
                    'status': 'healthy' if result else 'unhealthy',
                    'result': result
                }
            except Exception as e:
                results['checks'][name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Determine overall status
        healthy_checks = sum(1 for check in results['checks'].values() 
                           if check['status'] == 'healthy')
        total_checks = len(results['checks'])
        
        results['overall_status'] = 'healthy' if healthy_checks == total_checks else 'degraded'
        results['health_percentage'] = (healthy_checks / total_checks) * 100
        
        return results

# Usage
health_checker = SystemHealthChecker()

# Add system resource checks
health_checker.add_check('cpu', lambda: psutil.cpu_percent() < 80)
health_checker.add_check('memory', lambda: psutil.virtual_memory().percent < 85)
health_checker.add_check('disk', lambda: psutil.disk_usage('/').percent < 90)

# Add API health checks
health_checker.add_check('api', lambda: requests.get('http://localhost:8000/health').status_code == 200)

# Run checks
health_results = health_checker.run_checks()
print(f"System health: {health_results['overall_status']} ({health_results['health_percentage']:.1f}%)")
```

### Database Diagnostic Tool

```python
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

class DatabaseDiagnostic:
    """Database diagnostic and optimization tool."""
    
    def __init__(self, connection_params):
        self.connection_params = connection_params
    
    def run_diagnostics(self):
        """Run comprehensive database diagnostics."""
        diagnostics = {
            'timestamp': datetime.now().isoformat(),
            'connection': {},
            'performance': {},
            'schema': {},
            'indexes': {}
        }
        
        try:
            # Test connection
            with psycopg2.connect(**self.connection_params) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    
                    # Connection diagnostics
                    diagnostics['connection'] = self._check_connection(conn)
                    
                    # Performance diagnostics
                    diagnostics['performance'] = self._check_performance(cursor)
                    
                    # Schema diagnostics
                    diagnostics['schema'] = self._check_schema(cursor)
                    
                    # Index diagnostics
                    diagnostics['indexes'] = self._check_indexes(cursor)
                    
        except Exception as e:
            diagnostics['error'] = str(e)
        
        return diagnostics
    
