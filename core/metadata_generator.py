"""
Metadata Generator Module

This module provides comprehensive metadata and statistics collection for OCR results.
It generates quality assessment reports and performance metrics.

Author: Kilo Code
Version: 1.0.0
"""

import os
import json
import hashlib
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import statistics

# Local imports
from errors.exceptions import ImageError
from errors.handler import ErrorHandler


class MetadataGenerator:
    """
    Generates comprehensive metadata and statistics for OCR results.
    Provides quality assessment and performance metrics.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize metadata generator.
        
        Args:
            config: Metadata configuration
        """
        self.config = config or {}
        self.error_handler = ErrorHandler()
        
        # Metadata settings
        self.include_detailed_stats = self.config.get('metadata', {}).get('include_detailed_stats', True)
        self.include_quality_metrics = self.config.get('metadata', {}).get('include_quality_metrics', True)
        self.include_performance_metrics = self.config.get('metadata', {}).get('include_performance_metrics', True)
        self.include_file_info = self.config.get('metadata', {}).get('include_file_info', True)
        self.include_processing_info = self.config.get('metadata', {}).get('include_processing_info', True)
    
    def generate_processing_metadata(self, image_path: str, ocr_results: Dict) -> Dict[str, Any]:
        """
        Generate processing metadata.
        
        Args:
            image_path: Path to processed image
            ocr_results: OCR results
            
        Returns:
            Dict: Processing metadata
        """
        try:
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'image_path': image_path,
                'image_hash': self._calculate_file_hash(image_path),
                'processing_metadata': {}
            }
            
            # Add file information
            if self.include_file_info:
                metadata['file_info'] = self._get_file_info(image_path)
            
            # Add processing information
            if self.include_processing_info:
                metadata['processing_metadata'] = self._get_processing_info(ocr_results)
            
            # Add quality metrics
            if self.include_quality_metrics:
                metadata['quality_metrics'] = self._calculate_quality_metrics(ocr_results)
            
            # Add performance metrics
            if self.include_performance_metrics:
                metadata['performance_metrics'] = self._calculate_performance_metrics(ocr_results)
            
            # Add detailed statistics
            if self.include_detailed_stats:
                metadata['detailed_statistics'] = self._calculate_detailed_statistics(ocr_results)
            
            return metadata
            
        except Exception as e:
            error_msg = f"Failed to generate processing metadata: {e}"
            self.error_handler.handle_image_error(ImageError(error_msg), image_path)
            raise ImageError(error_msg)
    
    def calculate_quality_metrics(self, ocr_results: Dict) -> Dict[str, Any]:
        """
        Calculate quality metrics for OCR results.
        
        Args:
            ocr_results: OCR results
            
        Returns:
            Dict: Quality metrics
        """
        try:
            quality_metrics = {
                'overall_score': 0.0,
                'confidence_score': 0.0,
                'completeness_score': 0.0,
                'consistency_score': 0.0,
                'readability_score': 0.0,
                'assessment': 'Unknown'
            }
            
            # Calculate confidence score
            if 'confidence_scores' in ocr_results:
                conf_scores = ocr_results['confidence_scores']
                avg_confidence = conf_scores.get('average_confidence', 0)
                quality_metrics['confidence_score'] = avg_confidence / 100.0  # Normalize to 0-1
            
            # Calculate completeness score
            if 'statistics' in ocr_results:
                stats = ocr_results['statistics']
                total_words = stats.get('total_words', 0)
                total_lines = stats.get('total_lines', 0)
                
                # Estimate expected words based on image size
                if 'metadata' in ocr_results:
                    img_size = ocr_results['metadata'].get('image_size', (0, 0))
                    expected_words = img_size[0] * img_size[1] / 1000  # Rough estimate
                    completeness = min(total_words / expected_words, 1.0) if expected_words > 0 else 0.0
                    quality_metrics['completeness_score'] = completeness
            
            # Calculate consistency score
            if 'text_blocks' in ocr_results:
                blocks = ocr_results['text_blocks']
                if len(blocks) > 1:
                    confidences = [block['confidence'] for block in blocks]
                    conf_std = statistics.stdev(confidences) if len(confidences) > 1 else 0
                    # Lower standard deviation = higher consistency
                    quality_metrics['consistency_score'] = max(0, 1 - (conf_std / 100))
            
            # Calculate readability score (based on line structure)
            if 'text_blocks' in ocr_results:
                blocks = ocr_results['text_blocks']
                line_numbers = [block['line_number'] for block in blocks]
                if len(line_numbers) > 1:
                    line_gaps = [line_numbers[i+1] - line_numbers[i] for i in range(len(line_numbers)-1)]
                    avg_gap = statistics.mean(line_gaps)
                    # Reasonable line spacing = higher readability
                    quality_metrics['readability_score'] = max(0, 1 - abs(avg_gap - 1) / 10)
            
            # Calculate overall score
            scores = [
                quality_metrics['confidence_score'],
                quality_metrics['completeness_score'],
                quality_metrics['consistency_score'],
                quality_metrics['readability_score']
            ]
            quality_metrics['overall_score'] = statistics.mean(scores)
            
            # Determine assessment
            overall_score = quality_metrics['overall_score']
            if overall_score >= 0.9:
                quality_metrics['assessment'] = 'Excellent'
            elif overall_score >= 0.75:
                quality_metrics['assessment'] = 'Good'
            elif overall_score >= 0.5:
                quality_metrics['assessment'] = 'Fair'
            else:
                quality_metrics['assessment'] = 'Poor'
            
            return quality_metrics
            
        except Exception as e:
            error_msg = f"Failed to calculate quality metrics: {e}"
            self.error_handler.handle_image_error(ImageError(error_msg), "quality_metrics")
            raise ImageError(error_msg)
    
    def generate_statistics_report(self, batch_results: List[Dict]) -> Dict[str, Any]:
        """
        Generate comprehensive statistics report.
        
        Args:
            batch_results: List of batch processing results
            
        Returns:
            Dict: Statistics report
        """
        try:
            if not batch_results:
                return {'error': 'No batch results provided'}
            
            report = {
                'report_timestamp': datetime.now().isoformat(),
                'total_files': len(batch_results),
                'successful_files': 0,
                'failed_files': 0,
                'overall_statistics': {},
                'quality_analysis': {},
                'performance_analysis': {},
                'error_analysis': {}
            }
            
            # Count successful and failed files
            successful_files = [r for r in batch_results if 'error' not in r]
            failed_files = [r for r in batch_results if 'error' in r]
            
            report['successful_files'] = len(successful_files)
            report['failed_files'] = len(failed_files)
            report['success_rate'] = (len(successful_files) / len(batch_results)) * 100
            
            # Calculate overall statistics
            if successful_files:
                report['overall_statistics'] = self._calculate_batch_statistics(successful_files)
            
            # Analyze quality across batch
            if successful_files:
                report['quality_analysis'] = self._analyze_batch_quality(successful_files)
            
            # Analyze performance across batch
            if successful_files:
                report['performance_analysis'] = self._analyze_batch_performance(successful_files)
            
            # Analyze errors
            if failed_files:
                report['error_analysis'] = self._analyze_batch_errors(failed_files)
            
            return report
            
        except Exception as e:
            error_msg = f"Failed to generate statistics report: {e}"
            self.error_handler.handle_image_error(ImageError(error_msg), "statistics_report")
            raise ImageError(error_msg)
    
    def assess_confidence_distribution(self, confidence_results: List[Dict]) -> Dict[str, Any]:
        """
        Assess confidence distribution and quality.
        
        Args:
            confidence_results: List of confidence results
            
        Returns:
            Dict: Confidence distribution analysis
        """
        try:
            if not confidence_results:
                return {'error': 'No confidence results provided'}
            
            # Flatten all confidence scores
            all_confidences = []
            for result in confidence_results:
                if 'confidences' in result:
                    all_confidences.extend(result['confidences'])
            
            if not all_confidences:
                return {'error': 'No confidence scores found'}
            
            # Calculate statistics
            avg_confidence = statistics.mean(all_confidences)
            median_confidence = statistics.median(all_confidences)
            conf_std = statistics.stdev(all_confidences) if len(all_confidences) > 1 else 0
            conf_min = min(all_confidences)
            conf_max = max(all_confidences)
            
            # Create distribution bins
            bins = {
                'excellent': sum(1 for c in all_confidences if c >= 90),
                'good': sum(1 for c in all_confidences if 75 <= c < 90),
                'fair': sum(1 for c in all_confidences if 50 <= c < 75),
                'poor': sum(1 for c in all_confidences if c < 50)
            }
            
            total_words = len(all_confidences)
            distribution = {
                'excellent_percentage': (bins['excellent'] / total_words) * 100,
                'good_percentage': (bins['good'] / total_words) * 100,
                'fair_percentage': (bins['fair'] / total_words) * 100,
                'poor_percentage': (bins['poor'] / total_words) * 100
            }
            
            # Calculate overall quality assessment
            overall_quality = 'Unknown'
            if avg_confidence >= 90:
                overall_quality = 'Excellent'
            elif avg_confidence >= 75:
                overall_quality = 'Good'
            elif avg_confidence >= 50:
                overall_quality = 'Fair'
            else:
                overall_quality = 'Poor'
            
            return {
                'total_words': total_words,
                'average_confidence': avg_confidence,
                'median_confidence': median_confidence,
                'standard_deviation': conf_std,
                'min_confidence': conf_min,
                'max_confidence': conf_max,
                'distribution': distribution,
                'bins': bins,
                'overall_quality': overall_quality,
                'consistency_score': max(0, 1 - (conf_std / 100))
            }
            
        except Exception as e:
            error_msg = f"Failed to assess confidence distribution: {e}"
            self.error_handler.handle_image_error(ImageError(error_msg), "confidence_distribution")
            raise ImageError(error_msg)
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file."""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return "unknown"
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information."""
        try:
            stat = os.stat(file_path)
            return {
                'filename': os.path.basename(file_path),
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'extension': os.path.splitext(file_path)[1].lower()
            }
        except Exception:
            return {'error': 'Failed to get file info'}
    
    def _get_processing_info(self, ocr_results: Dict) -> Dict[str, Any]:
        """Get processing information."""
        try:
            processing_info = {
                'processing_time': ocr_results.get('processing_time', 0),
                'timestamp': ocr_results.get('timestamp', ''),
                'tesseract_config': ocr_results.get('metadata', {}).get('tesseract_config', ''),
                'languages_used': ocr_results.get('metadata', {}).get('languages_used', []),
                'psm_mode': ocr_results.get('metadata', {}).get('psm_mode', ''),
                'oem_mode': ocr_results.get('metadata', {}).get('oem_mode', '')
            }
            return processing_info
        except Exception:
            return {'error': 'Failed to get processing info'}
    
    def _calculate_quality_metrics(self, ocr_results: Dict) -> Dict[str, Any]:
        """Calculate quality metrics."""
        return self.calculate_quality_metrics(ocr_results)
    
    def _calculate_performance_metrics(self, ocr_results: Dict) -> Dict[str, Any]:
        """Calculate performance metrics."""
        try:
            performance_metrics = {
                'words_per_second': 0.0,
                'lines_per_second': 0.0,
                'processing_efficiency': 0.0
            }
            
            processing_time = ocr_results.get('processing_time', 0)
            if processing_time > 0:
                stats = ocr_results.get('statistics', {})
                total_words = stats.get('total_words', 0)
                total_lines = stats.get('total_lines', 0)
                
                performance_metrics['words_per_second'] = total_words / processing_time
                performance_metrics['lines_per_second'] = total_lines / processing_time
                
                # Calculate efficiency (words per second normalized)
                performance_metrics['processing_efficiency'] = min(performance_metrics['words_per_second'] / 10, 1.0)
            
            return performance_metrics
            
        except Exception:
            return {'error': 'Failed to calculate performance metrics'}
    
    def _calculate_detailed_statistics(self, ocr_results: Dict) -> Dict[str, Any]:
        """Calculate detailed statistics."""
        try:
            detailed_stats = {}
            
            if 'text_blocks' in ocr_results:
                blocks = ocr_results['text_blocks']
                
                # Text length statistics
                text_lengths = [len(block['text']) for block in blocks]
                detailed_stats['text_length_stats'] = {
                    'min_length': min(text_lengths) if text_lengths else 0,
                    'max_length': max(text_lengths) if text_lengths else 0,
                    'avg_length': statistics.mean(text_lengths) if text_lengths else 0,
                    'total_characters': sum(text_lengths)
                }
                
                # Confidence statistics
                confidences = [block['confidence'] for block in blocks]
                detailed_stats['confidence_stats'] = {
                    'min_confidence': min(confidences) if confidences else 0,
                    'max_confidence': max(confidences) if confidences else 0,
                    'confidence_std': statistics.stdev(confidences) if len(confidences) > 1 else 0
                }
                
                # Position statistics
                x_positions = [block['x'] for block in blocks]
                y_positions = [block['y'] for block in blocks]
                detailed_stats['position_stats'] = {
                    'min_x': min(x_positions) if x_positions else 0,
                    'max_x': max(x_positions) if x_positions else 0,
                    'min_y': min(y_positions) if y_positions else 0,
                    'max_y': max(y_positions) if y_positions else 0,
                    'spread_x': max(x_positions) - min(x_positions) if x_positions else 0,
                    'spread_y': max(y_positions) - min(y_positions) if y_positions else 0
                }
            
            return detailed_stats
            
        except Exception:
            return {'error': 'Failed to calculate detailed statistics'}
    
    def _calculate_batch_statistics(self, successful_files: List[Dict]) -> Dict[str, Any]:
        """Calculate batch statistics."""
        try:
            total_words = sum(r.get('statistics', {}).get('total_words', 0) for r in successful_files)
            total_lines = sum(r.get('statistics', {}).get('total_lines', 0) for r in successful_files)
            total_time = sum(r.get('processing_time', 0) for r in successful_files)
            avg_confidence = sum(r.get('statistics', {}).get('average_confidence', 0) for r in successful_files) / len(successful_files)
            
            return {
                'total_words_extracted': total_words,
                'total_lines_extracted': total_lines,
                'total_processing_time': total_time,
                'average_processing_time': total_time / len(successful_files),
                'average_words_per_second': total_words / total_time if total_time > 0 else 0,
                'average_confidence': avg_confidence,
                'files_processed': len(successful_files)
            }
        except Exception:
            return {'error': 'Failed to calculate batch statistics'}
    
    def _analyze_batch_quality(self, successful_files: List[Dict]) -> Dict[str, Any]:
        """Analyze quality across batch."""
        try:
            quality_scores = []
            for result in successful_files:
                if 'statistics' in result:
                    avg_conf = result['statistics'].get('average_confidence', 0)
                    quality_scores.append(avg_conf)
            
            if quality_scores:
                return {
                    'average_quality': statistics.mean(quality_scores),
                    'quality_std': statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0,
                    'min_quality': min(quality_scores),
                    'max_quality': max(quality_scores),
                    'excellent_files': sum(1 for q in quality_scores if q >= 90),
                    'good_files': sum(1 for q in quality_scores if 75 <= q < 90),
                    'fair_files': sum(1 for q in quality_scores if 50 <= q < 75),
                    'poor_files': sum(1 for q in quality_scores if q < 50)
                }
            else:
                return {'error': 'No quality data found'}
        except Exception:
            return {'error': 'Failed to analyze batch quality'}
    
    def _analyze_batch_performance(self, successful_files: List[Dict]) -> Dict[str, Any]:
        """Analyze performance across batch."""
        try:
            processing_times = [r.get('processing_time', 0) for r in successful_files]
            words_per_second = []
            
            for result in successful_files:
                if 'statistics' in result:
                    words = result['statistics'].get('total_words', 0)
                    time = result.get('processing_time', 1)  # Avoid division by zero
                    words_per_second.append(words / time)
            
            return {
                'average_processing_time': statistics.mean(processing_times),
                'processing_time_std': statistics.stdev(processing_times) if len(processing_times) > 1 else 0,
                'min_processing_time': min(processing_times),
                'max_processing_time': max(processing_times),
                'average_words_per_second': statistics.mean(words_per_second) if words_per_second else 0,
                'performance_consistency': max(0, 1 - (statistics.stdev(words_per_second) / statistics.mean(words_per_second))) if words_per_second and statistics.mean(words_per_second) > 0 else 0
            }
        except Exception:
            return {'error': 'Failed to analyze batch performance'}
    
    def _analyze_batch_errors(self, failed_files: List[Dict]) -> Dict[str, Any]:
        """Analyze errors across batch."""
        try:
            error_types = {}
            error_messages = []
            
            for result in failed_files:
                error = result.get('error', 'Unknown error')
                error_messages.append(error)
                
                # Categorize errors
                if 'tesseract' in error.lower():
                    error_types['tesseract'] = error_types.get('tesseract', 0) + 1
                elif 'image' in error.lower():
                    error_types['image'] = error_types.get('image', 0) + 1
                elif 'file' in error.lower():
                    error_types['file'] = error_types.get('file', 0) + 1
                else:
                    error_types['other'] = error_types.get('other', 0) + 1
            
            return {
                'total_errors': len(failed_files),
                'error_types': error_types,
                'common_error_messages': error_messages[:5],  # Top 5 error messages
                'error_rate': (len(failed_files) / (len(failed_files) + len([r for r in failed_files if 'error' not in r]))) * 100
            }
        except Exception:
            return {'error': 'Failed to analyze batch errors'}
    
    def get_metadata_info(self) -> Dict[str, Any]:
        """Get current metadata configuration."""
        return {
            'include_detailed_stats': self.include_detailed_stats,
            'include_quality_metrics': self.include_quality_metrics,
            'include_performance_metrics': self.include_performance_metrics,
            'include_file_info': self.include_file_info,
            'include_processing_info': self.include_processing_info
        }
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """Update metadata configuration."""
        self.config.update(config)
        
        # Update settings
        metadata_config = config.get('metadata', {})
        self.include_detailed_stats = metadata_config.get('include_detailed_stats', self.include_detailed_stats)
        self.include_quality_metrics = metadata_config.get('include_quality_metrics', self.include_quality_metrics)
        self.include_performance_metrics = metadata_config.get('include_performance_metrics', self.include_performance_metrics)
        self.include_file_info = metadata_config.get('include_file_info', self.include_file_info)
        self.include_processing_info = metadata_config.get('include_processing_info', self.include_processing_info)