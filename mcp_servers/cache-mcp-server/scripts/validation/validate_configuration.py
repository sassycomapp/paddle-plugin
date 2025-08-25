#!/usr/bin/env python3
"""
Configuration Validation Script for Cache MCP Server

This script validates all configuration aspects of the cache MCP server including:
- Configuration file syntax and structure
- Environment variables
- Database connectivity
- External service integration
- Security settings
- Performance settings

Author: KiloCode
License: Apache 2.0
"""

import os
import sys
import logging
import asyncio
import json
import yaml
import aiohttp
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
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
class ValidationResult:
    """Result of configuration validation."""
    is_valid: bool = True
    errors: List[str] = None
    warnings: List[str] = None
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.recommendations is None:
            self.recommendations = []


class ConfigurationValidator:
    """Validates cache MCP server configuration."""
    
    def __init__(self):
        """Initialize validator."""
        self.project_root = Path(__file__).parent.parent.parent
        self.logger = logging.getLogger(__name__)
        self.session = None
        
        # Configuration paths
        self.config_paths = {
            "main": self.project_root / "config" / "cache_config.yaml",
            "env": self.project_root / ".env",
            "kilocode": self.project_root / ".kilocode" / "config" / "cache_integration.yaml",
            "docker": self.project_root / "docker-compose.yml"
        }
        
        # Required configuration sections
        self.required_sections = [
            "global", "predictive_cache", "semantic_cache", 
            "vector_cache", "global_cache", "vector_diary",
            "database", "mcp", "monitoring"
        ]
        
        # Required environment variables
        self.required_env_vars = [
            "CACHE_DB_HOST", "CACHE_DB_PORT", "CACHE_DB_NAME",
            "CACHE_DB_USER", "CACHE_DB_PASSWORD", "MCP_HOST", "MCP_PORT"
        ]
        
        # Required database tables
        self.required_tables = [
            "predictive_cache", "semantic_cache", "vector_cache", "vector_diary"
        ]
    
    async def initialize(self):
        """Initialize the validator."""
        try:
            self.logger.info("Initializing configuration validator...")
            
            # Create aiohttp session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
            
            self.logger.info("Configuration validator initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize configuration validator: {e}")
            raise
    
    async def close(self):
        """Close the validator."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def validate_all(self) -> ValidationResult:
        """Run all validation checks."""
        try:
            self.logger.info("Running comprehensive configuration validation...")
            
            result = ValidationResult()
            
            # Validate configuration files
            await self._validate_configuration_files(result)
            
            # Validate environment variables
            await self._validate_environment_variables(result)
            
            # Validate database configuration
            await self._validate_database_configuration(result)
            
            # Validate external service integration
            await self._validate_external_service_integration(result)
            
            # Validate security settings
            await self._validate_security_settings(result)
            
            # Validate performance settings
            await self._validate_performance_settings(result)
            
            # Validate deployment configuration
            await self._validate_deployment_configuration(result)
            
            # Generate recommendations
            await self._generate_recommendations(result)
            
            # Set overall validity
            result.is_valid = len(result.errors) == 0
            
            self.logger.info(f"Configuration validation completed: {result.is_valid}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            result.errors.append(f"Validation failed: {str(e)}")
            result.is_valid = False
            return result
    
    async def _validate_configuration_files(self, result: ValidationResult):
        """Validate configuration files."""
        try:
            self.logger.info("Validating configuration files...")
            
            # Validate main configuration file
            main_config = self.config_paths["main"]
            if main_config.exists():
                try:
                    with open(main_config, 'r') as f:
                        config_data = yaml.safe_load(f)
                    
                    # Check required sections
                    for section in self.required_sections:
                        if section not in config_data:
                            result.errors.append(f"Missing required section in main config: {section}")
                        elif not isinstance(config_data[section], dict):
                            result.errors.append(f"Section {section} in main config is not a dictionary")
                    
                    # Validate database configuration
                    if "database" in config_data:
                        db_config = config_data["database"]
                        if "host" not in db_config or not db_config["host"]:
                            result.errors.append("Database host is required")
                        if "port" not in db_config or not isinstance(db_config["port"], int):
                            result.errors.append("Database port must be an integer")
                        if "name" not in db_config or not db_config["name"]:
                            result.errors.append("Database name is required")
                    
                    # Validate MCP configuration
                    if "mcp" in config_data:
                        mcp_config = config_data["mcp"]
                        if "host" not in mcp_config or not mcp_config["host"]:
                            result.errors.append("MCP host is required")
                        if "port" not in mcp_config or not isinstance(mcp_config["port"], int):
                            result.errors.append("MCP port must be an integer")
                    
                    self.logger.info("Main configuration file validated successfully")
                    
                except yaml.YAMLError as e:
                    result.errors.append(f"Invalid YAML in main configuration: {e}")
                except Exception as e:
                    result.errors.append(f"Error reading main configuration: {e}")
            else:
                result.errors.append(f"Main configuration file not found: {main_config}")
            
            # Validate environment file
            env_file = self.config_paths["env"]
            if env_file.exists():
                try:
                    with open(env_file, 'r') as f:
                        env_content = f.read()
                    
                    # Check for required environment variables
                    for var in self.required_env_vars:
                        if f"{var}=" not in env_content:
                            result.warnings.append(f"Recommended environment variable not set: {var}")
                    
                    self.logger.info("Environment file validated successfully")
                    
                except Exception as e:
                    result.errors.append(f"Error reading environment file: {e}")
            else:
                result.warnings.append(f"Environment file not found: {env_file}")
            
            # Validate KiloCode integration configuration
            kilocode_config = self.config_paths["kilocode"]
            if kilocode_config.exists():
                try:
                    with open(kilocode_config, 'r') as f:
                        config_data = yaml.safe_load(f)
                    
                    # Check required sections
                    if "cache_integration" not in config_data:
                        result.warnings.append("Missing cache_integration section in KiloCode config")
                    
                    self.logger.info("KiloCode integration configuration validated successfully")
                    
                except Exception as e:
                    result.errors.append(f"Error reading KiloCode configuration: {e}")
            
            # Validate Docker configuration
            docker_config = self.config_paths["docker"]
            if docker_config.exists():
                try:
                    with open(docker_config, 'r') as f:
                        config_data = yaml.safe_load(f)
                    
                    # Check required services
                    if "services" not in config_data:
                        result.errors.append("Missing services section in Docker configuration")
                    
                    # Check for cache-mcp-server service
                    if "cache-mcp-server" not in config_data.get("services", {}):
                        result.warnings.append("cache-mcp-server service not found in Docker configuration")
                    
                    self.logger.info("Docker configuration validated successfully")
                    
                except Exception as e:
                    result.errors.append(f"Error reading Docker configuration: {e}")
            
        except Exception as e:
            self.logger.error(f"Configuration files validation failed: {e}")
            result.errors.append(f"Configuration files validation failed: {e}")
    
    async def _validate_environment_variables(self, result: ValidationResult):
        """Validate environment variables."""
        try:
            self.logger.info("Validating environment variables...")
            
            # Check required environment variables
            for var in self.required_env_vars:
                value = os.getenv(var)
                if not value:
                    result.errors.append(f"Required environment variable not set: {var}")
                elif var.endswith("_PORT") and not value.isdigit():
                    result.errors.append(f"Environment variable {var} must be a number")
            
            # Validate database URL
            db_url = os.getenv("DATABASE_URL")
            if db_url:
                if not db_url.startswith(("postgresql://", "sqlite://")):
                    result.errors.append("DATABASE_URL must start with postgresql:// or sqlite://")
            
            # Validate MCP settings
            mcp_host = os.getenv("MCP_HOST")
            mcp_port = os.getenv("MCP_PORT")
            
            if mcp_host and not mcp_host.replace(".", "").isdigit():
                result.warnings.append("MCP_HOST should be a valid hostname or IP address")
            
            if mcp_port and not mcp_port.isdigit():
                result.errors.append("MCP_PORT must be a number")
            
            # Validate cache settings
            cache_backend = os.getenv("CACHE_BACKEND")
            if cache_backend and cache_backend not in ["pgvector", "sqlite_vec", "faiss", "memory", "redis"]:
                result.warnings.append(f"Unknown cache backend: {cache_backend}")
            
            self.logger.info("Environment variables validation completed")
            
        except Exception as e:
            self.logger.error(f"Environment variables validation failed: {e}")
            result.errors.append(f"Environment variables validation failed: {e}")
    
    async def _validate_database_configuration(self, result: ValidationResult):
        """Validate database configuration."""
        try:
            self.logger.info("Validating database configuration...")
            
            # Get database configuration
            db_host = os.getenv("CACHE_DB_HOST", "localhost")
            db_port = int(os.getenv("CACHE_DB_PORT", "5432"))
            db_name = os.getenv("CACHE_DB_NAME", "paddle_plugin_cache")
            db_user = os.getenv("CACHE_DB_USER", "postgres")
            db_password = os.getenv("CACHE_DB_PASSWORD", "2001")
            
            # Test database connectivity
            try:
                import asyncpg
                
                conn = await asyncpg.connect(
                    host=db_host,
                    port=db_port,
                    user=db_user,
                    password=db_password,
                    database=db_name
                )
                
                # Check database tables
                tables = await conn.fetch("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                """)
                
                table_names = [table['table_name'] for table in tables]
                missing_tables = set(self.required_tables) - set(table_names)
                
                if missing_tables:
                    result.errors.append(f"Missing database tables: {missing_tables}")
                
                # Check database performance
                try:
                    stats = await conn.fetch("""
                        SELECT 
                            COUNT(*) as total_entries,
                            COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at < NOW() THEN 1 END) as expired_entries,
                            COUNT(CASE WHEN expires_at IS NULL OR expires_at >= NOW() THEN 1 END) as active_entries
                        FROM predictive_cache
                    """)
                    
                    if stats and stats[0]['total_entries'] > 10000:
                        result.warnings.append("Database has many entries, consider cleanup")
                
                except Exception as e:
                    result.warnings.append(f"Could not check database performance: {e}")
                
                await conn.close()
                
            except ImportError:
                result.warnings.append("asyncpg not installed, skipping database connectivity test")
            except Exception as e:
                result.errors.append(f"Database connectivity test failed: {e}")
            
            # Validate persistence directory
            persist_dir = os.getenv("CACHE_PERSIST_DIR", "./cache_storage")
            persist_path = Path(persist_dir)
            
            if not persist_path.exists():
                try:
                    persist_path.mkdir(parents=True, exist_ok=True)
                    result.warnings.append(f"Created persistence directory: {persist_dir}")
                except Exception as e:
                    result.errors.append(f"Could not create persistence directory: {e}")
            
            self.logger.info("Database configuration validation completed")
            
        except Exception as e:
            self.logger.error(f"Database configuration validation failed: {e}")
            result.errors.append(f"Database configuration validation failed: {e}")
    
    async def _validate_external_service_integration(self, result: ValidationResult):
        """Validate external service integration."""
        try:
            self.logger.info("Validating external service integration...")
            
            # Check MCP RAG Server
            rag_endpoint = os.getenv("MCP_RAG_SERVER_ENDPOINT", "http://localhost:8001")
            if rag_endpoint:
                try:
                    async with self.session.get(f"{rag_endpoint}/health", timeout=5) as response:
                        if response.status == 200:
                            self.logger.info("MCP RAG Server is accessible")
                        else:
                            result.warnings.append(f"MCP RAG Server health check failed: {response.status}")
                except Exception as e:
                    result.warnings.append(f"MCP RAG Server not accessible: {e}")
            
            # Check Vector Store MCP
            vector_endpoint = os.getenv("VECTOR_STORE_MCP_ENDPOINT", "http://localhost:8002")
            if vector_endpoint:
                try:
                    async with self.session.get(f"{vector_endpoint}/health", timeout=5) as response:
                        if response.status == 200:
                            self.logger.info("Vector Store MCP is accessible")
                        else:
                            result.warnings.append(f"Vector Store MCP health check failed: {response.status}")
                except Exception as e:
                    result.warnings.append(f"Vector Store MCP not accessible: {e}")
            
            # Check KiloCode Orchestration
            kilocode_endpoint = os.getenv("KILOCODE_ENDPOINT", "http://localhost:8080")
            if kilocode_endpoint:
                try:
                    async with self.session.get(f"{kilocode_endpoint}/health", timeout=5) as response:
                        if response.status == 200:
                            self.logger.info("KiloCode Orchestration is accessible")
                        else:
                            result.warnings.append(f"KiloCode Orchestration health check failed: {response.status}")
                except Exception as e:
                    result.warnings.append(f"KiloCode Orchestration not accessible: {e}")
            
            # Check Memory Bank
            memory_bank_path = os.getenv("MEMORY_BANK_PATH", "./memorybank")
            memory_bank = Path(memory_bank_path)
            
            if not memory_bank.exists():
                try:
                    memory_bank.mkdir(parents=True, exist_ok=True)
                    result.warnings.append(f"Created memory bank directory: {memory_bank_path}")
                except Exception as e:
                    result.warnings.append(f"Could not create memory bank directory: {e}")
            
            self.logger.info("External service integration validation completed")
            
        except Exception as e:
            self.logger.error(f"External service integration validation failed: {e}")
            result.errors.append(f"External service integration validation failed: {e}")
    
    async def _validate_security_settings(self, result: ValidationResult):
        """Validate security settings."""
        try:
            self.logger.info("Validating security settings...")
            
            # Check authentication settings
            mcp_auth_enabled = os.getenv("MCP_AUTH_ENABLED", "false").lower() == "true"
            mcp_api_key = os.getenv("MCP_API_KEY")
            
            if mcp_auth_enabled and not mcp_api_key:
                result.errors.append("MCP authentication enabled but no API key provided")
            
            # Check rate limiting settings
            rate_limiting_enabled = os.getenv("RATE_LIMITING_ENABLED", "true").lower() == "true"
            rate_limit_rpm = os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "100")
            
            if rate_limiting_enabled and not rate_limit_rpm.isdigit():
                result.errors.append("RATE_LIMIT_REQUESTS_PER_MINUTE must be a number")
            
            # Check SSL settings
            mcp_ssl_enabled = os.getenv("MCP_SSL_ENABLED", "false").lower() == "true"
            mcp_ssl_cert = os.getenv("MCP_SSL_CERT_PATH")
            mcp_ssl_key = os.getenv("MCP_SSL_KEY_PATH")
            
            if mcp_ssl_enabled and (not mcp_ssl_cert or not mcp_ssl_key):
                result.errors.append("SSL enabled but certificate or key path not provided")
            
            # Check input validation settings
            input_validation_enabled = os.getenv("INPUT_VALIDATION_ENABLED", "true").lower() == "true"
            max_key_length = os.getenv("MAX_KEY_LENGTH", "255")
            max_value_size = os.getenv("MAX_VALUE_SIZE", "10485760")
            
            if input_validation_enabled:
                if not max_key_length.isdigit():
                    result.errors.append("MAX_KEY_LENGTH must be a number")
                if not max_value_size.isdigit():
                    result.errors.append("MAX_VALUE_SIZE must be a number")
            
            self.logger.info("Security settings validation completed")
            
        except Exception as e:
            self.logger.error(f"Security settings validation failed: {e}")
            result.errors.append(f"Security settings validation failed: {e}")
    
    async def _validate_performance_settings(self, result: ValidationResult):
        """Validate performance settings."""
        try:
            self.logger.info("Validating performance settings...")
            
            # Check performance settings
            max_concurrent_requests = os.getenv("MAX_CONCURRENT_REQUESTS", "100")
            request_timeout = os.getenv("REQUEST_TIMEOUT", "30")
            enable_metrics = os.getenv("ENABLE_METRICS", "true").lower() == "true"
            
            if not max_concurrent_requests.isdigit():
                result.errors.append("MAX_CONCURRENT_REQUESTS must be a number")
            
            if not request_timeout.isdigit():
                result.errors.append("REQUEST_TIMEOUT must be a number")
            
            # Check cache settings
            predictive_cache_ttl = os.getenv("PREDICTIVE_CACHE_TTL", "3600")
            semantic_cache_ttl = os.getenv("SEMANTIC_CACHE_TTL", "86400")
            vector_cache_ttl = os.getenv("VECTOR_CACHE_TTL", "7200")
            global_cache_ttl = os.getenv("GLOBAL_CACHE_TTL", "86400")
            vector_diary_ttl = os.getenv("VECTOR_DIARY_TTL", "2592000")
            
            for ttl_var, ttl_value in [
                ("PREDICTIVE_CACHE_TTL", predictive_cache_ttl),
                ("SEMANTIC_CACHE_TTL", semantic_cache_ttl),
                ("VECTOR_CACHE_TTL", vector_cache_ttl),
                ("GLOBAL_CACHE_TTL", global_cache_ttl),
                ("VECTOR_DIARY_TTL", vector_diary_ttl)
            ]:
                if not ttl_value.isdigit():
                    result.errors.append(f"{ttl_var} must be a number")
            
            # Check cache size settings
            predictive_cache_max_size = os.getenv("PREDICTIVE_CACHE_MAX_SIZE", "1000")
            semantic_cache_max_size = os.getenv("SEMANTIC_CACHE_MAX_SIZE", "5000")
            vector_cache_max_size = os.getenv("VECTOR_CACHE_MAX_SIZE", "2000")
            global_cache_max_size = os.getenv("GLOBAL_CACHE_MAX_SIZE", "5000")
            vector_diary_max_size = os.getenv("VECTOR_DIARY_MAX_SIZE", "10000")
            
            for size_var, size_value in [
                ("PREDICTIVE_CACHE_MAX_SIZE", predictive_cache_max_size),
                ("SEMANTIC_CACHE_MAX_SIZE", semantic_cache_max_size),
                ("VECTOR_CACHE_MAX_SIZE", vector_cache_max_size),
                ("GLOBAL_CACHE_MAX_SIZE", global_cache_max_size),
                ("VECTOR_DIARY_MAX_SIZE", vector_diary_max_size)
            ]:
                if not size_value.isdigit():
                    result.errors.append(f"{size_var} must be a number")
            
            # Check similarity thresholds
            semantic_cache_similarity = os.getenv("SEMANTIC_CACHE_SIMILARITY_THRESHOLD", "0.8")
            vector_cache_similarity = os.getenv("VECTOR_CACHE_SIMILARITY_THRESHOLD", "0.75")
            
            for sim_var, sim_value in [
                ("SEMANTIC_CACHE_SIMILARITY_THRESHOLD", semantic_cache_similarity),
                ("VECTOR_CACHE_SIMILARITY_THRESHOLD", vector_cache_similarity)
            ]:
                try:
                    sim_float = float(sim_value)
                    if not (0.0 <= sim_float <= 1.0):
                        result.errors.append(f"{sim_var} must be between 0.0 and 1.0")
                except ValueError:
                    result.errors.append(f"{sim_var} must be a number")
            
            self.logger.info("Performance settings validation completed")
            
        except Exception as e:
            self.logger.error(f"Performance settings validation failed: {e}")
            result.errors.append(f"Performance settings validation failed: {e}")
    
    async def _validate_deployment_configuration(self, result: ValidationResult):
        """Validate deployment configuration."""
        try:
            self.logger.info("Validating deployment configuration...")
            
            # Check Docker configuration
            dockerfile_path = self.project_root / "Dockerfile"
            if dockerfile_path.exists():
                try:
                    with open(dockerfile_path, 'r') as f:
                        dockerfile_content = f.read()
                    
                    # Check for required Dockerfile instructions
                    required_instructions = ["FROM", "WORKDIR", "COPY", "EXPOSE", "CMD"]
                    for instruction in required_instructions:
                        if instruction not in dockerfile_content:
                            result.warnings.append(f"Missing Dockerfile instruction: {instruction}")
                    
                    self.logger.info("Dockerfile validation completed")
                    
                except Exception as e:
                    result.errors.append(f"Error reading Dockerfile: {e}")
            else:
                result.warnings.append("Dockerfile not found")
            
            # Check docker-compose configuration
            docker_compose_path = self.project_root / "docker-compose.yml"
            if docker_compose_path.exists():
                try:
                    with open(docker_compose_path, 'r') as f:
                        compose_data = yaml.safe_load(f)
                    
                    # Check for required services
                    required_services = ["cache-mcp-server", "postgres"]
                    for service in required_services:
                        if service not in compose_data.get("services", {}):
                            result.warnings.append(f"Missing service in docker-compose: {service}")
                    
                    self.logger.info("Docker Compose validation completed")
                    
                except Exception as e:
                    result.errors.append(f"Error reading docker-compose.yml: {e}")
            
            # Check deployment scripts
            deploy_scripts_dir = self.project_root / "scripts" / "deploy"
            if deploy_scripts_dir.exists():
                deploy_scripts = list(deploy_scripts_dir.glob("*.py"))
                if not deploy_scripts:
                    result.warnings.append("No deployment scripts found")
            
            self.logger.info("Deployment configuration validation completed")
            
        except Exception as e:
            self.logger.error(f"Deployment configuration validation failed: {e}")
            result.errors.append(f"Deployment configuration validation failed: {e}")
    
    async def _generate_recommendations(self, result: ValidationResult):
        """Generate recommendations based on validation results."""
        try:
            self.logger.info("Generating recommendations...")
            
            # General recommendations
            if len(result.errors) > 0:
                result.recommendations.append("Fix all errors before deploying the cache MCP server")
            
            if len(result.warnings) > 0:
                result.recommendations.append("Address warnings to improve system reliability")
            
            # Specific recommendations based on common issues
            if not os.getenv("DATABASE_URL"):
                result.recommendations.append("Set DATABASE_URL environment variable for database connectivity")
            
            if not os.getenv("MCP_API_KEY"):
                result.recommendations.append("Set MCP_API_KEY for secure authentication")
            
            if not os.getenv("CACHE_BACKEND"):
                result.recommendations.append("Set CACHE_BACKEND to specify the cache backend (pgvector recommended)")
            
            if not os.getenv("EMBEDDING_MODEL"):
                result.recommendations.append("Set EMBEDDING_MODEL for semantic and vector caching")
            
            # Performance recommendations
            if os.getenv("MAX_CONCURRENT_REQUESTS", "100") == "100":
                result.recommendations.append("Consider adjusting MAX_CONCURRENT_REQUESTS based on expected load")
            
            if os.getenv("REQUEST_TIMEOUT", "30") == "30":
                result.recommendations.append("Consider adjusting REQUEST_TIMEOUT based on expected response times")
            
            # Security recommendations
            if os.getenv("MCP_AUTH_ENABLED", "false").lower() == "false":
                result.recommendations.append("Enable MCP authentication for production deployment")
            
            if os.getenv("MCP_SSL_ENABLED", "false").lower() == "false":
                result.recommendations.append("Enable SSL for production deployment")
            
            # Monitoring recommendations
            if os.getenv("ENABLE_METRICS", "true").lower() == "false":
                result.recommendations.append("Enable metrics for monitoring and debugging")
            
            # Backup recommendations
            if os.getenv("BACKUP_ENABLED", "true").lower() == "false":
                result.recommendations.append("Enable backups for data protection")
            
            self.logger.info("Recommendations generated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to generate recommendations: {e}")
            result.errors.append(f"Failed to generate recommendations: {e}")


