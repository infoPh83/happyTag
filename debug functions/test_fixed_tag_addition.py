#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_fixed_tag_addition():
    """Test the fixed tag addition to ensure no duplication occurs"""
    try:
        from utilities.addTagDialog import AddKeywordDialog
        from utilities.tag_manager import TagManager
        from PyQt5.QtWidgets import QApplication
        
        print(f"[INFO] Testing fixed tag addition to prevent duplication")
        
        # Create QApplication if not exists
        app = QApplication.instance() or QApplication(sys.argv)
        
        spreadsheet_path = "D:/Python playfolder/happyTag/docs/Cloudinary tags.ods"
        
        # Load tags first
        tag_manager = TagManager()
        tags_data = tag_manager.read_tags_from_ods_alternative(spreadsheet_path)
        
        print(f"[INFO] Loaded {len(tags_data)} categories (header row should be skipped)")
        
        # Create AddKeywordDialog with tags_data
        dialog = AddKeywordDialog(spreadsheet_path, tags_data=tags_data)
        
        # Test adding a new tag that should trigger pandas fallback
        print(f"\n=== Testing New Tag Addition (should use pandas fallback) ===")
        
        new_tag = "peaceful"  # A new tag that doesn't exist
        category = "people's mood"
        color = "#f0c0c8"  # people's mood category color
        is_new_category = False
        
        print(f"[TEST] Adding tag '{new_tag}' to category '{category}'")
        
        # Check current state before adding
        print(f"\n--- BEFORE adding '{new_tag}' ---")
        from odf.opendocument import load
        from odf.table import Table, TableRow, TableCell
        from odf.text import P
        
        doc_before = load(spreadsheet_path)
        tags_sheet_before = None
        for table in doc_before.getElementsByType(Table):
            if table.getAttribute('name') == 'TAGs':
                tags_sheet_before = table
                break
        
        if not tags_sheet_before:
            print("[ERROR] Could not find TAGs sheet before")
            return
            
        rows_before = tags_sheet_before.getElementsByType(TableRow)
        for row_idx, row in enumerate(rows_before):
            cells = row.getElementsByType(TableCell)
            if len(cells) > 1:
                category_cell = cells[1]
                category_text = ""
                for p in category_cell.getElementsByType(P):
                    if p.firstChild:
                        category_text += str(p.firstChild)
                
                if category_text.strip().lower() == "people's mood":
                    print(f"Found 'people's mood' category at row {row_idx + 1}")
                    for col_idx in range(3, min(len(cells), 8)):  # Check first few tag columns
                        cell = cells[col_idx]
                        cell_text = ""
                        for p in cell.getElementsByType(P):
                            if p.firstChild:
                                cell_text += str(p.firstChild)
                        
                        if cell_text.strip():
                            print(f"  - Column {col_idx + 1}: '{cell_text.strip()}'")
                    break
        
        # Add the tag
        result = dialog.update_spreadsheet(new_tag, category, color, is_new_category)
        
        if result is True:
            print(f"[SUCCESS] Tag '{new_tag}' was added successfully")
        else:
            print(f"[ERROR] Failed to add tag '{new_tag}': {result}")
            return
        
        # Check after state
        print(f"\n--- AFTER adding '{new_tag}' ---")
        
        doc_after = load(spreadsheet_path)
        tags_sheet_after = None
        for table in doc_after.getElementsByType(Table):
            if table.getAttribute('name') == 'TAGs':
                tags_sheet_after = table
                break
        
        if not tags_sheet_after:
            print("[ERROR] Could not find TAGs sheet after")
            return
            
        rows_after = tags_sheet_after.getElementsByType(TableRow)
        for row_idx, row in enumerate(rows_after):
            cells = row.getElementsByType(TableCell)
            if len(cells) > 1:
                category_cell = cells[1]
                category_text = ""
                for p in category_cell.getElementsByType(P):
                    if p.firstChild:
                        category_text += str(p.firstChild)
                
                if category_text.strip().lower() == "people's mood":
                    print(f"Found 'people's mood' category at row {row_idx + 1}")
                    
                    # Count instances of the new tag
                    new_tag_count = 0
                    for col_idx in range(3, len(cells)):
                        cell = cells[col_idx]
                        cell_text = ""
                        for p in cell.getElementsByType(P):
                            if p.firstChild:
                                cell_text += str(p.firstChild)
                        
                        if cell_text.strip():
                            print(f"  - Column {col_idx + 1}: '{cell_text.strip()}'")
                            if cell_text.strip().lower() == new_tag.lower():
                                new_tag_count += 1
                        elif col_idx < 8:  # Only show first few empty columns
                            break
                    
                    # Report results
                    if new_tag_count == 1:
                        print(f"\n✅ SUCCESS: Tag '{new_tag}' appears exactly once (no duplication)")
                    elif new_tag_count > 1:
                        print(f"\n❌ DUPLICATION DETECTED: Tag '{new_tag}' appears {new_tag_count} times!")
                    else:
                        print(f"\n⚠️ WARNING: Tag '{new_tag}' not found after addition")
                    break
        
    except Exception as e:
        print(f"[ERROR] Failed to test fixed tag addition: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_tag_addition()