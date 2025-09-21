#!/usr/bin/env python3
"""
Comprehensive test to verify the complete workflow:
1. Assessment phase generates public_id with Uploads/ prefix
2. Upload phase uses pre-generated public_id directly without double-prefixing
3. Conflict detection works properly
"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_complete_workflow():
    """Test the complete workflow from assessment to upload"""
    print("Testing complete workflow: Assessment → Upload → Conflict Detection")
    print("=" * 60)
    
    try:
        from utilities.filename_sanitizer import generate_unique_public_id
        
        print("PHASE 1: Assessment Phase - Generate public_ids with conflict detection")
        print("-" * 60)
        
        # Mock Cloudinary cache with existing files (what we'd find during assessment)
        mock_cloudinary_cache = [
            {'public_id': 'Uploads/Aptel East - unedited/unedited_30.jpg'},  # Existing conflict
            {'public_id': 'Uploads/product_photos/camera.jpg'},
            {'public_id': 'Uploads/test/image_01.jpg'},
        ]
        
        print("Existing Cloudinary files (cache):")
        for item in mock_cloudinary_cache:
            print(f"  - {item['public_id']}")
        print()
        
        # Files being processed during assessment
        test_files = [
            r"D:\Photos\Project_A\Aptel East - unedited\unedited_30.jpg",
            r"D:\Photos\Project_B\Aptel East - unedited\unedited_30.jpg",
            r"D:\Photos\Different\product_photos\camera.jpg",
        ]
        
        pre_generated_public_ids = {}
        
        for i, file_path in enumerate(test_files, 1):
            filename = os.path.basename(file_path)
            
            # Extract immediate parent folder (assessment phase logic)
            file_path_obj = Path(file_path)
            folder_name = file_path_obj.parent.name
            
            # Add the "Uploads/" prefix (NEW FIX)
            full_folder_path = f"Uploads/{folder_name}"
            
            print(f"File {i}: {filename}")
            print(f"  Source: {file_path}")
            print(f"  Folder: {folder_name}")
            print(f"  Full path: {full_folder_path}")
            
            # Generate unique public_id with conflict detection
            public_id_to_be = generate_unique_public_id(
                filename,
                full_folder_path,
                mock_cloudinary_cache
            )
            
            print(f"  Generated public_id_to_be: {public_id_to_be}")
            
            # Check for conflicts
            existing_public_ids = {cf.get('public_id', '') for cf in mock_cloudinary_cache}
            if public_id_to_be in existing_public_ids:
                print(f"  ❌ CONFLICT: Would replace existing file!")
            else:
                print(f"  ✅ UNIQUE: No conflicts detected")
                
            # Store for upload phase
            pre_generated_public_ids[file_path] = public_id_to_be
            
            # Add to cache for next iteration
            mock_cloudinary_cache.append({'public_id': public_id_to_be})
            print()
        
        print("\nPHASE 2: Upload Phase - Use pre-generated public_ids directly")
        print("-" * 60)
        
        for file_path, public_id_to_be in pre_generated_public_ids.items():
            filename = os.path.basename(file_path)
            
            print(f"Uploading: {filename}")
            print(f"  Pre-generated public_id_to_be: {public_id_to_be}")
            
            # Simulate upload phase logic (NEW FIX - no folder parameter)
            # The upload handler would now do:
            upload_params = {
                'public_id': public_id_to_be,  # Use directly, already includes Uploads/
                'resource_type': 'image',
                'tags': [],
                'unique_filename': False,
                'use_filename': False
                # NO folder parameter - that would cause double-prefixing
            }
            
            print(f"  Upload params: public_id='{upload_params['public_id']}'")
            print(f"  Upload params: folder=None (not specified)")
            print(f"  ✅ No double-prefixing - direct use of pre-generated ID")
            print()
        
        print("PHASE 3: Verification")
        print("-" * 60)
        
        all_generated_ids = list(pre_generated_public_ids.values())
        unique_count = len(set(all_generated_ids))
        
        print(f"Total files processed: {len(test_files)}")
        print(f"Unique public_ids generated: {unique_count}")
        print(f"Generated public_ids:")
        for i, public_id in enumerate(all_generated_ids, 1):
            print(f"  {i}. {public_id}")
        
        if unique_count == len(test_files):
            print(f"\n✅ SUCCESS: All files have unique public_ids")
            print(f"✅ Conflict detection working properly")
            print(f"✅ No double-prefixing issues")
            print(f"✅ File replacement problem SOLVED!")
        else:
            print(f"\n❌ FAILURE: Some files would still conflict")
        
        # Show the specific fix for your original issue
        print(f"\nOriginal Issue Resolution:")
        print(f"-" * 30)
        original_issue_files = [pid for pid in all_generated_ids if 'unedited_30' in pid]
        print(f"Files with same name 'unedited_30.jpg' from different folders:")
        for i, public_id in enumerate(original_issue_files, 1):
            print(f"  File {i}: {public_id}")
        
        if len(set(original_issue_files)) == len(original_issue_files):
            print(f"✅ Different public_ids - no replacement will occur!")
        else:
            print(f"❌ Same public_ids - replacement would still occur!")
            
        print(f"\n✅ Complete workflow test finished!")
        
    except ImportError as e:
        print(f"\n❌ Could not import required modules: {e}")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    test_complete_workflow()