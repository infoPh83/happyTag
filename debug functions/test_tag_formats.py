#!/usr/bin/env python3
"""
Test different approaches to writing macOS Finder tags
"""

import subprocess
import plistlib
import os

def test_tag_formats(image_path):
    print(f"🧪 Testing different tag formats on: {image_path}")
    print("=" * 60)
    
    # Test 1: Simple string tags (what Finder might expect)
    print("\n1. Testing simple string format...")
    try:
        tags = ["Red\nRed", "Blue\nBlue", "Green\nGreen"]
        plist_data = plistlib.dumps(tags)
        
        result = subprocess.run([
            'xattr', '-w', 'com.apple.metadata:_kMDItemUserTags',
            plist_data.hex(), image_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Simple format written")
        else:
            print(f"   ❌ Error: {result.stderr}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 2: Check what Finder can actually read
    print("\n2. Testing Finder readability...")
    try:
        # Try to read with plutil (what Finder uses internally)
        result = subprocess.run([
            'plutil', '-convert', 'xml1', '-o', '-', 
            '/dev/stdin'
        ], input=plist_data, capture_output=True)
        
        if result.returncode == 0:
            print("   ✅ Plist is readable by system tools")
            print("   Raw data preview:")
            print(result.stdout.decode()[:200] + "...")
        else:
            print(f"   ❌ Plist not readable: {result.stderr}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 3: Try the exact format that Finder creates
    print("\n3. Testing Finder-native format...")
    try:
        # This is the exact format Finder uses when you manually add tags
        native_tags = [
            "TestTag1\n6",  # 6 = Orange
            "TestTag2\n2",  # 2 = Red  
            "TestTag3\n4"   # 4 = Blue
        ]
        
        native_plist = plistlib.dumps(native_tags)
        
        result = subprocess.run([
            'xattr', '-w', 'com.apple.metadata:_kMDItemUserTags',
            native_plist.hex(), image_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Finder-native format written")
        else:
            print(f"   ❌ Error: {result.stderr}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 4: Verify current state
    print("\n4. Current extended attributes:")
    try:
        result = subprocess.run(['xattr', '-l', image_path], 
                              capture_output=True, text=True, errors='ignore')
        
        lines = result.stdout.split('\n')
        for line in lines:
            if '_kMDItemUserTags' in line:
                print(f"   Found: {line[:80]}...")
                break
        else:
            print("   ❌ No _kMDItemUserTags found")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 Manual Test:")
    print("1. Open Finder")
    print("2. Navigate to the test image")
    print("3. Right-click → Get Info (⌘+I)")
    print("4. Look for 'Tags' section near the top")
    print("\nIf tags still don't appear, the issue is likely:")
    print("- Spotlight indexing (most common)")
    print("- Finder cache (try restarting Finder)")
    print("- macOS version compatibility")

if __name__ == "__main__":
    image_path = "test images/1.jpg"
    if os.path.exists(image_path):
        test_tag_formats(image_path)
    else:
        print(f"❌ Image not found: {image_path}")
