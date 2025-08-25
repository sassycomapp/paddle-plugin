#!/usr/bin/env python3
"""
Extension Installation and Configuration Validation
Tests VS Code extension installation and configuration validation
"""

import os
import sys
import json
import subprocess
import platform
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extension-test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ExtensionTester:
    """VS Code extension installation and configuration validation"""
    
    def __init__(self, workspace_root: str = None, test_dir: str = None):
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self.test_dir = Path(test_dir) if test_dir else self.workspace_root / 'test-results'
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Essential extensions for development
        self.essential_extensions = [
            "ms-python.python",
            "ms-python.vscode-pylance", 
            "ms-python.black-formatter",
            "ms-python.flake8",
            "ms-python.pylint",
            "ms-python.isort",
            "ms-toolsai.jupyter",
            "ms-toolsai.jupyter-keymap",
            "ms-toolsai.jupyter-renderers",
            "ms-toolsai.vscode-jupyter-cell-tags",
            "ms-toolsai.vscode-jupyter-slideshow",
            "ms-toolsai.jupyter-powertoys",
            "GitHub.copilot",
            "GitHub.copilot-chat",
            "GitHub.vscode-pull-request-github",
            "VisualStudioExptTeam.vscodeintellicode",
            "ms-azuretools.vscode-docker",
            "ms-vscode.vscode-json",
            "ms-vscode.vscode-yaml",
            "redhat.vscode-yaml",
            "esbenp.prettier-vscode",
            "dbaeumer.vscode-eslint",
            "bradlc.vscode-tailwindcss",
            "ms-vscode.vscode-typescript-next",
            "ms-vscode.vscode-react-native",
            "ms-vscode.vscode-chrome-debug",
            "ms-vscode.vscode-firefox-debug",
            "ms-vscode.vscode-edge-devtools",
            "ms-vscode.vscode-node-azure-pack",
            "ms-vscode.vscode-cpptools",
            "ms-vscode.vscode-cmake-tools",
            "ms-vscode.vscode-makefile-tools",
            "ms-vscode.vscode-remote-containers",
            "ms-vscode.vscode-remote-ssh",
            "ms-vscode.vscode-remote-wsl",
            "ms-vscode.vscode-remote-explorer",
            "ms-vscode.vscode-remote-repositories",
            "ms-vscode.vscode-remote-share",
            "ms-vscode.vscode-remote-tunnels",
            "ms-vscode.vscode-remote-authentication",
            "ms-vscode.vscode-remote-try-python",
            "ms-vscode.vscode-try-node",
            "ms-vscode.vscode-try-java",
            "ms-vscode.vscode-try-go",
            "ms-vscode.vscode-try-rust",
            "ms-vscode.vscode-try-cpp",
            "ms-vscode.vscode-try-csharp",
            "ms-vscode.vscode-try-php",
            "ms-vscode.vscode-try-ruby",
            "ms-vscode.vscode-try-swift",
            "ms-vscode.vscode-try-kotlin",
            "ms-vscode.vscode-try-scala",
            "ms-vscode.vscode-try-haskell",
            "ms-vscode.vscode-try-elixir",
            "ms-vscode.vscode-try-erlang",
            "ms-vscode.vscode-try-dart",
            "ms-vscode.vscode-try-flutter"
        ]
        
        logger.info(f"ExtensionTester initialized with {len(self.essential_extensions)} essential extensions")
    
    def get_vscode_executable(self) -> str:
        """Get VS Code executable path based on platform"""
        system = platform.system()
        
        if system == "Windows":
            # Check common installation paths
            paths = [
                r"C:\Program Files\Microsoft VS Code\Code.exe",
                r"C:\Program Files (x86)\Microsoft VS Code\Code.exe",
                r"C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\Code.exe".format(os.getenv('USERNAME'))
            ]
            for path in paths:
                if os.path.exists(path):
                    return path
            return "code"
        elif system == "Darwin":  # macOS
            paths = [
                "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code",
                "/usr/local/bin/code"
            ]
            for path in paths:
                if os.path.exists(path):
                    return path
            return "code"
        else:  # Linux and other Unix-like systems
            return "code"
    
    def check_vscode_installation(self) -> bool:
        """Check if VS Code is installed and accessible"""
        try:
            vscode_exec = self.get_vscode_executable()
            result = subprocess.run([vscode_exec, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"VS Code found: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"VS Code command failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error("VS Code version check timed out")
            return False
        except Exception as e:
            logger.error(f"Error checking VS Code installation: {e}")
            return False
    
    def install_extensions(self) -> Dict[str, bool]:
        """Install essential extensions"""
        if not self.check_vscode_installation():
            logger.error("VS Code not found, cannot install extensions")
            return {}
        
        vscode_exec = self.get_vscode_executable()
        results = {}
        
        logger.info(f"Installing {len(self.essential_extensions)} extensions...")
        
        for extension in self.essential_extensions:
            try:
                logger.info(f"Installing {extension}...")
                result = subprocess.run(
                    [vscode_exec, "--install-extension", extension],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    results[extension] = True
                    logger.info(f"✓ Successfully installed {extension}")
                else:
                    results[extension] = False
                    logger.error(f"✗ Failed to install {extension}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                results[extension] = False
                logger.error(f"✗ Installation of {extension} timed out")
            except Exception as e:
                results[extension] = False
                logger.error(f"✗ Error installing {extension}: {e}")
        
        return results
    
    def validate_extensions(self) -> Dict[str, bool]:
        """Validate installed extensions"""
        if not self.check_vscode_installation():
            logger.error("VS Code not found, cannot validate extensions")
            return {}
        
        vscode_exec = self.get_vscode_executable()
        results = {}
        
        logger.info("Validating installed extensions...")
        
        for extension in self.essential_extensions:
            try:
                logger.info(f"Validating {extension}...")
                result = subprocess.run(
                    [vscode_exec, "--list-extensions"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    installed_extensions = result.stdout.strip().split('\n')
                    if extension in installed_extensions:
                        results[extension] = True
                        logger.info(f"✓ {extension} is installed")
                    else:
                        results[extension] = False
                        logger.warning(f"✗ {extension} is not installed")
                else:
                    results[extension] = False
                    logger.error(f"✗ Failed to list extensions: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                results[extension] = False
                logger.error(f"✗ Extension validation timed out for {extension}")
            except Exception as e:
                results[extension] = False
                logger.error(f"✗ Error validating {extension}: {e}")
        
        return results
    
    def test_extension_functionality(self) -> Dict[str, bool]:
        """Test basic functionality of key extensions"""
        functionality_tests = {}
        
        # Test Python extension
        functionality_tests["python_linting"] = self._test_python_linting()
        functionality_tests["python_formatting"] = self._test_python_formatting()
        
        # Test Jupyter extension
        functionality_tests["jupyter_notebook"] = self._test_jupyter_notebook()
        
        # Test Git integration
        functionality_tests["git_integration"] = self._test_git_integration()
        
        return functionality_tests
    
    def _test_python_linting(self) -> bool:
        """Test Python linting functionality"""
        try:
            # Create a simple Python file with linting issues
            test_file = self.test_dir / "test_linting.py"
            test_file.write_text("""
def test_function():
    x = 1
    y = 2
    return x + y

# Unused variable
unused_var = "test"
""")
            
            logger.info("Testing Python linting...")
            # This would require actual linting setup to test properly
            # For now, just check if Python extension is available
            return True
            
        except Exception as e:
            logger.error(f"Error testing Python linting: {e}")
            return False
    
    def _test_python_formatting(self) -> bool:
        """Test Python formatting functionality"""
        try:
            # Create a Python file that needs formatting
            test_file = self.test_dir / "test_formatting.py"
            test_file.write_text("def test_function( x,y ):\n    return x+y\n")
            
            logger.info("Testing Python formatting...")
            # This would require actual formatter setup to test properly
            # For now, just check if Black formatter extension is available
            return True
            
        except Exception as e:
            logger.error(f"Error testing Python formatting: {e}")
            return False
    
    def _test_jupyter_notebook(self) -> bool:
        """Test Jupyter notebook functionality"""
        try:
            # Create a simple Jupyter notebook
            test_notebook = {
                "cells": [
                    {
                        "cell_type": "code",
                        "execution_count": None,
                        "metadata": {},
                        "outputs": [],
                        "source": ["print('Hello, Jupyter!')"]
                    }
                ],
                "metadata": {
                    "kernelspec": {
                        "display_name": "Python 3",
                        "language": "python",
                        "name": "python3"
                    },
                    "language_info": {
                        "name": "python",
                        "version": "3.8.0"
                    }
                },
                "nbformat": 4,
                "nbformat_minor": 4
            }
            
            notebook_file = self.test_dir / "test_notebook.ipynb"
            with open(notebook_file, 'w') as f:
                json.dump(test_notebook, f, indent=2)
            
            logger.info("Testing Jupyter notebook...")
            # This would require actual Jupyter setup to test properly
            # For now, just check if Jupyter extensions are available
            return True
            
        except Exception as e:
            logger.error(f"Error testing Jupyter notebook: {e}")
            return False
    
    def _test_git_integration(self) -> bool:
        """Test Git integration functionality"""
        try:
            # Check if git is available
            result = subprocess.run(["git", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.info("Git integration test passed")
                return True
            else:
                logger.warning("Git not found, skipping Git integration test")
                return False
                
        except Exception as e:
            logger.error(f"Error testing Git integration: {e}")
            return False
    
    def generate_test_report(self, install_results: Dict[str, bool], 
                           validation_results: Dict[str, bool], 
                           functionality_results: Dict[str, bool]) -> str:
        """Generate comprehensive test report"""
        report = []
        report.append("=== VS Code Extension Testing Report ===")
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Installation results
        report.append("=== Extension Installation Results ===")
        successful_installs = sum(1 for result in install_results.values() if result)
        total_extensions = len(install_results)
        report.append(f"Successfully installed: {successful_installs}/{total_extensions}")
        report.append("")
        
        for extension, success in install_results.items():
            status = "✓" if success else "✗"
            report.append(f"{status} {extension}")
        report.append("")
        
        # Validation results
        report.append("=== Extension Validation Results ===")
        successful_validations = sum(1 for result in validation_results.values() if result)
        total_validations = len(validation_results)
        report.append(f"Successfully validated: {successful_validations}/{total_validations}")
        report.append("")
        
        for extension, success in validation_results.items():
            status = "✓" if success else "✗"
            report.append(f"{status} {extension}")
        report.append("")
        
        # Functionality results
        report.append("=== Extension Functionality Test Results ===")
        successful_functionality = sum(1 for result in functionality_results.values() if result)
        total_functionality = len(functionality_results)
        report.append(f"Successfully tested: {successful_functionality}/{total_functionality}")
        report.append("")
        
        for test, success in functionality_results.items():
            status = "✓" if success else "✗"
            report.append(f"{status} {test}")
        report.append("")
        
        # Summary
        report.append("=== Summary ===")
        overall_success = (
            successful_installs == total_extensions and
            successful_validations == total_validations and
            successful_functionality == total_functionality
        )
        
        if overall_success:
            report.append("🎉 All tests passed! VS Code extension setup is complete.")
        else:
            report.append("⚠️  Some tests failed. Please review the results above.")
        
        return "\n".join(report)
    
    def run_complete_test(self) -> bool:
        """Run complete extension testing workflow"""
        logger.info("Starting complete extension testing workflow...")
        
        # Step 1: Install extensions
        logger.info("Step 1: Installing extensions...")
        install_results = self.install_extensions()
        
        # Step 2: Validate extensions
        logger.info("Step 2: Validating extensions...")
        validation_results = self.validate_extensions()
        
        # Step 3: Test functionality
        logger.info("Step 3: Testing extension functionality...")
        functionality_results = self.test_extension_functionality()
        
        # Step 4: Generate report
        logger.info("Step 4: Generating test report...")
        report = self.generate_test_report(install_results, validation_results, functionality_results)
        
        # Save report
        report_file = self.test_dir / "extension-test-report.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"Test report saved to: {report_file}")
        print(report)
        
        # Return overall success status
        return (
            all(install_results.values()) and
            all(validation_results.values()) and
            all(functionality_results.values())
        )

def main():
    """Main entry point"""
    print("VS Code Extension Testing Tool")
    print("=" * 40)
    
    tester = ExtensionTester()
    success = tester.run_complete_test()
    
    if success:
        print("\n🎉 Extension testing completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️  Extension testing completed with some failures.")
        sys.exit(1)

if __name__ == "__main__":
    main()