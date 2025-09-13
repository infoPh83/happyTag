#!/usr/bin/env python3
"""
Test CloudinaryCreditsBar Performance Optimizations
Tests the caching mechanism and reduced paint events
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import QTimer
from ui.cloudinaryCreditsBar import CloudinaryCreditsBar

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CloudinaryCreditsBar Performance Test")
        self.setGeometry(100, 100, 400, 200)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create credits bar
        self.credits_bar = CloudinaryCreditsBar()
        layout.addWidget(self.credits_bar)
        
        # Create test buttons
        test_button1 = QPushButton("Set Values (25, 15, 10)")
        test_button1.clicked.connect(lambda: self.test_set_values(25, 15, 10))
        layout.addWidget(test_button1)
        
        test_button2 = QPushButton("Set Same Values Again (should be cached)")
        test_button2.clicked.connect(lambda: self.test_set_values(25, 15, 10))
        layout.addWidget(test_button2)
        
        test_button3 = QPushButton("Set New Values (40, 20, 5)")
        test_button3.clicked.connect(lambda: self.test_set_values(40, 20, 5))
        layout.addWidget(test_button3)
        
        resize_button = QPushButton("Trigger Resize")
        resize_button.clicked.connect(self.trigger_resize)
        layout.addWidget(resize_button)
        
        # Set initial values
        print("Setting initial values...")
        self.credits_bar.setPercentages(30, 20, 15)
        
        # Test automatic repaints
        self.repaint_timer = QTimer()
        self.repaint_timer.timeout.connect(self.trigger_repaint)
        
        trigger_repaints_button = QPushButton("Start Automatic Repaints (should use cache)")
        trigger_repaints_button.clicked.connect(self.start_repaint_test)
        layout.addWidget(trigger_repaints_button)
        
        stop_repaints_button = QPushButton("Stop Automatic Repaints")
        stop_repaints_button.clicked.connect(self.stop_repaint_test)
        layout.addWidget(stop_repaints_button)
        
    def test_set_values(self, storage, utilities, usage):
        print(f"\n=== Testing setPercentages({storage}, {utilities}, {usage}) ===")
        self.credits_bar.setPercentages(storage, utilities, usage)
        
    def trigger_resize(self):
        print("\n=== Testing Resize (should invalidate cache) ===")
        current_size = self.size()
        self.resize(current_size.width() + 50, current_size.height())
        
    def trigger_repaint(self):
        # Force a repaint without changing values (should use cache)
        self.credits_bar.update()
        
    def start_repaint_test(self):
        print("\n=== Starting automatic repaint test (every 100ms) ===")
        print("This should demonstrate cache effectiveness...")
        self.repaint_timer.start(100)  # Trigger repaint every 100ms
        
    def stop_repaint_test(self):
        print("\n=== Stopping automatic repaint test ===")
        self.repaint_timer.stop()

def main():
    app = QApplication(sys.argv)
    
    print("=" * 60)
    print("CloudinaryCreditsBar Performance Test")
    print("=" * 60)
    print("This test will show:")
    print("1. Initial paint (cache miss)")
    print("2. Subsequent paints with same values (cache hit)")
    print("3. Paint after value changes (cache miss)")
    print("4. Paint after resize (cache miss)")
    print("5. Excessive repaints with same data (cache hits)")
    print("=" * 60)
    
    window = TestWindow()
    window.show()
    
    print("\nWindow shown. Use the buttons to test different scenarios.")
    print("Watch the debug output to see cache behavior...")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()