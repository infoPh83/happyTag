#!/usr/bin/env python3
"""
Test the upload sequence with a fresh file to verify the fix is working correctly.
"""

import os
import subprocess
import sys
from pathlib import Path

# Add the project root to the path to import our modules
script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from utilities.exiftool_utils import write_cloudinary_metadata_to_file, get_cloudinary_public_id_from_metadata

def set_test_finder_tags(file_path, tags):
    """Set test Finder tags on a file."""
    try:
        import plistlib
        
        # Format tags for Finder (with color info)
        formatted_tags = []
        for i, tag in enumerate(tags):
            formatted_tags.append(f"{tag}\n{i % 7}")  # Cycle through color indices 0-6
        
        # Create binary plist
        plist_data = plistlib.dumps(formatted_tags)
        hex_data = plist_data.hex()
        
        # Write to extended attributes
        result = subprocess.run([
            'xattr', '-w', '-x', 'com.apple.metadata:_kMDItemUserTags', hex_data, file_path
        ], capture_output=True, text=True)
        
        return result.returncode == 0
    except Exception:
        return False

def check_finder_tags_exist(file_path):
    """Check if Finder tags exist on a file."""
    try:
        result = subprocess.run(
            ['xattr', '-p', '-x', 'com.apple.metadata:_kMDItemUserTags', file_path],
            capture_output=True, text=True
        )
        return result.returncode == 0
    except Exception:
        return False

def main():
    """Test the upload fix."""
    test_file = "test_cross_platform.jpg"
    
    if not os.path.exists(test_file):
        print(f"Test file {test_file} not found.")
        return
    
    print("Testing upload fix...")
    print("=" * 40)
    
    # Set test tags
    test_tags = ["upload_test1", "upload_test2"]
    if set_test_finder_tags(test_file, test_tags):
        print("✅ Set test Finder tags")
    else:
        print("❌ Failed to set test Finder tags")
        return
    
    # Verify tags exist
    if check_finder_tags_exist(test_file):
        print("✅ Verified Finder tags exist before upload")
    else:
        print("❌ Finder tags missing before upload")
        return
    
    # Simulate upload metadata write
    result = write_cloudinary_metadata_to_file(
        test_file, 
        "test_upload_fix_12345", 
        tags=test_tags
    )
    
    if result['success']:
        print("✅ Upload metadata write successful")
    else:
        print(f"❌ Upload metadata write failed: {result['message']}")
        return
    
    # Check if tags still exist after upload
    if check_finder_tags_exist(test_file):
        print("✅ SUCCESS: Finder tags preserved after upload!")
    else:
        print("❌ FAILURE: Finder tags cleared after upload")
        return
    
    # Verify public_id was written
    public_id = get_cloudinary_public_id_from_metadata(test_file)
    if public_id == "test_upload_fix_12345":
        print("✅ Public ID correctly written")
    else:
        print(f"❌ Public ID incorrect: {public_id}")
        return
    
    print("\n🎉 ALL TESTS PASSED - Upload fix is working correctly!")

if __name__ == "__main__":
    main()
