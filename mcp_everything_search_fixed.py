#!/usr/bin/env python
"""
Fixed MCP Everything Search Server launcher.
This script provides a workaround for the PyWin32 import issues.
"""

import os
import sys
import site
import ctypes

def setup_environment():
    """Set up the environment for PyWin32 and MCP"""
    user_site = site.getusersitepackages()
    if user_site:
        # Add user site-packages to Python path
        if user_site not in sys.path:
            sys.path.insert(0, user_site)
            print(f"Added user site-packages to path: {user_site}")
        
        # Add DLL directories
        pywin32_system32 = os.path.join(user_site, 'pywin32_system32')
        if os.path.exists(pywin32_system32):
            os.add_dll_directory(pywin32_system32)
            print(f"Added DLL directory: {pywin32_system32}")
        
        os.add_dll_directory(user_site)
        print(f"Added DLL directory: {user_site}")

def test_pywin32_basic():
    """Test basic PyWin32 functionality"""
    try:
        import pywintypes
        import pythoncom
        print("SUCCESS: Basic PyWin32 modules imported")
        return True
    except ImportError as e:
        print(f"ERROR: Basic PyWin32 import failed: {e}")
        return False

def test_everything_sdk():
    """Test Everything SDK"""
    try:
        import ctypes
        everything_sdk_path = os.environ.get('EVERYTHING_SDK_PATH')
        if everything_sdk_path:
            ctypes.WinDLL(everything_sdk_path)
            print(f"SUCCESS: Everything SDK loaded from: {everything_sdk_path}")
            return True
        else:
            print("ERROR: EVERYTHING_SDK_PATH not set")
            return False
    except Exception as e:
        print(f"ERROR: Everything SDK test failed: {e}")
        return False

