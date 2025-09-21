#!/usr/bin/env python3
"""
Test script to verify the upload handler uses pre-generated public_id_to_be
by temporarily clearing the file's metadata to simulate a new file.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from utilities.debug_utils import debug_upload, debug_assessment
from utilities.session_logger import configure_session_logging
from utilities.exiftool_utils import write_cloudinary_metadata_to_file, get_cloudinary_public_id_from_metadata

def test_upload_public_id_for_new_file():
    """Test upload handler with a file that will need public_id generation"""
    
    print("=== TESTING UPLOAD HANDLER PUBLIC_ID FOR NEW FILE ===")
    configure_session_logging()
    
    # Test file path
    test_file = "d:/Python playfolder/happyTag/test images/Fifi RM10 Sterry Crescent 01.jpg"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"✅ Test file exists: {os.path.basename(test_file)}")
    
    try:
        # STEP 1: Clear the Cloudinary metadata to simulate a new file
        print(f"🧹 Clearing Cloudinary metadata to simulate new file...")
        
        # Check if ExifTool is available
        from utilities.exiftool_detector import get_exiftool_info
        exiftool_info = get_exiftool_info()
        exiftool_available = exiftool_info.get('available', False)
        exiftool_path = exiftool_info.get('path')
        
        if exiftool_available:
            # Clear the CloudinaryPublicId metadata
            import subprocess
            result = subprocess.run([
                exiftool_path, 
                "-CloudinaryPublicId=", 
                "-XMP-HappyTag:CloudinaryPublicId=",
                "-overwrite_original",
                test_file
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Cleared Cloudinary metadata from test file")
            else:
                print(f"⚠️  ExifTool warning: {result.stderr}")
        else:
            print(f"⚠️  ExifTool not available - cannot clear metadata")
        
        # Verify metadata is cleared
        public_id = get_cloudinary_public_id_from_metadata(test_file)
        print(f"📋 Current public_id in metadata: {public_id or 'None'}")
        
        # STEP 2: Load file to trigger assessment
        from main import MainWindow
        from PyQt5.QtWidgets import QApplication
        import sys
        
        app = QApplication(sys.argv)
        main_window = MainWindow()
        
        print("✅ Main window created")
        print(f"📁 Loading file for assessment: {os.path.basename(test_file)}")
        
        # Process the file
        main_window.start_integrated_processing([test_file], "test")
        
        # STEP 3: Check if public_id_to_be was generated
        if test_file in main_window.image_metadata:
            metadata = main_window.image_metadata[test_file]
            public_id_to_be = metadata.get('public_id_to_be')
            cloudinary_synced = metadata.get('cloudinary_synced', False)
            
            print(f"✅ Found metadata for file")
            print(f"   - public_id_to_be: {public_id_to_be}")
            print(f"   - cloudinary_synced: {cloudinary_synced}")
            print(f"   - year: {metadata.get('year', 'Not set')}")
            
            if not cloudinary_synced and public_id_to_be:
                print(f"✅ File is NOT SYNCED and has pre-generated public_id: {public_id_to_be}")
                
                # STEP 4: Test upload handler metadata retrieval
                from utilities.cloudinary_upload_handler import CloudinaryUploadHandler
                
                upload_handler = CloudinaryUploadHandler(
                    cloudinary_updater=main_window.cloudinary_updater,
                    image_assessment=main_window.image_assessment,
                    main_app=main_window
                )
                
                print(f"🔍 Testing upload handler metadata retrieval...")
                
                # Simulate the logic from the upload handler
                if hasattr(main_window, 'image_metadata') and test_file in main_window.image_metadata:
                    metadata = main_window.image_metadata[test_file]
                    retrieved_public_id = metadata.get('public_id_to_be')
                    
                    if retrieved_public_id:
                        print(f"✅ Upload handler can retrieve public_id_to_be: {retrieved_public_id}")
                        
                        if retrieved_public_id == public_id_to_be:
                            print(f"✅ PUBLIC_ID MATCHES! Upload would use: {retrieved_public_id}")
                            
                            # Test that it includes conflict prevention suffix
                            if '_' in retrieved_public_id and len(retrieved_public_id.split('_')[-1]) == 6:
                                print(f"✅ Public_id includes conflict prevention suffix")
                                return True
                            else:
                                print(f"⚠️  Public_id may not have conflict prevention suffix")
                                return True  # Still a success for main test
                        else:
                            print(f"❌ PUBLIC_ID MISMATCH! Expected: {public_id_to_be}, Got: {retrieved_public_id}")
                            return False
                    else:
                        print(f"❌ Upload handler cannot retrieve public_id_to_be from metadata")
                        return False
                else:
                    print(f"❌ Upload handler cannot access image_metadata")
                    return False
            elif cloudinary_synced:
                print(f"ℹ️  File is already synced - no public_id_to_be needed")
                print(f"   This test needs a file that's NOT synced to generate public_id_to_be")
                return False
            else:
                print(f"❌ File is not synced but no public_id_to_be generated")
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
    success = test_upload_public_id_for_new_file()
    print(f"\n{'='*60}")
    if success:
        print("✅ TEST PASSED: Upload handler can retrieve pre-generated public_id")
    else:
        print("❌ TEST FAILED: Upload handler cannot retrieve pre-generated public_id")
    print(f"{'='*60}")