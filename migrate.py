#!/usr/bin/env python3
"""
Automated migration script from fragmented to unified dependency management.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MigrationManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backup_dir = None
        
    def create_backup(self):
        """Create a backup of the current project state."""
        timestamp = subprocess.check_output(
            ["date", "+%Y%m%d-%H%M%S"], 
            text=True
        ).strip()
        self.backup_dir = self.project_root.parent / f"paddle-plugin-backup-{timestamp}"
        
        logger.info(f"Creating backup at {self.backup_dir}")
        
        # Create backup excluding .git and node_modules
        exclude_patterns = [
            ".git",
            "node_modules",
            ".venv",
            "venv",
            "__pycache__",
            "*.pyc",
            ".pytest_cache"
        ]
        
        # Use rsync for efficient backup
        try:
            cmd = [
                "rsync", "-av",
                "--exclude=.git",
                "--exclude=node_modules",
                "--exclude=.venv",
                "--exclude=venv",
                "--exclude=__pycache__",
                "--exclude=*.pyc",
                "--exclude=.pytest_cache",
                str(self.project_root) + "/",
                str(self.backup_dir) + "/"
            ]
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            # Fallback to cp if rsync not available
            shutil.copytree(
                self.project_root,
                self.backup_dir,
                ignore=shutil.ignore_patterns(*exclude_patterns)
            )
        
        logger.info(f"Backup created at {self.backup_dir}")
    
    def remove_old_configs(self):
        """Remove old configuration files."""
        old_files = [
            "src/orchestration/requirements.txt",
            "mcp_servers/mcp-memory-service/requirements.txt",
            "mcp_servers/package.json",
            "brave-search-integration/package.json",
            "simba/requirements.txt",
            "simba/pyproject.toml",
            "simba/poetry.lock"
        ]
        
        for file_path in old_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                logger.info(f"Removing {file_path}")
                full_path.unlink()
    
    def cleanup_old_environments(self):
        """Remove old virtual environments and node_modules."""
        old_dirs = [
            ".venv",
            "venv",
            "simba/.venv",
            "mcp_servers/.venv",
            "node_modules",
            "mcp_servers/node_modules",
            "brave-search-integration/node_modules"
        ]
        
        for dir_path in old_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists():
                logger.info(f"Removing {dir_path}")
                shutil.rmtree(full_path)
    
    def migrate_environment_variables(self):
        """Migrate old .env files to new unified .env."""
        old_env_files = [
            "src/orchestration/.env",
            "mcp_servers/.env",
            "brave-search-integration/.env"
        ]
        
        new_env_file = self.project_root / ".env"
        
        # Collect all environment variables
        all_env_vars = {}
        
        for old_env_file in old_env_files:
            old_path = self.project_root / old_env_file
            if old_path.exists():
                logger.info(f"Migrating {old_env_file}")
                with open(old_path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            all_env_vars[key] = value
        
        # Write to new .env file
        if all_env_vars:
            from utils.encoding_utils import safe_write_text
            safe_write_text(new_env_file, '', encoding='utf-8')
            with open(new_env_file, 'w', encoding='utf-8') as f:
                f.write("# Migrated environment variables\n")
                for key, value in all_env_vars.items():
                    f.write(f"{key}={value}\n")
            logger.info("Environment variables migrated to .env")
    
    def run_migration(self):
        """Run the complete migration process."""
        logger.info("Starting migration to unified dependency management...")
        
        # Create backup
        self.create_backup()
        
        # Remove old configurations
        self.remove_old_configs()
        
        # Clean up old environments
        self.cleanup_old_environments()
        
        # Migrate environment variables
        self.migrate_environment_variables()
        
        # Run the new unified setup
        logger.info("Running unified setup...")
        subprocess.run([sys.executable, "setup.py"], check=True)
        
        logger.info("✅ Migration completed successfully!")
        logger.info(f"Backup available at: {self.backup_dir}")
        logger.info("\nNext steps:")
        logger.info("1. Review the new .env file")
        logger.info("2. Test your workflows with the new commands")
        logger.info("3. Remove the backup directory once you're satisfied")

if __name__ == "__main__":
    migration_manager = MigrationManager()
    migration_manager.run_migration()
