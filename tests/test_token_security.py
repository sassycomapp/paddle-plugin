"""
Comprehensive test suite for token security system.

This module provides comprehensive tests for all security components including
secure token storage, revocation services, content filtering, and the main
security manager.
"""

import unittest
import pytest
import uuid
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Import the security modules
from src.vault_token_storage import VaultTokenStorage
from src.token_revocation_service import TokenRevocationService, RevocationReason
from src.sensitive_content_filter import SensitiveContentFilter, FilterType, FilterAction
from src.token_security_manager import TokenSecurityManager, SecurityContext, SecurityLevel
from simba.simba.database.postgres import PostgresDB


class TestVaultTokenStorage(unittest.TestCase):
    """Test cases for VaultTokenStorage."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.vault_storage = VaultTokenStorage()
        self.test_user_id = "test-user"
        self.test_service_name = "test-service"
        self.test_token = "sk-test123456789"
    
    @patch('src.vault_token_storage.hvac.Client')
    def test_store_token_securely(self, mock_vault_client):
        """Test storing tokens securely in Vault."""
        # Mock Vault client
        mock_client = Mock()
        mock_vault_client.return_value = mock_client
        
        # Test token storage
        result = self.vault_storage.store_token_securely(
            user_id=self.test_user_id,
            service_name=self.test_service_name,
            token=self.test_token,
            token_type="api_key"
        )
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        
        # Verify Vault client was called
        mock_client.secrets.kv.v2.create_or_update_secret.assert_called_once()
    
    @patch('src.vault_token_storage.hvac.Client')
    def test_retrieve_token_securely(self, mock_vault_client):
        """Test retrieving tokens securely from Vault."""
        # Mock Vault client
        mock_client = Mock()
        mock_vault_client.return_value = mock_client
        
        # Mock token data
        mock_data = {
            'data': {
                'token': self.test_token,
                'metadata': {'type': 'api_key'}
            }
        }
        mock_client.secrets.kv.v2.read_secret_version.return_value = mock_data
        
        # Test token retrieval
        result = self.vault_storage.retrieve_token_securely(
            user_id=self.test_user_id,
            service_name=self.test_service_name
        )
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result['token'], self.test_token)
        
        # Verify Vault client was called
        mock_client.secrets.kv.v2.read_secret_version.assert_called_once()
    
    @patch('src.vault_token_storage.hvac.Client')
    def test_revoke_token(self, mock_vault_client):
        """Test token revocation in Vault."""
        # Mock Vault client
        mock_client = Mock()
        mock_vault_client.return_value = mock_client
        
        # Test token revocation
        result = self.vault_storage.revoke_token(
            user_id=self.test_user_id,
            service_name=self.test_service_name,
            token_id="test-token-id"
        )
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify Vault client was called
        mock_client.secrets.kv.v2.create_or_update_secret.assert_called_once()
    
    @patch('src.vault_token_storage.hvac.Client')
    def test_list_user_tokens(self, mock_vault_client):
        """Test listing user tokens from Vault."""
        # Mock Vault client
        mock_client = Mock()
        mock_vault_client.return_value = mock_client
        
        # Mock token list
        mock_list = {
            'data': {
                'keys': ['token1', 'token2', 'token3']
            }
        }
        mock_client.secrets.kv.v2.list_secrets.return_value = mock_list
        
        # Test token listing
        result = self.vault_storage.list_user_tokens(self.test_user_id)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        
        # Verify Vault client was called
        mock_client.secrets.kv.v2.list_secrets.assert_called_once()


class TestTokenRevocationService(unittest.TestCase):
    """Test cases for TokenRevocationService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.revocation_service = TokenRevocationService()
        self.test_token_id = "test-token-123"
        self.test_user_id = "test-user"
        self.test_service_name = "test-service"
    
    @patch('src.token_revocation_service.VaultTokenStorage')
    @patch('src.token_revocation_service.PostgresDB')
    def test_revoke_token(self, mock_postgres, mock_vault):
        """Test token revocation."""
        # Mock dependencies
        mock_vault_instance = Mock()
        mock_postgres_instance = Mock()
        mock_vault.return_value = mock_vault_instance
        mock_postgres.return_value = mock_postgres_instance
        
        # Mock successful Vault revocation
        mock_vault_instance.revoke_token.return_value = True
        
        # Test token revocation
        result = self.revocation_service.revoke_token(
            token_id=self.test_token_id,
            user_id=self.test_user_id,
            service_name=self.test_service_name,
            reason=RevocationReason.USER_REQUEST
        )
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify Vault was called
        mock_vault_instance.revoke_token.assert_called_once()
    
    def test_check_token_revocation(self):
        """Test checking token revocation status."""
        # Test with non-revoked token
        result = self.revocation_service.check_token_revocation("non-revoked-token")
        
        # Should return False (not revoked)
        self.assertFalse(result)
    
    def test_revoke_user_tokens(self):
        """Test revoking all tokens for a user."""
        # Mock the list_user_tokens method
        with patch.object(self.revocation_service, 'list_user_tokens') as mock_list:
            mock_list.return_value = [
                {'hash': 'token1', 'service_name': 'service1'},
                {'hash': 'token2', 'service_name': 'service2'}
            ]
            
            # Mock the revoke_tokens_batch method
            with patch.object(self.revocation_service, 'revoke_tokens_batch') as mock_revoke:
                mock_revoke.return_value = {'token1': True, 'token2': True}
                
                # Test user token revocation
                result = self.revocation_service.revoke_user_tokens(
                    user_id=self.test_user_id,
                    service_name="all_services"
                )
                
                # Verify the result
                self.assertEqual(len(result), 2)
                self.assertTrue(all(result.values()))
    
    def test_get_revocation_statistics(self):
        """Test getting revocation statistics."""
        # Mock database fetch
        with patch.object(self.revocation_service.postgres_db, 'fetch_one') as mock_fetch:
            mock_fetch.return_value = {'total_revocations': 10}
            
            # Mock fetch_all for reason statistics
            with patch.object(self.revocation_service.postgres_db, 'fetch_all') as mock_fetch_all:
                mock_fetch_all.return_value = [
                    {'reason': 'user_request', 'count': 5},
                    {'reason': 'security_breach', 'count': 5}
                ]
                
                # Test getting statistics
                result = self.revocation_service.get_revocation_statistics()
                
                # Verify the result
                self.assertIsInstance(result, dict)
                self.assertIn('total_revocations', result)
                self.assertIn('recent_revocations', result)
                self.assertIn('cache_size', result)
                self.assertIn('revocations_by_reason', result)


