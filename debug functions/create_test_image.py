#!/usr/bin/env python3
"""Create a test image with metadata for testing ExifTool functionality"""

import os
from PIL import Image, ImageDraw
from PIL.ExifTags import TAGS
import subprocess

def create_test_image():
    """Create a simple test image"""
    # Create a simple test image
    img = Image.new('RGB', (800, 600), color='lightblue')
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "Test Image for ExifTool", fill='black')
    draw.text((50, 100), "Should have keywords: business, test, sample", fill='black')
    
    # Save the basic image
    test_path = os.path.join(os.path.dirname(__file__), 'test_image.jpg')
    img.save(test_path, 'JPEG', quality=95)
    return test_path

def add_metadata_with_exiftool(image_path):
    """Add metadata using ExifTool if available"""
    
    exiftool_path = os.path.join(os.path.dirname(__file__), 'packages', 
                                'exiftool_win64', 'exiftool-13.34_64', 'exiftool(-k).exe')
    
    if os.path.exists(exiftool_path):
        try:
            # Add keywords using ExifTool
            cmd = [
                exiftool_path,
                '-keywords=business',
                '-keywords+=test', 
                '-keywords+=sample',
                '-description=Test image for ExifTool functionality',
                '-overwrite_original',
                image_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Successfully added metadata to {image_path}")
                print("Keywords added: business, test, sample")
                return True
            else:
                print(f"ExifTool error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error running ExifTool: {e}")
            return False
    else:
        print(f"ExifTool not found at: {exiftool_path}")
        return False

if __name__ == "__main__":
    print("Creating test image...")
    image_path = create_test_image()
    print(f"Created basic image: {image_path}")
    
    print("\nAdding metadata with ExifTool...")
    if add_metadata_with_exiftool(image_path):
        print("\nTest image created successfully!")
        print(f"You can now test the app with: {image_path}")
    else:
        print("\nFailed to add metadata, but basic image created.")
