#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import ExifTool module
import exiftool as et

def test_webp_array_fix():
    """Test the new XMP Subject array structure for WebP files"""
    
    webp_file = r"tag test images\01\webP_from_raw_NO_INITIAL_TAGS.webp"
    
    if not os.path.exists(webp_file):
        print(f"WebP file not found: {webp_file}")
        return
    
    print(f"Testing XMP Subject array fix on: {webp_file}")
    
    try:
        # Use local ExifTool
        exiftool_path = r"packages\exiftool_win64\exiftool-13.34_64\exiftool(-k).exe"
        
        with et.ExifTool(executable=exiftool_path) as exiftool:
            # Test keywords
            test_keywords = ["2025", "WebP", "Windows", "Compatible"]
            
            print(f"\n=== BEFORE: Reading existing metadata ===")
            subject_before = exiftool.execute('-XMP:Subject', webp_file)
            print(f"XMP:Subject before: {subject_before}")
            
            print(f"\n=== FIXING: Writing keywords as individual array elements ===")
            
            # Clear existing subject first
            print("Clearing existing XMP:Subject...")
            exiftool.execute('-XMP:Subject=', '-overwrite_original', webp_file)
            
            # Add each keyword as separate array element
            for keyword in test_keywords:
                print(f"Adding keyword: {keyword}")
                exiftool.execute(f'-XMP:Subject+={keyword}', '-overwrite_original', webp_file)
            
            print(f"\n=== AFTER: Reading updated metadata ===")
            
            # Read back the updated metadata
            subject_after = exiftool.execute('-XMP:Subject', webp_file)
            print(f"XMP:Subject after: {subject_after}")
            
            # Read XMP structure to see the array format
            print(f"\n=== RAW XMP STRUCTURE ===")
            xmp_raw = exiftool.execute('-XMP', '-b', webp_file)
            if xmp_raw and 'dc:subject' in xmp_raw:
                # Extract just the subject section
                start = xmp_raw.find('<dc:subject>')
                end = xmp_raw.find('</dc:subject>') + len('</dc:subject>')
                if start != -1 and end != -1:
                    subject_xml = xmp_raw[start:end]
                    print("Subject XML structure:")
                    print(subject_xml)
                else:
                    print("Subject section in full XMP:")
                    # Look for rdf:Bag structure
                    if 'rdf:Bag' in xmp_raw:
                        lines = xmp_raw.split('\n')
                        in_subject = False
                        for line in lines:
                            if '<dc:subject>' in line:
                                in_subject = True
                            if in_subject:
                                print(line.strip())
                            if '</dc:subject>' in line:
                                in_subject = False
                                break
            
            print(f"\n=== VERIFICATION ===")
            print("The XMP:Subject should now show individual keywords as separate entries")
            print("Windows Explorer should be able to read these tags!")
            
    except Exception as e:
        print(f"Error testing WebP fix: {e}")

if __name__ == "__main__":
    test_webp_array_fix()
