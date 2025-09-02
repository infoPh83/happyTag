#!/usr/bin/env python3
"""
Check Spotlight indexing status and provide solutions
"""

import os
import subprocess
import sys

def check_spotlight_status(path):
    """Check Spotlight indexing status for a given path"""
    try:
        result = subprocess.run(['mdutil', '-s', path], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Error checking status: {e}"

def check_privacy_list():
    """Check Spotlight privacy exclusions"""
    try:
        # Read Spotlight preferences
        result = subprocess.run([
            'defaults', 'read', 'com.apple.Spotlight', 'orderedItems'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Spotlight preferences accessible")
        else:
            print("❌ Cannot read Spotlight preferences")
            
    except Exception as e:
        print(f"Error reading preferences: {e}")

def force_reindex(path):
    """Try to force reindexing (without sudo)"""
    try:
        print(f"Attempting to trigger reindex for {path}...")
        
        # Try to touch some files to trigger indexing
        result = subprocess.run(['find', path, '-name', '*.jpg', '-exec', 'touch', '{}', '+'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Triggered file updates to encourage indexing")
        else:
            print("❌ Could not update files")
            
    except subprocess.TimeoutExpired:
        print("⏱️  Timeout - there are many files to update")
    except Exception as e:
        print(f"Error: {e}")

def main():
    marketing_path = "/Volumes/Marketing/"
    
    print("🔍 SPOTLIGHT INDEXING DIAGNOSTIC")
    print("=" * 50)
    
    # Check if drive exists
    if not os.path.exists(marketing_path):
        print(f"❌ Marketing drive not found at {marketing_path}")
        return
    
    print(f"📁 Drive found: {marketing_path}")
    
    # Check current status
    print(f"\n📊 Current Spotlight Status:")
    status = check_spotlight_status(marketing_path)
    print(f"   {status}")
    
    # Check if indexing is enabled
    if "disabled" in status.lower():
        print("\n❌ PROBLEM: Indexing is disabled")
        print("🔧 SOLUTION: Enable indexing via System Preferences:")
        print("   1. Open System Preferences/Settings")
        print("   2. Go to Spotlight → Privacy")
        print("   3. Remove Marketing drive from exclusion list")
        
    elif "enabled" in status.lower() or "search enabled" in status.lower():
        print("\n✅ Indexing appears to be enabled")
        print("🔧 If tags still not visible, try:")
        print("   1. Wait for indexing to complete (can take hours for large drives)")
        print("   2. Force reindex specific files")
        print("   3. Check file permissions")
        
        # Check a specific file
        test_file = "/Volumes/Marketing/00. Media Library/LIFESTYLE PHOTOS (upload and tag)/lifestyle 01/LIFESTYLE_AND_DETAILS_066.jpg"
        if os.path.exists(test_file):
            print(f"\n🧪 Testing specific file indexing...")
            # Force reindex this file
            subprocess.run(['mdimport', test_file], capture_output=True)
            print(f"   Triggered reindex for test file")
            
            # Check metadata
            result = subprocess.run(['mdls', test_file], capture_output=True, text=True)
            if "kMDItemUserTags" in result.stdout:
                print("   ✅ File has user tags in metadata")
            else:
                print("   ❌ File missing user tags in metadata")
    
    print(f"\n💡 MANUAL STEPS TO ENABLE SPOTLIGHT:")
    print("   1. Open System Preferences (older macOS) or System Settings (newer macOS)")
    print("   2. Search for 'Spotlight'")
    print("   3. Click on Spotlight")
    print("   4. Go to 'Privacy' tab")
    print("   5. If 'Marketing' drive is listed, select it and click '-' to remove")
    print("   6. If not listed, indexing should be working")
    print("   7. Wait for indexing to complete (check Activity Monitor for 'mdworker')")

if __name__ == "__main__":
    main()
