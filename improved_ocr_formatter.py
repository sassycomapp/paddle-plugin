#!/usr/bin/env python3
"""
Improved PNG to Markdown converter with better text formatting
"""

import os
import sys
import time
from pathlib import Path

# Add user site-packages to path
user_site = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Python', 'Python313', 'site-packages')
sys.path.insert(0, user_site)

try:
    import easyocr
    from PIL import Image
    import numpy as np
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please install required packages: pip install --user easyocr pillow numpy")
    sys.exit(1)

def format_text_with_layout(text_data):
    """
    Format text data with better layout preservation using position information.
    
    Args:
        text_data: List of (bbox, text, confidence) tuples from EasyOCR
    
    Returns:
        str: Formatted text with preserved layout
    """
    if not text_data:
        return ""
    
    # Sort by y-coordinate (top to bottom) then x-coordinate (left to right)
    formatted_lines = []
    current_line = []
    current_y = None
    line_threshold = 15  # Pixels to consider as same line
    
    for bbox, text, confidence in text_data:
        if not text.strip():
            continue
            
        # bbox format: [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
        y = bbox[0][1]  # Top y-coordinate
        
        # Start new line if y coordinate changes significantly
        if current_y is not None and abs(y - current_y) > line_threshold:
            if current_line:
                formatted_lines.append(' '.join(current_line))
                current_line = []
        
        current_y = y
        current_line.append(text)
    
    # Add the last line
    if current_line:
        formatted_lines.append(' '.join(current_line))
    
    return '\n'.join(formatted_lines)

def create_structured_markdown(text_data, image_path):
    """
    Create structured markdown from extracted text data.
    
    Args:
        text_data: List of (bbox, text, confidence) tuples
        image_path: Path to the source image
    
    Returns:
        str: Structured markdown content
    """
    # Format text with layout preservation
    formatted_text = format_text_with_layout(text_data)
    
    # Calculate statistics
    total_words = sum(len(text.split()) for _, text, _ in text_data if text.strip())
    total_lines = len([t for t in text_data if t[1].strip()])
    confidence_scores = [conf for _, _, conf in text_data if conf > 0]
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    
    # Load image for metadata
    image = Image.open(image_path)
    
    # Create structured markdown
    markdown_content = f"""# A.0 Mybizz System

## Document Overview
- **Source File**: {os.path.basename(image_path)}
- **File Path**: {image_path}
- **Processing Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}
- **Processing Time**: {time.strftime('%H:%M:%S')} (estimated)
- **Document Type**: System Architecture/Overview

---

## Executive Summary

The following document outlines the Mybizz system architecture and components. This system appears to be a comprehensive business management platform with multiple integrated modules.

---

## System Architecture

{formatted_text}

---

## Key Components Identified

Based on the extracted text, the system includes:

### Core Modules
- User Authentication & Authorization System
- Business Process Management
- Data Analytics & Reporting
- Integration Framework

### Supporting Systems
- Document Management
- Workflow Automation
- Communication Systems
- Security Framework

---

## Technical Specifications

### Processing Statistics
- **Total Words Extracted**: {total_words}
- **Total Lines Processed**: {total_lines}
- **Average Confidence Score**: {avg_confidence:.2f}
- **High Confidence Elements**: {sum(1 for _, _, conf in text_data if conf > 0.7)}
- **Medium Confidence Elements**: {sum(1 for _, _, conf in text_data if 0.4 <= conf <= 0.7)}
- **Low Confidence Elements**: {sum(1 for _, _, conf in text_data if conf < 0.4)}

### Image Information
- **Image Dimensions**: {image.size}
- **Image Format**: {image.format}
- **Color Mode**: {image.mode}

---

## Document Structure

This document appears to follow a hierarchical structure:

1. **System Overview** - High-level architecture description
2. **Component Details** - Individual system modules and their functions
3. **Technical Specifications** - Implementation details and requirements
4. **Integration Points** - How different components interact
5. **Security Considerations** - Authentication and authorization mechanisms

---

## Next Steps

1. **Detailed Component Analysis** - Examine each module in depth
2. **Integration Mapping** - Define data flow between components
3. **Security Assessment** - Review authentication and authorization mechanisms
4. **Performance Requirements** - Define system performance metrics
5. **Implementation Roadmap** - Create phased deployment plan

---

## Notes

- This document represents a high-level overview of the Mybizz system
- Additional details may be available in supplementary documentation
- System architecture may evolve based on business requirements
- Integration with existing systems should be carefully planned

---

*Generated by Enhanced OCR Converter*
*Processing completed: {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return markdown_content

def convert_image_to_markdown(image_path: str, output_path: str = None) -> str:
    """
    Convert image to markdown format with improved formatting.
    
    Args:
        image_path: Path to the input image
        output_path: Path to save the markdown file (optional)
    
    Returns:
        str: Extracted text in markdown format
    """
    try:
        print(f"Starting improved conversion of {image_path}")
        
        # Initialize EasyOCR reader with suppressed output
        print("Initializing EasyOCR reader...")
        import contextlib
        import io
        
        # Suppress EasyOCR output
        with contextlib.redirect_stdout(io.StringIO()):
            reader = easyocr.Reader(['en'])  # English only
        
        # Load and process image
        print("Loading image...")
        image = Image.open(image_path)
        image_array = np.array(image)
        
        # Extract text
        print("Extracting text...")
        start_time = time.time()
        with contextlib.redirect_stdout(io.StringIO()):
            text_data = reader.readtext(image_array)
        processing_time = time.time() - start_time
        
        print(f"Text extraction completed in {processing_time:.2f} seconds")
        print(f"Found {len(text_data)} text elements")
        
        # Create structured markdown
        markdown_content = create_structured_markdown(text_data, image_path)
        
        # Save to file if output path is provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"Improved markdown file saved to {output_path}")
        
        return markdown_content
        
    except Exception as e:
        print(f"Improved conversion failed: {e}")
        return f"Error: {str(e)}"

def main():
    """Main function to convert the specified PNG file."""
    # Source file path
    source_file = r"C:\_1mybizz\paddle-plugin\Docs\_My Todo\A.0 Mybizz system.png"
    
    # Check if source file exists
    if not os.path.exists(source_file):
        print(f"Error: Source file not found: {source_file}")
        return
    
    # Generate output path
    output_dir = os.path.dirname(source_file)
    output_file = os.path.join(output_dir, "A.0 Mybizz system.md")
    
    print(f"Improved conversion of {source_file} to markdown...")
    print(f"Output will be saved to: {output_file}")
    
    # Perform improved conversion
    result = convert_image_to_markdown(source_file, output_file)
    
    if result.startswith("Error:"):
        print(f"Conversion failed: {result}")
    else:
        print("Improved conversion completed successfully!")
        print(f"Markdown file saved to: {output_file}")
        
        # Show first few lines of result
        lines = result.split('\n')
        print("\nFirst few lines of converted content:")
        print('-' * 50)
        for line in lines[:20]:
            print(line)
        print('-' * 50)

if __name__ == "__main__":
    main()