#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def clean_shocked_duplication():
    """Clean up the 'shocked' duplication in the people's mood category"""
    try:
        from odf.opendocument import load
        from odf.table import Table, TableRow, TableCell
        from odf.text import P
        
        spreadsheet_path = "D:/Python playfolder/happyTag/docs/Cloudinary tags.ods"
        
        print(f"[INFO] Cleaning 'shocked' duplication from: {spreadsheet_path}")
        
        # Create a backup first
        import shutil
        backup_path = spreadsheet_path.replace('.ods', '_backup_before_shocked_cleanup.ods')
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
        
        # Find the people's mood row
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
                    
                    # Clean up duplicates: keep only the first occurrence of each tag
                    seen_tags = set()
                    
                    for col_idx in range(3, len(cells)):  # Start from column D (tag columns)
                        cell = cells[col_idx]
                        cell_text = ""
                        for p in cell.getElementsByType(P):
                            if p.firstChild:
                                cell_text += str(p.firstChild)
                        
                        cell_text = cell_text.strip()
                        if cell_text:
                            if cell_text.lower() in seen_tags:
                                # This is a duplicate, clear it
                                for p in cell.getElementsByType(P):
                                    cell.removeChild(p)
                                print(f"[INFO] Removed duplicate '{cell_text}' from column {col_idx + 1}")
                            else:
                                # First occurrence, keep it
                                seen_tags.add(cell_text.lower())
                                print(f"[INFO] Keeping first occurrence of '{cell_text}' in column {col_idx + 1}")
                    
                    break
        
        # Save the cleaned document
        doc.save(spreadsheet_path)
        print("[SUCCESS] Cleaned duplicates and saved")
        
        # Verify the result
        print(f"\n=== VERIFICATION ===")
        doc_verify = load(spreadsheet_path)
        tags_sheet_verify = None
        for table in doc_verify.getElementsByType(Table):
            if table.getAttribute('name') == 'TAGs':
                tags_sheet_verify = table
                break
        
        if tags_sheet_verify:
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
                        for col_idx in range(3, min(len(cells), 10)):
                            cell = cells[col_idx]
                            cell_text = ""
                            for p in cell.getElementsByType(P):
                                if p.firstChild:
                                    cell_text += str(p.firstChild)
                            
                            if cell_text.strip():
                                print(f"  Column {col_idx + 1}: '{cell_text.strip()}'")
                        break
        
    except Exception as e:
        print(f"[ERROR] Failed to clean duplication: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    clean_shocked_duplication()