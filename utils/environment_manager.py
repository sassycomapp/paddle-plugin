#!/usr/bin/env python3
"""
Environment Manager for Virtual Environment Standardization

This module provides comprehensive environment detection, validation, and management
for Python projects. It ensures consistent behavior across global and virtual
Python environments with automatic fallback mechanisms.
"""

import os
import sys
import subprocess
import logging
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import platform

@dataclass
class EnvironmentInfo:
    """Information about the current Python environment"""
    is_virtual: bool
    environment_name: str
    python_executable: str
    python_version: str
    environment_path: Optional[str]
    site_packages: List[str]
    missing_dependencies: List[str]
    environment_type: str  # 'virtual', 'global', 'conda', 'unknown'

class EnvironmentManager:
    """
    Comprehensive environment manager for Python projects.
    
    Provides functionality for:
    - Environment detection and classification
    - Virtual environment validation
    - Dependency checking
    - Automatic fallback mechanisms
    - Environment-specific configuration
    """
    
    def __init__(self, workspace_root: Optional[str] = None):
        """Initialize the environment manager."""
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.logger = self._setup_logging()
        self.environment_info = None
        self.config = self._load_config()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the environment manager."""
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
    
    def _load_config(self) -> Dict[str, Any]:
        """Load environment configuration from file."""
        config_file = self.workspace_root / 'environment_config.json'
        default_config = {
            'virtual_env_name': 'venv',
            'preferred_interpreter_path': None,
            'fallback_to_global': True,
            'required_packages': [
                'PIL', 'numpy', 'pytest'
            ],
            'optional_packages': [
                'opencv-python', 'scikit-image', 'psutil'
            ],
            'tesseract_paths': [],
            'user_site_packages': True,
            'auto_activate_venv': True
        }
        
        if config_file.exists():
            try:
                from .encoding_utils import safe_read_text
                config_content = safe_read_text(config_file, encoding='utf-8')
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    default_config.update(config)
                    self.logger.info(f"Loaded environment configuration from {config_file}")
            except Exception as e:
                self.logger.warning(f"Failed to load config file: {e}")
        
        return default_config
    
    def detect_environment(self) -> EnvironmentInfo:
        """
        Detect and analyze the current Python environment.
        
        Returns:
            EnvironmentInfo: Detailed information about the current environment
        """
        self.logger.info("Detecting Python environment...")
        
        # Basic environment detection
        is_virtual = self._is_virtual_environment()
        environment_name = self._get_environment_name()
        python_executable = sys.executable
        python_version = platform.python_version()
        
        # Environment path
        environment_path = self._get_environment_path()
        
        # Site packages
        site_packages = self._get_site_packages()
        
        # Dependency checking
        missing_dependencies = self._check_dependencies()
        
        # Environment type classification
        environment_type = self._classify_environment(is_virtual, environment_path)
        
        environment_info = EnvironmentInfo(
            is_virtual=is_virtual,
            environment_name=environment_name,
            python_executable=python_executable,
            python_version=python_version,
            environment_path=environment_path,
            site_packages=site_packages,
            missing_dependencies=missing_dependencies,
            environment_type=environment_type
        )
        
        self.environment_info = environment_info
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
        
        if self.config['user_site_packages']:
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
        """Check for required and optional dependencies."""
        missing = []
        
        # Check required packages
        for package in self.config['required_packages']:
            if not self._is_package_installed(package):
                missing.append(package)
        
        # Check optional packages
        for package in self.config['optional_packages']:
            if not self._is_package_installed(package):
                missing.append(f"[optional] {package}")
        
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
    
    def validate_environment(self) -> Dict[str, Any]:
        """
        Validate the current environment and return validation results.
        
        Returns:
            Dict: Validation results with status and recommendations
        """
        self.logger.info("Validating Python environment...")
        
        if not self.environment_info:
            self.detect_environment()
        
        # Ensure environment_info is not None
        if self.environment_info is None:
            self.environment_info = self.detect_environment()
        
        validation_result = {
            'status': 'pass',
            'details': {},
            'recommendations': [],
            'critical_issues': [],
            'warnings': []
        }
        
        # Check Python version
        python_version = self.environment_info.python_version
        version_parts = python_version.replace('Python ', '').split('.')
        major, minor = int(version_parts[0]), int(version_parts[1])
        
        if major < 3 or (major == 3 and minor < 8):
            validation_result['status'] = 'fail'
            validation_result['critical_issues'].append(
                f"Python {python_version} is outdated. Python 3.8+ is required."
            )
        
        # Check virtual environment
        if not self.environment_info.is_virtual and self.config['auto_activate_venv']:
            validation_result['warnings'].append(
                "Not running in a virtual environment. Consider activating one."
            )
        
        
        # Check dependencies
        if self.environment_info.missing_dependencies:
            missing_required = [
                dep for dep in self.environment_info.missing_dependencies 
                if not dep.startswith('[optional]')
            ]
            missing_optional = [
                dep[11:] for dep in self.environment_info.missing_dependencies 
                if dep.startswith('[optional]')
            ]
            
            if missing_required:
                validation_result['critical_issues'].append(
                    f"Missing required dependencies: {missing_required}"
                )
                validation_result['status'] = 'fail'
            
            if missing_optional:
                validation_result['warnings'].append(
                    f"Missing optional dependencies: {missing_optional}"
                )
        
        # Check environment path
        if self.environment_info.environment_path:
            env_path = Path(self.environment_info.environment_path)
            if not env_path.exists():
                validation_result['critical_issues'].append(
                    f"Environment path does not exist: {env_path}"
                )
                validation_result['status'] = 'fail'
        
        return validation_result
    
    def configure_environment(self) -> Dict[str, Any]:
        """
        Configure the environment based on detected settings.
        
        Returns:
            Dict: Configuration results with applied settings
        """
        self.logger.info("Configuring environment...")
        
        if not self.environment_info:
            self.detect_environment()
        
        # Ensure environment_info is not None
        if self.environment_info is None:
            self.environment_info = self.detect_environment()
        
        config_result = {
            'actions_taken': [],
            'settings_applied': {},
            'errors': []
        }
        
        try:
            
            # Add site-packages to path if configured
            if self.config['user_site_packages'] and self.environment_info.site_packages:
                for site_package in self.environment_info.site_packages:
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
    
    
    def get_environment_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of the current environment."""
        if not self.environment_info:
            self.detect_environment()
        
        # Ensure environment_info is not None
        if self.environment_info is None:
            self.environment_info = self.detect_environment()
        
        return {
            'environment_type': self.environment_info.environment_type,
            'is_virtual': self.environment_info.is_virtual,
            'environment_name': self.environment_info.environment_name,
            'python_version': self.environment_info.python_version,
            'python_executable': self.environment_info.python_executable,
            'environment_path': self.environment_info.environment_path,
            'site_packages_count': len(self.environment_info.site_packages),
            'missing_dependencies': self.environment_info.missing_dependencies,
            'config': self.config
        }
    
    def save_environment_info(self, output_file: str = 'environment_info.json'):
        """Save environment information to a file."""
        if not self.environment_info:
            self.detect_environment()
        
        summary = self.get_environment_summary()
        
        from .encoding_utils import safe_write_text
        safe_write_text(output_file, '', encoding='utf-8')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str)
        
        self.logger.info(f"Environment information saved to {output_file}")
        return output_file

