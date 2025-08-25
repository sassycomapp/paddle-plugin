#!/usr/bin/env python3
"""
EasyOCR MCP Server Deployment Script

This script sets up the EasyOCR MCP server to run as a background service
with proper configuration, monitoring, and logging integration.

Author: Kilo Code
License: Apache 2.0
"""

import os
import sys
import json
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EasyOCRServiceDeployer:
    """Handles deployment and setup of EasyOCR MCP server as a background service."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize deployer."""
        self.project_root = Path(__file__).parent.parent.parent
        self.config_path = config_path or str(self.project_root / "config" / "easyocr_mcp_config.json")
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self._load_config()
        
        # Service configuration
        self.service_name = "easyocr-mcp"
        self.service_port = self.config.get('service', {}).get('port', 8003)
        self.service_host = self.config.get('service', {}).get('host', '0.0.0.0')
        self.service_workers = self.config.get('service', {}).get('workers', 1)
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Add service configuration if not present
            if 'service' not in config:
                config['service'] = {
                    'port': 8003,
                    'host': '0.0.0.0',
                    'workers': 1,
                    'reload': False,
                    'log_level': 'info'
                }
            
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Return default configuration
            return {
                'service': {
                    'port': 8003,
                    'host': '0.0.0.0',
                    'workers': 1,
                    'reload': False,
                    'log_level': 'info'
                }
            }
    
    def setup_directories(self) -> bool:
        """Setup required directories."""
        try:
            self.logger.info("Setting up directories...")
            
            # Create required directories
            directories = [
                'logs',
                'temp',
                'output',
                'models',
                'pid'
            ]
            
            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created directory: {dir_path}")
            
            # Set permissions
            for directory in directories:
                dir_path = self.project_root / directory
                os.chmod(dir_path, 0o755)
            
            self.logger.info("Directories setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup directories: {e}")
            return False
    
    def setup_logging(self) -> bool:
        """Setup logging configuration."""
        try:
            self.logger.info("Setting up logging...")
            
            # Create logging configuration
            logging_config = {
                'version': 1,
                'disable_existing_loggers': False,
                'formatters': {
                    'standard': {
                        'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                    },
                    'detailed': {
                        'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
                    }
                },
                'handlers': {
                    'console': {
                        'level': 'INFO',
                        'class': 'logging.StreamHandler',
                        'formatter': 'standard'
                    },
                    'file': {
                        'level': 'INFO',
                        'class': 'logging.handlers.RotatingFileHandler',
                        'filename': str(self.project_root / 'logs' / 'easyocr_mcp.log'),
                        'maxBytes': 10485760,  # 10MB
                        'backupCount': 5,
                        'formatter': 'detailed'
                    },
                    'error_file': {
                        'level': 'ERROR',
                        'class': 'logging.handlers.RotatingFileHandler',
                        'filename': str(self.project_root / 'logs' / 'easyocr_mcp_error.log'),
                        'maxBytes': 10485760,  # 10MB
                        'backupCount': 3,
                        'formatter': 'detailed'
                    }
                },
                'loggers': {
                    '': {
                        'handlers': ['console', 'file', 'error_file'],
                        'level': 'INFO',
                        'propagate': False
                    }
                }
            }
            
            # Save logging configuration
            logging_config_path = self.project_root / 'config' / 'logging_config.json'
            with open(logging_config_path, 'w') as f:
                json.dump(logging_config, f, indent=2)
            
            self.logger.info("Logging setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup logging: {e}")
            return False
    
    def setup_environment(self) -> bool:
        """Setup environment variables."""
        try:
            self.logger.info("Setting up environment...")
            
            # Create environment configuration
            env_config = {
                'EASYOCR_MCP_PORT': str(self.service_port),
                'EASYOCR_MCP_HOST': self.service_host,
                'EASYOCR_MCP_WORKERS': str(self.service_workers),
                'EASYOCR_MCP_CONFIG': self.config_path,
                'EASYOCR_MCP_LOG_LEVEL': self.config.get('service', {}).get('log_level', 'info'),
                'PYTHONPATH': str(self.project_root / 'src'),
                'PYTHONUNBUFFERED': '1'
            }
            
            # Save environment configuration
            env_config_path = self.project_root / 'config' / 'env_config.json'
            with open(env_config_path, 'w') as f:
                json.dump(env_config, f, indent=2)
            
            # Create .env file
            env_file_path = self.project_root / '.env'
            with open(env_file_path, 'w') as f:
                for key, value in env_config.items():
                    f.write(f"{key}={value}\n")
            
            self.logger.info("Environment setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup environment: {e}")
            return False
    
    def setup_monitoring(self) -> bool:
        """Setup monitoring and health checks."""
        try:
            self.logger.info("Setting up monitoring...")
            
            # Create health check script
            health_check_script = self.project_root / 'scripts' / 'monitoring' / 'health_check.py'
            health_check_script.parent.mkdir(parents=True, exist_ok=True)
            
            health_check_content = '''#!/usr/bin/env python3
"""
EasyOCR MCP Server Health Check Script

This script provides health check functionality for the EasyOCR MCP server.
"""

import os
import sys
import json
import requests
import logging
from pathlib import Path
from typing import Dict, Any

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_service_health() -> Dict[str, Any]:
    """Check the health of the EasyOCR MCP server."""
    try:
        # Get service configuration
        config_path = Path(__file__).parent.parent.parent / "config" / "env_config.json"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            port = config.get('EASYOCR_MCP_PORT', '8003')
            host = config.get('EASYOCR_MCP_HOST', 'localhost')
        else:
            port = '8003'
            host = 'localhost'
        
        # Try to connect to the service
        try:
            response = requests.get(
                f"http://{host}:{port}/health",
                timeout=5
            )
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'service': 'easyocr-mcp',
                    'port': port,
                    'host': host,
                    'response_time': response.elapsed.total_seconds(),
                    'timestamp': str(response.json().get('timestamp', 'unknown'))
                }
            else:
                return {
                    'status': 'unhealthy',
                    'service': 'easyocr-mcp',
                    'port': port,
                    'host': host,
                    'error': f'HTTP {response.status_code}',
                    'timestamp': str(response.json().get('timestamp', 'unknown'))
                }
        
        except requests.exceptions.ConnectionError:
            return {
                'status': 'unhealthy',
                'service': 'easyocr-mcp',
                'port': port,
                'host': host,
                'error': 'Connection refused',
                'timestamp': str(datetime.now())
            }
        
        except requests.exceptions.Timeout:
            return {
                'status': 'unhealthy',
                'service': 'easyocr-mcp',
                'port': port,
                'host': host,
                'error': 'Connection timeout',
                'timestamp': str(datetime.now())
            }
        
        except Exception as e:
            return {
                'status': 'unhealthy',
                'service': 'easyocr-mcp',
                'port': port,
                'host': host,
                'error': str(e),
                'timestamp': str(datetime.now())
            }
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'error',
            'service': 'easyocr-mcp',
            'error': str(e),
            'timestamp': str(datetime.now())
        }

if __name__ == "__main__":
    health = check_service_health()
    print(json.dumps(health, indent=2))
    
    if health['status'] != 'healthy':
        sys.exit(1)
'''
            
            with open(health_check_script, 'w') as f:
                f.write(health_check_content)
            
            # Make health check script executable
            os.chmod(health_check_script, 0o755)
            
            # Create monitoring configuration
            monitoring_config = {
                'enabled': True,
                'health_check_interval': 30,
                'health_check_timeout': 10,
                'metrics_collection': True,
                'log_monitoring': True,
                'error_alerting': True,
                'alert_thresholds': {
                    'response_time': 5.0,
                    'error_rate': 0.1,
                    'memory_usage': 0.8
                }
            }
            
            # Save monitoring configuration
            monitoring_config_path = self.project_root / 'config' / 'monitoring_config.json'
            with open(monitoring_config_path, 'w') as f:
                json.dump(monitoring_config, f, indent=2)
            
            self.logger.info("Monitoring setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup monitoring: {e}")
            return False
    
    def setup_network_configuration(self) -> bool:
        """Setup network configuration."""
        try:
            self.logger.info("Setting up network configuration...")
            
            # Create network configuration
            network_config = {
                'host': self.service_host,
                'port': self.service_port,
                'workers': self.service_workers,
                'reload': self.config.get('service', {}).get('reload', False),
                'ssl_enabled': False,
                'ssl_cert_path': None,
                'ssl_key_path': None,
                'cors_enabled': True,
                'cors_origins': ['*'],
                'rate_limiting': {
                    'enabled': True,
                    'requests_per_minute': 100
                },
                'timeout': {
                    'connection': 30,
                    'read': 60,
                    'write': 30
                }
            }
            
            # Save network configuration
            network_config_path = self.project_root / 'config' / 'network_config.json'
            with open(network_config_path, 'w') as f:
                json.dump(network_config, f, indent=2)
            
            self.logger.info("Network configuration setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup network configuration: {e}")
            return False
    
    def setup_authentication(self) -> bool:
        """Setup authentication and security configuration."""
        try:
            self.logger.info("Setting up authentication...")
            
            # Create authentication configuration
            auth_config = {
                'enabled': False,
                'auth_type': 'none',  # none, api_key, jwt, oauth
                'api_key_required': False,
                'api_key_header': 'X-API-Key',
                'jwt_required': False,
                'jwt_secret_key': None,
                'jwt_algorithm': 'HS256',
                'oauth_required': False,
                'oauth_provider': None,
                'oauth_client_id': None,
                'oauth_client_secret': None,
                'oauth_redirect_uri': None,
                'user_management': {
                    'enabled': False,
                    'user_file': 'users.json',
                    'role_based_access': False,
                    'admin_users': []
                },
                'rate_limiting': {
                    'enabled': True,
                    'requests_per_minute': 100,
                    'burst_limit': 20
                },
                'ip_whitelist': [],
                'ip_blacklist': []
            }
            
            # Save authentication configuration
            auth_config_path = self.project_root / 'config' / 'auth_config.json'
            with open(auth_config_path, 'w') as f:
                json.dump(auth_config, f, indent=2)
            
            self.logger.info("Authentication setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup authentication: {e}")
            return False
    
    def create_windows_service_script(self) -> bool:
        """Create Windows service script."""
        try:
            self.logger.info("Creating Windows service script...")
            
            # Create Windows service script
            service_script = self.project_root / 'scripts' / 'deploy' / 'easyocr_mcp_service.py'
            service_script.parent.mkdir(parents=True, exist_ok=True)
            
            service_content = '''#!/usr/bin/env python3
"""
EasyOCR MCP Server Windows Service Script

This script provides Windows service functionality for the EasyOCR MCP server.
"""

import os
import sys
import time
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EasyOCRWindowsService:
    """Windows service for EasyOCR MCP server."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.service_name = "EasyOCR-MCP-Server"
        self.service_display_name = "EasyOCR MCP Server"
        self.service_description = "EasyOCR MCP Server for text extraction from images"
        self.python_executable = sys.executable
        self.service_script = str(self.project_root / "main.py")
        
    def install_service(self) -> bool:
        """Install the Windows service."""
        try:
            logger.info("Installing Windows service...")
            
            # Create service installation command
            cmd = [
                'sc',
                'create',
                self.service_name,
                f'displayname= "{self.service_display_name}"',
                f'description= "{self.service_description}"',
                f'binPath= "{self.python_executable} {self.service_script}"',
                'start= auto',
                'type= own'
            ]
            
            # Run installation command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Windows service installed successfully")
                
                # Set service dependencies
                self._set_service_dependencies()
                
                return True
            else:
                logger.error(f"Failed to install Windows service: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to install Windows service: {e}")
            return False
    
    def _set_service_dependencies(self) -> bool:
        """Set service dependencies."""
        try:
            # Set service dependencies (if any)
            cmd = [
                'sc',
                'config',
                self.service_name,
                'depend= '  # Add dependencies if needed
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Service dependencies set successfully")
                return True
            else:
                logger.error(f"Failed to set service dependencies: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to set service dependencies: {e}")
            return False
    
    def start_service(self) -> bool:
        """Start the Windows service."""
        try:
            logger.info("Starting Windows service...")
            
            cmd = ['sc', 'start', self.service_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Windows service started successfully")
                return True
            else:
                logger.error(f"Failed to start Windows service: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start Windows service: {e}")
            return False
    
    def stop_service(self) -> bool:
        """Stop the Windows service."""
        try:
            logger.info("Stopping Windows service...")
            
            cmd = ['sc', 'stop', self.service_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Windows service stopped successfully")
                return True
            else:
                logger.error(f"Failed to stop Windows service: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to stop Windows service: {e}")
            return False
    
    def restart_service(self) -> bool:
        """Restart the Windows service."""
        try:
            logger.info("Restarting Windows service...")
            
            # Stop service
            if not self.stop_service():
                return False
            
            # Wait a moment
            time.sleep(2)
            
            # Start service
            return self.start_service()
            
        except Exception as e:
            logger.error(f"Failed to restart Windows service: {e}")
            return False
    
    def remove_service(self) -> bool:
        """Remove the Windows service."""
        try:
            logger.info("Removing Windows service...")
            
            # Stop service first
            self.stop_service()
            
            # Remove service
            cmd = ['sc', 'delete', self.service_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Windows service removed successfully")
                return True
            else:
                logger.error(f"Failed to remove Windows service: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove Windows service: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status."""
        try:
            cmd = ['sc', 'query', self.service_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                status = result.stdout
                
                # Parse status
                status_dict = {
                    'service_name': self.service_name,
                    'status': 'unknown',
                    'state': 'unknown'
                }
                
                if 'RUNNING' in status:
                    status_dict['status'] = 'running'
                    status_dict['state'] = 'running'
                elif 'STOPPED' in status:
                    status_dict['status'] = 'stopped'
                    status_dict['state'] = 'stopped'
                elif 'PENDING' in status:
                    status_dict['status'] = 'pending'
                    status_dict['state'] = 'pending'
                
                return status_dict
            else:
                return {
                    'service_name': self.service_name,
                    'status': 'error',
                    'error': result.stderr
                }
                
        except Exception as e:
            return {
                'service_name': self.service_name,
                'status': 'error',
                'error': str(e)
            }

def main():
    """Main function."""
    service = EasyOCRWindowsService()
    
    if len(sys.argv) < 2:
        print("Usage: python easyocr_mcp_service.py <install|start|stop|restart|remove|status>")
        return
    
    command = sys.argv[1]
    
    if command == 'install':
        success = service.install_service()
        sys.exit(0 if success else 1)
    elif command == 'start':
        success = service.start_service()
        sys.exit(0 if success else 1)
    elif command == 'stop':
        success = service.stop_service()
        sys.exit(0 if success else 1)
    elif command == 'restart':
        success = service.restart_service()
        sys.exit(0 if success else 1)
    elif command == 'remove':
        success = service.remove_service()
        sys.exit(0 if success else 1)
    elif command == 'status':
        status = service.get_service_status()
        print(json.dumps(status, indent=2))
        sys.exit(0 if status['status'] == 'running' else 1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
            
            with open(service_script, 'w') as f:
                f.write(service_content)
            
            # Make service script executable
            os.chmod(service_script, 0o755)
            
            self.logger.info("Windows service script created")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create Windows service script: {e}")
            return False
    
    def create_startup_scripts(self) -> bool:
        """Create startup scripts for Windows environment."""
        try:
            self.logger.info("Creating startup scripts...")
            
            # Create startup directory
            startup_dir = self.project_root / 'scripts' / 'startup'
            startup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create batch file for starting service
            batch_file = startup_dir / 'start_service.bat'
            batch_content = f'''@echo off
echo Starting EasyOCR MCP Server...
cd /d "{self.project_root}"
python main.py --config {self.config_path}
pause
'''
            with open(batch_file, 'w') as f:
                f.write(batch_content)
            
            # Create batch file for stopping service
            stop_batch_file = startup_dir / 'stop_service.bat'
            stop_batch_content = f'''@echo off
echo Stopping EasyOCR MCP Server...
cd /d "{self.project_root}"
python scripts/deploy/easyocr_mcp_service.py stop
pause
'''
            with open(stop_batch_file, 'w') as f:
                f.write(stop_batch_content)
            
            # Create batch file for restarting service
            restart_batch_file = startup_dir / 'restart_service.bat'
            restart_batch_content = f'''@echo off
echo Restarting EasyOCR MCP Server...
cd /d "{self.project_root}"
python scripts/deploy/easyocr_mcp_service.py restart
pause
'''
            with open(restart_batch_file, 'w') as f:
                f.write(restart_batch_content)
            
            # Create batch file for checking service status
            status_batch_file = startup_dir / 'check_status.bat'
            status_batch_content = f'''@echo off
echo Checking EasyOCR MCP Server Status...
cd /d "{self.project_root}"
python scripts/deploy/easyocr_mcp_service.py status
pause
'''
            with open(status_batch_file, 'w') as f:
                f.write(status_batch_content)
            
            # Create PowerShell script for advanced management
            ps1_file = startup_dir / 'EasyOCR-MCP-Management.ps1'
            ps1_content = '''# EasyOCR MCP Server Management Script
# This script provides advanced management for the EasyOCR MCP Server

param(
    [string]$Action = "status",
    [string]$ConfigPath = "$PSScriptRoot\..\config\easyocr_mcp_config.json"
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ServiceScript = Join-Path $ProjectRoot "scripts\deploy\easyocr_mcp_service.py"

function Show-Menu {
    Write-Host "EasyOCR MCP Server Management" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    Write-Host "1. Install Service"
    Write-Host "2. Start Service"
    Write-Host "3. Stop Service"
    Write-Host "4. Restart Service"
    Write-Host "5. Remove Service"
    Write-Host "6. Check Status"
    Write-Host "7. View Logs"
    Write-Host "8. Exit"
    Write-Host ""
}

function Install-Service {
    Write-Host "Installing EasyOCR MCP Server..."
    python $ServiceScript install
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Service installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Failed to install service!" -ForegroundColor Red
    }
}

function Start-Service {
    Write-Host "Starting EasyOCR MCP Server..."
    python $ServiceScript start
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Service started successfully!" -ForegroundColor Green
    } else {
        Write-Host "Failed to start service!" -ForegroundColor Red
    }
}

