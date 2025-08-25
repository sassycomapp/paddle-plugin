#!/usr/bin/env python3
"""
Test script for AG2 Orchestration System - Lite Mode
"""

import subprocess
import json
import time
import os
import sys
from pathlib import Path

def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def test_mcp_server(server_name, server_path):
    """Test if an MCP server starts correctly"""
    print(f"Testing {server_name}...")
    
    try:
        # Start the server
        process = subprocess.Popen(
            ["node", server_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it a moment to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print_success(f"{server_name} started successfully")
            process.terminate()
            process.wait()
            return True
        else:
            stdout, stderr = process.communicate()
            print_error(f"{server_name} failed to start")
            if stderr:
                print(f"Error: {stderr}")
            return False
            
    except Exception as e:
        print_error(f"Error testing {server_name}: {e}")
        return False

def test_directory_structure():
    """Test if required directories exist"""
    print_header("Testing Directory Structure")
    
    directories = [
        "mock_memory",
        "mock_rag_data",
        "logs"
    ]
    
    all_exist = True
    for directory in directories:
        if Path(directory).exists():
            print_success(f"Directory exists: {directory}")
        else:
            print_error(f"Directory missing: {directory}")
            all_exist = False
    
    return all_exist

def test_configuration():
    """Test if configuration files exist"""
    print_header("Testing Configuration")
    
    config_files = [
        "mcp_servers_config_lite.json",
        "mcp_servers_config_lite.yaml"
    ]
    
    for config_file in config_files:
        if Path(config_file).exists():
            print_success(f"Configuration file exists: {config_file}")
            
            # Test JSON validity
            if config_file.endswith('.json'):
                try:
                    with open(config_file, 'r') as f:
                        json.load(f)
                    print_success(f"JSON valid: {config_file}")
                except json.JSONDecodeError as e:
                    print_error(f"Invalid JSON in {config_file}: {e}")
                    return False
        else:
            print_error(f"Configuration file missing: {config_file}")
            return False
    
    return True

def test_mock_data():
    """Test if mock data is available"""
    print_header("Testing Mock Data")
    
    # Create sample mock data if it doesn't exist
    rag_data_dir = Path("mock_rag_data")
    if not any(rag_data_dir.iterdir()):
        print_info("Creating sample RAG data...")
        
        sample_data = {
            "ag2_overview": {
                "content": "AG2 is an advanced orchestration system that coordinates multiple AI agents to perform complex tasks. It uses a multi-agent architecture where specialized agents handle different aspects of task execution.",
                "metadata": {
                    "source": "mock_document",
                    "type": "overview"
                }
            },
            "orchestration_benefits": {
                "content": "The benefits of AG2 orchestration include improved task efficiency, better resource utilization, and the ability to handle complex multi-step processes through agent collaboration.",
                "metadata": {
                    "source": "mock_document",
                    "type": "benefits"
                }
            }
        }
        
        with open(rag_data_dir / "sample_data.json", "w") as f:
            json.dump(sample_data, f, indent=2)
        
        print_success("Sample RAG data created")
    
    # Create sample memory data
    memory_dir = Path("mock_memory")
    if not any(memory_dir.iterdir()):
        print_info("Creating sample memory data...")
        
        sample_memory = {
            "agents": {
                "researcher": {
                    "conversations": [],
                    "context": {}
                },
                "coordinator": {
                    "conversations": [],
                    "context": {}
                }
            }
        }
        
        with open(memory_dir / "sample_memory.json", "w") as f:
            json.dump(sample_memory, f, indent=2)
        
        print_success("Sample memory data created")
    
    return True

def test_python_dependencies():
    """Test Python dependencies"""
    print_header("Testing Python Dependencies")
    
    try:
        import yaml
        print_success("PyYAML is available")
        return True
    except ImportError:
        print_error("PyYAML not found. Run: pip install pyyaml")
        return False

def test_node_dependencies():
    """Test Node.js dependencies"""
    print_header("Testing Node.js Dependencies")
    
    try:
        # Check if node_modules exists
        node_modules = Path("../../mcp_servers/node_modules")
        if node_modules.exists():
            print_success("Node.js dependencies installed")
            return True
        else:
            print_error("Node.js dependencies not found. Run: npm install in mcp_servers/")
            return False
    except Exception as e:
        print_error(f"Error checking Node.js dependencies: {e}")
        return False

def main():
    """Main test function"""
    print_header("AG2 Orchestration System - Lite Mode Test")
    
    # Change to correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Test steps
    tests = [
        test_directory_structure,
        test_configuration,
        test_mock_data,
        test_python_dependencies,
        test_node_dependencies
    ]
    
    all_passed = True
    for test in tests:
        try:
            if not test():
                all_passed = False
        except Exception as e:
            print_error(f"Error in {test.__name__}: {e}")
            all_passed = False
    
    # Test MCP servers
    print_header("Testing MCP Servers")
    
    servers = [
        ("RAG Server", "../../mcp_servers/rag-mcp-server-lite.js"),
        ("Agent Memory", "../../mcp_servers/agent-memory-lite.js"),
        ("Brave Search", "../../mcp_servers/brave-search-mcp-server-lite.js")
    ]
    
    for server_name, server_path in servers:
        if Path(server_path).exists():
            if not test_mcp_server(server_name, server_path):
                all_passed = False
        else:
            print_error(f"Server file not found: {server_path}")
            all_passed = False
    
    print_header("Test Results")
    if all_passed:
        print_success("All tests passed! The system is ready to use.")
        print("\nNext steps:")
        print("1. Run: python run_lite.py")
        print("2. Test with sample queries")
        print("3. Review logs in logs/ directory")
    else:
        print_error("Some tests failed. Please check the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
