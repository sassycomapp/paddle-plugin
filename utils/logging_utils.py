"""
Logging Utilities Module

This module provides utility functions for logging and monitoring.
It includes various logging configuration and management techniques.

Author: Kilo Code
Version: 1.0.0
"""

import logging
import logging.handlers
import os
import sys
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json

# Local imports
from errors.exceptions import LoggingError
from errors.handler import ErrorHandler


class LoggingUtils:
    """
    Utility class for logging and monitoring.
    Provides various logging configuration and management techniques.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize logging utilities.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler()
        self.config = config or {}
        
        # Default settings
        self.default_settings = {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'date_format': '%Y-%m-%d %H:%M:%S',
            'file': None,
            'max_size': '10MB',
            'backup_count': 5,
            'console': True,
            'enable_file_logging': True,
            'enable_console_logging': True,
            'enable_structured_logging': False,
            'log_directory': './logs',
            'create_log_directory': True
        }
        
        # Merge with provided config
        if config:
            self.default_settings.update(config)
        
        # Initialize loggers
        self.loggers = {}
        self.setup_logging()
    
    def setup_logging(self, logger_name: str = None) -> bool:
        """
        Setup logging configuration.
        
        Args:
            logger_name: Logger name to setup (None for root logger)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get logger
            if logger_name:
                logger = logging.getLogger(logger_name)
            else:
                logger = logging.getLogger()
            
            # Clear existing handlers
            logger.handlers.clear()
            
            # Set level
            level = self.default_settings['level']
            logger.setLevel(getattr(logging, level.upper()))
            
            # Create formatter
            formatter = logging.Formatter(
                fmt=self.default_settings['format'],
                datefmt=self.default_settings['date_format']
            )
            
            # Console handler
            if self.default_settings['enable_console_logging']:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(logger.level)
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)
            
            # File handler
            if self.default_settings['enable_file_logging']:
                file_handler = self._create_file_handler()
                if file_handler:
                    file_handler.setLevel(logger.level)
                    file_handler.setFormatter(formatter)
                    logger.addHandler(file_handler)
            
            # Store logger
            if logger_name:
                self.loggers[logger_name] = logger
            
            self.logger.info(f"Logging setup completed for {logger_name or 'root'} logger")
            return True
            
        except Exception as e:
            error_msg = f"Error setting up logging: {e}"
            self.error_handler.handle_logging_error(Exception(error_msg))
            return False
    
    def _create_file_handler(self) -> Optional[logging.Handler]:
        """Create file handler with rotation."""
        try:
            log_file = self.default_settings['file']
            
            if not log_file:
                # Create default log file
                log_file = os.path.join(
                    self.default_settings['log_directory'],
                    f'converter_{datetime.now().strftime("%Y%m%d")}.log'
                )
            
            # Create log directory if needed
            log_dir = os.path.dirname(log_file)
            if log_dir and self.default_settings['create_log_directory']:
                os.makedirs(log_dir, exist_ok=True)
            
            # Parse max size
            max_size = self._parse_size(self.default_settings['max_size'])
            
            # Create rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_size,
                backupCount=self.default_settings['backup_count']
            )
            
            return file_handler
            
        except Exception as e:
            error_msg = f"Error creating file handler: {e}"
            self.error_handler.handle_logging_error(Exception(error_msg))
            return None
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes."""
        try:
            size_str = size_str.upper()
            
            if size_str.endswith('KB'):
                return int(size_str[:-2]) * 1024
            elif size_str.endswith('MB'):
                return int(size_str[:-2]) * 1024 * 1024
            elif size_str.endswith('GB'):
                return int(size_str[:-2]) * 1024 * 1024 * 1024
            else:
                return int(size_str)
                
        except Exception:
            return 10 * 1024 * 1024  # Default to 10MB
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get logger instance.
        
        Args:
            name: Logger name
            
        Returns:
            logging.Logger: Logger instance
        """
        try:
            if name not in self.loggers:
                logger = logging.getLogger(name)
                self.loggers[name] = logger
            
            return self.loggers[name]
            
        except Exception as e:
            error_msg = f"Error getting logger {name}: {e}"
            self.error_handler.handle_logging_error(Exception(error_msg))
            return logging.getLogger()
    
    def log_event(self, logger_name: str, level: str, message: str, **kwargs) -> None:
        """
        Log event with structured data.
        
        Args:
            logger_name: Logger name
            level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
            message: Log message
            **kwargs: Additional data to log
        """
        try:
            logger = self.get_logger(logger_name)
            log_level = getattr(logging, level.upper())
            
            # Create structured log entry
            if self.default_settings['enable_structured_logging']:
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'level': level,
                    'logger': logger_name,
                    'message': message,
                    'data': kwargs
                }
                structured_message = json.dumps(log_entry, ensure_ascii=False)
                logger.log(log_level, structured_message)
            else:
                # Format additional data
                if kwargs:
                    data_str = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
                    message = f"{message} [{data_str}]"
                
                logger.log(log_level, message)
                
        except Exception as e:
            error_msg = f"Error logging event: {e}"
            self.error_handler.handle_logging_error(Exception(error_msg))
    
    def log_processing_event(self, logger_name: str, event_type: str, message: str, data: Dict = None) -> None:
        """
        Log processing event.
        
        Args:
            logger_name: Logger name
            event_type: Event type (e.g., 'start', 'progress', 'complete', 'error')
            message: Log message
            data: Additional event data
        """
        try:
            event_data = {
                'event_type': event_type,
                'timestamp': datetime.now().isoformat()
            }
            
            if data:
                event_data.update(data)
            
            self.log_event(logger_name, 'INFO', message, **event_data)
            
        except Exception as e:
            error_msg = f"Error logging processing event: {e}"
            self.error_handler.handle_logging_error(Exception(error_msg))
    
    def log_error(self, logger_name: str, error: Exception, context: Dict = None) -> None:
        """
        Log error with context.
        
        Args:
            logger_name: Logger name
            error: Exception to log
            context: Additional context data
        """
        try:
            error_data = {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'timestamp': datetime.now().isoformat()
            }
            
            if context:
                error_data.update(context)
            
            self.log_event(logger_name, 'ERROR', f"Error occurred: {error}", **error_data)
            
        except Exception as e:
            error_msg = f"Error logging error: {e}"
            self.error_handler.handle_logging_error(Exception(error_msg))
    
    def log_performance(self, logger_name: str, operation: str, duration: float, **kwargs) -> None:
        """
        Log performance metrics.
        
        Args:
            logger_name: Logger name
            operation: Operation name
            duration: Duration in seconds
            **kwargs: Additional performance data
        """
        try:
            perf_data = {
                'operation': operation,
                'duration_seconds': duration,
                'timestamp': datetime.now().isoformat()
            }
            
            if kwargs:
                perf_data.update(kwargs)
            
            self.log_event(logger_name, 'INFO', f"Performance: {operation}", **perf_data)
            
        except Exception as e:
            error_msg = f"Error logging performance: {e}"
            self.error_handler.handle_logging_error(Exception(error_msg))
    
    def create_audit_logger(self, name: str = 'audit') -> logging.Logger:
        """
        Create audit logger for security and compliance.
        
        Args:
            name: Logger name
            
        Returns:
            logging.Logger: Audit logger instance
        """
        try:
            audit_logger = logging.getLogger(name)
            
            # Clear existing handlers
            audit_logger.handlers.clear()
            
            # Set level
            audit_logger.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                fmt='%(asctime)s - AUDIT - %(message)s',
                datefmt=self.default_settings['date_format']
            )
            
            # Create file handler
            audit_file = os.path.join(
                self.default_settings['log_directory'],
                f'audit_{datetime.now().strftime("%Y%m%d")}.log'
            )
            
            audit_handler = logging.handlers.RotatingFileHandler(
                audit_file,
                maxBytes=self._parse_size('50MB'),
                backupCount=10
            )
            audit_handler.setFormatter(formatter)
            audit_logger.addHandler(audit_handler)
            
            # Store logger
            self.loggers[name] = audit_logger
            
            self.logger.info(f"Audit logger created: {name}")
            return audit_logger
            
        except Exception as e:
            error_msg = f"Error creating audit logger: {e}"
            self.error_handler.handle_logging_error(Exception(error_msg))
            return logging.getLogger()
    
    def log_audit_event(self, user: str, action: str, resource: str, details: Dict = None) -> None:
        """
        Log audit event.
        
        Args:
            user: User performing action
            action: Action performed
            resource: Resource affected
            details: Additional details
        """
        try:
            audit_logger = self.create_audit_logger()
            
            audit_data = {
                'user': user,
                'action': action,
                'resource': resource,
                'timestamp': datetime.now().isoformat()
            }
            
            if details:
                audit_data.update(details)
            
            audit_message = json.dumps(audit_data, ensure_ascii=False)
            audit_logger.info(audit_message)
            
        except Exception as e:
            error_msg = f"Error logging audit event: {e}"
            self.error_handler.handle_logging_error(Exception(error_msg))
    
    def get_log_files(self, log_directory: str = None) -> List[str]:
        """
        Get list of log files.
        
        Args:
            log_directory: Log directory path
            
        Returns:
            List[str]: List of log file paths
        """
        try:
            if log_directory is None:
                log_directory = self.default_settings['log_directory']
            
            if not os.path.exists(log_directory):
                return []
            
            log_files = []
            for filename in os.listdir(log_directory):
                if filename.endswith('.log'):
                    log_files.append(os.path.join(log_directory, filename))
            
            return sorted(log_files)
            
        except Exception as e:
            error_msg = f"Error getting log files: {e}"
            self.error_handler.handle_logging_error(Exception(error_msg))
            return []
    
    def rotate_logs(self) -> bool:
        """
        Rotate log files.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            log_directory = self.default_settings['log_directory']
            if not os.path.exists(log_directory):
                return True
            
            for filename in os.listdir(log_directory):
                if filename.endswith('.log'):
                    log_file = os.path.join(log_directory, filename)
                    
                    # Check if rotation is needed
                    if os.path.exists(log_file):
                        stat = os.stat(log_file)
                        if stat.st_size > self._parse_size(self.default_settings['max_size']):
                            # Force rotation
                            handler = logging.handlers.RotatingFileHandler(
                                log_file,
                                maxBytes=self._parse_size(self.default_settings['max_size']),
                                backupCount=self.default_settings['backup_count']
                            )
                            handler.doRollover()
            
            self.logger.info("Log rotation completed")
            return True
            
        except Exception as e:
            error_msg = f"Error rotating logs: {e}"
            self.error_handler.handle_logging_error(Exception(error_msg))
            return False
    
    def cleanup_old_logs(self, days: int = 30) -> bool:
        """
        Clean up old log files.
        
        Args:
            days: Number of days to keep logs
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            log_directory = self.default_settings['log_directory']
            if not os.path.exists(log_directory):
                return True
            
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for filename in os.listdir(log_directory):
                if filename.endswith('.log'):
                    log_file = os.path.join(log_directory, filename)
                    
                    if os.path.exists(log_file):
                        stat = os.stat(log_file)
                        if stat.st_mtime < cutoff_time:
                            try:
                                os.remove(log_file)
                                self.logger.info(f"Deleted old log file: {log_file}")
                            except Exception as e:
                                self.logger.warning(f"Failed to delete log file {log_file}: {e}")
            
            self.logger.info(f"Cleaned up logs older than {days} days")
            return True
            
        except Exception as e:
            error_msg = f"Error cleaning up old logs: {e}"
            self.error_handler.handle_logging_error(Exception(error_msg))
            return False
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """
        Get logging statistics.
        
        Returns:
            Dict: Logging statistics
        """
        try:
            stats = {
                'log_directory': self.default_settings['log_directory'],
                'log_files': [],
                'total_size': 0,
                'oldest_log': None,
                'newest_log': None
            }
            
            log_files = self.get_log_files()
            
            if not log_files:
                return stats
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    stat = os.stat(log_file)
                    stats['log_files'].append({
                        'path': log_file,
                        'size': stat.st_size,
                        'size_human': self._format_size(stat.st_size),
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                    stats['total_size'] += stat.st_size
                    
                    if stats['oldest_log'] is None or stat.st_mtime < stats['oldest_log']:
                        stats['oldest_log'] = stat.st_mtime
                    
                    if stats['newest_log'] is None or stat.st_mtime > stats['newest_log']:
                        stats['newest_log'] = stat.st_mtime
            
            if stats['oldest_log']:
                stats['oldest_log'] = datetime.fromtimestamp(stats['oldest_log']).isoformat()
            
            if stats['newest_log']:
                stats['newest_log'] = datetime.fromtimestamp(stats['newest_log']).isoformat()
            
            stats['total_size_human'] = self._format_size(stats['total_size'])
            
            return stats
            
        except Exception as e:
            error_msg = f"Error getting log statistics: {e}"
            self.error_handler.handle_logging_error(Exception(error_msg))
            return {}
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Update configuration.
        
        Args:
            config: New configuration
        """
        try:
            self.default_settings.update(config)
            
            # Re-setup logging if needed
            if 'level' in config or 'format' in config or 'file' in config:
                self.setup_logging()
            
            self.logger.info("Logging utilities configuration updated")
            
        except Exception as e:
            error_msg = f"Failed to update configuration: {e}"
            self.error_handler.handle_configuration_error(Exception(error_msg))
            raise LoggingError(error_msg)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.
        
        Returns:
            Dict: Current configuration
        """
        return self.default_settings.copy()
    
    def shutdown(self) -> None:
        """
        Shutdown logging system.
        """
        try:
            for logger in self.loggers.values():
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)
            
            self.logger.info("Logging system shutdown completed")
            
        except Exception as e:
            error_msg = f"Error shutting down logging system: {e}"
            self.error_handler.handle_logging_error(Exception(error_msg))