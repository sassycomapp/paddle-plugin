#!/usr/bin/env python3
"""
Stress Test Runner for Cache Management System.

This script runs all stress tests for the cache management system.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def run_stress_tests(verbose=False, coverage=False, pattern=None):
    """Run stress tests for the cache management system."""
    
    # Build pytest command
    cmd = ["pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
    
    # Add stress test directory
    stress_test_dir = Path(__file__).parent / "stress"
    cmd.append(str(stress_test_dir))
    
    # Add pattern if specified
    if pattern:
        cmd.extend(["-k", pattern])
    
    # Run tests
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running stress tests: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run stress tests for cache management system")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    parser.add_argument("--pattern", "-k", help="Run tests matching pattern")
    
    args = parser.parse_args()
    
    print("Running stress tests for cache management system...")
    
    success = run_stress_tests(
        verbose=args.verbose,
        coverage=args.coverage,
        pattern=args.pattern
    )
    
    if success:
        print("✓ Stress tests passed!")
        sys.exit(0)
    else:
        print("✗ Stress tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()