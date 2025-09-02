#!/usr/bin/env python3
"""
Create a test image and examine metadata compatibility across platforms
"""

from PIL import Image
import os

def create_test_image():
    """Create a simple test JPEG image"""
    # Create a simple 100x100 red image
    img = Image.new('RGB', (100, 100), color='red')
    
    # Save as JPEG
    test_path = "/Volumes/Marketing/Simone Morciano/python working folder/happyTag/happyTag/metadata_test.jpg"
    img.save(test_path, "JPEG")
    print(f"Created test image: {test_path}")
    return test_path

def test_current_metadata_writing():
    """Test what metadata is currently being written"""
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Import the main application to use its metadata writing
    from main import MainWindow
    from PyQt5.QtWidgets import QApplication
    
    # Create minimal Qt app
    app = QApplication([])
    
    # Create the main window to get access to metadata methods
    main_window = MainWindow()
    
    # Create test image
    test_path = create_test_image()
    
    # Test writing metadata using current implementation
    test_keywords = "2023, Cafes & Restaurants, The Oxford Market"
    print(f"\nTesting current metadata writing with keywords: {test_keywords}")
    
    success, error = main_window.save_keywords_to_image(test_path, test_keywords)
    print(f"Save result: success={success}, error='{error}'")
    
    return test_path

def analyze_metadata(image_path):
    """Analyze what metadata fields are present in the image"""
    import subprocess
    
    exiftool_path = "/Volumes/Marketing/Simone Morciano/python working folder/happyTag/happyTag/packages/Image-ExifTool-13.34/exiftool"
    
    print(f"\nAnalyzing metadata in: {os.path.basename(image_path)}")
    print("=" * 60)
    
    # Check various keyword/tag fields
    fields_to_check = [
        "IPTC:Keywords",
        "XMP:Keywords", 
        "XMP:Subject",
        "XMP-dc:Subject",
        "Exif:ImageDescription",
        "File:Comment"
    ]
    
    for field in fields_to_check:
        try:
            result = subprocess.run(
                [exiftool_path, f"-{field}", image_path],
                capture_output=True, text=True, check=True
            )
            output = result.stdout.strip()
            if output and not output.startswith("Warning"):
                print(f"✅ {field:20} = {output}")
            else:
                print(f"❌ {field:20} = (empty)")
        except subprocess.CalledProcessError:
            print(f"❌ {field:20} = (error reading)")
    
    print("\nFull metadata dump:")
    print("-" * 30)
    try:
        result = subprocess.run(
            [exiftool_path, "-All", image_path],
            capture_output=True, text=True, check=True
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error reading metadata: {e}")

if __name__ == "__main__":
    # Test current implementation
    test_path = test_current_metadata_writing()
    
    # Analyze what was written
    analyze_metadata(test_path)
