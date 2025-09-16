#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_odf_writing_behavior():
    """Test if the ODF library is causing duplication when writing to cells"""
    try:
        from odf.opendocument import load
        from odf.table import Table, TableRow, TableCell
        from odf.text import P
        
        spreadsheet_path = "D:/Python playfolder/happyTag/docs/Cloudinary tags.ods"
        
        print(f"[INFO] Testing ODF writing behavior")
        
        # Load the document
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
        
        # Find the people's mood category row
        rows = tags_sheet.getElementsByType(TableRow)
        category_row = None
        category_row_index = None
        
        for row_index, row in enumerate(rows):
            cells = row.getElementsByType(TableCell)
            if len(cells) > 1:
                # Get text from the second cell (category column)
                category_cell = cells[1]
                category_text = ""
                for p in category_cell.getElementsByType(P):
                    if p.firstChild:
                        category_text += str(p.firstChild)
                
                if category_text.strip().lower() == "people's mood":
                    category_row = row
                    category_row_index = row_index
                    print(f"[DEBUG] Found 'people's mood' category at row {row_index + 1}")
                    break
        
        if category_row is None:
            print("[ERROR] 'people's mood' category not found")
            return
        
        # Show current state before adding
        print(f"\n=== BEFORE ADDING TEST TAG ===")
        cells = category_row.getElementsByType(TableCell)
        for col_idx in range(3, len(cells)):
            cell = cells[col_idx]
            cell_text = ""
            for p in cell.getElementsByType(P):
                if p.firstChild:
                    cell_text += str(p.firstChild)
            
            if cell_text.strip():
                print(f"  Column {col_idx + 1}: '{cell_text.strip()}'")
        
        # Add a test tag using the same logic as AddKeywordDialog
        test_tag = "test_odf_behavior"
        
        # Find the first empty cell
        tag_added = False
        for cell_index in range(3, len(cells)):
            cell = cells[cell_index]
            # Check if cell is empty
            cell_text = ""
            for p in cell.getElementsByType(P):
                if p.firstChild:
                    cell_text += str(p.firstChild)
            
            if not cell_text.strip():
                print(f"[DEBUG] Found empty cell at column {cell_index + 1}, adding test tag")
                
                # Clear existing content (even if empty)
                for p in cell.getElementsByType(P):
                    cell.removeChild(p)
                
                # Add new text
                new_p = P()
                new_p.addText(test_tag)
                cell.appendChild(new_p)
                
                print(f"[DEBUG] Added tag '{test_tag}' to cell at column {cell_index + 1}")
                tag_added = True
                break
        
        if not tag_added:
            print("[DEBUG] No empty cell found, adding new cell to the row")
            # Add a new cell to the row for the tag
            new_cell = TableCell()
            new_p = P()
            new_p.addText(test_tag)
            new_cell.appendChild(new_p)
            category_row.appendChild(new_cell)
            print(f"[DEBUG] Added new cell with tag '{test_tag}' to end of row")
        
        # Save the document
        doc.save(spreadsheet_path)
        print("[DEBUG] Document saved")
        
        # Reload and check the result
        print(f"\n=== AFTER ADDING TEST TAG ===")
        doc_reloaded = load(spreadsheet_path)
        
        # Find the TAGs sheet again
        tags_sheet_reloaded = None
        for table in doc_reloaded.getElementsByType(Table):
            if table.getAttribute('name') == 'TAGs':
                tags_sheet_reloaded = table
                break
        
        # Find the people's mood row again
        if not tags_sheet_reloaded:
            print("[ERROR] Could not find TAGs sheet after reload")
            return
            
        rows_reloaded = tags_sheet_reloaded.getElementsByType(TableRow)
        for row_index, row in enumerate(rows_reloaded):
            cells = row.getElementsByType(TableCell)
            if len(cells) > 1:
                # Get text from the second cell (category column)
                category_cell = cells[1]
                category_text = ""
                for p in category_cell.getElementsByType(P):
                    if p.firstChild:
                        category_text += str(p.firstChild)
                
                if category_text.strip().lower() == "people's mood":
                    print(f"[DEBUG] Found 'people's mood' category at row {row_index + 1} after reload")
                    
                    # Count instances of our test tag
                    test_tag_count = 0
                    cells_reloaded = row.getElementsByType(TableCell)
                    
                    for col_idx in range(3, len(cells_reloaded)):
                        cell = cells_reloaded[col_idx]
                        cell_text = ""
                        for p in cell.getElementsByType(P):
                            if p.firstChild:
                                cell_text += str(p.firstChild)
                        
                        if cell_text.strip():
                            print(f"  Column {col_idx + 1}: '{cell_text.strip()}'")
                            if cell_text.strip() == test_tag:
                                test_tag_count += 1
                    
                    # Report results
                    if test_tag_count == 1:
                        print(f"\n✅ SUCCESS: Test tag '{test_tag}' appears exactly once")
                    elif test_tag_count > 1:
                        print(f"\n❌ DUPLICATION DETECTED: Test tag '{test_tag}' appears {test_tag_count} times!")
                    else:
                        print(f"\n⚠️ WARNING: Test tag '{test_tag}' not found after writing")
                    break
        
    except Exception as e:
        print(f"[ERROR] Failed to test ODF writing behavior: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_odf_writing_behavior()