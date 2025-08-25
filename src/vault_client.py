"""
HashiCorp Vault Client for paddle-plugin System

This module provides a secure interface to HashiCorp Vault for retrieving secrets
and managing credentials across the application.

Author: KiloCode
License: Apache 2.0
"""

import os
import logging
import json
from typing import Optional, Dict, Any, Union
from pathlib import Path
from dataclasses import dataclass
from functools import lru_cache
import hvac
from hvac.exceptions import VaultError

logger = logging.getLogger(__name__)


@dataclass
class VaultConfig:
    """Vault configuration settings"""
    vault_url: str = "http://127.0.0.1:8200"
    vault_token: Optional[str] = None
    vault_role: Optional[str] = None
    vault_auth_method: str = "token"  # token, approle, kubernetes
    vault_namespace: Optional[str] = None
    vault_timeout: int = 30
    vault_retries: int = 3
    vault_ca_cert: Optional[str] = None
    vault_verify_ssl: bool = True


class VaultClient:
    """
    HashiCorp Vault client for secure secret management.
    
    This client provides methods to retrieve secrets from Vault with proper
    error handling, caching, and fallback mechanisms.
    """
    
    def __init__(self, config: Optional[VaultConfig] = None):
        """
        Initialize Vault client with configuration.
        
        Args:
            config: Vault configuration. If None, uses environment variables.
        """
        self.config = config or self._load_config_from_env()
        self.client = None
        self._authenticated = False
        
    def _load_config_from_env(self) -> VaultConfig:
        """Load configuration from environment variables."""
        return VaultConfig(
            vault_url=os.getenv("VAULT_ADDR", "http://127.0.0.1:8200"),
            vault_token=os.getenv("VAULT_TOKEN"),
            vault_role=os.getenv("VAULT_ROLE"),
            vault_auth_method=os.getenv("VAULT_AUTH_METHOD", "token"),
            vault_namespace=os.getenv("VAULT_NAMESPACE"),
            vault_timeout=int(os.getenv("VAULT_TIMEOUT", "30")),
            vault_retries=int(os.getenv("VAULT_RETRIES", "3")),
            vault_ca_cert=os.getenv("VAULT_CA_CERT"),
            vault_verify_ssl=os.getenv("VAULT_VERIFY_SSL", "true").lower() == "true"
        )
    
    def authenticate(self) -> bool:
        """
        Authenticate with Vault using configured method.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            if not self.config.vault_token:
                logger.error("No Vault token provided")
                return False
                
            self.client = hvac.Client(
                url=self.config.vault_url,
                token=self.config.vault_token,
                namespace=self.config.vault_namespace,
                verify=self.config.vault_verify_ssl,
                cert=(self.config.vault_ca_cert, "") if self.config.vault_ca_cert else None
            )
            
            # Test connection
            if not self.client.is_authenticated():
                logger.error("Vault authentication failed")
                return False
                
            self._authenticated = True
            logger.info("Successfully authenticated with Vault")
            return True
            
        except Exception as e:
            logger.error(f"Vault authentication error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Vault authentication error: {str(e)}")
            return False
    
    def get_secret(self, path: str, key: str = "value", default: Any = None) -> Any:
        """
        Retrieve a secret from Vault.
        
        Args:
            path: Vault secret path (e.g., "secret/data/api-keys/openrouter")
            key: Key within the secret to retrieve
            default: Default value if key not found
            
        Returns:
            Secret value or default if not found
        """
        if not self._authenticated and not self.authenticate():
            logger.warning(f"Failed to authenticate with Vault, using default for {path}")
            return default
            
        if not self.client:
            logger.warning(f"Vault client not available, using default for {path}")
            return default
            
        try:
            # Read secret from Vault
            response = self.client.secrets.kv.v2.read_secret_version(path=path)
            
            if response and 'data' in response and 'data' in response['data']:
                secret_data = response['data']['data']
                return secret_data.get(key, default)
                
            logger.warning(f"Secret not found at path: {path}")
            return default
            
        except VaultError as e:
            logger.error(f"Vault error reading secret {path}: {str(e)}")
            return default
        except Exception as e:
            logger.error(f"Unexpected error reading secret {path}: {str(e)}")
            return default
    
    def get_database_credentials(self, db_name: str) -> Dict[str, str]:
        """
        Retrieve database credentials from Vault.
        
        Args:
            db_name: Database name (e.g., "postgres", "redis")
            
        Returns:
            Dictionary with database credentials
        """
        path = f"secret/data/database/{db_name}"
        secret = self.get_secret(path)
        
        if secret:
            return {
                "host": secret.get("host", "localhost"),
                "port": secret.get("port", "5432"),
                "username": secret.get("username", "postgres"),
                "password": secret.get("password", ""),
                "database": secret.get("database", db_name)
            }
        
        # Fallback to environment variables if Vault not available
        return self._get_fallback_db_credentials(db_name)
    
    def get_api_key(self, service: str) -> Optional[str]:
        """
        Retrieve API key for a specific service.
        
        Args:
            service: Service name (e.g., "openrouter", "brave-search")
            
        Returns:
            API key or None if not found
        """
        path = f"secret/data/api-keys/{service}"
        return self.get_secret(path, "api_key")
    
    def get_application_config(self, app_name: str) -> Dict[str, Any]:
        """
        Retrieve application configuration from Vault.
        
        Args:
            app_name: Application name (e.g., "simba", "mcp-memory")
            
        Returns:
            Application configuration dictionary
        """
        path = f"secret/data/applications/{app_name}"
        return self.get_secret(path) or {}
    
    def _get_fallback_db_credentials(self, db_name: str) -> Dict[str, str]:
        """Get database credentials from environment variables as fallback."""
        if db_name == "postgres":
            return {
                "host": os.getenv("POSTGRES_HOST", "localhost"),
                "port": os.getenv("POSTGRES_PORT", "5432"),
                "username": os.getenv("POSTGRES_USER", "postgres"),
                "password": os.getenv("POSTGRES_PASSWORD", ""),
                "database": os.getenv("POSTGRES_DB", "postgres")
            }
        elif db_name == "redis":
            return {
                "host": os.getenv("REDIS_HOST", "localhost"),
                "port": os.getenv("REDIS_PORT", "6379"),
                "password": os.getenv("REDIS_PASSWORD", ""),
                "database": os.getenv("REDIS_DB", "0")
            }
        else:
            return {"host": "localhost", "port": "5432", "username": "", "password": "", "database": db_name}
    
    @lru_cache(maxsize=128)
    def get_cached_secret(self, path: str, key: str = "value") -> Any:
        """
        Retrieve a secret with caching to reduce Vault API calls.
        
        Args:
            path: Vault secret path
            key: Key within the secret
            
        Returns:
            Secret value
        """
        return self.get_secret(path, key)
    
    def is_available(self) -> bool:
        """Check if Vault is available and authenticated."""
        if not self._authenticated:
            return self.authenticate()
        return bool(self._authenticated and self.client and self.client.is_authenticated())
    
    def close(self):
        """Close Vault client connection."""
        if self.client:
            self.client = None
            self._authenticated = False
            logger.info("Vault client connection closed")


# Global Vault client instance
_vault_client = None


def get_vault_client() -> VaultClient:
    """Get global Vault client instance."""
    global _vault_client
    if _vault_client is None:
        _vault_client = VaultClient()
    return _vault_client


def get_secret(path: str, key: str = "value", default: Any = None) -> Any:
    """
    Convenience function to get a secret from Vault.
    
    Args:
        path: Vault secret path
        key: Key within the secret
        default: Default value if not found
        
    Returns:
        Secret value or default
    """
    client = get_vault_client()
    return client.get_secret(path, key, default)


def get_database_credentials(db_name: str) -> Dict[str, str]:
    """
    Convenience function to get database credentials.
    
    Args:
        db_name: Database name
        
    Returns:
        Database credentials dictionary
    """
    client = get_vault_client()
    return client.get_database_credentials(db_name)


def get_api_key(service: str) -> Optional[str]:
    """
    Convenience function to get API key.
    
    Args:
        service: Service name
        
    Returns:
        API key or None
    """
    client = get_vault_client()
    return client.get_api_key(service)


def initialize_vault_secrets():
    """
    Initialize Vault with default secrets if they don't exist.
    This should be called during system setup.
    """
    client = get_vault_client()
    
    if not client.is_available():
        logger.warning("Vault not available, skipping secret initialization")
        return
    
    # Initialize with default secrets
    default_secrets = {
        "secret/data/database/postgres": {
            "host": "localhost",
            "port": "5432",
            "username": "postgres",
            "password": os.getenv("POSTGRES_PASSWORD", "secure_password_change_me"),
            "database": "postgres"
        },
        "secret/data/api-keys/openrouter": {
            "api_key": os.getenv("OPENROUTER_API_KEY", "sk-or-v1-your-api-key-here")
        },
        "secret/data/api-keys/brave-search": {
            "api_key": os.getenv("BRAVE_API_KEY", "your-brave-api-key-here")
        },
        "secret/data/storage/minio": {
            "access_key": os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            "secret_key": os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            "endpoint": os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            "bucket": os.getenv("MINIO_BUCKET", "simba-bucket")
        }
    }
    
    for path, data in default_secrets.items():
        try:
            # Check if secret exists
            existing = client.get_secret(path)
            if not existing:
                # Create secret
                if client.client:
                    client.client.secrets.kv.v2.create_or_update_secret(
                        path=path,
                        secret=data
                    )
                logger.info(f"Created default secret at {path}")
            else:
                logger.info(f"Secret already exists at {path}")
        except Exception as e:
            logger.error(f"Failed to create secret at {path}: {str(e)}")


if __name__ == "__main__":
    # Test Vault connection
    client = get_vault_client()
    if client.authenticate():
        print("Vault connection successful")
        # Test retrieving a secret
        secret = client.get_secret("secret/data/test/hello")
        print(f"Test secret: {secret}")
    else:
        print("Vault connection failed")