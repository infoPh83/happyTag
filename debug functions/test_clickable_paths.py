#!/usr/bin/env python3
"""
Test script to verify that the clickable paths functionality works correctly.
"""

import sys
import os
sys.path.append('.')

from PyQt5.QtWidgets import QApplication
from utilities.settings_dialog import SettingsDialog

def test_clickable_paths():
    """Test the clickable paths functionality"""
    app = QApplication(sys.argv)
    
    # Create the settings dialog
    dialog = SettingsDialog()
    
    print("Testing clickable paths functionality...")
    
    # Check if the widgets exist and are properly configured
    if hasattr(dialog, 'settingsPathLabel'):
        print(f"✓ settingsPathLabel widget found")
        print(f"  Text: {dialog.settingsPathLabel.text()}")
        print(f"  Tooltip: {dialog.settingsPathLabel.toolTip()}")
        print(f"  Cursor: {dialog.settingsPathLabel.cursor()}")
        print(f"  StyleSheet: {dialog.settingsPathLabel.styleSheet()}")
    else:
        print("✗ settingsPathLabel widget not found")
    
    if hasattr(dialog, 'logFile_path'):
        print(f"✓ logFile_path widget found")
        print(f"  Text: {dialog.logFile_path.text()}")
        print(f"  Tooltip: {dialog.logFile_path.toolTip()}")
        print(f"  Cursor: {dialog.logFile_path.cursor()}")
        print(f"  StyleSheet: {dialog.logFile_path.styleSheet()}")
    else:
        print("✗ logFile_path widget not found")
    
    # Test the folder opening methods (without actually opening)
    print(f"\nTesting folder opening methods...")
    
    # Test settings folder path
    try:
        from utilities.settings_dialog import get_settings_file_path
        settings_path = get_settings_file_path()
        settings_folder = settings_path.parent
        print(f"✓ Settings folder path: {settings_folder}")
        print(f"  Exists: {settings_folder.exists()}")
    except Exception as e:
        print(f"✗ Error getting settings folder: {e}")
    
    # Test log folder (if set)
    if dialog.log_folder_path:
        print(f"✓ Log folder path: {dialog.log_folder_path}")
        print(f"  Exists: {os.path.exists(dialog.log_folder_path)}")
    else:
        print("ℹ No log folder path set")
    
    print(f"\nTest completed!")
    app.quit()

if __name__ == "__main__":
    test_clickable_paths()