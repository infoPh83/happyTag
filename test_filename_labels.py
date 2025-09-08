#!/usr/bin/env python3
"""
Test the filename label functionality of ImageCardWidget
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

# Add the current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utilities.image_card_widget import ImageCardWidget

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Filename Label Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Find test images in the test_images directory
        test_images_dir = Path('test_images')
        test_files = []
        if test_images_dir.exists():
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.tiff', '*.tif', '*.bmp', '*.gif', '*.webp']:
                test_files.extend(test_images_dir.glob(ext))
                if len(test_files) >= 3:  # We only need a few for testing
                    break
        
        if not test_files:
            # Create a test file entry even if no images found
            test_files = [Path("test_image_very_long_filename_that_should_be_truncated.jpg")]
        
        # Create image cards with different widths to test truncation
        widths = [200, 150, 300]
        for i, file_path in enumerate(test_files[:3]):
            width = widths[i % len(widths)]
            print(f"Creating ImageCardWidget for {file_path} with width {width}")
            
            # Create a dummy pixmap if file doesn't exist
            if not file_path.exists():
                # Create a simple test pixmap
                pixmap = QPixmap(width, int(width * 0.75))
                pixmap.fill(Qt.blue)
                card = ImageCardWidget(str(file_path), max_width=width, preview_pixmap=pixmap)
            else:
                card = ImageCardWidget(str(file_path), max_width=width)
            
            layout.addWidget(card)
            print(f"Added ImageCardWidget for {file_path.name}")

def main():
    app = QApplication(sys.argv)
    
    # Create and show test window
    window = TestWindow()
    window.show()
    
    print("Filename label test window created. Check if filename labels appear on images.")
    print("Look for:")
    print("- Semi-transparent black labels at top-left of each image")
    print("- Filename text (without path) in white")
    print("- Text truncation with ellipsis if filename is too long")
    
    # Run for a few seconds then close
    from PyQt5.QtCore import QTimer
    QTimer.singleShot(5000, app.quit)  # Close after 5 seconds
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
