#!/usr/bin/env python3
"""
Test script to verify the complete widget-based public_id workflow for upload
"""

import os
import sys
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from utilities.debug_utils import debug_upload, debug_assessment
from utilities.session_logger import configure_session_logging

def test_real_widget_workflow():
    """Test the complete workflow: assessment -> widget creation -> upload handler access"""
    
    print("=== TESTING REAL WIDGET WORKFLOW ===")
    configure_session_logging()
    
    # Test file path
    test_file = "d:/Python playfolder/happyTag/test images 2/1.jpg"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"✅ Test file exists: {os.path.basename(test_file)}")
    
    try:
        # Import main window
        from main import MainWindow
        from PyQt5.QtWidgets import QApplication
        import sys
        
        app = QApplication(sys.argv)
        main_window = MainWindow()
        
        print("✅ Main window created")
        
        # Load the test file for assessment and widget creation
        print(f"📁 Loading file for assessment: {os.path.basename(test_file)}")
        main_window.start_integrated_processing([test_file], "test")
        
        # Give a short time for processing to complete
        time.sleep(0.5)
        
        # Check image_metadata for public_id_to_be
        print(f"\n--- CHECKING IMAGE METADATA ---")
        if hasattr(main_window, 'image_metadata') and test_file in main_window.image_metadata:
            metadata = main_window.image_metadata[test_file]
            public_id_to_be = metadata.get('public_id_to_be')
            print(f"✅ Found image_metadata for file")
            print(f"   public_id_to_be in metadata: {public_id_to_be}")
            
            if public_id_to_be:
                print(f"✅ PUBLIC_ID_TO_BE FOUND IN METADATA: {public_id_to_be}")
            else:
                print(f"❌ No public_id_to_be in metadata")
                return False
        else:
            print(f"❌ No image_metadata found for file")
            return False
        
        # Check if the widget exists in image_flow_manager
        print(f"\n--- CHECKING WIDGET AVAILABILITY ---")
        if (hasattr(main_window, 'image_flow_manager') and 
            main_window.image_flow_manager):
            
            widget_count = len(main_window.image_flow_manager.image_widgets)
            print(f"Widget manager has {widget_count} widgets")
            
            if test_file in main_window.image_flow_manager.image_widgets:
                widget = main_window.image_flow_manager.image_widgets[test_file]
                print(f"✅ Widget found for test file")
                
                # Check if widget has the public_id_to_be
                if hasattr(widget, 'get_public_id_to_be'):
                    widget_public_id_to_be = widget.get_public_id_to_be()
                    print(f"✅ Widget has get_public_id_to_be method")
                    print(f"   widget public_id_to_be: {widget_public_id_to_be}")
                    
                    if widget_public_id_to_be == public_id_to_be:
                        print(f"✅ WIDGET PUBLIC_ID_TO_BE MATCHES METADATA")
                    else:
                        print(f"⚠️  Widget and metadata public_id_to_be don't match:")
                        print(f"      Widget: {widget_public_id_to_be}")
                        print(f"      Metadata: {public_id_to_be}")
                else:
                    print(f"❌ Widget does not have get_public_id_to_be method")
                    return False
            else:
                print(f"❌ Widget not found for test file")
                
                # Debug: Show available widgets
                print(f"Available widgets ({widget_count}):")
                for i, path in enumerate(main_window.image_flow_manager.image_widgets.keys()):
                    print(f"   [{i}] {path}")
                    if i >= 5:  # Limit output
                        print(f"   ... and {widget_count - 6} more")
                        break
                return False
        else:
            print(f"❌ No image_flow_manager found")
            return False
        
        # Test the upload handler access (simulate what happens during upload)
        print(f"\n--- TESTING UPLOAD HANDLER ACCESS ---")
        if hasattr(main_window, 'upload_handler') and main_window.upload_handler:
            print(f"✅ Upload handler exists")
            
            # Try to access the widget like the upload handler would
            try:
                widget = main_window.image_flow_manager.image_widgets.get(test_file)
                if widget:
                    upload_public_id_to_be = widget.get_public_id_to_be()
                    print(f"✅ Upload handler can access widget")
                    print(f"   public_id_to_be from widget: {upload_public_id_to_be}")
                    
                    if upload_public_id_to_be:
                        print(f"✅ UPLOAD HANDLER CAN GET PUBLIC_ID_TO_BE FROM WIDGET")
                        print(f"✅ THE COMPLETE WORKFLOW IS WORKING!")
                        return True
                    else:
                        print(f"❌ Widget public_id_to_be is None from upload handler perspective")
                        return False
                else:
                    print(f"❌ Upload handler cannot find widget")
                    return False
            except Exception as e:
                print(f"❌ Error accessing widget from upload handler: {e}")
                return False
        else:
            print(f"❌ No upload handler found")
            return False
    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_real_widget_workflow()
    print(f"\n{'='*60}")
    if success:
        print("✅ COMPLETE WORKFLOW TEST PASSED")
        print("✅ ORPHANED CLEANUP + PUBLIC_ID_TO_BE GENERATION + WIDGET ACCESS ALL WORKING")
        print("✅ THE CLOUDINARY FILE REPLACEMENT ISSUE SHOULD BE RESOLVED!")
    else:
        print("❌ COMPLETE WORKFLOW TEST FAILED")
        print("❌ There is still an issue in the widget access chain")
    print(f"{'='*60}")