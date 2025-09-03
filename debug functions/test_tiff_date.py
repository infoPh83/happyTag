#!/usr/bin/env python3
"""
Test script to verify TIFF XMP date extraction functionality
"""

import os
import re
import sys
from datetime import datetime

def test_tiff_xmp_extraction(file_path):
    """Test XMP date extraction from a TIFF file"""
    print(f"Testing XMP extraction for: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None
        
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            # Convert to string for regex search (decode errors ignored)
            content_str = content.decode('utf-8', errors='ignore')
            
            # Look for XMP CreateDate tag
            create_date_match = re.search(r'<xmp:CreateDate>([^<]+)</xmp:CreateDate>', content_str)
            if create_date_match:
                date_str = create_date_match.group(1)
                print(f"Found XMP CreateDate: {date_str}")
                
                # Parse ISO format date (e.g., "2023-05-23T12:54:53+01:00")
                if 'T' in date_str:
                    date_part = date_str.split('T')[0]
                    year = datetime.strptime(date_part, '%Y-%m-%d').year
                    print(f"Extracted year: {year}")
                    return year
            else:
                print("No XMP CreateDate found")
                
                # Look for other possible date tags
                date_patterns = [
                    r'<xmp:MetadataDate>([^<]+)</xmp:MetadataDate>',
                    r'<xmp:ModifyDate>([^<]+)</xmp:ModifyDate>',
                    r'DateTimeOriginal>([^<]+)<',
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, content_str)
                    if match:
                        print(f"Found alternative date: {match.group(1)}")
                        break
                        
    except Exception as e:
        print(f"Error reading TIFF file: {e}")
    
    return None

if __name__ == "__main__":
    # Test with a sample TIFF file path
    # You can modify this path to test with your actual TIFF file
    test_file = "sample.tif"  # Replace with actual TIFF file path
    
    print("TIFF XMP Date Extraction Test")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    
    result = test_tiff_xmp_extraction(test_file)
    
    if result:
        print(f"\n✅ Successfully extracted year: {result}")
    else:
        print(f"\n❌ Could not extract year from: {test_file}")
