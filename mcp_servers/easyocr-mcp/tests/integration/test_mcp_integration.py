#!/usr/bin/env python3
"""
EasyOCR MCP Server Integration Tests

This module provides comprehensive integration tests for the EasyOCR MCP server
to verify it works correctly with the existing system architecture.

Author: Kilo Code
License: Apache 2.0
"""

import os
import sys
import json
import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestEasyOCRMCPServerIntegration(unittest.TestCase):
    """Test cases for EasyOCR MCP server integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.project_root = Path(__file__).parent.parent.parent
        self.config_path = str(self.project_root / "config" / "easyocr_mcp_config.json")
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test configuration
        self.test_config = {
            "easyocr": {
                "languages": ["en"],
                "gpu": False,
                "model_storage_directory": str(self.temp_dir / "models"),
                "confidence_threshold": 30
            },
            "preprocessing": {
                "enabled": True,
                "max_image_size": 1024,
                "use_grayscale": True,
                "use_binarization": True
            },
            "batch": {
                "size": 5,
                "timeout": 30
            },
            "logging": {
                "level": "INFO",
                "file": str(self.temp_dir / "test.log")
            }
        }
        
        # Save test configuration
        with open(self.config_path, 'w') as f:
            json.dump(self.test_config, f, indent=2)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_server_initialization(self):
        """Test server initialization with configuration."""
        try:
            from easyocr_mcp_server import EasyOCRMCPServer
            
            # Create server instance
            server = EasyOCRMCPServer(self.config_path)
            
            # Verify server properties
            self.assertIsNotNone(server)
            self.assertIsNotNone(server.config_manager)
            self.assertIsNotNone(server.ocr_processor)
            self.assertIsNotNone(server.mcp)
            
            # Verify server info
            info = server.get_server_info()
            self.assertEqual(info['server_name'], 'EasyOCR MCP Server')
            self.assertEqual(info['version'], '1.0.0')
            
            logger.info("✓ Server initialization test passed")
            
        except Exception as e:
            logger.error(f"✗ Server initialization test failed: {e}")
            self.fail(f"Server initialization failed: {e}")
    
    def test_ocr_processor_initialization(self):
        """Test OCR processor initialization."""
        try:
            from easyocr_processor import EasyOCRProcessor
            
            # Create processor instance
            processor = EasyOCRProcessor(self.test_config)
            
            # Verify processor properties
            self.assertIsNotNone(processor)
            self.assertEqual(processor.languages, ["en"])
            self.assertFalse(processor.gpu)
            self.assertEqual(processor.confidence_threshold, 30)
            
            # Test processor info
            info = processor.get_processor_info()
            self.assertEqual(info['processor_type'], 'EasyOCR')
            self.assertEqual(info['languages'], ["en"])
            self.assertFalse(info['gpu_enabled'])
            
            logger.info("✓ OCR processor initialization test passed")
            
        except Exception as e:
            logger.error(f"✗ OCR processor initialization test failed: {e}")
            self.fail(f"OCR processor initialization failed: {e}")
    
    def test_mcp_tools_registration(self):
        """Test MCP tools registration."""
        try:
            from easyocr_mcp_server import EasyOCRMCPServer
            
            # Create server instance
            server = EasyOCRMCPServer(self.config_path)
            
            # Verify tools are registered
            tools = server.mcp._tools
            self.assertGreater(len(tools), 0)
            
            # Check for expected tools
            tool_names = [tool.name for tool in tools]
            expected_tools = [
                'extract_text_from_image',
                'extract_text_from_batch',
                'get_available_languages',
                'validate_ocr_installation',
                'get_processor_info',
                'extract_text_from_base64'
            ]
            
            for expected_tool in expected_tools:
                self.assertIn(expected_tool, tool_names)
            
            logger.info("✓ MCP tools registration test passed")
            
        except Exception as e:
            logger.error(f"✗ MCP tools registration test failed: {e}")
            self.fail(f"MCP tools registration failed: {e}")
    
    def test_configuration_loading(self):
        """Test configuration loading and validation."""
        try:
            from config.manager import ConfigurationManager
            
            # Create config manager
            config_manager = ConfigurationManager(self.config_path)
            
            # Test configuration sections
            easyocr_config = config_manager.get_config('easyocr', {})
            self.assertEqual(easyocr_config['languages'], ["en"])
            self.assertFalse(easyocr_config['gpu'])
            
            preprocessing_config = config_manager.get_config('preprocessing', {})
            self.assertTrue(preprocessing_config['enabled'])
            self.assertEqual(preprocessing_config['max_image_size'], 1024)
            
            batch_config = config_manager.get_config('batch', {})
            self.assertEqual(batch_config['size'], 5)
            
            logger.info("✓ Configuration loading test passed")
            
        except Exception as e:
            logger.error(f"✗ Configuration loading test failed: {e}")
            self.fail(f"Configuration loading failed: {e}")
    
    def test_integration_with_cache_server(self):
        """Test integration with cache MCP server."""
        try:
            # Mock cache server responses
            mock_cache_response = {
                "status": "ok",
                "message": "Cache server healthy",
                "timestamp": "2025-01-01T00:00:00Z"
            }
            
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_get.return_value.__aenter__.return_value.status = 200
                mock_get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_cache_response)
                
                from scripts.integration.integrate_with_mcp_servers import MCPIntegrator, MCPIntegrationConfig
                
                # Create integration config
                config = MCPIntegrationConfig(
                    cache_server_enabled=True,
                    cache_server_endpoint="http://localhost:8001"
                )
                
                # Create integrator
                integrator = MCPIntegrator(config)
                
                # Test connection
                asyncio.run(integrator._test_connections())
                
                logger.info("✓ Cache server integration test passed")
                
        except Exception as e:
            logger.error(f"✗ Cache server integration test failed: {e}")
            self.fail(f"Cache server integration failed: {e}")
    
    def test_integration_with_kilocode(self):
        """Test integration with KiloCode orchestration."""
        try:
            # Mock KiloCode responses
            mock_kilocode_response = {
                "status": "ok",
                "message": "KiloCode orchestration healthy",
                "timestamp": "2025-01-01T00:00:00Z"
            }
            
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_get.return_value.__aenter__.return_value.status = 200
                mock_get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_kilocode_response)
                
                from scripts.integration.integrate_with_mcp_servers import MCPIntegrator, MCPIntegrationConfig
                
                # Create integration config
                config = MCPIntegrationConfig(
                    kilocode_enabled=True,
                    kilocode_endpoint="http://localhost:8080"
                )
                
                # Create integrator
                integrator = MCPIntegrator(config)
                
                # Test connection
                asyncio.run(integrator._test_connections())
                
                logger.info("✓ KiloCode integration test passed")
                
        except Exception as e:
            logger.error(f"✗ KiloCode integration test failed: {e}")
            self.fail(f"KiloCode integration failed: {e}")
    
    def test_integration_with_memory_bank(self):
        """Test integration with memory bank."""
        try:
            from scripts.integration.integrate_with_mcp_servers import MCPIntegrator, MCPIntegrationConfig
            
            # Create integration config
            config = MCPIntegrationConfig(
                memory_bank_enabled=True,
                memory_bank_path=self.temp_dir
            )
            
            # Create integrator
            integrator = MCPIntegrator(config)
            
            # Test memory bank sync
            asyncio.run(integrator._sync_with_memory_bank())
            
            logger.info("✓ Memory bank integration test passed")
            
        except Exception as e:
            logger.error(f"✗ Memory bank integration test failed: {e}")
            self.fail(f"Memory bank integration failed: {e}")
    
    def test_service_deployment(self):
        """Test service deployment setup."""
        try:
            from scripts.deploy.deploy_easyocr_service import EasyOCRServiceDeployer
            
            # Create deployer
            deployer = EasyOCRServiceDeployer(self.config_path)
            
            # Test directory setup
            self.assertTrue(deployer.setup_directories())
            
            # Test logging setup
            self.assertTrue(deployer.setup_logging())
            
            # Test environment setup
            self.assertTrue(deployer.setup_environment())
            
            # Test monitoring setup
            self.assertTrue(deployer.setup_monitoring())
            
            # Test network configuration
            self.assertTrue(deployer.setup_network_configuration())
            
            # Test authentication setup
            self.assertTrue(deployer.setup_authentication())
            
            logger.info("✓ Service deployment test passed")
            
        except Exception as e:
            logger.error(f"✗ Service deployment test failed: {e}")
            self.fail(f"Service deployment failed: {e}")
    
    def test_health_check_functionality(self):
        """Test health check functionality."""
        try:
            from scripts.monitoring.health_check import check_service_health
            
            # Mock healthy response
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "status": "healthy",
                    "timestamp": "2025-01-01T00:00:00Z"
                }
                mock_response.elapsed.total_seconds.return_value = 0.5
                mock_get.return_value = mock_response
                
                # Test health check
                health = check_service_health()
                self.assertEqual(health['status'], 'healthy')
                self.assertEqual(health['service'], 'easyocr-mcp')
                
                logger.info("✓ Health check test passed")
                
        except Exception as e:
            logger.error(f"✗ Health check test failed: {e}")
            self.fail(f"Health check failed: {e}")
    
    def test_error_handling(self):
        """Test error handling in integration scenarios."""
        try:
            from scripts.integration.integrate_with_mcp_servers import MCPIntegrator, MCPIntegrationConfig
            
            # Create integration config with disabled services
            config = MCPIntegrationConfig(
                cache_server_enabled=False,
                kilocode_enabled=False,
                memory_bank_enabled=False
            )
            
            # Create integrator
            integrator = MCPIntegrator(config)
            
            # Test initialization with disabled services
            asyncio.run(integrator.initialize())
            
            # Test that disabled services don't cause errors
            self.assertIsNotNone(integrator.session)
            
            logger.info("✓ Error handling test passed")
            
        except Exception as e:
            logger.error(f"✗ Error handling test failed: {e}")
            self.fail(f"Error handling failed: {e}")
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        try:
            from config.manager import ConfigurationManager
            
            # Create config manager
            config_manager = ConfigurationManager(self.config_path)
            
            # Test configuration validation
            config = config_manager.get_config('easyocr', {})
            self.assertIsInstance(config, dict)
            self.assertIn('languages', config)
            self.assertIn('gpu', config)
            self.assertIn('confidence_threshold', config)
            
            # Test logging configuration
            logging_config = config_manager.get_logging_config()
            self.assertIsInstance(logging_config, dict)
            self.assertIn('level', logging_config)
            self.assertIn('file', logging_config)
            
            logger.info("✓ Configuration validation test passed")
            
        except Exception as e:
            logger.error(f"✗ Configuration validation test failed: {e}")
            self.fail(f"Configuration validation failed: {e}")
    
    def test_batch_processing(self):
        """Test batch processing functionality."""
        try:
            from easyocr_processor import EasyOCRProcessor
            
            # Create processor instance
            processor = EasyOCRProcessor(self.test_config)
            
            # Test batch processing with empty list
            result = processor.extract_batch([])
            self.assertEqual(result['total_files'], 0)
            self.assertEqual(result['successful_files'], 0)
            self.assertEqual(result['failed_files'], 0)
            
            logger.info("✓ Batch processing test passed")
            
        except Exception as e:
            logger.error(f"✗ Batch processing test failed: {e}")
            self.fail(f"Batch processing failed: {e}")
    
    def test_language_support(self):
        """Test language support functionality."""
        try:
            from easyocr_processor import EasyOCRProcessor
            
            # Create processor instance
            processor = EasyOCRProcessor(self.test_config)
            
            # Test available languages
            languages = processor.get_available_languages()
            self.assertIsInstance(languages, list)
            
            # Test language setting
            processor.set_languages(['en', 'fr'])
            self.assertEqual(processor.languages, ['en', 'fr'])
            
            logger.info("✓ Language support test passed")
            
        except Exception as e:
            logger.error(f"✗ Language support test failed: {e}")
            self.fail(f"Language support failed: {e}")
    
    def test_gpu_configuration(self):
        """Test GPU configuration."""
        try:
            from easyocr_processor import EasyOCRProcessor
            
            # Create processor instance
            processor = EasyOCRProcessor(self.test_config)
            
            # Test GPU setting
            self.assertFalse(processor.gpu)
            
            # Test GPU toggle
            processor.set_gpu(True)
            self.assertTrue(processor.gpu)
            
            processor.set_gpu(False)
            self.assertFalse(processor.gpu)
            
            logger.info("✓ GPU configuration test passed")
            
        except Exception as e:
            logger.error(f"✗ GPU configuration test failed: {e}")
            self.fail(f"GPU configuration failed: {e}")
    
    def test_confidence_threshold(self):
        """Test confidence threshold configuration."""
        try:
            from easyocr_processor import EasyOCRProcessor
            
            # Create processor instance
            processor = EasyOCRProcessor(self.test_config)
            
            # Test confidence threshold
            self.assertEqual(processor.confidence_threshold, 30)
            
            # Test confidence threshold setting
            processor.set_confidence_threshold(50)
            self.assertEqual(processor.confidence_threshold, 50)
            
            # Test invalid confidence threshold
            with self.assertRaises(ValueError):
                processor.set_confidence_threshold(150)
            
            logger.info("✓ Confidence threshold test passed")
            
        except Exception as e:
            logger.error(f"✗ Confidence threshold test failed: {e}")
            self.fail(f"Confidence threshold failed: {e}")


class TestEasyOCRMCPServerIntegrationAsync(unittest.IsolatedAsyncioTestCase):
    """Async test cases for EasyOCR MCP server integration."""
    
    async def asyncSetUp(self):
        """Set up async test environment."""
        self.project_root = Path(__file__).parent.parent.parent
        self.config_path = str(self.project_root / "config" / "easyocr_mcp_config.json")
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test configuration
        self.test_config = {
            "easyocr": {
                "languages": ["en"],
                "gpu": False,
                "model_storage_directory": str(self.temp_dir / "models"),
                "confidence_threshold": 30
            },
            "preprocessing": {
                "enabled": True,
                "max_image_size": 1024,
                "use_grayscale": True,
                "use_binarization": True
            },
            "batch": {
                "size": 5,
                "timeout": 30
            },
            "logging": {
                "level": "INFO",
                "file": str(self.temp_dir / "test.log")
            }
        }
        
        # Save test configuration
        with open(self.config_path, 'w') as f:
            json.dump(self.test_config, f, indent=2)
    
    async def asyncTearDown(self):
        """Clean up async test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    async def test_async_server_initialization(self):
        """Test async server initialization."""
        try:
            from easyocr_mcp_server import EasyOCRMCPServer
            
            # Create server instance
            server = EasyOCRMCPServer(self.config_path)
            
            # Test server info
            info = server.get_server_info()
            self.assertEqual(info['server_name'], 'EasyOCR MCP Server')
            
            logger.info("✓ Async server initialization test passed")
            
        except Exception as e:
            logger.error(f"✗ Async server initialization test failed: {e}")
            self.fail(f"Async server initialization failed: {e}")
    
    async def test_async_ocr_processing(self):
        """Test async OCR processing."""
        try:
            from easyocr_mcp_server import EasyOCRMCPServer
            
            # Create server instance
            server = EasyOCRMCPServer(self.config_path)
            
            # Test available languages
            languages = await server.get_available_languages()
            self.assertIsInstance(languages, list)
            
            # Test processor info
            info = await server.get_processor_info()
            self.assertEqual(info['processor_type'], 'EasyOCR')
            
            logger.info("✓ Async OCR processing test passed")
            
        except Exception as e:
            logger.error(f"✗ Async OCR processing test failed: {e}")
            self.fail(f"Async OCR processing failed: {e}")
    
    async def test_async_integration_process(self):
        """Test async integration process."""
        try:
            from scripts.integration.integrate_with_mcp_servers import MCPIntegrator, MCPIntegrationConfig
            
            # Create integration config
            config = MCPIntegrationConfig(
                cache_server_enabled=False,
                kilocode_enabled=False,
                memory_bank_enabled=False
            )
            
            # Create integrator
            integrator = MCPIntegrator(config)
            
            # Test async initialization
            await integrator.initialize()
            
            # Test async integration process
            await integrator.run_integration()
            
            # Test async cleanup
            await integrator.close()
            
            logger.info("✓ Async integration process test passed")
            
        except Exception as e:
            logger.error(f"✗ Async integration process test failed: {e}")
            self.fail(f"Async integration process failed: {e}")


def run_integration_tests():
    """Run all integration tests."""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestEasyOCRMCPServerIntegration))
    suite.addTest(unittest.makeSuite(TestEasyOCRMCPServerIntegrationAsync))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return test result
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)