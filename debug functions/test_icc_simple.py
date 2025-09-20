#!/usr/bin/env python3
"""
Simple test of the ICC profile conversion logic without Qt dependency
"""

import os
from PIL import Image, ImageOps, ImageCms

def test_icc_conversion_simple():
    """Test just the ICC conversion part without Qt"""
    
    test_image_path = r"d:\Python playfolder\happyTag\test images\Archway_highRes_002.jpg"
    
    if not os.path.exists(test_image_path):
        print("ERROR: Could not find test image")
        return False
    
    print(f"Testing ICC conversion on: {test_image_path}")
    
    try:
        with Image.open(test_image_path) as img:
            print(f"Original: {img.size}, {img.mode}")
            
            # Apply EXIF orientation correction first
            img_corrected = ImageOps.exif_transpose(img)
            print(f"After EXIF: {img_corrected.size}")
            
            # Check ICC profile
            if 'icc_profile' in img_corrected.info:
                icc_size = len(img_corrected.info['icc_profile'])
                print(f"Has ICC profile: {icc_size} bytes")
                
                # Save original with ICC
                img_corrected.save("test_with_icc.jpg", quality=95)
                print("Saved: test_with_icc.jpg (with ICC profile)")
                
                # Method 1: Convert with ImageCms (our current approach)
                try:
                    srgb_profile = ImageCms.createProfile('sRGB')
                    img_converted = ImageCms.profileToProfile(img_corrected, srgb_profile, outputProfile=srgb_profile, outputMode='RGB')
                    if img_converted:
                        img_converted.save("test_icc_converted.jpg", quality=95)
                        print("Saved: test_icc_converted.jpg (ICC converted to sRGB)")
                        print(f"Converted image: {img_converted.size}, {img_converted.mode}")
                    else:
                        print("ICC conversion returned None")
                except Exception as e:
                    print(f"ICC conversion failed: {e}")
                
                # Method 2: Just remove ICC profile (old approach)
                img_no_icc = img_corrected.copy()
                if 'icc_profile' in img_no_icc.info:
                    del img_no_icc.info['icc_profile']
                img_no_icc.save("test_icc_removed.jpg", quality=95)
                print("Saved: test_icc_removed.jpg (ICC profile removed)")
                
                # Method 3: Convert to sRGB explicitly without profile conversion
                img_srgb = img_corrected.convert('RGB')
                # Remove ICC profile from the converted image
                if 'icc_profile' in img_srgb.info:
                    del img_srgb.info['icc_profile']
                img_srgb.save("test_convert_rgb.jpg", quality=95)
                print("Saved: test_convert_rgb.jpg (converted to RGB, no ICC)")
                
            else:
                print("No ICC profile found")
                
            print("\nTest completed. Check the generated images for visual differences.")
            return True
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    os.chdir(r"d:\Python playfolder\happyTag")
    test_icc_conversion_simple()