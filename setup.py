#!/usr/bin/env python3
"""
Unified setup script for the vsc_ide project.
Consolidates all dependency management into a single setup process.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import shutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SetupManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.is_windows = platform.system() == "Windows"
        self.python_executable = sys.executable
        
    def run_command(self, command, cwd=None, shell=None):
        """Run a command and handle errors."""
        if shell is None:
            shell = self.is_windows
            
        try:
            logger.info(f"Running: {command}")
            result = subprocess.run(
                command,
                shell=shell,
                cwd=cwd or self.project_root,
                check=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                logger.info(result.stdout)
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")
            raise
    
    def check_prerequisites(self):
        """Check if required tools are installed."""
        logger.info("Checking prerequisites...")
        
        # Check Python version - support both 3.7x for Anvil and 3.10+ for advanced features
        python_version = sys.version_info
        if python_version < (3, 7):
            raise RuntimeError(f"Python 3.7+ required, found {python_version.major}.{python_version.minor}")
        logger.info(f"Python {python_version.major}.{python_version.minor} ✓")
        
        # Check Node.js
        try:
            result = self.run_command("node --version")
            node_version = result.stdout.strip()
            logger.info(f"Node.js {node_version} ✓")
        except subprocess.CalledProcessError:
            raise RuntimeError("Node.js not found. Please install Node.js 18+")
        
        # Check npm
        try:
            result = self.run_command("npm --version")
            npm_version = result.stdout.strip()
            logger.info(f"npm {npm_version} ✓")
        except subprocess.CalledProcessError:
            raise RuntimeError("npm not found")
        
        # Check Poetry
        try:
            result = self.run_command("poetry --version")
            poetry_version = result.stdout.strip()
            logger.info(f"{poetry_version} ✓")
        except subprocess.CalledProcessError:
            logger.warning("Poetry not found. Installing...")
            self.install_poetry()
    
    def install_poetry(self):
        """Install Poetry if not found."""
        logger.info("Installing Poetry...")
        if self.is_windows:
            command = "(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -"
        else:
            command = "curl -sSL https://install.python-poetry.org | python3 -"
        
        self.run_command(command)
        
        # Add Poetry to PATH
        if not self.is_windows:
            poetry_path = Path.home() / ".local" / "bin"
            if str(poetry_path) not in os.environ.get("PATH", ""):
                logger.warning(f"Add {poetry_path} to your PATH")
    
    def cleanup_old_environments(self):
        """Remove old virtual environments and node_modules."""
        logger.info("Cleaning up old environments...")
        
        # Remove old Python environments
        old_envs = [".venv", "venv", "simba/.venv", "mcp_servers/.venv"]
        for env in old_envs:
            env_path = self.project_root / env
            if env_path.exists():
                logger.info(f"Removing {env}")
                shutil.rmtree(env_path)
        
        # Remove old node_modules
        old_node_modules = [
            "node_modules",
            "mcp_servers/node_modules",
            "brave-search-integration/node_modules"
        ]
        for nm in old_node_modules:
            nm_path = self.project_root / nm
            if nm_path.exists():
                logger.info(f"Removing {nm}")
                shutil.rmtree(nm_path)
    
    def setup_python_environment(self):
        """Set up Python environment with Poetry."""
        logger.info("Setting up Python environment...")
        
        # Clear Poetry cache to ensure fresh dependency resolution
        self.run_command("poetry cache clear --all . --quiet")
        
        # Install Poetry dependencies without dev and docs extras to avoid conflicts
        self.run_command("poetry install --without dev --without docs")
        
        # Install optional dependency groups
        optional_groups = ["ag2", "simba", "mcp", "database"]
        for group in optional_groups:
            logger.info(f"Installing optional group: {group}")
            try:
                self.run_command(f"poetry install --with {group}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to install group {group}: {e}")
    
    def setup_node_environment(self):
        """Set up Node.js environment."""
        logger.info("Setting up Node.js environment...")
        
        # Install root dependencies
        self.run_command("npm install")
        
        # Install workspace dependencies
        self.run_command("npm install --workspaces")
    
    def create_environment_files(self):
        """Create environment files if they don't exist."""
        logger.info("Creating environment files...")
        
        env_template = """# AG2 Orchestrator Configuration
AG2_API_KEY=your_ag2_api_key_here
AG2_BASE_URL=https://api.ag2.dev/v1
AG2_MODEL=gpt-4

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/paddle_plugin
REDIS_URL=redis://localhost:6379

# MCP Configuration
MCP_MEMORY_SERVER_URL=http://localhost:8000
MCP_RAG_SERVER_URL=http://localhost:8001
MCP_BRAVE_SERVER_URL=http://localhost:8002

# Brave Search Configuration
BRAVE_API_KEY=your_brave_api_key_here

# PGvector Configuration
"Placeholder"_PERSIST_DIRECTORY=./"Placeholder"-data

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/vsc_ide.log

# Development
DEBUG=true
ENVIRONMENT=development
"""
        
        env_file = self.project_root / ".env"
        if not env_file.exists():
            env_file.write_text(env_template)
            logger.info("Created .env file")
    
    def verify_setup(self):
        """Verify that the setup was successful."""
        logger.info("Verifying setup...")
        
        # Check Python imports
        python_test = """
import sys
  # PGvector import check removed as part of migration to pgvector

try:
    import langchain
    print("✓ langchain imported successfully")
except ImportError as e:
    print(f"✗ langchain import failed: {e}")
    sys.exit(1)

print("All Python dependencies verified!")
"""
        
        with open("test_imports.py", "w") as f:
            f.write(python_test)
        
        try:
            self.run_command("poetry run python test_imports.py")
        finally:
            Path("test_imports.py").unlink(missing_ok=True)
        
        # Check Node.js modules
        node_test = """
const fs = require('fs');
const path = require('path');

const checkModule = (moduleName) => {
    try {
        require.resolve(moduleName);
        console.log(`✓ ${moduleName} available`);
        return true;
    } catch (e) {
        console.log(`✗ ${moduleName} missing: ${e.message}`);
        return false;
    }
};

const modules = [
    '@modelcontextprotocol/sdk',
    'axios',
    'dotenv',
    'uuid',
    'fs-extra'
];

let allGood = true;
modules.forEach(mod => {
    if (!checkModule(mod)) allGood = false;
});

if (allGood) {
    console.log('All Node.js dependencies verified!');
    process.exit(0);
} else {
    console.log('Some Node.js dependencies are missing!');
    process.exit(1);
}
"""
        
        with open("test_modules.js", "w") as f:
            f.write(node_test)
        
        try:
            self.run_command("node test_modules.js")
        finally:
            Path("test_modules.js").unlink(missing_ok=True)
    
    def create_setup_complete_marker(self):
        """Create a marker file to indicate successful setup."""
        marker_file = self.project_root / ".setup_complete"
        marker_file.write_text("Setup completed successfully")
        logger.info("Setup complete marker created")
    
    def run(self):
        """Run the complete setup process."""
        try:
            logger.info("Starting unified setup for vsc_ide...")
            
            self.check_prerequisites()
            self.cleanup_old_environments()
            self.setup_python_environment()
            self.setup_node_environment()
            self.create_environment_files()
            self.verify_setup()
            self.create_setup_complete_marker()
            
            logger.info("✅ Setup completed successfully!")
            logger.info("\nNext steps:")
            logger.info("1. Edit .env file with your API keys and configuration")
            logger.info("2. Run 'npm run start:ag2' to start the AG2 orchestrator")
            logger.info("3. Run 'npm run start:memory' to start the memory MCP server")
            logger.info("4. Run 'npm run start:rag' to start the RAG MCP server")
            logger.info("5. Run 'npm run start:brave' to start the Brave search MCP server")
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    setup_manager = SetupManager()
    setup_manager.run()
