#!/usr/bin/env python3
"""
Test the improved filename label with reverse truncation
"""

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
import sys
import os
from pathlib import Path

# Add the current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utilities.image_card_widget import ImageCardWidget

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Improved Filename Label Test")
        self.setGeometry(100, 100, 900, 700)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Test files with different name lengths
        test_cases = [
            ("test_images/large_image.jpg", 150),  # Normal filename, narrow width
            ("test_images/normal_image.jpg", 200),  # Normal filename, medium width
            ("test_images/very_large_image.jpg", 180),  # Longer filename, medium width
            # Simulate very long filename
            ("test_super_long_filename_that_should_definitely_be_truncated_but_show_extension.jpg", 220),
            ("another_extremely_long_filename_with_multiple_words_and_descriptive_text.png", 160)
        ]
        
        for i, (file_path, width) in enumerate(test_cases):
            print(f"Creating test case {i+1}: {os.path.basename(file_path)} with width {width}")
            
            # Create pixmap for files that don't exist
            if not Path(file_path).exists():
                # Create a test pixmap
                pixmap = QPixmap(width, int(width * 0.75))
                pixmap.fill(Qt.gray)
                card = ImageCardWidget(file_path, max_width=width, preview_pixmap=pixmap)
            else:
                card = ImageCardWidget(file_path, max_width=width)
            
            layout.addWidget(card)
            print(f"Added card for: {os.path.basename(file_path)}")

def main():
    app = QApplication(sys.argv)
    
    # Create and show test window
    window = TestWindow()
    window.show()
    
    print("\n=== Filename Label Test Results ===")
    print("Check for:")
    print("1. ✅ Reverse truncation (extensions visible: .jpg, .png)")
    print("2. ✅ No character cutoff (all visible characters properly rendered)")
    print("3. ✅ Improved padding (better spacing around text)")
    print("4. ✅ Natural text wrapping for long filenames")
    
    # Keep window open for 8 seconds
    QTimer.singleShot(8000, app.quit)
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
