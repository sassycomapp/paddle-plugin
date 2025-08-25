"""
Error Handler Module

This module provides comprehensive error handling and logging system.
It provides graceful degradation and detailed error reporting.

Author: Kilo Code
Version: 1.0.0
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

# Local imports
from .exceptions import (
    PNGToMarkdownError,
    DependencyError,
    ImageError,
    OCRError,
    ConfigurationError,
    FileOperationError,
    ProcessingError,
    ValidationError,
    TimeoutError,
    MemoryError,
    ConversionError,
    BatchProcessingError,
    QualityError,
    PreprocessingError,
    FormattingError,
    MetadataError,
    SecurityError,
    NetworkError,
    SystemError,
    UnsupportedFormatError,
    PermissionError,
    ResourceNotFoundError,
    DataCorruptionError,
    ConcurrentProcessingError,
    InitializationError,
    CleanupError,
    CacheError,
    PerformanceError,
    EncodingError
)


class ErrorHandler:
    """
    Comprehensive error handling and logging system.
    Provides graceful degradation and detailed error reporting.
    """
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None):
        """
        Initialize error handler.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path
        """
        self.log_level = log_level
        self.log_file = log_file
        self.logger = self._setup_logger()
        
        # Error statistics
        self.error_stats = {
            'total_errors': 0,
            'error_by_type': {},
            'error_by_module': {},
            'recent_errors': [],
            'error_history': []
        }
        
        # Recovery strategies
        self.recovery_strategies = {
            'DependencyError': self._recover_from_dependency_error,
            'ImageError': self._recover_from_image_error,
            'OCRError': self._recover_from_ocr_error,
            'ConfigurationError': self._recover_from_configuration_error,
            'FileOperationError': self._recover_from_file_error,
            'ProcessingError': self._recover_from_processing_error,
            'ValidationError': self._recover_from_validation_error,
            'TimeoutError': self._recover_from_timeout_error,
            'MemoryError': self._recover_from_memory_error,
            'ConversionError': self._recover_from_conversion_error,
            'BatchProcessingError': self._recover_from_batch_error,
            'QualityError': self._recover_from_quality_error,
            'PreprocessingError': self._recover_from_preprocessing_error,
            'FormattingError': self._recover_from_formatting_error,
            'MetadataError': self._recover_from_metadata_error,
            'SecurityError': self._recover_from_security_error,
            'NetworkError': self._recover_from_network_error,
            'SystemError': self._recover_from_system_error,
            'UnsupportedFormatError': self._recover_from_unsupported_format_error,
            'PermissionError': self._recover_from_permission_error,
            'ResourceNotFoundError': self._recover_from_resource_not_found_error,
            'DataCorruptionError': self._recover_from_data_corruption_error,
            'ConcurrentProcessingError': self._recover_from_concurrent_error,
            'InitializationError': self._recover_from_initialization_error,
            'CleanupError': self._recover_from_cleanup_error,
            'CacheError': self._recover_from_cache_error,
            'PerformanceError': self._recover_from_performance_error,
            'EncodingError': self._recover_from_encoding_error
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger('PNGToMarkdownConverter')
        logger.setLevel(getattr(logging, self.log_level))
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.log_level))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        if self.log_file:
            # Create log directory if it doesn't exist
            log_dir = Path(self.log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(getattr(logging, self.log_level))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle any type of error with appropriate recovery strategy.
        
        Args:
            error: Exception that occurred
            context: Context information
            
        Returns:
            Dict: Error response with recovery suggestions
        """
        try:
            context = context or {}
            
            # Log the error
            self._log_error(error, context)
            
            # Update error statistics
            self._update_error_stats(error)
            
            # Get error type
            error_type = type(error).__name__
            
            # Apply recovery strategy if available
            if error_type in self.recovery_strategies:
                recovery_result = self.recovery_strategies[error_type](error, context)
            else:
                recovery_result = self._recover_from_generic_error(error, context)
            
            # Return error response
            error_response = {
                'error_type': error_type,
                'error_message': str(error),
                'timestamp': datetime.now().isoformat(),
                'context': context,
                'recovery_suggestions': recovery_result.get('suggestions', []),
                'recovery_actions': recovery_result.get('actions', []),
                'severity': recovery_result.get('severity', 'medium'),
                'recoverable': recovery_result.get('recoverable', False)
            }
            
            return error_response
            
        except Exception as e:
            # If error handling fails, return basic error response
            return {
                'error_type': 'ErrorHandlerError',
                'error_message': f"Error handling failed: {e}",
                'timestamp': datetime.now().isoformat(),
                'context': context,
                'recovery_suggestions': ['Check system logs for details'],
                'recovery_actions': [],
                'severity': 'critical',
                'recoverable': False
            }
    
    def handle_ocr_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle OCR-specific errors.
        
        Args:
            error: Exception that occurred
            context: Context information
            
        Returns:
            Dict: Error response with recovery suggestions
        """
        return self.handle_error(error, context or {'module': 'OCR'})
    
    def handle_image_error(self, error: Exception, image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle image processing errors.
        
        Args:
            error: Exception that occurred
            image_path: Path to the problematic image
            
        Returns:
            Dict: Error response with recovery suggestions
        """
        context = {'module': 'Image'}
        if image_path:
            context['image_path'] = image_path
        
        return self.handle_error(error, context)
    
    def handle_file_error(self, error: Exception, file_path: Optional[str] = None, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle file operation errors.
        
        Args:
            error: Exception that occurred
            file_path: Path to the problematic file
            operation: File operation that failed
            
        Returns:
            Dict: Error response with recovery suggestions
        """
        context = {'module': 'File'}
        if file_path:
            context['file_path'] = file_path
        if operation:
            context['operation'] = operation
        
        return self.handle_error(error, context)
    
    def handle_configuration_error(self, error: Exception, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle configuration errors.
        
        Args:
            error: Exception that occurred
            config_path: Path to the problematic configuration
            
        Returns:
            Dict: Error response with recovery suggestions
        """
        context = {'module': 'Configuration'}
        if config_path:
            context['config_path'] = config_path
        
        return self.handle_error(error, context)
    
    def handle_processing_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle general processing errors.
        
        Args:
            error: Exception that occurred
            context: Context information
            
        Returns:
            Dict: Error response with recovery suggestions
        """
        return self.handle_error(error, context or {'module': 'Processing'})
    
    def handle_encoding_error(self, error: Exception, file_path: str = None, operation: str = None) -> Dict[str, Any]:
        """
        Handle encoding-specific errors.
        
        Args:
            error: Exception that occurred
            file_path: Path to the problematic file
            operation: Operation that failed due to encoding
            
        Returns:
            Dict: Error response with recovery suggestions
        """
        context = {'module': 'Encoding'}
        if file_path:
            context['file_path'] = file_path
        if operation:
            context['operation'] = operation
        
        return self.handle_error(error, context)
    
    def log_processing_event(self, event_type: str, message: str, data: Optional[Dict] = None):
        """Log processing events with structured data."""
        event_data = {
            'event_type': event_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'data': data or {}
        }
        
        if event_type == 'ERROR':
            self.logger.error(f"{message} - Data: {data}")
        elif event_type == 'WARNING':
            self.logger.warning(f"{message} - Data: {data}")
        elif event_type == 'INFO':
            self.logger.info(f"{message} - Data: {data}")
        elif event_type == 'DEBUG':
            self.logger.debug(f"{message} - Data: {data}")
        else:
            self.logger.info(f"{message} - Data: {data}")
    
    def create_error_report(self, errors: List[Dict]) -> str:
        """
        Create comprehensive error report.
        
        Args:
            errors: List of error dictionaries
            
        Returns:
            str: Formatted error report
        """
        if not errors:
            return "No errors to report."
        
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("PNG TO MARKDOWN CONVERTER - ERROR REPORT")
        report_lines.append("=" * 60)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Total Errors: {len(errors)}")
        report_lines.append("")
        
        # Error summary
        error_types = {}
        for error in errors:
            error_type = error.get('error_type', 'Unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        report_lines.append("ERROR SUMMARY:")
        report_lines.append("-" * 40)
        for error_type, count in error_types.items():
            report_lines.append(f"{error_type}: {count}")
        report_lines.append("")
        
        # Detailed errors
        report_lines.append("DETAILED ERRORS:")
        report_lines.append("-" * 40)
        
        for i, error in enumerate(errors, 1):
            report_lines.append(f"Error {i}:")
            report_lines.append(f"  Type: {error.get('error_type', 'Unknown')}")
            report_lines.append(f"  Message: {error.get('error_message', 'No message')}")
            report_lines.append(f"  Timestamp: {error.get('timestamp', 'Unknown')}")
            report_lines.append(f"  Severity: {error.get('severity', 'Unknown')}")
            report_lines.append(f"  Recoverable: {error.get('recoverable', False)}")
            
            if error.get('context'):
                report_lines.append(f"  Context: {error['context']}")
            
            if error.get('recovery_suggestions'):
                report_lines.append("  Recovery Suggestions:")
                for suggestion in error['recovery_suggestions']:
                    report_lines.append(f"    - {suggestion}")
            
            report_lines.append("")
        
        # Statistics
        report_lines.append("ERROR STATISTICS:")
        report_lines.append("-" * 40)
        report_lines.append(f"Total Errors: {self.error_stats['total_errors']}")
        
        if self.error_stats['error_by_type']:
            report_lines.append("Errors by Type:")
            for error_type, count in self.error_stats['error_by_type'].items():
                report_lines.append(f"  {error_type}: {count}")
        
        if self.error_stats['error_by_module']:
            report_lines.append("Errors by Module:")
            for module, count in self.error_stats['error_by_module'].items():
                report_lines.append(f"  {module}: {count}")
        
        report_lines.append("")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def _log_error(self, error: Exception, context: Dict[str, Any]):
        """Log error with context."""
        error_type = type(error).__name__
        error_message = str(error)
        
        # Create detailed error message
        log_message = f"Error occurred: {error_type} - {error_message}"
        if context:
            log_message += f" - Context: {context}"
        
        # Log with appropriate level
        if isinstance(error, (DependencyError, ImageError, OCRError, ConfigurationError)):
            self.logger.error(log_message, exc_info=True)
        elif isinstance(error, (FileOperationError, ProcessingError, ValidationError)):
            self.logger.warning(log_message, exc_info=True)
        else:
            self.logger.error(log_message, exc_info=True)
    
    def _update_error_stats(self, error: Exception):
        """Update error statistics."""
        self.error_stats['total_errors'] += 1
        
        # Update by type
        error_type = type(error).__name__
        self.error_stats['error_by_type'][error_type] = (
            self.error_stats['error_by_type'].get(error_type, 0) + 1
        )
        
        # Update by module (extract from context)
        context = getattr(error, 'context', {})
        module = context.get('module', 'Unknown')
        self.error_stats['error_by_module'][module] = (
            self.error_stats['error_by_module'].get(module, 0) + 1
        )
        
        # Add to recent errors
        recent_error = {
            'error_type': error_type,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat(),
            'context': context
        }
        
        self.error_stats['recent_errors'].append(recent_error)
        
        # Keep only last 100 errors
        if len(self.error_stats['recent_errors']) > 100:
            self.error_stats['recent_errors'] = self.error_stats['recent_errors'][-100:]
        
        # Add to error history
        self.error_stats['error_history'].append(recent_error)
        
        # Keep only last 1000 errors
        if len(self.error_stats['error_history']) > 1000:
            self.error_stats['error_history'] = self.error_stats['error_history'][-1000:]
    
    def _recover_from_dependency_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle dependency errors."""
        suggestions = [
            "Install missing dependencies using pip",
            "Check if Tesseract OCR is installed and in PATH",
            "Verify all required Python packages are installed"
        ]
        
        actions = [
            "Run: pip install -r requirements.txt",
            "Install Tesseract OCR from official website",
            "Check Python environment and dependencies"
        ]
        
        return {
            'suggestions': suggestions,
            'actions': actions,
            'severity': 'high',
            'recoverable': True
        }
    
    def _recover_from_image_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle image processing errors."""
        suggestions = [
            "Check if the image file is not corrupted",
            "Verify the image format is supported",
            "Ensure the image file has read permissions"
        ]
        
        actions = [
            "Try opening the image with a different viewer",
            "Convert the image to a supported format (PNG, JPEG, etc.)",
            "Check file permissions and disk space"
        ]
        
        return {
            'suggestions': suggestions,
            'actions': actions,
            'severity': 'medium',
            'recoverable': True
        }
    
    def _recover_from_ocr_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle OCR errors."""
        suggestions = [
            "Check if Tesseract OCR is properly installed",
            "Verify language data files are available",
            "Try different OCR configuration settings"
        ]
        
        actions = [
            "Test Tesseract installation: tesseract --version",
            "Install additional language data if needed",
            "Try different PSM or OEM settings"
        ]
        
        return {
            'suggestions': suggestions,
            'actions': actions,
            'severity': 'medium',
            'recoverable': True
        }
    
    def _recover_from_configuration_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle configuration errors."""
        suggestions = [
            "Check configuration file syntax",
            "Verify all required configuration sections are present",
            "Use default configuration as reference"
        ]
        
        actions = [
            "Validate JSON syntax of configuration file",
            "Check configuration against template",
            "Reset to default configuration"
        ]
        
        return {
            'suggestions': suggestions,
            'actions': actions,
            'severity': 'medium',
            'recoverable': True
        }
    
    def _recover_from_file_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file operation errors."""
        suggestions = [
            "Check file permissions",
            "Verify disk space availability",
            "Ensure file paths are correct"
        ]
        
        actions = [
            "Check read/write permissions",
            "Free up disk space if needed",
            "Verify file paths and network connectivity"
        ]
        
        return {
            'suggestions': suggestions,
            'actions': actions,
            'severity': 'medium',
            'recoverable': True
        }
    
    def _recover_from_processing_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general processing errors."""
        suggestions = [
            "Check system resources (memory, CPU)",
            "Verify input data integrity",
            "Try processing with simplified settings"
        ]
        
        actions = [
            "Monitor system resources during processing",
            "Validate input data format and content",
            "Reduce batch size or complexity"
        ]
        
        return {
            'suggestions': suggestions,
            'actions': actions,
            'severity': 'medium',
            'recoverable': True
        }
    
    def _recover_from_generic_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic errors."""
        suggestions = [
            "Check system logs for more details",
            "Try running the operation again",
            "Contact support if the issue persists"
        ]
        
        actions = [
            "Review detailed error logs",
            "Restart the application",
            "Check system status and dependencies"
        ]
        
        return {
            'suggestions': suggestions,
            'actions': actions,
            'severity': 'low',
            'recoverable': True
        }
    
    # Additional recovery methods for specific error types
    def _recover_from_validation_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle validation errors."""
        return {
            'suggestions': ["Check input parameters and format"],
            'actions': ["Validate input data before processing"],
            'severity': 'low',
            'recoverable': True
        }
    
    def _recover_from_timeout_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle timeout errors."""
        return {
            'suggestions': ["Increase timeout settings", "Check network connectivity"],
            'actions': ["Adjust timeout configuration", "Optimize processing speed"],
            'severity': 'medium',
            'recoverable': True
        }
    
    def _recover_from_memory_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle memory errors."""
        return {
            'suggestions': ["Increase available memory", "Reduce batch size"],
            'actions': ["Free up system memory", "Process files in smaller batches"],
            'severity': 'high',
            'recoverable': True
        }
    
    def _recover_from_conversion_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conversion errors."""
        return {
            'suggestions': ["Check input format compatibility", "Verify conversion settings"],
            'actions': ["Convert to compatible format", "Adjust conversion parameters"],
            'severity': 'medium',
            'recoverable': True
        }
    
    def _recover_from_batch_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle batch processing errors."""
        return {
            'suggestions': ["Reduce batch size", "Check individual file status"],
            'actions': ["Process files individually", "Skip problematic files"],
            'severity': 'medium',
            'recoverable': True
        }
    
    def _recover_from_quality_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle quality errors."""
        return {
            'suggestions': ["Adjust quality settings", "Preprocess images better"],
            'actions': ["Optimize image quality", "Use different preprocessing"],
            'severity': 'low',
            'recoverable': True
        }
    
    def _recover_from_preprocessing_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle preprocessing errors."""
        return {
            'suggestions': ["Disable preprocessing", "Use simpler preprocessing steps"],
            'actions': ["Skip preprocessing step", "Adjust preprocessing parameters"],
            'severity': 'low',
            'recoverable': True
        }
    
    def _recover_from_formatting_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle formatting errors."""
        return {
            'suggestions': ["Simplify formatting rules", "Use basic formatting"],
            'actions': ["Disable advanced formatting", "Adjust formatting parameters"],
            'severity': 'low',
            'recoverable': True
        }
    
    def _recover_from_metadata_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle metadata errors."""
        return {
            'suggestions': ["Skip metadata generation", "Use basic metadata"],
            'actions': ["Disable metadata features", "Simplify metadata collection"],
            'severity': 'low',
            'recoverable': True
        }
    
    def _recover_from_security_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle security errors."""
        return {
            'suggestions': ["Check file permissions", "Verify security settings"],
            'actions': ["Adjust security policies", "Use safer file paths"],
            'severity': 'high',
            'recoverable': True
        }
    
    def _recover_from_network_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle network errors."""
        return {
            'suggestions': ["Check network connectivity", "Verify remote services"],
            'actions': ["Retry operation", "Use offline mode if available"],
            'severity': 'medium',
            'recoverable': True
        }
    
    def _recover_from_system_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system errors."""
        return {
            'suggestions': ["Check system status", "Verify system resources"],
            'actions': ["Restart system services", "Free up system resources"],
            'severity': 'high',
            'recoverable': True
        }
    
    def _recover_from_unsupported_format_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unsupported format errors."""
        return {
            'suggestions': ["Convert to supported format", "Use format converter"],
            'actions': ["Convert image format", "Install additional format support"],
            'severity': 'medium',
            'recoverable': True
        }
    
    def _recover_from_permission_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle permission errors."""
        return {
            'suggestions': ["Check file permissions", "Run with elevated privileges"],
            'actions': ["Adjust file permissions", "Use appropriate user account"],
            'severity': 'medium',
            'recoverable': True
        }
    
    def _recover_from_resource_not_found_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resource not found errors."""
        return {
            'suggestions': ["Check resource path", "Verify resource availability"],
            'actions': ["Correct resource path", "Install missing resources"],
            'severity': 'medium',
            'recoverable': True
        }
    
    def _recover_from_data_corruption_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle data corruption errors."""
        return {
            'suggestions': ["Check data integrity", "Use backup data"],
            'actions': ["Repair corrupted data", "Restore from backup"],
            'severity': 'high',
            'recoverable': True
        }
    
    def _recover_from_concurrent_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle concurrent processing errors."""
        return {
            'suggestions': ["Reduce concurrency", "Use sequential processing"],
            'actions': ["Limit parallel processes", "Use single-threaded mode"],
            'severity': 'medium',
            'recoverable': True
        }
    
    def _recover_from_initialization_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialization errors."""
        return {
            'suggestions': ["Check initialization parameters", "Verify dependencies"],
            'actions': ["Reset configuration", "Reinitialize components"],
            'severity': 'high',
            'recoverable': True
        }
    
    def _recover_from_cleanup_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cleanup errors."""
        return {
            'suggestions': ["Manual cleanup may be required", "Check temporary files"],
            'actions': ["Delete temporary files", "Reset system state"],
            'severity': 'low',
            'recoverable': True
        }
    
    def _recover_from_cache_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cache errors."""
        return {
            'suggestions': ["Clear cache", "Disable caching"],
            'actions': ["Delete cache files", "Reset cache settings"],
            'severity': 'low',
            'recoverable': True
        }
    
    def _recover_from_performance_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle performance errors."""
        return {
            'suggestions': ["Optimize performance settings", "Reduce workload"],
            'actions': ["Adjust performance parameters", "Use faster algorithms"],
            'severity': 'medium',
            'recoverable': True
        }
    
    def _recover_from_encoding_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle encoding errors."""
        suggestions = [
            "Check file encoding settings",
            "Try different encoding fallbacks",
            "Convert file to UTF-8 format",
            "Use explicit encoding specification",
            "Verify file content encoding"
        ]
        
        actions = [
            "Try reading file with different encoding",
            "Convert file to UTF-8 using encoding tools",
            "Use encoding detection utilities",
            "Apply encoding fallback mechanisms",
            "Check for mixed encoding in file"
        ]
        
        return {
            'suggestions': suggestions,
            'actions': actions,
            'severity': 'medium',
            'recoverable': True
        }
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        return self.error_stats.copy()
    
    def clear_error_statistics(self) -> None:
        """Clear error statistics."""
        self.error_stats = {
            'total_errors': 0,
            'error_by_type': {},
            'error_by_module': {},
            'recent_errors': [],
            'error_history': []
        }
        self.logger.info("Error statistics cleared")
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent errors."""
        return self.error_stats['recent_errors'][-limit:]
    
    def get_error_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get error history."""
        return self.error_stats['error_history'][-limit:]