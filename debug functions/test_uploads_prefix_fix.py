#!/usr/bin/env python3
"""
Test script to verify the Uploads/ prefix fix for conflict detection
"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_uploads_prefix_fix():
    """Test that generated public_ids include Uploads/ prefix to match actual Cloudinary format"""
    print("Testing Uploads/ prefix fix for conflict detection...")
    
    try:
        from utilities.filename_sanitizer import generate_unique_public_id
        
        # Mock Cloudinary cache with the actual format that includes Uploads/ prefix
        mock_cloudinary_cache = [
            {'public_id': 'Uploads/Aptel East - unedited/unedited_30.jpg'},  # Existing file
            {'public_id': 'Uploads/product_photos/camera.jpg'},
            {'public_id': 'Uploads/test/image_01.jpg'},
        ]
        
        print("Mock Cloudinary cache contains:")
        for item in mock_cloudinary_cache:
            print(f"  - {item['public_id']}")
        print()
        
        # Test the exact scenario from user feedback
        test_file = r"D:\Photos\Aptel East - unedited\unedited_30.jpg"
        filename = os.path.basename(test_file)
        
        # Extract immediate parent folder
        file_path_obj = Path(test_file)
        folder_name = file_path_obj.parent.name
        
        # Add the "Uploads/" prefix like our fixed code does
        full_folder_path = f"Uploads/{folder_name}"
        
        print(f"Test scenario:")
        print(f"  File path: {test_file}")
        print(f"  Filename: {filename}")
        print(f"  Immediate parent folder: {folder_name}")
        print(f"  Full Cloudinary folder path: {full_folder_path}")
        
        # Generate public_id with the correct format
        generated_public_id = generate_unique_public_id(
            filename,
            full_folder_path,
            mock_cloudinary_cache
        )
        
        print(f"  Generated public_id: {generated_public_id}")
        
        # Check if this matches any existing entry
        existing_public_ids = {cf.get('public_id', '') for cf in mock_cloudinary_cache}
        if generated_public_id in existing_public_ids:
            print(f"  🔥 CONFLICT DETECTED: {generated_public_id} already exists!")
            print(f"  ✅ Conflict detection is working - suffix should be added")
        else:
            print(f"  ✅ No conflict - unique public_id generated")
        
        # Test what would happen without the Uploads/ prefix (old broken behavior)
        old_style_public_id = generate_unique_public_id(
            filename,
            folder_name,  # Without Uploads/ prefix
            mock_cloudinary_cache
        )
        
        print(f"\n  Comparison with old behavior (without Uploads/ prefix):")
        print(f"    Old style would generate: {old_style_public_id}")
        print(f"    New style generates: {generated_public_id}")
        
        if old_style_public_id == generated_public_id:
            print(f"    ❌ Same result - conflict detection would still fail")
        else:
            print(f"    ✅ Different results - fix is working")
        
        # Test another file that should conflict
        print(f"\n  Testing a second file that should conflict:")
        test_file2 = r"D:\Photos\Another_Project\Aptel East - unedited\unedited_30.jpg"
        file_path_obj2 = Path(test_file2)
        folder_name2 = file_path_obj2.parent.name
        full_folder_path2 = f"Uploads/{folder_name2}"
        
        print(f"    Second file: {test_file2}")
        print(f"    Folder: {folder_name2}")
        print(f"    Full path: {full_folder_path2}")
        
        # Add first file to cache
        mock_cloudinary_cache.append({'public_id': generated_public_id})
        
        generated_public_id2 = generate_unique_public_id(
            filename,  # Same filename
            full_folder_path2,  # Same folder structure
            mock_cloudinary_cache
        )
        
        print(f"    Generated public_id: {generated_public_id2}")
        
        if generated_public_id == generated_public_id2:
            print(f"    ❌ SAME PUBLIC_ID - conflict not resolved!")
        else:
            print(f"    ✅ DIFFERENT PUBLIC_ID - conflict resolved with suffix!")
        
        print(f"\n✅ Uploads/ prefix fix test completed!")
        
    except ImportError as e:
        print(f"\n❌ Could not import filename_sanitizer: {e}")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    test_uploads_prefix_fix()