class TestSensitiveContentFilter(unittest.TestCase):
    """Test cases for SensitiveContentFilter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.content_filter = SensitiveContentFilter()
        self.test_content = """
        Contact me at john.doe@example.com or call 555-123-4567.
        My API key is sk-1234567890abcdef1234567890abcdef.
        Password: mysecretpassword123
        """
    
    def test_filter_content_pii(self):
        """Test PII filtering."""
        result = self.content_filter.filter_content(
            content=self.test_content,
            filter_types=[FilterType.PII],
            action=FilterAction.SANITIZE
        )
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIn('[EMAIL]', result.filtered_content)
        self.assertIn('[PHONE]', result.filtered_content)
        self.assertTrue(len(result.violations) > 0)
    
    def test_filter_content_sensitive_data(self):
        """Test sensitive data filtering."""
        result = self.content_filter.filter_content(
            content=self.test_content,
            filter_types=[FilterType.SENSITIVE_DATA],
            action=FilterAction.SANITIZE
        )
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIn('[API_KEY_REDACTED]', result.filtered_content)
        self.assertIn('[PASSWORD_REDACTED]', result.filtered_content)
        self.assertTrue(len(result.violations) > 0)
    
    def test_filter_content_malicious(self):
        """Test malicious content filtering."""
        malicious_content = """
        <script>alert('xss')</script>
        javascript:malicious();
        """
        
        result = self.content_filter.filter_content(
            content=malicious_content,
            filter_types=[FilterType.MALICIOUS_CONTENT],
            action=FilterAction.BLOCK
        )
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIn('[CONTENT_BLOCKED_DUE_TO_SECURITY_VIOLATION]', result.filtered_content)
    
    def test_detect_sensitive_patterns(self):
        """Test sensitive pattern detection."""
        result = self.content_filter.detect_sensitive_patterns(self.test_content)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIn('pii_detected', result)
        self.assertIn('sensitive_data_detected', result)
        self.assertIn('total_violations', result)
        self.assertIn('risk_score', result)
        
        # Check that violations were detected
        self.assertTrue(result['total_violations'] > 0)
        self.assertTrue(result['risk_score'] > 0)
    
    def test_sanitize_input(self):
        """Test input sanitization."""
        test_input = "  Hello\t\nWorld  "
        sanitized = self.content_filter.sanitize_input(test_input)
        
        # Verify the result
        self.assertEqual(sanitized, "Hello World")
    
    def test_batch_filter_content(self):
        """Test batch content filtering."""
        contents = [
            "Email: test@example.com",
            "API Key: sk-test123456789",
            "Normal text"
        ]
        
        results = self.content_filter.batch_filter_content(contents)
        
        # Verify the results
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsNotNone(result)
            self.assertIsInstance(result.filtered_content, str)
    
    def test_get_filter_statistics(self):
        """Test getting filter statistics."""
        stats = self.content_filter.get_filter_statistics()
        
        # Verify the result
        self.assertIsNotNone(stats)
        self.assertIn('filters_enabled', stats)
        self.assertIn('pattern_counts', stats)
        self.assertIn('cache_info', stats)


class TestTokenSecurityManager(unittest.TestCase):
    """Test cases for TokenSecurityManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.security_manager = TokenSecurityManager()
        self.test_user_id = "test-user"
        self.test_service_name = "test-service"
        self.test_token = "sk-test123456789"
        
        # Create security context
        self.security_context = SecurityContext(
            user_id=self.test_user_id,
            session_id="test-session",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            security_level=SecurityLevel.MEDIUM,
            permissions=["read", "write"],
            timestamp=datetime.utcnow()
        )
    
    @patch('src.token_security_manager.VaultTokenStorage')
    @patch('src.token_security_service.TokenRevocationService')
    @patch('src.token_security_manager.SensitiveContentFilter')
    @patch('src.token_security_manager.PostgresDB')
    def test_store_token_securely(self, mock_postgres, mock_filter, mock_revocation, mock_vault):
        """Test secure token storage."""
        # Mock dependencies
        mock_vault_instance = Mock()
        mock_revocation_instance = Mock()
        mock_filter_instance = Mock()
        mock_postgres_instance = Mock()
        
        mock_vault.return_value = mock_vault_instance
        mock_revocation.return_value = mock_revocation_instance
        mock_filter.return_value = mock_filter_instance
        mock_postgres.return_value = mock_postgres_instance
        
        # Mock successful token storage
        mock_vault_instance.store_token_securely.return_value = "token-id-123"
        
        # Test token storage
        result = self.security_manager.store_token_securely(
            user_id=self.test_user_id,
            service_name=self.test_service_name,
            token=self.test_token,
            security_context=self.security_context
        )
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        
        # Verify Vault was called
        mock_vault_instance.store_token_securely.assert_called_once()
    
    @patch('src.token_security_manager.VaultTokenStorage')
    @patch('src.token_security_service.TokenRevocationService')
    @patch('src.token_security_manager.SensitiveContentFilter')
    @patch('src.token_security_manager.PostgresDB')
    def test_retrieve_token_securely(self, mock_postgres, mock_filter, mock_revocation, mock_vault):
        """Test secure token retrieval."""
        # Mock dependencies
        mock_vault_instance = Mock()
        mock_revocation_instance = Mock()
        mock_filter_instance = Mock()
        mock_postgres_instance = Mock()
        
        mock_vault.return_value = mock_vault_instance
        mock_revocation.return_value = mock_revocation_instance
        mock_filter.return_value = mock_filter_instance
        mock_postgres.return_value = mock_postgres_instance
        
        # Mock successful token retrieval
        mock_vault_instance.retrieve_token_securely.return_value = {
            'token': self.test_token,
            'metadata': {'type': 'api_key'}
        }
        
        # Test token retrieval
        result = self.security_manager.retrieve_token_securely(
            user_id=self.test_user_id,
            service_name=self.test_service_name,
            security_context=self.security_context
        )
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result['token'], self.test_token)
        
        # Verify Vault was called
        mock_vault_instance.retrieve_token_securely.assert_called_once()
    
    @patch('src.token_security_manager.VaultTokenStorage')
    @patch('src.token_security_service.TokenRevocationService')
    @patch('src.token_security_manager.SensitiveContentFilter')
    @patch('src.token_security_manager.PostgresDB')
    def test_revoke_token(self, mock_postgres, mock_filter, mock_revocation, mock_vault):
        """Test token revocation."""
        # Mock dependencies
        mock_vault_instance = Mock()
        mock_revocation_instance = Mock()
        mock_filter_instance = Mock()
        mock_postgres_instance = Mock()
        
        mock_vault.return_value = mock_vault_instance
        mock_revocation.return_value = mock_revocation_instance
        mock_filter.return_value = mock_filter_instance
        mock_postgres.return_value = mock_postgres_instance
        
        # Mock successful token revocation
        mock_revocation_instance.revoke_token.return_value = True
        
        # Test token revocation
        result = self.security_manager.revoke_token(
            user_id=self.test_user_id,
            service_name=self.test_service_name,
            token_id="test-token-id",
            reason=RevocationReason.USER_REQUEST,
            security_context=self.security_context
        )
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify revocation service was called
        mock_revocation_instance.revoke_token.assert_called_once()
    
    @patch('src.token_security_manager.VaultTokenStorage')
    @patch('src.token_security_service.TokenRevocationService')
    @patch('src.token_security_manager.SensitiveContentFilter')
    @patch('src.token_security_manager.PostgresDB')
    def test_filter_sensitive_content(self, mock_postgres, mock_filter, mock_revocation, mock_vault):
        """Test sensitive content filtering."""
        # Mock dependencies
        mock_vault_instance = Mock()
        mock_revocation_instance = Mock()
        mock_filter_instance = Mock()
        mock_postgres_instance = Mock()
        
        mock_vault.return_value = mock_vault_instance
        mock_revocation.return_value = mock_revocation_instance
        mock_filter.return_value = mock_filter_instance
        mock_postgres.return_value = mock_postgres_instance
        
        # Mock content filter result
        mock_result = Mock()
        mock_result.filtered_content = "Filtered content"
        mock_result.violations = ["PII detected"]
        mock_result.confidence_scores = {"email": 0.95}
        mock_filter_instance.filter_content.return_value = mock_result
        
        # Test content filtering
        result = self.security_manager.filter_sensitive_content(
            content="test content with email@example.com",
            filter_types=["pii"],
            action="sanitize",
            security_context=self.security_context
        )
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result['filtered_content'], "Filtered content")
        self.assertIn('violations', result)
        self.assertIn('confidence_scores', result)
        
        # Verify content filter was called
        mock_filter_instance.filter_content.assert_called_once()
    
    def test_get_security_metrics(self):
        """Test getting security metrics."""
        metrics = self.security_manager.get_security_metrics()
        
        # Verify the result
        self.assertIsNotNone(metrics)
        self.assertIsInstance(metrics, type(self.security_manager.security_metrics))
        self.assertIn('total_tokens', metrics.__dict__)
        self.assertIn('active_tokens', metrics.__dict__)
        self.assertIn('revoked_tokens', metrics.__dict__)
        self.assertIn('security_events', metrics.__dict__)
        self.assertIn('violations', metrics.__dict__)
    
    def test_get_security_report(self):
        """Test getting security report."""
        report = self.security_manager.get_security_report()
        
        # Verify the result
        self.assertIsNotNone(report)
        self.assertIsInstance(report, dict)
        self.assertIn('metrics', report)
        self.assertIn('timestamp', report)
    
    def test_emergency_shutdown(self):
        """Test emergency shutdown."""
        # This is a difficult test to implement properly without mocking
        # the actual shutdown behavior, but we can at least verify it doesn't crash
        try:
            self.security_manager.emergency_shutdown()
            # If we get here, the shutdown didn't crash
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Emergency shutdown failed: {e}")


