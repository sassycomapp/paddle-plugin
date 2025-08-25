"""
Unit tests for Configuration Management.

This module contains comprehensive unit tests for the configuration management system,
testing configuration loading, validation, and environment variable handling.
"""

import pytest
import os
import tempfile
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import patch, Mock

from src.core.config import (
    CacheConfig,
    DatabaseConfig,
    EmbeddingConfig,
    PredictiveCacheConfig,
    SemanticCacheConfig,
    VectorCacheConfig,
    GlobalCacheConfig,
    VectorDiaryConfig,
    PerformanceConfig,
    LoggingConfig,
    SecurityConfig,
    load_config,
    validate_config,
    create_default_config_file
)


class TestDatabaseConfig:
    """Test DatabaseConfig functionality."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = DatabaseConfig()
        
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "cache_db"
        assert config.username == "postgres"
        assert config.password == "password"
        assert config.ssl_mode == "prefer"
        assert config.connection_pool_size == 10
        assert config.connection_timeout == 30
        assert config.max_overflow == 20
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = DatabaseConfig(
            host="db.example.com",
            port=5433,
            database="test_db",
            username="test_user",
            password="test_pass",
            ssl_mode="require",
            connection_pool_size=20,
            connection_timeout=60,
            max_overflow=30
        )
        
        assert config.host == "db.example.com"
        assert config.port == 5433
        assert config.database == "test_db"
        assert config.username == "test_user"
        assert config.password == "test_pass"
        assert config.ssl_mode == "require"
        assert config.connection_pool_size == 20
        assert config.connection_timeout == 60
        assert config.max_overflow == 30
    
    def test_config_to_dict(self):
        """Test configuration to dictionary conversion."""
        config = DatabaseConfig(
            host="db.example.com",
            port=5433,
            database="test_db"
        )
        
        config_dict = config.__dict__
        assert config_dict["host"] == "db.example.com"
        assert config_dict["port"] == 5433
        assert config_dict["database"] == "test_db"


class TestEmbeddingConfig:
    """Test EmbeddingConfig functionality."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = EmbeddingConfig()
        
        assert config.model_name == "all-MiniLM-L6-v2"
        assert config.dimension == 384
        assert config.batch_size == 32
        assert config.device == "cpu"
        assert config.similarity_threshold == 0.7
        assert config.max_similarity == 0.95
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = EmbeddingConfig(
            model_name="bert-base-uncased",
            dimension=768,
            batch_size=64,
            device="cuda",
            similarity_threshold=0.8,
            max_similarity=0.99
        )
        
        assert config.model_name == "bert-base-uncased"
        assert config.dimension == 768
        assert config.batch_size == 64
        assert config.device == "cuda"
        assert config.similarity_threshold == 0.8
        assert config.max_similarity == 0.99


class TestPredictiveCacheConfig:
    """Test PredictiveCacheConfig functionality."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = PredictiveCacheConfig()
        
        assert config.enabled is True
        assert config.prediction_window_seconds == 300
        assert config.max_predictions == 10
        assert config.confidence_threshold == 0.8
        assert config.model_path is None
        assert config.training_data_path is None
        assert config.cache_ttl_seconds == 60
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = PredictiveCacheConfig(
            enabled=False,
            prediction_window_seconds=600,
            max_predictions=20,
            confidence_threshold=0.9,
            model_path="/path/to/model",
            training_data_path="/path/to/training/data",
            cache_ttl_seconds=120
        )
        
        assert config.enabled is False
        assert config.prediction_window_seconds == 600
        assert config.max_predictions == 20
        assert config.confidence_threshold == 0.9
        assert config.model_path == "/path/to/model"
        assert config.training_data_path == "/path/to/training/data"
        assert config.cache_ttl_seconds == 120


class TestSemanticCacheConfig:
    """Test SemanticCacheConfig functionality."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SemanticCacheConfig()
        
        assert config.enabled is True
        assert config.max_entries == 10000
        assert config.similarity_threshold == 0.85
        assert config.hash_algorithm == "sha256"
        assert config.compression_enabled is True
        assert config.cache_ttl_seconds == 3600
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = SemanticCacheConfig(
            enabled=False,
            max_entries=5000,
            similarity_threshold=0.9,
            hash_algorithm="md5",
            compression_enabled=False,
            cache_ttl_seconds=1800
        )
        
        assert config.enabled is False
        assert config.max_entries == 5000
        assert config.similarity_threshold == 0.9
        assert config.hash_algorithm == "md5"
        assert config.compression_enabled is False
        assert config.cache_ttl_seconds == 1800


