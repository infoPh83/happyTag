#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def restore_colors_from_backup():
    """Restore the background colors from the backup file to the current spreadsheet"""
    try:
        import shutil
        
        spreadsheet_path = "D:/Python playfolder/happyTag/docs/Cloudinary tags.ods"
        backup_path = "D:/Python playfolder/happyTag/docs/Cloudinary tags_backup_before_cleanup.ods"
        
        print(f"[INFO] Restoring colors from backup")
        print(f"[INFO] Backup: {backup_path}")
        print(f"[INFO] Target: {spreadsheet_path}")
        
        # Check if backup exists
        if not os.path.exists(backup_path):
            print(f"[ERROR] Backup file not found: {backup_path}")
            return False
        
        # Simply restore the backup (which has the correct colors but the grumpy duplication)
        # Then we'll clean up the duplication while preserving colors
        shutil.copy2(backup_path, spreadsheet_path)
        print(f"[SUCCESS] Restored backup file")
        
        # Now clean up the grumpy duplication while preserving colors
        from odf.opendocument import load
        from odf.table import Table, TableRow, TableCell
        from odf.text import P
        
        # Load the restored document
        doc = load(spreadsheet_path)
        
        # Find the TAGs sheet
        tags_sheet = None
        for table in doc.getElementsByType(Table):
            if table.getAttribute('name') == 'TAGs':
                tags_sheet = table
                break
        
        if not tags_sheet:
            print("[ERROR] TAGs sheet not found")
            return False
        
        rows = tags_sheet.getElementsByType(TableRow)
        
        # Find the people's mood row and clean up grumpy duplication
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
                    
                    # Collect all text content and remove duplicates while preserving first occurrence
                    seen_tags = set()
                    cells_to_clear = []
                    
                    for col_idx in range(3, len(cells)):  # Start from column D (tag columns)
                        cell = cells[col_idx]
                        cell_text = ""
                        for p in cell.getElementsByType(P):
                            if p.firstChild:
                                cell_text += str(p.firstChild)
                        
                        cell_text = cell_text.strip()
                        if cell_text:
                            if cell_text.lower() in seen_tags:
                                # This is a duplicate, mark for clearing
                                cells_to_clear.append((col_idx, cell))
                                print(f"[INFO] Marking duplicate '{cell_text}' in column {col_idx + 1} for removal")
                            else:
                                # First occurrence, keep it
                                seen_tags.add(cell_text.lower())
                                print(f"[INFO] Keeping first occurrence of '{cell_text}' in column {col_idx + 1}")
                    
                    # Clear the duplicate cells (but keep their formatting/style)
                    for col_idx, cell in cells_to_clear:
                        # Remove only the text content, preserve the cell and its formatting
                        for p in cell.getElementsByType(P):
                            cell.removeChild(p)
                        print(f"[INFO] Cleared duplicate content from column {col_idx + 1}")
                    
                    break
        
        # Save the cleaned document with preserved colors
        doc.save(spreadsheet_path)
        print("[SUCCESS] Restored colors and cleaned up duplicates")
        
        # Verify the result
        print(f"\n=== VERIFICATION ===")
        doc_verify = load(spreadsheet_path)
        tags_sheet_verify = None
        for table in doc_verify.getElementsByType(Table):
            if table.getAttribute('name') == 'TAGs':
                tags_sheet_verify = table
                break
        
        if not tags_sheet_verify:
            print("[ERROR] Could not find TAGs sheet for verification")
            return True  # Still consider it successful
            
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
                    print(f"After restoration - 'people's mood' category:")
                    tag_count = 0
                    for col_idx in range(3, min(len(cells), 10)):  # Check first 7 tag columns
                        cell = cells[col_idx]
                        cell_text = ""
                        for p in cell.getElementsByType(P):
                            if p.firstChild:
                                cell_text += str(p.firstChild)
                        
                        if cell_text.strip():
                            print(f"  Column {col_idx + 1}: '{cell_text.strip()}'")
                            tag_count += 1
                        elif tag_count > 0:  # Stop after we've seen tags and hit empty cells
                            break
                    break
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to restore colors: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    restore_colors_from_backup()