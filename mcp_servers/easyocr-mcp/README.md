# EasyOCR MCP Server

A Model Context Protocol (MCP) server for EasyOCR optimized for low-resource usage on Asus x515ae laptops.

## Features

- **Low-Resource Optimized**: Specifically configured for Asus x515ae with limited resources
- **English Language Only**: Uses only English language models to reduce memory footprint
- **GPU Disabled**: CPU-only processing for better compatibility
- **Custom Model Storage**: Models stored in `C:/easyocr_models` for better organization
- **Image Preprocessing**: Automatic resizing to 1024px, grayscale conversion, and binarization
- **Batch Processing**: Efficient batch processing with configurable batch sizes
- **Model Preloading**: Avoids repeated loading delays with model preloading
- **Confidence Thresholds**: Configurable confidence score thresholds for better accuracy
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **MCP Protocol**: Full MCP protocol integration for seamless integration with MCP clients

## Configuration

The server is configured with the following low-resource optimizations:

### EasyOCR Settings
- **Languages**: `['en']` (English only)
- **GPU**: `false` (CPU processing)
- **Model Storage Directory**: `C:/easyocr_models`
- **Confidence Threshold**: `30` (balanced accuracy/speed)

### Image Preprocessing
- **Max Image Size**: `1024px` (reduces memory usage)
- **Grayscale Conversion**: `true` (reduces processing complexity)
- **Binarization**: `true` (improves text clarity)
- **Contrast Enhancement**: `true` (better OCR accuracy)

### Batch Processing
- **Batch Size**: `5` (optimal for low-resource systems)
- **Timeout**: `30` seconds
- **Retry Count**: `3` (for robust processing)

### Performance Optimizations
- **Model Preloading**: Enabled to avoid loading delays
- **Memory Limit**: `512MB` (prevents excessive memory usage)
- **CPU Optimization**: Enabled for better performance
- **Thread Pool Size**: `2` (conservative for low-resource systems)

## Installation

1. Clone or download the EasyOCR MCP server
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure EasyOCR models are downloaded (automatic on first run)

## Usage

### Starting the Server

```bash
python main.py
```

### Command Line Options

```bash
python main.py --help
```

Available options:
- `--config, -c`: Path to configuration file (default: config/easyocr_mcp_config.json)
- `--log-level, -l`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--validate`: Validate configuration and exit
- `--info`: Display server information and exit

### Validation

```bash
python main.py --validate
```

### Server Information

```bash
python main.py --info
```

## MCP Tools

The server provides the following MCP tools:

### 1. extract_text_from_image
Extract text from a single image file.

**Parameters:**
- `image_path` (string): Path to the image file

**Returns:**
- OCR results with metadata including text, confidence scores, and processing statistics

### 2. extract_text_from_batch
Extract text from multiple images in batch.

**Parameters:**
- `image_paths` (array): List of image file paths

**Returns:**
- Batch OCR results with comprehensive statistics

### 3. extract_text_from_base64
Extract text from a base64 encoded image.

**Parameters:**
- `base64_image` (string): Base64 encoded image string
- `image_format` (string): Image format (png, jpg, jpeg, etc.)

**Returns:**
- OCR results with metadata

### 4. get_available_languages
Get list of available OCR languages.

**Returns:**
- Array of available language codes

### 5. validate_ocr_installation
Validate OCR installation and dependencies.

**Returns:**
- Validation results with processor information

### 6. get_processor_info
Get processor information and configuration.

**Returns:**
- Detailed processor information including configuration settings

## Configuration File

The main configuration file is located at `config/easyocr_mcp_config.json`. You can modify settings to suit your specific needs:

```json
{
  "easyocr": {
    "languages": ["en"],
    "gpu": false,
    "model_storage_directory": "C:/easyocr_models",
    "confidence_threshold": 30
  },
  "preprocessing": {
    "max_image_size": 1024,
    "use_grayscale": true,
    "use_binarization": true
  },
  "batch": {
    "size": 5,
    "timeout": 30
  }
}
```

## Performance Optimizations

### Memory Management
- Model preloading reduces memory overhead
- Configurable memory limits prevent excessive usage
- Efficient image preprocessing reduces memory footprint

### CPU Optimization
- GPU disabled for better CPU utilization
- Conservative thread pool size for low-resource systems
- Optimized batch processing for better throughput

### Model Management
- Custom model storage directory for better organization
- Automatic model downloading and caching
- Language-specific model loading reduces memory usage

## Logging

The server provides comprehensive logging:

- **File Logging**: Logs written to `easyocr_mcp.log`
- **Console Logging**: Real-time logging output
- **Configurable Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Performance Metrics**: Processing time, memory usage, error tracking

## Troubleshooting

### Common Issues

1. **Model Download Issues**
   - Ensure internet connection is available
   - Check model storage directory permissions
   - Verify disk space availability

2. **Memory Issues**
   - Reduce batch size in configuration
   - Disable image preprocessing if needed
   - Monitor system memory usage

3. **Performance Issues**
   - Adjust confidence threshold for better accuracy/speed balance
   - Enable/disable grayscale conversion based on needs
   - Optimize batch size for your system

### Debug Mode

Enable debug logging for troubleshooting:

```bash
python main.py --log-level DEBUG
```

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Support

For support and questions, please open an issue in the project repository.