#!/usr/bin/env python3
"""
Basic Everything Search MCP Server Integration Test

This script performs basic integration tests without requiring MCP dependencies.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def test_file_structure():
    """Test if all required files exist."""
    print("Testing file structure...")
    
    base_path = Path(__file__).parent
    
    # Check required files
    required_files = [
        "mcp_everything_search_fixed.py",
        "src/everything_search_mcp_server.py",
        "config/everything_search_mcp_config.json",
        "requirements.txt"
    ]
    
    for file_path in required_files:
        full_path = base_path / file_path
        if not full_path.exists():
            print(f"FAIL: Missing file: {file_path}")
            return False
        print(f"PASS: Found file: {file_path}")
    
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
            print("PASS: SDK path uses environment variable (expected)")
        else:
            print(f"INFO: SDK path configured: {sdk_path}")
        
        return True
        
    except Exception as e:
        print(f"FAIL: Configuration test failed: {e}")
        return False

def test_main_config_integration():
    """Test integration with main MCP servers config."""
    print("\nTesting main MCP config integration...")
    
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
        
        # Check if the script path is correct
        expected_script = "./everything-search-mcp/mcp_everything_search_fixed.py"
        if everything_search_config['script'] != expected_script:
            print(f"FAIL: Incorrect script path. Expected: {expected_script}, Got: {everything_search_config['script']}")
            return False
        
        # Check if environment variables are set
        expected_env = {
            "EVERYTHING_SDK_PATH": "C:\\Users\\salib\\Everything64.dll",
            "NODE_ENV": "development"
        }
        
        if everything_search_config['env'] != expected_env:
            print(f"FAIL: Incorrect environment variables. Expected: {expected_env}, Got: {everything_search_config['env']}")
            return False
        
        print("PASS: Environment variables correctly configured")
        
        return True
        
    except Exception as e:
        print(f"FAIL: Main MCP config test failed: {e}")
        return False

def test_launcher_script():
    """Test if the launcher script can be executed."""
    print("\nTesting launcher script...")
    
    try:
        launcher_path = Path(__file__).parent / "mcp_everything_search_fixed.py"
        
        # Test if the script can be executed (help command)
        result = subprocess.run([sys.executable, str(launcher_path), '--help'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("PASS: Launcher script can be executed")
            return True
        else:
            print(f"FAIL: Launcher script execution failed: {result.stderr}")
            return False
        
    except Exception as e:
        print(f"FAIL: Launcher script test failed: {e}")
        return False

def test_requirements():
    """Test if requirements.txt is valid."""
    print("\nTesting requirements.txt...")
    
    try:
        requirements_path = Path(__file__).parent / "requirements.txt"
        
        with open(requirements_path, 'r') as f:
            requirements = f.read()
        
        # Check for key requirements
        key_requirements = [
            "mcp",
            "pywin32",
            "asyncio",
            "datetime"
        ]
        
        for req in key_requirements:
            if req.lower() not in requirements.lower():
                print(f"FAIL: Missing requirement: {req}")
                return False
        
        print("PASS: requirements.txt contains key dependencies")
        return True
        
    except Exception as e:
        print(f"FAIL: requirements.txt test failed: {e}")
        return False

def main():
    """Run all basic integration tests."""
    print("Everything Search MCP Server Basic Integration Test")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Configuration", test_configuration),
        ("Main MCP Config Integration", test_main_config_integration),
        ("Launcher Script", test_launcher_script),
        ("Requirements", test_requirements),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"FAIL: {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Basic Integration Test Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("SUCCESS: All basic integration tests passed!")
        print("\nThe Everything Search MCP Server is properly integrated.")
        print("To use the server, ensure Everything Search is installed and")
        print("the EVERYTHING_SDK_PATH environment variable is set correctly.")
        return 0
    else:
        print("WARNING: Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())