"""
Markdown Formatter Module

This module provides advanced markdown formatting with layout preservation.
It converts OCR results to structured markdown with metadata and statistics.

Author: Kilo Code
Version: 1.0.0
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import textwrap

# Local imports
from errors.exceptions import ImageError
from errors.handler import ErrorHandler


class MarkdownFormatter:
    """
    Advanced markdown formatter with layout preservation.
    Converts OCR results to structured markdown with metadata.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize markdown formatter.
        
        Args:
            config: Formatting configuration
        """
        self.config = config or {}
        self.error_handler = ErrorHandler()
        
        # Formatting settings
        self.preserve_layout = self.config.get('formatting', {}).get('preserve_layout', True)
        self.include_metadata = self.config.get('formatting', {}).get('include_metadata', True)
        self.include_statistics = self.config.get('formatting', {}).get('include_statistics', True)
        self.confidence_threshold = self.config.get('formatting', {}).get('confidence_threshold', 0)
        
        # Layout detection settings
        self.table_detection_threshold = self.config.get('formatting', {}).get('table_detection_threshold', 0.7)
        self.column_detection_threshold = self.config.get('formatting', {}).get('column_detection_threshold', 0.6)
        self.heading_detection_threshold = self.config.get('formatting', {}).get('heading_detection_threshold', 0.8)
        
        # Markdown formatting settings
        self.max_line_length = self.config.get('formatting', {}).get('max_line_length', 80)
        self.paragraph_spacing = self.config.get('formatting', {}).get('paragraph_spacing', 2)
        self.table_alignment = self.config.get('formatting', {}).get('table_alignment', 'left')
    
    def format_ocr_results(self, ocr_results: Dict[str, Any]) -> str:
        """
        Format OCR results into comprehensive markdown.
        
        Args:
            ocr_results: OCR results from processor
            
        Returns:
            str: Formatted markdown content
        """
        try:
            print("Formatting OCR results to markdown")
            
            # Initialize markdown content
            markdown_content = []
            
            # Add header
            markdown_content.append(self._generate_header(ocr_results))
            
            # Add main content
            if self.preserve_layout:
                markdown_content.append(self._preserve_layout(ocr_results.get('text_blocks', [])))
            else:
                markdown_content.append(self._format_basic_text(ocr_results.get('text', '')))
            
            # Add metadata section
            if self.include_metadata:
                markdown_content.append(self._add_metadata_section(ocr_results))
            
            # Add statistics section
            if self.include_statistics:
                markdown_content.append(self._add_statistics_section(ocr_results))
            
            # Add confidence analysis
            if 'confidence_scores' in ocr_results:
                markdown_content.append(self._add_confidence_analysis(ocr_results['confidence_scores']))
            
            # Combine all sections
            full_content = '\n\n'.join(markdown_content)
            
            print("Markdown formatting completed")
            return full_content
            
        except Exception as e:
            error_msg = f"Markdown formatting failed: {e}"
            self.error_handler.handle_image_error(ImageError(error_msg), "formatting")
            raise ImageError(error_msg)
    
    def _generate_header(self, ocr_results: Dict[str, Any]) -> str:
        """Generate markdown header with document information."""
        header_lines = [
            "# OCR Document",
            "",
            f"**Source File:** {ocr_results.get('input_path', 'Unknown')}",
            f"**Processed:** {ocr_results.get('timestamp', datetime.now().isoformat())}",
            f"**Processing Time:** {ocr_results.get('processing_time', 0):.2f} seconds",
            "",
            "---",
            ""
        ]
        return '\n'.join(header_lines)
    
    def _preserve_layout(self, text_blocks: List[Dict]) -> str:
        """Preserve original layout in markdown format."""
        if not text_blocks:
            return ""
        
        # Sort blocks by position to maintain reading order
        sorted_blocks = sorted(text_blocks, key=lambda x: (x['y'], x['x']))
        
        # Group blocks by line and paragraph
        line_groups = self._group_blocks_by_line(sorted_blocks)
        paragraph_groups = self._group_blocks_by_paragraph(line_groups)
        
        # Format each paragraph
        formatted_paragraphs = []
        for paragraph in paragraph_groups:
            formatted_paragraph = self._format_paragraph(paragraph)
            if formatted_paragraph.strip():
                formatted_paragraphs.append(formatted_paragraph)
        
        return '\n\n'.join(formatted_paragraphs)
    
    def _group_blocks_by_line(self, blocks: List[Dict]) -> List[List[Dict]]:
        """Group text blocks by line based on y-coordinate."""
        if not blocks:
            return []
        
        lines = []
        current_line = []
        current_y = blocks[0]['y']
        line_tolerance = 10  # Pixels tolerance for same line
        
        for block in blocks:
            if abs(block['y'] - current_y) <= line_tolerance:
                current_line.append(block)
            else:
                # Sort line by x-coordinate
                current_line.sort(key=lambda x: x['x'])
                lines.append(current_line)
                current_line = [block]
                current_y = block['y']
        
        # Add the last line
        if current_line:
            current_line.sort(key=lambda x: x['x'])
            lines.append(current_line)
        
        return lines
    
    def _group_blocks_by_paragraph(self, lines: List[List[Dict]]) -> List[List[List[Dict]]]:
        """Group lines into paragraphs based on spacing."""
        if not lines:
            return []
        
        paragraphs = []
        current_paragraph = []
        prev_y = 0
        
        for line in lines:
            if current_paragraph:
                # Check if this line is a new paragraph (significant y gap)
                y_gap = line[0]['y'] - prev_y
                if y_gap > 20:  # Threshold for new paragraph
                    paragraphs.append(current_paragraph)
                    current_paragraph = []
            
            current_paragraph.append(line)
            prev_y = line[0]['y']
        
        # Add the last paragraph
        if current_paragraph:
            paragraphs.append(current_paragraph)
        
        return paragraphs
    
    def _format_paragraph(self, paragraph: List[List[Dict]]) -> str:
        """Format a paragraph with proper markdown."""
        paragraph_text = []
        
        for line in paragraph:
            line_text = ' '.join([block['text'] for block in line if block['text'].strip()])
            if line_text.strip():
                paragraph_text.append(line_text)
        
        return '\n'.join(paragraph_text)
    
    def _format_basic_text(self, text: str) -> str:
        """Format basic text without layout preservation."""
        if not text:
            return ""
        
        # Clean up text
        text = text.strip()
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Wrap long lines
        lines = []
        for line in text.split('\n'):
            if len(line) > self.max_line_length:
                wrapped = textwrap.fill(line, width=self.max_line_length)
                lines.extend(wrapped.split('\n'))
            else:
                lines.append(line)
        
        return '\n'.join(lines)
    
    def _add_metadata_section(self, ocr_results: Dict[str, Any]) -> str:
        """Add metadata section to markdown output."""
        metadata_lines = [
            "## Metadata",
            ""
        ]
        
        # Add processing metadata
        metadata_lines.append("### Processing Information")
        metadata_lines.extend([
            f"- **Input File:** {ocr_results.get('input_path', 'Unknown')}",
            f"- **Processing Timestamp:** {ocr_results.get('timestamp', 'Unknown')}",
            f"- **Processing Time:** {ocr_results.get('processing_time', 0):.2f} seconds",
            ""
        ])
        
        # Add image metadata
        if 'metadata' in ocr_results:
            img_meta = ocr_results['metadata']
            metadata_lines.append("### Image Properties")
            metadata_lines.extend([
                f"- **Image Size:** {img_meta.get('image_size', 'Unknown')}",
                f"- **Image Mode:** {img_meta.get('image_mode', 'Unknown')}",
                f"- **Tesseract Config:** {img_meta.get('tesseract_config', 'Unknown')}",
                f"- **Languages Used:** {', '.join(img_meta.get('languages_used', []))}",
                f"- **PSM Mode:** {img_meta.get('psm_mode', 'Unknown')}",
                f"- **OEM Mode:** {img_meta.get('oem_mode', 'Unknown')}",
                ""
            ])
        
        # Add configuration metadata
        metadata_lines.append("### Configuration")
        metadata_lines.extend([
            f"- **Layout Preservation:** {self.preserve_layout}",
            f"- **Confidence Threshold:** {self.confidence_threshold}",
            f"- **Include Metadata:** {self.include_metadata}",
            f"- **Include Statistics:** {self.include_statistics}",
            ""
        ])
        
        return '\n'.join(metadata_lines)
    
    def _add_statistics_section(self, ocr_results: Dict[str, Any]) -> str:
        """Add statistics and analysis section."""
        stats_lines = [
            "## Statistics",
            ""
        ]
        
        # Add processing statistics
        if 'statistics' in ocr_results:
            stats = ocr_results['statistics']
            stats_lines.append("### Text Statistics")
            stats_lines.extend([
                f"- **Total Words:** {stats.get('total_words', 0)}",
                f"- **Total Lines:** {stats.get('total_lines', 0)}",
                f"- **Average Confidence:** {stats.get('average_confidence', 0):.1f}%",
                f"- **High Confidence Words:** {stats.get('high_confidence_words', 0)}",
                f"- **Low Confidence Words:** {stats.get('low_confidence_words', 0)}",
                ""
            ])
        
        # Add block statistics
        if 'text_blocks' in ocr_results:
            blocks = ocr_results['text_blocks']
            stats_lines.append("### Layout Statistics")
            stats_lines.extend([
                f"- **Total Text Blocks:** {len(blocks)}",
                f"- **Unique Lines:** {len(set(block['line_number'] for block in blocks))}",
                f"- **Unique Blocks:** {len(set(block['block_number'] for block in blocks))}",
                f"- **Unique Paragraphs:** {len(set(block['paragraph_number'] for block in blocks))}",
                ""
            ])
        
        # Add quality assessment
        stats_lines.append("### Quality Assessment")
        if 'confidence_scores' in ocr_results:
            conf_scores = ocr_results['confidence_scores']
            avg_conf = conf_scores.get('average_confidence', 0)
            if avg_conf >= 90:
                quality_grade = "Excellent"
            elif avg_conf >= 75:
                quality_grade = "Good"
            elif avg_conf >= 50:
                quality_grade = "Fair"
            else:
                quality_grade = "Poor"
            
            stats_lines.extend([
                f"- **Overall Quality:** {quality_grade}",
                f"- **Average Confidence:** {avg_conf:.1f}%",
                f"- **High Confidence Words:** {conf_scores.get('high_confidence_count', 0)}",
                f"- **Low Confidence Words:** {conf_scores.get('low_confidence_count', 0)}",
                ""
            ])
        
        return '\n'.join(stats_lines)
    
    def _add_confidence_analysis(self, confidence_results: Dict[str, Any]) -> str:
        """Add confidence analysis section."""
        analysis_lines = [
            "## Confidence Analysis",
            ""
        ]
        
        # Overall confidence analysis
        avg_conf = confidence_results.get('average_confidence', 0)
        analysis_lines.append("### Overall Confidence")
        analysis_lines.extend([
            f"- **Average Confidence:** {avg_conf:.1f}%",
            f"- **Confidence Threshold:** {confidence_results.get('confidence_threshold', 0)}",
            f"- **Words Above Threshold:** {confidence_results.get('high_confidence_count', 0)}",
            f"- **Words Below Threshold:** {confidence_results.get('low_confidence_count', 0)}",
            ""
        ])
        
        # Confidence distribution
        confidences = confidence_results.get('confidences', [])
        if confidences:
            high_conf = sum(1 for c in confidences if c >= 90)
            med_conf = sum(1 for c in confidences if 75 <= c < 90)
            low_conf = sum(1 for c in confidences if 50 <= c < 75)
            very_low_conf = sum(1 for c in confidences if c < 50)
            
            analysis_lines.append("### Confidence Distribution")
            analysis_lines.extend([
                f"- **High Confidence (90-100%):** {high_conf} words",
                f"- **Medium Confidence (75-89%):** {med_conf} words",
                f"- **Low Confidence (50-74%):** {low_conf} words",
                f"- **Very Low Confidence (<50%):** {very_low_conf} words",
                ""
            ])
        
        # Recommendations
        analysis_lines.append("### Recommendations")
        if avg_conf < 75:
            analysis_lines.extend([
                "- Consider preprocessing the image for better quality",
                "- Try different Tesseract configuration settings",
                "- Check if image resolution is adequate",
                ""
            ])
        elif avg_conf < 90:
            analysis_lines.extend([
                "- Good overall quality, minor improvements possible",
                "- Consider adjusting confidence threshold if needed",
                ""
            ])
        else:
            analysis_lines.extend([
                "- Excellent quality extraction",
                "- No immediate improvements needed",
                ""
            ])
        
        return '\n'.join(analysis_lines)
    
    def detect_tables(self, text_blocks: List[Dict]) -> List[Dict]:
        """Detect table structures in text blocks."""
        tables = []
        
        # Simple table detection based on alignment patterns
        # This is a basic implementation - in production, you'd want more sophisticated detection
        for i in range(len(text_blocks) - 2):
            # Check if we have a potential table row (aligned text blocks)
            if self._is_potential_table_row(text_blocks[i:i+3]):
                table_row = {
                    'type': 'table_row',
                    'blocks': text_blocks[i:i+3],
                    'confidence': self._calculate_row_confidence(text_blocks[i:i+3])
                }
                tables.append(table_row)
        
        return tables
    
    def _is_potential_table_row(self, blocks: List[Dict]) -> bool:
        """Check if blocks form a potential table row."""
        if len(blocks) < 2:
            return False
        
        # Check if blocks are roughly aligned (similar y-coordinates)
        y_coords = [block['y'] for block in blocks]
        y_variation = max(y_coords) - min(y_coords)
        
        # Check if blocks have reasonable spacing
        x_coords = [block['x'] for block in blocks]
        x_spacing = [x_coords[i+1] - x_coords[i] for i in range(len(x_coords)-1)]
        
        # Simple heuristic: low y variation and consistent x spacing
        return y_variation < 20 and all(spacing > 10 for spacing in x_spacing)
    
    def _calculate_row_confidence(self, blocks: List[Dict]) -> float:
        """Calculate confidence for a table row."""
        if not blocks:
            return 0.0
        
        avg_confidence = sum(block['confidence'] for block in blocks) / len(blocks)
        return avg_confidence
    
    def create_markdown_table(self, table_data: List[List[str]]) -> str:
        """Create markdown table from table data."""
        if not table_data:
            return ""
        
        # Calculate column widths
        col_widths = [max(len(str(row[i])) for row in table_data) for i in range(len(table_data[0]))]
        
        # Build table
        table_lines = []
        
        # Header
        header = " | ".join(str(table_data[0][i]).ljust(col_widths[i]) for i in range(len(table_data[0])))
        table_lines.append(header)
        
        # Separator
        separator = " | ".join("-" * col_widths[i] for i in range(len(table_data[0])))
        table_lines.append(separator)
        
        # Data rows
        for row in table_data[1:]:
            data_row = " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))
            table_lines.append(data_row)
        
        return '\n'.join(table_lines)
    
    def format_multicolumn_content(self, columns: List[List[Dict]]) -> str:
        """Format multicolumn content in markdown."""
        if not columns:
            return ""
        
        # Simple multicolumn formatting using HTML tables
        # In production, you might want more sophisticated layout preservation
        result = []
        result.append("<div style='display: flex;'>")
        
        for i, column in enumerate(columns):
            result.append(f"<div style='flex: 1; margin: 0 10px;'>")
            
            for block in column:
                result.append(block['text'])
            
            result.append("</div>")
        
        result.append("</div>")
        
        return '\n'.join(result)
    
    def get_formatting_info(self) -> Dict[str, Any]:
        """Get current formatting configuration."""
        return {
            'preserve_layout': self.preserve_layout,
            'include_metadata': self.include_metadata,
            'include_statistics': self.include_statistics,
            'confidence_threshold': self.confidence_threshold,
            'table_detection_threshold': self.table_detection_threshold,
            'column_detection_threshold': self.column_detection_threshold,
            'heading_detection_threshold': self.heading_detection_threshold,
            'max_line_length': self.max_line_length,
            'paragraph_spacing': self.paragraph_spacing,
            'table_alignment': self.table_alignment
        }
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """Update formatting configuration."""
        self.config.update(config)
        
        # Update settings
        formatting_config = config.get('formatting', {})
        self.preserve_layout = formatting_config.get('preserve_layout', self.preserve_layout)
        self.include_metadata = formatting_config.get('include_metadata', self.include_metadata)
        self.include_statistics = formatting_config.get('include_statistics', self.include_statistics)
        self.confidence_threshold = formatting_config.get('confidence_threshold', self.confidence_threshold)
        
        # Update detection thresholds
        self.table_detection_threshold = formatting_config.get('table_detection_threshold', self.table_detection_threshold)
        self.column_detection_threshold = formatting_config.get('column_detection_threshold', self.column_detection_threshold)
        self.heading_detection_threshold = formatting_config.get('heading_detection_threshold', self.heading_detection_threshold)
        
        # Update formatting settings
        self.max_line_length = formatting_config.get('max_line_length', self.max_line_length)
        self.paragraph_spacing = formatting_config.get('paragraph_spacing', self.paragraph_spacing)
        self.table_alignment = formatting_config.get('table_alignment', self.table_alignment)