class TestVectorCacheConfig:
    """Test VectorCacheConfig functionality."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = VectorCacheConfig()
        
        assert config.enabled is True
        assert config.max_entries == 50000
        assert config.similarity_threshold == 0.75
        assert config.reranking_enabled is True
        assert config.reranking_model == "cross-encoder/ms-marco-MiniLM-L-6-v2"
        assert config.cache_ttl_seconds == 1800
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = VectorCacheConfig(
            enabled=False,
            max_entries=100000,
            similarity_threshold=0.8,
            reranking_enabled=False,
            reranking_model="cross-encoder/ms-marco-MiniLM-L-12-v2",
            cache_ttl_seconds=3600
        )
        
        assert config.enabled is False
        assert config.max_entries == 100000
        assert config.similarity_threshold == 0.8
        assert config.reranking_enabled is False
        assert config.reranking_model == "cross-encoder/ms-marco-MiniLM-L-12-v2"
        assert config.cache_ttl_seconds == 3600


class TestGlobalCacheConfig:
    """Test GlobalCacheConfig functionality."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = GlobalCacheConfig()
        
        assert config.enabled is True
        assert config.rag_server_url == "http://localhost:8000"
        assert config.rag_server_timeout == 30
        assert config.fallback_enabled is True
        assert config.max_fallback_entries == 1000
        assert config.cache_ttl_seconds == 7200
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = GlobalCacheConfig(
            enabled=False,
            rag_server_url="http://rag.example.com:8000",
            rag_server_timeout=60,
            fallback_enabled=False,
            max_fallback_entries=2000,
            cache_ttl_seconds=14400
        )
        
        assert config.enabled is False
        assert config.rag_server_url == "http://rag.example.com:8000"
        assert config.rag_server_timeout == 60
        assert config.fallback_enabled is False
        assert config.max_fallback_entries == 2000
        assert config.cache_ttl_seconds == 14400


class TestVectorDiaryConfig:
    """Test VectorDiaryConfig functionality."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = VectorDiaryConfig()
        
        assert config.enabled is True
        assert config.max_entries == 100000
        assert config.retention_days == 30
        assert config.compression_enabled is True
        assert config.auto_consolidate is True
        assert config.consolidation_interval_hours == 24
        assert config.cache_ttl_seconds == 86400
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = VectorDiaryConfig(
            enabled=False,
            max_entries=50000,
            retention_days=7,
            compression_enabled=False,
            auto_consolidate=False,
            consolidation_interval_hours=12,
            cache_ttl_seconds=43200
        )
        
        assert config.enabled is False
        assert config.max_entries == 50000
        assert config.retention_days == 7
        assert config.compression_enabled is False
        assert config.auto_consolidate is False
        assert config.consolidation_interval_hours == 12
        assert config.cache_ttl_seconds == 43200


class TestPerformanceConfig:
    """Test PerformanceConfig functionality."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = PerformanceConfig()
        
        assert config.enable_metrics is True
        assert config.metrics_interval_seconds == 60
        assert config.enable_profiling is False
        assert config.profiling_interval_seconds == 300
        assert config.max_concurrent_requests == 100
        assert config.request_timeout_seconds == 30
        assert config.enable_circuit_breaker is True
        assert config.circuit_breaker_threshold == 0.1
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = PerformanceConfig(
            enable_metrics=False,
            metrics_interval_seconds=120,
            enable_profiling=True,
            profiling_interval_seconds=600,
            max_concurrent_requests=200,
            request_timeout_seconds=60,
            enable_circuit_breaker=False,
            circuit_breaker_threshold=0.2
        )
        
        assert config.enable_metrics is False
        assert config.metrics_interval_seconds == 120
        assert config.enable_profiling is True
        assert config.profiling_interval_seconds == 600
        assert config.max_concurrent_requests == 200
        assert config.request_timeout_seconds == 60
        assert config.enable_circuit_breaker is False
        assert config.circuit_breaker_threshold == 0.2


