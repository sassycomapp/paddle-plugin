"""
File Utilities Module

This module provides utility functions for file operations and management.
It includes various file handling, validation, and manipulation techniques.

Author: Kilo Code
Version: 1.0.0
"""

import os
import json
import hashlib
import shutil
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime

# Local imports
from errors.exceptions import FileOperationError, ValidationError
from errors.handler import ErrorHandler


class FileUtils:
    """
    Utility class for file operations and management.
    Provides various file handling, validation, and manipulation techniques.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize file utilities.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler()
        self.config = config or {}
        
        # Default settings
        self.default_settings = {
            'max_file_size': 104857600,  # 100MB
            'min_file_size': 1024,       # 1KB
            'max_filename_length': 255,
            'max_path_length': 4096,
            'allowed_extensions': ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif', '.webp'],
            'backup_enabled': True,
            'backup_count': 5,
            'temp_directory': './temp',
            'cleanup_temp_files': True
        }
        
        # Merge with provided config
        if config:
            self.default_settings.update(config)
    
    def validate_file_path(self, file_path: str) -> Dict[str, Any]:
        """
        Validate file path.
        
        Args:
            file_path: Path to validate
            
        Returns:
            Dict: Validation results
        """
        try:
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'file_info': {}
            }
            
            # Check if path is too long
            if len(file_path) > self.default_settings['max_path_length']:
                error_msg = f"File path too long: {len(file_path)} characters"
                validation_result['valid'] = False
                validation_result['errors'].append(error_msg)
                return validation_result
            
            # Check if file exists
            if not os.path.exists(file_path):
                error_msg = f"File does not exist: {file_path}"
                validation_result['valid'] = False
                validation_result['errors'].append(error_msg)
                return validation_result
            
            # Get file info
            file_info = self.get_file_info(file_path)
            validation_result['file_info'] = file_info
            
            # Validate file size
            size_result = self.validate_file_size(file_info['size'])
            if not size_result['valid']:
                validation_result['valid'] = False
                validation_result['errors'].extend(size_result['errors'])
            
            # Validate file extension
            extension_result = self.validate_file_extension(file_info['extension'])
            if not extension_result['valid']:
                validation_result['valid'] = False
                validation_result['errors'].extend(extension_result['errors'])
            
            # Validate filename
            filename_result = self.validate_filename(file_info['filename'])
            if not filename_result['valid']:
                validation_result['valid'] = False
                validation_result['errors'].extend(filename_result['errors'])
            
            # Add warnings
            validation_result['warnings'].extend(size_result.get('warnings', []))
            validation_result['warnings'].extend(extension_result.get('warnings', []))
            validation_result['warnings'].extend(filename_result.get('warnings', []))
            
            return validation_result
            
        except Exception as e:
            error_msg = f"Error validating file path {file_path}: {e}"
            self.error_handler.handle_file_error(Exception(error_msg), file_path, 'validation')
            return {
                'valid': False,
                'errors': [error_msg],
                'warnings': [],
                'file_info': {}
            }
    
    def validate_file_size(self, file_size: int) -> Dict[str, Any]:
        """
        Validate file size.
        
        Args:
            file_size: File size in bytes
            
        Returns:
            Dict: Validation results
        """
        try:
            result = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            max_size = self.default_settings['max_file_size']
            min_size = self.default_settings['min_file_size']
            
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
            
        except Exception as e:
            error_msg = f"Error validating file size: {e}"
            self.error_handler.handle_validation_error(Exception(error_msg))
            return {
                'valid': False,
                'errors': [error_msg],
                'warnings': []
            }
    
    def validate_file_extension(self, file_extension: str) -> Dict[str, Any]:
        """
        Validate file extension.
        
        Args:
            file_extension: File extension
            
        Returns:
            Dict: Validation results
        """
        try:
            result = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            allowed_extensions = self.default_settings['allowed_extensions']
            
            if file_extension.lower() not in allowed_extensions:
                error_msg = f"File extension '{file_extension}' is not supported"
                result['valid'] = False
                result['errors'].append(error_msg)
            
            return result
            
        except Exception as e:
            error_msg = f"Error validating file extension: {e}"
            self.error_handler.handle_validation_error(Exception(error_msg))
            return {
                'valid': False,
                'errors': [error_msg],
                'warnings': []
            }
    
    def validate_filename(self, filename: str) -> Dict[str, Any]:
        """
        Validate filename.
        
        Args:
            filename: Filename to validate
            
        Returns:
            Dict: Validation results
        """
        try:
            result = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            max_length = self.default_settings['max_filename_length']
            
            if len(filename) > max_length:
                error_msg = f"Filename too long: {len(filename)} characters (max: {max_length})"
                result['valid'] = False
                result['errors'].append(error_msg)
            
            # Check for invalid characters
            import re
            invalid_chars = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
            if invalid_chars.search(filename):
                error_msg = f"Filename contains invalid characters: {filename}"
                result['valid'] = False
                result['errors'].append(error_msg)
            
            # Check for reserved names
            reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
            if filename.upper() in reserved_names:
                error_msg = f"Filename is reserved: {filename}"
                result['valid'] = False
                result['errors'].append(error_msg)
            
            # Check for leading/trailing spaces
            if filename.startswith(' ') or filename.endswith(' '):
                warning_msg = f"Filename has leading or trailing spaces: {filename}"
                result['warnings'].append(warning_msg)
            
            # Check for leading dots
            if filename.startswith('.'):
                warning_msg = f"Filename starts with dot: {filename}"
                result['warnings'].append(warning_msg)
            
            return result
            
        except Exception as e:
            error_msg = f"Error validating filename: {e}"
            self.error_handler.handle_validation_error(Exception(error_msg))
            return {
                'valid': False,
                'errors': [error_msg],
                'warnings': []
            }
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get comprehensive file information.
        
        Args:
            file_path: Path to file
            
        Returns:
            Dict: File information
        """
        try:
            if not os.path.exists(file_path):
                raise FileOperationError(f"File does not exist: {file_path}", file_path, 'read')
            
            stat = os.stat(file_path)
            
            file_info = {
                'path': file_path,
                'filename': os.path.basename(file_path),
                'directory': os.path.dirname(file_path),
                'extension': os.path.splitext(file_path)[1].lower(),
                'size': stat.st_size,
                'size_human': self._format_file_size(stat.st_size),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'accessed': datetime.fromtimestamp(stat.st_atime),
                'is_file': os.path.isfile(file_path),
                'is_directory': os.path.isdir(file_path),
                'is_readable': os.access(file_path, os.R_OK),
                'is_writable': os.access(file_path, os.W_OK),
                'is_executable': os.access(file_path, os.X_OK),
                'permissions': oct(stat.st_mode)[-3:],
                'hash': self.calculate_file_hash(file_path)
            }
            
            return file_info
            
        except Exception as e:
            error_msg = f"Error getting file info for {file_path}: {e}"
            self.error_handler.handle_file_error(Exception(error_msg), file_path, 'info')
            raise FileOperationError(error_msg, file_path, 'info')
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def calculate_file_hash(self, file_path: str, algorithm: str = 'sha256') -> str:
        """
        Calculate file hash.
        
        Args:
            file_path: Path to file
            algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
            
        Returns:
            str: File hash
        """
        try:
            hash_func = hashlib.new(algorithm)
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            
            return hash_func.hexdigest()
            
        except Exception as e:
            error_msg = f"Error calculating hash for {file_path}: {e}"
            self.error_handler.handle_file_error(Exception(error_msg), file_path, 'hash')
            return ""
    
    def create_directory(self, directory_path: str, exist_ok: bool = True) -> bool:
        """
        Create directory.
        
        Args:
            directory_path: Path to directory
            exist_ok: Whether to allow existing directory
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            os.makedirs(directory_path, exist_ok=exist_ok)
            self.logger.debug(f"Created directory: {directory_path}")
            return True
            
        except Exception as e:
            error_msg = f"Error creating directory {directory_path}: {e}"
            self.error_handler.handle_file_error(Exception(error_msg), directory_path, 'create')
            return False
    
    def copy_file(self, source_path: str, destination_path: str, overwrite: bool = False) -> bool:
        """
        Copy file.
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            overwrite: Whether to overwrite existing file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if source exists
            if not os.path.exists(source_path):
                raise FileOperationError(f"Source file does not exist: {source_path}", source_path, 'read')
            
            # Check if destination exists
            if os.path.exists(destination_path) and not overwrite:
                raise FileOperationError(f"Destination file already exists: {destination_path}", destination_path, 'write')
            
            # Create destination directory if needed
            dest_dir = os.path.dirname(destination_path)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            
            # Copy file
            shutil.copy2(source_path, destination_path)
            
            self.logger.debug(f"Copied file: {source_path} -> {destination_path}")
            return True
            
        except Exception as e:
            error_msg = f"Error copying file {source_path} -> {destination_path}: {e}"
            self.error_handler.handle_file_error(Exception(error_msg), destination_path, 'copy')
            return False
    
    def move_file(self, source_path: str, destination_path: str, overwrite: bool = False) -> bool:
        """
        Move file.
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            overwrite: Whether to overwrite existing file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if source exists
            if not os.path.exists(source_path):
                raise FileOperationError(f"Source file does not exist: {source_path}", source_path, 'read')
            
            # Check if destination exists
            if os.path.exists(destination_path) and not overwrite:
                raise FileOperationError(f"Destination file already exists: {destination_path}", destination_path, 'write')
            
            # Create destination directory if needed
            dest_dir = os.path.dirname(destination_path)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            
            # Move file
            shutil.move(source_path, destination_path)
            
            self.logger.debug(f"Moved file: {source_path} -> {destination_path}")
            return True
            
        except Exception as e:
            error_msg = f"Error moving file {source_path} -> {destination_path}: {e}"
            self.error_handler.handle_file_error(Exception(error_msg), destination_path, 'move')
            return False
    
    def delete_file(self, file_path: str, force: bool = False) -> bool:
        """
        Delete file.
        
        Args:
            file_path: Path to file to delete
            force: Whether to delete without confirmation
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileOperationError(f"File does not exist: {file_path}", file_path, 'delete')
            
            # Delete file
            os.remove(file_path)
            
            self.logger.debug(f"Deleted file: {file_path}")
            return True
            
        except Exception as e:
            error_msg = f"Error deleting file {file_path}: {e}"
            self.error_handler.handle_file_error(Exception(error_msg), file_path, 'delete')
            return False
    
    def backup_file(self, file_path: str, backup_count: int = None) -> List[str]:
        """
        Create backup of file.
        
        Args:
            file_path: Path to file to backup
            backup_count: Number of backups to keep
            
        Returns:
            List[str]: List of backup file paths
        """
        try:
            if backup_count is None:
                backup_count = self.default_settings['backup_count']
            
            if not os.path.exists(file_path):
                raise FileOperationError(f"File does not exist: {file_path}", file_path, 'backup')
            
            # Create backup directory
            backup_dir = os.path.join(os.path.dirname(file_path), 'backups')
            self.create_directory(backup_dir)
            
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{os.path.basename(file_path)}.backup_{timestamp}"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Copy file to backup
            shutil.copy2(file_path, backup_path)
            
            # Clean up old backups
            self._cleanup_old_backups(file_path, backup_count)
            
            self.logger.debug(f"Created backup: {backup_path}")
            return [backup_path]
            
        except Exception as e:
            error_msg = f"Error creating backup for {file_path}: {e}"
            self.error_handler.handle_file_error(Exception(error_msg), file_path, 'backup')
            return []
    
    def _cleanup_old_backups(self, file_path: str, keep_count: int) -> None:
        """Clean up old backup files."""
        try:
            backup_dir = os.path.join(os.path.dirname(file_path), 'backups')
            if not os.path.exists(backup_dir):
                return
            
            # Get all backup files
            base_name = os.path.basename(file_path)
            backup_files = []
            
            for filename in os.listdir(backup_dir):
                if filename.startswith(base_name + '.backup_'):
                    backup_path = os.path.join(backup_dir, filename)
                    backup_files.append((backup_path, os.path.getmtime(backup_path)))
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Delete old backups
            for backup_path, _ in backup_files[keep_count:]:
                try:
                    os.remove(backup_path)
                    self.logger.debug(f"Deleted old backup: {backup_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to delete old backup {backup_path}: {e}")
                    
        except Exception as e:
            self.logger.warning(f"Error cleaning up old backups: {e}")
    
    def list_files(self, directory: str, pattern: str = None, recursive: bool = False) -> List[str]:
        """
        List files in directory.
        
        Args:
            directory: Directory to search
            pattern: File pattern to match
            recursive: Whether to search recursively
            
        Returns:
            List[str]: List of file paths
        """
        try:
            if not os.path.exists(directory):
                raise FileOperationError(f"Directory does not exist: {directory}", directory, 'read')
            
            files = []
            
            if recursive:
                for root, dirs, filenames in os.walk(directory):
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        if pattern is None or self._matches_pattern(file_path, pattern):
                            files.append(file_path)
            else:
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    if os.path.isfile(file_path):
                        if pattern is None or self._matches_pattern(file_path, pattern):
                            files.append(file_path)
            
            return sorted(files)
            
        except Exception as e:
            error_msg = f"Error listing files in {directory}: {e}"
            self.error_handler.handle_file_error(Exception(error_msg), directory, 'list')
            return []
    
    def _matches_pattern(self, file_path: str, pattern: str) -> bool:
        """Check if file path matches pattern."""
        import fnmatch
        return fnmatch.fnmatch(os.path.basename(file_path), pattern)
    
    def read_json_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Dict: JSON data
        """
        try:
            if not os.path.exists(file_path):
                raise FileOperationError(f"JSON file does not exist: {file_path}", file_path, 'read')
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data
            
        except Exception as e:
            error_msg = f"Error reading JSON file {file_path}: {e}"
            self.error_handler.handle_file_error(Exception(error_msg), file_path, 'read')
            raise FileOperationError(error_msg, file_path, 'read')
    
    def write_json_file(self, file_path: str, data: Dict[str, Any], indent: int = 2) -> bool:
        """
        Write JSON file.
        
        Args:
            file_path: Path to JSON file
            data: JSON data to write
            indent: JSON indentation
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create directory if needed
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            # Write JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            
            self.logger.debug(f"Wrote JSON file: {file_path}")
            return True
            
        except Exception as e:
            error_msg = f"Error writing JSON file {file_path}: {e}"
            self.error_handler.handle_file_error(Exception(error_msg), file_path, 'write')
            return False
    
    def create_temp_file(self, content: str = None, suffix: str = None) -> str:
        """
        Create temporary file.
        
        Args:
            content: File content
            suffix: File suffix
            
        Returns:
            str: Temporary file path
        """
        try:
            # Create temp directory if needed
            temp_dir = self.default_settings['temp_directory']
            self.create_directory(temp_dir)
            
            # Create temp file
            import tempfile
            temp_fd, temp_path = tempfile.mkstemp(suffix=suffix, dir=temp_dir)
            
            # Write content if provided
            if content is not None:
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                os.close(temp_fd)
            
            self.logger.debug(f"Created temp file: {temp_path}")
            return temp_path
            
        except Exception as e:
            error_msg = f"Error creating temp file: {e}"
            self.error_handler.handle_file_error(Exception(error_msg), temp_dir, 'create')
            raise FileOperationError(error_msg, temp_dir, 'create')
    
    def cleanup_temp_files(self) -> bool:
        """
        Clean up temporary files.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            temp_dir = self.default_settings['temp_directory']
            if not os.path.exists(temp_dir):
                return True
            
            # Remove all files in temp directory
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    self.logger.warning(f"Failed to delete temp file {file_path}: {e}")
            
            self.logger.debug("Cleaned up temp files")
            return True
            
        except Exception as e:
            error_msg = f"Error cleaning up temp files: {e}"
            self.error_handler.handle_file_error(Exception(error_msg), temp_dir, 'cleanup')
            return False
    
    def get_file_permissions(self, file_path: str) -> Dict[str, Any]:
        """
        Get file permissions.
        
        Args:
            file_path: Path to file
            
        Returns:
            Dict: File permissions
        """
        try:
            if not os.path.exists(file_path):
                raise FileOperationError(f"File does not exist: {file_path}", file_path, 'read')
            
            stat = os.stat(file_path)
            
            permissions = {
                'readable': os.access(file_path, os.R_OK),
                'writable': os.access(file_path, os.W_OK),
                'executable': os.access(file_path, os.X_OK),
                'mode': oct(stat.st_mode)[-3:],
                'uid': stat.st_uid,
                'gid': stat.st_gid
            }
            
            return permissions
            
        except Exception as e:
            error_msg = f"Error getting permissions for {file_path}: {e}"
            self.error_handler.handle_file_error(Exception(error_msg), file_path, 'permissions')
            raise FileOperationError(error_msg, file_path, 'permissions')
    
    def set_file_permissions(self, file_path: str, permissions: str) -> bool:
        """
        Set file permissions.
        
        Args:
            file_path: Path to file
            permissions: Permission string (e.g., '755')
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                raise FileOperationError(f"File does not exist: {file_path}", file_path, 'write')
            
            # Convert permission string to octal
            mode = int(permissions, 8)
            os.chmod(file_path, mode)
            
            self.logger.debug(f"Set permissions for {file_path} to {permissions}")
            return True
            
        except Exception as e:
            error_msg = f"Error setting permissions for {file_path}: {e}"
            self.error_handler.handle_file_error(Exception(error_msg), file_path, 'permissions')
            return False
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Update configuration.
        
        Args:
            config: New configuration
        """
        try:
            self.default_settings.update(config)
            self.logger.info("File utilities configuration updated")
        except Exception as e:
            error_msg = f"Failed to update configuration: {e}"
            self.error_handler.handle_configuration_error(Exception(error_msg))
            raise FileOperationError(error_msg, '', 'config')
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.
        
        Returns:
            Dict: Current configuration
        """
        return self.default_settings.copy()