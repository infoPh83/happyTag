#!/usr/bin/env python3
"""
Test script to verify the exact scenario from user feedback:
Files with same names from different folders should get unique public_ids
"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_exact_user_scenario():
    """Test the exact scenario that was failing"""
    print("Testing exact user scenario - same filename, same immediate parent folder...")
    
    try:
        from utilities.filename_sanitizer import generate_unique_public_id
        
        # Simulate the exact scenario: unedited_20.jpg in different source folders
        # but both having the same immediate parent folder name
        test_scenarios = [
            {
                'file_path': r"D:\Photos\Project_A\exports\unedited_20.jpg",
                'description': "First file from Project_A/exports"
            },
            {
                'file_path': r"D:\Photos\Project_B\exports\unedited_20.jpg", 
                'description': "Second file from Project_B/exports (same immediate parent + filename)"
            },
            {
                'file_path': r"D:\Photos\Different_Shoot\outputs\unedited_20.jpg",
                'description': "Third file from Different_Shoot/outputs (different parent folder)"
            }
        ]
        
        # Start with empty cache to simulate first time processing
        mock_cloudinary_cache = []
        
        print("  Processing files in order they might be encountered:")
        results = []
        
        for i, scenario in enumerate(test_scenarios, 1):
            file_path = scenario['file_path']
            filename = os.path.basename(file_path)
            
            # Extract immediate parent folder (this is what our fix does)
            file_path_obj = Path(file_path)
            folder_name = file_path_obj.parent.name
            
            print(f"\n  Scenario {i}: {scenario['description']}")
            print(f"    File path: {file_path}")
            print(f"    Filename: {filename}")
            print(f"    Immediate parent folder: {folder_name}")
            print(f"    Cache entries before processing: {len(mock_cloudinary_cache)}")
            
            # Generate unique public_id (this is the core fix)
            unique_public_id = generate_unique_public_id(
                filename,
                folder_name, 
                mock_cloudinary_cache
            )
            
            print(f"    Generated public_id: {unique_public_id}")
            
            # Check if this matches any previous result
            conflict_with = None
            for prev_result in results:
                if prev_result['public_id'] == unique_public_id:
                    conflict_with = prev_result
                    break
                    
            if conflict_with:
                print(f"    ❌ CONFLICT: Same as {conflict_with['description']}")
            else:
                print(f"    ✅ UNIQUE: No conflicts detected")
            
            # Store result
            result = {
                'description': scenario['description'],
                'file_path': file_path,
                'folder_name': folder_name,
                'public_id': unique_public_id,
                'filename': filename
            }
            results.append(result)
            
            # Add to cache for next iteration
            mock_cloudinary_cache.append({'public_id': unique_public_id})
        
        # Summary
        print(f"\n  SUMMARY:")
        print(f"    Total files processed: {len(results)}")
        all_public_ids = [r['public_id'] for r in results]
        unique_count = len(set(all_public_ids))
        print(f"    Unique public_ids generated: {unique_count}")
        
        if unique_count == len(results):
            print(f"    ✅ SUCCESS: All files got unique public_ids")
            print(f"    ✅ File replacement issue is SOLVED!")
        else:
            print(f"    ❌ FAILURE: Some files would still replace each other")
            
        # Show the specific results for same filename cases
        print(f"\n  Specific results for 'unedited_20.jpg' files:")
        for result in results:
            if result['filename'] == 'unedited_20.jpg':
                print(f"    {result['folder_name']}/unedited_20.jpg → {result['public_id']}")
        
        print(f"\n✅ User scenario test completed!")
        
    except ImportError as e:
        print(f"\n❌ Could not import filename_sanitizer: {e}")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    test_exact_user_scenario()