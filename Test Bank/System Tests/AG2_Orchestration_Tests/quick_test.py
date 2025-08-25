"""
Quick test runner for AG2 orchestration system
"""
import pytest
import sys
from pathlib import Path

def run_quick_tests():
    """Run a quick subset of tests to verify basic functionality."""
    print("⚡ Running Quick Tests...")
    
    # Run a subset of unit tests
    result = pytest.main([
        str(Path(__file__).parent / "unit" / "test_agents.py"),
        "-v",
        "-k", "test_researcher_agent_initialization or test_analyst_agent_initialization",
        "--tb=short"
    ])
    
    if result == 0:
        print("✅ Quick tests passed!")
    else:
        print("❌ Quick tests failed!")
    
    return result == 0

if __name__ == "__main__":
    success = run_quick_tests()
    sys.exit(0 if success else 1)
