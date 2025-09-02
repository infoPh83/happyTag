#!/usr/bin/env python3
"""
Test script to apply macOS Finder tags to the test image and verify they work
"""

import sys
import os
import subprocess
import plistlib
from pathlib import Path

def main():
    # Path to test image
    test_image = "test images/1.jpg"
    
    if not os.path.exists(test_image):
        print(f"❌ Test image not found: {test_image}")
        return
    
    print(f"🔍 Testing macOS Finder tag integration on: {test_image}")
    print("=" * 60)
    
    # Check current extended attributes
    print("\n1. Current extended attributes:")
    try:
        result = subprocess.run(['xattr', '-l', test_image], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            print(result.stdout)
        else:
            print("   No extended attributes found")
    except Exception as e:
        print(f"   Error checking attributes: {e}")
    
    # Check current Spotlight metadata
    print("\n2. Current Spotlight metadata:")
    try:
        result = subprocess.run(['mdls', test_image], 
                              capture_output=True, text=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['tag', 'keyword', 'subject']):
                print(f"   {line.strip()}")
    except Exception as e:
        print(f"   Error checking Spotlight metadata: {e}")
    
    # Apply macOS Finder tags using our method
    print("\n3. Applying macOS Finder tags...")
    tags = ["2024", "Christmas", "Compatibility Test", "HappyTag"]
    
    try:
        # Create the plist data for Finder tags
        tag_data = []
        colors = ["None", "Gray", "Green", "Purple", "Blue", "Yellow", "Red", "Orange"]
        
        for i, tag in enumerate(tags):
            color_idx = (i % (len(colors) - 1)) + 1  # Skip "None" for visibility
            tag_data.append(f"{tag}\n{colors[color_idx]}")
        
        # Create binary plist
        plist_data = plistlib.dumps(tag_data)
        
        # Write to extended attributes
        result = subprocess.run([
            'xattr', '-w', 'com.apple.metadata:_kMDItemUserTags',
            plist_data.hex(), test_image
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Extended attributes written successfully")
        else:
            print(f"   ❌ Error writing extended attributes: {result.stderr}")
            
        # Also write Spotlight metadata
        for tag in tags:
            subprocess.run([
                'xattr', '-w', f'com.apple.metadata:kMDItemUserTags_{tag}', 
                tag, test_image
            ], capture_output=True)
            
        print("   ✅ Spotlight metadata written")
        
    except Exception as e:
        print(f"   ❌ Error applying tags: {e}")
    
    # Verify the changes
    print("\n4. Verifying changes:")
    try:
        result = subprocess.run(['xattr', '-l', test_image], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            print("   Extended attributes after change:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"     {line}")
        
        # Check if mdls shows the tags
        result = subprocess.run(['mdls', '-name', 'kMDItemUserTags', test_image], 
                              capture_output=True, text=True)
        print(f"\n   Spotlight kMDItemUserTags: {result.stdout.strip()}")
        
    except Exception as e:
        print(f"   ❌ Error verifying changes: {e}")
    
    # Check Spotlight indexing status
    print("\n5. Spotlight indexing status:")
    try:
        # Check if Marketing drive is being indexed
        result = subprocess.run(['mdutil', '-s', '/Volumes/Marketing'], 
                              capture_output=True, text=True)
        print(f"   Marketing drive status: {result.stdout.strip()}")
        
        # Check if there are active mdworker processes
        result = subprocess.run(['pgrep', '-l', 'mdworker'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            worker_count = len(result.stdout.strip().split('\n'))
            print(f"   Active mdworker processes: {worker_count}")
        else:
            print("   No active mdworker processes found")
            
    except Exception as e:
        print(f"   Error checking Spotlight status: {e}")
    
    print("\n" + "=" * 60)
    print("🔧 Next steps:")
    print("1. Right-click the image in Finder and select 'Get Info'")
    print("2. Look for 'Tags' section in the info panel")
    print("3. If tags don't appear, check System Preferences → Spotlight → Privacy")
    print("4. Make sure Marketing drive is NOT in the exclusion list")
    print("5. If it is excluded, remove it and wait for re-indexing")

if __name__ == "__main__":
    main()
