#!/usr/bin/env python3
"""
Enhanced PNG to Markdown converter with better formatting preservation
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
    Format text data with better layout preservation.
    
    Args:
        text_data: List of (bbox, text, confidence) tuples from EasyOCR
    
    Returns:
        str: Formatted text with preserved layout
    """
    if not text_data:
        return ""
    
    # Sort by y-coordinate (top to bottom) then x-coordinate (left to right)
    sorted_data = sorted(text_data, key=lambda x: (x[0][1], x[0][0]))
    
    formatted_lines = []
    current_line = []
    current_y = None
    line_threshold = 20  # Pixels to consider as same line
    
    for bbox, text, confidence in sorted_data:
        if not text.strip():
            continue
            
        y = bbox[1]  # Top y-coordinate
        
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

def detect_document_structure(text_data):
    """
    Detect document structure like headings, sections, etc.
    
    Args:
        text_data: List of (bbox, text, confidence) tuples
    
    Returns:
        dict: Document structure information
    """
    structure = {
        'headings': [],
        'paragraphs': [],
        'lists': [],
        'tables': []
    }
    
    # Simple heuristics for structure detection
    for bbox, text, confidence in text_data:
        if not text.strip():
            continue
            
        # Check if it might be a heading (short, high confidence, at top)
        if len(text) < 50 and confidence > 0.7 and bbox[0][1] < 200:  # Top portion of image
            structure['headings'].append(text)
        elif len(text) > 10:  # Longer text likely paragraphs
            structure['paragraphs'].append(text)
    
    return structure

def convert_image_to_markdown(image_path: str, output_path: str = None) -> str:
    """
    Convert image to markdown format with better formatting preservation.
    
    Args:
        image_path: Path to the input image
        output_path: Path to save the markdown file (optional)
    
    Returns:
        str: Extracted text in markdown format with preserved structure
    """
    try:
        print(f"Starting enhanced conversion of {image_path}")
        
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
        
        # Calculate statistics
        total_words = sum(len(text.split()) for _, text, _ in text_data if text.strip())
        total_lines = len([t for t in text_data if t[1].strip()])
        confidence_scores = [conf for _, _, conf in text_data if conf > 0]  # All valid confidence scores
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Format text with better layout preservation
        formatted_text = format_text_with_layout(text_data)
        
        # Detect document structure
        structure = detect_document_structure(text_data)
        
        # Create enhanced markdown content
        markdown_content = f"""# A.0 Mybizz System

## Document Information
- **Source File**: {os.path.basename(image_path)}
- **Path**: {image_path}
- **Processing Time**: {processing_time:.2f} seconds
- **Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S')}
- **Total Words**: {total_words}
- **Total Lines**: {total_lines}
- **Average Confidence**: {avg_confidence:.2f}

---

## Extracted Content

{formatted_text}

---

## Document Structure Detected

### Headings
{chr(10).join(f"## {heading}" for heading in structure['headings'])}

### Content
{chr(10).join(f"{paragraph}" for paragraph in structure['paragraphs'])}

---

## Processing Details

### Image Metadata
- **Image Size**: {image.size}
- **Image Mode**: {image.mode}

### OCR Statistics
- **Total Text Elements**: {len(text_data)}
- **High Confidence Elements**: {sum(1 for _, _, conf in text_data if conf > 0.7)}
- **Medium Confidence Elements**: {sum(1 for _, _, conf in text_data if 0.4 <= conf <= 0.7)}
- **Low Confidence Elements**: {sum(1 for _, _, conf in text_data if conf < 0.4)}

### Confidence Distribution
- **High Confidence (>70%)**: {sum(1 for _, _, conf in text_data if conf > 0.7)}
- **Medium Confidence (40-70%)**: {sum(1 for _, _, conf in text_data if 0.4 <= conf <= 0.7)}
- **Low Confidence (<40%)**: {sum(1 for _, _, conf in text_data if conf < 0.4)}

---

*Generated by Enhanced EasyOCR Converter*
*Processing completed on {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        # Save to file if output path is provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"Enhanced markdown file saved to {output_path}")
        
        return markdown_content
        
    except Exception as e:
        print(f"Enhanced conversion failed: {e}")
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
    
    print(f"Enhanced conversion of {source_file} to markdown...")
    print(f"Output will be saved to: {output_file}")
    
    # Perform enhanced conversion
    result = convert_image_to_markdown(source_file, output_file)
    
    if result.startswith("Error:"):
        print(f"Conversion failed: {result}")
    else:
        print("Enhanced conversion completed successfully!")
        print(f"Markdown file saved to: {output_file}")
        
        # Show first few lines of result
        lines = result.split('\n')
        print("\nFirst few lines of converted content:")
        print('-' * 50)
        for line in lines[:15]:
            print(line)
        print('-' * 50)

if __name__ == "__main__":
    main()