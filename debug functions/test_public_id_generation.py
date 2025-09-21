#!/usr/bin/env python3
"""
Test script to verify the new public_id generation logic
Tests that duplicate filenames get unique public_ids
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utilities.filename_sanitizer import generate_unique_public_id

def test_unique_public_id_generation():
    """Test that duplicate filenames get unique public_ids"""
    print("=== Testing Public ID Generation ===")
    
    # Mock Cloudinary cache with existing files
    mock_cloudinary_cache = [
        {'public_id': 'Uploads/image_01.jpg'},
        {'public_id': 'Uploads/test_file.jpg'},
        {'public_id': 'Uploads/CopyrightLuca_Piffaretti_A.jpg'},
    ]
    
    print("Mock Cloudinary cache contains:")
    for item in mock_cloudinary_cache:
        print(f"  - {item['public_id']}")
    print()
    
    # Test cases for duplicate detection
    test_cases = [
        # Case 1: File that doesn't exist - should use base name
        ("new_file.jpg", "Uploads", "Should get base name"),
        
        # Case 2: File that already exists - should get unique suffix
        ("image_01.jpg", "Uploads", "Should get unique suffix (conflicts with existing)"),
        
        # Case 3: Special characters - should be sanitized
        ("©Luca Piffaretti_A.jpg", "Uploads", "Should be sanitized"),
        
        # Case 4: Same filename from different folder
        ("image_01.jpg", "test images", "Different folder - should not conflict"),
        
        # Case 5: No folder path
        ("standalone.jpg", "", "No folder path"),
    ]
    
    results = []
    
    for filename, folder, description in test_cases:
        print(f"Test: {description}")
        print(f"  Input: filename='{filename}', folder='{folder}'")
        
        public_id = generate_unique_public_id(filename, folder, mock_cloudinary_cache)
        
        print(f"  Generated public_id: '{public_id}'")
        print(f"  Unique: {public_id not in [item['public_id'] for item in mock_cloudinary_cache]}")
        print()
        
        results.append({
            'filename': filename,
            'folder': folder,
            'public_id': public_id,
            'description': description
        })
    
    # Summary
    print("=== SUMMARY ===")
    existing_ids = {item['public_id'] for item in mock_cloudinary_cache}
    
    for result in results:
        conflict = result['public_id'] in existing_ids
        status = "❌ CONFLICT" if conflict else "✅ UNIQUE"
        print(f"{status}: {result['public_id']} ({result['description']})")
    
    print()
    print("=== Additional Tests ===")
    
    # Test multiple conflicts for the same file
    print("Testing multiple files with same name:")
    for i in range(3):
        public_id = generate_unique_public_id("image_01.jpg", "Uploads", mock_cloudinary_cache)
        # Add to cache to simulate conflicts
        mock_cloudinary_cache.append({'public_id': public_id})
        print(f"  Attempt {i+1}: {public_id}")
    
    # Test filename sanitization
    print("\nTesting special character sanitization:")
    special_files = [
        "Test with €50 and £30.jpg",
        "Café résumé.jpg", 
        "Document with § and ¶.jpg",
        "Temperature 25°C.jpg"
    ]
    
    for filename in special_files:
        public_id = generate_unique_public_id(filename, "test", [])
        print(f"  '{filename}' -> '{public_id}'")

if __name__ == "__main__":
    test_unique_public_id_generation()