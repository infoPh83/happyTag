#!/usr/bin/env python3
"""
Console launcher that forces output visibility for PyInstaller executables
"""

import subprocess
import sys
import os

def run_with_console():
    """Run the executable and capture its output"""
    exe_path = os.path.join(os.path.dirname(__file__), "dist", "HappyTag.exe")
    
    if not os.path.exists(exe_path):
        print(f"ERROR: Executable not found at {exe_path}")
        input("Press Enter to exit...")
        return
    
    print("=== HappyTag Console Launcher ===")
    print(f"Launching: {exe_path}")
    print("=" * 50)
    
    try:
        # Run the executable and capture output
        process = subprocess.Popen(
            [exe_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Print output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        return_code = process.poll()
        print(f"\nApplication finished with exit code: {return_code}")
        
    except Exception as e:
        print(f"Error running executable: {e}")
    
    finally:
        print("\n" + "=" * 50)
        print("Press Enter to close this window...")
        input()

if __name__ == '__main__':
    run_with_console()
