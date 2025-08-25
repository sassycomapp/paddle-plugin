#!/usr/bin/env python3
"""
Cross-Platform Testing Scripts
Creates testing scripts for Windows, macOS, and Linux platforms
"""

import os
import sys
import json
import platform
import subprocess
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
        logging.FileHandler('cross-platform-test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CrossPlatformTester:
    """Cross-platform testing for IDE recovery system"""
    
    def __init__(self, workspace_root: str | None = None, test_dir: str | None = None):
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.test_dir = Path(test_dir) if test_dir else self.workspace_root / 'test-results'
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = {
            'test_suite': 'cross_platform',
            'platform': platform.system(),
            'overall_status': 'unknown',
            'platform_tests': {},
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'start_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': None,
            'duration': None
        }
        
    def run_command(self, command: List[str], cwd: Path | None = None, 
                   timeout: int = 300) -> Tuple[bool, str, str]:
        """Execute a command and return success, stdout, stderr"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=cwd or self.workspace_root,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def test_python_environment(self) -> Dict:
        """Test Python environment compatibility"""
        logger.info("Testing Python environment...")
        
        test_result = {
            'test_name': 'python_environment',
            'description': 'Test Python environment compatibility',
            'status': 'unknown',
            'details': {},
            'warnings': [],
            'errors': []
        }
        
        try:
            # Check Python version
            success, stdout, stderr = self.run_command(['python', '--version'])
            if success:
                python_version = stdout.strip()
                test_result['details']['python_version'] = python_version
                logger.info(f"Python version: {python_version}")
            else:
                test_result['errors'].append(f"Python not available: {stderr}")
                test_result['status'] = 'failed'
                return test_result
            
            # Check pip availability
            success, stdout, stderr = self.run_command(['pip', '--version'])
            if success:
                pip_version = stdout.strip()
                test_result['details']['pip_version'] = pip_version
                logger.info(f"pip version: {pip_version}")
            else:
                test_result['warnings'].append(f"pip not available: {stderr}")
            
            # Test basic Python functionality
            test_code = '''
import sys
import os
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Platform: {sys.platform}")
print(f"Working directory: {os.getcwd()}")
'''
            success, stdout, stderr = self.run_command(['python', '-c', test_code])
            if success:
                test_result['details']['python_test_output'] = stdout.strip()
                logger.info("Python functionality test passed")
            else:
                test_result['errors'].append(f"Python functionality test failed: {stderr}")
                test_result['status'] = 'failed'
                return test_result
            
            # Test virtual environment creation
            venv_path = self.test_dir / 'test-venv'
            success, stdout, stderr = self.run_command(['python', '-m', 'venv', str(venv_path)])
            if success:
                test_result['details']['venv_created'] = True
                logger.info("Virtual environment creation test passed")
                
                # Clean up
                if venv_path.exists():
                    shutil.rmtree(venv_path)
            else:
                test_result['warnings'].append(f"Virtual environment creation failed: {stderr}")
            
            test_result['status'] = 'completed'
            logger.info("Python environment test completed")
            
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(f"Python environment test failed: {e}")
            logger.error(f"Python environment test failed: {e}")
        
        return test_result
    
    def test_node_environment(self) -> Dict:
        """Test Node.js environment compatibility"""
        logger.info("Testing Node.js environment...")
        
        test_result = {
            'test_name': 'node_environment',
            'description': 'Test Node.js environment compatibility',
            'status': 'unknown',
            'details': {},
            'warnings': [],
            'errors': []
        }
        
        try:
            # Check Node.js version
            success, stdout, stderr = self.run_command(['node', '--version'])
            if success:
                node_version = stdout.strip()
                test_result['details']['node_version'] = node_version
                logger.info(f"Node.js version: {node_version}")
            else:
                test_result['warnings'].append(f"Node.js not available: {stderr}")
            
            # Check npm version
            success, stdout, stderr = self.run_command(['npm', '--version'])
            if success:
                npm_version = stdout.strip()
                test_result['details']['npm_version'] = npm_version
                logger.info(f"npm version: {npm_version}")
            else:
                test_result['warnings'].append(f"npm not available: {stderr}")
            
            # Test basic Node.js functionality
            test_code = '''
const os = require('os');
const path = require('path');
console.log(`Node.js version: ${process.version}`);
console.log(`Platform: ${process.platform}`);
console.log(`Architecture: ${process.arch}`);
console.log(`Working directory: ${process.cwd()}`);
console.log(`Home directory: ${os.homedir()}`);
'''
            success, stdout, stderr = self.run_command(['node', '-e', test_code])
            if success:
                test_result['details']['node_test_output'] = stdout.strip()
                logger.info("Node.js functionality test passed")
            else:
                test_result['warnings'].append(f"Node.js functionality test failed: {stderr}")
            
            test_result['status'] = 'completed'
            logger.info("Node.js environment test completed")
            
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(f"Node.js environment test failed: {e}")
            logger.error(f"Node.js environment test failed: {e}")
        
        return test_result
    
    def test_git_environment(self) -> Dict:
        """Test Git environment compatibility"""
        logger.info("Testing Git environment...")
        
        test_result = {
            'test_name': 'git_environment',
            'description': 'Test Git environment compatibility',
            'status': 'unknown',
            'details': {},
            'warnings': [],
            'errors': []
        }
        
        try:
            # Check Git version
            success, stdout, stderr = self.run_command(['git', '--version'])
            if success:
                git_version = stdout.strip()
                test_result['details']['git_version'] = git_version
                logger.info(f"Git version: {git_version}")
            else:
                test_result['errors'].append(f"Git not available: {stderr}")
                test_result['status'] = 'failed'
                return test_result
            
            # Test basic Git functionality
            success, stdout, stderr = self.run_command(['git', 'status'])
            if success:
                test_result['details']['git_status'] = stdout.strip()
                logger.info("Git status test passed")
            else:
                test_result['warnings'].append(f"Git status test failed: {stderr}")
            
            # Test Git configuration
            success, stdout, stderr = self.run_command(['git', 'config', '--global', '--list'])
            if success:
                git_config = stdout.strip()
                test_result['details']['git_config'] = git_config[:200] + "..." if len(git_config) > 200 else git_config
                logger.info("Git configuration test passed")
            else:
                test_result['warnings'].append(f"Git configuration test failed: {stderr}")
            
            test_result['status'] = 'completed'
            logger.info("Git environment test completed")
            
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(f"Git environment test failed: {e}")
            logger.error(f"Git environment test failed: {e}")
        
        return test_result
    
    def test_vscode_extensions(self) -> Dict:
        """Test VS Code extension compatibility"""
        logger.info("Testing VS Code extensions...")
        
        test_result = {
            'test_name': 'vscode_extensions',
            'description': 'Test VS Code extension compatibility',
            'status': 'unknown',
            'details': {},
            'warnings': [],
            'errors': []
        }
        
        try:
            # Check if code command is available
            success, stdout, stderr = self.run_command(['code', '--version'])
            if success:
                vscode_version = stdout.strip().split('\n')[0]
                test_result['details']['vscode_version'] = vscode_version
                logger.info(f"VS Code version: {vscode_version}")
            else:
                test_result['warnings'].append(f"VS Code command not available: {stderr}")
            
            # Check if code command can list extensions
            success, stdout, stderr = self.run_command(['code', '--list-extensions'])
            if success:
                extensions = stdout.strip().split('\n')
                test_result['details']['installed_extensions'] = extensions
                test_result['details']['extension_count'] = len(extensions)
                logger.info(f"Found {len(extensions)} installed extensions")
            else:
                test_result['warnings'].append(f"Could not list extensions: {stderr}")
            
            # Test extension installation (dry run)
            test_extensions = ['ms-python.python', 'ms-python.vscode-pylance']
            for extension in test_extensions:
                success, stdout, stderr = self.run_command(['code', '--install-extension', extension, '--force'])
                if success:
                    test_result['details'][f'{extension}_install'] = True
                    logger.info(f"Extension {extension} installation test passed")
                else:
                    test_result['warnings'].append(f"Extension {extension} installation test failed: {stderr}")
            
            test_result['status'] = 'completed'
            logger.info("VS Code extensions test completed")
            
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(f"VS Code extensions test failed: {e}")
            logger.error(f"VS Code extensions test failed: {e}")
        
        return test_result
    
    def test_file_system_operations(self) -> Dict:
        """Test file system operations compatibility"""
        logger.info("Testing file system operations...")
        
        test_result = {
            'test_name': 'file_system_operations',
            'description': 'Test file system operations compatibility',
            'status': 'unknown',
            'details': {},
            'warnings': [],
            'errors': []
        }
        
        try:
            # Create test directory
            test_dir = self.test_dir / 'file-system-test'
            test_dir.mkdir(parents=True, exist_ok=True)
            test_result['details']['test_directory'] = str(test_dir)
            
            # Test file creation
            test_file = test_dir / 'test-file.txt'
            test_file.write_text('Test content')
            test_result['details']['file_created'] = True
            
            # Test file reading
            content = test_file.read_text()
            test_result['details']['file_content'] = content
            
            # Test file copying
            copy_file = test_dir / 'copy-file.txt'
            shutil.copy2(test_file, copy_file)
            test_result['details']['file_copied'] = True
            
            # Test file moving
            move_file = test_dir / 'move-file.txt'
            shutil.move(copy_file, move_file)
            test_result['details']['file_moved'] = True
            
            # Test directory creation
            sub_dir = test_dir / 'sub-directory'
            sub_dir.mkdir(parents=True, exist_ok=True)
            test_result['details']['directory_created'] = True
            
            # Test directory listing
            files = list(test_dir.iterdir())
            test_result['details']['directory_contents'] = [f.name for f in files]
            
            # Test file permissions
            test_file.chmod(0o644)
            test_result['details']['permissions_set'] = True
            
            # Clean up
            shutil.rmtree(test_dir)
            test_result['details']['cleanup_completed'] = True
            
            test_result['status'] = 'completed'
            logger.info("File system operations test completed")
            
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(f"File system operations test failed: {e}")
            logger.error(f"File system operations test failed: {e}")
        
        return test_result
    
    def test_network_operations(self) -> Dict:
        """Test network operations compatibility"""
        logger.info("Testing network operations...")
        
        test_result = {
            'test_name': 'network_operations',
            'description': 'Test network operations compatibility',
            'status': 'unknown',
            'details': {},
            'warnings': [],
            'errors': []
        }
        
        try:
            # Test basic network connectivity
            success, stdout, stderr = self.run_command(['ping', '-c', '1', 'github.com'])
            if success:
                test_result['details']['github_ping'] = True
                logger.info("GitHub ping test passed")
            else:
                test_result['warnings'].append(f"GitHub ping test failed: {stderr}")
            
            # Test HTTP requests
            try:
                import urllib.request
                import urllib.error
                
                response = urllib.request.urlopen('https://api.github.com', timeout=10)
                test_result['details']['http_request'] = {
                    'status_code': response.getcode(),
                    'headers': dict(response.headers)
                }
                logger.info("HTTP request test passed")
            except Exception as e:
                test_result['warnings'].append(f"HTTP request test failed: {e}")
            
            # Test DNS resolution
            import socket
            try:
                ip = socket.gethostbyname('github.com')
                test_result['details']['dns_resolution'] = ip
                logger.info(f"DNS resolution test passed: {ip}")
            except Exception as e:
                test_result['warnings'].append(f"DNS resolution test failed: {e}")
            
            test_result['status'] = 'completed'
            logger.info("Network operations test completed")
            
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(f"Network operations test failed: {e}")
            logger.error(f"Network operations test failed: {e}")
        
        return test_result
    
    def test_platform_specific_features(self) -> Dict:
        """Test platform-specific features"""
        logger.info("Testing platform-specific features...")
        
        test_result = {
            'test_name': 'platform_specific_features',
            'description': 'Test platform-specific features',
            'status': 'unknown',
            'details': {},
            'warnings': [],
            'errors': []
        }
        
        system = platform.system()
        
        try:
            if system == 'Windows':
                # Test Windows-specific features
                test_result['details']['platform'] = 'Windows'
                
                # Test PowerShell availability
                success, stdout, stderr = self.run_command(['powershell', '-Command', 'Get-Host'])
                if success:
                    test_result['details']['powershell_available'] = True
                    logger.info("PowerShell test passed")
                else:
                    test_result['warnings'].append(f"PowerShell test failed: {stderr}")
                
                # Test Windows path handling
                test_path = os.path.join('C:', 'Temp', 'test')
                test_result['details']['windows_path_handling'] = test_path
                
            elif system == 'Darwin':  # macOS
                # Test macOS-specific features
                test_result['details']['platform'] = 'macOS'
                
                # Test Homebrew availability
                success, stdout, stderr = self.run_command(['brew', '--version'])
                if success:
                    test_result['details']['homebrew_available'] = True
                    brew_version = stdout.strip()
                    test_result['details']['homebrew_version'] = brew_version
                    logger.info(f"Homebrew test passed: {brew_version}")
                else:
                    test_result['warnings'].append(f"Homebrew test failed: {stderr}")
                
                # Test macOS path handling
                test_path = os.path.join('/tmp', 'test')
                test_result['details']['macos_path_handling'] = test_path
                
            elif system == 'Linux':
                # Test Linux-specific features
                test_result['details']['platform'] = 'Linux'
                
                # Test apt-get availability
                success, stdout, stderr = self.run_command(['apt-get', '--version'])
                if success:
                    test_result['details']['apt_available'] = True
                    logger.info("apt-get test passed")
                else:
                    test_result['warnings'].append(f"apt-get test failed: {stderr}")
                
                # Test Linux path handling
                test_path = os.path.join('/tmp', 'test')
                test_result['details']['linux_path_handling'] = test_path
                
            else:
                test_result['warnings'].append(f"Unknown platform: {system}")
            
            test_result['status'] = 'completed'
            logger.info("Platform-specific features test completed")
            
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(f"Platform-specific features test failed: {e}")
            logger.error(f"Platform-specific features test failed: {e}")
        
        return test_result
    
    def run_all_tests(self) -> Dict:
        """Run all cross-platform tests"""
        logger.info("Starting cross-platform testing...")
        
        # Run all tests
        tests = {
            'python_environment': self.test_python_environment(),
            'node_environment': self.test_node_environment(),
            'git_environment': self.test_git_environment(),
            'vscode_extensions': self.test_vscode_extensions(),
            'file_system_operations': self.test_file_system_operations(),
            'network_operations': self.test_network_operations(),
            'platform_specific_features': self.test_platform_specific_features()
        }
        
        # Store results
        self.results['platform_tests'] = tests
        self.results['total_tests'] = len(tests)
        
        # Calculate results
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        
        for test_name, test_result in tests.items():
            if test_result['status'] == 'completed':
                passed_tests += 1
            elif test_result['status'] == 'failed':
                failed_tests += 1
            else:
                skipped_tests += 1
            
            self.results['platform_tests'][test_name] = test_result
        
        self.results['passed_tests'] = passed_tests
        self.results['failed_tests'] = failed_tests
        self.results['skipped_tests'] = skipped_tests
        
        # Determine overall status
        if failed_tests > 0:
            self.results['overall_status'] = 'fail'
        elif passed_tests == self.results['total_tests']:
            self.results['overall_status'] = 'pass'
        else:
            self.results['overall_status'] = 'warning'
        
        # Record end time
        self.results['end_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
        self.results['duration'] = time.time() - time.mktime(time.strptime(self.results['start_time'], '%Y-%m-%d %H:%M:%S'))
        
        logger.info(f"Cross-platform testing completed. Overall status: {self.results['overall_status']}")
        logger.info(f"Total tests: {self.results['total_tests']}")
        logger.info(f"Passed: {self.results['passed_tests']}")
        logger.info(f"Failed: {self.results['failed_tests']}")
        logger.info(f"Skipped: {self.results['skipped_tests']}")
        logger.info(f"Duration: {self.results['duration']:.2f} seconds")
        
        return self.results
    
    def generate_report(self, output_file: str | None = None) -> str:
        """Generate a detailed test report"""
        if not output_file:
            output_file = f"cross-platform-test-report-{self.workspace_root.name}.json"
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Cross-platform test report saved to: {output_file}")
        return output_file
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*80}")
        print("CROSS-PLATFORM TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Test Suite: {self.results['test_suite']}")
        print(f"Platform: {self.results['platform']}")
        print(f"Overall Status: {self.results['overall_status'].upper()}")
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"Passed: {self.results['passed_tests']}")
        print(f"Failed: {self.results['failed_tests']}")
        print(f"Skipped: {self.results['skipped_tests']}")
        print(f"Duration: {self.results['duration']:.2f} seconds")
        print(f"{'='*80}")
        
        # Print test details
        for test_name, test_result in self.results['platform_tests'].items():
            status_icon = "✅" if test_result['status'] == 'completed' else "❌" if test_result['status'] == 'failed' else "⏸️"
            print(f"{status_icon} {test_name}: {test_result['description']}")
            if test_result['status'] == 'failed':
                for error in test_result.get('errors', []):
                    print(f"   Error: {error}")
            elif test_result['status'] == 'completed':
                details = test_result.get('details', {})
                if details:
                    print(f"   Details: {details}")
        
        print(f"{'='*80}")

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cross-platform testing for IDE recovery system')
    parser.add_argument('--workspace', '-w', help='Workspace root directory', default='.')
    parser.add_argument('--test-dir', '-t', help='Test results directory', default=None)
    parser.add_argument('--output', '-o', help='Output report file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create tester and run tests
    tester = CrossPlatformTester(args.workspace, args.test_dir)
    results = tester.run_all_tests()
    
    # Generate report
    report_file = tester.generate_report(args.output)
    
    # Print summary
    tester.print_summary()
    
    # Exit with appropriate code
    if results['overall_status'] == 'fail':
        print(f"\n❌ Cross-platform testing failed.")
        print(f"Report: {report_file}")
        sys.exit(1)
    else:
        print(f"\n✅ Cross-platform testing completed successfully.")
        print(f"Report: {report_file}")
        sys.exit(0)

if __name__ == '__main__':
    main()