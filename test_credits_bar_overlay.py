#!/usr/bin/env python3
"""
Test script to demonstrate the CloudinaryCreditsBar with text overlay feature.
Shows how to display the number of assets on Cloudinary as overlapping text.
"""

import sys
from pathlib import Path

# Add the project root to the path to import our modules
script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt5.QtCore import Qt
from ui.cloudinaryCreditsBar import CloudinaryCreditsBar

class CreditsBarTestWindow(QMainWindow):
    """Test window to demonstrate the credits bar with text overlay"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cloudinary Credits Bar - Text Overlay Test")
        self.setGeometry(100, 100, 500, 300)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Add title
        title = QLabel("Cloudinary Credits Bar with Asset Count Overlay")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Create credits bar
        self.credits_bar = CloudinaryCreditsBar()
        self.credits_bar.setFixedHeight(30)  # Make it taller for better text visibility
        layout.addWidget(self.credits_bar)
        
        # Add description
        description = QLabel("The credits bar shows usage percentages with centered text showing the number of online images.")
        description.setWordWrap(True)
        description.setStyleSheet("color: #666; font-size: 12px;")
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)
        
        # Add test buttons
        button_layout = QVBoxLayout()
        
        test1_btn = QPushButton("Test: 156 online images")
        test1_btn.clicked.connect(lambda: self.test_scenario(4.5, 12.3, 2.1, 156))
        button_layout.addWidget(test1_btn)
        
        test2_btn = QPushButton("Test: 9 online images (current)")
        test2_btn.clicked.connect(lambda: self.test_scenario(4.896, 0.033, 0.0, 9))
        button_layout.addWidget(test2_btn)
        
        test3_btn = QPushButton("Test: 1,247 online images")
        test3_btn.clicked.connect(lambda: self.test_scenario(85.2, 8.7, 3.1, 1247))
        button_layout.addWidget(test3_btn)
        
        test4_btn = QPushButton("Test: No text overlay")
        test4_btn.clicked.connect(lambda: self.test_scenario(25.0, 15.5, 8.2, 0))
        button_layout.addWidget(test4_btn)
        
        layout.addLayout(button_layout)
        
        # Initialize with default values
        self.test_scenario(4.896, 0.033, 0.0, 9)
        
    def test_scenario(self, storage_pct, utilities_pct, usage_pct, asset_count):
        """Test a specific scenario with given percentages and asset count"""
        print(f"\nTesting scenario:")
        print(f"  Storage: {storage_pct}%")
        print(f"  Utilities: {utilities_pct}%") 
        print(f"  Usage: {usage_pct}%")
        print(f"  Assets: {asset_count}")
        
        # Set colors (matching Cloudinary theme)
        self.credits_bar.setColors("#b83232", "#32a4ba", "#dbde3e")
        
        # Set percentages
        self.credits_bar.setPercentages(storage_pct, utilities_pct, usage_pct)
        
        # Set overlay text
        if asset_count > 0:
            overlay_text = f"{asset_count:,} online images"  # Format with commas for large numbers
        else:
            overlay_text = ""
        
        self.credits_bar.setOverlayText(overlay_text)
        
        print(f"  Overlay text: '{overlay_text}'")

def main():
    """Run the credits bar test"""
    app = QApplication(sys.argv)
    
    window = CreditsBarTestWindow()
    window.show()
    
    print("Credits Bar Test Window opened.")
    print("Click the test buttons to see different scenarios.")
    print("The text overlay shows the number of assets currently on Cloudinary.")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
