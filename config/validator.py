"""
Input Validator Module

This module provides input validation and sanitization functionality for the PNG to Markdown converter.
It ensures data integrity and security for file operations.

Author: Kilo Code
Version: 1.0.0
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import logging
import hashlib
import mimetypes

# Local imports
from errors.exceptions import ValidationError, FileOperationError, SecurityError
from errors.handler import ErrorHandler


class InputValidator:
    """
    Validates and sanitizes input files and parameters.
    Ensures data integrity and security.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize input validator.
        
        Args:
            config: Validation configuration
        """
        self.config = config or {}
        self.error_handler = ErrorHandler()
        self.logger = logging.getLogger(__name__)
        
        # Default validation settings
        self.default_validation_config = {
            "max_file_size": 104857600,  # 100MB
            "min_file_size": 1024,       # 1KB
            "max_image_width": 10000,
            "max_image_height": 10000,
            "supported_formats": [".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif", ".webp"],
            "max_filename_length": 255,
            "allowed_characters": r"^[a-zA-Z0-9_\-\.\s]+$",
            "max_path_length": 4096,
            "check_file_permissions": True,
            "validate_file_integrity": True,
            "check_virus_scan": False,
            "max_concurrent_files": 1000
        }
        
        # Merge with provided config
        if config:
            self._merge_validation_config(config)
    
    def _merge_validation_config(self, config: Dict[str, Any]) -> None:
        """Merge validation configuration with defaults."""
        for key, value in config.items():
            if key in self.default_validation_config:
                self.default_validation_config[key] = value
    
    def validate_image_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate image file for processing.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Dict: Validation results
        """
        try:
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'file_info': {},
                'validation_details': {}
            }
            
            # Check if file exists
            if not os.path.exists(file_path):
                error_msg = f"File does not exist: {file_path}"
                validation_result['valid'] = False
                validation_result['errors'].append(error_msg)
                return validation_result
            
            # Check file path length
            if len(file_path) > self.default_validation_config['max_path_length']:
                error_msg = f"File path too long: {len(file_path)} characters"
                validation_result['valid'] = False
                validation_result['errors'].append(error_msg)
                return validation_result
            
            # Check file permissions
            if self.default_validation_config['check_file_permissions']:
                permission_result = self._check_file_permissions(file_path, 'read')
                if not permission_result['has_permission']:
                    error_msg = f"No read permission for file: {file_path}"
                    validation_result['valid'] = False
                    validation_result['errors'].append(error_msg)
                    return validation_result
            
            # Get file info
            file_info = self._get_file_info(file_path)
            validation_result['file_info'] = file_info
            
            # Validate file size
            size_result = self._validate_file_size(file_info['size'], file_path)
            if not size_result['valid']:
                validation_result['valid'] = False
                validation_result['errors'].extend(size_result['errors'])
            
            # Validate file format
            format_result = self._validate_file_format(file_info['extension'], file_path)
            if not format_result['valid']:
                validation_result['valid'] = False
                validation_result['errors'].extend(format_result['errors'])
            
            # Validate image dimensions
            if file_info['is_image']:
                dimension_result = self._validate_image_dimensions(file_info['width'], file_info['height'], file_path)
                if not dimension_result['valid']:
                    validation_result['valid'] = False
                    validation_result['errors'].extend(dimension_result['errors'])
            
            # Validate file integrity
            if self.default_validation_config['validate_file_integrity']:
                integrity_result = self._validate_file_integrity(file_path)
                if not integrity_result['valid']:
                    validation_result['valid'] = False
                    validation_result['errors'].extend(integrity_result['errors'])
            
            # Validate filename
            filename_result = self._validate_filename(os.path.basename(file_path))
            if not filename_result['valid']:
                validation_result['valid'] = False
                validation_result['errors'].extend(filename_result['errors'])
            
            # Add warnings
            validation_result['warnings'].extend(size_result.get('warnings', []))
            validation_result['warnings'].extend(format_result.get('warnings', []))
            validation_result['warnings'].extend(dimension_result.get('warnings', []))
            validation_result['warnings'].extend(integrity_result.get('warnings', []))
            validation_result['warnings'].extend(filename_result.get('warnings', []))
            
            # Log validation result
            if validation_result['valid']:
                self.logger.info(f"File validation passed: {file_path}")
            else:
                self.logger.error(f"File validation failed: {file_path} - {', '.join(validation_result['errors'])}")
            
            return validation_result
            
        except Exception as e:
            error_msg = f"Error validating file {file_path}: {e}"
            self.error_handler.handle_file_error(Exception(error_msg), file_path, 'validation')
            return {
                'valid': False,
                'errors': [error_msg],
                'warnings': [],
                'file_info': {},
                'validation_details': {}
            }
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate processing parameters.
        
        Args:
            params: Processing parameters
            
        Returns:
            Dict: Validation results
        """
        try:
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'validated_params': {}
            }
            
            # Validate required parameters
            required_params = ['input_path', 'output_path']
            for param in required_params:
                if param not in params:
                    error_msg = f"Missing required parameter: {param}"
                    validation_result['valid'] = False
                    validation_result['errors'].append(error_msg)
            
            # Validate input path
            if 'input_path' in params:
                input_validation = self.validate_image_file(params['input_path'])
                if not input_validation['valid']:
                    validation_result['valid'] = False
                    validation_result['errors'].extend(input_validation['errors'])
                validation_result['validated_params']['input_path'] = input_validation
            
            # Validate output path
            if 'output_path' in params:
                output_validation = self.sanitize_output_path(params['output_path'])
                validation_result['validated_params']['output_path'] = output_validation
            
            # Validate confidence threshold
            if 'confidence_threshold' in params:
                threshold = params['confidence_threshold']
                if not isinstance(threshold, (int, float)) or not (0 <= threshold <= 100):
                    error_msg = f"Confidence threshold must be between 0 and 100, got: {threshold}"
                    validation_result['valid'] = False
                    validation_result['errors'].append(error_msg)
                else:
                    validation_result['validated_params']['confidence_threshold'] = threshold
            
            # Validate batch size
            if 'batch_size' in params:
                batch_size = params['batch_size']
                if not isinstance(batch_size, int) or batch_size <= 0:
                    error_msg = f"Batch size must be a positive integer, got: {batch_size}"
                    validation_result['valid'] = False
                    validation_result['errors'].append(error_msg)
                elif batch_size > self.default_validation_config['max_concurrent_files']:
                    warning_msg = f"Batch size {batch_size} exceeds recommended maximum of {self.default_validation_config['max_concurrent_files']}"
                    validation_result['warnings'].append(warning_msg)
                else:
                    validation_result['validated_params']['batch_size'] = batch_size
            
            # Validate timeout
            if 'timeout' in params:
                timeout = params['timeout']
                if not isinstance(timeout, int) or timeout <= 0:
                    error_msg = f"Timeout must be a positive integer, got: {timeout}"
                    validation_result['valid'] = False
                    validation_result['errors'].append(error_msg)
                else:
                    validation_result['validated_params']['timeout'] = timeout
            
            # Validate boolean parameters
            boolean_params = ['preprocess', 'preserve_layout', 'include_metadata', 'include_statistics', 'overwrite']
            for param in boolean_params:
                if param in params and not isinstance(params[param], bool):
                    error_msg = f"Parameter '{param}' must be a boolean, got: {type(params[param])}"
                    validation_result['valid'] = False
                    validation_result['errors'].append(error_msg)
                elif param in params:
                    validation_result['validated_params'][param] = params[param]
            
            # Validate languages
            if 'languages' in params:
                languages = params['languages']
                if not isinstance(languages, list):
                    error_msg = f"Languages must be a list, got: {type(languages)}"
                    validation_result['valid'] = False
                    validation_result['errors'].append(error_msg)
                else:
                    validation_result['validated_params']['languages'] = languages
            
            # Validate PSM
            if 'psm' in params:
                psm = params['psm']
                if not isinstance(psm, int) or not (0 <= psm <= 14):
                    error_msg = f"PSM must be an integer between 0 and 14, got: {psm}"
                    validation_result['valid'] = False
                    validation_result['errors'].append(error_msg)
                else:
                    validation_result['validated_params']['psm'] = psm
            
            # Validate encoding parameters
            if 'encoding' in params:
                encoding_params = params['encoding']
                if 'default_encoding' in encoding_params and not isinstance(encoding_params['default_encoding'], str):
                    error_msg = "'default_encoding' must be a string"
                    validation_result['valid'] = False
                    validation_result['errors'].append(error_msg)
                
                if 'fallback_encodings' in encoding_params and not isinstance(encoding_params['fallback_encodings'], list):
                    error_msg = "'fallback_encodings' must be a list"
                    validation_result['valid'] = False
                    validation_result['errors'].append(error_msg)
                
                if 'file_encoding' in encoding_params and not isinstance(encoding_params['file_encoding'], str):
                    error_msg = "'file_encoding' must be a string"
                    validation_result['valid'] = False
                    validation_result['errors'].append(error_msg)
                
                if 'console_encoding' in encoding_params and not isinstance(encoding_params['console_encoding'], str):
                    error_msg = "'console_encoding' must be a string"
                    validation_result['valid'] = False
                    validation_result['errors'].append(error_msg)
                
                if 'strict_mode' in encoding_params and not isinstance(encoding_params['strict_mode'], bool):
                    error_msg = "'strict_mode' must be a boolean"
                    validation_result['valid'] = False
                    validation_result['errors'].append(error_msg)
                
                if 'auto_detect' in encoding_params and not isinstance(encoding_params['auto_detect'], bool):
                    error_msg = "'auto_detect' must be a boolean"
                    validation_result['valid'] = False
                    validation_result['errors'].append(error_msg)
                
                if 'error_handling' in encoding_params:
                    valid_error_handling = ['strict', 'ignore', 'replace', 'backslashreplace']
                    if encoding_params['error_handling'] not in valid_error_handling:
                        error_msg = f"'error_handling' must be one of {valid_error_handling}"
                        validation_result['valid'] = False
                        validation_result['errors'].append(error_msg)
            
            # Log validation result
            if validation_result['valid']:
                self.logger.info("Parameter validation passed")
            else:
                self.logger.error(f"Parameter validation failed - {', '.join(validation_result['errors'])}")
            
            return validation_result
            
        except Exception as e:
            error_msg = f"Error validating parameters: {e}"
            self.error_handler.handle_validation_error(Exception(error_msg))
            return {
                'valid': False,
                'errors': [error_msg],
                'warnings': [],
                'validated_params': {}
            }
    
    def sanitize_output_path(self, output_path: str) -> str:
        """
        Sanitize output path for security.
        
        Args:
            output_path: Raw output path
            
        Returns:
            str: Sanitized output path
        """
        try:
            # Check path length
            if len(output_path) > self.default_validation_config['max_path_length']:
                raise SecurityError(f"Output path too long: {len(output_path)} characters")
            
            # Normalize path
            normalized_path = os.path.normpath(output_path)
            
            # Check for directory traversal attempts
            if '..' in normalized_path:
                raise SecurityError("Directory traversal attempt detected in output path")
            
            # Check for potentially dangerous characters
            dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
            for char in dangerous_chars:
                if char in normalized_path:
                    raise SecurityError(f"Dangerous character detected in output path: {char}")
            
            # Check file extension
            _, extension = os.path.splitext(normalized_path)
            if extension.lower() not in ['.md', '.markdown']:
                # If no extension or wrong extension, add .md
                if not extension:
                    normalized_path += '.md'
                else:
                    self.logger.warning(f"Output file has non-markdown extension: {extension}")
            
            # Create directory if it doesn't exist
            output_dir = os.path.dirname(normalized_path)
            if output_dir and not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except Exception as e:
                    raise FileOperationError(f"Failed to create output directory: {output_dir}", output_dir, 'create')
            
            # Check write permissions
            if self.default_validation_config['check_file_permissions']:
                permission_result = self._check_file_permissions(output_dir, 'write')
                if not permission_result['has_permission']:
                    raise FileOperationError(f"No write permission for output directory: {output_dir}", output_dir, 'write')
            
            self.logger.info(f"Output path sanitized: {normalized_path}")
            return normalized_path
            
        except Exception as e:
            error_msg = f"Error sanitizing output path: {e}"
            self.error_handler.handle_security_error(Exception(error_msg), 'output_path_sanitization')
            raise SecurityError(error_msg)
    
    def check_file_permissions(self, file_path: str, operation: str) -> bool:
        """
        Check file permissions for specified operation.
        
        Args:
            file_path: Path to file
            operation: Operation type (read, write, execute)
            
        Returns:
            bool: True if permissions allow operation
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            if operation == 'read':
                return os.access(file_path, os.R_OK)
            elif operation == 'write':
                return os.access(file_path, os.W_OK)
            elif operation == 'execute':
                return os.access(file_path, os.X_OK)
            else:
                return False
                
        except Exception as e:
            error_msg = f"Error checking file permissions: {e}"
            self.error_handler.handle_file_error(Exception(error_msg), file_path, 'permission_check')
            return False
    
    def _check_file_permissions(self, file_path: str, operation: str) -> Dict[str, Any]:
        """Check file permissions with detailed result."""
        try:
            has_permission = self.check_file_permissions(file_path, operation)
            
            result = {
                'has_permission': has_permission,
                'operation': operation,
                'file_path': file_path,
                'error': None
            }
            
            if not has_permission:
                result['error'] = f"No {operation} permission for file: {file_path}"
            
            return result
            
        except Exception as e:
            return {
                'has_permission': False,
                'operation': operation,
                'file_path': file_path,
                'error': str(e)
            }
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get detailed file information."""
        try:
            stat = os.stat(file_path)
            
            file_info = {
                'size': stat.st_size,
                'modified_time': stat.st_mtime,
                'created_time': stat.st_ctime,
                'extension': os.path.splitext(file_path)[1].lower(),
                'is_image': False,
                'width': None,
                'height': None,
                'mime_type': mimetypes.guess_type(file_path)[0],
                'file_hash': None
            }
            
            # Check if it's an image file
            supported_extensions = self.default_validation_config['supported_formats']
            if file_info['extension'] in supported_extensions:
                file_info['is_image'] = True
                
                # Try to get image dimensions
                try:
                    from PIL import Image
                    with Image.open(file_path) as img:
                        file_info['width'] = img.width
                        file_info['height'] = img.height
                except Exception:
                    pass
            
            # Calculate file hash
            if self.default_validation_config['validate_file_integrity']:
                file_info['file_hash'] = self._calculate_file_hash(file_path)
            
            return file_info
            
        except Exception as e:
            self.logger.error(f"Error getting file info for {file_path}: {e}")
            return {
                'size': 0,
                'modified_time': 0,
                'created_time': 0,
                'extension': '',
                'is_image': False,
                'width': None,
                'height': None,
                'mime_type': None,
                'file_hash': None
            }
    
    def _validate_file_size(self, file_size: int, file_path: str) -> Dict[str, Any]:
        """Validate file size."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        max_size = self.default_validation_config['max_file_size']
        min_size = self.default_validation_config['min_file_size']
        
        if file_size > max_size:
            error_msg = f"File size {file_size} bytes exceeds maximum allowed size {max_size} bytes"
            result['valid'] = False
            result['errors'].append(error_msg)
        
        if file_size < min_size:
            error_msg = f"File size {file_size} bytes is below minimum allowed size {min_size} bytes"
            result['valid'] = False
            result['errors'].append(error_msg)
        
        if file_size > max_size * 0.8:  # 80% of max size
            warning_msg = f"File size {file_size} bytes is close to maximum allowed size {max_size} bytes"
            result['warnings'].append(warning_msg)
        
        return result
    
    def _validate_file_format(self, file_extension: str, file_path: str) -> Dict[str, Any]:
        """Validate file format."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        supported_formats = self.default_validation_config['supported_formats']
        
        if file_extension not in supported_formats:
            error_msg = f"Unsupported file format: {file_extension}"
            result['valid'] = False
            result['errors'].append(error_msg)
        
        return result
    
    def _validate_image_dimensions(self, width: int, height: int, file_path: str) -> Dict[str, Any]:
        """Validate image dimensions."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        max_width = self.default_validation_config['max_image_width']
        max_height = self.default_validation_config['max_image_height']
        
        if width > max_width:
            error_msg = f"Image width {width} pixels exceeds maximum allowed width {max_width} pixels"
            result['valid'] = False
            result['errors'].append(error_msg)
        
        if height > max_height:
            error_msg = f"Image height {height} pixels exceeds maximum allowed height {max_height} pixels"
            result['valid'] = False
            result['errors'].append(error_msg)
        
        if width > max_width * 0.8:  # 80% of max width
            warning_msg = f"Image width {width} pixels is close to maximum allowed width {max_width} pixels"
            result['warnings'].append(warning_msg)
        
        if height > max_height * 0.8:  # 80% of max height
            warning_msg = f"Image height {height} pixels is close to maximum allowed height {max_height} pixels"
            result['warnings'].append(warning_msg)
        
        return result
    
    def _validate_file_integrity(self, file_path: str) -> Dict[str, Any]:
        """Validate file integrity."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Try to open the file
            with open(file_path, 'rb') as f:
                # Read first few bytes to check if file is readable
                f.read(1024)
            
            # Check if file can be opened as image if it's supposed to be an image
            file_info = self._get_file_info(file_path)
            if file_info['is_image']:
                try:
                    from PIL import Image
                    with Image.open(file_path) as img:
                        img.verify()  # Verify image integrity
                except Exception as e:
                    error_msg = f"Image file is corrupted: {e}"
                    result['valid'] = False
                    result['errors'].append(error_msg)
            
        except Exception as e:
            error_msg = f"File integrity check failed: {e}"
            result['valid'] = False
            result['errors'].append(error_msg)
        
        return result
    
    def _validate_filename(self, filename: str) -> Dict[str, Any]:
        """Validate filename."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        max_length = self.default_validation_config['max_filename_length']
        allowed_pattern = self.default_validation_config['allowed_characters']
        
        if len(filename) > max_length:
            error_msg = f"Filename too long: {len(filename)} characters (max: {max_length})"
            result['valid'] = False
            result['errors'].append(error_msg)
        
        if not re.match(allowed_pattern, filename):
            error_msg = f"Filename contains invalid characters: {filename}"
            result['valid'] = False
            result['errors'].append(error_msg)
        
        if filename.startswith('.') or filename.startswith(' '):
            warning_msg = f"Filename starts with dot or space: {filename}"
            result['warnings'].append(warning_msg)
        
        if filename.endswith(' '):
            warning_msg = f"Filename ends with space: {filename}"
            result['warnings'].append(warning_msg)
        
        return result
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file."""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating file hash: {e}")
            return ""
    
    def validate_batch_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Validate multiple files for batch processing.
        
        Args:
            file_paths: List of file paths to validate
            
        Returns:
            Dict: Batch validation results
        """
        try:
            batch_result = {
                'total_files': len(file_paths),
                'valid_files': 0,
                'invalid_files': 0,
                'validation_results': {},
                'summary': {
                    'total_errors': 0,
                    'total_warnings': 0,
                    'error_types': {},
                    'warning_types': {}
                }
            }
            
            if len(file_paths) > self.default_validation_config['max_concurrent_files']:
                warning_msg = f"Batch size {len(file_paths)} exceeds recommended maximum of {self.default_validation_config['max_concurrent_files']}"
                self.logger.warning(warning_msg)
                batch_result['summary']['warnings'].append(warning_msg)
                batch_result['summary']['total_warnings'] += 1
            
            for file_path in file_paths:
                validation_result = self.validate_image_file(file_path)
                batch_result['validation_results'][file_path] = validation_result
                
                if validation_result['valid']:
                    batch_result['valid_files'] += 1
                else:
                    batch_result['invalid_files'] += 1
                    batch_result['summary']['total_errors'] += len(validation_result['errors'])
                    
                    # Count error types
                    for error in validation_result['errors']:
                        error_type = error.split(':')[0] if ':' in error else 'Unknown'
                        batch_result['summary']['error_types'][error_type] = batch_result['summary']['error_types'].get(error_type, 0) + 1
                
                # Count warnings
                batch_result['summary']['total_warnings'] += len(validation_result['warnings'])
                
                # Count warning types
                for warning in validation_result['warnings']:
                    warning_type = warning.split(':')[0] if ':' in warning else 'Unknown'
                    batch_result['summary']['warning_types'][warning_type] = batch_result['summary']['warning_types'].get(warning_type, 0) + 1
            
            batch_result['summary']['success_rate'] = (batch_result['valid_files'] / batch_result['total_files']) * 100 if batch_result['total_files'] > 0 else 0
            
            self.logger.info(f"Batch validation completed: {batch_result['valid_files']}/{batch_result['total_files']} files valid")
            return batch_result
            
        except Exception as e:
            error_msg = f"Error in batch validation: {e}"
            self.error_handler.handle_batch_processing_error(Exception(error_msg), len(file_paths))
            return {
                'total_files': 0,
                'valid_files': 0,
                'invalid_files': 0,
                'validation_results': {},
                'summary': {
                    'total_errors': 1,
                    'total_warnings': 0,
                    'error_types': {'BatchValidation': 1},
                    'warning_types': {},
                    'success_rate': 0
                }
            }
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Update validation configuration.
        
        Args:
            config: New validation configuration
        """
        try:
            self._merge_validation_config(config)
            self.logger.info("Validation configuration updated")
        except Exception as e:
            error_msg = f"Failed to update validation configuration: {e}"
            self.error_handler.handle_configuration_error(Exception(error_msg))
            raise ValidationError(error_msg)
    
    def get_validation_config(self) -> Dict[str, Any]:
        """
        Get current validation configuration.
        
        Returns:
            Dict: Current validation configuration
        """
        return self.default_validation_config.copy()
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get validation configuration summary.
        
        Returns:
            Dict: Validation summary
        """
        return {
            'max_file_size': self.default_validation_config['max_file_size'],
            'min_file_size': self.default_validation_config['min_file_size'],
            'max_image_width': self.default_validation_config['max_image_width'],
            'max_image_height': self.default_validation_config['max_image_height'],
            'supported_formats': self.default_validation_config['supported_formats'],
            'max_filename_length': self.default_validation_config['max_filename_length'],
            'max_path_length': self.default_validation_config['max_path_length'],
            'check_file_permissions': self.default_validation_config['check_file_permissions'],
            'validate_file_integrity': self.default_validation_config['validate_file_integrity'],
            'max_concurrent_files': self.default_validation_config['max_concurrent_files']
        }