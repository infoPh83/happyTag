#!/usr/bin/env python3
"""
Debug script to reproduce and understand the upload tag clearing issue.
Tests the sequence of operations that happen during upload to identify where tags get cleared.
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

def check_finder_tags(file_path):
    """Check the current Finder tags on a file."""
    try:
        result = subprocess.run(
            ['xattr', '-p', '-x', 'com.apple.metadata:_kMDItemUserTags', file_path],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return f"Finder tags found: {result.stdout.strip()}"
        else:
            return "No Finder tags found"
    except Exception as e:
        return f"Error checking Finder tags: {e}"

def check_exif_tags(file_path):
    """Check EXIF/metadata tags in the file."""
    try:
        # Try to get keywords from the file
        result = subprocess.run([
            'exiftool', '-Keywords', '-Subject', '-sep', ',', file_path
        ], capture_output=True, text=True)
        if result.returncode == 0:
            return f"EXIF tags found: {result.stdout.strip()}"
        else:
            return "No EXIF tags found"
    except Exception as e:
        return f"Error checking EXIF tags: {e}"

def set_test_finder_tags(file_path, tags):
    """Set test Finder tags on a file."""
    try:
        # Create binary plist format for tags
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
        
        if result.returncode == 0:
            return "Successfully set Finder tags"
        else:
            return f"Failed to set Finder tags: {result.stderr}"
    except Exception as e:
        return f"Error setting Finder tags: {e}"

def test_upload_sequence(test_file_path):
    """Test the sequence of operations that happen during upload."""
    print(f"Testing upload sequence on: {test_file_path}")
    print("=" * 60)
    
    # Step 1: Set initial Finder tags
    print("Step 1: Setting initial Finder tags...")
    test_tags = ["tag1", "tag2", "tag3"]
    result = set_test_finder_tags(test_file_path, test_tags)
    print(f"  Result: {result}")
    
    # Step 2: Check initial state
    print("\nStep 2: Checking initial state...")
    finder_tags = check_finder_tags(test_file_path)
    print(f"  Finder tags: {finder_tags}")
    exif_tags = check_exif_tags(test_file_path)
    print(f"  EXIF tags: {exif_tags}")
    
    # Step 3: Simulate upload - write public_id metadata
    print("\nStep 3: Simulating upload - writing public_id metadata...")
    test_public_id = "test_upload_12345"
    metadata_result = write_cloudinary_metadata_to_file(
        test_file_path, 
        test_public_id, 
        tags=test_tags  # This is what the upload handler does
    )
    print(f"  Metadata write result: {metadata_result}")
    
    # Step 4: Check state after metadata write
    print("\nStep 4: Checking state after metadata write...")
    finder_tags_after = check_finder_tags(test_file_path)
    print(f"  Finder tags after: {finder_tags_after}")
    exif_tags_after = check_exif_tags(test_file_path)
    print(f"  EXIF tags after: {exif_tags_after}")
    
    # Step 5: Verify public_id was written
    print("\nStep 5: Verifying public_id was written...")
    public_id_result = get_cloudinary_public_id_from_metadata(test_file_path)
    print(f"  Public ID retrieved: {public_id_result}")
    
    # Step 6: Analysis
    print("\nStep 6: Analysis...")
    if "No Finder tags found" in finder_tags_after and "Finder tags found" in finder_tags:
        print("  ❌ ISSUE CONFIRMED: Finder tags were cleared during metadata write!")
    elif finder_tags == finder_tags_after:
        print("  ✅ Finder tags preserved during metadata write")
    else:
        print("  ⚠️  Finder tags changed during metadata write")
    
    return metadata_result

def main():
    """Main test function."""
    # Use test image or create one if needed
    test_file = "test_cross_platform.jpg"
    
    if not os.path.exists(test_file):
        print(f"Test file {test_file} not found. Please provide a test image file.")
        return
    
    try:
        test_upload_sequence(test_file)
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
