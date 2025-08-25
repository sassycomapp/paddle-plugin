#!/usr/bin/env python
"""
Script to run MCP Everything Search Server with proper PyWin32 configuration.
This script ensures that the user site-packages directory is in Python's path
so that PyWin32 modules can be imported correctly.
"""

import os
import sys
import subprocess
import site

def add_user_site_packages_to_path():
    """Add user site-packages directory to Python path"""
    user_site = site.getusersitepackages()
    if user_site and user_site not in sys.path:
        sys.path.insert(0, user_site)
        print(f"Added user site-packages to path: {user_site}")

def test_pywin32_import():
    """Test if PyWin32 modules can be imported"""
    try:
        import pywintypes
        import pythoncom
        print("SUCCESS: PyWin32 modules imported successfully")
        return True
    except ImportError as e:
        print(f"ERROR: Failed to import PyWin32 modules: {e}")
        return False

def test_everything_sdk():
    """Test if Everything SDK can be loaded"""
    try:
        import ctypes
        everything_sdk_path = os.environ.get('EVERYTHING_SDK_PATH')
        if everything_sdk_path:
            ctypes.WinDLL(everything_sdk_path)
            print(f"SUCCESS: Everything SDK loaded successfully from: {everything_sdk_path}")
            return True
        else:
            print("ERROR: EVERYTHING_SDK_PATH environment variable not set")
            return False
    except Exception as e:
        print(f"ERROR: Error loading Everything SDK: {e}")
        return False

def run_mcp_server():
    """Run the MCP Everything Search Server"""
    try:
        # Import the MCP server
        from mcp_server_everything_search import main
        print("Starting MCP Everything Search Server...")
        main()
    except ImportError as e:
        print(f"ERROR: Failed to import MCP server: {e}")
        print("Make sure mcp-server-everything-search is installed")
        return False
    except Exception as e:
        print(f"ERROR: Error running MCP server: {e}")
        return False

def main():
    """Main function"""
    print("=== MCP Everything Search Server Launcher ===")
    
    # Add user site-packages to path
    add_user_site_packages_to_path()
    
    # Test PyWin32 import
    if not test_pywin32_import():
        print("Cannot proceed without PyWin32 modules")
        return 1
    
    # Test Everything SDK
    if not test_everything_sdk():
        print("Cannot proceed without Everything SDK")
        return 1
    
    # Run MCP server
    if run_mcp_server():
        print("SUCCESS: MCP server started successfully")
        return 0
    else:
        print("ERROR: Failed to start MCP server")
        return 1

if __name__ == "__main__":
    sys.exit(main())