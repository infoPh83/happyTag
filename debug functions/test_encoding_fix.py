#!/usr/bin/env python3
"""Test script to verify metadata writing after encoding fixes"""

from utilities.exiftool_utils import write_cloudinary_metadata_to_file, get_cloudinary_public_id_from_metadata

def test_encoding_fix():
    print("Testing metadata write/read after encoding fixes...")
    
    # Test file with special characters
    file_path = r'test images\©Luca Piffaretti_ISE 5 Norwich_Print_0008.jpg'
    test_public_id = 'FIXED_PUBLIC_ID_123'
    test_tags = ['test', 'debug', 'fixed']
    
    print(f"Testing file: {file_path}")
    print(f"Writing public_id: {test_public_id}")
    print(f"Writing tags: {test_tags}")
    
    # Write metadata
    success = write_cloudinary_metadata_to_file(file_path, test_public_id, test_tags)
    print(f"Write success: {success}")
    
    if success:
        # Read back the public_id
        public_id = get_cloudinary_public_id_from_metadata(file_path)
        print(f"Read public_id: {public_id}")
        
        if public_id == test_public_id:
            print("✅ SUCCESS: Public ID correctly written and read!")
        else:
            print(f"❌ FAILED: Expected '{test_public_id}', got '{public_id}'")
    else:
        print("❌ FAILED: Could not write metadata")

if __name__ == "__main__":
    test_encoding_fix()