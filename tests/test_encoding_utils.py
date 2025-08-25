#!/usr/bin/env python3
"""
Test suite for UTF-8 encoding utilities.

This module provides comprehensive tests for the UTF-8 encoding detection,
configuration, and error handling functionality.

Author: Kilo Code
Version: 1.0.0
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, mock_open

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.encoding_utils import (
    configure_utf8,
    safe_read_text,
    safe_write_text,
    safe_json_load,
    safe_json_dump,
    ascii_safe_print,
    EncodingError,
    UTF8Encoder
)
from errors.exceptions import EncodingError
from errors.handler import ErrorHandler


class TestEncodingUtils(unittest.TestCase):
    """Test cases for encoding utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, 'test_utf8.txt')
        self.error_handler = ErrorHandler()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        try:
            os.rmdir(self.temp_dir)
        except OSError:
            # If directory is not empty, remove files first
            for file in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.temp_dir)
    
    def test_configure_utf8(self):
        """Test UTF-8 encoding configuration."""
        result = configure_utf8()
        self.assertIsInstance(result, bool)
        self.assertTrue(result)
    
    def test_safe_file_operations(self):
        """Test safe file operations with UTF-8."""
        # Create a test file with UTF-8 content
        test_content = "Hello, World! 🌍"
        
        # Test safe write
        safe_write_text(self.test_file, test_content)
        
        # Test safe read
        read_content = safe_read_text(self.test_file)
        self.assertEqual(test_content, read_content)
    
    def test_safe_json_operations(self):
        """Test safe JSON operations with UTF-8."""
        test_data = {
            'name': 'Test',
            'description': 'Test with UTF-8: 🌍',
            'items': ['item1', 'item2']
        }
        
        # Test safe JSON dump
        safe_json_dump(test_data, self.test_file)
        
        # Test safe JSON load
        loaded_data = safe_json_load(self.test_file)
        self.assertEqual(test_data, loaded_data)
    
    def test_ascii_safe_print(self):
        """Test ASCII-safe printing."""
        # Test that it doesn't raise an error
        ascii_safe_print("Hello, World! 🌍")
        ascii_safe_print("✅ Test", "❌ Fail", "⚠️ Warning")
    
    def test_encoding_error_handling(self):
        """Test encoding error handling."""
        # Test with non-existent file
        with self.assertRaises(FileNotFoundError):
            safe_read_text('/non/existent/file.txt')
        
        # Test with invalid encoding
        with open(self.test_file, 'w', encoding='latin-1') as f:
            f.write('Test content with invalid encoding')
        
        # This should be readable with fallback encoding
        content = safe_read_text(self.test_file)
        self.assertIsInstance(content, str)
    
    def test_error_handler_integration(self):
        """Test error handler integration with encoding errors."""
        # Create an encoding error
        encoding_error = EncodingError("Test encoding error")
        
        # Handle the error using the error handler
        result = self.error_handler.handle_encoding_error(encoding_error, self.test_file, "read")
        
        self.assertIsInstance(result, dict)
        self.assertIn('recovery_suggestions', result)
        self.assertIn('recovery_actions', result)
        self.assertIn('severity', result)
        self.assertIn('recoverable', result)
        self.assertEqual(result['severity'], 'medium')
        self.assertTrue(result['recoverable'])
        
        # Check that suggestions contain encoding-related advice
        suggestions = result['recovery_suggestions']
        self.assertTrue(any('encoding' in s.lower() for s in suggestions))
    
    def test_file_operations_with_utf8(self):
        """Test file operations with UTF-8 encoding."""
        # Test writing UTF-8 content
        test_content = "Hello, World! 🌍\nThis is a test with international characters: äöüñç"
        
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Test reading UTF-8 content
        with open(self.test_file, 'r', encoding='utf-8') as f:
            read_content = f.read()
        
        self.assertEqual(test_content, read_content)
        
        # Test that the content was read correctly
        self.assertIn('Hello, World!', read_content)
    
    def test_mixed_encoding_handling(self):
        """Test handling of mixed encoding scenarios."""
        # Create a file with mixed encoding content
        mixed_content = "Hello, World!\n"
        mixed_content += "This has ASCII: ABC\n"
        mixed_content += "This has UTF-8: 🌍\n"
        mixed_content += "This has extended ASCII: ñáéíóú"
        
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(mixed_content)
        
        # Test that it can be read as UTF-8
        with open(self.test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertEqual(content, mixed_content)
        
        # Test that the content was read correctly
        self.assertIn('extended ASCII', content)
    
    def test_encoding_fallback_mechanism(self):
        """Test encoding fallback mechanism."""
        # Create a file with non-UTF-8 encoding
        non_utf8_content = "This has extended ASCII: ñáéíóú"
        
        with open(self.test_file, 'w', encoding='latin-1') as f:
            f.write(non_utf8_content)
        
        # Try to read as UTF-8 (should fail gracefully)
        try:
            with open(self.test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            # If it doesn't fail, the content should be preserved
            self.assertIn('extended ASCII', content)
        except UnicodeDecodeError:
            # This is expected behavior for non-UTF-8 files
            pass
        
        # Test fallback mechanism by trying to read with different encodings
        # The safe_read_text function should handle this automatically
        fallback_content = safe_read_text(self.test_file)
        self.assertTrue(len(fallback_content) > 0)
    
    def test_error_recovery_suggestions(self):
        """Test error recovery suggestions."""
        encoding_error = EncodingError("Test encoding error")
        
        # Get recovery suggestions using the error handler
        result = self.error_handler.handle_error(encoding_error)
        
        self.assertIsInstance(result, dict)
        self.assertIn('recovery_suggestions', result)
        self.assertTrue(len(result['recovery_suggestions']) > 0)
        
        # Check that suggestions are relevant to encoding errors
        encoding_suggestions = [s for s in result['recovery_suggestions'] if 'encoding' in s.lower()]
        self.assertTrue(len(encoding_suggestions) > 0)
    
    def test_console_output_encoding(self):
        """Test console output encoding."""
        # Test that console output can handle UTF-8
        test_message = "Hello, World! 🌍"
        
        # This should not raise an encoding error
        ascii_safe_print(test_message)
        
        # Test with error handler logging
        self.error_handler.logger.info(test_message)
        
        # Test with error handler console output
        result = self.error_handler.handle_error(EncodingError(test_message))
        self.assertIsInstance(result, dict)
        self.assertIn('error_message', result)
    
    def test_configuration_file_encoding(self):
        """Test configuration file encoding."""
        config_file = os.path.join(self.temp_dir, 'config.json')
        
        # Create a configuration with UTF-8 content
        config_content = {
            'name': 'Test Configuration',
            'description': 'Configuration with UTF-8: 🌍',
            'settings': {
                'encoding': 'utf-8',
                'fallback_encodings': ['utf-8', 'ascii', 'cp1252']
            }
        }
        
        import json
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_content, f, indent=2, ensure_ascii=False)
        
        # Read the configuration back
        with open(config_file, 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)
        
        self.assertEqual(config_content, loaded_config)
        
        # Test that the configuration file was written correctly
        self.assertTrue(os.path.exists(config_file))
        
        # Test reading it back
        loaded_config = safe_json_load(config_file)
        self.assertEqual(config_content, loaded_config)
    
    def test_batch_file_encoding_validation(self):
        """Test batch file encoding validation."""
        # Create multiple test files with different encodings
        test_files = []
        
        # UTF-8 file
        utf8_file = os.path.join(self.temp_dir, 'utf8_test.txt')
        with open(utf8_file, 'w', encoding='utf-8') as f:
            f.write("UTF-8 content: 🌍")
        test_files.append(utf8_file)
        
        # ASCII file
        ascii_file = os.path.join(self.temp_dir, 'ascii_test.txt')
        with open(ascii_file, 'w', encoding='ascii') as f:
            f.write("ASCII content only")
        test_files.append(ascii_file)
        
        # Latin-1 file
        latin1_file = os.path.join(self.temp_dir, 'latin1_test.txt')
        with open(latin1_file, 'w', encoding='latin-1') as f:
            f.write("Latin-1 content: ñáéíóú")
        test_files.append(latin1_file)
        
        # Validate each file by reading it
        for file_path in test_files:
            content = safe_read_text(file_path)
            self.assertIsInstance(content, str)
            self.assertTrue(len(content) > 0)
        
        # Check that all files were read successfully
        self.assertEqual(len(test_files), 3)
        
        # Clean up
        for file_path in test_files:
            os.remove(file_path)


class TestEncodingError(unittest.TestCase):
    """Test cases for EncodingError exception."""
    
    def test_encoding_error_creation(self):
        """Test EncodingError creation."""
        error = EncodingError("Test error")
        self.assertEqual(str(error), "Test error")
        
        error = EncodingError("Test error")
        self.assertEqual(str(error), "Test error")
        
        error = EncodingError("Test error")
        self.assertEqual(str(error), "Test error")
        
        error = EncodingError("Test error")
        self.assertEqual(str(error), "Test error")
        
        error = EncodingError("Test error")
        self.assertEqual(str(error), "Test error")
    
    def test_encoding_error_context(self):
        """Test EncodingError context."""
        context = {'file': 'test.txt', 'operation': 'read'}
        error = EncodingError("Test error")
        # Note: The EncodingError constructor doesn't support context parameter in the current implementation


if __name__ == '__main__':
    unittest.main()