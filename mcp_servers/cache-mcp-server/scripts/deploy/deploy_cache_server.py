#!/usr/bin/env python3
"""
Deployment Script for Cache MCP Server

This script handles the complete deployment of the cache MCP server including:
- Environment setup
- Database initialization
- Configuration validation
- Service deployment
- Integration testing
- Health checks

Author: KiloCode
License: Apache 2.0
"""

import os
import sys
import logging
import asyncio
import json
import yaml
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DeploymentConfig:
    """Configuration for deployment."""
    # Environment
    environment: str = "production"
    debug: bool = False
    
    # Database settings
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "paddle_plugin_cache"
    db_user: str = "postgres"
    db_password: str = "2001"
    
    # Cache server settings
    cache_host: str = "0.0.0.0"
    cache_port: int = 8080
    cache_workers: int = 4
    
    # External services
    rag_server_endpoint: str = "http://localhost:8001"
    vector_store_endpoint: str = "http://localhost:8002"
    kilocode_endpoint: str = "http://localhost:8080"
    
    # Deployment settings
    create_directories: bool = True
    validate_config: bool = True
    run_tests: bool = True
    run_health_check: bool = True
    start_service: bool = True
    
    # Backup settings
    backup_before_deploy: bool = True
    backup_after_deploy: bool = True
    
    # Monitoring settings
    enable_monitoring: bool = True
    monitoring_port: int = 9090


