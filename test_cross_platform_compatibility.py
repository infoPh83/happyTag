#!/usr/bin/env python3
"""
Final test to verify cross-platform metadata compatibility
"""

import subprocess
import os
from PIL import Image

def create_sample_images():
    """Create sample images with different formats"""
    base_path = "/Volumes/Marketing/Simone Morciano/python working folder/happyTag/happyTag"
    
    # Create test images
    formats = [
        ('test_final.jpg', 'JPEG'),
        ('test_final.png', 'PNG'),
        ('test_final.tiff', 'TIFF')
    ]
    
    created_files = []
    for filename, format_name in formats:
        img = Image.new('RGB', (200, 200), color='green')
        file_path = os.path.join(base_path, filename)
        img.save(file_path, format_name)
        created_files.append(file_path)
        print(f"Created: {filename}")
    
    return created_files

def write_metadata_with_improved_method(file_path, keywords):
    """Write metadata using the improved cross-platform method"""
    exiftool_path = "/Volumes/Marketing/Simone Morciano/python working folder/happyTag/happyTag/packages/Image-ExifTool-13.34/exiftool"
    
    file_ext = os.path.splitext(file_path)[1].lower()
    print(f"\nWriting metadata to {os.path.basename(file_path)} ({file_ext})...")
    
    try:
        # 1. Write IPTC Keywords (semicolon-separated for legacy compatibility)
        keywords_str = ';'.join(keywords)
        subprocess.run([exiftool_path, f'-IPTC:Keywords={keywords_str}', '-overwrite_original', file_path], 
                      check=True, capture_output=True)
        
        # 2. Write XMP Keywords (semicolon-separated for some applications)
        subprocess.run([exiftool_path, f'-XMP:Keywords={keywords_str}', '-overwrite_original', file_path], 
                      check=True, capture_output=True)
        
        # 3. Write XMP-dc:Subject as individual array elements (for macOS Finder)
        # Clear first
        subprocess.run([exiftool_path, '-XMP-dc:Subject=', '-overwrite_original', file_path], 
                      check=True, capture_output=True)
        # Add each keyword
        for keyword in keywords:
            subprocess.run([exiftool_path, f'-XMP-dc:Subject+={keyword}', '-overwrite_original', file_path], 
                          check=True, capture_output=True)
        
        # 4. Write XMP:Subject as individual array elements (for Windows Explorer)
        # Clear first
        subprocess.run([exiftool_path, '-XMP:Subject=', '-overwrite_original', file_path], 
                      check=True, capture_output=True)
        # Add each keyword
        for keyword in keywords:
            subprocess.run([exiftool_path, f'-XMP:Subject+={keyword}', '-overwrite_original', file_path], 
                          check=True, capture_output=True)
        
        print("✅ Metadata written successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error writing metadata: {e}")
        return False

def analyze_cross_platform_compatibility(file_path):
    """Analyze the metadata for cross-platform compatibility"""
    exiftool_path = "/Volumes/Marketing/Simone Morciano/python working folder/happyTag/happyTag/packages/Image-ExifTool-13.34/exiftool"
    
    print(f"\nCross-platform compatibility analysis for {os.path.basename(file_path)}:")
    print("=" * 70)
    
    # Check key fields for different platforms
    compatibility_fields = [
        ("IPTC:Keywords", "Legacy applications"),
        ("XMP:Keywords", "General XMP applications"),
        ("XMP:Subject", "Windows Explorer, Adobe apps"),
        ("XMP-dc:Subject", "macOS Finder, Dublin Core compatible apps"),
    ]
    
    for field, platform in compatibility_fields:
        try:
            result = subprocess.run([exiftool_path, f"-{field}", file_path], 
                                   capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            if output and not output.startswith("Warning"):
                # Extract just the value part
                if ':' in output:
                    value = output.split(':', 1)[1].strip()
                    print(f"✅ {field:15} = {value}")
                    print(f"   📱 Compatible with: {platform}")
                else:
                    print(f"✅ {field:15} = {output}")
            else:
                print(f"❌ {field:15} = (not set)")
        except subprocess.CalledProcessError:
            print(f"❌ {field:15} = (error reading)")
        print()
    
    # Test Spotlight/macOS metadata extraction
    print("macOS Spotlight compatibility test:")
    print("-" * 40)
    try:
        # Use mdls to check what macOS Spotlight sees
        result = subprocess.run(['mdls', '-name', 'kMDItemKeywords', file_path], 
                               capture_output=True, text=True, check=True)
        spotlight_output = result.stdout.strip()
        if 'null' not in spotlight_output.lower():
            print(f"✅ Spotlight Keywords: {spotlight_output}")
        else:
            print(f"❌ Spotlight Keywords: Not detected by macOS Spotlight")
        
        # Check subject
        result = subprocess.run(['mdls', '-name', 'kMDItemSubject', file_path], 
                               capture_output=True, text=True, check=True)
        subject_output = result.stdout.strip()
        if 'null' not in subject_output.lower():
            print(f"✅ Spotlight Subject: {subject_output}")
        else:
            print(f"❌ Spotlight Subject: Not detected by macOS Spotlight")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error checking Spotlight compatibility: {e}")

def main():
    """Main test function"""
    print("Cross-Platform Metadata Compatibility Test")
    print("=" * 50)
    
    # Test keywords
    test_keywords = ['2023', 'Cafes & Restaurants', 'The Oxford Market']
    print(f"Test keywords: {test_keywords}")
    
    # Create test images
    print("\nCreating test images...")
    image_files = create_sample_images()
    
    # Write metadata to each image
    for image_file in image_files:
        success = write_metadata_with_improved_method(image_file, test_keywords)
        if success:
            analyze_cross_platform_compatibility(image_file)
    
    print("\n" + "=" * 70)
    print("SUMMARY:")
    print("If you see ✅ for XMP-dc:Subject, the tags should be visible in macOS Finder!")
    print("If you see ✅ for XMP:Subject, the tags should be visible in Windows Explorer!")
    print("The combination ensures maximum cross-platform compatibility.")
    print("=" * 70)

if __name__ == "__main__":
    main()
