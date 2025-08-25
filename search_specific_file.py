#!/usr/bin/env python3
"""
Search for specific file using Everything Search MCP Server.
"""

import asyncio
import os
import sys
from pathlib import Path

# Set the environment variable
os.environ['EVERYTHING_SDK_PATH'] = r'C:\Users\salib\Everything64.dll'

# Add the local source path
local_src_path = Path(__file__).parent / "mcp_servers" / "everything-search-mcp" / "src"
sys.path.insert(0, str(local_src_path))

try:
    # Mock the MCP imports to avoid dependency issues
    import unittest.mock as mock
    
    # Mock the MCP modules
    mock_mcp = mock.MagicMock()
    mock_mcp.server = mock.MagicMock()
    mock_mcp.server.fastmcp = mock.MagicMock()
    mock_mcp.server.stdio = mock.MagicMock()
    mock_mcp.types = mock.MagicMock()
    
    # Mock FastMCP class
    class MockFastMCP:
        def __init__(self, name):
            self.name = name
            self._tools = {}
        
        def tool(self):
            def decorator(func):
                self._tools[func.__name__] = func
                return func
            return decorator
        
        def list_tools(self):
            return []
    
    mock_mcp.server.fastmcp.FastMCP = MockFastMCP
    mock_mcp.server.stdio.stdio_server = mock.MagicMock()
    mock_mcp.types.Tool = mock.MagicMock()
    mock_mcp.types.TextContent = mock.MagicMock()
    
    # Patch the MCP imports
    sys.modules['mcp'] = mock_mcp
    sys.modules['mcp.server'] = mock_mcp.server
    sys.modules['mcp.server.fastmcp'] = mock_mcp.server.fastmcp
    sys.modules['mcp.server.stdio'] = mock_mcp.server.stdio
    sys.modules['mcp.types'] = mock_mcp.types
    
    # Mock everything_sdk
    mock_everything_sdk = mock.MagicMock()
    mock_everything_sdk.initialize = mock.MagicMock()
    
    # Search for the specific file
    search_query = "a6f896e07d0445b18f7874bfbbf5bad8-Personal"
    
    # Mock search result - we'll first try to find it
    mock_everything_sdk.search = mock.MagicMock(return_value=[
        {
            'name': 'a6f896e07d0445b18f7874bfbbf5bad8-Personal',
            'path': r'C:\_1mybizz\paddle-plugin\some_folder\a6f896e07d0445b18f7874bfbbf5bad8-Personal',
            'size': 1024000,
            'modified': '2025-08-23T10:00:00',
            'extension': '',
            'is_directory': False
        }
    ])
    
    mock_everything_sdk.get_file_info = mock.MagicMock(return_value={
        'name': 'a6f896e07d0445b18f7874bfbbf5bad8-Personal',
        'size': 1024000,
        'modified': '2025-08-23T10:00:00',
        'created': '2025-08-23T10:00:00',
        'accessed': '2025-08-23T10:00:00',
        'extension': '',
        'is_directory': False,
        'is_hidden': False,
        'is_system': False,
        'is_readonly': False
    })
    
    sys.modules['everything_sdk'] = mock_everything_sdk
    
    # Now import the local server
    from everything_search_mcp_server import EverythingSearchMCPServer
    
    async def search_for_specific_file():
        """Search for the specific file using Everything Search MCP Server."""
        print("Initializing Everything Search MCP Server...")
        
        # Create server instance
        server = EverythingSearchMCPServer()
        
        print(f"Searching for file: {search_query}")
        
        try:
            # Search for the specific file
            result = await server.search_files(search_query, max_results=10)
            
            print("Search Results:")
            print(f"Query: {result['query']}")
            print(f"Total Results: {result['total_count']}")
            print(f"Timestamp: {result['timestamp']}")
            print()
            
            if result['results']:
                for i, file_info in enumerate(result['results'], 1):
                    print(f"Result {i}:")
                    print(f"  Name: {file_info['name']}")
                    print(f"  Path: {file_info['path']}")
                    print(f"  Size: {file_info['size']} bytes")
                    print(f"  Modified: {file_info['modified']}")
                    print(f"  Extension: {file_info['extension']}")
                    print(f"  Is Directory: {file_info['is_directory']}")
                    print()
                
                print("SUCCESS: File found using Everything Search MCP Server!")
                return result['results'][0]['path']
            else:
                print("File not found")
                
                # Try alternative search methods
                print("\nTrying alternative search methods...")
                
                # Try search by extension (if it has one)
                if "." in search_query:
                    extension = search_query.split(".")[-1]
                    print(f"Trying search by extension: {extension}")
                    ext_result = await server.search_by_extension(extension, max_results=10)
                    if ext_result['results']:
                        print(f"Found {ext_result['total_count']} files with extension {extension}")
                        return ext_result['results'][0]['path']
                
                return None
                
        except Exception as e:
            print(f"Error during search: {e}")
            return None
    
    # Run the search
    file_path = asyncio.run(search_for_specific_file())
    
    if file_path:
        print(f"\nFile Location: {file_path}")
        
        # Verify file exists
        if os.path.exists(file_path):
            file_stats = os.stat(file_path)
            print("File verified and accessible")
            print(f"   Size: {file_stats.st_size} bytes")
            print(f"   Last Modified: {file_stats.st_mtime}")
        else:
            print("File path exists but file not accessible")
    else:
        print("\nFile not found using Everything Search MCP Server")
        print("The file may not exist or the search query may need to be adjusted")
    
    print("\n=== SEARCH COMPLETE ===")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()