"""
Configuration Management for Cache MCP Server

This module handles configuration loading, validation, and management for the
intelligent caching system. It supports environment variables, YAML files,
and programmatic configuration.

Author: KiloCode
License: Apache 2.0
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

# Import Vault client for secret management
try:
    from src.vault_client import get_secret
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False
    logging.warning("Vault client not available, using environment variables only")

logger = logging.getLogger(__name__)


class CacheBackend(Enum):
    """Supported cache backends."""
    PGVECTOR = "pgvector"
    SQLITE_VEC = "sqlite_vec"
    FAISS = "faiss"
    MEMORY = "memory"
    REDIS = "redis"


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    host: str = "localhost"
    port: int = 5432
    database: str = "cache_db"
    username: str = "postgres"
    password: str = "password"
    ssl_mode: str = "prefer"
    connection_pool_size: int = 10
    connection_timeout: int = 30
    max_overflow: int = 20


@dataclass
class EmbeddingConfig:
    """Embedding model configuration."""
    model_name: str = "all-MiniLM-L6-v2"
    dimension: int = 384
    batch_size: int = 32
    device: str = "cpu"
    similarity_threshold: float = 0.7
    max_similarity: float = 0.95


@dataclass
class PredictiveCacheConfig:
    """Predictive cache configuration."""
    enabled: bool = True
    prediction_window_seconds: int = 300  # 5 minutes
    max_predictions: int = 10
    confidence_threshold: float = 0.8
    model_path: Optional[str] = None
    training_data_path: Optional[str] = None
    cache_ttl_seconds: int = 60  # 1 minute


@dataclass
class SemanticCacheConfig:
    """Semantic cache configuration."""
    enabled: bool = True
    max_entries: int = 10000
    similarity_threshold: float = 0.85
    hash_algorithm: str = "sha256"
    compression_enabled: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour


@dataclass
class VectorCacheConfig:
    """Vector cache configuration."""
    enabled: bool = True
    max_entries: int = 50000
    similarity_threshold: float = 0.75
    reranking_enabled: bool = True
    reranking_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    cache_ttl_seconds: int = 1800  # 30 minutes


@dataclass
class GlobalCacheConfig:
    """Global knowledge cache configuration."""
    enabled: bool = True
    rag_server_url: str = "http://localhost:8000"
    rag_server_timeout: int = 30
    fallback_enabled: bool = True
    max_fallback_entries: int = 1000
    cache_ttl_seconds: int = 7200  # 2 hours


@dataclass
class VectorDiaryConfig:
    """Vector diary configuration."""
    enabled: bool = True
    max_entries: int = 100000
    retention_days: int = 30
    compression_enabled: bool = True
    auto_consolidate: bool = True
    consolidation_interval_hours: int = 24
    cache_ttl_seconds: int = 86400  # 24 hours


@dataclass
class PerformanceConfig:
    """Performance optimization configuration."""
    enable_metrics: bool = True
    metrics_interval_seconds: int = 60
    enable_profiling: bool = False
    profiling_interval_seconds: int = 300
    cache_invalidation_enabled: bool = True
    cleanup_interval_seconds: int = 3600
    max_concurrent_operations: int = 100
    request_timeout_seconds: int = 30


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size_mb: int = 10
    backup_count: int = 5
    enable_access_logs: bool = True
    enable_performance_logs: bool = True


@dataclass
class MCPConfig:
    """MCP server configuration."""
    host: str = "0.0.0.0"
    port: int = 8001
    max_connections: int = 100
    request_timeout: int = 30
    enable_ssl: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    auth_enabled: bool = False
    api_key: Optional[str] = None


@dataclass
class CacheConfig:
    """
    Main configuration class for the cache MCP server.
    
    This class aggregates all configuration settings for the five-layer
    caching architecture and provides validation and defaults.
    """
    
    # Core settings
    cache_backend: CacheBackend = CacheBackend.PGVECTOR
    environment: str = "development"
    debug: bool = False
    
    # Database configuration
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    
    # Embedding configuration
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    
    # Cache layer configurations
    predictive_cache: PredictiveCacheConfig = field(default_factory=PredictiveCacheConfig)
    semantic_cache: SemanticCacheConfig = field(default_factory=SemanticCacheConfig)
    vector_cache: VectorCacheConfig = field(default_factory=VectorCacheConfig)
    global_cache: GlobalCacheConfig = field(default_factory=GlobalCacheConfig)
    vector_diary: VectorDiaryConfig = field(default_factory=VectorDiaryConfig)
    
    # Performance and monitoring
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)
    
    # Paths
    data_dir: str = "./data"
    config_file_path: Optional[str] = None
    log_dir: str = "./logs"
    
    def __post_init__(self):
        """Post-initialization setup."""
        # Ensure directories exist
        self._ensure_directories()
        
        # Load configuration from file if specified
        if self.config_file_path:
            self.load_from_file(self.config_file_path)
        
        # Override with environment variables
        self.load_from_env()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        for path in [self.data_dir, self.log_dir]:
            Path(path).mkdir(parents=True, exist_ok=True)
    
    def load_from_file(self, config_path: str):
        """
        Load configuration from a YAML file.
        
        Args:
            config_path: Path to the configuration file
        """
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            if config_data:
                self._update_from_dict(config_data)
            
            logger.info(f"Configuration loaded from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            raise
    
    def load_from_env(self):
        """
        Load configuration from environment variables and Vault.
        
        Environment variables take precedence over file configuration.
        """
        # Database configuration
        # Try Vault first, then environment variables
        if VAULT_AVAILABLE:
            try:
                db_creds = get_secret("secret/data/cache/database")
                if db_creds:
                    self.database.host = db_creds.get("host", self.database.host)
                    self.database.port = db_creds.get("port", self.database.port)
                    self.database.database = db_creds.get("database", self.database.database)
                    self.database.username = db_creds.get("username", self.database.username)
                    self.database.password = db_creds.get("password", self.database.password)
                    logging.info("Database configuration loaded from Vault")
                else:
                    logging.warning("Vault database credentials not found, using environment variables")
            except Exception as e:
                logging.warning(f"Failed to load database credentials from Vault: {e}")
        
        # Override with environment variables if provided
        if os.getenv('CACHE_DB_HOST'):
            self.database.host = os.getenv('CACHE_DB_HOST') or self.database.host
        if os.getenv('CACHE_DB_PORT'):
            self.database.port = int(os.getenv('CACHE_DB_PORT') or self.database.port)
        if os.getenv('CACHE_DB_NAME'):
            self.database.database = os.getenv('CACHE_DB_NAME') or self.database.database
        if os.getenv('CACHE_DB_USER'):
            self.database.username = os.getenv('CACHE_DB_USER') or self.database.username
        if os.getenv('CACHE_DB_PASSWORD'):
            self.database.password = os.getenv('CACHE_DB_PASSWORD') or self.database.password
        
        # Cache backend
        if os.getenv('CACHE_BACKEND'):
            try:
                self.cache_backend = CacheBackend(os.getenv('CACHE_BACKEND'))
            except ValueError:
                logger.warning(f"Invalid cache backend: {os.getenv('CACHE_BACKEND')}")
        
        # Embedding configuration
        if os.getenv('EMBEDDING_MODEL'):
            self.embedding.model_name = os.getenv('EMBEDDING_MODEL') or self.embedding.model_name
        if os.getenv('EMBEDDING_DIMENSION'):
            self.embedding.dimension = int(os.getenv('EMBEDDING_DIMENSION') or self.embedding.dimension)
        
        # MCP configuration
        # Try Vault first for API key, then environment variables
        if VAULT_AVAILABLE:
            try:
                mcp_creds = get_secret("secret/data/mcp/cache-server")
                if mcp_creds and mcp_creds.get("api_key"):
                    self.mcp.api_key = mcp_creds["api_key"]
                    self.mcp.auth_enabled = True
                    logging.info("MCP API key loaded from Vault")
            except Exception as e:
                logging.warning(f"Failed to load MCP API key from Vault: {e}")
        
        # Override with environment variables if provided
        if os.getenv('MCP_HOST'):
            self.mcp.host = os.getenv('MCP_HOST') or self.mcp.host
        if os.getenv('MCP_PORT'):
            self.mcp.port = int(os.getenv('MCP_PORT') or self.mcp.port)
        if os.getenv('MCP_API_KEY'):
            self.mcp.api_key = os.getenv('MCP_API_KEY')
            self.mcp.auth_enabled = True
        
        # Logging configuration
        if os.getenv('LOG_LEVEL'):
            self.logging.level = os.getenv('LOG_LEVEL') or self.logging.level
        if os.getenv('LOG_FILE'):
            self.logging.file_path = os.getenv('LOG_FILE') or self.logging.file_path
        
        logger.info("Configuration loaded from environment variables")
    
    def _update_from_dict(self, config_data: Dict[str, Any]):
        """
        Update configuration from a dictionary.
        
        Args:
            config_data: Configuration dictionary
        """
        for section, values in config_data.items():
            if hasattr(self, section):
                section_obj = getattr(self, section)
                if isinstance(section_obj, dict):
                    section_obj.update(values)
                elif hasattr(section_obj, '__dict__'):
                    for key, value in values.items():
                        if hasattr(section_obj, key):
                            setattr(section_obj, key, value)
    
    def save_to_file(self, config_path: str):
        """
        Save configuration to a YAML file.
        
        Args:
            config_path: Path to save the configuration file
        """
        try:
            config_dict = self.to_dict()
            with open(config_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration saved to {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {config_path}: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Configuration dictionary
        """
        config_dict = {}
        
        # Add all sections
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                if hasattr(value, 'to_dict'):
                    config_dict[key] = value.to_dict()
                elif hasattr(value, '__dict__'):
                    config_dict[key] = {k: v for k, v in value.__dict__.items() if not k.startswith('_')}
                else:
                    config_dict[key] = value
        
        return config_dict
    
    def validate(self) -> List[str]:
        """
        Validate configuration settings.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate database configuration
        if not self.database.host:
            errors.append("Database host is required")
        if self.database.port <= 0 or self.database.port > 65535:
            errors.append("Database port must be between 1 and 65535")
        
        # Validate embedding configuration
        if self.embedding.dimension <= 0:
            errors.append("Embedding dimension must be positive")
        if not (0.0 <= self.embedding.similarity_threshold <= 1.0):
            errors.append("Similarity threshold must be between 0.0 and 1.0")
        
        # Validate cache configurations
        for cache_name, cache_config in [
            ('predictive_cache', self.predictive_cache),
            ('semantic_cache', self.semantic_cache),
            ('vector_cache', self.vector_cache),
            ('global_cache', self.global_cache),
            ('vector_diary', self.vector_diary)
        ]:
            if cache_config.max_entries <= 0:
                errors.append(f"{cache_name} max_entries must be positive")
            if cache_config.cache_ttl_seconds < 0:
                errors.append(f"{cache_name} cache_ttl_seconds must be non-negative")
        
        # Validate MCP configuration
        if not (0 <= self.mcp.port <= 65535):
            errors.append("MCP port must be between 0 and 65535")
        
        return errors
    
    def get_cache_config(self, layer_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific cache layer.
        
        Args:
            layer_name: Name of the cache layer
            
        Returns:
            Configuration dictionary for the layer
        """
        layer_configs = {
            'predictive': self.predictive_cache,
            'semantic': self.semantic_cache,
            'vector': self.vector_cache,
            'global': self.global_cache,
            'vector_diary': self.vector_diary
        }
        
        if layer_name in layer_configs:
            return layer_configs[layer_name].__dict__
        
        raise ValueError(f"Unknown cache layer: {layer_name}")


def load_config(config_path: Optional[str] = None) -> CacheConfig:
    """
    Load configuration from file or create default.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        CacheConfig instance
    """
    if config_path and os.path.exists(config_path):
        config = CacheConfig(config_file_path=config_path)
    else:
        config = CacheConfig()
    
    # Validate configuration
    errors = config.validate()
    if errors:
        logger.error(f"Configuration validation failed: {errors}")
        raise ValueError(f"Invalid configuration: {errors}")
    
    return config


def create_default_config_file(path: str):
    """
    Create a default configuration file.
    
    Args:
        path: Path to create the configuration file
    """
    config = CacheConfig()
    config.save_to_file(path)
    logger.info(f"Default configuration file created at {path}")