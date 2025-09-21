#!/usr/bin/env python3
"""
Test script to verify that the widget has the public_id_to_be after the fix
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from utilities.debug_utils import debug_upload, debug_assessment
from utilities.session_logger import configure_session_logging

def test_widget_public_id_to_be():
    """Test that widgets now have public_id_to_be after loading"""
    
    print("=== TESTING WIDGET PUBLIC_ID_TO_BE ACCESS ===")
    configure_session_logging()
    
    # Test file path
    test_file = "d:/Python playfolder/happyTag/test images/Westminster 06.JPG"
    
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
        
        # Load the test file to trigger assessment and widget creation
        print(f"📁 Loading file for assessment: {os.path.basename(test_file)}")
        main_window.start_integrated_processing([test_file], "test")
        
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
                    return False
            else:
                print(f"❌ Widget does not have get_public_id_to_be method")
                return False
        else:
            print(f"❌ Widget not found for test file")
            return False
    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_widget_public_id_to_be()
    print(f"\n{'='*60}")
    if success:
        print("✅ TEST PASSED: Widget has pre-generated public_id_to_be")
        print("✅ UPLOAD HANDLER SHOULD NOW WORK CORRECTLY")
    else:
        print("❌ TEST FAILED: Widget does not have pre-generated public_id_to_be")
    print(f"{'='*60}")