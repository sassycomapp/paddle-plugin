import os
import json
import sys
from datetime import datetime

def generate_compatibility_report():
    """Generate a compatibility report from test results"""
    print("Generating compatibility report...")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_python_versions': 3,
        'tested_python_versions': [],
        'compatibility_issues': [],
        'recommendations': []
    }
    
    # Process test results for each Python version
    python_versions = ['3.8', '3.11', '3.13']
    
    for version in python_versions:
        version_dir = f'test-results-python-{version}'
        if os.path.exists(version_dir):
            report['tested_python_versions'].append(version)
            
            # Check for test results
            test_file = os.path.join(version_dir, 'test_results.json')
            if os.path.exists(test_file):
                try:
                    with open(test_file, 'r') as f:
                        test_results = json.load(f)
                        
                    # Analyze test results
                    if 'tests' in test_results:
                        passed_tests = sum(1 for test in test_results['tests'] if test.get('status') == 'passed')
                        failed_tests = sum(1 for test in test_results['tests'] if test.get('status') == 'failed')
                        
                        report[f'python_{version}_tests'] = {
                            'total': len(test_results['tests']),
                            'passed': passed_tests,
                            'failed': failed_tests,
                            'success_rate': passed_tests / len(test_results['tests']) * 100 if test_results['tests'] else 0
                        }
                        
                        if failed_tests > 0:
                            report['compatibility_issues'].append(
                                f"Python {version}: {failed_tests} tests failed"
                            )
                            
                except Exception as e:
                    report['compatibility_issues'].append(
                        f"Error processing Python {version} results: {e}"
                    )
    
    # Generate recommendations
    if 'python_3.8_tests' in report:
        success_rate = report['python_3.8_tests']['success_rate']
        if success_rate < 100:
            report['recommendations'].append(
                "Python 3.8 compatibility issues detected. This is critical for Anvil deployment."
            )
    
    if 'python_3.11_tests' in report:
        success_rate = report['python_3.11_tests']['success_rate']
        if success_rate < 100:
            report['recommendations'].append(
                "Python 3.11 tests have failures. Consider fixing these issues."
            )
    
    if 'python_3.13_tests' in report:
        success_rate = report['python_3.13_tests']['success_rate']
        if success_rate < 100:
            report['recommendations'].append(
                "Python 3.13 tests have failures. These may indicate future compatibility issues."
            )
    
    # Save report
    with open('compatibility_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("✓ Compatibility report generated")
    return report

def main():
    print("Starting compatibility report generation...")
    
    try:
        report = generate_compatibility_report()
        
        print("\nCompatibility Report Summary:")
        print(f"  Timestamp: {report['timestamp']}")
        print(f"  Tested Python versions: {', '.join(report['tested_python_versions'])}")
        
        if report['compatibility_issues']:
            print("\n⚠️ Compatibility Issues:")
            for issue in report['compatibility_issues']:
                print(f"  - {issue}")
        
        if report['recommendations']:
            print("\n💡 Recommendations:")
            for recommendation in report['recommendations']:
                print(f"  - {recommendation}")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"Error generating compatibility report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()