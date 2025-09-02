#!/usr/bin/env python3
"""
Simple debug launcher that keeps console open
"""

import sys
import subprocess
import os

def main():
    print("=== HappyTag Debug Launcher ===")
    print("Starting application...")
    print()
    
    # Get the python executable path
    python_exe = r"D:/Python playfolder/happyTag/.venv/Scripts/python.exe"
    
    # Run the main application
    try:
        result = subprocess.run([python_exe, "main.py"], 
                              cwd=os.path.dirname(os.path.abspath(__file__)),
                              capture_output=False,  # Let output show in console
                              text=True)
        
        print(f"\nApplication finished with exit code: {result.returncode}")
        
    except Exception as e:
        print(f"Error running application: {e}")
    
    print("\nPress Enter to close this window...")
    input()

if __name__ == '__main__':
    main()
