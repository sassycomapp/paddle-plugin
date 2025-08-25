"""
Comprehensive token security manager integrating all security components.

This module provides the main security and token management system that
coordinates between secure storage, revocation services, content filtering,
and monitoring capabilities.
"""

import logging
import uuid
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Callable
from enum import Enum
from dataclasses import dataclass
from functools import wraps
import threading
from concurrent.futures import ThreadPoolExecutor
import json

from src.vault_token_storage import VaultTokenStorage
from src.token_revocation_service import TokenRevocationService, RevocationReason
from src.sensitive_content_filter import SensitiveContentFilter, FilterType, FilterAction
from simba.simba.database.postgres import PostgresDB

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for different operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEvent(Enum):
    """Types of security events."""
    TOKEN_CREATED = "token_created"
    TOKEN_RETRIEVED = "token_retrieved"
    TOKEN_REVOKED = "token_revoked"
    TOKEN_RENEWED = "token_renewed"
    SECURITY_VIOLATION = "security_violation"
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_FAILURE = "authorization_failure"
    DATA_ACCESS = "data_access"
    CONFIGURATION_CHANGE = "configuration_change"


@dataclass
class SecurityContext:
    """Security context for operations."""
    user_id: str
    session_id: str
    ip_address: str
    user_agent: str
    security_level: SecurityLevel
    permissions: List[str]
    timestamp: datetime


@dataclass
class SecurityMetrics:
    """Security metrics and monitoring data."""
    total_tokens: int
    active_tokens: int
    revoked_tokens: int
    security_events: int
    violations: int
    average_response_time: float
    uptime_percentage: float
    last_audit: datetime


