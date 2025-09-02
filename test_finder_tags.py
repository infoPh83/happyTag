#!/usr/bin/env python3

import os
import subprocess
import plistlib
import tempfile

def write_macos_finder_tags(file_path, keywords):
    """Write macOS Finder tags using extended attributes"""
    try:
        if not keywords or os.name != 'posix' or not hasattr(os, 'uname') or os.uname().sysname != 'Darwin':
            return True, "Not macOS or no keywords"
        
        # Create a plist with the tag data
        tag_data = []
        colors = [1, 2, 3, 4, 5, 6, 7]  # Different colors for visibility
        for i, keyword in enumerate(keywords):
            # Create a colored tag entry with rotating colors
            tag_entry = {
                'n': keyword,  # tag name
                'l': colors[i % len(colors)],  # label index (1-7 = different colors)
            }
            tag_data.append(tag_entry)
        
        # Convert to binary plist format
        plist_data = plistlib.dumps(tag_data, fmt=plistlib.FMT_BINARY)
        
        # Convert binary data to hex string
        hex_data = plist_data.hex()
        
        # Use xattr command with hex data
        result = subprocess.run([
            'xattr', '-w', '-x', 'com.apple.metadata:_kMDItemUserTags',
            hex_data, file_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Successfully wrote macOS Finder tags to {os.path.basename(file_path)}")
            return True, "Success"
        else:
            print(f"Failed to write macOS Finder tags: {result.stderr}")
            return False, f"xattr error: {result.stderr}"
            
    except Exception as e:
        print(f"Error writing macOS Finder tags: {e}")
        return False, f"Error: {str(e)}"

def read_finder_tags(file_path):
    """Read macOS Finder tags from a file"""
    try:
        result = subprocess.run([
            'xattr', '-p', '-x', 'com.apple.metadata:_kMDItemUserTags', file_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            # Convert hex string back to binary
            hex_string = result.stdout.replace('\n', '').replace(' ', '')
            if hex_string:
                plist_data = bytes.fromhex(hex_string)
                # Parse the binary plist data
                tag_list = plistlib.loads(plist_data)
                tags = [tag['n'] for tag in tag_list if 'n' in tag]
                return tags
        return []
    except Exception as e:
        print(f"Error reading Finder tags: {e}")
        return []

if __name__ == "__main__":
    # Test file
    test_file = "test_finder_tags_demo.jpg"
    
    if not os.path.exists(test_file):
        print(f"Test file {test_file} not found")
        exit(1)
    
    # Test keywords
    test_keywords = ["VisibleInFinder", "Test", "macOS", "Tags"]
    
    print(f"Writing Finder tags to {test_file}: {test_keywords}")
    success, msg = write_macos_finder_tags(test_file, test_keywords)
    
    if success:
        print("Write successful!")
        
        # Read back the tags
        print("Reading back tags...")
        read_tags = read_finder_tags(test_file)
        print(f"Read tags: {read_tags}")
        
        # Force reindex
        print("Forcing Spotlight reindex...")
        subprocess.run(['mdimport', test_file], capture_output=True)
        
        print(f"\n✅ SUCCESS! File '{test_file}' now has Finder tags.")
        print("🔍 To see them:")
        print("   1. Open Finder")
        print("   2. Navigate to this folder")
        print("   3. Look for colored tags next to the filename")
        print("   4. Right-click the file and check 'Tags' in the context menu")
        
    else:
        print(f"Write failed: {msg}")
