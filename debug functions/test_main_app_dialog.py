#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from main import MainWindow

def test_dialog_in_main_app():
    """Test opening the Add Keyword Dialog from the main application"""
    
    app = QApplication(sys.argv)
    
    try:
        # Create the main application window
        print("Creating MainWindow...")
        main_window = MainWindow()
        main_window.show()
        
        # Give it a moment to initialize
        def test_tag_manager():
            try:
                print("Attempting to open Tag Manager...")
                
                # Try to access the Tag Manager menu action
                if hasattr(main_window, 'actionTags_Window'):
                    print("Found actionTags_Window, triggering...")
                    main_window.actionTags_Window.trigger()
                    print("Tag Manager action triggered successfully")
                else:
                    print("❌ actionTags_Window not found")
                    print("Available actions:")
                    for attr in dir(main_window):
                        if 'action' in attr.lower() or 'tag' in attr.lower():
                            print(f"  - {attr}")
                
                # Also try direct access to tag manager
                if hasattr(main_window, 'open_tag_manager'):
                    print("Found open_tag_manager method, calling directly...")
                    main_window.open_tag_manager()
                    print("Tag manager opened directly")
                else:
                    print("❌ open_tag_manager method not found")
                
            except Exception as e:
                print(f"❌ Error testing tag manager: {e}")
                import traceback
                traceback.print_exc()
            
            # Exit after test
            QTimer.singleShot(2000, app.quit)  # Close after 2 seconds
        
        # Run test after a short delay to let the app initialize
        QTimer.singleShot(1000, test_tag_manager)
        
        print("Starting application event loop...")
        return app.exec_()
        
    except Exception as e:
        print(f"❌ Error creating main application: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = test_dialog_in_main_app()
    print(f"Test completed with exit code: {exit_code}")
    sys.exit(exit_code)
