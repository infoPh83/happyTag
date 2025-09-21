#!/usr/bin/env python3
"""
Test script to verify duplicate public_id conflict resolution works correctly
"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_duplicate_conflict_resolution():
    """Test that files with same folder+filename get unique public_ids"""
    print("Testing duplicate conflict resolution...")
    
    try:
        from utilities.filename_sanitizer import generate_unique_public_id
        
        # Start with empty cache
        mock_cloudinary_cache = []
        
        # Test files with potential conflicts
        test_files = [
            r"D:\Python playfolder\happyTag\test images\shoot1\test\image_01.jpg",
            r"D:\Python playfolder\happyTag\test images\shoot2\test\image_01.jpg",  # Same folder+filename
            r"D:\Python playfolder\happyTag\test images\product_photos\camera.jpg",
            r"D:\Python playfolder\happyTag\test images\other_shoot\test\image_01.jpg",  # Another conflict
        ]
        
        generated_ids = []
        
        print("  Processing files sequentially to simulate upload order:")
        for i, file_path in enumerate(test_files, 1):
            filename = os.path.basename(file_path)
            
            # Extract immediate parent folder
            file_path_obj = Path(file_path)
            folder_name = file_path_obj.parent.name
            
            print(f"\n  File {i}: {filename}")
            print(f"    Source path: {file_path}")
            print(f"    Folder: {folder_name}")
            print(f"    Current cache size: {len(mock_cloudinary_cache)}")
            
            # Generate unique public_id
            unique_public_id = generate_unique_public_id(
                filename,
                folder_name, 
                mock_cloudinary_cache
            )
            
            print(f"    Generated public_id: {unique_public_id}")
            
            # Add to our tracking
            generated_ids.append(unique_public_id)
            
            # Simulate adding to Cloudinary cache (keep the full public_id with extension)
            mock_cloudinary_cache.append({'public_id': unique_public_id})
            print(f"    Added to cache: {unique_public_id}")
        
        print(f"\n  Summary:")
        print(f"    Total files processed: {len(test_files)}")
        print(f"    Generated public_ids: {len(generated_ids)}")
        print(f"    Unique public_ids: {len(set(generated_ids))}")
        
        # Verify all generated IDs are unique
        if len(generated_ids) == len(set(generated_ids)):
            print("    ✅ All public_ids are unique - conflict resolution working!")
        else:
            print("    ❌ Duplicate public_ids found - conflict resolution failed!")
            
        # Show specific conflicts that were resolved
        print(f"\n  Conflict resolution examples:")
        for i, public_id in enumerate(generated_ids):
            if 'test/image_01' in public_id:
                print(f"    File {i+1}: {public_id}")
                
        print("\n✅ Duplicate conflict resolution test completed!")
        
    except ImportError as e:
        print(f"\n❌ Could not import filename_sanitizer: {e}")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    test_duplicate_conflict_resolution()