function Stop-Service {
    Write-Host "Stopping EasyOCR MCP Server..."
    python $ServiceScript stop
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Service stopped successfully!" -ForegroundColor Green
    } else {
        Write-Host "Failed to stop service!" -ForegroundColor Red
    }
}

function Restart-Service {
    Write-Host "Restarting EasyOCR MCP Server..."
    python $ServiceScript restart
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Service restarted successfully!" -ForegroundColor Green
    } else {
        Write-Host "Failed to restart service!" -ForegroundColor Red
    }
}

function Remove-Service {
    Write-Host "Removing EasyOCR MCP Server..."
    python $ServiceScript remove
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Service removed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Failed to remove service!" -ForegroundColor Red
    }
}

function Check-Status {
    Write-Host "Checking EasyOCR MCP Server Status..."
    python $ServiceScript status
}

function View-Logs {
    Write-Host "Viewing EasyOCR MCP Server Logs..."
    $LogFile = Join-Path $ProjectRoot "logs\easyocr_mcp.log"
    if (Test-Path $LogFile) {
        Get-Content $LogFile -Tail 50 -Wait
    } else {
        Write-Host "Log file not found: $LogFile" -ForegroundColor Yellow
    }
}

# Main execution
switch ($Action) {
    "install" { Install-Service }
    "start" { Start-Service }
    "stop" { Stop-Service }
    "restart" { Restart-Service }
    "remove" { Remove-Service }
    "status" { Check-Status }
    "logs" { View-Logs }
    default {
        Show-Menu
        $choice = Read-Host "Select an option (1-8)"
        
        switch ($choice) {
            "1" { Install-Service }
            "2" { Start-Service }
            "3" { Stop-Service }
            "4" { Restart-Service }
            "5" { Remove-Service }
            "6" { Check-Status }
            "7" { View-Logs }
            "8" { exit }
            default { Write-Host "Invalid option!" -ForegroundColor Red }
        }
    }
}
'''
            with open(ps1_file, 'w') as f:
                f.write(ps1_content)
            
            self.logger.info("Startup scripts created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create startup scripts: {e}")
            return False
    
    def run_deployment(self) -> bool:
        """Run the complete deployment process."""
        try:
            self.logger.info("Starting EasyOCR MCP server deployment...")
            
            # Run deployment steps
            steps = [
                ("Setup directories", self.setup_directories),
                ("Setup logging", self.setup_logging),
                ("Setup environment", self.setup_environment),
                ("Setup monitoring", self.setup_monitoring),
                ("Setup network configuration", self.setup_network_configuration),
                ("Setup authentication", self.setup_authentication),
                ("Create Windows service script", self.create_windows_service_script),
                ("Create startup scripts", self.create_startup_scripts)
            ]
            
            for step_name, step_func in steps:
                self.logger.info(f"Running: {step_name}")
                if not step_func():
                    self.logger.error(f"Failed: {step_name}")
                    return False
                self.logger.info(f"Completed: {step_name}")
            
            self.logger.info("EasyOCR MCP server deployment completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Deployment failed: {e}")
            return False


def main():
    """Main entry point for deployment."""
    try:
        # Create deployer
        deployer = EasyOCRServiceDeployer()
        
        # Run deployment
        success = deployer.run_deployment()
        
        if success:
            print("\nEasyOCR MCP server deployment completed successfully!")
            print("The server is now ready to run as a background service.")
            print("\nTo start the service, run:")
            print("  python scripts/deploy/easyocr_mcp_service.py start")
            print("\nOr use the PowerShell script:")
            print("  .\\scripts\\startup\\EasyOCR-MCP-Management.ps1")
        else:
            print("\nDeployment failed. Please check the logs for details.")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        print(f"Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()