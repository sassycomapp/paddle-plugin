import ctypes
import os

print('Testing Everything SDK loading...')
try:
    everything_sdk_path = os.environ.get('EVERYTHING_SDK_PATH')
    if everything_sdk_path:
        ctypes.WinDLL(everything_sdk_path)
        print('Everything SDK loaded successfully!')
    else:
        print('EVERYTHING_SDK_PATH environment variable not set')
except Exception as e:
    print(f'Error loading Everything SDK: {e}')