#!/usr/bin/env python3
"""
Test the Portrait Orientation Fix
Quick test to verify that the EXIF orientation fix is working
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the main app to test the create_preview method
import main

class TestPortraitFix:
    def __init__(self):
        # Initialize minimal required attributes for testing
        self.image_previews = {}
        self.unsupported_files = []
        self.MAX_PREVIEW_SIZE = 800
    
    def test_orientation_fix(self):
        """Test the create_preview method with orientation test images"""
        print("🧪 Testing Portrait Orientation Fix")
        print("=" * 50)
        
        # Test images we created
        test_images = [
            "debug functions/test_orientation_1.jpg",  # Normal
            "debug functions/test_orientation_6.jpg",  # Rotated 90° (portrait from landscape)
            "debug functions/test_orientation_8.jpg",  # Rotated 270° (portrait from landscape)
        ]
        
        for img_path in test_images:
            if os.path.exists(img_path):
                print(f"\n📸 Testing: {os.path.basename(img_path)}")
                
                # Test our fixed create_preview method
                try:
                    # Create a minimal instance with required attributes
                    app_instance = type('MockApp', (), {
                        'image_previews': {},
                        'unsupported_files': [],
                        'MAX_PREVIEW_SIZE': 800,
                        'image_metadata': {},
                        'get_image_metadata': lambda self, path: ("2025", [])
                    })()
                    
                    # Add the create_preview method from main
                    app_instance.create_preview = main.HappyTagApp.create_preview.__get__(app_instance)
                    
                    # Test the fixed method
                    result = app_instance.create_preview(img_path)
                    
                    if result:
                        print(f"  ✅ Successfully created preview")
                        if img_path in app_instance.image_previews:
                            pixmap = app_instance.image_previews[img_path]
                            print(f"  📏 Preview size: {pixmap.width()}x{pixmap.height()}")
                            
                            # Check if this is a portrait orientation that should be corrected
                            if "orientation_6" in img_path or "orientation_8" in img_path:
                                if pixmap.height() > pixmap.width():
                                    print(f"  🎯 PORTRAIT FIX WORKING: Height ({pixmap.height()}) > Width ({pixmap.width()})")
                                else:
                                    print(f"  ⚠️  Still appears landscape: Width ({pixmap.width()}) >= Height ({pixmap.height()})")
                        else:
                            print(f"  ❌ Preview not found in cache")
                    else:
                        print(f"  ❌ Failed to create preview")
                        
                except Exception as e:
                    print(f"  💥 Error testing {img_path}: {e}")
            else:
                print(f"\n❌ Test image not found: {img_path}")
        
        print(f"\n✅ Test complete!")

if __name__ == "__main__":
    tester = TestPortraitFix()
    tester.test_orientation_fix()