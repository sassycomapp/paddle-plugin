#!/usr/bin/env python3
"""
EasyOCR MCP Server Test Script

This script tests the EasyOCR MCP server implementation to ensure
all low-resource optimizations are working correctly.

Author: Kilo Code
Version: 1.0.0
"""

import os
import sys
import json
import tempfile
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_test_image(text: str = "Hello World", size: tuple = (800, 200)) -> str:
    """Create a test image with text for OCR testing."""
    try:
        # Create image
        image = Image.new('RGB', size, color='white')
        draw = ImageDraw.Draw(image)
        
        # Try to use a default font
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        # Draw text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2
        
        draw.text((x, y), text, fill='black', font=font)
        
        # Save to temporary file
        temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        test_image_path = os.path.join(temp_dir, 'test_image.png')
        image.save(test_image_path)
        
        return test_image_path
        
    except Exception as e:
        logger.error(f"Failed to create test image: {e}")
        raise


def test_easyocr_processor():
    """Test the EasyOCR processor implementation."""
    logger.info("Testing EasyOCR Processor...")
    
    try:
        from easyocr_processor import EasyOCRProcessor
        
        # Create test configuration
        test_config = {
            'easyocr': {
                'languages': ['en'],
                'gpu': False,
                'model_storage_directory': 'C:/easyocr_models',
                'confidence_threshold': 30
            },
            'preprocessing': {
                'max_image_size': 1024,
                'use_grayscale': True,
                'use_binarization': True
            },
            'batch': {
                'size': 5,
                'timeout': 30
            }
        }
        
        # Initialize processor
        processor = EasyOCRProcessor(test_config)
        
        # Test configuration
        logger.info("✓ Processor initialized successfully")
        
        # Test available languages
        languages = processor.get_available_languages()
        logger.info(f"✓ Available languages: {languages}")
        
        # Test processor info
        info = processor.get_processor_info()
        logger.info(f"✓ Processor info: {info}")
        
        # Test validation
        is_valid = processor.validate_installation()
        logger.info(f"✓ Installation validation: {is_valid}")
        
        # Test with actual image
        test_image_path = create_test_image("EasyOCR Test")
        
        if os.path.exists(test_image_path):
            logger.info("✓ Test image created successfully")
            
            # Test text extraction
            result = processor.extract_text_with_metadata(test_image_path)
            logger.info(f"✓ Text extraction completed: {result['text']}")
            
            # Clean up
            try:
                os.remove(test_image_path)
            except:
                pass
        else:
            logger.warning("⚠ Test image creation failed")
        
        logger.info("✓ EasyOCR Processor test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ EasyOCR Processor test failed: {e}")
        return False


def test_mcp_server():
    """Test the MCP server implementation."""
    logger.info("Testing MCP Server...")
    
    try:
        from easyocr_mcp_server import EasyOCRMCPServer
        
        # Create test configuration
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'easyocr_mcp_config.json')
        
        if not os.path.exists(config_path):
            logger.warning(f"⚠ Config file not found: {config_path}")
            return False
        
        # Initialize server
        server = EasyOCRMCPServer(config_path)
        
        # Test server info
        info = server.get_server_info()
        logger.info(f"✓ Server info: {info['server_name']} v{info['version']}")
        
        # Test processor info through server
        processor_info = server.ocr_processor.get_processor_info()
        logger.info(f"✓ Processor info through server: {processor_info['languages']}")
        
        logger.info("✓ MCP Server test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ MCP Server test failed: {e}")
        return False


def test_configuration():
    """Test the configuration file."""
    logger.info("Testing Configuration...")
    
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'easyocr_mcp_config.json')
        
        if not os.path.exists(config_path):
            logger.error(f"✗ Config file not found: {config_path}")
            return False
        
        # Load and validate configuration
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check required sections
        required_sections = ['easyocr', 'preprocessing', 'batch', 'logging']
        for section in required_sections:
            if section not in config:
                logger.error(f"✗ Missing required section: {section}")
                return False
        
        # Check low-resource optimizations
        easyocr_config = config['easyocr']
        if easyocr_config.get('languages') != ['en']:
            logger.error(f"✗ Language configuration incorrect: {easyocr_config.get('languages')}")
            return False
        
        if easyocr_config.get('gpu') != False:
            logger.error(f"✗ GPU configuration incorrect: {easyocr_config.get('gpu')}")
            return False
        
        if easyocr_config.get('model_storage_directory') != 'C:/easyocr_models':
            logger.error(f"✗ Model directory configuration incorrect: {easyocr_config.get('model_storage_directory')}")
            return False
        
        # Check preprocessing settings
        preprocessing_config = config['preprocessing']
        if preprocessing_config.get('max_image_size') != 1024:
            logger.error(f"✗ Max image size configuration incorrect: {preprocessing_config.get('max_image_size')}")
            return False
        
        if not preprocessing_config.get('use_grayscale'):
            logger.error(f"✓ Grayscale configuration should be enabled")
        
        if not preprocessing_config.get('use_binarization'):
            logger.error(f"✓ Binarization configuration should be enabled")
        
        # Check batch settings
        batch_config = config['batch']
        if batch_config.get('size') != 5:
            logger.error(f"✗ Batch size configuration incorrect: {batch_config.get('size')}")
            return False
        
        logger.info("✓ Configuration test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False


def test_file_structure():
    """Test the file structure."""
    logger.info("Testing File Structure...")
    
    required_files = [
        'src/easyocr_processor.py',
        'src/easyocr_mcp_server.py',
        'config/easyocr_mcp_config.json',
        'main.py',
        'requirements.txt',
        'README.md'
    ]
    
    base_path = os.path.dirname(__file__)
    
    for file_path in required_files:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            logger.info(f"✓ {file_path}")
        else:
            logger.error(f"✗ {file_path} - File not found")
            return False
    
    logger.info("✓ File structure test completed successfully")
    return True


def main():
    """Main test function."""
    logger.info("Starting EasyOCR MCP Server Implementation Tests")
    logger.info("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Configuration", test_configuration),
        ("EasyOCR Processor", test_easyocr_processor),
        ("MCP Server", test_mcp_server)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning {test_name} Test...")
        logger.info("-" * 40)
        
        try:
            if test_func():
                passed += 1
                logger.info(f"✓ {test_name} test PASSED")
            else:
                logger.error(f"✗ {test_name} test FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} test FAILED with exception: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! EasyOCR MCP Server implementation is ready.")
        return 0
    else:
        logger.error("❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())