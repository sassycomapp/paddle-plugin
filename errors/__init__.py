"""
Errors Module Package

This package contains error handling components for the PNG to Markdown converter.
"""

from .handler import ErrorHandler
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
    PerformanceError
)

__all__ = [
    'ErrorHandler',
    'PNGToMarkdownError',
    'DependencyError',
    'ImageError',
    'OCRError',
    'ConfigurationError',
    'FileOperationError',
    'ProcessingError',
    'ValidationError',
    'TimeoutError',
    'MemoryError',
    'ConversionError',
    'BatchProcessingError',
    'QualityError',
    'PreprocessingError',
    'FormattingError',
    'MetadataError',
    'SecurityError',
    'NetworkError',
    'SystemError',
    'UnsupportedFormatError',
    'PermissionError',
    'ResourceNotFoundError',
    'DataCorruptionError',
    'ConcurrentProcessingError',
    'InitializationError',
    'CleanupError',
    'CacheError',
    'PerformanceError'
]