#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_tag_addition():
    """Test adding a tag to see if duplication occurs"""
    try:
        # First, let's check the current state before adding
        spreadsheet_path = "D:/Python playfolder/happyTag/docs/Cloudinary tags.ods"
        
        print(f"[INFO] Testing tag addition to: {spreadsheet_path}")
        
        # Check if "grumpy" already exists
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
        
        # Look for "grumpy" in the spreadsheet
        grumpy_count = 0
        grumpy_locations = []
        
        rows = tags_sheet.getElementsByType(TableRow)
        for row_idx, row in enumerate(rows):
            cells = row.getElementsByType(TableCell)
            for col_idx, cell in enumerate(cells):
                cell_text = ""
                for p in cell.getElementsByType(P):
                    if p.firstChild:
                        cell_text += str(p.firstChild)
                
                if cell_text.strip().lower() == "grumpy":
                    grumpy_count += 1
                    grumpy_locations.append((row_idx + 1, col_idx + 1))
        
        print(f"\n=== GRUMPY TAG ANALYSIS ===")
        print(f"Found {grumpy_count} instances of 'grumpy':")
        for row, col in grumpy_locations:
            print(f"  - Row {row}, Column {col}")
        
        # Also check what's in the "people's mood" category
        print(f"\n=== PEOPLE'S MOOD CATEGORY ===")
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
                    # Show all tags in this category
                    for col_idx in range(3, len(cells)):
                        cell = cells[col_idx]
                        cell_text = ""
                        for p in cell.getElementsByType(P):
                            if p.firstChild:
                                cell_text += str(p.firstChild)
                        
                        if cell_text.strip():
                            print(f"  - Column {col_idx + 1}: '{cell_text.strip()}'")
                    break
        
    except Exception as e:
        print(f"[ERROR] Failed to analyze tag addition: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tag_addition()