"""
Image Utilities Module

This module provides utility functions for image processing and manipulation.
It includes various image enhancement and preprocessing techniques.

Author: Kilo Code
Version: 1.0.0
"""

import os
import io
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path

# External imports
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw, ImageFont

# Local imports
from errors.exceptions import ImageError, ProcessingError
from errors.handler import ErrorHandler


class ImageUtils:
    """
    Utility class for image processing and manipulation.
    Provides various image enhancement and preprocessing techniques.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize image utilities.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler()
        self.config = config or {}
        
        # Default settings
        self.default_settings = {
            'max_size': 3000,
            'enhance_contrast': True,
            'remove_noise': True,
            'binarize': True,
            'sharpen': True,
            'deskew': True,
            'contrast_factor': 1.5,
            'brightness_factor': 1.1,
            'sharpen_factor': 1.0,
            'noise_reduction_radius': 1,
            'binarization_threshold': 128
        }
        
        # Merge with provided config
        if config:
            self.default_settings.update(config)
    
    def load_image(self, image_path: str) -> Image.Image:
        """
        Load image from file path.
        
        Args:
            image_path: Path to image file
            
        Returns:
            PIL.Image: Loaded image
        """
        try:
            if not os.path.exists(image_path):
                raise ImageError(f"Image file not found: {image_path}", image_path)
            
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode not in ['RGB', 'L']:
                image = image.convert('RGB')
            
            self.logger.debug(f"Loaded image: {image_path} ({image.size[0]}x{image.size[1]}, {image.mode})")
            return image
            
        except Exception as e:
            error_msg = f"Failed to load image {image_path}: {e}"
            self.error_handler.handle_image_error(Exception(error_msg), image_path)
            raise ImageError(error_msg, image_path)
    
    def save_image(self, image: Image.Image, output_path: str, quality: int = 95) -> bool:
        """
        Save image to file.
        
        Args:
            image: PIL.Image to save
            output_path: Path to save image
            quality: Image quality (1-100)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # Save image
            image.save(output_path, quality=quality, optimize=True)
            
            self.logger.debug(f"Saved image: {output_path}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to save image to {output_path}: {e}"
            self.error_handler.handle_image_error(Exception(error_msg), output_path)
            return False
    
    def resize_image(self, image: Image.Image, max_size: int = None) -> Image.Image:
        """
        Resize image while maintaining aspect ratio.
        
        Args:
            image: PIL.Image to resize
            max_size: Maximum size (width or height)
            
        Returns:
            PIL.Image: Resized image
        """
        try:
            if max_size is None:
                max_size = self.default_settings.get('max_size', 3000)
            
            # Get current dimensions
            width, height = image.size
            
            # Check if resize is needed
            if width <= max_size and height <= max_size:
                return image
            
            # Calculate new dimensions
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            
            # Resize image
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            self.logger.debug(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            return resized_image
            
        except Exception as e:
            error_msg = f"Failed to resize image: {e}"
            self.error_handler.handle_image_error(Exception(error_msg))
            raise ImageError(error_msg)
    
    def enhance_contrast(self, image: Image.Image, factor: float = None) -> Image.Image:
        """
        Enhance image contrast.
        
        Args:
            image: PIL.Image to enhance
            factor: Contrast enhancement factor
            
        Returns:
            PIL.Image: Enhanced image
        """
        try:
            if factor is None:
                factor = self.default_settings.get('contrast_factor', 1.5)
            
            enhancer = ImageEnhance.Contrast(image)
            enhanced_image = enhancer.enhance(factor)
            
            self.logger.debug(f"Enhanced contrast with factor: {factor}")
            return enhanced_image
            
        except Exception as e:
            error_msg = f"Failed to enhance contrast: {e}"
            self.error_handler.handle_image_error(Exception(error_msg))
            raise ImageError(error_msg)
    
    def adjust_brightness(self, image: Image.Image, factor: float = None) -> Image.Image:
        """
        Adjust image brightness.
        
        Args:
            image: PIL.Image to adjust
            factor: Brightness adjustment factor
            
        Returns:
            PIL.Image: Adjusted image
        """
        try:
            if factor is None:
                factor = self.default_settings.get('brightness_factor', 1.1)
            
            enhancer = ImageEnhance.Brightness(image)
            adjusted_image = enhancer.enhance(factor)
            
            self.logger.debug(f"Adjusted brightness with factor: {factor}")
            return adjusted_image
            
        except Exception as e:
            error_msg = f"Failed to adjust brightness: {e}"
            self.error_handler.handle_image_error(Exception(error_msg))
            raise ImageError(error_msg)
    
    def sharpen_image(self, image: Image.Image, factor: float = None) -> Image.Image:
        """
        Sharpen image.
        
        Args:
            image: PIL.Image to sharpen
            factor: Sharpening factor
            
        Returns:
            PIL.Image: Sharpened image
        """
        try:
            if factor is None:
                factor = self.default_settings.get('sharpen_factor', 1.0)
            
            enhancer = ImageEnhance.Sharpness(image)
            sharpened_image = enhancer.enhance(factor)
            
            self.logger.debug(f"Sharpened image with factor: {factor}")
            return sharpened_image
            
        except Exception as e:
            error_msg = f"Failed to sharpen image: {e}"
            self.error_handler.handle_image_error(Exception(error_msg))
            raise ImageError(error_msg)
    
    def remove_noise(self, image: Image.Image, radius: int = None) -> Image.Image:
        """
        Remove noise from image.
        
        Args:
            image: PIL.Image to denoise
            radius: Noise reduction radius
            
        Returns:
            PIL.Image: Denoised image
        """
        try:
            if radius is None:
                radius = self.default_settings.get('noise_reduction_radius', 1)
            
            # Apply median filter for noise reduction
            denoised_image = image.filter(ImageFilter.MedianFilter(size=radius))
            
            self.logger.debug(f"Removed noise with radius: {radius}")
            return denoised_image
            
        except Exception as e:
            error_msg = f"Failed to remove noise: {e}"
            self.error_handler.handle_image_error(Exception(error_msg))
            raise ImageError(error_msg)
    
    def binarize_image(self, image: Image.Image, threshold: int = None) -> Image.Image:
        """
        Convert image to black and white.
        
        Args:
            image: PIL.Image to binarize
            threshold: Binarization threshold (0-255)
            
        Returns:
            PIL.Image: Binarized image
        """
        try:
            if threshold is None:
                threshold = self.default_settings.get('binarization_threshold', 128)
            
            # Convert to grayscale
            gray_image = image.convert('L')
            
            # Apply threshold
            binarized_image = gray_image.point(lambda x: 0 if x < threshold else 255, '1')
            
            self.logger.debug(f"Binarized image with threshold: {threshold}")
            return binarized_image
            
        except Exception as e:
            error_msg = f"Failed to binarize image: {e}"
            self.error_handler.handle_image_error(Exception(error_msg))
            raise ImageError(error_msg)
    
    def deskew_image(self, image: Image.Image) -> Image.Image:
        """
        Deskew image (correct rotation).
        
        Args:
            image: PIL.Image to deskew
            
        Returns:
            PIL.Image: Deskewed image
        """
        try:
            # Convert to grayscale
            gray_image = image.convert('L')
            
            # Find edges
            edges = gray_image.filter(ImageFilter.FIND_EDGES)
            
            # Convert to numpy array
            img_array = np.array(edges)
            
            # Calculate skew angle
            angle = self._calculate_skew_angle(img_array)
            
            # Rotate image if angle is significant
            if abs(angle) > 0.5:
                deskewed_image = image.rotate(-angle, expand=True, fillcolor='white')
                self.logger.debug(f"Deskewed image by angle: {angle:.2f}°")
                return deskewed_image
            else:
                self.logger.debug("No significant skew detected")
                return image
                
        except Exception as e:
            error_msg = f"Failed to deskew image: {e}"
            self.error_handler.handle_image_error(Exception(error_msg))
            raise ImageError(error_msg)
    
    def _calculate_skew_angle(self, img_array: np.ndarray) -> float:
        """Calculate skew angle from image array."""
        try:
            # Calculate horizontal and vertical projections
            horizontal_proj = np.sum(img_array, axis=1)
            vertical_proj = np.sum(img_array, axis=0)
            
            # Find the main angle using Hough transform approximation
            # This is a simplified approach
            height, width = img_array.shape
            
            # Calculate the angle based on the distribution of white pixels
            white_pixels = np.where(img_array > 0)
            if len(white_pixels[0]) == 0:
                return 0.0
            
            # Simple angle calculation
            y_coords = white_pixels[0]
            x_coords = white_pixels[1]
            
            if len(y_coords) < 2:
                return 0.0
            
            # Calculate angle using linear regression
            angle = np.arctan2(np.cov(x_coords, y_coords)[0, 1], np.cov(x_coords, y_coords)[0, 0])
            angle_degrees = np.degrees(angle)
            
            return angle_degrees
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate skew angle: {e}")
            return 0.0
    
    def convert_to_optimal_format(self, image: Image.Image) -> Image.Image:
        """
        Convert image to optimal format for OCR.
        
        Args:
            image: PIL.Image to convert
            
        Returns:
            PIL.Image: Converted image
        """
        try:
            # Convert to RGB if necessary
            if image.mode not in ['RGB', 'L']:
                image = image.convert('RGB')
            
            # Convert to 8-bit grayscale if color is not needed
            if image.mode == 'RGB':
                # Check if image is mostly grayscale
                img_array = np.array(image)
                if np.all(img_array == img_array[:, :, 0][:, :, np.newaxis]):
                    image = image.convert('L')
            
            # Ensure it's not palette-based
            if image.mode == 'P':
                image = image.convert('RGB')
            
            self.logger.debug(f"Converted image to optimal format: {image.mode}")
            return image
            
        except Exception as e:
            error_msg = f"Failed to convert image format: {e}"
            self.error_handler.handle_image_error(Exception(error_msg))
            raise ImageError(error_msg)
    
    def apply_preprocessing_pipeline(self, image: Image.Image) -> Image.Image:
        """
        Apply complete preprocessing pipeline to image.
        
        Args:
            image: PIL.Image to preprocess
            
        Returns:
            PIL.Image: Preprocessed image
        """
        try:
            processed_image = image.copy()
            
            # Convert to optimal format
            processed_image = self.convert_to_optimal_format(processed_image)
            
            # Resize if necessary
            max_size = self.default_settings.get('max_size', 3000)
            processed_image = self.resize_image(processed_image, max_size)
            
            # Enhance contrast if enabled
            if self.default_settings.get('enhance_contrast', True):
                processed_image = self.enhance_contrast(processed_image)
            
            # Adjust brightness if enabled
            if self.default_settings.get('brightness_factor', 1.1) != 1.0:
                processed_image = self.adjust_brightness(processed_image)
            
            # Remove noise if enabled
            if self.default_settings.get('remove_noise', True):
                processed_image = self.remove_noise(processed_image)
            
            # Binarize if enabled
            if self.default_settings.get('binarize', True):
                processed_image = self.binarize_image(processed_image)
            
            # Sharpen if enabled
            if self.default_settings.get('sharpen', True):
                processed_image = self.sharpen_image(processed_image)
            
            # Deskew if enabled
            if self.default_settings.get('deskew', True):
                processed_image = self.deskew_image(processed_image)
            
            self.logger.debug("Applied complete preprocessing pipeline")
            return processed_image
            
        except Exception as e:
            error_msg = f"Failed to apply preprocessing pipeline: {e}"
            self.error_handler.handle_image_error(Exception(error_msg))
            raise ImageError(error_msg)
    
    def get_image_info(self, image: Image.Image) -> Dict[str, Any]:
        """
        Get comprehensive image information.
        
        Args:
            image: PIL.Image to analyze
            
        Returns:
            Dict: Image information
        """
        try:
            info = {
                'width': image.width,
                'height': image.height,
                'mode': image.mode,
                'format': image.format,
                'size_bytes': len(image.tobytes()),
                'has_transparency': image.mode in ['RGBA', 'LA'] or 'transparency' in image.info,
                'dpi': image.info.get('dpi', (72, 72)),
                'has_exif': hasattr(image, '_getexif') and image._getexif() is not None
            }
            
            # Calculate aspect ratio
            info['aspect_ratio'] = image.width / image.height if image.height > 0 else 1.0
            
            # Estimate file size
            info['estimated_file_size'] = len(image.tobytes()) / 1024  # KB
            
            return info
            
        except Exception as e:
            error_msg = f"Failed to get image info: {e}"
            self.error_handler.handle_image_error(Exception(error_msg))
            raise ImageError(error_msg)
    
    def create_thumbnail(self, image: Image.Image, size: Tuple[int, int] = (200, 200)) -> Image.Image:
        """
        Create thumbnail of image.
        
        Args:
            image: PIL.Image to thumbnail
            size: Thumbnail size (width, height)
            
        Returns:
            PIL.Image: Thumbnail image
        """
        try:
            thumbnail = image.copy()
            thumbnail.thumbnail(size, Image.Resampling.LANCZOS)
            return thumbnail
            
        except Exception as e:
            error_msg = f"Failed to create thumbnail: {e}"
            self.error_handler.handle_image_error(Exception(error_msg))
            raise ImageError(error_msg)
    
    def convert_colorspace(self, image: Image.Image, target_mode: str) -> Image.Image:
        """
        Convert image to target colorspace.
        
        Args:
            image: PIL.Image to convert
            target_mode: Target colorspace ('RGB', 'L', 'CMYK', etc.)
            
        Returns:
            PIL.Image: Converted image
        """
        try:
            if image.mode == target_mode:
                return image
            
            converted_image = image.convert(target_mode)
            self.logger.debug(f"Converted colorspace from {image.mode} to {target_mode}")
            return converted_image
            
        except Exception as e:
            error_msg = f"Failed to convert colorspace: {e}"
            self.error_handler.handle_image_error(Exception(error_msg))
            raise ImageError(error_msg)
    
    def apply_mask(self, image: Image.Image, mask: Image.Image) -> Image.Image:
        """
        Apply mask to image.
        
        Args:
            image: PIL.Image to mask
            mask: PIL.Image mask
            
        Returns:
            PIL.Image: Masked image
        """
        try:
            # Ensure mask is grayscale
            if mask.mode != 'L':
                mask = mask.convert('L')
            
            # Create composite image
            masked_image = Image.composite(image, Image.new('RGB', image.size), mask)
            
            self.logger.debug("Applied mask to image")
            return masked_image
            
        except Exception as e:
            error_msg = f"Failed to apply mask: {e}"
            self.error_handler.handle_image_error(Exception(error_msg))
            raise ImageError(error_msg)
    
    def extract_region(self, image: Image.Image, box: Tuple[int, int, int, int]) -> Image.Image:
        """
        Extract region from image.
        
        Args:
            image: PIL.Image to extract from
            box: Bounding box (left, top, right, bottom)
            
        Returns:
            PIL.Image: Extracted region
        """
        try:
            region = image.crop(box)
            self.logger.debug(f"Extracted region: {box}")
            return region
            
        except Exception as e:
            error_msg = f"Failed to extract region: {e}"
            self.error_handler.handle_image_error(Exception(error_msg))
            raise ImageError(error_msg)
    
    def merge_images(self, images: List[Image.Image], direction: str = 'horizontal') -> Image.Image:
        """
        Merge multiple images.
        
        Args:
            images: List of PIL.Image to merge
            direction: Merge direction ('horizontal' or 'vertical')
            
        Returns:
            PIL.Image: Merged image
        """
        try:
            if not images:
                raise ImageError("No images to merge")
            
            if len(images) == 1:
                return images[0]
            
            # Get dimensions
            widths, heights = zip(*(img.size for img in images))
            
            if direction == 'horizontal':
                total_width = sum(widths)
                max_height = max(heights)
                merged_image = Image.new('RGB', (total_width, max_height), 'white')
                
                x_offset = 0
                for img in images:
                    merged_image.paste(img, (x_offset, 0))
                    x_offset += img.width
                    
            elif direction == 'vertical':
                max_width = max(widths)
                total_height = sum(heights)
                merged_image = Image.new('RGB', (max_width, total_height), 'white')
                
                y_offset = 0
                for img in images:
                    merged_image.paste(img, (0, y_offset))
                    y_offset += img.height
            
            else:
                raise ImageError(f"Invalid merge direction: {direction}")
            
            self.logger.debug(f"Merged {len(images)} images {direction}ly")
            return merged_image
            
        except Exception as e:
            error_msg = f"Failed to merge images: {e}"
            self.error_handler.handle_image_error(Exception(error_msg))
            raise ImageError(error_msg)
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Update configuration.
        
        Args:
            config: New configuration
        """
        try:
            self.default_settings.update(config)
            self.logger.info("Image utilities configuration updated")
        except Exception as e:
            error_msg = f"Failed to update configuration: {e}"
            self.error_handler.handle_configuration_error(Exception(error_msg))
            raise ImageError(error_msg)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.
        
        Returns:
            Dict: Current configuration
        """
        return self.default_settings.copy()