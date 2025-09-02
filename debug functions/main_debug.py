#!/usr/bin/env python3
"""
Debug wrapper for HappyTag that keeps console open
"""
import sys
import traceback

def main():
    try:
        print("Starting HappyTag Debug...")
        print("Python version:", sys.version)
        print("Python executable:", sys.executable)
        print("Working directory:", sys.path[0] if sys.path else "Unknown")
        print("=" * 50)
        
        # Import and run the main application
        from main import main as run_main
        print("Imported main module successfully")
        
        print("Starting application...")
        run_main()
        
    except Exception as e:
        print("\n" + "=" * 50)
        print("ERROR OCCURRED:")
        print("=" * 50)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        
    finally:
        print("\n" + "=" * 50)
        print("Application finished. Press Enter to close console...")
        input()  # Keep console open until user presses Enter

if __name__ == "__main__":
    main()
