#!/usr/bin/env python3
"""
Test the updated color system with new spreadsheet structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from utilities.tag_manager import TagManager
from utilities.settings_dialog import SettingsDialog

def test_new_color_system():
    """Test the updated color system"""
    
    # Create minimal QApplication for Qt widgets
    app = QApplication([])
    
    # Get the settings to find the spreadsheet path
    settings = SettingsDialog.get_saved_settings()
    cloudinary_tags_path = settings.get('cloudinary_tags_path')
    
    if not cloudinary_tags_path or not os.path.exists(cloudinary_tags_path):
        print(f"[ERROR] Cloudinary tags file not found: {cloudinary_tags_path}")
        return False
    
    print(f"[INFO] Testing new color system with spreadsheet: {cloudinary_tags_path}")
    
    try:
        # Create TagManager instance to load tags into memory
        print("[INFO] Creating TagManager to test new structure...")
        tag_manager = TagManager()
        
        # Force populate the tags list to load in-memory structure
        tag_manager.populate_tags_list()
        
        # Check if we have the in-memory structure
        if hasattr(tag_manager, 'original_tags_data') and tag_manager.original_tags_data:
            print(f"[SUCCESS] TagManager loaded {len(tag_manager.original_tags_data)} categories into memory")
            
            # Show the new structure
            print("\n=== NEW IN-MEMORY STRUCTURE ===")
            for category_name, category_color, tags in tag_manager.original_tags_data:
                print(f"Category: '{category_name}' (Color: {category_color})")
                print(f"  Tags: {tags}")
                print(f"  Tag count: {len(tags)}")
                print()
                
            # Test AddKeywordDialog with new structure
            print("=== TESTING ADD KEYWORD DIALOG ===")
            from utilities.addTagDialog import AddKeywordDialog
            
            add_dialog = AddKeywordDialog(cloudinary_tags_path, tag_manager, tag_manager.original_tags_data)
            
            # Check that categories were loaded correctly
            print(f"[INFO] AddKeywordDialog loaded {len(add_dialog.existing_categories)} categories:")
            for category in add_dialog.existing_categories:
                color = add_dialog.category_colors.get(category, "N/A")
                print(f"  - {category}: {color}")
            
            return True
        else:
            print("[ERROR] TagManager failed to load tags into memory")
            return False
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = test_new_color_system()
    sys.exit(0 if result else 1)