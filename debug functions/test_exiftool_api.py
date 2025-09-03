#!/usr/bin/env python3

import exiftool
import os

# Test ExifTool API to understand correct methods
exiftool_path = r'packages\exiftool_win64\exiftool-13.34_64\exiftool(-k).exe'
test_image = r'tag test images\CC 001.jpg'

print("Testing PyExifTool API...")

try:
    with exiftool.ExifTool(executable=exiftool_path) as et:
        print("ExifTool started successfully")
        
        # Check available methods
        methods = [m for m in dir(et) if not m.startswith('_') and callable(getattr(et, m))]
        print(f"Available methods: {methods}")
        
        # Try different approaches to read metadata
        print("\n1. Testing execute method:")
        try:
            result = et.execute("-j", test_image)
            print(f"execute result: {result}")
        except Exception as e:
            print(f"execute failed: {e}")
        
        print("\n2. Testing get_metadata method:")
        try:
            result = et.get_metadata(test_image)
            print(f"get_metadata result: {result}")
        except Exception as e:
            print(f"get_metadata failed: {e}")
        
        print("\n3. Testing get_tags method:")
        try:
            result = et.get_tags(['IPTC:Keywords', 'XMP:Subject'], test_image)
            print(f"get_tags result: {result}")
        except Exception as e:
            print(f"get_tags failed: {e}")
        
        print("\n4. Testing get_tag method:")
        try:
            result = et.get_tag('IPTC:Keywords', test_image)
            print(f"get_tag result: {result}")
        except Exception as e:
            print(f"get_tag failed: {e}")

except Exception as e:
    print(f"Failed to initialize ExifTool: {e}")
