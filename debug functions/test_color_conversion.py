#!/usr/bin/env python3
"""
Test Color Space Conversion Issues
Debug the PIL to QImage conversion for color distortion
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageOps
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt

def test_color_conversion_methods(image_path):
    """Test different methods of converting PIL to QPixmap"""
    print(f"🧪 Testing Color Conversion for: {os.path.basename(image_path)}")
    print("=" * 60)
    
    app = QApplication([])
    
    try:
        with Image.open(image_path) as img:
            # Apply EXIF orientation correction
            img_corrected = ImageOps.exif_transpose(img)
            print(f"Original size: {img.size}")
            print(f"Corrected size: {img_corrected.size}")
            print(f"Image mode: {img_corrected.mode}")
            
            # Test Method 1: Current approach (potentially problematic)
            print(f"\n📸 Method 1 - Current RGB byte conversion:")
            try:
                if img_corrected.mode == 'RGB':
                    rgb_data = img_corrected.tobytes('raw', 'RGB')
                    qimage = QImage(rgb_data, img_corrected.width, img_corrected.height, QImage.Format_RGB888)
                    pixmap1 = QPixmap.fromImage(qimage)
                    print(f"  Result: QPixmap {pixmap1.width()}x{pixmap1.height()}, isNull: {pixmap1.isNull()}")
                else:
                    img_rgb = img_corrected.convert('RGB')
                    rgb_data = img_rgb.tobytes('raw', 'RGB')
                    qimage = QImage(rgb_data, img_rgb.width, img_rgb.height, QImage.Format_RGB888)
                    pixmap1 = QPixmap.fromImage(qimage)
                    print(f"  Result: QPixmap {pixmap1.width()}x{pixmap1.height()}, isNull: {pixmap1.isNull()}")
            except Exception as e:
                print(f"  ERROR: {e}")
                pixmap1 = None
            
            # Test Method 2: Using different byte order
            print(f"\n📸 Method 2 - RGB to BGR conversion:")
            try:
                if img_corrected.mode == 'RGB':
                    # Convert RGB to BGR (swap red and blue channels)
                    import numpy as np
                    rgb_array = np.array(img_corrected)
                    bgr_array = rgb_array[:, :, ::-1]  # Reverse the channel order
                    height, width, channel = bgr_array.shape
                    bytes_per_line = 3 * width
                    qimage = QImage(bgr_array.data.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
                    pixmap2 = QPixmap.fromImage(qimage)
                    print(f"  Result: QPixmap {pixmap2.width()}x{pixmap2.height()}, isNull: {pixmap2.isNull()}")
                else:
                    img_rgb = img_corrected.convert('RGB')
                    rgb_array = np.array(img_rgb)
                    bgr_array = rgb_array[:, :, ::-1]
                    height, width, channel = bgr_array.shape
                    bytes_per_line = 3 * width
                    qimage = QImage(bgr_array.data.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888)
                    pixmap2 = QPixmap.fromImage(qimage)
                    print(f"  Result: QPixmap {pixmap2.width()}x{pixmap2.height()}, isNull: {pixmap2.isNull()}")
            except Exception as e:
                print(f"  ERROR: {e}")
                pixmap2 = None
            
            # Test Method 3: Direct QPixmap loading (reference)
            print(f"\n📸 Method 3 - Direct QPixmap (reference):")
            try:
                pixmap3 = QPixmap(image_path)
                print(f"  Result: QPixmap {pixmap3.width()}x{pixmap3.height()}, isNull: {pixmap3.isNull()}")
                # Note: This won't have EXIF orientation correction
            except Exception as e:
                print(f"  ERROR: {e}")
                pixmap3 = None
            
            # Test Method 4: Using QImage.Format_RGB32
            print(f"\n📸 Method 4 - RGB32 format conversion:")
            try:
                if img_corrected.mode == 'RGB':
                    # Convert to RGBA first
                    img_rgba = img_corrected.convert('RGBA')
                    qimage = QImage(img_rgba.tobytes(), img_rgba.width, img_rgba.height, QImage.Format_RGBA8888)
                    pixmap4 = QPixmap.fromImage(qimage)
                    print(f"  Result: QPixmap {pixmap4.width()}x{pixmap4.height()}, isNull: {pixmap4.isNull()}")
                else:
                    img_rgba = img_corrected.convert('RGBA')
                    qimage = QImage(img_rgba.tobytes(), img_rgba.width, img_rgba.height, QImage.Format_RGBA8888)
                    pixmap4 = QPixmap.fromImage(qimage)
                    print(f"  Result: QPixmap {pixmap4.width()}x{pixmap4.height()}, isNull: {pixmap4.isNull()}")
            except Exception as e:
                print(f"  ERROR: {e}")
                pixmap4 = None
            
            print(f"\n📊 Summary:")
            print(f"  Method 1 (Current RGB): {'✅ Success' if pixmap1 and not pixmap1.isNull() else '❌ Failed'}")
            print(f"  Method 2 (BGR swap): {'✅ Success' if pixmap2 and not pixmap2.isNull() else '❌ Failed'}")
            print(f"  Method 3 (Direct): {'✅ Success' if pixmap3 and not pixmap3.isNull() else '❌ Failed'}")
            print(f"  Method 4 (RGBA): {'✅ Success' if pixmap4 and not pixmap4.isNull() else '❌ Failed'}")
            
    except Exception as e:
        print(f"💥 Error loading image: {e}")

def main():
    # Test with a portrait image that's showing issues
    test_image = "debug functions/test_orientation_6.jpg"
    
    if os.path.exists(test_image):
        test_color_conversion_methods(test_image)
    else:
        print(f"❌ Test image not found: {test_image}")
        print("Please run create_orientation_test_images.py first")

if __name__ == "__main__":
    main()