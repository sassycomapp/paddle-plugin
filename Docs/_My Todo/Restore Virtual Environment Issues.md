Virtual Environment Restoration and Consolidation Plan
Executive Summary
This document provides a comprehensive workflow to address the virtual environment issues identified in the "Mapping - Virtual Environments.md" document. The plan focuses on consolidating duplicate environments, standardizing environment management, and ensuring all functionalities remain intact during the migration process.

Current Issues Analysis
Critical Issues Identified
Duplicate Virtual Environments (HIGH SEVERITY)

Multiple virtual environments with identical Python versions (3.13.3)
Locations: easyocr-env and venv
Impact: Wasted disk space, potential dependency conflicts, development confusion
Inconsistent Environment Management (MEDIUM SEVERITY)

Mixed environment management approaches:
Standard venv (easyocr-env, venv)
Poetry (simba)
UV (easyocr-mcp)
Impact: Inconsistent dependency management, difficult maintenance
Deeply Nested Dependencies (MEDIUM SEVERITY)

Complex dependency chains in multiple environments
Examples:
easyocr-env: Contains 100+ packages with complex ML/AI dependencies
simba: Contains 40+ packages with RAG and vector database dependencies
Impact: Long installation times, potential conflicts, difficult troubleshooting
Integration Point Confusion (MEDIUM SEVERITY)

Unclear which environment serves which purpose
Examples:
Both easyocr-env and easyocr-mcp handle OCR functionality
VS Code points to venv but easyocr-env is used for OCR
Impact: Development confusion, potential runtime errors, difficult onboarding
Environment Inventory
Current Environments
easyocr-env

Location: C:\_1mybizz\paddle-plugin\easyocr-env
Python Version: 3.13.3
Base Python: C:\Python313\python.exe
Configuration: include-system-site-packages = false
Purpose: Dedicated environment for EasyOCR operations
Integration Points: Used by easyocr-mcp module, Environment variable: EASYOCR_LANGUAGES
venv (Root Level)

Location: C:\_1mybizz\paddle-plugin\venv
Python Version: 3.13.3
Base Python: C:\Python313\python.exe
Configuration: include-system-site-packages = false
Purpose: General development environment
Integration Points: VS Code default interpreter, Used by setup scripts
simba Environment

Location: C:\_1mybizz\paddle-plugin\simba
Python Version: 3.13.3 (specified in .python-version)
Management: Poetry-based
Purpose: Knowledge Management System
Integration Points: CLI tool simba, Dependencies: langchain, faiss-cpu, sentence-transformers
easyocr-mcp Environment

Location: C:\_1mybizz\paddle-plugin\easyocr-mcp
Management: UV-based (pyproject.toml + uv.lock)
Python Version: >=3.13
Purpose: MCP server for EasyOCR integration
Integration Points: MCP server integration, Environment variable: EASYOCR_LANGUAGES
Recommended Workflow
Phase 1: Assessment and Planning (Week 1)
1.1 Create Comprehensive Backups
# Create timestamped backups
$backupDate = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item -Path "C:\_1mybizz\paddle-plugin\easyocr-env" -Destination "C:\_1mybizz\paddle-plugin\backups\easyocr-env-backup_$backupDate" -Recurse
Copy-Item -Path "C:\_1mybizz\paddle-plugin\venv" -Destination "C:\_1mybizz\paddle-plugin\backups\venv-backup_$backupDate" -Recurse
Copy-Item -Path "C:\_1mybizz\paddle-plugin\simba" -Destination "C:\_1mybizz\paddle-plugin\backups\simba-backup_$backupDate" -Recurse
Copy-Item -Path "C:\_1mybizz\paddle-plugin\easyocr-mcp" -Destination "C:\_1mybizz\paddle-plugin\backups\easyocr-mcp-backup_$backupDate" -Recurse

bash


1.2 Document Current State
Create dependency matrix showing all packages across environments
Map which services use which environments
Document environment variables and their sources
Record current integration points and configurations
1.3 Create Rollback Plan
Document backup locations and restoration procedures
Create step-by-step rollback instructions
Identify critical success metrics for validation
Phase 2: Environment Consolidation (Week 2)
2.1 Create Unified Poetry Environment
# Navigate to project root
cd C:\_1mybizz\paddle-plugin

# Initialize Poetry if not already done
poetry init

# Create unified environment using Poetry
poetry env use python3.13

# Install all dependencies from all environments
poetry install --with dev,simba,mcp,ag2,database,docs

bash


2.2 Consolidate Dependencies
Merge requirements from easyocr-env, venv, simba, and easyocr-mcp
Resolve version conflicts by using the most recent compatible versions
Create a single pyproject.toml with all necessary dependencies
Update the main pyproject.toml to include all required dependencies
2.3 Update Environment Configurations
Modify .kilocode/config/services.yaml to point to the unified environment
Update VS Code settings to use the new Poetry environment
Update MCP server configurations to use the unified environment
Phase 3: Migration Process (Week 3)
3.1 Migrate EasyOCR Functionality
# Install EasyOCR dependencies in unified environment
poetry add easyocr>=1.7.2 pillow>=8.0.0 numpy>=1.21.0 opencv-python>=4.5.0 pytesseract>=0.3.10
poetry add torch>=2.4.0 torchvision>=0.19.0 torchaudio>=2.4.0 sentence-transformers>=3.2.0

