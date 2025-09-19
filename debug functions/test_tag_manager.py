#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from PyQt5.QtWidgets import QApplication
from utilities.tagManager import TagManagerDialog

def test_tag_manager():
    """Test the Tag Manager Dialog"""
    app = QApplication(sys.argv)
    
    try:
        # Create tag manager dialog
        dialog = TagManagerDialog()
        
        # Check if the button exists
        if hasattr(dialog, 'openAddKeywordDialogButton'):
            print("✅ openAddKeywordDialogButton found in dialog")
            print(f"Button text: {dialog.openAddKeywordDialogButton.text()}")
            print(f"Button enabled: {dialog.openAddKeywordDialogButton.isEnabled()}")
            
            # Test the button click manually
            print("Testing button click...")
            dialog.open_add_keyword_dialog()
            print("✅ Button click method executed successfully")
            
        else:
            print("❌ openAddKeywordDialogButton NOT found in dialog")
            print("Available attributes:")
            for attr in dir(dialog):
                if 'button' in attr.lower() or 'Button' in attr:
                    print(f"  - {attr}")
        
        # Show dialog
        dialog.show()
        
        print("Tag Manager Dialog created and shown successfully")
        
        # Don't start event loop, just test creation
        return True
        
    except Exception as e:
        print(f"❌ Error creating tag manager dialog: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_tag_manager()
    if success:
        print("✅ Tag Manager test completed successfully")
    else:
        print("❌ Tag Manager test failed")
