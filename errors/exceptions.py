"""
Custom Exceptions Module

This module defines custom exception classes for the PNG to Markdown converter.
It provides a comprehensive hierarchy of exceptions for different error scenarios.

Author: Kilo Code
Version: 1.0.0
"""

from typing import Dict, Any, Optional, List


class PNGToMarkdownError(Exception):
    """Base exception class for PNG to Markdown converter."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize base exception.
        
        Args:
            message: Error message
            context: Context information
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
    
    def __str__(self) -> str:
        """String representation of the exception."""
        if self.context:
            return f"{self.message} (Context: {self.context})"
        return self.message


class DependencyError(PNGToMarkdownError):
    """Missing or invalid dependencies."""
    
    def __init__(self, message: str, dependency: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize dependency error.
        
        Args:
            message: Error message
            dependency: Name of the missing dependency
            context: Context information
        """
        if dependency:
            message = f"{message}: {dependency}"
        super().__init__(message, context)
        self.dependency = dependency


class ImageError(PNGToMarkdownError):
    """Image processing errors."""
    
    def __init__(self, message: str, image_path: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize image error.
        
        Args:
            message: Error message
            image_path: Path to the problematic image
            context: Context information
        """
        if image_path:
            message = f"{message}: {image_path}"
        super().__init__(message, context)
        self.image_path = image_path


class OCRError(PNGToMarkdownError):
    """OCR processing errors."""
    
    def __init__(self, message: str, ocr_engine: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize OCR error.
        
        Args:
            message: Error message
            ocr_engine: Name of the OCR engine
            context: Context information
        """
        if ocr_engine:
            message = f"{message} ({ocr_engine})"
        super().__init__(message, context)
        self.ocr_engine = ocr_engine


class ConfigurationError(PNGToMarkdownError):
    """Configuration errors."""
    
    def __init__(self, message: str, config_path: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            config_path: Path to the problematic configuration
            context: Context information
        """
        if config_path:
            message = f"{message}: {config_path}"
        super().__init__(message, context)
        self.config_path = config_path


class FileOperationError(PNGToMarkdownError):
    """File operation errors."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, operation: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize file operation error.
        
        Args:
            message: Error message
            file_path: Path to the problematic file
            operation: File operation that failed
            context: Context information
        """
        if file_path:
            message = f"{message}: {file_path}"
        if operation:
            message = f"{message} ({operation})"
        super().__init__(message, context)
        self.file_path = file_path
        self.operation = operation


class ProcessingError(PNGToMarkdownError):
    """General processing errors."""
    
    def __init__(self, message: str, step: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize processing error.
        
        Args:
            message: Error message
            step: Processing step where error occurred
            context: Context information
        """
        if step:
            message = f"{message} (Step: {step})"
        super().__init__(message, context)
        self.step = step


class ValidationError(PNGToMarkdownError):
    """Validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Field that failed validation
            value: Invalid value
            context: Context information
        """
        if field:
            message = f"{message} (Field: {field})"
        if value is not None:
            message = f"{message} (Value: {value})"
        super().__init__(message, context)
        self.field = field
        self.value = value


class TimeoutError(PNGToMarkdownError):
    """Timeout errors."""
    
    def __init__(self, message: str, operation: Optional[str] = None, timeout_seconds: Optional[int] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize timeout error.
        
        Args:
            message: Error message
            operation: Operation that timed out
            timeout_seconds: Timeout duration in seconds
            context: Context information
        """
        if operation:
            message = f"{message} (Operation: {operation})"
        if timeout_seconds:
            message = f"{message} (Timeout: {timeout_seconds}s)"
        super().__init__(message, context)
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class MemoryError(PNGToMarkdownError):
    """Memory errors."""
    
    def __init__(self, message: str, required_memory: Optional[int] = None, available_memory: Optional[int] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize memory error.
        
        Args:
            message: Error message
            required_memory: Required memory in bytes
            available_memory: Available memory in bytes
            context: Context information
        """
        if required_memory and available_memory:
            message = f"{message} (Required: {required_memory} bytes, Available: {available_memory} bytes)"
        super().__init__(message, context)
        self.required_memory = required_memory
        self.available_memory = available_memory


class ConversionError(PNGToMarkdownError):
    """Conversion errors."""
    
    def __init__(self, message: str, input_format: Optional[str] = None, output_format: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize conversion error.
        
        Args:
            message: Error message
            input_format: Input format
            output_format: Output format
            context: Context information
        """
        if input_format and output_format:
            message = f"{message} ({input_format} -> {output_format})"
        super().__init__(message, context)
        self.input_format = input_format
        self.output_format = output_format


class BatchProcessingError(PNGToMarkdownError):
    """Batch processing errors."""
    
    def __init__(self, message: str, batch_size: Optional[int] = None, processed_count: Optional[int] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize batch processing error.
        
        Args:
            message: Error message
            batch_size: Batch size
            processed_count: Number of processed items
            context: Context information
        """
        if batch_size and processed_count:
            message = f"{message} (Batch: {batch_size}, Processed: {processed_count})"
        super().__init__(message, context)
        self.batch_size = batch_size
        self.processed_count = processed_count


class QualityError(PNGToMarkdownError):
    """Quality-related errors."""
    
    def __init__(self, message: str, quality_score: Optional[float] = None, threshold: Optional[float] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize quality error.
        
        Args:
            message: Error message
            quality_score: Quality score
            threshold: Required threshold
            context: Context information
        """
        if quality_score is not None and threshold is not None:
            message = f"{message} (Score: {quality_score}, Threshold: {threshold})"
        super().__init__(message, context)
        self.quality_score = quality_score
        self.threshold = threshold


class PreprocessingError(PNGToMarkdownError):
    """Preprocessing errors."""
    
    def __init__(self, message: str, preprocessing_step: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize preprocessing error.
        
        Args:
            message: Error message
            preprocessing_step: Preprocessing step that failed
            context: Context information
        """
        if preprocessing_step:
            message = f"{message} (Step: {preprocessing_step})"
        super().__init__(message, context)
        self.preprocessing_step = preprocessing_step


class FormattingError(PNGToMarkdownError):
    """Formatting errors."""
    
    def __init__(self, message: str, format_type: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize formatting error.
        
        Args:
            message: Error message
            format_type: Type of formatting
            context: Context information
        """
        if format_type:
            message = f"{message} (Format: {format_type})"
        super().__init__(message, context)
        self.format_type = format_type


class MetadataError(PNGToMarkdownError):
    """Metadata errors."""
    
    def __init__(self, message: str, metadata_field: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize metadata error.
        
        Args:
            message: Error message
            metadata_field: Metadata field that failed
            context: Context information
        """
        if metadata_field:
            message = f"{message} (Field: {metadata_field})"
        super().__init__(message, context)
        self.metadata_field = metadata_field


class SecurityError(PNGToMarkdownError):
    """Security-related errors."""
    
    def __init__(self, message: str, security_check: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize security error.
        
        Args:
            message: Error message
            security_check: Security check that failed
            context: Context information
        """
        if security_check:
            message = f"{message} (Check: {security_check})"
        super().__init__(message, context)
        self.security_check = security_check


class NetworkError(PNGToMarkdownError):
    """Network-related errors."""
    
    def __init__(self, message: str, endpoint: Optional[str] = None, status_code: Optional[int] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize network error.
        
        Args:
            message: Error message
            endpoint: Network endpoint
            status_code: HTTP status code
            context: Context information
        """
        if endpoint:
            message = f"{message} (Endpoint: {endpoint})"
        if status_code:
            message = f"{message} (Status: {status_code})"
        super().__init__(message, context)
        self.endpoint = endpoint
        self.status_code = status_code


class SystemError(PNGToMarkdownError):
    """System-related errors."""
    
    def __init__(self, message: str, system_component: Optional[str] = None, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize system error.
        
        Args:
            message: Error message
            system_component: System component
            error_code: System error code
            context: Context information
        """
        if system_component:
            message = f"{message} (Component: {system_component})"
        if error_code:
            message = f"{message} (Code: {error_code})"
        super().__init__(message, context)
        self.system_component = system_component
        self.error_code = error_code


class UnsupportedFormatError(PNGToMarkdownError):
    """Unsupported format errors."""
    
    def __init__(self, message: str, format_name: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize unsupported format error.
        
        Args:
            message: Error message
            format_name: Unsupported format name
            context: Context information
        """
        if format_name:
            message = f"{message}: {format_name}"
        super().__init__(message, context)
        self.format_name = format_name


class PermissionError(PNGToMarkdownError):
    """Permission errors."""
    
    def __init__(self, message: str, resource: Optional[str] = None, permission: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize permission error.
        
        Args:
            message: Error message
            resource: Resource that requires permission
            permission: Required permission
            context: Context information
        """
        if resource:
            message = f"{message} (Resource: {resource})"
        if permission:
            message = f"{message} (Permission: {permission})"
        super().__init__(message, context)
        self.resource = resource
        self.permission = permission


class ResourceNotFoundError(PNGToMarkdownError):
    """Resource not found errors."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_name: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize resource not found error.
        
        Args:
            message: Error message
            resource_type: Type of resource
            resource_name: Name of resource
            context: Context information
        """
        if resource_type and resource_name:
            message = f"{message} ({resource_type}: {resource_name})"
        super().__init__(message, context)
        self.resource_type = resource_type
        self.resource_name = resource_name


class DataCorruptionError(PNGToMarkdownError):
    """Data corruption errors."""
    
    def __init__(self, message: str, data_type: Optional[str] = None, corruption_type: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize data corruption error.
        
        Args:
            message: Error message
            data_type: Type of corrupted data
            corruption_type: Type of corruption
            context: Context information
        """
        if data_type:
            message = f"{message} (Data: {data_type})"
        if corruption_type:
            message = f"{message} (Corruption: {corruption_type})"
        super().__init__(message, context)
        self.data_type = data_type
        self.corruption_type = corruption_type


class ConcurrentProcessingError(PNGToMarkdownError):
    """Concurrent processing errors."""
    
    def __init__(self, message: str, concurrent_limit: Optional[int] = None, active_processes: Optional[int] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize concurrent processing error.
        
        Args:
            message: Error message
            concurrent_limit: Concurrent process limit
            active_processes: Number of active processes
            context: Context information
        """
        if concurrent_limit and active_processes:
            message = f"{message} (Limit: {concurrent_limit}, Active: {active_processes})"
        super().__init__(message, context)
        self.concurrent_limit = concurrent_limit
        self.active_processes = active_processes


class InitializationError(PNGToMarkdownError):
    """Initialization errors."""
    
    def __init__(self, message: str, component: Optional[str] = None, initialization_step: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize initialization error.
        
        Args:
            message: Error message
            component: Component that failed to initialize
            initialization_step: Initialization step that failed
            context: Context information
        """
        if component:
            message = f"{message} (Component: {component})"
        if initialization_step:
            message = f"{message} (Step: {initialization_step})"
        super().__init__(message, context)
        self.component = component
        self.initialization_step = initialization_step


class CleanupError(PNGToMarkdownError):
    """Cleanup errors."""
    
    def __init__(self, message: str, cleanup_type: Optional[str] = None, resource: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize cleanup error.
        
        Args:
            message: Error message
            cleanup_type: Type of cleanup operation
            resource: Resource being cleaned up
            context: Context information
        """
        if cleanup_type:
            message = f"{message} (Type: {cleanup_type})"
        if resource:
            message = f"{message} (Resource: {resource})"
        super().__init__(message, context)
        self.cleanup_type = cleanup_type
        self.resource = resource


class CacheError(PNGToMarkdownError):
    """Cache errors."""
    
    def __init__(self, message: str, cache_operation: Optional[str] = None, cache_key: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize cache error.
        
        Args:
            message: Error message
            cache_operation: Cache operation that failed
            cache_key: Cache key involved
            context: Context information
        """
        if cache_operation:
            message = f"{message} (Operation: {cache_operation})"
        if cache_key:
            message = f"{message} (Key: {cache_key})"
        super().__init__(message, context)
        self.cache_operation = cache_operation
        self.cache_key = cache_key


class PerformanceError(PNGToMarkdownError):
    """Performance-related errors."""
    
    def __init__(self, message: str, performance_metric: Optional[str] = None, actual_value: Optional[float] = None, expected_value: Optional[float] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize performance error.
        
        Args:
            message: Error message
            performance_metric: Performance metric
            actual_value: Actual performance value
            expected_value: Expected performance value
            context: Context information
        """
        if performance_metric:
            message = f"{message} (Metric: {performance_metric})"
        if actual_value is not None and expected_value is not None:
            message = f"{message} (Actual: {actual_value}, Expected: {expected_value})"
        super().__init__(message, context)
        self.performance_metric = performance_metric
        self.actual_value = actual_value
        self.expected_value = expected_value


class EncodingError(PNGToMarkdownError):
    """Encoding-related errors."""
    
    def __init__(self, message: str, encoding: Optional[str] = None, file_path: Optional[str] = None,
                 operation: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize encoding error.
        
        Args:
            message: Error message
            encoding: Encoding that caused the error
            file_path: Path to the problematic file
            operation: Operation that failed due to encoding
            context: Context information
        """
        if encoding:
            message = f"{message} (Encoding: {encoding})"
        if file_path:
            message = f"{message} (File: {file_path})"
        if operation:
            message = f"{message} (Operation: {operation})"
        super().__init__(message, context)
        self.encoding = encoding
        self.file_path = file_path
        self.operation = operation


# Additional utility functions for exception handling

def create_error_response(exception: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a standardized error response from an exception.
    
    Args:
        exception: The exception that occurred
        context: Additional context information
        
    Returns:
        Dict: Standardized error response
    """
    error_response = {
        'error_type': type(exception).__name__,
        'error_message': str(exception),
        'timestamp': None,  # Will be set by caller
        'context': context or {},
        'recoverable': False,
        'severity': 'medium'
    }
    
    # Add specific fields based on exception type
    if isinstance(exception, DependencyError):
        error_response['dependency'] = exception.dependency
        error_response['recoverable'] = True
        error_response['severity'] = 'high'
    elif isinstance(exception, ImageError):
        error_response['image_path'] = exception.image_path
        error_response['recoverable'] = True
        error_response['severity'] = 'medium'
    elif isinstance(exception, OCRError):
        error_response['ocr_engine'] = exception.ocr_engine
        error_response['recoverable'] = True
        error_response['severity'] = 'medium'
    elif isinstance(exception, ConfigurationError):
        error_response['config_path'] = exception.config_path
        error_response['recoverable'] = True
        error_response['severity'] = 'medium'
    elif isinstance(exception, FileOperationError):
        error_response['file_path'] = exception.file_path
        error_response['operation'] = exception.operation
        error_response['recoverable'] = True
        error_response['severity'] = 'medium'
    elif isinstance(exception, ProcessingError):
        error_response['step'] = exception.step
        error_response['recoverable'] = True
        error_response['severity'] = 'medium'
    elif isinstance(exception, ValidationError):
        error_response['field'] = exception.field
        error_response['value'] = exception.value
        error_response['recoverable'] = True
        error_response['severity'] = 'low'
    elif isinstance(exception, TimeoutError):
        error_response['operation'] = exception.operation
        error_response['timeout_seconds'] = exception.timeout_seconds
        error_response['recoverable'] = True
        error_response['severity'] = 'medium'
    elif isinstance(exception, MemoryError):
        error_response['required_memory'] = exception.required_memory
        error_response['available_memory'] = exception.available_memory
        error_response['recoverable'] = True
        error_response['severity'] = 'high'
    elif isinstance(exception, ConversionError):
        error_response['input_format'] = exception.input_format
        error_response['output_format'] = exception.output_format
        error_response['recoverable'] = True
        error_response['severity'] = 'medium'
    elif isinstance(exception, BatchProcessingError):
        error_response['batch_size'] = exception.batch_size
        error_response['processed_count'] = exception.processed_count
        error_response['recoverable'] = True
        error_response['severity'] = 'medium'
    elif isinstance(exception, QualityError):
        error_response['quality_score'] = exception.quality_score
        error_response['threshold'] = exception.threshold
        error_response['recoverable'] = True
        error_response['severity'] = 'low'
    elif isinstance(exception, PreprocessingError):
        error_response['preprocessing_step'] = exception.preprocessing_step
        error_response['recoverable'] = True
        error_response['severity'] = 'low'
    elif isinstance(exception, FormattingError):
        error_response['format_type'] = exception.format_type
        error_response['recoverable'] = True
        error_response['severity'] = 'low'
    elif isinstance(exception, MetadataError):
        error_response['metadata_field'] = exception.metadata_field
        error_response['recoverable'] = True
        error_response['severity'] = 'low'
    elif isinstance(exception, SecurityError):
        error_response['security_check'] = exception.security_check
        error_response['recoverable'] = True
        error_response['severity'] = 'high'
    elif isinstance(exception, NetworkError):
        error_response['endpoint'] = exception.endpoint
        error_response['status_code'] = exception.status_code
        error_response['recoverable'] = True
        error_response['severity'] = 'medium'
    elif isinstance(exception, SystemError):
        error_response['system_component'] = exception.system_component
        error_response['error_code'] = exception.error_code
        error_response['recoverable'] = True
        error_response['severity'] = 'high'
    elif isinstance(exception, UnsupportedFormatError):
        error_response['format_name'] = exception.format_name
        error_response['recoverable'] = True
        error_response['severity'] = 'medium'
    elif isinstance(exception, PermissionError):
        error_response['resource'] = exception.resource
        error_response['permission'] = exception.permission
        error_response['recoverable'] = True
        error_response['severity'] = 'medium'
    elif isinstance(exception, ResourceNotFoundError):
        error_response['resource_type'] = exception.resource_type
        error_response['resource_name'] = exception.resource_name
        error_response['recoverable'] = True
        error_response['severity'] = 'medium'
    elif isinstance(exception, DataCorruptionError):
        error_response['data_type'] = exception.data_type
        error_response['corruption_type'] = exception.corruption_type
        error_response['recoverable'] = True
        error_response['severity'] = 'high'
    elif isinstance(exception, ConcurrentProcessingError):
        error_response['concurrent_limit'] = exception.concurrent_limit
        error_response['active_processes'] = exception.active_processes
        error_response['recoverable'] = True
        error_response['severity'] = 'medium'
    elif isinstance(exception, InitializationError):
        error_response['component'] = exception.component
        error_response['initialization_step'] = exception.initialization_step
        error_response['recoverable'] = True
        error_response['severity'] = 'high'
    elif isinstance(exception, CleanupError):
        error_response['cleanup_type'] = exception.cleanup_type
        error_response['resource'] = exception.resource
        error_response['recoverable'] = True
        error_response['severity'] = 'low'
    elif isinstance(exception, CacheError):
        error_response['cache_operation'] = exception.cache_operation
        error_response['cache_key'] = exception.cache_key
        error_response['recoverable'] = True
        error_response['severity'] = 'low'
    elif isinstance(exception, PerformanceError):
        error_response['performance_metric'] = exception.performance_metric
        error_response['actual_value'] = exception.actual_value
        error_response['expected_value'] = exception.expected_value
        error_response['recoverable'] = True
        error_response['severity'] = 'medium'
    elif isinstance(exception, EncodingError):
        error_response['encoding'] = exception.encoding
        error_response['file_path'] = exception.file_path
        error_response['operation'] = exception.operation
        error_response['recoverable'] = True
        error_response['severity'] = 'medium'
    
    return error_response


def is_recoverable_error(exception: Exception) -> bool:
    """
    Check if an error is recoverable.
    
    Args:
        exception: The exception to check
        
    Returns:
        bool: True if the error is recoverable, False otherwise
    """
    recoverable_types = (
        DependencyError, ImageError, OCRError, ConfigurationError,
        FileOperationError, ProcessingError, ValidationError, TimeoutError,
        MemoryError, ConversionError, BatchProcessingError, QualityError,
        PreprocessingError, FormattingError, MetadataError, SecurityError,
        NetworkError, SystemError, UnsupportedFormatError, PermissionError,
        ResourceNotFoundError, DataCorruptionError, ConcurrentProcessingError,
        InitializationError, CleanupError, CacheError, PerformanceError,
        EncodingError
    )
    
    return isinstance(exception, recoverable_types)


def get_error_severity(exception: Exception) -> str:
    """
    Get the severity level of an error.
    
    Args:
        exception: The exception to evaluate
        
    Returns:
        str: Severity level ('low', 'medium', 'high', 'critical')
    """
    if isinstance(exception, (DependencyError, SecurityError, SystemError, DataCorruptionError, InitializationError)):
        return 'high'
    elif isinstance(exception, (MemoryError, ConcurrentProcessingError)):
        return 'critical'
    elif isinstance(exception, (ImageError, OCRError, ConfigurationError, FileOperationError,
                              ProcessingError, TimeoutError, ConversionError, BatchProcessingError,
                              NetworkError, UnsupportedFormatError, PermissionError, ResourceNotFoundError,
                              EncodingError)):
        return 'medium'
    else:
        return 'low'


def get_error_recovery_suggestions(exception: Exception) -> List[str]:
    """
    Get recovery suggestions for an error.
    
    Args:
        exception: The exception to get suggestions for
        
    Returns:
        List[str]: List of recovery suggestions
    """
    suggestions = []
    
    if isinstance(exception, DependencyError):
        suggestions = [
            "Install missing dependencies using pip",
            "Check if required software is installed and in PATH",
            "Verify all required Python packages are installed"
        ]
    elif isinstance(exception, ImageError):
        suggestions = [
            "Check if the image file is not corrupted",
            "Verify the image format is supported",
            "Ensure the image file has read permissions",
            "Try converting the image to a different format"
        ]
    elif isinstance(exception, OCRError):
        suggestions = [
            "Check if Tesseract OCR is properly installed",
            "Verify language data files are available",
            "Try different OCR configuration settings",
            "Test Tesseract installation manually"
        ]
    elif isinstance(exception, ConfigurationError):
        suggestions = [
            "Check configuration file syntax",
            "Verify all required configuration sections are present",
            "Use default configuration as reference",
            "Validate configuration against schema"
        ]
    elif isinstance(exception, FileOperationError):
        suggestions = [
            "Check file permissions",
            "Verify disk space availability",
            "Ensure file paths are correct",
            "Check network connectivity for remote files"
        ]
    elif isinstance(exception, ProcessingError):
        suggestions = [
            "Check system resources (memory, CPU)",
            "Verify input data integrity",
            "Try processing with simplified settings",
            "Reduce batch size or complexity"
        ]
    elif isinstance(exception, ValidationError):
        suggestions = [
            "Check input parameters and format",
            "Validate input data before processing",
            "Refer to documentation for correct format"
        ]
    elif isinstance(exception, TimeoutError):
        suggestions = [
            "Increase timeout settings",
            "Check network connectivity",
            "Optimize processing speed",
            "Reduce workload per operation"
        ]
    elif isinstance(exception, MemoryError):
        suggestions = [
            "Increase available memory",
            "Reduce batch size",
            "Process files in smaller chunks",
            "Free up system memory"
        ]
    elif isinstance(exception, ConversionError):
        suggestions = [
            "Check input format compatibility",
            "Verify conversion settings",
            "Convert to compatible format first",
            "Use different conversion library"
        ]
    elif isinstance(exception, BatchProcessingError):
        suggestions = [
            "Reduce batch size",
            "Check individual file status",
            "Process files individually",
            "Skip problematic files"
        ]
    elif isinstance(exception, QualityError):
        suggestions = [
            "Adjust quality settings",
            "Preprocess images better",
            "Use different OCR parameters",
            "Accept lower quality if necessary"
        ]
    elif isinstance(exception, PreprocessingError):
        suggestions = [
            "Disable preprocessing",
            "Use simpler preprocessing steps",
            "Adjust preprocessing parameters",
            "Skip problematic preprocessing steps"
        ]
    elif isinstance(exception, FormattingError):
        suggestions = [
            "Simplify formatting rules",
            "Use basic formatting",
            "Disable advanced formatting",
            "Adjust formatting parameters"
        ]
    elif isinstance(exception, MetadataError):
        suggestions = [
            "Skip metadata generation",
            "Use basic metadata",
            "Disable metadata features",
            "Simplify metadata collection"
        ]
    elif isinstance(exception, SecurityError):
        suggestions = [
            "Check file permissions",
            "Verify security settings",
            "Adjust security policies",
            "Use safer file paths"
        ]
    elif isinstance(exception, NetworkError):
        suggestions = [
            "Check network connectivity",
            "Verify remote services",
            "Retry operation",
            "Use offline mode if available"
        ]
    elif isinstance(exception, SystemError):
        suggestions = [
            "Check system status",
            "Verify system resources",
            "Restart system services",
            "Free up system resources"
        ]
    elif isinstance(exception, UnsupportedFormatError):
        suggestions = [
            "Convert to supported format",
            "Use format converter",
            "Install additional format support",
            "Use different file type"
        ]
    elif isinstance(exception, PermissionError):
        suggestions = [
            "Check file permissions",
            "Run with elevated privileges",
            "Adjust file permissions",
            "Use appropriate user account"
        ]
    elif isinstance(exception, ResourceNotFoundError):
        suggestions = [
            "Check resource path",
            "Verify resource availability",
            "Correct resource path",
            "Install missing resources"
        ]
    elif isinstance(exception, DataCorruptionError):
        suggestions = [
            "Check data integrity",
            "Use backup data",
            "Repair corrupted data",
            "Restore from backup"
        ]
    elif isinstance(exception, ConcurrentProcessingError):
        suggestions = [
            "Reduce concurrency",
            "Use sequential processing",
            "Limit parallel processes",
            "Use single-threaded mode"
        ]
    elif isinstance(exception, InitializationError):
        suggestions = [
            "Check initialization parameters",
            "Verify dependencies",
            "Reset configuration",
            "Reinitialize components"
        ]
    elif isinstance(exception, CleanupError):
        suggestions = [
            "Manual cleanup may be required",
            "Check temporary files",
            "Delete temporary files",
            "Reset system state"
        ]
    elif isinstance(exception, CacheError):
        suggestions = [
            "Clear cache",
            "Disable caching",
            "Delete cache files",
            "Reset cache settings"
        ]
    elif isinstance(exception, PerformanceError):
        suggestions = [
            "Optimize performance settings",
            "Reduce workload",
            "Adjust performance parameters",
            "Use faster algorithms"
        ]
    elif isinstance(exception, EncodingError):
        suggestions = [
            "Check file encoding settings",
            "Try different encoding fallbacks",
            "Convert file to UTF-8 format",
            "Use explicit encoding specification",
            "Verify file content encoding"
        ]
    else:
        suggestions = [
            "Check system logs for more details",
            "Try running the operation again",
            "Contact support if the issue persists"
        ]
    
    return suggestions