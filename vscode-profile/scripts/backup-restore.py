#!/usr/bin/env python3
"""
Backup and Restore Automation Script
Automates backup and restore operations for IDE recovery
"""

import os
import sys
import json
import subprocess
import platform
import shutil
import time
import tarfile
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup-restore.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BackupRestoreManager:
    """Backup and restore automation for IDE recovery"""
    
    def __init__(self, workspace_root: str | None = None, backup_dir: str | None = None):
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.backup_dir = Path(backup_dir) if backup_dir else self.workspace_root / 'backups'
        self.results = {
            'operation': 'unknown',
            'overall_status': 'unknown',
            'details': {},
            'warnings': [],
            'errors': [],
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def run_command(self, command: List[str], cwd: Path | None = None) -> Tuple[bool, str, str]:
        """Execute a command and return success, stdout, stderr"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=cwd or self.workspace_root,
                timeout=300
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Could not calculate hash for {file_path}: {e}")
            return ""
    
    def create_backup(self, backup_name: str | None = None, include_venv: bool = True,
                     include_node_modules: bool = True, include_git: bool = True) -> Dict:
        """Create a backup of the workspace"""
        logger.info("Creating backup...")
        
        self.results['operation'] = 'create_backup'
        
        if not backup_name:
            backup_name = f"backup-{time.strftime('%Y%m%d-%H%M%S')}"
        
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)
        
        operation_result = {
            'operation': 'create_backup',
            'status': 'success',
            'backup_name': backup_name,
            'backup_path': str(backup_path),
            'backup_size': 0,
            'files_backed_up': [],
            'excluded_files': [],
            'warnings': []
        }
        
        # Create backup manifest
        manifest = {
            'backup_name': backup_name,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'workspace_path': str(self.workspace_root),
            'platform': {
                'system': platform.system(),
                'version': platform.version(),
                'architecture': platform.machine()
            },
            'files': {},
            'exclusions': [],
            'settings': {
                'include_venv': include_venv,
                'include_node_modules': include_node_modules,
                'include_git': include_git
            }
        }
        
        # Define files to backup
        files_to_backup = []
        files_to_exclude = []
        
        # Essential files
        essential_files = [
            'README.md',
            'requirements.txt',
            'setup.py',
            'pyproject.toml',
            'package.json',
            '.gitignore',
            'restore-guide.md',
            'vscode-profile/settings.json',
            'vscode-profile/keybindings.json',
            'vscode-profile/extensions.txt',
            'vscode-profile/profile.code-profile'
        ]
        
        # Essential directories
        essential_dirs = [
            'src',
            'tests',
            'docs',
            'scripts',
            'vscode-profile'
        ]
        
        # Add essential files
        for file in essential_files:
            file_path = self.workspace_root / file
            if file_path.exists():
                files_to_backup.append(file_path)
                logger.info(f"Essential file: {file}")
            else:
                files_to_exclude.append(file)
                operation_result['excluded_files'].append(file)
                operation_result['warnings'].append(f"Essential file not found: {file}")
        
        # Add essential directories
        for dir_name in essential_dirs:
            dir_path = self.workspace_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                files_to_backup.append(dir_path)
                logger.info(f"Essential directory: {dir_name}")
            else:
                files_to_exclude.append(dir_name)
                operation_result['excluded_files'].append(dir_name)
                operation_result['warnings'].append(f"Essential directory not found: {dir_name}")
        
        # Optional files based on settings
        if include_venv:
            venv_path = self.workspace_root / '.venv'
            if venv_path.exists():
                files_to_backup.append(venv_path)
                logger.info("Including virtual environment")
            else:
                files_to_exclude.append('.venv')
                operation_result['excluded_files'].append('.venv')
                operation_result['warnings'].append("Virtual environment not found")
        
        if include_node_modules:
            node_modules_path = self.workspace_root / 'node_modules'
            if node_modules_path.exists():
                files_to_backup.append(node_modules_path)
                logger.info("Including node_modules")
            else:
                files_to_exclude.append('node_modules')
                operation_result['excluded_files'].append('node_modules')
                operation_result['warnings'].append("node_modules not found")
        
        if include_git:
            git_path = self.workspace_root / '.git'
            if git_path.exists():
                files_to_backup.append(git_path)
                logger.info("Including git repository")
            else:
                files_to_exclude.append('.git')
                operation_result['excluded_files'].append('.git')
                operation_result['warnings'].append("Git repository not found")
        
        # Create backup archive
        try:
            # Create tar.gz archive
            archive_path = backup_path / f"{backup_name}.tar.gz"
            with tarfile.open(archive_path, 'w:gz') as tar:
                for file_path in files_to_backup:
                    if file_path.is_file():
                        tar.add(file_path, arcname=file_path.name)
                        manifest['files'][str(file_path)] = {
                            'type': 'file',
                            'size': file_path.stat().st_size,
                            'hash': self.calculate_file_hash(file_path)
                        }
                        operation_result['files_backed_up'].append(str(file_path))
                    elif file_path.is_dir():
                        tar.add(file_path, arcname=file_path.name)
                        manifest['files'][str(file_path)] = {
                            'type': 'directory',
                            'size': sum(f.stat().st_size for f in file_path.rglob('*') if f.is_file()),
                            'hash': 'directory'
                        }
                        operation_result['files_backed_up'].append(str(file_path))
            
            # Calculate backup size
            backup_size = archive_path.stat().st_size
            operation_result['backup_size'] = backup_size
            manifest['backup_size'] = backup_size
            
            # Save manifest
            manifest_path = backup_path / 'backup-manifest.json'
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Backup created successfully: {archive_path}")
            logger.info(f"Backup size: {backup_size / (1024*1024):.2f} MB")
            logger.info(f"Files backed up: {len(operation_result['files_backed_up'])}")
            
        except Exception as e:
            operation_result['status'] = 'failed'
            operation_result['error'] = str(e)
            self.results['errors'].append(f"Backup creation failed: {e}")
            logger.error(f"Backup creation failed: {e}")
        
        self.results['details'] = operation_result
        return operation_result
    
    def list_backups(self) -> Dict:
        """List available backups"""
        logger.info("Listing available backups...")
        
        operation_result = {
            'operation': 'list_backups',
            'status': 'success',
            'backups': [],
            'total_backups': 0
        }
        
        try:
            backup_files = list(self.backup_dir.glob('*.tar.gz'))
            
            for backup_file in backup_files:
                backup_info = {
                    'name': backup_file.stem,
                    'path': str(backup_file),
                    'size': backup_file.stat().st_size,
                    'created': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(backup_file.stat().st_ctime)),
                    'modified': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(backup_file.stat().st_mtime))
                }
                
                # Try to read manifest if available
                manifest_path = backup_file.parent / f"{backup_file.stem}-manifest.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)
                            backup_info['manifest'] = manifest
                    except Exception as e:
                        logger.warning(f"Could not read manifest for {backup_file}: {e}")
                
                operation_result['backups'].append(backup_info)
            
            operation_result['total_backups'] = len(operation_result['backups'])
            operation_result['backups'].sort(key=lambda x: x['created'], reverse=True)
            
            logger.info(f"Found {operation_result['total_backups']} backups")
            
        except Exception as e:
            operation_result['status'] = 'failed'
            operation_result['error'] = str(e)
            self.results['errors'].append(f"Backup listing failed: {e}")
            logger.error(f"Backup listing failed: {e}")
        
        self.results['details'] = operation_result
        return operation_result
    
    def restore_backup(self, backup_name: str, overwrite: bool = False, 
                      validate: bool = True) -> Dict:
        """Restore a backup"""
        logger.info(f"Restoring backup: {backup_name}")
        
        self.results['operation'] = 'restore_backup'
        
        operation_result = {
            'operation': 'restore_backup',
            'status': 'success',
            'backup_name': backup_name,
            'files_restored': [],
            'warnings': []
        }
        
        # Find backup file
        backup_file = self.backup_dir / f"{backup_name}.tar.gz"
        if not backup_file.exists():
            operation_result['status'] = 'failed'
            operation_result['error'] = f"Backup file not found: {backup_file}"
            self.results['errors'].append(f"Backup file not found: {backup_file}")
            self.results['details'] = operation_result
            return operation_result
        
        # Read manifest if available
        manifest_path = self.backup_dir / f"{backup_name}-manifest.json"
        manifest = None
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                logger.info(f"Backup manifest loaded: {manifest['backup_name']}")
            except Exception as e:
                logger.warning(f"Could not read backup manifest: {e}")
        
        # Validate backup if requested
        if validate and manifest:
            validation_result = self.validate_backup_integrity(backup_file, manifest)
            if not validation_result['valid']:
                operation_result['status'] = 'failed'
                operation_result['error'] = f"Backup validation failed: {validation_result['errors']}"
                self.results['errors'].append(f"Backup validation failed: {validation_result['errors']}")
                self.results['details'] = operation_result
                return operation_result
        
        # Extract backup
        try:
            with tarfile.open(backup_file, 'r:gz') as tar:
                # Extract files
                for member in tar.getmembers():
                    # Skip directories (they'll be created automatically)
                    if member.isdir():
                        continue
                    
                    # Extract file
                    file_path = self.workspace_root / member.name
                    
                    # Check if file exists and handle overwrite
                    if file_path.exists() and not overwrite:
                        operation_result['warnings'].append(f"File exists and overwrite disabled: {file_path}")
                        continue
                    
                    # Create parent directories if needed
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Extract file
                    extracted_file = tar.extractfile(member)
                    if extracted_file:
                        with extracted_file as f:
                            with open(file_path, 'wb') as out_file:
                                out_file.write(f.read())
                    
                    operation_result['files_restored'].append(str(file_path))
                    logger.info(f"Restored: {file_path}")
                
                # Extract directories
                for member in tar.getmembers():
                    if member.isdir():
                        dir_path = self.workspace_root / member.name
                        dir_path.mkdir(parents=True, exist_ok=True)
                        logger.info(f"Created directory: {dir_path}")
            
            logger.info(f"Backup restored successfully: {backup_name}")
            logger.info(f"Files restored: {len(operation_result['files_restored'])}")
            
        except Exception as e:
            operation_result['status'] = 'failed'
            operation_result['error'] = str(e)
            self.results['errors'].append(f"Backup restoration failed: {e}")
            logger.error(f"Backup restoration failed: {e}")
        
        self.results['details'] = operation_result
        return operation_result
    
    def validate_backup_integrity(self, backup_file: Path, manifest: Dict) -> Dict:
        """Validate backup integrity"""
        logger.info("Validating backup integrity...")
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'validated_files': 0,
            'failed_files': 0
        }
        
        try:
            with tarfile.open(backup_file, 'r:gz') as tar:
                for file_path, file_info in manifest.get('files', {}).items():
                    if file_info['type'] == 'file':
                        # Extract file temporarily
                        member_name = Path(file_path).name
                        member = None
                        
                        # Find member in archive
                        for m in tar.getmembers():
                            if m.name == member_name or m.path.endswith(member_name):
                                member = m
                                break
                        
                        if member:
                            extracted_file = tar.extractfile(member)
                            if extracted_file:
                                with extracted_file as f:
                                    extracted_data = f.read()
                            
                            # Calculate hash
                            sha256_hash = hashlib.sha256()
                            sha256_hash.update(extracted_data)
                            calculated_hash = sha256_hash.hexdigest()
                            
                            # Compare with manifest
                            if calculated_hash != file_info['hash']:
                                validation_result['valid'] = False
                                validation_result['errors'].append(
                                    f"Hash mismatch for {file_path}: expected {file_info['hash']}, got {calculated_hash}"
                                )
                                validation_result['failed_files'] += 1
                            else:
                                validation_result['validated_files'] += 1
                        else:
                            validation_result['valid'] = False
                            validation_result['errors'].append(f"File not found in archive: {file_path}")
                            validation_result['failed_files'] += 1
                
                logger.info(f"Backup integrity validation: {validation_result['validated_files']} files validated, {validation_result['failed_files']} files failed")
                
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Validation error: {e}")
            logger.error(f"Backup integrity validation failed: {e}")
        
        return validation_result
    
    def delete_backup(self, backup_name: str) -> Dict:
        """Delete a backup"""
        logger.info(f"Deleting backup: {backup_name}")
        
        operation_result = {
            'operation': 'delete_backup',
            'status': 'success',
            'backup_name': backup_name
        }
        
        try:
            backup_file = self.backup_dir / f"{backup_name}.tar.gz"
            if backup_file.exists():
                backup_file.unlink()
                logger.info(f"Deleted backup file: {backup_file}")
            else:
                operation_result['status'] = 'failed'
                operation_result['error'] = f"Backup file not found: {backup_file}"
                self.results['errors'].append(f"Backup file not found: {backup_file}")
                self.results['details'] = operation_result
                return operation_result
            
            # Delete manifest if it exists
            manifest_path = self.backup_dir / f"{backup_name}-manifest.json"
            if manifest_path.exists():
                manifest_path.unlink()
                logger.info(f"Deleted manifest file: {manifest_path}")
            
            logger.info(f"Backup deleted successfully: {backup_name}")
            
        except Exception as e:
            operation_result['status'] = 'failed'
            operation_result['error'] = str(e)
            self.results['errors'].append(f"Backup deletion failed: {e}")
            logger.error(f"Backup deletion failed: {e}")
        
        self.results['details'] = operation_result
        return operation_result
    
    def generate_report(self, output_file: str | None = None) -> str:
        """Generate a detailed backup/restore report"""
        if not output_file:
            output_file = f"backup-restore-report-{self.workspace_root.name}.json"
        
        # Add summary
        self.results['summary'] = {
            'operation': self.results['operation'],
            'overall_status': self.results['overall_status'],
            'workspace_path': str(self.workspace_root),
            'backup_directory': str(self.backup_dir),
            'warnings': len(self.results['warnings']),
            'errors': len(self.results['errors']),
            'timestamp': self.results['timestamp']
        }
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Backup/restore report saved to: {output_file}")
        return output_file

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Backup and restore IDE workspace')
    parser.add_argument('--workspace', '-w', help='Workspace root directory', default='.')
    parser.add_argument('--backup-dir', '-b', help='Backup directory', default=None)
    parser.add_argument('--operation', '-o', choices=['backup', 'restore', 'list', 'delete'], 
                       required=True, help='Operation to perform')
    parser.add_argument('--backup-name', '-n', help='Backup name (for restore/delete operations)')
    parser.add_argument('--include-venv', action='store_true', help='Include virtual environment in backup')
    parser.add_argument('--include-node-modules', action='store_true', help='Include node_modules in backup')
    parser.add_argument('--include-git', action='store_true', help='Include git repository in backup')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing files during restore')
    parser.add_argument('--validate', action='store_true', help='Validate backup integrity during restore')
    parser.add_argument('--output', '-f', help='Output report file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create manager
    manager = BackupRestoreManager(args.workspace, args.backup_dir)
    
    # Perform operation
    if args.operation == 'backup':
        result = manager.create_backup(
            backup_name=args.backup_name,
            include_venv=args.include_venv,
            include_node_modules=args.include_node_modules,
            include_git=args.include_git
        )
        manager.results['overall_status'] = result['status']
    
    elif args.operation == 'restore':
        if not args.backup_name:
            print("Error: --backup-name is required for restore operation")
            sys.exit(1)
        result = manager.restore_backup(
            backup_name=args.backup_name,
            overwrite=args.overwrite,
            validate=args.validate
        )
        manager.results['overall_status'] = result['status']
    
    elif args.operation == 'list':
        result = manager.list_backups()
        manager.results['overall_status'] = result['status']
    
    elif args.operation == 'delete':
        if not args.backup_name:
            print("Error: --backup-name is required for delete operation")
            sys.exit(1)
        result = manager.delete_backup(backup_name=args.backup_name)
        manager.results['overall_status'] = result['status']
    
    # Generate report
    report_file = manager.generate_report(args.output)
    
    # Print summary
    print(f"\n{'='*60}")
    print("BACKUP/RESTORE SUMMARY")
    print(f"{'='*60}")
    print(f"Workspace: {manager.workspace_root}")
    print(f"Operation: {args.operation.upper()}")
    print(f"Overall Status: {manager.results['overall_status'].upper()}")
    print(f"Report: {report_file}")
    print(f"{'='*60}")
    
    # Print operation-specific details
    if args.operation == 'backup' and 'details' in manager.results:
        details = manager.results['details']
        print(f"Backup Name: {details.get('backup_name', 'N/A')}")
        print(f"Backup Size: {details.get('backup_size', 0) / (1024*1024):.2f} MB")
        print(f"Files Backed Up: {len(details.get('files_backed_up', []))}")
        print(f"Excluded Files: {len(details.get('excluded_files', []))}")
        print(f"Warnings: {len(details.get('warnings', []))}")
    
    elif args.operation == 'restore' and 'details' in manager.results:
        details = manager.results['details']
        print(f"Backup Name: {details.get('backup_name', 'N/A')}")
        print(f"Files Restored: {len(details.get('files_restored', []))}")
        print(f"Warnings: {len(details.get('warnings', []))}")
    
    elif args.operation == 'list' and 'details' in manager.results:
        details = manager.results['details']
        print(f"Total Backups: {details.get('total_backups', 0)}")
        for backup in details.get('backups', []):
            print(f"  - {backup['name']} ({backup['size'] / (1024*1024):.2f} MB, {backup['created']})")
    
    elif args.operation == 'delete' and 'details' in manager.results:
        details = manager.results['details']
        print(f"Backup Name: {details.get('backup_name', 'N/A')}")
    
    print(f"{'='*60}")
    
    # Exit with appropriate code
    if manager.results['overall_status'] == 'failed':
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()