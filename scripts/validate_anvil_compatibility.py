import os
import sys
import subprocess
import ast
import re

def check_python_syntax():
    """Check Python syntax for all Python files"""
    print("Checking Python syntax...")
    result = subprocess.run(['python', '-m', 'py_compile', 'src/'], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Python syntax error: {result.stderr}")
        return False
    print("✓ Python syntax OK")
    return True

def check_anvil_compatibility():
    """Check for Python 3.7x compatibility using Python 3.8"""
    print("Checking Python 3.7x compatibility...")
    
    # Check for Python 3.7+ specific features
    issues = []
    
    # Check for f-strings (Python 3.6+)
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Check for f-strings
                    if 'f"' in content or "f'" in content:
                        issues.append(f"F-string found in {file_path} (Python 3.6+)")
                        
                    # Check for walrus operator (Python 3.8+)
                    if ':=' in content:
                        issues.append(f"Walrus operator found in {file_path} (Python 3.8+)")
                        
                    # Check for positional-only parameters (Python 3.8+)
                    if re.search(r'def\s+\w+\s*\([^)]*\)\s*->', content):
                        issues.append(f"Type hints found in {file_path} (check Python 3.7+ compatibility)")
                        
                except Exception as e:
                    issues.append(f"Error reading {file_path}: {e}")
    
    if issues:
        print("⚠️ Compatibility issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✓ Python 3.7x compatibility OK")
        return True

def check_dependencies():
    """Check dependencies for Python 3.7+ compatibility"""
    print("Checking dependencies...")
    
    if not os.path.exists('requirements.txt'):
        print("⚠️ requirements.txt not found")
        return False
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        # Check for Python 3.8+ specific packages
        python38_packages = ['pydantic>=2.0', 'fastapi>=0.100']
        for package in python38_packages:
            if package in requirements:
                print(f"⚠️ Package may require Python 3.8+: {package}")
        
        print("✓ Dependencies checked")
        return True
    except Exception as e:
        print(f"Error checking dependencies: {e}")
        return False

def check_anvil_yaml():
    """Check anvil.yaml configuration"""
    print("Checking anvil.yaml...")
    
    anvil_yaml_path = 'anvil.yaml'
    if not os.path.exists(anvil_yaml_path):
        print("⚠️ anvil.yaml not found")
        return True  # Not critical for validation
    
    try:
        with open(anvil_yaml_path, 'r') as f:
            content = f.read()
        
        # Basic validation
        if 'app' not in content.lower():
            print("⚠️ anvil.yaml may be missing app configuration")
        
        print("✓ anvil.yaml structure OK")
        return True
    except Exception as e:
        print(f"Error checking anvil.yaml: {e}")
        return False

def main():
    print("Starting Anvil compatibility validation...")
    
    checks = [
        check_python_syntax,
        check_anvil_compatibility,
        check_dependencies,
        check_anvil_yaml
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
        print()  # Add spacing
    
    if all_passed:
        print("✓ All compatibility checks passed!")
        sys.exit(0)
    else:
        print("✗ Some compatibility checks failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()