async def main():
    """Main entry point for configuration validation."""
    try:
        # Initialize validator
        validator = ConfigurationValidator()
        
        # Initialize
        await validator.initialize()
        
        # Run validation
        result = await validator.validate_all()
        
        # Print results
        print("\n" + "="*60)
        print("CACHE MCP SERVER CONFIGURATION VALIDATION REPORT")
        print("="*60)
        print(f"Validation Result: {'PASSED' if result.is_valid else 'FAILED'}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        if result.errors:
            print(f"\nERRORS ({len(result.errors)}):")
            for error in result.errors:
                print(f"  ❌ {error}")
        
        if result.warnings:
            print(f"\nWARNINGS ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"  ⚠️  {warning}")
        
        if result.recommendations:
            print(f"\nRECOMMENDATIONS ({len(result.recommendations)}):")
            for rec in result.recommendations:
                print(f"  💡 {rec}")
        
        if not result.errors:
            print(f"\n✅ Configuration validation PASSED!")
            print("The cache MCP server is ready for deployment.")
        else:
            print(f"\n❌ Configuration validation FAILED!")
            print("Please fix all errors before deploying.")
        
        print("="*60)
        
        # Close validator
        await validator.close()
        
        # Exit with appropriate code
        sys.exit(0 if result.is_valid else 1)
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        print(f"Configuration validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())