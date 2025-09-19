"""
Debug the ExifTool metadata writing issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utilities.exiftool_utils import write_cloudinary_metadata_to_file
from utilities.debug_utils import debug_upload

def test_metadata_writing():
    """Test metadata writing with debug output"""
    test_file = 'd:/Python playfolder/happyTag/test images/1.jpg'  # Use a simpler filename
    public_id = 'TEST_PUBLIC_ID_123'
    tags = ['test', 'debug']
    
    print("Testing metadata writing...")
    result = write_cloudinary_metadata_to_file(test_file, public_id, tags)
    print(f"Result: {result}")

if __name__ == "__main__":
    test_metadata_writing()