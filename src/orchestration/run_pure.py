#!/usr/bin/env python3
"""
Runner script for AG2 Pure Python version
"""

import os
import sys
import asyncio
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ag2_pure import AG2Orchestrator

async def main():
    """Main runner function"""
    print("Starting AG2 Pure Python Orchestrator...")
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Initialize orchestrator
    orchestrator = AG2Orchestrator()
    
    # Run in interactive mode
    await orchestrator.interactive_mode()
    
    print("\nAG2 Pure Python Orchestrator stopped.")

if __name__ == "__main__":
    asyncio.run(main())
