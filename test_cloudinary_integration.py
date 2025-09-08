#!/usr/bin/env python3
"""
Simple test to verify Cloudinary visual status integration
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utilities.image_card_widget import ImageCardWidget

def test_cloudinary_visual_integration():
    """Test the Cloudinary visual integration"""
    
    app = QApplication(sys.argv)
    
    # Create a simple test window
    window = QMainWindow()
    window.setWindowTitle("Cloudinary Visual Integration Test")
    window.setGeometry(200, 200, 600, 400)
    
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    
    layout = QVBoxLayout(central_widget)
    
    # Header
    header = QLabel("Cloudinary Visual Status Integration Test")
    header.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
    header.setAlignment(Qt.AlignCenter)
    layout.addWidget(header)
    
    # Create test images if they don't exist
    test_files = []
    for i in range(3):
        filename = f"test_integration_{i+1}.jpg"
        if not os.path.exists(filename):
            # Create a simple colored pixmap
            pixmap = QPixmap(160, 120)
            colors = [Qt.red, Qt.green, Qt.blue]
            pixmap.fill(colors[i])
            pixmap.save(filename, "JPG")
        test_files.append(filename)
    
    # Cards container
    cards_layout = QHBoxLayout()
    layout.addLayout(cards_layout)
    
    cards = []
    for i, filename in enumerate(test_files):
        card = ImageCardWidget(filename, max_width=150)
        card.set_tags([f"test-{i+1}", "sample"])
        
        # Test different combinations
        if i == 0:
            # Normal state
            pass
        elif i == 1:
            # Cloudinary synced
            card.set_cloudinary_status(True)
        elif i == 2:
            # Cloudinary synced + selected
            card.set_cloudinary_status(True)
            card.set_selected(True)
        
        cards.append(card)
        cards_layout.addWidget(card)
    
    # Status description
    status = QLabel("Left: Normal | Center: Cloudinary Synced (Dark Yellow) | Right: Synced + Selected")
    status.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 4px;")
    status.setAlignment(Qt.AlignCenter)
    layout.addWidget(status)
    
    # Control button
    toggle_btn = QPushButton("Toggle Center Card Cloudinary Status")
    toggle_btn.clicked.connect(lambda: toggle_cloudinary_status(cards[1]))
    layout.addWidget(toggle_btn)
    
    def toggle_cloudinary_status(card):
        current = card.get_cloudinary_status()
        card.set_cloudinary_status(not current)
        print(f"Toggled Cloudinary status to: {not current}")
    
    window.show()
    
    print("🎨 Cloudinary Visual Integration Test")
    print("=" * 50)
    print("Expected Visual Results:")
    print("• Left card: White background (normal)")
    print("• Center card: Dark yellow background (Cloudinary synced)")
    print("• Right card: Light golden background + blue border (synced + selected)")
    print("=" * 50)
    print("Use the toggle button to test dynamic status changes!")
    
    # Clean up function
    def cleanup():
        for filename in test_files:
            try:
                os.remove(filename)
                print(f"Cleaned up {filename}")
            except:
                pass
    
    # Schedule cleanup on app exit
    app.aboutToQuit.connect(cleanup)
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(test_cloudinary_visual_integration())
