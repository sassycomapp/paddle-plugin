#!/usr/bin/env python3
"""
Everything Search MCP Server - Fixed Launcher

This script provides the main entry point for the Everything Search MCP server.
It handles command-line arguments and starts the server with proper PyWin32 fixes.

Author: Kilo Code
Version: 1.0.0
"""

import os
import sys
import argparse
import logging
import asyncio
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# PyWin32 fix - ensure proper DLL loading
try:
    import ctypes
    everything_sdk_path = os.environ.get('EVERYTHING_SDK_PATH')
    if everything_sdk_path:
        # Load the Everything SDK DLL with proper error handling
        try:
            ctypes.WinDLL(everything_sdk_path)
            print(f"Everything SDK loaded successfully from: {everything_sdk_path}")
        except Exception as e:
            print(f"Warning: Could not load Everything SDK from {everythingthing_sdk_path}: {e}")
            print("Please ensure the Everything Search application is installed and the SDK path is correct.")
    else:
        print("Warning: EVERYTHING_SDK_PATH environment variable not set")
        print("Please set this environment variable to point to Everything64.dll")
except Exception as e:
    print(f"Error setting up PyWin32 environment: {e}")

# MCP imports
try:
    from mcp.server.fastmcp import FastMCP
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    import mcp.server.stdio
    import mcp.types
except ImportError as e:
    print(f"MCP package not found: {e}")
    print("Please install MCP dependencies: pip install mcp")
    sys.exit(1)

# Local imports
try:
    from everything_search_mcp_server import EverythingSearchMCPServer
except ImportError as e:
    print(f"Could not import Everything Search MCP server: {e}")
    print("Please ensure the server module is in the src directory")
    sys.exit(1)


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration."""
    try:
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('everything_search_mcp.log'),
                logging.StreamHandler()
            ]
        )
    except Exception as e:
        print(f"Failed to setup logging: {e}")
        # Fallback to basic logging
        logging.basicConfig(level=logging.INFO)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Everything Search MCP Server - Fast local file search via MCP'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        default='config/everything_search_mcp_config.json',
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
        server = EverythingSearchMCPServer(config_path)
        
        # Validate Everything SDK installation
        result = server.validate_sdk_installation()
        
        if result['valid']:
            print("Configuration validation successful")
            print(f"SDK info: {result['sdk_info']}")
        else:
            print("Configuration validation failed")
            print(f"SDK info: {result['sdk_info']}")
        
        return result['valid']
        
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        return False


def display_server_info(config_path: str) -> None:
    """Display server information."""
    try:
        server = EverythingSearchMCPServer(config_path)
        info = server.get_server_info()
        
        print("Everything Search MCP Server Information")
        print("=" * 50)
        print(f"Server Name: {info['server_name']}")
        print(f"Version: {info['version']}")
        print(f"Description: {info['description']}")
        print(f"Author: {info['author']}")
        print(f"Config Path: {info['config_path']}")
        
        if info['sdk_info']:
            print("\nSDK Information:")
            print(f"  SDK Path: {info['sdk_info']['sdk_path']}")
            print(f"  SDK Available: {info['sdk_info']['sdk_available']}")
            print(f"  SDK Version: {info['sdk_info']['sdk_version']}")
        
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
        print(f"Starting Everything Search MCP Server with config: {args.config}")
        
        # Create server
        server = EverythingSearchMCPServer(args.config)
        
        # Display server info
        info = server.get_server_info()
        print(f"Server: {info['server_name']} v{info['version']}")
        
        sdk_info = info.get('sdk_info', {})
        print(f"SDK Available: {sdk_info.get('sdk_available', False)}")
        if sdk_info.get('sdk_available'):
            print(f"SDK Path: {sdk_info.get('sdk_path', 'Not set')}")
            print(f"SDK Version: {sdk_info.get('sdk_version', 'Unknown')}")
        
        print("\nPress Ctrl+C to stop the server")
        
        # Start server
        asyncio.run(server.start_server())
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()