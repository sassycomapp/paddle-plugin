#!/usr/bin/env python3
"""
Run script for AG2 Orchestration System - Lite Mode
"""

import os
import sys
import asyncio
import json
import yaml
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

def check_environment():
    """Check if environment is ready"""
    print_header("Environment Check")
    
    # Check if we're in the right directory
    if not Path("ag2_orchestrator.py").exists():
        print_error("ag2_orchestrator.py not found. Please run from src/orchestration/")
        return False
    
    # Check configuration
    config_files = ["mcp_servers_config_lite.json", "mcp_servers_config_lite.yaml"]
    config_exists = any(Path(f).exists() for f in config_files)
    
    if not config_exists:
        print_error("No configuration file found. Please run setup_lite.py first")
        return False
    
    # Check directories
    directories = ["mock_memory", "mock_rag_data", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print_success("Environment check passed")
    return True

async def run_orchestrator():
    """Run the AG2 orchestrator in lite mode"""
    print_header("Starting AG2 Orchestrator - Lite Mode")
    
    try:
        # Import the orchestrator
        from ag2_orchestrator import AG2Orchestrator, LLMConfigBuilder
        
        # Set environment variables for lite mode
        os.environ["LITE_MODE"] = "true"
        
        # Use YAML config if it exists, otherwise JSON
        config_file = "mcp_servers_config_lite.yaml"
        if not Path(config_file).exists():
            config_file = "mcp_servers_config_lite.json"
        
        print_info(f"Using configuration: {config_file}")
        
        # Build LLM configuration (will use mock mode if no API keys)
        llm_config = LLMConfigBuilder.build_config()
        
        # Initialize orchestrator
        orchestrator = AG2Orchestrator(llm_config)
        
        # Set up MCP servers
        print_info("Setting up MCP servers...")
        await orchestrator.setup_from_config(config_file)
        
        # Initialize agent
        print_info("Initializing agent...")
        await orchestrator.initialize_agent()
        
        print_success("AG2 Orchestrator started successfully!")
        print_info(f"Available tools: {list(orchestrator.toolkits.keys())}")
        print_info("Type 'quit' to exit")
        print_info("Type your questions below:\n")
        
        # Interactive mode
        while True:
            try:
                query = input("> ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if query:
                    print_info("Processing query...")
                    response = await orchestrator.run_query(query)
                    print(f"\nResponse: {response}\n")
                    
            except KeyboardInterrupt:
                print("\n\nShutting down...")
                break
            except Exception as e:
                print_error(f"Error processing query: {e}")
        
        # Cleanup
        await orchestrator.aclose()
        return True
        
    except ImportError as e:
        print_error(f"Failed to import AG2Orchestrator: {e}")
        return False
    except Exception as e:
        print_error(f"Failed to run orchestrator: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    # Change to correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Run the orchestrator
    if await run_orchestrator():
        print_success("AG2 orchestrator stopped successfully")
    else:
        print_error("Failed to run AG2 orchestrator")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
