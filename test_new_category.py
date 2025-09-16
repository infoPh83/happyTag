#!/usr/bin/env python3

"""
Test the NEW category functionality in Add Keyword Dialog
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

def test_new_category_functionality():
    print("Testing NEW category functionality...")
    
    app = QApplication(sys.argv)
    
    from utilities.addTagDialog import AddKeywordDialog
    
    # Create test dialog with some sample data
    test_tags_data = [
        ("Category A", "#FF0000", [("tag1", "#FF0000"), ("tag2", "#FF0000")]),
        ("Category B", "#00FF00", [("tag3", "#00FF00")]),
    ]
    
    dialog = AddKeywordDialog(
        spreadsheet_path="test_tags.ods",  # Use a test file instead of hardcoded path
        parent=None,
        tags_data=test_tags_data
    )
    
    # Show the dialog to ensure proper initialization
    dialog.show()
    app.processEvents()  # Process any pending events
    
    print("✅ Dialog created successfully")
    print(f"Category combo has {dialog.category_combo.count()} items")
    
    # List all items in the combo
    print("Categories in combo:")
    for i in range(dialog.category_combo.count()):
        item_text = dialog.category_combo.itemText(i)
        print(f"  - {item_text}")
    
    # Test selecting NEW
    new_index = -1
    for i in range(dialog.category_combo.count()):
        if dialog.category_combo.itemText(i) == "NEW":
            new_index = i
            break
    
    if new_index >= 0:
        print(f"✅ Found NEW option at index {new_index}")
        
        # Select NEW
        dialog.category_combo.setCurrentIndex(new_index)
        
        # Check if new category controls are visible
        print(f"[DEBUG] new_category_input visible: {dialog.new_category_input.isVisible()}")
        print(f"[DEBUG] color_picker visible: {dialog.color_picker.isVisible()}")
        print(f"[DEBUG] new_category_label visible: {dialog.new_category_label.isVisible()}")
        print(f"[DEBUG] color_picker_label visible: {dialog.color_picker_label.isVisible()}")
        
        if dialog.new_category_input.isVisible() and dialog.color_picker.isVisible():
            print("✅ New category controls are visible when NEW is selected")
        else:
            print("❌ New category controls are not visible")
        
        # Test entering a new category name
        dialog.new_category_input.setText("Test Category")
        dialog.tag_text_input.setText("Test Tag")
        
        print("✅ Test data entered:")
        print(f"  Tag: {dialog.tag_text_input.text()}")
        print(f"  New category: {dialog.new_category_input.text()}")
        print(f"  Color: {dialog.color_picker.get_color().name()}")
        
    else:
        print("❌ NEW option not found in combo")
    
    # Test selecting an existing category
    if dialog.category_combo.count() > 1:
        dialog.category_combo.setCurrentIndex(0)  # Select first existing category
        
        if not dialog.new_category_input.isVisible() and not dialog.color_picker.isVisible():
            print("✅ New category controls are hidden when existing category is selected")
        else:
            print("❌ New category controls should be hidden for existing categories")
    
    print("🎉 NEW category functionality test completed!")
    
    app.quit()
    return 0

if __name__ == "__main__":
    exit_code = test_new_category_functionality()
    sys.exit(exit_code)
