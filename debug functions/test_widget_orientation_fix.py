#!/usr/bin/env python3
"""
Test ImageCardWidget Portrait Orientation Fix
Test the widget fallback case for EXIF orientation correction
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from utilities.image_card_widget import ImageCardWidget

def test_widget_orientation_fix():
    """Test ImageCardWidget with orientation test images"""
    app = QApplication([])
    
    print("🧪 Testing ImageCardWidget Portrait Orientation Fix")
    print("=" * 60)
    
    test_images = [
        "debug functions/test_orientation_6.jpg",  # 90° clockwise (should be portrait)  
        "debug functions/test_orientation_8.jpg",  # 270° clockwise (should be portrait)
    ]
    
    for img_path in test_images:
        if os.path.exists(img_path):
            print(f"\n📸 Testing widget with: {os.path.basename(img_path)}")
            
            try:
                # Create widget WITHOUT preview_pixmap to trigger fallback case
                widget = ImageCardWidget(
                    file_path=img_path,
                    max_width=300,
                    preview_pixmap=None,  # Force fallback to file loading
                    cloudinary_synced=False
                )
                
                # The widget should automatically load and apply orientation correction
                print(f"  ✅ Widget created successfully")
                
                # Check if image loaded correctly by accessing the image label pixmap
                if hasattr(widget, 'image_label') and widget.image_label:
                    pixmap = widget.image_label.pixmap()
                    if pixmap and not pixmap.isNull():
                        width, height = pixmap.width(), pixmap.height()
                        print(f"  📏 Widget image size: {width}x{height}")
                        
                        if height > width:
                            print(f"  🎯 SUCCESS: Portrait orientation maintained (H:{height} > W:{width})")
                        else:
                            print(f"  ⚠️  Appears landscape (W:{width} >= H:{height}) - check orientation fix")
                    else:
                        print(f"  ❌ No pixmap found in widget")
                else:
                    print(f"  ❌ Image label not found in widget")
                    
            except Exception as e:
                print(f"  💥 Error creating widget: {e}")
        else:
            print(f"\n❌ Test image not found: {img_path}")
    
    print(f"\n✅ Widget orientation test complete!")

if __name__ == "__main__":
    test_widget_orientation_fix()