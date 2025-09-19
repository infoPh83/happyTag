#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from PyQt5.QtWidgets import QApplication
from utilities.addTagDialog import AddKeywordDialog

def test_add_keyword_with_tags_data():
    """Test the Add Keyword Dialog with sample tags data structure"""
    app = QApplication(sys.argv)
    
    # Sample tags data structure like what comes from tag_manager
    sample_tags_data = [
        ("in/outdoor", "#ecaba2", [
            ("Indoor", "#ecaba2"),
            ("Outdoor", "#ecaba2"),
            ("Window Frontage", "#ecaba2")
        ]),
        ("season", "#ecdc9f", [
            ("Summer", "#ecdc9f"),
            ("Spring / Autumn", "#ecdc9f"),
            ("Winter", "#ecdc9f"),
            ("Christmas", "#ecdc9f")
        ]),
        ("weather", "#a5ecc7", [
            ("Sunshine", "#a5ecc7"),
            ("Cloudy", "#a5ecc7"),
            ("Night", "#a5ecc7")
        ]),
        ("people", "#b9bcef", [
            ("No people", "#b9bcef"),
            ("Couples", "#b9bcef"),
            ("Business attire", "#b9bcef"),
            ("Diversity", "#b9bcef")
        ])
    ]
    
    try:
        # Create dialog with sample tags data
        spreadsheet_path = "test images/TAGs final.ods"
        dialog = AddKeywordDialog(spreadsheet_path, tags_data=sample_tags_data)
        
        print("✅ AddKeywordDialog created successfully with tags data")
        print(f"Spreadsheet path: {dialog.spreadsheet_path}")
        print(f"Existing categories loaded: {len(dialog.existing_categories)}")
        print(f"Category colors loaded: {len(dialog.category_colors)}")
        
        if dialog.existing_categories:
            print("Categories loaded from tags data:")
            for category in dialog.existing_categories:
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
                print("Categories in combo:")
                for i in range(combo_count):
                    print(f"  - {dialog.category_combo.itemText(i)}")
        
        # Show dialog briefly to test UI
        dialog.show()
        
        print("✅ Add Keyword Dialog with tags data test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error in tags data test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_add_keyword_with_tags_data()
    if success:
        print("\n🎉 Add Keyword Dialog with tags data test passed!")
    else:
        print("\n❌ Test failed")
