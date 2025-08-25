"""
Configuration Manager Module

This module provides configuration management functionality for the PNG to Markdown converter.
It handles loading, validating, and managing configuration settings.

Author: Kilo Code
Version: 1.0.0
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging

# Local imports
from errors.exceptions import ConfigurationError, ValidationError
from errors.handler import ErrorHandler


class ConfigurationManager:
    """
    Manages configuration loading, validation, and updates.
    Provides environment-specific settings and user customization options.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path
        self.config = {}
        self.error_handler = ErrorHandler()
        self.logger = logging.getLogger(__name__)
        
        # Load default configuration
        self._load_default_config()
        
        # Load configuration from file if provided
        if config_path:
            self.load_config(config_path)
    
    def _load_default_config(self) -> None:
        """Load default configuration."""
        self.config = {
            "_description": "PNG to Markdown Converter Default Configuration",
            "_version": "1.0.0",
            "_generated_by": "ConfigurationManager",
            "_timestamp": "2025-01-01T00:00:00Z",
            
            
            "preprocessing": {
                "enabled": True,
                "max_size": 3000,
                "enhance_contrast": True,
                "remove_noise": True,
                "binarize": True,
                "sharpen": True,
                "deskew": True,
                "contrast_factor": 1.5,
                "brightness_factor": 1.1,
                "sharpen_factor": 1.0,
                "noise_reduction_radius": 1,
                "binarization_threshold": 128
            },
            
            "formatting": {
                "preserve_layout": True,
                "include_metadata": True,
                "include_statistics": True,
                "confidence_threshold": 0,
                "table_detection_threshold": 0.7,
                "column_detection_threshold": 0.6,
                "heading_detection_threshold": 0.8,
                "max_line_length": 80,
                "paragraph_spacing": 2,
                "table_alignment": "left"
            },
            
            "batch": {
                "size": 10,
                "timeout": 30,
                "retry_count": 3
            },
            
            "output": {
                "directory": "./output",
                "filename_pattern": "{original_name}_OCR.md",
                "include_backup": True
            },
            
            "logging": {
                "level": "INFO",
                "file": "./logs/converter.log",
                "max_size": "10MB",
                "backup_count": 5,
                "encoding": "utf-8"
            },
            
            "encoding": {
                "default_encoding": "utf-8",
                "fallback_encodings": ["utf-8", "latin-1", "cp1252"],
                "file_encoding": "utf-8",
                "console_encoding": "utf-8",
                "strict_mode": True,
                "auto_detect": True,
                "error_handling": "strict"
            },
            
            "metadata": {
                "include_detailed_stats": True,
                "include_quality_metrics": True,
                "include_performance_metrics": True,
                "include_file_info": True,
                "include_processing_info": True
            },
            
            "validation": {
                "max_file_size": 104857600,
                "min_file_size": 1024,
                "max_image_width": 10000,
                "max_image_height": 10000,
                "supported_formats": [".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif", ".webp"]
            }
        }
    
    def load_config(self, config_path: str) -> bool:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(config_path):
                raise ConfigurationError(f"Configuration file not found: {config_path}", config_path)
            
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            # Validate configuration
            if not self.validate_config(file_config):
                raise ConfigurationError("Invalid configuration format", config_path)
            
            # Merge with existing configuration
            self._merge_config(file_config)
            self.config_path = config_path
            
            self.logger.info(f"Configuration loaded from {config_path}")
            return True
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in configuration file: {e}"
            self.error_handler.handle_configuration_error(Exception(error_msg), config_path)
            return False
        except Exception as e:
            error_msg = f"Failed to load configuration: {e}"
            self.error_handler.handle_configuration_error(Exception(error_msg), config_path)
            return False
    
    def save_config(self, config_path: str) -> bool:
        """
        Save current configuration to file.
        
        Args:
            config_path: Path to save configuration
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            config_dir = os.path.dirname(config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            # Add metadata
            config_to_save = self.config.copy()
            config_to_save['_saved_at'] = "2025-01-01T00:00:00Z"
            config_to_save['_saved_by'] = "ConfigurationManager"
            
            from utils.encoding_utils import safe_write_text
            safe_write_text(config_path, '', encoding='utf-8')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration saved to {config_path}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to save configuration: {e}"
            self.error_handler.handle_configuration_error(Exception(error_msg), config_path)
            return False
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration settings.
        
        Args:
            config: Configuration to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check required sections
            required_sections = [
                'tesseract', 'preprocessing', 'formatting',
                'batch', 'output', 'logging', 'encoding', 'metadata', 'validation'
            ]
            
            for section in required_sections:
                if section not in config:
                    raise ValidationError(f"Missing required section: {section}", section)
            
            
            # Validate preprocessing section
            preprocess_config = config['preprocessing']
            if 'enabled' in preprocess_config and not isinstance(preprocess_config['enabled'], bool):
                raise ValidationError("'enabled' must be a boolean", 'enabled')
            
            if 'max_size' in preprocess_config and not isinstance(preprocess_config['max_size'], int):
                raise ValidationError("'max_size' must be an integer", 'max_size')
            
            # Validate formatting section
            format_config = config['formatting']
            if 'confidence_threshold' in format_config:
                threshold = format_config['confidence_threshold']
                if not isinstance(threshold, (int, float)) or not (0 <= threshold <= 100):
                    raise ValidationError("'confidence_threshold' must be between 0 and 100", 'confidence_threshold')
            
            # Validate batch section
            batch_config = config['batch']
            if 'size' in batch_config and not isinstance(batch_config['size'], int):
                raise ValidationError("'size' must be an integer", 'size')
            
            if 'timeout' in batch_config and not isinstance(batch_config['timeout'], int):
                raise ValidationError("'timeout' must be an integer", 'timeout')
            
            # Validate output section
            output_config = config['output']
            if 'directory' in output_config and not isinstance(output_config['directory'], str):
                raise ValidationError("'directory' must be a string", 'directory')
            
            if 'filename_pattern' in output_config and not isinstance(output_config['filename_pattern'], str):
                raise ValidationError("'filename_pattern' must be a string", 'filename_pattern')
            
            # Validate logging section
            logging_config = config['logging']
            if 'level' in logging_config:
                valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
                if logging_config['level'] not in valid_levels:
                    raise ValidationError(f"'level' must be one of {valid_levels}", 'level')
            
            # Validate encoding section
            encoding_config = config['encoding']
            if 'default_encoding' in encoding_config and not isinstance(encoding_config['default_encoding'], str):
                raise ValidationError("'default_encoding' must be a string", 'default_encoding')
            
            if 'fallback_encodings' in encoding_config and not isinstance(encoding_config['fallback_encodings'], list):
                raise ValidationError("'fallback_encodings' must be a list", 'fallback_encodings')
            
            if 'file_encoding' in encoding_config and not isinstance(encoding_config['file_encoding'], str):
                raise ValidationError("'file_encoding' must be a string", 'file_encoding')
            
            if 'console_encoding' in encoding_config and not isinstance(encoding_config['console_encoding'], str):
                raise ValidationError("'console_encoding' must be a string", 'console_encoding')
            
            if 'strict_mode' in encoding_config and not isinstance(encoding_config['strict_mode'], bool):
                raise ValidationError("'strict_mode' must be a boolean", 'strict_mode')
            
            if 'auto_detect' in encoding_config and not isinstance(encoding_config['auto_detect'], bool):
                raise ValidationError("'auto_detect' must be a boolean", 'auto_detect')
            
            if 'error_handling' in encoding_config:
                valid_error_handling = ['strict', 'ignore', 'replace', 'backslashreplace']
                if encoding_config['error_handling'] not in valid_error_handling:
                    raise ValidationError(f"'error_handling' must be one of {valid_error_handling}", 'error_handling')
            
            # Validate validation section
            validation_config = config['validation']
            if 'max_file_size' in validation_config and not isinstance(validation_config['max_file_size'], int):
                raise ValidationError("'max_file_size' must be an integer", 'max_file_size')
            
            if 'min_file_size' in validation_config and not isinstance(validation_config['min_file_size'], int):
                raise ValidationError("'min_file_size' must be an integer", 'min_file_size')
            
            if 'supported_formats' in validation_config and not isinstance(validation_config['supported_formats'], list):
                raise ValidationError("'supported_formats' must be a list", 'supported_formats')
            
            self.logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            error_msg = f"Configuration validation failed: {e}"
            self.error_handler.handle_configuration_error(Exception(error_msg))
            return False
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with new values.
        
        Args:
            updates: Configuration updates to apply
        """
        try:
            # Validate updates
            if not self.validate_config(updates):
                raise ValidationError("Invalid configuration updates")
            
            # Merge updates
            self._merge_config(updates)
            
            self.logger.info("Configuration updated")
            
        except Exception as e:
            error_msg = f"Failed to update configuration: {e}"
            self.error_handler.handle_configuration_error(Exception(error_msg))
            raise ConfigurationError(error_msg)
    
    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """
        Merge new configuration with existing configuration.
        
        Args:
            new_config: New configuration to merge
        """
        def deep_merge(base: Dict, update: Dict) -> Dict:
            """Deep merge two dictionaries."""
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
            return base
        
        deep_merge(self.config, new_config)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'tesseract.languages')
            default: Default value if key not found
            
        Returns:
            Any: Configuration value
        """
        try:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            self.logger.warning(f"Failed to get config key '{key}': {e}")
            return default
    
    def set_config(self, key: str, value: Any) -> None:
        """
        Set configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'tesseract.languages')
            value: Value to set
        """
        try:
            keys = key.split('.')
            config = self.config
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set the value
            config[keys[-1]] = value
            
            self.logger.info(f"Configuration key '{key}' set to '{value}'")
            
        except Exception as e:
            error_msg = f"Failed to set config key '{key}': {e}"
            self.error_handler.handle_configuration_error(Exception(error_msg))
            raise ConfigurationError(error_msg)
    
    
    def get_preprocessing_config(self) -> Dict[str, Any]:
        """Get preprocessing configuration."""
        return self.get_config('preprocessing', {})
    
    def get_formatting_config(self) -> Dict[str, Any]:
        """Get formatting configuration."""
        return self.get_config('formatting', {})
    
    def get_batch_config(self) -> Dict[str, Any]:
        """Get batch configuration."""
        return self.get_config('batch', {})
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration."""
        return self.get_config('output', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get_config('logging', {})
    
    def get_metadata_config(self) -> Dict[str, Any]:
        """Get metadata configuration."""
        return self.get_config('metadata', {})
    
    def get_encoding_config(self) -> Dict[str, Any]:
        """Get encoding configuration."""
        return self.get_config('encoding', {})
    
    def get_validation_config(self) -> Dict[str, Any]:
        """Get validation configuration."""
        return self.get_config('validation', {})
    
    def copy_config(self) -> Dict[str, Any]:
        """
        Get a copy of the current configuration.
        
        Returns:
            Dict: Copy of configuration
        """
        import copy
        return copy.deepcopy(self.config)
    
    def reset_config(self) -> None:
        """Reset configuration to defaults."""
        self._load_default_config()
        self.logger.info("Configuration reset to defaults")
    
    def get_config_diff(self, other_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get differences between current configuration and another configuration.
        
        Args:
            other_config: Configuration to compare with
            
        Returns:
            Dict: Configuration differences
        """
        def get_changes(config1: Dict, config2: Dict, path: str = "") -> Dict[str, Any]:
            changes = {}
            
            # Check keys in config1
            for key, value in config1.items():
                current_path = f"{path}.{key}" if path else key
                
                if key not in config2:
                    changes[current_path] = {'old': value, 'new': None, 'action': 'removed'}
                elif isinstance(value, dict) and isinstance(config2[key], dict):
                    changes.update(get_changes(value, config2[key], current_path))
                elif value != config2[key]:
                    changes[current_path] = {
                        'old': value, 
                        'new': config2[key], 
                        'action': 'modified'
                    }
            
            # Check keys in config2 but not in config1
            for key, value in config2.items():
                current_path = f"{path}.{key}" if path else key
                
                if key not in config1:
                    changes[current_path] = {'old': None, 'new': value, 'action': 'added'}
            
            return changes
        
        return get_changes(self.config, other_config)
    
    def apply_environment_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        try:
            # Environment variable prefixes
            env_prefixes = ['PNG2MD_', 'P2MD_', 'OCR_']
            
            for prefix in env_prefixes:
                env_vars = {k: v for k, v in os.environ.items() if k.startswith(prefix)}
                
                for env_key, env_value in env_vars.items():
                    # Convert environment key to config key
                    config_key = env_key[len(prefix):].lower()
                    
                    # Replace underscores with dots for nested keys
                    config_key = config_key.replace('_', '.')
                    
                    # Parse environment value
                    parsed_value = self._parse_env_value(env_value)
                    
                    # Set configuration value
                    self.set_config(config_key, parsed_value)
            
            self.logger.info("Environment overrides applied")
            
        except Exception as e:
            error_msg = f"Failed to apply environment overrides: {e}"
            self.error_handler.handle_configuration_error(Exception(error_msg))
    
    def _parse_env_value(self, value: str) -> Any:
        """
        Parse environment variable value to appropriate type.
        
        Args:
            value: String value from environment
            
        Returns:
            Any: Parsed value
        """
        # Try to parse as JSON first
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
        
        # Try to parse as boolean
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        
        # Try to parse as integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try to parse as float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current configuration.
        
        Returns:
            Dict: Configuration summary
        """
        summary = {
            'config_file': self.config_path,
            'sections': list(self.config.keys()),
            'preprocessing_enabled': self.get_config('preprocessing.enabled', False),
            'formatting_options': {
                'preserve_layout': self.get_config('formatting.preserve_layout', False),
                'include_metadata': self.get_config('formatting.include_metadata', False),
                'include_statistics': self.get_config('formatting.include_statistics', False),
                'confidence_threshold': self.get_config('formatting.confidence_threshold', 0)
            },
            'batch_settings': {
                'size': self.get_config('batch.size', 0),
                'timeout': self.get_config('batch.timeout', 0),
                'retry_count': self.get_config('batch.retry_count', 0)
            },
            'output_settings': {
                'directory': self.get_config('output.directory', ''),
                'filename_pattern': self.get_config('output.filename_pattern', ''),
                'include_backup': self.get_config('output.include_backup', False)
            },
            'logging_settings': {
                'level': self.get_config('logging.level', ''),
                'file': self.get_config('logging.file', ''),
                'max_size': self.get_config('logging.max_size', ''),
                'backup_count': self.get_config('logging.backup_count', 0)
            },
            'encoding_settings': {
                'default_encoding': self.get_config('encoding.default_encoding', ''),
                'file_encoding': self.get_config('encoding.file_encoding', ''),
                'console_encoding': self.get_config('encoding.console_encoding', ''),
                'strict_mode': self.get_config('encoding.strict_mode', False),
                'auto_detect': self.get_config('encoding.auto_detect', False),
                'error_handling': self.get_config('encoding.error_handling', '')
            }
        }
        
        return summary
    
    def export_config_template(self, template_path: str) -> bool:
        """
        Export configuration template to file.
        
        Args:
            template_path: Path to save template
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            template_config = self.copy_config()
            
            # Add comments and descriptions
            template_config['_description'] = "PNG to Markdown Converter Configuration Template"
            template_config['_instructions'] = "Edit this file to customize the converter settings"
            
            # Create directory if it doesn't exist
            template_dir = os.path.dirname(template_path)
            if template_dir and not os.path.exists(template_dir):
                os.makedirs(template_dir, exist_ok=True)
            
            from utils.encoding_utils import safe_write_text
            safe_write_text(template_path, '', encoding='utf-8')
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(template_config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration template exported to {template_path}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to export configuration template: {e}"
            self.error_handler.handle_configuration_error(Exception(error_msg))
            return False
    
    def import_config_template(self, template_path: str) -> bool:
        """
        Import configuration from template file.
        
        Args:
            template_path: Path to template file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(template_path):
                raise ConfigurationError(f"Template file not found: {template_path}", template_path)
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_config = json.load(f)
            
            # Remove metadata fields
            metadata_fields = ['_description', '_instructions', '_saved_at', '_saved_by']
            for field in metadata_fields:
                template_config.pop(field, None)
            
            # Validate and merge template
            if self.validate_config(template_config):
                self._merge_config(template_config)
                self.logger.info(f"Configuration template imported from {template_path}")
                return True
            else:
                raise ConfigurationError("Invalid template configuration", template_path)
            
        except Exception as e:
            error_msg = f"Failed to import configuration template: {e}"
            self.error_handler.handle_configuration_error(Exception(error_msg), template_path)
            return False