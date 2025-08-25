#!/usr/bin/env python3
"""
Vault Integration Testing Suite

This module provides comprehensive tests for HashiCorp Vault integration across
the entire system. It includes unit tests, integration tests, and end-to-end tests.

Author: KiloCode
License: Apache 2.0
"""

import os
import sys
import unittest
import pytest
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vault_client import VaultClient
from environment_validator import EnvironmentValidator, ValidationResult, ValidationLevel
from credential_rotation import CredentialRotator, RotationType


class TestVaultClient(unittest.TestCase):
    """Test cases for Vault client."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_vault_addr = "http://localhost:8200"
        self.test_vault_token = "s.test_token"
        os.environ["VAULT_ADDR"] = self.test_vault_addr
        os.environ["VAULT_TOKEN"] = self.test_vault_token
    
    def tearDown(self):
        """Clean up test fixtures."""
        if "VAULT_ADDR" in os.environ:
            del os.environ["VAULT_ADDR"]
        if "VAULT_TOKEN" in os.environ:
            del os.environ["VAULT_TOKEN"]
    
    def test_vault_client_initialization(self):
        """Test Vault client initialization."""
        client = VaultClient()
        self.assertIsNotNone(client)
        self.assertEqual(client.vault_addr, self.test_vault_addr)
        self.assertEqual(client.vault_token, self.test_vault_token)
    
    @patch('hvac.Client')
    def test_vault_authentication_success(self, mock_hvac_client):
        """Test successful Vault authentication."""
        mock_client = Mock()
        mock_hvac_client.return_value = mock_client
        mock_client.auth_token.return_value = True
        
        client = VaultClient()
        result = client.authenticate()
        
        self.assertTrue(result)
        mock_client.auth_token.assert_called_once()
    
    @patch('hvac.Client')
    def test_vault_authentication_failure(self, mock_hvac_client):
        """Test failed Vault authentication."""
        mock_client = Mock()
        mock_hvac_client.return_value = mock_client
        mock_client.auth_token.side_effect = Exception("Authentication failed")
        
        client = VaultClient()
        result = client.authenticate()
        
        self.assertFalse(result)
    
    @patch('hvac.Client')
    def test_write_and_read_secret(self, mock_hvac_client):
        """Test writing and reading secrets."""
        mock_client = Mock()
        mock_hvac_client.return_value = mock_client
        mock_client.auth_token.return_value = True
        
        test_secret = {"key": "value", "number": 42}
        test_path = "secret/data/test/hello"
        
        client = VaultClient()
        
        # Write secret
        client.write_secret(test_path, test_secret)
        mock_client.secrets.kv.v2.create_or_update_secret.assert_called_once()
        
        # Read secret
        mock_client.secrets.kv.v2.read_secret_version.return_value = {"data": {"data": test_secret}}
        result = client.read_secret(test_path)
        
        self.assertEqual(result, test_secret)
        mock_client.secrets.kv.v2.read_secret_version.assert_called_once_with(path=test_path)
    
    @patch('hvac.Client')
    def test_delete_secret(self, mock_hvac_client):
        """Test deleting secrets."""
        mock_client = Mock()
        mock_hvac_client.return_value = mock_client
        mock_client.auth_token.return_value = True
        
        test_path = "secret/data/test/hello"
        
        client = VaultClient()
        client.delete_secret(test_path)
        
        mock_client.secrets.kv.v2.delete_metadata_and_all_versions.assert_called_once_with(path=test_path)
    
    @patch('hvac.Client')
    def test_list_secrets(self, mock_hvac_client):
        """Test listing secrets."""
        mock_client = Mock()
        mock_hvac_client.return_value = mock_client
        mock_client.auth_token.return_value = True
        
        expected_secrets = ["secret/data/test/hello", "secret/data/test/world"]
        mock_client.secrets.kv.v2.list_secrets.return_value = {"data": {"keys": expected_secrets}}
        
        client = VaultClient()
        result = client.list_secrets("secret/data/test/")
        
        self.assertEqual(result, expected_secrets)
        mock_client.secrets.kv.v2.list_secrets.assert_called_once_with(path="secret/data/test/")
    
    @patch('hvac.Client')
    def test_vault_unavailable(self, mock_hvac_client):
        """Test Vault client when Vault is unavailable."""
        mock_hvac_client.side_effect = Exception("Connection refused")
        
        client = VaultClient()
        self.assertFalse(client.is_available())
        self.assertFalse(client.authenticate())


class TestEnvironmentValidator(unittest.TestCase):
    """Test cases for environment validator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = EnvironmentValidator()
    
    def test_validator_initialization(self):
        """Test validator initialization."""
        self.assertIsInstance(self.validator, EnvironmentValidator)
        self.assertIsInstance(self.validator.results, list)
    
    @patch('os.getenv')
    def test_validate_database_credentials_success(self, mock_getenv):
        """Test successful database credentials validation."""
        mock_getenv.side_effect = lambda key: {
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_PORT': '5432',
            'POSTGRES_USER': 'postgres',
            'POSTGRES_PASSWORD': 'password',
            'POSTGRES_DB': 'testdb'
        }.get(key, '')
        
        results = self.validator.validate_database_credentials()
        
        self.assertTrue(len(results) > 0)
        self.assertTrue(any(r.is_valid for r in results))
    
    @patch('os.getenv')
    def test_validate_database_credentials_missing(self, mock_getenv):
        """Test database credentials validation with missing credentials."""
        mock_getenv.return_value = None
        
        results = self.validator.validate_database_credentials()
        
        self.assertTrue(len(results) > 0)
        self.assertTrue(any(not r.is_valid for r in results))
    
    @patch('os.getenv')
    def test_validate_api_keys_success(self, mock_getenv):
        """Test successful API key validation."""
        mock_getenv.side_effect = lambda key: {
            'OPENROUTER_API_KEY': 'sk-test-key-123',
            'BRAVE_API_KEY': 'test-brave-key',
            'OPENAI_API_KEY': 'sk-test-openai-key'
        }.get(key, '')
        
        results = self.validator.validate_api_keys()
        
        self.assertTrue(len(results) > 0)
        self.assertTrue(all(r.is_valid for r in results))
    
    @patch('os.getenv')
    def test_validate_api_keys_placeholder(self, mock_getenv):
        """Test API key validation with placeholder keys."""
        mock_getenv.side_effect = lambda key: {
            'OPENROUTER_API_KEY': 'your_openrouter_api_key_here',
            'BRAVE_API_KEY': 'test-brave-key',
            'OPENAI_API_KEY': 'your_openai_api_key_here'
        }.get(key, '')
        
        results = self.validator.validate_api_keys()
        
        self.assertTrue(len(results) > 0)
        placeholder_warnings = [r for r in results if not r.is_valid and r.level == ValidationLevel.WARNING]
        self.assertTrue(len(placeholder_warnings) > 0)
    
    @patch('os.getenv')
    def test_validate_storage_credentials_success(self, mock_getenv):
        """Test successful storage credentials validation."""
        mock_getenv.side_effect = lambda key: {
            'MINIO_ACCESS_KEY': 'test-access-key',
            'MINIO_SECRET_KEY': 'test-secret-key',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_BUCKET': 'test-bucket'
        }.get(key, '')
        
        results = self.validator.validate_storage_credentials()
        
        self.assertTrue(len(results) > 0)
        self.assertTrue(all(r.is_valid for r in results))
    
    def test_validate_vault_configuration_success(self):
        """Test successful Vault configuration validation."""
        with patch.object(self.validator, '_check_vault_availability', return_value=True):
            with patch('src.vault_client.VaultClient') as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                mock_client.authenticate.return_value = True
                mock_client.get_secret.return_value = {"test": "value"}
                
                results = self.validator.validate_vault_configuration()
                
                self.assertTrue(len(results) > 0)
                self.assertTrue(all(r.is_valid for r in results))
    
    def test_validate_vault_configuration_failure(self):
        """Test failed Vault configuration validation."""
        with patch.object(self.validator, '_check_vault_availability', return_value=False):
            results = self.validator.validate_vault_configuration()
            
            self.assertTrue(len(results) > 0)
            self.assertTrue(any(not r.is_valid for r in results))
    
    def test_validate_all(self):
        """Test complete validation process."""
        with patch.object(self.validator, 'validate_vault_configuration', return_value=[
            ValidationResult(True, ValidationLevel.INFO, "Vault OK", "vault")
        ]):
            with patch.object(self.validator, 'validate_database_credentials', return_value=[
                ValidationResult(True, ValidationLevel.INFO, "Database OK", "database")
            ]):
                with patch.object(self.validator, 'validate_api_keys', return_value=[
                    ValidationResult(True, ValidationLevel.INFO, "API Keys OK", "api_keys")
                ]):
                    results = self.validator.validate_all()
                    
                    self.assertTrue(len(results) > 0)
                    self.assertTrue(all(r.is_valid for r in results))


