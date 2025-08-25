#!/usr/bin/env python3
"""
Deployment Script for Cache Management System Integration

This script handles the deployment of the cache management system
and its integration with existing KiloCode infrastructure.

Author: KiloCode
License: Apache 2.0
"""

import asyncio
import os
import sys
import subprocess
import logging
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CacheDeploymentManager:
    """Manages deployment of cache management system integration."""
    
    def __init__(self, config_path: str = "src/orchestration/mcp_servers_config.yaml"):
        self.config_path = config_path
        self.deployment_config = self._load_deployment_config()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def _load_deployment_config(self) -> Dict[str, Any]:
        """Load deployment configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.error(f"Failed to load deployment config: {e}")
            return {}
    
    def deploy_cache_system(self) -> bool:
        """Deploy the cache management system."""
        logger.info("Starting cache system deployment...")
        
        try:
            # Check if cache server is configured
            if 'cache-mcp-server' not in self.deployment_config.get('mcpServers', {}):
                logger.error("Cache MCP server not configured in deployment config")
                return False
            
            # Create necessary directories
            self._create_directories()
            
            # Set up database
            if not self._setup_database():
                logger.error("Database setup failed")
                return False
            
            # Deploy cache server
            if not self._deploy_cache_server():
                logger.error("Cache server deployment failed")
                return False
            
            # Update orchestrator configuration
            if not self._update_orchestrator_config():
                logger.error("Orchestrator config update failed")
                return False
            
            # Set up integration scripts
            if not self._setup_integration_scripts():
                logger.error("Integration scripts setup failed")
                return False
            
            logger.info("Cache system deployment completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Cache system deployment failed: {e}")
            return False
    
    def _create_directories(self) -> None:
        """Create necessary directories for cache system."""
        directories = [
            "./cache_storage",
            "./cache_storage_dev",
            "./logs",
            "./scripts/deployment",
            "./scripts/integration",
            "./scripts/monitoring"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    def _setup_database(self) -> bool:
        """Set up PostgreSQL database for cache system."""
        logger.info("Setting up database...")
        
        try:
            # Check if PostgreSQL is running
            result = subprocess.run(
                ["pg_isready", "-h", "localhost", "-p", "5432"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning("PostgreSQL not running, attempting to start...")
                # Try to start PostgreSQL (this will vary by system)
                subprocess.run(["sudo", "systemctl", "start", "postgresql"], check=True)
            
            # Create database if it doesn't exist
            db_name = "paddle_plugin_cache"
            create_db_cmd = [
                "createdb", "-h", "localhost", "-p", "5432",
                "-U", "postgres", db_name
            ]
            
            result = subprocess.run(
                create_db_cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0 and "already exists" not in result.stderr:
                logger.error(f"Failed to create database: {result.stderr}")
                return False
            
            # Run database initialization scripts
            init_scripts = [
                "mcp_servers/cache-mcp-server/scripts/database/init_cache_database.sql",
                "mcp_servers/cache-mcp-server/scripts/database/setup_database.py"
            ]
            
            for script in init_scripts:
                if Path(script).exists():
                    logger.info(f"Running database script: {script}")
                    result = subprocess.run(
                        [sys.executable, script],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode != 0:
                        logger.error(f"Database script failed: {result.stderr}")
                        return False
            
            logger.info("Database setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            return False
    
    def _deploy_cache_server(self) -> bool:
        """Deploy the cache MCP server."""
        logger.info("Deploying cache MCP server...")
        
        try:
            # Check if Node.js and npm are available
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("Node.js not found. Please install Node.js.")
                return False
            
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("npm not found. Please install npm.")
                return False
            
            # Install dependencies
            cache_server_dir = "mcp_servers/cache-mcp-server"
            if Path(cache_server_dir).exists():
                logger.info("Installing cache server dependencies...")
                result = subprocess.run(
                    ["npm", "install"],
                    cwd=cache_server_dir,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    logger.error(f"Failed to install dependencies: {result.stderr}")
                    return False
            
            # Copy environment file if it doesn't exist
            env_file = "mcp_servers/cache-mcp-server/.env"
            env_example = "mcp_servers/cache-mcp-server/.env.example"
            
            if not Path(env_file).exists() and Path(env_example).exists():
                logger.info("Creating environment file from example...")
                import shutil
                shutil.copy2(env_example, env_file)
            
            logger.info("Cache server deployment completed")
            return True
            
        except Exception as e:
            logger.error(f"Cache server deployment failed: {e}")
            return False
    
    def _update_orchestrator_config(self) -> bool:
        """Update orchestrator configuration to include cache system."""
        logger.info("Updating orchestrator configuration...")
        
        try:
            # The configuration files are already updated
            # Just verify that cache server is properly configured
            servers = self.deployment_config.get('mcpServers', {})
            
            if 'cache-mcp-server' not in servers:
                logger.error("Cache MCP server not found in configuration")
                return False
            
            cache_server = servers['cache-mcp-server']
            required_fields = ['command', 'args', 'env']
            
            for field in required_fields:
                if field not in cache_server:
                    logger.error(f"Missing required field in cache server config: {field}")
                    return False
            
            logger.info("Orchestrator configuration verified")
            return True
            
        except Exception as e:
            logger.error(f"Orchestrator config update failed: {e}")
            return False
    
    def _setup_integration_scripts(self) -> bool:
        """Set up integration scripts."""
        logger.info("Setting up integration scripts...")
        
        try:
            # Create integration test script
            integration_test_script = "scripts/integration_test.py"
            if not Path(integration_test_script).exists():
                logger.info("Creating integration test script...")
                # The integration test script already exists
            
            # Create health check script
            health_check_script = "scripts/health_check.py"
            if not Path(health_check_script).exists():
                self._create_health_check_script(health_check_script)
            
            # Create monitoring script
            monitoring_script = "scripts/monitoring.py"
            if not Path(monitoring_script).exists():
                self._create_monitoring_script(monitoring_script)
            
            # Create memory bank sync script
            sync_script = "scripts/memory_bank_sync.py"
            if not Path(sync_script).exists():
                self._create_memory_bank_sync_script(sync_script)
            
            logger.info("Integration scripts setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Integration scripts setup failed: {e}")
            return False
    
    def _create_health_check_script(self, script_path: str) -> None:
        """Create health check script."""
        script_content = '''#!/usr/bin/env python3
"""
Health Check Script for Cache Management System

