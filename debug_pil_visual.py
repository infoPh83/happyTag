#!/usr/bin/env python3
"""
Advanced debug script to investigate PIL to QImage conversion visual corruption.
This will save converted images to see the actual visual differences.
"""

import os
import sys
from PIL import Image

def debug_pil_conversions(image_path):
    """Test different PIL conversion methods and save results."""
    print(f"\n=== TESTING PIL CONVERSIONS: {os.path.basename(image_path)} ===")
    
    try:
        with Image.open(image_path) as pil_img:
            print(f"Original: {pil_img.mode}, {pil_img.size}, ICC: {'icc_profile' in pil_img.info}")
            
            # Method 1: Standard RGB conversion (what we're currently using)
            try:
                if pil_img.mode != 'RGB':
                    rgb_img = pil_img.convert('RGB')
                else:
                    rgb_img = pil_img.copy()
                
                # Resize to preview size to match app behavior
                rgb_img.thumbnail((800, 800), Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.Resampling.LANCZOS)
                
                # Save to see visual result
                output_path = "debug_method1_rgb.jpg"
                rgb_img.save(output_path, "JPEG", quality=95)
                print(f"  Method 1 (RGB): Saved as {output_path} - {rgb_img.size}")
                
            except Exception as e:
                print(f"  Method 1 (RGB): Failed - {str(e)}")
            
            # Method 2: Remove ICC profile first, then convert
            try:
                clean_img = pil_img.copy()
                # Remove all color management info
                if 'icc_profile' in clean_img.info:
                    del clean_img.info['icc_profile']
                
                if clean_img.mode != 'RGB':
                    clean_img = clean_img.convert('RGB')
                
                # Resize to preview size
                clean_img.thumbnail((800, 800), Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.Resampling.LANCZOS)
                
                # Save to see visual result
                output_path = "debug_method2_no_icc.jpg"
                clean_img.save(output_path, "JPEG", quality=95)
                print(f"  Method 2 (No ICC): Saved as {output_path} - {clean_img.size}")
                
            except Exception as e:
                print(f"  Method 2 (No ICC): Failed - {str(e)}")
            
            # Method 3: Convert via sRGB color space
            try:
                # Force conversion to sRGB if image has color profile
                if 'icc_profile' in pil_img.info:
                    # Convert using PIL's color management
                    from PIL import ImageCms
                    try:
                        # Get the current profile
                        input_profile = ImageCms.ImageCmsProfile(pil_img.info['icc_profile'])
                        # Create sRGB profile
                        srgb_profile = ImageCms.createProfile('sRGB')
                        # Transform to sRGB
                        srgb_img = ImageCms.profileToProfile(pil_img, input_profile, srgb_profile, renderingIntent=0, outputMode='RGB')
                    except:
                        # Fallback to simple conversion
                        srgb_img = pil_img.convert('RGB')
                else:
                    srgb_img = pil_img.convert('RGB')
                
                # Resize to preview size
                srgb_img.thumbnail((800, 800), Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.Resampling.LANCZOS)
                
                # Save to see visual result
                output_path = "debug_method3_srgb.jpg"
                srgb_img.save(output_path, "JPEG", quality=95)
                print(f"  Method 3 (sRGB): Saved as {output_path} - {srgb_img.size}")
                
            except Exception as e:
                print(f"  Method 3 (sRGB): Failed - {str(e)}")
            
            # Method 4: Simple resize without color space conversion
            try:
                simple_img = pil_img.copy()
                simple_img.thumbnail((800, 800), Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.Resampling.LANCZOS)
                
                # Save without changing color profile
                output_path = "debug_method4_simple.jpg"
                simple_img.save(output_path, "JPEG", quality=95)
                print(f"  Method 4 (Simple): Saved as {output_path} - {simple_img.size}")
                
            except Exception as e:
                print(f"  Method 4 (Simple): Failed - {str(e)}")
                
            print("\nTest images saved. Compare them visually to see which method preserves colors correctly.")
            print("If any look grayscale/distorted, that method has the issue.")
            
    except Exception as e:
        print(f"Error opening image: {str(e)}")

def main():
    """Main debug function."""
    test_image = r"D:\Python playfolder\happyTag\test images\test_finder_tags_demo.jpg"
    
    if not os.path.exists(test_image):
        print(f"Error: Test image not found at {test_image}")
        return
    
    debug_pil_conversions(test_image)

if __name__ == "__main__":
    main()