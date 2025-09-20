#!/usr/bin/env python3
"""
Create Test Images with Different EXIF Orientations
This creates sample images to test orientation handling
"""

import os
from PIL import Image, ImageDraw
from PIL.ExifTags import TAGS
import piexif

def create_test_image_with_orientation(orientation, filename):
    """Create a test image with specific EXIF orientation"""
    
    # Create a distinctive test image that shows orientation clearly
    # Make it landscape originally (400x300)
    width, height = 400, 300
    
    # Create image with distinctive content to show rotation
    img = Image.new('RGB', (width, height), 'lightblue')
    draw = ImageDraw.Draw(img)
    
    # Draw orientation indicators
    # Top banner
    draw.rectangle([0, 0, width, 50], fill='red')
    draw.text((10, 15), "TOP", fill='white')
    
    # Bottom banner  
    draw.rectangle([0, height-50, width, height], fill='green')
    draw.text((10, height-35), "BOTTOM", fill='white')
    
    # Left side
    draw.rectangle([0, 50, 50, height-50], fill='blue')
    draw.text((5, height//2), "LEFT", fill='white')
    
    # Right side
    draw.rectangle([width-50, 50, width, height-50], fill='yellow')
    draw.text((width-45, height//2), "RIGHT", fill='black')
    
    # Center text showing orientation
    draw.text((width//2-50, height//2-10), f"ORIENTATION {orientation}", fill='black')
    
    # Create EXIF data with the specified orientation
    exif_dict = {"0th": {piexif.ImageIFD.Orientation: orientation}}
    exif_bytes = piexif.dump(exif_dict)
    
    # Save with EXIF data
    output_path = os.path.join("debug functions", filename)
    img.save(output_path, exif=exif_bytes)
    print(f"Created {filename} with orientation {orientation}")
    
    return output_path

def create_orientation_test_set():
    """Create a complete set of test images with different orientations"""
    print("Creating test images with different EXIF orientations...")
    
    # Orientation descriptions
    orientations = {
        1: "Normal (0°)",
        2: "Mirrored horizontally", 
        3: "Rotated 180°",
        4: "Mirrored vertically",
        5: "Mirrored horizontally + rotated 270°",
        6: "Rotated 90° clockwise (Portrait from Landscape)",
        7: "Mirrored horizontally + rotated 90°", 
        8: "Rotated 270° clockwise (Portrait from Landscape)"
    }
    
    created_files = []
    for orientation, description in orientations.items():
        filename = f"test_orientation_{orientation}.jpg"
        file_path = create_test_image_with_orientation(orientation, filename)
        created_files.append(file_path)
        print(f"  {filename}: {description}")
    
    print(f"\nCreated {len(created_files)} test images in debug functions folder")
    return created_files

if __name__ == "__main__":
    try:
        import piexif
        print("✅ piexif library available")
    except ImportError:
        print("❌ piexif library not found")
        print("Installing piexif...")
        import subprocess
        subprocess.check_call(["pip", "install", "piexif"])
        import piexif
        print("✅ piexif installed successfully")
    
    # Create test images
    created_files = create_orientation_test_set()
    
    print(f"\n✅ Test complete! Created {len(created_files)} orientation test images.")
    print("You can now run test_portrait_orientation.py with the debug functions folder to see the issues.")