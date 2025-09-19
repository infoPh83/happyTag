#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def detailed_column_analysis():
    """Detailed analysis to check for infinite column duplication"""
    try:
        from odf.opendocument import load
        from odf.table import Table, TableRow, TableCell
        from odf.text import P
        
        spreadsheet_path = "D:/Python playfolder/happyTag/docs/Cloudinary tags.ods"
        
        print(f"[INFO] Detailed column analysis of: {spreadsheet_path}")
        
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
        
        print(f"\n=== DETAILED COLUMN ANALYSIS ===")
        
        # Focus on people's mood row
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
                    print(f"[INFO] This row has {len(cells)} total cells")
                    
                    # Check ALL cells in this row, not just the first few
                    aloof_count = 0
                    non_empty_count = 0
                    last_content_column = 0
                    
                    for col_idx in range(len(cells)):
                        cell = cells[col_idx]
                        cell_text = ""
                        for p in cell.getElementsByType(P):
                            if p.firstChild:
                                cell_text += str(p.firstChild)
                        
                        if cell_text.strip():
                            non_empty_count += 1
                            last_content_column = col_idx
                            if col_idx < 20:  # Show first 20 columns
                                print(f"  Column {col_idx + 1}: '{cell_text.strip()}'")
                            
                            if cell_text.strip().lower() == "aloof":
                                aloof_count += 1
                    
                    if len(cells) > 20:
                        print(f"  ... (showing first 20 columns only)")
                        print(f"  Total cells in row: {len(cells)}")
                        print(f"  Last column with content: {last_content_column + 1}")
                    
                    print(f"\n[SUMMARY]")
                    print(f"  - Total cells in people's mood row: {len(cells)}")
                    print(f"  - Non-empty cells: {non_empty_count}")
                    print(f"  - Instances of 'aloof': {aloof_count}")
                    
                    if aloof_count > 1:
                        print(f"  ❌ DUPLICATION DETECTED: 'aloof' appears {aloof_count} times")
                        
                        # Show all instances of aloof
                        print(f"  Locations of 'aloof':")
                        for col_idx in range(len(cells)):
                            cell = cells[col_idx]
                            cell_text = ""
                            for p in cell.getElementsByType(P):
                                if p.firstChild:
                                    cell_text += str(p.firstChild)
                            
                            if cell_text.strip().lower() == "aloof":
                                print(f"    - Column {col_idx + 1}")
                    else:
                        print(f"  ✅ No duplication detected")
                    
                    # Check if there are suspiciously many cells
                    if len(cells) > 50:
                        print(f"  ⚠️ WARNING: Row has {len(cells)} cells, which seems excessive")
                        print(f"  This might indicate a LibreOffice display issue even if content looks correct")
                    
                    break
        
    except Exception as e:
        print(f"[ERROR] Failed to analyze columns: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    detailed_column_analysis()