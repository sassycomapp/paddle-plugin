#!/usr/bin/env python3
"""
OCR Results to Markdown Converter

This script converts OCR JSON results to a comprehensive markdown file
with professional formatting, statistics, and organized presentation.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List
import re


class OCRMarkdownConverter:
    """
    Converts OCR JSON results to professional markdown format.
    """
    
    def __init__(self, json_file_path: str):
        """
        Initialize the converter with OCR JSON data.
        
        Args:
            json_file_path (str): Path to the OCR results JSON file
        """
        self.json_file_path = json_file_path
        self.ocr_data = None
        self.target_image_dir = None
        self.target_image_filename = None
        
    def load_ocr_data(self) -> bool:
        """
        Load OCR data from JSON file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                self.ocr_data = json.load(f)
            
            # Extract target image information
            target_image = self.ocr_data.get('target_image', '')
            if target_image:
                self.target_image_dir = os.path.dirname(target_image)
                self.target_image_filename = os.path.basename(target_image)
            
            return True
            
        except Exception as e:
            print(f"Error loading OCR data: {e}")
            return False
    
    def generate_markdown_content(self) -> str:
        """
        Generate comprehensive markdown content from OCR data.
        
        Returns:
            str: Complete markdown content
        """
        if not self.ocr_data:
            return "# Error: OCR data not loaded"
        
        # Get current timestamp
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Build markdown content
        markdown_content = []
        
        # Header section
        markdown_content.append(self._generate_header_section(current_time))
        
        # Summary statistics
        markdown_content.append(self._generate_summary_statistics())
        
        # Extracted text by confidence levels
        markdown_content.append(self._generate_confidence_organized_text())
        
        # Raw data section
        markdown_content.append(self._generate_raw_data_section())
        
        # Processing information
        markdown_content.append(self._generate_processing_info())
        
        return '\n'.join(markdown_content)
    
    def _generate_header_section(self, current_time: str) -> str:
        """Generate the header section with metadata."""
        content = []
        content.append("# MyBizz System OCR Results")
        content.append("")
        content.append("## Processing Information")
        content.append("")
        content.append(f"- **Processing Date**: {current_time}")
        content.append(f"- **Source File**: `{self.ocr_data.get('target_image', 'Unknown')}`")
        content.append(f"- **OCR Engine**: Tesseract OCR")
        content.append(f"- **Total Text Blocks**: {self.ocr_data.get('total_blocks', 0)}")
        content.append(f"- **High Confidence Blocks**: {self.ocr_data.get('high_confidence_blocks', 0)}")
        content.append("")
        content.append("---")
        content.append("")
        return '\n'.join(content)
    
    def _generate_summary_statistics(self) -> str:
        """Generate summary statistics section."""
        content = []
        content.append("## Summary Statistics")
        content.append("")
        
        # Basic statistics
        total_blocks = self.ocr_data.get('total_blocks', 0)
        high_conf_blocks = self.ocr_data.get('high_confidence_blocks', 0)
        avg_confidence = self.ocr_data.get('average_confidence', 0)
        
        content.append("### Key Metrics")
        content.append("")
        content.append(f"| Metric | Value |")
        content.append(f"|--------|-------|")
        content.append(f"| **Total Text Blocks** | {total_blocks} |")
        content.append(f"| **High Confidence Blocks** | {high_conf_blocks} |")
        content.append(f"| **Average Confidence** | {avg_confidence:.2f}% |")
        content.append(f"| **High Confidence Rate** | {(high_conf_blocks/total_blocks*100):.1f}% |")
        content.append("")
        
        # Confidence distribution
        content.append("### Confidence Distribution")
        content.append("")
        
        confidence_results = self.ocr_data.get('confidence_results', [])
        if confidence_results:
            high_conf = len([r for r in confidence_results if r.get('confidence', 0) >= 80])
            medium_conf = len([r for r in confidence_results if 50 <= r.get('confidence', 0) < 80])
            low_conf = len([r for r in confidence_results if r.get('confidence', 0) < 50])
            
            content.append(f"| Confidence Level | Count | Percentage |")
            content.append(f"|------------------|-------|------------|")
            content.append(f"| **High (≥80%)** | {high_conf} | {(high_conf/total_blocks*100):.1f}% |")
            content.append(f"| **Medium (50-79%)** | {medium_conf} | {(medium_conf/total_blocks*100):.1f}% |")
            content.append(f"| **Low (<50%)** | {low_conf} | {(low_conf/total_blocks*100):.1f}% |")
            content.append("")
        
        # Text analysis
        content.append("### Text Analysis")
        content.append("")
        
        # Extract and analyze text
        all_text = ' '.join([r.get('text', '') for r in confidence_results])
        content.append(f"- **Total Characters**: {len(all_text)}")
        content.append(f"- **Unique Words**: {len(set(all_text.lower().split())) if all_text else 0}")
        content.append(f"- **Contains Numbers**: {any(c.isdigit() for c in all_text)}")
        content.append(f"- **Contains Special Characters**: {any(not c.isalnum() and not c.isspace() for c in all_text)}")
        content.append("")
        
        return '\n'.join(content)
    
    def _generate_confidence_organized_text(self) -> str:
        """Generate text organized by confidence levels."""
        content = []
        content.append("## Extracted Text by Confidence Level")
        content.append("")
        
        confidence_results = self.ocr_data.get('confidence_results', [])
        if not confidence_results:
            content.append("*No text results available*")
            content.append("")
            return '\n'.join(content)
        
        # Group by confidence levels
        high_conf_text = [r for r in confidence_results if r.get('confidence', 0) >= 80]
        medium_conf_text = [r for r in confidence_results if 50 <= r.get('confidence', 0) < 80]
        low_conf_text = [r for r in confidence_results if r.get('confidence', 0) < 50]
        
        # High confidence text
        if high_conf_text:
            content.append("### High Confidence Text (≥80%)")
            content.append("")
            content.append("```text")
            for i, result in enumerate(high_conf_text, 1):
                content.append(f"{i:3d}. {result.get('text', ''):<30} (Confidence: {result.get('confidence', 0):3.1f}%)")
            content.append("```")
            content.append("")
        
        # Medium confidence text
        if medium_conf_text:
            content.append("### Medium Confidence Text (50-79%)")
            content.append("")
            content.append("```text")
            for i, result in enumerate(medium_conf_text, 1):
                content.append(f"{i:3d}. {result.get('text', ''):<30} (Confidence: {result.get('confidence', 0):3.1f}%)")
            content.append("```")
            content.append("")
        
        # Low confidence text
        if low_conf_text:
            content.append("### Low Confidence Text (<50%)")
            content.append("")
            content.append("```text")
            for i, result in enumerate(low_conf_text, 1):
                content.append(f"{i:3d}. {result.get('text', ''):<30} (Confidence: {result.get('confidence', 0):3.1f}%)")
            content.append("```")
            content.append("")
        
        # Reconstructed text
        content.append("### Reconstructed Document Text")
        content.append("")
        content.append("```text")
        # Sort by confidence (highest first) and reconstruct
        sorted_results = sorted(confidence_results, key=lambda x: x.get('confidence', 0), reverse=True)
        for result in sorted_results:
            if result.get('text', '').strip():
                content.append(result.get('text', ''))
        content.append("```")
        content.append("")
        
        return '\n'.join(content)
    
    def _generate_raw_data_section(self) -> str:
        """Generate raw data section with complete results."""
        content = []
        content.append("## Raw OCR Data")
        content.append("")
        content.append("### Complete Results Table")
        content.append("")
        
        confidence_results = self.ocr_data.get('confidence_results', [])
        if confidence_results:
            content.append("| # | Text | Confidence Level | Status |")
            content.append("|---|------|------------------|--------|")
            
            for i, result in enumerate(confidence_results, 1):
                text = result.get('text', '')
                confidence = result.get('confidence', 0)
                
                # Determine status and confidence level
                if confidence >= 80:
                    status = "✅ High"
                    conf_level = "High"
                elif confidence >= 50:
                    status = "⚠️ Medium"
                    conf_level = "Medium"
                else:
                    status = "❌ Low"
                    conf_level = "Low"
                
                # Escape pipe characters in text
                text = text.replace('|', '\\|')
                content.append(f"| {i} | {text} | {conf_level} ({confidence:.1f}%) | {status} |")
            
            content.append("")
        
        # JSON data preview
        content.append("### JSON Data Structure")
        content.append("")
        content.append("```json")
        # Create a simplified version for display
        simplified_data = {
            "timestamp": self.ocr_data.get('timestamp'),
            "target_image": self.ocr_data.get('target_image'),
            "total_blocks": self.ocr_data.get('total_blocks'),
            "average_confidence": self.ocr_data.get('average_confidence'),
            "high_confidence_blocks": self.ocr_data.get('high_confidence_blocks'),
            "confidence_results_count": len(confidence_results)
        }
        content.append(json.dumps(simplified_data, indent=2))
        content.append("```")
        content.append("")
        
        return '\n'.join(content)
    
    def _generate_processing_info(self) -> str:
        """Generate processing information section."""
        content = []
        content.append("## Processing Information")
        content.append("")
        
        # Timestamps
        content.append("### Timestamps")
        content.append("")
        content.append(f"- **Original Processing Time**: {self.ocr_data.get('timestamp', 'Unknown')}")
        content.append(f"- **Markdown Generation**: {datetime.now().isoformat()}")
        content.append("")
        
        # File information
        content.append("### File Information")
        content.append("")
        content.append(f"- **Source JSON File**: `{self.json_file_path}`")
        content.append(f"- **Target Image Directory**: `{self.target_image_dir or 'Unknown'}`")
        content.append(f"- **Target Image Filename**: `{self.target_image_filename or 'Unknown'}`")
        content.append("")
        
        # OCR settings
        content.append("### OCR Settings")
        content.append("")
        content.append("- **Engine**: Tesseract OCR")
        content.append("- **Language**: English (eng)")
        content.append("- **Output Format**: Detailed with confidence scores")
        content.append("- **Processing**: Full text extraction with confidence analysis")
        content.append("")
        
        # Quality assessment
        content.append("### Quality Assessment")
        content.append("")
        avg_confidence = self.ocr_data.get('average_confidence', 0)
        total_blocks = self.ocr_data.get('total_blocks', 0)
        
        if avg_confidence >= 85:
            quality_rating = "Excellent"
        elif avg_confidence >= 70:
            quality_rating = "Good"
        elif avg_confidence >= 50:
            quality_rating = "Fair"
        else:
            quality_rating = "Poor"
        
        content.append(f"- **Overall Quality Rating**: {quality_rating}")
        content.append(f"- **Confidence Score**: {avg_confidence:.2f}%")
        content.append(f"- **Text Completeness**: {total_blocks} blocks extracted")
        content.append("")
        
        # Recommendations
        content.append("### Recommendations")
        content.append("")
        if avg_confidence < 70:
            content.append("- Consider image preprocessing (noise reduction, contrast enhancement)")
            content.append("- Try different Tesseract configurations or page segmentation modes")
        if total_blocks < 10:
            content.append("- Low text volume detected; verify image contains readable text")
        content.append("- For critical applications, manually verify high-confidence results")
        content.append("")
        
        content.append("---")
        content.append("")
        content.append("*This markdown report was generated automatically from OCR JSON results.*")
        content.append(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return '\n'.join(content)
    
    def save_markdown_file(self, output_path: str) -> bool:
        """
        Save the generated markdown to a file.
        
        Args:
            output_path (str): Path to save the markdown file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Generate markdown content
            markdown_content = self.generate_markdown_content()
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save to file
            from utils.encoding_utils import safe_write_text
            safe_write_text(output_path, '', encoding='utf-8')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"SUCCESS: Markdown file saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"ERROR: Error saving markdown file: {e}")
            return False


def main():
    """
    Main function to convert OCR results to markdown.
    """
    print("=" * 60)
    print("OCR Results to Markdown Converter")
    print("=" * 60)
    
    # Input JSON file
    json_file = "ocr_results/test_results.json"
    
    # Output markdown file
    markdown_file = "Docs/_My Todo/A.0_Mybizz_system_OCR_Results.md"
    
    print(f"Input JSON: {json_file}")
    print(f"Output Markdown: {markdown_file}")
    print("=" * 60)
    
    # Initialize converter
    converter = OCRMarkdownConverter(json_file)
    
    # Load OCR data
    if not converter.load_ocr_data():
        print("❌ Failed to load OCR data")
        return 1
    
    # Save markdown file
    if not converter.save_markdown_file(markdown_file):
        print("❌ Failed to save markdown file")
        return 1
    
    print("\nConversion completed successfully!")
    print(f"Generated markdown file: {markdown_file}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())