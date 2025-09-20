#!/usr/bin/env python3
"""
Test Portrait Orientation Issue
Debug script to identify and fix corrupted portrait image previews
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageOps
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt

def analyze_image_orientation(file_path):
    """Analyze an image's orientation and EXIF data"""
    print(f"\n=== ANALYZING: {os.path.basename(file_path)} ===")
    
    try:
        with Image.open(file_path) as img:
            # Basic info
            print(f"PIL Size: {img.size} (width x height)")
            print(f"PIL Mode: {img.mode}")
            print(f"PIL Format: {img.format}")
            
            # Check for EXIF orientation
            exif = img.getexif()
            orientation = exif.get(274, 1)  # 274 is the EXIF orientation tag
            print(f"EXIF Orientation: {orientation}")
            
            orientation_descriptions = {
                1: "Normal (0°)",
                2: "Mirrored horizontally",
                3: "Rotated 180°",
                4: "Mirrored vertically", 
                5: "Mirrored horizontally + rotated 270°",
                6: "Rotated 90° clockwise",
                7: "Mirrored horizontally + rotated 90°",
                8: "Rotated 270° clockwise (90° counter-clockwise)"
            }
            
            print(f"Orientation meaning: {orientation_descriptions.get(orientation, 'Unknown')}")
            
            # Test PIL with and without EXIF auto-orientation
            print("\n--- PIL WITHOUT auto-orientation ---")
            print(f"Size: {img.size}")
            
            print("\n--- PIL WITH ImageOps.exif_transpose ---")
            img_corrected = ImageOps.exif_transpose(img)
            print(f"Size: {img_corrected.size}")
            print(f"Size changed: {img.size != img_corrected.size}")
            
            return {
                'original_size': img.size,
                'corrected_size': img_corrected.size,
                'orientation': orientation,
                'orientation_desc': orientation_descriptions.get(orientation, 'Unknown'),
                'needs_correction': img.size != img_corrected.size,
                'corrected_image': img_corrected.copy()
            }
            
    except Exception as e:
        print(f"ERROR analyzing {file_path}: {e}")
        return None

def create_test_previews(file_path):
    """Create test previews with and without orientation correction"""
    print(f"\n=== CREATING TEST PREVIEWS FOR: {os.path.basename(file_path)} ===")
    
    try:
        with Image.open(file_path) as img:
            # Preview 1: Current method (no orientation correction)
            print("\n--- Creating preview WITHOUT orientation correction ---")
            preview_uncorrected = create_preview_uncorrected(img)
            
            # Preview 2: Fixed method (with orientation correction)
            print("\n--- Creating preview WITH orientation correction ---")
            preview_corrected = create_preview_corrected(img)
            
            return preview_uncorrected, preview_corrected
            
    except Exception as e:
        print(f"ERROR creating previews for {file_path}: {e}")
        return None, None

def create_preview_uncorrected(img):
    """Simulate current preview creation method (problematic)"""
    MAX_PREVIEW_SIZE = 800
    orig_width, orig_height = img.size
    
    # Calculate size (current logic from main.py)
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
    
    # Resize without orientation correction (current problematic method)
    if orig_width > MAX_PREVIEW_SIZE or orig_height > MAX_PREVIEW_SIZE:
        try:
            resample_filter = getattr(Image.Resampling, 'LANCZOS', getattr(Image, 'LANCZOS', 1))
        except AttributeError:
            resample_filter = 1
        
        resized_img = img.resize((width, height), resample_filter)
        
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
    else:
        pixmap = QPixmap(img.filename) if hasattr(img, 'filename') else None
    
    print(f"Uncorrected preview size: {pixmap.width()}x{pixmap.height()}" if pixmap else "Failed to create uncorrected preview")
    return pixmap

