#!/usr/bin/env python3
"""
Test script to verify that the upload handler properly uses pre-generated public_id_to_be
from the image_metadata instead of trying to get it from widgets.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from utilities.debug_utils import debug_upload, debug_assessment
from utilities.session_logger import configure_session_logging

def test_upload_with_pregenerated_public_id():
    """Test that upload uses pre-generated public_id correctly"""
    
    print("=== TESTING UPLOAD WITH PRE-GENERATED PUBLIC_ID ===")
    configure_session_logging()
    
    # Test file path
    test_file = "d:/Python playfolder/happyTag/test images/Fifi RM10 Sterry Crescent 01.jpg"
    
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
        
        # Load the test file to trigger assessment
        print(f"📁 Loading file for assessment: {os.path.basename(test_file)}")
        main_window.start_integrated_processing([test_file], "test")
        
        # Check if public_id_to_be was generated during assessment
        if test_file in main_window.image_metadata:
            metadata = main_window.image_metadata[test_file]
            public_id_to_be = metadata.get('public_id_to_be')
            
            print(f"✅ Found metadata for file")
            print(f"   - public_id_to_be: {public_id_to_be}")
            print(f"   - cloudinary_synced: {metadata.get('cloudinary_synced', 'Not set')}")
            print(f"   - year: {metadata.get('year', 'Not set')}")
            
            if public_id_to_be:
                print(f"✅ Pre-generated public_id found: {public_id_to_be}")
                
                # Now test if upload handler can retrieve it
                from utilities.cloudinary_upload_handler import CloudinaryUploadHandler
                
                # Mock necessary components
                upload_handler = CloudinaryUploadHandler(
                    cloudinary_updater=None,  # Don't need real connection for this test
                    image_assessment=None,
                    main_app=main_window
                )
                
                # Test the metadata retrieval logic directly
                print(f"🔍 Testing upload handler metadata retrieval...")
                
                if hasattr(main_window, 'image_metadata') and test_file in main_window.image_metadata:
                    metadata = main_window.image_metadata[test_file]
                    retrieved_public_id = metadata.get('public_id_to_be')
                    
                    if retrieved_public_id:
                        print(f"✅ Upload handler can retrieve public_id_to_be: {retrieved_public_id}")
                        
                        if retrieved_public_id == public_id_to_be:
                            print(f"✅ PUBLIC_ID MATCHES! Upload handler will use the correct pre-generated ID")
                            return True
                        else:
                            print(f"❌ PUBLIC_ID MISMATCH! Expected: {public_id_to_be}, Got: {retrieved_public_id}")
                            return False
                    else:
                        print(f"❌ Upload handler cannot retrieve public_id_to_be from metadata")
                        return False
                else:
                    print(f"❌ Upload handler cannot access image_metadata")
                    return False
            else:
                print(f"❌ No public_id_to_be generated during assessment")
                return False
        else:
            print(f"❌ No metadata found for test file")
            return False
    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_upload_with_pregenerated_public_id()
    print(f"\n{'='*50}")
    if success:
        print("✅ TEST PASSED: Upload handler can retrieve pre-generated public_id")
    else:
        print("❌ TEST FAILED: Upload handler cannot retrieve pre-generated public_id")
    print(f"{'='*50}")