class TestLoggingConfig:
    """Test LoggingConfig functionality."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = LoggingConfig()
        
        assert config.level == "INFO"
        assert config.format == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        assert config.file_path is None
        assert config.max_file_size_mb == 100
        assert config.backup_count == 5
        assert config.enable_json_logging is False
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = LoggingConfig(
            level="DEBUG",
            format="[%(levelname)s] %(asctime)s - %(name)s: %(message)s",
            file_path="/var/log/cache-server.log",
            max_file_size_mb=200,
            backup_count=10,
            enable_json_logging=True
        )
        
        assert config.level == "DEBUG"
        assert config.format == "[%(levelname)s] %(asctime)s - %(name)s: %(message)s"
        assert config.file_path == "/var/log/cache-server.log"
        assert config.max_file_size_mb == 200
        assert config.backup_count == 10
        assert config.enable_json_logging is True


class TestSecurityConfig:
    """Test SecurityConfig functionality."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SecurityConfig()
        
        assert config.enable_authentication is False
        assert config.api_key is None
        assert config.jwt_secret is None
        assert config.jwt_expiration_hours == 24
        assert config.enable_rate_limiting is True
        assert config.rate_limit_requests_per_minute == 100
        assert config.enable_ssl is False
        assert config.ssl_cert_path is None
        assert config.ssl_key_path is None
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = SecurityConfig(
            enable_authentication=True,
            api_key="test-api-key",
            jwt_secret="test-jwt-secret",
            jwt_expiration_hours=12,
            enable_rate_limiting=False,
            rate_limit_requests_per_minute=1000,
            enable_ssl=True,
            ssl_cert_path="/path/to/cert.pem",
            ssl_key_path="/path/to/key.pem"
        )
        
        assert config.enable_authentication is True
        assert config.api_key == "test-api-key"
        assert config.jwt_secret == "test-jwt-secret"
        assert config.jwt_expiration_hours == 12
        assert config.enable_rate_limiting is False
        assert config.rate_limit_requests_per_minute == 1000
        assert config.enable_ssl is True
        assert config.ssl_cert_path == "/path/to/cert.pem"
        assert config.ssl_key_path == "/path/to/key.pem"


