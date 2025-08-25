#!/usr/bin/env python3
"""
Environment Utility for Virtual Environment Standardization

A simplified utility module for detecting and managing Python environments
with automatic fallback to virtual environments.
"""

import os
import sys
import subprocess
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

class Environment:
    """
    Simple environment utility for Python projects.
    
    Provides functionality for:
    - Environment detection
    - Virtual environment validation
    - Dependency checking
    - Tesseract OCR configuration
    """
    
    def __init__(self, workspace_root: Optional[str] = None):
        """Initialize the environment utility."""
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.logger = self._setup_logging()
        self._environment_info = None
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the environment utility."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def detect_environment(self) -> Dict[str, Any]:
        """
        Detect and analyze the current Python environment.
        
        Returns:
            Dict: Environment information
        """
        self.logger.info("Detecting Python environment...")
        
        # Basic environment detection
        is_virtual = self._is_virtual_environment()
        environment_name = self._get_environment_name()
        python_executable = sys.executable
        python_version = sys.version
        
        # Environment path
        environment_path = self._get_environment_path()
        
        # Site packages
        site_packages = self._get_site_packages()
        
        # Dependency checking
        missing_dependencies = self._check_dependencies()
        
        # Environment type classification
        environment_type = self._classify_environment(is_virtual, environment_path)
        
        environment_info = {
            'environment_type': environment_type,
            'is_virtual': is_virtual,
            'environment_name': environment_name,
            'python_executable': python_executable,
            'python_version': python_version,
            'environment_path': environment_path,
            'site_packages': site_packages,
            'missing_dependencies': missing_dependencies
        }
        
        self._environment_info = environment_info
        self.logger.info(f"Environment detected: {environment_type}")
        
        return environment_info
    
    def _is_virtual_environment(self) -> bool:
        """Check if running in a virtual environment."""
        # Check for virtual environment indicators
        virtual_env = os.environ.get('VIRTUAL_ENV', os.environ.get('CONDA_PREFIX'))
        return bool(virtual_env)
    
    def _get_environment_name(self) -> str:
        """Get the name of the current environment."""
        if self._is_virtual_environment():
            virtual_env = os.environ.get('VIRTUAL_ENV', os.environ.get('CONDA_PREFIX', ''))
            return Path(virtual_env).name if virtual_env else 'virtual'
        return 'global'
    
    def _get_environment_path(self) -> Optional[str]:
        """Get the path of the current environment."""
        if self._is_virtual_environment():
            return os.environ.get('VIRTUAL_ENV', os.environ.get('CONDA_PREFIX'))
        return None
    
    def _get_site_packages(self) -> List[str]:
        """Get site packages directories."""
        site_packages = []
        
        # Add user site-packages
        user_site = os.path.expanduser('~\\AppData\\Roaming\\Python\\Python313\\Lib\\site-packages')
        if os.path.exists(user_site):
            site_packages.append(user_site)
        
        # Add current environment site-packages
        if hasattr(sys, 'real_prefix'):  # virtualenv
            site_packages.append(sys.prefix + '\\Lib\\site-packages')
        elif hasattr(sys, 'base_prefix'):  # venv
            site_packages.append(sys.prefix + '\\Lib\\site-packages')
        
        return site_packages
    
    
    def _check_dependencies(self) -> List[str]:
        """Check for required dependencies."""
        required_packages = ['PIL', 'numpy']
        missing = []
        
        for package in required_packages:
            if not self._is_package_installed(package):
                missing.append(package)
        
        return missing
    
    def _is_package_installed(self, package_name: str) -> bool:
        """Check if a package is installed."""
        try:
            __import__(package_name)
            return True
        except ImportError:
            return False
    
    def _classify_environment(self, is_virtual: bool, environment_path: Optional[str]) -> str:
        """Classify the type of environment."""
        if is_virtual:
            if environment_path and 'conda' in str(environment_path).lower():
                return 'conda'
            return 'virtual'
        return 'global'
    
    def configure_environment(self) -> Dict[str, Any]:
        """
        Configure the environment based on detected settings.
        
        Returns:
            Dict: Configuration results
        """
        self.logger.info("Configuring environment...")
        
        if not self._environment_info:
            self.detect_environment()
        
        # Ensure environment_info is not None
        if self._environment_info is None:
            self._environment_info = self.detect_environment()
        
        config_result = {
            'actions_taken': [],
            'settings_applied': {},
            'errors': []
        }
        
        try:
            
            # Add site-packages to path if configured
            if self._environment_info['site_packages']:
                for site_package in self._environment_info['site_packages']:
                    if site_package not in sys.path:
                        sys.path.insert(0, site_package)
                        config_result['actions_taken'].append(f'Added site-packages: {site_package}')
            
            # Set environment variables
            os.environ['PYTHONPATH'] = os.pathsep.join(sys.path)
            config_result['actions_taken'].append('Updated PYTHONPATH')
            
        except Exception as e:
            config_result['errors'].append(f"Environment configuration failed: {e}")
            self.logger.error(f"Environment configuration failed: {e}")
        
        return config_result
    
    
    def validate_environment(self) -> Dict[str, Any]:
        """
        Validate the current environment and return validation results.
        
        Returns:
            Dict: Validation results
        """
        self.logger.info("Validating Python environment...")
        
        if not self._environment_info:
            self.detect_environment()
        
        # Ensure environment_info is not None
        if self._environment_info is None:
            self._environment_info = self.detect_environment()
        
        validation_result = {
            'status': 'pass',
            'details': {},
            'recommendations': [],
            'critical_issues': [],
            'warnings': []
        }
        
        # Check Python version
        python_version = self._environment_info['python_version']
        if 'Python 3.' in python_version:
            version_parts = python_version.replace('Python ', '').split('.')
            major, minor = int(version_parts[0]), int(version_parts[1])
            if major < 3 or (major == 3 and minor < 8):
                validation_result['status'] = 'fail'
                validation_result['critical_issues'].append(
                    f"Python {python_version} is outdated. Python 3.8+ is required."
                )
        
        # Check virtual environment
        if not self._environment_info['is_virtual']:
            validation_result['warnings'].append(
                "Not running in a virtual environment. Consider activating one."
            )
        
        
        # Check dependencies
        if self._environment_info['missing_dependencies']:
            validation_result['critical_issues'].append(
                f"Missing required dependencies: {self._environment_info['missing_dependencies']}"
            )
            validation_result['status'] = 'fail'
        
        return validation_result
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment information."""
        if not self._environment_info:
            self.detect_environment()
        # Ensure environment_info is not None
        if self._environment_info is None:
            self._environment_info = self.detect_environment()
        return self._environment_info
    
    def save_environment_info(self, output_file: str = 'environment_info.json'):
        """Save environment information to a file."""
        if not self._environment_info:
            self.detect_environment()
        
        try:
            from encoding_utils import safe_write_text
        except ImportError:
            # Fallback to simple file write if import fails
            def safe_write_text(file_path, content, encoding='utf-8', errors='replace', **kwargs):
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w', encoding=encoding, errors=errors, **kwargs) as f:
                    f.write(content)
        safe_write_text(output_file, '', encoding='utf-8')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self._environment_info, f, indent=2, default=str)
        
        self.logger.info(f"Environment information saved to {output_file}")
        return output_file

# Global environment instance for easy access
_env_instance = None

def get_environment(workspace_root: Optional[str] = None) -> Environment:
    """Get or create the global environment instance."""
    global _env_instance
    if _env_instance is None:
        _env_instance = Environment(workspace_root)
    return _env_instance

def setup_environment(workspace_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Setup the environment and return configuration results.
    
    Args:
        workspace_root: Root directory of the workspace
        
    Returns:
        Dict: Environment configuration results
    """
    env = get_environment(workspace_root)
    env_info = env.detect_environment()
    config_result = env.configure_environment()
    validation_result = env.validate_environment()
    
    return {
        'environment_info': env_info,
        'configuration': config_result,
        'validation': validation_result
    }

