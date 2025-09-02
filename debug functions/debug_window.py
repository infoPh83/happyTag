#!/usr/bin/env python3
"""
Debug version that forces the window to appear in front and center screen
"""

import sys
import traceback
from main import *

class DebugMainWindow(MainWindow):
    def __init__(self):
        super().__init__()
        
        # Force window to center of screen and bring to front
        self.center_on_screen()
        self.force_to_front()
        
    def center_on_screen(self):
        """Center the window on the primary screen"""
        from PyQt5.QtWidgets import QDesktopWidget
        
        # Get screen geometry
        desktop = QDesktopWidget()
        screen_rect = desktop.screenGeometry()
        
        # Set a reasonable default size if not set
        if self.width() < 800 or self.height() < 600:
            self.resize(1200, 800)
        
        # Calculate center position
        x = (screen_rect.width() - self.width()) // 2
        y = (screen_rect.height() - self.height()) // 2
        
        # Move window to center
        self.move(x, y)
        print(f"[DEBUG] Window positioned at ({x}, {y}) with size {self.width()}x{self.height()}")
        
    def force_to_front(self):
        """Force window to appear in front of all other windows"""
        # Show window and force it to front
        self.show()
        self.raise_()
        self.activateWindow()
        
        print("[DEBUG] Window forced to front")
        
    def remove_stay_on_top(self):
        """Remove the stay-on-top flag after the window is visible"""
        # This method is no longer needed but kept for compatibility
        print("[DEBUG] Window should now be visible")

def debug_main():
    """Main function with window positioning debug"""
    try:
        print("=== HappyTag Debug Mode (with window positioning) ===")
        print("Starting application...")
        
        app = QApplication(sys.argv)
        
        print("Creating debug MainWindow...")
        window = DebugMainWindow()
        
        print("Window created successfully!")
        print("If you still don't see the window, check your taskbar or try Alt+Tab")
        
        result = app.exec_()
        print(f"Application exited with code: {result}")
        return result
        
    except Exception as e:
        print(f"\n=== ERROR OCCURRED ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"\n=== FULL TRACEBACK ===")
        traceback.print_exc()
        return 1
    
    finally:
        print("\n=== DEBUG SESSION COMPLETE ===")
        print("Press Enter to close this window...")
        try:
            input()
        except:
            import time
            time.sleep(5)

if __name__ == '__main__':
    debug_main()