class TestCacheConfig:
    """Test CacheConfig functionality."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = CacheConfig()
        
        assert config.database.host == "localhost"
        assert config.database.port == 5432
        assert config.database.database == "cache_db"
        assert config.embedding.model_name == "all-MiniLM-L6-v2"
        assert config.embedding.dimension == 384
        assert config.predictive_cache.enabled is True
        assert config.semantic_cache.enabled is True
        assert config.vector_cache.enabled is True
        assert config.global_cache.enabled is True
        assert config.vector_diary.enabled is True
        assert config.performance.enable_metrics is True
        assert config.logging.level == "INFO"
        assert config.security.enable_authentication is False
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = CacheConfig(
            database=DatabaseConfig(host="custom.db", port=5433),
            embedding=EmbeddingConfig(model_name="custom-model", dimension=512),
            predictive_cache=PredictiveCacheConfig(enabled=False),
            semantic_cache=SemanticCacheConfig(max_entries=5000),
            vector_cache=VectorCacheConfig(max_entries=100000),
            global_cache=GlobalCacheConfig(rag_server_url="http://custom-rag:8000"),
            vector_diary=VectorDiaryConfig(retention_days=7),
            performance=PerformanceConfig(max_concurrent_requests=200),
            logging=LoggingConfig(level="DEBUG"),
            security=SecurityConfig(enable_authentication=True)
        )
        
        assert config.database.host == "custom.db"
        assert config.database.port == 5433
        assert config.embedding.model_name == "custom-model"
        assert config.embedding.dimension == 512
        assert config.predictive_cache.enabled is False
        assert config.semantic_cache.max_entries == 5000
        assert config.vector_cache.max_entries == 100000
        assert config.global_cache.rag_server_url == "http://custom-rag:8000"
        assert config.vector_diary.retention_days == 7
        assert config.performance.max_concurrent_requests == 200
        assert config.logging.level == "DEBUG"
        assert config.security.enable_authentication is True
    
    def test_config_to_dict(self):
        """Test configuration to dictionary conversion."""
        config = CacheConfig(
            database=DatabaseConfig(host="test.db"),
            embedding=EmbeddingConfig(model_name="test-model")
        )
        
        config_dict = config.to_dict()
        assert "database" in config_dict
        assert "embedding" in config_dict
        assert config_dict["database"]["host"] == "test.db"
        assert config_dict["embedding"]["model_name"] == "test-model"
    
    def test_config_from_dict(self):
        """Test configuration from dictionary creation."""
        config_dict = {
            "database": {
                "host": "test.db",
                "port": 5433
            },
            "embedding": {
                "model_name": "test-model",
                "dimension": 512
            },
            "predictive_cache": {
                "enabled": False
            }
        }
        
        config = CacheConfig.from_dict(config_dict)
        
        assert config.database.host == "test.db"
        assert config.database.port == 5433
        assert config.embedding.model_name == "test-model"
        assert config.embedding.dimension == 512
        assert config.predictive_cache.enabled is False
    
    def test_config_save_and_load(self):
        """Test configuration save and load functionality."""
        config = CacheConfig(
            database=DatabaseConfig(host="test.db"),
            embedding=EmbeddingConfig(model_name="test-model")
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            # Save configuration
            config.save_to_file(temp_path)
            
            # Load configuration
            loaded_config = CacheConfig(config_file_path=temp_path)
            
            assert loaded_config.database.host == "test.db"
            assert loaded_config.embedding.model_name == "test-model"
            
        finally:
            os.unlink(temp_path)
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Valid configuration
        config = CacheConfig()
        errors = config.validate()
        assert len(errors) == 0
        
        # Invalid configuration - negative port
        config = CacheConfig(database=DatabaseConfig(port=-1))
        errors = config.validate()
        assert len(errors) > 0
        assert any("port" in error.lower() for error in errors)
        
        # Invalid configuration - invalid similarity threshold
        config = CacheConfig(semantic_cache=SemanticCacheConfig(similarity_threshold=1.5))
        errors = config.validate()
        assert len(errors) > 0
        assert any("similarity" in error.lower() for error in errors)
        
        # Invalid configuration - invalid TTL
        config = CacheConfig(predictive_cache=PredictiveCacheConfig(cache_ttl_seconds=-1))
        errors = config.validate()
        assert len(errors) > 0
        assert any("ttl" in error.lower() for error in errors)


class TestConfigLoading:
    """Test configuration loading functionality."""
    
    def test_load_config_from_file(self):
        """Test loading configuration from file."""
        config_data = {
            "database": {
                "host": "file.db",
                "port": 5433
            },
            "embedding": {
                "model_name": "file-model",
                "dimension": 512
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            
            assert config.database.host == "file.db"
            assert config.database.port == 5433
            assert config.embedding.model_name == "file-model"
            assert config.embedding.dimension == 512
            
        finally:
            os.unlink(temp_path)
    
    def test_load_config_nonexistent_file(self):
        """Test loading configuration from non-existent file."""
        config = load_config("/nonexistent/path/config.yaml")
        
        # Should return default configuration
        assert config.database.host == "localhost"
        assert config.database.port == 5432
        assert config.embedding.model_name == "all-MiniLM-L6-v2"
    
    def test_load_config_invalid_yaml(self):
        """Test loading configuration from invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            
            # Should return default configuration on invalid YAML
            assert config.database.host == "localhost"
            assert config.database.port == 5432
            
        finally:
            os.unlink(temp_path)
    
    def test_load_config_with_environment_variables(self):
        """Test loading configuration with environment variables."""
        # Set environment variables
        os.environ["CACHE_DB_HOST"] = "env.db"
        os.environ["CACHE_DB_PORT"] = "5434"
        os.environ["CACHE_EMBEDDING_MODEL"] = "env-model"
        
        try:
            config = load_config()
            
            # Should use environment variables
            assert config.database.host == "env.db"
            assert config.database.port == 5434
            assert config.embedding.model_name == "env-model"
            
        finally:
            # Clean up environment variables
            os.environ.pop("CACHE_DB_HOST", None)
            os.environ.pop("CACHE_DB_PORT", None)
            os.environ.pop("CACHE_EMBEDDING_MODEL", None)
    
    def test_validate_config(self):
        """Test configuration validation."""
        # Valid configuration
        config = CacheConfig()
        errors = validate_config(config)
        assert len(errors) == 0
        
        # Invalid configuration
        config = CacheConfig(database=DatabaseConfig(port=-1))
        errors = validate_config(config)
        assert len(errors) > 0
    
    def test_create_default_config_file(self):
        """Test creating default configuration file."""
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            create_default_config_file(temp_path)
            
            # Check if file was created
            assert os.path.exists(temp_path)
            
            # Check if file contains valid configuration
            with open(temp_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            assert "database" in config_data
            assert "embedding" in config_data
            assert "predictive_cache" in config_data
            
        finally:
            os.unlink(temp_path)


class TestConfigEnvironmentVariables:
    """Test environment variable handling."""
    
    def test_database_config_env_vars(self):
        """Test database configuration environment variables."""
        # Set environment variables
        os.environ["CACHE_DB_HOST"] = "env.db.host"
        os.environ["CACHE_DB_PORT"] = "5435"
        os.environ["CACHE_DB_NAME"] = "env.db.name"
        os.environ["CACHE_DB_USER"] = "env.db.user"
        os.environ["CACHE_DB_PASSWORD"] = "env.db.pass"
        
        try:
            config = CacheConfig()
            
            assert config.database.host == "env.db.host"
            assert config.database.port == 5435
            assert config.database.database == "env.db.name"
            assert config.database.username == "env.db.user"
            assert config.database.password == "env.db.pass"
            
        finally:
            # Clean up environment variables
            for key in ["CACHE_DB_HOST", "CACHE_DB_PORT", "CACHE_DB_NAME", 
                       "CACHE_DB_USER", "CACHE_DB_PASSWORD"]:
                os.environ.pop(key, None)
    
    def test_cache_config_env_vars(self):
        """Test cache configuration environment variables."""
        # Set environment variables
        os.environ["CACHE_PREDICTIVE_TTL"] = "120"
        os.environ["CACHE_SEMANTIC_MAX_ENTRIES"] = "20000"
        os.environ["CACHE_VECTOR_SIMILARITY_THRESHOLD"] = "0.8"
        os.environ["CACHE_GLOBAL_RAG_URL"] = "http://env-rag:8000"
        os.environ["CACHE_DIARY_RETENTION_DAYS"] = "14"
        
        try:
            config = CacheConfig()
            
            assert config.predictive_cache.cache_ttl_seconds == 120
            assert config.semantic_cache.max_entries == 20000
            assert config.vector_cache.similarity_threshold == 0.8
            assert config.global_cache.rag_server_url == "http://env-rag:8000"
            assert config.vector_diary.retention_days == 14
            
        finally:
            # Clean up environment variables
            for key in ["CACHE_PREDICTIVE_TTL", "CACHE_SEMANTIC_MAX_ENTRIES", 
                       "CACHE_VECTOR_SIMILARITY_THRESHOLD", "CACHE_GLOBAL_RAG_URL", 
                       "CACHE_DIARY_RETENTION_DAYS"]:
                os.environ.pop(key, None)
    
    def test_performance_config_env_vars(self):
        """Test performance configuration environment variables."""
        # Set environment variables
        os.environ["CACHE_METRICS_ENABLED"] = "false"
        os.environ["CACHE_MAX_CONCURRENT_REQUESTS"] = "500"
        os.environ["CACHE_REQUEST_TIMEOUT"] = "60"
        
        try:
            config = CacheConfig()
            
            assert config.performance.enable_metrics is False
            assert config.performance.max_concurrent_requests == 500
            assert config.performance.request_timeout_seconds == 60
            
        finally:
            # Clean up environment variables
            for key in ["CACHE_METRICS_ENABLED", "CACHE_MAX_CONCURRENT_REQUESTS", 
                       "CACHE_REQUEST_TIMEOUT"]:
                os.environ.pop(key, None)


class TestConfigEdgeCases:
    """Test configuration edge cases."""
    
    def test_partial_config(self):
        """Test partial configuration loading."""
        config_data = {
            "database": {
                "host": "partial.db"
            }
            # Missing other sections
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            
            # Should use provided values and defaults for missing ones
            assert config.database.host == "partial.db"
            assert config.database.port == 5432  # Default
            assert config.embedding.model_name == "all-MiniLM-L6-v2"  # Default
            
        finally:
            os.unlink(temp_path)
    
    def test_empty_config_file(self):
        """Test loading from empty configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            
            # Should return default configuration
            assert config.database.host == "localhost"
            assert config.database.port == 5432
            
        finally:
            os.unlink(temp_path)
    
    def test_config_with_null_values(self):
        """Test configuration with null values."""
        config_data = {
            "database": {
                "host": None,
                "port": None
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            
            # Should use default values for null
            assert config.database.host == "localhost"  # Default
            assert config.database.port == 5432  # Default
            
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])