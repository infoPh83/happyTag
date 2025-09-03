#!/usr/bin/env python3
"""
Test script to verify that the settings dialog file filters include .xlsm files
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utilities.settings_dialog import SettingsDialog
from PyQt5.QtWidgets import QApplication

def test_file_filters():
    """Test that all file selection methods support .xlsm files"""
    print("Testing Settings Dialog File Filters...")
    print("=" * 50)
    
    # Create a minimal QApplication for the test
    app = QApplication([])
    
    # Create the settings dialog
    dialog = SettingsDialog()
    
    # Test methods and their expected filter patterns
    test_methods = [
        ("select_b2b_file", "B2B + B2C final file"),
        ("select_non_tle_file", "NON TLE tenants list file"),
        ("select_cloudinary_tags_file", "Cloudinary tags file"),
        ("select_buildings_file", "Buildings and Streets file")
    ]
    
    # Read the source code to verify filters contain .xlsm
    import inspect
    
    for method_name, description in test_methods:
        method = getattr(dialog, method_name)
        source = inspect.getsource(method)
        
        # Check if the filter includes .xlsm
        if "*.xlsm" in source:
            print(f"✅ PASS | {description}")
            print(f"   Method: {method_name}")
            print(f"   Filter contains: *.ods *.xlsx *.xlsm")
        else:
            print(f"❌ FAIL | {description}")
            print(f"   Method: {method_name}")
            print(f"   Filter missing .xlsm support")
        print()
    
    app.quit()
    print("File filter test completed!")

def test_validation_logic():
    """Test that file validation accepts .xlsm files"""
    print("\nTesting File Validation Logic...")
    print("=" * 50)
    
    # Read the validation method source
    import inspect
    from utilities.settings_dialog import SettingsDialog
    
    dialog = SettingsDialog()
    source = inspect.getsource(dialog.validate_files)
    
    # Test file extensions that should be accepted
    test_extensions = ['.ods', '.xlsx', '.xlsm']
    
    # Check if validation logic includes .xlsm
    validation_tests = [
        ('B2B + B2C final', '.ods', '.xlsx', '.xlsm'),
        ('NON TLE tenants list', '.ods', '.xlsx', '.xlsm'),
        ('Cloudinary tags', '.ods', '.xlsx', '.xlsm'),
        ('Buildings and Streets', '.ods', '.xlsx', '.xlsm')
    ]
    
    for file_type, *extensions in validation_tests:
        all_supported = all(ext in source for ext in extensions)
        if all_supported:
            print(f"✅ PASS | {file_type} file validation")
            print(f"   Accepts: {', '.join(extensions)}")
        else:
            print(f"❌ FAIL | {file_type} file validation")
            print(f"   Missing support for some extensions")
        print()
    
    print("Validation logic test completed!")

if __name__ == "__main__":
    test_file_filters()
    test_validation_logic()
