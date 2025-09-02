#!/usr/bin/env python3

import os
import subprocess
import time

def refresh_finder_view():
    """Force Finder to refresh the current view"""
    try:
        # Use AppleScript to refresh Finder
        script = '''
        tell application "Finder"
            if exists front window then
                set current view of front window to list view
                delay 0.1
                set current view of front window to icon view
            end if
        end tell
        '''
        subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
        print("Finder view refreshed")
    except Exception as e:
        print(f"Could not refresh Finder view: {e}")

def open_file_in_finder(file_path):
    """Open the file location in Finder and select the file"""
    try:
        subprocess.run(['open', '-R', file_path], capture_output=True, timeout=5)
        time.sleep(0.5)  # Give Finder time to open
        refresh_finder_view()
        print(f"Opened {os.path.basename(file_path)} in Finder")
    except Exception as e:
        print(f"Could not open in Finder: {e}")

if __name__ == "__main__":
    # Test file
    test_file = "test_finder_tags_demo.jpg"
    
    if os.path.exists(test_file):
        print(f"Opening {test_file} in Finder...")
        open_file_in_finder(os.path.abspath(test_file))
        print("\n🔍 Check if you can see the colored tags next to the filename!")
        print("The tags should be: VisibleInFinder, Test, macOS, Tags")
    else:
        print(f"Test file {test_file} not found")
