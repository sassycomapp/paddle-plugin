#!/usr/bin/env python3
"""
Comprehensive Test Runner for Token Management System

This script provides a unified interface for running all types of tests
for the token management system, including unit tests, integration tests,
performance tests, and security tests.
"""

import subprocess
import sys
import os
import argparse
import json
import time
from datetime import datetime
from pathlib import Path


class TestRunner:
    """Comprehensive test runner for the token management system."""
    
    def __init__(self, project_root: str = None):
        """Initialize the test runner."""
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def run_command(self, command: list, cwd: str = None) -> dict:
        """Run a command and return the result."""
        try:
            start_time = time.time()
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=cwd or self.project_root,
                timeout=300  # 5 minutes timeout
            )
            end_time = time.time()
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'duration': end_time - start_time,
                'command': ' '.join(command)
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': 'Command timed out after 300 seconds',
                'duration': 300,
                'command': ' '.join(command)
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'duration': 0,
                'command': ' '.join(command)
            }
    
    def run_unit_tests(self, verbose: bool = False, coverage: bool = False) -> dict:
        """Run unit tests for the token management system."""
        print("Running unit tests...")
        
        command = [sys.executable, '-m', 'pytest']
        
        if verbose:
            command.append('-v')
        
        if coverage:
            command.extend(['--cov=src/token_management', '--cov-report=html', '--cov-report=term'])
        
        command.extend([
            'tests/test_token_counter.py',
            'tests/test_rate_limiter.py',
            'tests/test_token_security.py',
            '-m', 'not integration'
        ])
        
        result = self.run_command(command)
        self.test_results['unit_tests'] = result
        
        if result['success']:
            print("✓ Unit tests passed")
        else:
            print("✗ Unit tests failed")
            if result['stderr']:
                print(f"Error: {result['stderr']}")
        
        return result
    
    def run_integration_tests(self, verbose: bool = False) -> dict:
        """Run integration tests."""
        print("Running integration tests...")
        
        command = [sys.executable, '-m', 'pytest']
        
        if verbose:
            command.append('-v')
        
        command.extend([
            'tests/test_token_integration.py',
            'tests/test_mcp_kilocode_integration.py',
            'tests/test_pg_tiktoken_integration.py',
            'tests/test_vault_integration.py',
            '-m', 'integration'
        ])
        
        result = self.run_command(command)
        self.test_results['integration_tests'] = result
        
        if result['success']:
            print("✓ Integration tests passed")
        else:
            print("✗ Integration tests failed")
            if result['stderr']:
                print(f"Error: {result['stderr']}")
        
        return result
    
    def run_performance_tests(self, verbose: bool = False) -> dict:
        """Run performance and load tests."""
        print("Running performance tests...")
        
        command = [sys.executable, '-m', 'pytest']
        
        if verbose:
            command.append('-v')
        
        command.extend([
            'tests/test_token_performance.py',
            '-m', 'performance'
        ])
        
        result = self.run_command(command)
        self.test_results['performance_tests'] = result
        
        if result['success']:
            print("✓ Performance tests passed")
        else:
            print("✗ Performance tests failed")
            if result['stderr']:
                print(f"Error: {result['stderr']}")
        
        return result
    
    def run_security_tests(self, verbose: bool = False) -> dict:
        """Run security tests."""
        print("Running security tests...")
        
        command = [sys.executable, '-m', 'pytest']
        
        if verbose:
            command.append('-v')
        
        command.extend([
            'tests/test_token_security.py',
            '-m', 'security'
        ])
        
        result = self.run_command(command)
        self.test_results['security_tests'] = result
        
        if result['success']:
            print("✓ Security tests passed")
        else:
            print("✗ Security tests failed")
            if result['stderr']:
                print(f"Error: {result['stderr']}")
        
        return result
    
    def run_end_to_end_tests(self, verbose: bool = False) -> dict:
        """Run end-to-end tests."""
        print("Running end-to-end tests...")
        
        command = [sys.executable, '-m', 'pytest']
        
        if verbose:
            command.append('-v')
        
        command.extend([
            'tests/test_token_management_complete.py',
            '-m', 'end_to_end'
        ])
        
        result = self.run_command(command)
        self.test_results['end_to_end_tests'] = result
        
        if result['success']:
            print("✓ End-to-end tests passed")
        else:
            print("✗ End-to-end tests failed")
            if result['stderr']:
                print(f"Error: {result['stderr']}")
        
        return result
    
    def run_all_tests(self, verbose: bool = False, with_coverage: bool = False) -> dict:
        """Run all tests."""
        print("Running all tests...")
        print("=" * 50)
        
        self.start_time = time.time()
        
        # Run all test suites
        results = {
            'unit_tests': self.run_unit_tests(verbose, with_coverage),
            'integration_tests': self.run_integration_tests(verbose),
            'performance_tests': self.run_performance_tests(verbose),
            'security_tests': self.run_security_tests(verbose),
            'end_to_end_tests': self.run_end_to_end_tests(verbose)
        }
        
        self.end_time = time.time()
        self.test_results = results
        
        # Generate summary
        self._generate_summary()
        
        return results
    
    def _generate_summary(self):
        """Generate a test summary."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        total_duration = sum(result['duration'] for result in self.test_results.values())
        
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        print(f"Total test suites: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Total duration: {total_duration:.2f} seconds")
        
        if self.start_time and self.end_time:
            print(f"Started: {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Ended: {datetime.fromtimestamp(self.end_time).strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Print detailed results
        for test_name, result in self.test_results.items():
            status = "✓ PASS" if result['success'] else "✗ FAIL"
            print(f"{test_name}: {status} ({result['duration']:.2f}s)")
        
        # Save results to file
        self._save_results()
    
    def _save_results(self):
        """Save test results to a JSON file."""
        results_file = self.project_root / 'test_results.json'
        
        # Convert datetime objects to strings for JSON serialization
        serializable_results = {}
        for test_name, result in self.test_results.items():
            serializable_result = result.copy()
            # Add timestamp
            serializable_result['timestamp'] = datetime.now().isoformat()
            serializable_results[test_name] = serializable_result
        
        with open(results_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"\nTest results saved to: {results_file}")
    
    def run_specific_test(self, test_file: str, verbose: bool = False) -> dict:
        """Run a specific test file."""
        print(f"Running specific test: {test_file}")
        
        command = [sys.executable, '-m', 'pytest']
        
        if verbose:
            command.append('-v')
        
        command.append(test_file)
        
        result = self.run_command(command)
        
        if result['success']:
            print("✓ Test passed")
        else:
            print("✗ Test failed")
            if result['stderr']:
                print(f"Error: {result['stderr']}")
        
        return result


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description='Run comprehensive tests for the token management system')
    parser.add_argument('--type', choices=['all', 'unit', 'integration', 'performance', 'security', 'e2e'],
                       default='all', help='Type of tests to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--coverage', '-c', action='store_true', help='Run with coverage')
    parser.add_argument('--test-file', help='Run a specific test file')
    parser.add_argument('--project-root', help='Project root directory')
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = TestRunner(args.project_root)
    
    # Run tests based on arguments
    if args.test_file:
        # Run specific test file
        result = runner.run_specific_test(args.test_file, args.verbose)
        sys.exit(0 if result['success'] else 1)
    elif args.type == 'all':
        # Run all tests
        results = runner.run_all_tests(args.verbose, args.coverage)
        # Exit with non-zero code if any tests failed
        if not all(result['success'] for result in results.values()):
            sys.exit(1)
    else:
        # Run specific test type
        if args.type == 'unit':
            result = runner.run_unit_tests(args.verbose, args.coverage)
        elif args.type == 'integration':
            result = runner.run_integration_tests(args.verbose)
        elif args.type == 'performance':
            result = runner.run_performance_tests(args.verbose)
        elif args.type == 'security':
            result = runner.run_security_tests(args.verbose)
        elif args.type == 'e2e':
            result = runner.run_end_to_end_tests(args.verbose)
        
        # Exit with non-zero code if tests failed
        if not result['success']:
            sys.exit(1)


if __name__ == '__main__':
    main()