"""
Test Execution Script - Run All Tests.

This script provides comprehensive test execution capabilities for the cache management system,
including unit tests, integration tests, performance tests, stress tests, error handling tests,
and end-to-end tests.
"""

import pytest
import asyncio
import argparse
import sys
import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess
import concurrent.futures
from dataclasses import dataclass, asdict


@dataclass
class TestResult:
    """Test result data structure."""
    test_type: str
    test_name: str
    status: str  # "passed", "failed", "skipped"
    duration: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class TestSuiteResult:
    """Test suite result data structure."""
    suite_name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration: float
    start_time: datetime
    end_time: datetime
    results: List[TestResult]
    summary: Optional[Dict[str, Any]] = None


class TestExecutor:
    """Main test executor class."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.results = []
        self.start_time = datetime.now()
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Test categories
        self.test_categories = {
            "unit": {
                "description": "Unit tests for cache layers and core components",
                "directories": ["unit"],
                "command": "pytest unit/ -v --tb=short"
            },
            "integration": {
                "description": "Integration tests for MCP server and external services",
                "directories": ["integration"],
                "command": "pytest integration/ -v --tb=short"
            },
            "performance": {
                "description": "Performance tests for cache and database operations",
                "directories": ["performance"],
                "command": "pytest performance/ -v --tb=short"
            },
            "stress": {
                "description": "Stress tests for high load and system limits",
                "directories": ["stress"],
                "command": "pytest stress/ -v --tb=short"
            },
            "error_handling": {
                "description": "Error handling tests for cache and integration errors",
                "directories": ["error_handling"],
                "command": "pytest error_handling/ -v --tb=short"
            },
            "e2e": {
                "description": "End-to-end tests for complete workflows",
                "directories": ["e2e"],
                "command": "pytest e2e/ -v --tb=short"
            }
        }
        
        # Default test configuration
        self.default_config = {
            "parallel_execution": True,
            "max_workers": 4,
            "timeout": 300,  # 5 minutes per test suite
            "stop_on_failure": False,
            "verbose": False,
            "coverage": True,
            "html_report": True,
            "json_report": True,
            "junit_report": True
        }
        
        # Merge config with defaults
        self.test_config = {**self.default_config, **self.config}
    
    def run_test_suite(self, category: str) -> TestSuiteResult:
        """Run a specific test suite."""
        if category not in self.test_categories:
            raise ValueError(f"Unknown test category: {category}")
        
        suite_info = self.test_categories[category]
        self.logger.info(f"Running {category} test suite: {suite_info['description']}")
        
        start_time = datetime.now()
        
        try:
            # Run pytest command
            result = subprocess.run(
                suite_info["command"].split(),
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                timeout=self.test_config["timeout"]
            )
            
            # Parse results
            results = self._parse_pytest_output(result.stdout, result.stderr)
            
            # Count results
            total = len(results)
            passed = sum(1 for r in results if r.status == "passed")
            failed = sum(1 for r in results if r.status == "failed")
            skipped = sum(1 for r in results if r.status == "skipped")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Create suite result
            suite_result = TestSuiteResult(
                suite_name=category,
                total_tests=total,
                passed=passed,
                failed=failed,
                skipped=skipped,
                duration=duration,
                start_time=start_time,
                end_time=end_time,
                results=results,
                summary={
                    "success_rate": passed / total if total > 0 else 0,
                    "average_duration": sum(r.duration for r in results) / total if total > 0 else 0,
                    "error_rate": failed / total if total > 0 else 0
                }
            )
            
            self.results.append(suite_result)
            return suite_result
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Test suite {category} timed out after {self.test_config['timeout']} seconds")
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            suite_result = TestSuiteResult(
                suite_name=category,
                total_tests=0,
                passed=0,
                failed=1,
                skipped=0,
                duration=duration,
                start_time=start_time,
                end_time=end_time,
                results=[TestResult(
                    test_type=category,
                    test_name="timeout",
                    status="failed",
                    duration=duration,
                    error_message=f"Test suite timed out after {self.test_config['timeout']} seconds"
                )],
                summary={
                    "success_rate": 0,
                    "average_duration": duration,
                    "error_rate": 1.0
                }
            )
            
            self.results.append(suite_result)
            return suite_result
        
        except Exception as e:
            self.logger.error(f"Error running test suite {category}: {e}")
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            suite_result = TestSuiteResult(
                suite_name=category,
                total_tests=0,
                passed=0,
                failed=1,
                skipped=0,
                duration=duration,
                start_time=start_time,
                end_time=end_time,
                results=[TestResult(
                    test_type=category,
                    test_name="error",
                    status="failed",
                    duration=duration,
                    error_message=str(e)
                )],
                summary={
                    "success_rate": 0,
                    "average_duration": duration,
                    "error_rate": 1.0
                }
            )
            
            self.results.append(suite_result)
            return suite_result
    
    def run_all_tests(self) -> List[TestSuiteResult]:
        """Run all test suites."""
        self.logger.info("Starting comprehensive test execution")
        
        # Get all test categories
        categories = list(self.test_categories.keys())
        
        if self.test_config["parallel_execution"]:
            # Run tests in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.test_config["max_workers"]) as executor:
                future_to_category = {
                    executor.submit(self.run_test_suite, category): category
                    for category in categories
                }
                
                for future in concurrent.futures.as_completed(future_to_category):
                    category = future_to_category[future]
                    try:
                        result = future.result()
                        self.logger.info(f"Completed {category} test suite: {result.passed}/{result.total_tests} passed")
                    except Exception as e:
                        self.logger.error(f"Error in {category} test suite: {e}")
        else:
            # Run tests sequentially
            for category in categories:
                result = self.run_test_suite(category)
                self.logger.info(f"Completed {category} test suite: {result.passed}/{result.total_tests} passed")
        
        return self.results
    
    def run_specific_tests(self, test_names: List[str]) -> List[TestSuiteResult]:
        """Run specific tests by name."""
        self.logger.info(f"Running specific tests: {test_names}")
        
        # For specific tests, we need to run pytest with specific test names
        results = []
        
        for test_name in test_names:
            try:
                # Run pytest with specific test name
                result = subprocess.run(
                    ["pytest", test_name, "-v", "--tb=short"],
                    cwd=Path(__file__).parent,
                    capture_output=True,
                    text=True,
                    timeout=self.test_config["timeout"]
                )
                
                # Parse results
                test_results = self._parse_pytest_output(result.stdout, result.stderr)
                
                # Create suite result for this test
                suite_result = TestSuiteResult(
                    suite_name=f"specific_{test_name}",
                    total_tests=len(test_results),
                    passed=sum(1 for r in test_results if r.status == "passed"),
                    failed=sum(1 for r in test_results if r.status == "failed"),
                    skipped=sum(1 for r in test_results if r.status == "skipped"),
                    duration=sum(r.duration for r in test_results),
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    results=test_results
                )
                
                results.append(suite_result)
                self.results.append(suite_result)
                
            except Exception as e:
                self.logger.error(f"Error running test {test_name}: {e}")
        
        return results
    
    def _parse_pytest_output(self, stdout: str, stderr: str) -> List[TestResult]:
        """Parse pytest output and extract test results."""
        results = []
        
        # Combine stdout and stderr
        output = stdout + "\n" + stderr
        
        # Parse test results (simplified parsing)
        lines = output.split('\n')
        current_test = None
        
        for line in lines:
            line = line.strip()
            
            # Look for test result lines
            if "PASSED" in line or "FAILED" in line or "SKIPPED" in line:
                # Extract test name and status
                if "::" in line:
                    parts = line.split("::")
                    test_name = parts[-1].split()[0]  # Get test name before status
                    status = line.split()[-1]  # Get status (PASSED, FAILED, SKIPPED)
                    
                    # Extract duration if available
                    duration = 0.0
                    if "in" in line and "s" in line:
                        try:
                            duration_str = line.split("in")[-1].split("s")[0].strip()
                            duration = float(duration_str)
                        except:
                            pass
                    
                    result = TestResult(
                        test_type="unknown",
                        test_name=test_name,
                        status=status.lower(),
                        duration=duration
                    )
                    
                    results.append(result)
        
        return results
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate overall statistics
        total_tests = sum(s.total_tests for s in self.results)
        total_passed = sum(s.passed for s in self.results)
        total_failed = sum(s.failed for s in self.results)
        total_skipped = sum(s.skipped for s in self.results)
        
        overall_success_rate = total_passed / total_tests if total_tests > 0 else 0
        overall_error_rate = total_failed / total_tests if total_tests > 0 else 0
        
        # Generate detailed report
        report = {
            "execution_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_duration_seconds": total_duration,
                "config": self.test_config
            },
            "overall_summary": {
                "total_test_suites": len(self.results),
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "skipped": total_skipped,
                "success_rate": overall_success_rate,
                "error_rate": overall_error_rate
            },
            "suite_results": [],
            "category_analysis": {},
            "performance_analysis": {
                "fastest_suite": None,
                "slowest_suite": None,
                "average_suite_duration": sum(s.duration for s in self.results) / len(self.results) if self.results else 0
            },
            "recommendations": []
        }
        
        # Add suite results
        for suite in self.results:
            suite_data = {
                "name": suite.suite_name,
                "total_tests": suite.total_tests,
                "passed": suite.passed,
                "failed": suite.failed,
                "skipped": suite.skipped,
                "duration_seconds": suite.duration,
                "success_rate": suite.summary["success_rate"] if suite.summary else 0,
                "average_duration": suite.summary["average_duration"] if suite.summary else 0,
                "error_rate": suite.summary["error_rate"] if suite.summary else 0,
                "start_time": suite.start_time.isoformat(),
                "end_time": suite.end_time.isoformat()
            }
            report["suite_results"].append(suite_data)
        
        # Analyze by category
        for suite in self.results:
            category = suite.suite_name
            if category not in report["category_analysis"]:
                report["category_analysis"][category] = {
                    "total_tests": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "success_rate": 0,
                    "average_duration": 0
                }
            
            report["category_analysis"][category]["total_tests"] += suite.total_tests
            report["category_analysis"][category]["passed"] += suite.passed
            report["category_analysis"][category]["failed"] += suite.failed
            report["category_analysis"][category]["skipped"] += suite.skipped
            
            if suite.total_tests > 0:
                report["category_analysis"][category]["success_rate"] = suite.summary["success_rate"]
                report["category_analysis"][category]["average_duration"] = suite.summary["average_duration"]
        
        # Find fastest and slowest suites
        if self.results:
            fastest = min(self.results, key=lambda s: s.duration)
            slowest = max(self.results, key=lambda s: s.duration)
            
            report["performance_analysis"]["fastest_suite"] = {
                "name": fastest.suite_name,
                "duration": fastest.duration
            }
            
            report["performance_analysis"]["slowest_suite"] = {
                "name": slowest.suite_name,
                "duration": slowest.duration
            }
        
        # Generate recommendations
        if overall_success_rate < 0.8:
            report["recommendations"].append("Overall success rate is low. Consider improving test coverage and fixing failing tests.")
        
        if overall_error_rate > 0.1:
            report["recommendations"].append("High error rate detected. Investigate failing tests and improve error handling.")
        
        for suite in self.results:
            if suite.failed > 0:
                report["recommendations"].append(f"Suite '{suite.suite_name}' has {suite.failed} failing tests. Review and fix these tests.")
        
        if total_duration > 600:  # 10 minutes
            report["recommendations"].append("Test execution took longer than expected. Consider optimizing test performance or running in parallel.")
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_dir: str = "reports"):
        """Save test report to file."""
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON report
        json_file = os.path.join(output_dir, f"test_report_{timestamp}.json")
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Save HTML report
        html_file = os.path.join(output_dir, f"test_report_{timestamp}.html")
        self._generate_html_report(report, html_file)
        
        # Save summary report
        summary_file = os.path.join(output_dir, f"test_summary_{timestamp}.txt")
        self._generate_summary_report(report, summary_file)
        
        self.logger.info(f"Test reports saved to {output_dir}")
        self.logger.info(f"JSON report: {json_file}")
        self.logger.info(f"HTML report: {html_file}")
        self.logger.info(f"Summary report: {summary_file}")
        
        return json_file, html_file, summary_file
    
    def _generate_html_report(self, report: Dict[str, Any], output_file: str):
        """Generate HTML test report."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cache Management System Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; margin-bottom: 20px; }}
                .summary {{ background-color: #e8f5e8; padding: 15px; margin-bottom: 20px; }}
                .error {{ background-color: #ffe8e8; padding: 15px; margin-bottom: 20px; }}
                .suite {{ margin-bottom: 20px; border: 1px solid #ddd; padding: 15px; }}
                .suite-header {{ background-color: #f8f8f8; padding: 10px; margin-bottom: 10px; }}
                .test-result {{ margin: 5px 0; padding: 5px; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                .skipped {{ color: orange; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Cache Management System Test Report</h1>
                <p><strong>Generated:</strong> {report['execution_info']['start_time']}</p>
                <p><strong>Total Duration:</strong> {report['execution_info']['total_duration_seconds']:.2f} seconds</p>
            </div>
            
            <div class="summary">
                <h2>Overall Summary</h2>
                <table>
                    <tr><th>Total Test Suites</th><td>{report['overall_summary']['total_test_suites']}</td></tr>
                    <tr><th>Total Tests</th><td>{report['overall_summary']['total_tests']}</td></tr>
                    <tr><th>Passed</th><td class="passed">{report['overall_summary']['passed']}</td></tr>
                    <tr><th>Failed</th><td class="failed">{report['overall_summary']['failed']}</td></tr>
                    <tr><th>Skipped</th><td class="skipped">{report['overall_summary']['skipped']}</td></tr>
                    <tr><th>Success Rate</th><td>{report['overall_summary']['success_rate']:.2%}</td></tr>
                    <tr><th>Error Rate</th><td>{report['overall_summary']['error_rate']:.2%}</td></tr>
                </table>
            </div>
            
            <div class="error">
                <h2>Recommendations</h2>
                <ul>
        """
        
        for recommendation in report['recommendations']:
            html_content += f"<li>{recommendation}</li>"
        
        html_content += """
                </ul>
            </div>
            
            <div class="suites">
                <h2>Test Suite Results</h2>
        """
        
        for suite in report['suite_results']:
            html_content += f"""
                <div class="suite">
                    <div class="suite-header">
                        <h3>{suite['name']}</h3>
                        <p>Duration: {suite['duration_seconds']:.2f}s | Success Rate: {suite['success_rate']:.2%}</p>
                    </div>
                    <table>
                        <tr><th>Total Tests</th><td>{suite['total_tests']}</td></tr>
                        <tr><th>Passed</th><td class="passed">{suite['passed']}</td></tr>
                        <tr><th>Failed</th><td class="failed">{suite['failed']}</td></tr>
                        <tr><th>Skipped</th><td class="skipped">{suite['skipped']}</td></tr>
                    </table>
                </div>
            """
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_content)
    
    def _generate_summary_report(self, report: Dict[str, Any], output_file: str):
        """Generate summary text report."""
        summary_content = f"""
        Cache Management System Test Report
        ==================================
        
        Generated: {report['execution_info']['start_time']}
        Total Duration: {report['execution_info']['total_duration_seconds']:.2f} seconds
        
        Overall Summary:
        - Total Test Suites: {report['overall_summary']['total_test_suites']}
        - Total Tests: {report['overall_summary']['total_tests']}
        - Passed: {report['overall_summary']['passed']}
        - Failed: {report['overall_summary']['failed']}
        - Skipped: {report['overall_summary']['skipped']}
        - Success Rate: {report['overall_summary']['success_rate']:.2%}
        - Error Rate: {report['overall_summary']['error_rate']:.2%}
        
        Test Suite Results:
        """
        
        for suite in report['suite_results']:
            summary_content += f"""
        {suite['name']}:
          - Duration: {suite['duration_seconds']:.2f}s
          - Tests: {suite['total_tests']} (Passed: {suite['passed']}, Failed: {suite['failed']}, Skipped: {suite['skipped']})
          - Success Rate: {suite['success_rate']:.2%}
          - Average Duration: {suite['average_duration']:.2f}s
            """
        
        summary_content += """
        
        Recommendations:
        """
        
        for recommendation in report['recommendations']:
            summary_content += f"- {recommendation}\n"
        
        with open(output_file, 'w') as f:
            f.write(summary_content)


def main():
    """Main function to run tests."""
    parser = argparse.ArgumentParser(description='Cache Management System Test Runner')
    parser.add_argument('--category', '-c', choices=list(TestExecutor().test_categories.keys()),
                       help='Run specific test category')
    parser.add_argument('--test', '-t', nargs='+', help='Run specific tests')
    parser.add_argument('--config', '-f', help='Test configuration file')
    parser.add_argument('--output', '-o', default='reports', help='Output directory for reports')
    parser.add_argument('--parallel', '-p', action='store_true', help='Run tests in parallel')
    parser.add_argument('--workers', '-w', type=int, default=4, help='Number of parallel workers')
    parser.add_argument('--timeout', type=int, default=300, help='Timeout in seconds')
    parser.add_argument('--stop-on-failure', action='store_true', help='Stop execution on first failure')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--html', action='store_true', help='Generate HTML report')
    parser.add_argument('--json', action='store_true', help='Generate JSON report')
    parser.add_argument('--junit', action='store_true', help='Generate JUnit report')
    
    args = parser.parse_args()
    
    # Load configuration if provided
    config = {}
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            sys.exit(1)
    
    # Override config with command line arguments
    if args.parallel:
        config['parallel_execution'] = True
    if args.workers:
        config['max_workers'] = args.workers
    if args.timeout:
        config['timeout'] = args.timeout
    if args.stop_on_failure:
        config['stop_on_failure'] = True
    if args.verbose:
        config['verbose'] = True
    if args.coverage:
        config['coverage'] = True
    if args.html:
        config['html_report'] = True
    if args.json:
        config['json_report'] = True
    if args.junit:
        config['junit_report'] = True
    
    # Create test executor
    executor = TestExecutor(config)
    
    try:
        # Run tests
        if args.category:
            results = [executor.run_test_suite(args.category)]
        elif args.test:
            results = executor.run_specific_tests(args.test)
        else:
            results = executor.run_all_tests()
        
        # Generate and save reports
        report = executor.generate_report()
        executor.save_report(report, args.output)
        
        # Print summary
        print("\n" + "="*50)
        print("TEST EXECUTION SUMMARY")
        print("="*50)
        print(f"Total Test Suites: {len(results)}")
        print(f"Total Tests: {sum(s.total_tests for s in results)}")
        print(f"Passed: {sum(s.passed for s in results)}")
        print(f"Failed: {sum(s.failed for s in results)}")
        print(f"Skipped: {sum(s.skipped for s in results)}")
        print(f"Success Rate: {sum(s.passed for s in results) / sum(s.total_tests for s in results) if sum(s.total_tests for s in results) > 0 else 0:.2%}")
        
        # Exit with appropriate code
        if sum(s.failed for s in results) > 0:
            sys.exit(1)
        else:
            sys.exit(0)
        
    except Exception as e:
        print(f"Error during test execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()