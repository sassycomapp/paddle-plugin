#!/usr/bin/env python3
"""
Direct test script for MCP Scheduler server.
This script tests the MCP Scheduler server directly without using the MCP Python client.
"""

import subprocess
import json
import time
import os
import sys
from pathlib import Path

def test_mcp_scheduler_server():
    """Test the MCP Scheduler server directly."""
    print("Testing MCP Scheduler Server directly...")
    
    # Get the path to the MCP Scheduler server
    server_path = Path("C:/_1mybizz/paddle-plugin/mcp_servers/mcp-scheduler-server.js")
    
    if not server_path.exists():
        print(f"Error: MCP Scheduler server not found at {server_path}")
        return False
    
    print(f"Found MCP Scheduler server at: {server_path}")
    
    # Test if Node.js is available
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("Error: Node.js is not available or not working correctly")
            return False
        print(f"Node.js version: {result.stdout.strip()}")
    except FileNotFoundError:
        print("Error: Node.js is not installed or not in PATH")
        return False
    
    # Try to start the server and check if it loads correctly
    try:
        print("Attempting to start MCP Scheduler server...")
        process = subprocess.Popen(
            ["node", str(server_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it a moment to start
        time.sleep(3)
        
        # Check if the process is still running
        if process.poll() is None:
            print("MCP Scheduler server started successfully")
            process.terminate()
            process.wait()
            return True
        else:
            # Process terminated, check output
            stdout, stderr = process.communicate()
            print(f"Server output: {stdout}")
            if stderr:
                print(f"Server errors: {stderr}")
            return False
            
    except Exception as e:
        print(f"Error testing MCP Scheduler server: {str(e)}")
        return False

def test_package_json():
    """Test if the package.json has the correct dependencies."""
    print("\nTesting package.json...")
    
    package_json_path = Path("C:/_1mybizz/paddle-plugin/mcp_servers/package.json")
    
    if not package_json_path.exists():
        print(f"Error: package.json not found at {package_json_path}")
        return False
    
    try:
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
        
        print("package.json contents:")
        print(json.dumps(package_data, indent=2))
        
        # Check if required dependencies are present
        required_deps = ["sqlite3", "node-schedule", "winston"]
        dependencies = package_data.get("dependencies", {})
        
        for dep in required_deps:
            if dep in dependencies:
                print(f"✓ {dep}: {dependencies[dep]}")
            else:
                print(f"✗ {dep}: NOT FOUND")
                return False
        
        return True
        
    except Exception as e:
        print(f"Error reading package.json: {str(e)}")
        return False

def main():
    """Main test function."""
    print("=== MCP Scheduler Direct Test ===\n")
    
    # Test package.json
    package_test = test_package_json()
    
    # Test server
    server_test = test_mcp_scheduler_server()
    
    print("\n=== Test Results ===")
    print(f"Package.json test: {'PASSED' if package_test else 'FAILED'}")
    print(f"Server test: {'PASSED' if server_test else 'FAILED'}")
    
    if package_test and server_test:
        print("\n✓ All tests passed! MCP Scheduler is properly installed and configured.")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
