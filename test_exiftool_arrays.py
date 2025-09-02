#!/usr/bin/env python3
"""
Test ExifTool array writing directly to understand the correct syntax
"""

import subprocess
import os

def test_exiftool_array_writing():
    """Test different ways to write arrays with ExifTool"""
    
    # Create a test image first
    from PIL import Image
    test_path = "/Volumes/Marketing/Simone Morciano/python working folder/happyTag/happyTag/array_test.jpg"
    img = Image.new('RGB', (100, 100), color='blue')
    img.save(test_path, "JPEG")
    print(f"Created test image: {test_path}")
    
    exiftool_path = "/Volumes/Marketing/Simone Morciano/python working folder/happyTag/happyTag/packages/Image-ExifTool-13.34/exiftool"
    
    keywords = ['2023', 'Cafes & Restaurants', 'The Oxford Market']
    
    print("\nTesting different array writing methods:")
    print("=" * 50)
    
    # Method 1: Clear and add individual elements (what we're currently doing)
    print("Method 1: Clear + Individual additions")
    try:
        # Clear first
        subprocess.run([exiftool_path, '-XMP-dc:Subject=', '-overwrite_original', test_path], 
                      check=True, capture_output=True)
        # Add individual elements
        for keyword in keywords:
            subprocess.run([exiftool_path, f'-XMP-dc:Subject+={keyword}', '-overwrite_original', test_path], 
                          check=True, capture_output=True)
        
        # Check result
        result = subprocess.run([exiftool_path, '-XMP-dc:Subject', test_path], 
                               capture_output=True, text=True, check=True)
        print(f"Result: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    
    # Method 2: Single command with multiple -XMP-dc:Subject+=
    print("\nMethod 2: Multiple += in single command")
    try:
        # Clear and set all at once
        cmd = [exiftool_path, '-XMP-dc:Subject=', '-overwrite_original']
        for keyword in keywords:
            cmd.extend([f'-XMP-dc:Subject+={keyword}'])
        cmd.append(test_path)
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Check result
        result = subprocess.run([exiftool_path, '-XMP-dc:Subject', test_path], 
                               capture_output=True, text=True, check=True)
        print(f"Result: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    
    # Method 3: Using list syntax
    print("\nMethod 3: List syntax")
    try:
        # Try list syntax with quotes
        keywords_list = '", "'.join(keywords)
        keywords_formatted = f'["{keywords_list}"]'
        
        subprocess.run([exiftool_path, f'-XMP-dc:Subject={keywords_formatted}', '-overwrite_original', test_path], 
                      check=True, capture_output=True)
        
        # Check result
        result = subprocess.run([exiftool_path, '-XMP-dc:Subject', test_path], 
                               capture_output=True, text=True, check=True)
        print(f"Result: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    
    # Show all metadata fields
    print("\nFull metadata analysis:")
    print("-" * 30)
    try:
        result = subprocess.run([exiftool_path, '-XMP-dc:Subject', '-XMP:Subject', '-XMP:Keywords', '-IPTC:Keywords', test_path], 
                               capture_output=True, text=True, check=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error reading metadata: {e}")

if __name__ == "__main__":
    test_exiftool_array_writing()
