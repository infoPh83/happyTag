#!/usr/bin/env python3
"""
Manual test to verify Cloudinary visual status functionality
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import MainWindow

def test_cloudinary_visual_status():
    """Test that Cloudinary visual status is working"""
    
    app = QApplication(sys.argv)
    window = MainWindow()
    
    def test_cloudinary_after_load():
        """Test Cloudinary status after images are loaded"""
        try:
            if hasattr(window.image_flow_manager, 'image_widgets') and window.image_flow_manager.image_widgets:
                widgets = list(window.image_flow_manager.image_widgets.values())
                
                if len(widgets) >= 3:
                    print(f"\n🎨 Testing Cloudinary visual status with {len(widgets)} widgets")
                    
                    # Test different Cloudinary states
                    print("Setting Cloudinary statuses...")
                    widgets[0].set_cloudinary_status(False)  # Normal - white
                    widgets[1].set_cloudinary_status(True)   # Cloudinary - dark yellow
                    widgets[2].set_cloudinary_status(True)   # Cloudinary + selected
                    widgets[2].set_selected(True)
                    
                    # Verify the statuses were set
                    print(f"Widget 0 Cloudinary status: {widgets[0].get_cloudinary_status()}")
                    print(f"Widget 1 Cloudinary status: {widgets[1].get_cloudinary_status()}")
                    print(f"Widget 2 Cloudinary status: {widgets[2].get_cloudinary_status()}")
                    print(f"Widget 2 selection status: {widgets[2].is_selected_state()}")
                    
                    print("\n✅ Cloudinary visual status test complete!")
                    print("Expected visual results:")
                    print("  • Widget 1: White background (normal)")
                    print("  • Widget 2: Dark yellow background (#DAA520)")
                    print("  • Widget 3: Light golden background + blue border (#F0E68C)")
                    
                else:
                    print("❌ Not enough widgets loaded for testing")
                    
            else:
                print("❌ No image widgets available for testing")
                
        except Exception as e:
            print(f"❌ Error during Cloudinary test: {e}")
            import traceback
            traceback.print_exc()
    
    # Set up delayed test
    QTimer.singleShot(3000, test_cloudinary_after_load)  # 3 second delay
    
    window.show()
    
    print("🚀 Cloudinary Visual Status Test")
    print("=" * 50)
    print("1. Load some images (File > Open Folder)")
    print("2. Wait 3 seconds for automatic test")
    print("3. Check console output for results")
    print("4. Observe visual changes in the application")
    print("=" * 50)
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(test_cloudinary_visual_status())