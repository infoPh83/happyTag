#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_spreadsheet_header():
    """Check the first few rows of the spreadsheet to understand header structure"""
    try:
        from odf.opendocument import load
        from odf.table import Table, TableRow, TableCell
        from odf.text import P
        from odf.style import Style
        
        spreadsheet_path = "D:/Python playfolder/happyTag/docs/Cloudinary tags.ods"
        
        print(f"[INFO] Checking spreadsheet header structure: {spreadsheet_path}")
        
        # Load the document
        doc = load(spreadsheet_path)
        
        # Get the first table (sheet)
        tables = doc.getElementsByType(Table)
        if not tables:
            print("[ERROR] No tables found in spreadsheet")
            return
            
        table = tables[0]
        rows = table.getElementsByType(TableRow)
        
        print(f"[INFO] Found {len(rows)} rows in spreadsheet")
        print("\n=== FIRST 5 ROWS ===")
        
        for row_idx in range(min(5, len(rows))):
            row = rows[row_idx]
            cells = row.getElementsByType(TableCell)
            
            print(f"\nRow {row_idx + 1}:")
            for col_idx in range(min(10, len(cells))):  # Show first 10 columns
                cell = cells[col_idx]
                
                # Get cell text
                text_content = ""
                for text_node in cell.getElementsByType(P):
                    text_content += str(text_node).strip()
                
                # Get background color
                bg_color = "none"
                if hasattr(cell, 'getAttribute') and cell.getAttribute('stylename'):
                    style_name = cell.getAttribute('stylename')
                    if style_name:
                        # Find the style
                        styles = doc.automaticstyles.getElementsByType(Style)
                        for style in styles:
                            if style.getAttribute('name') == style_name:
                                for prop in style.childNodes:
                                    if hasattr(prop, 'getAttribute'):
                                        bg = prop.getAttribute('backgroundcolor')
                                        if bg:
                                            bg_color = bg
                                            break
                
                print(f"  Col {col_idx + 1}: '{text_content}' (bg: {bg_color})")
            
    except Exception as e:
        print(f"[ERROR] Failed to check spreadsheet: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_spreadsheet_header()