def create_win32_stubs():
    """Create stubs for win32 modules to avoid import errors"""
    user_site = site.getusersitepackages()
    if not user_site:
        return
    
    # Create win32api stub
    win32api_stub = os.path.join(user_site, 'win32api.py')
    if not os.path.exists(win32api_stub):
        stub_content = '''# Stub for win32api to avoid import errors
import ctypes
import os

# Add DLL directories
if hasattr(os, 'add_dll_directory'):
    user_site = os.path.dirname(os.path.abspath(__file__))
    os.add_dll_directory(user_site)
    pywin32_system32 = os.path.join(os.path.dirname(user_site), 'pywin32_system32')
    if os.path.exists(pywin32_system32):
        os.add_dll_directory(pywin32_system32)

# Try to import the real win32api
try:
    from win32 import win32api
except ImportError:
    # Create a minimal stub
    class Win32APIStub:
        def __getattr__(self, name):
            raise NotImplementedError(f"win32api.{name} is not implemented in stub")
    
    win32api = Win32APIStub()
'''
        with open(win32api_stub, 'w') as f:
            f.write(stub_content)
        print(f"Created win32api stub at: {win32api_stub}")
    
    # Create win32con stub
    win32con_stub = os.path.join(user_site, 'win32con.py')
    if not os.path.exists(win32con_stub):
        stub_content = '''# Stub for win32con to avoid import errors
# Common Windows constants
try:
    from win32 import win32con
except ImportError:
    # Define some common constants
    class Win32Con:
        # File attributes
        FILE_ATTRIBUTE_READONLY = 0x00000001
        FILE_ATTRIBUTE_HIDDEN = 0x00000002
        FILE_ATTRIBUTE_SYSTEM = 0x00000004
        FILE_ATTRIBUTE_DIRECTORY = 0x00000010
        FILE_ATTRIBUTE_ARCHIVE = 0x00000020
        FILE_ATTRIBUTE_NORMAL = 0x00000080
        
        # Window styles
        WS_OVERLAPPED = 0x00000000
        WS_POPUP = 0x80000000
        WS_CHILD = 0x40000000
        WS_MINIMIZE = 0x20000000
        WS_VISIBLE = 0x10000000
        WS_DISABLED = 0x08000000
        WS_CLIPSIBLINGS = 0x04000000
        WS_CLIPCHILDREN = 0x02000000
        WS_MAXIMIZE = 0x01000000
        WS_CAPTION = 0x00C00000
        WS_BORDER = 0x00800000
        WS_DLGFRAME = 0x00400000
        WS_VSCROLL = 0x00200000
        WS_HSCROLL = 0x00100000
        WS_SYSMENU = 0x00080000
        WS_THICKFRAME = 0x00040000
        WS_GROUP = 0x00020000
        WS_TABSTOP = 0x00010000
        
        # Message constants
        WM_NULL = 0x0000
        WM_CREATE = 0x0001
        WM_DESTROY = 0x0002
        WM_MOVE = 0x0003
        WM_SIZE = 0x0005
        WM_ACTIVATE = 0x0006
        WM_SETFOCUS = 0x0007
        WM_KILLFOCUS = 0x0008
        WM_ENABLE = 0x000A
        WM_SETREDRAW = 0x000B
        WM_SETTEXT = 0x000C
        WM_GETTEXT = 0x000D
        WM_GETTEXTLENGTH = 0x000E
        WM_PAINT = 0x000F
        WM_CLOSE = 0x0010
        WM_QUERYENDSESSION = 0x0011
        WM_QUIT = 0x0012
        WM_QUERYOPEN = 0x0013
        WM_ERASEBKGND = 0x0014
        WM_SYSCOLORCHANGE = 0x0015
        WM_ENDSESSION = 0x0016
        WM_SYSTEMERROR = 0x0017
        WM_SHOWWINDOW = 0x0018
        WM_CTLCOLOR = 0x0019
        WM_WININICHANGE = 0x001A
        WM_DEVMODECHANGE = 0x001B
        WM_ACTIVATEAPP = 0x001C
        WM_FONTCHANGE = 0x001D
        WM_TIMECHANGE = 0x001E
        WM_CANCELMODE = 0x001F
        WM_SETCURSOR = 0x0020
        WM_MOUSEACTIVATE = 0x0021
        WM_CHILDACTIVATE = 0x0022
        WM_QUEUESYNC = 0x0023
        WM_GETMINMAXINFO = 0x0024
        WM_PAINTICON = 0x0026
        WM_ICONERASEBKGND = 0x0027
        WM_NEXTDLGCTL = 0x0028
        WM_SPOOLERSTATUS = 0x002A
        WM_DRAWITEM = 0x002B
        WM_MEASUREITEM = 0x002C
        WM_DELETEITEM = 0x002D
        WM_VKEYTOITEM = 0x002E
        WM_CHARTOITEM = 0x002F
        WM_SETFONT = 0x0030
        WM_GETFONT = 0x0031
        WM_SETHOTKEY = 0x0032
        WM_GETHOTKEY = 0x0033
        WM_QUERYDRAGICON = 0x0037
        WM_COMPAREITEM = 0x0039
        WM_GETOBJECT = 0x003D
        WM_COMPACTING = 0x0041
        WM_COMMNOTIFY = 0x0044
        WM_WINDOWPOSCHANGING = 0x0046
        WM_WINDOWPOSCHANGED = 0x0047
        WM_POWER = 0x0048
        WM_COPYDATA = 0x004A
        WM_CANCELJOURNAL = 0x004B
        WM_NOTIFY = 0x004E
        WM_INPUTLANGCHANGEREQUEST = 0x0050
        WM_INPUTLANGCHANGE = 0x0051
        WM_TCARD = 0x0052
        WM_HELP = 0x0053
        WM_USERCHANGED = 0x0054
        WM_NOTIFYFORMAT = 0x0055
        WM_CONTEXTMENU = 0x007B
        WM_STYLECHANGING = 0x007C
        WM_STYLECHANGED = 0x007D
        WM_DISPLAYCHANGE = 0x007E
        WM_SETICON = 0x0080
        WM_NCCREATE = 0x0081
        WM_NCDESTROY = 0x0082
        WM_NCCALCSIZE = 0x0083
        WM_NCHITTEST = 0x0084
        WM_NCPAINT = 0x0085
        WM_NCACTIVATE = 0x0086
        WM_GETDLGCODE = 0x0087
        WM_SYNCPAINT = 0x0088
        WM_NCMOUSEMOVE = 0x00A0
        WM_NCLBUTTONDOWN = 0x00A1
        WM_NCLBUTTONUP = 0x00A2
        WM_NCLBUTTONDBLCLK = 0x00A3
        WM_NCRBUTTONDOWN = 0x00A4
        WM_NCRBUTTONUP = 0x00A5
        WM_NCRBUTTONDBLCLK = 0x00A6
        WM_NCMBUTTONDOWN = 0x00A7
        WM_NCMBUTTONUP = 0x00A8
        WM_NCMBUTTONDBLCLK = 0x00A9
        WM_KEYFIRST = 0x0100
        WM_KEYDOWN = 0x0100
        WM_KEYUP = 0x0101
        WM_CHAR = 0x0102
        WM_DEADCHAR = 0x0103
        WM_SYSKEYDOWN = 0x0104
        WM_SYSKEYUP = 0x0105
        WM_SYSCHAR = 0x0106
        WM_SYSDEADCHAR = 0x0107
        WM_KEYLAST = 0x0108
        WM_IME_STARTCOMPOSITION = 0x010D
        WM_IME_ENDCOMPOSITION = 0x010E
        WM_IME_COMPOSITION = 0x010F
        WM_IME_SETCONTEXT = 0x0281
        WM_IME_NOTIFY = 0x0282
        WM_IME_CONTROL = 0x0283
        WM_IME_COMPOSITIONFULL = 0x0284
        WM_IME_SELECT = 0x0285
        WM_IME_CHAR = 0x0286
        WM_IME_REQUESTRECONVERT = 0x0288
        WM_IME_KEYDOWN = 0x0290
        WM_IME_KEYUP = 0x0291
        WM_MOUSEFIRST = 0x0200
        WM_MOUSEMOVE = 0x0200
        WM_LBUTTONDOWN = 0x0201
        WM_LBUTTONUP = 0x0202
        WM_LBUTTONDBLCLK = 0x0203
        WM_RBUTTONDOWN = 0x0204
        WM_RBUTTONUP = 0x0205
        WM_RBUTTONDBLCLK = 0x0206
        WM_MBUTTONDOWN = 0x0207
        WM_MBUTTONUP = 0x0208
        WM_MBUTTONDBLCLK = 0x0209
        WM_MOUSEWHEEL = 0x020A
        WM_MOUSELAST = 0x020A
        WM_PARENTNOTIFY = 0x0210
        WM_ENTERMENULOOP = 0x0211
        WM_EXITMENULOOP = 0x0212
        WM_NEXTMENU = 0x0213
        WM_SIZING = 0x0214
        WM_CAPTURECHANGED = 0x0215
        WM_MOVING = 0x0216
        WM_POWERBROADCAST = 0x0218
        WM_DEVICECHANGE = 0x0219
        WM_MDICREATE = 0x0220
        WM_MDIDESTROY = 0x0221
        WM_MDIACTIVATE = 0x0222
        WM_MDIRESTORE = 0x0223
        WM_MDINEXT = 0x0224
        WM_MDIMAXIMIZE = 0x0225
        WM_MDITILE = 0x0226
        WM_MDICASCADE = 0x0227
        WM_MDIICONARRANGE = 0x0228
        WM_MDIGETACTIVE = 0x0229
        WM_MDISETMENU = 0x0230
        WM_ENTERSIZEMOVE = 0x0231
        WM_EXITSIZEMOVE = 0x0232
        WM_DROPFILES = 0x0233
        WM_MDIREFRESHMENU = 0x0234
        WM_IME_SETOPENSTATUS = 0x0235
        WM_IME_NOTIFY = 0x0282
        WM_IME_CONTROL = 0x0283
        WM_IME_COMPOSITIONFULL = 0x0284
        WM_IME_SELECT = 0x0285
        WM_IME_CHAR = 0x0286
        WM_IME_REQUESTRECONVERT = 0x0288
        WM_IME_KEYDOWN = 0x0290
        WM_IME_KEYUP = 0x0291
        WM_MOUSEHOVER = 0x02A0
        WM_MOUSELEAVE = 0x02A1
        WM_CUT = 0x0300
        WM_COPY = 0x0301
        WM_PASTE = 0x0302
        WM_CLEAR = 0x0303
        WM_UNDO = 0x0304
        WM_RENDERFORMAT = 0x0305
        WM_RENDERALLFORMATS = 0x0306
        WM_DESTROYCLIPBOARD = 0x0307
        WM_DRAWCLIPBOARD = 0x0308
        WM_PAINTCLIPBOARD = 0x0309
        WM_VSCROLLCLIPBOARD = 0x030A
        WM_SIZECLIPBOARD = 0x030B
        WM_ASKCBFORMATNAME = 0x030C
        WM_CHANGECBCHAIN = 0x030D
        WM_HSCROLLCLIPBOARD = 0x030E
        WM_QUERYNEWPALETTE = 0x030F
        WM_PALETTEISCHANGING = 0x0310
        WM_PALETTECHANGED = 0x0311
        WM_HOTKEY = 0x0312
        WM_PRINT = 0x0317
        WM_PRINTCLIENT = 0x0318
        WM_HANDHELDFIRST = 0x0358
        WM_HANDHELDLAST = 0x035F
        WM_PENWINFIRST = 0x0380
        WM_PENWINLAST = 0x038F
        WM_APP = 0x8000
        WM_USER = 0x0400
        
    win32con = Win32Con()
'''
        with open(win32con_stub, 'w') as f:
            f.write(stub_content)
        print(f"Created win32con stub at: {win32con_stub}")
    
    # Create other common win32 stubs
    common_modules = ['win32gui', 'win32event', 'win32process', 'win32service', 'win32job']
    for module in common_modules:
        module_stub = os.path.join(user_site, f'{module}.py')
        if not os.path.exists(module_stub):
            # Create stub content using string formatting
            class_name = module.title().replace('32', '32')
            stub_content = f"""# Stub for {module} to avoid import errors
try:
    from win32 import {module}
except ImportError:
    # Create a minimal stub
    class {class_name}Stub:
        def __getattr__(self, attr_name):
            raise NotImplementedError(f"{module}." + attr_name + " is not implemented in stub")
    
    {module} = {class_name}Stub()
"""
            with open(module_stub, 'w') as f:
                f.write(stub_content)
            print(f"Created {module} stub at: {module_stub}")

def run_mcp_server():
    """Run the MCP Everything Search Server"""
    try:
        # Import the MCP server
        from mcp_server_everything_search import main
        print("Starting MCP Everything Search Server...")
        main()
        return True
    except ImportError as e:
        print(f"ERROR: Failed to import MCP server: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Running MCP server failed: {e}")
        return False

def main():
    """Main function"""
    print("=== MCP Everything Search Server (Fixed Version) ===")
    
    # Set up environment
    setup_environment()
    
    # Test basic PyWin32
    if not test_pywin32_basic():
        print("ERROR: Basic PyWin32 functionality failed")
        return 1
    
    # Test Everything SDK
    if not test_everything_sdk():
        print("ERROR: Everything SDK test failed")
        return 1
    
    # Create win32 stubs
    create_win32_stubs()
    
    # Try to run MCP server
    if run_mcp_server():
        print("SUCCESS: MCP server started successfully")
        return 0
    else:
        print("ERROR: MCP server failed to start")
        return 1

if __name__ == "__main__":
    sys.exit(main())