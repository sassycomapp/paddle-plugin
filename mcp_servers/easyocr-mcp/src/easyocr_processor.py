"""
EasyOCR Processor Module

This module provides the core OCR processing functionality using EasyOCR.
It handles text extraction with confidence scores, metadata collection, and
batch processing capabilities with low-resource optimizations.

Author: Kilo Code
Version: 1.0.0
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from PIL import Image
import numpy as np

# Local imports
from ...errors.exceptions import OCRError, DependencyError
from errors.handler import ErrorHandler


class EasyOCRProcessor:
    """
    Core OCR processing engine with EasyOCR integration.
    Handles text extraction with confidence scores and metadata.
    Optimized for low-resource usage on Asus x515ae.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize OCR processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.error_handler = ErrorHandler()
        self.logger = logging.getLogger(__name__)
        
        # Initialize OCR settings with low-resource defaults
        self.languages = self.config.get('easyocr', {}).get('languages', ['en'])
        self.gpu = self.config.get('easyocr', {}).get('gpu', False)
        self.model_storage_directory = self.config.get('easyocr', {}).get('model_storage_directory', 'C:/easyocr_models')
        self.confidence_threshold = self.config.get('easyocr', {}).get('confidence_threshold', 30)
        self.recognize_text_args = self.config.get('easyocr', {}).get('recognize_text_args', {})
        
        # Preprocessing settings
        self.max_image_size = self.config.get('preprocessing', {}).get('max_image_size', 1024)
        self.use_grayscale = self.config.get('preprocessing', {}).get('use_grayscale', True)
        self.use_binarization = self.config.get('preprocessing', {}).get('use_binarization', True)
        
        # Batch processing settings
        self.batch_size = self.config.get('batch', {}).get('size', 5)
        self.batch_timeout = self.config.get('batch', {}).get('timeout', 30)
        
        # Model preloading
        self.model_loaded = False
        self.reader = None
        
        # Validate OCR dependencies
        self._validate_dependencies()
    
    def _validate_dependencies(self) -> bool:
        """Validate OCR dependencies."""
        try:
            # Check if required packages are available
            import easyocr
            print(f"EasyOCR version: {easyocr.__version__}")
            
            # Check if model storage directory exists
            if not os.path.exists(self.model_storage_directory):
                print(f"Creating model storage directory: {self.model_storage_directory}")
                os.makedirs(self.model_storage_directory, exist_ok=True)
            
            # Check if language data is available
            available_languages = self._get_available_languages()
            missing_languages = [lang for lang in self.languages if lang not in available_languages]
            
            if missing_languages:
                print(f"Warning: Missing language data for: {missing_languages}")
                print(f"Available languages: {available_languages}")
            
            return True
            
        except Exception as e:
            error_msg = f"OCR dependencies validation failed: {e}"
            self.error_handler.handle_ocr_error(OCRError(error_msg), {'processor': 'EasyOCRProcessor'})
            raise OCRError(error_msg)
    
    def _load_model(self) -> None:
        """Load EasyOCR model with preloading."""
        if self.model_loaded:
            return
        
        try:
            print("Loading EasyOCR model...")
            import easyocr
            
            # Configure model loading with low-resource settings
            model_args = {
                'gpu': self.gpu,
                'model_storage_directory': self.model_storage_directory,
                'download_enabled': True,
                'verbose': True
            }
            
            # Add custom recognition arguments
            model_args.update(self.recognize_text_args)
            
            # Initialize reader
            self.reader = easyocr.Reader(
                lang_list=self.languages,
                gpu=self.gpu,
                model_storage_directory=self.model_storage_directory,
                **model_args
            )
            
            # Test model loading
            test_image = np.zeros((100, 100, 3), dtype=np.uint8)
            self.reader.readtext(test_image)
            
            self.model_loaded = True
            print("EasyOCR model loaded successfully")
            
        except Exception as e:
            error_msg = f"Failed to load EasyOCR model: {e}"
            self.error_handler.handle_ocr_error(OCRError(error_msg), {'processor': 'EasyOCRProcessor'})
            raise OCRError(error_msg)
    
    def extract_text_with_metadata(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text with comprehensive metadata.
        
        Args:
            image_path: Path to input image
            
        Returns:
            Dict: Contains text, confidence scores, bounding boxes, timestamps
        """
        start_time = time.time()
        
        try:
            # Validate input
            if not os.path.exists(image_path):
                raise OCRError(f"Image file not found: {image_path}")
            
            # Load and preprocess image
            image = self._load_and_preprocess_image(image_path)
            
            # Load model if not already loaded
            self._load_model()
            
            # Extract text data
            text_data = self._extract_text_data(image)
            
            # Calculate processing statistics
            processing_time = time.time() - start_time
            
            # Build result dictionary
            result = {
                'input_path': image_path,
                'timestamp': datetime.now().isoformat(),
                'processing_time': processing_time,
                'text': self._format_text_output(text_data),
                'text_blocks': self._organize_text_blocks(text_data),
                'confidence_scores': self._extract_confidence_scores(text_data),
                'statistics': {
                    'total_words': len(self._extract_words(text_data)),
                    'total_lines': len([line for line in self._extract_lines(text_data) if line.strip()]),
                    'average_confidence': self._calculate_average_confidence(text_data),
                    'high_confidence_words': self._count_high_confidence_words(text_data),
                    'low_confidence_words': self._count_low_confidence_words(text_data)
                },
                'metadata': {
                    'image_size': image.size,
                    'image_mode': image.mode,
                    'easyocr_config': {
                        'languages': self.languages,
                        'gpu': self.gpu,
                        'confidence_threshold': self.confidence_threshold,
                        'model_storage_directory': self.model_storage_directory
                    },
                    'preprocessing_applied': {
                        'max_image_size': self.max_image_size,
                        'use_grayscale': self.use_grayscale,
                        'use_binarization': self.use_binarization
                    }
                }
            }
            
            return result
            
        except Exception as e:
            error_msg = f"OCR extraction failed for {image_path}: {e}"
            self.error_handler.handle_ocr_error(OCRError(error_msg), {'image_path': image_path})
            raise OCRError(error_msg)
    
    def extract_batch(self, image_paths: List[str]) -> Dict[str, Any]:
        """
        Extract text from multiple images in batch.
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            Dict: Batch extraction results with statistics
        """
        start_time = time.time()
        results = []
        failed_files = []
        
        # Process in batches
        for i in range(0, len(image_paths), self.batch_size):
            batch_paths = image_paths[i:i + self.batch_size]
            batch_start = time.time()
            
            for image_path in batch_paths:
                try:
                    print(f"Processing {i + 1}/{len(image_paths)}: {image_path}")
                    result = self.extract_text_with_metadata(image_path)
                    results.append(result)
                except Exception as e:
                    print(f"Failed to process {image_path}: {e}")
                    failed_files.append(image_path)
                    results.append({
                        'input_path': image_path,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
            
            batch_time = time.time() - batch_start
            print(f"Batch {i//self.batch_size + 1} completed in {batch_time:.2f} seconds")
        
        # Calculate batch statistics
        batch_time = time.time() - start_time
        successful_files = len([r for r in results if 'error' not in r])
        
        # Aggregate statistics
        total_words = sum(r.get('statistics', {}).get('total_words', 0) for r in results if 'error' not in r)
        total_lines = sum(r.get('statistics', {}).get('total_lines', 0) for r in results if 'error' not in r)
        avg_confidence = sum(r.get('statistics', {}).get('average_confidence', 0) for r in results if 'error' not in r)
        avg_confidence = avg_confidence / successful_files if successful_files > 0 else 0
        
        batch_result = {
            'batch_timestamp': datetime.now().isoformat(),
            'total_processing_time': batch_time,
            'total_files': len(image_paths),
            'successful_files': successful_files,
            'failed_files': len(failed_files),
            'success_rate': (successful_files / len(image_paths)) * 100 if image_paths else 0,
            'failed_file_paths': failed_files,
            'results': results,
            'batch_statistics': {
                'total_words_extracted': total_words,
                'total_lines_extracted': total_lines,
                'average_confidence': avg_confidence,
                'average_processing_time': batch_time / len(image_paths) if image_paths else 0,
                'batch_size': self.batch_size,
                'batches_processed': (len(image_paths) + self.batch_size - 1) // self.batch_size
            }
        }
        
        return batch_result
    
    def _load_and_preprocess_image(self, image_path: str) -> Image.Image:
        """Load and preprocess image for OCR."""
        try:
            # Load image
            image = Image.open(image_path)
            
            # Apply preprocessing
            image = self._preprocess_image(image)
            
            return image
            
        except Exception as e:
            raise OCRError(f"Failed to load and preprocess image {image_path}: {e}")
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Apply preprocessing pipeline to image."""
        try:
            # Resize image to max dimensions
            image = self._resize_image(image)
            
            # Convert to grayscale if enabled
            if self.use_grayscale:
                image = image.convert('L')
            
            # Apply binarization if enabled
            if self.use_binarization:
                image = self._binarize_image(image)
            
            return image
            
        except Exception as e:
            raise OCRError(f"Image preprocessing failed: {e}")
    
    def _resize_image(self, image: Image.Image) -> Image.Image:
        """Resize image to max dimensions while maintaining aspect ratio."""
        try:
            width, height = image.size
            
            # Resize if too large
            if max(width, height) > self.max_image_size:
                print(f"Resizing image from {width}x{height} (max: {self.max_image_size})")
                ratio = self.max_image_size / max(width, height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            raise OCRError(f"Image resizing failed: {e}")
    
    def _binarize_image(self, image: Image.Image) -> Image.Image:
        """Convert image to black and white for better OCR."""
        try:
            # Convert to grayscale if not already
            if image.mode != 'L':
                image = image.convert('L')
            
            # Apply threshold
            threshold = 128
            binary = image.point(lambda x: 0 if x < threshold else 255, '1')
            
            return binary
            
        except Exception as e:
            raise OCRError(f"Image binarization failed: {e}")
    
    def _extract_text_data(self, image: Image.Image) -> List[Tuple[str, Tuple[int, int, int, int], float]]:
        """Extract text data using EasyOCR."""
        try:
            # Convert PIL image to numpy array
            image_array = np.array(image)
            
            # Extract text with EasyOCR
            results = self.reader.readtext(
                image_array,
                decoder='beamsearch',
                beamWidth=5,
                batch_size=1,
                workers=1 if not self.gpu else 0,
                allowlist=None,
                blocklist=None,
                detail=1,
                rotation_info=[0],
                y_ths=0.5,
                x_ths=0.5,
                contrast_ths=0.1,
                adjust_contrast=0.0,
                filter_ths=0.1,
                text_threshold=self.confidence_threshold / 100.0,
                link_threshold=0.4,
                low_text=0.4,
                output_format='dict'
            )
            
            return results
            
        except Exception as e:
            raise OCRError(f"Text extraction failed: {e}")
    
    def _organize_text_blocks(self, text_data: List[Tuple[str, Tuple[int, int, int, int], float]]) -> List[Dict[str, Any]]:
        """Organize text blocks with position information."""
        blocks = []
        
        for i, (text, bbox, confidence) in enumerate(text_data):
            if text.strip():  # Only process non-empty text
                block = {
                    'text': text,
                    'confidence': confidence,
                    'bbox': bbox,
                    'x': bbox[0],
                    'y': bbox[1],
                    'width': bbox[2] - bbox[0],
                    'height': bbox[3] - bbox[1],
                    'line_number': i,
                    'block_number': i // 10,  # Simple grouping
                    'word_count': len(text.split())
                }
                blocks.append(block)
        
        return blocks
    
    def _extract_confidence_scores(self, text_data: List[Tuple[str, Tuple[int, int, int, int], float]]) -> Dict[str, Any]:
        """Extract confidence scores from text data."""
        confidences = []
        high_confidence_count = 0
        low_confidence_count = 0
        
        for _, _, confidence in text_data:
            confidences.append(confidence)
            
            if confidence >= self.confidence_threshold / 100.0:
                high_confidence_count += 1
            else:
                low_confidence_count += 1
        
        average_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'confidences': confidences,
            'average_confidence': average_confidence,
            'high_confidence_count': high_confidence_count,
            'low_confidence_count': low_confidence_count,
            'confidence_threshold': self.confidence_threshold / 100.0
        }
    
    def _format_text_output(self, text_data: List[Tuple[str, Tuple[int, int, int, int], float]]) -> str:
        """Format text output with proper line breaks."""
        lines = []
        current_y = None
        current_line = ""
        
        for text, bbox, confidence in text_data:
            y = bbox[1]
            
            # Start new line if y coordinate changes significantly
            if current_y is not None and abs(y - current_y) > 20:
                if current_line.strip():
                    lines.append(current_line)
                current_line = ""
            
            current_y = y
            current_line += text + " "
        
        # Add the last line
        if current_line.strip():
            lines.append(current_line)
        
        return '\n'.join(lines)
    
    def _extract_words(self, text_data: List[Tuple[str, Tuple[int, int, int, int], float]]) -> List[str]:
        """Extract all words from text data."""
        words = []
        for text, _, _ in text_data:
            words.extend(text.split())
        return words
    
    def _extract_lines(self, text_data: List[Tuple[str, Tuple[int, int, int, int], float]]) -> List[str]:
        """Extract all lines from text data."""
        lines = []
        current_y = None
        current_line = ""
        
        for text, bbox, _ in text_data:
            y = bbox[1]
            
            if current_y is not None and abs(y - current_y) > 20:
                if current_line.strip():
                    lines.append(current_line)
                current_line = ""
            
            current_y = y
            current_line += text + " "
        
        if current_line.strip():
            lines.append(current_line)
        
        return lines
    
    def _calculate_average_confidence(self, text_data: List[Tuple[str, Tuple[int, int, int, int], float]]) -> float:
        """Calculate average confidence score."""
        if not text_data:
            return 0
        
        total_confidence = sum(confidence for _, _, confidence in text_data)
        return total_confidence / len(text_data)
    
    def _count_high_confidence_words(self, text_data: List[Tuple[str, Tuple[int, int, int, int], float]]) -> int:
        """Count words with high confidence."""
        threshold = self.confidence_threshold / 100.0
        return sum(1 for _, _, confidence in text_data if confidence >= threshold)
    
    def _count_low_confidence_words(self, text_data: List[Tuple[str, Tuple[int, int, int, int], float]]) -> int:
        """Count words with low confidence."""
        threshold = self.confidence_threshold / 100.0
        return sum(1 for _, _, confidence in text_data if confidence < threshold)
    
    def get_available_languages(self) -> List[str]:
        """Get list of available OCR languages."""
        try:
            import easyocr
            # Get available languages from EasyOCR
            return list(easyocr.languages.LANGUAGES.keys())
        except Exception as e:
            self.error_handler.handle_ocr_error(OCRError(f"Failed to get available languages: {e}"), {})
            return []
    
    def validate_installation(self) -> bool:
        """Validate OCR installation and dependencies."""
        try:
            # Test basic functionality
            test_image = Image.new('RGB', (100, 100), color='white')
            test_image_array = np.array(test_image)
            
            # Load model and test
            self._load_model()
            results = self.reader.readtext(test_image_array)
            
            return True
            
        except Exception as e:
            self.error_handler.handle_ocr_error(OCRError(f"Installation validation failed: {e}"), {})
            return False
    
    def set_languages(self, languages: List[str]) -> None:
        """Set OCR languages."""
        self.languages = languages
        # Reset model to reload with new languages
        self.model_loaded = False
        self.reader = None
    
    def set_gpu(self, gpu: bool) -> None:
        """Enable/disable GPU usage."""
        self.gpu = gpu
        # Reset model to apply GPU setting
        self.model_loaded = False
        self.reader = None
    
    def set_confidence_threshold(self, threshold: int) -> None:
        """Set confidence threshold."""
        if 0 <= threshold <= 100:
            self.confidence_threshold = threshold
        else:
            raise ValueError("Confidence threshold must be between 0 and 100")
    
    def set_model_storage_directory(self, directory: str) -> None:
        """Set model storage directory."""
        self.model_storage_directory = directory
        # Reset model to use new directory
        self.model_loaded = False
        self.reader = None
    
    def get_processor_info(self) -> Dict[str, Any]:
        """Get processor information and configuration."""
        return {
            'processor_type': 'EasyOCR',
            'languages': self.languages,
            'gpu_enabled': self.gpu,
            'model_storage_directory': self.model_storage_directory,
            'confidence_threshold': self.confidence_threshold,
            'model_loaded': self.model_loaded,
            'preprocessing_settings': {
                'max_image_size': self.max_image_size,
                'use_grayscale': self.use_grayscale,
                'use_binarization': self.use_binarization
            },
            'batch_settings': {
                'batch_size': self.batch_size,
                'batch_timeout': self.batch_timeout
            }
        }