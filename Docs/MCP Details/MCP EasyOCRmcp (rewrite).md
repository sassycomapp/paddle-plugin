# EasyOCR MCP Server Documentation

## Brief Overview
The EasyOCR MCP Server provides a comprehensive Model Context Protocol (MCP) server for optical character recognition (OCR) functionality, specifically optimized for low-resource usage on Asus x515ae laptops. It implements advanced text extraction from images with configurable preprocessing, batch processing, and integration with existing MCP infrastructure. The server now includes an enhanced formatter for improved document structure preservation and better Markdown output formatting.

## Tool list
- extract_text_from_image
- extract_text_from_batch
- extract_text_from_base64
- get_available_languages
- validate_ocr_installation
- get_processor_info
- format_text_with_layout
- create_structured_markdown

## Available Tools and Usage
### Tool 1: extract_text_from_image
**Description:** Extract text from a single image file with enhanced formatting.

**Parameters:**
- `image_path` (string): Path to the image file

**Returns:**
OCR results with metadata including text, confidence scores, processing statistics, and enhanced formatting

**Example:**
```javascript
// Example usage
result = await client.call_tool("extract_text_from_image", {
    "image_path": "/path/to/image.png"
});
console.log("Extracted text:", result.text);
console.log("Statistics:", result.statistics);
```

### Tool 2: extract_text_from_batch
**Description:** Extract text from multiple images in batch with enhanced formatting.

**Parameters:**
- `image_paths` (array): List of image file paths

**Returns:**
Batch OCR results with comprehensive statistics and enhanced formatting for each document

**Example:**
```javascript
// Example usage
result = await client.call_tool("extract_text_from_batch", {
    "image_paths": ["/path/to/image1.png", "/path/to/image2.png"]
});
console.log("Batch results:", result.results);
console.log("Batch statistics:", result.batch_statistics);
```

### Tool 3: extract_text_from_base64
**Description:** Extract text from a base64 encoded image with enhanced formatting.

**Parameters:**
- `base64_image` (string): Base64 encoded image string
- `image_format` (string): Image format (png, jpg, jpeg, etc.)

**Returns:**
OCR results with metadata and enhanced formatting

**Example:**
```javascript
// Example usage
result = await client.call_tool("extract_text_from_base64", {
    "base64_image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "image_format": "png"
});
```

### Tool 4: get_available_languages
**Description:** Get list of available OCR languages.

**Returns:**
Array of available language codes

**Example:**
```javascript
// Example usage
languages = await client.call_tool("get_available_languages");
console.log("Available languages:", languages);
```

### Tool 5: validate_ocr_installation
**Description:** Validate OCR installation and dependencies.

**Returns:**
Validation results with processor information and system status

**Example:**
```javascript
// Example usage
validation = await client.call_tool("validate_ocr_installation");
console.log("Validation status:", validation.valid);
console.log("Processor info:", validation.processor_info);
```

### Tool 6: get_processor_info
**Description:** Get processor information and configuration.

**Returns:**
Detailed processor information including configuration settings, performance optimizations, and system status

**Example:**
```javascript
// Example usage
info = await client.call_tool("get_processor_info");
console.log("Languages:", info.languages);
console.log("GPU enabled:", info.gpu_enabled);
console.log("Model directory:", info.model_storage_directory);
```

### Tool 7: format_text_with_layout
**Description:** Format extracted text with layout preservation (enhanced formatter).

**Parameters:**
- `text_data` (array): Raw OCR text data with position information
- `format_options` (object): Optional formatting preferences

**Returns:**
Formatted text with preserved layout and structure

**Example:**
```javascript
// Example usage
formatted_text = await client.call_tool("format_text_with_layout", {
    "text_data": raw_ocr_results,
    "format_options": {
        "line_threshold": 15,
        "preserve_structure": true
    }
});
```

### Tool 8: create_structured_markdown
**Description:** Create structured Markdown document from extracted text.

**Parameters:**
- `text_data` (array): Raw OCR text data
- `document_info` (object): Document metadata and context

**Returns:**
Structured Markdown document with proper formatting

**Example:**
```javascript
// Example usage
markdown_doc = await client.call_tool("create_structured_markdown", {
    "text_data": raw_ocr_results,
    "document_info": {
        "title": "My Document",
        "author": "John Doe",
        "date": "2025-01-01"
    }
});
```

## Installation Information
- **Installation Scripts**: `scripts/deploy/deploy_easyocr_service.py` (complete deployment)
- **Main Server**: `mcp_servers/easyocr-mcp/src/easyocr_mcp_server.py`
- **Dependencies**: Python 3.7+, EasyOCR>=1.7.0, MCP>=1.0.0, FastMCP>=0.1.0
- **Model Storage**: `C:/easyocr_models` (custom directory for better organization)
- **Status**: ✅ **INSTALLED** (verified by comprehensive test suite)

