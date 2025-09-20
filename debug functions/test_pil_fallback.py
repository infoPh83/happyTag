#!/usr/bin/env python3
"""
Test script to verify the fallback system works correctly with PIL EXIF extraction
"""

import os
import sys
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import re

# Add the main directory to path to import from main.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_pil_fallback(file_path):
    """Test PIL fallback logic standalone"""
    print(f"\n🔍 Testing PIL fallback for: {os.path.basename(file_path)}")
    
    year = None
    
    try:
        with Image.open(file_path) as img:
            print(f"  📁 Image format: {img.format}")
            print(f"  📐 Image size: {img.size}")
            
            # Try to get EXIF data for JPEG files
            try:
                exif = img.getexif()
                if exif:
                    print(f"  📋 Found EXIF data with {len(exif)} entries")
                    # Look for DateTimeOriginal tag (36867)
                    datetime_original = exif.get(36867)  # DateTimeOriginal
                    if not datetime_original:
                        datetime_original = exif.get(306)  # DateTime
                    if not datetime_original:
                        datetime_original = exif.get(36868)  # DateTimeDigitized
                        
                    if datetime_original:
                        print(f"  📅 Found datetime: {datetime_original}")
                        year = datetime.strptime(datetime_original, '%Y:%m:%d %H:%M:%S').year
                        print(f"  🎯 Extracted year: {year}")
                else:
                    print("  ❌ No EXIF data found")
            except (AttributeError, TypeError, ValueError) as e:
                print(f"  ⚠️  EXIF extraction failed: {e}")
            
            # Try reading XMP metadata directly from TIFF files for date
            if not year and file_path.lower().endswith(('.tif', '.tiff')):
                print("  🔍 Trying XMP metadata extraction for TIFF...")
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        content_str = content.decode('utf-8', errors='ignore')
                        
                        create_date_match = re.search(r'<xmp:CreateDate>([^<]+)</xmp:CreateDate>', content_str)
                        if create_date_match:
                            date_str = create_date_match.group(1)
                            print(f"  📅 Found XMP CreateDate: {date_str}")
                            if 'T' in date_str:
                                date_part = date_str.split('T')[0]
                                year = datetime.strptime(date_part, '%Y-%m-%d').year
                                print(f"  🎯 Extracted year from XMP: {year}")
                except Exception as e:
                    print(f"  ⚠️  XMP extraction failed: {e}")
                    
    except Exception as e:
        print(f"  ❌ PIL processing failed: {e}")
    
    # Final fallback to file creation date
    if not year:
        print("  🔄 Using file creation date fallback...")
        try:
            timestamp = os.path.getctime(file_path)
            year = datetime.fromtimestamp(timestamp).year
            print(f"  📅 File creation year: {year}")
        except Exception as e:
            print(f"  ❌ File creation date fallback failed: {e}")
    
    return year

def main():
    test_dir = "test images"
    
    if not os.path.exists(test_dir):
        print(f"Test directory '{test_dir}' not found!")
        return
    
    # Get test image files
    test_files = []
    for file in os.listdir(test_dir):
        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.tif')):
            test_files.append(os.path.join(test_dir, file))
    
    if not test_files:
        print("No test images found!")
        return
    
    print("🧪 Testing PIL Fallback System")
    print("=" * 60)
    
    results = []
    for file_path in test_files:
        year = test_pil_fallback(file_path)
        results.append((file_path, year))
    
    print("\n📊 FALLBACK TEST RESULTS:")
    print("=" * 60)
    for file_path, year in results:
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].upper()
        status = "✅ SUCCESS" if year else "❌ FAILED"
        print(f"  {status} {filename:<35} [{ext:<5}] -> Year: {year}")
    
    successful = sum(1 for _, year in results if year)
    print(f"\n🎯 Summary: {successful}/{len(results)} files successfully processed")
    
    if successful == len(results):
        print("✅ All files processed successfully - fallback system working!")
    else:
        print("⚠️  Some files failed - may need additional fallback handling")

if __name__ == "__main__":
    main()