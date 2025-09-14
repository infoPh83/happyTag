#!/usr/bin/env python3
"""
Test ImageAssessment Integration
Tests the new process_single_image_with_cloudinary_logic method
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from utilities.image_assessment import ImageAssessment
from utilities.settings_dialog import SettingsDialog

def test_image_assessment_integration():
    """Test the new single image processing method"""
    
    # Find a test image
    test_images_dir = Path("test_images")
    if not test_images_dir.exists():
        test_images_dir = Path("test images")
    
    if not test_images_dir.exists():
        print("[ERROR] No test images directory found")
        return False
    
    # Find first image file
    image_files = []
    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
        image_files.extend(test_images_dir.glob(f"*{ext}"))
        image_files.extend(test_images_dir.glob(f"*{ext.upper()}"))
    
    if not image_files:
        print("[ERROR] No test images found")
        return False
    
    test_image = str(image_files[0])
    print(f"[INFO] Testing with image: {test_image}")
    
    try:
        # Initialize ImageAssessment with explicit max file size for testing
        test_max_size = 3.2 * 1024 * 1024  # 3.2MB for testing
        assessment = ImageAssessment(max_file_size=test_max_size)
        
        # Create a mock settings dialog (None should work for basic testing)
        settings_dialog = None
        
        # Test the new method
        print("[INFO] Testing process_single_image_with_cloudinary_logic...")
        success, result_data, optimized_file = assessment.process_single_image_with_cloudinary_logic(
            test_image, settings_dialog
        )
        
        print(f"[RESULT] Success: {success}")
        print(f"[RESULT] Result data: {result_data}")
        print(f"[RESULT] Optimized file: {optimized_file}")
        
        if success:
            print("✅ Integration test PASSED")
            return True
        else:
            print("❌ Integration test FAILED")
            return False
            
    except Exception as e:
        print(f"[ERROR] Integration test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Testing ImageAssessment Integration")
    print("=" * 50)
    
    success = test_image_assessment_integration()
    
    print("=" * 50)
    if success:
        print("🎉 All tests PASSED!")
    else:
        print("💥 Tests FAILED!")
    print("=" * 50)