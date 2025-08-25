#!/usr/bin/env python3
"""
Setup script for AG2 Orchestration System - Lite Mode
"""

import os
import sys
import subprocess
import json
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

def check_prerequisites():
    """Check if prerequisites are met"""
    print_header("Checking Prerequisites")
    
    # Check Python
    try:
        result = subprocess.run([sys.executable, "--version"], 
                              capture_output=True, text=True)
        python_version = result.stdout.strip()
        print_success(f"Python found: {python_version}")
    except Exception as e:
        print_error(f"Python not found: {e}")
        return False
    
    # Check Node.js
    try:
        result = subprocess.run(["node", "--version"], 
                              capture_output=True, text=True)
        node_version = result.stdout.strip()
        print_success(f"Node.js found: {node_version}")
    except Exception as e:
        print_error(f"Node.js not found: {e}")
        print_info("Please install Node.js from https://nodejs.org/")
        return False
    
    # Check npm
    try:
        result = subprocess.run(["npm", "--version"], 
                              capture_output=True, text=True)
        npm_version = result.stdout.strip()
        print_success(f"npm found: {npm_version}")
    except Exception as e:
        print_error(f"npm not found: {e}")
        return False
    
    return True

def create_directories():
    """Create required directories"""
    print_header("Creating Directories")
    
    directories = [
        "mock_memory",
        "mock_rag_data",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print_success(f"Created directory: {directory}")
    
    return True

def install_python_dependencies():
    """Install Python dependencies"""
    print_header("Installing Python Dependencies")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pyyaml"], 
                      check=True)
        print_success("Python dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install Python dependencies: {e}")
        return False

def install_node_dependencies():
    """Install Node.js dependencies"""
    print_header("Installing Node.js Dependencies")
    
    try:
        # Change to mcp_servers directory
        mcp_servers_dir = Path("../../mcp_servers")
        if mcp_servers_dir.exists():
            os.chdir(mcp_servers_dir)
            subprocess.run(["npm", "install"], check=True)
            print_success("Node.js dependencies installed")
            return True
        else:
            print_error("mcp_servers directory not found")
            return False
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install Node.js dependencies: {e}")
        return False
    finally:
        # Change back to original directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

def create_sample_data():
    """Create sample mock data"""
    print_header("Creating Sample Data")
    
    # Create sample RAG data
    rag_data = {
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
        },
        "agent_roles": {
            "content": "AG2 uses specialized agents including: Research Agent for information gathering, Coordinator Agent for task management, Memory Agent for context storage, and Search Agent for web queries.",
            "metadata": {
                "source": "mock_document",
                "type": "technical"
            }
        }
    }
    
    with open("mock_rag_data/sample_data.json", "w") as f:
        json.dump(rag_data, f, indent=2)
    print_success("Sample RAG data created")
    
    # Create sample memory data
    memory_data = {
        "agents": {
            "researcher": {
                "conversations": [],
                "context": {
                    "expertise": ["research", "analysis", "information gathering"],
                    "preferences": {
                        "search_depth": "comprehensive",
                        "source_reliability": "high"
                    }
                }
            },
            "coordinator": {
                "conversations": [],
                "context": {
                    "expertise": ["task management", "coordination", "workflow"],
                    "preferences": {
                        "parallel_processing": True,
                        "timeout": 30
                    }
                }
            },
            "memory": {
                "conversations": [],
                "context": {
                    "storage_type": "ephemeral",
                    "retention_policy": "session_based"
                }
            }
        }
    }
    
    with open("mock_memory/sample_memory.json", "w") as f:
        json.dump(memory_data, f, indent=2)
    print_success("Sample memory data created")
    
    return True

def create_configuration():
    """Create configuration files"""
    print_header("Creating Configuration")
    
    # Create JSON configuration
    config = {
        "mcpServers": {
            "rag": {
                "command": "node",
                "args": ["../../mcp_servers/rag-mcp-server-lite.js"],
                "env": {
                    "MOCK_DATA_PATH": "mock_rag_data"
                }
            },
            "agent-memory": {
                "command": "node",
                "args": ["../../mcp_servers/agent-memory-lite.js"],
                "env": {
                    "MEMORY_PATH": "mock_memory"
                }
            },
            "brave-search": {
                "command": "node",
                "args": ["../../mcp_servers/brave-search-mcp-server-lite.js"],
                "env": {
                    "MOCK_MODE": "true"
                }
            }
        }
    }
    
    with open("mcp_servers_config_lite.json", "w") as f:
        json.dump(config, f, indent=2)
    print_success("Configuration file created: mcp_servers_config_lite.json")
    
    return True

def main():
    """Main setup function"""
    print_header("AG2 Orchestration System - Lite Mode Setup")
    
    # Change to correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Setup steps
    steps = [
        check_prerequisites,
        create_directories,
        install_python_dependencies,
        install_node_dependencies,
        create_sample_data,
        create_configuration
    ]
    
    all_success = True
    for step in steps:
        try:
            if not step():
                all_success = False
                break
        except Exception as e:
            print_error(f"Error in {step.__name__}: {e}")
            all_success = False
            break
    
    print_header("Setup Results")
    if all_success:
        print_success("Setup completed successfully!")
        print("\nNext steps:")
        print("1. Test the setup: python test_lite.py")
        print("2. Run the system: python run_lite.py")
        print("3. Check logs in: logs/")
    else:
        print_error("Setup failed. Please check the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
