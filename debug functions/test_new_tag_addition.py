#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_new_tag_addition():
    """Test adding a completely new tag to see if it gets duplicated"""
    try:
        from utilities.addTagDialog import AddKeywordDialog
        from utilities.tag_manager import TagManager
        from PyQt5.QtWidgets import QApplication
        
        print(f"[INFO] Testing new tag addition to check for duplication bug")
        
        # Create QApplication if not exists
        app = QApplication.instance() or QApplication(sys.argv)
        
        spreadsheet_path = "D:/Python playfolder/happyTag/docs/Cloudinary tags.ods"
        
        # Load tags first
        tag_manager = TagManager()
        tags_data = tag_manager.read_tags_from_ods_alternative(spreadsheet_path)
        
        # Create AddKeywordDialog with tags_data
        dialog = AddKeywordDialog(spreadsheet_path, tags_data=tags_data)
        
        # Test adding a completely new tag
        print(f"\n=== Testing New Tag Addition ===")
        
        new_tag = "test_tag_unique"
        category = "people's mood"
        color = "#f0c0c8"  # people's mood category color
        is_new_category = False
        
        print(f"[TEST] Adding new tag '{new_tag}' to category '{category}'")
        
        # Check the before state
        print(f"\n--- BEFORE adding '{new_tag}' ---")
        from comprehensive_analysis import comprehensive_spreadsheet_analysis
        
        # Add the tag
        result = dialog.update_spreadsheet(new_tag, category, color, is_new_category)
        
        if result is True:
            print(f"[SUCCESS] Tag '{new_tag}' was added successfully")
        else:
            print(f"[ERROR] Failed to add tag '{new_tag}': {result}")
            return
        
        # Check the after state
        print(f"\n--- AFTER adding '{new_tag}' ---")
        
        # Re-analyze the spreadsheet to see if duplication occurred
        from odf.opendocument import load
        from odf.table import Table, TableRow, TableCell
        from odf.text import P
        
        doc = load(spreadsheet_path)
        
        # Find the TAGs sheet
        tags_sheet = None
        for table in doc.getElementsByType(Table):
            if table.getAttribute('name') == 'TAGs':
                tags_sheet = table
                break
        
        if not tags_sheet:
            print("[ERROR] TAGs sheet not found")
            return
        
        rows = tags_sheet.getElementsByType(TableRow)
        
        # Find the people's mood row and check for duplicates
        for row_idx, row in enumerate(rows):
            cells = row.getElementsByType(TableCell)
            if len(cells) > 1:
                # Check category name in column B
                category_cell = cells[1]
                category_text = ""
                for p in category_cell.getElementsByType(P):
                    if p.firstChild:
                        category_text += str(p.firstChild)
                
                if category_text.strip().lower() == "people's mood":
                    print(f"Found 'people's mood' category at row {row_idx + 1}")
                    
                    # Check all tag columns for our new tag
                    new_tag_instances = []
                    for col_idx in range(3, len(cells)):
                        cell = cells[col_idx]
                        cell_text = ""
                        for p in cell.getElementsByType(P):
                            if p.firstChild:
                                cell_text += str(p.firstChild)
                        
                        if cell_text.strip().lower() == new_tag.lower():
                            new_tag_instances.append((row_idx + 1, col_idx + 1))
                        
                        if cell_text.strip():
                            print(f"  - Column {col_idx + 1}: '{cell_text.strip()}'")
                    
                    # Report duplication
                    if len(new_tag_instances) > 1:
                        print(f"\n❌ DUPLICATION DETECTED! Tag '{new_tag}' appears {len(new_tag_instances)} times:")
                        for row, col in new_tag_instances:
                            print(f"    Row {row}, Column {col}")
                    elif len(new_tag_instances) == 1:
                        print(f"\n✅ No duplication detected. Tag '{new_tag}' appears once at Row {new_tag_instances[0][0]}, Column {new_tag_instances[0][1]}")
                    else:
                        print(f"\n⚠️ Tag '{new_tag}' not found after addition!")
                    break
        
    except Exception as e:
        print(f"[ERROR] Failed to test tag addition: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_tag_addition()