def main():
    """Main function for testing the environment manager."""
    print("=" * 60)
    print("Environment Manager - Virtual Environment Standardization")
    print("=" * 60)
    
    # Create environment manager
    env_manager = EnvironmentManager()
    
    # Detect environment
    env_info = env_manager.detect_environment()
    
    from utils.encoding_utils import ascii_safe_print
    # Print environment information
    ascii_safe_print(f"\n[CHECK] Environment Detection Results:")
    ascii_safe_print(f"   Type: {env_info.environment_type}")
    ascii_safe_print(f"   Virtual: {env_info.is_virtual}")
    ascii_safe_print(f"   Name: {env_info.environment_name}")
    ascii_safe_print(f"   Python: {env_info.python_version}")
    ascii_safe_print(f"   Executable: {env_info.python_executable}")
    
    # Validate environment
    validation = env_manager.validate_environment()
    ascii_safe_print(f"\n[OK] Environment Validation:")
    ascii_safe_print(f"   Status: {validation['status']}")
    if validation['critical_issues']:
        ascii_safe_print(f"   Critical Issues: {validation['critical_issues']}")
    if validation['warnings']:
        ascii_safe_print(f"   Warnings: {validation['warnings']}")
    
    # Configure environment
    config_result = env_manager.configure_environment()
    ascii_safe_print(f"\n[CONFIG] Environment Configuration:")
    ascii_safe_print(f"   Actions: {config_result['actions_taken']}")
    
    # Save environment info
    env_file = env_manager.save_environment_info()
    ascii_safe_print(f"\n[FILE] Environment information saved to: {env_file}")
    
    print("\n" + "=" * 60)
    print("Environment management completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()