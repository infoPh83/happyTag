#!/usr/bin/env python3
"""
Direct test of upload handler widget access
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from utilities.debug_utils import debug_upload
from utilities.session_logger import configure_session_logging

def test_upload_handler_widget_access():
    """Test the upload handler's widget access directly"""
    
    print("=== TESTING UPLOAD HANDLER WIDGET ACCESS ===")
    configure_session_logging()
    
    # Enable upload debugging
    os.environ['DEBUG_ENABLED'] = 'cloudinary,assessment,upload,file_ops,errors'
    
    # Test file path
    test_file = "d:/Python playfolder/happyTag/test images 2/1.jpg"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"✅ Test file exists: {os.path.basename(test_file)}")
    
    try:
        # Import and create main window to get a realistic setup
        from main import MainWindow
        from PyQt5.QtWidgets import QApplication
        import sys
        
        app = QApplication(sys.argv)
        main_window = MainWindow()
        
        print("✅ Main window created")
        
        # Load the test file to create widgets
        print(f"📁 Loading file to create widgets: {os.path.basename(test_file)}")
        main_window.start_integrated_processing([test_file], "test")
        
        # Give processing time to complete
        import time
        time.sleep(2)
        
        # Check if widgets were created
        widget_count = 0
        if (hasattr(main_window, 'image_flow_manager') and 
            main_window.image_flow_manager and
            hasattr(main_window.image_flow_manager, 'image_widgets')):
            widget_count = len(main_window.image_flow_manager.image_widgets)
            print(f"✅ Image flow manager has {widget_count} widgets")
        else:
            print(f"❌ No image flow manager or widgets available")
            return False
        
        if widget_count == 0:
            print(f"❌ No widgets created - stopping test")
            return False
        
        # Get the upload handler
        if hasattr(main_window, 'upload_handler') and main_window.upload_handler:
            upload_handler = main_window.upload_handler
            print(f"✅ Upload handler found")
        else:
            print(f"❌ Upload handler not found")
            return False
        
        # Ensure Cloudinary is connected
        if not hasattr(main_window, 'cloudinary_connected') or not main_window.cloudinary_connected:
            # Wait for connection
            print("⏳ Waiting for Cloudinary connection...")
            for _ in range(10):  # Wait up to 10 seconds
                time.sleep(1)
                if hasattr(main_window, 'cloudinary_connected') and main_window.cloudinary_connected:
                    break
            
            if not main_window.cloudinary_connected:
                print("⚠️ Cloudinary not connected - proceeding anyway for widget test")
            else:
                print("✅ Cloudinary connected")
        
        # Now test the widget access by directly calling the upload method
        print(f"\n--- TESTING WIDGET ACCESS DURING UPLOAD ---")
        print(f"Attempting upload of: {test_file}")
        
        # Call the upload_single_file method which contains our debug code
        # Note: We expect this to show the debug output for widget access
        try:
            # This should trigger our debug output about widget access
            result = upload_handler.upload_single_file(test_file)
            print(f"Upload result: {result}")
        except Exception as upload_error:
            print(f"Upload error (expected): {upload_error}")
            print("This is expected if Cloudinary isn't fully set up, but we should see the widget access debug output")
        
        return True
    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_upload_handler_widget_access()
    print(f"\n{'='*60}")
    if success:
        print("✅ WIDGET ACCESS TEST COMPLETED")
        print("Check the debug output above for widget access details")
    else:
        print("❌ WIDGET ACCESS TEST FAILED")
    print(f"{'='*60}")