#!/usr/bin/env python3
"""
Integration Test Runner for Cache Management System.

This script runs all integration tests for the cache management system.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def run_integration_tests(verbose=False, coverage=False, pattern=None):
    """Run integration tests for the cache management system."""
    
    # Build pytest command
    cmd = ["pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
    
    # Add integration test directory
    integration_test_dir = Path(__file__).parent / "integration"
    cmd.append(str(integration_test_dir))
    
    # Add pattern if specified
    if pattern:
        cmd.extend(["-k", pattern])
    
    # Run tests
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running integration tests: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run integration tests for cache management system")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    parser.add_argument("--pattern", "-k", help="Run tests matching pattern")
    
    args = parser.parse_args()
    
    print("Running integration tests for cache management system...")
    
    success = run_integration_tests(
        verbose=args.verbose,
        coverage=args.coverage,
        pattern=args.pattern
    )
    
    if success:
        print("✓ Integration tests passed!")
        sys.exit(0)
    else:
        print("✗ Integration tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()