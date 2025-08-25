#!/usr/bin/env python
"""
Script to fix PyWin32 environment for MCP Everything Search Server.
This script sets up the environment properly so that all PyWin32 modules work correctly.
"""

import os
import sys
import site
import shutil
import ctypes

def add_dll_directory():
    """Add DLL directories to Windows search path"""
    user_site = site.getusersitepackages()
    if user_site:
        # Add pywin32_system32 directory to DLL search path
        pywin32_system32 = os.path.join(user_site, 'pywin32_system32')
        if os.path.exists(pywin32_system32):
            os.add_dll_directory(pywin32_system32)
            print(f"Added DLL directory: {pywin32_system32}")
        
        # Add main site-packages directory to DLL search path
        os.add_dll_directory(user_site)
        print(f"Added DLL directory: {user_site}")

def setup_pywin32_modules():
    """Set up PyWin32 modules properly"""
    user_site = site.getusersitepackages()
    if not user_site:
        print("ERROR: Could not find user site-packages directory")
        return False
    
    # Copy DLLs to main site-packages directory
    pywin32_system32 = os.path.join(user_site, 'pywin32_system32')
    if os.path.exists(pywin32_system32):
        # Copy pywintypes313.dll
        src_pywintypes = os.path.join(pywin32_system32, 'pywintypes313.dll')
        dst_pywintypes = os.path.join(user_site, 'pywintypes313.dll')
        if os.path.exists(src_pywintypes) and not os.path.exists(dst_pywintypes):
            shutil.copy2(src_pywintypes, dst_pywintypes)
            print(f"Copied {src_pywintypes} to {dst_pywintypes}")
        
        # Copy pythoncom313.dll
        src_pythoncom = os.path.join(pywin32_system32, 'pythoncom313.dll')
        dst_pythoncom = os.path.join(user_site, 'pythoncom313.dll')
        if os.path.exists(src_pythoncom) and not os.path.exists(dst_pythoncom):
            shutil.copy2(src_pythoncom, dst_pythoncom)
            print(f"Copied {src_pythoncom} to {dst_pythoncom}")
    
    # Create pywintypes.py if it doesn't exist
    pywintypes_py = os.path.join(user_site, 'pywintypes.py')
    if not os.path.exists(pywintypes_py):
        create_pywintypes_py(user_site)
        print(f"Created {pywintypes_py}")
    
    return True

def create_pywintypes_py(user_site):
    """Create a pywintypes.py file that can load the DLL"""
    pywintypes_py = os.path.join(user_site, 'pywintypes.py')
    content = '''import ctypes
import os

# Load the pywintypes DLL
try:
    # Try to load from the current directory first
    if hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(os.path.dirname(os.path.abspath(__file__)))
    
    # Load the pywintypes DLL
    _pywintypes = ctypes.CDLL('pywintypes313.dll')
    
    # Define the __import_pywin32_system_module__ function
    def __import_pywin32_system_module(module_name, globals_dict):
        """Import a pywin32 system module"""
        if module_name == 'pythoncom':
            import pythoncom
            globals_dict.update(pythoncom.__dict__)
        elif module_name == 'win32api':
            import win32api
            globals_dict.update(win32api.__dict__)
        # Add other modules as needed
    
    # Add the function to the module
    globals()['__import_pywin32_system_module'] = __import_pywin32_system_module
    
except Exception as e:
    # If loading fails, raise an informative error
    raise ImportError(f"Failed to load pywintypes313.dll: {e}")
'''
    with open(pywintypes_py, 'w') as f:
        f.write(content)

def test_pywin32_modules():
    """Test if PyWin32 modules can be imported"""
    try:
        import pywintypes
        import pythoncom
        import win32api
        print("SUCCESS: All PyWin32 modules imported successfully")
        return True
    except ImportError as e:
        print(f"ERROR: Failed to import PyWin32 modules: {e}")
        return False

def test_mcp_import():
    """Test if MCP modules can be imported"""
    try:
        import mcp
        print("SUCCESS: MCP module imported successfully")
        return True
    except ImportError as e:
        print(f"ERROR: Failed to import MCP module: {e}")
        return False

def test_everything_sdk():
    """Test if Everything SDK can be loaded"""
    try:
        import ctypes
        everything_sdk_path = os.environ.get('EVERYTHING_SDK_PATH')
        if everything_sdk_path:
            ctypes.WinDLL(everything_sdk_path)
            print(f"SUCCESS: Everything SDK loaded successfully from: {everything_sdk_path}")
            return True
        else:
            print("ERROR: EVERYTHING_SDK_PATH environment variable not set")
            return False
    except Exception as e:
        print(f"ERROR: Error loading Everything SDK: {e}")
        return False

def main():
    """Main function"""
    print("=== PyWin32 Environment Fix Script ===")
    
    # Add DLL directories
    add_dll_directory()
    
    # Set up PyWin32 modules
    if not setup_pywin32_modules():
        print("ERROR: Failed to set up PyWin32 modules")
        return 1
    
    # Add user site-packages to Python path
    user_site = site.getusersitepackages()
    if user_site and user_site not in sys.path:
        sys.path.insert(0, user_site)
        print(f"Added user site-packages to path: {user_site}")
    
    # Test PyWin32 modules
    if not test_pywin32_modules():
        print("ERROR: PyWin32 modules are not working")
        return 1
    
    # Test MCP import
    if not test_mcp_import():
        print("ERROR: MCP module is not working")
        return 1
    
    # Test Everything SDK
    if not test_everything_sdk():
        print("ERROR: Everything SDK is not working")
        return 1
    
    print("SUCCESS: All tests passed! Environment is ready.")
    return 0

if __name__ == "__main__":
    sys.exit(main())