#!/usr/bin/env python3
"""
Test ICC Profile Color Conversion Fix
Test if the ICC profile to sRGB conversion fixes color distortion
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageOps, ImageCms
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap, QImage

def test_icc_profile_fix(image_path):
    """Test ICC profile conversion to sRGB"""
    print(f"🧪 Testing ICC Profile Fix for: {os.path.basename(image_path)}")
    print("=" * 60)
    
    app = QApplication([])
    
    try:
        with Image.open(image_path) as img:
            # Apply EXIF orientation correction
            img_corrected = ImageOps.exif_transpose(img)
            print(f"Original size: {img.size}")
            print(f"Corrected size: {img_corrected.size}")
            print(f"Image mode: {img_corrected.mode}")
            
            # Check for ICC profile
            has_icc = 'icc_profile' in img_corrected.info
            print(f"Has ICC profile: {has_icc}")
            if has_icc:
                print(f"ICC profile size: {len(img_corrected.info['icc_profile'])} bytes")
            
            # Method 1: Old approach (just remove ICC profile)
            print(f"\n📸 Method 1 - Remove ICC profile (old approach):")
            try:
                img1 = img_corrected.copy()
                if 'icc_profile' in img1.info:
                    del img1.info['icc_profile']
                    print("  ICC profile removed")
                
                # Convert to QPixmap
                if img1.mode == 'RGB':
                    rgb_data = img1.tobytes('raw', 'RGB')
                    qimage = QImage(rgb_data, img1.width, img1.height, QImage.Format_RGB888)
                    pixmap1 = QPixmap.fromImage(qimage)
                    print(f"  Result: {pixmap1.width()}x{pixmap1.height()}, valid: {not pixmap1.isNull()}")
                else:
                    print("  Non-RGB mode, converting to RGB")
                    img1 = img1.convert('RGB')
                    rgb_data = img1.tobytes('raw', 'RGB')
                    qimage = QImage(rgb_data, img1.width, img1.height, QImage.Format_RGB888)
                    pixmap1 = QPixmap.fromImage(qimage)
                    print(f"  Result: {pixmap1.width()}x{pixmap1.height()}, valid: {not pixmap1.isNull()}")
                    
            except Exception as e:
                print(f"  ERROR: {e}")
                pixmap1 = None
            
            # Method 2: New approach (convert ICC to sRGB)
            print(f"\n📸 Method 2 - Convert ICC to sRGB (new approach):")
            try:
                img2 = img_corrected.copy()
                
                if 'icc_profile' in img2.info:
                    print("  Converting ICC profile to sRGB...")
                    try:
                        srgb_profile = ImageCms.createProfile('sRGB')
                        img2 = ImageCms.profileToProfile(img2, srgb_profile, outputProfile=srgb_profile, outputMode='RGB')
                        print("  ✅ ICC to sRGB conversion successful")
                    except Exception as icc_error:
                        print(f"  ❌ ICC conversion failed: {icc_error}")
                        print("  Falling back to profile removal")
                        if 'icc_profile' in img2.info:
                            del img2.info['icc_profile']
                else:
                    print("  No ICC profile to convert")
                
                # Convert to QPixmap
                if img2.mode == 'RGB':
                    rgb_data = img2.tobytes('raw', 'RGB')
                    qimage = QImage(rgb_data, img2.width, img2.height, QImage.Format_RGB888)
                    pixmap2 = QPixmap.fromImage(qimage)
                    print(f"  Result: {pixmap2.width()}x{pixmap2.height()}, valid: {not pixmap2.isNull()}")
                else:
                    print("  Non-RGB mode, converting to RGB")
                    img2 = img2.convert('RGB')
                    rgb_data = img2.tobytes('raw', 'RGB')
                    qimage = QImage(rgb_data, img2.width, img2.height, QImage.Format_RGB888)
                    pixmap2 = QPixmap.fromImage(qimage)
                    print(f"  Result: {pixmap2.width()}x{pixmap2.height()}, valid: {not pixmap2.isNull()}")
                    
            except Exception as e:
                print(f"  ERROR: {e}")
                pixmap2 = None
            
            # Method 3: Direct QPixmap (reference)
            print(f"\n📸 Method 3 - Direct QPixmap (reference):")
            try:
                pixmap3 = QPixmap(image_path)
                print(f"  Result: {pixmap3.width()}x{pixmap3.height()}, valid: {not pixmap3.isNull()}")
            except Exception as e:
                print(f"  ERROR: {e}")
                pixmap3 = None
            
            print(f"\n📊 Analysis:")
            if has_icc:
                print("  🔍 Image has ICC profile - this could cause color distortion")
                print("  💡 Method 2 (sRGB conversion) should fix color issues")
            else:
                print("  ✅ Image has no ICC profile - color distortion unlikely from this cause")
            
            print(f"\n📈 Results:")
            print(f"  Method 1 (remove ICC): {'✅ Success' if pixmap1 and not pixmap1.isNull() else '❌ Failed'}")
            print(f"  Method 2 (convert ICC): {'✅ Success' if pixmap2 and not pixmap2.isNull() else '❌ Failed'}")
            print(f"  Method 3 (direct): {'✅ Success' if pixmap3 and not pixmap3.isNull() else '❌ Failed'}")
            
    except Exception as e:
        print(f"💥 Error: {e}")

def main():
    # Test with a real image that has ICC profile issues
    # You can also test with your portrait image path
    test_image = "debug functions/test_orientation_6.jpg"
    
    if os.path.exists(test_image):
        test_icc_profile_fix(test_image)
        
        # Also test with a different image if available
        print(f"\n" + "="*60)
        print("If you have a portrait image with ICC profile issues,")
        print("you can test it by modifying the test_image path in this script.")
    else:
        print(f"❌ Test image not found: {test_image}")

if __name__ == "__main__":
    main()