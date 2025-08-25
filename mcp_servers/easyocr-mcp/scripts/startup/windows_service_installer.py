#!/usr/bin/env python3
"""
EasyOCR MCP Server Windows Service Installer

This script provides a complete Windows service installation and management
solution for the EasyOCR MCP Server.

Author: Kilo Code
License: Apache 2.0
"""

import os
import sys
import json
import logging
import subprocess
import winreg
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


class WindowsServiceInstaller:
    """Windows service installer for EasyOCR MCP Server."""
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize installer."""
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent.parent
        self.service_name = "EasyOCR-MCP-Server"
        self.service_display_name = "EasyOCR MCP Server"
        self.service_description = "EasyOCR MCP Server for text extraction from images"
        self.python_executable = sys.executable
        self.service_script = str(self.project_root / "main.py")
        self.config_path = str(self.project_root / "config" / "easyocr_mcp_config.json")
        
        # Service configuration
        self.service_port = 8003
        self.service_host = "0.0.0.0"
        self.service_workers = 1
        
        # Logging
        self.logger = logging.getLogger(__name__)
        
        # Check if running as administrator
        self.is_administrator = self._check_administrator()
        
    def _check_administrator(self) -> bool:
        """Check if running as administrator."""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _check_python_version(self) -> bool:
        """Check if Python version is compatible."""
        try:
            version = sys.version_info
            if version.major < 3 or (version.major == 3 and version.minor < 7):
                self.logger.error(f"Python 3.7+ required. Current version: {version.major}.{version.minor}.{version.micro}")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Failed to check Python version: {e}")
            return False
    
    def _check_dependencies(self) -> bool:
        """Check if all dependencies are installed."""
        try:
            required_packages = [
                'aiohttp',
                'fastmcp',
                'easyocr',
                'pillow',
                'numpy',
                'opencv-python'
            ]
            
            missing_packages = []
            
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                self.logger.error(f"Missing packages: {', '.join(missing_packages)}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to check dependencies: {e}")
            return False
    
    def _create_service_config(self) -> bool:
        """Create service configuration file."""
        try:
            config = {
                "service": {
                    "name": self.service_name,
                    "display_name": self.service_display_name,
                    "description": self.service_description,
                    "port": self.service_port,
                    "host": self.service_host,
                    "workers": self.service_workers,
                    "python_executable": self.python_executable,
                    "service_script": self.service_script,
                    "config_path": self.config_path,
                    "working_directory": str(self.project_root),
                    "log_file": str(self.project_root / "logs" / "service.log"),
                    "error_file": str(self.project_root / "logs" / "service_error.log"),
                    "auto_start": True,
                    "delayed_start": False,
                    "restart_on_failure": True,
                    "restart_attempts": 3,
                    "restart_interval": 60
                },
                "environment": {
                    "PYTHONPATH": str(self.project_root / "src"),
                    "PYTHONUNBUFFERED": "1",
                    "EASYOCR_MCP_PORT": str(self.service_port),
                    "EASYOCR_MCP_HOST": self.service_host,
                    "EASYOCR_MCP_WORKERS": str(self.service_workers),
                    "EASYOCR_MCP_CONFIG": self.config_path
                }
            }
            
            # Save service configuration
            service_config_path = self.project_root / "config" / "service_config.json"
            with open(service_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info("Service configuration created")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create service configuration: {e}")
            return False
    
    def _create_registry_entries(self) -> bool:
        """Create Windows registry entries."""
        try:
            # Open registry key
            key_path = r"SYSTEM\CurrentControlSet\Services\EasyOCR-MCP-Server"
            
            try:
                # Try to open existing key
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS)
                winreg.CloseKey(key)
            except FileNotFoundError:
                # Create new key
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                winreg.CloseKey(key)
            
            # Set registry values
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS)
            
            # Service configuration
            winreg.SetValueEx(key, "Type", 0, winreg.REG_DWORD, 0x110)  # SERVICE_WIN32_OWN_PROCESS | SERVICE_INTERACTIVE_PROCESS
            winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, 0x3)   # SERVICE_AUTO_START
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, self.service_display_name)
            winreg.SetValueEx(key, "Description", 0, winreg.REG_SZ, self.service_description)
            winreg.SetValueEx(key, "ObjectName", 0, winreg.REG_SZ, "LocalSystem")
            
            # Image path
            image_path = f'"{self.python_executable}" "{self.service_script}"'
            winreg.SetValueEx(key, "ImagePath", 0, winreg.REG_SZ, image_path)
            
            # Working directory
            winreg.SetValueEx(key, "ObjectName", 0, winreg.REG_SZ, "LocalSystem")
            
            winreg.CloseKey(key)
            
            # Create Parameters key
            param_key_path = r"SYSTEM\CurrentControlSet\Services\EasyOCR-MCP-Server\Parameters"
            try:
                param_key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, param_key_path)
                winreg.SetValueEx(param_key, "Application", 0, winreg.REG_SZ, self.python_executable)
                winreg.SetValueEx(param_key, "AppParameters", 0, winreg.REG_SZ, f'"{self.service_script}"')
                winreg.SetValueEx(param_key, "AppDirectory", 0, winreg.REG_SZ, str(self.project_root))
                winreg.CloseKey(param_key)
            except Exception as e:
                self.logger.warning(f"Failed to create Parameters key: {e}")
            
            self.logger.info("Registry entries created")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create registry entries: {e}")
            return False
    
    def _create_event_log_source(self) -> bool:
        """Create event log source."""
        try:
            import win32evtlogutil
            import win32api
            import win32con
            
            # Try to create event source
            try:
                win32api.RegisterEventSource(
                    None,
                    self.service_name
                )
                self.logger.info("Event log source created")
                return True
            except Exception as e:
                if "exists" in str(e):
                    self.logger.info("Event log source already exists")
                    return True
                else:
                    self.logger.error(f"Failed to create event log source: {e}")
                    return False
                    
        except ImportError:
            self.logger.warning("pywin32 not available, skipping event log source creation")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create event log source: {e}")
            return False
    
    def _create_service_files(self) -> bool:
        """Create service-related files."""
        try:
            # Create service batch file
            batch_file = self.project_root / "scripts" / "startup" / "install_service.bat"
            batch_file.parent.mkdir(parents=True, exist_ok=True)
            
            batch_content = f'''@echo off
echo Installing EasyOCR MCP Server as Windows Service...
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Please run this script as Administrator
    pause
    exit /b 1
)

:: Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo Failed to install dependencies
    pause
    exit /b 1
)

:: Create directories
echo Creating directories...
mkdir logs 2>nul
mkdir temp 2>nul
mkdir output 2>nul
mkdir models 2>nul

:: Run Python installer
echo Running Python installer...
python "{self.project_root}\\scripts\\deploy\\deploy_easyocr_service.py"

:: Install service
echo Installing Windows Service...
python "{self.project_root}\\scripts\\startup\\windows_service_installer.py" install

if %errorLevel% neq 0 (
    echo Service installation failed
    pause
    exit /b 1
)

echo.
echo EasyOCR MCP Server installed successfully!
echo.
echo To start the service:
echo   net start EasyOCR-MCP-Server
echo.
echo To check service status:
echo   sc query EasyOCR-MCP-Server
echo.
pause
'''
            
            with open(batch_file, 'w') as f:
                f.write(batch_content)
            
            # Create uninstall batch file
            uninstall_batch_file = self.project_root / "scripts" / "startup" / "uninstall_service.bat"
            uninstall_batch_content = f'''@echo off
echo Uninstalling EasyOCR MCP Server...
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Please run this script as Administrator
    pause
    exit /b 1
)

:: Stop service
echo Stopping service...
net stop EasyOCR-MCP-Server 2>nul

:: Remove service
echo Removing service...
python "{self.project_root}\\scripts\\startup\\windows_service_installer.py" uninstall

if %errorLevel% neq 0 (
    echo Service removal failed
    pause
    exit /b 1
)

echo.
echo EasyOCR MCP Server uninstalled successfully!
echo.
pause
'''
            
            with open(uninstall_batch_file, 'w') as f:
                f.write(uninstall_batch_content)
            
            # Create service management script
            ps1_file = self.project_root / "scripts" / "startup" / "EasyOCR-MCP-Management.ps1"
            ps1_content = '''# EasyOCR MCP Server Management Script
# This script provides advanced management for the EasyOCR MCP Server

param(
    [string]$Action = "status",
    [string]$ConfigPath = "$PSScriptRoot\\..\\config\\easyocr_mcp_config.json"
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ServiceScript = Join-Path $ProjectRoot "scripts\\startup\\windows_service_installer.py"

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
    Write-Host "8. Configure Service"
    Write-Host "9. Exit"
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
    net start EasyOCR-MCP-Server
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Service started successfully!" -ForegroundColor Green
    } else {
        Write-Host "Failed to start service!" -ForegroundColor Red
    }
}

function Stop-Service {
    Write-Host "Stopping EasyOCR MCP Server..."
    net stop EasyOCR-MCP-Server
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Service stopped successfully!" -ForegroundColor Green
    } else {
        Write-Host "Failed to stop service!" -ForegroundColor Red
    }
}

function Restart-Service {
    Write-Host "Restarting EasyOCR MCP Server..."
    net stop EasyOCR-MCP-Server
    Start-Sleep -Seconds 2
    net start EasyOCR-MCP-Server
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Service restarted successfully!" -ForegroundColor Green
    } else {
        Write-Host "Failed to restart service!" -ForegroundColor Red
    }
}

function Remove-Service {
    Write-Host "Removing EasyOCR MCP Server..."
    python $ServiceScript uninstall
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Service removed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Failed to remove service!" -ForegroundColor Red
    }
}

function Check-Status {
    Write-Host "Checking EasyOCR MCP Server Status..."
    sc query EasyOCR-MCP-Server
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

function Configure-Service {
    Write-Host "Configuring EasyOCR MCP Server..."
    $ConfigFile = Join-Path $ProjectRoot "config\easyocr_mcp_config.json"
    if (Test-Path $ConfigFile) {
        notepad $ConfigFile
    } else {
        Write-Host "Configuration file not found: $ConfigFile" -ForegroundColor Yellow
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
    "configure" { Configure-Service }
    default {
        Show-Menu
        $choice = Read-Host "Select an option (1-9)"
        
        switch ($choice) {
            "1" { Install-Service }
            "2" { Start-Service }
            "3" { Stop-Service }
            "4" { Restart-Service }
            "5" { Remove-Service }
            "6" { Check-Status }
            "7" { View-Logs }
            "8" { Configure-Service }
            "9" { exit }
            default { Write-Host "Invalid option!" -ForegroundColor Red }
        }
    }
}
'''
            
            with open(ps1_file, 'w') as f:
                f.write(ps1_content)
            
            self.logger.info("Service files created")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create service files: {e}")
            return False
    
    def install_service(self) -> bool:
        """Install the Windows service."""
        try:
            self.logger.info("Installing Windows service...")
            
            # Check prerequisites
            if not self.is_administrator:
                self.logger.error("Administrator privileges required")
                return False
            
            if not self._check_python_version():
                return False
            
            if not self._check_dependencies():
                return False
            
            # Create service configuration
            if not self._create_service_config():
                return False
            
            # Create registry entries
            if not self._create_registry_entries():
                return False
            
            # Create event log source
            if not self._create_event_log_source():
                return False
            
            # Create service files
            if not self._create_service_files():
                return False
            
            # Install service using sc
            cmd = [
                'sc',
                'create',
                self.service_name,
                f'displayname= "{self.service_display_name}"',
                f'description= "{self.service_description}"',
                f'binPath= "{self.python_executable} {self.service_script}"',
                'start= auto',
                'type= own',
                'depend= '
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("Windows service installed successfully")
                
                # Set service dependencies
                self._set_service_dependencies()
                
                # Start service
                self.start_service()
                
                return True
            else:
                self.logger.error(f"Failed to install Windows service: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to install Windows service: {e}")
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
                self.logger.info("Service dependencies set successfully")
                return True
            else:
                self.logger.error(f"Failed to set service dependencies: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to set service dependencies: {e}")
            return False
    
    def start_service(self) -> bool:
        """Start the Windows service."""
        try:
            self.logger.info("Starting Windows service...")
            
            cmd = ['net', 'start', self.service_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("Windows service started successfully")
                return True
            else:
                self.logger.error(f"Failed to start Windows service: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start Windows service: {e}")
            return False
    
    def stop_service(self) -> bool:
        """Stop the Windows service."""
        try:
            self.logger.info("Stopping Windows service...")
            
            cmd = ['net', 'stop', self.service_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("Windows service stopped successfully")
                return True
            else:
                self.logger.error(f"Failed to stop Windows service: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to stop Windows service: {e}")
            return False
    
    def restart_service(self) -> bool:
        """Restart the Windows service."""
        try:
            self.logger.info("Restarting Windows service...")
            
            # Stop service
            if not self.stop_service():
                return False
            
            # Wait a moment
            import time
            time.sleep(2)
            
            # Start service
            return self.start_service()
            
        except Exception as e:
            self.logger.error(f"Failed to restart Windows service: {e}")
            return False
    
    def remove_service(self) -> bool:
        """Remove the Windows service."""
        try:
            self.logger.info("Removing Windows service...")
            
            # Stop service first
            self.stop_service()
            
            # Remove service
            cmd = ['sc', 'delete', self.service_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("Windows service removed successfully")
                return True
            else:
                self.logger.error(f"Failed to remove Windows service: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to remove Windows service: {e}")
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
    
    def run_installation(self) -> bool:
        """Run the complete installation process."""
        try:
            self.logger.info("Starting EasyOCR MCP Server Windows installation...")
            
            # Run installation steps
            steps = [
                ("Check administrator privileges", lambda: self.is_administrator),
                ("Check Python version", self._check_python_version),
                ("Check dependencies", self._check_dependencies),
                ("Create service configuration", self._create_service_config),
                ("Create registry entries", self._create_registry_entries),
                ("Create event log source", self._create_event_log_source),
                ("Create service files", self._create_service_files),
                ("Install service", self.install_service)
            ]
            
            for step_name, step_func in steps:
                self.logger.info(f"Running: {step_name}")
                if callable(step_func):
                    if not step_func():
                        self.logger.error(f"Failed: {step_name}")
                        return False
                else:
                    if not step_func:
                        self.logger.error(f"Failed: {step_name}")
                        return False
                self.logger.info(f"Completed: {step_name}")
            
            self.logger.info("EasyOCR MCP Server Windows installation completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Installation failed: {e}")
            return False


def main():
    """Main entry point for Windows service installer."""
    try:
        # Parse command line arguments
        if len(sys.argv) < 2:
            print("Usage: python windows_service_installer.py <install|start|stop|restart|remove|status>")
            sys.exit(1)
        
        action = sys.argv[1]
        
        # Create installer
        installer = WindowsServiceInstaller()
        
        # Execute action
        if action == 'install':
            success = installer.run_installation()
            sys.exit(0 if success else 1)
        elif action == 'start':
            success = installer.start_service()
            sys.exit(0 if success else 1)
        elif action == 'stop':
            success = installer.stop_service()
            sys.exit(0 if success else 1)
        elif action == 'restart':
            success = installer.restart_service()
            sys.exit(0 if success else 1)
        elif action == 'remove':
            success = installer.remove_service()
            sys.exit(0 if success else 1)
        elif action == 'status':
            status = installer.get_service_status()
            print(json.dumps(status, indent=2))
            sys.exit(0 if status['status'] == 'running' else 1)
        else:
            print(f"Unknown action: {action}")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Windows service installer failed: {e}")
        print(f"Windows service installer failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()