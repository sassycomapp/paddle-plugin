"""
Test Configuration for Cache Management System.

This module provides configuration for testing the cache management system,
including database settings, cache configurations, and test environment setup.
"""

import os
import tempfile
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json


@dataclass
class TestDatabaseConfig:
    """Test database configuration."""
    host: str = "localhost"
    port: int = 5432
    name: str = "paddle_plugin_cache_test"
    user: str = "test_user"
    password: str = "test_password"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class TestCacheConfig:
    """Test cache configuration."""
    predictive_cache: Dict[str, Any] = None
    semantic_cache: Dict[str, Any] = None
    vector_cache: Dict[str, Any] = None
    global_cache: Dict[str, Any] = None
    vector_diary: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default configurations."""
        if self.predictive_cache is None:
            self.predictive_cache = {
                "cache_ttl_seconds": 60,  # 1 minute for testing
                "max_cache_size": 100,
                "prediction_window_seconds": 300,
                "max_predictions": 10,
                "confidence_threshold": 0.8,
                "pattern_analysis_enabled": True,
                "user_session_tracking": True
            }
        
        if self.semantic_cache is None:
            self.semantic_cache = {
                "cache_ttl_seconds": 300,  # 5 minutes for testing
                "max_cache_size": 500,
                "similarity_threshold": 0.8,
                "embedding_dimension": 384,
                "max_entries": 1000,
                "semantic_hashing_enabled": True,
                "prompt_reuse_enabled": True
            }
        
        if self.vector_cache is None:
            self.vector_cache = {
                "cache_ttl_seconds": 180,  # 3 minutes for testing
                "max_cache_size": 1000,
                "similarity_threshold": 0.75,
                "reranking_enabled": True,
                "max_entries": 5000,
                "context_selection_enabled": True,
                "embedding_model": "text-embedding-ada-002"
            }
        
        if self.global_cache is None:
            self.global_cache = {
                "cache_ttl_seconds": 600,  # 10 minutes for testing
                "max_cache_size": 2000,
                "rag_server_url": "http://localhost:8000",
                "rag_server_timeout": 30,
                "fallback_enabled": True,
                "max_fallback_entries": 1000,
                "external_service_timeout": 60
            }
        
        if self.vector_diary is None:
            self.vector_diary = {
                "cache_ttl_seconds": 86400,  # 24 hours for testing
                "max_cache_size": 5000,
                "max_entries": 1000,
                "session_management_enabled": True,
                "longitudinal_reasoning_enabled": True,
                "insight_generation_enabled": True,
                "session_timeout_seconds": 3600
            }


@dataclass
class TestMCPConfig:
    """Test MCP server configuration."""
    host: str = "localhost"
    port: int = 8081  # Different port for testing
    max_connections: int = 100
    request_timeout: int = 30
    enable_metrics: bool = True
    log_level: str = "INFO"


@dataclass
class TestPerformanceConfig:
    """Test performance configuration."""
    benchmark_duration_seconds: int = 300
    warmup_duration_seconds: int = 60
    concurrent_users: int = 50
    requests_per_user: int = 100
    measurement_interval_seconds: int = 5
    memory_monitoring_enabled: bool = True
    cpu_monitoring_enabled: bool = True
    network_monitoring_enabled: bool = True


@dataclass
class TestStressConfig:
    """Test stress configuration."""
    high_load_duration_seconds: int = 600
    concurrent_requests: int = 200
    request_rate_per_second: int = 100
    memory_limit_mb: int = 1024
    cpu_limit_percent: int = 80
    timeout_seconds: int = 10
    retry_attempts: int = 3
    circuit_breaker_enabled: bool = True


@dataclass
class TestErrorConfig:
    """Test error handling configuration."""
    error_injection_enabled: bool = True
    error_types: list = None
    error_probability: float = 0.1
    recovery_attempts: int = 3
    timeout_seconds: int = 5
    fallback_enabled: bool = True
    
    def __post_init__(self):
        """Initialize default error types."""
        if self.error_types is None:
            self.error_types = [
                "timeout",
                "connection_error",
                "memory_error",
                "storage_error",
                "corruption_error",
                "network_error",
                "permission_error"
            ]


@dataclass
class TestEnvironmentConfig:
    """Test environment configuration."""
    test_mode: bool = True
    debug_mode: bool = False
    log_level: str = "INFO"
    temp_dir: Optional[str] = None
    cleanup_temp_files: bool = True
    mock_external_services: bool = True
    enable_profiling: bool = False


class TestConfig:
    """Main test configuration class."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize test configuration."""
        self.database = TestDatabaseConfig()
        self.cache = TestCacheConfig()
        self.mcp = TestMCPConfig()
        self.performance = TestPerformanceConfig()
        self.stress = TestStressConfig()
        self.error = TestErrorConfig()
        self.environment = TestEnvironmentConfig()
        
        # Load configuration from file if provided
        if config_file:
            self.load_from_file(config_file)
        
        # Override with environment variables
        self.load_from_env()
        
        # Set up temporary directory
        if self.environment.temp_dir is None:
            self.environment.temp_dir = tempfile.mkdtemp(prefix="cache_test_")
    
    def load_from_file(self, config_file: str):
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Update database config
            if 'database' in config_data:
                self.database = TestDatabaseConfig(**config_data['database'])
            
            # Update cache config
            if 'cache' in config_data:
                self.cache = TestCacheConfig(**config_data['cache'])
            
            # Update MCP config
            if 'mcp' in config_data:
                self.mcp = TestMCPConfig(**config_data['mcp'])
            
            # Update performance config
            if 'performance' in config_data:
                self.performance = TestPerformanceConfig(**config_data['performance'])
            
            # Update stress config
            if 'stress' in config_data:
                self.stress = TestStressConfig(**config_data['stress'])
            
            # Update error config
            if 'error' in config_data:
                self.error = TestErrorConfig(**config_data['error'])
            
            # Update environment config
            if 'environment' in config_data:
                self.environment = TestEnvironmentConfig(**config_data['environment'])
                
        except Exception as e:
            print(f"Error loading configuration from {config_file}: {e}")
            raise
    
    def load_from_env(self):
        """Load configuration from environment variables."""
        # Database configuration
        if os.getenv('TEST_DB_HOST'):
            self.database.host = os.getenv('TEST_DB_HOST')
        if os.getenv('TEST_DB_PORT'):
            self.database.port = int(os.getenv('TEST_DB_PORT'))
        if os.getenv('TEST_DB_NAME'):
            self.database.name = os.getenv('TEST_DB_NAME')
        if os.getenv('TEST_DB_USER'):
            self.database.user = os.getenv('TEST_DB_USER')
        if os.getenv('TEST_DB_PASSWORD'):
            self.database.password = os.getenv('TEST_DB_PASSWORD')
        
        # Cache configuration
        if os.getenv('TEST_PREDICTIVE_CACHE_TTL'):
            self.cache.predictive_cache['cache_ttl_seconds'] = int(os.getenv('TEST_PREDICTIVE_CACHE_TTL'))
        if os.getenv('TEST_SEMANTIC_CACHE_TTL'):
            self.cache.semantic_cache['cache_ttl_seconds'] = int(os.getenv('TEST_SEMANTIC_CACHE_TTL'))
        if os.getenv('TEST_VECTOR_CACHE_TTL'):
            self.cache.vector_cache['cache_ttl_seconds'] = int(os.getenv('TEST_VECTOR_CACHE_TTL'))
        if os.getenv('TEST_GLOBAL_CACHE_TTL'):
            self.cache.global_cache['cache_ttl_seconds'] = int(os.getenv('TEST_GLOBAL_CACHE_TTL'))
        
        # MCP configuration
        if os.getenv('TEST_MCP_HOST'):
            self.mcp.host = os.getenv('TEST_MCP_HOST')
        if os.getenv('TEST_MCP_PORT'):
            self.mcp.port = int(os.getenv('TEST_MCP_PORT'))
        
        # Environment configuration
        if os.getenv('TEST_MODE'):
            self.environment.test_mode = os.getenv('TEST_MODE').lower() == 'true'
        if os.getenv('DEBUG_MODE'):
            self.environment.debug_mode = os.getenv('DEBUG_MODE').lower() == 'true'
        if os.getenv('LOG_LEVEL'):
            self.environment.log_level = os.getenv('LOG_LEVEL')
    
    def get_database_url(self) -> str:
        """Get database connection URL."""
        return f"postgresql://{self.database.user}:{self.database.password}@{self.database.host}:{self.database.port}/{self.database.name}"
    
    def get_cache_config(self, cache_layer: str) -> Dict[str, Any]:
        """Get configuration for specific cache layer."""
        if cache_layer == "predictive":
            return self.cache.predictive_cache
        elif cache_layer == "semantic":
            return self.cache.semantic_cache
        elif cache_layer == "vector":
            return self.cache.vector_cache
        elif cache_layer == "global":
            return self.cache.global_cache
        elif cache_layer == "vector_diary":
            return self.cache.vector_diary
        else:
            raise ValueError(f"Unknown cache layer: {cache_layer}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "database": asdict(self.database),
            "cache": asdict(self.cache),
            "mcp": asdict(self.mcp),
            "performance": asdict(self.performance),
            "stress": asdict(self.stress),
            "error": asdict(self.error),
            "environment": asdict(self.environment)
        }
    
    def save_to_file(self, config_file: str):
        """Save configuration to JSON file."""
        with open(config_file, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def cleanup(self):
        """Clean up temporary files and resources."""
        if self.environment.cleanup_temp_files and self.environment.temp_dir:
            try:
                import shutil
                shutil.rmtree(self.environment.temp_dir)
            except Exception as e:
                print(f"Error cleaning up temporary directory: {e}")


# Global test configuration instance
TEST_CONFIG = TestConfig()


def get_test_config() -> TestConfig:
    """Get the global test configuration instance."""
    return TEST_CONFIG


def create_test_config_file(config_file: str = "test_config.json"):
    """Create a test configuration file."""
    config = TestConfig()
    config.save_to_file(config_file)
    return config_file


if __name__ == "__main__":
    # Create test configuration file
    config_file = create_test_config_file()
    print(f"Test configuration file created: {config_file}")
    
    # Load and display configuration
    config = TestConfig(config_file)
    print("Test configuration loaded:")
    print(json.dumps(config.to_dict(), indent=2))