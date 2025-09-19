#!/usr/bin/env python3
"""Test script to check Cloudinary cache and file recognition"""

import sys
import os
sys.path.append('.')

from utilities.cloudinary_upload_handler import get_cloudinary_public_id_from_metadata

def test_file_recognition():
    print("Testing local file public_id recognition...")
    
    # Test file recognition
    test_files = [
        'test images/1.jpg',
        'test images/array_test.jpg', 
        'test images/metadata_test.jpg',
        'test images/super long file name to be truncated.jpg',
        'test images/test_final.jpg'
    ]
    
    print("Results:")
    for test_file in test_files:
        if os.path.exists(test_file):
            public_id = get_cloudinary_public_id_from_metadata(test_file)
            filename = os.path.basename(test_file)
            if public_id:
                print(f"  ✅ {filename}: '{public_id}'")
            else:
                print(f"  ❌ {filename}: No public_id found")
        else:
            print(f"  ❓ {test_file}: File not found")

if __name__ == "__main__":
    test_file_recognition()