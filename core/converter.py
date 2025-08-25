"""
PNG to Markdown Converter - Main Converter Class

This module provides the main converter class that orchestrates the entire PNG to Markdown conversion process.
It coordinates all components and provides both CLI interface and programmatic API.

Author: Kilo Code
Version: 1.0.0
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import concurrent.futures
import time

# Local imports
from core.ocr_processor import TesseractOCRProcessor
from core.preprocessor import ImagePreprocessor
from core.formatter import MarkdownFormatter
from core.metadata_generator import MetadataGenerator
from config.manager import ConfigurationManager
from config.validator import InputValidator
from errors.handler import ErrorHandler
from errors.exceptions import PNGToMarkdownError, ProcessingError, FileOperationError


class PNGToMarkdownConverter:
    """
    Main entry point for PNG to Markdown conversion.
    Provides both CLI interface and programmatic API.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the converter with configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler()
        
        # Initialize configuration
        if config:
            self.config_manager = ConfigurationManager()
            self.config_manager._merge_config(config)
        else:
            self.config_manager = ConfigurationManager()
        
        # Initialize components
        self.ocr_processor = TesseractOCRProcessor(
            tesseract_path=self.config_manager.get_config('tesseract.path'),
            config=self.config_manager.get_tesseract_config()
        )
        
        self.preprocessor = ImagePreprocessor(
            config=self.config_manager.get_preprocessing_config()
        )
        
        self.formatter = MarkdownFormatter(
            config=self.config_manager.get_formatting_config()
        )
        
        self.metadata_generator = MetadataGenerator(
            config=self.config_manager.get_metadata_config()
        )
        
        self.validator = InputValidator(
            config=self.config_manager.get_validation_config()
        )
        
        # Initialize statistics
        self.statistics = {
            'total_files_processed': 0,
            'successful_files': 0,
            'failed_files': 0,
            'total_processing_time': 0,
            'average_processing_time': 0,
            'start_time': None,
            'end_time': None
        }
    
    def convert_file(self, input_path: str, output_path: str, **kwargs) -> bool:
        """
        Convert a single PNG file to markdown.
        
        Args:
            input_path: Path to input PNG file
            output_path: Path to output markdown file
            **kwargs: Additional configuration options
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info(f"Starting conversion: {input_path} -> {output_path}")
            
            # Update statistics
            if self.statistics['start_time'] is None:
                self.statistics['start_time'] = datetime.now()
            
            # Validate input
            validation_result = self.validator.validate_image_file(input_path)
            if not validation_result['valid']:
                error_msg = f"Input validation failed: {', '.join(validation_result['errors'])}"
                self.error_handler.handle_image_error(Exception(error_msg), input_path)
                return False
            
            # Sanitize output path
            output_path = self.validator.sanitize_output_path(output_path)
            
            # Process the file
            start_time = time.time()
            
            # Apply preprocessing if enabled
            processed_image = input_path
            if kwargs.get('preprocess', self.config_manager.get_config('preprocessing.enabled')):
                processed_image = self.preprocessor.preprocess_image(input_path)
            
            # Extract text with OCR
            ocr_results = self.ocr_processor.extract_text_with_metadata(processed_image)
            
            # Apply confidence threshold if specified
            confidence_threshold = kwargs.get('confidence_threshold', self.config_manager.get_config('formatting.confidence_threshold'))
            if confidence_threshold > 0:
                ocr_results = self._apply_confidence_threshold(ocr_results, confidence_threshold)
            
            # Format results to markdown
            markdown_content = self.formatter.format_ocr_results(ocr_results)
            
            # Generate metadata if enabled
            if kwargs.get('include_metadata', self.config_manager.get_config('formatting.include_metadata')):
                metadata = self.metadata_generator.generate_processing_metadata(input_path, ocr_results)
                markdown_content += f"\n\n## Metadata\n\n{json.dumps(metadata, indent=2, ensure_ascii=False)}"
            
            # Generate statistics if enabled
            if kwargs.get('include_statistics', self.config_manager.get_config('formatting.include_statistics')):
                statistics = self.metadata_generator.calculate_quality_metrics(ocr_results)
                markdown_content += f"\n\n## Statistics\n\n{json.dumps(statistics, indent=2, ensure_ascii=False)}"
            
            # Write output file
            self._write_output_file(output_path, markdown_content)
            
            # Update statistics
            processing_time = time.time() - start_time
            self.statistics['total_files_processed'] += 1
            self.statistics['successful_files'] += 1
            self.statistics['total_processing_time'] += processing_time
            self.statistics['average_processing_time'] = self.statistics['total_processing_time'] / self.statistics['total_files_processed']
            
            self.logger.info(f"Successfully converted: {input_path} -> {output_path}")
            return True
            
        except Exception as e:
            # Update statistics
            self.statistics['total_files_processed'] += 1
            self.statistics['failed_files'] += 1
            
            # Handle error
            error_msg = f"Failed to convert {input_path}: {e}"
            self.error_handler.handle_processing_error(Exception(error_msg), 'file_conversion')
            self.logger.error(error_msg)
            return False
    
    def convert_directory(self, input_dir: str, output_dir: str, **kwargs) -> Dict[str, Any]:
        """
        Convert all PNG files in a directory to markdown.
        
        Args:
            input_dir: Directory containing PNG files
            output_dir: Directory to save markdown files
            **kwargs: Additional configuration options
            
        Returns:
            Dict: Conversion results summary
        """
        try:
            self.logger.info(f"Starting directory conversion: {input_dir} -> {output_dir}")
            
            # Update statistics
            if self.statistics['start_time'] is None:
                self.statistics['start_time'] = datetime.now()
            
            # Validate input directory
            if not os.path.exists(input_dir):
                raise FileOperationError(f"Input directory does not exist: {input_dir}", input_dir, 'read')
            
            # Validate and create output directory
            output_dir = self.validator.sanitize_output_path(output_dir)
            
            # Find all PNG files in input directory
            png_files = self._find_png_files(input_dir)
            
            if not png_files:
                self.logger.warning(f"No PNG files found in directory: {input_dir}")
                return {
                    'success': False,
                    'error': 'No PNG files found in directory',
                    'summary': {
                        'total_files': 0,
                        'successful_files': 0,
                        'failed_files': 0,
                        'success_rate': 0
                    }
                }
            
            # Process files
            results = self._process_batch(png_files, output_dir, **kwargs)
            
            # Update end time
            self.statistics['end_time'] = datetime.now()
            
            # Generate summary
            summary = self._generate_summary(results)
            
            self.logger.info(f"Directory conversion completed: {summary}")
            return {
                'success': True,
                'results': results,
                'summary': summary
            }
            
        except Exception as e:
            error_msg = f"Failed to convert directory {input_dir}: {e}"
            self.error_handler.handle_processing_error(Exception(error_msg), 'directory_conversion')
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'summary': {
                    'total_files': 0,
                    'successful_files': 0,
                    'failed_files': 0,
                    'success_rate': 0
                }
            }
    
    def _find_png_files(self, directory: str) -> List[str]:
        """Find all PNG files in a directory."""
        png_files = []
        supported_formats = self.config_manager.get_config('validation.supported_formats', [])
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in supported_formats:
                    file_path = os.path.join(root, file)
                    png_files.append(file_path)
        
        return png_files
    
    def _process_batch(self, files: List[str], output_dir: str, **kwargs) -> Dict[str, Any]:
        """Process files in batch."""
        results = {}
        batch_size = kwargs.get('batch_size', self.config_manager.get_config('batch.size', 10))
        timeout = kwargs.get('timeout', self.config_manager.get_config('batch.timeout', 30))
        
        # Process files in batches
        for i in range(0, len(files), batch_size):
            batch_files = files[i:i + batch_size]
            batch_results = self._process_batch_files(batch_files, output_dir, **kwargs)
            results.update(batch_results)
        
        return results
    
    def _process_batch_files(self, files: List[str], output_dir: str, **kwargs) -> Dict[str, Any]:
        """Process a batch of files."""
        results = {}
        
        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_file = {}
            
            for file_path in files:
                # Generate output filename
                output_filename = self._generate_output_filename(file_path, kwargs.get('filename_pattern'))
                output_path = os.path.join(output_dir, output_filename)
                
                # Submit conversion task
                future = executor.submit(self.convert_file, file_path, output_path, **kwargs)
                future_to_file[future] = file_path
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_file, timeout=timeout):
                file_path = future_to_file[future]
                try:
                    success = future.result()
                    results[file_path] = {
                        'success': success,
                        'output_path': os.path.join(output_dir, self._generate_output_filename(file_path, kwargs.get('filename_pattern'))),
                        'error': None
                    }
                except Exception as e:
                    results[file_path] = {
                        'success': False,
                        'output_path': None,
                        'error': str(e)
                    }
        
        return results
    
    def _generate_output_filename(self, input_path: str, pattern: Optional[str] = None) -> str:
        """Generate output filename based on input and pattern."""
        if pattern is None:
            pattern = self.config_manager.get_config('output.filename_pattern', '{original_name}_OCR.md')
        
        # Extract filename without extension
        filename = os.path.basename(input_path)
        name_without_ext = os.path.splitext(filename)[0]
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Format filename
        output_filename = pattern.format(
            original_name=name_without_ext,
            timestamp=timestamp,
            filename=filename
        )
        
        # Ensure it has .md extension
        if not output_filename.endswith('.md'):
            output_filename += '.md'
        
        return output_filename
    
    def _apply_confidence_threshold(self, ocr_results: Dict[str, Any], threshold: int) -> Dict[str, Any]:
        """Apply confidence threshold to OCR results."""
        if 'text_blocks' in ocr_results:
            filtered_blocks = []
            for block in ocr_results['text_blocks']:
                if block.get('confidence', 0) >= threshold:
                    filtered_blocks.append(block)
            ocr_results['text_blocks'] = filtered_blocks
        
        return ocr_results
    
    def _write_output_file(self, output_path: str, content: str) -> None:
        """Write output file."""
        try:
            # Create directory if it doesn't exist
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # Write file
            from utils.encoding_utils import safe_write_text
            safe_write_text(output_path, '', encoding='utf-8')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Create backup if enabled
            if self.config_manager.get_config('output.include_backup', True):
                backup_path = self._create_backup(output_path)
                self.logger.info(f"Backup created: {backup_path}")
            
        except Exception as e:
            raise FileOperationError(f"Failed to write output file: {output_path}", output_path, 'write')
    
    def _create_backup(self, file_path: str) -> str:
        """Create backup of existing file."""
        import shutil
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup_{timestamp}"
        
        try:
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            self.logger.warning(f"Failed to create backup: {e}")
            return file_path
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate processing summary."""
        total_files = len(results)
        successful_files = sum(1 for result in results.values() if result['success'])
        failed_files = total_files - successful_files
        success_rate = (successful_files / total_files) * 100 if total_files > 0 else 0
        
        # Get failed files
        failed_file_list = [file_path for file_path, result in results.items() if not result['success']]
        
        return {
            'total_files': total_files,
            'successful_files': successful_files,
            'failed_files': failed_files,
            'success_rate': success_rate,
            'failed_files': failed_file_list,
            'processing_time': self.statistics['total_processing_time'],
            'average_processing_time': self.statistics['average_processing_time']
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.statistics.copy()
    
    def reset_statistics(self) -> None:
        """Reset processing statistics."""
        self.statistics = {
            'total_files_processed': 0,
            'successful_files': 0,
            'failed_files': 0,
            'total_processing_time': 0,
            'average_processing_time': 0,
            'start_time': None,
            'end_time': None
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current configuration."""
        try:
            config = self.config_manager.copy_config()
            
            # Validate each section
            validation_results = {}
            for section in config.keys():
                if not section.startswith('_'):  # Skip metadata sections
                    validation_results[section] = self.config_manager.validate_config({section: config[section]})
            
            # Overall validation
            overall_valid = all(result['valid'] for result in validation_results.values())
            
            return {
                'valid': overall_valid,
                'sections': validation_results,
                'errors': [error for result in validation_results.values() for error in result.get('errors', [])]
            }
            
        except Exception as e:
            return {
                'valid': False,
                'sections': {},
                'errors': [str(e)]
            }
    
    def update_configuration(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        try:
            self.config_manager.update_config(updates)
            
            # Update component configurations
            self.ocr_processor.update_config(self.config_manager.get_tesseract_config())
            self.preprocessor.update_config(self.config_manager.get_preprocessing_config())
            self.formatter.update_config(self.config_manager.get_formatting_config())
            self.metadata_generator.update_config(self.config_manager.get_metadata_config())
            self.validator.update_config(self.config_manager.get_validation_config())
            
            self.logger.info("Configuration updated successfully")
            
        except Exception as e:
            error_msg = f"Failed to update configuration: {e}"
            self.error_handler.handle_configuration_error(Exception(error_msg))
            raise PNGToMarkdownError(error_msg)
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config_manager.copy_config()
    
    def export_configuration(self, file_path: str) -> bool:
        """Export current configuration to file."""
        try:
            return self.config_manager.save_config(file_path)
        except Exception as e:
            error_msg = f"Failed to export configuration: {e}"
            self.error_handler.handle_configuration_error(Exception(error_msg))
            return False
    
    def import_configuration(self, file_path: str) -> bool:
        """Import configuration from file."""
        try:
            success = self.config_manager.load_config(file_path)
            if success:
                # Update component configurations
                self.update_configuration(self.config_manager.copy_config())
            return success
        except Exception as e:
            error_msg = f"Failed to import configuration: {e}"
            self.error_handler.handle_configuration_error(Exception(error_msg))
            return False
    
    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Reset statistics
            self.reset_statistics()
            
            # Clear any temporary files
            temp_dir = self.config_manager.get_config('output.directory', './output')
            if os.path.exists(temp_dir):
                # Clean up temporary files (keep processed files)
                for file in os.listdir(temp_dir):
                    if file.startswith('temp_') or file.endswith('.tmp'):
                        try:
                            os.remove(os.path.join(temp_dir, file))
                        except Exception:
                            pass
            
            self.logger.info("Cleanup completed")
            
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {e}")