def create_preview_corrected(img):
    """Create preview with proper orientation correction (fixed method)"""
    MAX_PREVIEW_SIZE = 800
    
    # CRITICAL FIX: Apply EXIF orientation correction FIRST
    img_corrected = ImageOps.exif_transpose(img)
    orig_width, orig_height = img_corrected.size  # Use corrected dimensions
    
    print(f"After orientation correction: {orig_width}x{orig_height}")
    
    # Calculate size (using corrected dimensions)
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
    
    # Resize with orientation-corrected image
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
    else:
        # For small images, still need to create QPixmap from corrected PIL image
        if img_corrected.mode == 'RGB':
            rgb_data = img_corrected.tobytes('raw', 'RGB')
            qimage = QImage(rgb_data, img_corrected.width, img_corrected.height, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
        else:
            img_rgb = img_corrected.convert('RGB')
            rgb_data = img_rgb.tobytes('raw', 'RGB')
            qimage = QImage(rgb_data, img_rgb.width, img_rgb.height, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
    
    print(f"Corrected preview size: {pixmap.width()}x{pixmap.height()}" if pixmap else "Failed to create corrected preview")
    return pixmap

def test_portrait_images_in_folder(folder_path):
    """Test all images in folder and identify portrait orientation issues"""
    print(f"\n=== TESTING PORTRAIT IMAGES IN: {folder_path} ===")
    
    if not os.path.exists(folder_path):
        print(f"ERROR: Folder not found: {folder_path}")
        return
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp'}
    
    portrait_issues = []
    landscape_issues = []
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            _, ext = os.path.splitext(filename.lower())
            if ext in image_extensions:
                print(f"\n{'='*60}")
                result = analyze_image_orientation(file_path)
                if result and result['needs_correction']:
                    original_w, original_h = result['original_size']
                    corrected_w, corrected_h = result['corrected_size']
                    
                    if original_h > original_w:  # Original appears portrait
                        portrait_issues.append({
                            'file': filename,
                            'orientation': result['orientation'],
                            'desc': result['orientation_desc'],
                            'original_size': result['original_size'],
                            'corrected_size': result['corrected_size']
                        })
                        print(f"🔴 PORTRAIT ISSUE DETECTED: {filename}")
                    else:
                        landscape_issues.append({
                            'file': filename,
                            'orientation': result['orientation'],
                            'desc': result['orientation_desc'], 
                            'original_size': result['original_size'],
                            'corrected_size': result['corrected_size']
                        })
                        print(f"🟡 LANDSCAPE ISSUE DETECTED: {filename}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"Portrait images with orientation issues: {len(portrait_issues)}")
    print(f"Landscape images with orientation issues: {len(landscape_issues)}")
    
    if portrait_issues:
        print(f"\n🔴 PORTRAIT ISSUES:")
        for issue in portrait_issues:
            print(f"  {issue['file']}: {issue['desc']} ({issue['original_size']} -> {issue['corrected_size']})")
    
    if landscape_issues:
        print(f"\n🟡 LANDSCAPE ISSUES:")
        for issue in landscape_issues:
            print(f"  {issue['file']}: {issue['desc']} ({issue['original_size']} -> {issue['corrected_size']})")
    
    return portrait_issues, landscape_issues

if __name__ == "__main__":
    print("🔍 Portrait Orientation Debug Tool")
    print("This tool identifies EXIF orientation issues causing corrupted previews")
    
    # Test with the current image folder (update path as needed)
    test_folder = input("Enter folder path to test (or press Enter for test_images): ").strip()
    if not test_folder:
        # Default to test_images folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        test_folder = os.path.join(parent_dir, "test_images")
    
    if os.path.exists(test_folder):
        portrait_issues, landscape_issues = test_portrait_images_in_folder(test_folder)
        
        if portrait_issues or landscape_issues:
            print(f"\n🔧 DIAGNOSIS:")
            print(f"The corrupted portrait images are likely caused by EXIF orientation data.")
            print(f"The current create_preview() method doesn't apply EXIF orientation correction.")
            print(f"Portrait images with rotation data (orientations 6, 8) appear distorted.")
            print(f"\n💡 SOLUTION:")
            print(f"Apply ImageOps.exif_transpose() before resizing in create_preview() method.")
        else:
            print(f"\n✅ No orientation issues detected in test folder.")
    else:
        print(f"❌ Test folder not found: {test_folder}")
        print(f"Please provide a valid folder path containing test images.")