class TokenSecurityManager:
    """
    Main token security manager coordinating all security components.
    
    This class integrates secure token storage, revocation services,
    content filtering, and security monitoring into a comprehensive
    security management system.
    """
    
    def __init__(self, vault_storage: Optional[VaultTokenStorage] = None,
                 revocation_service: Optional[TokenRevocationService] = None,
                 content_filter: Optional[SensitiveContentFilter] = None,
                 postgres_db: Optional[PostgresDB] = None,
                 max_workers: int = 10):
        """
        Initialize the token security manager.
        
        Args:
            vault_storage: Vault token storage instance
            revocation_service: Token revocation service instance
            content_filter: Content filter instance
            postgres_db: PostgreSQL database instance
            max_workers: Maximum number of worker threads
        """
        self.vault_storage = vault_storage or VaultTokenStorage()
        self.revocation_service = revocation_service or TokenRevocationService(
            vault_storage=self.vault_storage,
            postgres_db=postgres_db
        )
        self.content_filter = content_filter or SensitiveContentFilter()
        self.postgres_db = postgres_db or PostgresDB()
        self.max_workers = max_workers
        
        # Security configuration
        self.security_config = self._load_security_config()
        
        # Rate limiting
        self.rate_limiter = {}
        self.rate_limit_lock = threading.Lock()
        
        # Security metrics
        self.security_metrics = SecurityMetrics(
            total_tokens=0,
            active_tokens=0,
            revoked_tokens=0,
            security_events=0,
            violations=0,
            average_response_time=0.0,
            uptime_percentage=100.0,
            last_audit=datetime.utcnow()
        )
        
        # Background tasks
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._start_background_tasks()
        
        logger.info("TokenSecurityManager initialized")
    
    def _load_security_config(self) -> Dict[str, Any]:
        """Load security configuration from database."""
        try:
            query = """
                SELECT config_key, config_value, config_type 
                FROM security_configurations 
                WHERE is_active = true
            """
            results = self.postgres_db.fetch_all(query)
            
            config = {}
            for row in results:
                key = row['config_key']
                value = row['config_value']
                config_type = row['config_type']
                
                # Convert value to appropriate type
                if config_type == 'integer':
                    value = int(value)
                elif config_type == 'boolean':
                    value = value.lower() == 'true'
                elif config_type == 'json':
                    value = json.loads(value)
                
                config[key] = value
            
            return config
            
        except Exception as e:
            logger.error(f"Error loading security config: {e}")
            return {
                'token_retention_days': 90,
                'audit_log_retention_days': 365,
                'max_failed_attempts': 5,
                'lockout_duration_minutes': 30,
                'enable_rate_limiting': True,
                'max_requests_per_minute': 60,
                'token_rotation_days': 30,
                'enable_mfa': False,
                'session_timeout_minutes': 60,
                'password_expiry_days': 90
            }
    
    def _start_background_tasks(self):
        """Start background security tasks."""
        # Start security monitoring
        self._executor.submit(self._security_monitoring_loop)
        
        # Start token cleanup
        self._executor.submit(self._token_cleanup_loop)
        
        # Start compliance checking
        self._executor.submit(self._compliance_checking_loop)
    
    def _security_monitoring_loop(self):
        """Background security monitoring loop."""
        while True:
            try:
                time.sleep(60)  # Run every minute
                
                # Check system health
                self._check_system_health()
                
                # Monitor security events
                self._monitor_security_events()
                
                # Update metrics
                self._update_security_metrics()
                
            except Exception as e:
                logger.error(f"Error in security monitoring loop: {e}")
    
    def _token_cleanup_loop(self):
        """Background token cleanup loop."""
        while True:
            try:
                time.sleep(3600)  # Run every hour
                
                # Clean up expired tokens
                self._cleanup_expired_tokens()
                
                # Clean up old audit logs
                self._cleanup_old_audit_logs()
                
            except Exception as e:
                logger.error(f"Error in token cleanup loop: {e}")
    
    def _compliance_checking_loop(self):
        """Background compliance checking loop."""
        while True:
            try:
                time.sleep(86400)  # Run every day
                
                # Check compliance
                self._check_compliance()
                
                # Generate compliance report
                self._generate_compliance_report()
                
            except Exception as e:
                logger.error(f"Error in compliance checking loop: {e}")
    
    def _check_system_health(self):
        """Check overall system health."""
        try:
            # Check Vault status
            vault_status = self.vault_storage.get_vault_status()
            
            # Check database connectivity
            db_status = self.postgres_db.check_connection()
            
            # Update health metrics
            self.security_metrics.uptime_percentage = (
                100.0 if vault_status.get('vault_status', False) and db_status else 0.0
            )
            
            # Log health status
            logger.info(f"System health - Vault: {vault_status}, Database: {db_status}")
            
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
    
    def _monitor_security_events(self):
        """Monitor security events and detect anomalies."""
        try:
            # Get recent security events
            recent_events = self._get_recent_security_events()
            
            # Detect anomalies
            anomalies = self._detect_security_anomalies(recent_events)
            
            # Handle anomalies
            for anomaly in anomalies:
                self._handle_security_anomaly(anomaly)
                
        except Exception as e:
            logger.error(f"Error monitoring security events: {e}")
    
    def _update_security_metrics(self):
        """Update security metrics."""
        try:
            # Get token statistics
            token_stats = self._get_token_statistics()
            
            # Update metrics
            self.security_metrics.total_tokens = token_stats.get('total_tokens', 0)
            self.security_metrics.active_tokens = token_stats.get('active_tokens', 0)
            self.security_metrics.revoked_tokens = token_stats.get('revoked_tokens', 0)
            
            # Get security event count
            event_count = self._get_security_event_count()
            self.security_metrics.security_events = event_count
            
            # Get violation count
            violation_count = self._get_violation_count()
            self.security_metrics.violations = violation_count
            
            # Update last audit time
            self.security_metrics.last_audit = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error updating security metrics: {e}")
    
    def _cleanup_expired_tokens(self):
        """Clean up expired tokens."""
        try:
            retention_days = self.security_config.get('token_retention_days', 90)
            cleaned_count = self.vault_storage.cleanup_expired_tokens(retention_days)
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired tokens")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")
    
    def _cleanup_old_audit_logs(self):
        """Clean up old audit logs."""
        try:
            retention_days = self.security_config.get('audit_log_retention_days', 365)
            
            # This would be implemented with proper database cleanup
            logger.info(f"Cleaning up audit logs older than {retention_days} days")
            
        except Exception as e:
            logger.error(f"Error cleaning up audit logs: {e}")
    
    def _check_compliance(self):
        """Check system compliance."""
        try:
            # This would implement comprehensive compliance checking
            logger.info("Running compliance checks")
            
        except Exception as e:
            logger.error(f"Error checking compliance: {e}")
    
    def _generate_compliance_report(self):
        """Generate compliance report."""
        try:
            # This would generate a comprehensive compliance report
            logger.info("Generating compliance report")
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
    
    def _get_recent_security_events(self) -> List[Dict[str, Any]]:
        """Get recent security events."""
        try:
            query = """
                SELECT event_type, severity_level, user_id, service_name, 
                       created_at, details
                FROM security_audit_log 
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                ORDER BY created_at DESC
            """
            return self.postgres_db.fetch_all(query)
            
        except Exception as e:
            logger.error(f"Error getting recent security events: {e}")
            return []
    
    def _detect_security_anomalies(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect security anomalies in events."""
        anomalies = []
        
        try:
            # Check for unusual login patterns
            failed_logins = [e for e in events if e['event_type'] == 'authentication_failure']
            if len(failed_logins) > 10:  # Threshold for anomaly detection
                anomalies.append({
                    'type': 'unusual_login_pattern',
                    'severity': 'high',
                    'description': f'High number of failed logins: {len(failed_logins)}',
                    'events': failed_logins
                })
            
            # Check for rapid token access
            token_access = [e for e in events if e['event_type'] == 'token_retrieved']
            if len(token_access) > 50:  # Threshold for rapid access
                anomalies.append({
                    'type': 'rapid_token_access',
                    'severity': 'medium',
                    'description': f'High number of token retrievals: {len(token_access)}',
                    'events': token_access
                })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting security anomalies: {e}")
            return []
    
    def _handle_security_anomaly(self, anomaly: Dict[str, Any]):
        """Handle detected security anomaly."""
        try:
            if anomaly['type'] == 'unusual_login_pattern':
                # Implement appropriate response
                logger.warning(f"Security anomaly detected: {anomaly['description']}")
                
            elif anomaly['type'] == 'rapid_token_access':
                # Implement rate limiting or other measures
                logger.warning(f"Security anomaly detected: {anomaly['description']}")
                
        except Exception as e:
            logger.error(f"Error handling security anomaly: {e}")
    
    def _get_token_statistics(self) -> Dict[str, int]:
        """Get token statistics."""
        try:
            # This would query the database for token statistics
            return {
                'total_tokens': 0,
                'active_tokens': 0,
                'revoked_tokens': 0
            }
            
        except Exception as e:
            logger.error(f"Error getting token statistics: {e}")
            return {}
    
    def _get_security_event_count(self) -> int:
        """Get security event count."""
        try:
            query = "SELECT COUNT(*) as count FROM security_audit_log"
            result = self.postgres_db.fetch_one(query)
            return result['count'] if result else 0
            
        except Exception as e:
            logger.error(f"Error getting security event count: {e}")
            return 0
    
    def _get_violation_count(self) -> int:
        """Get security violation count."""
        try:
            query = "SELECT COUNT(*) as count FROM security_alerts WHERE status = 'OPEN'"
            result = self.postgres_db.fetch_one(query)
            return result['count'] if result else 0
            
        except Exception as e:
            logger.error(f"Error getting violation count: {e}")
            return 0
    
    def store_token_securely(self, user_id: str, service_name: str, token: str,
                           token_type: str = 'api_key', expires_at: Optional[datetime] = None,
                           metadata: Optional[Dict[str, Any]] = None,
                           security_context: Optional[SecurityContext] = None) -> str:
        """
        Store a token securely with comprehensive security checks.
        
        Args:
            user_id: User identifier
            service_name: Service name
            token: The token to store
            token_type: Type of token
            expires_at: Optional expiration datetime
            metadata: Additional metadata
            security_context: Security context for the operation
            
        Returns:
            Token ID for reference
        """
        start_time = time.time()
        
        try:
            # Validate security context
            if security_context:
                self._validate_security_context(security_context)
            
            # Filter sensitive content from metadata
            if metadata:
                filtered_metadata = self.content_filter.filter_content(
                    content=json.dumps(metadata),
                    filter_types=[FilterType.SENSITIVE_DATA],
                    action=FilterAction.SANITIZE
                ).filtered_content
                metadata = json.loads(filtered_metadata)
            
            # Store token in Vault
            token_id = self.vault_storage.store_token_securely(
                user_id=user_id,
                service_name=service_name,
                token=token,
                token_type=token_type,
                expires_at=expires_at,
                metadata=metadata
            )
            
            # Log security event
            self._log_security_event(
                event_type=SecurityEvent.TOKEN_CREATED,
                user_id=user_id,
                service_name=service_name,
                details={'token_id': token_id, 'token_type': token_type},
                security_context=security_context
            )
            
            # Update metrics
            response_time = time.time() - start_time
            self._update_response_time(response_time)
            
            logger.info(f"Securely stored token {token_id} for user {user_id}")
            return token_id
            
        except Exception as e:
            logger.error(f"Error storing token securely: {e}")
            raise Exception(f"Failed to store token securely: {e}")
    
    def retrieve_token_securely(self, user_id: str, service_name: str,
                              token_id: Optional[str] = None,
                              security_context: Optional[SecurityContext] = None) -> Dict[str, Any]:
        """
        Retrieve a token securely with comprehensive security checks.
        
        Args:
            user_id: User identifier
            service_name: Service name
            token_id: Optional token ID
            security_context: Security context for the operation
            
        Returns:
            Dictionary containing token and metadata
        """
        start_time = time.time()
        
        try:
            # Validate security context
            if security_context:
                self._validate_security_context(security_context)
            
            # Check if token is revoked
            if token_id and self.revocation_service.check_token_revocation(token_id):
                raise Exception(f"Token {token_id} has been revoked")
            
            # Retrieve token from Vault
            token_data = self.vault_storage.retrieve_token_securely(
                user_id=user_id,
                service_name=service_name,
                token_id=token_id
            )
            
            # Log security event
            self._log_security_event(
                event_type=SecurityEvent.TOKEN_RETRIEVED,
                user_id=user_id,
                service_name=service_name,
                details={'token_id': token_id or 'all', 'token_type': token_data.get('metadata', {}).get('token_type')},
                security_context=security_context
            )
            
            # Update metrics
            response_time = time.time() - start_time
            self._update_response_time(response_time)
            
            logger.info(f"Retrieved token for user {user_id}, service {service_name}")
            return token_data
            
        except Exception as e:
            logger.error(f"Error retrieving token securely: {e}")
            raise Exception(f"Failed to retrieve token securely: {e}")
    
    def revoke_token(self, user_id: str, service_name: str, token_id: str,
                    reason: RevocationReason, reason_details: Optional[str] = None,
                    security_context: Optional[SecurityContext] = None) -> bool:
        """
        Revoke a token with comprehensive security checks.
        
        Args:
            user_id: User identifier
            service_name: Service name
            token_id: Token ID to revoke
            reason: Reason for revocation
            reason_details: Additional details
            security_context: Security context for the operation
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        
        try:
            # Validate security context
            if security_context:
                self._validate_security_context(security_context)
            
            # Revoke token
            success = self.revocation_service.revoke_token(
                token_id=token_id,
                user_id=user_id,
                service_name=service_name,
                reason=reason,
                reason_details=reason_details,
                immediate=True
            )
            
            if success:
                # Log security event
                self._log_security_event(
                    event_type=SecurityEvent.TOKEN_REVOKED,
                    user_id=user_id,
                    service_name=service_name,
                    details={'token_id': token_id, 'reason': reason.value},
                    security_context=security_context
                )
                
                # Update metrics
                response_time = time.time() - start_time
                self._update_response_time(response_time)
                
                logger.info(f"Revoked token {token_id} for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False
    
    def renew_token(self, user_id: str, service_name: str, old_token: str,
                   new_token: str, security_context: Optional[SecurityContext] = None) -> bool:
        """
        Renew a token with comprehensive security checks.
        
        Args:
            user_id: User identifier
            service_name: Service name
            old_token: Old token to replace
            new_token: New token to store
            security_context: Security context for the operation
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        
        try:
            # Validate security context
            if security_context:
                self._validate_security_context(security_context)
            
            # Get token metadata
            token_data = self.vault_storage.retrieve_token_securely(
                user_id=user_id,
                service_name=service_name
            )
            
            # Rotate token
            success = self.vault_storage.rotate_token(
                user_id=user_id,
                service_name=service_name,
                old_token=old_token,
                new_token=new_token
            )
            
            if success:
                # Log security event
                self._log_security_event(
                    event_type=SecurityEvent.TOKEN_RENEWED,
                    user_id=user_id,
                    service_name=service_name,
                    details={'old_token_hash': token_data['metadata']['hash']},
                    security_context=security_context
                )
                
                # Update metrics
                response_time = time.time() - start_time
                self._update_response_time(response_time)
                
                logger.info(f"Renewed token for user {user_id}, service {service_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error renewing token: {e}")
            return False
    
    def filter_sensitive_content(self, content: str, filter_types: List[str] = None,
                               action: str = 'sanitize', security_context: Optional[SecurityContext] = None) -> Dict[str, Any]:
        """
        Filter sensitive content with comprehensive security checks.
        
        Args:
            content: Content to filter
            filter_types: Types of filters to apply
            action: Action to take when violations are found
            security_context: Security context for the operation
            
        Returns:
            Dictionary with filtering results
        """
        try:
            # Validate security context
            if security_context:
                self._validate_security_context(security_context)
            
            # Convert filter types to enum
            filter_type_enums = []
            if filter_types:
                for filter_type in filter_types:
                    try:
                        filter_type_enums.append(FilterType(filter_type))
                    except ValueError:
                        logger.warning(f"Unknown filter type: {filter_type}")
            
            # Convert action to enum
            try:
                action_enum = FilterAction(action)
            except ValueError:
                action_enum = FilterAction.SANITIZE
                logger.warning(f"Unknown action: {action}, defaulting to SANITIZE")
            
            # Filter content
            result = self.content_filter.filter_content(
                content=content,
                filter_types=filter_type_enums or None,
                action=action_enum,
                user_id=security_context.user_id if security_context else None,
                session_id=security_context.session_id if security_context else None
            )
            
            # Log security event if violations found
            if result.violations:
                self._log_security_event(
                    event_type=SecurityEvent.SECURITY_VIOLATION,
                    user_id=security_context.user_id if security_context else 'unknown',
                    service_name='content_filter',
                    details={
                        'violations': result.violations,
                        'filter_types': [ft.value for ft in filter_type_enums] if filter_type_enums else [],
                        'action': action_enum.value
                    },
                    security_context=security_context
                )
            
            return {
                'filtered_content': result.filtered_content,
                'violations': result.violations,
                'confidence_scores': result.confidence_scores,
                'action_taken': action_enum.value
            }
            
        except Exception as e:
            logger.error(f"Error filtering sensitive content: {e}")
            raise Exception(f"Failed to filter sensitive content: {e}")
    
    def _validate_security_context(self, security_context: SecurityContext):
        """Validate security context for operations."""
        try:
            # Check if user has required permissions
            required_permissions = self._get_required_permissions(security_context.security_level)
            
            missing_permissions = [
                perm for perm in required_permissions 
                if perm not in security_context.permissions
            ]
            
            if missing_permissions:
                raise Exception(f"Missing permissions: {missing_permissions}")
            
            # Check session timeout
            session_timeout = self.security_config.get('session_timeout_minutes', 60)
            if (datetime.utcnow() - security_context.timestamp).total_seconds() > session_timeout * 60:
                raise Exception("Session has expired")
            
        except Exception as e:
            logger.error(f"Security context validation failed: {e}")
            raise Exception(f"Security validation failed: {e}")
    
    def _get_required_permissions(self, security_level: SecurityLevel) -> List[str]:
        """Get required permissions for security level."""
        permissions_map = {
            SecurityLevel.LOW: ['read'],
            SecurityLevel.MEDIUM: ['read', 'write'],
            SecurityLevel.HIGH: ['read', 'write', 'admin'],
            SecurityLevel.CRITICAL: ['read', 'write', 'admin', 'security']
        }
        return permissions_map.get(security_level, [])
    
    def _log_security_event(self, event_type: SecurityEvent, user_id: str,
                          service_name: str, details: Dict[str, Any],
                          security_context: Optional[SecurityContext] = None):
        """Log security event to audit log."""
        try:
            # Log to Vault
            self.vault_storage.audit_security_event(
                event_type=event_type.value,
                severity_level='INFO',
                user_id=user_id,
                service_name=service_name,
                action=event_type.value,
                details=details,
                ip_address=security_context.ip_address if security_context else None,
                user_agent=security_context.user_agent if security_context else None,
                session_id=security_context.session_id if security_context else None
            )
            
            # Log to database
            self._log_security_event_to_db(
                event_type=event_type.value,
                user_id=user_id,
                service_name=service_name,
                action=event_type.value,
                details=details,
                ip_address=security_context.ip_address if security_context else None,
                user_agent=security_context.user_agent if security_context else None,
                session_id=security_context.session_id if security_context else None
            )
            
            # Update security metrics
            self.security_metrics.security_events += 1
            
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
    
    def _log_security_event_to_db(self, event_type: str, user_id: str,
                                service_name: str, action: str, details: Dict[str, Any],
                                ip_address: Optional[str] = None,
                                user_agent: Optional[str] = None,
                                session_id: Optional[str] = None):
        """Log security event to database."""
        try:
            query = """
                INSERT INTO security_audit_log 
                (event_type, severity_level, user_id, service_name, action, details, ip_address, user_agent, session_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.postgres_db.execute(query, (
                event_type, 'INFO', user_id, service_name, action,
                json.dumps(details), ip_address, user_agent, session_id
            ))
            
        except Exception as e:
            logger.error(f"Error logging security event to database: {e}")
    
    def _update_response_time(self, response_time: float):
        """Update average response time."""
        try:
            # Simple moving average
            alpha = 0.1  # Smoothing factor
            self.security_metrics.average_response_time = (
                alpha * response_time + 
                (1 - alpha) * self.security_metrics.average_response_time
            )
            
        except Exception as e:
            logger.error(f"Error updating response time: {e}")
    
    def get_security_metrics(self) -> SecurityMetrics:
        """Get current security metrics."""
        return self.security_metrics
    
    def get_security_report(self) -> Dict[str, Any]:
        """Get comprehensive security report."""
        try:
            metrics = self.get_security_metrics()
            
            # Get revocation statistics
            revocation_stats = self.revocation_service.get_revocation_statistics()
            
            # Get filter statistics
            filter_stats = self.content_filter.get_filter_statistics()
            
            # Get Vault status
            vault_status = self.vault_storage.get_vault_status()
            
            return {
                'metrics': {
                    'total_tokens': metrics.total_tokens,
                    'active_tokens': metrics.active_tokens,
                    'revoked_tokens': metrics.revoked_tokens,
                    'security_events': metrics.security_events,
                    'violations': metrics.violations,
                    'average_response_time': metrics.average_response_time,
                    'uptime_percentage': metrics.uptime_percentage,
                    'last_audit': metrics.last_audit.isoformat()
                },
                'revocation_statistics': revocation_stats,
                'filter_statistics': filter_stats,
                'vault_status': vault_status,
                'security_config': self.security_config,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating security report: {e}")
            return {'error': str(e)}
    
    def emergency_shutdown(self):
        """Emergency shutdown procedure."""
        try:
            logger.warning("EMERGENCY SHUTDOWN initiated")
            
            # Revoke all tokens
            self.revocation_service.emergency_revocation_all()
            
            # Stop background tasks
            self._executor.shutdown(wait=True)
            
            # Close connections
            self.vault_storage.session.close()
            self.postgres_db.close_pool()
            
            logger.info("Emergency shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during emergency shutdown: {e}")
    
    def close(self):
        """Clean up resources."""
        try:
            self._executor.shutdown(wait=True)
            self.revocation_service.close()
            logger.info("TokenSecurityManager closed")
        except Exception as e:
            logger.error(f"Error closing TokenSecurityManager: {e}")


# Example usage and testing
if __name__ == "__main__":
    # Initialize security manager
    security_manager = TokenSecurityManager()
    
    try:
        # Create security context
        security_context = SecurityContext(
            user_id="test-user",
            session_id="test-session",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            security_level=SecurityLevel.MEDIUM,
            permissions=["read", "write"],
            timestamp=datetime.utcnow()
        )
        
        # Test token storage
        token_id = security_manager.store_token_securely(
            user_id="test-user",
            service_name="openai",
            token="sk-test123456789",
            token_type="api_key",
            metadata={"environment": "testing"},
            security_context=security_context
        )
        print(f"Stored token with ID: {token_id}")
        
        # Test token retrieval
        token_data = security_manager.retrieve_token_securely(
            user_id="test-user",
            service_name="openai",
            security_context=security_context
        )
        print(f"Retrieved token: {token_data['token'][:10]}...")
        
        # Test content filtering
        test_content = "Contact me at john@example.com or call 555-123-4567."
        filtered_result = security_manager.filter_sensitive_content(
            content=test_content,
            filter_types=["pii"],
            action="sanitize",
            security_context=security_context
        )
        print(f"Filtered content: {filtered_result['filtered_content']}")
        
        # Get security report
        report = security_manager.get_security_report()
        print(f"Security report: {report}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        security_manager.close()