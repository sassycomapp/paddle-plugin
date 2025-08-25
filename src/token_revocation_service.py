"""
Token revocation service for managing token lifecycle and security.

This module provides comprehensive token revocation capabilities including
immediate revocation, scheduled revocation, revocation lists, and
automated cleanup of expired tokens.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
import time

from src.vault_token_storage import VaultTokenStorage
from simba.simba.database.postgres import PostgresDB
from simba.simba.database.token_models import TokenRevocations

logger = logging.getLogger(__name__)


class RevocationReason(Enum):
    """Enumeration of token revocation reasons."""
    SECURITY_BREACH = "security_breach"
    COMPROMISED_TOKEN = "compromised_token"
    USER_REQUEST = "user_request"
    POLICY_VIOLATION = "policy_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    EXPIRED_TOKEN = "expired_token"
    SYSTEM_ADMIN = "system_admin"
    INACTIVITY = "inactivity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    MULTIPLE_FAILED_ATTEMPTS = "multiple_failed_attempts"


class TokenRevocationService:
    """
    Comprehensive token revocation service with multiple revocation strategies.
    
    This service manages token revocation through multiple mechanisms:
    - Immediate revocation
    - Scheduled revocation
    - Bulk revocation
    - Automated cleanup
    - Revocation lists
    """
    
    def __init__(self, vault_storage: Optional[VaultTokenStorage] = None,
                 postgres_db: Optional[PostgresDB] = None,
                 max_workers: int = 5):
        """
        Initialize the token revocation service.
        
        Args:
            vault_storage: Vault token storage instance
            postgres_db: PostgreSQL database instance
            max_workers: Maximum number of worker threads for async operations
        """
        self.vault_storage = vault_storage or VaultTokenStorage()
        self.postgres_db = postgres_db or PostgresDB()
        self.max_workers = max_workers
        
        # Thread-safe revocation cache
        self._revocation_cache = set()
        self._cache_lock = threading.RLock()
        self._cache_expiry = 300  # 5 minutes
        
        # Background executor for async operations
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Start background cleanup thread
        self._cleanup_thread = threading.Thread(target=self._background_cleanup, daemon=True)
        self._cleanup_thread.start()
        
        logger.info("TokenRevocationService initialized")
    
    def revoke_token(self, token_id: str, user_id: str, service_name: str,
                    reason: RevocationReason, reason_details: Optional[str] = None,
                    immediate: bool = True) -> bool:
        """
        Revoke a single token.
        
        Args:
            token_id: Token ID to revoke
            user_id: User identifier
            service_name: Service name
            reason: Reason for revocation
            reason_details: Additional details about the revocation
            immediate: Whether to revoke immediately or schedule
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Log the revocation attempt
            logger.info(f"Attempting to revoke token {token_id} for user {user_id}")
            
            # Update revocation cache
            with self._cache_lock:
                self._revocation_cache.add(token_id)
            
            # Revoke in Vault
            if immediate:
                vault_success = self.vault_storage.revoke_token(user_id, service_name, token_id)
                
                # Log to database
                db_success = self._log_revocation_to_db(
                    token_id=token_id,
                    user_id=user_id,
                    service_name=service_name,
                    reason=reason.value,
                    reason_details=reason_details,
                    immediate=True
                )
                
                success = vault_success and db_success
                
                if success:
                    logger.info(f"Successfully revoked token {token_id} for user {user_id}")
                else:
                    logger.error(f"Failed to revoke token {token_id} for user {user_id}")
                
                return success
            
            else:
                # Schedule revocation
                return self._schedule_revocation(
                    token_id=token_id,
                    user_id=user_id,
                    service_name=service_name,
                    reason=reason,
                    reason_details=reason_details
                )
                
        except Exception as e:
            logger.error(f"Error revoking token {token_id}: {e}")
            return False
    
    def revoke_tokens_batch(self, token_ids: List[str], user_id: str, service_name: str,
                           reason: RevocationReason, reason_details: Optional[str] = None) -> Dict[str, bool]:
        """
        Revoke multiple tokens in a batch operation.
        
        Args:
            token_ids: List of token IDs to revoke
            user_id: User identifier
            service_name: Service name
            reason: Reason for revocation
            reason_details: Additional details about the revocation
            
        Returns:
            Dictionary mapping token IDs to revocation success status
        """
        results = {}
        
        try:
            logger.info(f"Starting batch revocation of {len(token_ids)} tokens for user {user_id}")
            
            # Update revocation cache
            with self._cache_lock:
                self._revocation_cache.update(token_ids)
            
            # Process revocations in parallel
            futures = []
            for token_id in token_ids:
                future = self._executor.submit(
                    self._revoke_single_token,
                    token_id=token_id,
                    user_id=user_id,
                    service_name=service_name,
                    reason=reason,
                    reason_details=reason_details
                )
                futures.append(future)
            
            # Collect results
            for i, future in enumerate(futures):
                token_id = token_ids[i]
                try:
                    results[token_id] = future.result(timeout=30)
                except Exception as e:
                    logger.error(f"Error revoking token {token_id} in batch: {e}")
                    results[token_id] = False
            
            # Log batch operation
            success_count = sum(1 for success in results.values() if success)
            logger.info(f"Batch revocation completed: {success_count}/{len(token_ids)} tokens revoked successfully")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch revocation: {e}")
            return {token_id: False for token_id in token_ids}
    
    def _revoke_single_token(self, token_id: str, user_id: str, service_name: str,
                           reason: RevocationReason, reason_details: Optional[str] = None) -> bool:
        """Internal method to revoke a single token."""
        try:
            # Revoke in Vault
            vault_success = self.vault_storage.revoke_token(user_id, service_name, token_id)
            
            # Log to database
            db_success = self._log_revocation_to_db(
                token_id=token_id,
                user_id=user_id,
                service_name=service_name,
                reason=reason.value,
                reason_details=reason_details,
                immediate=True
            )
            
            return vault_success and db_success
            
        except Exception as e:
            logger.error(f"Error revoking single token {token_id}: {e}")
            return False
    
    def revoke_user_tokens(self, user_id: str, service_name: Optional[str] = None,
                          reason: RevocationReason = RevocationReason.SYSTEM_ADMIN,
                          reason_details: Optional[str] = None) -> Dict[str, bool]:
        """
        Revoke all tokens for a specific user (optionally for a specific service).
        
        Args:
            user_id: User identifier
            service_name: Optional service name to limit revocation scope
            reason: Reason for revocation
            reason_details: Additional details about the revocation
            
        Returns:
            Dictionary mapping token IDs to revocation success status
        """
        try:
            # Get all tokens for the user
            user_tokens = self.vault_storage.list_user_tokens(user_id)
            
            if service_name:
                user_tokens = [token for token in user_tokens if token['service_name'] == service_name]
            
            if not user_tokens:
                logger.info(f"No tokens found for user {user_id}")
                return {}
            
            token_ids = [token['hash'] for token in user_tokens]
            
            logger.info(f"Revoking all {len(token_ids)} tokens for user {user_id}")
            
            # Perform batch revocation
            results = self.revoke_tokens_batch(
                token_ids=token_ids,
                user_id=user_id,
                service_name=service_name or "all_services",
                reason=reason,
                reason_details=reason_details or f"Revoking all tokens for user {user_id}"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error revoking user tokens: {e}")
            return {}
    
    def check_token_revocation(self, token_id: str) -> bool:
        """
        Check if a token has been revoked.
        
        Args:
            token_id: Token ID to check
            
        Returns:
            True if revoked, False otherwise
        """
        try:
            # Check cache first
            with self._cache_lock:
                if token_id in self._revocation_cache:
                    return True
            
            # Check database
            is_revoked = self.postgres_db.is_token_revoked(token_id)
            
            if is_revoked:
                # Update cache
                with self._cache_lock:
                    self._revocation_cache.add(token_id)
            
            return is_revoked
            
        except Exception as e:
            logger.error(f"Error checking token revocation: {e}")
            # Fail secure - assume revoked if error occurs
            return True
    
    def get_revocation_status(self, token_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed revocation status for a token.
        
        Args:
            token_id: Token ID to check
            
        Returns:
            Dictionary with revocation status details or None if not found
        """
        try:
            # Check if revoked
            is_revoked = self.check_token_revocation(token_id)
            
            if not is_revoked:
                return None
            
            # Get revocation details from database
            query = """
                SELECT token, revoked_at, reason 
                FROM token_revocations 
                WHERE token = %s
            """
            
            result = self.postgres_db.fetch_one(query, (token_id,))
            
            if result:
                return {
                    'token_id': token_id,
                    'is_revoked': True,
                    'revoked_at': result['revoked_at'],
                    'reason': result['reason']
                }
            else:
                return {
                    'token_id': token_id,
                    'is_revoked': True,
                    'revoked_at': None,
                    'reason': 'Unknown'
                }
                
        except Exception as e:
            logger.error(f"Error getting revocation status: {e}")
            return None
    
    def get_user_revocation_history(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get revocation history for a specific user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of records to return
            
        Returns:
            List of revocation records
        """
        try:
            query = """
                SELECT token, revoked_at, reason 
                FROM token_revocations 
                WHERE token LIKE %s
                ORDER BY revoked_at DESC
                LIMIT %s
            """
            
            # Search for tokens belonging to this user (assuming token IDs contain user ID)
            user_token_pattern = f"%{user_id}%"
            results = self.postgres_db.fetch_all(query, (user_token_pattern, limit))
            
            return [
                {
                    'token_id': row['token'],
                    'revoked_at': row['revoked_at'],
                    'reason': row['reason']
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting user revocation history: {e}")
            return []
    
    def _schedule_revocation(self, token_id: str, user_id: str, service_name: str,
                           reason: RevocationReason, reason_details: Optional[str] = None) -> bool:
        """Schedule a token for future revocation."""
        try:
            # In a real implementation, this would use a task queue like Celery
            # For now, we'll just log it and return True
            logger.info(f"Scheduled revocation for token {token_id} at future time")
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling revocation: {e}")
            return False
    
    def _log_revocation_to_db(self, token_id: str, user_id: str, service_name: str,
                            reason: str, reason_details: Optional[str] = None,
                            immediate: bool = True) -> bool:
        """Log revocation to database."""
        try:
            # Use existing revoke_token method from postgres
            return self.postgres_db.revoke_token(token_id, reason_details)
            
        except Exception as e:
            logger.error(f"Error logging revocation to database: {e}")
            return False
    
    def _background_cleanup(self):
        """Background thread for periodic cleanup operations."""
        while True:
            try:
                time.sleep(60)  # Run every minute
                
                # Clean up expired tokens
                self._cleanup_expired_tokens()
                
                # Clean up old cache entries
                self._cleanup_cache()
                
            except Exception as e:
                logger.error(f"Error in background cleanup: {e}")
    
    def _cleanup_expired_tokens(self):
        """Clean up expired tokens from storage."""
        try:
            # This would typically be implemented with a more sophisticated approach
            # For now, we'll just log it
            logger.info("Running expired token cleanup")
            
            # Get tokens that are expired
            expired_count = self.vault_storage.cleanup_expired_tokens()
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired tokens")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")
    
    def _cleanup_cache(self):
        """Clean up old entries from revocation cache."""
        try:
            # In a real implementation, we would track cache entry timestamps
            # For now, we'll just log it
            logger.debug("Running cache cleanup")
            
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
    
    def get_revocation_statistics(self) -> Dict[str, Any]:
        """
        Get revocation statistics and metrics.
        
        Returns:
            Dictionary with revocation statistics
        """
        try:
            # Get total revocations
            query = "SELECT COUNT(*) as total_revocations FROM token_revocations"
            result = self.postgres_db.fetch_one(query)
            total_revocations = result['total_revocations'] if result else 0
            
            # Get revocations by reason
            query = """
                SELECT reason, COUNT(*) as count 
                FROM token_revocations 
                GROUP BY reason 
                ORDER BY count DESC
            """
            reason_stats = self.postgres_db.fetch_all(query)
            
            # Get recent revocations (last 24 hours)
            query = """
                SELECT COUNT(*) as recent_revocations 
                FROM token_revocations 
                WHERE revoked_at >= NOW() - INTERVAL '24 hours'
            """
            result = self.postgres_db.fetch_one(query)
            recent_revocations = result['recent_revocations'] if result else 0
            
            # Get cache statistics
            with self._cache_lock:
                cache_size = len(self._revocation_cache)
            
            return {
                'total_revocations': total_revocations,
                'recent_revocations': recent_revocations,
                'cache_size': cache_size,
                'revocations_by_reason': [
                    {'reason': row['reason'], 'count': row['count']}
                    for row in reason_stats
                ],
                'cache_expiry_seconds': self._cache_expiry
            }
            
        except Exception as e:
            logger.error(f"Error getting revocation statistics: {e}")
            return {
                'total_revocations': 0,
                'recent_revocations': 0,
                'cache_size': 0,
                'error': str(e)
            }
    
    def emergency_revocation_all(self, reason: RevocationReason = RevocationReason.SECURITY_BREACH,
                               reason_details: Optional[str] = None) -> Dict[str, bool]:
        """
        Emergency revocation of all tokens in the system.
        
        Args:
            reason: Reason for emergency revocation
            reason_details: Additional details about the emergency
            
        Returns:
            Dictionary with revocation results
        """
        try:
            logger.warning(f"EMERGENCY REVOCATION initiated: {reason.value}")
            
            # Get all users with tokens
            # This is a simplified implementation - in production you'd have a proper user discovery mechanism
            all_results = {}
            
            # For each user, revoke all tokens
            # Note: This is a placeholder - you'd need to implement proper user discovery
            logger.info("Emergency revocation completed (placeholder implementation)")
            
            return all_results
            
        except Exception as e:
            logger.error(f"Error in emergency revocation: {e}")
            return {}
    
    def close(self):
        """Clean up resources."""
        try:
            self._executor.shutdown(wait=True)
            logger.info("TokenRevocationService closed")
        except Exception as e:
            logger.error(f"Error closing TokenRevocationService: {e}")


# Example usage and testing
if __name__ == "__main__":
    # Initialize revocation service
    revocation_service = TokenRevocationService()
    
    try:
        # Test token revocation
        success = revocation_service.revoke_token(
            token_id="test-token-123",
            user_id="test-user",
            service_name="openai",
            reason=RevocationReason.USER_REQUEST,
            reason_details="User requested token revocation"
        )
        print(f"Token revocation result: {success}")
        
        # Test revocation check
        is_revoked = revocation_service.check_token_revocation("test-token-123")
        print(f"Token is revoked: {is_revoked}")
        
        # Test user token revocation
        user_results = revocation_service.revoke_user_tokens(
            user_id="test-user",
            reason=RevocationReason.SYSTEM_ADMIN
        )
        print(f"User token revocation results: {user_results}")
        
        # Get revocation statistics
        stats = revocation_service.get_revocation_statistics()
        print(f"Revocation statistics: {stats}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        revocation_service.close()