class TestCredentialRotation(unittest.TestCase):
    """Test cases for credential rotation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rotator = CredentialRotator()
    
    def test_rotator_initialization(self):
        """Test rotator initialization."""
        self.assertIsInstance(self.rotator, CredentialRotator)
        self.assertIsInstance(self.rotator.configs, dict)
    
    def test_add_database_rotation(self):
        """Test adding database rotation configuration."""
        self.rotator.add_database_rotation("secret/data/test/db", 24)
        
        self.assertIn("secret/data/test/db", self.rotator.configs)
        config = self.rotator.configs["secret/data/test/db"]
        self.assertEqual(config.rotation_type, RotationType.DATABASE)
        self.assertEqual(config.rotation_interval, 24)
    
    def test_add_api_key_rotation(self):
        """Test adding API key rotation configuration."""
        self.rotator.add_api_key_rotation("secret/data/test/api", 168)
        
        self.assertIn("secret/data/test/api", self.rotator.configs)
        config = self.rotator.configs["secret/data/test/api"]
        self.assertEqual(config.rotation_type, RotationType.API_KEY)
        self.assertEqual(config.rotation_interval, 168)
    
    def test_add_storage_rotation(self):
        """Test adding storage rotation configuration."""
        self.rotator.add_storage_rotation("secret/data/test/storage", 168)
        
        self.assertIn("secret/data/test/storage", self.rotator.configs)
        config = self.rotator.configs["secret/data/test/storage"]
        self.assertEqual(config.rotation_type, RotationType.STORAGE)
        self.assertEqual(config.rotation_interval, 168)
    
    def test_generate_secure_password(self):
        """Test secure password generation."""
        password = self.rotator._generate_secure_password(16)
        
        self.assertEqual(len(password), 16)
        self.assertTrue(any(c.isalpha() for c in password))
        self.assertTrue(any(c.isdigit() for c in password))
        self.assertTrue(any(c in "!@#$%^&*" for c in password))
    
    def test_generate_api_key(self):
        """Test API key generation."""
        api_key = self.rotator._generate_api_key()
        
        self.assertTrue(api_key.startswith("sk-") or api_key.startswith("key-"))
        self.assertEqual(len(api_key), 42)  # prefix + 32 hex chars
    
    def test_generate_access_key(self):
        """Test access key generation."""
        access_key = self.rotator._generate_access_key()
        
        self.assertTrue(access_key.startswith("AKIA"))
        self.assertEqual(len(access_key), 20)  # "AKIA" + 16 hex chars
    
    def test_generate_secret_key(self):
        """Test secret key generation."""
        secret_key = self.rotator._generate_secret_key()
        
        self.assertEqual(len(secret_key), 64)  # 32 hex chars
    
    @patch('src.vault_client.VaultClient')
    def test_rotate_database_credentials_success(self, mock_client_class):
        """Test successful database credential rotation."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_secret.return_value = {"rotation_count": 5}
        
        self.rotator.add_database_rotation("secret/data/test/db")
        
        with patch.object(self.rotator, '_check_vault_availability', return_value=True):
            result = self.rotator._rotate_database_credentials("secret/data/test/db")
            
            self.assertTrue(result)
            mock_client.write_secret.assert_called_once()
    
    @patch('src.vault_client.VaultClient')
    def test_rotate_api_key_success(self, mock_client_class):
        """Test successful API key rotation."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_secret.return_value = {"rotation_count": 3}
        
        self.rotator.add_api_key_rotation("secret/data/test/api")
        
        with patch.object(self.rotator, '_check_vault_availability', return_value=True):
            result = self.rotator._rotate_api_key("secret/data/test/api")
            
            self.assertTrue(result)
            mock_client.write_secret.assert_called_once()
    
    def test_get_rotation_status(self):
        """Test getting rotation status."""
        self.rotator.add_database_rotation("secret/data/test/db", 24)
        self.rotator.add_api_key_rotation("secret/data/test/api", 168)
        
        status = self.rotator.get_rotation_status()
        
        self.assertIn("secret/data/test/db", status)
        self.assertIn("secret/data/test/api", status)
        self.assertEqual(status["secret/data/test/db"]["rotation_type"], "database")
        self.assertEqual(status["secret/data/test/api"]["rotation_type"], "api_key")


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete Vault system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_config_path = os.path.join(self.temp_dir, "vault-config.json")
        
        # Create test configuration
        test_config = {
            "VAULT_ADDR": "http://localhost:8200",
            "VAULT_TOKEN": "s.test_token",
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_USER": "testuser",
            "POSTGRES_PASSWORD": "testpass",
            "POSTGRES_DB": "testdb",
            "OPENROUTER_API_KEY": "sk-test-key-123",
            "BRAVE_API_KEY": "test-brave-key",
            "MINIO_ACCESS_KEY": "test-access-key",
            "MINIO_SECRET_KEY": "test-secret-key",
            "MINIO_ENDPOINT": "localhost:9000",
            "MINIO_BUCKET": "test-bucket"
        }
        
        with open(self.vault_config_path, 'w') as f:
            json.dump(test_config, f, indent=2)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_complete_vault_workflow(self):
        """Test complete Vault workflow from setup to validation."""
        # Set up environment variables
        test_config = {
            "VAULT_ADDR": "http://localhost:8200",
            "VAULT_TOKEN": "s.test_token",
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_USER": "testuser",
            "POSTGRES_PASSWORD": "testpass",
            "POSTGRES_DB": "testdb",
            "OPENROUTER_API_KEY": "sk-test-key-123",
            "BRAVE_API_KEY": "test-brave-key",
            "MINIO_ACCESS_KEY": "test-access-key",
            "MINIO_SECRET_KEY": "test-secret-key",
            "MINIO_ENDPOINT": "localhost:9000",
            "MINIO_BUCKET": "test-bucket"
        }
        
        for key, value in test_config.items():
            os.environ[key] = value
        
        # Test Vault client
        with patch('hvac.Client') as mock_hvac_client:
            mock_client = Mock()
            mock_hvac_client.return_value = mock_client
            mock_client.auth_token.return_value = True
            
            vault_client = VaultClient()
            self.assertTrue(vault_client.authenticate())
            
            # Test writing and reading secrets
            test_secret = {"test": "value", "number": 42}
            vault_client.write_secret("secret/data/test/integration", test_secret)
            
            mock_client.secrets.kv.v2.create_or_update_secret.assert_called_once()
            mock_client.secrets.kv.v2.read_secret_version.return_value = {"data": {"data": test_secret}}
            
            read_secret = vault_client.read_secret("secret/data/test/integration")
            self.assertEqual(read_secret, test_secret)
        
        # Test environment validator
        validator = EnvironmentValidator()
        results = validator.validate_all()
        
        # Should have some valid results even with mocked Vault
        self.assertTrue(len(results) > 0)
        
        # Test credential rotator
        rotator = CredentialRotator()
        rotator.setup_default_rotations()
        
        status = rotator.get_rotation_status()
        self.assertTrue(len(status) > 0)
        
        # Clean up environment variables
        for key in test_config.keys():
            if key in os.environ:
                del os.environ[key]


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)