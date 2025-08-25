#!/usr/bin/env python3
"""
Code Coverage Report Generator for Token Management System

This script generates comprehensive code coverage reports for the token management system,
including HTML reports, XML reports for CI/CD, and summary statistics.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
from typing import Dict, List, Any


class CoverageReporter:
    """Generate comprehensive coverage reports for the token management system."""
    
    def __init__(self, project_root: str = None):
        """Initialize the coverage reporter."""
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.coverage_dir = self.project_root / 'coverage'
        self.src_dir = self.project_root / 'src'
        self.test_dir = self.project_root / 'tests'
        
        # Create coverage directory if it doesn't exist
        self.coverage_dir.mkdir(exist_ok=True)
    
    def run_coverage_analysis(self, modules: List[str] = None) -> Dict[str, Any]:
        """Run coverage analysis on specified modules."""
        if modules is None:
            modules = ['token_management']
        
        coverage_results = {}
        
        for module in modules:
            print(f"Running coverage analysis for {module}...")
            
            # Run pytest with coverage
            result = subprocess.run([
                sys.executable, '-m', 'pytest',
                '--cov=src/' + module,
                '--cov-report=term-missing',
                '--cov-report=html:' + str(self.coverage_dir / module),
                '--cov-report=xml:' + str(self.coverage_dir / f'{module}_coverage.xml'),
                '--cov-fail-under=80',  # Minimum 80% coverage
                '-v'
            ], capture_output=True, text=True, cwd=self.project_root)
            
            coverage_results[module] = {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'timestamp': datetime.now().isoformat()
            }
            
            if result.returncode == 0:
                print(f"✓ Coverage analysis for {module} completed successfully")
            else:
                print(f"✗ Coverage analysis for {module} failed")
                if result.stderr:
                    print(f"Error: {result.stderr}")
        
        return coverage_results
    
    def parse_coverage_xml(self, xml_file: Path) -> Dict[str, Any]:
        """Parse coverage XML file and extract metrics."""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Extract coverage metrics
            metrics = {
                'line_rate': float(root.get('line-rate', 0)),
                'branch_rate': float(root.get('branch-rate', 0)),
                'lines_covered': int(root.get('lines-covered', 0)),
                'lines_valid': int(root.get('lines-valid', 0)),
                'branches_covered': int(root.get('branches-covered', 0)),
                'branches_valid': int(root.get('branches-valid', 0)),
                'complexity': float(root.get('complexity', 0))
            }
            
            # Extract file-level coverage
            files = []
            for class_elem in root.findall('.//class'):
                filename = class_elem.get('name', '')
                line_rate = float(class_elem.get('line-rate', 0))
                branch_rate = float(class_elem.get('branch-rate', 0))
                
                files.append({
                    'filename': filename,
                    'line_rate': line_rate,
                    'branch_rate': branch_rate,
                    'lines_covered': int(class_elem.get('line-covered', 0)),
                    'lines_valid': int(class_elem.get('line-valid', 0))
                })
            
            return {
                'metrics': metrics,
                'files': files
            }
        except Exception as e:
            print(f"Error parsing XML file {xml_file}: {e}")
            return {
                'metrics': {},
                'files': [],
                'error': str(e)
            }
    
    def generate_comprehensive_report(self, coverage_results: Dict[str, Any]) -> str:
        """Generate a comprehensive coverage report."""
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("CODE COVERAGE REPORT")
        report_lines.append("=" * 60)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Overall summary
        total_modules = len(coverage_results)
        passed_modules = sum(1 for result in coverage_results.values() if result['success'])
        failed_modules = total_modules - passed_modules
        
        report_lines.append("OVERALL SUMMARY")
        report_lines.append("-" * 30)
        report_lines.append(f"Total modules analyzed: {total_modules}")
        report_lines.append(f"Passed coverage requirements: {passed_modules}")
        report_lines.append(f"Failed coverage requirements: {failed_modules}")
        report_lines.append("")
        
        # Module details
        report_lines.append("MODULE DETAILS")
        report_lines.append("-" * 30)
        
        for module, result in coverage_results.items():
            status = "✓ PASS" if result['success'] else "✗ FAIL"
            report_lines.append(f"{module}: {status}")
            
            if not result['success']:
                if result['stderr']:
                    # Extract coverage percentage from stderr
                    lines = result['stderr'].split('\n')
                    for line in lines:
                        if 'coverage:' in line.lower():
                            report_lines.append(f"  Coverage: {line.strip()}")
                            break
                report_lines.append(f"  Error: {result['stderr']}")
            report_lines.append("")
        
        # Generate HTML report
        html_report = self.generate_html_report(coverage_results)
        
        # Save text report
        report_file = self.coverage_dir / 'coverage_report.txt'
        with open(report_file, 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"Coverage report saved to: {report_file}")
        return '\n'.join(report_lines)
    
    def generate_html_report(self, coverage_results: Dict[str, Any]) -> str:
        """Generate an HTML coverage report."""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Token Management System - Coverage Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .module {{ margin: 10px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .pass {{ background-color: #d4edda; }}
        .fail {{ background-color: #f8d7da; }}
        .coverage-bar {{ width: 100%; height: 20px; background-color: #e0e0e0; border-radius: 10px; overflow: hidden; }}
        .coverage-fill {{ height: 100%; background-color: #28a745; transition: width 0.3s ease; }}
        .coverage-text {{ text-align: center; margin-top: 5px; font-size: 12px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Token Management System - Coverage Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h2>Overall Summary</h2>
        <table>
            <tr>
                <th>Total Modules</th>
                <th>Passed</th>
                <th>Failed</th>
                <th>Success Rate</th>
            </tr>
            <tr>
                <td>{len(coverage_results)}</td>
                <td>{sum(1 for result in coverage_results.values() if result['success'])}</td>
                <td>{sum(1 for result in coverage_results.values() if not result['success'])}</td>
                <td>{(sum(1 for result in coverage_results.values() if result['success']) / len(coverage_results)) * 100:.1f}%</td>
            </tr>
        </table>
    </div>
    
    <div class="modules">
        <h2>Module Coverage Details</h2>
"""
        
        for module, result in coverage_results.items():
            status_class = "pass" if result['success'] else "fail"
            status_text = "PASS" if result['success'] else "FAIL"
            
            # Extract coverage percentage from output
            coverage_percent = "N/A"
            if result['stderr']:
                lines = result['stderr'].split('\n')
                for line in lines:
                    if 'TOTAL' in line and 'coverage:' in line:
                        coverage_percent = line.split('coverage:')[1].strip().split('%')[0].strip() + '%'
                        break
            
            html_content += f"""
        <div class="module {status_class}">
            <h3>{module} - {status_text}</h3>
            <div class="coverage-bar">
                <div class="coverage-fill" style="width: {coverage_percent.replace('%', '')}%"></div>
            </div>
            <div class="coverage-text">{coverage_percent} coverage</div>
            <p><strong>Command:</strong> {result.get('command', 'N/A')}</p>
            <p><strong>Duration:</strong> {result.get('duration', 0):.2f}s</p>
            {f'<p><strong>Error:</strong> {result["stderr"]}</p>' if not result['success'] and result['stderr'] else ''}
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        # Save HTML report
        html_file = self.coverage_dir / 'coverage_report.html'
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        print(f"HTML coverage report saved to: {html_file}")
        return html_content
    
    def generate_junit_report(self, coverage_results: Dict[str, Any]) -> str:
        """Generate JUnit XML report for CI/CD integration."""
        testsuites = ET.Element('testsuites')
        
        for module, result in coverage_results.items():
            testsuite = ET.SubElement(testsuites, 'testsuite', {
                'name': f'coverage_{module}',
                'tests': '1',
                'failures': '0' if result['success'] else '1',
                'errors': '0',
                'time': str(result.get('duration', 0))
            })
            
            testcase = ET.SubElement(testsuite, 'testcase', {
                'name': f'coverage_{module}',
                'classname': f'coverage.{module}',
                'time': str(result.get('duration', 0))
            })
            
            if not result['success']:
                failure = ET.SubElement(testcase, 'failure', {
                    'message': 'Coverage requirements not met',
                    'type': 'coverage.failure'
                })
                failure.text = result.get('stderr', 'Coverage analysis failed')
        
        # Generate XML string
        xml_str = ET.tostring(testsuites, encoding='unicode')
        
        # Save JUnit report
        junit_file = self.coverage_dir / 'junit_coverage.xml'
        with open(junit_file, 'w') as f:
            f.write(xml_str)
        
        print(f"JUnit coverage report saved to: {junit_file}")
        return xml_str
    
    def generate_trend_report(self, historical_data: List[Dict[str, Any]] = None) -> str:
        """Generate coverage trend analysis report."""
        if historical_data is None:
            # Try to load historical data from previous reports
            historical_file = self.coverage_dir / 'coverage_history.json'
            if historical_file.exists():
                with open(historical_file, 'r') as f:
                    historical_data = json.load(f)
            else:
                historical_data = []
        
        # Add current data
        current_data = {
            'timestamp': datetime.now().isoformat(),
            'coverage_results': self.get_current_coverage_metrics()
        }
        historical_data.append(current_data)
        
        # Keep only last 10 reports
        historical_data = historical_data[-10:]
        
        # Save historical data
        with open(self.coverage_dir / 'coverage_history.json', 'w') as f:
            json.dump(historical_data, f, indent=2)
        
        # Generate trend report
        trend_lines = []
        trend_lines.append("COVERAGE TREND ANALYSIS")
        trend_lines.append("=" * 30)
        
        if len(historical_data) > 1:
            # Calculate trends
            latest = historical_data[-1]['coverage_results']
            previous = historical_data[-2]['coverage_results']
            
            trend_lines.append("TRENDS (vs previous report)")
            trend_lines.append("-" * 30)
            
            for module in latest:
                if module in previous:
                    current_cov = latest[module].get('line_rate', 0)
                    previous_cov = previous[module].get('line_rate', 0)
                    change = current_cov - previous_cov
                    
                    trend = "improved" if change > 0 else "declined" if change < 0 else "stable"
                    trend_lines.append(f"{module}: {trend} ({change:+.1%})")
        
        trend_lines.append(f"\nHistorical data points: {len(historical_data)}")
        
        # Save trend report
        trend_file = self.coverage_dir / 'coverage_trend.txt'
        with open(trend_file, 'w') as f:
            f.write('\n'.join(trend_lines))
        
        print(f"Coverage trend report saved to: {trend_file}")
        return '\n'.join(trend_lines)
    
    def get_current_coverage_metrics(self) -> Dict[str, Any]:
        """Get current coverage metrics from XML files."""
        metrics = {}
        
        for xml_file in self.coverage_dir.glob('*_coverage.xml'):
            module = xml_file.stem.replace('_coverage', '')
            coverage_data = self.parse_coverage_xml(xml_file)
            metrics[module] = coverage_data.get('metrics', {})
        
        return metrics
    
    def run_full_coverage_analysis(self, modules: List[str] = None) -> Dict[str, Any]:
        """Run complete coverage analysis with all reports."""
        print("Starting comprehensive coverage analysis...")
        
        # Run coverage analysis
        coverage_results = self.run_coverage_analysis(modules)
        
        # Generate reports
        self.generate_comprehensive_report(coverage_results)
        self.generate_html_report(coverage_results)
        self.generate_junit_report(coverage_results)
        self.generate_trend_report()
        
        return coverage_results


def main():
    """Main entry point for the coverage reporter."""
    parser = argparse.ArgumentParser(description='Generate coverage reports for the token management system')
    parser.add_argument('--modules', nargs='+', default=['token_management'],
                       help='Modules to analyze for coverage')
    parser.add_argument('--project-root', help='Project root directory')
    parser.add_argument('--output-format', choices=['text', 'html', 'junit', 'all'],
                       default='all', help='Output format for reports')
    
    args = parser.parse_args()
    
    # Initialize coverage reporter
    reporter = CoverageReporter(args.project_root)
    
    # Run coverage analysis
    if args.output_format == 'all':
        results = reporter.run_full_coverage_analysis(args.modules)
    else:
        results = reporter.run_coverage_analysis(args.modules)
        
        if args.output_format == 'text':
            reporter.generate_comprehensive_report(results)
        elif args.output_format == 'html':
            reporter.generate_html_report(results)
        elif args.output_format == 'junit':
            reporter.generate_junit_report(results)
    
    # Exit with non-zero code if any coverage analysis failed
    if not all(result['success'] for result in results.values()):
        sys.exit(1)


if __name__ == '__main__':
    main()