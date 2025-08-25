#!/usr/bin/env python3
"""
Complete AG2 Orchestrator Setup Script
This script sets up all required services and dependencies for the AG2 system.
"""

import os
import sys
import subprocess
import time
import json
import signal
import atexit
from pathlib import Path
import platform
from src.vault_client import initialize_vault_secrets, get_database_credentials

class AG2Setup:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.orchestration_dir = self.project_root / "src" / "orchestration"
        self.mcp_servers_dir = self.project_root / "mcp_servers"
        self.processes = []
        
        # Colors for output
        self.RED = '\033[0;31m'
        self.GREEN = '\033[0;32m'
        self.YELLOW = '\033[1;33m'
        self.BLUE = '\033[0;34m'
        self.NC = '\033[0m'  # No Color
        
    def print_status(self, message):
        print(f"{self.GREEN}[INFO]{self.NC} {message}")
        
    def print_warning(self, message):
        print(f"{self.YELLOW}[WARNING]{self.NC} {message}")
        
    def print_error(self, message):
        print(f"{self.RED}[ERROR]{self.NC} {message}")
        
    def print_header(self, message):
        print(f"\n{self.BLUE}=== {message} ==={self.NC}")
        
    def check_command(self, command):
        """Check if a command is available in the system."""
        try:
            subprocess.run([command, "--version"], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
            
    def check_port(self, port, host='localhost'):
        """Check if a port is available."""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex((host, port))
                return result != 0
        except Exception:
            return True
            
    def install_python_dependencies(self):
        """Install Python dependencies."""
        self.print_header("Installing Python Dependencies")
        
        requirements_file = self.orchestration_dir / "requirements.txt"
        if requirements_file.exists():
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                ], check=True)
                self.print_status("Python dependencies installed successfully")
            except subprocess.CalledProcessError:
                self.print_error("Failed to install Python dependencies")
                return False
        else:
            self.print_warning("requirements.txt not found")
        return True
        
    def install_node_dependencies(self):
        """Install Node.js dependencies."""
        self.print_header("Installing Node.js Dependencies")
        
        package_json = self.mcp_servers_dir / "package.json"
        if package_json.exists():
            try:
                subprocess.run([
                    "npm", "install"
                ], cwd=str(self.mcp_servers_dir), check=True)
                self.print_status("Node.js dependencies installed successfully")
            except subprocess.CalledProcessError:
                self.print_error("Failed to install Node.js dependencies")
                return False
        else:
            self.print_warning("package.json not found")
        return True
        
    def check_docker(self):
        """Check if Docker is available."""
        return self.check_command("docker")
        
    def start_PGvector(self):
        """Start PGvector service."""
        self.print_header("Starting PGvector")
        
        try:
            import requests
        except ImportError:
            self.print_error("requests library not available. Please install it with: pip install requests")
            return None
            
        if not self.check_docker():
            self.print_error("Docker is not available. PGvector requires Docker.")
            return None
            
        # Check if PGvector is already running
        try:
            response = requests.get("http://localhost:8000/api/v1/heartbeat", timeout=5)
            if response.status_code == 200:
                self.print_status("PGvector is already running on port 8000")
                return None
        except requests.exceptions.RequestException:
            pass
            
        # Start PGvector in Docker
        try:
            process = subprocess.Popen([
                "docker", "run", "--rm", "-d",
                "--name", "PGvector",
                "-p", "8000:8000",
                "PGvector/"Placeholder":latest"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait a bit for container to start
            time.sleep(5)
            
            # Check if container started successfully
            result = subprocess.run([
                "docker", "ps", "--filter", "name=PGvector", "--format", "table {{.Names}}"
            ], capture_output=True, text=True)
            
            if "PGvector" in result.stdout:
                self.print_status("PGvector started successfully in Docker")
                return process
            else:
                self.print_error("Failed to start PGvector container")
                return None
                
        except Exception as e:
            self.print_error(f"Error starting PGvector: {e}")
            return None
            
    def start_postgresql(self):
        """Start PostgreSQL service."""
        self.print_header("Starting PostgreSQL")
        
        if not self.check_docker():
            self.print_error("Docker is not available. PostgreSQL requires Docker.")
            return None
            
        # Check if PostgreSQL is already running
        try:
            import psycopg2
            # Get database credentials from Vault
            db_creds = get_database_credentials("postgres")
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="postgres",
                user=db_creds["username"],
                password=db_creds["password"]
            )
            conn.close()
            self.print_status("PostgreSQL is already running on port 5432")
            return None
        except ImportError:
            self.print_error("psycopg2 not available. Please install it with: pip install psycopg2-binary")
            return None
        except:
            pass
            
        # Start PostgreSQL in Docker
        try:
            process = subprocess.Popen([
                "docker", "run", "--rm", "-d",
                "--name", "postgres",
                "-p", "5432:5432",
                # Get database credentials from Vault
                db_creds = get_database_credentials("postgres")
                "-e", f"POSTGRES_PASSWORD={db_creds['password']}",
                "-e", "POSTGRES_DB=postgres",
                "postgres:15"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for PostgreSQL to start
            time.sleep(10)
            
            # Check if container started successfully
            result = subprocess.run([
                "docker", "ps", "--filter", "name=postgres", "--format", "table {{.Names}}"
            ], capture_output=True, text=True)
            
            if "postgres" in result.stdout:
                self.print_status("PostgreSQL started successfully in Docker")
                
                # Create required tables
                self.create_postgresql_tables()
                return process
            else:
                self.print_error("Failed to start PostgreSQL container")
                return None
                
        except Exception as e:
            self.print_error(f"Error starting PostgreSQL: {e}")
            return None
            
    def create_postgresql_tables(self):
        """Create required PostgreSQL tables."""
        self.print_header("Creating PostgreSQL Tables")
        
        try:
            import psycopg2
            
            # Get database credentials from Vault
            db_creds = get_database_credentials("postgres")
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="postgres",
                user=db_creds["username"],
                password=db_creds["password"]
            )
            
            cursor = conn.cursor()
            
            # Create tables for agent memory
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS episodic_memory (
                    id SERIAL PRIMARY KEY,
                    agent_id VARCHAR(255),
                    session_id VARCHAR(255),
                    context JSONB,
                    memory_type VARCHAR(50),
                    relevance_score FLOAT,
                    tags TEXT[],
                    timestamp TIMESTAMP DEFAULT NOW()
                );
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS semantic_memory (
                    id SERIAL PRIMARY KEY,
                    entity VARCHAR(255),
                    data JSONB,
                    category VARCHAR(100),
                    agent_id VARCHAR(255),
                    tags TEXT[],
                    access_count INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT NOW(),
                    UNIQUE(entity, agent_id)
                );
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS working_memory (
                    id SERIAL PRIMARY KEY,
                    agent_id VARCHAR(255),
                    session_id VARCHAR(255),
                    key VARCHAR(255),
                    value JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    expires_at TIMESTAMP,
                    UNIQUE(agent_id, session_id, key)
                );
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.print_status("PostgreSQL tables created successfully")
            
        except Exception as e:
            self.print_error(f"Error creating PostgreSQL tables: {e}")
            
    def create_env_file(self):
        """Create .env file if it doesn't exist."""
        env_file = self.orchestration_dir / ".env"
        
        if not env_file.exists():
            self.print_header("Creating .env file")
            
            # Initialize Vault with default secrets
            initialize_vault_secrets()
            
            env_content = """# OpenRouter (Recommended)
# API key is now stored in Vault at secret/data/api-keys/openrouter
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_HTTP_REFERER=http://localhost
OPENROUTER_X_TITLE=AG2 Orchestrator Test

# OR OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# OR Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# Brave Search API Key
# API key is now stored in Vault at secret/data/api-keys/brave-search
BRAVE_API_KEY=your_brave_api_key_here

# Database Configuration
# Database URL - credentials are now managed through Vault
DATABASE_URL=postgresql://postgres:secure_password@localhost:5432/postgres

# PGvector Configuration
"Placeholder"_URL=http://localhost:8000
"""
            
            with open(env_file, 'w') as f:
                f.write(env_content)
                
            self.print_warning("Please edit .env file with your actual API keys")
            
    def test_mcp_servers(self):
        """Test MCP servers."""
        self.print_header("Testing MCP Servers")
        
        try:
            # Test MCP servers
            result = subprocess.run([
                sys.executable, "test_mcp_servers.py"
            ], cwd=str(self.orchestration_dir), capture_output=True, text=True)
            
            if result.returncode == 0:
                self.print_status("MCP servers test passed")
                return True
            else:
                self.print_error("MCP servers test failed")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except Exception as e:
            self.print_error(f"Error testing MCP servers: {e}")
            return False
            
    def cleanup(self):
        """Clean up running processes."""
        self.print_header("Cleaning up")
        
        # Stop Docker containers
        try:
            subprocess.run(["docker", "stop", "PGvector"], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
            subprocess.run(["docker", "stop", "postgres"], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
            self.print_status("Docker containers stopped")
        except:
            pass
            
    def run(self):
        """Run the complete setup."""
        self.print_header("AG2 Orchestrator Complete Setup")
        
        # Check prerequisites
        if not self.check_command("python3") and not self.check_command("python"):
            self.print_error("Python is not installed")
            return False
            
        if not self.check_command("node"):
            self.print_error("Node.js is not installed")
            return False
            
        if not self.check_command("npm"):
            self.print_error("npm is not installed")
            return False
            
        # Install dependencies
        if not self.install_python_dependencies():
            return False
            
        if not self.install_node_dependencies():
            return False
            
        # Create .env file
        self.create_env_file()
        
        # Start services
        PGvector_process = self.start_PGvector()
        postgres_process = self.start_postgresql()
        
        # Wait for services to be ready
        self.print_header("Waiting for services to be ready")
        time.sleep(15)
        
        # Test MCP servers
        success = self.test_mcp_servers()
        
        if success:
            self.print_header("Setup Complete")
            self.print_status("All services are running successfully!")
            self.print_status("You can now run the AG2 system tests")
            self.print_status("Press Ctrl+C to stop services")
            
            try:
                # Keep services running
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.print_status("Shutting down...")
                
        self.cleanup()
        return success

if __name__ == "__main__":
    setup = AG2Setup()
    success = setup.run()
    sys.exit(0 if success else 1)
