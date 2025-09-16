#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_duplicate_prevention():
    """Test the duplicate prevention by simulating adding an existing tag"""
    try:
        from utilities.addTagDialog import AddKeywordDialog
        from PyQt5.QtWidgets import QApplication
        
        print(f"[INFO] Testing duplicate prevention in AddKeywordDialog")
        
        # Create QApplication if not exists
        app = QApplication.instance() or QApplication(sys.argv)
        
        spreadsheet_path = "D:/Python playfolder/happyTag/docs/Cloudinary tags.ods"
        
        # Load tags first
        from utilities.tag_manager import TagManager
        tag_manager = TagManager()
        tags_data = tag_manager.read_tags_from_ods_alternative(spreadsheet_path)
        
        # Create AddKeywordDialog with tags_data
        dialog = AddKeywordDialog(spreadsheet_path, tags_data=tags_data)
        
        # Test adding "grumpy" to "people's mood" category (it should already exist)
        print("\n=== Testing Duplicate Detection ===")
        
        # Directly test the update_spreadsheet method
        tag_text = "grumpy"
        category = "people's mood"
        color = "#f0c0c8"  # people's mood category color
        is_new_category = False
        
        print(f"[TEST] Attempting to add existing tag '{tag_text}' to category '{category}'")
        
        result = dialog.update_spreadsheet(tag_text, category, color, is_new_category)
        
        if result is False:
            print(f"[SUCCESS] ✅ Duplicate prevention worked! Tag '{tag_text}' was rejected.")
        elif result is True:
            print(f"[ERROR] ❌ Duplicate prevention failed! Tag '{tag_text}' was added (but shouldn't have been).")
        else:
            print(f"[ERROR] ❌ Unexpected result: {result}")
        
        # Test adding a new tag that doesn't exist
        print(f"\n=== Testing New Tag Addition ===")
        new_tag = "cheerful"
        print(f"[TEST] Attempting to add new tag '{new_tag}' to category '{category}'")
        
        result2 = dialog.update_spreadsheet(new_tag, category, color, is_new_category)
        
        if result2 is True:
            print(f"[SUCCESS] ✅ New tag addition worked! Tag '{new_tag}' was added.")
            # Note: This actually modifies the spreadsheet, so we should clean it up
            print(f"[INFO] Note: '{new_tag}' was actually added to the spreadsheet")
        elif result2 is False:
            print(f"[INFO] New tag '{new_tag}' was rejected (might already exist)")
        else:
            print(f"[ERROR] ❌ Unexpected result for new tag: {result2}")
        
    except Exception as e:
        print(f"[ERROR] Failed to test duplicate prevention: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_duplicate_prevention()