#!/usr/bin/env python3
"""
Wrapper script to run AG2 system test with proper Python path configuration.
"""

import sys
import site
import os
import asyncio
import argparse

# Add user site-packages to Python path
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.insert(0, user_site)

# Now run the actual test
import test_ag2_system

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the AG2 Orchestrator and MCP servers.")
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Skip LLM initialization and API calls. Useful for testing MCP server setup in isolation."
    )
    args = parser.parse_args()
    
    asyncio.run(test_ag2_system.test_ag2_system(skip_llm=args.skip_llm))
