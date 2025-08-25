"""
Sensitive content filtering and sanitization for security and compliance.

This module provides comprehensive content filtering capabilities including
PII detection, sensitive data identification, content sanitization,
and security pattern matching.
"""

import re
import logging
import hashlib
import json
from typing import List, Dict, Any, Optional, Set, Tuple, Pattern
from datetime import datetime
from enum import Enum
import unicodedata
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class FilterType(Enum):
    """Types of content filtering."""
    PII = "pii"  # Personally Identifiable Information
    SENSITIVE_DATA = "sensitive_data"  # Sensitive business data
    MALICIOUS_CONTENT = "malicious_content"  # Malicious patterns
    PROFANITY = "profanity"  # Inappropriate language
    SECURITY_PATTERNS = "security_patterns"  # Security-related patterns
    COMPLIANCE = "compliance"  # Compliance-related content


class FilterAction(Enum):
    """Actions to take when filtering content."""
    BLOCK = "block"  # Block the content entirely
    SANITIZE = "sanitize"  # Remove or replace sensitive parts
    LOG = "log"  # Log the violation but allow content
    ESCALATE = "escalate"  # Escalate to security team


@dataclass
class FilterResult:
    """Result of content filtering operation."""
    original_content: str
    filtered_content: str
    filter_type: FilterType
    action_taken: FilterAction
    violations: List[str]
    confidence_scores: Dict[str, float]
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class SensitiveContentFilter:
    """
    Comprehensive sensitive content filtering system.
    
    This class provides multiple layers of content filtering including:
    - PII detection and masking
    - Sensitive data identification
    - Malicious content detection
    - Profanity filtering
    - Security pattern matching
    - Compliance checking
    """
    
    def __init__(self, enable_pii_detection: bool = True,
                 enable_sensitive_data_detection: bool = True,
                 enable_malicious_content_detection: bool = True,
                 enable_profanity_filter: bool = True,
                 enable_security_patterns: bool = True,
                 enable_compliance_checks: bool = True):
        """
        Initialize the sensitive content filter.
        
        Args:
            enable_pii_detection: Enable PII detection
            enable_sensitive_data_detection: Enable sensitive data detection
            enable_malicious_content_detection: Enable malicious content detection
            enable_profanity_filter: Enable profanity filtering
            enable_security_patterns: Enable security pattern matching
            enable_compliance_checks: Enable compliance checking
        """
        self.enable_pii_detection = enable_pii_detection
        self.enable_sensitive_data_detection = enable_sensitive_data_detection
        self.enable_malicious_content_detection = enable_malicious_content_detection
        self.enable_profanity_filter = enable_profanity_filter
        self.enable_security_patterns = enable_security_patterns
        self.enable_compliance_checks = enable_compliance_checks
        
        # Initialize pattern collections
        self._initialize_patterns()
        
        # Cache for performance
        self._pattern_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        logger.info("SensitiveContentFilter initialized")
    
    def _initialize_patterns(self):
        """Initialize all filtering patterns."""
        # PII Patterns
        self.pii_patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', re.IGNORECASE),
            'phone': re.compile(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'),
            'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
            'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            'ip_address': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
            'mac_address': re.compile(r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b'),
            'url': re.compile(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'),
            'ipv6': re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'),
            'license_plate': re.compile(r'\b[A-Z]{1,3}\d{1,4}[A-Z]?\d?[A-Z]?\b'),
            'passport_number': re.compile(r'\b[A-Z]\d{8,9}\b'),
            'bank_account': re.compile(r'\b\d{8,17}\b'),
        }
        
        # Sensitive Data Patterns
        self.sensitive_data_patterns = {
            'api_key': re.compile(r'\b(?:api[_-]?key|secret|token|access[_-]?key|private[_-]?key)[\s]*[:=][\s]*["\']?([a-zA-Z0-9\-_]{16,})["\']?', re.IGNORECASE),
            'password': re.compile(r'\b(?:password|pwd|pass)[\s]*[:=][\s]*["\']?([^"\']{8,})["\']?', re.IGNORECASE),
            'jwt_token': re.compile(r'\beyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b'),
            'database_url': re.compile(r'\b(?:postgresql|mysql|mongodb|redis)://[^\s]+'),
            'aws_key': re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
            'google_api_key': re.compile(r'\bAIza[0-9A-Za-z_-]{35}\b'),
            'github_token': re.compile(r'\bghp_[0-9A-Za-z]{36}\b'),
        }
        
        # Security Patterns
        self.security_patterns = {
            'sql_injection': re.compile(r'(\b(?:union|select|insert|update|delete|drop|create|alter|exec|execute)\b\s+.*\b(?:from|into|table|database|user)\b)', re.IGNORECASE),
            'xss_attack': re.compile(r'<script[^>]*>.*?</script>|javascript:|on\w+\s*=', re.IGNORECASE),
            'command_injection': re.compile(r'(\b(?:rm|del|rmdir|mkdir|chmod|chown|system|exec|eval)\b)', re.IGNORECASE),
            'path_traversal': re.compile(r'\.\./|\.\.\\|\.\.\/|\.\.\\\\'),
            'file_inclusion': re.compile(r'(\b(?:include|require|include_once|require_once)\b\s*["\'][\s]*\.\.?["\'])', re.IGNORECASE),
        }
        
        # Profanity patterns (basic list - in production use a comprehensive list)
        self.profanity_patterns = [
            re.compile(r'\b(?:damn|hell|shit|fuck|crap|bitch|bastard)\b', re.IGNORECASE),
            re.compile(r'\b(?:idiot|moron|imbecile|fool|stupid)\b', re.IGNORECASE),
            re.compile(r'\b(?:ass|dick|cock|pussy|cunt)\b', re.IGNORECASE),
        ]
        
        # Compliance patterns
        self.compliance_patterns = {
            'gdpr': re.compile(r'\b(?:GDPR|General Data Protection Regulation)\b', re.IGNORECASE),
            'hipaa': re.compile(r'\b(?:HIPAA|Health Insurance Portability and Accountability Act)\b', re.IGNORECASE),
            'sox': re.compile(r'\b(?:SOX|Sarbanes-Oxley)\b', re.IGNORECASE),
            'pci_dss': re.compile(r'\b(?:PCI DSS|Payment Card Industry Data Security Standard)\b', re.IGNORECASE),
        }
    
    def filter_content(self, content: str, filter_types: List[FilterType] = None,
                      action: FilterAction = FilterAction.SANITIZE,
                      user_id: Optional[str] = None,
                      session_id: Optional[str] = None) -> FilterResult:
        """
        Filter content based on specified filter types.
        
        Args:
            content: Content to filter
            filter_types: List of filter types to apply (all if None)
            action: Action to take when violations are found
            user_id: User identifier for logging
            session_id: Session identifier for logging
            
        Returns:
            FilterResult object with filtering results
        """
        if not content:
            return FilterResult(
                original_content="",
                filtered_content="",
                filter_type=FilterType.PII,
                action_taken=action,
                violations=[],
                confidence_scores={},
                timestamp=datetime.utcnow(),
                user_id=user_id,
                session_id=session_id
            )
        
        # Determine which filters to apply
        if filter_types is None:
            filter_types = [
                FilterType.PII,
                FilterType.SENSITIVE_DATA,
                FilterType.MALICIOUS_CONTENT,
                FilterType.PROFANITY,
                FilterType.SECURITY_PATTERNS,
                FilterType.COMPLIANCE
            ]
        
        filtered_content = content
        violations = []
        confidence_scores = {}
        
        # Apply each filter type
        for filter_type in filter_types:
            if not self._is_filter_enabled(filter_type):
                continue
            
            filter_result = self._apply_filter(filtered_content, filter_type, action)
            filtered_content = filter_result.filtered_content
            violations.extend(filter_result.violations)
            confidence_scores.update(filter_result.confidence_scores)
        
        return FilterResult(
            original_content=content,
            filtered_content=filtered_content,
            filter_type=filter_types[0] if filter_types else FilterType.PII,
            action_taken=action,
            violations=violations,
            confidence_scores=confidence_scores,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=session_id
        )
    
    def _is_filter_enabled(self, filter_type: FilterType) -> bool:
        """Check if a specific filter type is enabled."""
        if filter_type == FilterType.PII:
            return self.enable_pii_detection
        elif filter_type == FilterType.SENSITIVE_DATA:
            return self.enable_sensitive_data_detection
        elif filter_type == FilterType.MALICIOUS_CONTENT:
            return self.enable_malicious_content_detection
        elif filter_type == FilterType.PROFANITY:
            return self.enable_profanity_filter
        elif filter_type == FilterType.SECURITY_PATTERNS:
            return self.enable_security_patterns
        elif filter_type == FilterType.COMPLIANCE:
            return self.enable_compliance_checks
        return False
    
    def _apply_filter(self, content: str, filter_type: FilterType,
                     action: FilterAction) -> FilterResult:
        """Apply a specific filter type to content."""
        violations = []
        confidence_scores = {}
        filtered_content = content
        
        if filter_type == FilterType.PII:
            filtered_content, violations, confidence_scores = self._filter_pii(content, action)
        elif filter_type == FilterType.SENSITIVE_DATA:
            filtered_content, violations, confidence_scores = self._filter_sensitive_data(content, action)
        elif filter_type == FilterType.MALICIOUS_CONTENT:
            filtered_content, violations, confidence_scores = self._filter_malicious_content(content, action)
        elif filter_type == FilterType.PROFANITY:
            filtered_content, violations, confidence_scores = self._filter_profanity(content, action)
        elif filter_type == FilterType.SECURITY_PATTERNS:
            filtered_content, violations, confidence_scores = self._filter_security_patterns(content, action)
        elif filter_type == FilterType.COMPLIANCE:
            filtered_content, violations, confidence_scores = self._filter_compliance(content, action)
        
        return FilterResult(
            original_content=content,
            filtered_content=filtered_content,
            filter_type=filter_type,
            action_taken=action,
            violations=violations,
            confidence_scores=confidence_scores,
            timestamp=datetime.utcnow()
        )
    
    def _filter_pii(self, content: str, action: FilterAction) -> Tuple[str, List[str], Dict[str, float]]:
        """Filter Personally Identifiable Information."""
        violations = []
        confidence_scores = {}
        filtered_content = content
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = pattern.findall(content)
            if matches:
                violations.extend([f"PII detected: {pii_type}"])
                confidence_scores[pii_type] = 0.95  # High confidence for PII
                
                if action == FilterAction.SANITIZE:
                    # Replace PII with placeholders
                    if pii_type == 'email':
                        filtered_content = pattern.sub('[EMAIL]', filtered_content)
                    elif pii_type == 'phone':
                        filtered_content = pattern.sub('[PHONE]', filtered_content)
                    elif pii_type == 'ssn':
                        filtered_content = pattern.sub('[SSN]', filtered_content)
                    elif pii_type == 'credit_card':
                        filtered_content = pattern.sub('[CREDIT_CARD]', filtered_content)
                    elif pii_type == 'ip_address':
                        filtered_content = pattern.sub('[IP_ADDRESS]', filtered_content)
                    else:
                        filtered_content = pattern.sub('[REDACTED]', filtered_content)
        
        return filtered_content, violations, confidence_scores
    
    def _filter_sensitive_data(self, content: str, action: FilterAction) -> Tuple[str, List[str], Dict[str, float]]:
        """Filter sensitive data like API keys, passwords, etc."""
        violations = []
        confidence_scores = {}
        filtered_content = content
        
        for data_type, pattern in self.sensitive_data_patterns.items():
            matches = pattern.findall(content)
            if matches:
                violations.extend([f"Sensitive data detected: {data_type}"])
                confidence_scores[data_type] = 0.90  # High confidence for sensitive data
                
                if action == FilterAction.SANITIZE:
                    filtered_content = pattern.sub(f'[{data_type.upper()}_REDACTED]', filtered_content)
        
        return filtered_content, violations, confidence_scores
    
    def _filter_malicious_content(self, content: str, action: FilterAction) -> Tuple[str, List[str], Dict[str, float]]:
        """Filter malicious content and attack patterns."""
        violations = []
        confidence_scores = {}
        filtered_content = content
        
        # Check for common attack patterns
        attack_patterns = [
            (r'<script[^>]*>.*?</script>', 'script_tag', 0.99),
            (r'javascript:', 'javascript_protocol', 0.98),
            (r'on\w+\s*=', 'event_handler', 0.95),
            (r'union\s+select', 'sql_injection', 0.97),
            (r'drop\s+table', 'sql_injection', 0.99),
            (r'exec\s*\(', 'command_injection', 0.96),
            (r'eval\s*\(', 'command_injection', 0.98),
        ]
        
        for pattern, violation_type, confidence in attack_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(f"Malicious content detected: {violation_type}")
                confidence_scores[violation_type] = confidence
                
                if action == FilterAction.BLOCK:
                    return "[CONTENT_BLOCKED_DUE_TO_SECURITY_VIOLATION]", violations, confidence_scores
                elif action == FilterAction.SANITIZE:
                    filtered_content = re.sub(pattern, '[REDACTED]', filtered_content, flags=re.IGNORECASE)
        
        return filtered_content, violations, confidence_scores
    
    def _filter_profanity(self, content: str, action: FilterAction) -> Tuple[str, List[str], Dict[str, float]]:
        """Filter profanity and inappropriate language."""
        violations = []
        confidence_scores = {}
        filtered_content = content
        
        for pattern in self.profanity_patterns:
            matches = pattern.findall(content)
            if matches:
                violations.append("Profanity detected")
                confidence_scores['profanity'] = 0.85
                
                if action == FilterAction.SANITIZE:
                    filtered_content = pattern.sub('[***]', filtered_content)
        
        return filtered_content, violations, confidence_scores
    
    def _filter_security_patterns(self, content: str, action: FilterAction) -> Tuple[str, List[str], Dict[str, float]]:
        """Filter security-related patterns that might indicate malicious intent."""
        violations = []
        confidence_scores = {}
        filtered_content = content
        
        for pattern_type, pattern in self.security_patterns.items():
            matches = pattern.findall(content)
            if matches:
                violations.append(f"Security pattern detected: {pattern_type}")
                confidence_scores[pattern_type] = 0.90
                
                if action == FilterAction.BLOCK:
                    return "[CONTENT_BLOCKED_DUE_TO_SECURITY_PATTERN]", violations, confidence_scores
                elif action == FilterAction.SANITIZE:
                    filtered_content = pattern.sub('[REDACTED]', filtered_content)
        
        return filtered_content, violations, confidence_scores
    
    def _filter_compliance(self, content: str, action: FilterAction) -> Tuple[str, List[str], Dict[str, float]]:
        """Filter compliance-related content."""
        violations = []
        confidence_scores = {}
        filtered_content = content
        
        for compliance_type, pattern in self.compliance_patterns.items():
            matches = pattern.findall(content)
            if matches:
                violations.append(f"Compliance reference: {compliance_type}")
                confidence_scores[compliance_type] = 0.95
        
        return filtered_content, violations, confidence_scores
    
    def sanitize_input(self, input_text: str, max_length: int = 10000) -> str:
        """
        Sanitize input text by removing control characters and normalizing.
        
        Args:
            input_text: Input text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
        """
        if not input_text:
            return ""
        
        # Truncate to max length
        if len(input_text) > max_length:
            input_text = input_text[:max_length]
            logger.warning(f"Input text truncated to {max_length} characters")
        
        # Remove control characters except for common whitespace
        sanitized = ''.join(
            char for char in input_text 
            if unicodedata.category(char)[0] != 'C' or char in ['\n', '\r', '\t', ' ']
        )
        
        # Normalize whitespace
        sanitized = ' '.join(sanitized.split())
        
        return sanitized
    
    def detect_sensitive_patterns(self, content: str) -> Dict[str, Any]:
        """
        Detect sensitive patterns in content without filtering.
        
        Args:
            content: Content to analyze
            
        Returns:
            Dictionary with detected patterns and their details
        """
        results = {
            'pii_detected': [],
            'sensitive_data_detected': [],
            'malicious_content_detected': [],
            'security_patterns_detected': [],
            'compliance_references': [],
            'total_violations': 0,
            'risk_score': 0.0
        }
        
        # PII Detection
        for pii_type, pattern in self.pii_patterns.items():
            matches = pattern.findall(content)
            if matches:
                results['pii_detected'].append({
                    'type': pii_type,
                    'count': len(matches),
                    'matches': matches[:5]  # Limit to first 5 matches
                })
        
        # Sensitive Data Detection
        for data_type, pattern in self.sensitive_data_patterns.items():
            matches = pattern.findall(content)
            if matches:
                results['sensitive_data_detected'].append({
                    'type': data_type,
                    'count': len(matches),
                    'matches': matches[:5]
                })
        
        # Malicious Content Detection
        attack_patterns = [
            (r'<script[^>]*>.*?</script>', 'script_tag'),
            (r'javascript:', 'javascript_protocol'),
            (r'on\w+\s*=', 'event_handler'),
            (r'union\s+select', 'sql_injection'),
            (r'drop\s+table', 'sql_injection'),
        ]
        
        for pattern, violation_type in attack_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                results['malicious_content_detected'].append(violation_type)
        
        # Security Patterns
        for pattern_type, pattern in self.security_patterns.items():
            matches = pattern.findall(content)
            if matches:
                results['security_patterns_detected'].append({
                    'type': pattern_type,
                    'count': len(matches)
                })
        
        # Compliance References
        for compliance_type, pattern in self.compliance_patterns.items():
            matches = pattern.findall(content)
            if matches:
                results['compliance_references'].append({
                    'type': compliance_type,
                    'count': len(matches)
                })
        
        # Calculate total violations and risk score
        total_violations = (
            len(results['pii_detected']) +
            len(results['sensitive_data_detected']) +
            len(results['malicious_content_detected']) +
            len(results['security_patterns_detected']) +
            len(results['compliance_references'])
        )
        
        results['total_violations'] = total_violations
        
        # Calculate risk score (0.0 to 1.0)
        risk_score = 0.0
        if results['malicious_content_detected']:
            risk_score += 0.8
        if results['security_patterns_detected']:
            risk_score += 0.6
        if results['sensitive_data_detected']:
            risk_score += 0.4
        if results['pii_detected']:
            risk_score += 0.2
        
        results['risk_score'] = min(risk_score, 1.0)
        
        return results
    
    def create_content_hash(self, content: str) -> str:
        """
        Create a hash of content for duplicate detection.
        
        Args:
            content: Content to hash
            
        Returns:
            SHA-256 hash of content
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def batch_filter_content(self, contents: List[str], filter_types: List[FilterType] = None,
                           action: FilterAction = FilterAction.SANITIZE) -> List[FilterResult]:
        """
        Filter multiple content items in batch.
        
        Args:
            contents: List of content items to filter
            filter_types: List of filter types to apply
            action: Action to take when violations are found
            
        Returns:
            List of FilterResult objects
        """
        results = []
        
        for i, content in enumerate(contents):
            result = self.filter_content(
                content=content,
                filter_types=filter_types,
                action=action,
                user_id=f"batch_user_{i}",
                session_id=f"batch_session_{i}"
            )
            results.append(result)
        
        return results
    
    def get_filter_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about filtering operations.
        
        Returns:
            Dictionary with filtering statistics
        """
        return {
            'filters_enabled': {
                'pii_detection': self.enable_pii_detection,
                'sensitive_data_detection': self.enable_sensitive_data_detection,
                'malicious_content_detection': self.enable_malicious_content_detection,
                'profanity_filter': self.enable_profanity_filter,
                'security_patterns': self.enable_security_patterns,
                'compliance_checks': self.enable_compliance_checks
            },
            'pattern_counts': {
                'pii_patterns': len(self.pii_patterns),
                'sensitive_data_patterns': len(self.sensitive_data_patterns),
                'security_patterns': len(self.security_patterns),
                'profanity_patterns': len(self.profanity_patterns),
                'compliance_patterns': len(self.compliance_patterns)
            },
            'cache_info': {
                'cache_size': len(self._pattern_cache),
                'cache_ttl': self._cache_ttl
            }
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize content filter
    content_filter = SensitiveContentFilter()
    
    # Test content
    test_content = """
    Contact me at john.doe@example.com or call 555-123-4567.
    My API key is sk-1234567890abcdef1234567890abcdef.
    Password: mysecretpassword123
    """
    
    # Filter content
    result = content_filter.filter_content(
        content=test_content,
        filter_types=[FilterType.PII, FilterType.SENSITIVE_DATA],
        action=FilterAction.SANITIZE
    )
    
    print(f"Original content: {result.original_content}")
    print(f"Filtered content: {result.filtered_content}")
    print(f"Violations: {result.violations}")
    print(f"Confidence scores: {result.confidence_scores}")
    
    # Test pattern detection
    patterns = content_filter.detect_sensitive_patterns(test_content)
    print(f"Detected patterns: {patterns}")
    
    # Test batch filtering
    batch_contents = [
        "Email: test@example.com",
        "API Key: ai1234567890abcdef1234567890abcdef",
        "Normal text without sensitive data"
    ]
    
    batch_results = content_filter.batch_filter_content(batch_contents)
    print(f"Batch filtering results: {len(batch_results)} items processed")
    
    # Get filter statistics
    stats = content_filter.get_filter_statistics()
    print(f"Filter statistics: {stats}")