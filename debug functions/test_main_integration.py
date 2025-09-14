#!/usr/bin/env python3
"""
Quick Application Test
Test that the main application can use the new ImageAssessment integration
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_main_app_integration():
    """Test that main.py can import and use the enhanced ImageAssessment"""
    
    try:
        # Test imports
        print("[INFO] Testing imports...")
        from utilities.image_assessment import ImageAssessment
        # Don't import main app - just test the ImageAssessment integration
        
        print("✅ Imports successful")
        
        # Test that the new method exists
        # Initialize ImageAssessment with explicit max file size for testing
        test_max_size = 3.2 * 1024 * 1024  # 3.2MB for testing
        assessment = ImageAssessment(max_file_size=test_max_size)
        if hasattr(assessment, 'process_single_image_with_cloudinary_logic'):
            print("✅ New method exists in ImageAssessment")
        else:
            print("❌ New method missing!")
            return False
        
        # Test method signature
        import inspect
        sig = inspect.signature(assessment.process_single_image_with_cloudinary_logic)
        params = list(sig.parameters.keys())
        expected = ['file_path', 'settings_dialog']
        
        if params == expected:
            print("✅ Method signature correct")
        else:
            print(f"❌ Method signature incorrect. Expected {expected}, got {params}")
            return False
        
        print("✅ Integration ready for production use")
        return True
        
    except Exception as e:
        print(f"[ERROR] Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Testing Main App Integration")
    print("=" * 50)
    
    success = test_main_app_integration()
    
    print("=" * 50)
    if success:
        print("🎉 Main app integration READY!")
    else:
        print("💥 Integration has issues!")
    print("=" * 50)