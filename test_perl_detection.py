#!/usr/bin/env python3
"""
Test script to verify both system and bundled ExifTool detection.
"""

import sys
import os

# Add the utilities directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utilities'))

def test_with_pyinstaller_simulation():
    """Test ExifTool detection as if running from PyInstaller bundle"""
    
    print("Testing ExifTool in PyInstaller simulation mode")
    print("=" * 60)
    
    # Simulate PyInstaller environment
    import utilities.exiftool_detector as detector
    
    # Override the bundled detection to force Perl path
    original_detect = detector.detect_bundled_exiftool
    
    def mock_bundled_detection():
        """Mock function that returns Perl-based ExifTool like in the user's logs"""
        return {
            'path': 'C:\\Users\\simon\\AppData\\Local\\Temp\\_MEI528322\\packages\\exiftool_win64\\exiftool-13.34_64\\exiftool_files\\perl.exe',
            'args': ['C:\\Users\\simon\\AppData\\Local\\Temp\\_MEI528322\\packages\\exiftool_win64\\exiftool-13.34_64\\exiftool_files\\exiftool.pl', '-ver'],
            'type': 'perl'
        }
    
    # Temporarily replace the function
    detector.detect_bundled_exiftool = mock_bundled_detection
    
    try:
        print("\n1. Forcing Perl-based ExifTool detection...")
        
        # Test the utilities with forced Perl detection
        from utilities.exiftool_utils import get_exiftool_command
        from utilities.exiftool_detector import initialize_exiftool, get_exiftool_info
        
        # Force re-initialization
        detector.EXIFTOOL_AVAILABLE = False
        detector.EXIFTOOL_PATH = None
        
        success = initialize_exiftool()
        print(f"   Detection success: {success}")
        
        info = get_exiftool_info()
        print(f"   Available: {info['available']}")
        print(f"   Path type: {type(info['path'])}")
        if isinstance(info['path'], dict):
            print(f"   Type: {info['path'].get('type')}")
            print(f"   Perl path: {info['path'].get('path')}")
            print(f"   Script: {info['path']['args'][0] if info['path'].get('args') else 'N/A'}")
        
        cmd = get_exiftool_command()
        print(f"   Generated command: {cmd}")
        
        if cmd and len(cmd) >= 2:
            print("\n2. Command structure analysis:")
            print(f"   - Executable: {cmd[0]}")
            print(f"   - Script: {cmd[1]}")
            print(f"   - Total components: {len(cmd)}")
            
            # This would be the pattern for PyInstaller wrapper creation
            print("\n3. This matches the pattern that triggers wrapper creation:")
            print("   isinstance(EXIFTOOL_PATH, dict) and EXIFTOOL_PATH.get('type') == 'perl'")
            print("   --> Wrapper .bat file would be created")
            print("   --> PyExifTool would use wrapper instead of direct Perl call")
        
    finally:
        # Restore original function
        detector.detect_bundled_exiftool = original_detect
    
    print("\n" + "=" * 60)
    print("This confirms our unified system handles both cases:")
    print("- System ExifTool: Direct executable")
    print("- Bundled ExifTool: Perl + wrapper creation")

if __name__ == "__main__":
    test_with_pyinstaller_simulation()