#!/usr/bin/env python3
"""
Test script to verify the complete fallback chain works when ExifTool fails or returns no data
"""

import os
import sys
import shutil
from datetime import datetime
from PIL import Image

def test_fallback_chain():
    """Test the complete fallback chain: ExifTool -> PIL -> File creation time"""
    
    # Create a test image without metadata
    test_file = "test_no_metadata.jpg"
    test_path = os.path.join("test images", test_file)
    
    print("🧪 Testing Complete Fallback Chain")
    print("=" * 60)
    
    # Create a simple test image without any EXIF metadata
    try:
        img = Image.new('RGB', (100, 100), color='red')
        img.save(test_path, 'JPEG')
        print(f"✅ Created test image: {test_file}")
    except Exception as e:
        print(f"❌ Failed to create test image: {e}")
        return
    
    # Now test the application's metadata extraction
    try:
        # Import the main application
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from main import MainWindow
        from PyQt5.QtWidgets import QApplication
        
        # Create minimal QApplication for testing
        app = QApplication([])
        
        # Create main window instance
        main_window = MainWindow()
        
        # Test metadata extraction
        print(f"\n🔍 Testing metadata extraction for: {test_file}")
        
        year, keywords = main_window.get_image_metadata(test_path)
        
        print(f"📅 Extracted year: {year}")
        print(f"🏷️  Extracted keywords: {keywords}")
        
        # Verify we got a year (should come from file creation time)
        if year:
            current_year = datetime.now().year
            if year == current_year:
                print(f"✅ SUCCESS: Fallback to file creation time worked! Year: {year}")
            else:
                print(f"⚠️  Got year {year}, expected {current_year} (current year)")
        else:
            print("❌ FAILED: No year extracted from any source")
        
        # Test the specific fallback method
        print(f"\n🔄 Testing direct fallback method...")
        fallback_year, fallback_keywords = main_window._get_metadata_fallback(test_path)
        print(f"📅 Fallback year: {fallback_year}")
        print(f"🏷️  Fallback keywords: {fallback_keywords}")
        
        if fallback_year:
            print(f"✅ SUCCESS: Direct fallback method worked! Year: {fallback_year}")
        else:
            print("❌ FAILED: Direct fallback method returned no year")
        
        app.quit()
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test file
        try:
            if os.path.exists(test_path):
                os.remove(test_path)
                print(f"\n🧹 Cleaned up test file: {test_file}")
        except Exception as e:
            print(f"⚠️  Failed to clean up test file: {e}")

def test_tiff_xmp_fallback():
    """Test TIFF XMP metadata fallback specifically"""
    
    print("\n🔍 Testing TIFF XMP Fallback")
    print("-" * 40)
    
    # Look for existing TIFF files to test
    test_dir = "test images"
    tiff_files = [f for f in os.listdir(test_dir) if f.lower().endswith(('.tif', '.tiff'))]
    
    if not tiff_files:
        print("ℹ️  No TIFF files found to test XMP fallback")
        return
    
    for tiff_file in tiff_files:
        tiff_path = os.path.join(test_dir, tiff_file)
        print(f"\n📁 Testing TIFF file: {tiff_file}")
        
        # Check if it has XMP metadata manually
        try:
            with open(tiff_path, 'rb') as f:
                content = f.read()
                content_str = content.decode('utf-8', errors='ignore')
                
                if '<xmp:CreateDate>' in content_str:
                    print("✅ File contains XMP CreateDate metadata")
                    
                    import re
                    create_date_match = re.search(r'<xmp:CreateDate>([^<]+)</xmp:CreateDate>', content_str)
                    if create_date_match:
                        date_str = create_date_match.group(1)
                        print(f"📅 Found XMP date: {date_str}")
                        
                        if 'T' in date_str:
                            date_part = date_str.split('T')[0]
                            try:
                                year = datetime.strptime(date_part, '%Y-%m-%d').year
                                print(f"🎯 Extracted year: {year}")
                            except ValueError as e:
                                print(f"❌ Failed to parse date: {e}")
                else:
                    print("ℹ️  No XMP CreateDate found in file")
                    
        except Exception as e:
            print(f"❌ Error reading TIFF file: {e}")

if __name__ == "__main__":
    test_fallback_chain()
    test_tiff_xmp_fallback()