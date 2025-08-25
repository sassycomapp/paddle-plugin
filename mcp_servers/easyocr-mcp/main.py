#!/usr/bin/env python3
"""
EasyOCR MCP Server Main Entry Point

This script provides the main entry point for the EasyOCR MCP server.
It handles command-line arguments and starts the server.

Author: Kilo Code
Version: 1.0.0
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from easyocr_mcp_server import create_server, EasyOCRMCPServer


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('easyocr_mcp.log'),
            logging.StreamHandler()
        ]
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='EasyOCR MCP Server - Optimized for Low-Resource Usage'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        default='config/easyocr_mcp_config.json',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--log-level', '-l',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=None,
        help='Port to run the server on (not applicable for stdio mode)'
    )
    
    parser.add_argument(
        '--host', '-H',
        type=str,
        default='localhost',
        help='Host to bind the server to (not applicable for stdio mode)'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate configuration and exit'
    )
    
    parser.add_argument(
        '--info',
        action='store_true',
        help='Display server information and exit'
    )
    
    return parser.parse_args()


def validate_config(config_path: str) -> bool:
    """Validate configuration file."""
    try:
        if not os.path.exists(config_path):
            print(f"Configuration file not found: {config_path}")
            return False
        
        # Try to load configuration
        server = create_server(config_path)
        
        # Validate OCR installation
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(server.validate_ocr_installation())
            is_valid = result['valid']
            
            if is_valid:
                print("Configuration validation successful")
                print(f"Processor info: {result['processor_info']}")
            else:
                print("Configuration validation failed")
                print(f"Processor info: {result['processor_info']}")
            
            return is_valid
            
        finally:
            loop.close()
            
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        return False


def display_server_info(config_path: str) -> None:
    """Display server information."""
    try:
        server = create_server(config_path)
        info = server.get_server_info()
        
        print("EasyOCR MCP Server Information")
        print("=" * 40)
        print(f"Server Name: {info['server_name']}")
        print(f"Version: {info['version']}")
        print(f"Description: {info['description']}")
        print(f"Author: {info['author']}")
        print(f"Config Path: {info['config_path']}")
        
        if info['processor_info']:
            print("\nProcessor Information:")
            print(f"  Languages: {info['processor_info']['languages']}")
            print(f"  GPU Enabled: {info['processor_info']['gpu_enabled']}")
            print(f"  Model Directory: {info['processor_info']['model_storage_directory']}")
            print(f"  Confidence Threshold: {info['processor_info']['confidence_threshold']}")
            print(f"  Model Loaded: {info['processor_info']['model_loaded']}")
        
    except Exception as e:
        print(f"Failed to get server info: {e}")


def main() -> None:
    """Main entry point."""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Handle special commands
    if args.validate:
        success = validate_config(args.config)
        sys.exit(0 if success else 1)
    
    if args.info:
        display_server_info(args.config)
        sys.exit(0)
    
    try:
        print(f"Starting EasyOCR MCP Server with config: {args.config}")
        
        # Create server
        server = create_server(args.config)
        
        # Display server info
        info = server.get_server_info()
        print(f"Server: {info['server_name']} v{info['version']}")
        print(f"Languages: {info['processor_info']['languages']}")
        print(f"GPU: {'Enabled' if info['processor_info']['gpu_enabled'] else 'Disabled'}")
        print(f"Model Directory: {info['processor_info']['model_storage_directory']}")
        print(f"Max Image Size: {info['processor_info']['preprocessing_settings']['max_image_size']}px")
        print(f"Use Grayscale: {info['processor_info']['preprocessing_settings']['use_grayscale']}")
        print(f"Use Binarization: {info['processor_info']['preprocessing_settings']['use_binarization']}")
        print(f"Batch Size: {info['processor_info']['batch_settings']['batch_size']}")
        print(f"Confidence Threshold: {info['processor_info']['confidence_threshold']}")
        print("\nPress Ctrl+C to stop the server")
        
        # Start server
        import asyncio
        asyncio.run(server.start_server())
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()