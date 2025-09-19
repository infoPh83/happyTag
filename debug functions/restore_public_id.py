#!/usr/bin/env python3
"""
Manual Cloudinary Public ID Restoration Tool
This script helps restore lost Cloudinary public_ids to image metadata
"""

import os
import sys
import subprocess

def restore_public_id_to_image(image_path, public_id):
    """
    Manually restore a Cloudinary public_id to an image's UserComment field
    """
    # Use the correct ExifTool path for macOS
    exiftool_path = '/opt/homebrew/bin/exiftool'
    
    print(f"🔧 Restoring public_id to {os.path.basename(image_path)}")
    print(f"   Public ID: {public_id}")
    
    try:
        # Write the public_id to UserComment field
        result = subprocess.run([
            exiftool_path,
            '-overwrite_original',
            f'-UserComment=cloudinary_public_id:{public_id}',
            image_path
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ Successfully restored public_id to {os.path.basename(image_path)}")
            
            # Verify the write
            verify_result = subprocess.run([
                exiftool_path,
                '-UserComment',
                '-s3',
                image_path
            ], capture_output=True, text=True, timeout=10)
            
            if verify_result.returncode == 0 and verify_result.stdout.strip():
                print(f"📋 Verification: UserComment = \"{verify_result.stdout.strip()}\"")
                if verify_result.stdout.strip().startswith(f'cloudinary_public_id:{public_id}'):
                    print("✅ Public ID correctly written and verified!")
                    return True
                else:
                    print("❌ Public ID not written correctly")
                    return False
            else:
                print("❌ Could not verify the write")
                return False
        else:
            print(f"❌ ExifTool error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("=== CLOUDINARY PUBLIC ID RESTORATION TOOL ===")
    print()
    
    # Configuration
    test_image = "/Volumes/Marketing/Simone Morciano/python working folder/happyTag/happyTag/test images/1.jpg"
    
    # YOU NEED TO PROVIDE THE ACTUAL PUBLIC_ID FROM YOUR CLOUDINARY DASHBOARD
    # Replace this with the actual public_id of the image from Cloudinary
    cloudinary_public_id = "YOUR_ACTUAL_PUBLIC_ID_HERE"  # ← CHANGE THIS!
    
    if cloudinary_public_id == "YOUR_ACTUAL_PUBLIC_ID_HERE":
        print("❌ Please edit this script and provide the actual Cloudinary public_id")
        print("   1. Go to your Cloudinary dashboard")
        print("   2. Find the image '1.jpg' (or similar)")
        print("   3. Copy its public_id")
        print("   4. Replace 'YOUR_ACTUAL_PUBLIC_ID_HERE' in this script")
        print("   5. Run the script again")
        sys.exit(1)
    
    print(f"Image: {os.path.basename(test_image)}")
    print(f"Public ID to restore: {cloudinary_public_id}")
    print()
    
    if not os.path.exists(test_image):
        print(f"❌ Image not found: {test_image}")
        sys.exit(1)
    
    # Show current UserComment content
    exiftool_path = '/opt/homebrew/bin/exiftool'
    try:
        current_result = subprocess.run([
            exiftool_path,
            '-UserComment',
            '-s3',
            test_image
        ], capture_output=True, text=True, timeout=10)
        
        if current_result.returncode == 0 and current_result.stdout.strip():
            print(f"📋 Current UserComment: \"{current_result.stdout.strip()}\"")
        else:
            print("📋 Current UserComment: (empty)")
    except:
        print("📋 Could not read current UserComment")
    
    print()
    
    # Perform the restoration
    success = restore_public_id_to_image(test_image, cloudinary_public_id)
    
    if success:
        print()
        print("🎉 SUCCESS! The public_id has been restored.")
        print("   Now try loading this image in HappyTag - it should be recognized as being on Cloudinary!")
    else:
        print()
        print("❌ FAILED to restore the public_id.")
        print("   Please check the error messages above.")