## Configuration
**Environment Configuration (.env):**
```bash
EASYOCR_MODEL_STORAGE=C:/easyocr_models
EASYOCR_CONFIDENCE_THRESHOLD=30
EASYOCR_MAX_IMAGE_SIZE=1024
EASYOCR_GPU_ENABLED=false
EASYOCR_BATCH_SIZE=5
EASYOCR_MEMORY_LIMIT=512MB
EASYOCR_THREAD_POOL_SIZE=2
```

**MCP Configuration (mcp.json):**
```json
{
  "mcpServers": {
    "easyocr": {
      "command": "python",
      "args": ["mcp_servers/easyocr-mcp/src/easyocr_mcp_server.py"],
      "env": {
        "EASYOCR_MODEL_STORAGE": "C:/easyocr_models",
        "EASYOCR_CONFIDENCE_THRESHOLD": "30",
        "EASYOCR_MAX_IMAGE_SIZE": "1024",
        "EASYOCR_GPU_ENABLED": "false",
        "EASYOCR_BATCH_SIZE": "5",
        "EASYOCR_MEMORY_LIMIT": "512MB",
        "EASYOCR_THREAD_POOL_SIZE": "2"
      }
    }
  }
}
```

## Integration
- **VS Code Extension**: Integration with VS Code through MCP protocol
- **Companion Systems**: Integration with KiloCode + AG2 orchestration environment, Cache MCP Server, Memory Bank Files
- **API Compatibility**: Compatible with MCP protocol standard, EasyOCR library interface

## How to Start and Operate this MCP
### Manual Start:
```bash
# Start the server directly
python mcp_servers/easyocr-mcp/src/easyocr_mcp_server.py

# With custom configuration
python mcp_servers/easyocr-mcp/src/easyocr_mcp_server.py --config config/easyocr_mcp_config.json
```

### Automated Start:
```bash
# Using deployment script
cd mcp_servers/easyocr-mcp
python scripts/deploy/deploy_easyocr_service.py

# As a Windows service
python scripts/startup/windows_service_installer.py install
net start EasyOCR-MCP-Server

# Using systemd (Linux)
sudo systemctl enable --now easyocr-mcp-server
```

### Service Management:
```bash
# Windows Service Management
net start EasyOCR-MCP-Server    # Start service
net stop EasyOCR-MCP-Server     # Stop service
sc query EasyOCR-MCP-Server     # Check status

# PowerShell Management
.\scripts\startup\EasyOCR-MCP-Management.ps1  # Interactive menu

# Linux Service Management
sudo systemctl start easyocr-mcp-server    # Start service
sudo systemctl stop easyocr-mcp-server     # Stop service
sudo systemctl status easyocr-mcp-server   # Check status
```

## Configuration Options
- **Core Configuration**: Languages, GPU settings, model storage directory, confidence threshold
- **Preprocessing**: Image resizing, grayscale conversion, binarization, contrast enhancement
- **Batch Processing**: Batch size, timeout, retry count
- **Performance**: Model preloading, memory limits, CPU optimization, thread pool size
- **Low-Resource Optimizations**: Memory management, CPU processing, image resizing, grayscale conversion, conservative threading

## Key Features
1. **Dynamic Text Extraction**: Extract text from single images, batches, or base64 encoded images
2. **Enhanced Formatting**: Superior document structure preservation and Markdown formatting
3. **Low-Resource Optimization**: Specifically optimized for Asus x515ae and similar low-resource systems
4. **Batch Processing**: Efficient handling of multiple images with comprehensive statistics
5. **Memory Management**: Configurable 512MB memory limit prevents excessive usage
6. **CPU Optimization**: Disabled GPU usage for better CPU utilization on low-resource systems

## Security Considerations
- **File Security**: Input validation for all image files, file size limits (100MB maximum), supported format validation, temporary file cleanup
- **Access Control**: Windows service runs with LocalSystem privileges, configurable authentication options, IP whitelisting support, rate limiting enabled
- **Data Protection**: No sensitive data logging, temporary file encryption option, secure model storage, configurable data retention

## Troubleshooting
- **Model Download Issues**: Check internet connection and model directory permissions, use `python main.py --validate`
- **Memory Issues**: Reduce batch size, disable preprocessing if needed, adjust `memory_limit` and `batch.size` in config
- **Performance Issues**: Enable CPU optimization, reduce image size, adjust `confidence_threshold` and `preprocessing` settings
- **Service Not Starting**: Check logs, run as administrator, validate dependencies, use `sc query EasyOCR-MCP-Server`
- **Debug Mode**: Enable debug logging with `python main.py --log-level DEBUG`, validate configuration with `python main.py --validate`

## Testing and Validation
**Test Suite:**
```bash
# Run all tests
python -m pytest tests/

# Run integration tests
python tests/integration/test_mcp_integration.py

# Run validation
python main.py --validate

# Test performance with sample images
python scripts/monitoring/monitoring_integration.py
```

## Performance Metrics
- **Expected Performance on Asus x515ae**: 1-3 seconds per image (1024px max), 5-15 seconds per batch (5 images), 200-400MB memory usage during operation, 30-60% CPU usage during processing, 85-95% accuracy for clear text documents
- **Monitoring Metrics**: Response time tracking, memory usage monitoring, error rate calculation, throughput measurement, resource utilization tracking

