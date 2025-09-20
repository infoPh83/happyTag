#!/usr/bin/env python3
"""
Test QImage bytes_per_line Issues
Check if missing bytes_per_line parameter is causing distortion
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageOps
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap, QImage

def test_bytes_per_line_issue(image_path):
    """Test if missing bytes_per_line causes distortion"""
    print(f"🧪 Testing bytes_per_line for: {os.path.basename(image_path)}")
    print("=" * 60)
    
    app = QApplication([])
    
    try:
        with Image.open(image_path) as img:
            img_corrected = ImageOps.exif_transpose(img)
            
            if img_corrected.mode != 'RGB':
                img_corrected = img_corrected.convert('RGB')
            
            print(f"Image size: {img_corrected.width}x{img_corrected.height}")
            print(f"Image mode: {img_corrected.mode}")
            
            # Method 1: Current approach (NO bytes_per_line) - POTENTIALLY PROBLEMATIC
            print(f"\n📸 Method 1 - WITHOUT bytes_per_line (current approach):")
            try:
                rgb_data = img_corrected.tobytes('raw', 'RGB')
                qimage1 = QImage(rgb_data, img_corrected.width, img_corrected.height, QImage.Format_RGB888)
                pixmap1 = QPixmap.fromImage(qimage1)
                print(f"  RGB data length: {len(rgb_data)}")
                print(f"  Expected length: {img_corrected.width * img_corrected.height * 3}")
                print(f"  QImage valid: {not qimage1.isNull()}")
                print(f"  QPixmap size: {pixmap1.width()}x{pixmap1.height()}")
                print(f"  QPixmap valid: {not pixmap1.isNull()}")
            except Exception as e:
                print(f"  ERROR: {e}")
                pixmap1 = None
            
            # Method 2: WITH bytes_per_line (CORRECT approach)
            print(f"\n📸 Method 2 - WITH bytes_per_line (correct approach):")
            try:
                rgb_data = img_corrected.tobytes('raw', 'RGB')
                bytes_per_line = img_corrected.width * 3  # 3 bytes per pixel for RGB
                qimage2 = QImage(rgb_data, img_corrected.width, img_corrected.height, bytes_per_line, QImage.Format_RGB888)
                pixmap2 = QPixmap.fromImage(qimage2)
                print(f"  RGB data length: {len(rgb_data)}")
                print(f"  Bytes per line: {bytes_per_line}")
                print(f"  QImage valid: {not qimage2.isNull()}")
                print(f"  QPixmap size: {pixmap2.width()}x{pixmap2.height()}")
                print(f"  QPixmap valid: {not pixmap2.isNull()}")
            except Exception as e:
                print(f"  ERROR: {e}")
                pixmap2 = None
            
            # Method 3: Test with non-standard width (padding issues)
            print(f"\n📸 Method 3 - Testing potential padding issues:")
            try:
                # Create a slightly non-standard size to test padding
                test_width = img_corrected.width
                test_height = img_corrected.height
                
                print(f"  Width: {test_width} (width % 4 = {test_width % 4})")
                print(f"  Height: {test_height}")
                
                # Some systems expect scanlines to be padded to 4-byte boundaries
                aligned_width = (test_width + 3) & ~3  # Round up to nearest multiple of 4
                print(f"  4-byte aligned width: {aligned_width}")
                
                if aligned_width != test_width:
                    print(f"  ⚠️  Width alignment mismatch may cause distortion!")
                else:
                    print(f"  ✅ Width is already 4-byte aligned")
                    
            except Exception as e:
                print(f"  ERROR: {e}")
            
            print(f"\n📊 Analysis:")
            if pixmap1 and pixmap2:
                if pixmap1.isNull() and not pixmap2.isNull():
                    print("  🔴 Method 1 (no bytes_per_line) failed, Method 2 (with bytes_per_line) succeeded")
                    print("  💡 FIX: Add bytes_per_line parameter to QImage constructor")
                elif not pixmap1.isNull() and not pixmap2.isNull():
                    print("  🟡 Both methods succeeded - distortion may be elsewhere")
                    print("  💡 Check color space, ICC profiles, or pixel format issues")
                else:
                    print("  🔴 Both methods had issues")
            
    except Exception as e:
        print(f"💥 Error: {e}")

def main():
    test_image = "debug functions/test_orientation_6.jpg"
    
    if os.path.exists(test_image):
        test_bytes_per_line_issue(test_image)
    else:
        print(f"❌ Test image not found: {test_image}")

if __name__ == "__main__":
    main()