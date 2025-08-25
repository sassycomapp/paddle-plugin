#!/usr/bin/env python3
"""
Environment Variable Validation System

This module provides comprehensive validation of environment variables and 
Vault integration across the entire system. It ensures all required secrets
are properly configured and accessible.

Author: KiloCode
License: Apache 2.0
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Result of environment variable validation."""
    is_valid: bool
    level: ValidationLevel
    message: str
    component: str
    details: Optional[Dict[str, Any]] = None


class EnvironmentValidator:
    """Comprehensive environment variable validator."""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.vault_available = self._check_vault_availability()
        
    def _check_vault_availability(self) -> bool:
        """Check if Vault client is available."""
        try:
            from src.vault_client import VaultClient
            client = VaultClient()
            return client.is_available()
        except ImportError:
            logger.warning("Vault client not available")
            return False
        except Exception as e:
            logger.warning(f"Vault connection failed: {e}")
            return False
    
    def validate_database_credentials(self) -> List[ValidationResult]:
        """Validate database credentials configuration."""
        results = []
        
        # Check PostgreSQL credentials
        postgres_vars = [
            'POSTGRES_HOST',
            'POSTGRES_PORT', 
            'POSTGRES_USER',
            'POSTGRES_PASSWORD',
            'POSTGRES_DB'
        ]
        
        missing_vars = [var for var in postgres_vars if not os.getenv(var)]
        
        if missing_vars:
            if self.vault_available:
                # Try to get credentials from Vault
                try:
                    from src.vault_client import get_database_credentials
                    db_creds = get_database_credentials("postgres")
                    if db_creds:
                        results.append(ValidationResult(
                            is_valid=True,
                            level=ValidationLevel.INFO,
                            message="Database credentials found in Vault",
                            component="database",
                            details={"source": "vault"}
                        ))
                    else:
                        results.append(ValidationResult(
                            is_valid=False,
                            level=ValidationLevel.CRITICAL,
                            message="Database credentials not found in environment variables or Vault",
                            component="database",
                            details={"missing_vars": missing_vars, "vault_available": True}
                        ))
                except Exception as e:
                    results.append(ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.CRITICAL,
                        message=f"Failed to retrieve database credentials from Vault: {e}",
                        component="database",
                        details={"missing_vars": missing_vars}
                    ))
            else:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.CRITICAL,
                    message="Database credentials not found and Vault not available",
                    component="database",
                    details={"missing_vars": missing_vars}
                ))
        else:
            results.append(ValidationResult(
                is_valid=True,
                level=ValidationLevel.INFO,
                message="Database credentials configured via environment variables",
                component="database",
                details={"source": "environment"}
            ))
        
        return results
    
    def validate_api_keys(self) -> List[ValidationResult]:
        """Validate API key configuration."""
        results = []
        api_keys = {
            'OPENROUTER_API_KEY': 'OpenRouter',
            'BRAVE_API_KEY': 'Brave Search',
            'OPENAI_API_KEY': 'OpenAI',
            'ANTHROPIC_API_KEY': 'Anthropic',
            'GOOGLE_API_KEY': 'Google'
        }
        
        for var_name, service_name in api_keys.items():
            api_key = os.getenv(var_name)
            
            if api_key:
                # Check if it's a placeholder (not a real key)
                if api_key.startswith('your_') or api_key == 'test' or len(api_key) < 10:
                    results.append(ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.WARNING,
                        message=f"{service_name} API key appears to be a placeholder",
                        component="api_keys",
                        details={"variable": var_name, "key": api_key[:10] + '...' if len(api_key) > 10 else api_key}
                    ))
                else:
                    results.append(ValidationResult(
                        is_valid=True,
                        level=ValidationLevel.INFO,
                        message=f"{service_name} API key configured",
                        component="api_keys",
                        details={"variable": var_name}
                    ))
            else:
                if self.vault_available:
                    try:
                        from src.vault_client import get_api_key
                        vault_key = get_api_key(service_name.lower().replace(' ', '-'))
                        if vault_key:
                            results.append(ValidationResult(
                                is_valid=True,
                                level=ValidationLevel.INFO,
                                message=f"{service_name} API key found in Vault",
                                component="api_keys",
                                details={"variable": var_name, "source": "vault"}
                            ))
                        else:
                            results.append(ValidationResult(
                                is_valid=False,
                                level=ValidationLevel.WARNING,
                                message=f"{service_name} API key not found in environment variables or Vault",
                                component="api_keys",
                                details={"variable": var_name}
                            ))
                    except Exception as e:
                        results.append(ValidationResult(
                            is_valid=False,
                            level=ValidationLevel.WARNING,
                            message=f"Failed to retrieve {service_name} API key from Vault: {e}",
                            component="api_keys",
                            details={"variable": var_name}
                        ))
                else:
                    results.append(ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.WARNING,
                        message=f"{service_name} API key not found and Vault not available",
                        component="api_keys",
                        details={"variable": var_name}
                    ))
        
        return results
    
    def validate_storage_credentials(self) -> List[ValidationResult]:
        """Validate storage credentials (MinIO, etc.)."""
        results = []
        
        # MinIO credentials
        minio_vars = [
            'MINIO_ACCESS_KEY',
            'MINIO_SECRET_KEY',
            'MINIO_ENDPOINT',
            'MINIO_BUCKET'
        ]
        
        missing_minio = [var for var in minio_vars if not os.getenv(var)]
        
        if missing_minio:
            if self.vault_available:
                try:
                    from src.vault_client import get_secret
                    minio_creds = get_secret("secret/data/storage/minio")
                    if minio_creds:
                        results.append(ValidationResult(
                            is_valid=True,
                            level=ValidationLevel.INFO,
                            message="MinIO credentials found in Vault",
                            component="storage",
                            details={"source": "vault"}
                        ))
                    else:
                        results.append(ValidationResult(
                            is_valid=False,
                            level=ValidationLevel.CRITICAL,
                            message="MinIO credentials not found in environment variables or Vault",
                            component="storage",
                            details={"missing_vars": missing_minio}
                        ))
                except Exception as e:
                    results.append(ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.CRITICAL,
                        message=f"Failed to retrieve MinIO credentials from Vault: {e}",
                        component="storage",
                        details={"missing_vars": missing_minio}
                    ))
            else:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.CRITICAL,
                    message="MinIO credentials not found and Vault not available",
                    component="storage",
                    details={"missing_vars": missing_minio}
                ))
        else:
            results.append(ValidationResult(
                is_valid=True,
                level=ValidationLevel.INFO,
                message="MinIO credentials configured via environment variables",
                component="storage",
                details={"source": "environment"}
            ))
        
        return results
    
    def validate_mcp_servers(self) -> List[ValidationResult]:
        """Validate MCP server configurations."""
        results = []
        
        # Check cache-mcp-server configuration
        cache_mcp_vars = [
            'CACHE_DB_HOST',
            'CACHE_DB_PORT',
            'CACHE_DB_USER',
            'CACHE_DB_PASSWORD'
        ]
        
        missing_cache = [var for var in cache_mcp_vars if not os.getenv(var)]
        
        if missing_cache:
            if self.vault_available:
                try:
                    from src.vault_client import get_secret
                    cache_creds = get_secret("secret/data/cache/database")
                    if cache_creds:
                        results.append(ValidationResult(
                            is_valid=True,
                            level=ValidationLevel.INFO,
                            message="Cache MCP server database credentials found in Vault",
                            component="mcp_cache",
                            details={"source": "vault"}
                        ))
                    else:
                        results.append(ValidationResult(
                            is_valid=False,
                            level=ValidationLevel.WARNING,
                            message="Cache MCP server database credentials not found",
                            component="mcp_cache",
                            details={"missing_vars": missing_cache}
                        ))
                except Exception as e:
                    results.append(ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.WARNING,
                        message=f"Failed to retrieve cache MCP credentials from Vault: {e}",
                        component="mcp_cache",
                        details={"missing_vars": missing_cache}
                    ))
            else:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.WARNING,
                    message="Cache MCP server database credentials not found and Vault not available",
                    component="mcp_cache",
                    details={"missing_vars": missing_cache}
                ))
        
        # Check MCP API keys
        mcp_api_key = os.getenv('MCP_API_KEY')
        if not mcp_api_key:
            if self.vault_available:
                try:
                    from src.vault_client import get_secret
                    mcp_creds = get_secret("secret/data/mcp/cache-server")
                    if mcp_creds and mcp_creds.get("api_key"):
                        results.append(ValidationResult(
                            is_valid=True,
                            level=ValidationLevel.INFO,
                            message="MCP API key found in Vault",
                            component="mcp_auth",
                            details={"source": "vault"}
                        ))
                    else:
                        results.append(ValidationResult(
                            is_valid=False,
                            level=ValidationLevel.WARNING,
                            message="MCP API key not found in environment variables or Vault",
                            component="mcp_auth"
                        ))
                except Exception as e:
                    results.append(ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.WARNING,
                        message=f"Failed to retrieve MCP API key from Vault: {e}",
                        component="mcp_auth"
                    ))
            else:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.WARNING,
                    message="MCP API key not found and Vault not available",
                    component="mcp_auth"
                ))
        
        return results
    
    def validate_vault_configuration(self) -> List[ValidationResult]:
        """Validate Vault configuration."""
        results = []
        
        if not self.vault_available:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.CRITICAL,
                message="Vault client not available or not configured",
                component="vault",
                details={
                    "VAULT_ADDR": os.getenv("VAULT_ADDR"),
                    "VAULT_TOKEN": os.getenv("VAULT_TOKEN", "Not set")
                }
            ))
            return results
        
        # Check Vault connection
        try:
            from src.vault_client import VaultClient
            client = VaultClient()
            
            if client.authenticate():
                results.append(ValidationResult(
                    is_valid=True,
                    level=ValidationLevel.INFO,
                    message="Vault connection successful",
                    component="vault",
                    details={
                        "VAULT_ADDR": os.getenv("VAULT_ADDR"),
                        "authenticated": True
                    }
                ))
                
                # Test secret retrieval
                test_secret = client.get_secret("secret/data/test/hello")
                if test_secret:
                    results.append(ValidationResult(
                        is_valid=True,
                        level=ValidationLevel.INFO,
                        message="Vault secret retrieval working",
                        component="vault",
                        details={"test_secret": test_secret}
                    ))
                else:
                    results.append(ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.WARNING,
                        message="Vault connection works but secret retrieval failed",
                        component="vault"
                    ))
            else:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.CRITICAL,
                    message="Vault authentication failed",
                    component="vault"
                ))
                
        except Exception as e:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.CRITICAL,
                message=f"Vault validation error: {e}",
                component="vault"
            ))
        
        return results
    
    def validate_frontend_configuration(self) -> List[ValidationResult]:
        """Validate frontend configuration."""
        results = []
        
        # Check frontend environment variables
        frontend_vars = [
            'VITE_API_URL',
            'VITE_APP_NAME',
            'VITE_ENABLE_AUTH',
            'VITE_ENABLE_API_KEYS'
        ]
        
        missing_frontend = [var for var in frontend_vars if not os.getenv(var)]
        
        if missing_frontend:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message="Frontend environment variables missing",
                component="frontend",
                details={"missing_vars": missing_frontend}
            ))
        else:
            results.append(ValidationResult(
                is_valid=True,
                level=ValidationLevel.INFO,
                message="Frontend environment variables configured",
                component="frontend"
            ))
        
        # Check API keys for frontend
        frontend_api_keys = [
            'VITE_OPENROUTER_API_KEY',
            'VITE_BRAVE_API_KEY',
            'VITE_OPENAI_API_KEY'
        ]
        
        missing_api_keys = [var for var in frontend_api_keys if not os.getenv(var)]
        
        if missing_api_keys:
            results.append(ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message="Frontend API keys missing",
                component="frontend",
                details={"missing_api_keys": missing_api_keys}
            ))
        else:
            results.append(ValidationResult(
                is_valid=True,
                level=ValidationLevel.INFO,
                message="Frontend API keys configured",
                component="frontend"
            ))
        
        return results
    
    def validate_all(self) -> List[ValidationResult]:
        """Run all validation checks."""
        logger.info("Starting comprehensive environment validation...")
        
        # Run all validation checks
        self.results.extend(self.validate_vault_configuration())
        self.results.extend(self.validate_database_credentials())
        self.results.extend(self.validate_api_keys())
        self.results.extend(self.validate_storage_credentials())
        self.results.extend(self.validate_mcp_servers())
        self.results.extend(self.validate_frontend_configuration())
        
        # Summary
        critical_issues = [r for r in self.results if r.level == ValidationLevel.CRITICAL and not r.is_valid]
        warning_issues = [r for r in self.results if r.level == ValidationLevel.WARNING and not r.is_valid]
        
        logger.info(f"Validation complete: {len(critical_issues)} critical issues, {len(warning_issues)} warnings")
        
        if critical_issues:
            logger.error("Critical issues found:")
            for issue in critical_issues:
                logger.error(f"  - {issue.component}: {issue.message}")
        
        if warning_issues:
            logger.warning("Warnings found:")
            for issue in warning_issues:
                logger.warning(f"  - {issue.component}: {issue.message}")
        
        return self.results
    
    def print_report(self):
        """Print a formatted validation report."""
        print("\n" + "="*60)
        print("ENVIRONMENT VALIDATION REPORT")
        print("="*60)
        
        by_component = {}
        for result in self.results:
            if result.component not in by_component:
                by_component[result.component] = []
            by_component[result.component].append(result)
        
        for component, results in by_component.items():
            print(f"\n📁 {component.upper()}")
            print("-" * 40)
            
            for result in results:
                status = "✅" if result.is_valid else "❌"
                level_icon = {
                    ValidationLevel.CRITICAL: "🔴",
                    ValidationLevel.WARNING: "🟠", 
                    ValidationLevel.INFO: "🔵"
                }.get(result.level, "⚪")
                
                print(f"  {status} {level_icon} {result.message}")
                
                if result.details:
                    for key, value in result.details.items():
                        if isinstance(value, dict):
                            print(f"    {key}: {json.dumps(value, indent=2)}")
                        else:
                            print(f"    {key}: {value}")
        
        # Summary
        total = len(self.results)
        valid = len([r for r in self.results if r.is_valid])
        invalid = total - valid
        
        print(f"\n{'='*60}")
        print(f"SUMMARY: {valid}/{total} checks passed, {invalid} failed")
        print(f"{'='*60}")
        
        if invalid > 0:
            print("\n🔴 CRITICAL ISSUES MUST BE RESOLVED BEFORE PRODUCTION DEPLOYMENT")
            print("🟠 WARNINGS SHOULD BE ADDRESSED FOR BETTER SECURITY")
        
        return invalid == 0


def main():
    """Main validation function."""
    validator = EnvironmentValidator()
    results = validator.validate_all()
    success = validator.print_report()
    
    if success:
        print("\n✅ Environment validation passed!")
        sys.exit(0)
    else:
        print("\n❌ Environment validation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()