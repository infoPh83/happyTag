#!/usr/bin/env python3
"""
Debug wrapper for main.py - keeps console open to see error messages
"""

import sys
import traceback
from main import *

def debug_main():
    """Main function with debug output and console pause"""
    try:
        print("=== HappyTag Debug Mode ===")
        print("Starting application...")
        
        # Create the application
        print("Creating QApplication...")
        app = QApplication(sys.argv)
        
        print("Creating MainWindow...")
        window = MainWindow()
        
        print("Showing window...")
        window.show()
        
        print("Application started successfully!")
        print("Starting event loop...")
        
        # Run the application
        result = app.exec_()
        
        print(f"Application exited with code: {result}")
        return result
        
    except Exception as e:
        print(f"\n=== ERROR OCCURRED ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"\n=== FULL TRACEBACK ===")
        traceback.print_exc()
        print(f"\n=== END ERROR INFO ===")
        
        return 1
    
    finally:
        print("\n=== DEBUG SESSION COMPLETE ===")
        print("Press Enter to close this window...")
        try:
            input()
        except:
            # In case input() fails, wait for a bit
            import time
            time.sleep(5)

if __name__ == '__main__':
    debug_main()
