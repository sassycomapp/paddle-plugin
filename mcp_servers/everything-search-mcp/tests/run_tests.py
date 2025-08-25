#!/usr/bin/env python3
"""
Test Runner Script for Everything Search MCP Server

This script provides a comprehensive test runner for the Everything Search MCP Server test suite.
It can run individual test modules or the entire test suite with various options.

Author: Kilo Code
Version: 1.0.0
"""

import os
import sys
import subprocess
import argparse
import json
import time
from pathlib import Path
from datetime import datetime

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Test directories
TEST_DIRS = {
    'unit': 'unit',
    'integration': 'integration', 
    'performance': 'performance',
    'all': ''
}

def run_pytest(test_dir, test_file=None, verbose=False, coverage=False, html_report=False):
    """Run pytest with specified options."""
    # Build pytest command
    cmd = ['python', '-m', 'pytest']
    
    if verbose:
        cmd.append('-v')
    
    if coverage:
        cmd.extend(['--cov=src', '--cov-report=term-missing'])
        if html_report:
            cmd.append('--cov-report=html')
    
    # Add test directory or file
    if test_file:
        test_path = Path(__file__).parent / test_dir / test_file
        cmd.append(str(test_path))
    else:
        test_path = Path(__file__).parent / test_dir
        cmd.append(str(test_path))
    
    # Run pytest
    print(f"Running: {' '.join(cmd)}")
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        end_time = time.time()
        
        return {
            'success': result.returncode == 0,
            'execution_time': end_time - start_time,
            'return_code': result.returncode
        }
    except Exception as e:
        end_time = time.time()
        return {
            'success': False,
            'execution_time': end_time - start_time,
            'error': str(e),
            'return_code': -1
        }

def run_test_suite(test_type='all', verbose=False, coverage=False, html_report=False):
    """Run the complete test suite."""
    print(f"Running {test_type} test suite...")
    print("=" * 60)
    
    results = {}
    total_start_time = time.time()
    
    if test_type == 'all':
        # Run all test types
        for test_dir in TEST_DIRS.values():
            if test_dir:  # Skip 'all' itself
                print(f"\nRunning {test_dir} tests...")
                result = run_pytest(test_dir, verbose=verbose, coverage=coverage, html_report=html_report)
                results[test_dir] = result
    else:
        # Run specific test type
        if test_type not in TEST_DIRS:
            print(f"Error: Unknown test type '{test_type}'")
            print(f"Available test types: {list(TEST_DIRS.keys())}")
            return None
        
        test_dir = TEST_DIRS[test_type]
        result = run_pytest(test_dir, verbose=verbose, coverage=coverage, html_report=html_report)
        results[test_type] = result
    
    total_end_time = time.time()
    total_execution_time = total_end_time - total_start_time
    
    # Generate summary
    print("\n" + "=" * 60)
    print("Test Suite Summary")
    print("=" * 60)
    
    passed = 0
    failed = 0
    total_tests = 0
    
    for test_type, result in results.items():
        status = "PASS" if result['success'] else "FAIL"
        print(f"{status}: {test_type} tests")
        print(f"  Execution time: {result['execution_time']:.2f} seconds")
        
        if result['success']:
            passed += 1
        else:
            failed += 1
            if 'error' in result:
                print(f"  Error: {result['error']}")
        
        total_tests += 1
    
    print(f"\nTotal: {passed + failed} test suites")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total execution time: {total_execution_time:.2f} seconds")
    
    if coverage:
        print("\nCoverage report generated.")
        if html_report:
            print("HTML coverage report available in htmlcov/")
    
    return {
        'total_tests': total_tests,
        'passed': passed,
        'failed': failed,
        'total_execution_time': total_execution_time,
        'results': results
    }

def run_specific_test(test_file, verbose=False, coverage=False, html_report=False):
    """Run a specific test file."""
    # Determine test type from file path
    test_path = Path(test_file)
    test_dir = test_path.parent.name
    
    if test_dir not in TEST_DIRS:
        print(f"Error: Unknown test directory '{test_dir}'")
        return None
    
    print(f"Running specific test: {test_file}")
    print("=" * 60)
    
    result = run_pytest(test_dir, test_file, verbose=verbose, coverage=coverage, html_report=html_report)
    
    print("\n" + "=" * 60)
    print("Test Result")
    print("=" * 60)
    
    status = "PASS" if result['success'] else "FAIL"
    print(f"Status: {status}")
    print(f"Execution time: {result['execution_time']:.2f} seconds")
    
    if not result['success'] and 'error' in result:
        print(f"Error: {result['error']}")
    
    return result

def generate_test_report(results, output_file=None):
    """Generate a detailed test report."""
    if not results:
        print("No results to report.")
        return
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': results.get('total_tests', 0),
        'passed': results.get('passed', 0),
        'failed': results.get('failed', 0),
        'total_execution_time': results.get('total_execution_time', 0),
        'results': results.get('results', {})
    }
    
    # Calculate success rate
    if report['total_tests'] > 0:
        report['success_rate'] = (report['passed'] / report['total_tests']) * 100
    else:
        report['success_rate'] = 0
    
    # Generate report
    report_content = json.dumps(report, indent=2)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report_content)
        print(f"Test report saved to: {output_file}")
    else:
        print("\n" + "=" * 60)
        print("Detailed Test Report")
        print("=" * 60)
        print(report_content)

def check_dependencies():
    """Check if all required dependencies are available."""
    required_packages = [
        'pytest',
        'pytest-asyncio',
        'pytest-cov',
        'psutil'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install " + " ".join(missing_packages))
        return False
    
    return True

def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description='Test runner for Everything Search MCP Server')
    parser.add_argument('--type', '-t', choices=list(TEST_DIRS.keys()), default='all',
                       help='Type of tests to run (default: all)')
    parser.add_argument('--file', '-f', type=str,
                       help='Specific test file to run')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Run tests in verbose mode')
    parser.add_argument('--coverage', '-c', action='store_true',
                       help='Generate coverage report')
    parser.add_argument('--html-report', '-r', action='store_true',
                       help='Generate HTML coverage report')
    parser.add_argument('--report', '-o', type=str,
                       help='Output file for test report')
    parser.add_argument('--check-deps', '-d', action='store_true',
                       help='Check if all dependencies are available')
    
    args = parser.parse_args()
    
    # Check dependencies if requested
    if args.check_deps:
        if check_dependencies():
            print("All dependencies are available.")
        else:
            print("Some dependencies are missing.")
            sys.exit(1)
        return
    
    # Check dependencies before running tests
    if not check_dependencies():
        print("Please install missing dependencies before running tests.")
        sys.exit(1)
    
    # Run tests
    if args.file:
        # Run specific test file
        results = run_specific_test(args.file, args.verbose, args.coverage, args.html_report)
    else:
        # Run test suite
        results = run_test_suite(args.type, args.verbose, args.coverage, args.html_report)
    
    # Generate report if requested
    if args.report and results:
        generate_test_report(results, args.report)
    
    # Exit with appropriate code
    if results and results.get('failed', 0) > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()