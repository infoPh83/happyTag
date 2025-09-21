#!/usr/bin/env python3
"""
Integration test to verify the complete solution works end-to-end
Tests the scenario where files with same names from different folders 
get unique public_ids and don't replace each other
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_duplicate_filename_scenario():
    """Test the specific scenario mentioned by the user"""
    print("=== Testing Duplicate Filename Scenario ===")
    print("Simulating: shoot1/test/image_01.jpg vs shoot2/test/image_01.jpg")
    print()
    
    from utilities.filename_sanitizer import generate_unique_public_id
    
    # Simulate existing Cloudinary cache (empty initially)
    cloudinary_cache = []
    
    # Simulate the assessment phase for multiple files with the same name
    test_files = [
        {"path": "D:/shoot1/test/image_01.jpg", "folder": "Uploads"},
        {"path": "D:/shoot2/test/image_01.jpg", "folder": "Uploads"},
        {"path": "D:/project1/images/photo.jpg", "folder": "Uploads"},
        {"path": "D:/project2/images/photo.jpg", "folder": "Uploads"},
        {"path": "D:/work/final_version.jpg", "folder": "Uploads"},
        {"path": "D:/backup/final_version.jpg", "folder": "Uploads"},
    ]
    
    print("Files to process:")
    for file_info in test_files:
        print(f"  - {file_info['path']}")
    print()
    
    # Simulate assessment phase - generate public_id_to_be for each file
    results = []
    for i, file_info in enumerate(test_files, 1):
        filename = os.path.basename(file_info['path'])
        folder = file_info['folder']
        
        print(f"Processing file {i}: {filename}")
        
        # Generate unique public_id with current cache state
        public_id_to_be = generate_unique_public_id(filename, folder, cloudinary_cache)
        
        print(f"  Generated public_id_to_be: {public_id_to_be}")
        
        # Add to cache to simulate it being "reserved" for upload
        cloudinary_cache.append({'public_id': public_id_to_be})
        
        results.append({
            'original_path': file_info['path'], 
            'filename': filename,
            'public_id_to_be': public_id_to_be
        })
        print()
    
    # Analysis
    print("=== RESULTS ANALYSIS ===")
    
    # Check for conflicts
    public_ids = [r['public_id_to_be'] for r in results]
    unique_public_ids = set(public_ids)
    
    print(f"Total files processed: {len(results)}")
    print(f"Unique public_ids generated: {len(unique_public_ids)}")
    print(f"Conflicts detected: {len(public_ids) - len(unique_public_ids)}")
    print()
    
    if len(public_ids) == len(unique_public_ids):
        print("✅ SUCCESS: All files got unique public_ids - no conflicts!")
    else:
        print("❌ FAILURE: Some files got duplicate public_ids!")
    
    print("\nDetailed results:")
    for result in results:
        print(f"  {result['filename']} -> {result['public_id_to_be']}")
    
    # Specific test case validation
    print("\n=== SPECIFIC TEST CASE VALIDATION ===")
    
    # Find the two image_01.jpg files
    image_01_results = [r for r in results if r['filename'] == 'image_01.jpg']
    
    if len(image_01_results) >= 2:
        print("Found multiple image_01.jpg files:")
        for i, result in enumerate(image_01_results):
            print(f"  File {i+1}: {result['original_path']} -> {result['public_id_to_be']}")
        
        # Check if they have different public_ids
        public_ids_for_image_01 = [r['public_id_to_be'] for r in image_01_results]
        if len(set(public_ids_for_image_01)) == len(public_ids_for_image_01):
            print("✅ SUCCESS: Files with same name got different public_ids!")
        else:
            print("❌ FAILURE: Files with same name got same public_ids!")
    
    # Find the two photo.jpg files  
    photo_results = [r for r in results if r['filename'] == 'photo.jpg']
    
    if len(photo_results) >= 2:
        print("\nFound multiple photo.jpg files:")
        for i, result in enumerate(photo_results):
            print(f"  File {i+1}: {result['original_path']} -> {result['public_id_to_be']}")
        
        # Check if they have different public_ids
        public_ids_for_photo = [r['public_id_to_be'] for r in photo_results]
        if len(set(public_ids_for_photo)) == len(public_ids_for_photo):
            print("✅ SUCCESS: Files with same name got different public_ids!")
        else:
            print("❌ FAILURE: Files with same name got same public_ids!")
    
    print("\n=== CLOUDINARY UPLOAD SIMULATION ===")
    print("This shows what would happen during actual upload:")
    
    for result in results:
        print(f"Upload: {result['filename']}")
        print(f"  public_id: {result['public_id_to_be']}")
        print(f"  unique_filename: False (disabled - we handle conflicts)")
        print(f"  use_filename: False (disabled - we provide explicit public_id)")
        print()

if __name__ == "__main__":
    test_duplicate_filename_scenario()