## Backup and Recovery
**Configuration Backup:**
```bash
# Backup configuration
cp config/easyocr_mcp_config.json config/easyocr_mcp_config_backup.json

# Backup models
cp -r C:/easyocr_models C:/easyocr_models_backup
```

**Service Recovery:**
```bash
# Restart service on failure
net stop EasyOCR-MCP-Server
net start EasyOCR-MCP-Server

# Check logs for errors
Get-Content logs/easyocr_mcp_error.log -Tail 20
```

## Version Information
- **Current Version**: 1.0.0
- **Last Updated**: 2025-01-01
- **Compatibility**: MCP Protocol v1.0+, Python 3.7+
- **Model Storage**: C:/easyocr_models

## Support and Maintenance
**Documentation:**
- Main README: `mcp_servers/easyocr-mcp/README.md`
- Configuration Guide: `config/easyocr_mcp_config.json`
- API Reference: Inline documentation in source files

**Community Support:**
- GitHub Issues: Project repository
- Documentation Updates: Regular maintenance
- Performance Monitoring: Built-in monitoring tools

**Maintenance Schedule:**
- **Daily**: Log rotation and monitoring
- **Weekly**: Performance optimization review
- **Monthly**: Configuration validation and updates
- **Quarterly**: Security assessment and testing

## References
- EasyOCR Documentation: https://github.com/JaidedAI/EasyOCR
- MCP Protocol Specification: https://modelcontextprotocol.io
- Project Repository: https://github.com/your-org/easyocr-mcp-server

---

## Extra Info
### Enhanced OCR Formatter

The EasyOCR MCP Server includes an enhanced formatter that provides superior document structure preservation and Markdown formatting. This formatter goes beyond basic text extraction to create well-structured, readable documents that maintain the original layout and organization.

**Key Features:**
- **Layout Preservation**: Maintains original document structure and formatting
- **Enhanced Markdown**: Creates properly formatted Markdown with headings, sections, and organization
- **Document Metadata**: Includes processing statistics, timestamps, and image information
- **Structure Detection**: Automatically identifies headings, paragraphs, and document sections
- **Improved Readability**: Better text organization and formatting for human consumption

### System Requirements and Compatibility

**Hardware Requirements:**
- **CPU**: Intel Core i5 or equivalent (minimum)
- **RAM**: 4GB minimum, 8GB recommended for Asus x515ae
- **Storage**: 2GB free space for models and temporary files
- **GPU**: Optional (CPU processing enabled by default)

**Software Requirements:**
- **Operating System**: Windows 10/11 (primary), Linux (secondary)
- **Python**: 3.7 or later
- **Memory Management**: Configurable 512MB memory limit
- **Network**: Local network access for model downloads

**Asus x515ae Specific Optimizations:**
- **CPU Optimization**: Disabled GPU usage for better CPU utilization
- **Memory Management**: Conservative 512MB memory limit
- **Thread Pool**: Reduced to 2 threads for low-resource systems
- **Batch Processing**: Optimized batch size of 5 images
- **Image Preprocessing**: Resized to 1024px maximum to reduce memory footprint

### Kilo Code Recognition System

Kilo Code should automatically recognize when to use the EasyOCR MCP Server based on the following patterns:

**Trigger Patterns:**
1. **Image-to-Markdown Conversion Requests**: Keywords like "convert", "extract", "process" with image file extensions (.png, .jpg, etc.) and output format (.md, markdown)
2. **Text Extraction from Images**: Keywords like "extract text", "get text", "read text", "OCR" with image files
3. **Document Processing Requests**: Keywords like "process multiple images", "batch convert", "create document" with multiple images

**Usage Decision Flow:**
```
User Request
    ↓
Check for image files (.png, .jpg, etc.)
    ↓
Check for conversion keywords (convert, extract, etc.)
    ↓
Check for output format (.md, markdown)
    ↓
Use EasyOCR MCP Server
    ↓
Select appropriate MCP tool based on:
- Number of images (single vs batch)
- Image format (file path vs base64)
- Processing requirements
    ↓
Apply enhanced formatting
    ↓
Save output with .md extension
```

### Recent Enhancements

**Improved OCR Formatter:**
- Enhanced Layout Preservation: Better text organization based on position information
- Structured Markdown Output: Creates well-formatted documents with proper headings and sections
- Document Metadata: Includes processing statistics, confidence scores, and system information
- Performance Optimization: Faster processing with improved text extraction algorithms
- Error Handling: Robust error handling with detailed logging

**Successful Test Case:**
- File Converted: "A.0 Mybizz system.png" → "A.0 Mybizz system.md"
- Text Elements Extracted: 80 text elements
- Processing Time: 29.77 seconds
- Output Quality: Structured Markdown with preserved layout
- Location: C:\_1mybizz\paddle-plugin\Docs\_My Todo\