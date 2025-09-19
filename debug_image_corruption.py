#!/usr/bin/env python3
"""
Debug script to investigate image corruption issue with test_finder_tags_demo.jpg
This script will analyze the image properties and test different conversion methods.
"""

import os
import sys
from PIL import Image
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

def debug_image_properties(image_path):
    """Analyze the image properties that might cause conversion issues."""
    print(f"\n=== ANALYZING IMAGE: {os.path.basename(image_path)} ===")
    
    try:
        # PIL Image analysis
        with Image.open(image_path) as pil_img:
            print(f"\nPIL Image Properties:")
            print(f"  Mode: {pil_img.mode}")
            print(f"  Size: {pil_img.size}")
            print(f"  Format: {pil_img.format}")
            print(f"  Has transparency: {pil_img.mode in ('RGBA', 'LA') or 'transparency' in pil_img.info}")
            print(f"  Color profile: {'icc_profile' in pil_img.info}")
            if 'icc_profile' in pil_img.info:
                print(f"  ICC profile size: {len(pil_img.info['icc_profile'])} bytes")
            
            # Try different conversion methods
            print(f"\n=== Testing PIL to QImage Conversion Methods ===")
            
            # Method 1: Direct conversion (current failing method)
            try:
                if pil_img.mode != 'RGB':
                    rgb_img = pil_img.convert('RGB')
                else:
                    rgb_img = pil_img
                
                width, height = rgb_img.size
                bytes_per_line = 3 * width
                
                # This is the method currently failing
                qimage = QImage(rgb_img.tobytes('raw', 'RGB'), width, height, bytes_per_line, QImage.Format_RGB888)
                print(f"  ✓ Method 1 (current): Success - {qimage.width()}x{qimage.height()}")
                
            except Exception as e:
                print(f"  ✗ Method 1 (current): Failed - {str(e)}")
            
            # Method 2: Convert to RGBA first
            try:
                rgba_img = pil_img.convert('RGBA')
                width, height = rgba_img.size
                bytes_per_line = 4 * width
                
                qimage = QImage(rgba_img.tobytes('raw', 'RGBA'), width, height, bytes_per_line, QImage.Format_RGBA8888)
                print(f"  ✓ Method 2 (RGBA): Success - {qimage.width()}x{qimage.height()}")
                
            except Exception as e:
                print(f"  ✗ Method 2 (RGBA): Failed - {str(e)}")
            
            # Method 3: Use BGR format instead of RGB
            try:
                if pil_img.mode != 'RGB':
                    rgb_img = pil_img.convert('RGB')
                else:
                    rgb_img = pil_img
                
                width, height = rgb_img.size
                bytes_per_line = 3 * width
                
                # Try BGR format which Qt might handle better
                qimage = QImage(rgb_img.tobytes('raw', 'BGR'), width, height, bytes_per_line, QImage.Format_RGB888)
                print(f"  ✓ Method 3 (BGR): Success - {qimage.width()}x{qimage.height()}")
                
            except Exception as e:
                print(f"  ✗ Method 3 (BGR): Failed - {str(e)}")
                
            # Method 4: Remove color profile and try again
            try:
                clean_img = pil_img.copy()
                # Remove ICC profile
                if 'icc_profile' in clean_img.info:
                    del clean_img.info['icc_profile']
                
                if clean_img.mode != 'RGB':
                    clean_img = clean_img.convert('RGB')
                
                width, height = clean_img.size
                bytes_per_line = 3 * width
                
                qimage = QImage(clean_img.tobytes('raw', 'RGB'), width, height, bytes_per_line, QImage.Format_RGB888)
                print(f"  ✓ Method 4 (no ICC): Success - {qimage.width()}x{qimage.height()}")
                
            except Exception as e:
                print(f"  ✗ Method 4 (no ICC): Failed - {str(e)}")
        
        # QPixmap direct load (this works)
        print(f"\n=== Testing QPixmap Direct Load ===")
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                print(f"  ✓ QPixmap direct: Success - {pixmap.width()}x{pixmap.height()}")
            else:
                print(f"  ✗ QPixmap direct: Failed - null pixmap")
        except Exception as e:
            print(f"  ✗ QPixmap direct: Failed - {str(e)}")
            
    except Exception as e:
        print(f"  ✗ Could not open image: {str(e)}")

def main():
    """Main debug function."""
    # Test the problematic image
    test_image = r"D:\Python playfolder\happyTag\test images\test_finder_tags_demo.jpg"
    
    if not os.path.exists(test_image):
        print(f"Error: Test image not found at {test_image}")
        return
    
    debug_image_properties(test_image)
    
    # Also test a working image for comparison if available
    working_images = [
        r"D:\Python playfolder\happyTag\test images\CopyrightLuca Piffaretti_A.jpg",
        r"D:\Python playfolder\happyTag\test images\CopyrightLuca Piffaretti_B.jpg"
    ]
    
    for working_image in working_images:
        if os.path.exists(working_image):
            debug_image_properties(working_image)
            break

if __name__ == "__main__":
    main()