# Tesseract OCR Configuration Documentation

## Overview

The `tesseract_config.py` script provides a comprehensive Tesseract OCR configuration class that enables robust text extraction from images with various configuration options, error handling, and output formatting.

## Features

- **Basic text extraction** from images
- **Text extraction with confidence scores** for quality assessment
- **Batch processing** of multiple images
- **Configuration options** for different languages and settings
- **Error handling and validation** for robust operation
- **Markdown output** for formatted results
- **Image preprocessing** for better OCR accuracy
- **Logging** for debugging and monitoring

## Installation

### Prerequisites

1. **Tesseract OCR**: Install Tesseract OCR from [https://github.com/tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract)
   - Windows: Download installer from UB Mannheim
   - macOS: `brew install tesseract`
   - Linux: `sudo apt-get install tesseract-ocr`

2. **Python Packages**:
   ```bash
   pip install pytesseract pillow
   ```

### Configuration

Ensure Tesseract is installed and accessible. The default path is:
- Windows: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- macOS: `/usr/local/bin/tesseract`
- Linux: `/usr/bin/tesseract`

## Usage

### Basic Usage

```python
from tesseract_config import TesseractOCRConfig

# Initialize the OCR configuration
ocr_config = TesseractOCRConfig()

# Extract text from a single image
text = ocr_config.extract_text("path/to/image.png")
print(text)
```

### Advanced Usage

```python
from tesseract_config import TesseractOCRConfig

# Initialize with custom configuration
config = {
    'languages': ['eng', 'fra'],  # Multiple languages
    'psm': 6,  # Page segmentation mode
    'confidence_threshold': 70,  # Minimum confidence score
    'preprocess': True,  # Enable image preprocessing
    'output_dir': './results'  # Output directory
}

ocr_config = TesseractOCRConfig(config=config)

# Extract text with confidence scores
result = ocr_config.extract_text_with_confidence("image.png")
print(f"Text: {result['text']}")
print(f"Average confidence: {result['average_confidence']:.2f}")

# Process multiple images
image_paths = ["image1.png", "image2.png", "image3.png"]
batch_result = ocr_config.batch_extract_text(image_paths)

# Save results to markdown
ocr_config.save_to_markdown(batch_result, "results.md", "Batch OCR Results")
```

## API Reference

### TesseractOCRConfig Class

#### Constructor

```python
TesseractOCRConfig(tesseract_path=None, config=None)
```

**Parameters:**
- `tesseract_path` (str, optional): Path to Tesseract executable
- `config` (dict, optional): Configuration dictionary

**Default Configuration:**
```python
{
    'languages': ['eng'],
    'psm': 3,  # Default page segmentation mode
    'config': '',
    'oem': 3,  # Default OCR engine mode
    'confidence_threshold': 0.0,
    'output_format': 'text',
    'batch_size': 10,
    'timeout': 30,
    'preprocess': True,
    'save_intermediate': False,
    'output_dir': './ocr_results'
}
```

#### Methods

##### `extract_text(image_path, **kwargs)`
Extract text from a single image.

**Parameters:**
- `image_path` (str): Path to the image file
- `**kwargs`: Additional configuration options

**Returns:**
- `str`: Extracted text

##### `extract_text_with_confidence(image_path, **kwargs)`
Extract text with confidence scores and bounding box information.

**Parameters:**
- `image_path` (str): Path to the image file
- `**kwargs`: Additional configuration options

**Returns:**
- `dict`: Dictionary containing:
  - `text`: Combined text
  - `detailed_results`: List of text segments with confidence and bounding boxes
  - `average_confidence`: Average confidence score

##### `batch_extract_text(image_paths, **kwargs)`
Extract text from multiple images in batch.

**Parameters:**
- `image_paths` (list): List of image file paths
- `**kwargs`: Additional configuration options

**Returns:**
- `dict`: Dictionary containing:
  - `results`: Individual results for each image
  - `errors`: List of errors encountered
  - `summary`: Summary statistics

##### `save_to_markdown(results, output_path, title)`
Save OCR results to markdown format.

**Parameters:**
- `results` (dict): OCR results dictionary
- `output_path` (str): Path to save the markdown file
- `title` (str): Title for the markdown document

##### `get_available_languages()`
Get list of available languages in Tesseract.

**Returns:**
- `list`: List of available language codes

##### `validate_image(image_path)`
Validate if an image file is suitable for OCR.

**Parameters:**
- `image_path` (str): Path to the image file

**Returns:**
- `bool`: True if valid, False otherwise

##### `update_config(new_config)`
Update configuration settings.

**Parameters:**
- `new_config` (dict): New configuration settings

## Configuration Options

### Page Segmentation Modes (PSM)
- `0`: Orientation and script detection (OSD) only
- `1`: Automatic page segmentation with OSD
- `2`: Automatic page segmentation, but no OSD or OCR
- `3`: Fully automatic page segmentation, but no OSD
- `4`: Assume a single column of text of variable sizes
- `5`: Assume a single uniform block of vertically aligned text
- `6`: Assume a single uniform block of text
- `7`: Treat the image as a single text line
- `8`: Treat the image as a single word
- `9`: Treat the image as a single word in a circle
- `10`: Treat the image as a single character
- `11`: Sparse text. Find as much text as possible in no particular order
- `12`: Sparse text with OSD
- `13`: Raw line. Treat the image as a single text line, bypassing hacks that are Tesseract-specific

### OCR Engine Modes (OEM)
- `0`: Legacy engine only
- `1`: Neural nets LSTM engine only
- `2`: Legacy + LSTM engines
- `3`: Default, based on what is available

### Supported Languages
Common language codes:
- `eng`: English
- `spa`: Spanish
- `fra`: French
- `deu`: German
- `ita`: Italian
- `por`: Portuguese
- `rus`: Russian
- `chi_sim`: Simplified Chinese
- `chi_tra`: Traditional Chinese
- `jpn`: Japanese
- `kor`: Korean

## Error Handling

The class includes comprehensive error handling for:
- Missing or invalid image files
- Tesseract installation issues
- Language data availability
- Image format compatibility
- Permission errors
- Configuration validation

## Examples

### Example 1: Basic Text Extraction

```python
from tesseract_config import TesseractOCRConfig

# Initialize OCR
ocr_config = TesseractOCRConfig()

# Extract text from image
text = ocr_config.extract_text("Docs/_My Todo/A.0 Mybizz system.png")
print("Extracted text:")
print(text)
```

### Example 2: Confidence-Based Extraction

```python
from tesseract_config import TesseractOCRConfig

# Initialize with confidence threshold
config = {'confidence_threshold': 70}
ocr_config = TesseractOCRConfig(config=config)

# Extract with confidence
result = ocr_config.extract_text_with_confidence("document.png")

print(f"Text: {result['text']}")
print(f"Confidence: {result['average_confidence']:.2f}")

# Print detailed results with high confidence
for item in result['detailed_results']:
    if item['confidence'] >= 80:
        print(f"High confidence text: '{item['text']}' (confidence: {item['confidence']})")
```

### Example 3: Batch Processing

```python
from tesseract_config import TesseractOCRConfig

# Initialize OCR
ocr_config = TesseractOCRConfig()

# List of images to process
image_paths = [
    "Docs/_My Todo/A.0 Mybizz system.png",
    "Docs/_My Todo/A.1. User Authentication & Authorization System.png",
    "other_document.png"
]

# Process batch
batch_result = ocr_config.batch_extract_text(image_paths)

# Print summary
print(f"Processed {batch_result['summary']['total']} images")
print(f"Success: {batch_result['summary']['success']}")
print(f"Failed: {batch_result['summary']['failed']}")

# Save results
ocr_config.save_to_markdown(batch_result, "batch_results.md", "Batch OCR Processing")
```

### Example 4: Multi-Language Processing

```python
from tesseract_config import TesseractOCRConfig

# Configure for multiple languages
config = {
    'languages': ['eng', 'spa', 'fra'],
    'psm': 6,  # Assume uniform block of text
    'preprocess': True
}

ocr_config = TesseractOCRConfig(config=config)

# Process multilingual document
text = ocr_config.extract_text("multilingual_document.png")
print(text)
```

## Testing

Run the included test script:

```bash
python tesseract_config.py
```

This will:
1. Test with the target image `Docs/_My Todo/A.0 Mybizz system.png`
2. Demonstrate basic text extraction
3. Show confidence-based extraction
4. Save results to markdown format
5. Display available languages

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'pytesseract'**
   - Install pytesseract: `pip install pytesseract`

2. **TesseractNotFoundError**
   - Ensure Tesseract is installed and the path is correct
   - Verify the tesseract executable is in your PATH

3. **Language data not found**
   - Install additional language packs for Tesseract
   - Check available languages with `ocr_config.get_available_languages()`

4. **Poor OCR results**
   - Enable image preprocessing: `config['preprocess'] = True`
   - Try different page segmentation modes
   - Ensure image quality is good (high resolution, clear text)

5. **Permission errors**
   - Check file permissions for input images and output directories
   - Ensure the output directory exists

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

ocr_config = TesseractOCRConfig()
```

## Performance Considerations

- **Batch processing**: Use batch processing for multiple images to improve performance
- **Image preprocessing**: Enable preprocessing for better accuracy with complex images
- **Language selection**: Use only necessary languages to improve speed
- **Page segmentation**: Choose appropriate PSM mode for your image type
- **Confidence threshold**: Set appropriate thresholds to filter low-quality results

## Integration

The TesseractOCRConfig class can be easily integrated into larger applications:

```python
class DocumentProcessor:
    def __init__(self):
        self.ocr_config = TesseractOCRConfig()
    
    def process_document(self, image_path):
        try:
            result = self.ocr_config.extract_text_with_confidence(image_path)
            return self._process_result(result)
        except Exception as e:
            self.logger.error(f"Document processing failed: {e}")
            return None
    
    def _process_result(self, ocr_result):
        # Custom processing logic
        processed_text = self._clean_text(ocr_result['text'])
        return {
            'text': processed_text,
            'confidence': ocr_result['average_confidence']
        }
```

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Support

For support and questions:
- Check the troubleshooting section
- Review the examples
- Enable debug logging for detailed error information
- Verify Tesseract installation and language data