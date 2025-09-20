#!/usr/bin/env python3
"""
Direct Test of Portrait Orientation Fix
Test the EXIF orientation fix directly without the full app
"""

import os
from PIL import Image, ImageOps
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap, QImage

def test_create_preview_fixed(file_path):
    """Test the fixed create_preview logic directly"""
    MAX_PREVIEW_SIZE = 800
    
    print(f"Testing: {os.path.basename(file_path)}")
    
    try:
        with Image.open(file_path) as img:
            print(f"  Original PIL size: {img.size}")
            
            # Get EXIF orientation
            exif = img.getexif()
            orientation = exif.get(274, 1)
            print(f"  EXIF Orientation: {orientation}")
            
            # CRITICAL FIX: Apply EXIF orientation correction FIRST
            img_corrected = ImageOps.exif_transpose(img)
            orig_width, orig_height = img_corrected.size
            print(f"  After EXIF correction: {orig_width}x{orig_height}")
            
            # Calculate target size
            if orig_width > orig_height:
                if orig_width > MAX_PREVIEW_SIZE:
                    width = MAX_PREVIEW_SIZE
                    height = int(orig_height * (MAX_PREVIEW_SIZE / orig_width))
                else:
                    width = orig_width
                    height = orig_height
            else:
                if orig_height > MAX_PREVIEW_SIZE:
                    height = MAX_PREVIEW_SIZE
                    width = int(orig_width * (MAX_PREVIEW_SIZE / orig_height))
                else:
                    width = orig_width
                    height = orig_height
            
            print(f"  Target size: {width}x{height}")
            
            # Apply the fix for large images
            if orig_width > MAX_PREVIEW_SIZE or orig_height > MAX_PREVIEW_SIZE:
                try:
                    resample_filter = getattr(Image.Resampling, 'LANCZOS', getattr(Image, 'LANCZOS', 1))
                except AttributeError:
                    resample_filter = 1
                
                resized_img = img_corrected.resize((width, height), resample_filter)
                
                # Convert to QPixmap
                if resized_img.mode == 'RGB':
                    rgb_data = resized_img.tobytes('raw', 'RGB')
                    qimage = QImage(rgb_data, resized_img.width, resized_img.height, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimage)
                else:
                    resized_img = resized_img.convert('RGB')
                    rgb_data = resized_img.tobytes('raw', 'RGB')
                    qimage = QImage(rgb_data, resized_img.width, resized_img.height, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimage)
                print(f"  Used PIL resize: {orig_width}x{orig_height} -> {resized_img.width}x{resized_img.height}")
            else:
                # For small images, use orientation-corrected image
                if img_corrected.mode == 'RGB':
                    rgb_data = img_corrected.tobytes('raw', 'RGB')
                    qimage = QImage(rgb_data, img_corrected.width, img_corrected.height, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimage)
                else:
                    img_rgb = img_corrected.convert('RGB')
                    rgb_data = img_rgb.tobytes('raw', 'RGB')
                    qimage = QImage(rgb_data, img_rgb.width, img_rgb.height, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimage)
                print(f"  Used small image fix: {img.size} -> {orig_width}x{orig_height}")
            
            if not pixmap.isNull():
                print(f"  ✅ Final QPixmap size: {pixmap.width()}x{pixmap.height()}")
                
                # Analyze the result
                if orientation in [6, 8]:  # These should be portrait after correction
                    if pixmap.height() > pixmap.width():
                        print(f"  🎯 SUCCESS: Portrait orientation corrected! (H:{pixmap.height()} > W:{pixmap.width()})")
                        return True
                    else:
                        print(f"  ❌ FAIL: Still appears landscape (W:{pixmap.width()} >= H:{pixmap.height()})")
                        return False
                else:
                    print(f"  ℹ️  Non-portrait orientation, result looks correct")
                    return True
            else:
                print(f"  ❌ Failed to create QPixmap")
                return False
                
    except Exception as e:
        print(f"  💥 Error: {e}")
        return False

def main():
    # Initialize QApplication (required for QPixmap operations)
    app = QApplication([])
    
    print("🧪 Testing Portrait Orientation Fix (Direct)")
    print("=" * 60)
    
    # Test with our orientation test images
    test_files = [
        "debug functions/test_orientation_1.jpg",  # Normal (0°)
        "debug functions/test_orientation_6.jpg",  # 90° clockwise (should become portrait)
        "debug functions/test_orientation_8.jpg",  # 270° clockwise (should become portrait)
    ]
    
    results = []
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n📸 {'-' * 40}")
            success = test_create_preview_fixed(test_file)
            results.append((test_file, success))
        else:
            print(f"\n❌ Test file not found: {test_file}")
            results.append((test_file, False))
    
    print(f"\n{'=' * 60}")
    print("📊 SUMMARY:")
    for test_file, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {os.path.basename(test_file)}: {status}")
    
    # Count successes
    successes = sum(1 for _, success in results if success)
    print(f"\n🎯 Portrait orientation fix: {successes}/{len(results)} tests passed")
    
    if successes == len(results):
        print("🎉 All tests passed! Portrait orientation fix is working!")
    else:
        print("⚠️  Some tests failed. Check the implementation.")

if __name__ == "__main__":
    main()