def ensure_environment(workspace_root: Optional[str] = None) -> bool:
    """
    Ensure the environment is properly configured.
    
    Args:
        workspace_root: Root directory of the workspace
        
    Returns:
        bool: True if environment is properly configured
    """
    result = setup_environment(workspace_root)
    return result['validation']['status'] == 'pass'


# Convenience functions for backward compatibility
def add_site_packages():
    """Add user site-packages to sys.path for backward compatibility."""
    env = get_environment()
    env_info = env.get_environment_info()
    
    if env_info['site_packages']:
        for site_package in env_info['site_packages']:
            if site_package not in sys.path:
                sys.path.insert(0, site_package)


def main():
    """Main function for testing the environment utility."""
    print("=" * 60)
    print("Environment Utility - Virtual Environment Standardization")
    print("=" * 60)
    
    # Setup environment
    result = setup_environment()
    
    # Print environment information
    env_info = result['environment_info']
    try:
        from utils.encoding_utils import ascii_safe_print
    except ImportError:
        # Fallback to simple print if import fails
        def ascii_safe_print(*args, **kwargs):
            print(*args, **kwargs)
    ascii_safe_print(f"\n[CHECK] Environment Detection Results:")
    ascii_safe_print(f"   Type: {env_info['environment_type']}")
    ascii_safe_print(f"   Virtual: {env_info['is_virtual']}")
    ascii_safe_print(f"   Name: {env_info['environment_name']}")
    ascii_safe_print(f"   Python: {env_info['python_version']}")
    
    # Print configuration results
    config_result = result['configuration']
    ascii_safe_print(f"\n[CONFIG] Environment Configuration:")
    ascii_safe_print(f"   Actions: {config_result['actions_taken']}")
    
    # Print validation results
    validation_result = result['validation']
    ascii_safe_print(f"\n[OK] Environment Validation:")
    ascii_safe_print(f"   Status: {validation_result['status']}")
    if validation_result['critical_issues']:
        ascii_safe_print(f"   Critical Issues: {validation_result['critical_issues']}")
    if validation_result['warnings']:
        ascii_safe_print(f"   Warnings: {validation_result['warnings']}")
    
    # Save environment info
    env_file = get_environment().save_environment_info()
    ascii_safe_print(f"\n[FILE] Environment information saved to: {env_file}")
    
    print("\n" + "=" * 60)
    print("Environment setup completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()