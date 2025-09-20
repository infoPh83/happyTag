#!/usr/bin/env python3
"""
Debug System Demonstration
==========================

This script demonstrates how to use the improved debug categorization system in HappyTag.

Run this script with different HAPPYTAG_DEBUG environment variable settings to see
how debug output can be controlled for better development experience and performance testing.
"""

import os
import sys
import time

# Add the current directory to Python path so we can import utilities
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utilities.debug_utils import *

def demo_all_categories():
    """Demonstrate all available debug categories"""
    print("\n=== Demonstrating All Debug Categories ===")
    
    # Test each category
    debug_startup("Application starting up...")
    debug_layout("Layout being updated...")
    debug_tags("Processing image tags...")
    debug_metadata("Reading EXIF metadata...")
    debug_cloudinary("Uploading to Cloudinary...")
    debug_assessment("Running image assessment...")
    debug_upload("File upload in progress...")
    debug_memory("Memory usage: 256MB")
    debug_timers("Operation took 1.23 seconds")
    debug_ui_events("Button clicked")
    debug_file_ops("Reading file: image.jpg")
    debug_errors("This is an error message")
    
    # New categories added during debug system improvement
    debug_image_loading("Loading image preview...")
    debug_exiftool("Running ExifTool command...")
    debug_layout_fix("Fixing layout issue...")
    debug_width_control("Adjusting widget width...")
    debug_ctrl_operations("Ctrl+click operation...")
    debug_orientation("Correcting image orientation...")
    debug_color_conversion("Converting color profile...")
    debug_file_dialogs("Opening file dialog...")
    debug_tag_widgets("Updating tag widgets...")
    debug_temp_files("Creating temporary file...")

def demo_performance_testing():
    """Demonstrate performance testing with minimal debug output"""
    print("\n=== Performance Testing Demo ===")
    print("To test performance with minimal debug output, run:")
    print('  $env:HAPPYTAG_DEBUG="errors"; python main.py')
    print("\nOr for completely silent operation:")
    print('  $env:HAPPYTAG_DEBUG=""; python main.py')
    
def demo_selective_debugging():
    """Demonstrate selective debugging for specific features"""
    print("\n=== Selective Debugging Examples ===")
    print("\nFor image loading issues:")
    print('  $env:HAPPYTAG_DEBUG="image_loading,temp_files,color_conversion"')
    
    print("\nFor ExifTool problems:")
    print('  $env:HAPPYTAG_DEBUG="exiftool,file_ops,errors"')
    
    print("\nFor layout problems:")
    print('  $env:HAPPYTAG_DEBUG="layout,layout_fix,width_control"')
    
    print("\nFor business/upload issues:")
    print('  $env:HAPPYTAG_DEBUG="business,cloudinary,upload,assessment"')

def main():
    """Main demonstration function"""
    print("HappyTag Debug System Demonstration")
    print("=" * 50)
    
    # Show current debug configuration
    print_debug_status()
    
    # Get current environment setting
    current_debug = os.environ.get('HAPPYTAG_DEBUG', 'default')
    print(f"\nCurrent HAPPYTAG_DEBUG setting: {current_debug}")
    
    # Run demos
    demo_all_categories()
    demo_performance_testing()
    demo_selective_debugging()
    
    print("\n" + "=" * 50)
    print("Debug system demonstration complete!")
    print("\nKey Benefits:")
    print("✅ Granular control over debug output")
    print("✅ Performance testing with minimal output")
    print("✅ Selective debugging for specific features")
    print("✅ Clean categorization of all debug messages")

if __name__ == "__main__":
    main()