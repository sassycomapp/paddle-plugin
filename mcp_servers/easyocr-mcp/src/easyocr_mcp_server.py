"""
EasyOCR MCP Server

This module provides the MCP (Model Context Protocol) server for EasyOCR.
It handles MCP protocol communication and exposes OCR functionality.

Author: Kilo Code
Version: 1.0.0
"""

import os
import sys
import json
import logging
import asyncio
import base64
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from PIL import Image
import numpy as np

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# MCP imports
try:
    from mcp.server.fastmcp import FastMCP
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    import mcp.server.stdio
    import mcp.types
except ImportError:
    print("MCP package not found. Please install MCP dependencies.")
    sys.exit(1)

# Local imports
from easyocr_processor import EasyOCRProcessor
from config.manager import ConfigurationManager


class EasyOCRMCPServer:
    """
    EasyOCR MCP Server that implements the MCP protocol.
    Provides OCR functionality through MCP tools.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the EasyOCR MCP server.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config_manager = ConfigurationManager(config_path)
        self.ocr_processor = None
        self.logger = logging.getLogger(__name__)
        
        # Initialize MCP server
        self.mcp = FastMCP("EasyOCR MCP Server")
        
        # Setup logging
        self._setup_logging()
        
        # Initialize OCR processor
        self._initialize_ocr_processor()
        
        # Register tools
        self._register_tools()
        
        self.logger.info("EasyOCR MCP Server initialized")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        try:
            logging_config = self.config_manager.get_logging_config()
            
            # Configure logging
            logging.basicConfig(
                level=getattr(logging, logging_config.get('level', 'INFO')),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(logging_config.get('file', 'easyocr_mcp.log')),
                    logging.StreamHandler()
                ]
            )
            
            self.logger.info("Logging configured successfully")
            
        except Exception as e:
            print(f"Failed to setup logging: {e}")
            # Fallback to basic logging
            logging.basicConfig(level=logging.INFO)
    
    def _initialize_ocr_processor(self) -> None:
        """Initialize the OCR processor with configuration."""
        try:
            # Get OCR configuration
            ocr_config = self.config_manager.get_config('easyocr', {})
            preprocessing_config = self.config_manager.get_config('preprocessing', {})
            batch_config = self.config_manager.get_config('batch', {})
            
            # Merge configurations
            full_config = {
                'easyocr': ocr_config,
                'preprocessing': preprocessing_config,
                'batch': batch_config
            }
            
            # Initialize OCR processor
            self.ocr_processor = EasyOCRProcessor(full_config)
            
            self.logger.info("OCR processor initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize OCR processor: {e}")
            raise
    
    def _register_tools(self) -> None:
        """Register MCP tools."""
        try:
            # Register OCR tools
            self.mcp.tool()(self.extract_text_from_image)
            self.mcp.tool()(self.extract_text_from_batch)
            self.mcp.tool()(self.get_available_languages)
            self.mcp.tool()(self.validate_ocr_installation)
            self.mcp.tool()(self.get_processor_info)
            self.mcp.tool()(self.extract_text_from_base64)
            
            self.logger.info("MCP tools registered successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to register MCP tools: {e}")
            raise
    
    async def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text from a single image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict: OCR results with metadata
        """
        try:
            self.logger.info(f"Extracting text from image: {image_path}")
            
            # Validate image path
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Extract text
            result = self.ocr_processor.extract_text_with_metadata(image_path)
            
            self.logger.info(f"Text extraction completed for {image_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to extract text from {image_path}: {e}")
            raise
    
    async def extract_text_from_batch(self, image_paths: List[str]) -> Dict[str, Any]:
        """
        Extract text from multiple images in batch.
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            Dict: Batch OCR results with statistics
        """
        try:
            self.logger.info(f"Extracting text from batch of {len(image_paths)} images")
            
            # Validate image paths
            valid_paths = []
            for path in image_paths:
                if os.path.exists(path):
                    valid_paths.append(path)
                else:
                    self.logger.warning(f"Image file not found: {path}")
            
            if not valid_paths:
                raise ValueError("No valid image files provided")
            
            # Extract text in batch
            result = self.ocr_processor.extract_batch(valid_paths)
            
            self.logger.info(f"Batch text extraction completed for {len(valid_paths)} images")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to extract text from batch: {e}")
            raise
    
    async def extract_text_from_base64(self, base64_image: str, image_format: str = "png") -> Dict[str, Any]:
        """
        Extract text from a base64 encoded image.
        
        Args:
            base64_image: Base64 encoded image string
            image_format: Image format (png, jpg, jpeg, etc.)
            
        Returns:
            Dict: OCR results with metadata
        """
        try:
            self.logger.info("Extracting text from base64 image")
            
            # Decode base64 image
            try:
                image_data = base64.b64decode(base64_image)
            except Exception as e:
                raise ValueError(f"Invalid base64 image data: {e}")
            
            # Create temporary file
            temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            temp_path = os.path.join(temp_dir, f"temp_image.{image_format}")
            
            # Save image to temporary file
            with open(temp_path, 'wb') as f:
                f.write(image_data)
            
            # Extract text
            result = self.ocr_processor.extract_text_with_metadata(temp_path)
            
            # Clean up temporary file
            try:
                os.remove(temp_path)
            except:
                pass
            
            self.logger.info("Text extraction from base64 image completed")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to extract text from base64 image: {e}")
            raise
    
    async def get_available_languages(self) -> List[str]:
        """
        Get list of available OCR languages.
        
        Returns:
            List: Available language codes
        """
        try:
            languages = self.ocr_processor.get_available_languages()
            self.logger.info(f"Retrieved {len(languages)} available languages")
            return languages
            
        except Exception as e:
            self.logger.error(f"Failed to get available languages: {e}")
            raise
    
    async def validate_ocr_installation(self) -> Dict[str, Any]:
        """
        Validate OCR installation and dependencies.
        
        Returns:
            Dict: Validation results
        """
        try:
            self.logger.info("Validating OCR installation")
            
            is_valid = self.ocr_processor.validate_installation()
            processor_info = self.ocr_processor.get_processor_info()
            
            result = {
                'valid': is_valid,
                'processor_info': processor_info,
                'timestamp': str(asyncio.get_event_loop().time())
            }
            
            self.logger.info(f"OCR installation validation completed: {is_valid}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to validate OCR installation: {e}")
            raise
    
    async def get_processor_info(self) -> Dict[str, Any]:
        """
        Get processor information and configuration.
        
        Returns:
            Dict: Processor information
        """
        try:
            info = self.ocr_processor.get_processor_info()
            self.logger.info("Retrieved processor information")
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get processor info: {e}")
            raise
    
    async def start_server(self) -> None:
        """Start the MCP server."""
        try:
            self.logger.info("Starting EasyOCR MCP Server")
            
            # Start server with stdio transport
            async with stdio_server() as (read_stream, write_stream):
                await self.mcp.run(
                    read_stream,
                    write_stream,
                    create_task=asyncio.create_task
                )
                
        except Exception as e:
            self.logger.error(f"Failed to start MCP server: {e}")
            raise
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        return {
            'server_name': 'EasyOCR MCP Server',
            'version': '1.0.0',
            'description': 'MCP server for EasyOCR with low-resource optimizations',
            'author': 'Kilo Code',
            'config_path': self.config_path,
            'processor_info': self.ocr_processor.get_processor_info() if self.ocr_processor else None
        }


def create_server(config_path: Optional[str] = None) -> EasyOCRMCPServer:
    """
    Create and return an EasyOCR MCP server instance.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        EasyOCRMCPServer: Server instance
    """
    return EasyOCRMCPServer(config_path)


async def main() -> None:
    """Main entry point for the MCP server."""
    try:
        # Create server with default config
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'easyocr_mcp_config.json')
        server = create_server(config_path)
        
        # Start server
        await server.start_server()
        
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())