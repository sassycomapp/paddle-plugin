#!/usr/bin/env python3
"""
Post-Recovery Validation Script
Validates IDE environment after recovery operations are completed
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
        logging.FileHandler('post-recovery-validation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PostRecoveryValidator:
    """Post-recovery validation for IDE environment"""
    
    def __init__(self, workspace_root: str | None = None):
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.results = {
            'overall_status': 'unknown',
            'checks': {},
            'recommendations': [],
            'critical_issues': [],
            'warnings': [],
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'recovery_summary': {
                'start_time': None,
                'end_time': None,
                'duration': None,
                'operations_completed': []
            }
        }
        
    def validate_python_environment(self) -> Dict:
        """Validate Python environment after recovery"""
        logger.info("Validating Python environment after recovery...")
        
        check_result = {
            'name': 'Python Environment',
            'status': 'pass',
            'details': {},
            'recommendations': []
        }
        
        # Check Python installation
        success, stdout, stderr = self.run_command(['python', '--version'])
        if success:
            python_version = stdout.strip()
            check_result['details']['python_version'] = python_version
            logger.info(f"Python version: {python_version}")
            
            # Check Python version compatibility
            version_parts = python_version.replace('Python ', '').split('.')
            major, minor = int(version_parts[0]), int(version_parts[1])
            if major < 3 or (major == 3 and minor < 8):
                check_result['status'] = 'fail'
                check_result['recommendations'].append(
                    f"Python {python_version} is outdated. Python 3.8+ is recommended."
                )
                self.results['critical_issues'].append(
                    f"Python version {python_version} is below minimum requirement (3.8)"
                )
        else:
            check_result['status'] = 'fail'
            check_result['details']['error'] = stderr
            check_result['recommendations'].append("Python is not installed or not in PATH")
            self.results['critical_issues'].append("Python is not available")
        
        # Check pip
        success, stdout, stderr = self.run_command(['pip', '--version'])
        if success:
            pip_version = stdout.strip()
            check_result['details']['pip_version'] = pip_version
            logger.info(f"Pip version: {pip_version}")
        else:
            check_result['status'] = 'fail'
            check_result['recommendations'].append("Pip is not available")
            self.results['critical_issues'].append("Pip is not available")
        
        # Check virtual environment
        venv_path = self.workspace_root / '.venv'
        if venv_path.exists():
            check_result['details']['virtual_env'] = str(venv_path)
            logger.info(f"Virtual environment found: {venv_path}")
            
            # Check if virtual environment is activated
            if sys.prefix == str(venv_path):
                check_result['details']['venv_activated'] = True
                logger.info("Virtual environment is activated")
            else:
                check_result['details']['venv_activated'] = False
                check_result['recommendations'].append("Virtual environment exists but not activated")
                self.results['warnings'].append("Virtual environment not activated")
        else:
            check_result['recommendations'].append("Virtual environment not found")
            self.results['warnings'].append("No virtual environment detected")
        
        # Check key Python packages
        required_packages = [
            'black', 'flake8', 'pylint', 'isort', 'pytest', 'mypy',
            'jupyter', 'notebook', 'ipython', 'matplotlib', 'pandas', 'numpy'
        ]
        
        installed_packages = []
        for package in required_packages:
            success, stdout, stderr = self.run_command(['pip', 'show', package])
            if success:
                installed_packages.append(package)
                logger.info(f"Package {package} is installed")
            else:
                check_result['recommendations'].append(f"Package {package} is not installed")
                self.results['warnings'].append(f"Missing package: {package}")
        
        check_result['details']['installed_packages'] = installed_packages
        check_result['details']['missing_packages'] = [p for p in required_packages if p not in installed_packages]
        
        # Check if packages are importable
        importable_packages = []
        for package in installed_packages:
            success, stdout, stderr = self.run_command(['python', '-c', f'import {package}'])
            if success:
                importable_packages.append(package)
                logger.info(f"Package {package} is importable")
            else:
                check_result['recommendations'].append(f"Package {package} is installed but not importable")
                self.results['warnings'].append(f"Package {package} not importable")
        
        check_result['details']['importable_packages'] = importable_packages
        check_result['details']['non_importable_packages'] = [p for p in installed_packages if p not in importable_packages]
        
        self.results['checks']['python_environment'] = check_result
        return check_result
    
    def validate_nodejs_environment(self) -> Dict:
        """Validate Node.js environment after recovery"""
        logger.info("Validating Node.js environment after recovery...")
        
        check_result = {
            'name': 'Node.js Environment',
            'status': 'pass',
            'details': {},
            'recommendations': []
        }
        
        # Check Node.js installation
        success, stdout, stderr = self.run_command(['node', '--version'])
        if success:
            node_version = stdout.strip()
            check_result['details']['node_version'] = node_version
            logger.info(f"Node.js version: {node_version}")
            
            # Check Node.js version compatibility
            version_parts = node_version.replace('v', '').split('.')
            major, minor = int(version_parts[0]), int(version_parts[1])
            if major < 14 or (major == 14 and minor < 17):
                check_result['status'] = 'fail'
                check_result['recommendations'].append(
                    f"Node.js {node_version} is outdated. Node.js 14.17+ is recommended."
                )
                self.results['warnings'].append(
                    f"Node.js version {node_version} is below recommended minimum (14.17)"
                )
        else:
            check_result['status'] = 'fail'
            check_result['details']['error'] = stderr
            check_result['recommendations'].append("Node.js is not installed or not in PATH")
            self.results['warnings'].append("Node.js is not available")
        
        # Check npm
        success, stdout, stderr = self.run_command(['npm', '--version'])
        if success:
            npm_version = stdout.strip()
            check_result['details']['npm_version'] = npm_version
            logger.info(f"npm version: {npm_version}")
        else:
            check_result['status'] = 'fail'
            check_result['recommendations'].append("npm is not available")
            self.results['warnings'].append("npm is not available")
        
        # Check package.json
        package_json_path = self.workspace_root / 'package.json'
        if package_json_path.exists():
            check_result['details']['package_json'] = str(package_json_path)
            logger.info("package.json found")
            
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    check_result['details']['package_name'] = package_data.get('name', 'Unknown')
                    check_result['details']['package_version'] = package_data.get('version', 'Unknown')
                    check_result['details']['dependencies'] = list(package_data.get('dependencies', {}).keys())
                    check_result['details']['dev_dependencies'] = list(package_data.get('devDependencies', {}).keys())
            except json.JSONDecodeError as e:
                check_result['status'] = 'fail'
                check_result['recommendations'].append(f"package.json is malformed: {e}")
                self.results['warnings'].append("package.json is invalid JSON")
        else:
            check_result['recommendations'].append("package.json not found")
            self.results['warnings'].append("No package.json detected")
        
        # Check node_modules
        node_modules_path = self.workspace_root / 'node_modules'
        if node_modules_path.exists():
            check_result['details']['node_modules'] = str(node_modules_path)
            logger.info("node_modules directory found")
            
            # Check if node_modules contains expected packages
            if package_json_path.exists():
                try:
                    with open(package_json_path, 'r') as f:
                        package_data = json.load(f)
                        dependencies = list(package_data.get('dependencies', {}).keys())
                        dev_dependencies = list(package_data.get('devDependencies', {}).keys())
                        
                        # Check if dependencies are installed
                        installed_deps = []
                        for dep in dependencies + dev_dependencies:
                            dep_path = node_modules_path / dep
                            if dep_path.exists():
                                installed_deps.append(dep)
                        
                        check_result['details']['installed_dependencies'] = installed_deps
                        check_result['details']['missing_dependencies'] = [d for d in dependencies + dev_dependencies if d not in installed_deps]
                        
                        if missing_deps := [d for d in dependencies + dev_dependencies if d not in installed_deps]:
                            check_result['recommendations'].append(f"Missing dependencies: {missing_deps}")
                            self.results['warnings'].append(f"Missing Node.js dependencies: {missing_deps}")
                            
                except Exception as e:
                    check_result['recommendations'].append(f"Could not check dependencies: {e}")
                    self.results['warnings'].append(f"Dependency check failed: {e}")
        else:
            check_result['recommendations'].append("node_modules directory not found")
            self.results['warnings'].append("Dependencies not installed")
        
        self.results['checks']['nodejs_environment'] = check_result
        return check_result
    
    def validate_vscode_configuration(self) -> Dict:
        """Validate VS Code configuration after recovery"""
        logger.info("Validating VS Code configuration after recovery...")
        
        check_result = {
            'name': 'VS Code Configuration',
            'status': 'pass',
            'details': {},
            'recommendations': []
        }
        
        # Check VS Code settings file
        settings_path = self.workspace_root / 'vscode-profile' / 'settings.json'
        if settings_path.exists():
            check_result['details']['settings_file'] = str(settings_path)
            logger.info("VS Code settings file found")
            
            try:
                with open(settings_path, 'r') as f:
                    settings_data = json.load(f)
                    check_result['details']['settings_count'] = len(settings_data)
                    check_result['details']['python_settings'] = [k for k in settings_data.keys() if k.startswith('python.')]
                    check_result['details']['editor_settings'] = [k for k in settings_data.keys() if k.startswith('editor.')]
                    check_result['details']['terminal_settings'] = [k for k in settings_data.keys() if k.startswith('terminal.')]
                    check_result['details']['git_settings'] = [k for k in settings_data.keys() if k.startswith('git.')]
                    
                    # Check for essential settings
                    essential_settings = [
                        'python.defaultInterpreterPath',
                        'python.linting.enabled',
                        'python.formatting.provider',
                        'editor.formatOnSave',
                        'terminal.integrated.shell.windows'
                    ]
                    
                    missing_settings = [s for s in essential_settings if s not in settings_data]
                    if missing_settings:
                        check_result['recommendations'].append(f"Missing essential settings: {missing_settings}")
                        self.results['warnings'].append(f"Missing VS Code settings: {missing_settings}")
                        
            except json.JSONDecodeError as e:
                check_result['status'] = 'fail'
                check_result['recommendations'].append(f"settings.json is malformed: {e}")
                self.results['warnings'].append("VS Code settings file is invalid JSON")
        else:
            check_result['status'] = 'fail'
            check_result['recommendations'].append("VS Code settings file not found")
            self.results['critical_issues'].append("VS Code settings file missing")
        
        # Check VS Code extensions file
        extensions_path = self.workspace_root / 'vscode-profile' / 'extensions.txt'
        if extensions_path.exists():
            check_result['details']['extensions_file'] = str(extensions_path)
            logger.info("VS Code extensions file found")
            
            try:
                with open(extensions_path, 'r') as f:
                    extensions = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    check_result['details']['extensions_count'] = len(extensions)
                    check_result['details']['extensions'] = extensions
            except Exception as e:
                check_result['status'] = 'fail'
                check_result['recommendations'].append(f"extensions.txt could not be read: {e}")
                self.results['warnings'].append("VS Code extensions file could not be read")
        else:
            check_result['status'] = 'fail'
            check_result['recommendations'].append("VS Code extensions file not found")
            self.results['critical_issues'].append("VS Code extensions file missing")
        
        # Check VS Code keybindings file
        keybindings_path = self.workspace_root / 'vscode-profile' / 'keybindings.json'
        if keybindings_path.exists():
            check_result['details']['keybindings_file'] = str(keybindings_path)
            logger.info("VS Code keybindings file found")
            
            try:
                with open(keybindings_path, 'r') as f:
                    keybindings_data = json.load(f)
                    check_result['details']['keybindings_count'] = len(keybindings_data)
            except json.JSONDecodeError as e:
                check_result['status'] = 'fail'
                check_result['recommendations'].append(f"keybindings.json is malformed: {e}")
                self.results['warnings'].append("VS Code keybindings file is invalid JSON")
        else:
            check_result['status'] = 'fail'
            check_result['recommendations'].append("VS Code keybindings file not found")
            self.results['critical_issues'].append("VS Code keybindings file missing")
        
        # Check VS Code profile file
        profile_path = self.workspace_root / 'vscode-profile' / 'profile.code-profile'
        if profile_path.exists():
            check_result['details']['profile_file'] = str(profile_path)
            logger.info("VS Code profile file found")
            
            try:
                with open(profile_path, 'r') as f:
                    profile_data = json.load(f)
                    check_result['details']['profile_version'] = profile_data.get('version', 'Unknown')
                    check_result['details']['profile_name'] = profile_data.get('name', 'Unknown')
                    check_result['details']['profile_settings_count'] = len(profile_data.get('settings', {}))
                    check_result['details']['profile_extensions_count'] = len(profile_data.get('extensions', []))
            except json.JSONDecodeError as e:
                check_result['status'] = 'fail'
                check_result['recommendations'].append(f"profile.code-profile is malformed: {e}")
                self.results['warnings'].append("VS Code profile file is invalid JSON")
        else:
            check_result['status'] = 'fail'
            check_result['recommendations'].append("VS Code profile file not found")
            self.results['critical_issues'].append("VS Code profile file missing")
        
        self.results['checks']['vscode_configuration'] = check_result
        return check_result
    
    def validate_project_structure(self) -> Dict:
        """Validate project structure after recovery"""
        logger.info("Validating project structure after recovery...")
        
        check_result = {
            'name': 'Project Structure',
            'status': 'pass',
            'details': {},
            'recommendations': []
        }
        
        # Define essential directories and files
        essential_items = {
            'directories': [
                'src',
                'tests',
                'docs',
                'scripts',
                'vscode-profile'
            ],
            'files': [
                'README.md',
                'requirements.txt',
                'setup.py',
                'pyproject.toml',
                '.gitignore',
                'restore-guide.md'
            ]
        }
        
        # Check directories
        missing_directories = []
        existing_directories = []
        
        for directory in essential_items['directories']:
            dir_path = self.workspace_root / directory
            if dir_path.exists() and dir_path.is_dir():
                existing_directories.append(str(dir_path))
                logger.info(f"Directory found: {directory}")
            else:
                missing_directories.append(directory)
                check_result['recommendations'].append(f"Directory '{directory}' not found")
                self.results['warnings'].append(f"Missing directory: {directory}")
        
        check_result['details']['directories'] = {
            'existing': existing_directories,
            'missing': missing_directories
        }
        
        # Check files
        missing_files = []
        existing_files = []
        
        for file in essential_items['files']:
            file_path = self.workspace_root / file
            if file_path.exists() and file_path.is_file():
                existing_files.append(str(file_path))
                logger.info(f"File found: {file}")
            else:
                missing_files.append(file)
                check_result['recommendations'].append(f"File '{file}' not found")
                self.results['warnings'].append(f"Missing file: {file}")
        
        check_result['details']['files'] = {
            'existing': existing_files,
            'missing': missing_files
        }
        
        # Check if there are any missing essential items
        if missing_directories or missing_files:
            check_result['status'] = 'fail'
        
        self.results['checks']['project_structure'] = check_result
        return check_result
    
    def validate_git_repository(self) -> Dict:
        """Validate Git repository after recovery"""
        logger.info("Validating Git repository after recovery...")
        
        check_result = {
            'name': 'Git Repository',
            'status': 'pass',
            'details': {},
            'recommendations': []
        }
        
        # Check if this is a git repository
        git_dir = self.workspace_root / '.git'
        if not git_dir.exists():
            check_result['status'] = 'fail'
            check_result['recommendations'].append("Not a git repository")
            self.results['critical_issues'].append("Not a git repository")
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
            
            # Check git remote
            success, stdout, stderr = self.run_command(['git', 'remote', '-v'])
            if success:
                remotes = stdout.strip().split('\n') if stdout.strip() else []
                check_result['details']['git_remotes'] = remotes
                logger.info(f"Git remotes: {remotes}")
            else:
                check_result['recommendations'].append("Could not get git remotes")
                self.results['warnings'].append("Git remote check failed")
            
            # Check git log
            success, stdout, stderr = self.run_command(['git', 'log', '--oneline', '-5'])
            if success:
                commits = stdout.strip().split('\n') if stdout.strip() else []
                check_result['details']['recent_commits'] = commits
                logger.info(f"Recent commits: {commits}")
            else:
                check_result['recommendations'].append("Could not get git log")
                self.results['warnings'].append("Git log check failed")
        
        self.results['checks']['git_repository'] = check_result
        return check_result
    
    def validate_application_functionality(self) -> Dict:
        """Validate application functionality after recovery"""
        logger.info("Validating application functionality after recovery...")
        
        check_result = {
            'name': 'Application Functionality',
            'status': 'pass',
            'details': {},
            'recommendations': []
        }
        
        # Test basic Python functionality
        try:
            success, stdout, stderr = self.run_command(['python', '-c', 'print("Hello, World!")'])
            if success:
                check_result['details']['python_basic_test'] = True
                logger.info("Basic Python functionality test passed")
            else:
                check_result['status'] = 'fail'
                check_result['recommendations'].append("Basic Python functionality test failed")
                self.results['critical_issues'].append("Python functionality test failed")
        except Exception as e:
            check_result['status'] = 'fail'
            check_result['recommendations'].append(f"Python functionality test error: {e}")
            self.results['critical_issues'].append(f"Python functionality test error: {e}")
        
        # Test basic Node.js functionality
        try:
            success, stdout, stderr = self.run_command(['node', '-e', 'console.log("Hello, World!");'])
            if success:
                check_result['details']['nodejs_basic_test'] = True
                logger.info("Basic Node.js functionality test passed")
            else:
                check_result['status'] = 'fail'
                check_result['recommendations'].append("Basic Node.js functionality test failed")
                self.results['warnings'].append("Node.js functionality test failed")
        except Exception as e:
            check_result['recommendations'].append(f"Node.js functionality test error: {e}")
            self.results['warnings'].append(f"Node.js functionality test error: {e}")
        
        # Test if essential scripts are executable
        scripts_dir = self.workspace_root / 'scripts'
        if scripts_dir.exists():
            executable_scripts = []
            for script_file in scripts_dir.glob('*.py'):
                if script_file.is_file():
                    try:
                        success, stdout, stderr = self.run_command(['python', str(script_file)])
                        if success:
                            executable_scripts.append(str(script_file))
                            logger.info(f"Script {script_file} is executable")
                        else:
                            check_result['recommendations'].append(f"Script {script_file} failed to execute")
                            self.results['warnings'].append(f"Script execution failed: {script_file}")
                    except Exception as e:
                        check_result['recommendations'].append(f"Script {script_file} execution error: {e}")
                        self.results['warnings'].append(f"Script execution error: {script_file}")
            
            check_result['details']['executable_scripts'] = executable_scripts
        
        self.results['checks']['application_functionality'] = check_result
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
    
    def run_all_validations(self) -> Dict:
        """Run all post-recovery validations"""
        logger.info("Starting post-recovery validation...")
        
        # Record start time
        start_time = time.time()
        self.results['recovery_summary']['start_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Run all validations
        self.validate_python_environment()
        self.validate_nodejs_environment()
        self.validate_vscode_configuration()
        self.validate_project_structure()
        self.validate_git_repository()
        self.validate_application_functionality()
        
        # Record end time
        end_time = time.time()
        self.results['recovery_summary']['end_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
        self.results['recovery_summary']['duration'] = round(end_time - start_time, 2)
        
        # Determine overall status
        failed_checks = [check for check in self.results['checks'].values() if check['status'] == 'fail']
        critical_issues = len(self.results['critical_issues'])
        
        if critical_issues > 0:
            self.results['overall_status'] = 'fail'
        elif failed_checks:
            self.results['overall_status'] = 'warning'
        else:
            self.results['overall_status'] = 'pass'
        
        # Generate summary
        logger.info(f"Post-recovery validation completed. Overall status: {self.results['overall_status']}")
        logger.info(f"Failed checks: {len(failed_checks)}")
        logger.info(f"Critical issues: {critical_issues}")
        logger.info(f"Warnings: {len(self.results['warnings'])}")
        logger.info(f"Validation duration: {self.results['recovery_summary']['duration']} seconds")
        
        return self.results
    
    def generate_report(self, output_file: str | None = None) -> str:
        """Generate a detailed post-recovery validation report"""
        if not output_file:
            output_file = f"post-recovery-validation-report-{self.workspace_root.name}.json"
        
        # Add summary
        self.results['summary'] = {
            'total_checks': len(self.results['checks']),
            'failed_checks': len([check for check in self.results['checks'].values() if check['status'] == 'fail']),
            'passed_checks': len([check for check in self.results['checks'].values() if check['status'] == 'pass']),
            'critical_issues': len(self.results['critical_issues']),
            'warnings': len(self.results['warnings']),
            'recommendations': len(self.results['recommendations']),
            'workspace_path': str(self.workspace_root),
            'validation_duration': self.results['recovery_summary']['duration']
        }
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Post-recovery validation report saved to: {output_file}")
        return output_file
    
    def is_recovery_successful(self) -> bool:
        """Determine if recovery was successful based on validation results"""
        if self.results['overall_status'] == 'fail':
            logger.error("Post-recovery validation failed. Recovery was not successful.")
            return False
        elif self.results['overall_status'] == 'warning':
            logger.warning("Post-recovery validation has warnings. Recovery may have issues.")
            return True
        else:
            logger.info("Post-recovery validation passed. Recovery was successful.")
            return True

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run post-recovery validation for IDE environment')
    parser.add_argument('--workspace', '-w', help='Workspace root directory', default='.')
    parser.add_argument('--output', '-o', help='Output report file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create validator and run validations
    validator = PostRecoveryValidator(args.workspace)
    results = validator.run_all_validations()
    
    # Generate report
    report_file = validator.generate_report(args.output)
    
    # Print summary
    print(f"\n{'='*60}")
    print("POST-RECOVERY VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"Workspace: {validator.workspace_root}")
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Total Checks: {len(results['checks'])}")
    print(f"Failed Checks: {len([check for check in results['checks'].values() if check['status'] == 'fail'])}")
    print(f"Critical Issues: {len(results['critical_issues'])}")
    print(f"Warnings: {len(results['warnings'])}")
    print(f"Recommendations: {len(results['recommendations'])}")
    print(f"Validation Duration: {results['recovery_summary']['duration']} seconds")
    print(f"Report: {report_file}")
    print(f"{'='*60}")
    
    # Determine if recovery was successful
    if validator.is_recovery_successful():
        print("\n✅ Post-recovery validation passed. Recovery was successful.")
        sys.exit(0)
    else:
        print("\n❌ Post-recovery validation failed. Recovery was not successful.")
        sys.exit(1)

if __name__ == '__main__':
    main()