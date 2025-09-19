#!/usr/bin/env python3
"""
Test script to verify the upload progress bar implementation.
This script simulates the upload progress signals to verify the UI updates correctly.
"""

import sys
import os
from pathlib import Path
import time

# Add the project root to the path to import our modules
script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
# from main import MainWindow  # We'll implement our own test version instead

class UploadSimulator(QObject):
    """Simulate upload progress signals"""
    upload_progress_signal = pyqtSignal(int)  # Progress percentage (0-100)
    upload_status_signal = pyqtSignal(str)    # Status message
    upload_complete_signal = pyqtSignal(list) # [uploaded_count, error_count]
    upload_preview_signal = pyqtSignal(str)   # Current file being processed

    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.current_progress = 0
        self.test_files = [
            "test_image_1.jpg",
            "test_image_2.jpg", 
            "test_image_3.jpg",
            "test_image_4.jpg",
            "test_image_5.jpg"
        ]
        self.current_file_index = 0

    def start_simulation(self):
        """Start the upload simulation"""
        self.current_progress = 0
        self.current_file_index = 0
        self.upload_status_signal.emit("Starting upload simulation...")
        self.timer.start(500)  # Update every 500ms

    def update_progress(self):
        """Update progress simulation"""
        if self.current_progress >= 100:
            self.timer.stop()
            self.upload_complete_signal.emit([len(self.test_files), 0, 0])
            return

        # Update current file preview
        if self.current_file_index < len(self.test_files):
            self.upload_preview_signal.emit(f"Uploading: {self.test_files[self.current_file_index]}")

        # Update progress
        self.current_progress += 20  # Increment by 20% each update
        self.upload_progress_signal.emit(self.current_progress)
        
        # Update status
        files_completed = int((self.current_progress / 100) * len(self.test_files))
        self.upload_status_signal.emit(f"Uploading files... {files_completed}/{len(self.test_files)} completed")
        
        # Move to next file
        if self.current_progress % 20 == 0:
            self.current_file_index += 1

class TestWindow(QMainWindow):
    """Test window with upload progress functionality"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Upload Progress Test")
        self.setGeometry(100, 100, 600, 400)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create test button
        self.test_button = QPushButton("Test Upload Progress")
        self.test_button.clicked.connect(self.test_upload_progress)
        layout.addWidget(self.test_button)
        
        # Initialize HappyTag's progress system
        self.init_progress_system()
        
        # Create upload simulator
        self.upload_simulator = UploadSimulator()
        self.setup_simulator_connections()

    def init_progress_system(self):
        """Initialize the progress overlay system from HappyTag"""
        # Copy the progress system methods from HappyTag
        self.progress_overlay = None
        self.progress_bar = None
        self.progress_label = None

    def create_progress_overlay(self):
        """Create progress overlay - copied from HappyTag"""
        from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QFont
        
        # Create overlay widget
        self.progress_overlay = QWidget(self)
        self.progress_overlay.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.7);
            }
        """)
        
        # Create main layout for the overlay
        overlay_layout = QVBoxLayout(self.progress_overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setAlignment(Qt.AlignCenter)
        
        # Create progress bar container with adaptive height
        progress_container = QWidget()
        progress_container.setFixedSize(400, 80)  # Fixed width, adaptive height
        progress_container.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 10px;
                border: 2px solid #ccc;
            }
        """)
        
        # Create progress bar layout with controlled spacing
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(20, 20, 20, 20)
        progress_layout.setSpacing(10)  # Controlled spacing between elements
        
        # Create status label with word wrap and center alignment
        self.progress_label = QLabel("Processing files...")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setWordWrap(True)
        self.progress_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.progress_label.setStyleSheet("color: #333; margin: 0px;")
        progress_layout.addWidget(self.progress_label)
        
        # Create progress bar with fixed height
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(20)  # Fixed height for progress bar
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        # Add container to overlay
        overlay_layout.addWidget(progress_container)
        
        # Initially hide the overlay
        self.progress_overlay.hide()

    def show_progress(self, total_files, message=None):
        """Show progress bar with total file count and custom message"""
        if not self.progress_overlay:
            self.create_progress_overlay()
        
        if message:
            self.progress_label.setText(message)
        else:
            self.progress_label.setText("Processing files...")
        
        self.progress_bar.setRange(0, total_files)
        self.progress_bar.setValue(0)
        self.progress_overlay.resize(self.size())
        self.progress_overlay.show()
        self.progress_overlay.raise_()

    def update_upload_progress(self, percentage):
        """Update progress bar with percentage (0-100) for uploads"""
        if self.progress_bar:
            # Convert percentage to file count based on total range
            total_files = self.progress_bar.maximum()
            current_value = int((percentage / 100.0) * total_files)
            self.progress_bar.setValue(current_value)
            QApplication.processEvents()  # Force UI update

    def update_progress_label(self, message):
        """Update the progress label with a custom message"""
        if hasattr(self, 'progress_label') and self.progress_label:
            self.progress_label.setText(message)
            QApplication.processEvents()

    def hide_progress(self):
        """Hide progress bar"""
        if self.progress_overlay:
            self.progress_overlay.hide()

    def setup_simulator_connections(self):
        """Setup connections for the upload simulator"""
        self.upload_simulator.upload_progress_signal.connect(self.update_upload_progress)
        self.upload_simulator.upload_status_signal.connect(self.update_progress_label)
        self.upload_simulator.upload_complete_signal.connect(self.on_upload_complete)
        self.upload_simulator.upload_preview_signal.connect(self.on_upload_preview)

    def test_upload_progress(self):
        """Test the upload progress functionality"""
        print("Starting upload progress test...")
        
        # Show progress bar
        total_files = 5
        upload_message = f"Uploading to Cloudinary...\n{total_files} files to process"
        self.show_progress(total_files, upload_message)
        
        # Start simulation
        self.upload_simulator.start_simulation()

    def on_upload_complete(self, upload_data):
        """Handle upload completion"""
        self.hide_progress()
        uploaded_count, error_count, metadata_failures = upload_data
        print(f"Upload complete: {uploaded_count} files uploaded, {error_count} errors, {metadata_failures} metadata failures")

    def on_upload_preview(self, file_path):
        """Handle upload preview updates"""
        print(f"Currently uploading: {file_path}")

    def resizeEvent(self, event):
        """Handle window resize to reposition progress overlay"""
        super().resizeEvent(event)
        if self.progress_overlay:
            self.progress_overlay.resize(self.size())

def main():
    """Run the upload progress test"""
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    print("Upload Progress Test Window opened.")
    print("Click 'Test Upload Progress' to see the upload progress bar in action.")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
