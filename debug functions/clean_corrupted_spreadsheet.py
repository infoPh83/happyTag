#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def clean_corrupted_spreadsheet():
    """Clean up the corrupted spreadsheet by removing duplicate grumpy entries"""
    try:
        from odf.opendocument import load
        from odf.table import Table, TableRow, TableCell
        from odf.text import P
        
        spreadsheet_path = "D:/Python playfolder/happyTag/docs/Cloudinary tags.ods"
        
        print(f"[INFO] Cleaning corrupted spreadsheet: {spreadsheet_path}")
        
        # Create a backup first
        import shutil
        backup_path = spreadsheet_path.replace('.ods', '_backup_before_cleanup.ods')
        shutil.copy2(spreadsheet_path, backup_path)
        print(f"[INFO] Created backup: {backup_path}")
        
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
        
        rows = tags_sheet.getElementsByType(TableRow)
        
        # Find the people's mood row (row 13 according to screenshot)
        for row_idx, row in enumerate(rows):
            cells = row.getElementsByType(TableCell)
            if len(cells) > 1:
                # Get text from the second cell (category column)
                category_cell = cells[1]
                category_text = ""
                for p in category_cell.getElementsByType(P):
                    if p.firstChild:
                        category_text += str(p.firstChild)
                
                if category_text.strip().lower() == "people's mood":
                    print(f"[INFO] Found 'people's mood' category at row {row_idx + 1}")
                    
                    # Count current grumpy instances
                    grumpy_count = 0
                    for col_idx in range(3, len(cells)):
                        cell = cells[col_idx]
                        cell_text = ""
                        for p in cell.getElementsByType(P):
                            if p.firstChild:
                                cell_text += str(p.firstChild)
                        
                        if cell_text.strip().lower() == "grumpy":
                            grumpy_count += 1
                    
                    print(f"[INFO] Found {grumpy_count} instances of 'grumpy' in this row")
                    
                    # Clean up: keep only the legitimate tags
                    legitimate_tags = ["Smiling", "grumpy"]  # The original tags we want to keep
                    
                    # Clear all tag cells (starting from column D, index 3)
                    cells_to_remove = []
                    for col_idx in range(3, len(cells)):
                        cell = cells[col_idx]
                        # Clear the cell content
                        for p in cell.getElementsByType(P):
                            cell.removeChild(p)
                    
                    # Re-add only the legitimate tags
                    for i, tag in enumerate(legitimate_tags):
                        if i + 3 < len(cells):  # Make sure we have enough cells
                            cell = cells[i + 3]
                            new_p = P()
                            new_p.addText(tag)
                            cell.appendChild(new_p)
                            print(f"[INFO] Restored tag '{tag}' to column {i + 4}")
                    
                    break
        
        # Save the cleaned document
        doc.save(spreadsheet_path)
        print(f"[SUCCESS] Cleaned spreadsheet saved to: {spreadsheet_path}")
        print(f"[INFO] Backup available at: {backup_path}")
        
        # Verify the cleanup
        print(f"\n=== VERIFICATION ===")
        doc_verify = load(spreadsheet_path)
        tags_sheet_verify = None
        for table in doc_verify.getElementsByType(Table):
            if table.getAttribute('name') == 'TAGs':
                tags_sheet_verify = table
                break
        
        rows_verify = tags_sheet_verify.getElementsByType(TableRow)
        for row_idx, row in enumerate(rows_verify):
            cells = row.getElementsByType(TableCell)
            if len(cells) > 1:
                category_cell = cells[1]
                category_text = ""
                for p in category_cell.getElementsByType(P):
                    if p.firstChild:
                        category_text += str(p.firstChild)
                
                if category_text.strip().lower() == "people's mood":
                    print(f"After cleanup - 'people's mood' category:")
                    for col_idx in range(3, min(len(cells), 10)):  # Check first 7 tag columns
                        cell = cells[col_idx]
                        cell_text = ""
                        for p in cell.getElementsByType(P):
                            if p.firstChild:
                                cell_text += str(p.firstChild)
                        
                        if cell_text.strip():
                            print(f"  Column {col_idx + 1}: '{cell_text.strip()}'")
                    break
        
    except Exception as e:
        print(f"[ERROR] Failed to clean spreadsheet: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    clean_corrupted_spreadsheet()