class TestSecurityIntegration(unittest.TestCase):
    """Integration tests for the complete security system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_user_id = "integration-test-user"
        self.test_service_name = "integration-test-service"
        self.test_token = "sk-integration-test-123456789"
    
    @patch('src.token_security_manager.VaultTokenStorage')
    @patch('src.token_security_service.TokenRevocationService')
    @patch('src.token_security_manager.SensitiveContentFilter')
    @patch('src.token_security_manager.PostgresDB')
    def test_complete_token_lifecycle(self, mock_postgres, mock_filter, mock_revocation, mock_vault):
        """Test complete token lifecycle from creation to revocation."""
        # Mock dependencies
        mock_vault_instance = Mock()
        mock_revocation_instance = Mock()
        mock_filter_instance = Mock()
        mock_postgres_instance = Mock()
        
        mock_vault.return_value = mock_vault_instance
        mock_revocation.return_value = mock_revocation_instance
        mock_filter.return_value = mock_filter_instance
        mock_postgres.return_value = mock_postgres_instance
        
        # Mock successful operations
        mock_vault_instance.store_token_securely.return_value = "integration-token-id"
        mock_vault_instance.retrieve_token_securely.return_value = {
            'token': self.test_token,
            'metadata': {'type': 'api_key'}
        }
        mock_revocation_instance.revoke_token.return_value = True
        mock_revocation_instance.check_token_revocation.return_value = False
        
        # Create security manager
        security_manager = TokenSecurityManager(
            vault_storage=mock_vault_instance,
            revocation_service=mock_revocation_instance,
            content_filter=mock_filter_instance,
            postgres_db=mock_postgres_instance
        )
        
        # Create security context
        security_context = SecurityContext(
            user_id=self.test_user_id,
            session_id="integration-test-session",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            security_level=SecurityLevel.MEDIUM,
            permissions=["read", "write"],
            timestamp=datetime.utcnow()
        )
        
        # Step 1: Store token
        token_id = security_manager.store_token_securely(
            user_id=self.test_user_id,
            service_name=self.test_service_name,
            token=self.test_token,
            security_context=security_context
        )
        self.assertIsNotNone(token_id)
        
        # Step 2: Retrieve token
        token_data = security_manager.retrieve_token_securely(
            user_id=self.test_user_id,
            service_name=self.test_service_name,
            security_context=security_context
        )
        self.assertEqual(token_data['token'], self.test_token)
        
        # Step 3: Revoke token
        revoke_success = security_manager.revoke_token(
            user_id=self.test_user_id,
            service_name=self.test_service_name,
            token_id=token_id,
            reason=RevocationReason.USER_REQUEST,
            security_context=security_context
        )
        self.assertTrue(revoke_success)
        
        # Step 4: Try to retrieve revoked token (should fail)
        mock_revocation_instance.check_token_revocation.return_value = True
        try:
            security_manager.retrieve_token_securely(
                user_id=self.test_user_id,
                service_name=self.test_service_name,
                security_context=security_context
            )
            self.fail("Expected exception when retrieving revoked token")
        except Exception as e:
            self.assertIn("revoked", str(e).lower())
        
        # Clean up
        security_manager.close()
    
    @patch('src.token_security_manager.VaultTokenStorage')
    @patch('src.token_security_service.TokenRevocationService')
    @patch('src.token_security_manager.SensitiveContentFilter')
    @patch('src.token_security_manager.PostgresDB')
    def test_content_filtering_integration(self, mock_postgres, mock_filter, mock_revocation, mock_vault):
        """Test content filtering integration with security manager."""
        # Mock dependencies
        mock_vault_instance = Mock()
        mock_revocation_instance = Mock()
        mock_filter_instance = Mock()
        mock_postgres_instance = Mock()
        
        mock_vault.return_value = mock_vault_instance
        mock_revocation.return_value = mock_revocation_instance
        mock_filter.return_value = mock_filter_instance
        mock_postgres.return_value = mock_postgres_instance
        
        # Mock content filter result
        mock_result = Mock()
        mock_result.filtered_content = "Content with [EMAIL] redacted"
        mock_result.violations = ["PII detected"]
        mock_result.confidence_scores = {"email": 0.95}
        mock_filter_instance.filter_content.return_value = mock_result
        
        # Create security manager
        security_manager = TokenSecurityManager(
            vault_storage=mock_vault_instance,
            revocation_service=mock_revocation_instance,
            content_filter=mock_filter_instance,
            postgres_db=mock_postgres_instance
        )
        
        # Test content filtering
        test_content = "Contact me at john@example.com"
        result = security_manager.filter_sensitive_content(
            content=test_content,
            filter_types=["pii"],
            action="sanitize"
        )
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result['filtered_content'], "Content with [EMAIL] redacted")
        self.assertIn('violations', result)
        self.assertTrue(len(result['violations']) > 0)
        
        # Clean up
        security_manager.close()


class TestSecurityPerformance(unittest.TestCase):
    """Performance tests for the security system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_user_id = "performance-test-user"
        self.test_service_name = "performance-test-service"
        self.test_token = "sk-performance-test-123456789"
    
    @patch('src.token_security_manager.VaultTokenStorage')
    @patch('src.token_security_service.TokenRevocationService')
    @patch('src.token_security_manager.SensitiveContentFilter')
    @patch('src.token_security_manager.PostgresDB')
    def test_token_storage_performance(self, mock_postgres, mock_filter, mock_revocation, mock_vault):
        """Test token storage performance."""
        # Mock dependencies
        mock_vault_instance = Mock()
        mock_revocation_instance = Mock()
        mock_filter_instance = Mock()
        mock_postgres_instance = Mock()
        
        mock_vault.return_value = mock_vault_instance
        mock_revocation.return_value = mock_revocation_instance
        mock_filter.return_value = mock_filter_instance
        mock_postgres.return_value = mock_postgres_instance
        
        # Mock successful operations
        mock_vault_instance.store_token_securely.return_value = "performance-token-id"
        
        # Create security manager
        security_manager = TokenSecurityManager(
            vault_storage=mock_vault_instance,
            revocation_service=mock_revocation_instance,
            content_filter=mock_filter_instance,
            postgres_db=mock_postgres_instance
        )
        
        # Create security context
        security_context = SecurityContext(
            user_id=self.test_user_id,
            session_id="performance-test-session",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            security_level=SecurityLevel.MEDIUM,
            permissions=["read", "write"],
            timestamp=datetime.utcnow()
        )
        
        # Test performance
        start_time = time.time()
        iterations = 100
        
        for i in range(iterations):
            security_manager.store_token_securely(
                user_id=self.test_user_id,
                service_name=self.test_service_name,
                token=f"{self.test_token}-{i}",
                security_context=security_context
            )
        
        end_time = time.time()
        avg_time = (end_time - start_time) / iterations
        
        # Verify performance (should be under 1 second per operation)
        self.assertLess(avg_time, 1.0)
        
        # Clean up
        security_manager.close()
    
    @patch('src.token_security_manager.VaultTokenStorage')
    @patch('src.token_security_service.TokenRevocationService')
    @patch('src.token_security_manager.SensitiveContentFilter')
    @patch('src.token_security_manager.PostgresDB')
    def test_content_filtering_performance(self, mock_postgres, mock_filter, mock_revocation, mock_vault):
        """Test content filtering performance."""
        # Mock dependencies
        mock_vault_instance = Mock()
        mock_revocation_instance = Mock()
        mock_filter_instance = Mock()
        mock_postgres_instance = Mock()
        
        mock_vault.return_value = mock_vault_instance
        mock_revocation.return_value = mock_revocation_instance
        mock_filter.return_value = mock_filter_instance
        mock_postgres.return_value = mock_postgres_instance
        
        # Mock content filter result
        mock_result = Mock()
        mock_result.filtered_content = "Filtered content"
        mock_result.violations = []
        mock_result.confidence_scores = {}
        mock_filter_instance.filter_content.return_value = mock_result
        
        # Create security manager
        security_manager = TokenSecurityManager(
            vault_storage=mock_vault_instance,
            revocation_service=mock_revocation_instance,
            content_filter=mock_filter_instance,
            postgres_db=mock_postgres_instance
        )
        
        # Test performance
        start_time = time.time()
        iterations = 100
        
        for i in range(iterations):
            security_manager.filter_sensitive_content(
                content=f"Test content {i} with email@example.com",
                filter_types=["pii"],
                action="sanitize"
            )
        
        end_time = time.time()
        avg_time = (end_time - start_time) / iterations
        
        # Verify performance (should be under 0.5 seconds per operation)
        self.assertLess(avg_time, 0.5)
        
        # Clean up
        security_manager.close()


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)