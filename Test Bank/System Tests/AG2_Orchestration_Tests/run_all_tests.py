"""
Comprehensive test runner for AG2 orchestration system
"""
import pytest
import sys
import os
from pathlib import Path

def run_unit_tests():
    """Run unit tests."""
    print("🧪 Running Unit Tests...")
    unit_test_dir = Path(__file__).parent / "unit"
    result = pytest.main([
        str(unit_test_dir),
        "-v",
        "--tb=short",
        "--strict-markers",
        "-m", "unit"
    ])
    return result == 0

def run_integration_tests():
    """Run integration tests."""
    print("🔗 Running Integration Tests...")
    integration_test_dir = Path(__file__).parent / "integration"
    result = pytest.main([
        str(integration_test_dir),
        "-v",
        "--tb=short",
        "--strict-markers",
        "-m", "integration"
    ])
    return result == 0

def run_e2e_tests():
    """Run end-to-end tests."""
    print("🚀 Running End-to-End Tests...")
    e2e_test_dir = Path(__file__).parent / "e2e"
    result = pytest.main([
        str(e2e_test_dir),
        "-v",
        "--tb=short",
        "--strict-markers",
        "-m", "e2e"
    ])
    return result == 0

def run_all_tests():
    """Run all test suites."""
    print("🎯 Starting AG2 Orchestration Test Suite")
    print("=" * 50)
    
    results = []
    
    # Run unit tests
    results.append(run_unit_tests())
    
    # Run integration tests
    results.append(run_integration_tests())
    
    # Run end-to-end tests
    results.append(run_e2e_tests())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"Unit Tests: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"Integration Tests: {'✅ PASS' if results[1] else '❌ FAIL'}")
    print(f"End-to-End Tests: {'✅ PASS' if results[2] else '❌ FAIL'}")
    
    if all(results):
        print("\n🎉 All tests passed! AG2 orchestration system is ready for production.")
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
    
    return all(results)

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
