#!/usr/bin/env python3
"""
Credential Rotation System

This module provides automated credential rotation for HashiCorp Vault secrets.
It supports automatic rotation of database credentials, API keys, and other secrets.

Author: KiloCode
License: Apache 2.0
"""

import os
import sys
import logging
import time
import threading
import schedule
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import secrets
import string

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RotationType(Enum):
    """Types of credential rotation."""
    DATABASE = "database"
    API_KEY = "api_key"
    STORAGE = "storage"
    CUSTOM = "custom"


@dataclass
class RotationConfig:
    """Configuration for credential rotation."""
    secret_path: str
    rotation_type: RotationType
    rotation_interval: int  # hours
    rotation_schedule: str  # cron expression
    enabled: bool = True
    last_rotated: Optional[datetime] = None
    next_rotation: Optional[datetime] = None
    rotation_function: Optional[Callable] = None
    rotation_params: Dict[str, Any] = field(default_factory=dict)


class CredentialRotator:
    """Handles automated credential rotation."""
    
    def __init__(self):
        self.configs: Dict[str, RotationConfig] = {}
        self.scheduler = schedule.Scheduler()
        self.running = False
        self.thread = None
        self.vault_available = self._check_vault_availability()
        
    def _check_vault_availability(self) -> bool:
        """Check if Vault client is available."""
        try:
            from src.vault_client import VaultClient
            client = VaultClient()
            return client.is_available()
        except ImportError:
            logger.warning("Vault client not available for credential rotation")
            return False
        except Exception as e:
            logger.warning(f"Vault connection failed: {e}")
            return False
    
    def add_database_rotation(self, secret_path: str, rotation_interval: int = 24) -> None:
        """Add database credential rotation."""
        config = RotationConfig(
            secret_path=secret_path,
            rotation_type=RotationType.DATABASE,
            rotation_interval=rotation_interval,
            rotation_schedule=f"0 */{rotation_interval} * * *",  # Every X hours
            rotation_function=self._rotate_database_credentials,
            rotation_params={"secret_path": secret_path}
        )
        self.configs[secret_path] = config
        logger.info(f"Added database rotation for {secret_path}")
    
    def add_api_key_rotation(self, secret_path: str, rotation_interval: int = 168) -> None:  # 1 week
        """Add API key rotation."""
        config = RotationConfig(
            secret_path=secret_path,
            rotation_type=RotationType.API_KEY,
            rotation_interval=rotation_interval,
            rotation_schedule=f"0 0 */{rotation_interval} * *",  # Every X days at midnight
            rotation_function=self._rotate_api_key,
            rotation_params={"secret_path": secret_path}
        )
        self.configs[secret_path] = config
        logger.info(f"Added API key rotation for {secret_path}")
    
    def add_storage_rotation(self, secret_path: str, rotation_interval: int = 168) -> None:  # 1 week
        """Add storage credential rotation."""
        config = RotationConfig(
            secret_path=secret_path,
            rotation_type=RotationType.STORAGE,
            rotation_interval=rotation_interval,
            rotation_schedule=f"0 0 */{rotation_interval} * *",  # Every X days at midnight
            rotation_function=self._rotate_storage_credentials,
            rotation_params={"secret_path": secret_path}
        )
        self.configs[secret_path] = config
        logger.info(f"Added storage rotation for {secret_path}")
    
    def add_custom_rotation(self, secret_path: str, rotation_function: Callable, 
                          rotation_interval: int = 24) -> None:
        """Add custom credential rotation."""
        config = RotationConfig(
            secret_path=secret_path,
            rotation_type=RotationType.CUSTOM,
            rotation_interval=rotation_interval,
            rotation_schedule=f"0 */{rotation_interval} * * *",
            rotation_function=rotation_function,
            rotation_params={"secret_path": secret_path}
        )
        self.configs[secret_path] = config
        logger.info(f"Added custom rotation for {secret_path}")
    
    def _rotate_database_credentials(self, secret_path: str) -> bool:
        """Rotate database credentials."""
        if not self.vault_available:
            logger.error("Vault not available for database credential rotation")
            return False
        
        try:
            from src.vault_client import VaultClient
            client = VaultClient()
            
            # Generate new credentials
            new_password = self._generate_secure_password()
            new_username = f"user_{secrets.token_hex(8)}"
            
            # Update Vault secret
            secret_data = {
                "host": os.getenv("POSTGRES_HOST", "localhost"),
                "port": int(os.getenv("POSTGRES_PORT", 5432)),
                "database": os.getenv("POSTGRES_DB", "postgres"),
                "username": new_username,
                "password": new_password,
                "rotation_timestamp": datetime.utcnow().isoformat(),
                "rotation_count": client.get_secret(secret_path).get("rotation_count", 0) + 1
            }
            
            client.write_secret(secret_path, secret_data)
            
            # Log the rotation
            logger.info(f"Database credentials rotated for {secret_path}")
            logger.info(f"New username: {new_username}")
            logger.warning(f"New password: {new_password[:4]}**** (first 4 characters shown)")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate database credentials for {secret_path}: {e}")
            return False
    
    def _rotate_api_key(self, secret_path: str) -> bool:
        """Rotate API key."""
        if not self.vault_available:
            logger.error("Vault not available for API key rotation")
            return False
        
        try:
            from src.vault_client import VaultClient
            client = VaultClient()
            
            # Generate new API key
            new_api_key = self._generate_api_key()
            
            # Update Vault secret
            current_secret = client.get_secret(secret_path) or {}
            secret_data = {
                **current_secret,
                "api_key": new_api_key,
                "rotation_timestamp": datetime.utcnow().isoformat(),
                "rotation_count": current_secret.get("rotation_count", 0) + 1,
                "previous_api_key": current_secret.get("api_key")
            }
            
            client.write_secret(secret_path, secret_data)
            
            # Log the rotation
            logger.info(f"API key rotated for {secret_path}")
            logger.warning(f"New API key: {new_api_key[:8]}**** (first 8 characters shown)")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate API key for {secret_path}: {e}")
            return False
    
    def _rotate_storage_credentials(self, secret_path: str) -> bool:
        """Rotate storage credentials."""
        if not self.vault_available:
            logger.error("Vault not available for storage credential rotation")
            return False
        
        try:
            from src.vault_client import VaultClient
            client = VaultClient()
            
            # Generate new credentials
            new_access_key = self._generate_access_key()
            new_secret_key = self._generate_secret_key()
            
            # Update Vault secret
            current_secret = client.get_secret(secret_path) or {}
            secret_data = {
                **current_secret,
                "access_key": new_access_key,
                "secret_key": new_secret_key,
                "rotation_timestamp": datetime.utcnow().isoformat(),
                "rotation_count": current_secret.get("rotation_count", 0) + 1,
                "previous_access_key": current_secret.get("access_key"),
                "previous_secret_key": current_secret.get("secret_key")
            }
            
            client.write_secret(secret_path, secret_data)
            
            # Log the rotation
            logger.info(f"Storage credentials rotated for {secret_path}")
            logger.warning(f"New access key: {new_access_key[:8]}**** (first 8 characters shown)")
            logger.warning(f"New secret key: {new_secret_key[:8]}**** (first 8 characters shown)")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate storage credentials for {secret_path}: {e}")
            return False
    
    def _generate_secure_password(self, length: int = 16) -> str:
        """Generate a secure password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    def _generate_api_key(self) -> str:
        """Generate an API key."""
        prefix = "sk-" if "openrouter" in self.configs else "key-"
        return prefix + secrets.token_hex(32)
    
    def _generate_access_key(self) -> str:
        """Generate an access key."""
        return "AKIA" + secrets.token_hex(16)
    
    def _generate_secret_key(self) -> str:
        """Generate a secret key."""
        return secrets.token_hex(32)
    
    def start_rotation(self) -> None:
        """Start the credential rotation scheduler."""
        if not self.vault_available:
            logger.error("Cannot start rotation: Vault not available")
            return
        
        if self.running:
            logger.warning("Rotation scheduler already running")
            return
        
        self.running = True
        
        # Schedule all enabled rotations
        for config in self.configs.values():
            if config.enabled:
                self.scheduler.every().day.at("00:00").do(self._rotate_secret, config)
        
        # Start the scheduler in a separate thread
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        logger.info("Credential rotation scheduler started")
    
    def stop_rotation(self) -> None:
        """Stop the credential rotation scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.scheduler.clear()
        logger.info("Credential rotation scheduler stopped")
    
    def _run_scheduler(self) -> None:
        """Run the scheduler loop."""
        while self.running:
            self.scheduler.run_pending()
            time.sleep(60)  # Check every minute
    
    def _rotate_secret(self, config: RotationConfig) -> None:
        """Rotate a specific secret."""
        if not config.enabled:
            return
        
        logger.info(f"Rotating secret: {config.secret_path}")
        
        try:
            if config.rotation_function:
                success = config.rotation_function(**config.rotation_params)
                if success:
                    config.last_rotated = datetime.utcnow()
                    config.next_rotation = config.last_rotated + timedelta(hours=config.rotation_interval)
                    logger.info(f"Successfully rotated {config.secret_path}")
                else:
                    logger.error(f"Failed to rotate {config.secret_path}")
            else:
                logger.error(f"No rotation function defined for {config.secret_path}")
                
        except Exception as e:
            logger.error(f"Error rotating {config.secret_path}: {e}")
    
    def rotate_now(self, secret_path: str) -> bool:
        """Manually trigger rotation for a specific secret."""
        if secret_path not in self.configs:
            logger.error(f"No rotation configuration found for {secret_path}")
            return False
        
        config = self.configs[secret_path]
        return self._rotate_secret(config)
    
    def get_rotation_status(self) -> Dict[str, Any]:
        """Get the status of all rotation configurations."""
        status = {}
        
        for secret_path, config in self.configs.items():
            status[secret_path] = {
                "enabled": config.enabled,
                "rotation_type": config.rotation_type.value,
                "rotation_interval": config.rotation_interval,
                "last_rotated": config.last_rotated.isoformat() if config.last_rotated else None,
                "next_rotation": config.next_rotation.isoformat() if config.next_rotation else None,
                "secret_path": config.secret_path
            }
        
        return status
    
    def setup_default_rotations(self) -> None:
        """Set up default rotation configurations."""
        # Database credentials rotation (every 24 hours)
        self.add_database_rotation("secret/data/database/postgres", 24)
        
        # API key rotations (every 7 days)
        self.add_api_key_rotation("secret/data/api-keys/openrouter", 168)
        self.add_api_key_rotation("secret/data/api-keys/brave-search", 168)
        self.add_api_key_rotation("secret/data/api-keys/openai", 168)
        
        # Storage credentials rotation (every 7 days)
        self.add_storage_rotation("secret/data/storage/minio", 168)
        
        logger.info("Default rotation configurations set up")


def main():
    """Main function for testing credential rotation."""
    rotator = CredentialRotator()
    
    # Set up default rotations
    rotator.setup_default_rotations()
    
    # Start rotation
    rotator.start_rotation()
    
    # Print status
    print("Credential Rotation Status:")
    status = rotator.get_rotation_status()
    for secret_path, info in status.items():
        print(f"  {secret_path}: {info}")
    
    # Keep running
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nStopping credential rotation...")
        rotator.stop_rotation()


if __name__ == "__main__":
    main()