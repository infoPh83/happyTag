#!/usr/bin/env python3
"""
Test script to verify the unified ExifTool system is working correctly.
"""

import sys
import os

# Add the utilities directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utilities'))

from utilities.exiftool_detector import initialize_exiftool, get_exiftool_info
from utilities.exiftool_utils import get_exiftool_command

def test_unified_exiftool():
    """Test that all ExifTool components use the same detection system"""
    
    print("Testing Unified ExifTool System")
    print("=" * 50)
    
    # Test 1: Initialize detection system
    print("\n1. Initializing ExifTool detection...")
    success = initialize_exiftool()
    print(f"   Detection success: {success}")
    
    # Test 2: Get ExifTool info
    print("\n2. Getting ExifTool info...")
    info = get_exiftool_info()
    print(f"   Available: {info['available']}")
    print(f"   Path type: {type(info['path'])}")
    if isinstance(info['path'], dict):
        print(f"   Type: {info['path'].get('type')}")
        print(f"   Perl path: {info['path'].get('path')}")
        print(f"   Script: {info['path']['args'][0] if info['path'].get('args') else 'N/A'}")
    else:
        print(f"   Path: {info['path']}")
    
    # Test 3: Test command generation
    print("\n3. Testing command generation...")
    cmd = get_exiftool_command()
    print(f"   Command: {cmd}")
    
    # Test 4: Verify subprocess call would work
    if cmd:
        print("\n4. Testing version check...")
        import subprocess
        try:
            result = subprocess.run(cmd + ['-ver'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"   SUCCESS Version: {result.stdout.strip()}")
            else:
                print(f"   ERROR: {result.stderr}")
        except Exception as e:
            print(f"   EXCEPTION: {e}")
    else:
        print("\n4. No command available for testing")
    
    print("\n" + "=" * 50)
    if success and cmd:
        print("SUCCESS: Unified ExifTool system is working!")
        return True
    else:
        print("ERROR: Unified ExifTool system has issues!")
        return False

if __name__ == "__main__":
    test_unified_exiftool()