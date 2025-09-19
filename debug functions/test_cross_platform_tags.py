#!/usr/bin/env python3
"""
Test script to verify cross-platform metadata tag writing.
This script tests the new unified metadata approach.
"""

import os
import sys
import shutil
from PIL import Image

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_image(path):
    """Create a simple test image"""
    img = Image.new('RGB', (100, 100), color='red')
    img.save(path, 'JPEG', quality=95)
    print(f"Created test image: {path}")

def test_cross_platform_metadata():
    """Test the cross-platform metadata writing"""
    print("=== Cross-Platform Metadata Tag Test ===\n")
    
    # Import the main module
    import main
    
    # Create a temporary test image
    test_image = "test_cross_platform.jpg"
    if os.path.exists(test_image):
        os.remove(test_image)
    
    create_test_image(test_image)
    
    # Create a mock main window instance (minimal setup)
    class MockMainWindow:
        def __init__(self):
            self.exiftool_available = main.EXIFTOOL_AVAILABLE
            self.persistent_exiftool = None
            self.original_keywords = {}
            
            if self.exiftool_available:
                try:
                    if main.EXIFTOOL_PATH:
                        self.persistent_exiftool = main.et_module.ExifTool(executable=main.EXIFTOOL_PATH)
                    else:
                        self.persistent_exiftool = main.et_module.ExifTool()
                    self.persistent_exiftool.__enter__()
                    print("✅ ExifTool initialized for testing")
                except Exception as e:
                    print(f"❌ Failed to initialize ExifTool: {e}")
                    return False
        
        def cleanup(self):
            if self.persistent_exiftool:
                try:
                    self.persistent_exiftool.__exit__(None, None, None)
                except:
                    pass
    
    # Test the metadata writing
    mock_window = MockMainWindow()
    
    if not mock_window.exiftool_available:
        print("❌ ExifTool not available, cannot test metadata writing")
        return False
    
    try:
        # Test keywords
        test_keywords = ["cross-platform", "test", "metadata", "2024"]
        keywords_text = ", ".join(test_keywords)
        
        print(f"Testing with keywords: {test_keywords}")
        
        # Test the save_keywords_to_image method
        success, error_msg = main.MainWindow.save_keywords_to_image(mock_window, test_image, keywords_text)
        
        if success:
            print("✅ Keywords saved successfully")
            
            # Verify the metadata was written correctly
            print("\n=== Verifying Written Metadata ===")
            
            et = mock_window.persistent_exiftool
            
            # Check all the fields we should have written
            fields_to_check = [
                'IPTC:Keywords',
                'XMP:Keywords', 
                'XMP-dc:Subject',
                'XMP:Subject',
                'EXIF:Keywords',
                'Keywords',
                'Tags',
                'Subject'
            ]
            
            for field in fields_to_check:
                try:
                    result = et.execute(f'-{field}', test_image)
                    if result and not result.startswith('Warning') and result.strip():
                        print(f"✅ {field}: {result.strip()}")
                    else:
                        print(f"❌ {field}: No data found")
                except Exception as e:
                    print(f"❌ {field}: Error reading - {e}")
            
            # Test platform-specific tags
            print(f"\n=== Testing Platform-Specific Tags ===")
            platform_success, platform_msg = main.MainWindow.write_platform_specific_tags(mock_window, test_image, test_keywords)
            
            if platform_success:
                print(f"✅ Platform-specific tags: {platform_msg}")
            else:
                print(f"❌ Platform-specific tags failed: {platform_msg}")
            
        else:
            print(f"❌ Failed to save keywords: {error_msg}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        # Cleanup
        mock_window.cleanup()
        if os.path.exists(test_image):
            os.remove(test_image)
            print(f"\n🧹 Cleaned up test image: {test_image}")
    
    print("\n=== Test Complete ===")
    return True

if __name__ == "__main__":
    success = test_cross_platform_metadata()
    sys.exit(0 if success else 1)
