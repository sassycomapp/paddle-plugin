#!/usr/bin/env python3
"""
Pre-flight Checks for IDE Recovery
Validates system requirements and dependencies before recovery operations
"""

import os
import sys
import json
import subprocess
import platform
import shutil
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('preflight-checks.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PreflightChecker:
    """Pre-flight checks for IDE recovery operations"""
    
    def __init__(self, workspace_root: str | None = None):
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.results = {
            'overall_status': 'unknown',
            'checks': {},
            'recommendations': [],
            'critical_failures': [],
            'warnings': [],
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    def check_disk_space(self, min_gb: int = 2) -> Dict:
        """Check available disk space for recovery operations"""
        logger.info(f"Checking disk space (minimum {min_gb}GB required)...")
        
        check_result = {
            'name': 'Disk Space',
            'status': 'pass',
            'details': {},
            'recommendations': []
        }
        
        try:
            disk_usage = shutil.disk_usage(self.workspace_root)
            free_gb = disk_usage.free / (1024**3)
            
            check_result['details'] = {
                'total_gb': round(disk_usage.total / (1024**3), 2),
                'used_gb': round(disk_usage.used / (1024**3), 2),
                'free_gb': round(free_gb, 2),
                'min_required_gb': min_gb
            }
            
            logger.info(f"Available disk space: {free_gb:.2f}GB")
            
            if free_gb < min_gb:
                check_result['status'] = 'fail'
                check_result['recommendations'].append(
                    f"Insufficient disk space: {free_gb:.2f}GB available, {min_gb}GB required"
                )
                self.results['critical_failures'].append(
                    f"Disk space check failed: {free_gb:.2f}GB < {min_gb}GB"
                )
        except Exception as e:
            check_result['status'] = 'fail'
            check_result['details']['error'] = str(e)
            check_result['recommendations'].append(f"Could not check disk space: {e}")
            self.results['critical_failures'].append(f"Disk space check error: {e}")
        
        self.results['checks']['disk_space'] = check_result
        return check_result
    
    def check_memory(self, min_mb: int = 1024) -> Dict:
        """Check available memory for recovery operations"""
        logger.info(f"Checking memory (minimum {min_mb}MB required)...")
        
        check_result = {
            'name': 'Memory',
            'status': 'pass',
            'details': {},
            'recommendations': []
        }
        
        try:
            import psutil
            memory = psutil.virtual_memory()
            available_mb = memory.available / (1024**2)
            
            check_result['details'] = {
                'total_mb': round(memory.total / (1024**2), 2),
                'available_mb': round(available_mb, 2),
                'used_mb': round(memory.used / (1024**2), 2),
                'min_required_mb': min_mb,
                'usage_percent': memory.percent
            }
            
            logger.info(f"Available memory: {available_mb:.2f}MB ({memory.percent:.1f}% used)")
            
            if available_mb < min_mb:
                check_result['status'] = 'fail'
                check_result['recommendations'].append(
                    f"Insufficient memory: {available_mb:.2f}MB available, {min_mb}MB required"
                )
                self.results['warnings'].append(
                    f"Low memory: {available_mb:.2f}MB < {min_mb}MB"
                )
        except ImportError:
            check_result['recommendations'].append("psutil not available for memory check")
            self.results['warnings'].append("Memory check skipped (psutil not available)")
        except Exception as e:
            check_result['status'] = 'fail'
            check_result['details']['error'] = str(e)
            check_result['recommendations'].append(f"Could not check memory: {e}")
            self.results['warnings'].append(f"Memory check error: {e}")
        
        self.results['checks']['memory'] = check_result
        return check_result
    
    def check_network_connectivity(self) -> Dict:
        """Check network connectivity for recovery operations"""
        logger.info("Checking network connectivity...")
        
        check_result = {
            'name': 'Network Connectivity',
            'status': 'pass',
            'details': {},
            'recommendations': []
        }
        
        try:
            import socket
            import urllib.request
            
            # Test basic connectivity
            test_hosts = [
                ('8.8.8.8', 53),  # Google DNS
                ('1.1.1.1', 53),  # Cloudflare DNS
                ('github.com', 443)  # GitHub
            ]
            
            connectivity_results = []
            for host, port in test_hosts:
                try:
                    socket.create_connection((host, port), timeout=5)
                    connectivity_results.append(f"{host}:{port} - OK")
                    logger.info(f"Network connectivity test passed: {host}:{port}")
                except Exception as e:
                    connectivity_results.append(f"{host}:{port} - Failed: {e}")
                    logger.warning(f"Network connectivity test failed: {host}:{port} - {e}")
            
            check_result['details']['connectivity_tests'] = connectivity_results
            
            # Test internet access
            try:
                urllib.request.urlopen('https://www.google.com', timeout=10)
                check_result['details']['internet_access'] = True
                logger.info("Internet access test passed")
            except Exception as e:
                check_result['details']['internet_access'] = False
                check_result['recommendations'].append(f"Internet access test failed: {e}")
                self.results['warnings'].append(f"Internet connectivity issues: {e}")
            
            # Check if any tests failed
            failed_tests = [result for result in connectivity_results if 'Failed' in result]
            if failed_tests:
                check_result['status'] = 'fail'
                check_result['recommendations'].append(f"Network connectivity tests failed: {failed_tests}")
                self.results['warnings'].append("Network connectivity issues detected")
                
        except Exception as e:
            check_result['status'] = 'fail'
            check_result['details']['error'] = str(e)
            check_result['recommendations'].append(f"Could not check network connectivity: {e}")
            self.results['critical_failures'].append(f"Network connectivity check error: {e}")
        
        self.results['checks']['network_connectivity'] = check_result
        return check_result
    
    def check_python_availability(self) -> Dict:
        """Check Python availability and version"""
        logger.info("Checking Python availability...")
        
        check_result = {
            'name': 'Python Availability',
            'status': 'pass',
            'details': {},
            'recommendations': []
        }
        
        try:
            # Check Python installation
            success, stdout, stderr = self.run_command(['python', '--version'])
            if success:
                python_version = stdout.strip()
                check_result['details']['python_version'] = python_version
                logger.info(f"Python version: {python_version}")
                
                # Parse version
                version_parts = python_version.replace('Python ', '').split('.')
                major, minor = int(version_parts[0]), int(version_parts[1])
                
                if major < 3 or (major == 3 and minor < 8):
                    check_result['status'] = 'fail'
                    check_result['recommendations'].append(
                        f"Python {python_version} is outdated. Python 3.8+ is required."
                    )
                    self.results['critical_failures'].append(
                        f"Python version {python_version} is below minimum requirement (3.8)"
                    )
            else:
                check_result['status'] = 'fail'
                check_result['details']['error'] = stderr
                check_result['recommendations'].append("Python is not installed or not in PATH")
                self.results['critical_failures'].append("Python is not available")
                
        except Exception as e:
            check_result['status'] = 'fail'
            check_result['details']['error'] = str(e)
            check_result['recommendations'].append(f"Could not check Python: {e}")
            self.results['critical_failures'].append(f"Python check error: {e}")
        
        self.results['checks']['python_availability'] = check_result
        return check_result
    
    def check_git_availability(self) -> Dict:
        """Check Git availability and repository status"""
        logger.info("Checking Git availability...")
        
        check_result = {
            'name': 'Git Availability',
            'status': 'pass',
            'details': {},
            'recommendations': []
        }
        
        try:
            # Check Git installation
            success, stdout, stderr = self.run_command(['git', '--version'])
            if success:
                git_version = stdout.strip()
                check_result['details']['git_version'] = git_version
                logger.info(f"Git version: {git_version}")
            else:
                check_result['status'] = 'fail'
                check_result['details']['error'] = stderr
                check_result['recommendations'].append("Git is not installed or not in PATH")
                self.results['critical_failures'].append("Git is not available")
            
            # Check if this is a git repository
            git_dir = self.workspace_root / '.git'
            if not git_dir.exists():
                check_result['status'] = 'fail'
                check_result['recommendations'].append("Not a git repository")
                self.results['critical_failures'].append("Not a git repository")
            else:
                check_result['details']['git_repository'] = True
                logger.info("Git repository detected")
                
                # Check git status
                success, stdout, stderr = self.run_command(['git', 'status', '--porcelain'])
                if success:
                    status_lines = stdout.strip().split('\n') if stdout.strip() else []
                    check_result['details']['uncommitted_changes'] = len(status_lines)
                    
                    if status_lines:
                        check_result['recommendations'].append("Working directory has uncommitted changes")
                        self.results['warnings'].append("Uncommitted changes in git repository")
                else:
                    check_result['recommendations'].append("Could not get git status")
                    self.results['warnings'].append("Git status check failed")
                    
        except Exception as e:
            check_result['status'] = 'fail'
            check_result['details']['error'] = str(e)
            check_result['recommendations'].append(f"Could not check Git: {e}")
            self.results['critical_failures'].append(f"Git check error: {e}")
        
        self.results['checks']['git_availability'] = check_result
        return check_result
    
    def check_recovery_files(self) -> Dict:
        """Check if essential recovery files are present"""
        logger.info("Checking recovery files...")
        
        check_result = {
            'name': 'Recovery Files',
            'status': 'pass',
            'details': {},
            'recommendations': []
        }
        
        # Define essential recovery files
        essential_files = [
            'vscode-profile/settings.json',
            'vscode-profile/keybindings.json',
            'vscode-profile/extensions.txt',
            'vscode-profile/profile.code-profile',
            'restore-guide.md',
            'requirements.txt',
            'setup.py'
        ]
        
        missing_files = []
        existing_files = []
        
        for file_path in essential_files:
            full_path = self.workspace_root / file_path
            if full_path.exists():
                existing_files.append(str(full_path))
                logger.info(f"Recovery file found: {file_path}")
            else:
                missing_files.append(file_path)
                check_result['recommendations'].append(f"Recovery file missing: {file_path}")
                self.results['critical_failures'].append(f"Missing recovery file: {file_path}")
        
        check_result['details'] = {
            'existing_files': existing_files,
            'missing_files': missing_files,
            'total_files': len(essential_files),
            'found_files': len(existing_files)
        }
        
        if missing_files:
            check_result['status'] = 'fail'
        
        self.results['checks']['recovery_files'] = check_result
        return check_result
    
    def check_system_resources(self) -> Dict:
        """Check overall system resource availability"""
        logger.info("Checking system resources...")
        
        check_result = {
            'name': 'System Resources',
            'status': 'pass',
            'details': {},
            'recommendations': []
        }
        
        try:
            import psutil
            
            # Get system information
            system_info = {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'python_implementation': platform.python_implementation()
            }
            check_result['details']['system_info'] = system_info
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            check_result['details']['cpu_usage_percent'] = cpu_percent
            
            if cpu_percent > 90:
                check_result['status'] = 'fail'
                check_result['recommendations'].append(
                    f"High CPU usage: {cpu_percent}% (>90% threshold)"
                )
                self.results['warnings'].append(f"High CPU usage: {cpu_percent}%")
            
            # Check disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                check_result['details']['disk_io'] = {
                    'read_count': disk_io.read_count,
                    'write_count': disk_io.write_count,
                    'read_bytes': disk_io.read_bytes,
                    'write_bytes': disk_io.write_bytes
                }
            
            # Check network I/O
            net_io = psutil.net_io_counters()
            if net_io:
                check_result['details']['network_io'] = {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv
                }
                
        except ImportError:
            check_result['recommendations'].append("psutil not available for system resource check")
            self.results['warnings'].append("System resource check skipped (psutil not available)")
        except Exception as e:
            check_result['status'] = 'fail'
            check_result['details']['error'] = str(e)
            check_result['recommendations'].append(f"Could not check system resources: {e}")
            self.results['warnings'].append(f"System resource check error: {e}")
        
        self.results['checks']['system_resources'] = check_result
        return check_result
    
    def run_command(self, command: List[str], cwd: Path | None = None) -> Tuple[bool, str, str]:
        """Execute a command and return success, stdout, stderr"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=cwd or self.workspace_root,
                timeout=30
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def run_all_checks(self) -> Dict:
        """Run all pre-flight checks"""
        logger.info("Starting pre-flight checks...")
        
        # Run all checks
        self.check_disk_space()
        self.check_memory()
        self.check_network_connectivity()
        self.check_python_availability()
        self.check_git_availability()
        self.check_recovery_files()
        self.check_system_resources()
        
        # Determine overall status
        failed_checks = [check for check in self.results['checks'].values() if check['status'] == 'fail']
        critical_failures = len(self.results['critical_failures'])
        
        if critical_failures > 0:
            self.results['overall_status'] = 'fail'
        elif failed_checks:
            self.results['overall_status'] = 'warning'
        else:
            self.results['overall_status'] = 'pass'
        
        # Generate summary
        logger.info(f"Pre-flight checks completed. Overall status: {self.results['overall_status']}")
        logger.info(f"Failed checks: {len(failed_checks)}")
        logger.info(f"Critical failures: {critical_failures}")
        logger.info(f"Warnings: {len(self.results['warnings'])}")
        
        return self.results
    
    def generate_report(self, output_file: str | None = None) -> str:
        """Generate a detailed pre-flight check report"""
        if not output_file:
            output_file = f"preflight-checks-report-{self.workspace_root.name}.json"
        
        # Add summary
        self.results['summary'] = {
            'total_checks': len(self.results['checks']),
            'failed_checks': len([check for check in self.results['checks'].values() if check['status'] == 'fail']),
            'passed_checks': len([check for check in self.results['checks'].values() if check['status'] == 'pass']),
            'critical_failures': len(self.results['critical_failures']),
            'warnings': len(self.results['warnings']),
            'recommendations': len(self.results['recommendations']),
            'workspace_path': str(self.workspace_root)
        }
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Pre-flight check report saved to: {output_file}")
        return output_file
    
    def should_proceed(self) -> bool:
        """Determine if recovery should proceed based on pre-flight checks"""
        if self.results['overall_status'] == 'fail':
            logger.error("Pre-flight checks failed. Recovery cannot proceed.")
            return False
        elif self.results['overall_status'] == 'warning':
            logger.warning("Pre-flight checks have warnings. Recovery may proceed with caution.")
            return True
        else:
            logger.info("Pre-flight checks passed. Recovery can proceed.")
            return True

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run pre-flight checks for IDE recovery')
    parser.add_argument('--workspace', '-w', help='Workspace root directory', default='.')
    parser.add_argument('--output', '-o', help='Output report file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--min-disk-gb', type=int, default=2, help='Minimum disk space in GB')
    parser.add_argument('--min-memory-mb', type=int, default=1024, help='Minimum memory in MB')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create checker and run checks
    checker = PreflightChecker(args.workspace)
    results = checker.run_all_checks()
    
    # Generate report
    report_file = checker.generate_report(args.output)
    
    # Print summary
    print(f"\n{'='*60}")
    print("PRE-FLIGHT CHECKS SUMMARY")
    print(f"{'='*60}")
    print(f"Workspace: {checker.workspace_root}")
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Total Checks: {len(results['checks'])}")
    print(f"Failed Checks: {len([check for check in results['checks'].values() if check['status'] == 'fail'])}")
    print(f"Critical Failures: {len(results['critical_failures'])}")
    print(f"Warnings: {len(results['warnings'])}")
    print(f"Recommendations: {len(results['recommendations'])}")
    print(f"Report: {report_file}")
    print(f"{'='*60}")
    
    # Determine if we should proceed
    if checker.should_proceed():
        print("\n✅ Pre-flight checks passed. Recovery can proceed.")
        sys.exit(0)
    else:
        print("\n❌ Pre-flight checks failed. Recovery cannot proceed.")
        sys.exit(1)

if __name__ == '__main__':
    main()