class CacheServerDeployer:
    """Handles deployment of the cache MCP server."""
    
    def __init__(self, config: DeploymentConfig):
        """Initialize deployer."""
        self.config = config
        self.project_root = Path(__file__).parent.parent.parent
        self.logger = logging.getLogger(__name__)
        self.session = None
        
        # Deployment paths
        self.paths = {
            "config": self.project_root / "config",
            "scripts": self.project_root / "scripts",
            "src": self.project_root / "src",
            "logs": self.project_root / "logs",
            "data": self.project_root / "data",
            "cache": self.project_root / "cache_storage",
            "backups": self.project_root / "backups",
            "docker": self.project_root / "docker",
            "docs": self.project_root / "docs"
        }
        
        # Deployment state
        self.deployment_state = {
            "start_time": None,
            "end_time": None,
            "steps_completed": [],
            "errors": [],
            "warnings": [],
            "backup_created": False,
            "config_validated": False,
            "database_initialized": False,
            "service_started": False,
            "health_check_passed": False
        }
    
    async def initialize(self):
        """Initialize the deployer."""
        try:
            self.logger.info("Initializing cache server deployer...")
            
            # Create aiohttp session
            import aiohttp
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            # Set start time
            self.deployment_state["start_time"] = datetime.now()
            
            self.logger.info("Cache server deployer initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize cache server deployer: {e}")
            raise
    
    async def close(self):
        """Close the deployer."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def deploy(self):
        """Run the complete deployment process."""
        try:
            self.logger.info("Starting cache MCP server deployment...")
            
            # Create backup if requested
            if self.config.backup_before_deploy:
                await self._create_backup()
            
            # Create required directories
            if self.config.create_directories:
                await self._create_directories()
            
            # Validate configuration
            if self.config.validate_config:
                await self._validate_configuration()
            
            # Initialize database
            await self._initialize_database()
            
            # Run tests
            if self.config.run_tests:
                await self._run_tests()
            
            # Start service
            if self.config.start_service:
                await self._start_service()
            
            # Run health check
            if self.config.run_health_check:
                await self._run_health_check()
            
            # Create backup after deployment
            if self.config.backup_after_deploy:
                await self._create_backup()
            
            # Set end time
            self.deployment_state["end_time"] = datetime.now()
            
            # Generate deployment report
            await self._generate_deployment_report()
            
            self.logger.info("Cache MCP server deployment completed successfully!")
            
        except Exception as e:
            self.logger.error(f"Deployment failed: {e}")
            self.deployment_state["errors"].append(str(e))
            raise
        finally:
            await self.close()
    
    async def _create_backup(self):
        """Create backup of current deployment."""
        try:
            self.logger.info("Creating backup...")
            
            backup_dir = self.paths["backups"]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"backup_{timestamp}"
            
            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup configuration files
            config_files = [
                self.project_root / "config" / "cache_config.yaml",
                self.project_root / ".env",
                self.project_root / "docker-compose.yml"
            ]
            
            for config_file in config_files:
                if config_file.exists():
                    shutil.copy2(config_file, backup_path / config_file.name)
            
            # Backup database if possible
            try:
                import asyncpg
                conn = await asyncpg.connect(
                    host=self.config.db_host,
                    port=self.config.db_port,
                    user=self.config.db_user,
                    password=self.config.db_password,
                    database=self.config.db_name
                )
                
                # Export database schema
                schema = await conn.fetch("SELECT * FROM information_schema.tables")
                with open(backup_path / "schema.json", 'w') as f:
                    json.dump([dict(row) for row in schema], f, indent=2)
                
                # Export data from each table
                for table in ["predictive_cache", "semantic_cache", "vector_cache", "vector_diary"]:
                    data = await conn.fetch(f"SELECT * FROM {table}")
                    if data:
                        with open(backup_path / f"{table}.json", 'w') as f:
                            json.dump([dict(row) for row in data], f, indent=2)
                
                await conn.close()
                
            except Exception as e:
                self.logger.warning(f"Could not backup database: {e}")
            
            self.deployment_state["backup_created"] = True
            self.logger.info(f"Backup created at: {backup_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            self.deployment_state["warnings"].append(f"Backup failed: {e}")
    
    async def _create_directories(self):
        """Create required directories."""
        try:
            self.logger.info("Creating required directories...")
            
            for name, path in self.paths.items():
                if name in ["logs", "data", "cache", "backups"]:
                    path.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"Created directory: {path}")
            
            # Set appropriate permissions
            for path in self.paths.values():
                if path.exists():
                    path.chmod(0o755)
            
            self.deployment_state["directories_created"] = True
            self.logger.info("Directories created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create directories: {e}")
            raise
    
    async def _validate_configuration(self):
        """Validate configuration."""
        try:
            self.logger.info("Validating configuration...")
            
            # Import and run configuration validation
            from scripts.validation.validate_configuration import ConfigurationValidator
            
            validator = ConfigurationValidator()
            await validator.initialize()
            
            try:
                result = await validator.validate_all()
                
                if not result.is_valid:
                    self.deployment_state["errors"].extend(result.errors)
                    raise Exception(f"Configuration validation failed: {result.errors}")
                
                self.deployment_state["config_validated"] = True
                self.logger.info("Configuration validation passed")
                
            finally:
                await validator.close()
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            self.deployment_state["errors"].append(f"Configuration validation failed: {e}")
            raise
    
    async def _initialize_database(self):
        """Initialize database."""
        try:
            self.logger.info("Initializing database...")
            
            # Import database initialization script
            from scripts.database.init_database import DatabaseInitializer
            
            db_init = DatabaseInitializer(
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password
            )
            
            await db_init.initialize()
            
            self.deployment_state["database_initialized"] = True
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            self.deployment_state["errors"].append(f"Database initialization failed: {e}")
            raise
    
    async def _run_tests(self):
        """Run tests."""
        try:
            self.logger.info("Running tests...")
            
            # Run unit tests
            test_result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/", 
                "-v", "--tb=short"
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if test_result.returncode != 0:
                self.logger.warning(f"Unit tests failed: {test_result.stderr}")
                self.deployment_state["warnings"].append(f"Unit tests failed: {test_result.stderr}")
            else:
                self.logger.info("Unit tests passed")
            
            # Run integration tests
            integration_result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/integration/", 
                "-v", "--tb=short"
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if integration_result.returncode != 0:
                self.logger.warning(f"Integration tests failed: {integration_result.stderr}")
                self.deployment_state["warnings"].append(f"Integration tests failed: {integration_result.stderr}")
            else:
                self.logger.info("Integration tests passed")
            
            self.deployment_state["tests_passed"] = True
            self.logger.info("Tests completed")
            
        except Exception as e:
            self.logger.error(f"Tests failed: {e}")
            self.deployment_state["warnings"].append(f"Tests failed: {e}")
    
    async def _start_service(self):
        """Start the cache MCP server service."""
        try:
            self.logger.info("Starting cache MCP server...")
            
            # Check if service is already running
            try:
                import psutil
                for proc in psutil.process_iter(['pid', 'name']):
                    if 'python' in proc.info['name'] and 'cache-mcp-server' in ' '.join(proc.info.get('cmdline', [])):
                        self.logger.warning("Cache MCP server is already running")
                        self.deployment_state["service_started"] = True
                        return
            except:
                pass
            
            # Start the service
            cmd = [
                sys.executable, "-m", "uvicorn",
                "src.mcp.server:app",
                "--host", self.config.cache_host,
                "--port", str(self.config.cache_port),
                "--workers", str(self.config.cache_workers),
                "--log-level", "info"
            ]
            
            # Start the service in background
            process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for service to start
            import time
            time.sleep(5)
            
            # Check if service is running
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                self.logger.error(f"Service failed to start: {stderr}")
                self.deployment_state["errors"].append(f"Service failed to start: {stderr}")
                raise Exception(f"Service failed to start: {stderr}")
            
            self.deployment_state["service_started"] = True
            self.logger.info("Cache MCP server started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start service: {e}")
            self.deployment_state["errors"].append(f"Failed to start service: {e}")
            raise
    
    async def _run_health_check(self):
        """Run health check."""
        try:
            self.logger.info("Running health check...")
            
            # Import and run health check
            from scripts.monitoring.health_check import HealthChecker
            
            health_config = HealthCheckConfig(
                db_host=self.config.db_host,
                db_port=self.config.db_port,
                db_name=self.config.db_name,
                db_user=self.config.db_user,
                db_password=self.config.db_password,
                cache_server_host=self.config.cache_host,
                cache_server_port=self.config.cache_port,
                rag_server_endpoint=self.config.rag_server_endpoint,
                vector_store_endpoint=self.config.vector_store_endpoint,
                kilocode_endpoint=self.config.kilocode_endpoint
            )
            
            health_checker = HealthChecker(health_config)
            await health_checker.initialize()
            
            try:
                health_report = await health_checker.get_health_report()
                
                if health_report["health_status"]["overall"] != "healthy":
                    self.logger.warning(f"Health check failed: {health_report['health_status']['overall']}")
                    self.deployment_state["warnings"].extend(health_report["health_status"]["overall"])
                else:
                    self.deployment_state["health_check_passed"] = True
                    self.logger.info("Health check passed")
                
            finally:
                await health_checker.close()
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            self.deployment_state["warnings"].append(f"Health check failed: {e}")
    
    async def _generate_deployment_report(self):
        """Generate deployment report."""
        try:
            self.logger.info("Generating deployment report...")
            
            # Calculate deployment duration
            start_time = self.deployment_state["start_time"]
            end_time = self.deployment_state["end_time"]
            duration = end_time - start_time if end_time and start_time else None
            
            # Generate report
            report = {
                "deployment_timestamp": datetime.now().isoformat(),
                "environment": self.config.environment,
                "duration_seconds": duration.total_seconds() if duration else None,
                "steps_completed": self.deployment_state["steps_completed"],
                "errors": self.deployment_state["errors"],
                "warnings": self.deployment_state["warnings"],
                "backup_created": self.deployment_state["backup_created"],
                "config_validated": self.deployment_state["config_validated"],
                "database_initialized": self.deployment_state["database_initialized"],
                "service_started": self.deployment_state["service_started"],
                "health_check_passed": self.deployment_state["health_check_passed"],
                "deployment_successful": len(self.deployment_state["errors"]) == 0
            }
            
            # Save report
            report_path = self.paths["backups"] / f"deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"Deployment report saved to: {report_path}")
            
            # Print summary
            print("\n" + "="*60)
            print("CACHE MCP SERVER DEPLOYMENT SUMMARY")
            print("="*60)
            print(f"Environment: {self.config.environment}")
            print(f"Duration: {duration.total_seconds():.2f} seconds" if duration else "Duration: Unknown")
            print(f"Backup Created: {'Yes' if self.deployment_state['backup_created'] else 'No'}")
            print(f"Config Validated: {'Yes' if self.deployment_state['config_validated'] else 'No'}")
            print(f"Database Initialized: {'Yes' if self.deployment_state['database_initialized'] else 'No'}")
            print(f"Service Started: {'Yes' if self.deployment_state['service_started'] else 'No'}")
            print(f"Health Check Passed: {'Yes' if self.deployment_state['health_check_passed'] else 'No'}")
            
            if self.deployment_state["errors"]:
                print(f"\nErrors ({len(self.deployment_state['errors'])}):")
                for error in self.deployment_state["errors"]:
                    print(f"  ❌ {error}")
            
            if self.deployment_state["warnings"]:
                print(f"\nWarnings ({len(self.deployment_state['warnings'])}):")
                for warning in self.deployment_state["warnings"]:
                    print(f"  ⚠️  {warning}")
            
            print(f"\nDeployment Status: {'SUCCESS' if not self.deployment_state['errors'] else 'FAILED'}")
            print("="*60)
            
        except Exception as e:
            self.logger.error(f"Failed to generate deployment report: {e}")
            self.deployment_state["warnings"].append(f"Failed to generate deployment report: {e}")


async def main():
    """Main entry point for deployment."""
    try:
        # Parse command line arguments
        environment = "production"
        debug = False
        
        if len(sys.argv) > 1:
            environment = sys.argv[1]
        
        if len(sys.argv) > 2:
            debug = sys.argv[2].lower() == "true"
        
        # Create deployment configuration
        config = DeploymentConfig(
            environment=environment,
            debug=debug,
            db_host="localhost",
            db_port=5432,
            db_name="paddle_plugin_cache",
            db_user="postgres",
            db_password="2001",
            cache_host="0.0.0.0",
            cache_port=8080,
            cache_workers=4,
            rag_server_endpoint="http://localhost:8001",
            vector_store_endpoint="http://localhost:8002",
            kilocode_endpoint="http://localhost:8080",
            create_directories=True,
            validate_config=True,
            run_tests=True,
            run_health_check=True,
            start_service=True,
            backup_before_deploy=True,
            backup_after_deploy=True,
            enable_monitoring=True,
            monitoring_port=9090
        )
        
        # Initialize deployer
        deployer = CacheServerDeployer(config)
        
        # Initialize
        await deployer.initialize()
        
        # Run deployment
        await deployer.deploy()
        
        # Close deployer
        await deployer.close()
        
        print("\n🎉 Cache MCP server deployment completed successfully!")
        print("The cache MCP server is now running and ready for use.")
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())