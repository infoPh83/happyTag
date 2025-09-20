#!/usr/bin/env python3
"""
Isolated test for the specific image causing issues: Archway_highRes_002.jpg
This replicates the exact create_preview logic to identify the problem.
"""

import os
import sys
from PIL import Image, ImageOps, ImageCms
from PyQt5.QtGui import QImage, QPixmap

def test_archway_image():
    """Test the exact same logic as create_preview() on the problem image"""
    
    # Find the test image
    test_image_path = None
    possible_paths = [
        r"d:\Python playfolder\happyTag\test images\Archway_highRes_002.jpg",
        r"test images\Archway_highRes_002.jpg",
        r"test_images\Archway_highRes_002.jpg"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            test_image_path = path
            break
    
    if not test_image_path:
        print("ERROR: Could not find Archway_highRes_002.jpg")
        return False
    
    print(f"Testing image: {test_image_path}")
    print("=" * 60)
    
    MAX_PREVIEW_SIZE = 400  # Same as in main app
    
    try:
        with Image.open(test_image_path) as img:
            print(f"Original image info:")
            print(f"  Size: {img.size}")
            print(f"  Mode: {img.mode}")
            print(f"  Format: {img.format}")
            
            # Check for EXIF data
            if hasattr(img, '_getexif') and img._getexif():
                exif = img._getexif()
                orientation = exif.get(274, 1) if exif else 1
                print(f"  EXIF Orientation: {orientation}")
            else:
                print(f"  EXIF Orientation: None or 1 (normal)")
            
            # Check for ICC profile
            if 'icc_profile' in img.info:
                print(f"  ICC Profile: {len(img.info['icc_profile'])} bytes")
            else:
                print(f"  ICC Profile: None")
            
            print("\n" + "-" * 40)
            print("STEP 1: Apply EXIF orientation correction")
            print("-" * 40)
            
            # CRITICAL FIX: Apply EXIF orientation correction FIRST
            img_corrected = ImageOps.exif_transpose(img)
            orig_width, orig_height = img_corrected.size
            print(f"After EXIF correction: {orig_width}x{orig_height}")
            
            # Calculate preview dimensions
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
            
            print(f"Preview dimensions will be: {width}x{height}")
            
            print("\n" + "-" * 40)
            print("STEP 2: Handle ICC Profile")
            print("-" * 40)
            
            # Handle ICC color profiles that might cause Qt conversion issues
            if 'icc_profile' in img_corrected.info:
                print(f"Image has ICC profile ({len(img_corrected.info['icc_profile'])} bytes), converting to sRGB...")
                
                # Save the ICC profile version first (BEFORE conversion)
                img_corrected.save("debug_before_icc_conversion.jpg", quality=95)
                print("Saved: debug_before_icc_conversion.jpg")
                
                # CRITICAL FIX: Convert to sRGB color space instead of just removing profile
                try:
                    srgb_profile = ImageCms.createProfile('sRGB')
                    img_corrected = ImageCms.profileToProfile(img_corrected, srgb_profile, outputProfile=srgb_profile, outputMode='RGB')
                    print(f"Successfully converted ICC profile to sRGB")
                    
                    # Save the converted version
                    img_corrected.save("debug_after_icc_conversion.jpg", quality=95)
                    print("Saved: debug_after_icc_conversion.jpg")
                    
                except Exception as icc_error:
                    print(f"ICC conversion failed ({icc_error}), removing profile without conversion")
                    # Fallback: just remove the profile (original behavior)
                    img_corrected = img_corrected.copy()
                    if 'icc_profile' in img_corrected.info:
                        del img_corrected.info['icc_profile']
                        
                    # Save the profile-removed version
                    img_corrected.save("debug_profile_removed.jpg", quality=95)
                    print("Saved: debug_profile_removed.jpg")
            
            print("\n" + "-" * 40)
            print("STEP 3: Resize and Convert to QPixmap")
            print("-" * 40)
            
            # Optimize large image handling: resize with PIL first for better performance
            if orig_width > MAX_PREVIEW_SIZE or orig_height > MAX_PREVIEW_SIZE:
                print("Large image - resizing with PIL first")
                
                # Use LANCZOS for better quality
                try:
                    resample_filter = getattr(Image.Resampling, 'LANCZOS', getattr(Image, 'LANCZOS', 1))
                except AttributeError:
                    resample_filter = 1  # LANCZOS constant value
                
                resized_img = img_corrected.resize((width, height), resample_filter)
                print(f"Resized to: {resized_img.size}")
                
                # Save the resized version
                resized_img.save("debug_resized.jpg", quality=95)
                print("Saved: debug_resized.jpg")
                
                # Convert PIL image to QPixmap based on image mode
                if resized_img.mode == 'RGBA':
                    qimage = QImage(resized_img.tobytes(), resized_img.width, resized_img.height, QImage.Format_RGBA8888)
                    pixmap = QPixmap.fromImage(qimage)
                elif resized_img.mode == 'RGB':
                    # Ensure proper RGB byte order for Qt
                    rgb_data = resized_img.tobytes('raw', 'RGB')
                    qimage = QImage(rgb_data, resized_img.width, resized_img.height, QImage.Format_RGB888)
                    
                    # Verify QImage is not null and create QPixmap
                    if qimage.isNull():
                        print("ERROR: QImage is null!")
                        return False
                    else:
                        pixmap = QPixmap.fromImage(qimage)
                        print(f"Successfully created QPixmap: {pixmap.size().width()}x{pixmap.size().height()}")
                else:
                    # Convert other modes to RGB first
                    resized_img = resized_img.convert('RGB')
                    rgb_data = resized_img.tobytes('raw', 'RGB')
                    qimage = QImage(rgb_data, resized_img.width, resized_img.height, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimage)
                
                # Save the final QPixmap result
                pixmap.save("debug_final_qpixmap.jpg", "JPG")
                print("Saved: debug_final_qpixmap.jpg")
                
            else:
                print("Small image - converting directly")
                # For small images, also apply orientation correction but don't resize
                if img_corrected.mode == 'RGB':
                    rgb_data = img_corrected.tobytes('raw', 'RGB')
                    qimage = QImage(rgb_data, img_corrected.width, img_corrected.height, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimage)
                elif img_corrected.mode == 'RGBA':
                    qimage = QImage(img_corrected.tobytes(), img_corrected.width, img_corrected.height, QImage.Format_RGBA8888)
                    pixmap = QPixmap.fromImage(qimage)
                else:
                    # Convert other modes to RGB first
                    img_rgb = img_corrected.convert('RGB')
                    rgb_data = img_rgb.tobytes('raw', 'RGB')
                    qimage = QImage(rgb_data, img_rgb.width, img_rgb.height, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimage)
                
                # Save the final QPixmap result
                pixmap.save("debug_final_qpixmap.jpg", "JPG")
                print("Saved: debug_final_qpixmap.jpg")
            
            print("\n" + "=" * 60)
            print("SUMMARY:")
            print(f"  Original: {img.size} {img.mode}")
            print(f"  After EXIF: {orig_width}x{orig_height}")
            print(f"  Final preview: {width}x{height}")
            print(f"  QPixmap valid: {not pixmap.isNull()}")
            if not pixmap.isNull():
                print(f"  QPixmap size: {pixmap.size().width()}x{pixmap.size().height()}")
            
            return not pixmap.isNull()
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Make sure we're in the right directory
    os.chdir(r"d:\Python playfolder\happyTag")
    
    print("Testing Archway_highRes_002.jpg with exact create_preview logic")
    print("This will save intermediate steps to debug the issue")
    print()
    
    success = test_archway_image()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")