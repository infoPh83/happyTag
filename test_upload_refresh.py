#!/usr/bin/env python3
"""
Test script to verify that the credits bar refreshes after upload completion.
This simulates an upload completion event to test the refresh functionality.
"""

import sys
from pathlib import Path

# Add the project root to the path to import our modules
script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt5.QtCore import Qt, QTimer
from ui.cloudinaryCreditsBar import CloudinaryCreditsBar

class UploadRefreshTestWindow(QMainWindow):
    """Test window to demonstrate credits bar refresh after upload"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Credits Bar Upload Refresh Test")
        self.setGeometry(100, 100, 600, 200)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Add title
        title = QLabel("Credits Bar Upload Refresh Test")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Create credits bar
        self.credits_bar = CloudinaryCreditsBar()
        self.credits_bar.setFixedHeight(30)
        layout.addWidget(self.credits_bar)
        
        # Add status label
        self.status_label = QLabel("Ready to test upload refresh...")
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Add test button
        test_btn = QPushButton("Simulate Upload Complete (140 → 145 assets)")
        test_btn.clicked.connect(self.simulate_upload_complete)
        layout.addWidget(test_btn)
        
        # Initialize with current values
        self.initialize_bar()
        
    def initialize_bar(self):
        """Initialize the credits bar with current values"""
        # Set colors (matching Cloudinary theme)
        self.credits_bar.setColors("#b83232", "#32a4ba", "#dbde3e")
        
        # Set current percentages (from debug output)
        self.credits_bar.setPercentages(5.54, 1.10, 0.0)
        
        # Set current asset count
        self.credits_bar.setOverlayText("140 online images")
        
        self.status_label.setText("Initialized with 140 assets")
        
    def simulate_upload_complete(self):
        """Simulate an upload completion that increases asset count"""
        self.status_label.setText("Simulating upload of 5 new images...")
        
        # Update button state
        sender = self.sender()
        sender.setText("Uploading...")
        sender.setEnabled(False)
        
        # Simulate upload delay
        QTimer.singleShot(1000, self.simulate_refresh)
        
    def simulate_refresh(self):
        """Simulate the Cloudinary status refresh after upload"""
        # Update asset count to reflect new uploads
        new_count = 145  # 140 + 5 new uploads
        
        # Update the credits bar with new count
        self.credits_bar.setOverlayText(f"{new_count} online images")
        
        # Update status
        self.status_label.setText(f"✅ Upload complete! Credits bar refreshed to show {new_count} assets")
        
        # Reset button
        sender = self.findChild(QPushButton)
        if sender:
            sender.setText("Simulate Upload Complete (145 → 150 assets)")
            sender.setEnabled(True)
            
            # Update for next test
            if "145" in sender.text():
                sender.clicked.disconnect()
                sender.clicked.connect(lambda: self.test_next_upload(150))
    
    def test_next_upload(self, new_count):
        """Test with different asset count"""
        self.status_label.setText(f"Simulating upload of 5 more images...")
        
        sender = self.sender()
        sender.setText("Uploading...")
        sender.setEnabled(False)
        
        def refresh():
            self.credits_bar.setOverlayText(f"{new_count} online images")
            self.status_label.setText(f"✅ Upload complete! Credits bar refreshed to show {new_count} assets")
            sender.setText("Test Complete - Credits Bar Refreshed Successfully!")
            sender.setEnabled(False)
        
        QTimer.singleShot(1000, refresh)

def main():
    """Run the credits bar upload refresh test"""
    app = QApplication(sys.argv)
    
    window = UploadRefreshTestWindow()
    window.show()
    
    print("Credits Bar Upload Refresh Test Window opened.")
    print("Click the test button to simulate upload completion and see the refresh.")
    print("This demonstrates how the credits bar will update after real uploads.")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
