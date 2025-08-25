"""
Everything Search MCP Server

This module provides the MCP (Model Context Protocol) server for Everything Search.
It handles MCP protocol communication and exposes file search functionality through the Everything SDK.

Author: Kilo Code
Version: 1.0.0
"""

import os
import sys
import json
import logging
import asyncio
import ctypes
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime

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

# Everything SDK imports
try:
    import everything_sdk
except ImportError:
    print("Everything SDK not found. Please install everything-sdk.")
    sys.exit(1)


class EverythingSearchMCPServer:
    """
    Everything Search MCP Server that implements the MCP protocol.
    Provides fast local file search functionality through Everything SDK.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Everything Search MCP server.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        
        # Initialize MCP server
        self.mcp = FastMCP("Everything Search MCP Server")
        
        # Setup logging
        self._setup_logging()
        
        # Initialize Everything SDK
        self._initialize_everything_sdk()
        
        # Register tools
        self._register_tools()
        
        self.logger.info("Everything Search MCP Server initialized")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        try:
            # Default logging configuration
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler('everything_search_mcp.log'),
                    logging.StreamHandler()
                ]
            )
            
            self.logger.info("Logging configured successfully")
            
        except Exception as e:
            print(f"Failed to setup logging: {e}")
            # Fallback to basic logging
            logging.basicConfig(level=logging.INFO)
    
    def _initialize_everything_sdk(self) -> None:
        """Initialize the Everything SDK with configuration."""
        try:
            # Get SDK path from environment
            self.sdk_path = os.environ.get('EVERYTHING_SDK_PATH')
            
            if not self.sdk_path:
                raise ValueError("EVERYTHING_SDK_PATH environment variable not set")
            
            # Validate SDK path
            if not os.path.exists(self.sdk_path):
                raise FileNotFoundError(f"Everything SDK not found at: {self.sdk_path}")
            
            # Load the Everything SDK
            try:
                ctypes.WinDLL(self.sdk_path)
                self.sdk_available = True
                self.logger.info(f"Everything SDK loaded successfully from: {self.sdk_path}")
            except Exception as e:
                self.sdk_available = False
                self.logger.error(f"Failed to load Everything SDK: {e}")
                raise
            
            # Initialize Everything SDK
            everything_sdk.initialize()
            self.logger.info("Everything SDK initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Everything SDK: {e}")
            self.sdk_available = False
            raise
    
    def _register_tools(self) -> None:
        """Register MCP tools."""
        try:
            # Register search tools
            self.mcp.tool()(self.search_files)
            self.mcp.tool()(self.search_files_advanced)
            self.mcp.tool()(self.get_file_info)
            self.mcp.tool()(self.list_drives)
            self.mcp.tool()(self.validate_sdk_installation)
            self.mcp.tool()(self.get_server_info)
            self.mcp.tool()(self.search_by_extension)
            self.mcp.tool()(self.search_by_size)
            self.mcp.tool()(self.search_by_date)
            
            self.logger.info("MCP tools registered successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to register MCP tools: {e}")
            raise
    
    async def search_files(self, query: str, max_results: int = 100) -> Dict[str, Any]:
        """
        Search for files using a simple query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            Dict: Search results with metadata
        """
        try:
            self.logger.info(f"Searching for files with query: {query}")
            
            if not self.sdk_available:
                raise RuntimeError("Everything SDK is not available")
            
            # Perform search
            results = everything_sdk.search(query, max_results)
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'name': result.get('name', ''),
                    'path': result.get('path', ''),
                    'size': result.get('size', 0),
                    'modified': result.get('modified', ''),
                    'extension': result.get('extension', ''),
                    'is_directory': result.get('is_directory', False)
                })
            
            self.logger.info(f"Found {len(formatted_results)} results for query: {query}")
            
            return {
                'query': query,
                'results': formatted_results,
                'total_count': len(formatted_results),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to search files: {e}")
            raise
    
    async def search_files_advanced(self, query: str, max_results: int = 100, 
                                   case_sensitive: bool = False, 
                                   whole_word: bool = False,
                                   regex: bool = False) -> Dict[str, Any]:
        """
        Search for files using advanced search options.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            case_sensitive: Whether search is case sensitive
            whole_word: Whether to match whole words only
            regex: Whether to use regex pattern matching
            
        Returns:
            Dict: Search results with metadata
        """
        try:
            self.logger.info(f"Advanced search for files with query: {query}")
            
            if not self.sdk_available:
                raise RuntimeError("Everything SDK is not available")
            
            # Set search options
            everything_sdk.set_case_sensitive(case_sensitive)
            everything_sdk.set_whole_word(whole_word)
            everything_sdk.set_regex(regex)
            
            # Perform search
            results = everything_sdk.search(query, max_results)
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'name': result.get('name', ''),
                    'path': result.get('path', ''),
                    'size': result.get('size', 0),
                    'modified': result.get('modified', ''),
                    'extension': result.get('extension', ''),
                    'is_directory': result.get('is_directory', False)
                })
            
            # Reset search options
            everything_sdk.set_case_sensitive(False)
            everything_sdk.set_whole_word(False)
            everything_sdk.set_regex(False)
            
            self.logger.info(f"Found {len(formatted_results)} results for advanced query: {query}")
            
            return {
                'query': query,
                'results': formatted_results,
                'total_count': len(formatted_results),
                'options': {
                    'case_sensitive': case_sensitive,
                    'whole_word': whole_word,
                    'regex': regex
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to perform advanced search: {e}")
            raise
    
    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dict: File information
        """
        try:
            self.logger.info(f"Getting file info for: {file_path}")
            
            if not self.sdk_available:
                raise RuntimeError("Everything SDK is not available")
            
            # Get file information
            info = everything_sdk.get_file_info(file_path)
            
            if not info:
                raise FileNotFoundError(f"File not found: {file_path}")
            
            self.logger.info(f"Retrieved info for file: {file_path}")
            
            return {
                'path': file_path,
                'name': info.get('name', ''),
                'size': info.get('size', 0),
                'modified': info.get('modified', ''),
                'created': info.get('created', ''),
                'accessed': info.get('accessed', ''),
                'extension': info.get('extension', ''),
                'is_directory': info.get('is_directory', False),
                'is_hidden': info.get('is_hidden', False),
                'is_system': info.get('is_system', False),
                'is_readonly': info.get('is_readonly', False),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get file info: {e}")
            raise
    
    async def list_drives(self) -> List[Dict[str, Any]]:
        """
        List available drives.
        
        Returns:
            List: Drive information
        """
        try:
            self.logger.info("Listing available drives")
            
            if not self.sdk_available:
                raise RuntimeError("Everything SDK is not available")
            
            # Get drives
            drives = everything_sdk.list_drives()
            
            formatted_drives = []
            for drive in drives:
                formatted_drives.append({
                    'name': drive.get('name', ''),
                    'path': drive.get('path', ''),
                    'type': drive.get('type', ''),
                    'size': drive.get('size', 0),
                    'free_space': drive.get('free_space', 0),
                    'is_ready': drive.get('is_ready', False)
                })
            
            self.logger.info(f"Found {len(formatted_drives)} drives")
            
            return formatted_drives
            
        except Exception as e:
            self.logger.error(f"Failed to list drives: {e}")
            raise
    
    async def search_by_extension(self, extension: str, max_results: int = 100) -> Dict[str, Any]:
        """
        Search for files by extension.
        
        Args:
            extension: File extension (e.g., "txt", "pdf")
            max_results: Maximum number of results to return
            
        Returns:
            Dict: Search results
        """
        try:
            self.logger.info(f"Searching for files with extension: {extension}")
            
            if not self.sdk_available:
                raise RuntimeError("Everything SDK is not available")
            
            # Perform search by extension
            query = f"*.{extension}"
            results = everything_sdk.search(query, max_results)
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'name': result.get('name', ''),
                    'path': result.get('path', ''),
                    'size': result.get('size', 0),
                    'modified': result.get('modified', ''),
                    'extension': result.get('extension', ''),
                    'is_directory': result.get('is_directory', False)
                })
            
            self.logger.info(f"Found {len(formatted_results)} files with extension: {extension}")
            
            return {
                'extension': extension,
                'results': formatted_results,
                'total_count': len(formatted_results),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to search by extension: {e}")
            raise
    
    async def search_by_size(self, min_size: int = 0, max_size: int = None, 
                           size_unit: str = "bytes", max_results: int = 100) -> Dict[str, Any]:
        """
        Search for files by size.
        
        Args:
            min_size: Minimum file size
            max_size: Maximum file size (None for no limit)
            size_unit: Unit of size (bytes, KB, MB, GB)
            max_results: Maximum number of results to return
            
        Returns:
            Dict: Search results
        """
        try:
            self.logger.info(f"Searching for files by size: {min_size}-{max_size} {size_unit}")
            
            if not self.sdk_available:
                raise RuntimeError("Everything SDK is not available")
            
            # Convert size to bytes
            size_multiplier = {
                'bytes': 1,
                'kb': 1024,
                'mb': 1024 * 1024,
                'gb': 1024 * 1024 * 1024
            }
            
            multiplier = size_multiplier.get(size_unit.lower(), 1)
            min_bytes = min_size * multiplier
            max_bytes = max_size * multiplier if max_size else None
            
            # Perform search
            results = everything_sdk.search_by_size(min_bytes, max_bytes, max_results)
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'name': result.get('name', ''),
                    'path': result.get('path', ''),
                    'size': result.get('size', 0),
                    'modified': result.get('modified', ''),
                    'extension': result.get('extension', ''),
                    'is_directory': result.get('is_directory', False)
                })
            
            self.logger.info(f"Found {len(formatted_results)} files in size range")
            
            return {
                'size_range': {
                    'min': min_size,
                    'max': max_size,
                    'unit': size_unit
                },
                'results': formatted_results,
                'total_count': len(formatted_results),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to search by size: {e}")
            raise
    
    async def search_by_date(self, date_from: str = None, date_to: str = None, 
                           date_format: str = "%Y-%m-%d", max_results: int = 100) -> Dict[str, Any]:
        """
        Search for files by modification date.
        
        Args:
            date_from: Start date (YYYY-MM-DD format)
            date_to: End date (YYYY-MM-DD format)
            date_format: Date format string
            max_results: Maximum number of results to return
            
        Returns:
            Dict: Search results
        """
        try:
            self.logger.info(f"Searching for files by date: {date_from} to {date_to}")
            
            if not self.sdk_available:
                raise RuntimeError("Everything SDK is not available")
            
            # Parse dates
            from_date = None
            to_date = None
            
            if date_from:
                from_date = datetime.strptime(date_from, date_format)
            if date_to:
                to_date = datetime.strptime(date_to, date_format)
            
            # Perform search
            results = everything_sdk.search_by_date(from_date, to_date, max_results)
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'name': result.get('name', ''),
                    'path': result.get('path', ''),
                    'size': result.get('size', 0),
                    'modified': result.get('modified', ''),
                    'extension': result.get('extension', ''),
                    'is_directory': result.get('is_directory', False)
                })
            
            self.logger.info(f"Found {len(formatted_results)} files in date range")
            
            return {
                'date_range': {
                    'from': date_from,
                    'to': date_to,
                    'format': date_format
                },
                'results': formatted_results,
                'total_count': len(formatted_results),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to search by date: {e}")
            raise
    
    async def validate_sdk_installation(self) -> Dict[str, Any]:
        """
        Validate Everything SDK installation and dependencies.
        
        Returns:
            Dict: Validation results
        """
        try:
            self.logger.info("Validating Everything SDK installation")
            
            sdk_info = {
                'sdk_path': self.sdk_path,
                'sdk_available': self.sdk_available,
                'sdk_version': None,
                'error_message': None
            }
            
            if self.sdk_available:
                try:
                    # Try to get SDK version
                    version = everything_sdk.get_version()
                    sdk_info['sdk_version'] = version
                except:
                    sdk_info['sdk_version'] = "Unknown"
            else:
                sdk_info['error_message'] = "Everything SDK not available"
            
            result = {
                'valid': self.sdk_available,
                'sdk_info': sdk_info,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"SDK validation completed: {self.sdk_available}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to validate SDK installation: {e}")
            raise
    
    async def start_server(self) -> None:
        """Start the MCP server."""
        try:
            self.logger.info("Starting Everything Search MCP Server")
            
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
            'server_name': 'Everything Search MCP Server',
            'version': '1.0.0',
            'description': 'MCP server for Everything Search with fast local file search',
            'author': 'Kilo Code',
            'config_path': self.config_path,
            'sdk_info': {
                'sdk_path': self.sdk_path,
                'sdk_available': self.sdk_available,
                'sdk_version': None
            }
        }


def create_server(config_path: Optional[str] = None) -> EverythingSearchMCPServer:
    """
    Create and return an Everything Search MCP server instance.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        EverythingSearchMCPServer: Server instance
    """
    return EverythingSearchMCPServer(config_path)


async def main() -> None:
    """Main entry point for the MCP server."""
    try:
        # Create server with default config
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'everything_search_mcp_config.json')
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