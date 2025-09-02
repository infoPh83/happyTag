#!/usr/bin/env python3
"""
Compare macOS native tags vs our implementation
"""

import subprocess
import os

def analyze_file(filepath, label):
    print(f"\n🔍 Analyzing: {label}")
    print(f"File: {filepath}")
    print("-" * 50)
    
    if not os.path.exists(filepath):
        print("❌ File not found")
        return
    
    # Check extended attributes
    print("Extended Attributes:")
    try:
        result = subprocess.run(['xattr', filepath], capture_output=True, text=True)
        attrs = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        for attr in attrs:
            if attr:
                print(f"  • {attr}")
                
                # For the key attribute, show size
                if '_kMDItemUserTags' in attr:
                    size_result = subprocess.run(['xattr', '-p', attr, filepath], 
                                                capture_output=True)
                    if size_result.returncode == 0:
                        size = len(size_result.stdout)
                        print(f"    Size: {size} bytes")
                        
                        # Try to show first few readable characters
                        try:
                            hex_data = size_result.stdout.hex()
                            print(f"    Hex preview: {hex_data[:32]}...")
                        except:
                            pass
        
        if not attrs or not any(attrs):
            print("  (No extended attributes)")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Check Spotlight metadata  
    print("\nSpotlight Metadata:")
    try:
        result = subprocess.run(['mdls', filepath], capture_output=True, text=True)
        if result.stdout.strip():
            lines = result.stdout.split('\n')
            tag_lines = [line for line in lines if any(keyword in line.lower() 
                        for keyword in ['tag', 'keyword', 'subject'])]
            
            if tag_lines:
                for line in tag_lines:
                    print(f"  {line.strip()}")
            else:
                print("  (No tag-related metadata found)")
        else:
            print("  (No Spotlight metadata)")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def main():
    print("🔬 macOS Finder Tags Analysis")
    print("=" * 60)
    
    # Compare both files
    analyze_file("test images/1.jpg", "Original file (our tags)")
    analyze_file("test images/1 macOs tags.jpg", "macOS Finder tagged file")
    
    print("\n" + "=" * 60)
    print("🎯 Key Insights:")
    
    print("\n1. Both files should have similar extended attribute structures")
    print("2. The difference might be in the binary plist format")
    print("3. Spotlight indexing affects visibility in both cases")
    
    print("\n🧪 Manual Test:")
    print("Right-click 'test images/1 macOs tags.jpg' in Finder")
    print("Select 'Get Info' - do YOU see tags there?")
    print("If YES: the format is correct but our implementation needs adjustment")
    print("If NO: it's definitely a Spotlight indexing issue")

if __name__ == "__main__":
    main()
