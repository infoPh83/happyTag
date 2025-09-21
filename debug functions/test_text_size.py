#!/usr/bin/env python3
"""
Quick test script to verify text size controls functionality
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt

# Add the project directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utilities.image_card_widget import ImageCardWidget
from utilities.image_flow_manager import ImageFlowManager

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text Size Control Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Set up the UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create control buttons
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        
        self.size_label = QLabel("Current text size: 12px")
        controls_layout.addWidget(self.size_label)
        
        plus_button = QPushButton("Text Size + (textSizePlus)")
        plus_button.clicked.connect(self.increase_text_size)
        controls_layout.addWidget(plus_button)
        
        minus_button = QPushButton("Text Size - (textSizeMinus)")
        minus_button.clicked.connect(self.decrease_text_size)
        controls_layout.addWidget(minus_button)
        
        layout.addWidget(controls_widget)
        
        # Set up text size tracking
        self.current_text_size = 12
        self.min_text_size = 8
        self.max_text_size = 24
        self.text_size_step = 2
        
        # Create a flow manager (simulated)
        self.image_flow_manager = ImageFlowManager()
        layout.addWidget(self.image_flow_manager)
        
        # Create some test image widgets
        test_image_path = "test_images/test.jpg"  # This can be a dummy path for testing
        if os.path.exists("test_images"):
            for i in range(3):
                self.image_flow_manager.add_image(f"test_images/test_{i}.jpg", tags=f"test tag {i}")
        
        print("Text Size Control Test Window Created")
        print("Click + and - buttons to test text size functionality")
        
    def increase_text_size(self):
        """Increase the font size of all text input fields"""
        if self.current_text_size < self.max_text_size:
            self.current_text_size += self.text_size_step
            self._apply_text_size_to_all_widgets()
            print(f"Increased text size to {self.current_text_size}px")
            self.size_label.setText(f"Current text size: {self.current_text_size}px")

    def decrease_text_size(self):
        """Decrease the font size of all text input fields"""
        if self.current_text_size > self.min_text_size:
            self.current_text_size -= self.text_size_step
            self._apply_text_size_to_all_widgets()
            print(f"Decreased text size to {self.current_text_size}px")
            self.size_label.setText(f"Current text size: {self.current_text_size}px")

    def _apply_text_size_to_all_widgets(self):
        """Apply the current text size to all image card widgets"""
        if hasattr(self, 'image_flow_manager') and self.image_flow_manager:
            # Update the flow manager's default text size and apply to all widgets
            self.image_flow_manager.set_text_size(self.current_text_size)
            print(f"Applied text size {self.current_text_size}px to {len(self.image_flow_manager.image_widgets)} widgets")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    
    print("\n=== Text Size Control Test ===")
    print("1. Click 'Text Size +' to increase font size")
    print("2. Click 'Text Size -' to decrease font size")
    print("3. Check that text in image widgets updates correctly")
    print("4. Font size should be limited between 8px and 24px")
    print("===================================\n")
    
    sys.exit(app.exec_())