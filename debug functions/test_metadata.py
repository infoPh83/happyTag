#!/usr/bin/env python3
"""
Test script to analyze metadata reading from the test images
"""
import os
import sys

# Test what happens when we try to read metadata from these specific files
test_folder = "tag test images"
test_files = [f for f in os.listdir(test_folder) if f.endswith('.jpg')]

print(f"Found {len(test_files)} test files:")
for f in test_files:
    print(f"  - {f}")

print("\n" + "="*50)
print("Testing basic file access...")

# Test 1: Basic file access
for i, filename in enumerate(test_files[:3]):  # Test first 3 files
    file_path = os.path.join(test_folder, filename)
    try:
        file_size = os.path.getsize(file_path)
        print(f"✓ {filename}: {file_size} bytes")
        
        # Test reading first few bytes
        with open(file_path, 'rb') as f:
            header = f.read(10)
            print(f"  Header: {header}")
            
    except Exception as e:
        print(f"✗ {filename}: Error - {e}")

print("\n" + "="*50)
print("Testing IPTC library import...")

try:
    import iptcinfo3
    print("✓ iptcinfo3 imported successfully")
    IPTC_AVAILABLE = True
except ImportError as e:
    print(f"✗ iptcinfo3 import failed: {e}")
    IPTC_AVAILABLE = False

try:
    import pyexiv2
    print("✓ pyexiv2 imported successfully")
    EXIV2_AVAILABLE = True
except ImportError as e:
    print(f"✗ pyexiv2 import failed: {e}")
    EXIV2_AVAILABLE = False

print("\n" + "="*50)
print("Testing IPTC reading with first file only...")

if IPTC_AVAILABLE:
    first_file = os.path.join(test_folder, test_files[0])
    print(f"Testing: {first_file}")
    
    try:
        print("Attempting iptcinfo3.IPTCInfo with force=False...")
        info = iptcinfo3.IPTCInfo(first_file, force=False)
        if info:
            print("✓ IPTC info created successfully")
            if 'keywords' in info:
                print(f"✓ Keywords found: {info['keywords']}")
            else:
                print("- No keywords in IPTC data")
        else:
            print("- No IPTC info returned")
            
    except Exception as e:
        print(f"✗ IPTC force=False failed: {e}")
        print(f"   Exception type: {type(e)}")
        
        # Try to get more details
        import traceback
        print("Full traceback:")
        traceback.print_exc()

print("\n" + "="*50)
print("Testing XMP reading with first file...")

if EXIV2_AVAILABLE:
    first_file = os.path.join(test_folder, test_files[0])
    try:
        print("Attempting pyexiv2.Image...")
        with pyexiv2.Image(first_file) as img:
            print("✓ pyexiv2 image opened successfully")
            xmp_data = img.read_xmp()
            print(f"✓ XMP data read: {len(xmp_data)} entries")
            
            if 'Xmp.dc.subject' in xmp_data:
                print(f"✓ XMP keywords found: {xmp_data['Xmp.dc.subject']}")
            else:
                print("- No XMP keywords found")
                print("Available XMP keys:")
                for key in sorted(xmp_data.keys())[:10]:  # Show first 10 keys
                    print(f"  {key}: {xmp_data[key]}")
                    
    except Exception as e:
        print(f"✗ XMP reading failed: {e}")
        print(f"   Exception type: {type(e)}")
        
        import traceback
        print("Full traceback:")
        traceback.print_exc()

print("\n" + "="*50)
print("Test completed!")
