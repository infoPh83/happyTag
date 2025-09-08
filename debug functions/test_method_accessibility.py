#!/usr/bin/env python3
"""
Test script to verify that process_single_image_assessment method is accessible
without requiring full dependencies
"""

import sys
import inspect
from pathlib import Path

# Add utilities to path
sys.path.append(str(Path(__file__).parent / "utilities"))

def test_method_accessibility():
    """Test if the method is properly defined in the class"""
    try:
        # We'll mock the dependencies that cause import errors
        import sys
        from unittest.mock import MagicMock
        
        # Mock the problematic imports
        sys.modules['requests'] = MagicMock()
        sys.modules['cloudinary'] = MagicMock()
        sys.modules['cloudinary.uploader'] = MagicMock()
        sys.modules['cloudinary.api'] = MagicMock()
        sys.modules['PIL'] = MagicMock()
        sys.modules['PIL.Image'] = MagicMock()
        sys.modules['PIL.ExifTags'] = MagicMock()
        
        # Now try to import the CloudinaryUpdater
        from cloudinary_update_v13 import CloudinaryUpdater
        
        print("✅ CloudinaryUpdater imported successfully!")
        
        # Check if the method exists
        if hasattr(CloudinaryUpdater, 'process_single_image_assessment'):
            print("✅ process_single_image_assessment method found!")
            
            # Get method info
            method = getattr(CloudinaryUpdater, 'process_single_image_assessment')
            sig = inspect.signature(method)
            print(f"   Method signature: {sig}")
            
            # Check if it's properly a method (has self parameter)
            params = list(sig.parameters.keys())
            if 'self' in params:
                print("✅ Method properly defined with 'self' parameter!")
                print(f"   Parameters: {params}")
                return True
            else:
                print("❌ Method missing 'self' parameter - not a proper class method!")
                return False
        else:
            print("❌ process_single_image_assessment method NOT found!")
            # List available methods for debugging
            methods = [name for name in dir(CloudinaryUpdater) if not name.startswith('_')]
            print(f"   Available methods: {methods}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing method accessibility: {e}")
        return False

if __name__ == "__main__":
    success = test_method_accessibility()
    sys.exit(0 if success else 1)
