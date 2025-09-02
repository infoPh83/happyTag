#!/usr/bin/env python3
"""
Final verification script for macOS Finder tags
"""

import subprocess
import os

def main():
    test_image = "test images/1.jpg"
    
    print("🎯 macOS Finder Tags - Final Status Check")
    print("=" * 50)
    
    if not os.path.exists(test_image):
        print(f"❌ Test image not found: {test_image}")
        return
    
    print(f"📁 Checking: {test_image}")
    print()
    
    # Check if extended attributes are present
    try:
        result = subprocess.run(['xattr', '-l', test_image], 
                              capture_output=True, text=True, errors='ignore')
        
        has_finder_tags = False
        has_spotlight_meta = False
        
        for line in result.stdout.split('\n'):
            if '_kMDItemUserTags' in line:
                has_finder_tags = True
            if 'kMDItemKeywords' in line or 'kMDItemSubject' in line:
                has_spotlight_meta = True
        
        print("✅ Technical Status:")
        print(f"   Finder Tags: {'✅ Present' if has_finder_tags else '❌ Missing'}")
        print(f"   Spotlight Metadata: {'✅ Present' if has_spotlight_meta else '❌ Missing'}")
        
    except Exception as e:
        print(f"❌ Error checking attributes: {e}")
        return
    
    # Check Spotlight indexing status
    try:
        result = subprocess.run(['mdutil', '-s', '/Volumes/Marketing'], 
                              capture_output=True, text=True)
        
        is_indexing_enabled = 'Indexing enabled' in result.stdout
        is_server_search = 'Server search enabled' in result.stdout
        
        print()
        print("🔍 Spotlight Status:")
        if is_indexing_enabled:
            print("   ✅ Full Spotlight indexing enabled")
            print("   → Tags should be visible in Finder!")
        elif is_server_search:
            print("   ⚠️  Only server search enabled")
            print("   → This is why tags aren't visible!")
        else:
            print("   ❌ Spotlight disabled")
            
    except Exception as e:
        print(f"❌ Error checking Spotlight: {e}")
    
    print()
    print("🧪 MANUAL TEST:")
    print("1. Right-click 'test images/1.jpg' in Finder")
    print("2. Select 'Get Info' (⌘+I)")
    print("3. Look for 'Tags' section")
    print()
    
    if not is_indexing_enabled:
        print("🔧 TO FIX:")
        print("1. Open System Preferences → Spotlight")
        print("2. Click 'Privacy' tab")
        print("3. Add Marketing drive, then immediately remove it")
        print("4. Wait 10-30 minutes for re-indexing")
        print("5. Then check again!")
    else:
        print("🎉 Everything looks good technically!")
        print("   If tags still don't show, try restarting Finder:")
        print("   Hold ⌥ key → Right-click Finder in Dock → Relaunch")

if __name__ == "__main__":
    main()
