#!/usr/bin/env python3
"""
Simple script to completely clean and reset keywords on the corrupted test image
"""

import subprocess
import sys
import os

def run_exiftool(args):
    """Run ExifTool command and return result"""
    exiftool_path = "/Volumes/Marketing/Simone Morciano/python working folder/happyTag/happyTag/packages/Image-ExifTool-13.34/exiftool"
    
    cmd = [exiftool_path] + args
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Result: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Stderr: {e.stderr}")
        return None

def clean_keywords(file_path):
    """Completely clean all keyword fields from an image"""
    print(f"\n=== CLEANING KEYWORDS FROM {file_path} ===")
    
    # First, let's see what's currently in the file
    print("\n1. Current keywords:")
    run_exiftool(['-IPTC:Keywords', '-XMP:Keywords', '-XMP-dc:Subject', '-XMP:Subject', file_path])
    
    # Clear ALL keyword fields
    print("\n2. Clearing all keyword fields:")
    run_exiftool([
        '-IPTC:Keywords=',
        '-XMP:Keywords=', 
        '-XMP-dc:Subject=',
        '-XMP:Subject=',
        '-overwrite_original',
        file_path
    ])
    
    # Check if cleared
    print("\n3. After clearing:")
    run_exiftool(['-IPTC:Keywords', '-XMP:Keywords', '-XMP-dc:Subject', '-XMP:Subject', file_path])
    
    # Set simple test keywords
    print("\n4. Setting simple test keywords:")
    run_exiftool([
        '-IPTC:Keywords=CLEAN TEST',
        '-XMP:Keywords=CLEAN TEST',
        '-XMP-dc:Subject=CLEAN TEST',
        '-XMP:Subject=CLEAN TEST',
        '-overwrite_original',
        file_path
    ])
    
    # Final check
    print("\n5. Final result:")
    run_exiftool(['-IPTC:Keywords', '-XMP:Keywords', '-XMP-dc:Subject', '-XMP:Subject', file_path])
    
    print("\n=== CLEANING COMPLETE ===")

if __name__ == "__main__":
    test_image = "/Volumes/Marketing/Simone Morciano/python working folder/happyTag/happyTag/test images/1.jpg"
    
    if not os.path.exists(test_image):
        print(f"Error: {test_image} not found!")
        sys.exit(1)
    
    clean_keywords(test_image)
