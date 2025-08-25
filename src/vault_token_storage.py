"""
HashiCorp Vault integration for secure token storage and retrieval.

This module provides secure storage and retrieval of API tokens and keys
using HashiCorp Vault as the primary secure storage backend.
"""

import os
import json
import logging
import hashlib
import base64
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class VaultTokenStorage:
    """
    HashiCorp Vault integration for secure token storage.
    
    This class provides methods to securely store, retrieve, and manage
    API tokens and keys using HashiCorp Vault's key-value secrets engine.
    """
    
    def __init__(self, vault_url: Optional[str] = None, vault_token: Optional[str] = None):
        """
        Initialize Vault client with configuration.
        
        Args:
            vault_url: HashiCorp Vault server URL
            vault_token: Vault authentication token
        """
        self.vault_url = vault_url or os.getenv('VAULT_ADDR', 'http://localhost:8200')
        self.vault_token = vault_token or os.getenv('VAULT_TOKEN')
        self.vault_mount_path = os.getenv('VAULT_MOUNT_PATH', 'secret/')
        self.timeout = int(os.getenv('VAULT_TIMEOUT', '30'))
        
        # Validate configuration
        if not self.vault_url:
            raise ValueError("Vault URL must be provided or set via VAULT_ADDR environment variable")
        if not self.vault_token:
            raise ValueError("Vault token must be provided or set via VAULT_TOKEN environment variable")
        
        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'X-Vault-Token': self.vault_token,
            'Content-Type': 'application/json'
        })
        
        # Encryption settings for local caching
        self.encryption_key = self._get_or_create_encryption_key()
        self.cache_enabled = os.getenv('VAULT_CACHE_ENABLED', 'true').lower() == 'true'
        self.cache_ttl = int(os.getenv('VAULT_CACHE_TTL', '300'))  # 5 minutes
        
        logger.info(f"VaultTokenStorage initialized with URL: {self.vault_url}")
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for local caching."""
        key_file = os.path.expanduser('~/.vault_cache_key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new encryption key
            key = os.urandom(32)
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            return key
    
    def _hash_token(self, token: str) -> str:
        """Create SHA-256 hash of token for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def _encrypt_data(self, data: str) -> bytes:
        """Encrypt data using AES-256-GCM for local caching."""
        # Generate random nonce
        nonce = os.urandom(12)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.encryption_key),
            modes.GCM(nonce),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Encrypt data
        ciphertext = encryptor.update(data.encode()) + encryptor.finalize()
        
        # Return nonce + tag + ciphertext
        return nonce + encryptor.tag + ciphertext
    
    def _decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt data using AES-256-GCM."""
        # Extract nonce, tag, and ciphertext
        nonce = encrypted_data[:12]
        tag = encrypted_data[12:28]
        ciphertext = encrypted_data[28:]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.encryption_key),
            modes.GCM(nonce, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt data
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext.decode()
    
    def _make_vault_request(self, method: str, path: str, data: Optional[Dict] = None) -> Dict:
        """
        Make authenticated request to HashiCorp Vault.
        
        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            path: Vault API path
            data: Request data (optional)
            
        Returns:
            Response data from Vault
            
        Raises:
            Exception: If Vault request fails
        """
        url = f"{self.vault_url}/v1/{path}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Vault request failed: {e}")
            raise Exception(f"Vault request failed: {e}")
    
    def store_token_securely(self, user_id: str, service_name: str, token: str,
                           token_type: str = 'api_key', expires_at: Optional[datetime] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store a token securely in HashiCorp Vault.
        
        Args:
            user_id: User identifier
            service_name: Service name (e.g., 'openai', 'anthropic')
            token: The token to store
            token_type: Type of token ('api_key', 'access_token', 'refresh_token', 'jwt')
            expires_at: Optional expiration datetime
            metadata: Additional metadata to store with the token
            
        Returns:
            Token ID for reference
            
        Raises:
            Exception: If storage fails
        """
        try:
            # Create token metadata
            token_metadata = {
                'user_id': user_id,
                'service_name': service_name,
                'token_type': token_type,
                'created_at': datetime.utcnow().isoformat(),
                'hash': self._hash_token(token)
            }
            
            if expires_at:
                token_metadata['expires_at'] = expires_at.isoformat()
            
            if metadata:
                token_metadata.update(metadata)
            
            # Store in Vault
            vault_path = f"{self.vault_mount_path}{user_id}/{service_name}/token"
            self._make_vault_request('POST', vault_path, {
                'token': token,
                'metadata': token_metadata
            })
            
            # Log the security event
            logger.info(f"Securely stored token for user {user_id}, service {service_name}")
            
            return token_metadata['hash']
            
        except Exception as e:
            logger.error(f"Failed to store token securely: {e}")
            raise Exception(f"Failed to store token securely: {e}")
    
    def retrieve_token_securely(self, user_id: str, service_name: str, 
                              token_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve a token securely from HashiCorp Vault.
        
        Args:
            user_id: User identifier
            service_name: Service name
            token_id: Optional token ID for specific token
            
        Returns:
            Dictionary containing token and metadata
            
        Raises:
            Exception: If retrieval fails
        """
        try:
            # Build Vault path
            if token_id:
                vault_path = f"{self.vault_mount_path}{user_id}/{service_name}/token/{token_id}"
            else:
                vault_path = f"{self.vault_mount_path}{user_id}/{service_name}/token"
            
            # Retrieve from Vault
            response = self._make_vault_request('GET', vault_path)
            
            # Check if token exists
            if 'data' not in response or 'token' not in response['data']:
                raise Exception("Token not found")
            
            token_data = response['data']
            
            # Verify token hash if available
            if 'hash' in token_data['metadata']:
                current_hash = self._hash_token(token_data['token'])
                if current_hash != token_data['metadata']['hash']:
                    raise Exception("Token integrity check failed")
            
            # Check expiration
            if 'expires_at' in token_data['metadata']:
                expires_at = datetime.fromisoformat(token_data['metadata']['expires_at'])
                if datetime.utcnow() > expires_at:
                    raise Exception("Token has expired")
            
            # Update last used timestamp
            token_data['metadata']['last_used'] = datetime.utcnow().isoformat()
            
            # Log the security event
            logger.info(f"Retrieved token for user {user_id}, service {service_name}")
            
            return token_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve token securely: {e}")
            raise Exception(f"Failed to retrieve token securely: {e}")
    
    def revoke_token(self, user_id: str, service_name: str, token_id: str) -> bool:
        """
        Revoke a token in HashiCorp Vault.
        
        Args:
            user_id: User identifier
            service_name: Service name
            token_id: Token ID to revoke
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build Vault path
            vault_path = f"{self.vault_mount_path}{user_id}/{service_name}/token/{token_id}"
            
            # Delete from Vault
            self._make_vault_request('DELETE', vault_path)
            
            # Log the security event
            logger.info(f"Revoked token {token_id} for user {user_id}, service {service_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False
    
    def list_user_tokens(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all tokens for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of token metadata
        """
        try:
            # List all paths for the user
            vault_path = f"{self.vault_mount_path}{user_id}/"
            response = self._make_vault_request('LIST', vault_path)
            
            tokens = []
            if 'data' in response and 'keys' in response['data']:
                for service_key in response['data']['keys']:
                    if service_key.endswith('/'):
                        service_name = service_key[:-1]  # Remove trailing slash
                        
                        # Get token metadata
                        token_path = f"{vault_path}{service_name}/token"
                        token_response = self._make_vault_request('GET', token_path)
                        
                        if 'data' in token_response and 'metadata' in token_response['data']:
                            token_metadata = token_response['data']['metadata'].copy()
                            token_metadata['service_name'] = service_name
                            tokens.append(token_metadata)
            
            return tokens
            
        except Exception as e:
            logger.error(f"Failed to list user tokens: {e}")
            return []
    
    def rotate_token(self, user_id: str, service_name: str, old_token: str,
                    new_token: str) -> bool:
        """
        Rotate a token by storing the new one and revoking the old one.
        
        Args:
            user_id: User identifier
            service_name: Service name
            old_token: Old token to revoke
            new_token: New token to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get token metadata for the old token
            old_token_data = self.retrieve_token_securely(user_id, service_name)
            metadata = old_token_data['metadata'].copy()
            
            # Update metadata for new token
            metadata['created_at'] = datetime.utcnow().isoformat()
            metadata['previous_token_hash'] = metadata.get('hash')
            
            # Store new token
            self.store_token_securely(
                user_id=user_id,
                service_name=service_name,
                token=new_token,
                token_type=metadata.get('token_type', 'api_key'),
                expires_at=datetime.fromisoformat(metadata['expires_at']) if 'expires_at' in metadata else None,
                metadata=metadata
            )
            
            # Revoke old token
            self.revoke_token(user_id, service_name, metadata['hash'])
            
            logger.info(f"Rotated token for user {user_id}, service {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate token: {e}")
            return False
    
    def check_token_health(self, user_id: str, service_name: str) -> Dict[str, Any]:
        """
        Check the health and status of a token.
        
        Args:
            user_id: User identifier
            service_name: Service name
            
        Returns:
            Dictionary with token health information
        """
        try:
            token_data = self.retrieve_token_securely(user_id, service_name)
            metadata = token_data['metadata']
            
            # Calculate days until expiration
            days_until_expiry = None
            if 'expires_at' in metadata:
                expires_at = datetime.fromisoformat(metadata['expires_at'])
                days_until_expiry = (expires_at - datetime.utcnow()).days
            
            # Check if token is expired
            is_expired = days_until_expiry is not None and days_until_expiry <= 0
            
            # Check if token is about to expire (within 7 days)
            is_expiring_soon = days_until_expiry is not None and 0 < days_until_expiry <= 7
            
            return {
                'token_id': metadata.get('hash'),
                'user_id': user_id,
                'service_name': service_name,
                'token_type': metadata.get('token_type'),
                'created_at': metadata.get('created_at'),
                'last_used': metadata.get('last_used'),
                'expires_at': metadata.get('expires_at'),
                'days_until_expiry': days_until_expiry,
                'is_expired': is_expired,
                'is_expiring_soon': is_expiring_soon,
                'health_status': 'expired' if is_expired else 'expiring_soon' if is_expiring_soon else 'healthy'
            }
            
        except Exception as e:
            logger.error(f"Failed to check token health: {e}")
            return {
                'user_id': user_id,
                'service_name': service_name,
                'health_status': 'error',
                'error': str(e)
            }
    
    def cleanup_expired_tokens(self, days_threshold: int = 30) -> int:
        """
        Clean up expired tokens from Vault.
        
        Args:
            days_threshold: Number of days to consider a token expired
            
        Returns:
            Number of tokens cleaned up
        """
        try:
            # This is a simplified implementation
            # In production, you would need to implement proper token discovery and cleanup
            logger.info(f"Token cleanup not fully implemented - threshold: {days_threshold} days")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired tokens: {e}")
            return 0
    
    def get_vault_status(self) -> Dict[str, Any]:
        """
        Get HashiCorp Vault status and health.
        
        Returns:
            Dictionary with Vault status information
        """
        try:
            # Check Vault health
            health_response = self._make_vault_request('GET', 'sys/health')
            
            # Get Vault version
            version_response = self._make_vault_request('GET', 'sys/version')
            
            return {
                'vault_status': health_response.get('initialized', False),
                'vault_sealed': health_response.get('sealed', False),
                'vault_version': version_response.get('version', 'unknown'),
                'vault_cluster_name': health_response.get('cluster_name', 'unknown'),
                'vault_cluster_id': health_response.get('cluster_id', 'unknown'),
                'vault_high_availability': health_response.get('ha_enabled', False),
                'vault_renewable': health_response.get('renewable', False),
                'vault_lease_duration': health_response.get('lease_duration', 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get Vault status: {e}")
            return {
                'vault_status': False,
                'vault_sealed': True,
                'vault_version': 'unknown',
                'vault_error': str(e)
            }
    
    def audit_security_event(self, event_type: str, severity_level: str,
                           user_id: str, service_name: str, action: str,
                           details: Optional[Dict[str, Any]] = None,
                           ip_address: Optional[str] = None,
                           user_agent: Optional[str] = None,
                           session_id: Optional[str] = None) -> bool:
        """
        Log a security event to Vault audit logs.
        
        Args:
            event_type: Type of security event
            severity_level: Severity level ('INFO', 'WARNING', 'ERROR', 'CRITICAL')
            user_id: User identifier
            service_name: Service name
            action: Action performed
            details: Additional event details
            ip_address: Client IP address
            user_agent: User agent string
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create audit event
            audit_event = {
                'event_type': event_type,
                'severity_level': severity_level,
                'user_id': user_id,
                'service_name': service_name,
                'action': action,
                'timestamp': datetime.utcnow().isoformat(),
                'details': details or {}
            }
            
            if ip_address:
                audit_event['ip_address'] = ip_address
            if user_agent:
                audit_event['user_agent'] = user_agent
            if session_id:
                audit_event['session_id'] = session_id
            
            # Store audit event in Vault
            audit_path = f"{self.vault_mount_path}audit_logs/{user_id}/{service_name}"
            self._make_vault_request('POST', audit_path, audit_event)
            
            logger.info(f"Logged security event: {event_type} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to audit security event: {e}")
            return False


# Example usage and testing
if __name__ == "__main__":
    # Initialize Vault storage
    vault_storage = VaultTokenStorage()
    
    # Test token storage
    try:
        token_id = vault_storage.store_token_securely(
            user_id="test-user",
            service_name="openai",
            token="sk-test123456789",
            token_type="api_key",
            metadata={"environment": "testing", "purpose": "api_integration"}
        )
        print(f"Stored token with ID: {token_id}")
        
        # Test token retrieval
        token_data = vault_storage.retrieve_token_securely("test-user", "openai")
        print(f"Retrieved token: {token_data['token'][:10]}...")
        
        # Test token health check
        health = vault_storage.check_token_health("test-user", "openai")
        print(f"Token health: {health}")
        
        # Test Vault status
        status = vault_storage.get_vault_status()
        print(f"Vault status: {status}")
        
    except Exception as e:
        print(f"Error: {e}")