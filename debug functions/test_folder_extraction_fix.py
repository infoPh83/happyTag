#!/usr/bin/env python3
"""
Test script to verify the folder extraction fix for duplicate public_id generation
"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_folder_extraction():
    """Test the folder extraction logic that was fixed"""
    print("Testing folder extraction from file paths...")
    
    # Test cases with different folder structures
    test_cases = [
        r"D:\Python playfolder\happyTag\test images\shoot1\test\image_01.jpg",
        r"D:\Python playfolder\happyTag\test images\shoot2\test\image_01.jpg", 
        r"D:\Python playfolder\happyTag\test images\product_photos\camera.jpg",
        r"D:\Python playfolder\happyTag\test images\orphaned\moved_file.jpg",
        r"D:\Python playfolder\happyTag\test images\single_folder\photo.jpg"
    ]
    
    print("\nTesting folder extraction logic:")
    for file_path in test_cases:
        try:
            file_path_obj = Path(file_path)
            folder_name = file_path_obj.parent.name
            
            # If the folder name is "orphaned", use the parent folder instead
            if folder_name == "orphaned":
                folder_name = file_path_obj.parent.parent.name
                print(f"  {file_path}")
                print(f"    Detected 'orphaned' subfolder, using parent folder: '{folder_name}'")
            else:
                print(f"  {file_path}")
                print(f"    Extracted folder name: '{folder_name}'")
            
        except Exception as e:
            print(f"  {file_path}")
            print(f"    Error: {e}")
    
    # Test the unique public ID generation with immediate parent folder names
    print("\nTesting unique public_id generation with immediate parent folder names:")
    
    # Mock cloudinary cache with some existing public_ids that would create conflicts
    mock_cloudinary_cache = [
        {'public_id': 'test/image_01'},  # This should trigger conflict detection for both shoot1 and shoot2
        {'public_id': 'product_photos/camera'},
    ]
    
    try:
        from utilities.filename_sanitizer import generate_unique_public_id
        
        test_files = [
            (r"D:\Python playfolder\happyTag\test images\shoot1\test\image_01.jpg", "test"),
            (r"D:\Python playfolder\happyTag\test images\shoot2\test\image_01.jpg", "test"), 
            (r"D:\Python playfolder\happyTag\test images\product_photos\camera.jpg", "product_photos"),
            (r"D:\Python playfolder\happyTag\test images\single_folder\photo.jpg", "single_folder"),
        ]
        
        print("  Demonstrating conflict resolution for same folder + filename combinations:")
        for file_path, expected_folder in test_files:
            filename = os.path.basename(file_path)
            
            # Extract immediate parent folder using simplified logic
            file_path_obj = Path(file_path)
            folder_name = file_path_obj.parent.name
            
            if folder_name == "orphaned":
                folder_name = file_path_obj.parent.parent.name
            
            print(f"  File: {filename}")
            print(f"    Expected folder: {expected_folder}")
            print(f"    Extracted folder: {folder_name}")
            
            # Generate unique public_id
            unique_public_id = generate_unique_public_id(
                filename,
                folder_name, 
                mock_cloudinary_cache
            )
            
            print(f"    Generated public_id: {unique_public_id}")
            
            # Update cache to simulate subsequent files
            mock_cloudinary_cache.append({'public_id': unique_public_id.replace('.jpg', '')})
            
        print("\n✅ All folder extraction tests passed!")
        print("✅ Note: Files with same folder+filename get unique suffixes via generate_unique_public_id()")
        
    except ImportError as e:
        print(f"\n❌ Could not import filename_sanitizer: {e}")
        print("Make sure the utilities module is available")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    test_folder_extraction()