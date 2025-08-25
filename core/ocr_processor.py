"""
Tesseract OCR Processor Module

This module provides the core OCR processing functionality using Tesseract OCR.
It handles text extraction with confidence scores, metadata collection, and
batch processing capabilities.

Author: Kilo Code
Version: 1.0.0
"""

import os
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from PIL import Image

# Local imports
from errors.exceptions import OCRError, DependencyError
from errors.handler import ErrorHandler


class TesseractOCRProcessor:
    """
    Core OCR processing engine with Tesseract integration.
    Handles text extraction with confidence scores and metadata.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize OCR processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.error_handler = ErrorHandler()
        
        # Initialize OCR settings
        self.languages = self.config.get('tesseract', {}).get('languages', ['eng'])
        self.psm = self.config.get('tesseract', {}).get('psm', 3)
        self.oem = self.config.get('tesseract', {}).get('oem', 3)
        self.confidence_threshold = self.config.get('tesseract', {}).get('confidence_threshold', 0)
        self.custom_config = self.config.get('tesseract', {}).get('config', '')
        
        # Validate OCR dependencies
        self._validate_dependencies()
    
    def _validate_dependencies(self) -> bool:
        """Validate OCR dependencies."""
        try:
            # Check if required packages are available
            import PIL
            print(f"PIL version: {PIL.__version__}")
            
            # Check if language data is available
            available_languages = self._get_available_languages()
            missing_languages = [lang for lang in self.languages if lang not in available_languages]
            
            if missing_languages:
                print(f"Warning: Missing language data for: {missing_languages}")
                print(f"Available languages: {available_languages}")
            
            return True
            
        except Exception as e:
            error_msg = f"OCR dependencies validation failed: {e}"
            self.error_handler.handle_ocr_error(OCRError(error_msg), {'processor': 'OCRProcessor'})
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
            
            # Load image
            image = Image.open(image_path)
            
            # Build Tesseract configuration
            config = self._build_tesseract_config()
            
            # Extract text data
            text_data = self._extract_text_data(image, config)
            
            # Extract detailed text with bounding boxes
            detailed_text = self._extract_detailed_text(image, config)
            
            # Extract confidence information
            confidence_scores = self._extract_confidence_scores(text_data)
            
            # Calculate processing statistics
            processing_time = time.time() - start_time
            
            # Build result dictionary
            result = {
                'input_path': image_path,
                'timestamp': datetime.now().isoformat(),
                'processing_time': processing_time,
                'text': detailed_text.strip(),
                'text_blocks': self._organize_text_blocks(text_data),
                'confidence_scores': confidence_scores,
                'statistics': {
                    'total_words': len(text_data['text'].split()),
                    'total_lines': len([line for line in text_data['text'].split('\n') if line.strip()]),
                    'average_confidence': confidence_scores.get('average_confidence', 0),
                    'high_confidence_words': confidence_scores.get('high_confidence_count', 0),
                    'low_confidence_words': confidence_scores.get('low_confidence_count', 0)
                },
                'metadata': {
                    'image_size': image.size,
                    'image_mode': image.mode,
                    'tesseract_config': config,
                    'languages_used': self.languages,
                    'psm_mode': self.psm,
                    'oem_mode': self.oem
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
        
        for i, image_path in enumerate(image_paths):
            try:
                print(f"Processing {i+1}/{len(image_paths)}: {image_path}")
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
                'average_processing_time': batch_time / len(image_paths) if image_paths else 0
            }
        }
        
        return batch_result
    
    def _build_tesseract_config(self) -> str:
        """Build Tesseract configuration string."""
        config_parts = []
        
        # Add OEM and PSM
        config_parts.append(f"--oem {self.oem}")
        config_parts.append(f"--psm {self.psm}")
        
        # Add custom configuration
        if self.custom_config:
            config_parts.append(self.custom_config)
        
        return ' '.join(config_parts)
    
    def _extract_confidence_scores(self, text_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract confidence scores from Tesseract data."""
        confidences = []
        high_confidence_count = 0
        low_confidence_count = 0
        
        for i in range(len(text_data['text'])):
            confidence = int(text_data['conf'][i])
            confidences.append(confidence)
            
            if confidence >= self.confidence_threshold:
                high_confidence_count += 1
            else:
                low_confidence_count += 1
        
        average_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'confidences': confidences,
            'average_confidence': average_confidence,
            'high_confidence_count': high_confidence_count,
            'low_confidence_count': low_confidence_count,
            'confidence_threshold': self.confidence_threshold
        }
    
    def _organize_text_blocks(self, text_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Organize text blocks with position information."""
        blocks = []
        
        for i in range(len(text_data['text'])):
            if text_data['text'][i].strip():  # Only process non-empty text
                block = {
                    'text': text_data['text'][i],
                    'confidence': int(text_data['conf'][i]),
                    'x': int(text_data['left'][i]),
                    'y': int(text_data['top'][i]),
                    'width': int(text_data['width'][i]),
                    'height': int(text_data['height'][i]),
                    'line_number': int(text_data['line_num'][i]),
                    'block_number': int(text_data['block_num'][i]),
                    'paragraph_number': int(text_data['par_num'][i]),
                    'word_number': int(text_data['word_num'][i])
                }
                blocks.append(block)
        
        return blocks
    
    def get_available_languages(self) -> List[str]:
        """Get list of available OCR languages."""
        try:
            # This would normally call pytesseract.get_languages(config='')
            # For now, return a placeholder list
            return ['eng']  # Placeholder - should be updated when OCR engine is selected
        except Exception as e:
            self.error_handler.handle_ocr_error(OCRError(f"Failed to get available languages: {e}"), {})
            return []
    
    def validate_installation(self) -> bool:
        """Validate OCR installation and dependencies."""
        try:
            # Test basic functionality
            test_image = Image.new('RGB', (100, 100), color='white')
            test_text = self._extract_detailed_text(test_image, '--psm 6')
            
            return True
            
        except Exception as e:
            self.error_handler.handle_ocr_error(OCRError(f"Installation validation failed: {e}"), {})
            return False
    
    def set_languages(self, languages: List[str]) -> None:
        """Set OCR languages."""
        self.languages = languages
    
    def set_psm(self, psm: int) -> None:
        """Set page segmentation mode."""
        if 0 <= psm <= 14:
            self.psm = psm
        else:
            raise ValueError("PSM must be between 0 and 14")
    
    def set_oem(self, oem: int) -> None:
        """Set OCR engine mode."""
        if 0 <= oem <= 3:
            self.oem = oem
        else:
            raise ValueError("OEM must be between 0 and 3")
    
    def set_confidence_threshold(self, threshold: int) -> None:
        """Set confidence threshold."""
        if 0 <= threshold <= 100:
            self.confidence_threshold = threshold
        else:
            raise ValueError("Confidence threshold must be between 0 and 100")