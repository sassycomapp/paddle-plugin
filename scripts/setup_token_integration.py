#!/usr/bin/env python3
"""
Token Integration Setup Script

This script provides comprehensive setup and configuration for the MCP and KiloCode
token management integration system. It handles database migrations, configuration
setup, dependency installation, and system initialization.

Features:
- Database migration management
- Configuration file generation
- Dependency installation and verification
- System health checks
- Integration testing
- Performance optimization setup
"""

import os
import sys
import json
import logging
import argparse
import subprocess
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('token_integration_setup.log')
    ]
)
logger = logging.getLogger(__name__)


class TokenIntegrationSetup:
    """Main setup class for token integration system."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the setup system."""
        self.config_path = config_path or "config/token_integration_config.json"
        self.config = self._load_config()
        self.setup_directories()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        default_config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "token_management",
                "user": "postgres",
                "password": "",
                "ssl_mode": "prefer"
            },
            "mcp": {
                "host": "localhost",
                "port": 8000,
                "timeout": 30,
                "max_retries": 3
            },
            "kilocode": {
                "host": "localhost",
                "port": 8080,
                "timeout": 60,
                "max_concurrent_tasks": 10
            },
            "external_apis": {
                "timeout": 30,
                "max_retries": 3,
                "rate_limit": 60
            },
            "token_limits": {
                "daily_limit": 10000,
                "monthly_limit": 300000,
                "hard_limit": 1000000
            },
            "performance": {
                "enable_caching": True,
                "cache_size": 1000,
                "batch_size": 10,
                "async_operations": True
            },
            "logging": {
                "level": "INFO",
                "file": "logs/token_integration.log",
                "max_size": "10MB",
                "backup_count": 5
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with default config
                    return {**default_config, **config}
            else:
                logger.info(f"Config file not found at {self.config_path}, using defaults")
                return default_config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return default_config
    
    def setup_directories(self):
        """Create necessary directories."""
        directories = [
            "logs",
            "config",
            "data",
            "backups",
            "temp"
        ]
        
        for directory in directories:
            dir_path = Path(directory)
            dir_path.mkdir(exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed."""
        required_packages = [
            "psycopg2-binary",
            "asyncpg",
            "fastapi",
            "uvicorn",
            "aiohttp",
            "tiktoken",
            "pg_tiktoken",
            "sqlalchemy",
            "alembic",
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "redis",
            "celery",
            "python-dotenv",
            "pydantic",
            "mcp",
            "kilocode-sdk"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"Missing packages: {', '.join(missing_packages)}")
            logger.info("Run 'pip install -r requirements.txt' to install missing packages")
            return False
        
        logger.info("All required packages are installed")
        return True
    
    def check_database_connection(self) -> bool:
        """Check database connection and create necessary tables."""
        try:
            import psycopg2
            from psycopg2 import sql
            
            # Build connection string
            db_config = self.config["database"]
            conn_string = f"dbname={db_config['name']} user={db_config['user']} host={db_config['host']} port={db_config['port']} password={db_config['password']}"
            
            # Test connection
            with psycopg2.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    # Check if database exists
                    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_config['name'],))
                    if not cursor.fetchone():
                        logger.warning(f"Database {db_config['name']} does not exist")
                        return False
                    
                    # Check if tables exist
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name IN ('token_usage', 'token_limits', 'token_revocations')
                    """)
                    existing_tables = [row[0] for row in cursor.fetchall()]
                    
                    required_tables = ['token_usage', 'token_limits', 'token_revocations']
                    missing_tables = [table for table in required_tables if table not in existing_tables]
                    
                    if missing_tables:
                        logger.warning(f"Missing tables: {', '.join(missing_tables)}")
                        return False
                    
                    logger.info("Database connection successful and tables exist")
                    return True
                    
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def run_migrations(self) -> bool:
        """Run database migrations."""
        try:
            # Check if alembic is available
            try:
                subprocess.run(["alembic", "--version"], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.error("Alembic not found. Please install it: pip install alembic")
                return False
            
            # Run migrations
            migrations_dir = Path("src/database/migrations")
            if not migrations_dir.exists():
                logger.error(f"Migrations directory not found: {migrations_dir}")
                return False
            
            # Set up alembic configuration
            env = os.environ.copy()
            env["ALEMBIC_CONFIG"] = str(migrations_dir / "alembic.ini")
            
            # Run upgrade command
            result = subprocess.run(
                ["alembic", "-c", str(migrations_dir / "alembic.ini"), "upgrade", "head"],
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("Database migrations completed successfully")
                return True
            else:
                logger.error(f"Migration failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error running migrations: {e}")
            return False
    
    def setup_configuration(self) -> bool:
        """Setup configuration files."""
        try:
            # Create config directory if it doesn't exist
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            # Save configuration
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_path}")
            
            # Create environment file
            env_content = f"""
# Token Integration Configuration
DATABASE_HOST={self.config['database']['host']}
DATABASE_PORT={self.config['database']['port']}
DATABASE_NAME={self.config['database']['name']}
DATABASE_USER={self.config['database']['user']}
DATABASE_PASSWORD={self.config['database']['password']}
DATABASE_SSL_MODE={self.config['database']['ssl_mode']}

MCP_HOST={self.config['mcp']['host']}
MCP_PORT={self.config['mcp']['port']}
MCP_TIMEOUT={self.config['mcp']['timeout']}

KILOCODE_HOST={self.config['kilocode']['host']}
KILOCODE_PORT={self.config['kilocode']['port']}
KILOCODE_TIMEOUT={self.config['kilocode']['timeout']}

LOG_LEVEL={self.config['logging']['level']}
"""
            
            env_path = Path(".env")
            with open(env_path, 'w') as f:
                f.write(env_content)
            
            logger.info(f"Environment variables saved to {env_path}")
            
            # Create requirements file
            requirements = [
                "psycopg2-binary>=2.9.0",
                "asyncpg>=0.27.0",
                "fastapi>=0.100.0",
                "uvicorn>=0.23.0",
                "aiohttp>=3.8.0",
                "tiktoken>=0.4.0",
                "pg_tiktoken>=0.1.0",
                "sqlalchemy>=2.0.0",
                "alembic>=1.11.0",
                "pytest>=7.0.0",
                "pytest-asyncio>=0.21.0",
                "pytest-cov>=4.0.0",
                "redis>=4.5.0",
                "celery>=5.3.0",
                "python-dotenv>=1.0.0",
                "pydantic>=2.0.0",
                "mcp>=1.0.0",
                "kilocode-sdk>=1.0.0"
            ]
            
            with open("requirements.txt", 'w') as f:
                f.write('\n'.join(requirements))
            
            logger.info("Requirements file created")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up configuration: {e}")
            return False
    
    def setup_logging(self) -> bool:
        """Setup logging configuration."""
        try:
            import logging.config
            
            log_config = {
                'version': 1,
                'disable_existing_loggers': False,
                'formatters': {
                    'standard': {
                        'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                    },
                },
                'handlers': {
                    'console': {
                        'level': self.config['logging']['level'],
                        'class': 'logging.StreamHandler',
                        'formatter': 'standard'
                    },
                    'file': {
                        'level': self.config['logging']['level'],
                        'class': 'logging.handlers.RotatingFileHandler',
                        'filename': self.config['logging']['file'],
                        'maxBytes': 10 * 1024 * 1024,  # 10MB
                        'backupCount': self.config['logging']['backup_count'],
                        'formatter': 'standard'
                    }
                },
                'loggers': {
                    '': {
                        'handlers': ['console', 'file'],
                        'level': self.config['logging']['level'],
                        'propagate': False
                    }
                }
            }
            
            logging.config.dictConfig(log_config)
            logger.info("Logging configuration setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up logging: {e}")
            return False
    
    def setup_cache(self) -> bool:
        """Setup caching system."""
        try:
            # Create Redis configuration
            redis_config = {
                "host": "localhost",
                "port": 6379,
                "db": 0,
                "password": None,
                "decode_responses": True,
                "socket_timeout": 5,
                "socket_connect_timeout": 5,
                "retry_on_timeout": True,
                "max_connections": 100
            }
            
            # Save Redis configuration
            with open("config/redis_config.json", 'w') as f:
                json.dump(redis_config, f, indent=2)
            
            # Create cache initialization script
            cache_script = """
#!/usr/bin/env python3
"""
            cache_script += """
import redis
import json
from pathlib import Path

def setup_cache():
    \"\"\"Setup Redis cache for token integration.\"\"\"
    config_path = Path("config/redis_config.json")
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "password": None,
            "decode_responses": True
        }
    
    try:
        r = redis.Redis(**config)
        r.ping()
        print("Redis connection successful")
        
        # Setup cache structures
        r.set("cache:token_counts", json.dumps({}))
        r.set("cache:session_tokens", json.dumps({}))
        r.set("cache:api_limits", json.dumps({}))
        
        # Set cache expiration times
        r.expire("cache:token_counts", 3600)  # 1 hour
        r.expire("cache:session_tokens", 86400)  # 24 hours
        r.expire("cache:api_limits", 300)  # 5 minutes
        
        print("Cache setup complete")
        return True
        
    except Exception as e:
        print(f"Cache setup failed: {e}")
        return False

if __name__ == "__main__":
    setup_cache()
"""
            
            with open("scripts/setup_cache.py", 'w') as f:
                f.write(cache_script)
            
            # Make script executable
            os.chmod("scripts/setup_cache.py", 0o755)
            
            logger.info("Cache setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up cache: {e}")
            return False
    
    def setup_systemd_services(self) -> bool:
        """Setup systemd services for the integration system."""
        try:
            # Create systemd service files
            services = {
                "token-integration.service": """[Unit]
Description=Token Integration Service
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=token_user
Group=token_user
WorkingDirectory=/opt/token-integration
Environment=PYTHONPATH=/opt/token-integration/src
ExecStart=/opt/token-integration/venv/bin/python -m uvicorn token_management.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
""",
                "mcp-memory-service.service": """[Unit]
Description=MCP Memory Service
After=network.target

[Service]
Type=exec
User=mcp_user
Group=mcp_user
WorkingDirectory=/opt/mcp-memory-service
Environment=PYTHONPATH=/opt/mcp-memory-service/src
ExecStart=/opt/mcp-memory-service/venv/bin/python -m mcp_memory_service.server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
""",
                "kilocode-orchestrator.service": """[Unit]
Description=KiloCode Orchestrator
After=network.target

[Service]
Type=exec
User=kilocode_user
Group=kilocode_user
WorkingDirectory=/opt/kilocode-orchestrator
Environment=PYTHONPATH=/opt/kilocode-orchestrator/src
ExecStart=/opt/kilocode-orchestrator/venv/bin/python -m kilocode.orchestrator
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
            }
            
            services_dir = Path("systemd")
            services_dir.mkdir(exist_ok=True)
            
            for service_name, service_content in services.items():
                service_path = services_dir / service_name
                with open(service_path, 'w') as f:
                    f.write(service_content)
                
                logger.info(f"Created systemd service: {service_path}")
            
            logger.info("Systemd services setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up systemd services: {e}")
            return False
    
    def run_integration_tests(self) -> bool:
        """Run integration tests."""
        try:
            # Run pytest with coverage
            result = subprocess.run([
                "python", "-m", "pytest",
                "tests/test_mcp_kilocode_integration.py",
                "-v",
                "--cov=src",
                "--cov-report=html",
                "--cov-report=term-missing"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Integration tests passed")
                return True
            else:
                logger.error(f"Integration tests failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error running integration tests: {e}")
            return False
    
    def setup_performance_optimization(self) -> bool:
        """Setup performance optimization features."""
        try:
            # Create performance optimization configuration
            perf_config = {
                "database": {
                    "pool_size": 20,
                    "max_overflow": 30,
                    "pool_timeout": 30,
                    "pool_recycle": 3600
                },
                "cache": {
                    "enable": True,
                    "type": "redis",
                    "ttl": 3600,
                    "max_size": 10000
                },
                "async": {
                    "workers": 4,
                    "queue_size": 1000,
                    "timeout": 300
                },
                "batch": {
                    "size": 10,
                    "timeout": 30,
                    "max_retries": 3
                }
            }
            
            with open("config/performance_config.json", 'w') as f:
                json.dump(perf_config, f, indent=2)
            
            # Create performance monitoring script
            perf_script = '''#!/usr/bin/env python3
import asyncio
import time
import psutil
import logging
import json
from pathlib import Path
from typing import Dict, List, Any

class PerformanceMonitor:
    """Monitor system performance for token integration."""
    
    def __init__(self, config_path: str = "config/performance_config.json"):
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load performance configuration."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return {}
    
    async def monitor_system(self):
        """Monitor system performance metrics."""
        while True:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                disk_percent = psutil.disk_usage('/').percent
                
                # Get process metrics
                process = psutil.Process()
                process_cpu = process.cpu_percent()
                process_memory = process.memory_info().rss / 1024 / 1024  # MB
                
                # Log metrics
                metrics = {
                    "timestamp": time.time(),
                    "system": {
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory_percent,
                        "disk_percent": disk_percent
                    },
                    "process": {
                        "cpu_percent": process_cpu,
                        "memory_mb": process_memory
                    }
                }
                
                self.logger.info(f"Performance metrics: {metrics}")
                
                # Check thresholds
                if cpu_percent > 80:
                    self.logger.warning(f"High CPU usage: {cpu_percent}%")
                if memory_percent > 80:
                    self.logger.warning(f"High memory usage: {memory_percent}%")
                if disk_percent > 90:
                    self.logger.warning(f"High disk usage: {disk_percent}%")
                
                # Wait for next check
                await asyncio.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Error monitoring system: {e}")
                await asyncio.sleep(60)
    
    async def start_monitoring(self):
        """Start performance monitoring."""
        self.logger.info("Starting performance monitoring")
        await self.monitor_system()

if __name__ == "__main__":
    monitor = PerformanceMonitor()
    asyncio.run(monitor.start_monitoring())
'''
            
            with open("scripts/performance_monitor.py", 'w') as f:
                f.write(perf_script)
            
            # Make script executable
            os.chmod("scripts/performance_monitor.py", 0o755)
            
            logger.info("Performance optimization setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up performance optimization: {e}")
            return False
    
    def setup_backup_system(self) -> bool:
        """Setup backup system for data and configurations."""
        try:
            # Create backup script
            backup_script = """
#!/usr/bin/env python3
"""
            backup_script += """
import os
import shutil
import tarfile
from datetime import datetime
from pathlib import Path
import logging

class BackupManager:
    \"\"\"Manage backups for token integration system.\"\"\"
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
    def create_backup(self) -> bool:
        \"\"\"Create a backup of the system.\"\"\"
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"token_integration_backup_{timestamp}"
            backup_path = self.backup_dir / backup_name
            
            # Create backup directory
            backup_path.mkdir(exist_ok=True)
            
            # Backup configuration files
            config_files = [
                "config/token_integration_config.json",
                "config/performance_config.json",
                "config/redis_config.json",
                ".env"
            ]
            
            for config_file in config_files:
                src_path = Path(config_file)
                if src_path.exists():
                    dst_path = backup_path / config_file
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_path, dst_path)
            
            # Backup database
            self._backup_database(backup_path)
            
            # Create backup archive
            archive_path = self.backup_dir / f"{backup_name}.tar.gz"
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(backup_path, arcname=backup_name)
            
            # Clean up temporary backup directory
            shutil.rmtree(backup_path)
            
            # Clean old backups (keep last 7 days)
            self._cleanup_old_backups()
            
            self.logger.info(f"Backup created: {archive_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return False
    
    def _backup_database(self, backup_path: Path):
        \"\"\"Backup database.\"\"\"
        # This is a placeholder - implement actual database backup
        # For PostgreSQL: pg_dump
        # For SQLite: SQLite backup
        pass
    
    def _cleanup_old_backups(self):
        \"\"\"Clean up old backups.\"\"\"
        try:
            # Keep backups from last 7 days
            cutoff_time = datetime.now().timestamp() - 7 * 24 * 60 * 60
            
            for backup_file in self.backup_dir.glob("token_integration_backup_*.tar.gz"):
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    self.logger.info(f"Removed old backup: {backup_file}")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up old backups: {e}")
    
    def restore_backup(self, backup_name: str) -> bool:
        \"\"\"Restore a backup.\"\"\"
        try:
            backup_path = self.backup_dir / f"{backup_name}.tar.gz"
            
            if not backup_path.exists():
                self.logger.error(f"Backup not found: {backup_path}")
                return False
            
            # Extract backup
            extract_path = self.backup_dir / "restore"
            extract_path.mkdir(exist_ok=True)
            
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(extract_path)
            
            # Restore configuration files
            restore_config_path = extract_path / backup_name
            for config_file in ["config/token_integration_config.json", "config/performance_config.json", ".env"]:
                src_path = restore_config_path / config_file
                if src_path.exists():
                    dst_path = Path(config_file)
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_path, dst_path)
            
            # Restore database
            self._restore_database(restore_config_path / backup_name)
            
            # Clean up
            shutil.rmtree(extract_path)
            
            self.logger.info(f"Backup restored: {backup_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            return False

if __name__ == "__main__":
    backup_manager = BackupManager()
    backup_manager.create_backup()
"""
            
            with open("scripts/backup_manager.py", 'w') as f:
                f.write(backup_script)
            
            # Make script executable
            os.chmod("scripts/backup_manager.py", 0o755)
            
            logger.info("Backup system setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up backup system: {e}")
            return False
    
    def setup_monitoring(self) -> bool:
        """Setup monitoring and alerting system."""
        try:
            # Create monitoring configuration
            monitoring_config = {
                "metrics": {
                    "collection_interval": 60,
                    "retention_days": 30,
                    "alert_thresholds": {
                        "cpu_usage": 80,
                        "memory_usage": 85,
                        "disk_usage": 90,
                        "response_time": 5000,
                        "error_rate": 5
                    }
                },
                "alerts": {
                    "email": {
                        "enabled": True,
                        "recipients": ["admin@example.com"],
                        "smtp_server": "localhost",
                        "smtp_port": 587
                    },
                    "webhook": {
                        "enabled": True,
                        "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
                    }
                }
            }
            
            with open("config/monitoring_config.json", 'w') as f:
                json.dump(monitoring_config, f, indent=2)
            
            # Create monitoring script
            monitoring_script = '''#!/usr/bin/env python3
import asyncio
import time
import requests
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

class MonitoringSystem:
    """Monitoring and alerting system for token integration."""
    
    def __init__(self, config_path: str = "config/monitoring_config.json"):
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load monitoring configuration."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return {}
    
    async def collect_metrics(self):
        """Collect system metrics."""
        while True:
            try:
                # Collect various metrics
                metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "system": self._get_system_metrics(),
                    "application": self._get_application_metrics(),
                    "database": self._get_database_metrics(),
                    "external_apis": self._get_external_api_metrics()
                }
                
                # Store metrics
                await self._store_metrics(metrics)
                
                # Check for alerts
                await self._check_alerts(metrics)
                
                # Wait for next collection
                await asyncio.sleep(self.config["metrics"]["collection_interval"])
                
            except Exception as e:
                self.logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(60)
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics."""
        # Implementation for system metrics
        return {
            "cpu_usage": 0,
            "memory_usage": 0,
            "disk_usage": 0
        }
    
    def _get_application_metrics(self) -> Dict[str, Any]:
        """Get application metrics."""
        # Implementation for application metrics
        return {
            "active_sessions": 0,
            "total_tokens_used": 0,
            "error_rate": 0
        }
    
    def _get_database_metrics(self) -> Dict[str, Any]:
        """Get database metrics."""
        # Implementation for database metrics
        return {
            "connection_count": 0,
            "query_time": 0,
            "cache_hit_rate": 0
        }
    
    def _get_external_api_metrics(self) -> Dict[str, Any]:
        """Get external API metrics."""
        # Implementation for external API metrics
        return {
            "api_calls": 0,
            "response_time": 0,
            "error_rate": 0
        }
    
    async def _store_metrics(self, metrics: Dict[str, Any]):
        """Store metrics in database."""
        # Implementation for storing metrics
        pass
    
    async def _check_alerts(self, metrics: Dict[str, Any]):
        """Check for alert conditions."""
        thresholds = self.config["metrics"]["alert_thresholds"]
        
        # Check system metrics
        if metrics["system"]["cpu_usage"] > thresholds["cpu_usage"]:
            await self._send_alert("High CPU usage", metrics)
        
        if metrics["system"]["memory_usage"] > thresholds["memory_usage"]:
            await self._send_alert("High memory usage", metrics)
        
        if metrics["system"]["disk_usage"] > thresholds["disk_usage"]:
            await self._send_alert("High disk usage", metrics)
        
        # Check application metrics
        if metrics["application"]["error_rate"] > thresholds["error_rate"]:
            await self._send_alert("High error rate", metrics)
    
    async def _send_alert(self, alert_type: str, metrics: Dict[str, Any]):
        """Send alert via configured channels."""
        alert_message = f"ALERT: {alert_type}\\nMetrics: {json.dumps(metrics, indent=2)}"
        
        # Send email alert
        if self.config["alerts"]["email"]["enabled"]:
            await self._send_email_alert(alert_message)
        
        # Send webhook alert
        if self.config["alerts"]["webhook"]["enabled"]:
            await self._send_webhook_alert(alert_message)
        
        self.logger.warning(f"Alert sent: {alert_type}")
    
    async def _send_email_alert(self, message: str):
        """Send email alert."""
        # Implementation for email alerts
        pass
    
    async def _send_webhook_alert(self, message: str):
        """Send webhook alert."""
        try:
            response = requests.post(
                self.config["alerts"]["webhook"]["url"],
                json={"message": message},
                timeout=10
            )
            response.raise_for_status()
        except Exception as e:
            self.logger.error(f"Error sending webhook alert: {e}")
    
    async def start_monitoring(self):
        """Start monitoring system."""
        self.logger.info("Starting monitoring system")
        await self.collect_metrics()

if __name__ == "__main__":
    monitoring_system = MonitoringSystem()
    asyncio.run(monitoring_system.start_monitoring())
'''
            
            with open("scripts/monitoring_system.py", 'w') as f:
                f.write(monitoring_script)
            
            # Make script executable
            os.chmod("scripts/monitoring_system.py", 0o755)
            
            logger.info("Monitoring system setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up monitoring system: {e}")
            return False
    
    def setup_complete(self) -> bool:
        """Setup complete system."""
        try:
            logger.info("Starting token integration setup...")
            
            # Step 1: Check dependencies
            logger.info("Step 1: Checking dependencies...")
            if not self.check_dependencies():
                logger.error("Dependency check failed")
                return False
            
            # Step 2: Setup directories
            logger.info("Step 2: Setting up directories...")
            self.setup_directories()
            
            # Step 3: Setup configuration
            logger.info("Step 3: Setting up configuration...")
            if not self.setup_configuration():
                logger.error("Configuration setup failed")
                return False
            
            # Step 4: Setup logging
            logger.info("Step 4: Setting up logging...")
            if not self.setup_logging():
                logger.error("Logging setup failed")
                return False
            
            # Step 5: Check database connection
            logger.info("Step 5: Checking database connection...")
            if not self.check_database_connection():
                logger.error("Database connection check failed")
                return False
            
            # Step 6: Run migrations
            logger.info("Step 6: Running database migrations...")
            if not self.run_migrations():
                logger.error("Database migrations failed")
                return False
            
            # Step 7: Setup cache
            logger.info("Step 7: Setting up cache...")
            if not self.setup_cache():
                logger.error("Cache setup failed")
                return False
            
            # Step 8: Setup performance optimization
            logger.info("Step 8: Setting up performance optimization...")
            if not self.setup_performance_optimization():
                logger.error("Performance optimization setup failed")
                return False
            
            # Step 9: Setup backup system
            logger.info("Step 9: Setting up backup system...")
            if not self.setup_backup_system():
                logger.error("Backup system setup failed")
                return False
            
            # Step 10: Setup monitoring
            logger.info("Step 10: Setting up monitoring...")
            if not self.setup_monitoring():
                logger.error("Monitoring setup failed")
                return False
            
            # Step 11: Setup systemd services
            logger.info("Step 11: Setting up systemd services...")
            if not self.setup_systemd_services():
                logger.error("Systemd services setup failed")
                return False
            
            # Step 12: Run integration tests
            logger.info("Step 12: Running integration tests...")
            if not self.run_integration_tests():
                logger.error("Integration tests failed")
                return False
            
            logger.info("Token integration setup completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False


def main():
    """Main entry point for the setup script."""
    parser = argparse.ArgumentParser(description="Token Integration Setup Script")
    parser.add_argument(
        "--config",
        help="Path to configuration file",
        default="config/token_integration_config.json"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip integration tests"
    )
    parser.add_argument(
        "--skip-migrations",
        action="store_true",
        help="Skip database migrations"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create setup instance
    setup = TokenIntegrationSetup(args.config)
    
    # Run setup
    success = setup.setup_complete()
    
    if success:
        print("\n" + "="*50)
        print("TOKEN INTEGRATION SETUP COMPLETED SUCCESSFULLY!")
        print("="*50)
        print("\nNext steps:")
        print("1. Review configuration files in config/")
        print("2. Start services using systemd:")
        print("   sudo systemctl start token-integration")
        print("   sudo systemctl start mcp-memory-service")
        print("   sudo systemctl start kilocode-orchestrator")
        print("3. Check logs in logs/ directory")
        print("4. Run monitoring: python scripts/monitoring_system.py")
        print("5. Create backups: python scripts/backup_manager.py")
        sys.exit(0)
    else:
        print("\n" + "="*50)
        print("TOKEN INTEGRATION SETUP FAILED!")
        print("="*50)
        print("Check logs for details: token_integration_setup.log")
        sys.exit(1)


if __name__ == "__main__":
    main()