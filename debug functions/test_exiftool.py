"""
Test script to verify ExifTool utilities work correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utilities.exiftool_utils import (
    initialize_exiftool,
    write_cloudinary_metadata_to_file,
    get_cloudinary_public_id_from_metadata,
    EXIFTOOL_AVAILABLE,
    EXIFTOOL_PATH
)

def test_exiftool_utils():
    """Test the ExifTool utilities"""
    print("Testing ExifTool utilities...")
    
    print(f"ExifTool Available: {EXIFTOOL_AVAILABLE}")
    print(f"ExifTool Path: {EXIFTOOL_PATH}")
    
    if not EXIFTOOL_AVAILABLE:
        print("❌ ExifTool not available - metadata features will not work")
        print("To fix this:")
        print("1. Download ExifTool from https://exiftool.org/")
        print("2. Place exiftool.exe in the 'utilities' folder")
        print("3. Restart the application")
        return False
    else:
        print("✅ ExifTool is available and ready to use")
        return True

if __name__ == "__main__":
    test_exiftool_utils()