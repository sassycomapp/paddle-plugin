#!/usr/bin/env python3
"""
Simple health check for AG2 orchestration system
"""
import sys
import os
from pathlib import Path

def check_python_environment():
    """Check if Python environment is properly set up."""
    print("🔍 Checking Python environment...")
    
    try:
        from utils.environment import setup_environment
        print("✅ Environment utility available")
        
        # Setup environment
        result = setup_environment()
        env_info = result['environment_info']
        validation_result = result['validation']
        
        print(f"🔍 Environment: {env_info['environment_type']}")
        print(f"🔍 Virtual: {env_info['is_virtual']}")
        print(f"🔍 Python: {env_info['python_version']}")
        
        if validation_result['status'] != 'pass':
            print("❌ Environment validation failed:")
            for issue in validation_result['critical_issues']:
                print(f"   {issue}")
            return False
        
        return True
        
    except ImportError:
        print("❌ Environment utility not found, using basic checks")
        # Fallback to basic checks
        try:
            import pytest
            print("✅ pytest is available")
        except ImportError:
            print("❌ pytest not found - run setup_python_env.bat")
            return False
        
        try:
            import asyncio
            print("✅ asyncio is available")
        except ImportError:
            print("❌ asyncio not found")
            return False
        
        return True

def check_test_structure():
    """Check if test structure is complete."""
    print("\n🔍 Checking test structure...")
    
    test_root = Path("Test Bank/System Tests/AG2_Orchestration_Tests")
    
    required_files = [
        "quick_test.py",
        "unit/test_agents.py",
        "integration/test_orchestrator_integration.py",
        "pytest.ini",
        "requirements.txt"
    ]
    
    for file_path in required_files:
        full_path = test_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} not found")
            return False
    
    return True

def check_source_files():
    """Check if source files are available."""
    print("\n🔍 Checking source files...")
    
    src_files = [
        "src/orchestration/ag2_pure.py",
        "src/orchestration/ag2_orchestrator.py",
        "Test Bank/System Tests/AG2_Orchestration_Tests/src/ag2_pure.py"
    ]
    
    for file_path in src_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} not found")
            return False
    
    return True

def run_basic_import_test():
    """Test basic imports work."""
    print("\n🔍 Testing basic imports...")
    
    try:
        # Add test src to path
        test_src = Path("Test Bank/System Tests/AG2_Orchestration_Tests/src")
        sys.path.insert(0, str(test_src))
        
        from ag2_pure import AG2Agent, AG2Orchestrator, MockMemory, MockRAG, MockSearch
        print("✅ AG2 Pure imports successful")
        
        # Test basic initialization
        agent = AG2Agent("test", "test-role", ["rag"])
        orchestrator = AG2Orchestrator()
        print("✅ Basic initialization successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def main():
    """Run all health checks."""
    print("=" * 50)
    print("AG2 Orchestration System Health Check")
    print("=" * 50)
    
    checks = [
        check_python_environment,
        check_test_structure,
        check_source_files,
        run_basic_import_test
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All health checks passed!")
        print("The AG2 orchestration system is ready for testing.")
        return 0
    else:
        print("❌ Some health checks failed.")
        print("Please run setup_python_env.bat and check the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