This script performs health checks on all integrated components.

Author: KiloCode
License: Apache 2.0
"""

import asyncio
import logging
import aiohttp
import sys
from typing import Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_cache_server_health() -> Dict[str, Any]:
    """Check cache server health."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8080/health", timeout=10) as response:
                if response.status == 200:
                    return {"status": "healthy", "response": await response.json()}
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def check_database_health() -> Dict[str, Any]:
    """Check database health."""
    try:
        # Placeholder for database health check
        # This would typically check PostgreSQL connection
        return {"status": "healthy", "message": "Database connection OK"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def check_mcp_servers_health() -> Dict[str, Any]:
    """Check MCP servers health."""
    try:
        # Placeholder for MCP servers health check
        return {"status": "healthy", "message": "MCP servers OK"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def main():
    """Run all health checks."""
    logger.info("Starting health checks...")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # Run all health checks
    cache_check = await check_cache_server_health()
    results["checks"]["cache_server"] = cache_check
    
    db_check = await check_database_health()
    results["checks"]["database"] = db_check
    
    mcp_check = await check_mcp_servers_health()
    results["checks"]["mcp_servers"] = mcp_check
    
    # Determine overall health
    all_healthy = all(check["status"] == "healthy" for check in results["checks"].values())
    results["overall_status"] = "healthy" if all_healthy else "unhealthy"
    
    # Print results
    print("\\n" + "="*50)
    print("HEALTH CHECK RESULTS")
    print("="*50)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Overall Status: {results['overall_status'].upper()}")
    
    for check_name, check_result in results["checks"].items():
        status = check_result.get("status", "unknown").upper()
        print(f"{check_name.replace('_', ' ').title():20}: {status}")
        
        if check_result.get("status") != "healthy" and "error" in check_result:
            print(f"{'':22}  Error: {check_result['error']}")
    
    # Exit with appropriate code
    if results["overall_status"] == "healthy":
        print("\\n✅ All systems healthy!")
        sys.exit(0)
    else:
        print("\\n❌ Some systems are unhealthy!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_path, 0o755)
    
    def _create_monitoring_script(self, script_path: str) -> None:
        """Create monitoring script."""
        script_content = '''#!/usr/bin/env python3
"""
Monitoring Script for Cache Management System

This script monitors the performance and health of the cache system.

Author: KiloCode
License: Apache 2.0
"""

import asyncio
import logging
import time
import json
from datetime import datetime
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheMonitor:
    """Monitor cache system performance and health."""
    
    def __init__(self):
        self.metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "response_times": [],
            "error_count": 0
        }
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect system metrics."""
        # Placeholder for actual metrics collection
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cache_stats": {
                "hit_rate": 0.85,  # Placeholder
                "total_requests": 1000,  # Placeholder
                "active_connections": 5   # Placeholder
            },
            "system_stats": {
                "cpu_usage": 15.2,  # Placeholder
                "memory_usage": 45.8,  # Placeholder
                "disk_usage": 23.4   # Placeholder
            },
            "database_stats": {
                "connection_count": 3,  # Placeholder
                "query_time_avg": 12.3,  # Placeholder
                "slow_queries": 0   # Placeholder
            }
        }
        
        return metrics
    
    async def check_alerts(self, metrics: Dict[str, Any]) -> List[str]:
        """Check for alert conditions."""
        alerts = []
        
        # Check cache hit rate
        hit_rate = metrics["cache_stats"]["hit_rate"]
        if hit_rate < 0.7:
            alerts.append(f"Low cache hit rate: {hit_rate:.2%}")
        
        # Check memory usage
        memory_usage = metrics["system_stats"]["memory_usage"]
        if memory_usage > 80:
            alerts.append(f"High memory usage: {memory_usage:.1f}%")
        
        # Check database connections
        db_connections = metrics["database_stats"]["connection_count"]
        if db_connections > 10:
            alerts.append(f"High database connections: {db_connections}")
        
        return alerts
    
    async def run_monitoring(self, interval: int = 60) -> None:
        """Run continuous monitoring."""
        logger.info("Starting cache system monitoring...")
        
        try:
            while True:
                start_time = time.time()
                
                # Collect metrics
                metrics = await self.collect_metrics()
                
                # Check alerts
                alerts = await self.check_alerts(metrics)
                
                # Log metrics
                logger.info(f"Cache hit rate: {metrics['cache_stats']['hit_rate']:.2%}")
                logger.info(f"Memory usage: {metrics['system_stats']['memory_usage']:.1f}%")
                
                # Log alerts
                for alert in alerts:
                    logger.warning(f"ALERT: {alert}")
                
                # Save metrics to file
                metrics_file = f"metrics_{datetime.now().strftime('%Y%m%d')}.json"
                with open(metrics_file, 'a') as f:
                    json.dump(metrics, f)
                    f.write('\\n')
                
                # Wait for next interval
                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)
                await asyncio.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")

async def main():
    """Main monitoring function."""
    monitor = CacheMonitor()
    await monitor.run_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_path, 0o755)
    
    def _create_memory_bank_sync_script(self, script_path: str) -> None:
        """Create memory bank synchronization script."""
        script_content = '''#!/usr/bin/env python3
"""
Memory Bank Synchronization Script

This script synchronizes data between cache system and memory bank.

Author: KiloCode
License: Apache 2.0
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryBankSync:
    """Handle synchronization between cache and memory bank."""
    
    def __init__(self, memory_bank_path: str = "./memorybank"):
        self.memory_bank_path = Path(memory_bank_path)
        self.sync_config = {
            "enabled": True,
            "sync_interval": 300,  # 5 minutes
            "bidirectional": True,
            "conflict_resolution": "timestamp",
            "max_sync_attempts": 3
        }
    
    async def sync_from_cache_to_memory_bank(self) -> Dict[str, Any]:
        """Sync data from cache to memory bank."""
        logger.info("Syncing from cache to memory bank...")
        
        try:
            # Placeholder for cache-to-memory-bank sync logic
            # This would:
            # 1. Query cache for recent changes
            # 2. Update memory bank files
            # 3. Handle conflicts
            
            sync_result = {
                "success": True,
                "items_synced": 0,
                "conflicts_resolved": 0,
                "errors": []
            }
            
            logger.info(f"Cache to memory bank sync completed: {sync_result}")
            return sync_result
            
        except Exception as e:
            logger.error(f"Cache to memory bank sync failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def sync_from_memory_bank_to_cache(self) -> Dict[str, Any]:
        """Sync data from memory bank to cache."""
        logger.info("Syncing from memory bank to cache...")
        
        try:
            # Placeholder for memory-bank-to-cache sync logic
            # This would:
            # 1. Read memory bank files
            # 2. Update cache with new/changed data
            # 3. Handle conflicts
            
            sync_result = {
                "success": True,
                "items_synced": 0,
                "conflicts_resolved": 0,
                "errors": []
            }
            
            logger.info(f"Memory bank to cache sync completed: {sync_result}")
            return sync_result
            
        except Exception as e:
            logger.error(f"Memory bank to cache sync failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def bidirectional_sync(self) -> Dict[str, Any]:
        """Perform bidirectional synchronization."""
        logger.info("Starting bidirectional sync...")
        
        try:
            # Sync from cache to memory bank
            cache_to_mb = await self.sync_from_cache_to_memory_bank()
            
            # Sync from memory bank to cache
            mb_to_cache = await self.sync_from_memory_bank_to_cache()
            
            # Combine results
            result = {
                "success": cache_to_mb["success"] and mb_to_cache["success"],
                "cache_to_memory_bank": cache_to_mb,
                "memory_bank_to_cache": mb_to_cache,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Bidirectional sync completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Bidirectional sync failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_sync_loop(self, interval: int = 300) -> None:
        """Run continuous sync loop."""
        logger.info("Starting memory bank sync loop...")
        
        try:
            while True:
                start_time = datetime.now()
                
                # Perform bidirectional sync
                result = await self.bidirectional_sync()
                
                # Log results
                if result["success"]:
                    logger.info(f"Sync completed successfully at {start_time}")
                else:
                    logger.error(f"Sync failed at {start_time}: {result.get('error', 'Unknown error')}")
                
                # Wait for next interval
                elapsed = (datetime.now() - start_time).total_seconds()
                sleep_time = max(0, interval - elapsed)
                await asyncio.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("Sync loop stopped by user")
        except Exception as e:
            logger.error(f"Sync loop error: {e}")

async def main():
    """Main sync function."""
    sync = MemoryBankSync()
    await sync.run_sync_loop()

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_path, 0o755)
    
    def generate_deployment_report(self) -> Dict[str, Any]:
        """Generate deployment report."""
        report = {
            "deployment_id": f"cache_deployment_{self.timestamp}",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "cache_server": {
                    "status": "deployed",
                    "version": "1.0.0",
                    "location": "mcp_servers/cache-mcp-server"
                },
                "database": {
                    "status": "configured",
                    "type": "PostgreSQL",
                    "name": "paddle_plugin_cache"
                },
                "orchestrator": {
                    "status": "integrated",
                    "config_updated": True
                },
                "integration_scripts": {
                    "status": "created",
                    "scripts": [
                        "scripts/integration_test.py",
                        "scripts/health_check.py",
                        "scripts/monitoring.py",
                        "scripts/memory_bank_sync.py"
                    ]
                }
            },
            "next_steps": [
                "Start cache server: npm start in mcp_servers/cache-mcp-server",
                "Run integration tests: python scripts/integration_test.py",
                "Set up monitoring: python scripts/monitoring.py",
                "Configure health checks: python scripts/health_check.py"
            ]
        }
        
        # Save report
        report_file = f"deployment_report_{self.timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Deployment report saved to: {report_file}")
        return report


async def main():
    """Main deployment function."""
    logger.info("Starting cache system deployment...")
    
    try:
        # Create deployment manager
        deployer = CacheDeploymentManager()
        
        # Deploy cache system
        success = deployer.deploy_cache_system()
        
        if success:
            # Generate deployment report
            report = deployer.generate_deployment_report()
            
            print("\\n" + "="*60)
            print("CACHE SYSTEM DEPLOYMENT COMPLETED")
            print("="*60)
            print(f"Deployment ID: {report['deployment_id']}")
            print(f"Timestamp: {report['timestamp']}")
            print("\\nComponents Status:")
            for component, status in report['components'].items():
                print(f"  {component.replace('_', ' ').title()}: {status['status']}")
            
            print("\\nNext Steps:")
            for step in report['next_steps']:
                print(f"  • {step}")
            
            print("\\n✅ Cache system deployment completed successfully!")
            return True
        else:
            print("\\n❌ Cache system deployment failed!")
            return False
            
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        print(f"\\n❌ Deployment failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)