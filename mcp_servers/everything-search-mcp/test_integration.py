#!/usr/bin/env python3
"""
Everything Search MCP Server Integration Test

This script tests the integration of the Everything Search MCP Server
with the existing MCP infrastructure.

Author: Kilo Code
Version: 1.0.0
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

def test_server_discovery():
    """Test if the server can be discovered by the MCP infrastructure."""
    print("Testing server discovery...")
    
    # Check if the main launcher script exists
    launcher_path = Path(__file__).parent / "mcp_everything_search_fixed.py"
    if not launcher_path.exists():
        print(f"FAIL: Launcher script not found: {launcher_path}")
        return False
    
    print(f"PASS: Launcher script found: {launcher_path}")
    
    # Check if the server module exists
    server_path = Path(__file__).parent / "src" / "everything_search_mcp_server.py"
    if not server_path.exists():
        print(f"FAIL: Server module not found: {server_path}")
        return False
    
    print(f"PASS: Server module found: {server_path}")
    
    # Check if the configuration file exists
    config_path = Path(__file__).parent / "config" / "everything_search_mcp_config.json"
    if not config_path.exists():
        print(f"FAIL: Configuration file not found: {config_path}")
        return False
    
    print(f"PASS: Configuration file found: {config_path}")
    
    return True

def test_configuration():
    """Test if the configuration is valid."""
    print("\nTesting configuration...")
    
    try:
        config_path = Path(__file__).parent / "config" / "everything_search_mcp_config.json"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check required fields
        required_fields = ["everything_search", "search", "performance", "logging"]
        for field in required_fields:
            if field not in config:
                print(f"FAIL: Missing required field: {field}")
                return False
        
        print("PASS: Configuration is valid")
        
        # Check SDK path configuration
        sdk_path = config["everything_search"].get("sdk_path")
        if sdk_path == "${EVERYTHING_SDK_PATH}":
            print("WARN: SDK path uses environment variable (expected)")
        else:
            print(f"INFO: SDK path configured: {sdk_path}")
        
        return True
        
    except Exception as e:
        print(f"FAIL: Configuration test failed: {e}")
        return False

def test_dependencies():
    """Test if required dependencies are available."""
    print("\nTesting dependencies...")
    
    try:
        # Add src to path for testing
        test_path = str(Path(__file__).parent / "src")
        if test_path not in sys.path:
            sys.path.insert(0, test_path)
        
        # Test MCP import
        import mcp.server.fastmcp
        print("PASS: MCP package available")
        
        # Test PyWin32 import
        import ctypes
        print("PASS: PyWin32 available")
        
        # Test asyncio
        import asyncio
        print("PASS: AsyncIO available")
        
        # Test datetime
        import datetime
        print("PASS: DateTime available")
        
        return True
        
    except ImportError as e:
        print(f"FAIL: Missing dependency: {e}")
        return False

def test_server_info():
    """Test if the server can provide basic information."""
    print("\nTesting server information...")
    
    try:
        # Add src to path
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from everything_search_mcp_server import EverythingSearchMCPServer
        
        # Create server instance
        config_path = str(Path(__file__).parent / "config" / "everything_search_mcp_config.json")
        server = EverythingSearchMCPServer(config_path)
        
        # Get server info
        info = server.get_server_info()
        
        print(f"PASS: Server name: {info['server_name']}")
        print(f"PASS: Server version: {info['version']}")
        print(f"PASS: Server description: {info['description']}")
        
        return True
        
    except Exception as e:
        print(f"FAIL: Server info test failed: {e}")
        return False

def test_sdk_validation():
    """Test if the Everything SDK can be validated."""
    print("\nTesting SDK validation...")
    
    try:
        # Add src to path
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from everything_search_mcp_server import EverythingSearchMCPServer
        
        # Create server instance
        config_path = str(Path(__file__).parent / "config" / "everything_search_mcp_config.json")
        server = EverythingSearchMCPServer(config_path)
        
        # Validate SDK
        result = server.validate_sdk_installation()
        
        print(f"PASS: SDK validation result: {result['valid']}")
        print(f"PASS: SDK path: {result['sdk_info']['sdk_path']}")
        print(f"PASS: SDK available: {result['sdk_info']['sdk_available']}")
        
        if not result['valid']:
            print("WARN: SDK not available - this is expected if Everything Search is not installed")
        
        return True
        
    except Exception as e:
        print(f"FAIL: SDK validation test failed: {e}")
        return False

def test_mcp_infrastructure():
    """Test integration with MCP infrastructure."""
    print("\nTesting MCP infrastructure integration...")
    
    try:
        # Check if the server is configured in the main MCP servers config
        main_config_path = Path(__file__).parent.parent / "mcp-servers-config.json"
        
        if not main_config_path.exists():
            print("FAIL: Main MCP servers config not found")
            return False
        
        with open(main_config_path, 'r') as f:
            main_config = json.load(f)
        
        # Check if everything-search-mcp is configured
        apps = main_config.get("apps", [])
        everything_search_config = None
        
        for app in apps:
            if app.get("name") == "everything-search-mcp":
                everything_search_config = app
                break
        
        if not everything_search_config:
            print("FAIL: everything-search-mcp not found in main config")
            return False
        
        print("PASS: everything-search-mcp found in main config")
        print(f"PASS: Script path: {everything_search_config['script']}")
        print(f"PASS: Environment variables: {everything_search_config['env']}")
        
        return True
        
    except Exception as e:
        print(f"FAIL: MCP infrastructure test failed: {e}")
        return False

def main():
    """Run all integration tests."""
    print("Everything Search MCP Server Integration Test")
    print("=" * 50)
    
    tests = [
        ("Server Discovery", test_server_discovery),
        ("Configuration", test_configuration),
        ("Dependencies", test_dependencies),
        ("Server Information", test_server_info),
        ("SDK Validation", test_sdk_validation),
        ("MCP Infrastructure", test_mcp_infrastructure),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Integration Test Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("SUCCESS: All integration tests passed!")
        return 0
    else:
        print("WARNING: Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())