#!/usr/bin/env python3
"""
Quick test to verify UserComment extraction works with JSON output
"""
import sys
import os
import subprocess
import json

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_usercomment_extraction():
    """Test UserComment extraction for the problematic image"""
    
    # Test file that should have a public_id
    test_file = "test images/test_finder_tags_demo.jpg"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
        
    print(f"🔍 Testing UserComment extraction for: {test_file}")
    
    try:
        # Initialize ExifTool using the main app's initialization
        from utilities.exiftool_detector import initialize_exiftool, get_exiftool_info
        
        print("🔧 Initializing ExifTool...")
        initialize_exiftool()
        
        info = get_exiftool_info()
        print(f"   ExifTool available: {info['available']}")
        print(f"   ExifTool path: {info['path']}")
        
        if not info['available']:
            print("❌ ExifTool not available after initialization")
            return False
            
        from utilities.exiftool_utils import get_exiftool_command
        
        # Get ExifTool command
        exiftool_cmd = get_exiftool_command()
        if not exiftool_cmd:
            print("❌ ExifTool command not available")
            return False
            
        print(f"✅ ExifTool command: {exiftool_cmd}")
        
        # Test 1: Original lightweight assessment approach (JSON output)
        print("\n📋 Test 1: Lightweight assessment approach (JSON)")
        cmd = exiftool_cmd + ['-UserComment', '-j', test_file]
        print(f"   Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"   Raw output: {result.stdout}")
            data = json.loads(result.stdout)
            if data:
                user_comment = data[0].get('UserComment', '')
                print(f"   UserComment: '{user_comment}'")
                if user_comment and user_comment.startswith('cloudinary_public_id:'):
                    public_id = user_comment.replace('cloudinary_public_id:', '').strip()
                    print(f"   ✅ Found public_id: '{public_id}'")
                else:
                    print(f"   ❌ No valid public_id found")
            else:
                print("   ❌ No data returned")
        else:
            print(f"   ❌ ExifTool failed: {result.stderr}")
        
        # Test 2: New comprehensive approach (JSON output)
        print("\n📋 Test 2: Comprehensive approach (JSON)")
        cmd = exiftool_cmd + ['-DateTimeOriginal', '-CreateDate', '-IPTC:Keywords', '-XMP:Keywords', '-XMP:Subject', '-UserComment', '-j', test_file]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"   Raw output: {result.stdout}")
            data = json.loads(result.stdout)
            if data:
                metadata_dict = data[0]
                print(f"   Available fields: {list(metadata_dict.keys())}")
                
                # Check UserComment (handle both prefixed and non-prefixed)
                user_comment = None
                for field_name in ['UserComment', 'EXIF:UserComment']:
                    if field_name in metadata_dict:
                        user_comment = metadata_dict[field_name]
                        print(f"   Found {field_name}: '{user_comment}'")
                        break
                
                # Check date fields (handle both prefixed and non-prefixed)
                for date_field in ['DateTimeOriginal', 'CreateDate', 'EXIF:DateTimeOriginal', 'EXIF:CreateDate', 'XMP:CreateDate']:
                    if date_field in metadata_dict:
                        print(f"   Found {date_field}: {metadata_dict[date_field]}")

                # Check keyword fields (handle both prefixed and non-prefixed)
                for keyword_field in ['Keywords', 'Subject', 'IPTC:Keywords', 'XMP:Keywords', 'XMP:Subject']:
                    if keyword_field in metadata_dict:
                        print(f"   Found {keyword_field}: {metadata_dict[keyword_field]}")
                        
                if user_comment and user_comment.startswith('cloudinary_public_id:'):
                    public_id = user_comment.replace('cloudinary_public_id:', '').strip()
                    print(f"   ✅ Found public_id: '{public_id}'")
                    print("   ✅ Comprehensive metadata extraction is working correctly!")
                    return True
                else:
                    print(f"   ❌ No valid public_id found in user_comment: '{user_comment}'")
                    return False
            else:
                print("   ❌ No data returned")
                return False
        else:
            print(f"   ❌ ExifTool failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    success = test_usercomment_extraction()
    if success:
        print("\n🎉 UserComment extraction test PASSED!")
        sys.exit(0)
    else:
        print("\n❌ UserComment extraction test FAILED!")
        sys.exit(1)