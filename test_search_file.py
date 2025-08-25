#!/usr/bin/env python3
"""
Test script to use Everything Search MCP Server to find the file.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "mcp_servers" / "everything-search-mcp" / "src"))

# Set the environment variable
os.environ['EVERYTHING_SDK_PATH'] = r'C:\Users\salib\Everything64.dll'

try:
    from everything_search_mcp_server import EverythingSearchMCPServer
    
    async def search_for_file():
        """Search for the specific file using Everything Search MCP Server."""
        print("Initializing Everything Search MCP Server...")
        
        # Create server instance
        server = EverythingSearchMCPServer()
        
        print("Searching for file: A.0 Mybizz system.png")
        
        try:
            # Search for the specific file
            result = await server.search_files("A.0 Mybizz system.png", max_results=10)
            
            print(f"Search Results:")
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
                
                print("✅ SUCCESS: File 'A.0 Mybizz system.png' found using Everything Search MCP Server!")
                return result['results'][0]['path']
            else:
                print("❌ File not found")
                return None
                
        except Exception as e:
            print(f"❌ Error during search: {e}")
            return None
    
    # Run the search
    file_path = asyncio.run(search_for_file())
    
    if file_path:
        print(f"\n📍 File Location: {file_path}")
        
        # Verify file exists
        if os.path.exists(file_path):
            file_stats = os.stat(file_path)
            print(f"✅ File verified and accessible")
            print(f"   Size: {file_stats.st_size} bytes")
            print(f"   Last Modified: {file_stats.st_mtime}")
        else:
            print("❌ File path exists but file not accessible")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure everything_sdk is properly installed")
except Exception as e:
    print(f"❌ Unexpected error: {e}")