# Update easyocr-mcp to use unified environment
# Modify easyocr-mcp configuration to use Poetry environment

bash


3.2 Migrate Simba Functionality
Simba already uses Poetry, so it should integrate well with the unified environment
Update Simba's dependencies to use the shared environment
Test Simba functionality with unified environment
3.3 Migrate Development Tools
# Add development tools to unified environment
poetry add --group dev black>=25.1.0 flake8>=5.0.0 pytest>=7.0.0 isort>=6.0.0 mypy>=1.15.0

bash


Phase 4: Integration Updates (Week 4)
4.1 Update MCP Server Configurations
Modify all MCP servers to use the unified Poetry environment
Update environment variable references
Ensure all MCP servers can access required packages
Test each MCP server individually
4.2 Update VS Code Configuration
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
  "python.terminal.activateEnvironment": true,
  "python.linting.enabled": true,
  "python.formatting.provider": "black"
}

json


4.3 Update System Integration Points
Update .kilocode/config/services.yaml to reference the unified environment
Update any scripts that activate specific environments
Update documentation to reflect new environment structure
Phase 5: Validation and Testing (Week 5)
5.1 Create Validation Scripts
# validation_script.py
def validate_environment():
    """Validate that all required packages are available"""
    required_packages = [
        'easyocr', 'torch', 'langchain', 'faiss-cpu', 
        'sentence-transformers', 'fastapi', 'uvicorn',
        'psycopg2-binary', 'redis', 'pgvector'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing packages: {missing_packages}")
        return False
    return True

def test_integrations():
    """Test all integration points"""
    tests = [
        ("EasyOCR", lambda: test_easyocr()),
        ("Simba", lambda: test_simba()),
        ("MCP Servers", lambda: test_mcp_servers()),
        ("Database", lambda: test_database()),
        ("Vector System", lambda: test_vector_system())
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            results[name] = f"Failed: {str(e)}"
    
    return results

python



5.2 Run Comprehensive Tests
Test all MCP servers
Test database connections
Test OCR functionality
Test RAG system
Test memory system
Test all integration points
5.3 Performance Validation
Measure startup times
Test memory usage
Verify no performance regression
Phase 6: Cleanup and Documentation (Week 6)
6.1 Remove Duplicate Environments
# Only after successful validation
Remove-Item -Path "C:\_1mybizz\paddle-plugin\easyocr-env" -Recurse -Force
Remove-Item -Path "C:\_1mybizz\paddle-plugin\venv" -Recurse -Force

bash


6.2 Update Documentation
Create new environment setup guide
Update integration documentation
Document troubleshooting procedures
Create dependency matrix documentation
6.3 Create Maintenance Scripts
Environment activation script
Dependency update script
Validation script
Critical Success Factors
Backup everything before starting
Test incrementally - migrate one component at a time
Validate after each change - ensure no functionality is broken
Document everything - create clear migration records
Have a rollback plan - be able to restore original state if needed
Risk Mitigation
Data Loss: Complete backups before any changes
Downtime: Schedule migration during maintenance window
Compatibility Issues: Test all integrations thoroughly
Performance Issues: Benchmark before and after migration
Dependency Conflicts: Resolve conflicts systematically
Success Metrics
Functional Metrics
All MCP servers operational
Database connections working
OCR functionality operational
RAG system functional
Memory system operational
No import errors in any component
Performance Metrics
No degradation in startup times
Memory usage within acceptable limits
Response times maintained or improved
No performance bottlenecks introduced
Maintenance Metrics
Single environment to manage
Consistent dependency management
Clear integration points
Comprehensive documentation
Easy backup and restoration procedures
Timeline
Week 1: Assessment and Planning
Week 2: Environment Consolidation
Week 3: Migration Process
Week 4: Integration Updates
Week 5: Validation and Testing
Week 6: Cleanup and Documentation
Dependencies
Poetry must be installed and configured
All source code must be backed up
System must be available during migration windows
Documentation must be kept up-to-date throughout the process
Monitoring and Reporting
Daily progress reports
Issue tracking and resolution
Performance monitoring
Validation test results
Rollback readiness assessment
Post-Migration Review
After completing the migration, conduct a thorough review to ensure:

All functionality is preserved
Performance meets expectations
Documentation is complete and accurate
Maintenance procedures are documented
Team is trained on new environment procedures
Appendices
Appendix A: Current Environment Details
Detailed breakdown of each environment
Package lists and versions
Configuration files
Integration points
Appendix B: Backup and Recovery Procedures
Step-by-step backup procedures
Recovery instructions
Validation steps
Emergency contact information
Appendix C: Troubleshooting Guide
Common issues and solutions
Error message references
Debug procedures
Performance optimization tips
Appendix D: Reference Materials
Links to relevant documentation
Configuration examples
Best practices
External resources </content>