"""
Image Preprocessor Module

This module provides image preprocessing functionality for enhancing OCR accuracy.
It handles various image enhancement techniques including format conversion,
resizing, contrast enhancement, noise reduction, and binarization.

Author: Kilo Code
Version: 1.0.0
"""

import os
import io
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np

# Local imports
from errors.exceptions import ImageError
from errors.handler import ErrorHandler


class ImagePreprocessor:
    """
    Image preprocessing pipeline for enhancing OCR accuracy.
    Handles various image enhancement techniques.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize image preprocessor.
        
        Args:
            config: Preprocessing configuration
        """
        self.config = config or {}
        self.error_handler = ErrorHandler()
        
        # Preprocessing settings
        self.enabled = self.config.get('preprocessing', {}).get('enabled', True)
        self.max_size = self.config.get('preprocessing', {}).get('max_size', 3000)
        self.enhance_contrast = self.config.get('preprocessing', {}).get('enhance_contrast', True)
        self.remove_noise = self.config.get('preprocessing', {}).get('remove_noise', True)
        self.binarize = self.config.get('preprocessing', {}).get('binarize', True)
        self.sharpen = self.config.get('preprocessing', {}).get('sharpen', True)
        self.deskew = self.config.get('preprocessing', {}).get('deskew', True)
        
        # Enhancement parameters
        self.contrast_factor = self.config.get('preprocessing', {}).get('contrast_factor', 1.5)
        self.brightness_factor = self.config.get('preprocessing', {}).get('brightness_factor', 1.1)
        self.sharpen_factor = self.config.get('preprocessing', {}).get('sharpen_factor', 1.0)
        self.noise_reduction_radius = self.config.get('preprocessing', {}).get('noise_reduction_radius', 1)
        self.binarization_threshold = self.config.get('preprocessing', {}).get('binarization_threshold', 128)
    
    def preprocess_image(self, image_path: str) -> Image.Image:
        """
        Apply preprocessing pipeline to image.
        
        Args:
            image_path: Path to input image
            
        Returns:
            PIL.Image: Preprocessed image
        """
        try:
            if not self.enabled:
                print("Preprocessing disabled, loading image as-is")
                return Image.open(image_path)
            
            print(f"Preprocessing image: {image_path}")
            
            # Load image
            image = self._load_image(image_path)
            
            # Apply preprocessing pipeline
            image = self._validate_and_convert_format(image)
            image = self._optimize_size(image)
            image = self._convert_to_rgb(image)
            image = self._enhance_contrast(image)
            image = self._adjust_brightness(image)
            image = self._remove_noise(image)
            image = self._sharpen_image(image)
            image = self._deskew_image(image)
            image = self._binarize_image(image)
            
            print("Preprocessing completed successfully")
            return image
            
        except Exception as e:
            error_msg = f"Image preprocessing failed for {image_path}: {e}"
            self.error_handler.handle_image_error(ImageError(error_msg), image_path)
            raise ImageError(error_msg)
    
    def _load_image(self, image_path: str) -> Image.Image:
        """Load image from file path."""
        try:
            if not os.path.exists(image_path):
                raise ImageError(f"Image file not found: {image_path}")
            
            image = Image.open(image_path)
            
            # Verify image is not corrupted
            image.verify()
            image = Image.open(image_path)  # Reopen after verification
            
            return image
            
        except Exception as e:
            raise ImageError(f"Failed to load image {image_path}: {e}")
    
    def _validate_and_convert_format(self, image: Image.Image) -> Image.Image:
        """Validate image format and convert to optimal format."""
        try:
            # Convert to RGB if necessary
            if image.mode in ['RGBA', 'LA', 'P']:
                image = image.convert('RGB')
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
            
        except Exception as e:
            raise ImageError(f"Format conversion failed: {e}")
    
    def _optimize_size(self, image: Image.Image) -> Image.Image:
        """Optimize image size for OCR processing."""
        try:
            width, height = image.size
            
            # Resize if too large
            if max(width, height) > self.max_size:
                print(f"Resizing image from {width}x{height} (max: {self.max_size})")
                ratio = self.max_size / max(width, height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Resize if too small (minimum 300x300 for good OCR)
            elif min(width, height) < 300:
                print(f"Upsampling small image from {width}x{height}")
                ratio = 300 / min(width, height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.BICUBIC)
            
            return image
            
        except Exception as e:
            raise ImageError(f"Size optimization failed: {e}")
    
    def _convert_to_rgb(self, image: Image.Image) -> Image.Image:
        """Convert image to RGB color space."""
        try:
            if image.mode != 'RGB':
                image = image.convert('RGB')
            return image
            
        except Exception as e:
            raise ImageError(f"RGB conversion failed: {e}")
    
    def _enhance_contrast(self, image: Image.Image) -> Image.Image:
        """Enhance image contrast for better OCR."""
        try:
            if not self.enhance_contrast:
                return image
            
            print("Enhancing contrast")
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(self.contrast_factor)
            return image
            
        except Exception as e:
            raise ImageError(f"Contrast enhancement failed: {e}")
    
    def _adjust_brightness(self, image: Image.Image) -> Image.Image:
        """Adjust image brightness."""
        try:
            if self.brightness_factor != 1.0:
                print("Adjusting brightness")
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(self.brightness_factor)
            return image
            
        except Exception as e:
            raise ImageError(f"Brightness adjustment failed: {e}")
    
    def _remove_noise(self, image: Image.Image) -> Image.Image:
        """Remove noise from image."""
        try:
            if not self.remove_noise:
                return image
            
            print("Removing noise")
            
            # Apply median filter for noise reduction
            if self.noise_reduction_radius > 0:
                image = image.filter(ImageFilter.MedianFilter(size=self.noise_reduction_radius))
            
            # Additional noise reduction using bilateral filter approximation
            image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
            
            return image
            
        except Exception as e:
            raise ImageError(f"Noise removal failed: {e}")
    
    def _sharpen_image(self, image: Image.Image) -> Image.Image:
        """Sharpen image to enhance text edges."""
        try:
            if not self.sharpen:
                return image
            
            print("Sharpening image")
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(self.sharpen_factor)
            return image
            
        except Exception as e:
            raise ImageError(f"Image sharpening failed: {e}")
    
    def _deskew_image(self, image: Image.Image) -> Image.Image:
        """Deskew image to correct text orientation."""
        try:
            if not self.deskew:
                return image
            
            print("Deskewing image")
            
            # Convert to grayscale for better edge detection
            gray = image.convert('L')
            
            # Use edge detection to find text lines
            edges = gray.filter(ImageFilter.FIND_EDGES)
            
            # Simple deskewing using rotation (basic implementation)
            # In production, you might want to use OpenCV for more sophisticated deskewing
            image = image.rotate(0, expand=True)  # Placeholder - implement actual deskewing
            
            return image
            
        except Exception as e:
            print(f"Deskewing failed, continuing without deskewing: {e}")
            return image
    
    def _binarize_image(self, image: Image.Image) -> Image.Image:
        """Convert image to black and white for better OCR."""
        try:
            if not self.binarize:
                return image
            
            print("Binarizing image")
            
            # Convert to grayscale
            gray = image.convert('L')
            
            # Apply threshold
            threshold = self.binarization_threshold
            binary = gray.point(lambda x: 0 if x < threshold else 255, '1')
            
            return binary
            
        except Exception as e:
            raise ImageError(f"Image binarization failed: {e}")
    
    def preprocess_and_save(self, image_path: str, output_path: str) -> str:
        """
        Preprocess image and save to output path.
        
        Args:
            image_path: Path to input image
            output_path: Path to save preprocessed image
            
        Returns:
            str: Path to saved preprocessed image
        """
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image_path)
            
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # Save processed image
            processed_image.save(output_path, 'PNG', optimize=True)
            
            print(f"Preprocessed image saved to: {output_path}")
            return output_path
            
        except Exception as e:
            error_msg = f"Failed to save preprocessed image: {e}"
            self.error_handler.handle_image_error(ImageError(error_msg), output_path)
            raise ImageError(error_msg)
    
    def get_preprocessing_info(self) -> Dict[str, Any]:
        """Get current preprocessing configuration."""
        return {
            'enabled': self.enabled,
            'max_size': self.max_size,
            'enhance_contrast': self.enhance_contrast,
            'remove_noise': self.remove_noise,
            'binarize': self.binarize,
            'sharpen': self.sharpen,
            'deskew': self.deskew,
            'contrast_factor': self.contrast_factor,
            'brightness_factor': self.brightness_factor,
            'sharpen_factor': self.sharpen_factor,
            'noise_reduction_radius': self.noise_reduction_radius,
            'binarization_threshold': self.binarization_threshold
        }
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """Update preprocessing configuration."""
        self.config.update(config)
        
        # Update settings
        preprocessing_config = config.get('preprocessing', {})
        self.enabled = preprocessing_config.get('enabled', self.enabled)
        self.max_size = preprocessing_config.get('max_size', self.max_size)
        self.enhance_contrast = preprocessing_config.get('enhance_contrast', self.enhance_contrast)
        self.remove_noise = preprocessing_config.get('remove_noise', self.remove_noise)
        self.binarize = preprocessing_config.get('binarize', self.binarize)
        self.sharpen = preprocessing_config.get('sharpen', self.sharpen)
        self.deskew = preprocessing_config.get('deskew', self.deskew)
        
        # Update parameters
        self.contrast_factor = preprocessing_config.get('contrast_factor', self.contrast_factor)
        self.brightness_factor = preprocessing_config.get('brightness_factor', self.brightness_factor)
        self.sharpen_factor = preprocessing_config.get('sharpen_factor', self.sharpen_factor)
        self.noise_reduction_radius = preprocessing_config.get('noise_reduction_radius', self.noise_reduction_radius)
        self.binarization_threshold = preprocessing_config.get('binarization_threshold', self.binarization_threshold)
    
    def validate_image_format(self, image_path: str) -> bool:
        """Validate if image format is supported."""
        try:
            with Image.open(image_path) as img:
                img.verify()
                return True
        except Exception:
            return False
    
    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """Get image information."""
        try:
            with Image.open(image_path) as img:
                return {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'width': img.width,
                    'height': img.height,
                    'file_size': os.path.getsize(image_path)
                }
        except Exception as e:
            raise ImageError(f"Failed to get image info: {e}")