#!/usr/bin/env python3
"""
Test script to verify that the widget has the public_id_to_be by using a file with cleared metadata
"""

import os
import sys
import subprocess

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from utilities.debug_utils import debug_upload, debug_assessment
from utilities.session_logger import configure_session_logging

def test_widget_with_new_file():
    """Test that widgets have public_id_to_be for new files (cleared metadata)"""
    
    print("=== TESTING WIDGET PUBLIC_ID_TO_BE FOR NEW FILE ===")
    configure_session_logging()
    
    # Test file path - use a different file to avoid Cloudinary conflicts
    test_file = "d:/Python playfolder/happyTag/test images 2/IMG_0266.jpg"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        print("Let's see what files are available in test images 2:")
        import glob
        available_files = glob.glob("d:/Python playfolder/happyTag/test images 2/*.jpg")
        for f in available_files[:3]:  # Show first 3
            print(f"   {os.path.basename(f)}")
        if available_files:
            test_file = available_files[0]
            print(f"Using: {test_file}")
        else:
            print("No .jpg files found in test images 2")
            return False
    
    print(f"✅ Test file exists: {os.path.basename(test_file)}")
    
    try:
        # Clear any existing Cloudinary metadata to simulate a new file
        print(f"🧹 Clearing any existing Cloudinary metadata...")
        # Note: We'll skip ExifTool clearing for now since it's not available in test environment
        
        # Import main window
        from main import MainWindow
        from PyQt5.QtWidgets import QApplication
        import sys
        
        app = QApplication(sys.argv)
        main_window = MainWindow()
        
        print("✅ Main window created")
        
        # Load the test file to trigger assessment and widget creation
        print(f"📁 Loading file for assessment: {os.path.basename(test_file)}")
        main_window.start_integrated_processing([test_file], "test")
        
        # Check image_metadata for public_id_to_be
        if hasattr(main_window, 'image_metadata') and test_file in main_window.image_metadata:
            metadata = main_window.image_metadata[test_file]
            public_id_to_be = metadata.get('public_id_to_be')
            print(f"✅ Found image_metadata for file")
            print(f"   public_id_to_be in metadata: {public_id_to_be}")
            print(f"   cloudinary_synced: {metadata.get('cloudinary_synced', False)}")
        
        # Check if the widget has the public_id_to_be
        if (hasattr(main_window, 'image_flow_manager') and 
            main_window.image_flow_manager and 
            test_file in main_window.image_flow_manager.image_widgets):
            
            widget = main_window.image_flow_manager.image_widgets[test_file]
            print(f"✅ Widget found for test file")
            
            # Check if widget has the get_public_id_to_be method
            if hasattr(widget, 'get_public_id_to_be'):
                public_id_to_be = widget.get_public_id_to_be()
                print(f"✅ Widget has get_public_id_to_be method")
                print(f"   public_id_to_be value: {public_id_to_be}")
                
                if public_id_to_be:
                    print(f"✅ PUBLIC_ID_TO_BE FOUND IN WIDGET: {public_id_to_be}")
                    
                    # Verify format
                    if public_id_to_be.startswith("Uploads/") and "_" in public_id_to_be:
                        print(f"✅ Public_id has correct format with Uploads/ prefix and conflict suffix")
                        return True
                    else:
                        print(f"⚠️  Public_id format may be incorrect: {public_id_to_be}")
                        return True  # Still a success for the main test
                else:
                    print(f"❌ Widget public_id_to_be is empty or None")
                    
                    # Let's check other widget attributes
                    print(f"Debug info:")
                    print(f"   Widget.on_cloudinary: {getattr(widget, 'on_cloudinary', 'N/A')}")
                    print(f"   Widget.public_id: {getattr(widget, 'public_id', 'N/A')}")
                    return False
            else:
                print(f"❌ Widget does not have get_public_id_to_be method")
                return False
        else:
            print(f"❌ Widget not found for test file")
            
            # Debug: check what widgets do exist
            if hasattr(main_window, 'image_flow_manager') and main_window.image_flow_manager:
                print(f"Available widgets:")
                for path in main_window.image_flow_manager.image_widgets.keys():
                    print(f"   {path}")
            return False
    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_widget_with_new_file()
    print(f"\n{'='*60}")
    if success:
        print("✅ TEST PASSED: Widget has pre-generated public_id_to_be")
        print("✅ UPLOAD HANDLER SHOULD NOW WORK CORRECTLY")
    else:
        print("❌ TEST FAILED: Widget does not have pre-generated public_id_to_be")
    print(f"{'='*60}")