#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from PyQt5.QtWidgets import QApplication
from utilities.addTagDialog import AddKeywordDialog

def test_add_keyword_dialog_full():
    """Test the Add Keyword Dialog with full functionality"""
    app = QApplication(sys.argv)
    
    try:
        # Create dialog with a test spreadsheet path
        spreadsheet_path = "/Volumes/Marketing/06. Databases/TAGs final.ods"
        dialog = AddKeywordDialog(spreadsheet_path)
        
        print("✅ AddKeywordDialog created successfully")
        print(f"Spreadsheet path: {dialog.spreadsheet_path}")
        print(f"Existing categories loaded: {len(dialog.existing_categories)}")
        print(f"Category colors loaded: {len(dialog.category_colors)}")
        
        if dialog.existing_categories:
            print("Sample categories:")
            for i, category in enumerate(dialog.existing_categories[:5]):  # Show first 5
                color = dialog.category_colors.get(category, "N/A")
                print(f"  - {category}: {color}")
        
        # Check UI components
        print(f"Tag input field exists: {hasattr(dialog, 'tag_text_input')}")
        print(f"Category combo exists: {hasattr(dialog, 'category_combo')}")
        print(f"Color picker exists: {hasattr(dialog, 'color_picker')}")
        
        # Test category combo population
        if hasattr(dialog, 'category_combo'):
            combo_count = dialog.category_combo.count()
            print(f"Category combo has {combo_count} items")
            if combo_count > 0:
                print("First few categories in combo:")
                for i in range(min(3, combo_count)):
                    print(f"  - {dialog.category_combo.itemText(i)}")
        
        # Show dialog briefly to test UI
        dialog.show()
        
        print("✅ Full Add Keyword Dialog test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error in full test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_add_keyword_dialog_full()
    if success:
        print("\n🎉 All Add Keyword Dialog tests passed!")
    else:
        print("\n❌ Some tests failed")
