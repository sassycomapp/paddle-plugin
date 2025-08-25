#!/usr/bin/env python3
"""
Dependency Version Pinning Script
Ensures reproducible setups by pinning dependency versions
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
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dependency-pinning.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DependencyPinner:
    """Dependency version pinning for reproducible setups"""
    
    def __init__(self, workspace_root: str | None = None):
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.results = {
            'overall_status': 'unknown',
            'operations': [],
            'pinned_dependencies': {},
            'failed_operations': [],
            'warnings': [],
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    def run_command(self, command: List[str], cwd: Path | None = None) -> Tuple[bool, str, str]:
        """Execute a command and return success, stdout, stderr"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=cwd or self.workspace_root,
                timeout=60
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def pin_python_dependencies(self) -> Dict:
        """Pin Python dependencies to specific versions"""
        logger.info("Pinning Python dependencies...")
        
        operation_result = {
            'operation': 'pin_python_dependencies',
            'status': 'success',
            'details': {},
            'warnings': []
        }
        
        # Check if requirements.txt exists
        requirements_path = self.workspace_root / 'requirements.txt'
        if not requirements_path.exists():
            operation_result['status'] = 'skipped'
            operation_result['details']['reason'] = 'requirements.txt not found'
            self.results['warnings'].append('requirements.txt not found, skipping Python dependency pinning')
            self.results['operations'].append(operation_result)
            return operation_result
        
        # Read current requirements
        try:
            with open(requirements_path, 'r') as f:
                current_requirements = f.read().strip().split('\n')
            operation_result['details']['original_requirements'] = current_requirements
            logger.info(f"Found {len(current_requirements)} requirements in requirements.txt")
        except Exception as e:
            operation_result['status'] = 'failed'
            operation_result['details']['error'] = str(e)
            self.results['failed_operations'].append(operation_result)
            self.results['operations'].append(operation_result)
            return operation_result
        
        # Generate pinned requirements
        pinned_requirements = []
        for requirement in current_requirements:
            requirement = requirement.strip()
            if not requirement or requirement.startswith('#'):
                pinned_requirements.append(requirement)
                continue
            
            # Skip already pinned requirements
            if '==' in requirement or '>=' in requirement or '<=' in requirement or '>' in requirement or '<' in requirement:
                pinned_requirements.append(requirement)
                continue
            
            # Pin the requirement
            package_name = requirement.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].strip()
            logger.info(f"Pinning {package_name}...")
            
            # Get latest version
            success, stdout, stderr = self.run_command(['pip', 'install', package_name])
            if success:
                # Get installed version
                success, stdout, stderr = self.run_command(['pip', 'show', package_name])
                if success:
                    version_match = re.search(r'Version:\s+(.+)', stdout)
                    if version_match:
                        version = version_match.group(1)
                        pinned_requirement = f"{package_name}=={version}"
                        pinned_requirements.append(pinned_requirement)
                        logger.info(f"Pinned {package_name} to version {version}")
                    else:
                        pinned_requirements.append(requirement)
                        operation_result['warnings'].append(f"Could not determine version for {package_name}")
                else:
                    pinned_requirements.append(requirement)
                    operation_result['warnings'].append(f"Could not get version for {package_name}: {stderr}")
            else:
                pinned_requirements.append(requirement)
                operation_result['warnings'].append(f"Could not install {package_name}: {stderr}")
        
        # Write pinned requirements
        try:
            with open(requirements_path, 'w') as f:
                f.write('\n'.join(pinned_requirements) + '\n')
            operation_result['details']['pinned_requirements'] = pinned_requirements
            operation_result['details']['pinned_count'] = len([r for r in pinned_requirements if '==' in r and not r.startswith('#')])
            logger.info(f"Pinned {operation_result['details']['pinned_count']} Python dependencies")
        except Exception as e:
            operation_result['status'] = 'failed'
            operation_result['details']['error'] = str(e)
            self.results['failed_operations'].append(operation_result)
        
        self.results['operations'].append(operation_result)
        return operation_result
    
    def pin_nodejs_dependencies(self) -> Dict:
        """Pin Node.js dependencies to specific versions"""
        logger.info("Pinning Node.js dependencies...")
        
        operation_result = {
            'operation': 'pin_nodejs_dependencies',
            'status': 'success',
            'details': {},
            'warnings': []
        }
        
        # Check if package.json exists
        package_json_path = self.workspace_root / 'package.json'
        if not package_json_path.exists():
            operation_result['status'] = 'skipped'
            operation_result['details']['reason'] = 'package.json not found'
            self.results['warnings'].append('package.json not found, skipping Node.js dependency pinning')
            self.results['operations'].append(operation_result)
            return operation_result
        
        # Read package.json
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            operation_result['details']['original_package_json'] = package_data
            logger.info("Found package.json")
        except Exception as e:
            operation_result['status'] = 'failed'
            operation_result['details']['error'] = str(e)
            self.results['failed_operations'].append(operation_result)
            self.results['operations'].append(operation_result)
            return operation_result
        
        # Pin dependencies
        pinned_package_data = package_data.copy()
        
        # Pin regular dependencies
        if 'dependencies' in package_data:
            pinned_dependencies = {}
            for package, version_spec in package_data['dependencies'].items():
                logger.info(f"Pinning {package}...")
                
                # Get latest version
                success, stdout, stderr = self.run_command(['npm', 'view', package, 'version'])
                if success:
                    latest_version = stdout.strip()
                    pinned_dependencies[package] = latest_version
                    logger.info(f"Pinned {package} to version {latest_version}")
                else:
                    pinned_dependencies[package] = version_spec
                    operation_result['warnings'].append(f"Could not get version for {package}: {stderr}")
            
            pinned_package_data['dependencies'] = pinned_dependencies
        
        # Pin dev dependencies
        if 'devDependencies' in package_data:
            pinned_dev_dependencies = {}
            for package, version_spec in package_data['devDependencies'].items():
                logger.info(f"Pinning dev dependency {package}...")
                
                # Get latest version
                success, stdout, stderr = self.run_command(['npm', 'view', package, 'version'])
                if success:
                    latest_version = stdout.strip()
                    pinned_dev_dependencies[package] = latest_version
                    logger.info(f"Pinned {package} to version {latest_version}")
                else:
                    pinned_dev_dependencies[package] = version_spec
                    operation_result['warnings'].append(f"Could not get version for {package}: {stderr}")
            
            pinned_package_data['devDependencies'] = pinned_dev_dependencies
        
        # Write updated package.json
        try:
            with open(package_json_path, 'w') as f:
                json.dump(pinned_package_data, f, indent=2)
            operation_result['details']['pinned_package_json'] = pinned_package_data
            operation_result['details']['pinned_dependencies_count'] = len(pinned_package_data.get('dependencies', {}))
            operation_result['details']['pinned_dev_dependencies_count'] = len(pinned_package_data.get('devDependencies', {}))
            logger.info(f"Pinned {operation_result['details']['pinned_dependencies_count']} dependencies and {operation_result['details']['pinned_dev_dependencies_count']} dev dependencies")
        except Exception as e:
            operation_result['status'] = 'failed'
            operation_result['details']['error'] = str(e)
            self.results['failed_operations'].append(operation_result)
        
        self.results['operations'].append(operation_result)
        return operation_result
    
    def create_lock_files(self) -> Dict:
        """Create lock files for reproducible builds"""
        logger.info("Creating lock files...")
        
        operation_result = {
            'operation': 'create_lock_files',
            'status': 'success',
            'details': {},
            'warnings': []
        }
        
        # Create Python lock file
        try:
            success, stdout, stderr = self.run_command(['pip', 'freeze', '>', 'requirements.lock'])
            if success:
                operation_result['details']['python_lock_file'] = 'requirements.lock'
                logger.info("Created Python lock file: requirements.lock")
            else:
                operation_result['warnings'].append(f"Could not create Python lock file: {stderr}")
        except Exception as e:
            operation_result['warnings'].append(f"Could not create Python lock file: {e}")
        
        # Create Node.js lock file
        try:
            success, stdout, stderr = self.run_command(['npm', 'install', '--package-lock-only'])
            if success:
                operation_result['details']['nodejs_lock_file'] = 'package-lock.json'
                logger.info("Created Node.js lock file: package-lock.json")
            else:
                operation_result['warnings'].append(f"Could not create Node.js lock file: {stderr}")
        except Exception as e:
            operation_result['warnings'].append(f"Could not create Node.js lock file: {e}")
        
        # Create Python environment lock file
        try:
            venv_path = self.workspace_root / '.venv'
            if venv_path.exists():
                success, stdout, stderr = self.run_command(['pip', 'freeze'], cwd=venv_path)
                if success:
                    lock_file_path = self.workspace_root / 'environment.lock'
                    with open(lock_file_path, 'w') as f:
                        f.write(stdout)
                    operation_result['details']['environment_lock_file'] = str(lock_file_path)
                    logger.info("Created environment lock file: environment.lock")
                else:
                    operation_result['warnings'].append(f"Could not create environment lock file: {stderr}")
        except Exception as e:
            operation_result['warnings'].append(f"Could not create environment lock file: {e}")
        
        self.results['operations'].append(operation_result)
        return operation_result
    
    def create_dependency_manifest(self) -> Dict:
        """Create a comprehensive dependency manifest"""
        logger.info("Creating dependency manifest...")
        
        operation_result = {
            'operation': 'create_dependency_manifest',
            'status': 'success',
            'details': {},
            'warnings': []
        }
        
        manifest = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'platform': {
                'system': platform.system(),
                'version': platform.version(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'python_implementation': platform.python_implementation()
            },
            'dependencies': {
                'python': {},
                'nodejs': {},
                'system': {}
            }
        }
        
        # Get Python dependencies
        try:
            success, stdout, stderr = self.run_command(['pip', 'list', '--format=json'])
            if success:
                python_deps = json.loads(stdout)
                manifest['dependencies']['python'] = {
                    dep['name']: dep['version'] for dep in python_deps
                }
                logger.info(f"Found {len(python_deps)} Python dependencies")
            else:
                operation_result['warnings'].append(f"Could not get Python dependencies: {stderr}")
        except Exception as e:
            operation_result['warnings'].append(f"Could not get Python dependencies: {e}")
        
        # Get Node.js dependencies
        try:
            success, stdout, stderr = self.run_command(['npm', 'list', '--json', '--depth=0'])
            if success:
                nodejs_deps = json.loads(stdout)
                if 'dependencies' in nodejs_deps:
                    manifest['dependencies']['nodejs'] = nodejs_deps['dependencies']
                    logger.info(f"Found {len(nodejs_deps['dependencies'])} Node.js dependencies")
            else:
                operation_result['warnings'].append(f"Could not get Node.js dependencies: {stderr}")
        except Exception as e:
            operation_result['warnings'].append(f"Could not get Node.js dependencies: {e}")
        
        # Get system dependencies
        try:
            system_deps = {}
            
            # Get installed packages via package managers
            if platform.system() == 'Linux':
                # Try apt
                success, stdout, stderr = self.run_command(['dpkg', '-l'])
                if success:
                    system_deps['apt'] = stdout.strip().split('\n')
                
                # Try yum
                success, stdout, stderr = self.run_command(['rpm', '-qa'])
                if success:
                    system_deps['yum'] = stdout.strip().split('\n')
            
            elif platform.system() == 'Darwin':
                # Try brew
                success, stdout, stderr = self.run_command(['brew', 'list'])
                if success:
                    system_deps['brew'] = stdout.strip().split('\n')
            
            elif platform.system() == 'Windows':
                # Try winget
                success, stdout, stderr = self.run_command(['winget', 'list'])
                if success:
                    system_deps['winget'] = stdout.strip().split('\n')
            
            manifest['dependencies']['system'] = system_deps
            logger.info(f"Found system dependencies from: {list(system_deps.keys())}")
            
        except Exception as e:
            operation_result['warnings'].append(f"Could not get system dependencies: {e}")
        
        # Save manifest
        manifest_path = self.workspace_root / 'dependency-manifest.json'
        try:
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            operation_result['details']['manifest_file'] = str(manifest_path)
            logger.info(f"Created dependency manifest: {manifest_path}")
        except Exception as e:
            operation_result['status'] = 'failed'
            operation_result['details']['error'] = str(e)
            self.results['failed_operations'].append(operation_result)
        
        self.results['operations'].append(operation_result)
        return operation_result
    
    def pin_all_dependencies(self) -> Dict:
        """Pin all dependencies and create lock files"""
        logger.info("Starting dependency pinning process...")
        
        # Run all pinning operations
        self.pin_python_dependencies()
        self.pin_nodejs_dependencies()
        self.create_lock_files()
        self.create_dependency_manifest()
        
        # Determine overall status
        failed_operations = [op for op in self.results['operations'] if op['status'] == 'failed']
        warnings = len(self.results['warnings'])
        
        if failed_operations:
            self.results['overall_status'] = 'fail'
        elif warnings:
            self.results['overall_status'] = 'warning'
        else:
            self.results['overall_status'] = 'success'
        
        # Generate summary
        logger.info(f"Dependency pinning completed. Overall status: {self.results['overall_status']}")
        logger.info(f"Total operations: {len(self.results['operations'])}")
        logger.info(f"Failed operations: {len(failed_operations)}")
        logger.info(f"Warnings: {warnings}")
        
        return self.results
    
    def generate_report(self, output_file: str | None = None) -> str:
        """Generate a detailed dependency pinning report"""
        if not output_file:
            output_file = f"dependency-pinning-report-{self.workspace_root.name}.json"
        
        # Add summary
        self.results['summary'] = {
            'total_operations': len(self.results['operations']),
            'successful_operations': len([op for op in self.results['operations'] if op['status'] == 'success']),
            'failed_operations': len([op for op in self.results['operations'] if op['status'] == 'failed']),
            'skipped_operations': len([op for op in self.results['operations'] if op['status'] == 'skipped']),
            'warnings': len(self.results['warnings']),
            'workspace_path': str(self.workspace_root)
        }
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Dependency pinning report saved to: {output_file}")
        return output_file
    
    def is_pinning_successful(self) -> bool:
        """Determine if dependency pinning was successful"""
        if self.results['overall_status'] == 'fail':
            logger.error("Dependency pinning failed.")
            return False
        elif self.results['overall_status'] == 'warning':
            logger.warning("Dependency pinning completed with warnings.")
            return True
        else:
            logger.info("Dependency pinning completed successfully.")
            return True

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pin dependencies for reproducible setups')
    parser.add_argument('--workspace', '-w', help='Workspace root directory', default='.')
    parser.add_argument('--output', '-o', help='Output report file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create pinner and run pinning
    pinner = DependencyPinner(args.workspace)
    results = pinner.pin_all_dependencies()
    
    # Generate report
    report_file = pinner.generate_report(args.output)
    
    # Print summary
    print(f"\n{'='*60}")
    print("DEPENDENCY PINNING SUMMARY")
    print(f"{'='*60}")
    print(f"Workspace: {pinner.workspace_root}")
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Total Operations: {len(results['operations'])}")
    print(f"Successful Operations: {len([op for op in results['operations'] if op['status'] == 'success'])}")
    print(f"Failed Operations: {len([op for op in results['operations'] if op['status'] == 'failed'])}")
    print(f"Skipped Operations: {len([op for op in results['operations'] if op['status'] == 'skipped'])}")
    print(f"Warnings: {len(results['warnings'])}")
    print(f"Report: {report_file}")
    print(f"{'='*60}")
    
    # Determine if pinning was successful
    if pinner.is_pinning_successful():
        print("\n✅ Dependency pinning completed successfully.")
        sys.exit(0)
    else:
        print("\n❌ Dependency pinning failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()