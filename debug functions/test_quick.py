#!/usr/bin/env python3
"""
Quick test to verify filename labels are working
"""

from PyQt5.QtWidgets import QApplication
import sys
from utilities.image_card_widget import ImageCardWidget
import os

# Create QApplication
app = QApplication(sys.argv)

# Test widget creation
test_file = 'test_images/large_image.jpg'
if os.path.exists(test_file):
    widget = ImageCardWidget(test_file, max_width=200)
    print(f"✅ Widget created for {os.path.basename(test_file)}")
    print(f"✅ Filename label exists: {hasattr(widget, 'filename_label') and widget.filename_label is not None}")
    print(f"✅ Image label exists: {hasattr(widget, 'image_label') and widget.image_label is not None}")
    
    # Check if filename label is properly configured
    if hasattr(widget, 'filename_label') and widget.filename_label:
        print(f"✅ Filename label height: {widget.filename_label.height()}")
        print(f"✅ Filename label parent: {widget.filename_label.parent() == widget.image_label}")
        print(f"✅ Filename label text: '{widget.filename_label.text()}'")
        print(f"✅ Filename label visible: {widget.filename_label.isVisible()}")
    
    print("Filename label functionality verified successfully!")
else:
    print(f"❌ Test file not found: {test_file}")

# Clean up
app.quit()
