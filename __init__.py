"""
PNG to Markdown Converter Package

A comprehensive tool for converting PNG images to structured markdown documents
using Tesseract OCR with layout preservation and metadata generation.

Author: Kilo Code
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Kilo Code"
__email__ = "support@kilocode.com"
__description__ = "PNG to Markdown Converter with Tesseract OCR"

# Core modules
from core.converter import PNGToMarkdownConverter
from core.ocr_processor import TesseractOCRProcessor
from core.preprocessor import ImagePreprocessor
from core.formatter import MarkdownFormatter
from core.metadata_generator import MetadataGenerator

# Configuration and error handling
from config.manager import ConfigurationManager
from config.validator import InputValidator
from errors.handler import ErrorHandler
from errors.exceptions import (
    PNGToMarkdownError,
    DependencyError,
    ImageError,
    OCRError,
    ConfigurationError,
    FileOperationError,
    ProcessingError,
    ValidationError,
    TextProcessingError,
    LoggingError
)

# Utilities
from utils.image_utils import ImageUtils
from utils.text_utils import TextUtils
from utils.file_utils import FileUtils
from utils.logging_utils import LoggingUtils

# Package information
__all__ = [
    # Core classes
    'PNGToMarkdownConverter',
    'TesseractOCRProcessor',
    'ImagePreprocessor',
    'MarkdownFormatter',
    'MetadataGenerator',
    
    # Configuration and validation
    'ConfigurationManager',
    'InputValidator',
    
    # Error handling
    'ErrorHandler',
    'PNGToMarkdownError',
    'DependencyError',
    'ImageError',
    'OCRError',
    'ConfigurationError',
    'FileOperationError',
    'ProcessingError',
    'ValidationError',
    'TextProcessingError',
    'LoggingError',
    
    # Utilities
    'ImageUtils',
    'TextUtils',
    'FileUtils',
    'LoggingUtils',
    
    # Version info
    '__version__',
    '__author__',
    '__email__',
    '__description__'
]

# Initialize package
def initialize(config_path: str = None) -> PNGToMarkdownConverter:
    """
    Initialize the PNG to Markdown converter with optional configuration.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        PNGToMarkdownConverter: Initialized converter instance
    """
    try:
        # Load configuration
        config_manager = ConfigurationManager()
        if config_path:
            config = config_manager.load_config(config_path)
        else:
            config = config_manager.get_default_config()
        
        # Initialize converter
        converter = PNGToMarkdownConverter(config)
        
        return converter
        
    except Exception as e:
        raise PNGToMarkdownError(f"Failed to initialize converter: {e}")

# Quick start function
def convert_png_to_markdown(input_path: str, output_path: str, config_path: str = None) -> bool:
    """
    Quick function to convert PNG to markdown.
    
    Args:
        input_path: Path to input PNG file
        output_path: Path to output markdown file
        config_path: Optional path to configuration file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        converter = initialize(config_path)
        return converter.convert_file(input_path, output_path)
        
    except Exception as e:
        print(f"Error converting PNG to markdown: {e}")
        return False