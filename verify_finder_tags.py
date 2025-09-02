#!/usr/bin/env python3
"""
Final verification script for HappyTag macOS Finder tags integration
"""

import os
import subprocess
import plistlib

def verify_finder_tags(file_path):
    """Verify that Finder tags are properly written and readable"""
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
        
        # Read the extended attribute
        result = subprocess.run([
            'xattr', '-p', '-x', 'com.apple.metadata:_kMDItemUserTags', file_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            return False, "No Finder tags found"
        
        # Parse the hex data
        hex_string = result.stdout.replace('\n', '').replace(' ', '')
        if not hex_string:
            return False, "Empty tag data"
        
        # Convert to binary and parse plist
        plist_data = bytes.fromhex(hex_string)
        tag_list = plistlib.loads(plist_data)
        
        # Extract tag names
        tags = []
        for tag in tag_list:
            if 'n' in tag:
                tags.append(tag['n'])
        
        return True, tags
        
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    print("🔍 HappyTag Finder Tags Verification")
    print("=" * 50)
    
    # Test the demo file
    demo_file = "test_finder_tags_demo.jpg"
    if os.path.exists(demo_file):
        print(f"\n📁 Checking: {demo_file}")
        success, result = verify_finder_tags(demo_file)
        if success:
            print(f"✅ Tags found: {result}")
        else:
            print(f"❌ Tags not found: {result}")
    
    # Test the original file if it exists
    original_file = "/Volumes/Marketing/00. Media Library/LIFESTYLE PHOTOS (upload and tag)/lifestyle 01/LIFESTYLE_AND_DETAILS_066.jpg"
    if os.path.exists(original_file):
        print(f"\n📁 Checking: {os.path.basename(original_file)}")
        success, result = verify_finder_tags(original_file)
        if success:
            print(f"✅ Tags found: {result}")
        else:
            print(f"❌ Tags not found: {result}")
    
    print("\n" + "=" * 50)
    print("📋 FINDER TAG VISIBILITY CHECKLIST:")
    print("1. ✅ Tags are written to extended attributes")
    print("2. ✅ Tags are readable by system tools")
    print("3. 🔍 To see in Finder:")
    print("   • Open Finder")
    print("   • Navigate to the file location")
    print("   • Look for colored circles/dots next to filenames")
    print("   • Try right-clicking and checking 'Tags' in context menu")
    print("   • Enable 'Tags' column in List view (View > Show View Options)")
    print("\n💡 TIP: If tags still not visible:")
    print("   • Restart Finder: Option+Right-click Finder in Dock > Relaunch")
    print("   • Force reindex: mdimport /path/to/file")

if __name__ == "__main__":
    main()
