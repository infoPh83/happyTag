#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from main import MainWindow

def test_add_keyword_button():
    """Test clicking the Add Keyword button in the TagManager"""
    
    app = QApplication(sys.argv)
    
    try:
        print("Creating MainWindow...")
        main_window = MainWindow()
        main_window.show()
        
        def click_add_button():
            try:
                print("Opening Tag Manager...")
                main_window.show_tag_manager()
                
                # Give Tag Manager a moment to initialize
                def try_click_button():
                    try:
                        tag_manager = main_window.tag_manager
                        if tag_manager and hasattr(tag_manager, 'openAddKeywordDialogButton'):
                            print("Found Add Keyword button, clicking it...")
                            tag_manager.openAddKeywordDialogButton.click()
                            print("✅ Add Keyword button clicked successfully!")
                        else:
                            print("❌ Add Keyword button not found in TagManager")
                            
                    except Exception as e:
                        print(f"❌ Error clicking button: {e}")
                        import traceback
                        traceback.print_exc()
                    
                    # Exit after test
                    QTimer.singleShot(3000, app.quit)  # Close after 3 seconds
                
                # Try clicking the button after Tag Manager is shown
                QTimer.singleShot(500, try_click_button)
                
            except Exception as e:
                print(f"❌ Error opening Tag Manager: {e}")
                import traceback
                traceback.print_exc()
                QTimer.singleShot(1000, app.quit)
        
        # Run test after a short delay
        QTimer.singleShot(1000, click_add_button)
        
        print("Starting application...")
        return app.exec_()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = test_add_keyword_button()
    print(f"Test completed with exit code: {exit_code}")
    sys.exit(exit_code)
